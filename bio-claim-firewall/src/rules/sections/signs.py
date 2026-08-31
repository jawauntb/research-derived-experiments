"""§3 Sign matching -- R-SIGN-01, R-SIGN-02.

`check()` returns `(reason, inconclusive)` rather than plain `Reason |
None`: R-SIGN-02's own text carves out a third outcome besides "fires" /
"doesn't fire" -- a zero or directionless (`effect.sign == "null"`)
correlation is `INCONCLUSIVE`, not `SIGN_MISMATCH`. `RuleEngine.run()`
terminates the whole cascade on that signal (verdict=INCONCLUSIVE)
instead of treating it as "this section found nothing, keep going."

# RULES-DECISION: `evidence.schema.json`'s `effect.magnitude` is a
# required, non-nullable `number` -- there is no JSON `null` magnitude to
# compare against. `CanonicalEffect.sign`, however, keeps the schema's
# literal string `"null"` as a distinct enum value from Python `None`
# (see `normalize/types.py`'s own NORMALIZE-DECISION) -- exactly the
# "measured but directionless" case the rule text's "or null" refers to.
# So the INCONCLUSIVE carve-out fires on `magnitude == 0.0` OR
# `effect.sign == "null"`, not on any Python-`None` check.
"""

from __future__ import annotations

from typing import Sequence

from evidence.snapshot import SnapshotBundle
from normalize import CanonicalClaim

from ..cited import CitedRecord
from ..types import Reason
from ._shared import RELATION_CANONICAL_SIGN, edge_and_context_matched


def check(
    claim: CanonicalClaim, cited: Sequence[CitedRecord], snapshot: SnapshotBundle
) -> tuple[Reason | None, bool]:
    """Returns `(reason_or_none, inconclusive)`; `inconclusive=True` implies `reason is None`."""
    candidates = edge_and_context_matched(claim, cited, snapshot)
    if not candidates:
        return None, False  # nothing to compare; edges.py/context.py already gate this

    if claim.relation in RELATION_CANONICAL_SIGN:
        wanted = RELATION_CANONICAL_SIGN[claim.relation]
        matched = [c for c in candidates if c.canonical.effect is not None and c.canonical.effect.sign == wanted]
        # MUTATION-POINT: relation=increases/decreases requires the cited
        # effect's sign to match the relation's canonical direction.
        if matched:
            return None, False
        first = candidates[0]
        return (
            Reason(
                rule_id="R-SIGN-01",
                message=(
                    f"relation {claim.relation!r} requires effect.sign={wanted!r}, but no "
                    f"edge-eligible cited record has that sign (evidence_id={first.evidence_id!r})"
                ),
                evidence_id=first.evidence_id,
            ),
            False,
        )

    if claim.relation == "correlates_with":
        wants_positive = claim.polarity == "positive"
        matched = [
            c
            for c in candidates
            if c.canonical.effect is not None
            and (c.canonical.effect.magnitude > 0 if wants_positive else c.canonical.effect.magnitude < 0)
        ]
        # MUTATION-POINT: correlates_with requires a nonzero magnitude with
        # the sign the claim's polarity asserts.
        if matched:
            return None, False

        # MUTATION-POINT: zero magnitude or an explicitly directionless
        # sign is INCONCLUSIVE, not SIGN_MISMATCH -- R-SIGN-02's carve-out.
        zero_or_directionless = any(
            c.canonical.effect is not None and (c.canonical.effect.magnitude == 0.0 or c.canonical.effect.sign == "null")
            for c in candidates
        )
        if zero_or_directionless:
            return None, True

        first = candidates[0]
        return (
            Reason(
                rule_id="R-SIGN-02",
                message=(
                    f"correlates_with polarity={claim.polarity!r} requires a "
                    f"{'positive' if wants_positive else 'negative'} magnitude, but the cited "
                    f"record's magnitude disagrees (evidence_id={first.evidence_id!r})"
                ),
                evidence_id=first.evidence_id,
            ),
            False,
        )

    return None, False
