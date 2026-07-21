from __future__ import annotations

import json

from experiments.grounded_statecharts.run_unlearning_multishift_smoke import main
from experiments.grounded_statecharts.unlearning_multishift import (
    draft_shift_cases,
    generate_results,
)


def test_multishift_bank_has_nine_independent_instances() -> None:
    cases = draft_shift_cases()
    assert len(cases) == 9

    target_ids = [case.fixture.target_memory_id for case in cases]
    descendant_ids = [case.fixture.descendant_memory_id for case in cases]
    placebo_ids = [case.fixture.placebo_memory_id for case in cases]
    regime_pairs = [
        (case.fixture.prior_regime_id, case.fixture.shifted_regime_id) for case in cases
    ]
    # Independence means no two instances share a memory id or a regime pair,
    # not just a relabeled case_id over the same underlying ledger.
    assert len(set(target_ids)) == 9
    assert len(set(descendant_ids)) == 9
    assert len(set(placebo_ids)) == 9
    assert len(set(regime_pairs)) == 9
    assert len(set(case.case_id for case in cases)) == 9


def test_multishift_fixture_preserves_identical_semantics_control(tmp_path) -> None:
    summary = generate_results(tmp_path)
    rows = [json.loads(line) for line in (tmp_path / "rows.jsonl").read_text().splitlines()]

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


def test_multishift_cases_do_not_reuse_a_single_ledger(tmp_path) -> None:
    """The bank must not be the same fixture replayed 3x under new labels."""

    summary = generate_results(tmp_path)
    target_ids = {str(case["target_memory_id"]) for case in summary["cases"]}
    regime_pairs = {
        (str(case["prior_regime"]), str(case["shifted_regime"])) for case in summary["cases"]
    }
    assert len(target_ids) == 9
    assert len(regime_pairs) == 9


def test_run_unlearning_multishift_smoke_cli_writes_passing_bundle(tmp_path) -> None:
    """The documented credential-free CLI entry point must actually exist and
    run to a passing bundle (docs/module_explainer.md and README.md both
    document `run_unlearning_multishift_smoke`)."""

    exit_code = main(["--out-dir", str(tmp_path)])
    assert exit_code == 0
    summary = json.loads((tmp_path / "summary.json").read_text())
    assert all(summary["gates"].values())
