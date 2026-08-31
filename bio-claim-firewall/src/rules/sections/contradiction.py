"""§7 Contradiction -- R-CONTRA-01, R-CONTRA-02.

Checked against the R-EDGE + R-CTX matched subset (the records the claim
is actually relying on), using `EvidenceLedger.list_by(subject_id,
object_id)` to pull every other record the frozen ledger holds for the
same pair -- exactly the R-CONTRA-01 hook `src/INTERFACES.md` documents.
"""

from __future__ import annotations

from typing import Any, Sequence

from evidence.snapshot import SnapshotBundle
from normalize import CanonicalClaim

from ..cited import CitedRecord
from ..types import Reason
from ._shared import edge_and_context_matched

_RANKED_SIGNS = frozenset({"positive", "negative"})
_OUTRANKS = {"interventional": 1, "observational": 0}


def _check_record(record: CitedRecord, snapshot: SnapshotBundle) -> Reason | None:
    same_pair: list[dict[str, Any]] = snapshot.ledger.list_by(
        record.canonical.subject_id, record.canonical.object_id
    )

    for other in same_pair:
        if other.get("evidence_id") == record.evidence_id:
            continue
        # MUTATION-POINT: an explicit `contradicts` back-reference to the
        # cited record is a direct, curator-asserted contradiction.
        if record.evidence_id in other.get("contradicts", []):
            return Reason(
                rule_id="R-CONTRA-02",
                message=(
                    f"evidence_id={other.get('evidence_id')!r} lists cited "
                    f"evidence_id={record.evidence_id!r} in its contradicts array"
                ),
                evidence_id=record.evidence_id,
            )

    for other in same_pair:
        if other.get("evidence_id") == record.evidence_id:
            continue
        other_effect = other.get("effect")
        c_effect = record.canonical.effect
        if not other_effect or c_effect is None:
            continue
        other_sign = other_effect.get("sign")
        if other_sign not in _RANKED_SIGNS or c_effect.sign not in _RANKED_SIGNS:
            continue
        if other_sign == c_effect.sign:
            continue
        other_rank = _OUTRANKS.get(other.get("observation_type"), -1)
        c_rank = _OUTRANKS.get(record.canonical.observation_type, -1)
        # MUTATION-POINT: only a strictly higher-ranked opposite-sign
        # record contradicts the cited one (interventional outranks
        # observational); same-or-lower rank does not overrule it.
        if other_rank <= c_rank:
            continue
        if other.get("cell_context") != record.raw.get("cell_context"):
            continue
        if other.get("assay_context") != record.raw.get("assay_context"):
            continue
        return Reason(
            rule_id="R-CONTRA-01",
            message=(
                f"evidence_id={other.get('evidence_id')!r} reports the opposite sign under the "
                f"same context and outranks cited evidence_id={record.evidence_id!r}"
            ),
            evidence_id=record.evidence_id,
        )
    return None


def check(
    claim: CanonicalClaim, cited: Sequence[CitedRecord], snapshot: SnapshotBundle
) -> Reason | None:
    for record in edge_and_context_matched(claim, cited, snapshot):
        reason = _check_record(record, snapshot)
        if reason is not None:
            return reason
    return None
