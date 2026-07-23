"""Wave 1a specificity + promotion-harness regression tests.

Five tests, per the Wave 1a build brief:

1. **shape** — :func:`run_specificity_contrast` on a two-seed batch
   produces a well-formed :class:`SpecificityReport` with the frozen
   arm / comparator slate and one paired row per seed.
2. **cluster SE correctness** — the aggregator's cluster-robust SE with
   one observation per cluster matches the closed-form paired-seed SE
   ``s / sqrt(K)``.
3. **oracle refused** — :func:`score_e2a` raises :class:`PromotionRefused`
   when a report inadvertently lists ``oracle_ceiling`` as a promotable
   comparator (the Wave 1a §4 "Oracle is diagnostic" rule).
4. **family-reversal detected** — a synthetic report where both
   on-line-learned variants underperform ``frozen_wrong`` by a
   threshold-sized margin KILLs on the reversal gate.
5. **non-compensatory KILL propagates** — a single gate FAIL flips the
   overall verdict to ``promoted=False`` regardless of every other gate.
"""

from __future__ import annotations

import math

import pytest

from experiments.concern_gated_retrieval_e2.wave1a.conditions import (
    ORACLE_CEILING,
    PromotionRefused,
)
from experiments.concern_gated_retrieval_e2.wave1a.promotion_harness import (
    FamilyThresholds,
    FrozenThresholds,
    GATE_ID_FAMILY_EFFECT,
    GATE_ID_NO_FAMILY_REVERSAL,
    GATE_ID_SPECIFICITY_GENERIC,
    GATE_ID_SPECIFICITY_WRONG_AGENT,
    PromotionVerdict,
    WAVE1A_PREREGISTERED_THRESHOLDS,
    score_e2a,
)
from experiments.concern_gated_retrieval_e2.wave1a.specificity import (
    ARM_FROZEN_WRONG,
    ARM_ONLINE_DR,
    ARM_ONLINE_IPS,
    COMPARATOR_INFO_MATCHED_PRIORITY,
    COMPARATOR_INFO_MATCHED_RECENCY,
    COMPARATOR_INFO_MATCHED_VALUE,
    COMPARATOR_WRONG_AGENT,
    COMPARATORS,
    ContrastAggregate,
    SpecificityReport,
    SpecificityRow,
    VARIANTS,
    cluster_robust_se,
    compute_contrast_aggregate,
    run_specificity_contrast,
)


# --------------------------------------------------------------------------- #
# Test helpers
# --------------------------------------------------------------------------- #


def _rewards(
    frozen_wrong: float,
    online_ips: float,
    online_dr: float,
    info_value: float,
    info_priority: float,
    info_recency: float,
    wrong_agent: float,
) -> dict[str, float]:
    """Return a well-formed rewards mapping for :class:`SpecificityRow`."""

    return {
        ARM_FROZEN_WRONG: frozen_wrong,
        ARM_ONLINE_IPS: online_ips,
        ARM_ONLINE_DR: online_dr,
        COMPARATOR_INFO_MATCHED_VALUE: info_value,
        COMPARATOR_INFO_MATCHED_PRIORITY: info_priority,
        COMPARATOR_INFO_MATCHED_RECENCY: info_recency,
        COMPARATOR_WRONG_AGENT: wrong_agent,
    }


def _row(family: str, seed: int, **kwargs: float) -> SpecificityRow:
    """Build a synthetic :class:`SpecificityRow`."""

    return SpecificityRow(
        family=family,
        seed=seed,
        episode_id=f"{family}::synthetic::{seed:06d}",
        rewards=_rewards(**kwargs),
    )


def _build_report(family: str, rows: list[SpecificityRow]) -> SpecificityReport:
    """Assemble a :class:`SpecificityReport` from synthetic rows.

    The aggregator does not care whether the rows came from a real
    Modal run or from a test fixture; we compose the contrast slate
    the same way :func:`run_specificity_contrast` does.
    """

    seeds = tuple(row.seed for row in rows)
    arm_means: dict[str, float] = {}
    for arm in (ARM_FROZEN_WRONG,) + VARIANTS + COMPARATORS:
        arm_means[arm] = sum(row.rewards[arm] for row in rows) / len(rows)
    contrasts: list[ContrastAggregate] = []
    for variant in VARIANTS:
        for comparator in COMPARATORS:
            contrasts.append(
                compute_contrast_aggregate(
                    rows, variant=variant, comparator=comparator
                )
            )
    return SpecificityReport(
        family=family,
        seeds=seeds,
        rows=tuple(rows),
        variants=VARIANTS,
        comparators=COMPARATORS,
        contrasts=tuple(contrasts),
        arm_means=arm_means,
        frozen_wrong_mean=float(arm_means[ARM_FROZEN_WRONG]),
    )


