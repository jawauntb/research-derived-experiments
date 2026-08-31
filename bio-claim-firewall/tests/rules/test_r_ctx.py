"""§5 Context matching -- R-CTX-01..06 (sections/context.py)."""

from __future__ import annotations

from normalize import CanonicalClaim

from rules import RuleEngine


def test_context_mismatch_invalid_fixture_rejects(run_claim, expectations):
    entry = next(e for e in expectations if e["claim_path"].endswith("CONTEXT_MISMATCH__invalid.json"))
    result = run_claim("CONTEXT_MISMATCH__invalid.json")

    assert result.verdict == "REJECTED"
    assert result.fault_code == "CONTEXT_MISMATCH"
    assert result.reasons[0].rule_id.startswith(entry["expected_rule_id_prefix"])
    assert result.reasons[0].rule_id == "R-CTX-03"  # cell_line mismatch, per expectations.jsonl's note


def test_context_mismatch_valid_fixture_accepts(run_claim, expectations):
    entry = next(e for e in expectations if e["claim_path"].endswith("CONTEXT_MISMATCH__valid.json"))
    result = run_claim("CONTEXT_MISMATCH__valid.json")

    assert result.verdict == "ACCEPTED"
    for substring in entry["expected_conditions_contain"]:
        assert any(substring in condition for condition in result.conditions)


def _base_claim(**overrides) -> CanonicalClaim:
    fields = dict(
        schema_version="0.1.0",
        claim_id="66666666-6666-6666-6666-666666666666",
        subject_id="HGNC:1097",
        subject_label="BRCA1",
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
        evidence_ids=("perturbseq_v_test:fc1d7ea4dd7c21a7",),  # R1: K562, resting, CRISPRi
        confidence_language="supported",
        requested_status="hypothesis",
    )
    fields.update(overrides)
    return CanonicalClaim(**fields)


def test_r_ctx_01_fires_on_species_mismatch(bundle):
    # RULES-DECISION: R-SCOPE-90 (cascade position 3) already rejects any
    # non-human claim.species before R-CTX-* (position 6) is ever reached,
    # and every evidence record in this fixture world is species=human
    # too -- so a full-engine run can never actually observe R-CTX-01
    # firing here. We unit-test `context_ok` directly instead, the same
    # per-record helper `sections/context.py` itself calls, exercising its
    # R-CTX-01 branch in isolation.
    from normalize import CanonicalEvidence

    from rules.sections._shared import context_ok

    claim = _base_claim()
    evidence = CanonicalEvidence(
        schema_version="0.1.0",
        evidence_id="perturbseq_v_test:fc1d7ea4dd7c21a7",
        source="perturbseq_v_test",
        snapshot_hash="0" * 64,
        record_type="perturbation_effect",
        subject_id="HGNC:1097",
        subject_label="BRCA1",
        object_id="HGNC:6407",
        object_label="KRAS",
        species="NCBITaxon:10090",  # differs from the claim's NCBITaxon:9606
        cell_type="CL:0000988",
        cell_line="CLO:0009454",
        state="resting",
        assay="CRISPRi_screen",
        perturbation="CRISPRi:HGNC:1097",
        observation_type="interventional",
        effect=None,
        contradicts=(),
        retrieved_at="2026-01-15T00:00:00Z",
        license="CC0-1.0",
        source_citation=None,
    )
    ok, rule_id = context_ok(claim, evidence, bundle)
    assert ok is False
    assert rule_id == "R-CTX-01"


def test_r_ctx_04_fires_on_state_mismatch(bundle):
    canonical = _base_claim(state="IFNG_stimulated")
    result = RuleEngine(bundle, checker_version="0.1.0").run(canonical)
    assert result.verdict == "REJECTED"
    assert result.fault_code == "CONTEXT_MISMATCH"
    assert result.reasons[0].rule_id == "R-CTX-04"


def test_r_ctx_06_fires_on_perturbation_mismatch(bundle):
    canonical = _base_claim(perturbation="CRISPRi:HGNC:99999")
    result = RuleEngine(bundle, checker_version="0.1.0").run(canonical)
    assert result.verdict == "REJECTED"
    assert result.fault_code == "CONTEXT_MISMATCH"
    assert result.reasons[0].rule_id == "R-CTX-06"
