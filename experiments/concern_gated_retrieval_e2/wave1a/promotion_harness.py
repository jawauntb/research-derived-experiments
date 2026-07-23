"""COGR-E2a Wave 1a promotion harness (screen scoring).

Wave 1a's promotion decision is non-compensatory: a single fatal gate
FAIL kills the wave (``PROMOTION_CONTRACT.md``).  This module supplies
the per-family scoring entry point ``score_e2a(report, thresholds)`` and
the frozen threshold container the sweep runner loads from
``PREREGISTRATION.md`` §6.2.

Gates scored here (family-scoped subset of the Wave 1a fatal gates):

* **G3 Specificity** (``PREREGISTRATION.md`` §5.3, ``PROMOTION_CONTRACT``
  G3).  For every ``(variant, comparator)`` in
  ``{ips, dr} × {info_matched_value, info_matched_priority,
  info_matched_recency}``, the variant's lower confidence bound
  (``mean_delta - 2 * cluster_robust_se``) must clear
  ``sigma_hat_best_matched_wave0``; AND the wrong-agent comparator's
  lower confidence bound must clear
  ``sigma_hat_multiplicative_wave0``.  A FAIL on ANY family, ANY
  variant, ANY comparator KILLs the screen.
* **G4 Per-family effect** (``PREREGISTRATION.md`` §6.3, ``PROMOTION_
  CONTRACT`` G4).  For at least one variant, the paired-seed lower
  confidence bound against ``frozen_wrong`` must meet
  ``delta_thresh_E2a_{f}``.  Aggregate success across variants at
  ``frozen_wrong`` is enough; both variants failing is a KILL.
* **No family reversal** (``PREREGISTRATION.md`` §5.4).  If both
  on-line-learned variants underperform ``frozen_wrong`` at any
  threshold-sized margin on the family, the screen KILLs regardless
  of the other two families.  This gate is family-scoped by design;
  the Wave 1a §5.4 "aggregate cannot hide a per-family reversal" rule
  is enforced at the aggregate scoring layer (:func:`score_e2a_all`).

Gates enforced elsewhere in Wave 1a (referenced but not scored here):

* G0 anti-leakage → ``IntegrityAudit`` at import and inside the runner.
* G1 coverage → :mod:`experiments.concern_gated_retrieval_e2.wave1a.coverage_audit`.
* G2 propensity accounting → Wave 0 ``update_concern`` guards + Modal
  sweep runner ESS receipt (Wave 1b build task).
* G5 seed independence → template-split guard.
* G6 code freeze → provenance signature.
* G7 Modal budget → sweep runner receipt.

Wave 1a scope
-------------

This harness CAN reject the concern-update rule.  It CANNOT establish
learned memory geometry, an L1 dual-source-retrieval mechanism claim,
or an L2 history-derived-concern-recovery claim (Wave 1b objects).
Per the honor-the-preregistration rule, only knobs in
``PREREGISTRATION.md`` §7 may be rerun after a KILL; the harness does
not implement replay logic — the sweep runner does.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final, Mapping

from experiments.concern_gated_retrieval_e2.wave1a.conditions import (
    ORACLE_CEILING,
    PromotionRefused,
)
from experiments.concern_gated_retrieval_e2.wave1a.coverage_audit import (
    DEFAULT_COVERAGE_FLOOR,
)
from experiments.concern_gated_retrieval_e2.wave1a.specificity import (
    ARM_FROZEN_WRONG,
    COMPARATOR_INFO_MATCHED_PRIORITY,
    COMPARATOR_INFO_MATCHED_RECENCY,
    COMPARATOR_INFO_MATCHED_VALUE,
    COMPARATOR_WRONG_AGENT,
    ContrastAggregate,
    SpecificityReport,
    VARIANTS,
    cluster_robust_se,
    compute_contrast_aggregate,
)

__all__ = [
    "FamilyThresholds",
    "FrozenThresholds",
    "GATE_ID_FAMILY_EFFECT",
    "GATE_ID_NO_FAMILY_REVERSAL",
    "GATE_ID_SPECIFICITY_GENERIC",
    "GATE_ID_SPECIFICITY_WRONG_AGENT",
    "GateResult",
    "INFO_MATCHED_COMPARATORS",
    "PromotionVerdict",
    "WAVE1A_PREREGISTERED_THRESHOLDS",
    "score_e2a",
    "score_e2a_all",
]


# --------------------------------------------------------------------------- #
# Gate identifiers (stable strings; downstream receipts regex-match these)
# --------------------------------------------------------------------------- #


GATE_ID_SPECIFICITY_GENERIC: Final[str] = "G3_SPECIFICITY_GENERIC"
GATE_ID_SPECIFICITY_WRONG_AGENT: Final[str] = "G3_SPECIFICITY_WRONG_AGENT"
GATE_ID_FAMILY_EFFECT: Final[str] = "G4_PER_FAMILY_EFFECT"
GATE_ID_NO_FAMILY_REVERSAL: Final[str] = "G4_NO_FAMILY_REVERSAL"


#: Info-matched comparators (excludes ``wrong_agent`` — the wrong-agent
#: gate has a different threshold, per ``PREREGISTRATION.md`` §5.3).
INFO_MATCHED_COMPARATORS: Final[tuple[str, ...]] = (
    COMPARATOR_INFO_MATCHED_VALUE,
    COMPARATOR_INFO_MATCHED_PRIORITY,
    COMPARATOR_INFO_MATCHED_RECENCY,
)


# --------------------------------------------------------------------------- #
# Threshold containers
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class FamilyThresholds:
    """Per-family frozen thresholds from ``PREREGISTRATION.md`` §6.2.

    Attributes
    ----------
    family:
        The Wave 0 procedural family this threshold row applies to.
    sigma_hat_multiplicative:
        Wave 0 calibration standard deviation of the multiplicative
        baseline — the wrong-agent margin the screen must exceed.
    sigma_hat_best_matched:
        Wave 0 calibration standard deviation of the best matched-
        budget baseline — the generic-signal margin the screen must
        exceed.
    delta_thresh_E2a:
        Per-family screening threshold frozen at
        ``max( 2 * sigma_hat_multiplicative / sqrt(N_per_family),
              0.10 * headroom_to_ceiling,
              2 * sigma_hat_best_matched )``.
        Values below the paired-seed lower bound KILL the screen on
        this family.
    coverage_floor:
        Wave 1a coverage floor (``PREREGISTRATION.md`` §5.1).  Kept on
        the row so the sweep runner has a single source of truth per
        family; the harness itself does not score coverage (that lives
        on ``coverage_audit.audit_coverage``).
    """

    family: str
    sigma_hat_multiplicative: float
    sigma_hat_best_matched: float
    delta_thresh_E2a: float
    coverage_floor: float = DEFAULT_COVERAGE_FLOOR

    def __post_init__(self) -> None:
        if not isinstance(self.family, str) or not self.family:
            raise ValueError("family must be a non-empty string")
        for name in (
            "sigma_hat_multiplicative",
            "sigma_hat_best_matched",
            "delta_thresh_E2a",
            "coverage_floor",
        ):
            value = getattr(self, name)
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise TypeError(f"{name} must be a real number")
            if value < 0:
                raise ValueError(f"{name} must be non-negative; got {value!r}")


@dataclass(frozen=True)
class FrozenThresholds:
    """Immutable container of per-family thresholds for the whole wave.

    Attributes
    ----------
    per_family:
        Frozen mapping from family name to :class:`FamilyThresholds`.
    """

    per_family: Mapping[str, FamilyThresholds]

    def __post_init__(self) -> None:
        if not isinstance(self.per_family, Mapping):
            raise TypeError("per_family must be a Mapping[str, FamilyThresholds]")
        for family, thresholds in self.per_family.items():
            if not isinstance(family, str) or not family:
                raise ValueError("per_family keys must be non-empty strings")
            if not isinstance(thresholds, FamilyThresholds):
                raise TypeError(
                    f"per_family[{family!r}] must be a FamilyThresholds"
                )
            if thresholds.family != family:
                raise ValueError(
                    f"per_family[{family!r}].family mismatch: "
                    f"{thresholds.family!r}"
                )
        object.__setattr__(
            self, "per_family", MappingProxyType(dict(self.per_family))
        )

    def for_family(self, family: str) -> FamilyThresholds:
        if family not in self.per_family:
            raise KeyError(
                f"no thresholds registered for family {family!r}; expected "
                f"one of {sorted(self.per_family)}"
            )
        return self.per_family[family]


#: Wave 1a preregistered thresholds pinned in ``PREREGISTRATION.md``
#: §6.2.  These values are authoritative once the preregistration is
#: signed (WAVE1A_ANALYSIS_HASH written into §8); a subsequent change
#: is a redesign, not an update.  Exposed so the sweep runner and Wave
#: 1b's inheritance clauses can consume the frozen numbers without
#: re-parsing the markdown.
WAVE1A_PREREGISTERED_THRESHOLDS: Final[FrozenThresholds] = FrozenThresholds(
    per_family={
        "delayed_commitments": FamilyThresholds(
            family="delayed_commitments",
            sigma_hat_multiplicative=0.2080,
            sigma_hat_best_matched=0.0218,
            delta_thresh_E2a=0.04845,
        ),
        "maintenance_fault": FamilyThresholds(
            family="maintenance_fault",
            sigma_hat_multiplicative=0.1483,
            sigma_hat_best_matched=0.0267,
            delta_thresh_E2a=0.05340,
        ),
        "resource_constrained": FamilyThresholds(
            family="resource_constrained",
            sigma_hat_multiplicative=0.2905,
            sigma_hat_best_matched=0.0250,
            delta_thresh_E2a=0.05000,
        ),
    }
)


# --------------------------------------------------------------------------- #
# Gate result + verdict
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class GateResult:
    """One gate's outcome inside a promotion verdict.

    Attributes
    ----------
    gate_id:
        Stable identifier — one of ``GATE_ID_*``.
    variant:
        The candidate variant this gate was evaluated against
        (``online_learned_ips`` / ``online_learned_dr``), or ``None``
        for gates evaluated at the family level rather than the
        variant level.
    passed:
        ``True`` iff the gate is cleared.
    detail:
        Human-readable one-line explanation.  Stable enough that
        receipts can regex-match; parseable numeric fields live on
        :attr:`metrics`.
    metrics:
        Frozen mapping of the numeric quantities the gate compared,
        e.g. ``{"lower_bound_2se": ..., "threshold": ...}``.
    """

    gate_id: str
    passed: bool
    detail: str
    variant: str | None = None
    metrics: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.gate_id, str) or not self.gate_id:
            raise ValueError("gate_id must be a non-empty string")
        if self.variant is not None and (
            not isinstance(self.variant, str) or not self.variant
        ):
            raise ValueError("variant must be a non-empty string or None")
        if not isinstance(self.metrics, Mapping):
            raise TypeError("metrics must be a Mapping")
        object.__setattr__(
            self, "metrics", MappingProxyType(dict(self.metrics))
        )


@dataclass(frozen=True)
class PromotionVerdict:
    """Non-compensatory promotion verdict.

    Attributes
    ----------
    promoted:
        ``True`` iff every fatal gate passed.  Non-compensatory: a
        single gate FAIL flips this to ``False``.
    kill_reasons:
        Ordered tuple of gate_ids that FAILed.  Empty on a promoted
        verdict.
    per_gate:
        Frozen mapping from ``"{gate_id}::{variant or 'family'}"`` to
        the corresponding :class:`GateResult`.
    passing_variants:
        The subset of variants (from :data:`VARIANTS`) that cleared
        every family-effect and specificity gate.  Empty on KILL.  On
        a PASS at least one variant is present.
    family:
        Family this verdict was scored for.
    """

    promoted: bool
    kill_reasons: tuple[str, ...]
    per_gate: Mapping[str, GateResult]
    passing_variants: tuple[str, ...]
    family: str

    def __post_init__(self) -> None:
        if not isinstance(self.family, str) or not self.family:
            raise ValueError("family must be a non-empty string")
        if not isinstance(self.per_gate, Mapping):
            raise TypeError("per_gate must be a Mapping")
        object.__setattr__(
            self, "per_gate", MappingProxyType(dict(self.per_gate))
        )
        if self.promoted and self.kill_reasons:
            raise ValueError(
                "PromotionVerdict.promoted=True is inconsistent with a "
                f"non-empty kill_reasons {self.kill_reasons!r}"
            )
        if not self.promoted and not self.kill_reasons:
            raise ValueError(
                "PromotionVerdict.promoted=False requires at least one "
                "kill reason (non-compensatory)"
            )


# --------------------------------------------------------------------------- #
# Internal helpers
# --------------------------------------------------------------------------- #


def _find_contrast(
    report: SpecificityReport, variant: str, comparator: str
) -> ContrastAggregate:
    """Return the pre-computed contrast for a variant / comparator pair.

    :class:`SpecificityReport` freezes its contrasts at construction; if
    a pair is missing (a Wave 1b caller inserting a partial slate) we
    fall back to computing on the fly from the report's rows so the
    scorer still has a shape-stable answer.  This never rebuilds a
    contrast that is already present.
    """

    for contrast in report.contrasts:
        if contrast.variant == variant and contrast.comparator == comparator:
            return contrast
    return compute_contrast_aggregate(
        report.rows, variant=variant, comparator=comparator
    )


def _gate_key(gate_id: str, variant: str | None) -> str:
    return f"{gate_id}::{variant or 'family'}"


def _score_specificity_generic_one(
    report: SpecificityReport,
    thresholds: FamilyThresholds,
    variant: str,
    comparator: str,
) -> GateResult:
    """Score the info-matched generic-signal gate for a single comparator."""

    threshold = float(thresholds.sigma_hat_best_matched)
    contrast = _find_contrast(report, variant, comparator)
    passed = contrast.lower_bound_2se >= threshold
    detail = (
        f"variant={variant} vs comparator={comparator}: "
        f"lower_bound_2se={contrast.lower_bound_2se:.6f} vs threshold="
        f"sigma_hat_best_matched_wave0={threshold:.6f} -> "
        f"{'PASS' if passed else 'FAIL'}"
    )
    return GateResult(
        gate_id=GATE_ID_SPECIFICITY_GENERIC,
        passed=passed,
        detail=detail,
        variant=variant,
        metrics={
            "mean_delta": contrast.mean_delta,
            "cluster_robust_se": contrast.cluster_robust_se,
            "lower_bound_2se": contrast.lower_bound_2se,
            "threshold": threshold,
            "n_clusters": float(contrast.n_clusters),
        },
    )


def _score_specificity_wrong_agent(
    report: SpecificityReport, thresholds: FamilyThresholds, variant: str
) -> GateResult:
    """Score the wrong-agent specificity gate."""

    contrast = _find_contrast(report, variant, COMPARATOR_WRONG_AGENT)
    threshold = float(thresholds.sigma_hat_multiplicative)
    passed = contrast.lower_bound_2se >= threshold
    detail = (
        f"variant={variant} vs wrong_agent: "
        f"lower_bound_2se={contrast.lower_bound_2se:.6f} vs threshold="
        f"sigma_hat_multiplicative_wave0={threshold:.6f} → "
        f"{'PASS' if passed else 'FAIL'}"
    )
    return GateResult(
        gate_id=GATE_ID_SPECIFICITY_WRONG_AGENT,
        passed=passed,
        detail=detail,
        variant=variant,
        metrics={
            "mean_delta": contrast.mean_delta,
            "cluster_robust_se": contrast.cluster_robust_se,
            "lower_bound_2se": contrast.lower_bound_2se,
            "threshold": threshold,
            "n_clusters": float(contrast.n_clusters),
        },
    )


def _paired_delta_vs_frozen_wrong(
    report: SpecificityReport, variant: str
) -> ContrastAggregate:
    """Compute a variant-vs-frozen_wrong paired-seed contrast.

    :class:`SpecificityReport.contrasts` only carries variant-vs-
    comparator pairs; the family-effect gate needs variant-vs-baseline.
    This helper does the aggregation on the fly and never mutates the
    report.
    """

    deltas: list[float] = []
    for row in report.rows:
        v_reward = float(row.rewards[variant])
        b_reward = float(row.rewards[ARM_FROZEN_WRONG])
        deltas.append(v_reward - b_reward)
    n = len(deltas)
    mean_delta = sum(deltas) / n if n > 0 else 0.0
    se = cluster_robust_se(deltas)
    return ContrastAggregate(
        variant=variant,
        comparator=ARM_FROZEN_WRONG,
        n_clusters=n,
        mean_delta=float(mean_delta),
        cluster_robust_se=float(se),
        lower_bound_2se=float(mean_delta - 2.0 * se),
    )


def _score_family_effect(
    report: SpecificityReport, thresholds: FamilyThresholds, variant: str
) -> GateResult:
    """Score the per-family-effect gate for one variant.

    Returns PASS iff the paired-seed lower confidence bound of
    ``variant`` against ``frozen_wrong`` meets or exceeds
    ``delta_thresh_E2a_{f}``.
    """

    contrast = _paired_delta_vs_frozen_wrong(report, variant)
    threshold = float(thresholds.delta_thresh_E2a)
    passed = contrast.lower_bound_2se >= threshold
    detail = (
        f"variant={variant} vs frozen_wrong: "
        f"lower_bound_2se={contrast.lower_bound_2se:.6f} vs threshold="
        f"delta_thresh_E2a={threshold:.6f} → "
        f"{'PASS' if passed else 'FAIL'}"
    )
    return GateResult(
        gate_id=GATE_ID_FAMILY_EFFECT,
        passed=passed,
        detail=detail,
        variant=variant,
        metrics={
            "mean_delta": contrast.mean_delta,
            "cluster_robust_se": contrast.cluster_robust_se,
            "lower_bound_2se": contrast.lower_bound_2se,
            "threshold": threshold,
            "n_clusters": float(contrast.n_clusters),
        },
    )


def _score_no_family_reversal(
    report: SpecificityReport, thresholds: FamilyThresholds
) -> GateResult:
    """Score the "aggregate cannot hide a per-family reversal" gate.

    A reversal is: on this family, BOTH on-line-learned variants have a
    paired-seed mean delta against ``frozen_wrong`` less than or equal
    to ``-delta_thresh_E2a_{f}`` (a threshold-sized margin, per
    ``PREREGISTRATION.md`` §5.4).  If either variant clears zero, the
    reversal gate PASSes for that family.  If both are threshold-sized
    below zero, the family FAILs regardless of the other two.
    """

    threshold = float(thresholds.delta_thresh_E2a)
    per_variant: dict[str, float] = {}
    for variant in VARIANTS:
        per_variant[variant] = float(
            _paired_delta_vs_frozen_wrong(report, variant).mean_delta
        )
    # Reversal detected if EVERY variant is below -threshold.
    all_below = all(delta <= -threshold for delta in per_variant.values())
    passed = not all_below
    detail = (
        "family reversal check: "
        + "; ".join(
            f"{variant}: mean_delta={delta:.6f}"
            for variant, delta in per_variant.items()
        )
        + f"; threshold={threshold:.6f} → {'PASS' if passed else 'FAIL'}"
    )
    return GateResult(
        gate_id=GATE_ID_NO_FAMILY_REVERSAL,
        passed=passed,
        detail=detail,
        variant=None,
        metrics={
            **{
                f"mean_delta::{variant}": delta
                for variant, delta in per_variant.items()
            },
            "threshold": threshold,
        },
    )


# --------------------------------------------------------------------------- #
# Public entry points
# --------------------------------------------------------------------------- #


def score_e2a(
    report: SpecificityReport, thresholds: FrozenThresholds
) -> PromotionVerdict:
    """Return the non-compensatory Wave 1a promotion verdict for one family.

    Parameters
    ----------
    report:
        The :class:`SpecificityReport` produced by
        :func:`run_specificity_contrast` for one family.
    thresholds:
        The :class:`FrozenThresholds` container carrying the pinned
        per-family thresholds.  In production callers use
        :data:`WAVE1A_PREREGISTERED_THRESHOLDS` unchanged.

    Returns
    -------
    PromotionVerdict
        The verdict for this family.  Non-compensatory: any FAIL flips
        ``promoted`` to ``False``.  When a diagnostic-only arm slips
        into ``report.comparators`` (only ``oracle_ceiling`` is
        currently defined as diagnostic), raises
        :class:`PromotionRefused` before evaluating any gate — this
        mirrors :func:`promotion_admit_condition`'s refusal at the
        condition boundary.

    Raises
    ------
    PromotionRefused:
        Report references the oracle ceiling as a promotable
        comparator or arm.
    KeyError:
        No thresholds registered for the report's family.
    """

    if not isinstance(report, SpecificityReport):
        raise TypeError("report must be a SpecificityReport")
    if not isinstance(thresholds, FrozenThresholds):
        raise TypeError("thresholds must be a FrozenThresholds")

    if ORACLE_CEILING in report.comparators or ORACLE_CEILING in report.variants:
        raise PromotionRefused(
            f"SpecificityReport references {ORACLE_CEILING!r} as a "
            "promotable arm; the oracle ceiling is diagnostic-only "
            "(wave1a/PREREGISTRATION.md §4 'Oracle is diagnostic') and "
            "cannot enter the Wave 1a promotion contest."
        )

    family_thresholds = thresholds.for_family(report.family)
    per_gate: dict[str, GateResult] = {}
    kill_reasons: list[str] = []
    variant_survived: dict[str, bool] = {v: True for v in VARIANTS}

    # G3 Specificity — one gate per (variant, info-matched comparator).
    for variant in VARIANTS:
        for comparator in INFO_MATCHED_COMPARATORS:
            gate = _score_specificity_generic_one(
                report, family_thresholds, variant, comparator
            )
            key = f"{gate.gate_id}::{variant}::{comparator}"
            per_gate[key] = gate
            if not gate.passed:
                variant_survived[variant] = False
                kill_reasons.append(key)
        wrong_agent_gate = _score_specificity_wrong_agent(
            report, family_thresholds, variant
        )
        key = _gate_key(wrong_agent_gate.gate_id, variant)
        per_gate[key] = wrong_agent_gate
        if not wrong_agent_gate.passed:
            variant_survived[variant] = False
            kill_reasons.append(key)

    # G4 Per-family effect — one gate per variant.
    for variant in VARIANTS:
        effect_gate = _score_family_effect(
            report, family_thresholds, variant
        )
        key = _gate_key(effect_gate.gate_id, variant)
        per_gate[key] = effect_gate
        if not effect_gate.passed:
            variant_survived[variant] = False
    # Family-effect gate is "at least one variant clears".  If neither
    # variant cleared, the effect gate as a whole FAILs.
    any_variant_effect = any(
        per_gate[_gate_key(GATE_ID_FAMILY_EFFECT, v)].passed for v in VARIANTS
    )
    if not any_variant_effect:
        kill_reasons.append(_gate_key(GATE_ID_FAMILY_EFFECT, "family"))

    # No-family-reversal — family-level gate.
    reversal_gate = _score_no_family_reversal(report, family_thresholds)
    key = _gate_key(reversal_gate.gate_id, None)
    per_gate[key] = reversal_gate
    if not reversal_gate.passed:
        kill_reasons.append(key)

    # Non-compensatory: a passing variant must have cleared every
    # (specificity + wrong_agent) gate AND the family-effect gate, AND
    # the family must not be in reversal.
    passing_variants = tuple(
        v for v in VARIANTS if variant_survived[v] and reversal_gate.passed
    )
    promoted = len(passing_variants) > 0 and len(kill_reasons) == 0

    if promoted:
        return PromotionVerdict(
            promoted=True,
            kill_reasons=(),
            per_gate=per_gate,
            passing_variants=passing_variants,
            family=report.family,
        )
    # Ensure kill_reasons is non-empty when promoted is False
    # (dataclass __post_init__ enforces this).  A verdict with no
    # cleared variants but no logged failures is an impossible state;
    # if we reach it, synthesise a summary reason so the dataclass
    # invariant holds.
    if not kill_reasons:
        kill_reasons.append(
            _gate_key(GATE_ID_FAMILY_EFFECT, "family")
            if not any_variant_effect
            else _gate_key(GATE_ID_NO_FAMILY_REVERSAL, None)
        )
    return PromotionVerdict(
        promoted=False,
        kill_reasons=tuple(kill_reasons),
        per_gate=per_gate,
        passing_variants=(),
        family=report.family,
    )


def score_e2a_all(
    reports: Mapping[str, SpecificityReport],
    thresholds: FrozenThresholds,
) -> Mapping[str, PromotionVerdict]:
    """Score every family and honor the per-family-reversal veto.

    Wave 1a §5.4 states "aggregate success across families does not
    clear a per-family failure".  This helper scores each family
    independently through :func:`score_e2a` and returns the frozen
    per-family verdict mapping.  A caller wanting the aggregate
    Wave 1a screen decision (PASS iff every family PASSes) combines
    ``all(verdict.promoted for verdict in result.values())`` at its
    own layer; the harness itself never compensates across families.
    """

    if not isinstance(reports, Mapping):
        raise TypeError("reports must be a Mapping[str, SpecificityReport]")
    if not isinstance(thresholds, FrozenThresholds):
        raise TypeError("thresholds must be a FrozenThresholds")
    verdicts: dict[str, PromotionVerdict] = {}
    for family, report in reports.items():
        if report.family != family:
            raise ValueError(
                f"reports[{family!r}].family mismatch: {report.family!r}"
            )
        verdicts[family] = score_e2a(report, thresholds)
    return MappingProxyType(verdicts)
