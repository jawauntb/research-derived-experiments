from __future__ import annotations

import json
import uuid

import pytest

from proposer import ClaimBundle, Proposer, ProposerError


def test_valid_json_array_parses(fake_mm_factory, valid_claim):
    mm = fake_mm_factory(responses={"proposer": json.dumps([valid_claim])})
    proposer = Proposer(mm)

    bundle = proposer.propose("Does BRCA1 increase KRAS?", [])

    assert isinstance(bundle, ClaimBundle)
    assert len(bundle.claims) == 1
    assert bundle.claims[0] == valid_claim
    assert bundle.provider == "fake-provider"
    assert bundle.prompt_version == "v1"
    assert mm.calls[0]["task"] == "proposer"


def test_multiple_claims_parse(fake_mm_factory, make_claim):
    claim_a = make_claim(claim_id=str(uuid.uuid4()))
    claim_b = make_claim(claim_id=str(uuid.uuid4()))
    mm = fake_mm_factory(responses={"proposer": json.dumps([claim_a, claim_b])})
    proposer = Proposer(mm)

    bundle = proposer.propose("q", [])

    assert len(bundle.claims) == 2


def test_prose_outside_array_raises_contract_violated(fake_mm_factory, valid_claim):
    prose_wrapped = "Sure, here are the claims:\n" + json.dumps([valid_claim])
    mm = fake_mm_factory(responses={"proposer": prose_wrapped})
    proposer = Proposer(mm)

    with pytest.raises(ProposerError) as exc_info:
        proposer.propose("q", [])

    assert exc_info.value.code == "contract_violated"


def test_non_json_response_raises_contract_violated(fake_mm_factory):
    mm = fake_mm_factory(responses={"proposer": "not json at all"})
    proposer = Proposer(mm)

    with pytest.raises(ProposerError) as exc_info:
        proposer.propose("q", [])

    assert exc_info.value.code == "contract_violated"


def test_json_object_instead_of_array_raises_contract_violated(fake_mm_factory, valid_claim):
    mm = fake_mm_factory(responses={"proposer": json.dumps(valid_claim)})
    proposer = Proposer(mm)

    with pytest.raises(ProposerError) as exc_info:
        proposer.propose("q", [])

    assert exc_info.value.code == "contract_violated"


@pytest.mark.parametrize(
    "missing_field",
    ["subject", "relation", "object", "polarity", "species", "evidence_ids", "confidence_language"],
)
def test_missing_required_field_raises_contract_violated(fake_mm_factory, make_claim, missing_field):
    bad_claim = make_claim()
    del bad_claim[missing_field]
    mm = fake_mm_factory(responses={"proposer": json.dumps([bad_claim])})
    proposer = Proposer(mm)

    with pytest.raises(ProposerError) as exc_info:
        proposer.propose("q", [])

    assert exc_info.value.code == "contract_violated"
    assert missing_field in exc_info.value.message


def test_non_uuid_claim_id_is_filled_in(fake_mm_factory, make_claim):
    bad_claim = make_claim(claim_id="not-a-uuid-at-all")
    mm = fake_mm_factory(responses={"proposer": json.dumps([bad_claim])})
    proposer = Proposer(mm)

    bundle = proposer.propose("Does BRCA1 increase KRAS?", [])

    filled_id = bundle.claims[0]["claim_id"]
    assert filled_id != "not-a-uuid-at-all"
    uuid.UUID(filled_id)  # does not raise


def test_missing_claim_id_key_is_a_contract_error(fake_mm_factory, make_claim):
    bad_claim = make_claim()
    del bad_claim["claim_id"]
    mm = fake_mm_factory(responses={"proposer": json.dumps([bad_claim])})
    proposer = Proposer(mm)

    with pytest.raises(ProposerError) as exc_info:
        proposer.propose("q", [])

    assert exc_info.value.code == "contract_violated"


def test_valid_uuid_claim_id_is_preserved(fake_mm_factory, valid_claim):
    mm = fake_mm_factory(responses={"proposer": json.dumps([valid_claim])})
    proposer = Proposer(mm)

    bundle = proposer.propose("q", [])

    assert bundle.claims[0]["claim_id"] == valid_claim["claim_id"]
