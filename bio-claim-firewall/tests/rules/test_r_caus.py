"""§4 Causality -- R-CAUS-01..04 (sections/causality.py).

R-CAUS-04 maps to fault_code SCOPE_OVERCLAIM (see the RULES-DECISION in
sections/causality.py) and is exercised via `SCOPE_OVERCLAIM__invalid/
valid.json` in test_r_scope.py instead of here.
"""

from __future__ import annotations

from normalize import CanonicalClaim

from rules import RuleEngine


def test_causality_overclaim_invalid_fixture_rejects(run_claim, expectations):
    entry = next(e for e in expectations if e["claim_path"].endswith("CAUSALITY_OVERCLAIM__invalid.json"))
    result = run_claim("CAUSALITY_OVERCLAIM__invalid.json")

    assert result.verdict == "REJECTED"
    assert result.fault_code == "CAUSALITY_OVERCLAIM"
    assert result.reasons[0].rule_id.startswith(entry["expected_rule_id_prefix"])
    assert result.reasons[0].rule_id == "R-CAUS-01"


def test_causality_overclaim_valid_fixture_accepts(run_claim, expectations):
    entry = next(e for e in expectations if e["claim_path"].endswith("CAUSALITY_OVERCLAIM__valid.json"))
    result = run_claim("CAUSALITY_OVERCLAIM__valid.json")

    assert result.verdict == "ACCEPTED"
    for substring in entry["expected_conditions_contain"]:
        assert any(substring in condition for condition in result.conditions)


def _base_causes_claim(**overrides) -> CanonicalClaim:
    fields = dict(
        schema_version="0.1.0",
        claim_id="99999999-9999-9999-9999-999999999999",
        subject_id="HGNC:1097",
        subject_label="BRCA1",
        relation="causes",
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
        evidence_ids=("perturbseq_v_test:fc1d7ea4dd7c21a7",),  # R1: interventional
        confidence_language="supported",
        requested_status="hypothesis",
    )
    fields.update(overrides)
    return CanonicalClaim(**fields)


def test_r_caus_02_fires_when_perturbation_is_null(bundle):
    canonical = _base_causes_claim(perturbation=None)
    result = RuleEngine(bundle, checker_version="0.1.0").run(canonical)

    assert result.verdict == "REJECTED"
    assert result.fault_code == "CAUSALITY_OVERCLAIM"
    assert result.reasons[0].rule_id == "R-CAUS-02"


def test_r_caus_03_fires_for_non_causes_relation_with_causal_language(bundle):
    # RULES-DECISION (see sections/causality.py): R-CAUS-01/02's own text
    # conditions on `relation == causes`, but R-CAUS-03's does not -- it
    # is a standalone check on `confidence_language` alone, which is
    # exactly why spec/inference_rules.md §8 can describe R-CERT-02 as
    # "subsuming" it in general. `increases` (not `causes`) with
    # confidence_language=causal and only an observational citation (R3,
    # whose effect.sign=positive matches `increases`' canonical direction,
    # so R-SIGN-01 -- cascade position 7, ahead of R-CAUS at position 8 --
    # does not stop the cascade first) exercises that unconditioned branch
    # directly: R-CAUS-01/02 don't even apply to this relation, so
    # R-CAUS-03 is the first (and only) thing that can fire here.
    canonical = CanonicalClaim(
        schema_version="0.1.0",
        claim_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        subject_id="HGNC:11998",
        subject_label="TP53",
        relation="increases",
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
        evidence_ids=("perturbseq_v_test:dea2437bf1fa58bd",),  # R3: observational, sign=positive
        confidence_language="causal",
        requested_status="hypothesis",
    )
    result = RuleEngine(bundle, checker_version="0.1.0").run(canonical)

    assert result.verdict == "REJECTED"
    assert result.fault_code == "CAUSALITY_OVERCLAIM"
    assert result.reasons[0].rule_id == "R-CAUS-03"
