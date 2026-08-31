# Sourced from MIDAS with permission (see bio-claim-firewall/PROVENANCE.md), adapted for
# bio-claim-firewall — this exact class does not exist upstream.
"""Domain error for the model_manager package.

Distinct from:
  - configuration load errors (ValueError / FileNotFoundError raised by
    ModelManager._load_config, mirroring MIDAS's manager.py validation), and
  - provider-transport errors (ModelError / ModelTimeout / ModelRetryable in
    providers/base.py, raised by a provider's own .chat()).

ModelManagerError is for model_manager-level faults that are neither of
those: currently, a caller asking the manager to dispatch a task that is
deliberately not a model call. `checker` is a deterministic rule engine
(src/checker/, not part of this package) — per the fault-split invariant in
PHASE_4_PLAN.md, ModelManager.call(task="checker", ...) must refuse rather
than silently no-op or dispatch to a provider.
"""
from __future__ import annotations

from typing import Optional


class ModelManagerError(Exception):
    """Raised for model_manager-level faults.

    Args:
        code: a short, stable, machine-checkable identifier, e.g.
            "checker_is_not_a_model_task". Tests assert on `.code`.
        stage: where in the call lifecycle this happened (e.g. "dispatch").
        provider: the provider name involved, if any.
        task: the task name involved, if any.
        message: human-readable message. Defaults to `code` if omitted.
    """

    def __init__(
        self,
        code: str,
        *,
        stage: Optional[str] = None,
        provider: Optional[str] = None,
        task: Optional[str] = None,
        message: Optional[str] = None,
    ) -> None:
        self.code = code
        self.stage = stage
        self.provider = provider
        self.task = task
        super().__init__(message or code)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return (
            f"ModelManagerError(code={self.code!r}, stage={self.stage!r}, "
            f"provider={self.provider!r}, task={self.task!r})"
        )
