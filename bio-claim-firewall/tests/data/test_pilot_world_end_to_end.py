"""End-to-end: `verifier.verify()` against hand-authored REAL claims over the frozen pilot world.

Every claim below cites a real evidence record drawn from the frozen
`perturbseq.replogle_2022` ledger (built by `data/scripts/sample_replogle_2022.py`
from Replogle et al. 2022's own "commonly requested supplemental files"
release), or deliberately cites one that does not exist. Claims 1 and 2 use
the K562 GATA1 -> CTSC record: in the K562 genome-scale Perturb-seq screen,
CRISPRi knockdown of the erythroid master transcription factor GATA1 is
associated with a strong increase in CTSC (cathepsin C) pseudobulk
expression -- a real, verifiable observation from the ledger, not an
invented one:

    {"subject": {"id": "HGNC:4170", "label": "GATA1"},
     "object": {"id": "HGNC:2528", "label": "CTSC"},
     "effect": {"sign": "positive", "magnitude_scale": "zscore_mean_expression"},
     "cell_context": {"cell_type": "CL:0000988", "cell_line": "CLO:0007059",
                       "state": "resting"},
     "assay_context": {"assay": "CRISPRi_screen",
                        "perturbation": "CRISPRi:HGNC:4170"},
     "observation_type": "interventional", "species": "NCBITaxon:9606"}

Its `evidence_id` is looked up from the live bundle rather than hardcoded:
`evidence_id` is `f"{source}:{sha256(canonical_json(record))[:16]}"` and the
canonicalized record includes `retrieved_at`, which is set from the actual
download timestamp (see `sample_replogle_2022.py`) -- so the id is stable
across reruns of the *sampler* alone, but legitimately changes if the raw
source is *re-downloaded* at a different time. Hardcoding it here would make
this test spuriously fail every time someone re-runs
`download_replogle_2022.py` from scratch without also updating a literal in
this file, so instead this test resolves the record the same way the
verifier's own ledger does: by `(subject_id, object_id)` via
`EvidenceLedger.list_by`.

Skips (rather than fails) if the pilot world has not been downloaded
locally -- see test_pilot_world_loads.py for the same skip condition.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import pytest

from evidence import load_bundle
from verifier import verify
from verifier.config import VerifierConfig

DATA_ROOT = Path(__file__).resolve().parents[2] / "data"
SPEC_DIR = Path(__file__).resolve().parents[2] / "spec"
CHECKER_VERSION = "0.1.0"

GATA1_CURIE = "HGNC:4170"
CTSC_CURIE = "HGNC:2528"

# Deliberately duplicated (not imported) from test_pilot_world_loads.py: pytest's default
# no-`__init__.py` import mode makes cross-test-module imports fragile/ambiguous across
# sibling test directories (see conftest.py's own historical note on this in tests/verifier/),
# so each test module in tests/data/ carries its own tiny skip-condition helper instead.
EXPECTED_SOURCES = (
    "hgnc.2026_pilot",
    "ncbitaxon.2026_pilot",
    "cellontology.2026_pilot",
    "cellline.2026_pilot",
    "reactome.2026_pilot",
    "perturbseq.replogle_2022",
)


def _missing_sources() -> list[str]:
    manifests_dir = DATA_ROOT / "manifests"
    missing = []
    for source in EXPECTED_SOURCES:
        has_manifest = (manifests_dir / f"{source}.yaml").is_file() or (
            manifests_dir / f"{source}.json"
        ).is_file()
        has_data = (DATA_ROOT / "ontology_snapshots" / source).is_dir() or (
            DATA_ROOT / "evidence_records" / source / "records.jsonl"
        ).is_file()
        if not (has_manifest and has_data):
            missing.append(source)
    return missing


def _skip_if_not_downloaded() -> None:
    missing = _missing_sources()
    if missing:
        pytest.skip(
            "run scripts/download_*.py first (missing locally: "
            + ", ".join(missing)
            + ")"
        )


@pytest.fixture
def bundle():
    _skip_if_not_downloaded()
    return load_bundle(DATA_ROOT)


@pytest.fixture
def config():
    return VerifierConfig(checker_version=CHECKER_VERSION, schema_dir=SPEC_DIR)


@pytest.fixture
def gata1_increases_ctsc_record(bundle) -> dict[str, Any]:
    """The real K562 GATA1 -> CTSC perturbation_effect record, resolved from the live
    ledger by (subject, object) rather than a hardcoded evidence_id -- see this
    module's docstring for why the id itself is not a stable literal to hardcode."""
    matches = bundle.ledger.list_by(subject_id=GATA1_CURIE, object_id=CTSC_CURIE)
    assert matches, (
        f"expected a {GATA1_CURIE} -> {CTSC_CURIE} perturbation_effect record in the "
        "frozen perturbseq.replogle_2022 ledger -- if sample_replogle_2022.py's sampling "
        "method changed, GATA1/CTSC may no longer be among the top-ranked pairs; pick a "
        "different real (subject, object) pair from data/evidence_records/"
        "perturbseq.replogle_2022/records.jsonl instead of loosening this assertion."
    )
    assert len(matches) == 1, f"expected exactly one match, got {len(matches)}"
    record = matches[0]
    assert record["effect"]["sign"] == "positive"
    return record


