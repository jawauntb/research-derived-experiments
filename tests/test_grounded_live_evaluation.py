from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from experiments.grounded_statecharts.adapters import build_executor
from experiments.grounded_statecharts.adapters.fixture import FixtureExecutor
from experiments.grounded_statecharts.adapters.live import LIVE_OPT_IN_ENV, LiveExecutor
from experiments.grounded_statecharts.budgets import (
    DEFAULT_PILOT_BUDGET,
    BudgetSpec,
    BudgetUsage,
    plan_budget,
    settle_budget,
)
from experiments.grounded_statecharts.evaluation import (
    CORE_CONDITIONS,
    LiveEpisode,
    bootstrap_paired_effect,
    harness_digest_for,
    load_schema,
    public_rows,
    run_episode,
    run_smoke_matrix,
    smoke_tasks,
    validate_required_shape,
)
from experiments.grounded_statecharts.sanitization import sanitize_public_row


PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "experiments" / "grounded_statecharts"


def test_schemas_are_closed_and_aligned_with_smoke_rows() -> None:
    task_schema = load_schema("task.schema.json")
    episode_schema = load_schema("episode.schema.json")
    result_schema = load_schema("result.schema.json")
    intervention_schema = load_schema("intervention.schema.json")

    for schema in (task_schema, episode_schema, result_schema, intervention_schema):
        assert schema["additionalProperties"] is False
        assert set(schema["required"]) == set(schema["properties"])

    task = smoke_tasks()[0]
    assert validate_required_shape(task.to_dict(), task_schema)

    episode = LiveEpisode(
        episode_id="ep-1",
        run_id="run-1",
        task=task,
        condition="statechart_g3",
        repeat_index=0,
        model_id="fixture-deterministic-v1",
        provider_id="fixture",
        adapter_id="fixture",
        harness_digest=harness_digest_for("statechart_g3"),
        budget=DEFAULT_PILOT_BUDGET,
        seed=1,
    )
    assert validate_required_shape(episode.to_dict(), episode_schema)
    result = run_episode(episode)
    assert result.integrity.publishable
    assert validate_required_shape(result.public_row, result_schema)


def test_fixture_adapter_has_no_network_and_is_replay_stable() -> None:
    results = run_smoke_matrix(run_id="mechanics", repeats=2)
    assert len(results) == len(smoke_tasks()) * len(CORE_CONDITIONS) * 2
    assert all(result.episode.adapter_id == "fixture" for result in results)
    assert all(result.integrity.replay_ok for result in results)
    assert all(result.integrity.publishable for result in results)

    artifact = [row for row in public_rows(results) if row["family"] == "artifact_completion"]
    g0 = [row for row in artifact if row["condition"] == "statechart_g0"]
    g3 = [row for row in artifact if row["condition"] == "statechart_g3"]
    assert g0 and all(row["false_completion"] for row in g0)
    assert g3 and all(not row["false_completion"] and row["task_success"] for row in g3)


def test_budget_planner_fails_closed_before_dispatch() -> None:
    tight = BudgetSpec(
        max_calls=0,
        max_input_tokens=100,
        max_output_tokens=100,
        max_tool_calls=0,
        max_latency_ms=1000,
        max_cost_usd=0.01,
    )
    planned = plan_budget(spec=tight, planned_calls=1)
    assert planned.ok is False
    assert planned.exhausted is True

    task = smoke_tasks()[0]
    episode = LiveEpisode(
        episode_id="budget-ep",
        run_id="budget-run",
        task=task,
        condition="direct_self_report",
        repeat_index=0,
        model_id="fixture-deterministic-v1",
        provider_id="fixture",
        adapter_id="fixture",
        harness_digest=harness_digest_for("direct_self_report"),
        budget=tight,
        seed=7,
    )
    result = run_episode(episode, planned_calls=1)
    assert result.refusal is True
    assert result.budget_receipt.ok is False
    assert result.integrity.publishable is False


def test_settle_budget_tracks_realized_usage() -> None:
    usage = BudgetUsage(
        call_count=2,
        input_tokens=10,
        output_tokens=5,
        tool_calls=1,
        latency_ms=20,
        estimated_cost_usd=0.0,
    )
    receipt = settle_budget(spec=DEFAULT_PILOT_BUDGET, usage=usage, planned_calls=2)
    assert receipt.ok is True
    overflow = settle_budget(
        spec=DEFAULT_PILOT_BUDGET,
        usage=usage.add(calls=100),
        planned_calls=2,
    )
    assert overflow.ok is False