def _passing_thresholds(family: str) -> FrozenThresholds:
    """Return a threshold container so lax the fixtures below always pass.

    Wave 1a's real per-family thresholds live in
    :data:`WAVE1A_PREREGISTERED_THRESHOLDS`; the tests here need a
    tunable container so the non-compensatory contract can be tested
    in isolation.
    """

    return FrozenThresholds(
        per_family={
            family: FamilyThresholds(
                family=family,
                sigma_hat_multiplicative=1e-9,
                sigma_hat_best_matched=1e-9,
                delta_thresh_E2a=1e-9,
            )
        }
    )


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #


def test_specificity_report_shape_on_two_seed_batch():
    """One :func:`run_specificity_contrast` call yields the frozen shape.

    A two-seed confirmatory batch on ``delayed_commitments`` returns a
    :class:`SpecificityReport` whose rows/seeds align, whose arm set
    matches the frozen union of ``ARM_FROZEN_WRONG``, :data:`VARIANTS`,
    and :data:`COMPARATORS`, whose contrast slate is exactly
    ``|VARIANTS| * |COMPARATORS|`` rows in canonical order, and whose
    :attr:`SpecificityReport.frozen_wrong_mean` matches the sample mean.
    """

    seeds = (200_000, 200_001)
    report = run_specificity_contrast("delayed_commitments", seeds)

    # Structural shape.
    assert isinstance(report, SpecificityReport)
    assert report.family == "delayed_commitments"
    assert report.seeds == seeds
    assert len(report.rows) == len(seeds)
    for row, seed in zip(report.rows, seeds):
        assert isinstance(row, SpecificityRow)
        assert row.family == "delayed_commitments"
        assert row.seed == seed
        expected_arms = frozenset(
            (ARM_FROZEN_WRONG,) + VARIANTS + COMPARATORS
        )
        assert frozenset(row.rewards.keys()) == expected_arms

    # Comparators / variants tracked on the report (Wave 1a §4 oracle
    # exclusion invariant surfaces here).
    assert report.variants == VARIANTS
    assert report.comparators == COMPARATORS
    assert ORACLE_CEILING not in report.comparators
    assert ORACLE_CEILING not in report.variants

    # Contrast slate is |VARIANTS| * |COMPARATORS| entries in canonical
    # order.
    assert len(report.contrasts) == len(VARIANTS) * len(COMPARATORS)
    for i, variant in enumerate(VARIANTS):
        for j, comparator in enumerate(COMPARATORS):
            contrast = report.contrasts[i * len(COMPARATORS) + j]
            assert contrast.variant == variant
            assert contrast.comparator == comparator
            assert contrast.n_clusters == len(seeds)

    # frozen_wrong_mean matches arm_means[ARM_FROZEN_WRONG].
    assert report.frozen_wrong_mean == pytest.approx(
        report.arm_means[ARM_FROZEN_WRONG]
    )
    # Every per-row reward is finite (regression check for a runner
    # that produced NaN).
    for row in report.rows:
        for arm, reward in row.rewards.items():
            assert math.isfinite(reward), f"non-finite reward on {arm}"


def test_cluster_robust_se_matches_paired_seed_closed_form():
    """One-obs-per-cluster CR-SE reduces to the paired-seed SE ``s / sqrt(K)``.

    Uses a hand-computable delta sequence so a numerical drift in the
    aggregator (an off-by-one in the ``K * (K - 1)`` denominator, for
    instance) is caught immediately.  Also exercises
    :func:`compute_contrast_aggregate` on synthetic rows so the
    aggregator's ``lower_bound_2se`` is checked against
    ``mean - 2 * SE``.
    """

    # Deltas designed for an exact closed form:
    # d = [1.0, 2.0, 3.0, 4.0], mean = 2.5, ssq = sum((d - 2.5)^2) = 5.0
    # variance_sample = ssq / (K - 1) = 5.0 / 3, s = sqrt(5/3)
    # SE = s / sqrt(K) = sqrt(5/3) / 2 = sqrt(5 / 12)
    deltas = [1.0, 2.0, 3.0, 4.0]
    expected_se = math.sqrt(5.0 / 12.0)
    computed_se = cluster_robust_se(deltas)
    assert computed_se == pytest.approx(expected_se, rel=1e-12)

    # A one-cluster batch returns 0.0 by convention (Wave 1a's
    # ``2 * SE`` decision rule turns a one-cluster batch into a hard
    # ``mean_delta >= threshold`` check with no margin — the deeper
    # ``n_clusters`` audit lives on the promotion harness).
    assert cluster_robust_se([1.5]) == 0.0

    # Empty batch also returns 0.0.
    assert cluster_robust_se([]) == 0.0

    # Aggregate over synthetic rows: online_ips beats info_matched_value
    # by exactly [1.0, 2.0, 3.0, 4.0] on four seeds.
    rows = [
        _row(
            "delayed_commitments",
            200_000 + i,
            frozen_wrong=0.1,
            online_ips=0.1 + deltas[i],
            online_dr=0.1,
            info_value=0.1,
            info_priority=0.1,
            info_recency=0.1,
            wrong_agent=0.1,
        )
        for i in range(4)
    ]
    aggregate = compute_contrast_aggregate(
        rows,
        variant=ARM_ONLINE_IPS,
        comparator=COMPARATOR_INFO_MATCHED_VALUE,
    )
    assert aggregate.n_clusters == 4
    assert aggregate.mean_delta == pytest.approx(2.5, rel=1e-12)
    assert aggregate.cluster_robust_se == pytest.approx(expected_se, rel=1e-12)
    assert aggregate.lower_bound_2se == pytest.approx(
        2.5 - 2.0 * expected_se, rel=1e-12
    )


