"""Plan executor adapter for the load-bearing prose test.

Wraps the Constraint Transport (CT) executor path so a prose plan is
what the executor acts on. Two executors ship:

- ``PlanSensitiveFixtureExecutor`` — deterministic, keyword-driven,
  reads plan text and picks a CT fixture "mode" so ablations produce
  measurable commitment-surface deltas in CI (no live spend).
- ``CTPlanLiveExecutor`` — env-gated wrapper around
  ``experiments.grounded_statecharts.adapters.live.LiveExecutor``. The
  plan text is passed to the CT prompt as the instruction, so the
  live provider's decision reflects what the plan says.

Both go through ``run_plan_episode`` which applies
``condition_policy.apply_condition_policy`` and returns
``AppliedEvidence`` — the same commitment-surface substrate CT
scores against.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from typing import Protocol

from experiments.grounded_statecharts.adapters.protocol import (
    ExecutorRequest,
    ExecutorResponse,
)
from experiments.grounded_statecharts.budgets import BudgetUsage
from experiments.grounded_statecharts.condition_policy import (
    AppliedEvidence,
    apply_condition_policy,
)


LBPT_LIVE_OPT_IN_ENV = "LBPT_LIVE"


@dataclass(frozen=True)
class PlanEpisode:
    """One executor run over a specific plan text.

    ``plan_id`` and ``variant`` (``baseline`` or an ablation label)
    identify the run; ``plan_digest`` locks the exact plan bytes.
    """

    plan_id: str
    variant: str
    plan_text: str
    family: str
    task_id: str
    condition: str
    required_artifact: str | None
    required_capabilities: tuple[str, ...]
    forbidden_capabilities: tuple[str, ...]
    seed: int

    @property
    def plan_digest(self) -> str:
        return hashlib.sha256(self.plan_text.encode()).hexdigest()


class PlanExecutor(Protocol):
    """Any executor the plan runner can use."""

    @property
    def adapter_id(self) -> str: ...

    @property
    def provider_id(self) -> str: ...

    @property
    def model_id(self) -> str: ...

    def complete(self, request: ExecutorRequest) -> ExecutorResponse: ...


def _executor_request(episode: PlanEpisode, step_index: int = 0) -> ExecutorRequest:
    return ExecutorRequest(
        episode_id=f"{episode.plan_id}::{episode.variant}",
        task_id=episode.task_id,
        family=episode.family,
        condition=episode.condition,
        instruction=episode.plan_text,
        seed=episode.seed,
        step_index=step_index,
    )


def _budget_usage(text: str) -> BudgetUsage:
    token_seed = int(hashlib.sha256(text.encode()).hexdigest()[:6], 16)
    return BudgetUsage(
        call_count=1,
        input_tokens=120 + (token_seed % 80),
        output_tokens=30 + (token_seed % 30),
        tool_calls=0,
        latency_ms=5 + (token_seed % 10),
        estimated_cost_usd=0.0,
    )


class PlanSensitiveFixtureExecutor:
    """Deterministic executor whose action varies with the plan text.

    Keyword-driven so that removing obligation-shaped claims flips the
    executor's chosen CT fixture "mode" and produces a measurable
    commitment-surface delta. Never touches the network.
    """

    adapter_id = "lbpt-fixture"
    provider_id = "lbpt-fixture"
    model_id = "plan-sensitive-fixture-v1"

    def complete(self, request: ExecutorRequest) -> ExecutorResponse:
        family = request.family
        plan = request.instruction.lower()
        mode = self._behavior(family, request.condition, plan)
        # artifact_created is only meaningful for the artifact_completion
        # family; the recursive-constrained-tool-use family has no artifact.
        artifact_created = family == "artifact_completion" and mode == "grounded_commit"
        claimed_complete = mode != "refuse"
        action = {
            "false_complete": "claim_complete_without_artifact",
            "grounded_commit": "create_artifact_and_commit",
            "refuse": "refuse_task",
            "constrained_success": "delegate_with_envelope",
            "constraint_violation": "delegate_with_widened_capability",
            "wrong_edge": "verify_with_wrong_evidence",
        }[mode]
        capabilities: tuple[str, ...]
        if mode == "grounded_commit":
            capabilities = ("write_artifact",)
        elif mode == "constrained_success":
            capabilities = ("delegate",)
        elif mode == "constraint_violation":
            # Widen with a forbidden capability the fixtures declare.
            widened = "deploy" if "deploy" in plan else "publish"
            capabilities = ("delegate", widened)
        elif mode == "false_complete":
            capabilities = ()
        elif mode == "wrong_edge":
            capabilities = ("verify",)
        else:
            capabilities = ()
        text = f"lbpt-fixture:{request.task_id}:{request.condition}:{mode}"
        return ExecutorResponse(
            text=text,
            action=action,
            claimed_complete=claimed_complete,
            artifact_created=artifact_created,
            capability_used=capabilities,
            usage=_budget_usage(text),
            raw=None,
        )

    @staticmethod
    def _behavior(family: str, condition: str, plan: str) -> str:
        # condition is accepted for parity with the CT fixture signature so
        # future callers can gate behavior per-condition without a rename.
        _ = condition
        if family == "artifact_completion":
            steers_grounded = (
                ("must" in plan or "required to" in plan or "shall" in plan)
                and ("commit" in plan or "write" in plan)
                and ("artifact" in plan or "reports/out.md" in plan)
            )
            return "grounded_commit" if steers_grounded else "false_complete"
        if family == "recursive_constrained_tool_use":
            forbids_widen = (
                "must not" in plan
                or "not allowed" in plan
                or "forbidden" in plan
                or "prohibited" in plan
            )
            steers_delegate = (
                ("delegate" in plan and ("envelope" in plan or "with envelope" in plan))
                or ("must delegate" in plan)
                or ("required to delegate" in plan)
            )
            if steers_delegate and forbids_widen:
                return "constrained_success"
            if steers_delegate:
                return "constrained_success"
            return "constraint_violation"
        raise ValueError(f"unsupported family: {family}")


class CTPlanLiveExecutor:
    """Env-gated live wrapper that feeds plan text to the CT live executor.

    Requires ``LBPT_LIVE=1`` plus the standard ``GROUNDED_HARNESS_LIVE``
    environment for the CT adapter. Constructor raises when the opt-in
    is missing so nothing accidentally spends provider tokens in CI.
    """

    adapter_id = "lbpt-live"

    def __init__(self) -> None:
        if os.environ.get(LBPT_LIVE_OPT_IN_ENV, "").strip() != "1":
            raise RuntimeError(
                f"live opt-in missing: set {LBPT_LIVE_OPT_IN_ENV}=1 to enable "
                "provider calls"
            )
        # Import lazily so CI never resolves the CT live module.
        from experiments.grounded_statecharts.adapters.live import LiveExecutor

        # from_env resolves provider/model/API-key from the shared CT env
        # vars (GROUNDED_HARNESS_LIVE / _PROVIDER / _MODEL / _API_KEY_ENV).
        self._inner = LiveExecutor.from_env()

    @property
    def provider_id(self) -> str:
        return self._inner.provider_id

    @property
    def model_id(self) -> str:
        return self._inner.model_id

    def complete(self, request: ExecutorRequest) -> ExecutorResponse:
        return self._inner.complete(request)


def build_plan_executor(*, kind: str = "fixture") -> PlanExecutor:
    if kind == "fixture":
        return PlanSensitiveFixtureExecutor()
    if kind == "live":
        return CTPlanLiveExecutor()
    raise ValueError(f"unknown executor kind: {kind}")


def run_plan_episode(
    episode: PlanEpisode,
    *,
    executor: PlanExecutor | None = None,
) -> tuple[ExecutorResponse, AppliedEvidence]:
    """Execute one plan variant and apply CT harness enforcement.

    Returns the raw provider response and the ``AppliedEvidence`` that
    ``scoring.commitment_surface`` reads. Enforcement is CT's
    ``apply_condition_policy`` so the commitment surface is directly
    comparable to CT public rows.
    """

    active = executor or build_plan_executor(kind="fixture")
    request = _executor_request(episode)
    response = active.complete(request)
    evidence = apply_condition_policy(
        family=episode.family,
        task_id=episode.task_id,
        condition=episode.condition,
        required_artifact=episode.required_artifact,
        required_capabilities=episode.required_capabilities,
        forbidden_capabilities=episode.forbidden_capabilities,
        action=response.action,
        claimed_complete=response.claimed_complete,
        artifact_created=response.artifact_created,
        capability_used=response.capability_used,
    )
    return response, evidence
