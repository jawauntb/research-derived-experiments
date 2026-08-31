"""§2 Relation grammar -- R-REL-01, R-REL-02 (sections/relations.py).

# RULES-DECISION: `INVALID_RELATION__invalid.json` is intentionally NOT
# schema-valid (`expectations.jsonl`'s `schema_invalid: true` -- its
# `relation` value, `"regulates_epigenetically"`, is outside
# `claim.schema.json`'s closed enum). Per the task brief's Option 2
# (preferred), we bypass `normalize_claim` for this one fixture and
# hand-build a `CanonicalClaim` carrying the same bogus relation string,
# so R-REL-01 is actually exercised rather than skipped/xfailed.
"""

from __future__ import annotations

from normalize import CanonicalClaim

from rules import RuleEngine


def test_invalid_relation_invalid_fixture_rejects(bundle, load_claim, expectations):
    entry = next(e for e in expectations if e["claim_path"].endswith("INVALID_RELATION__invalid.json"))
    assert entry.get("schema_invalid") is True  # guards against this fixture silently becoming valid
    claim_dict = load_claim("INVALID_RELATION__invalid.json")

    canonical = CanonicalClaim(
        schema_version=claim_dict["schema_version"],
        claim_id=claim_dict["claim_id"],
        subject_id=claim_dict["subject"]["id"],
        subject_label=claim_dict["subject"]["label"],
        relation=claim_dict["relation"],  # "regulates_epigenetically" -- outside the schema enum
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
    assert result.fault_code == "INVALID_RELATION"
    assert result.reasons[0].rule_id.startswith(entry["expected_rule_id_prefix"])
    assert result.reasons[0].rule_id == "R-REL-01"


def test_invalid_relation_valid_fixture_accepts(run_claim, expectations):
    entry = next(e for e in expectations if e["claim_path"].endswith("INVALID_RELATION__valid.json"))
    result = run_claim("INVALID_RELATION__valid.json")

    assert result.verdict == "ACCEPTED"
    for substring in entry["expected_conditions_contain"]:
        assert any(substring in condition for condition in result.conditions)


def test_r_rel_02_fires_for_binds_with_nonzero_polarity(bundle):
    """R-REL-02: binds/expressed_in must carry polarity='none'."""
    canonical = CanonicalClaim(
        schema_version="0.1.0",
        claim_id="44444444-4444-4444-4444-444444444444",
        subject_id="HGNC:5173",
        subject_label="IL6",
        relation="binds",
        object_id="HGNC:8975",
        object_label="IL6R",
        polarity="positive",  # invalid for binds -- R-REL-02
        species="NCBITaxon:9606",
        cell_type="unspecified",
        cell_type_ancestors=(),
        cell_line=None,
        state=None,
        assay="co-IP",
        perturbation=None,
        evidence_ids=("perturbseq_v_test:5bde6e0544a4736f",),
        confidence_language="observed",
        requested_status="hypothesis",
    )
    result = RuleEngine(bundle, checker_version="0.1.0").run(canonical)

    assert result.verdict == "REJECTED"
    assert result.fault_code == "INVALID_RELATION"
    assert result.reasons[0].rule_id == "R-REL-02"
