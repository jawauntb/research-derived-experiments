from __future__ import annotations

from pathlib import Path

import pytest

from experiments.grounded_statecharts.budgets import DEFAULT_PILOT_BUDGET
from experiments.grounded_statecharts.chs_live_withheld_score import (
    generate_results,
    score_live_withheld_harvest,
)
from experiments.grounded_statecharts.evaluation import (
    LiveEpisode,
    harness_digest_for,
    public_rows,
    run_episode,
    smoke_tasks,
)


def _row(*, task, condition: str, seed: int) -> dict:
    episode = LiveEpisode(
        episode_id=f"ep-{task.task_id}-{condition}",
        run_id="chs-live-withheld",
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


def test_score_live_withheld_harvest_reports_coverage_and_agreement() -> None:
    candidates = [
        {"source_result_digest": "d1", "predicted_component": "orchestration"},
        {"source_result_digest": "d2", "predicted_component": "output"},
    ]
    sealed_labels = [
        {"source_result_digest": "d1", "responsible_component": "orchestration"},
        {"source_result_digest": "d2", "responsible_component": "orchestration"},
        {"source_result_digest": "d3", "responsible_component": "output"},
    ]
    rows = score_live_withheld_harvest(candidates, sealed_labels)
    by_digest = {row["source_result_digest"]: row for row in rows}

    assert by_digest["d1"]["harvest_covered"] is True
    assert by_digest["d1"]["top1_agrees"] is True

    assert by_digest["d2"]["harvest_covered"] is True
    assert by_digest["d2"]["top1_agrees"] is False

    assert by_digest["d3"]["harvest_covered"] is False
    assert by_digest["d3"]["harvested_component"] is None
    assert by_digest["d3"]["top1_agrees"] is False


def test_score_live_withheld_harvest_never_reads_predicted_component_off_the_seal() -> None:
    # The join must key strictly on source_result_digest; passing a seal row
    # that happens to also carry a predicted_component (it shouldn't, but
    # defensively) must not change the join outcome.
    candidates = [{"source_result_digest": "d1", "predicted_component": "output"}]
    sealed_labels = [
        {
            "source_result_digest": "d1",
            "responsible_component": "orchestration",
            "predicted_component": "orchestration",
        }
    ]
    rows = score_live_withheld_harvest(candidates, sealed_labels)
    assert rows[0]["harvested_component"] == "output"
    assert rows[0]["sealed_component"] == "orchestration"
    assert rows[0]["top1_agrees"] is False


def test_generate_results_refuses_results_output_dir(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="artifacts"):
        generate_results(
            rows_path=tmp_path / "rows.jsonl",
            output_dir=tmp_path / "results" / "chs_live_withheld_score",
        )


def test_generate_results_joins_fresh_seal_and_harvest_end_to_end(tmp_path: Path) -> None:
    artifact = next(task for task in smoke_tasks() if task.family == "artifact_completion")
    constraint = next(
        task for task in smoke_tasks() if task.family == "recursive_constrained_tool_use"
    )
    rows = public_rows(
        [
            run_episode(
                LiveEpisode(
                    episode_id=f"ep-{artifact.task_id}-statechart_g0",
                    run_id="chs-live-withheld",
                    task=artifact,
                    condition="statechart_g0",
                    repeat_index=0,
                    model_id="fixture-deterministic-v1",
                    provider_id="fixture",
                    adapter_id="fixture",
                    harness_digest=harness_digest_for("statechart_g0"),
                    budget=DEFAULT_PILOT_BUDGET,
                    seed=1,
                )
            ),
            run_episode(
                LiveEpisode(
                    episode_id=f"ep-{artifact.task_id}-statechart_g3",
                    run_id="chs-live-withheld",
                    task=artifact,
                    condition="statechart_g3",
                    repeat_index=0,
                    model_id="fixture-deterministic-v1",
                    provider_id="fixture",
                    adapter_id="fixture",
                    harness_digest=harness_digest_for("statechart_g3"),
                    budget=DEFAULT_PILOT_BUDGET,
                    seed=1,
                )
            ),
            run_episode(
                LiveEpisode(
                    episode_id=f"ep-{constraint.task_id}-envelope_only",
                    run_id="chs-live-withheld",
                    task=constraint,
                    condition="envelope_only",
                    repeat_index=0,
                    model_id="fixture-deterministic-v1",
                    provider_id="fixture",
                    adapter_id="fixture",
                    harness_digest=harness_digest_for("envelope_only"),
                    budget=DEFAULT_PILOT_BUDGET,
                    seed=2,
                )
            ),
            run_episode(
                LiveEpisode(
                    episode_id=f"ep-{constraint.task_id}-envelope_external_guards",
                    run_id="chs-live-withheld",
                    task=constraint,
                    condition="envelope_external_guards",
                    repeat_index=0,
                    model_id="fixture-deterministic-v1",
                    provider_id="fixture",
                    adapter_id="fixture",
                    harness_digest=harness_digest_for("envelope_external_guards"),
                    budget=DEFAULT_PILOT_BUDGET,
                    seed=2,
                )
            ),
        ]
    )
    rows_path = tmp_path / "rows.jsonl"
    rows_path.write_text("".join(__import__("json").dumps(row) + "\n" for row in rows))

    out_dir = tmp_path / "artifacts" / "chs_live_withheld_score"
    summary = generate_results(rows_path=rows_path, output_dir=out_dir)

    assert summary["gates"]["labels_under_artifacts_only"] is True
    assert summary["gates"]["harvest_never_reads_sealed_store"] is True
    assert summary["gates"]["seal_never_reads_harvest_predictions"] is True
    assert summary["gates"]["join_performed_after_both_independently_return"] is True
    # This gate is deliberately always False: a live join between an
    # orchestration/output-only paired-contrast seal and a heuristic
    # harvest is never a six-surface CHS1 result.
    assert summary["gates"]["six_surface_chs1_claim"] is False
    assert summary["sealed_count"] >= 1
    # These two paired contrasts are the same ones the heuristic harvest's
    # own rules are declared to match, so joint coverage and agreement must
    # both be complete for this fixture-deterministic scenario.
    assert summary["metrics"]["seal_coverage_rate"] == 1.0
    assert summary["metrics"]["top1_agreement_rate_given_coverage"] == 1.0
    assert (out_dir / "summary.json").exists()
    assert (out_dir / "rows.jsonl").exists()
    assert (out_dir / "sealed_labels.jsonl").exists()
    assert (out_dir / "harvest_candidates.jsonl").exists()
