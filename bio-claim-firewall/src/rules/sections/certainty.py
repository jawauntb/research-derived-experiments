"""§8 Certainty ladder -- R-CERT-01, R-CERT-02.

# RULES-DECISION: by the time the cascade reaches this section, `edges.py`
# and `context.py` have already guaranteed
# `_shared.edge_and_context_matched(...)` is non-empty (otherwise
# UNSUPPORTED_EDGE or CONTEXT_MISMATCH would already have stopped the
# cascade earlier) -- so the tier computation below never needs an
# "empty evidence" branch.
#
# RULES-DECISION: R-CERT-02's condition ("confidence_language=causal and
# no cited evidence is interventional") is a strict SUBSET of R-CERT-01's
# ("confidence_language rank exceeds the evidence tier"): `_tier()` always
# returns 1 (the lowest tier) when there is no interventional evidence,
# and rank("causal")=3 always exceeds tier 1 -- so whenever R-CERT-02
# would fire, R-CERT-01 already does too. Checking R-CERT-01 first (as an
# earlier draft did) would make R-CERT-02 unreachable even in isolated
# section-level testing, on top of being unreachable through the full
# cascade (R-CAUS-03 already catches it at position 8, per spec's own
# "verdict picks R-CAUS-03 as more specific"). We check the more specific
# R-CERT-02 condition first, so it is at least independently
# mutation-testable the way `sections/relations.py`'s R-REL-02/R-REL-01
# ordering is.
"""

from __future__ import annotations

from typing import Sequence

from evidence.snapshot import SnapshotBundle
from normalize import CanonicalClaim

from ..cited import CitedRecord
from ..types import Reason
from ._shared import edge_and_context_matched

_RANK: dict[str, int] = {"observed": 1, "supported": 2, "suggestive": 3, "causal": 3}


def _tier(claim: CanonicalClaim, matched: Sequence[CitedRecord]) -> int:
    interventional = [c for c in matched if c.canonical.observation_type == "interventional"]
    if not interventional:
        return 1  # observational only
    distinct_studies = {c.canonical.source_citation or c.canonical.source for c in interventional}
    distinct_lines = {c.canonical.cell_line for c in interventional}
    if len(interventional) >= 2 and (len(distinct_studies) >= 2 or len(distinct_lines) >= 2):
        return 3  # replicated across studies or cell lines
    return 2  # single-study interventional


def check_all(
    claim: CanonicalClaim, cited: Sequence[CitedRecord], snapshot: SnapshotBundle
) -> list[Reason]:
    matched = edge_and_context_matched(claim, cited, snapshot)

    interventional = [c for c in matched if c.canonical.observation_type == "interventional"]
    # MUTATION-POINT: confidence_language=causal always requires at least
    # one interventional record (subsumes R-CAUS-03, which -- running
    # earlier in the cascade -- fires first for any claim this would also
    # catch; checked first here so it remains independently
    # mutation-testable -- see the RULES-DECISION above).
    if claim.confidence_language == "causal" and not interventional:
        return [
            Reason(
                rule_id="R-CERT-02",
                message="confidence_language=causal but no cited evidence is interventional",
            )
        ]

    tier = _tier(claim, matched)
    # MUTATION-POINT: the claim's own confidence_language rank must not
    # exceed what the evidence tier actually supports.
    if _RANK[claim.confidence_language] > tier:
        return [
            Reason(
                rule_id="R-CERT-01",
                message=(
                    f"confidence_language={claim.confidence_language!r} exceeds what the "
                    f"accepted evidence set (tier {tier}) supports"
                ),
            )
        ]
    return []
