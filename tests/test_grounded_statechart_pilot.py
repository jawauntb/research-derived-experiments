from __future__ import annotations

from experiments.grounded_statecharts.adapters import build_executor
from experiments.grounded_statecharts.budgets import DEFAULT_PILOT_BUDGET, BudgetSpec
from experiments.grounded_statecharts.evaluation import LiveEpisode, harness_digest_for
from experiments.grounded_statecharts.sanitization import REQUIRED_PUBLIC_FIELDS
from experiments.grounded_statecharts.statechart_pilot import (
    artifact_smoke_tasks,
    run_statechart_episode,
    run_statechart_pilot_smoke,
)


def _artifact_episode(condition: str, budget: BudgetSpec = DEFAULT_PILOT_BUDGET) -> LiveEpisode:
    executor = build_executor("fixture")
    task = artifact_smoke_tasks()[0]
    return LiveEpisode(
        episode_id=f"pilot:{condition}",
        run_id="statechart-pilot-test",
        task=task,
        condition=condition,
        repeat_index=0,
        model_id=executor.model_id,
        provider_id=executor.provider_id,
        adapter_id=executor.adapter_id,
        harness_digest=harness_digest_for(condition),
        budget=budget,
        seed=0,
    )


def test_g0_and_direct_self_report_false_complete_on_replay_fixture() -> None:
    for condition in ("direct_self_report", "statechart_g0"):
        result = run_statechart_episode(_artifact_episode(condition))
        assert result.false_completion is True
        assert result.task_success is False
        assert result.integrity.publishable is True


def test_g3_replays_repair_then_commits() -> None:
    result = run_statechart_episode(_artifact_episode("statechart_g3"))
    assert result.false_completion is False
    assert result.task_success is True
    assert result.recovery_success is True
    assert result.integrity.replay_ok is True
    assert result.integrity.publishable is True


def test_wrong_edge_control_does_not_receive_g3_credit() -> None:
    result = run_statechart_episode(_artifact_episode("wrong_edge_guard"))
    assert result.invalid_transition is True
    assert result.false_completion is True
    assert result.task_success is False
    assert result.joint_success is False
    assert result.recovery_success is False


def test_pilot_fails_closed_before_replay_on_budget_overflow() -> None:
    tight = BudgetSpec(0, 12_000, 4_000, 12, 120_000, 0.25)
    result = run_statechart_episode(_artifact_episode("statechart_g3", tight))
    assert result.budget_receipt.ok is False
    assert result.integrity.budget_ok is False
    assert result.integrity.publishable is False
    assert result.public_event_digests == ()


def test_pilot_rows_are_sanitized_and_share_default_ceilings() -> None:
    results = run_statechart_pilot_smoke()
    artifact = [result for result in results if result.episode.task.family == "artifact_completion"]
    assert {result.episode.condition for result in artifact} == {
        "direct_self_report",
        "statechart_g0",
        "statechart_g3",
        "wrong_edge_guard",
    }
    assert all(result.budget_receipt.spec == DEFAULT_PILOT_BUDGET for result in results)
    assert all(result.budget_receipt.ok for result in results)
    assert all(result.sanitization.ok for result in results)
    assert all(set(result.public_row) == REQUIRED_PUBLIC_FIELDS for result in results)
