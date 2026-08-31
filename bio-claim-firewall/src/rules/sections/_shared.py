"""Shared tables and per-record matching helpers used by several sections.

Not a "section" itself (no rule ids live here) -- just the relation
grammar / assay-equivalence-class tables from spec/inference_rules.md §2
and §5, plus small pure helpers so `edges.py`, `context.py`, `signs.py`,
and `licensing.py` don't each re-derive the same candidate-narrowing logic
independently and drift out of sync.
"""

from __future__ import annotations

from typing import Sequence

from evidence.snapshot import SnapshotBundle
from normalize import CanonicalClaim, CanonicalEvidence

from ..cited import CitedRecord

# ---------------------------------------------------------------------------
# §2 Relation grammar
# ---------------------------------------------------------------------------

# (relation, polarity) pairs permitted by the grammar table.
ALLOWED_RELATION_POLARITY: frozenset[tuple[str, str]] = frozenset(
    {
        ("increases", "positive"),
        ("decreases", "negative"),
        ("binds", "none"),
        ("expressed_in", "none"),
        ("causes", "positive"),
        ("causes", "negative"),
        ("correlates_with", "positive"),
        ("correlates_with", "negative"),
    }
)

# relation -> record_types that can license it.
#
# RULES-DECISION: spec/inference_rules.md §2's table lists only
# `perturbation_effect` for `causes`. Taken literally, R-EDGE-01
# (cascade position 5) would reject `CAUSALITY_OVERCLAIM__invalid.json`
# as UNSUPPORTED_EDGE before the cascade ever reaches R-CAUS-01 (position
# 8) -- its cited record (R3) is `expression_observation`, not
# `perturbation_effect`. But `tests/fixtures/expectations.jsonl` is
# explicit and authoritative that this exact fixture must fire
# CAUSALITY_OVERCLAIM via an `R-CAUS-` rule ("fires R-CAUS-01 (and
# R-CAUS-02) before the cascade ever reaches R-CONTRA"), not
# UNSUPPORTED_EDGE. We resolve the conflict in the fixture pack's favor:
# `expression_observation` also edge-licenses `causes` (an observational
# measurement can still be *cited* toward a causal claim -- it is
# precisely R-CAUS-01/03 §4's job, running later in the cascade, to
# reject it for being non-interventional, not R-EDGE-01's).
RELATION_LICENSING_RECORD_TYPES: dict[str, frozenset[str]] = {
    "increases": frozenset({"perturbation_effect", "expression_observation"}),
    "decreases": frozenset({"perturbation_effect", "expression_observation"}),
    "binds": frozenset({"physical_interaction"}),
    "expressed_in": frozenset({"expression_observation", "ontology_annotation"}),
    "causes": frozenset({"perturbation_effect", "expression_observation"}),
    "correlates_with": frozenset({"expression_observation"}),
}

# increases/decreases -> the effect.sign the relation canonically asserts.
RELATION_CANONICAL_SIGN: dict[str, str] = {
    "increases": "positive",
    "decreases": "negative",
}

# RULES-DECISION: `binds` is the only relation without an inherent
# subject/object direction ("subject/object appear as a partner pair" per
# §2 -- a physical interaction is symmetric). Every other relation requires
# exact (subject, object) order after alias normalization, per R-EDGE-02's
# text ("does not match the claim's (subject, object) pair").
_DIRECTION_AGNOSTIC_RELATIONS = frozenset({"binds"})


# ---------------------------------------------------------------------------
# §5 Assay equivalence classes
# ---------------------------------------------------------------------------

ASSAY_EQUIVALENCE_CLASSES: tuple[frozenset[str], ...] = (
    frozenset({"scRNA-seq", "snRNA-seq", "bulk-RNA-seq"}),
    frozenset({"CRISPRi_screen", "CRISPRa_screen", "siRNA_knockdown", "ORF_overexpression"}),
    frozenset({"ChIP-seq", "CUT&RUN", "ChIP-nexus"}),
    frozenset({"co-IP", "AP-MS", "Y2H", "BioID"}),
)


def same_assay_class(claim_assay: str, evidence_assay: str) -> bool:
    """True iff the two assay strings are equal or share an equivalence class."""
    if claim_assay == evidence_assay:
        return True
    for cls in ASSAY_EQUIVALENCE_CLASSES:
        if claim_assay in cls and evidence_assay in cls:
            return True
    return False


# ---------------------------------------------------------------------------
# Candidate narrowing
# ---------------------------------------------------------------------------


