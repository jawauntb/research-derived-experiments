"""Structural tests for the live pilot runner (no live spend in CI)."""

from __future__ import annotations

import pytest

from experiments.load_bearing_prose_test.run_lbpt_live_pilot import (
    CT_TASKS_PATH,
    FAMILY_KAPPA,
    _load_ct_tasks,
    run_live_pilot,
)


def test_ct_tasks_load_and_cover_both_families() -> None:
    tasks = _load_ct_tasks()
    assert CT_TASKS_PATH.is_file()
    families = {task.family for task in tasks}
    assert families == set(FAMILY_KAPPA)
    # The CT bank ships 12 tasks per family for a 24-task pilot budget.
    counts = {fam: 0 for fam in families}
    for task in tasks:
        counts[task.family] += 1
    assert counts["artifact_completion"] == 12
    assert counts["recursive_constrained_tool_use"] == 12


def test_family_kappa_matches_ct_condition_policy_substrate() -> None:
    ac = FAMILY_KAPPA["artifact_completion"]
    rct = FAMILY_KAPPA["recursive_constrained_tool_use"]
    assert ac["required_artifact"] == "reports/out.md"
    assert "write_artifact" in ac["required_capabilities"]
    assert "deploy" in ac["forbidden_capabilities"]
    assert rct["required_artifact"] is None
    assert "delegate" in rct["required_capabilities"]
    for cap in ("publish", "deploy", "grant_admin"):
        assert cap in rct["forbidden_capabilities"]


def test_run_live_pilot_requires_lbpt_live_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Constructing the planner/executor must refuse without the flag."""

    monkeypatch.delenv("LBPT_LIVE", raising=False)
    with pytest.raises(RuntimeError, match="LBPT_LIVE"):
        run_live_pilot(seed=1, max_workers=1, limit=1)