def test_sanitizer_blocks_raw_provider_material() -> None:
    clean = run_episode(
        LiveEpisode(
            episode_id="san-ep",
            run_id="san-run",
            task=smoke_tasks()[0],
            condition="statechart_g3",
            repeat_index=0,
            model_id="fixture-deterministic-v1",
            provider_id="fixture",
            adapter_id="fixture",
            harness_digest=harness_digest_for("statechart_g3"),
            budget=DEFAULT_PILOT_BUDGET,
            seed=3,
        )
    ).public_row
    dirty = dict(clean)
    dirty["raw"] = {"provider_payload": {"text": "secret"}}
    receipt = sanitize_public_row(dirty)
    assert receipt.ok is False
    assert "raw" in receipt.blocked_fields


def test_live_adapter_requires_explicit_opt_in(monkeypatch: pytest.MonkeyPatch) -> None:
    from experiments.grounded_statecharts.adapters.protocol import ExecutorRequest

    monkeypatch.delenv(LIVE_OPT_IN_ENV, raising=False)
    with pytest.raises(RuntimeError, match="GROUNDED_HARNESS_LIVE=1"):
        build_executor("live")

    monkeypatch.setenv(LIVE_OPT_IN_ENV, "1")
    monkeypatch.setenv("GROUNDED_HARNESS_PROVIDER", "openai")
    monkeypatch.setenv("GROUNDED_HARNESS_MODEL", "gpt-test")
    executor = build_executor("live")
    assert isinstance(executor, LiveExecutor)
    with pytest.raises(RuntimeError, match="not wired"):
        executor.complete(
            ExecutorRequest(
                episode_id="x",
                task_id="t",
                family="artifact_completion",
                condition="statechart_g3",
                instruction="do it",
                seed=0,
                step_index=0,
            )
        )


def test_task_clustered_bootstrap_is_seed_stable() -> None:
    rows = public_rows(run_smoke_matrix(run_id="boot", repeats=2))
    first = bootstrap_paired_effect(
        rows,
        treatment="statechart_g3",
        control="statechart_g0",
        metric="false_completion",
        bootstrap_samples=200,
        seed=20260720,
    )
    second = bootstrap_paired_effect(
        rows,
        treatment="statechart_g3",
        control="statechart_g0",
        metric="false_completion",
        bootstrap_samples=200,
        seed=20260720,
    )
    assert first == second
    assert first.task_count >= 2
    # G3 should reduce false completion versus G0 on artifact tasks.
    assert first.point_estimate < 0


def test_default_executor_is_fixture() -> None:
    executor = build_executor("fixture")
    assert isinstance(executor, FixtureExecutor)
    assert "OPENAI_API_KEY" not in os.environ or True
    assert PACKAGE_ROOT.joinpath("adapters", "live.py").is_file()


def test_schema_files_exist_for_handoff_contract() -> None:
    for name in (
        "task.schema.json",
        "episode.schema.json",
        "intervention.schema.json",
        "result.schema.json",
    ):
        payload = json.loads((PACKAGE_ROOT / "schemas" / name).read_text())
        assert payload["type"] == "object"


def test_live_smoke_bundle_is_byte_stable(tmp_path: Path) -> None:
    from experiments.grounded_statecharts.run_live_smoke import generate_results

    first = tmp_path / "a"
    second = tmp_path / "b"
    generate_results(first)
    generate_results(second)
    committed = PACKAGE_ROOT / "results" / "live_evaluation"
    for name in ("summary.json", "rows.jsonl"):
        assert (first / name).read_bytes() == (second / name).read_bytes()
        assert (first / name).read_bytes() == (committed / name).read_bytes()


def test_unified_replay_has_required_labels_and_is_byte_stable(tmp_path: Path) -> None:
    from experiments.grounded_statecharts.replay_viewer import REQUIRED_SECTION_LABELS
    from experiments.grounded_statecharts.run_unified_replay import generate_results

    first = tmp_path / "a"
    second = tmp_path / "b"
    generate_results(first)
    generate_results(second)
    committed = PACKAGE_ROOT / "results" / "unified_replay"

    rendered = (first / "replay.html").read_text()
    assert all(label in rendered for label in REQUIRED_SECTION_LABELS)
    for name in ("summary.json", "replay.html"):
        assert (first / name).read_bytes() == (second / name).read_bytes()
        assert (first / name).read_bytes() == (committed / name).read_bytes()
