"""§8 Certainty ladder -- R-CERT-01, R-CERT-02 (sections/certainty.py)."""

from __future__ import annotations


def test_unsupported_certainty_invalid_fixture_rejects(run_claim, expectations):
    entry = next(e for e in expectations if e["claim_path"].endswith("UNSUPPORTED_CERTAINTY__invalid.json"))
    result = run_claim("UNSUPPORTED_CERTAINTY__invalid.json")

    assert result.verdict == "REJECTED"
    assert result.fault_code == "UNSUPPORTED_CERTAINTY"
    assert result.reasons[0].rule_id.startswith(entry["expected_rule_id_prefix"])
    assert result.reasons[0].rule_id == "R-CERT-01"


def test_unsupported_certainty_valid_fixture_accepts(run_claim, expectations):
    entry = next(e for e in expectations if e["claim_path"].endswith("UNSUPPORTED_CERTAINTY__valid.json"))
    result = run_claim("UNSUPPORTED_CERTAINTY__valid.json")

    assert result.verdict == "ACCEPTED"
    for substring in entry["expected_conditions_contain"]:
        assert any(substring in condition for condition in result.conditions)


def test_r_cert_02_fires_directly_when_reached_in_isolation():
    # RULES-DECISION: R-CERT-02 is textually subsumed by R-CAUS-03, which
    # sits earlier in the fixed cascade (§4, position 8, vs §8's position
    # 11) and always fires first for any claim reaching the engine with
    # confidence_language=causal and no interventional citation --
    # spec/inference_rules.md §8 says as much explicitly ("verdict picks
    # R-CAUS-03 as more specific"). So R-CERT-02 is unreachable through
    # `RuleEngine.run()` by design; we unit-test `certainty.check_all`
    # directly (in isolation from R-CAUS-03) to exercise it.
    from normalize import CanonicalClaim, CanonicalEvidence

    from rules.cited import CitedRecord
    from rules.sections import certainty

    claim = CanonicalClaim(
        schema_version="0.1.0",
        claim_id="eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee",
        subject_id="HGNC:11998",
        subject_label="TP53",
        relation="increases",
        object_id="HGNC:11892",
        object_label="CDKN1A",
        polarity="positive",
        species="NCBITaxon:9606",
        cell_type="CL:0000988",
        cell_type_ancestors=(),
        cell_line="CLO:0009454",
        state="IFNG_stimulated",
        assay="bulk-RNA-seq",
        perturbation=None,
        evidence_ids=("perturbseq_v_test:dea2437bf1fa58bd",),
        confidence_language="causal",
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
        effect=None,
        contradicts=(),
        retrieved_at="2026-01-15T00:00:00Z",
        license="CC0-1.0",
        source_citation=None,
    )
    cited = (CitedRecord(evidence_id=evidence.evidence_id, raw={"source": "perturbseq_v_test"}, canonical=evidence),)

    class _FakeBundle:
        def ancestors(self, curie):
            return ()

    reasons = certainty.check_all(claim, cited, _FakeBundle())
    assert len(reasons) == 1
    assert reasons[0].rule_id == "R-CERT-02"
