from __future__ import annotations

from pathlib import Path

from experiments.grounded_statecharts.chs_adjudication import (
    PROTOCOL_VERSION,
    seal_from_paired_contrasts,
)
from experiments.grounded_statecharts.evaluation import (
    LiveEpisode,
    harness_digest_for,
    public_rows,
    run_episode,
    smoke_tasks,
)
from experiments.grounded_statecharts.budgets import DEFAULT_PILOT_BUDGET


def _row(*, task, condition: str, seed: int) -> dict:
    episode = LiveEpisode(
        episode_id=f"ep-{task.task_id}-{condition}",
        run_id="chs-adj",
        task=task,
        condition=condition,
        repeat_index=0,
        model_id="fixture-deterministic-v1",
        provider_id="fixture",
        adapter_id="fixture",
        harness_digest=harness_digest_for(condition),
        budget=DEFAULT_PILOT_BUDGET,
        seed=seed,
    )
    return run_episode(episode).public_row


def test_paired_contrast_seals_orchestration_without_heuristic() -> None:
    artifact = next(task for task in smoke_tasks() if task.family == "artifact_completion")
    constraint = next(
        task for task in smoke_tasks() if task.family == "recursive_constrained_tool_use"
    )
    rows = [
        _row(task=artifact, condition="statechart_g0", seed=1),
        _row(task=artifact, condition="statechart_g3", seed=1),
        _row(task=constraint, condition="envelope_only", seed=2),
        _row(task=constraint, condition="envelope_external_guards", seed=2),
        _row(task=artifact, condition="wrong_edge_guard", seed=3),
    ]
    # Under harness-v2, G0 false completion may be repaired only on G3; fixture
    # already encodes that pattern. External enforcement may recover envelope fails.
    sealed = seal_from_paired_contrasts(rows)
    assert sealed
    assert all(item["protocol_version"] == PROTOCOL_VERSION for item in sealed)
    assert all(item["label_status"] == "sealed_by_paired_contrast" for item in sealed)
    assert "predicted_component" not in sealed[0]
    components = {item["responsible_component"] for item in sealed}
    assert components <= {"orchestration", "output"}


def test_public_rows_never_carry_sealed_labels() -> None:
    rows = public_rows(
        [
            run_episode(
                LiveEpisode(
                    episode_id="no-label",
                    run_id="chs-adj",
                    task=smoke_tasks()[0],
                    condition="statechart_g0",
                    repeat_index=0,
                    model_id="fixture-deterministic-v1",
                    provider_id="fixture",
                    adapter_id="fixture",
                    harness_digest=harness_digest_for("statechart_g0"),
                    budget=DEFAULT_PILOT_BUDGET,
                    seed=9,
                )
            )
        ]
    )
    assert "responsible_component" not in rows[0]
    assert "predicted_component" not in rows[0]
