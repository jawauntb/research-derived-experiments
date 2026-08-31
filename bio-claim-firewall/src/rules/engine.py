"""`RuleEngine`: the fixed rule cascade over a hash-verified snapshot.

Runs the sections from spec/inference_rules.md's `§Rule cascade order` in
their fixed sequence, stopping at the first rule that fires. See
src/INTERFACES.md's `rules` contract for the class signature this module
implements.
"""

from __future__ import annotations

from typing import Any

from evidence.errors import EvidenceError
from evidence.snapshot import SnapshotBundle
from normalize import CanonicalClaim, normalize_evidence

from .cited import CitedRecord
from .errors import RulesError
from .licensing import license_claim
from .sections import (
    causality,
    certainty,
    citations,
    context,
    contradiction,
    coverage,
    edges,
    entities,
    relations,
    scope,
    signs,
)
from .types import Reason, RuleResult

# Every rule id in spec/inference_rules.md -> the fault_code it renders on
# REJECTED, per spec/fault_taxonomy.md. One rule_id -> one fault_code
# always, but the mapping is NOT one section -> one fault_code: R-CAUS-04
# (implemented in sections/causality.py) renders SCOPE_OVERCLAIM, not
# CAUSALITY_OVERCLAIM -- see sections/causality.py's RULES-DECISION.
_FAULT_CODE_BY_RULE: dict[str, str] = {
    "R-CITE-01": "BAD_CITATION",
    "R-CITE-02": "BAD_CITATION",
    "R-CITE-03": "BAD_CITATION",
    "R-ENT-01": "UNKNOWN_ENTITY",
    "R-ENT-02": "UNKNOWN_ENTITY",
    "R-ENT-03": "UNKNOWN_ENTITY",
    "R-SCOPE-90": "OUT_OF_SCOPE",
    "R-SCOPE-91": "OUT_OF_SCOPE",
    "R-REL-01": "INVALID_RELATION",
    "R-REL-02": "INVALID_RELATION",
    "R-EDGE-01": "UNSUPPORTED_EDGE",
    "R-EDGE-02": "UNSUPPORTED_EDGE",
    "R-CTX-01": "CONTEXT_MISMATCH",
    "R-CTX-02": "CONTEXT_MISMATCH",
    "R-CTX-03": "CONTEXT_MISMATCH",
    "R-CTX-04": "CONTEXT_MISMATCH",
    "R-CTX-05": "CONTEXT_MISMATCH",
    "R-CTX-06": "CONTEXT_MISMATCH",
    "R-SIGN-01": "SIGN_MISMATCH",
    "R-SIGN-02": "SIGN_MISMATCH",
    "R-CAUS-01": "CAUSALITY_OVERCLAIM",
    "R-CAUS-02": "CAUSALITY_OVERCLAIM",
    "R-CAUS-03": "CAUSALITY_OVERCLAIM",
    "R-CAUS-04": "SCOPE_OVERCLAIM",
    "R-SCOPE-01": "SCOPE_OVERCLAIM",
    "R-SCOPE-02": "SCOPE_OVERCLAIM",
    "R-SCOPE-03": "SCOPE_OVERCLAIM",
    "R-CONTRA-01": "CONTRADICTED",
    "R-CONTRA-02": "CONTRADICTED",
    "R-CERT-01": "UNSUPPORTED_CERTAINTY",
    "R-CERT-02": "UNSUPPORTED_CERTAINTY",
}


def _fault_code_for(reasons: tuple[Reason, ...]) -> str:
    try:
        return _FAULT_CODE_BY_RULE[reasons[0].rule_id]
    except KeyError as exc:  # pragma: no cover - internal invariant guard
        raise RulesError(
            "UNKNOWN_RULE_ID", rule_id=reasons[0].rule_id
        ) from exc


