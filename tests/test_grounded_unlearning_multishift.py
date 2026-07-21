from __future__ import annotations

import json

from experiments.grounded_statecharts.unlearning_multishift import (
    draft_shift_cases,
    generate_results,
)


def test_multishift_fixture_preserves_identical_semantics_control(tmp_path) -> None:
    summary = generate_results(tmp_path)
    rows = [json.loads(line) for line in (tmp_path / "rows.jsonl").read_text().splitlines()]

    assert len(draft_shift_cases()) == 9
    assert all(summary["gates"].values())
    assert {row["shift_family"] for row in rows} == {
        "tool-schema",
        "environment-policy",
        "model/version-identical-semantics",
    }
    unchanged = [
        case for case in summary["cases"] if not case["semantics_changed"]
    ]
    assert len(unchanged) == 3
    assert all(case["append_only_shift_success"] for case in unchanged)
    assert all(not case["lifecycle_applied"] for case in unchanged)


def test_multishift_changed_cases_require_causal_use_before_quarantine(tmp_path) -> None:
    summary = generate_results(tmp_path)

    changed = [case for case in summary["cases"] if case["semantics_changed"]]
    assert len(changed) == 6
    assert all(case["causal_use_prerequisite"] for case in changed)
    assert all(not case["append_only_shift_success"] for case in changed)
    assert all(case["post_lifecycle_success"] for case in changed)
