"""§0 Coverage envelope -- R-SCOPE-90, R-SCOPE-91.

Runs at cascade position 3 (after R-CITE-* and R-ENT-*, before R-REL-*).
"""

from __future__ import annotations

from typing import Sequence

from evidence.snapshot import SnapshotBundle
from normalize import CanonicalClaim

from ..cited import CitedRecord
from ..types import Reason
from ._shared import RELATION_LICENSING_RECORD_TYPES

_HUMAN = "NCBITaxon:9606"


def check(
    claim: CanonicalClaim, cited: Sequence[CitedRecord], snapshot: SnapshotBundle
) -> Reason | None:
    # MUTATION-POINT: only the declared pilot species is in scope.
    if claim.species != _HUMAN:
        return Reason(
            rule_id="R-SCOPE-90",
            message=f"species {claim.species!r} is outside the human-only coverage envelope ({_HUMAN})",
        )

    # RULES-DECISION: `EvidenceLedger` exposes no whole-ledger scan (only
    # `.get()`, `.list_by(subject, object)`, `.count()`,
    # `.snapshot_hashes()`), so a literal "is this assay class present in
    # ANY frozen source" check is not queryable in general -- there is no
    # by-record-type index available. We use the one global signal the
    # ledger interface *does* expose, `EvidenceLedger.count()`, as the
    # closest reachable approximation of "nothing is snapshotted at all"
    # for a relation that requires record-backed evidence. In
    # `tests/fixtures/synthetic_world` the ledger holds 6 records spanning
    # every relation's required record-type family (perturbation_effect,
    # expression_observation, physical_interaction), so this never fires
    # there -- consistent with `expectations.jsonl`'s single OUT_OF_SCOPE
    # adversarial fixture exercising R-SCOPE-90 (species) rather than
    # R-SCOPE-91. `edges.py`'s R-EDGE-01 is what actually rejects
    # UNSUPPORTED_EDGE when a specific claim's *cited* evidence lacks the
    # right record_type despite the ledger holding one elsewhere.
    required = RELATION_LICENSING_RECORD_TYPES.get(claim.relation, frozenset())
    # MUTATION-POINT: an empty ledger cannot license any relation that
    # requires evidence at all.
    if required and snapshot.ledger.count() == 0:
        return Reason(
            rule_id="R-SCOPE-91",
            message=f"relation {claim.relation!r} requires evidence of type {sorted(required)}, "
            f"but the frozen ledger holds zero records of any type",
        )
    return None
