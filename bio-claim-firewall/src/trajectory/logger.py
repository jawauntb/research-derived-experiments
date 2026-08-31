"""`TrajectoryLogger`: append-only JSONL logging of every proposer/checker/
repairer attempt in an orchestrator run.

# MIDAS ATTRIBUTION: adapted from MIDAS `src/pipeline/trajectory.py`'s
# `TrajectoryLogger` (`start_trajectory` / `log_attempt` / `close_trajectory`
# lifecycle, one JSONL line per trajectory holding an ordered `attempts`
# list). Field renames and additions are documented in `types.py`. The
# write mechanism is changed from MIDAS's own `open(path, "a")` to the
# `os.open(..., O_CREAT | O_APPEND | O_WRONLY)` + `os.write` + `os.close`
# pattern already used by this project's `src/audit/ledger.py` (real
# O_APPEND at the OS level, matching this task's explicit "jsonl file
# opened O_APPEND" requirement, and consistent with the rest of the
# codebase's append-only-ledger style).
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .types import AttemptRecord, TrajectoryRecord


class TrajectoryLogger:
    """Logs bio-claim-firewall orchestrator trajectories to a JSONL file.

    Usage:
        logger = TrajectoryLogger("trajectories/bio_claim_trajectories.jsonl")
        tid = logger.start_trajectory(question)
        logger.log_attempt(tid, AttemptRecord(...))
        logger.close_trajectory(tid, final_status="accepted")

    `log_attempt`/`close_trajectory` on an unknown `trajectory_id` are
    silent no-ops (mirrors MIDAS): a logging-layer bug must never crash the
    orchestration it is trying to observe.
    """

    def __init__(self, log_path: str | Path) -> None:
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._active: dict[str, TrajectoryRecord] = {}

    def start_trajectory(self, question: str) -> str:
        tid = str(uuid.uuid4())
        self._active[tid] = TrajectoryRecord(
            trajectory_id=tid,
            timestamp=datetime.now(timezone.utc).isoformat(),
            question=question,
        )
        return tid

    def log_attempt(self, trajectory_id: str, record: AttemptRecord) -> None:
        traj = self._active.get(trajectory_id)
        if traj is None:
            return
        traj.attempts.append(record)

    def close_trajectory(self, trajectory_id: str, final_status: str) -> None:
        """Finalize and durably append the trajectory to disk.

        ALWAYS pops the trajectory out of `_active` (even if the write
        itself somehow fails) -- a logger must never leak state across
        orchestrator runs that reuse the same `TrajectoryLogger` instance.
        """
        traj = self._active.pop(trajectory_id, None)
        if traj is None:
            return

        traj.final_status = final_status
        traj.attempt_count = len(traj.attempts)

        record: dict[str, Any] = {
            "trajectory_id": traj.trajectory_id,
            "timestamp": traj.timestamp,
            "question": traj.question,
            "attempts": [asdict(a) for a in traj.attempts],
            "outcome": {
                "final_status": traj.final_status,
                "attempt_count": traj.attempt_count,
            },
        }

        line = json.dumps(record)
        fd = os.open(str(self.log_path), os.O_CREAT | os.O_APPEND | os.O_WRONLY, 0o644)
        try:
            os.write(fd, (line + "\n").encode("utf-8"))
        finally:
            os.close(fd)

    def read_trajectories(self, n: int = 50) -> list[dict[str, Any]]:
        """Return the N most recent trajectories, newest first."""
        if not self.log_path.exists():
            return []
        with open(self.log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        records: list[dict[str, Any]] = []
        for line in lines[-n:]:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return list(reversed(records))
