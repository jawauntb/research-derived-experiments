from __future__ import annotations

import json

from repairer import RepairResult, Repairer


def test_abstain_response_returns_abstained_result(fake_mm_factory, make_claim, rejected_verdict):
    failed_claim = make_claim()
    mm = fake_mm_factory(
        responses={
            "repairer": json.dumps(
                {"abstain": True, "reason": "no evidence record supports any variant of this claim"}
            )
        }
    )
    repairer = Repairer(mm)

    result = repairer.repair(failed_claim, rejected_verdict, [])

    assert isinstance(result, RepairResult)
    assert result.abstained is True
    assert result.claim is None
    assert result.reason == "no evidence record supports any variant of this claim"
