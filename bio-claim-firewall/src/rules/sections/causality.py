"""§4 Causality -- R-CAUS-01, R-CAUS-02, R-CAUS-03, R-CAUS-04.

Checked in rule-number order; the first that fires stops the section (and,
per the fixed cascade, the whole engine). R-CAUS-04's positive case does
not produce a `Reason` at all -- when it is satisfied, `established` is
simply allowed and the cascade proceeds to R-SCOPE-01..03.

# RULES-DECISION: R-CAUS-04 maps to `fault_code=SCOPE_OVERCLAIM`, not
# `CAUSALITY_OVERCLAIM`, per the rule text's own parenthetical ("also
# fires SCOPE_OVERCLAIM if requested_status was established") and per
# `SCOPE_OVERCLAIM__invalid.json`'s expectation
# (`expected_fault_code: SCOPE_OVERCLAIM`, `expected_rule_id_prefix:
# R-CAUS-`). `RuleEngine` looks this up from a single rule_id ->
# fault_code table rather than assuming "one section == one fault code".
#
# RULES-DECISION: R-CAUS-01, R-CAUS-02, and R-CAUS-04's own text all
# explicitly condition on `relation == causes`. R-CAUS-03's does not
# ("confidence_language==causal and no cited evidence has
# observation_type==interventional" -- no relation clause at all); that is
# exactly why spec/inference_rules.md §8 can say R-CERT-02 "subsumes
# R-CAUS-03" as a general statement, not one scoped to `causes` claims.
# Gating this whole section on `relation == causes` up front (as an
# earlier draft did) would make R-CAUS-03 unreachable for every other
# relation and turn the "R-CAUS-03 fires before R-CERT-02" cascade-order
# guarantee into dead code. So only the R-CAUS-01/02/04 checks are gated
# on `relation == causes`; R-CAUS-03 is checked unconditionally.
"""

from __future__ import annotations

from typing import Sequence

from evidence.snapshot import SnapshotBundle
from normalize import CanonicalClaim

from ..cited import CitedRecord
from ..types import Reason

_DIFFERENT_MODALITY_PAIR_HINT = (
    "two interventional records in different cell lines, or the same cell line across two "
    "perturbation modalities"
)


def _distinct_cell_lines(records: Sequence[CitedRecord]) -> set[str | None]:
    return {r.canonical.cell_line for r in records}


def _distinct_perturbation_modalities(records: Sequence[CitedRecord]) -> set[str | None]:
    # RULES-DECISION: "perturbation modality" is approximated by the
    # assay string itself (e.g. "CRISPRi_screen" vs "siRNA_knockdown") --
    # the closest field the canonical evidence model carries for "how the
    # perturbation was delivered." No fixture exercises the
    # same-cell-line-two-modalities branch, so this is a best-effort,
    # documented reading rather than one anchored to a passing test.
    return {r.canonical.assay for r in records}


def check_all(
    claim: CanonicalClaim, cited: Sequence[CitedRecord], snapshot: SnapshotBundle
) -> list[Reason]:
    if claim.relation == "causes":
        observational = [c for c in cited if c.canonical.observation_type == "observational"]
        # MUTATION-POINT: any observational citation on a `causes` claim overclaims.
        if observational:
            return [
                Reason(
                    rule_id="R-CAUS-01",
                    message=f"relation=causes but evidence_id={observational[0].evidence_id!r} is observational",
                    evidence_id=observational[0].evidence_id,
                )
            ]

        # MUTATION-POINT: `causes` requires a named intervention.
        if claim.perturbation is None:
            return [
                Reason(
                    rule_id="R-CAUS-02",
                    message="relation=causes requires assay_context.perturbation to be non-null",
                )
            ]

    interventional = [c for c in cited if c.canonical.observation_type == "interventional"]
    # MUTATION-POINT: confidence_language=causal requires at least one
    # interventional citation, for ANY relation (also see R-CERT-02, which
    # subsumes this but sits later in the cascade -- see the
    # RULES-DECISION above).
    if claim.confidence_language == "causal" and not interventional:
        return [
            Reason(
                rule_id="R-CAUS-03",
                message="confidence_language=causal but no cited evidence is interventional",
            )
        ]

    if claim.relation == "causes" and claim.requested_status == "established":
        distinct_lines = _distinct_cell_lines(interventional)
        distinct_modalities = _distinct_perturbation_modalities(interventional)
        replicated = len(interventional) >= 2 and (
            len(distinct_lines) >= 2 or (len(distinct_lines) == 1 and len(distinct_modalities) >= 2)
        )
        # MUTATION-POINT: established causes claims need real replication
        # across cell lines (or perturbation modalities within one line),
        # not just a single interventional record.
        if not replicated:
            return [
                Reason(
                    rule_id="R-CAUS-04",
                    message=(
                        f"requested_status=established on a causes claim requires "
                        f"{_DIFFERENT_MODALITY_PAIR_HINT}; found {len(interventional)} "
                        f"interventional record(s) across {len(distinct_lines)} cell line(s)"
                    ),
                )
            ]

    return []
