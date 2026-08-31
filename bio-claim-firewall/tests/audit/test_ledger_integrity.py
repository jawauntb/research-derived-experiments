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


def test_clean_ledger_passes_integrity_check(tmp_path: Path):
    path = tmp_path / "ledger.jsonl"
    ledger = AuditLedger(path)
    ledger.append(_claim("11111111-1111-4111-8111-111111111111"), _verdict())
    ledger.append(_claim("22222222-2222-4222-8222-222222222222"), _verdict(verdict="REJECTED", fault_code="BAD_CITATION"))
    ledger.verify_integrity()  # must not raise


def test_hand_edited_character_is_detected_with_correct_line_number(tmp_path: Path):
    path = tmp_path / "ledger.jsonl"
    ledger = AuditLedger(path)
    ledger.append(_claim("11111111-1111-4111-8111-111111111111"), _verdict())
    ledger.append(_claim("22222222-2222-4222-8222-222222222222"), _verdict(verdict="REJECTED", fault_code="BAD_CITATION"))
    ledger.append(_claim("33333333-3333-4333-8333-333333333333"), _verdict())

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3

    # Tamper with a single character deep inside line 2's claim_id, without
    # changing the line's length or JSON validity.
    target = lines[1]
    tampered_char_index = target.index("22222222") + 1
    tampered = target[:tampered_char_index] + "9" + target[tampered_char_index + 1 :]
    assert tampered != target
    lines[1] = tampered
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with pytest.raises(AuditError) as excinfo:
        ledger.verify_integrity()
    assert excinfo.value.code == "LEDGER_TAMPERED"
    assert excinfo.value.details.get("line") == 2


def test_malformed_json_line_is_detected_as_tampered(tmp_path: Path):
    path = tmp_path / "ledger.jsonl"
    ledger = AuditLedger(path)
    ledger.append(_claim(), _verdict())

    with open(path, "a", encoding="utf-8") as f:
        f.write("{not valid json\n")

    with pytest.raises(AuditError) as excinfo:
        ledger.verify_integrity()
    assert excinfo.value.code == "LEDGER_TAMPERED"
    assert excinfo.value.details.get("line") == 2


def test_empty_ledger_passes_integrity_check(tmp_path: Path):
    path = tmp_path / "ledger.jsonl"
    ledger = AuditLedger(path)
    ledger.verify_integrity()  # must not raise on an empty (freshly created) ledger
