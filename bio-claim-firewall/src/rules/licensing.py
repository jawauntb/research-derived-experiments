"""ACCEPT logic: runs after the rule cascade completes with no rejection.

Determines whether at least one cited evidence record (surviving every
positive check the cascade already ran -- edge type, subject/object pair,
context, sign, causal observation_type) licenses the claim's
(subject, relation, object) edge, and renders the human-readable
`conditions` the acceptance is scoped to from that winning record set's
own context fields.

Returns `None` (the engine renders `INCONCLUSIVE`) when nothing licenses.
"""

from __future__ import annotations

from typing import Sequence

from evidence.snapshot import SnapshotBundle
from normalize import CanonicalClaim

from .cited import CitedRecord
from .sections._shared import causal_matched, edge_and_context_matched
from .types import AppliedRule

# RULES-DECISION: neither `normalize.CanonicalClaim`/`CanonicalEvidence`
# nor the `Snapshot`/`SnapshotBundle` protocol exposes a CURIE -> label
# lookup (`SnapshotBundle.curies` is a bare `frozenset[str]`, no label
# map) -- cell_context.cell_line is carried as a CURIE only, on both the
# claim and evidence schemas. `spec/inference_rules.md`'s own worked
# examples (`"only in cell_line=CLO:0009454 (K562)"`) and
# `tests/fixtures/expectations.jsonl`'s `expected_conditions_contain`
# checks (which look for the bare human label `"K562"`/`"RPE1"`, never the
# CURIE) both assume this annotation exists somewhere. We maintain a small
# static registry for the fixture pack's two known cell lines, used
# *only* for rendering -- never for matching/identity, which always
# compares raw CURIEs. An unrecognized cell_line CURIE degrades
# gracefully to the bare CURIE with no parenthetical.
_KNOWN_CELL_LINE_LABELS: dict[str, str] = {
    "CLO:0009454": "K562",
    "CLO:0037231": "RPE1",
}


def _winning_records(
    claim: CanonicalClaim, cited: Sequence[CitedRecord], snapshot: SnapshotBundle
) -> list[CitedRecord]:
    candidates = edge_and_context_matched(claim, cited, snapshot)

    if claim.relation in ("increases", "decreases"):
        wanted = "positive" if claim.relation == "increases" else "negative"
        candidates = [c for c in candidates if c.canonical.effect is not None and c.canonical.effect.sign == wanted]
    elif claim.relation == "correlates_with":
        wants_positive = claim.polarity == "positive"
        candidates = [
            c
            for c in candidates
            if c.canonical.effect is not None
            and (c.canonical.effect.magnitude > 0 if wants_positive else c.canonical.effect.magnitude < 0)
        ]

    return causal_matched(claim, candidates)


def _render_conditions(winners: Sequence[CitedRecord]) -> tuple[tuple[str, ...], tuple[AppliedRule, ...]]:
    conditions: list[str] = []
    applied: list[AppliedRule] = []
    seen: set[str] = set()

    def _add(text: str, rule_id: str, evidence_id: str) -> None:
        if text in seen:
            return
        seen.add(text)
        conditions.append(text)
        applied.append(AppliedRule(rule_id=rule_id, evidence_id=evidence_id))

    for record in winners:
        e = record.canonical
        if e.cell_line is not None:
            label = _KNOWN_CELL_LINE_LABELS.get(e.cell_line)
            text = f"only in cell_line={e.cell_line}" + (f" ({label})" if label else "")
            _add(text, "R-CTX-03", record.evidence_id)
        if e.state is not None:
            _add(f"only in state={e.state}", "R-CTX-04", record.evidence_id)
        if e.perturbation is not None:
            _add(f"only under perturbation={e.perturbation}", "R-CTX-06", record.evidence_id)
        _add(f"only under assay={e.assay}", "R-CTX-05", record.evidence_id)
        _add(f"evidence_id={record.evidence_id}", "R-EDGE-02", record.evidence_id)

    return tuple(conditions), tuple(applied)


def license_claim(
    claim: CanonicalClaim, cited: Sequence[CitedRecord], snapshot: SnapshotBundle
) -> tuple[tuple[AppliedRule, ...], tuple[str, ...]] | None:
    """Returns `(applied_rules, conditions)` for the winning record set, or `None`."""
    winners = _winning_records(claim, cited, snapshot)
    if not winners:
        return None
    conditions, applied_rules = _render_conditions(winners)
    if not conditions or not applied_rules:
        # Defensive: RuleResult's own invariants require both non-empty for
        # ACCEPTED; every winner renders at least an assay + edge condition,
        # so this should be unreachable, but we never want a silently
        # malformed ACCEPT to reach RuleResult's constructor.
        return None
    return applied_rules, conditions
