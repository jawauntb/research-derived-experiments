from __future__ import annotations

import json

from orchestrator import Orchestrator, OrchestratorConfig
from proposer import Proposer
from repairer import Repairer
from verifier import VerifierConfig


def test_checker_error_halts_the_run(fake_mm_factory, snapshot, accepted_claim, tmp_path):
    """A broken `schema_dir` makes `verify()`'s own JSON-Schema-loading
    stage raise, which `verify()` fails closed into a `CHECKER_ERROR`
    verdict (never a `REJECTED_*` one -- spec/non_goals.md's first
    Prohibited move). The orchestrator must halt immediately: no repairer
    call, no further claims processed.
    """
    mm = fake_mm_factory(responses={"proposer": json.dumps([accepted_claim])})
    proposer = Proposer(mm)
    repairer = Repairer(mm)
    broken_verifier_config = VerifierConfig(
        checker_version="0.1.0", schema_dir=tmp_path / "does_not_exist"
    )
    config = OrchestratorConfig(max_repair_attempts=2, abort_on_checker_error=True)
    orch = Orchestrator(proposer, repairer, broken_verifier_config, snapshot, config)

    result = orch.run("Does BRCA1 increase KRAS?", [])

    assert result.status == "checker_error"
    assert result.final_verdicts[0]["verdict"] == "CHECKER_ERROR"
    assert result.final_verdicts[0]["checker_error"]["stage"] == "load_snapshot"

    repair_calls = [c for c in mm.calls if c["task"] == "repairer"]
    assert repair_calls == []
    # exactly the one proposer call and no other model call of any kind
    assert len(mm.calls) == 1


def test_checker_error_skips_claim_when_not_aborting(
    fake_mm_factory, snapshot, accepted_claim, tmp_path
):
    """`abort_on_checker_error=False` skips the claim instead of halting
    the whole run -- still no repairer call for a CHECKER_ERROR verdict
    (it is never treated as a "proposer error" to repair).
    """
    mm = fake_mm_factory(responses={"proposer": json.dumps([accepted_claim])})
    proposer = Proposer(mm)
    repairer = Repairer(mm)
    broken_verifier_config = VerifierConfig(
        checker_version="0.1.0", schema_dir=tmp_path / "does_not_exist"
    )
    config = OrchestratorConfig(max_repair_attempts=2, abort_on_checker_error=False)
    orch = Orchestrator(proposer, repairer, broken_verifier_config, snapshot, config)

    result = orch.run("Does BRCA1 increase KRAS?", [])

    assert result.status == "checker_error"
    assert result.final_verdicts[0]["verdict"] == "CHECKER_ERROR"
    repair_calls = [c for c in mm.calls if c["task"] == "repairer"]
    assert repair_calls == []
