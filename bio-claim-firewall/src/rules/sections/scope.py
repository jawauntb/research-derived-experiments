"""§6 Scope -- R-SCOPE-01, R-SCOPE-02, R-SCOPE-03.

# RULES-DECISION: `causes` claims are entirely exempted from R-SCOPE-01/02
# here. `causality.py`'s R-CAUS-04 already owns establishment-tier gating
# for `causes` specifically (and runs earlier in the cascade, §4 before
# §6), and its replication requirement is *stricter* than the generic
# "more than one study/cell_line" check below. Spec text for R-SCOPE-02
# says as much directly: "(Same as R-CAUS-04 for causes; here it applies
# to all relations.)" -- read as "R-SCOPE-01/02 generalize CAUS-04's idea
# to non-causes relations", not "re-apply a weaker version on top of it".
# `SCOPE_OVERCLAIM__valid.json` is the concrete case this avoids breaking:
# it is a `causes` claim licensed via R-CAUS-04's two-different-cell-lines
# path with both citations sharing the same `source` (so a naive
# study-id proxy below would wrongly re-reject it as single-study).
"""

from __future__ import annotations

from typing import Sequence

from evidence.snapshot import SnapshotBundle
from normalize import CanonicalClaim

from ..cited import CitedRecord
from ..types import Reason
from ._shared import edge_and_context_matched

_UNSPECIFIED = "unspecified"


def _study_key(record: CitedRecord) -> str:
    # RULES-DECISION: no dedicated "study id" field exists on
    # CanonicalEvidence; `source_citation` (the human study citation) is
    # the closest proxy, falling back to `source` (the ledger source name)
    # when the citation is null -- both are None-safe strings.
    return record.canonical.source_citation or record.canonical.source


def check_all(
    claim: CanonicalClaim, cited: Sequence[CitedRecord], snapshot: SnapshotBundle
) -> list[Reason]:
    matched = edge_and_context_matched(claim, cited, snapshot)

    if claim.requested_status == "established" and claim.relation != "causes":
        distinct_studies = {_study_key(c) for c in matched}
        # MUTATION-POINT: established requires more than one distinct study.
        if len(distinct_studies) <= 1:
            return [
                Reason(
                    rule_id="R-SCOPE-01",
                    message="requested_status=established but the accepted evidence set spans only one study",
                )
            ]

        distinct_lines = {c.canonical.cell_line for c in matched}
        # MUTATION-POINT: established requires more than one distinct cell_line.
        if len(distinct_lines) <= 1:
            return [
                Reason(
                    rule_id="R-SCOPE-02",
                    message="requested_status=established but the accepted evidence set spans only one cell_line",
                )
            ]

    if claim.cell_type != _UNSPECIFIED and matched:
        matched_cell_types = {c.canonical.cell_type for c in matched}
        # MUTATION-POINT: the claim's own cell_type must have direct
        # support from at least one matched record; if every matched
        # record is strictly narrower, the claim has generalized beyond
        # what was actually measured, with no rule-book entry allowing it.
        if claim.cell_type not in matched_cell_types:
            return [
                Reason(
                    rule_id="R-SCOPE-03",
                    message=(
                        f"cell_context.cell_type={claim.cell_type!r} generalizes beyond every "
                        f"matched record's cell_type {sorted(matched_cell_types)} with no "
                        f"rule-book entry authorizing it"
                    ),
                )
            ]

    return []
