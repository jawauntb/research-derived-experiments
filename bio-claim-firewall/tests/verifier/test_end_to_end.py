"""End-to-end: every entry of tests/fixtures/expectations.jsonl through `verify()`."""

from __future__ import annotations

from verifier import verify


def test_every_expectation(bundle, config, load_claim, expectations, assert_verdict_matches_schema):
    for entry in expectations:
        claim_name = entry["claim_path"].removeprefix("claims/")
        claim = load_claim(claim_name)
        verdict = verify(claim, bundle, config)

        assert_verdict_matches_schema(verdict)

        assert verdict["verdict"] == entry["expected_verdict"], (
            f"{claim_name}: expected verdict {entry['expected_verdict']!r}, got {verdict['verdict']!r} "
            f"(verdict={verdict!r})"
        )

        if entry["expected_verdict"] == "REJECTED":
            assert verdict["fault_code"] == entry["expected_fault_code"], claim_name
            prefix = entry["expected_rule_id_prefix"]
            for reason in verdict["reasons"]:
                assert reason["rule_id"].startswith(prefix), (
                    f"{claim_name}: rule_id {reason['rule_id']!r} does not start with {prefix!r}"
                )

        if entry["expected_verdict"] == "ACCEPTED_CONDITIONALLY":
            conditions = verdict["derivation"]["conditions"]
            for substring in entry.get("expected_conditions_contain", []):
                assert any(substring in c for c in conditions), (
                    f"{claim_name}: {substring!r} not found in conditions {conditions!r}"
                )

        assert len(verdict["verdict_id"]) == 32
        assert all(c in "0123456789abcdef" for c in verdict["verdict_id"])
        assert verdict["checker_version"] == config.checker_version
        assert verdict["snapshot_hashes"], f"{claim_name}: snapshot_hashes must be non-empty"


def test_schema_invalid_fixtures_reject_via_schema_path_not_rule_cascade(
    bundle, config, load_claim, expectations, assert_verdict_matches_schema
):
    """The two claims pre-authored as schema-invalid REJECT via the
    JSON-Schema-failure mapping path, never via the rule cascade -- see
    the task brief's `expectations.jsonl.schema_invalid` marker.
    """
    schema_invalid_entries = [e for e in expectations if e.get("schema_invalid")]
    assert schema_invalid_entries, "expected at least one schema_invalid expectation entry"

    for entry in schema_invalid_entries:
        claim_name = entry["claim_path"].removeprefix("claims/")
        claim = load_claim(claim_name)
        verdict = verify(claim, bundle, config)
        assert_verdict_matches_schema(verdict)
        assert verdict["verdict"] == "REJECTED"
        assert verdict["fault_code"] == entry["expected_fault_code"]
