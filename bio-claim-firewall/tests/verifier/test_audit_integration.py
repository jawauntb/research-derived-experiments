"""Audit-ledger integration: verify() durably appends, and a duplicate
re-verify of the exact same claim fails closed rather than silently
re-recording (or silently returning a stale-looking success).

# VERIFIER-DECISION (documented tradeoff): `verify()` is NOT idempotent
# when an `AuditLedger` is attached -- re-verifying the exact same claim
# against the exact same snapshot produces the exact same `verdict_id`
# (by construction; see test_verdict_id_stability.py), and the ledger's
# own `AuditLedger.append` treats a second append of that same id as
# `AuditError("DUPLICATE_VERDICT_ID")`, which `verify()` catches and
# reports as `CHECKER_ERROR` rather than silently returning the original
# (already-recorded) verdict a second time. An idempotent re-verify (find
# the existing ledger entry and return it unchanged) might be desirable
# eventually, but that's a product decision this task does not make --
# forcing the duplicate to surface as an explicit checker error means an
# upstream caller has to notice and decide whether it actually wanted to
# re-verify (e.g. because the claim legitimately changed) rather than the
# verifier quietly picking a policy on its behalf.
"""

from __future__ import annotations

from pathlib import Path

from audit import AuditLedger
from verifier import VerifierConfig, verify


def _spec_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "spec"


def test_verify_appends_one_matching_entry(bundle, load_claim, tmp_path, assert_verdict_matches_schema):
    ledger = AuditLedger(tmp_path / "ledger.jsonl")
    config = VerifierConfig(checker_version="0.1.0", schema_dir=_spec_dir(), audit_ledger=ledger)

    claim = load_claim("ACCEPTED_CONDITIONALLY__example.json")
    verdict = verify(claim, bundle, config)
    assert_verdict_matches_schema(verdict)
    assert verdict["verdict"] == "ACCEPTED_CONDITIONALLY"

    entries = ledger.find_by_claim_id(claim["claim_id"])
    assert len(entries) == 1
    assert entries[0].verdict_id == verdict["verdict_id"]
    assert entries[0].claim_id == claim["claim_id"]
    assert entries[0].claim == claim


def test_reverifying_same_claim_is_a_checker_error(bundle, load_claim, tmp_path, assert_verdict_matches_schema):
    ledger = AuditLedger(tmp_path / "ledger.jsonl")
    config = VerifierConfig(checker_version="0.1.0", schema_dir=_spec_dir(), audit_ledger=ledger)

    claim = load_claim("ACCEPTED_CONDITIONALLY__example.json")
    first = verify(claim, bundle, config)
    assert first["verdict"] == "ACCEPTED_CONDITIONALLY"

    second = verify(claim, bundle, config)
    assert_verdict_matches_schema(second)
    assert second["verdict"] == "CHECKER_ERROR"
    assert second["checker_error"]["exception_class"] == "AuditError"

    # Still exactly one entry -- the failed duplicate append wrote nothing.
    entries = ledger.find_by_claim_id(claim["claim_id"])
    assert len(entries) == 1
    assert entries[0].verdict_id == first["verdict_id"]


def test_no_ledger_means_no_append_attempted(bundle, load_claim):
    config = VerifierConfig(checker_version="0.1.0", schema_dir=_spec_dir(), audit_ledger=None)
    claim = load_claim("ACCEPTED_CONDITIONALLY__example.json")
    verdict = verify(claim, bundle, config)
    assert verdict["verdict"] == "ACCEPTED_CONDITIONALLY"
