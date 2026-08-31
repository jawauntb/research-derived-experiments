"""Fault-injection: monkey-patch each pipeline stage to raise, confirm the
returned verdict is CHECKER_ERROR with the expected `checker_error.stage`
and `exception_class`.

See `verifier/verify.py`'s own VERIFIER-DECISION docstring for the mapping
between this pipeline's five try/except-wrapped stages and
spec/verdict.schema.json's closed `checker_error.stage` enum
(`load_snapshot`, `resolve_entity`, `load_evidence`, `run_rules`,
`format_verdict`) -- every stage tested here is chosen to hit each branch
of that mapping at least once.
"""

from __future__ import annotations

import importlib

from evidence.errors import EvidenceError
from normalize import NormalizationError
from rules import RuleEngine
from verifier import verify

# NOTE: `import verifier.verify as verify_mod` would NOT give the
# `verifier.verify` submodule here -- `verifier/__init__.py` does
# `from .verify import verify`, which rebinds the *name* `verify` inside
# the `verifier` package's own namespace to the function, shadowing the
# submodule reference that `import verifier.verify` would otherwise leave
# there. `importlib.import_module` looks the submodule up in
# `sys.modules` directly instead of via attribute access on the package,
# sidestepping that shadowing.
verify_mod = importlib.import_module("verifier.verify")


class _Boom(RuntimeError):
    pass


def test_snapshot_hashes_read_failure_is_load_snapshot(bundle, config, load_claim, monkeypatch, assert_verdict_matches_schema):
    def _boom(self):
        raise _Boom("ledger read failed")

    monkeypatch.setattr(type(bundle.ledger), "snapshot_hashes", _boom)

    claim = load_claim("ACCEPTED_CONDITIONALLY__example.json")
    verdict = verify(claim, bundle, config)

    assert_verdict_matches_schema(verdict)
    assert verdict["verdict"] == "CHECKER_ERROR"
    assert verdict["checker_error"]["stage"] == "load_snapshot"
    assert verdict["checker_error"]["exception_class"] == "_Boom"


def test_schema_validation_failure_is_load_snapshot(bundle, config, load_claim, monkeypatch, assert_verdict_matches_schema):
    def _boom(instance, schema):
        raise _Boom("validator broke")

    monkeypatch.setattr(verify_mod, "validate_claim", _boom)

    claim = load_claim("ACCEPTED_CONDITIONALLY__example.json")
    verdict = verify(claim, bundle, config)

    assert_verdict_matches_schema(verdict)
    assert verdict["verdict"] == "CHECKER_ERROR"
    assert verdict["checker_error"]["stage"] == "load_snapshot"
    assert verdict["checker_error"]["exception_class"] == "_Boom"


def test_normalize_unexpected_exception_is_resolve_entity(bundle, config, load_claim, monkeypatch, assert_verdict_matches_schema):
    def _boom(claim, snapshot):
        raise _Boom("normalize broke")

    monkeypatch.setattr(verify_mod, "normalize_claim", _boom)

    claim = load_claim("ACCEPTED_CONDITIONALLY__example.json")
    verdict = verify(claim, bundle, config)

    assert_verdict_matches_schema(verdict)
    assert verdict["verdict"] == "CHECKER_ERROR"
    assert verdict["checker_error"]["stage"] == "resolve_entity"
    assert verdict["checker_error"]["exception_class"] == "_Boom"


def test_normalize_defensive_error_with_no_fault_code_is_resolve_entity(
    bundle, config, load_claim, monkeypatch, assert_verdict_matches_schema
):
    def _boom(claim, snapshot):
        raise NormalizationError("malformed shape", fault_code=None)

    monkeypatch.setattr(verify_mod, "normalize_claim", _boom)

    claim = load_claim("ACCEPTED_CONDITIONALLY__example.json")
    verdict = verify(claim, bundle, config)

    assert_verdict_matches_schema(verdict)
    assert verdict["verdict"] == "CHECKER_ERROR"
    assert verdict["checker_error"]["stage"] == "resolve_entity"
    assert verdict["checker_error"]["exception_class"] == "NormalizationError"


def test_rule_engine_unexpected_exception_is_run_rules(bundle, config, load_claim, monkeypatch, assert_verdict_matches_schema):
    def _boom(self, canonical_claim):
        raise _Boom("rule engine broke")

    monkeypatch.setattr(RuleEngine, "run", _boom)

    claim = load_claim("ACCEPTED_CONDITIONALLY__example.json")
    verdict = verify(claim, bundle, config)

    assert_verdict_matches_schema(verdict)
    assert verdict["verdict"] == "CHECKER_ERROR"
    assert verdict["checker_error"]["stage"] == "run_rules"
    assert verdict["checker_error"]["exception_class"] == "_Boom"


def test_rule_engine_hash_mismatch_is_load_evidence(bundle, config, load_claim, monkeypatch, assert_verdict_matches_schema):
    def _boom(self, canonical_claim):
        raise EvidenceError("HASH_MISMATCH", reason="tampered")

    monkeypatch.setattr(RuleEngine, "run", _boom)

    claim = load_claim("ACCEPTED_CONDITIONALLY__example.json")
    verdict = verify(claim, bundle, config)

    assert_verdict_matches_schema(verdict)
    assert verdict["verdict"] == "CHECKER_ERROR"
    assert verdict["checker_error"]["stage"] == "load_evidence"
    assert verdict["checker_error"]["exception_class"] == "EvidenceError"


def test_format_accepted_failure_is_format_verdict(bundle, config, load_claim, monkeypatch, assert_verdict_matches_schema):
    def _boom(*args, **kwargs):
        raise _Boom("formatter broke")

    monkeypatch.setattr(verify_mod, "format_accepted", _boom)

    claim = load_claim("ACCEPTED_CONDITIONALLY__example.json")
    verdict = verify(claim, bundle, config)

    assert_verdict_matches_schema(verdict)
    assert verdict["verdict"] == "CHECKER_ERROR"
    assert verdict["checker_error"]["stage"] == "format_verdict"
    assert verdict["checker_error"]["exception_class"] == "_Boom"


def test_audit_append_failure_is_format_verdict(bundle, load_claim, monkeypatch, assert_verdict_matches_schema, tmp_path):
    from audit import AuditLedger
    from verifier import VerifierConfig

    ledger = AuditLedger(tmp_path / "ledger.jsonl")

    def _boom(self, claim, verdict):
        raise _Boom("append broke")

    monkeypatch.setattr(AuditLedger, "append", _boom)

    cfg = VerifierConfig(
        checker_version="0.1.0",
        schema_dir=_spec_dir(),
        audit_ledger=ledger,
    )
    claim = load_claim("ACCEPTED_CONDITIONALLY__example.json")
    verdict = verify(claim, bundle, cfg)

    assert_verdict_matches_schema(verdict)
    assert verdict["verdict"] == "CHECKER_ERROR"
    assert verdict["checker_error"]["stage"] == "format_verdict"
    assert verdict["checker_error"]["exception_class"] == "_Boom"


def _spec_dir():
    from pathlib import Path

    return Path(__file__).resolve().parents[2] / "spec"
