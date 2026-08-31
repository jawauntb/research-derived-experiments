"""§5 Context matching -- R-CTX-01..06."""

from __future__ import annotations

from typing import Sequence

from evidence.snapshot import SnapshotBundle
from normalize import CanonicalClaim

from ..cited import CitedRecord
from ..types import Reason
from ._shared import context_matched, context_ok, edge_type_matched, pair_matched

_MESSAGES: dict[str, str] = {
    "R-CTX-01": "species differs from the cited record",
    "R-CTX-02": "cell_context.cell_type is neither equal to, nor a Cell-Ontology ancestor of, the cited record's cell_type",
    "R-CTX-03": "cell_context.cell_line is specified and does not equal the cited record's cell_line",
    "R-CTX-04": "cell_context.state is specified and does not equal the cited record's state",
    "R-CTX-05": "assay_context.assay differs from the cited record's assay and the two are not assay-equivalent",
    "R-CTX-06": "assay_context.perturbation is specified and does not match the cited record's perturbation",
}


def check(
    claim: CanonicalClaim, cited: Sequence[CitedRecord], snapshot: SnapshotBundle
) -> Reason | None:
    """Fires iff NOT ONE edge-eligible cited record's context matches the claim.

    Operates on the R-EDGE-eligible subset (right record_type, right
    (subject, object) pair) -- a record of the wrong type/pair was already
    rejected upstream by `edges.py` (or the cascade wouldn't have reached
    this section at all), so it isn't a meaningful context comparison
    target here.
    """
    edge_eligible = pair_matched(claim, edge_type_matched(claim, cited))
    if not edge_eligible:
        return None  # nothing to compare; edges.py already gates this case

    # MUTATION-POINT: at least one edge-eligible cited record must satisfy
    # every applicable context dimension.
    if context_matched(claim, edge_eligible, snapshot):
        return None

    # Report the first edge-eligible record's first failing dimension, in
    # citation order, as the representative finding.
    first = edge_eligible[0]
    _, rule_id = context_ok(claim, first.canonical, snapshot)
    assert rule_id is not None  # nosec: context_matched() being empty guarantees a failing rule_id
    return Reason(
        rule_id=rule_id,
        message=f"{_MESSAGES[rule_id]} (evidence_id={first.evidence_id!r})",
        evidence_id=first.evidence_id,
    )