class RuleEngine:
    """Runs the fixed rule cascade for one claim against one frozen snapshot."""

    def __init__(self, snapshot: SnapshotBundle, checker_version: str) -> None:
        self._snapshot = snapshot
        self._checker_version = checker_version

    def run(self, canonical_claim: CanonicalClaim) -> RuleResult:
        cited, cite_reasons = self._resolve_citations(canonical_claim)
        if cite_reasons:
            return RuleResult("REJECTED", _fault_code_for(cite_reasons), cite_reasons)

        reasons = citations.check_all(canonical_claim, cited, self._snapshot)
        if reasons:
            return RuleResult("REJECTED", _fault_code_for(tuple(reasons)), tuple(reasons))

        reasons = entities.check_all(canonical_claim, cited, self._snapshot)
        if reasons:
            return RuleResult("REJECTED", _fault_code_for(tuple(reasons)), tuple(reasons))

        coverage_reason = coverage.check(canonical_claim, cited, self._snapshot)
        if coverage_reason is not None:
            return RuleResult("REJECTED", _fault_code_for((coverage_reason,)), (coverage_reason,))

        reasons = relations.check_all(canonical_claim, cited, self._snapshot)
        if reasons:
            return RuleResult("REJECTED", _fault_code_for(tuple(reasons)), tuple(reasons))

        reasons = edges.check_all(canonical_claim, cited, self._snapshot)
        if reasons:
            return RuleResult("REJECTED", _fault_code_for(tuple(reasons)), tuple(reasons))

        ctx_reason = context.check(canonical_claim, cited, self._snapshot)
        if ctx_reason is not None:
            return RuleResult("REJECTED", _fault_code_for((ctx_reason,)), (ctx_reason,))

        sign_reason, sign_inconclusive = signs.check(canonical_claim, cited, self._snapshot)
        if sign_inconclusive:
            return RuleResult("INCONCLUSIVE", None)
        if sign_reason is not None:
            return RuleResult("REJECTED", _fault_code_for((sign_reason,)), (sign_reason,))

        reasons = causality.check_all(canonical_claim, cited, self._snapshot)
        if reasons:
            return RuleResult("REJECTED", _fault_code_for(tuple(reasons)), tuple(reasons))

        reasons = scope.check_all(canonical_claim, cited, self._snapshot)
        if reasons:
            return RuleResult("REJECTED", _fault_code_for(tuple(reasons)), tuple(reasons))

        contra_reason = contradiction.check(canonical_claim, cited, self._snapshot)
        if contra_reason is not None:
            return RuleResult("REJECTED", _fault_code_for((contra_reason,)), (contra_reason,))

        reasons = certainty.check_all(canonical_claim, cited, self._snapshot)
        if reasons:
            return RuleResult("REJECTED", _fault_code_for(tuple(reasons)), tuple(reasons))

        licensed = license_claim(canonical_claim, cited, self._snapshot)
        if licensed is None:
            return RuleResult("INCONCLUSIVE", None)
        applied_rules, conditions = licensed
        return RuleResult(
            "ACCEPTED", None, applied_rules=applied_rules, conditions=conditions
        )

    def _resolve_citations(
        self, canonical_claim: CanonicalClaim
    ) -> tuple[tuple[CitedRecord, ...], tuple[Reason, ...]]:
        """R-CITE-01: load every cited evidence_id, catching ONLY `EvidenceError("BAD_CITATION")`.

        Every other exception (a `HASH_MISMATCH` `EvidenceError`, a
        `NormalizationError` out of `normalize_evidence`, anything else)
        escalates uncaught, per src/INTERFACES.md's fail-closed contract --
        the top-level `verifier.verify()` is the one place that turns an
        uncaught exception into `CHECKER_ERROR`.
        """
        records: list[CitedRecord] = []
        missing: list[Reason] = []
        for evidence_id in canonical_claim.evidence_ids:
            try:
                raw: dict[str, Any] = self._snapshot.ledger.get(evidence_id)
            except EvidenceError as exc:
                # MUTATION-POINT: only BAD_CITATION is a claim-level fault;
                # anything else (e.g. a defensive HASH_MISMATCH) must
                # escalate, never get silently swallowed into R-CITE-01.
                if exc.fault_code != "BAD_CITATION":
                    raise
                missing.append(citations.missing_citation_reason(evidence_id))
                continue
            canonical = normalize_evidence(raw, self._snapshot)
            records.append(CitedRecord(evidence_id=evidence_id, raw=raw, canonical=canonical))
        return tuple(records), tuple(missing)
