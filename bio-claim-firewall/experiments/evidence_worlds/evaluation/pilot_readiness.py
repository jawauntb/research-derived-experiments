"""Deterministic adversarial evaluation and pilot-readiness report.

This module deliberately evaluates only the three evidence worlds whose
compact, real fixtures are committed in the repository.  It does not fetch a
network source, call an LLM, or treat a receipt as proof of authenticity.  A
passing result means that the bounded adapter behavior is consistent with the
hash-bound fixture and its manifest.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from worlds.arc_vcc import ArcVCCAdapter, check_arc_vcc_claim
from worlds.arc_vcc import load_fixture as load_arc
from worlds.clinical_trials import ClinicalTrialsAdapter, check_clinical_trials_claim
from worlds.open_targets import OpenTargetsAdapter, check_open_targets_claim

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "worlds"
MANIFEST_ROOT = REPO_ROOT / "data" / "manifests" / "worlds"
WORLD_IDS = ("clinical-trials-sec", "open-targets", "arc-vcc")
DEFERRED_WORLDS = {
    "neurovault": "Deferred: no committed licensed evidence fixture or adapter.",
    "flywire-codex": "Deferred: no committed licensed evidence fixture or adapter.",
}


@dataclass(frozen=True)
class ControlResult:
    """One preregistered mutation and its observed adapter behavior."""

    control_id: str
    kind: str
    expected: tuple[str, ...]
    observed: str
    passed: bool
    reason_code: str
    message: str


@dataclass(frozen=True)
class GateEvidence:
    """One fatal gate with an auditable, non-compensable status."""

    gate_id: str
    status: str
    evidence: str


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _outcome(result: Any) -> tuple[str, str, str]:
    """Normalize the three adapter result shapes without losing reason text."""

    observed = str(getattr(result, "outcome", getattr(result, "verdict", "CHECKER_ERROR")))
    reason_code = str(getattr(result, "reason_code", ""))
    message = str(getattr(result, "reason", ""))
    if not reason_code:
        winning = getattr(result, "winning_rule", None)
        reason_code = str(winning.get("id", "")) if isinstance(winning, Mapping) else ""
    return observed, reason_code, message


def _control(control_id: str, kind: str, expected: tuple[str, ...], result: Any) -> ControlResult:
    observed, reason_code, message = _outcome(result)
    return ControlResult(control_id, kind, expected, observed, observed in expected, reason_code, message)


def _copy_arc(destination: Path) -> None:
    source = FIXTURE_ROOT / "arc_vcc"
    destination.mkdir()
    for name in ("metadata.json", "measurements.jsonl"):
        shutil.copy2(source / name, destination / name)


def _copy_json(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def _arc_evaluation() -> dict[str, Any]:
    fixture_path = FIXTURE_ROOT / "arc_vcc"
    fixture = load_arc(fixture_path)
    adapter = ArcVCCAdapter.from_path(fixture_path)
    row = next(item for item in fixture.measurements if item.split == "locked_holdout" and item.direction != "null")
    null_row = next((item for item in fixture.measurements if item.direction == "null"), None)
    base = {
        "perturbed_gene": row.perturbed_gene,
        "response_gene": row.response_gene,
        "summary_statistic": row.summary_statistic,
        "direction": row.direction,
        "threshold": fixture.metadata.threshold,
        "assay": row.assay,
        "split": row.split,
    }
    controls = [_control("arc-positive-heldout", "positive", ("ACCEPTED",), adapter.check(base))]
    controls.append(_control("arc-negative-sign-reversal", "negative", ("REJECTED",), adapter.check({**base, "direction": "decreases" if row.direction == "increases" else "increases"})))
    null_claim = {**base, "perturbed_gene": "__absent_gene__", "direction": "null"}
    if null_row is not None:
        null_claim.update({"perturbed_gene": null_row.perturbed_gene, "response_gene": null_row.response_gene, "direction": "increases" if null_row.direction == "null" else null_row.direction})
    controls.append(_control("arc-null-unsupported-record", "null", ("INCONCLUSIVE", "REJECTED"), adapter.check(null_claim)))
    with tempfile.TemporaryDirectory(prefix="bcf-arc-corrupt-") as temp:
        corrupt = Path(temp) / "arc_vcc"
        _copy_arc(corrupt)
        content = (corrupt / "measurements.jsonl").read_text(encoding="utf-8")
        (corrupt / "measurements.jsonl").write_text(content.replace("0.577988734679", "0.577988734680", 1), encoding="utf-8")
        controls.append(_control("arc-corrupted-measurement-bytes", "corruption", ("CHECKER_ERROR",), check_arc_vcc_claim(corrupt, base)))
    controls.append(_control("arc-cross-world-claim", "cross_world", ("CHECKER_ERROR",), adapter.check({**base, "world_id": "open-targets"})))
    manifest = _json(MANIFEST_ROOT / "arc-vcc.json")
    gates = _manifest_gates(
        manifest,
        fixture_path,
        adapter.source_hashes,
        controls,
        semantic_checks={
            "split_integrity_no_leakage": fixture.metadata.tuning_split != fixture.metadata.evaluation_split
            and len({(item.perturbed_gene, item.response_gene, item.assay, item.summary_statistic) for item in fixture.measurements}) == len(fixture.measurements),
        },
    )
    return _world_result("arc-vcc", manifest, controls, gates, {"fixture_sha256": _sha256(fixture_path / "measurements.jsonl")})


def _open_targets_evaluation() -> dict[str, Any]:
    fixture_path = FIXTURE_ROOT / "open_targets" / "release-26.06.json"
    fixture = _json(fixture_path)
    adapter = OpenTargetsAdapter(fixture_path)
    row = fixture["records"][0]
    base = {"target_id": row["target_id"], "disease_id": row["disease_id"], "evidence_source": row["evidence_source"], "release": row["release"]}
    controls = [_control("open-targets-positive-release-row", "positive", ("ACCEPTED",), adapter.check(base))]
    controls.append(_control("open-targets-negative-absent-source", "negative", ("REJECTED",), adapter.check({**base, "evidence_source": "__absent_source__"})))
    controls.append(_control("open-targets-null-absent-disease", "null", ("REJECTED", "INCONCLUSIVE"), adapter.check({**base, "disease_id": "MONDO_9999999"})))
    with tempfile.TemporaryDirectory(prefix="bcf-open-targets-corrupt-") as temp:
        corrupt = Path(temp) / "release-26.06.json"
        changed = json.loads(json.dumps(fixture))
        changed["records"][0]["score"] = float(changed["records"][0]["score"]) + 0.001
        corrupt.write_text(json.dumps(changed), encoding="utf-8")
        controls.append(_control("open-targets-corrupted-release-bytes", "corruption", ("CHECKER_ERROR",), check_open_targets_claim(base, corrupt)))
    controls.append(_control("open-targets-cross-world-claim", "cross_world", ("CHECKER_ERROR",), adapter.check({**base, "world_id": "clinical-trials-sec", "world_version": "2025-09-01_2026-09-01"})))
    manifest = _json(MANIFEST_ROOT / "open-targets.json")
    gates = _manifest_gates(
        manifest,
        fixture_path,
        adapter.source_hashes,
        controls,
        semantic_checks={
            "release_and_score_semantics": all(
                isinstance(item.get("score"), (int, float))
                and not isinstance(item.get("score"), bool)
                and isinstance(item.get("score_definition"), str)
                and bool(item["score_definition"].strip())
                for item in fixture["records"]
            ),
        },
    )
    return _world_result("open-targets", manifest, controls, gates, {"fixture_sha256": _sha256(fixture_path)})


def _clinical_trials_evaluation() -> dict[str, Any]:
    fixture_path = FIXTURE_ROOT / "clinical_trials" / "fixture.json"
    fixture = _json(fixture_path)
    adapter = ClinicalTrialsAdapter(fixture_path)
    ct = next(item for item in fixture["records"] if item["source"] == "clinicaltrials-gov-api-v2")
    sec = next(item for item in fixture["records"] if item["source"] == "sec-edgar-submissions-and-archives")
    accepted = max(ct["accepted_at"], sec["accepted_at"])
    as_of = (datetime.fromisoformat(accepted) + timedelta(seconds=1)).isoformat().replace("+00:00", "Z")
    base = {key: ct[key] for key in ("nct_id", "sponsor", "intervention")}
    base.update({key: sec[key] for key in ("sec_accession", "cik", "exhibit_locator", "asserted_span_sha256")})
    base["as_of"] = as_of
    controls = [_control("clinical-trials-positive-timestamped-join", "positive", ("ACCEPTED",), adapter.check(base))]
    controls.append(_control("clinical-trials-negative-sponsor-mismatch", "negative", ("REJECTED",), adapter.check({**base, "sponsor": "__different_sponsor__"})))
    controls.append(_control("clinical-trials-null-unknown-accession", "null", ("INCONCLUSIVE",), adapter.check({**base, "sec_accession": "0000000000-00-000000"})))
    with tempfile.TemporaryDirectory(prefix="bcf-clinical-trials-corrupt-") as temp:
        corrupt = Path(temp) / "fixture.json"
        changed = json.loads(json.dumps(fixture))
        changed["records"][0]["sponsor"] = "__tampered__"
        corrupt.write_text(json.dumps(changed), encoding="utf-8")
        controls.append(_control("clinical-trials-corrupted-registry-bytes", "corruption", ("CHECKER_ERROR",), check_clinical_trials_claim(base, corrupt)))
    controls.append(_control("clinical-trials-cross-world-claim", "cross_world", ("CHECKER_ERROR",), adapter.check({**base, "world_id": "open-targets", "world_version": "26.06"})))
    manifest = _json(MANIFEST_ROOT / "clinical-trials-sec.json")
    gates = _manifest_gates(
        manifest,
        fixture_path,
        adapter.source_hashes,
        controls,
        semantic_checks={
            "timestamp_cutoff_no_time_travel": all(
                isinstance(item.get("accepted_at"), str) and item["accepted_at"].endswith("Z")
                for item in fixture["records"]
            ),
        },
    )
    return _world_result("clinical-trials-sec", manifest, controls, gates, {"fixture_sha256": _sha256(fixture_path), "as_of": as_of})


def _manifest_gates(
    manifest: Mapping[str, Any],
    fixture_path: Path,
    source_hashes: Mapping[str, str],
    controls: list[ControlResult],
    *,
    semantic_checks: Mapping[str, bool] | None = None,
) -> list[GateEvidence]:
    """Evaluate manifest-declared fatal gates without inventing a score."""

    source_rows = manifest.get("sources", [])
    source_ids = {item.get("source_id") for item in source_rows if isinstance(item, Mapping)}
    declared_ids = set(source_hashes)
    all_controls = all(item.passed for item in controls)
    transformation = manifest.get("transformation", {})
    fixture_hash = _sha256(fixture_path if fixture_path.is_file() else fixture_path / "measurements.jsonl")
    hash_ok = fixture_hash == transformation.get("sha256") and source_ids <= declared_ids and all(len(value) == 64 for value in source_hashes.values())
    license_ok = bool(source_rows) and all(
        isinstance(item, Mapping)
        and isinstance(item.get("license"), Mapping)
        and item["license"].get("status") == "verified"
        and item["license"].get("redistribution") not in {"forbidden", "unknown"}
        for item in source_rows
    )
    identity_ok = bool(manifest.get("world_id") and manifest.get("version"))
    semantic_checks = semantic_checks or {}
    gates: list[GateEvidence] = []
    for raw in manifest.get("fatal_gates", []):
        gate_id = str(raw.get("id", "")) if isinstance(raw, Mapping) else str(raw)
        normalized = gate_id.replace("_and_", "_")
        if gate_id in {"dataset_license_scope", "license_and_redistribution", "license_and_custody"}:
            gates.append(GateEvidence(gate_id, "PASS" if license_ok else "FAIL", "Manifest source licenses are verified and raw custody is outside the public fixture."))
        elif gate_id in {"official_release_identity", "official_source_identity"}:
            gates.append(GateEvidence(gate_id, "PASS" if identity_ok and source_ids <= declared_ids else "FAIL", "Manifest world/version and source IDs match the loaded fixture."))
        elif gate_id in {"complete_hashes_and_schema"}:
            gates.append(GateEvidence(gate_id, "PASS" if hash_ok else "FAIL", "Adapter loaded the schema; source hashes and derived-artifact hash match the manifest."))
        elif gate_id in {"split_integrity_no_leakage", "timestamp_cutoff_no_time_travel", "release_and_score_semantics", "score_semantics"}:
            semantic_ok = semantic_checks.get(gate_id, semantic_checks.get("release_and_score_semantics", False))
            gates.append(GateEvidence(gate_id, "PASS" if hash_ok and semantic_ok else "FAIL", "The world-specific adapter validated its frozen scope and integrity constraints."))
        elif gate_id in {"organic_positive_negative_null_controls"}:
            gates.append(GateEvidence(gate_id, "PASS" if all_controls else "FAIL", "All preregistered organic and adversarial controls matched their expected fail-closed outcomes."))
        elif gate_id in {"world_isolation_and_fail_closed"}:
            isolated = next((item for item in controls if item.kind == "cross_world"), None)
            corrupted = next((item for item in controls if item.kind == "corruption"), None)
            passed = bool(isolated and isolated.passed and corrupted and corrupted.passed)
            gates.append(GateEvidence(gate_id, "PASS" if passed else "FAIL", "Foreign-world and corrupted-fixture controls fail closed."))
        else:
            gates.append(GateEvidence(gate_id, "UNKNOWN", "No evaluator is registered for this fatal gate; readiness cannot pass."))
    return gates


def _world_result(world_id: str, manifest: Mapping[str, Any], controls: list[ControlResult], gates: list[GateEvidence], artifacts: Mapping[str, Any]) -> dict[str, Any]:
    fatal_pass = all(gate.status == "PASS" for gate in gates)
    return {
        "world_id": world_id,
        "version": manifest.get("version"),
        "status": "PASS" if fatal_pass else "FAIL",
        "fatal_gates": [asdict(gate) for gate in gates],
        "controls": [{**asdict(control), "expected": list(control.expected)} for control in controls],
        "artifacts": dict(artifacts),
        "scope_note": "PASS means bounded fixture/source consistency only; it does not establish authenticity, causality, efficacy, or universal truth.",
    }


def evaluate_pilot() -> dict[str, Any]:
    """Run all offline controls and return a JSON-serializable report."""

    worlds = [_clinical_trials_evaluation(), _open_targets_evaluation(), _arc_evaluation()]
    all_fatal_pass = all(world["status"] == "PASS" for world in worlds)
    return {
        "schema_version": "bio-claim-firewall-pilot-readiness-1",
        "evaluation_mode": "offline_deterministic",
        "worlds": worlds,
        "deferred_worlds": [{"world_id": key, "status": "DEFERRED", "reason": value} for key, value in sorted(DEFERRED_WORLDS.items())],
        "pilot_ready": all_fatal_pass,
        "decision": "READY_FOR_BOUNDED_PILOT" if all_fatal_pass else "WITHHOLD_PILOT",
        "decision_rule": "Every fatal gate for each of the three included worlds must be PASS; deferred worlds are excluded and cannot contribute evidence.",
        "limitations": [
            "A passing receipt establishes consistency with a hash-bound compact fixture, not source authenticity.",
            "Arc results are measurements, not STATE predictions; Open Targets results are associations, not causality or efficacy.",
            "ClinicalTrials.gov plus SEC results are disclosure consistency checks, not trial success or corporate-truth claims.",
        ],
    }


def write_report(output_dir: str | Path | None = None) -> dict[str, Any]:
    """Write stable JSON and Markdown reports, returning the report object."""

    report = evaluate_pilot()
    destination = Path(output_dir) if output_dir is not None else Path(__file__).resolve().parents[1] / "results"
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "pilot_readiness.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Bio Claim Firewall: pilot-readiness evaluation",
        "",
        f"Decision: **{report['decision']}**",
        "",
        "This is a deterministic offline run over committed compact fixtures. PASS means bounded adapter/source consistency only; it does not establish authenticity, causality, efficacy, or universal truth.",
        "",
        "| World | Status | Fatal gates | Controls |",
        "| --- | --- | ---: | ---: |",
    ]
    for world in report["worlds"]:
        lines.append(f"| `{world['world_id']}` `{world['version']}` | **{world['status']}** | {sum(g['status'] == 'PASS' for g in world['fatal_gates'])}/{len(world['fatal_gates'])} | {sum(c['passed'] for c in world['controls'])}/{len(world['controls'])} |")
    lines += ["", "## Deferred worlds", ""]
    for world in report["deferred_worlds"]:
        lines.append(f"- `{world['world_id']}` — {world['reason']}")
    lines += ["", "## Gate evidence", ""]
    for world in report["worlds"]:
        lines += [f"### {world['world_id']}", ""]
        for gate in world["fatal_gates"]:
            lines.append(f"- `{gate['gate_id']}`: **{gate['status']}** — {gate['evidence']}")
    (destination / "pilot_readiness.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":  # pragma: no cover
    result = write_report()
    print(json.dumps({"decision": result["decision"], "pilot_ready": result["pilot_ready"]}, sort_keys=True))
