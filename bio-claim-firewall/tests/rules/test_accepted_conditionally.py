"""ACCEPTED_CONDITIONALLY__example.json -> ACCEPTED with K562 in conditions."""

from __future__ import annotations


def test_accepted_conditionally_example_accepts(run_claim, expectations):
    entry = next(e for e in expectations if e["claim_path"].endswith("ACCEPTED_CONDITIONALLY__example.json"))
    result = run_claim("ACCEPTED_CONDITIONALLY__example.json")

    assert result.verdict == "ACCEPTED"
    assert result.fault_code is None
    assert result.applied_rules
    assert result.conditions
    assert any("K562" in condition for condition in result.conditions)
    for substring in entry["expected_conditions_contain"]:
        assert any(substring in condition for condition in result.conditions)
