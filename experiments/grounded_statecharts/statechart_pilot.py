"""Deterministic D2 mechanics bridge for the Grounded Statecharts pilot.

Artifact-completion conditions use the existing ReplayEngine and committed
false-success fixture. Constraint-family conditions deliberately remain on the
shared fixture-executor path until their separate transport pilot is frozen.
This module exercises the public live-result contract without contacting a
provider or treating smoke rows as held-out evidence.
"""

from __future__ import annotations

from pathlib import Path

from experiments.grounded_statecharts.adapters import ProviderExecutor, build_executor
from experiments.grounded_statecharts.budgets import (
    DEFAULT_PILOT_BUDGET,
    BudgetReceipt,
    BudgetSpec,
    BudgetUsage,
    plan_budget,
    settle_budget,
)
from experiments.grounded_statecharts.evaluation import (
    LiveEpisode,
    LiveResult,
    LiveTask,
    finalize_public_row,
    harness_digest_for,
    run_episode,
    smoke_tasks,
)
from experiments.grounded_statecharts.runtime import (
    Checkpoint,
    EpisodeOutcome,
    Fixture,
    HarnessManifest,
    ReplayEngine,
    digest,
)

PACKAGE_ROOT = Path(__file__).resolve().parent
ARTIFACT_CONDITIONS = frozenset(
    {"direct_self_report", "statechart_g0", "statechart_g3", "wrong_edge_guard"}
)


def artifact_smoke_tasks() -> tuple[LiveTask, ...]:
    """Return the existing smoke tasks in the artifact-completion family."""

    return tuple(task for task in smoke_tasks() if task.family == "artifact_completion")


def _load_replay_inputs() -> tuple[Fixture, HarnessManifest, HarnessManifest]:
    fixture = Fixture.load(PACKAGE_ROOT / "fixtures" / "false_success.json")
    g0 = HarnessManifest.load(PACKAGE_ROOT / "manifests" / "self_report.json")
    g3 = HarnessManifest.load(PACKAGE_ROOT / "manifests" / "independent_artifact.json")
    return fixture, g0, g3


def _outcome_for_condition(
    engine: ReplayEngine,
    fixture: Fixture,
    g0: HarnessManifest,
    g3: HarnessManifest,
    condition: str,
) -> tuple[Checkpoint, EpisodeOutcome]:
    """Run the committed checkpoint under the declared artifact condition."""

    checkpoint = engine.checkpoint_before_verification(fixture, g0)
    if condition == "statechart_g3":
        return checkpoint, engine.replay(checkpoint, fixture, g0, g3)
    if condition in {"direct_self_report", "statechart_g0", "wrong_edge_guard"}:
        return checkpoint, engine.replay(checkpoint, fixture, g0)
    raise ValueError(f"unsupported artifact condition: {condition}")


def _artifact_usage(outcome: EpisodeOutcome) -> BudgetUsage:
    """Fixed fixture accounting, intentionally separate from logical events."""

    return BudgetUsage(
        call_count=1,
        input_tokens=120,
        output_tokens=40,
        tool_calls=outcome.repair_count,
        latency_ms=10,
        estimated_cost_usd=0.0,
    )


def _failed_budget_result(episode: LiveEpisode, receipt: BudgetReceipt) -> LiveResult:
    candidate: dict[str, object] = {
        "episode_id": episode.episode_id,
        "run_id": episode.run_id,
        "task_id": episode.task.task_id,
        "family": episode.task.family,
        "condition": episode.condition,
        "repeat_index": episode.repeat_index,
        "adapter_id": episode.adapter_id,
        "model_id": episode.model_id,
        "provider_id": episode.provider_id,
        "false_completion": False,
        "task_success": False,
        "joint_success": False,
        "refusal": True,
        "invalid_transition": False,
        "recovery_success": False,
        "useful_autonomy": False,
        "call_count": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "tool_calls": 0,
        "latency_ms": 0,
        "estimated_cost_usd": 0.0,
        "budget_exhausted": receipt.exhausted,
        "task_digest": episode.task.task_digest,
        "harness_digest": episode.harness_digest,
        "budget_digest": episode.budget.digest(),
        "checkpoint_digest": digest({"status": "not_started"}),
        "event_count": 0,
        "public_event_digests": [],
    }
    integrity, sanitization, public_row = finalize_public_row(
        candidate, checkpoint_ok=False, replay_ok=False, budget_ok=False
    )
    return LiveResult(
        episode=episode,
        false_completion=False,
        task_success=False,
        joint_success=False,
        refusal=True,
        invalid_transition=False,
        recovery_success=False,
        useful_autonomy=False,
        budget_receipt=receipt,
        integrity=integrity,
        checkpoint_digest=str(candidate["checkpoint_digest"]),
        public_event_digests=(),
        sanitization=sanitization,
        public_row=public_row,
    )


