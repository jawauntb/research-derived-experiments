from __future__ import annotations

import json

from orchestrator import Orchestrator, OrchestratorConfig
from proposer import Proposer
from repairer import Repairer


def test_exhausted_repairs_status_and_trajectory(
    fake_mm_factory, verifier_config, snapshot, rejected_claim, tmp_path
):
    trajectory_path = tmp_path / "trajectories.jsonl"
    mm = fake_mm_factory(
        responses={
            "proposer": json.dumps([rejected_claim]),
            # every repair attempt just re-emits the same still-bad claim
            "repairer": [
                json.dumps({"repaired_claim": rejected_claim, "reason": "attempt 1"}),
                json.dumps({"repaired_claim": rejected_claim, "reason": "attempt 2"}),
            ],
        }
    )
    proposer = Proposer(mm)
    repairer = Repairer(mm)
    config = OrchestratorConfig(max_repair_attempts=2, trajectory_path=trajectory_path)
    orch = Orchestrator(proposer, repairer, verifier_config, snapshot, config)

    result = orch.run("Does BRCA1 increase KRAS?", [])

    assert result.status == "rejected_exhausted"
    # initial verify + one re-verify per repair attempt (capped at 2)
    assert result.attempts == 3
    assert result.final_verdicts[-1]["verdict"] == "REJECTED"
    assert result.final_verdicts[-1]["fault_code"] == "BAD_CITATION"

    repair_calls = [c for c in mm.calls if c["task"] == "repairer"]
    assert len(repair_calls) == 2  # capped at max_repair_attempts, never unbounded

    assert trajectory_path.exists()
    lines = trajectory_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
