from __future__ import annotations

import json

from repairer import RepairResult, Repairer


def test_repaired_claim_returns_result_with_claim(
    fake_mm_factory, make_claim, rejected_verdict
):
    failed_claim = make_claim(evidence_ids=["perturbseq_v_test:0000000000000000"])
    fixed_claim = make_claim(evidence_ids=["perturbseq_v_test:fc1d7ea4dd7c21a7"])
    mm = fake_mm_factory(
        responses={"repairer": json.dumps({"repaired_claim": fixed_claim, "reason": "swapped the bad citation"})}
    )
    repairer = Repairer(mm)

    result = repairer.repair(failed_claim, rejected_verdict, [])

    assert isinstance(result, RepairResult)
    assert result.abstained is False
    assert result.claim == fixed_claim
    assert result.reason == "swapped the bad citation"
    assert mm.calls[0]["task"] == "repairer"


def test_repaired_claim_without_reason_field_defaults_empty(
    fake_mm_factory, make_claim, rejected_verdict
):
    failed_claim = make_claim()
    fixed_claim = make_claim(evidence_ids=["perturbseq_v_test:fc1d7ea4dd7c21a7"])
    mm = fake_mm_factory(responses={"repairer": json.dumps({"repaired_claim": fixed_claim})})
    repairer = Repairer(mm)

    result = repairer.repair(failed_claim, rejected_verdict, [])

    assert result.claim == fixed_claim
    assert result.reason == ""
