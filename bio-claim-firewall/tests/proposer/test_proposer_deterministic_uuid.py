from __future__ import annotations

import json
import uuid

from proposer import Proposer


def _propose_with_bad_claim_id(fake_mm_factory, question: str, claim: dict) -> str:
    bad_claim = dict(claim)
    bad_claim["claim_id"] = "definitely-not-a-uuid"
    mm = fake_mm_factory(responses={"proposer": json.dumps([bad_claim])})
    proposer = Proposer(mm)
    bundle = proposer.propose(question, [])
    return bundle.claims[0]["claim_id"]


def test_same_question_subject_relation_object_evidence_yields_same_claim_id(
    fake_mm_factory, valid_claim
):
    question = "Does BRCA1 increase KRAS in CRISPRi_screen contexts?"

    first = _propose_with_bad_claim_id(fake_mm_factory, question, valid_claim)
    second = _propose_with_bad_claim_id(fake_mm_factory, question, valid_claim)

    uuid.UUID(first)
    uuid.UUID(second)
    assert first == second


def test_different_question_yields_different_claim_id(fake_mm_factory, valid_claim):
    first = _propose_with_bad_claim_id(fake_mm_factory, "Question A?", valid_claim)
    second = _propose_with_bad_claim_id(fake_mm_factory, "Question B?", valid_claim)

    assert first != second


def test_different_evidence_ids_yields_different_claim_id(fake_mm_factory, valid_claim):
    question = "Does BRCA1 increase KRAS?"
    claim_a = dict(valid_claim, evidence_ids=["perturbseq_v_test:aaaa"])
    claim_b = dict(valid_claim, evidence_ids=["perturbseq_v_test:bbbb"])

    first = _propose_with_bad_claim_id(fake_mm_factory, question, claim_a)
    second = _propose_with_bad_claim_id(fake_mm_factory, question, claim_b)

    assert first != second
