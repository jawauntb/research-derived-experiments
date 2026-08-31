"""Hand-crafted claims violating each JSON-Schema constraint verify() must
route correctly per mapping.py -- no crash, correct fault_code / CHECKER_ERROR.
"""

from __future__ import annotations

import copy

from verifier import verify


def _valid_claim(load_claim):
    return load_claim("ACCEPTED_CONDITIONALLY__example.json")


def test_missing_required_field_is_checker_error(bundle, config, load_claim, assert_verdict_matches_schema):
    claim = _valid_claim(load_claim)
    del claim["relation"]

    verdict = verify(claim, bundle, config)
    assert_verdict_matches_schema(verdict)
    assert verdict["verdict"] == "CHECKER_ERROR"


def test_bad_relation_enum_is_invalid_relation(bundle, config, load_claim, assert_verdict_matches_schema):
    claim = _valid_claim(load_claim)
    claim["relation"] = "regulates_epigenetically"

    verdict = verify(claim, bundle, config)
    assert_verdict_matches_schema(verdict)
    assert verdict["verdict"] == "REJECTED"
    assert verdict["fault_code"] == "INVALID_RELATION"
    assert all(r["rule_id"].startswith("R-REL-") for r in verdict["reasons"])


def test_bad_subject_curie_pattern_is_unknown_entity(bundle, config, load_claim, assert_verdict_matches_schema):
    claim = _valid_claim(load_claim)
    claim["subject"] = {"id": "NOTAPREFIX:123", "label": "bogus"}

    verdict = verify(claim, bundle, config)
    assert_verdict_matches_schema(verdict)
    assert verdict["verdict"] == "REJECTED"
    assert verdict["fault_code"] == "UNKNOWN_ENTITY"
    assert all(r["rule_id"].startswith("R-ENT-") for r in verdict["reasons"])


def test_bad_object_curie_pattern_is_unknown_entity(bundle, config, load_claim, assert_verdict_matches_schema):
    claim = _valid_claim(load_claim)
    claim["object"] = {"id": "NOTAPREFIX:456", "label": "bogus"}

    verdict = verify(claim, bundle, config)
    assert_verdict_matches_schema(verdict)
    assert verdict["verdict"] == "REJECTED"
    assert verdict["fault_code"] == "UNKNOWN_ENTITY"


def test_bad_species_curie_pattern_is_unknown_entity(bundle, config, load_claim, assert_verdict_matches_schema):
    claim = _valid_claim(load_claim)
    claim["species"] = "not-a-taxon-curie"

    verdict = verify(claim, bundle, config)
    assert_verdict_matches_schema(verdict)
    assert verdict["verdict"] == "REJECTED"
    assert verdict["fault_code"] == "UNKNOWN_ENTITY"


def test_empty_evidence_ids_is_checker_error(bundle, config, load_claim, assert_verdict_matches_schema):
    claim = _valid_claim(load_claim)
    claim["evidence_ids"] = []

    verdict = verify(claim, bundle, config)
    assert_verdict_matches_schema(verdict)
    assert verdict["verdict"] == "CHECKER_ERROR"


def test_additional_property_is_checker_error(bundle, config, load_claim, assert_verdict_matches_schema):
    claim = _valid_claim(load_claim)
    claim["totally_unexpected_field"] = "surprise"

    verdict = verify(claim, bundle, config)
    assert_verdict_matches_schema(verdict)
    assert verdict["verdict"] == "CHECKER_ERROR"


def test_wrong_type_is_checker_error(bundle, config, load_claim, assert_verdict_matches_schema):
    claim = _valid_claim(load_claim)
    claim["polarity"] = 12345  # should be a string enum

    verdict = verify(claim, bundle, config)
    assert_verdict_matches_schema(verdict)
    assert verdict["verdict"] == "CHECKER_ERROR"


def test_schema_valid_claim_is_unaffected(bundle, config, load_claim, assert_verdict_matches_schema):
    """Sanity: mutating a deep copy never touches the fixture used elsewhere."""
    original = _valid_claim(load_claim)
    mutant = copy.deepcopy(original)
    mutant["relation"] = "regulates_epigenetically"

    verdict = verify(mutant, bundle, config)
    assert verdict["fault_code"] == "INVALID_RELATION"

    verdict2 = verify(original, bundle, config)
    assert_verdict_matches_schema(verdict2)
    assert verdict2["verdict"] == "ACCEPTED_CONDITIONALLY"
