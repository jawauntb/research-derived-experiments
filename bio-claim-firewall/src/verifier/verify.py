"""`verify()`: the single public entry point of the bio-claim-firewall verifier.

Pipeline: JSON-Schema validate -> normalize -> rule cascade -> format
verdict -> (optionally) durably append to the audit ledger. Every stage is
wrapped in its own `try/except Exception`; nothing this function calls is
ever allowed to raise out of `verify()` itself -- an unexpected exception
at any stage becomes a `CHECKER_ERROR` verdict (fail-closed), never a
silently-converted `REJECTED_*` (spec/non_goals.md's first "Prohibited
move").

# VERIFIER-DECISION (checker_error.stage mapping): spec/verdict.schema.json
# closes `checker_error.stage` to exactly five values: `load_snapshot`,
# `resolve_entity`, `load_evidence`, `run_rules`, `format_verdict`. This
# pipeline has its own five try/except-wrapped stages (read snapshot
# hashes, schema-validate, normalize, run the rule cascade, format +
# durably append), which doesn't map onto that enum one-for-one by name.
# Chosen mapping, each documented at its call site below:
#
#   - `load_snapshot`   -- reading `snapshot.ledger.snapshot_hashes()` (a
#                           genuine read against the snapshot object), AND
#                           an unexpected exception from the JSON-Schema
#                           validation step itself (loading/parsing
#                           claim.schema.json, or a bug in the validator) --
#                           both are "we could not establish a trustworthy
#                           frozen input contract before touching the
#                           claim's own content."
#   - `resolve_entity`  -- `normalize.normalize_claim()` raising anything
#                           other than a claim-level `UNKNOWN_ENTITY`
#                           `NormalizationError` (exact semantic fit --
#                           this is literally the entity-resolution stage).
#   - `load_evidence`   -- specifically an `EvidenceError(fault_code=
#                           "HASH_MISMATCH")` surfacing through the rule
#                           cascade's evidence-citation lookups (see
#                           `src/INTERFACES.md`'s evidence contract: a
#                           `HASH_MISMATCH` means the frozen evidence
#                           records themselves failed to load
#                           trustworthily -- distinct from an ordinary
#                           rule-engine bug).
#   - `run_rules`       -- any other exception out of `RuleEngine.run()`.
#   - `format_verdict`  -- an unexpected exception while building the
#                           verdict dict, AND a failure durably appending
#                           it to the audit ledger. The ledger append is
#                           the last step before returning the verdict to
#                           the caller -- durably recording it is treated
#                           as part of "finalizing/emitting the verdict,"
#                           and no better-fitting name exists in the closed
#                           enum for a ledger-mechanics failure
#                           (`AuditError("DUPLICATE_VERDICT_ID"/
#                           "LEDGER_TAMPERED")`).
"""

from __future__ import annotations

from typing import Any

from evidence.errors import EvidenceError
from evidence.snapshot import SnapshotBundle
from normalize import NormalizationError, normalize_claim
from rules import RuleEngine
from rules.types import Reason

from .config import VerifierConfig
from .errors import VerifierError
from .formatter import (
    format_accepted,
    format_checker_error,
    format_inconclusive,
    format_rejected,
)
from .mapping import fault_code_for_schema_failure
from .schema import load_claim_schema, validate_claim


