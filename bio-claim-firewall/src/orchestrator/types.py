"""`OrchestratorConfig`/`OrchestratorResult`: the orchestrator's public
configuration and return types.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

Status = Literal["accepted", "abstained", "rejected_exhausted", "checker_error"]


@dataclass(frozen=True, slots=True)
class OrchestratorConfig:
    """Configuration for one `Orchestrator.run()` call.

    Attributes:
        max_repair_attempts: hard cap on repair->re-verify cycles per
            claim. NEVER unbounded (spec/non_goals.md's "Auto-repair loops
            with no cap" prohibited move).
        trajectory_path: if set, every attempt in the run is durably
            logged as one JSONL line to this path via `TrajectoryLogger`.
            `None` (the default) disables trajectory logging entirely.
        abort_on_checker_error: if `True` (the default), a `CHECKER_ERROR`
            verdict for any claim immediately halts the whole run
            (status=`"checker_error"`, no further proposer/repairer/verify
            calls for any remaining claim in the bundle) -- fail-closed.
            If `False`, that claim is skipped (its `CHECKER_ERROR` verdict
            is still recorded in `final_verdicts`) and the loop continues
            to the next claim.
    """

    max_repair_attempts: int = 2
    trajectory_path: Path | None = None
    abort_on_checker_error: bool = True

    def __post_init__(self) -> None:
        if self.max_repair_attempts < 0:
            raise ValueError("max_repair_attempts must be >= 0")


@dataclass(frozen=True, slots=True)
class OrchestratorResult:
    """The outcome of one `Orchestrator.run()` call.

    Attributes:
        final_verdicts: one verdict dict per claim the loop actually
            attempted, in bundle order -- the LAST verdict computed for
            that claim (i.e. after any repair) wins. Never rewritten after
            the fact (spec/non_goals.md's "Post-hoc rewriting of a
            verdict" prohibited move); each entry is exactly what
            `verify()` returned for whichever claim version was last
            checked.
        trajectory_id: the id of the JSONL trajectory record for this run
            (present even when `trajectory_path` was `None` -- in that
            case it is still a fresh uuid4, just never written to disk).
        attempts: total number of `verify()` calls made across the whole
            run (initial checks + every repair-driven re-verification).
            Does NOT count `propose()`/`repair()` model calls themselves.
        status: coarse run-level summary. See `orchestrator.py` for the
            per-claim -> aggregate mapping, including the
            PHASE4B-DECISION on how `INCONCLUSIVE` verdicts and
            multi-claim bundles are folded into this closed four-value
            enum.
    """

    final_verdicts: tuple[dict, ...]
    trajectory_id: str
    attempts: int
    status: Status
