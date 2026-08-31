"""§2 Evidence licensing -- R-EDGE-01, R-EDGE-02."""

from __future__ import annotations

from typing import Sequence

from evidence.snapshot import SnapshotBundle
from normalize import CanonicalClaim

from ..cited import CitedRecord
from ..types import Reason
from ._shared import RELATION_LICENSING_RECORD_TYPES, edge_type_matched, pair_matched


def check_all(
    claim: CanonicalClaim, cited: Sequence[CitedRecord], snapshot: SnapshotBundle
) -> list[Reason]:
    type_matched = edge_type_matched(claim, cited)
    # MUTATION-POINT: at least one cited record must have a record_type in
    # the relation's licensing set.
    if not type_matched:
        allowed = sorted(RELATION_LICENSING_RECORD_TYPES.get(claim.relation, frozenset()))
        return [
            Reason(
                rule_id="R-EDGE-01",
                message=f"no cited evidence record has a record_type in {allowed} "
                f"(required to license relation {claim.relation!r})",
                evidence_id=cited[0].evidence_id if cited else None,
            )
        ]

    matched = pair_matched(claim, type_matched)
    # MUTATION-POINT: among the record-type-eligible citations, at least
    # one must actually name the claim's (subject, object) pair.
    if not matched:
        return [
            Reason(
                rule_id="R-EDGE-02",
                message=(
                    f"cited record(s) of the right type do not name the claim's "
                    f"(subject={claim.subject_id!r}, object={claim.object_id!r}) pair"
                ),
                evidence_id=type_matched[0].evidence_id,
            )
        ]
    return []
