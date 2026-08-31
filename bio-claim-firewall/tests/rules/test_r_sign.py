"""§3 Sign matching -- R-SIGN-01, R-SIGN-02 (sections/signs.py)."""

from __future__ import annotations

from normalize import CanonicalClaim

from rules import RuleEngine


def test_sign_mismatch_invalid_fixture_rejects(run_claim, expectations):
    entry = next(e for e in expectations if e["claim_path"].endswith("SIGN_MISMATCH__invalid.json"))
    result = run_claim("SIGN_MISMATCH__invalid.json")

    assert result.verdict == "REJECTED"
    assert result.fault_code == "SIGN_MISMATCH"
    assert result.reasons[0].rule_id.startswith(entry["expected_rule_id_prefix"])
    assert result.reasons[0].rule_id == "R-SIGN-01"


def test_sign_mismatch_valid_fixture_accepts(run_claim, expectations):
    entry = next(e for e in expectations if e["claim_path"].endswith("SIGN_MISMATCH__valid.json"))
    result = run_claim("SIGN_MISMATCH__valid.json")

    assert result.verdict == "ACCEPTED"
    for substring in entry["expected_conditions_contain"]:
        assert any(substring in condition for condition in result.conditions)


def test_r_sign_02_fires_on_opposite_nonzero_correlation(bundle):
    """R-SIGN-02: correlates_with polarity=positive requires magnitude > 0."""
    canonical = CanonicalClaim(
        schema_version="0.1.0",
        claim_id="77777777-7777-7777-7777-777777777777",
        subject_id="HGNC:11998",
        subject_label="TP53",
        relation="correlates_with",
        object_id="HGNC:11892",
        object_label="CDKN1A",
        polarity="negative",  # R3's magnitude is 0.0 (positive sign, zero magnitude)
        species="NCBITaxon:9606",
        cell_type="CL:0000988",
        cell_type_ancestors=("CL:0000000",),
        cell_line="CLO:0009454",
        state="IFNG_stimulated",
        assay="bulk-RNA-seq",
        perturbation=None,
        evidence_ids=("perturbseq_v_test:dea2437bf1fa58bd",),  # R3
        confidence_language="observed",
        requested_status="hypothesis",
    )
    result = RuleEngine(bundle, checker_version="0.1.0").run(canonical)

    # R3's magnitude is exactly 0.0 -- R-SIGN-02's own carve-out makes this
    # INCONCLUSIVE, not SIGN_MISMATCH, regardless of requested polarity.
    assert result.verdict == "INCONCLUSIVE"
    assert result.reasons == ()


def test_r_sign_02_fires_on_nonzero_opposite_sign_correlation(bundle):
    # RULES-DECISION: no fixture record has a nonzero, wrong-signed
    # magnitude for correlates_with (R3 -- the only expression_observation
    # record -- has magnitude=0.0, which is R-SIGN-02's INCONCLUSIVE
    # carve-out, not its fires-a-Reason branch). We build a synthetic
    # CitedRecord directly to exercise sections/signs.py's R-SIGN-02
    # firing branch, which the full engine cannot reach with only the
    # frozen fixture ledger.
    from normalize import CanonicalEffect, CanonicalEvidence

    from rules.cited import CitedRecord
    from rules.sections import signs

    claim = CanonicalClaim(
        schema_version="0.1.0",
        claim_id="88888888-8888-8888-8888-888888888888",
        subject_id="HGNC:11998",
        subject_label="TP53",
        relation="correlates_with",
        object_id="HGNC:11892",
        object_label="CDKN1A",
        polarity="positive",
        species="NCBITaxon:9606",
        cell_type="CL:0000988",
        cell_type_ancestors=("CL:0000000",),
        cell_line="CLO:0009454",
        state="IFNG_stimulated",
        assay="bulk-RNA-seq",
        perturbation=None,
        evidence_ids=("perturbseq_v_test:dea2437bf1fa58bd",),
        confidence_language="observed",
        requested_status="hypothesis",
    )
    evidence = CanonicalEvidence(
        schema_version="0.1.0",
        evidence_id="perturbseq_v_test:dea2437bf1fa58bd",
        source="perturbseq_v_test",
        snapshot_hash="0" * 64,
        record_type="expression_observation",
        subject_id="HGNC:11998",
        subject_label="TP53",
        object_id="HGNC:11892",
        object_label="CDKN1A",
        species="NCBITaxon:9606",
        cell_type="CL:0000988",
        cell_line="CLO:0009454",
        state="IFNG_stimulated",
        assay="bulk-RNA-seq",
        perturbation=None,
        observation_type="observational",
        effect=CanonicalEffect(sign="negative", magnitude=-0.4, significance=0.02, magnitude_scale="pearson_r"),
        contradicts=(),
        retrieved_at="2026-01-15T00:00:00Z",
        license="CC0-1.0",
        source_citation=None,
    )
    cited = (CitedRecord(evidence_id=evidence.evidence_id, raw={"source": "perturbseq_v_test"}, canonical=evidence),)

    reason, inconclusive = signs.check(claim, cited, bundle)
    assert inconclusive is False
    assert reason is not None
    assert reason.rule_id == "R-SIGN-02"
