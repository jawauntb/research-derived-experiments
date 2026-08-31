from __future__ import annotations

import json

from orchestrator import Orchestrator, OrchestratorConfig
from proposer import Proposer
from repairer import Repairer


def test_accept_first_try_status_and_attempts(fake_mm_factory, verifier_config, snapshot, accepted_claim):
    mm = fake_mm_factory(responses={"proposer": json.dumps([accepted_claim])})
    proposer = Proposer(mm)
    repairer = Repairer(mm)
    config = OrchestratorConfig(max_repair_attempts=2)
    orch = Orchestrator(proposer, repairer, verifier_config, snapshot, config)

    result = orch.run("Does BRCA1 increase KRAS?", [])

    assert result.status == "accepted"
    assert result.attempts == 1
    assert len(result.final_verdicts) == 1
    assert result.final_verdicts[0]["verdict"] == "ACCEPTED_CONDITIONALLY"

    repair_calls = [c for c in mm.calls if c["task"] == "repairer"]
    assert repair_calls == []

    propose_calls = [c for c in mm.calls if c["task"] == "proposer"]
    assert len(propose_calls) == 1