def test_score_e2a_refuses_report_referencing_oracle_ceiling():
    """A report advertising ``oracle_ceiling`` as a comparator is refused.

    Wave 1a §4 marks the oracle as diagnostic-only; a caller who
    accidentally forwards a report whose ``comparators`` tuple lists
    ``oracle_ceiling`` is refused up-front — the same shape as
    :func:`promotion_admit_condition`'s refusal at the condition
    boundary.  The rejection carries the ``oracle_ceiling`` name in the
    message so downstream receipts can regex-match on it.
    """

    family = "delayed_commitments"
    # Build a report where the frozen slate is fine but the caller has
    # sneaked ``oracle_ceiling`` into the ``comparators`` tuple.
    rows = [
        _row(
            family,
            200_000 + i,
            frozen_wrong=0.1,
            online_ips=0.5,
            online_dr=0.5,
            info_value=0.05,
            info_priority=0.05,
            info_recency=0.05,
            wrong_agent=0.05,
        )
        for i in range(3)
    ]
    base_report = _build_report(family, rows)
    tainted_report = SpecificityReport(
        family=family,
        seeds=base_report.seeds,
        rows=base_report.rows,
        variants=base_report.variants,
        comparators=base_report.comparators + (ORACLE_CEILING,),
        contrasts=base_report.contrasts,
        arm_means=dict(base_report.arm_means),
        frozen_wrong_mean=base_report.frozen_wrong_mean,
    )

    with pytest.raises(PromotionRefused, match="oracle_ceiling"):
        score_e2a(tainted_report, WAVE1A_PREREGISTERED_THRESHOLDS)


def test_family_reversal_detected_by_promotion_harness():
    """Both variants below ``frozen_wrong`` by a threshold-sized margin KILLs.

    Wave 1a §5.4 says "a per-family reversal KILLs regardless of the
    other two families".  This test builds a synthetic per-family
    scenario where both on-line-learned variants sit at
    ``-2 * delta_thresh_E2a`` below ``frozen_wrong`` on every seed and
    verifies :func:`score_e2a` returns a KILL verdict with the
    ``GATE_ID_NO_FAMILY_REVERSAL`` gate in ``kill_reasons``.
    """

    family = "delayed_commitments"
    family_thresh = WAVE1A_PREREGISTERED_THRESHOLDS.for_family(family)
    threshold = family_thresh.delta_thresh_E2a
    # Push both variants well below frozen_wrong to guarantee reversal.
    frozen_reward = 0.60
    online_reward = frozen_reward - 2.0 * threshold  # comfortably < -threshold
    rows = [
        _row(
            family,
            200_000 + i,
            frozen_wrong=frozen_reward,
            online_ips=online_reward,
            online_dr=online_reward,
            info_value=0.05,
            info_priority=0.05,
            info_recency=0.05,
            wrong_agent=0.05,
        )
        for i in range(5)
    ]
    report = _build_report(family, rows)

    verdict = score_e2a(report, WAVE1A_PREREGISTERED_THRESHOLDS)
    assert isinstance(verdict, PromotionVerdict)
    assert verdict.promoted is False
    assert verdict.family == family
    # The reversal gate must appear in kill_reasons.
    reversal_key = f"{GATE_ID_NO_FAMILY_REVERSAL}::family"
    assert reversal_key in verdict.kill_reasons
    reversal_gate = verdict.per_gate[reversal_key]
    assert reversal_gate.passed is False
    # No variant survives a family reversal.
    assert verdict.passing_variants == ()