def run_statechart_episode(
    episode: LiveEpisode,
    *,
    executor: ProviderExecutor | None = None,
    planned_calls: int = 1,
) -> LiveResult:
    """Map a fixture episode to one sanitized public live-evaluation row."""

    if episode.task.family != "artifact_completion":
        # Constraint mechanics are explicitly delegated until their own pilot exists.
        return run_episode(episode, executor=executor, planned_calls=planned_calls)
    if episode.condition not in ARTIFACT_CONDITIONS:
        raise ValueError(f"artifact task cannot run condition: {episode.condition}")
    if episode.adapter_id != "fixture":
        raise ValueError("the statechart pilot bridge is fixture-only")

    plan = plan_budget(spec=episode.budget, planned_calls=planned_calls)
    if not plan.ok:
        return _failed_budget_result(episode, plan)

    fixture, g0, g3 = _load_replay_inputs()
    engine = ReplayEngine()
    checkpoint, outcome = _outcome_for_condition(engine, fixture, g0, g3, episode.condition)
    _, replay = _outcome_for_condition(engine, fixture, g0, g3, episode.condition)
    usage = _artifact_usage(outcome)
    budget_receipt = settle_budget(
        spec=episode.budget, usage=usage, planned_calls=planned_calls
    )
    wrong_edge = episode.condition == "wrong_edge_guard"
    task_success = outcome.task_success and not wrong_edge
    false_completion = outcome.false_completion
    recovery_success = outcome.repair_count == 1 and task_success
    event_digests = tuple(digest(event.to_dict()) for event in outcome.events)
    candidate: dict[str, object] = {
        "episode_id": episode.episode_id,
        "run_id": episode.run_id,
        "task_id": episode.task.task_id,
        "family": episode.task.family,
        "condition": episode.condition,
        "repeat_index": episode.repeat_index,
        "adapter_id": episode.adapter_id,
        "model_id": episode.model_id,
        "provider_id": episode.provider_id,
        "false_completion": false_completion,
        "task_success": task_success,
        "joint_success": task_success and not false_completion and not wrong_edge,
        "refusal": False,
        "invalid_transition": wrong_edge,
        "recovery_success": recovery_success,
        "useful_autonomy": task_success and not wrong_edge,
        "call_count": usage.call_count,
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "tool_calls": usage.tool_calls,
        "latency_ms": usage.latency_ms,
        "estimated_cost_usd": usage.estimated_cost_usd,
        "budget_exhausted": budget_receipt.exhausted,
        "task_digest": episode.task.task_digest,
        "harness_digest": episode.harness_digest,
        "budget_digest": episode.budget.digest(),
        "checkpoint_digest": checkpoint.checkpoint_digest,
        "event_count": len(outcome.events),
        "public_event_digests": list(event_digests),
    }
    integrity, sanitization, public_row = finalize_public_row(
        candidate,
        checkpoint_ok=True,
        replay_ok=outcome == replay,
        budget_ok=budget_receipt.ok,
    )
    return LiveResult(
        episode=episode,
        false_completion=false_completion,
        task_success=task_success,
        joint_success=bool(candidate["joint_success"]),
        refusal=False,
        invalid_transition=wrong_edge,
        recovery_success=recovery_success,
        useful_autonomy=bool(candidate["useful_autonomy"]),
        budget_receipt=budget_receipt,
        integrity=integrity,
        checkpoint_digest=checkpoint.checkpoint_digest,
        public_event_digests=event_digests,
        sanitization=sanitization,
        public_row=public_row,
    )


def run_statechart_pilot_smoke(
    *,
    run_id: str = "statechart-pilot-smoke",
    budget: BudgetSpec = DEFAULT_PILOT_BUDGET,
    repeats: int = 1,
) -> tuple[LiveResult, ...]:
    """Exercise both D2 families without producing held-out pilot outcomes."""

    executor = build_executor("fixture")
    results: list[LiveResult] = []
    for task in smoke_tasks():
        conditions = (
            tuple(sorted(ARTIFACT_CONDITIONS))
            if task.family == "artifact_completion"
            else ("envelope_only", "envelope_external_guards", "wrong_edge_guard")
        )
        for condition in conditions:
            for repeat_index in range(repeats):
                episode = LiveEpisode(
                    episode_id=f"{run_id}:{task.task_id}:{condition}:r{repeat_index}",
                    run_id=run_id,
                    task=task,
                    condition=condition,
                    repeat_index=repeat_index,
                    model_id=executor.model_id,
                    provider_id=executor.provider_id,
                    adapter_id=executor.adapter_id,
                    harness_digest=harness_digest_for(condition),
                    budget=budget,
                    seed=repeat_index,
                )
                results.append(run_statechart_episode(episode, executor=executor))
    if any(result.budget_receipt.spec != budget for result in results):
        raise RuntimeError("pilot conditions must share the declared budget ceiling")
    return tuple(results)