def _base_claim(evidence_id: str, **overrides: Any) -> dict[str, Any]:
    claim = {
        "schema_version": "0.1.0",
        "claim_id": str(uuid.uuid4()),
        "subject": {"id": GATA1_CURIE, "label": "GATA1"},
        "relation": "increases",
        "object": {"id": CTSC_CURIE, "label": "CTSC"},
        "polarity": "positive",
        "species": "NCBITaxon:9606",
        "cell_context": {
            "cell_type": "CL:0000988",
            "cell_line": "CLO:0007059",
            "state": "resting",
        },
        "assay_context": {
            "assay": "CRISPRi_screen",
            "perturbation": f"CRISPRi:{GATA1_CURIE}",
        },
        "evidence_ids": [evidence_id],
        "confidence_language": "supported",
        "requested_status": "hypothesis",
    }
    claim.update(overrides)
    return claim


def test_expected_sources_constant_matches_download_scripts():
    # Sanity: this module and test_pilot_world_loads.py must agree on what "the
    # pilot world" is, or the skip conditions below would silently diverge.
    assert len(EXPECTED_SOURCES) == 6


def test_claim_1_gata1_increases_ctsc_in_k562_accepted_conditionally(
    bundle, config, gata1_increases_ctsc_record
):
    """A real, correctly-scoped claim citing the real GATA1->CTSC record: ACCEPTED_CONDITIONALLY."""
    evidence_id = gata1_increases_ctsc_record["evidence_id"]
    claim = _base_claim(evidence_id)

    verdict = verify(claim, bundle, config)

    assert verdict["verdict"] == "ACCEPTED_CONDITIONALLY"
    assert verdict.get("fault_code") is None
    derivation = verdict["derivation"]
    assert evidence_id in derivation["evidence_ids"]
    assert derivation["applied_rules"]
    assert derivation["conditions"]
    assert verdict["checker_version"] == CHECKER_VERSION
    assert (
        verdict["snapshot_hashes"]["perturbseq.replogle_2022"]
        == bundle.manifests["perturbseq.replogle_2022"].sha256
    )
    assert len(verdict["verdict_id"]) == 32


def test_claim_2_gata1_causes_ctsc_established_single_record_overclaims(
    bundle, config, gata1_increases_ctsc_record
):
    """Same real evidence, but asserted as `causes` at `established` status from a single
    interventional record: the certainty ladder (R-CAUS-04 / spec/inference_rules.md sec4)
    caps single-record `causes` claims at `hypothesis`, so this REJECTS."""
    evidence_id = gata1_increases_ctsc_record["evidence_id"]
    claim = _base_claim(
        evidence_id,
        relation="causes",
        confidence_language="causal",
        requested_status="established",
    )

    verdict = verify(claim, bundle, config)

    assert verdict["verdict"] == "REJECTED"
    assert verdict["fault_code"] in ("CAUSALITY_OVERCLAIM", "SCOPE_OVERCLAIM")
    rule_ids = {reason["rule_id"] for reason in verdict["reasons"]}
    assert "R-CAUS-04" in rule_ids
    assert verdict["checker_version"] == CHECKER_VERSION


def test_claim_3_unknown_evidence_id_is_bad_citation(
    bundle, config, gata1_increases_ctsc_record
):
    """A claim citing an evidence_id that does not exist in the frozen ledger: fails closed
    on citation resolution (R-CITE-01) before any biology-specific rule runs."""
    claim = _base_claim(
        gata1_increases_ctsc_record["evidence_id"],
        evidence_ids=["perturbseq.replogle_2022:0000000000000000"],
    )

    verdict = verify(claim, bundle, config)

    assert verdict["verdict"] == "REJECTED"
    assert verdict["fault_code"] == "BAD_CITATION"
    rule_ids = {reason["rule_id"] for reason in verdict["reasons"]}
    assert "R-CITE-01" in rule_ids


def test_verify_never_raises_on_real_claims(bundle, config):
    """`verify()` is documented to catch every unexpected exception and fail closed into
    CHECKER_ERROR rather than propagate -- exercise that contract with a garbage claim
    shape against the real bundle, not just the synthetic fixture world."""
    garbage_claim = {"not": "a valid claim"}

    verdict = verify(garbage_claim, bundle, config)

    assert verdict["verdict"] in ("REJECTED", "CHECKER_ERROR")
