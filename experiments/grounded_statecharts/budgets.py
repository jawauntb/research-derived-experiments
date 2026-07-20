"""Matched-budget accounting for grounded live evaluation."""

from __future__ import annotations

from dataclasses import dataclass

from experiments.grounded_statecharts.runtime import digest


@dataclass(frozen=True)
class BudgetSpec:
    """Hard ceilings held fixed inside each paired comparison."""

    max_calls: int
    max_input_tokens: int
    max_output_tokens: int
    max_tool_calls: int
    max_latency_ms: int
    max_cost_usd: float

    def __post_init__(self) -> None:
        for name, value in (
            ("max_calls", self.max_calls),
            ("max_input_tokens", self.max_input_tokens),
            ("max_output_tokens", self.max_output_tokens),
            ("max_tool_calls", self.max_tool_calls),
            ("max_latency_ms", self.max_latency_ms),
        ):
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if self.max_cost_usd < 0:
            raise ValueError("max_cost_usd must be non-negative")

    def to_dict(self) -> dict[str, object]:
        return {
            "max_calls": self.max_calls,
            "max_input_tokens": self.max_input_tokens,
            "max_output_tokens": self.max_output_tokens,
            "max_tool_calls": self.max_tool_calls,
            "max_latency_ms": self.max_latency_ms,
            "max_cost_usd": self.max_cost_usd,
        }

    def digest(self) -> str:
        return digest(self.to_dict())


@dataclass(frozen=True)
class BudgetUsage:
    call_count: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    tool_calls: int = 0
    latency_ms: int = 0
    estimated_cost_usd: float = 0.0

    def __post_init__(self) -> None:
        for name, value in (
            ("call_count", self.call_count),
            ("input_tokens", self.input_tokens),
            ("output_tokens", self.output_tokens),
            ("tool_calls", self.tool_calls),
            ("latency_ms", self.latency_ms),
        ):
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if self.estimated_cost_usd < 0:
            raise ValueError("estimated_cost_usd must be non-negative")

    def to_dict(self) -> dict[str, object]:
        return {
            "call_count": self.call_count,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "tool_calls": self.tool_calls,
            "latency_ms": self.latency_ms,
            "estimated_cost_usd": self.estimated_cost_usd,
        }

    def add(
        self,
        *,
        calls: int = 0,
        input_tokens: int = 0,
        output_tokens: int = 0,
        tool_calls: int = 0,
        latency_ms: int = 0,
        estimated_cost_usd: float = 0.0,
    ) -> BudgetUsage:
        return BudgetUsage(
            call_count=self.call_count + calls,
            input_tokens=self.input_tokens + input_tokens,
            output_tokens=self.output_tokens + output_tokens,
            tool_calls=self.tool_calls + tool_calls,
            latency_ms=self.latency_ms + latency_ms,
            estimated_cost_usd=self.estimated_cost_usd + estimated_cost_usd,
        )


@dataclass(frozen=True)
class BudgetReceipt:
    spec: BudgetSpec
    usage: BudgetUsage
    planned_calls: int
    exhausted: bool
    ok: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "spec": self.spec.to_dict(),
            "usage": self.usage.to_dict(),
            "planned_calls": self.planned_calls,
            "exhausted": self.exhausted,
            "ok": self.ok,
            "budget_digest": self.spec.digest(),
        }


def plan_budget(*, spec: BudgetSpec, planned_calls: int) -> BudgetReceipt:
    """Fail closed before dispatch when the planned call ceiling is too high."""

    if planned_calls < 0:
        raise ValueError("planned_calls must be non-negative")
    exhausted = planned_calls > spec.max_calls
    return BudgetReceipt(
        spec=spec,
        usage=BudgetUsage(),
        planned_calls=planned_calls,
        exhausted=exhausted,
        ok=not exhausted,
    )


def settle_budget(*, spec: BudgetSpec, usage: BudgetUsage, planned_calls: int) -> BudgetReceipt:
    """Compare realized usage against the frozen ceilings."""

    exhausted = any(
        (
            usage.call_count > spec.max_calls,
            usage.input_tokens > spec.max_input_tokens,
            usage.output_tokens > spec.max_output_tokens,
            usage.tool_calls > spec.max_tool_calls,
            usage.latency_ms > spec.max_latency_ms,
            usage.estimated_cost_usd > spec.max_cost_usd,
            planned_calls > spec.max_calls,
        )
    )
    return BudgetReceipt(
        spec=spec,
        usage=usage,
        planned_calls=planned_calls,
        exhausted=exhausted,
        ok=not exhausted,
    )


DEFAULT_PILOT_BUDGET = BudgetSpec(
    max_calls=8,
    max_input_tokens=12_000,
    max_output_tokens=4_000,
    max_tool_calls=12,
    max_latency_ms=120_000,
    max_cost_usd=0.25,
)
