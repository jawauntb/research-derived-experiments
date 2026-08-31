from pathlib import Path

import pytest

from audit import AuditError, AuditLedger


def _claim(claim_id="11111111-1111-4111-8111-111111111111"):
    return {"claim_id": claim_id, "subject": {"id": "HGNC:1097", "label": "BRCA1"}}


def _verdict(**overrides):
    body = {
        "verdict": "ACCEPTED_CONDITIONALLY",
        "snapshot_hashes": {"ontology": "a" * 64},
        "checker_version": "0.1.0",
    }
    body.update(overrides)
    return body


def test_appending_identical_claim_and_verdict_raises_duplicate(tmp_path: Path):
    path = tmp_path / "ledger.jsonl"
    ledger = AuditLedger(path)
    ledger.append(_claim(), _verdict())

    with pytest.raises(AuditError) as excinfo:
        ledger.append(_claim(), _verdict())
    assert excinfo.value.code == "DUPLICATE_VERDICT_ID"

    # No second line was written.
    assert path.read_bytes().count(b"\n") == 1
    assert len(list(ledger.iter_entries())) == 1


def test_same_claim_different_verdict_is_not_a_duplicate(tmp_path: Path):
    # A superseding verdict: same claim, verdict body differs (e.g. new
    # checker_version) -> different verdict_id -> both entries coexist.
    path = tmp_path / "ledger.jsonl"
    ledger = AuditLedger(path)
    ledger.append(_claim(), _verdict(checker_version="0.1.0"))
    ledger.append(_claim(), _verdict(checker_version="0.2.0"))

    entries = list(ledger.iter_entries())
    assert len(entries) == 2
    assert entries[0].verdict_id != entries[1].verdict_id


def test_supersedes_field_produces_new_non_duplicate_entry(tmp_path: Path):
    path = tmp_path / "ledger.jsonl"
    ledger = AuditLedger(path)
    original = ledger.append(_claim(), _verdict())
    corrected = ledger.append(_claim(), _verdict(supersedes=original.verdict_id))

    assert corrected.verdict_id != original.verdict_id
    entries = ledger.find_by_claim_id(_claim()["claim_id"])
    assert len(entries) == 2
    # The old entry is still present, untouched.
    assert entries[0].verdict_id == original.verdict_id
    assert entries[0].verdict.get("supersedes") is None
    assert entries[1].verdict_id == corrected.verdict_id
    assert entries[1].verdict["supersedes"] == original.verdict_id


def test_duplicate_error_message_mentions_verdict_id(tmp_path: Path):
    path = tmp_path / "ledger.jsonl"
    ledger = AuditLedger(path)
    entry = ledger.append(_claim(), _verdict())

    with pytest.raises(AuditError) as excinfo:
        ledger.append(_claim(), _verdict())
    assert entry.verdict_id in str(excinfo.value)
