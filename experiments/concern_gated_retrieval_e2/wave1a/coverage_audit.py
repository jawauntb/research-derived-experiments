"""COGR-E2a coverage audit (Wave 1a scaffold).

Wave 1a's fatal Coverage gate (``PREREGISTRATION.md`` §5.1) is enforced
here. Every ``(family, condition)`` cell that logs receipts must clear a
propensity-weighted coverage floor of the true commitment region before
its IPS / DR estimates enter an aggregated statistic. This module
supplies the two callables the sweep runner uses:

* :func:`propensity_weighted_coverage` — computes
  ``coverage_{f,c} = ( Σ 1[r.candidate ∈ TCR(f)] / r.selection_propensity )
                       / len(receipts_{f,c})``
  for one cell.
* :func:`audit_coverage` — takes the receipts of one cell, a target
  region, and a floor, and returns a :class:`CoverageVerdict` on pass or
  raises :class:`CoverageAuditFailure` on breach.

Reuse boundary
--------------

The audit consumes only the policy-visible
:class:`~experiments.concern_gated_retrieval_e2.wave0.concern_update.ProbeReceipt`
fields — ``candidate`` and ``selection_propensity``. It never touches
the sealed :class:`EpisodeSpec`; ``role``, ``utility``, and
``_answer_key`` are enforced-out at the sealed-env boundary and would in
any case be structurally invisible here. The ``target_region`` argument
is the caller's pre-computed set of node ids that populate the true
commitment region for the family the cell was drawn from — the runner
resolves this from the evaluator side before invoking the audit.

Wave 1a scope
-------------

This module is scaffolding. Wave 1a experiment logic (the sweep, the
paired-seed variance estimator, the specificity check) lives in
sibling modules. Wave 1a is a screen for the concern-update rule; a
coverage breach is one of several fatal gates that can KILL the rule as
written. Per the honor-the-preregistration rule (human director's
memory ``feedback-honor-pre-registration``), only the knobs
``PREREGISTRATION.md`` §7 explicitly names as replayable may be rerun
after a KILL.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import AbstractSet, Iterable, Sequence

from experiments.concern_gated_retrieval_e2.wave0.concern_update import ProbeReceipt

__all__ = [
    "CoverageAuditFailure",
    "CoverageVerdict",
    "audit_coverage",
    "propensity_weighted_coverage",
]


#: Default coverage floor inherited from ``PREREGISTRATION.md`` §5.1. The
#: floor is derived from Wave 0's frozen ``DEFAULT_EPSILON = 0.05`` and
#: the confirmatory candidate cardinality (``|candidate_nodes| ≤ 20``):
#: ``epsilon * 1 / 20 = 0.0025`` lower bound, floor set at ``~4×`` that,
#: i.e. ``0.01``. The audit callers pass this in explicitly; the
#: constant is exposed for the sweep runner.
DEFAULT_COVERAGE_FLOOR: float = 0.01


class CoverageAuditFailure(RuntimeError):
    """Raised when the propensity-weighted coverage falls below the floor.

    The exception carries the numeric verdict on ``.verdict`` so callers
    can inspect the failing cell without re-running the audit. Message
    text is stable so downstream receipts can regex-match on it.
    """

    def __init__(self, message: str, *, verdict: "CoverageVerdict") -> None:
        super().__init__(message)
        self.verdict = verdict


@dataclass(frozen=True)
class CoverageVerdict:
    """Outcome of one coverage audit call.

    Attributes
    ----------
    passed:
        ``True`` iff ``coverage >= floor``. Callers of
        :func:`audit_coverage` only see a ``passed=True`` verdict —
        failures raise :class:`CoverageAuditFailure`.
    coverage:
        The propensity-weighted coverage computed by
        :func:`propensity_weighted_coverage`.
    floor:
        The floor the coverage was compared against. Preserved on the
        verdict so downstream receipts capture the exact threshold used.
    n_receipts:
        The number of receipts the coverage was averaged over. Aids
        diagnosis of a degenerate empty-cell case (``n_receipts == 0``,
        which is treated as an automatic failure).
    n_hits:
        The number of receipts whose ``candidate`` fell inside the
        ``target_region``. Reported separately from the coverage
        numerator to expose the ``epsilon``-random-branch coverage rate
        the runner can compare against ``DEFAULT_EPSILON``.
    """

    passed: bool
    coverage: float
    floor: float
    n_receipts: int
    n_hits: int


def _iter_receipts(receipts: Iterable[ProbeReceipt]) -> Sequence[ProbeReceipt]:
    """Materialise ``receipts`` as a validated sequence.

    Raises :class:`TypeError` if any element is not a
    :class:`ProbeReceipt`. The audit intentionally *does not* enforce a
    homogeneous ``template_family_split`` here — the sweep runner already
    partitions by ``(family, condition)`` cell before calling into
    :func:`audit_coverage`, and enforcing a homogeneous split at this
    layer would double-cover the guard on the update path.
    """
    materialised: list[ProbeReceipt] = []
    for i, r in enumerate(receipts):
        if not isinstance(r, ProbeReceipt):
            raise TypeError(f"receipts[{i}] is not a ProbeReceipt")
        materialised.append(r)
    return tuple(materialised)


def _validate_target_region(target_region: AbstractSet[str]) -> frozenset[str]:
    """Return a validated :class:`frozenset` copy of ``target_region``."""
    frozen: frozenset[str] = frozenset(target_region)
    for node in frozen:
        if not isinstance(node, str) or not node:
            raise ValueError(
                "target_region members must be non-empty strings; got "
                f"{node!r}"
            )
    return frozen


def propensity_weighted_coverage(
    receipts: Iterable[ProbeReceipt],
    target_region: AbstractSet[str],
) -> float:
    """Return ``coverage_{f,c}`` for one Wave 1a cell.

    Formula (``PREREGISTRATION.md`` §5.1)::

        coverage = ( Σ_{r ∈ receipts} 1[r.candidate ∈ target_region]
                                        / r.selection_propensity )
                    / len(receipts)

    ``ProbeReceipt.__post_init__`` guarantees every
    ``selection_propensity`` sits strictly in ``(0, 1]``, so the division
    is well-posed. An empty ``receipts`` returns ``0.0`` — the fatal
    Coverage gate treats an empty cell as an automatic failure.

    Parameters
    ----------
    receipts:
        Iterable of receipts drawn from one ``(family, condition)`` cell.
        The audit does not enforce homogeneity of family / condition here
        — the runner is responsible for partitioning before calling in.
    target_region:
        The true commitment region for the cell's family. The runner
        resolves this evaluator-side.

    Returns
    -------
    float
        The propensity-weighted coverage as a non-negative real number.
    """
    materialised = _iter_receipts(receipts)
    frozen_region = _validate_target_region(target_region)
    if not materialised:
        return 0.0
    numerator = 0.0
    for r in materialised:
        # ProbeReceipt guarantees strict positivity of selection_propensity.
        if r.candidate in frozen_region:
            numerator += 1.0 / float(r.selection_propensity)
    coverage = numerator / float(len(materialised))
    if not math.isfinite(coverage):
        # Only reachable if a caller-supplied propensity was pathological;
        # ProbeReceipt guards against this but a defence-in-depth
        # collapse-to-zero keeps the audit shape-stable.
        return 0.0
    return coverage


def audit_coverage(
    receipts: Iterable[ProbeReceipt],
    target_region: AbstractSet[str],
    *,
    floor: float = DEFAULT_COVERAGE_FLOOR,
) -> CoverageVerdict:
    """Return a :class:`CoverageVerdict` on pass; raise on floor breach.

    Wave 1a's fatal Coverage gate (``PREREGISTRATION.md`` §5.1) requires
    ``coverage_{f,c} >= floor`` for every receipt-producing ``(family,
    condition)`` cell. On breach this function raises
    :class:`CoverageAuditFailure` carrying the numeric verdict; on pass
    it returns the verdict. The floor defaults to
    :data:`DEFAULT_COVERAGE_FLOOR` (``0.01``).

    An empty ``receipts`` is an automatic failure — the sweep runner
    should never pass zero receipts through; the check catches a
    degenerate empty-cell case with the same shape as a real breach so
    callers do not have to special-case it.
    """
    if not math.isfinite(float(floor)) or float(floor) < 0.0:
        raise ValueError("floor must be a non-negative finite real")
    materialised = _iter_receipts(receipts)
    frozen_region = _validate_target_region(target_region)
    coverage = propensity_weighted_coverage(materialised, frozen_region)
    n_hits = sum(1 for r in materialised if r.candidate in frozen_region)
    verdict = CoverageVerdict(
        passed=coverage >= float(floor) and len(materialised) > 0,
        coverage=float(coverage),
        floor=float(floor),
        n_receipts=len(materialised),
        n_hits=int(n_hits),
    )
    if not verdict.passed:
        raise CoverageAuditFailure(
            "Wave 1a coverage floor breached: "
            f"coverage={verdict.coverage:.6f} < floor={verdict.floor:.6f} "
            f"(n_receipts={verdict.n_receipts}, n_hits={verdict.n_hits}); "
            "see wave1a/PREREGISTRATION.md §5.1",
            verdict=verdict,
        )
    return verdict
