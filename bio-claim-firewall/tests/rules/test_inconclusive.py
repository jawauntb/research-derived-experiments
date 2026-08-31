"""INCONCLUSIVE__example.json -> INCONCLUSIVE, empty reasons, empty applied_rules."""

from __future__ import annotations


def test_inconclusive_example_is_inconclusive_with_empty_derivation(run_claim):
    result = run_claim("INCONCLUSIVE__example.json")

    assert result.verdict == "INCONCLUSIVE"
    assert result.fault_code is None
    assert result.reasons == ()
    assert result.applied_rules == ()
    assert result.conditions == ()
