"""Append-only JSONL trajectory logging for the proposer/checker/repairer
loop.

`TrajectoryLogger` is the only entry point: `start_trajectory()` ->
repeated `log_attempt()` -> `close_trajectory()` (which durably appends one
JSONL line for the whole trajectory). See `logger.py`'s module docstring
for the MIDAS adaptation this is based on.
"""

from .errors import TrajectoryError
from .logger import TrajectoryLogger
from .types import AttemptRecord

__all__ = ["TrajectoryLogger", "AttemptRecord", "TrajectoryError"]
