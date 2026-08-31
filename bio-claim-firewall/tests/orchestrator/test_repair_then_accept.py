from __future__ import annotations

import json

from orchestrator import Orchestrator, OrchestratorConfig
from proposer import Proposer
from repairer import Repairer


def test_repair_then_accept(fake_mm_factory, verifier_config, snapshot, accepted_claim, rejected_claim):
    mm = fake_mm_factory(
        responses={
            "proposer": json.dumps([rejected_claim]),
            "repairer": json.dumps({"repaired_claim": accepted_claim, "reason": "fixed the bad citation"}),
        }
    )
    proposer = Proposer(mm)
    repairer = Repairer(mm)
    config = OrchestratorConfig(max_repair_attempts=2)
    orch = Orchestrator(proposer, repairer, verifier_config, snapshot, config)

    result = orch.run("Does BRCA1 increase KRAS?", [])

    assert result.status == "accepted"
    assert result.attempts == 2
    assert result.final_verdicts[-1]["verdict"] == "ACCEPTED_CONDITIONALLY"

    repair_calls = [c for c in mm.calls if c["task"] == "repairer"]
    assert len(repair_calls) == 1
