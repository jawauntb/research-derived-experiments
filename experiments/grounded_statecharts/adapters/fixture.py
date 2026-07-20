"""Deterministic fixture executor used by default tests and clean-clone paths."""

from __future__ import annotations

import hashlib

from experiments.grounded_statecharts.adapters.protocol import (
    ExecutorRequest,
    ExecutorResponse,
)
from experiments.grounded_statecharts.budgets import BudgetUsage


class FixtureExecutor:
    """Synthetic provider that never imports SDKs or touches the network."""

    adapter_id = "fixture"
    provider_id = "fixture"
    model_id = "fixture-deterministic-v1"

    def complete(self, request: ExecutorRequest) -> ExecutorResponse:
        mode = self._behavior(request)
        artifact_created = mode in {"grounded_commit", "constrained_success"}
        claimed_complete = mode != "refuse"
        action = {
            "false_complete": "claim_complete_without_artifact",
            "grounded_commit": "create_artifact_and_commit",
            "refuse": "refuse_task",
            "constrained_success": "delegate_with_envelope",
            "constraint_violation": "delegate_with_widened_capability",
            "wrong_edge": "verify_with_wrong_evidence",
        }[mode]
        text = f"fixture:{request.task_id}:{request.condition}:{mode}"
        capabilities = ("write_artifact",) if artifact_created else ()
        if mode == "constraint_violation":
            capabilities = ("write_artifact", "exfiltrate")
        if mode == "refuse":
            capabilities = ()
        token_seed = int(hashlib.sha256(text.encode()).hexdigest()[:6], 16)
        usage = BudgetUsage(
            call_count=1,
            input_tokens=80 + (token_seed % 40),
            output_tokens=20 + (token_seed % 20),
            tool_calls=1 if artifact_created or mode == "constraint_violation" else 0,
            latency_ms=5 + (token_seed % 10),
            estimated_cost_usd=0.0,
        )
        return ExecutorResponse(
            text=text,
            action=action,
            claimed_complete=claimed_complete,
            artifact_created=artifact_created,
            capability_used=capabilities,
            usage=usage,
            raw=None,
        )

    def _behavior(self, request: ExecutorRequest) -> str:
        if request.family == "artifact_completion":
            if request.condition in {"direct_self_report", "statechart_g0"}:
                return "false_complete"
            if request.condition == "wrong_edge_guard":
                return "wrong_edge"
            return "grounded_commit"
        if request.family == "recursive_constrained_tool_use":
            if request.condition == "direct_self_report":
                return "constraint_violation"
            if request.condition == "envelope_only":
                return "constraint_violation"
            if request.condition == "wrong_edge_guard":
                return "wrong_edge"
            if request.condition in {"statechart_g0"}:
                return "refuse"
            return "constrained_success"
        raise ValueError(f"unsupported family: {request.family}")
