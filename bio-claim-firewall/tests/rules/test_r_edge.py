"""§2 Evidence licensing -- R-EDGE-01, R-EDGE-02 (sections/edges.py)."""

from __future__ import annotations


def test_unsupported_edge_invalid_fixture_rejects(run_claim, expectations):
    entry = next(e for e in expectations if e["claim_path"].endswith("UNSUPPORTED_EDGE__invalid.json"))
    result = run_claim("UNSUPPORTED_EDGE__invalid.json")

    assert result.verdict == "REJECTED"
    assert result.fault_code == "UNSUPPORTED_EDGE"
    assert result.reasons[0].rule_id.startswith(entry["expected_rule_id_prefix"])
    assert result.reasons[0].rule_id == "R-EDGE-01"


def test_unsupported_edge_valid_fixture_accepts(run_claim, expectations):
    entry = next(e for e in expectations if e["claim_path"].endswith("UNSUPPORTED_EDGE__valid.json"))
    result = run_claim("UNSUPPORTED_EDGE__valid.json")

    assert result.verdict == "ACCEPTED"
    for substring in entry["expected_conditions_contain"]:
        assert any(substring in condition for condition in result.conditions)


def test_r_edge_02_fires_on_pair_mismatch(bundle):
    """R-EDGE-02: right record_type, wrong (subject, object) pair."""
    from normalize import CanonicalClaim

    from rules import RuleEngine

    canonical = CanonicalClaim(
        schema_version="0.1.0",
        claim_id="55555555-5555-5555-5555-555555555555",
        subject_id="HGNC:11998",  # TP53 -- R1 is BRCA1 -> KRAS, wrong pair entirely
        subject_label="TP53",
        relation="increases",
        object_id="HGNC:6407",
        object_label="KRAS",
        polarity="positive",
        species="NCBITaxon:9606",
        cell_type="CL:0000988",
        cell_type_ancestors=("CL:0000000",),
        cell_line="CLO:0009454",
        state="resting",
        assay="CRISPRi_screen",
        perturbation="CRISPRi:HGNC:1097",
        evidence_ids=("perturbseq_v_test:fc1d7ea4dd7c21a7",),  # R1: BRCA1 -> KRAS
        confidence_language="supported",
        requested_status="hypothesis",
    )
    result = RuleEngine(bundle, checker_version="0.1.0").run(canonical)

    assert result.verdict == "REJECTED"
    assert result.fault_code == "UNSUPPORTED_EDGE"
    assert result.reasons[0].rule_id == "R-EDGE-02"
