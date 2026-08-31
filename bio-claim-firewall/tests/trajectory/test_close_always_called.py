"""`close_trajectory` must always fire, even if the orchestrator raises
internally (which it shouldn't, but the loop is defensively wrapped in
`try/finally` -- see `src/orchestrator/orchestrator.py`'s `run()`). This
file tests the guarantee at both layers: the logger itself never leaks an
`_active` entry, and (via a minimal stand-in loop shaped like
`Orchestrator.run()`) a `try/finally` around it survives an unexpected
exception.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from trajectory import AttemptRecord, TrajectoryLogger


def test_close_trajectory_pops_active_entry_even_on_repeated_calls(tmp_path: Path):
    logger = TrajectoryLogger(tmp_path / "trajectories.jsonl")
    tid = logger.start_trajectory("q")
    assert tid in logger._active

    logger.close_trajectory(tid, final_status="accepted")
    assert tid not in logger._active

    # A second close on the same (now-unknown) id is a silent no-op, never
    # a crash and never a second JSONL line.
    logger.close_trajectory(tid, final_status="accepted")
    lines = (tmp_path / "trajectories.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1


def test_try_finally_around_the_loop_still_closes_on_unexpected_exception(tmp_path: Path):
    """Mirrors the exact shape `Orchestrator.run()` uses: `start_trajectory`,
    then a `try/finally` around the loop body where `close_trajectory` is
    the only thing in `finally`. If the loop body raises something
    `Orchestrator` did not anticipate, the trajectory must still close.
    """
    logger = TrajectoryLogger(tmp_path / "trajectories.jsonl")
    tid = logger.start_trajectory("q")

    class BoomError(RuntimeError):
        pass

    with pytest.raises(BoomError):
        try:
            logger.log_attempt(tid, AttemptRecord(attempt_number=1, stage="propose"))
            raise BoomError("unexpected failure deep in the loop")
        finally:
            logger.close_trajectory(tid, final_status="pending")

    assert tid not in logger._active
    lines = (tmp_path / "trajectories.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    import json

    record = json.loads(lines[0])
    assert record["outcome"]["final_status"] == "pending"
    assert len(record["attempts"]) == 1
