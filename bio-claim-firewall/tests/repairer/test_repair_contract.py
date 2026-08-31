from __future__ import annotations

import json

import pytest

from repairer import RepairerError, Repairer


def test_non_json_response_raises_contract_violated(fake_mm_factory, make_claim, rejected_verdict):
    mm = fake_mm_factory(responses={"repairer": "sure, let me think about that"})
    repairer = Repairer(mm)

    with pytest.raises(RepairerError) as exc_info:
        repairer.repair(make_claim(), rejected_verdict, [])

    assert exc_info.value.code == "contract_violated"


def test_json_array_instead_of_object_raises_contract_violated(fake_mm_factory, make_claim, rejected_verdict):
    mm = fake_mm_factory(responses={"repairer": json.dumps([{"repaired_claim": make_claim()}])})
    repairer = Repairer(mm)

    with pytest.raises(RepairerError) as exc_info:
        repairer.repair(make_claim(), rejected_verdict, [])

    assert exc_info.value.code == "contract_violated"


def test_neither_repaired_claim_nor_abstain_raises_contract_violated(
    fake_mm_factory, make_claim, rejected_verdict
):
    mm = fake_mm_factory(responses={"repairer": json.dumps({"unrelated_key": True})})
    repairer = Repairer(mm)

    with pytest.raises(RepairerError) as exc_info:
        repairer.repair(make_claim(), rejected_verdict, [])

    assert exc_info.value.code == "contract_violated"


def test_both_repaired_claim_and_abstain_raises_contract_violated(
    fake_mm_factory, make_claim, rejected_verdict
):
    mm = fake_mm_factory(
        responses={
            "repairer": json.dumps({"repaired_claim": make_claim(), "abstain": True, "reason": "confused"})
        }
    )
    repairer = Repairer(mm)

    with pytest.raises(RepairerError) as exc_info:
        repairer.repair(make_claim(), rejected_verdict, [])

    assert exc_info.value.code == "contract_violated"


def test_repaired_claim_missing_required_field_raises_contract_violated(
    fake_mm_factory, make_claim, rejected_verdict
):
    incomplete = make_claim()
    del incomplete["polarity"]
    mm = fake_mm_factory(responses={"repairer": json.dumps({"repaired_claim": incomplete})})
    repairer = Repairer(mm)

    with pytest.raises(RepairerError) as exc_info:
        repairer.repair(make_claim(), rejected_verdict, [])

    assert exc_info.value.code == "contract_violated"
    assert "polarity" in exc_info.value.message


def test_abstain_false_string_raises_contract_violated(fake_mm_factory, make_claim, rejected_verdict):
    mm = fake_mm_factory(responses={"repairer": json.dumps({"abstain": "yes", "reason": "why not"})})
    repairer = Repairer(mm)

    with pytest.raises(RepairerError) as exc_info:
        repairer.repair(make_claim(), rejected_verdict, [])

    assert exc_info.value.code == "contract_violated"
