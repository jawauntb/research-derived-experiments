from __future__ import annotations

import json
import os
from pathlib import Path

from trajectory import AttemptRecord, TrajectoryLogger


def test_jsonl_file_opened_o_append(tmp_path: Path, monkeypatch):
    """`close_trajectory` writes via `os.open(..., O_CREAT | O_APPEND | ...)`
    -- assert the real O_APPEND flag is actually passed, not just that the
    resulting file happens to grow (mode "a" alone wouldn't prove this).
    """
    log_path = tmp_path / "trajectories.jsonl"
    logger = TrajectoryLogger(log_path)

    seen_flags: list[int] = []
    real_open = os.open

    def spy_open(path, flags, *args, **kwargs):
        if str(path) == str(log_path):
            seen_flags.append(flags)
        return real_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", spy_open)

    tid = logger.start_trajectory("does BRCA1 increase KRAS?")
    logger.log_attempt(tid, AttemptRecord(attempt_number=1, stage="propose"))
    logger.close_trajectory(tid, final_status="accepted")

    assert seen_flags, "expected os.open to be called against the log path"
    for flags in seen_flags:
        assert flags & os.O_APPEND, f"O_APPEND not set (flags={flags!r})"
        assert flags & os.O_CREAT, f"O_CREAT not set (flags={flags!r})"


def test_multiple_writes_preserved_in_order(tmp_path: Path):
    log_path = tmp_path / "trajectories.jsonl"
    logger = TrajectoryLogger(log_path)

    trajectory_ids = []
    for i in range(5):
        tid = logger.start_trajectory(f"question {i}")
        logger.log_attempt(tid, AttemptRecord(attempt_number=1, stage="propose", note=f"attempt-{i}"))
        logger.close_trajectory(tid, final_status="accepted")
        trajectory_ids.append(tid)

    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 5

    records = [json.loads(line) for line in lines]
    for i, record in enumerate(records):
        assert record["trajectory_id"] == trajectory_ids[i]
        assert record["question"] == f"question {i}"
        assert record["attempts"][0]["note"] == f"attempt-{i}"


def test_close_trajectory_appends_without_truncating_existing_content(tmp_path: Path):
    log_path = tmp_path / "trajectories.jsonl"
    log_path.write_text('{"pre_existing": true}\n', encoding="utf-8")

    logger = TrajectoryLogger(log_path)
    tid = logger.start_trajectory("q")
    logger.close_trajectory(tid, final_status="accepted")

    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0]) == {"pre_existing": True}
