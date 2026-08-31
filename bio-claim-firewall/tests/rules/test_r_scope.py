"""§6 Scope -- R-SCOPE-01, R-SCOPE-02, R-SCOPE-03 (sections/scope.py).

`SCOPE_OVERCLAIM__invalid/valid.json` are licensed via R-CAUS-04
(sections/causality.py) rather than R-SCOPE-01/02 -- see
sections/causality.py's and sections/scope.py's RULES-DECISIONs. This
file exercises both: the fixture pair (fault_code=SCOPE_OVERCLAIM via
R-CAUS-04) and direct unit coverage of R-SCOPE-01/02/03 themselves.
"""

from __future__ import annotations

from normalize import CanonicalClaim

from rules import RuleEngine


def test_scope_overclaim_invalid_fixture_rejects(run_claim, expectations):
    entry = next(e for e in expectations if e["claim_path"].endswith("SCOPE_OVERCLAIM__invalid.json"))
    result = run_claim("SCOPE_OVERCLAIM__invalid.json")

    assert result.verdict == "REJECTED"
    assert result.fault_code == "SCOPE_OVERCLAIM"
    assert result.reasons[0].rule_id.startswith(entry["expected_rule_id_prefix"])
    assert result.reasons[0].rule_id == "R-CAUS-04"


def test_scope_overclaim_valid_fixture_accepts(run_claim, expectations):
    entry = next(e for e in expectations if e["claim_path"].endswith("SCOPE_OVERCLAIM__valid.json"))
    result = run_claim("SCOPE_OVERCLAIM__valid.json")

    assert result.verdict == "ACCEPTED"
    for substring in entry["expected_conditions_contain"]:
        assert any(substring in condition for condition in result.conditions)


def test_r_scope_01_fires_on_single_study_established_non_causes(bundle):
    """R-SCOPE-01: established, non-causes relation, single study."""
    canonical = CanonicalClaim(
        schema_version="0.1.0",
        claim_id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
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
        evidence_ids=("perturbseq_v_test:fc1d7ea4dd7c21a7",),  # R1: single record, single study
        confidence_language="supported",
        requested_status="established",
    )
    result = RuleEngine(bundle, checker_version="0.1.0").run(canonical)

    assert result.verdict == "REJECTED"
    assert result.fault_code == "SCOPE_OVERCLAIM"
    assert result.reasons[0].rule_id == "R-SCOPE-01"


def test_r_scope_03_fires_when_claim_generalizes_beyond_every_matched_record(bundle):
    """R-SCOPE-03: claim.cell_type generalizes beyond every matched record's cell_type."""
    from rules.sections import scope

    canonical = CanonicalClaim(
        schema_version="0.1.0",
        claim_id="cccccccc-cccc-cccc-cccc-cccccccccccc",
        subject_id="HGNC:1097",
        subject_label="BRCA1",
        relation="increases",
        object_id="HGNC:6407",
        object_label="KRAS",
        polarity="positive",
        species="NCBITaxon:9606",
        cell_type="CL:0000000",  # root -- broader than R1's CL:0000988
        cell_type_ancestors=(),
        cell_line="CLO:0009454",
        state="resting",
        assay="CRISPRi_screen",
        perturbation="CRISPRi:HGNC:1097",
        evidence_ids=("perturbseq_v_test:fc1d7ea4dd7c21a7",),  # R1: cell_type=CL:0000988 only
        confidence_language="supported",
        requested_status="hypothesis",
    )
    reasons = scope.check_all(canonical, cited=_resolve(bundle, canonical), snapshot=bundle)
    assert len(reasons) == 1
    assert reasons[0].rule_id == "R-SCOPE-03"


def _resolve(bundle, canonical: CanonicalClaim):
    """Resolve `canonical`'s cited evidence_ids into `CitedRecord`s, bypassing the engine."""
    from normalize import normalize_evidence

    from rules.cited import CitedRecord

    records = []
    for evidence_id in canonical.evidence_ids:
        raw = bundle.ledger.get(evidence_id)
        records.append(CitedRecord(evidence_id=evidence_id, raw=raw, canonical=normalize_evidence(raw, bundle)))
    return tuple(records)
