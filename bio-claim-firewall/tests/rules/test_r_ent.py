"""§1 Allowed prefixes -- R-ENT-01, R-ENT-02, R-ENT-03 (sections/entities.py).

# RULES-DECISION: `UNKNOWN_ENTITY__invalid.json` is schema-valid, but its
# `subject.id` (`HGNC:9999999`) fails to resolve during
# `normalize.normalize_claim()` itself -- a `NormalizationError` is raised
# there, before a `CanonicalClaim` (and therefore a `RuleEngine.run()`
# call) can even exist. In the full pipeline that failure is exactly what
# should happen (`normalize_claim` is the module chartered to raise
# `UNKNOWN_ENTITY`). To actually exercise `sections/entities.py`'s own
# R-ENT-02 check -- the deliverable this test file owns -- we hand-build a
# `CanonicalClaim` carrying the fixture's same bogus `subject_id` directly
# and run it through the engine, the same bypass-normalization pattern the
# task brief sanctions for R-REL-01/`INVALID_RELATION` (see
# `sections/entities.py`'s own module docstring for the general
# rationale).
"""

from __future__ import annotations

from normalize import CanonicalClaim

from rules import RuleEngine


def test_unknown_entity_invalid_fixture_rejects(bundle, load_claim, expectations):
    entry = next(e for e in expectations if e["claim_path"].endswith("UNKNOWN_ENTITY__invalid.json"))
    claim_dict = load_claim("UNKNOWN_ENTITY__invalid.json")

    canonical = CanonicalClaim(
        schema_version=claim_dict["schema_version"],
        claim_id=claim_dict["claim_id"],
        subject_id=claim_dict["subject"]["id"],  # HGNC:9999999 -- never canonicalized
        subject_label=claim_dict["subject"]["label"],
        relation=claim_dict["relation"],
        object_id=claim_dict["object"]["id"],
        object_label=claim_dict["object"]["label"],
        polarity=claim_dict["polarity"],
        species=claim_dict["species"],
        cell_type=claim_dict["cell_context"]["cell_type"],
        cell_type_ancestors=(),
        cell_line=claim_dict["cell_context"].get("cell_line"),
        state=claim_dict["cell_context"].get("state"),
        assay=claim_dict["assay_context"]["assay"],
        perturbation=claim_dict["assay_context"].get("perturbation"),
        evidence_ids=tuple(claim_dict["evidence_ids"]),
        confidence_language=claim_dict["confidence_language"],
        requested_status=claim_dict["requested_status"],
    )
    result = RuleEngine(bundle, checker_version="0.1.0").run(canonical)

    assert result.verdict == "REJECTED"
    assert result.fault_code == "UNKNOWN_ENTITY"
    assert result.reasons[0].rule_id.startswith(entry["expected_rule_id_prefix"])


def test_unknown_entity_valid_fixture_accepts(run_claim, expectations):
    entry = next(e for e in expectations if e["claim_path"].endswith("UNKNOWN_ENTITY__valid.json"))
    result = run_claim("UNKNOWN_ENTITY__valid.json")

    assert result.verdict == "ACCEPTED"
    for substring in entry["expected_conditions_contain"]:
        assert any(substring in condition for condition in result.conditions)
