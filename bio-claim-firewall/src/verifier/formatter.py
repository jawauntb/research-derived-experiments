"""Builds the spec/verdict.schema.json-conformant dict for each verdict shape.

Every `format_*` function here returns a complete, schema-conformant verdict
dict. Fields only ever appear when they apply to that verdict branch
(`fault_code`/`reasons` for REJECTED, `derivation` for
ACCEPTED_CONDITIONALLY, `checker_error` for CHECKER_ERROR) -- omitted
rather than set to a placeholder `null`/`[]` for the branches where they
don't apply, since `verdict.schema.json` makes all four optional at the top
level (only the `allOf`/`if`/`then` blocks conditionally require them for
their matching `verdict` value) and this keeps every returned dict minimal
and unambiguous about which branch produced it.

# VERIFIER-DECISION (verdict_id / issued_at circularity): `audit.compute_verdict_id`
# hashes `(claim, verdict_body, snapshot_hashes, checker_version)`. Both
# `verdict_id` itself (obviously -- it's the thing being computed) and
# `issued_at` (a wall-clock timestamp that changes on every call) are
# EXCLUDED from `verdict_body` before hashing -- an `issued_at` inside the
# hash input would make `compute_verdict_id` non-deterministic across two
# calls for the same claim/snapshot/checker_version, which directly
# contradicts spec/verdict.schema.json's own stability contract and this
# task's `test_verdict_id_stability.py` requirement. This matches
# `tests/audit/test_verdict_id.py`'s own `VERDICT_BODY` fixture, which
# likewise carries no `verdict_id`/`issued_at`/`checker_version`/
# `snapshot_hashes` (the latter two are passed as `compute_verdict_id`'s
# own separate arguments, not nested inside `verdict_body`).
#
# A second, related decision lives in `verify.py`: when a verdict this
# module built is appended to an `AuditLedger`, `verify.py` strips the
# `verdict_id` key back out of the dict before calling `ledger.append()`.
# `AuditLedger.append()` computes its own `verdict_id` via
# `compute_verdict_id(claim, verdict, ...)` over whatever `verdict` dict it
# is given verbatim (see `LedgerEntry`'s own docstring: it "includes
# verdict_id redundantly ... IF the caller put it there ... AuditLedger
# does not require or depend on that"). Stripping it first guarantees the
# ledger recomputes the *same* id this module already minted and returned
# to the external caller, rather than hashing a blob that includes its own
# id as a field (which would silently produce a different, unrelated id).
"""

from __future__ import annotations

import hashlib
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Sequence

from audit import compute_verdict_id
from rules.types import Reason, RuleResult

SCHEMA_VERSION = "0.1.0"

_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


def _safe_repr(obj: Any) -> str:
    """`repr(obj)`, guaranteed to never raise.

    `repr()` itself can still raise for a pathological `__repr__`
    implementation or (rarely) `RecursionError` on extreme nesting; this
    module must stay usable even then (see `test_never_raises.py`), so the
    fallback below never touches `obj` beyond `type()`/`id()`, neither of
    which can raise for any object.
    """
    try:
        return repr(obj)
    except Exception:
        return f"<{type(obj).__name__} id={id(obj)}>"


def _claim_id(claim: Any) -> str:
    """Extract a uuid-shaped `claim_id` for the verdict, or synthesize one.

    # VERIFIER-DECISION: `verdict.schema.json` requires `claim_id` on
    # EVERY verdict (including CHECKER_ERROR), format "uuid" -- but
    # `verify()` must never raise even when `claim` is garbage (not a
    # dict, or a dict with no/malformed `claim_id`; see
    # `test_never_raises.py`). When a well-formed uuid `claim_id` can't be
    # read off `claim`, deterministically derive a placeholder uuid from
    # `repr(claim)` via `uuid.uuid5` -- always syntactically valid, and
    # stable for the same garbage input (though nothing depends on that
    # stability; it's just a "least-surprise" property to have for free).
    """
    if isinstance(claim, dict):
        cid = claim.get("claim_id")
        if isinstance(cid, str) and _UUID_RE.match(cid):
            return cid
    return str(uuid.uuid5(uuid.NAMESPACE_OID, _safe_repr(claim)))