def test_non_compensatory_kill_propagates_from_a_single_gate():
    """A single gate FAIL flips the overall verdict regardless of every other.

    We seed a scenario where every info-matched comparator is beaten
    (specificity generic PASSes), the wrong-agent gate PASSes for
    ``online_ips``, no family reversal occurs, but the family-effect
    gate for ``online_ips`` FAILs (its lower-bound falls just below the
    frozen threshold) and the same holds for ``online_dr``.  With no
    variant clearing the family-effect gate the wave KILLs.  The KILL
    reason is exactly the family-effect gate; every other per-gate
    entry is PASS.  This exercises the non-compensatory contract:
    aggregate specificity + no-reversal cannot rescue a family-effect
    FAIL.
    """

    family = "delayed_commitments"
    family_thresh = WAVE1A_PREREGISTERED_THRESHOLDS.for_family(family)
    threshold_family_effect = family_thresh.delta_thresh_E2a

    # Bump online rewards enough to clear specificity gates but not the
    # family-effect gate.  Offsets vary per seed so cluster-robust SE
    # is non-zero (avoids the degenerate one-cluster fallback).
    # margin_over_generic: how far above each info-matched comparator
    # the online variant sits, per seed.
    margin_over_generic = 0.20
    margin_over_wrong_agent = 0.60
    # variance offsets to keep SE > 0
    offsets = [0.00, 0.01, -0.01, 0.02, -0.02]

    rows = []
    for i, offset in enumerate(offsets):
        # Base rewards.  Online variants are only slightly above
        # frozen_wrong so the family-effect gate fails.
        frozen_reward = 0.30
        online_gap_vs_frozen = 0.5 * threshold_family_effect  # < threshold
        online_reward = frozen_reward + online_gap_vs_frozen + offset

        rows.append(
            _row(
                family,
                200_000 + i,
                frozen_wrong=frozen_reward,
                online_ips=online_reward,
                online_dr=online_reward,
                info_value=online_reward - margin_over_generic,
                info_priority=online_reward - margin_over_generic,
                info_recency=online_reward - margin_over_generic,
                wrong_agent=online_reward - margin_over_wrong_agent,
            )
        )

    report = _build_report(family, rows)
    verdict = score_e2a(report, WAVE1A_PREREGISTERED_THRESHOLDS)

    # Non-compensatory KILL: promoted must be False.
    assert verdict.promoted is False
    assert verdict.family == family
    # Family-effect gate for both variants must FAIL.
    for variant in VARIANTS:
        gate = verdict.per_gate[f"{GATE_ID_FAMILY_EFFECT}::{variant}"]
        assert gate.passed is False, (
            f"{variant} family-effect should fail; got PASS with "
            f"metrics={dict(gate.metrics)!r}"
        )
        # The failing gate's lower bound is strictly below the frozen
        # threshold.
        assert gate.metrics["lower_bound_2se"] < gate.metrics["threshold"]
    # Aggregate family-effect kill key appears in kill_reasons.
    aggregate_key = f"{GATE_ID_FAMILY_EFFECT}::family"
    assert aggregate_key in verdict.kill_reasons

    # Specificity gates should be PASS on both variants (the design
    # margin against info-matched comparators clears the threshold, and
    # so does the wrong-agent margin).  If any of them FAILed the
    # non-compensatory contract still triggers a KILL — but the test
    # aims to prove that the KILL fires even when every other gate is
    # green, so assert them PASS explicitly.
    for variant in VARIANTS:
        for comparator in (
            COMPARATOR_INFO_MATCHED_VALUE,
            COMPARATOR_INFO_MATCHED_PRIORITY,
            COMPARATOR_INFO_MATCHED_RECENCY,
        ):
            key = f"{GATE_ID_SPECIFICITY_GENERIC}::{variant}::{comparator}"
            gate = verdict.per_gate[key]
            assert gate.passed is True, (
                f"specificity generic for {variant} vs {comparator} "
                f"should PASS on this fixture; got FAIL with "
                f"metrics={dict(gate.metrics)!r}"
            )
        wa_gate = verdict.per_gate[
            f"{GATE_ID_SPECIFICITY_WRONG_AGENT}::{variant}"
        ]
        assert wa_gate.passed is True

    # No family reversal on this fixture (online > frozen_wrong).
    reversal_key = f"{GATE_ID_NO_FAMILY_REVERSAL}::family"
    reversal_gate = verdict.per_gate[reversal_key]
    assert reversal_gate.passed is True
    assert reversal_key not in verdict.kill_reasons

    # No variant survives; passing_variants is empty.
    assert verdict.passing_variants == ()
