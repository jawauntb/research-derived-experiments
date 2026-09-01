"""Export sanitized public demo receipts from gate-passing real fixtures."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, TypedDict

SITE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = SITE_ROOT.parents[1]
FIREWALL_ROOT = REPO_ROOT / "bio-claim-firewall"
SRC = FIREWALL_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
from worlds.arc_vcc import ArcVCCAdapter  # noqa: E402
from worlds.clinical_trials import (  # noqa: E402
    ClinicalTrialsAdapter,
    check_clinical_trials_claim,
)
from worlds.clinical_trials.adapter import (  # noqa: E402
    CHECKER_VERSION as CLINICAL_CHECKER_VERSION,
)
from worlds.open_targets import OpenTargetsAdapter  # noqa: E402
from worlds.open_targets.adapter import CHECKER_VERSION as TARGETS_CHECKER_VERSION  # noqa: E402

READINESS = FIREWALL_ROOT / "experiments/evidence_worlds/results/pilot_readiness.json"
FIXTURES = FIREWALL_ROOT / "tests/fixtures/worlds"
GENERATED_FROM = (
    "bio-claim-firewall/experiments/evidence_worlds/results/pilot_readiness.json"
)
EXPECTED_WORLDS = {"arc-vcc", "clinical-trials-sec", "open-targets"}
ARC_CHECKER_VERSION = "0.1.0"
EVALUATOR = FIREWALL_ROOT / "experiments/evidence_worlds/evaluation/pilot_readiness.py"


class _ReceiptCommon(TypedDict):
    scope: str
    citation_catalog: dict[str, dict[str, str]]
    source_reference: dict[str, str] | None
    license_label: str
    retrieval_clock: str


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"expected an object in {path}")
    return value


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _evaluate_pilot() -> dict[str, Any]:
    """Load the repo-local evaluator without colliding with third-party packages."""
    spec = importlib.util.spec_from_file_location("_bcf_pilot_readiness", EVALUATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load pilot-readiness evaluator: {EVALUATOR}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    result = module.evaluate_pilot()
    if not isinstance(result, dict):
        raise TypeError("pilot-readiness evaluator returned a non-object")
    return result


def _require_readiness() -> dict[str, Any]:
    report = _load(READINESS)
    fresh_report = _evaluate_pilot()
    if fresh_report != report:
        raise RuntimeError(
            "public export refused: tracked pilot readiness differs from a fresh evaluation"
        )
    worlds = report.get("worlds")
    if not isinstance(worlds, list):
        raise TypeError("public export refused: readiness worlds must be a list")
    passed = {
        item.get("world_id")
        for item in worlds
        if isinstance(item, dict) and item.get("status") == "PASS"
    }
    if (
        report.get("decision") != "READY_FOR_BOUNDED_PILOT"
        or report.get("pilot_ready") is not True
    ):
        raise RuntimeError(
            "public export refused: readiness decision is not READY_FOR_BOUNDED_PILOT"
        )
    if passed != EXPECTED_WORLDS:
        raise RuntimeError(
            f"public export refused: expected exactly three passing worlds, got {sorted(passed)}"
        )
    for item in worlds:
        if item.get("world_id") in EXPECTED_WORLDS and any(
            gate.get("status") != "PASS" for gate in item.get("fatal_gates", [])
        ):
            raise RuntimeError(
                f"public export refused: fatal gate failed for {item['world_id']}"
            )
    return report


def _public_receipt(
    result: Any,
    *,
    public_id: str,
    preset_label: str,
    scope: str,
    rule_title: str,
    rule_rationale: str,
    citation_catalog: dict[str, dict[str, str]],
    source_reference: dict[str, str] | None,
    license_label: str,
    retrieval_clock: str,
    selected_world_context_digest: str | None = None,
) -> dict[str, Any]:
    raw = result.as_dict()
    engine = raw.get("receipt", {})
    canonical = engine.get("canonical_payload", {}) if isinstance(engine, dict) else {}
    outcome = raw.get("outcome") or raw.get("verdict")
    if outcome == "ACCEPTED_CONDITIONALLY":
        outcome = "ACCEPTED"
    world_id = raw.get("world_id") or canonical.get("world_id")
    if world_id not in EXPECTED_WORLDS:
        raise RuntimeError(
            f"adapter returned an unregistered public world id: {world_id!r}"
        )
    if canonical.get("world_id", world_id) != world_id:
        raise RuntimeError(f"adapter receipt world identity disagrees: {public_id}")
    engine_receipt_id = engine.get("receipt_id")
    if not isinstance(engine_receipt_id, str) or len(engine_receipt_id) != 64:
        raise RuntimeError(f"adapter returned an invalid receipt id: {public_id}")
    engine_citation_ids = canonical.get("citations", [])
    if not isinstance(engine_citation_ids, list) or any(
        not isinstance(item, str) for item in engine_citation_ids
    ):
        raise RuntimeError(f"adapter receipt has invalid citations: {public_id}")
    citations = [
        {"engine_id": citation_id, **citation_catalog[citation_id]}
        for citation_id in engine_citation_ids
        if citation_id in citation_catalog
    ]
    if len(citations) != len(engine_citation_ids):
        missing = sorted(set(engine_citation_ids) - set(citation_catalog))
        raise RuntimeError(
            f"public citation catalog is incomplete for {public_id}: {missing}"
        )
    winning = raw.get("winning_rule")
    rule_id = winning.get("id") if isinstance(winning, dict) else winning
    world_digest = canonical.get("world_digest")
    public_scope = scope
    if outcome == "INCONCLUSIVE":
        if engine_citation_ids:
            raise RuntimeError(
                f"inconclusive adapter receipt cites positive evidence: {public_id}"
            )
        citations = []
        source_reference = None
        public_scope = "No evidence scope was established because the requested claim was unresolved."
    elif outcome == "CHECKER_ERROR":
        if engine_citation_ids or world_digest is not None:
            raise RuntimeError(
                f"checker-error receipt carries evidence context: {public_id}"
            )
        citations = []
        source_reference = None
        world_digest = None
        public_scope = "No evidence scope was established because fixture integrity failed before checking."
    receipt: dict[str, Any] = {
        "receipt_id": public_id,
        "engine_receipt_id": engine_receipt_id,
        "world_id": world_id,
        "world_version": raw.get("world_version"),
        "world_digest": world_digest,
        "preset_label": preset_label,
        "outcome": outcome,
        "normalized_claim": raw.get("claim") or {},
        "winning_rule": {
            "id": rule_id or "NO_RULE",
            "title": rule_title,
            "rationale": rule_rationale,
        },
        "scope": public_scope,
        "citations": citations,
        "source_reference": source_reference,
        "evidence": raw.get("evidence"),
        "reason": raw.get("reason") or raw.get("message"),
        "reason_code": raw.get("reason_code") or rule_id,
        "source_hashes": raw.get("source_hashes") or raw.get("snapshot_hashes") or {},
        "license": license_label,
        "retrieval_clock": retrieval_clock,
        "checker_version": canonical.get("checker_version"),
        "rule_version": canonical.get("rule_version"),
        "schema_version_claim": canonical.get("schema_version")
        or canonical.get("schema_version_claim"),
    }
    if outcome == "CHECKER_ERROR":
        receipt["error"] = {
            "code": raw.get("reason_code") or "CORRUPT_EVIDENCE",
            "message": receipt["reason"],
        }
        if selected_world_context_digest is not None:
            receipt["selected_world_context_digest"] = selected_world_context_digest
    if outcome != "CHECKER_ERROR" and (
        not isinstance(receipt["world_digest"], str)
        or len(receipt["world_digest"]) != 64
    ):
        raise RuntimeError(f"adapter receipt has no valid world digest: {public_id}")
    receipt["canonical_digest"] = _digest(receipt)
    return receipt


def _clinical_receipts() -> tuple[list[dict[str, Any]], str]:
    fixture_path = FIXTURES / "clinical_trials/fixture.json"
    fixture = _load(fixture_path)
    adapter = ClinicalTrialsAdapter(
        fixture_path, checker_version=CLINICAL_CHECKER_VERSION
    )
    registry = next(
        row
        for row in fixture["records"]
        if row["source"] == "clinicaltrials-gov-api-v2"
    )
    filing = next(
        row
        for row in fixture["records"]
        if row["source"] == "sec-edgar-submissions-and-archives"
    )
    claim = {
        "nct_id": registry["nct_id"],
        "sponsor": registry["sponsor"],
        "intervention": registry["intervention"],
        "sec_accession": filing["sec_accession"],
        "cik": filing["cik"],
        "exhibit_locator": filing["exhibit_locator"],
        "asserted_span_sha256": filing["asserted_span_sha256"],
        "as_of": "2026-06-03T08:09:00Z",
    }
    citation_catalog: dict[str, dict[str, str]] = {
        registry["record_id"]: {
            "source": "ClinicalTrials.gov",
            "locator": registry["record_id"],
            "reference": f"https://clinicaltrials.gov/study/{registry['nct_id']}",
        },
        filing["record_id"]: {
            "source": "ClinicalTrials.gov + SEC EDGAR",
            "locator": filing["record_id"],
            "reference": "https://www.sec.gov/Archives/edgar/data/1829635/000110465926069810/tm2616719d1_ex99-1.htm",
        },
    }
    common: _ReceiptCommon = {
        "scope": "The filing's trial identity is consistent with the timestamped registry record; this is not an efficacy, safety, investment, or corporate-truth claim.",
        "citation_catalog": citation_catalog,
        "source_reference": None,
        "license_label": "ClinicalTrials.gov terms (processed 2026-09-01) + SEC EDGAR public filing",
        "retrieval_clock": "2026-09-01T22:37:00Z",
    }
    results = [
        _public_receipt(
            adapter.check(claim),
            public_id="trial-positive",
            preset_label="Accepted · identity consistent",
            rule_title="Disclosure identity is consistent",
            rule_rationale="The exact NCT ID, sponsor, intervention, accession, exhibit locator, hashed span, and source clocks align.",
            **common,
        ),
        _public_receipt(
            adapter.check({**claim, "sponsor": "Different Sponsor"}),
            public_id="trial-rejected",
            preset_label="Rejected · sponsor conflicts",
            rule_title="Sponsor identity conflicts",
            rule_rationale="The declared sponsor does not match both timestamped source records.",
            **common,
        ),
        _public_receipt(
            adapter.check({**claim, "sec_accession": "0001104659-26-069899"}),
            public_id="trial-inconclusive",
            preset_label="Inconclusive · accession absent",
            rule_title="Evidence is not answerable",
            rule_rationale="The exact NCT and SEC accession cannot both be resolved in the frozen fixture.",
            **common,
        ),
    ]
    admitted_world_digest = results[0]["world_digest"]
    with tempfile.TemporaryDirectory(prefix="bcf-public-corrupt-") as temp:
        corrupt = Path(temp) / "fixture.json"
        changed = json.loads(json.dumps(fixture))
        changed["records"][0]["sponsor"] = "tampered"
        corrupt.write_text(json.dumps(changed), encoding="utf-8")
        results.append(
            _public_receipt(
                check_clinical_trials_claim(
                    claim, corrupt, checker_version=CLINICAL_CHECKER_VERSION
                ),
                public_id="trial-error",
                preset_label="Checker error · integrity stopped",
                rule_title="Evidence integrity gate stopped checking",
                rule_rationale="A changed compact fixture fails closed before claim evaluation.",
                selected_world_context_digest=admitted_world_digest,
                **common,
            )
        )
    return results, results[0]["world_digest"]


def _open_targets_receipts() -> tuple[list[dict[str, Any]], str]:
    fixture_path = FIXTURES / "open_targets/release-26.06.json"
    fixture = _load(fixture_path)
    row = fixture["records"][0]
    adapter = OpenTargetsAdapter(fixture_path, checker_version=TARGETS_CHECKER_VERSION)
    claim = {
        key: row[key]
        for key in ("target_id", "disease_id", "evidence_source", "release")
    }
    record_id = row["record_id"]
    citation_catalog: dict[str, dict[str, str]] = {
        record_id: {
            "source": "Open Targets 26.06",
            "locator": record_id,
            "reference": "https://platform.opentargets.org/target/ENSG00000141510/associations/MONDO_0018875",
        }
    }
    common: _ReceiptCommon = {
        "scope": "A source-specific association in Open Targets 26.06; not causality, clinical efficacy, or a treatment recommendation.",
        "citation_catalog": citation_catalog,
        "source_reference": None,
        "license_label": "Open Targets Platform data · CC0 1.0",
        "retrieval_clock": fixture["provenance"]["retrieved_at"],
    }
    results = [
        _public_receipt(
            adapter.check(claim),
            public_id="targets-positive",
            preset_label="Accepted · association present",
            rule_title="Release-bound association is present",
            rule_rationale="The exact target, disease, datasource, and release resolve to the cited compact record.",
            **common,
        ),
        _public_receipt(
            adapter.check({**claim, "confidence_language": "causal efficacy"}),
            public_id="targets-rejected",
            preset_label="Rejected · causal overclaim",
            rule_title="Claim exceeds association semantics",
            rule_rationale="The selected release records an association, not causal efficacy.",
            **common,
        ),
    ]
    return results, results[0]["world_digest"]


def _arc_receipts() -> tuple[list[dict[str, Any]], str]:
    fixture_path = FIXTURES / "arc_vcc"
    metadata = _load(fixture_path / "metadata.json")
    adapter = ArcVCCAdapter.from_path(fixture_path, checker_version=ARC_CHECKER_VERSION)
    claim = {
        "perturbed_gene": "STAT1",
        "response_gene": "TAGLN",
        "summary_statistic": metadata["statistic"],
        "direction": "increases",
        "threshold": metadata["threshold"],
        "assay": "H1",
        "split": "locked_holdout",
    }
    common: _ReceiptCommon = {
        "scope": "A mean raw-count log2 fold-change direction in the real H1 subset; not a STATE prediction, mechanism, or universal biological law.",
        "citation_catalog": {},
        "source_reference": {
            "label": "Source reference (the Arc adapter does not issue citation IDs)",
            "source": "Arc Institute cell-eval2",
            "locator": "real H1 subset · STAT1 → TAGLN · 100 perturbed / 100 controls",
            "reference": metadata["official_url"],
        },
        "license_label": "ArcInstitute/cell-eval2 · MIT",
        "retrieval_clock": metadata["retrieval_at"],
    }
    results = [
        _public_receipt(
            adapter.check(claim),
            public_id="arc-positive",
            preset_label="Accepted · direction matches",
            rule_title="Declared H1 direction matches",
            rule_rationale="The locked-holdout real measurement supports the asserted direction at the preregistered threshold.",
            **common,
        ),
        _public_receipt(
            adapter.check({**claim, "direction": "decreases"}),
            public_id="arc-rejected",
            preset_label="Rejected · direction conflicts",
            rule_title="Declared H1 direction conflicts",
            rule_rationale="The locked-holdout real measurement reports the opposite direction.",
            **common,
        ),
    ]
    return results, results[0]["world_digest"]


def build() -> tuple[dict[str, Any], dict[str, Any]]:
    _require_readiness()
    clinical, clinical_digest = _clinical_receipts()
    targets, targets_digest = _open_targets_receipts()
    arc, arc_digest = _arc_receipts()
    receipts = clinical + targets + arc
    worlds = {
        "schema_version": "world-catalog-v1",
        "generated_from": GENERATED_FROM,
        "worlds": [
            {
                "id": "clinical-trials-sec",
                "presentation_id": "clinical_trials_sec",
                "title": "Clinical Trials / SEC",
                "short_title": "Trial disclosure integrity",
                "modality": "translational / commercial",
                "state": "ADMITTED",
                "version": "2025-09-01_2026-09-01",
                "world_digest": clinical_digest,
                "version_label": "2025–2026 filing window",
                "description": "Checks a separately reviewed filing-to-registry trial identity against exact timestamps and locators.",
                "capability": "NCT, sponsor, intervention, CIK/accession, exhibit, hashed span, and source clock consistency.",
                "scope": "Identity consistency only—not efficacy, safety, investment advice, or corporate truth.",
                "source_contract": "ClinicalTrials.gov API v2 + SEC EDGAR EX-99.1",
                "source_clock": "processed 2026-09-01",
                "receipt_ids": [item["receipt_id"] for item in clinical],
                "default_receipt": "trial-positive",
            },
            {
                "id": "open-targets",
                "presentation_id": "open_targets",
                "title": "Open Targets",
                "short_title": "Target–disease evidence",
                "modality": "translational",
                "state": "ADMITTED",
                "version": "26.06",
                "world_digest": targets_digest,
                "version_label": "release 26.06",
                "description": "Checks an exact source-specific target–disease association against the bounded 26.06 response.",
                "capability": "Target identity, disease identity, datasource, release, and source-defined association score.",
                "scope": "Association only—not causality, efficacy, or treatment guidance.",
                "source_contract": "Open Targets GraphQL 26.06 · CC0",
                "source_clock": "retrieved 2026-09-01",
                "receipt_ids": [item["receipt_id"] for item in targets],
                "default_receipt": "targets-positive",
            },
            {
                "id": "arc-vcc",
                "presentation_id": "arc_vcc",
                "title": "Arc VCC",
                "short_title": "Perturbational expression",
                "modality": "perturbational",
                "state": "ADMITTED",
                "version": "2025-h1-measurements",
                "world_digest": arc_digest,
                "version_label": "real H1 subset",
                "description": "Checks a preregistered gene-response direction in Arc's committed real 600-cell H1 sample.",
                "capability": "Perturbation, response gene, assay, split, statistic, threshold, and direction.",
                "scope": "Real measurements only—not STATE predictions, mechanisms, or general biological laws.",
                "source_contract": "ArcInstitute/cell-eval2 real H1 subset · MIT",
                "source_clock": "retrieved 2026-09-01",
                "receipt_ids": [item["receipt_id"] for item in arc],
                "default_receipt": "arc-positive",
            },
            {
                "id": "neurovault",
                "title": "NeuroVault",
                "short_title": "fMRI map claims",
                "modality": "neuroimaging",
                "state": "RESEARCHED_DEFERRED",
                "version": None,
                "version_label": None,
                "description": None,
                "capability": None,
                "scope": None,
                "source_contract": None,
                "source_clock": None,
                "gate_reason": "Coordinate-space and spatial preprocessing controls remain unresolved; no evidence receipt is published.",
                "receipt_ids": [],
                "default_receipt": None,
            },
            {
                "id": "flywire_connectome",
                "title": "FlyWire / Codex",
                "short_title": "Connectome links",
                "modality": "connectomics",
                "state": "RESEARCHED_DEFERRED",
                "version": None,
                "version_label": None,
                "description": None,
                "capability": None,
                "scope": None,
                "source_contract": None,
                "source_clock": None,
                "gate_reason": "Internal-use and public-display terms remain unresolved; no evidence-derived field is published.",
                "receipt_ids": [],
                "default_receipt": None,
            },
        ],
    }
    return worlds, {
        "schema_version": "receipt-v2",
        "generated_from": GENERATED_FROM,
        "receipts": receipts,
    }


def _serialized(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="fail if tracked exports differ"
    )
    args = parser.parse_args()
    worlds, receipts = build()
    outputs = {
        SITE_ROOT / "worlds.json": _serialized(worlds),
        SITE_ROOT / "receipts.json": _serialized(receipts),
    }
    if args.check:
        changed = [
            str(path)
            for path, content in outputs.items()
            if not path.is_file() or path.read_text(encoding="utf-8") != content
        ]
        if changed:
            raise SystemExit("public receipt export is stale: " + ", ".join(changed))
        return 0
    for path, content in outputs.items():
        path.write_text(content, encoding="utf-8")
    print(
        json.dumps(
            {
                "receipt_count": len(receipts["receipts"]),
                "world_count": len(worlds["worlds"]),
                "source": GENERATED_FROM,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
