"""TrajectoryError: the one exception type owned by src/trajectory."""

from __future__ import annotations

from typing import Any


class TrajectoryError(Exception):
    """Raised on a trajectory-logging failure (e.g. a write to the JSONL
    file itself fails). Never raised for "unknown trajectory_id" -- like
    MIDAS's `TrajectoryLogger`, `log_attempt`/`close_trajectory` on an
    unknown id is a silent no-op (defensive: an orchestrator bug should
    never crash the run it's trying to log).
    """

    def __init__(self, code: str, message: str = "", **details: Any) -> None:
        self.code = code
        self.message = message or code
        self.details = details
        super().__init__(f"[{code}] {self.message}")
