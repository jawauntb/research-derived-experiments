"""§9 Citation resolution -- R-CITE-01, R-CITE-02, R-CITE-03 (sections/citations.py)."""

from __future__ import annotations


def test_bad_citation_invalid_fixture_rejects(run_claim, expectations):
    entry = next(e for e in expectations if e["claim_path"].endswith("BAD_CITATION__invalid.json"))
    result = run_claim("BAD_CITATION__invalid.json")

    assert result.verdict == "REJECTED"
    assert result.fault_code == "BAD_CITATION"
    assert len(result.reasons) >= 1
    assert result.reasons[0].rule_id.startswith(entry["expected_rule_id_prefix"])


def test_bad_citation_valid_fixture_accepts(run_claim, expectations):
    entry = next(e for e in expectations if e["claim_path"].endswith("BAD_CITATION__valid.json"))
    result = run_claim("BAD_CITATION__valid.json")

    assert result.verdict == "ACCEPTED"
    for substring in entry["expected_conditions_contain"]:
        assert any(substring in condition for condition in result.conditions)