def edge_type_matched(claim: CanonicalClaim, cited: Sequence[CitedRecord]) -> list[CitedRecord]:
    """Cited records whose record_type is in the relation's licensing set (R-EDGE-01)."""
    allowed = RELATION_LICENSING_RECORD_TYPES.get(claim.relation, frozenset())
    return [c for c in cited if c.canonical.record_type in allowed]


def pair_matches(claim: CanonicalClaim, evidence: CanonicalEvidence) -> bool:
    """True iff `evidence`'s (subject, object) pair matches the claim's, per R-EDGE-02."""
    same_order = evidence.subject_id == claim.subject_id and evidence.object_id == claim.object_id
    if same_order:
        return True
    if claim.relation in _DIRECTION_AGNOSTIC_RELATIONS:
        return evidence.subject_id == claim.object_id and evidence.object_id == claim.subject_id
    return False


def pair_matched(claim: CanonicalClaim, candidates: Sequence[CitedRecord]) -> list[CitedRecord]:
    """Subset of `candidates` whose (subject, object) pair matches the claim's (R-EDGE-02)."""
    return [c for c in candidates if pair_matches(claim, c.canonical)]


def context_ok(
    claim: CanonicalClaim, evidence: CanonicalEvidence, snapshot: SnapshotBundle
) -> tuple[bool, str | None]:
    """Check `evidence`'s context against the claim's, in R-CTX-01..06 order.

    Returns `(True, None)` if every applicable dimension matches (waivers
    included), else `(False, <first-failing-rule-id>)`.
    """
    # MUTATION-POINT: R-CTX-01 -- species must match the cited record's.
    if claim.species != evidence.species:
        return False, "R-CTX-01"
    if claim.cell_type != "unspecified":
        # MUTATION-POINT: R-CTX-02 -- claim.cell_type must equal, or be a
        # Cell-Ontology ancestor of, the cited record's cell_type.
        if claim.cell_type != evidence.cell_type and claim.cell_type not in snapshot.ancestors(
            evidence.cell_type
        ):
            return False, "R-CTX-02"
    if claim.cell_line is not None:
        # MUTATION-POINT: R-CTX-03 -- a specified cell_line must match
        # exactly (cell_line=None waives this rule entirely).
        if claim.cell_line != evidence.cell_line:
            return False, "R-CTX-03"
    if claim.state is not None:
        # MUTATION-POINT: R-CTX-04 -- a specified state must match exactly
        # (state=None waives this rule entirely).
        if claim.state != evidence.state:
            return False, "R-CTX-04"
    # MUTATION-POINT: R-CTX-05 -- assay must match, or be in the same
    # assay-equivalence class as, the cited record's assay.
    if claim.assay != evidence.assay and not same_assay_class(claim.assay, evidence.assay):
        return False, "R-CTX-05"
    if claim.perturbation is not None:
        # MUTATION-POINT: R-CTX-06 -- a specified perturbation must match
        # the cited record's perturbation string exactly.
        if claim.perturbation != evidence.perturbation:
            return False, "R-CTX-06"
    return True, None


def context_matched(
    claim: CanonicalClaim, candidates: Sequence[CitedRecord], snapshot: SnapshotBundle
) -> list[CitedRecord]:
    """Subset of `candidates` whose context fully matches the claim's (R-CTX-01..06)."""
    return [c for c in candidates if context_ok(claim, c.canonical, snapshot)[0]]


def sign_matched(claim: CanonicalClaim, candidates: Sequence[CitedRecord]) -> list[CitedRecord]:
    """Subset with the correct `effect.sign` for `increases`/`decreases` (R-SIGN-01).

    A no-op filter (returns `candidates` unchanged) for every other
    relation, since sign comparison is only defined for increases/decreases.
    """
    wanted = RELATION_CANONICAL_SIGN.get(claim.relation)
    if wanted is None:
        return list(candidates)
    return [c for c in candidates if c.canonical.effect is not None and c.canonical.effect.sign == wanted]


def causal_matched(claim: CanonicalClaim, candidates: Sequence[CitedRecord]) -> list[CitedRecord]:
    """Subset that is `observation_type == interventional`, when `relation == causes`.

    A no-op filter for every other relation.
    """
    if claim.relation != "causes":
        return list(candidates)
    return [c for c in candidates if c.canonical.observation_type == "interventional"]


def edge_and_context_matched(
    claim: CanonicalClaim, cited: Sequence[CitedRecord], snapshot: SnapshotBundle
) -> list[CitedRecord]:
    """The full R-EDGE + R-CTX narrowing pipeline, in cascade order."""
    return context_matched(claim, pair_matched(claim, edge_type_matched(claim, cited)), snapshot)
