"""§7 Contradiction -- R-CONTRA-01, R-CONTRA-02 (sections/contradiction.py)."""

from __future__ import annotations


def test_contradicted_invalid_fixture_rejects(run_claim, expectations):
    entry = next(e for e in expectations if e["claim_path"].endswith("CONTRADICTED__invalid.json"))
    result = run_claim("CONTRADICTED__invalid.json")

    assert result.verdict == "REJECTED"
    assert result.fault_code == "CONTRADICTED"
    assert result.reasons[0].rule_id.startswith(entry["expected_rule_id_prefix"])
    assert result.reasons[0].rule_id == "R-CONTRA-02"  # R5.contradicts references R3's evidence_id


def test_contradicted_valid_fixture_accepts(run_claim, expectations):
    entry = next(e for e in expectations if e["claim_path"].endswith("CONTRADICTED__valid.json"))
    result = run_claim("CONTRADICTED__valid.json")

    assert result.verdict == "ACCEPTED"
    for substring in entry["expected_conditions_contain"]:
        assert any(substring in condition for condition in result.conditions)


def test_r_contra_01_fires_on_outranking_opposite_sign_same_context():
    # RULES-DECISION: no pair in the frozen synthetic world exercises
    # R-CONTRA-01 without an explicit `contradicts` back-reference (every
    # opposite-sign, same-context pair the fixture pack ships -- R3/R5 --
    # also carries a `contradicts` link, so R-CONTRA-02 always fires
    # first there). We unit-test `sections/contradiction.py`'s R-CONTRA-01
    # branch directly against a minimal fake ledger instead.
    from normalize import CanonicalEffect, CanonicalEvidence

    from rules.cited import CitedRecord
    from rules.sections import contradiction

    cited_raw = {
        "evidence_id": "src:aaaaaaaaaaaaaaaa",
        "source": "src",
        "observation_type": "observational",
        "cell_context": {"cell_type": "CL:0000988", "cell_line": "CLO:0009454", "state": "resting"},
        "assay_context": {"assay": "bulk-RNA-seq", "perturbation": None},
        "effect": {"sign": "positive", "magnitude": 0.5, "significance": 0.01},
        "contradicts": [],
    }
    outranking_raw = {
        "evidence_id": "src:bbbbbbbbbbbbbbbb",
        "source": "src",
        "observation_type": "interventional",
        "cell_context": {"cell_type": "CL:0000988", "cell_line": "CLO:0009454", "state": "resting"},
        "assay_context": {"assay": "bulk-RNA-seq", "perturbation": None},
        "effect": {"sign": "negative", "magnitude": -0.5, "significance": 0.001},
        "contradicts": [],
    }
    cited_canonical = CanonicalEvidence(
        schema_version="0.1.0",
        evidence_id=cited_raw["evidence_id"],
        source="src",
        snapshot_hash="0" * 64,
        record_type="expression_observation",
        subject_id="HGNC:11998",
        subject_label="TP53",
        object_id="HGNC:11892",
        object_label="CDKN1A",
        species="NCBITaxon:9606",
        cell_type="CL:0000988",
        cell_line="CLO:0009454",
        state="resting",
        assay="bulk-RNA-seq",
        perturbation=None,
        observation_type="observational",
        effect=CanonicalEffect(sign="positive", magnitude=0.5, significance=0.01, magnitude_scale="pearson_r"),
        contradicts=(),
        retrieved_at="2026-01-15T00:00:00Z",
        license="CC0-1.0",
        source_citation=None,
    )
    cited = (CitedRecord(evidence_id=cited_raw["evidence_id"], raw=cited_raw, canonical=cited_canonical),)

    class _FakeLedger:
        def list_by(self, subject_id, object_id):
            return [cited_raw, outranking_raw]

    class _FakeBundle:
        ledger = _FakeLedger()

    from normalize import CanonicalClaim

    claim = CanonicalClaim(
        schema_version="0.1.0",
        claim_id="dddddddd-dddd-dddd-dddd-dddddddddddd",
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
        state="resting",
        assay="bulk-RNA-seq",
        perturbation=None,
        evidence_ids=(cited_raw["evidence_id"],),
        confidence_language="observed",
        requested_status="hypothesis",
    )

    reason = contradiction.check(claim, cited, _FakeBundle())
    assert reason is not None
    assert reason.rule_id == "R-CONTRA-01"
