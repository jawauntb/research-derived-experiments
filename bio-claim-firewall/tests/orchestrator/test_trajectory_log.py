from __future__ import annotations

import json

from orchestrator import Orchestrator, OrchestratorConfig
from proposer import Proposer
from repairer import Repairer


def test_full_loop_logged_as_one_line_with_records_in_order(
    fake_mm_factory, verifier_config, snapshot, accepted_claim, rejected_claim, tmp_path
):
    trajectory_path = tmp_path / "trajectories.jsonl"
    mm = fake_mm_factory(
        responses={
            "proposer": json.dumps([rejected_claim]),
            "repairer": json.dumps({"repaired_claim": accepted_claim, "reason": "fixed"}),
        }
    )
    proposer = Proposer(mm)
    repairer = Repairer(mm)
    config = OrchestratorConfig(max_repair_attempts=2, trajectory_path=trajectory_path)
    orch = Orchestrator(proposer, repairer, verifier_config, snapshot, config)

    result = orch.run("Does BRCA1 increase KRAS?", [])
    assert result.status == "accepted"

    lines = trajectory_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1  # one JSONL line for the whole trajectory

    record = json.loads(lines[0])
    assert record["trajectory_id"] == result.trajectory_id
    assert record["question"] == "Does BRCA1 increase KRAS?"
    assert record["outcome"]["final_status"] == "accepted"

    stages = [a["stage"] for a in record["attempts"]]
    assert stages == ["propose", "verify", "repair", "verify"]

    propose_record, first_verify, repair_record, second_verify = record["attempts"]

    assert propose_record["verdict"] is None
    assert propose_record["proposed_claim"]["claim_id"] == rejected_claim["claim_id"]
    assert propose_record["provider"] == "fake-provider"
    assert propose_record["prompt_ref"] == "proposer/claim_bundle@v1"

    assert first_verify["verdict"] == "REJECTED"
    assert first_verify["fault_code"] == "BAD_CITATION"
    assert first_verify["reasons"]

    assert repair_record["proposed_claim"]["claim_id"] == accepted_claim["claim_id"]
    assert repair_record["prompt_ref"] == "repairer/claim_repair@v1"
    assert repair_record["note"] == "fixed"

    assert second_verify["verdict"] == "ACCEPTED_CONDITIONALLY"
    assert second_verify["proposed_claim"]["claim_id"] == accepted_claim["claim_id"]

    # attempt_number is strictly increasing across the whole trajectory
    attempt_numbers = [a["attempt_number"] for a in record["attempts"]]
    assert attempt_numbers == sorted(attempt_numbers)
    assert len(set(attempt_numbers)) == len(attempt_numbers)
