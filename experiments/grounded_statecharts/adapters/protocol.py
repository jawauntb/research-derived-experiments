"""Provider-neutral executor contract for grounded live evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from experiments.grounded_statecharts.budgets import BudgetUsage


@dataclass(frozen=True)
class ExecutorRequest:
    """Normalized request issued by the live evaluation runner."""

    episode_id: str
    task_id: str
    family: str
    condition: str
    instruction: str
    seed: int
    step_index: int

    def __post_init__(self) -> None:
        for name, value in (
            ("episode_id", self.episode_id),
            ("task_id", self.task_id),
            ("family", self.family),
            ("condition", self.condition),
            ("instruction", self.instruction),
        ):
            if not isinstance(value, str) or not value:
                raise ValueError(f"{name} must be a non-empty string")
        if self.seed < 0 or self.step_index < 0:
            raise ValueError("seed and step_index must be non-negative")


@dataclass(frozen=True)
class ExecutorResponse:
    """Normalized provider response used by the evaluation runner.

    Raw provider material may exist only on the private `raw` field and must
    never enter public result rows.
    """

    text: str
    action: str
    claimed_complete: bool
    artifact_created: bool
    capability_used: tuple[str, ...]
    usage: BudgetUsage
    raw: dict[str, object] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.text, str) or not self.text:
            raise ValueError("text must be a non-empty string")
        if not isinstance(self.action, str) or not self.action:
            raise ValueError("action must be a non-empty string")
        if not isinstance(self.claimed_complete, bool):
            raise ValueError("claimed_complete must be boolean")
        if not isinstance(self.artifact_created, bool):
            raise ValueError("artifact_created must be boolean")
        if not all(isinstance(item, str) and item for item in self.capability_used):
            raise ValueError("capability_used entries must be non-empty strings")


class ProviderExecutor(Protocol):
    @property
    def adapter_id(self) -> str: ...

    @property
    def provider_id(self) -> str: ...

    @property
    def model_id(self) -> str: ...

    def complete(self, request: ExecutorRequest) -> ExecutorResponse:
        """Return one normalized step response."""