def _issued_at() -> str:
    """Current time as ISO 8601 UTC with millisecond precision and a `Z` suffix."""
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"


def _reason_dict(reason: Reason) -> dict[str, Any]:
    return {
        "rule_id": reason.rule_id,
        "message": reason.message,
        "evidence_id": reason.evidence_id,
    }


def _safe_verdict_id(
    claim: Any,
    verdict_body: dict[str, Any],
    snapshot_hashes: dict[str, str],
    checker_version: str,
) -> str:
    """`audit.compute_verdict_id`, guaranteed to never raise.

    # VERIFIER-DECISION: `compute_verdict_id` requires a strictly
    # JSON-shaped payload (`audit.hashing._normalize` rejects sets,
    # arbitrary objects, and non-finite floats with `TypeError`/
    # `ValueError`). A garbage `claim` fed to `verify()` (see
    # `test_never_raises.py`) can absolutely fail that requirement -- and
    # this function is reached from every `format_*` call, including
    # `format_checker_error` itself, which is the pipeline's own
    # last-resort fail-closed path. If minting a verdict_id could raise,
    # a bad-enough `claim` could make even the fail-closed path fail,
    # which would defeat `verify()`'s "never raises" guarantee at the one
    # place that's not allowed to happen. Fall back to hashing a Python
    # `repr()` of the same four-tuple instead -- not part of the
    # `compute_verdict_id` tamper-evidence contract (a claim that reaches
    # this fallback was never JSON-shaped to begin with, so byte-exact
    # ledger-style tamper evidence doesn't apply to it anyway), just a
    # guaranteed-valid 32-hex-char id.
    """
    try:
        return compute_verdict_id(claim, verdict_body, snapshot_hashes, checker_version)
    except Exception:
        blob = _safe_repr((claim, verdict_body, snapshot_hashes, checker_version)).encode(
            "utf-8", errors="replace"
        )
        return hashlib.sha256(blob).hexdigest()[:32]


def _finalize(
    claim: Any,
    verdict_body: dict[str, Any],
    snapshot_hashes: dict[str, str],
    checker_version: str,
) -> dict[str, Any]:
    """Add `checker_version`/`snapshot_hashes`/`schema_version`, mint
    `verdict_id`, then add `issued_at`, in that exact order.

    # VERIFIER-DECISION (what exactly gets hashed): `verdict_id` is minted
    # over `verdict_body` PLUS `checker_version`/`snapshot_hashes`/
    # `schema_version` -- i.e. everything in the final dict EXCEPT
    # `verdict_id` itself (obviously) and `issued_at` (a wall-clock
    # timestamp; including it would make `compute_verdict_id`
    # non-deterministic across calls, breaking
    # `test_verdict_id_stability.py`'s "same inputs -> same id"
    # requirement). This exact dict shape -- "the final verdict minus
    # verdict_id and issued_at" -- is deliberate: it is also EXACTLY what
    # `verify.py` hands to `AuditLedger.append()` (after separately
    # stripping the now-added `verdict_id`/`issued_at` back out again).
    # `AuditLedger.append()` computes its own id via
    # `compute_verdict_id(claim, verdict, verdict["snapshot_hashes"],
    # verdict["checker_version"])` over WHATEVER dict it's handed, in
    # full, including checker_version/snapshot_hashes/schema_version
    # nested inside it -- so for the ledger's recomputed id to equal the
    # id this module already minted and returned to the caller (the
    # `test_audit_integration.py` "matching verdict_id" requirement),
    # both hashes must cover the identical dict shape. Hashing only the
    # bare `verdict_body` (claim_id/verdict/derivation/etc, as
    # `tests/audit/test_verdict_id.py`'s own minimal `VERDICT_BODY`
    # fixture does) would NOT match the ledger's later recomputation,
    # since the ledger has no way to hash a narrower slice than "the
    # whole dict it was given."
    """
    verdict = dict(verdict_body)
    verdict["checker_version"] = checker_version
    verdict["snapshot_hashes"] = dict(snapshot_hashes)
    verdict["schema_version"] = SCHEMA_VERSION
    verdict["verdict_id"] = _safe_verdict_id(claim, verdict, snapshot_hashes, checker_version)
    verdict["issued_at"] = _issued_at()
    return verdict


