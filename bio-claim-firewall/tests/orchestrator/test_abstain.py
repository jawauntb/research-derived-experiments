from __future__ import annotations

import json

from orchestrator import Orchestrator, OrchestratorConfig
from proposer import Proposer
from repairer import Repairer


def test_repairer_abstain_stops_the_repair_loop(
    fake_mm_factory, verifier_config, snapshot, rejected_claim
):
    mm = fake_mm_factory(
        responses={
            "proposer": json.dumps([rejected_claim]),
            "repairer": json.dumps({"abstain": True, "reason": "no supporting evidence exists"}),
        }
    )
    proposer = Proposer(mm)
    repairer = Repairer(mm)
    config = OrchestratorConfig(max_repair_attempts=2)
    orch = Orchestrator(proposer, repairer, verifier_config, snapshot, config)

    result = orch.run("Does BRCA1 increase KRAS?", [])

    assert result.status == "abstained"
    # the abstain produced no repaired claim, so no re-verify call happened
    assert result.attempts == 1
    assert result.final_verdicts[-1]["verdict"] == "REJECTED"

    repair_calls = [c for c in mm.calls if c["task"] == "repairer"]
    assert len(repair_calls) == 1  # stopped immediately, never retried after an abstain
