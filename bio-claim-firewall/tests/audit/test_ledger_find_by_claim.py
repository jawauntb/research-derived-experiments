from pathlib import Path

from audit import AuditLedger

CLAIM_ID = "11111111-1111-4111-8111-111111111111"
OTHER_CLAIM_ID = "22222222-2222-4222-8222-222222222222"


def _claim(claim_id=CLAIM_ID):
    return {"claim_id": claim_id, "subject": {"id": "HGNC:1097", "label": "BRCA1"}}


def _verdict(**overrides):
    body = {
        "verdict": "ACCEPTED_CONDITIONALLY",
        "snapshot_hashes": {"ontology": "a" * 64},
        "checker_version": "0.1.0",
    }
    body.update(overrides)
    return body


def test_two_superseding_verdicts_both_returned_in_order(tmp_path: Path):
    path = tmp_path / "ledger.jsonl"
    ledger = AuditLedger(path)

    # An unrelated claim, to make sure filtering actually filters.
    ledger.append(_claim(OTHER_CLAIM_ID), _verdict())

    first = ledger.append(_claim(), _verdict(verdict="REJECTED", fault_code="BAD_CITATION"))
    second = ledger.append(_claim(), _verdict(supersedes=first.verdict_id, verdict="ACCEPTED_CONDITIONALLY"))

    results = ledger.find_by_claim_id(CLAIM_ID)
    assert len(results) == 2
    assert [r.verdict_id for r in results] == [first.verdict_id, second.verdict_id]
    assert results[0].verdict["verdict"] == "REJECTED"
    assert results[1].verdict["verdict"] == "ACCEPTED_CONDITIONALLY"
    assert results[1].verdict["supersedes"] == first.verdict_id


def test_unknown_claim_id_returns_empty_list(tmp_path: Path):
    path = tmp_path / "ledger.jsonl"
    ledger = AuditLedger(path)
    ledger.append(_claim(), _verdict())
    assert ledger.find_by_claim_id("no-such-claim") == []


def test_empty_ledger_returns_empty_list(tmp_path: Path):
    path = tmp_path / "ledger.jsonl"
    ledger = AuditLedger(path)
    assert ledger.find_by_claim_id(CLAIM_ID) == []