def verify(claim: dict, snapshot: SnapshotBundle, config: VerifierConfig) -> dict:
    """Verify one claim end-to-end. NEVER raises. Every unexpected exception
    becomes a CHECKER_ERROR verdict with the failing stage recorded.
    """
    # Stage 0: snapshot_hashes are threaded into every verdict this call
    # can produce (including every CHECKER_ERROR below), so establish them
    # first, before touching the claim's own content at all.
    try:
        snapshot_hashes = dict(snapshot.ledger.snapshot_hashes())
    except Exception as exc:  # noqa: BLE001 - top-level fail-closed boundary
        return format_checker_error(
            claim,
            stage="load_snapshot",
            message=str(exc),
            exception_class=type(exc).__name__,
            snapshot_hashes={},
            checker_version=config.checker_version,
        )

    # Stage 1: JSON-Schema validation.
    try:
        schema = load_claim_schema(config.schema_dir)
        failure = validate_claim(claim, schema)
    except Exception as exc:  # noqa: BLE001
        return format_checker_error(
            claim,
            stage="load_snapshot",
            message=str(exc),
            exception_class=type(exc).__name__,
            snapshot_hashes=snapshot_hashes,
            checker_version=config.checker_version,
        )

    if failure is not None:
        mapped = fault_code_for_schema_failure(failure)
        if mapped is None:
            return format_checker_error(
                claim,
                stage="load_snapshot",
                message=(
                    f"claim failed JSON-Schema validation at "
                    f"{failure.field_path!r} ({failure.constraint_kind}): {failure.message}"
                ),
                exception_class="SchemaValidationError",
                snapshot_hashes=snapshot_hashes,
                checker_version=config.checker_version,
            )
        fault_code, rule_id = mapped
        reason = Reason(
            rule_id=rule_id,
            message=(
                f"schema validation failed at {failure.field_path!r} "
                f"({failure.constraint_kind}): {failure.message}"
            ),
            evidence_id=None,
        )
        return format_rejected(claim, fault_code, (reason,), snapshot_hashes, config.checker_version)

    # Stage 2: normalize (canonicalize + resolve every CURIE).
    try:
        canonical_claim = normalize_claim(claim, snapshot)
    except NormalizationError as exc:
        if exc.fault_code == "UNKNOWN_ENTITY":
            rule_id = "R-ENT-03" if (exc.where or "").startswith("cell_context.cell_type") else "R-ENT-02"
            reason = Reason(rule_id=rule_id, message=str(exc), evidence_id=None)
            return format_rejected(
                claim, "UNKNOWN_ENTITY", (reason,), snapshot_hashes, config.checker_version
            )
        return format_checker_error(
            claim,
            stage="resolve_entity",
            message=str(exc),
            exception_class=type(exc).__name__,
            snapshot_hashes=snapshot_hashes,
            checker_version=config.checker_version,
        )
    except Exception as exc:  # noqa: BLE001
        return format_checker_error(
            claim,
            stage="resolve_entity",
            message=str(exc),
            exception_class=type(exc).__name__,
            snapshot_hashes=snapshot_hashes,
            checker_version=config.checker_version,
        )

    # Stage 3: the fixed rule cascade.
    try:
        engine = RuleEngine(snapshot, config.checker_version)
        rule_result = engine.run(canonical_claim)
    except EvidenceError as exc:
        stage = "load_evidence" if exc.fault_code == "HASH_MISMATCH" else "run_rules"
        return format_checker_error(
            claim,
            stage=stage,
            message=str(exc),
            exception_class=type(exc).__name__,
            snapshot_hashes=snapshot_hashes,
            checker_version=config.checker_version,
        )
    except Exception as exc:  # noqa: BLE001
        return format_checker_error(
            claim,
            stage="run_rules",
            message=str(exc),
            exception_class=type(exc).__name__,
            snapshot_hashes=snapshot_hashes,
            checker_version=config.checker_version,
        )

    # Stage 4: format the verdict dict.
    try:
        if rule_result.verdict == "ACCEPTED":
            verdict = format_accepted(claim, rule_result, snapshot_hashes, config.checker_version)
        elif rule_result.verdict == "REJECTED":
            verdict = format_rejected(
                claim, rule_result.fault_code, rule_result.reasons, snapshot_hashes, config.checker_version
            )
        elif rule_result.verdict == "INCONCLUSIVE":
            verdict = format_inconclusive(claim, snapshot_hashes, config.checker_version)
        else:  # pragma: no cover - unreachable given RuleResult's own closed enum
            raise VerifierError(
                "format_verdict", f"unknown RuleResult.verdict {rule_result.verdict!r}"
            )
    except Exception as exc:  # noqa: BLE001
        return format_checker_error(
            claim,
            stage="format_verdict",
            message=str(exc),
            exception_class=type(exc).__name__,
            snapshot_hashes=snapshot_hashes,
            checker_version=config.checker_version,
        )

    # Stage 5: durable audit-ledger append. Acceptance requires durability
    # -- a failed append is NOT downgraded to "return the verdict anyway";
    # it fails closed into CHECKER_ERROR instead (see spec/non_goals.md;
    # this task's own instruction: "do NOT return the accepted verdict --
    # durability is required for acceptance").
    if config.audit_ledger is not None:
        try:
            # `verdict_id` AND `issued_at` are stripped before the ledger
            # append so the ledger's own `compute_verdict_id(claim,
            # verdict, ...)` recomputation hashes the exact same dict
            # shape `formatter.py` already hashed to mint `verdict_id` in
            # the first place -- see `formatter.py._finalize`'s
            # VERIFIER-DECISION docstring for why this must happen (in
            # particular, why `issued_at` must be excluded, not just
            # `verdict_id`).
            ledger_verdict = {
                k: v for k, v in verdict.items() if k not in ("verdict_id", "issued_at")
            }
            config.audit_ledger.append(claim, ledger_verdict)
        except Exception as exc:  # noqa: BLE001
            return format_checker_error(
                claim,
                stage="format_verdict",
                message=str(exc),
                exception_class=type(exc).__name__,
                snapshot_hashes=snapshot_hashes,
                checker_version=config.checker_version,
            )

    return verdict