def format_accepted(
    claim: Any,
    rule_result: RuleResult,
    snapshot_hashes: dict[str, str],
    checker_version: str,
) -> dict[str, Any]:
    """Build an ACCEPTED_CONDITIONALLY verdict from a `RuleResult`.

    `rule_result.verdict` must be `"ACCEPTED"`. `derivation.evidence_ids`
    and `derivation.applied_rules` are built from `rule_result.applied_rules`
    (order-preserving de-dup); every `AppliedRule` the `rules` package emits
    on an ACCEPTED result carries a non-`None` `evidence_id` (see
    `rules/licensing.py`), so both lists are guaranteed non-empty here,
    satisfying `derivation`'s own `minItems: 1` constraints.
    """
    evidence_ids: list[str] = []
    seen_evidence: set[str] = set()
    applied_rule_ids: list[str] = []
    seen_rules: set[str] = set()
    for applied in rule_result.applied_rules:
        if applied.evidence_id is not None and applied.evidence_id not in seen_evidence:
            seen_evidence.add(applied.evidence_id)
            evidence_ids.append(applied.evidence_id)
        if applied.rule_id not in seen_rules:
            seen_rules.add(applied.rule_id)
            applied_rule_ids.append(applied.rule_id)

    verdict_body = {
        "claim_id": _claim_id(claim),
        "verdict": "ACCEPTED_CONDITIONALLY",
        "derivation": {
            "evidence_ids": evidence_ids,
            "applied_rules": applied_rule_ids,
            "conditions": list(rule_result.conditions),
        },
    }
    return _finalize(claim, verdict_body, snapshot_hashes, checker_version)


def format_rejected(
    claim: Any,
    fault_code: str,
    reasons: Sequence[Reason],
    snapshot_hashes: dict[str, str],
    checker_version: str,
) -> dict[str, Any]:
    """Build a REJECTED verdict with the given closed-taxonomy `fault_code`."""
    verdict_body = {
        "claim_id": _claim_id(claim),
        "verdict": "REJECTED",
        "fault_code": fault_code,
        "reasons": [_reason_dict(r) for r in reasons],
    }
    return _finalize(claim, verdict_body, snapshot_hashes, checker_version)


def format_inconclusive(
    claim: Any,
    snapshot_hashes: dict[str, str],
    checker_version: str,
) -> dict[str, Any]:
    """Build an INCONCLUSIVE verdict -- distinct from REJECTED/CHECKER_ERROR."""
    verdict_body = {
        "claim_id": _claim_id(claim),
        "verdict": "INCONCLUSIVE",
    }
    return _finalize(claim, verdict_body, snapshot_hashes, checker_version)


def format_checker_error(
    claim: Any,
    stage: str,
    message: str,
    exception_class: str | None,
    snapshot_hashes: dict[str, str],
    checker_version: str,
) -> dict[str, Any]:
    """Build a CHECKER_ERROR verdict -- fail-closed; never a `REJECTED_*` code.

    `stage` must be one of the five values `verdict.schema.json`'s
    `checker_error.stage` enum permits (`load_snapshot`, `resolve_entity`,
    `load_evidence`, `run_rules`, `format_verdict`); `verify.py` is the one
    place responsible for choosing the right value (see its own
    VERIFIER-DECISION on mapping this pipeline's stages onto that closed
    set) -- this function does not validate `stage` itself, since doing so
    would risk raising from inside the module whose entire job is to never
    raise.
    """
    verdict_body = {
        "claim_id": _claim_id(claim),
        "verdict": "CHECKER_ERROR",
        "checker_error": {
            "stage": stage,
            "message": message,
            "exception_class": exception_class,
        },
    }
    return _finalize(claim, verdict_body, snapshot_hashes, checker_version)
