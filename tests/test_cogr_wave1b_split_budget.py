"""Tests for the Wave 1b split-budget ``k_split_care_uncertain_audit`` ablation.

Five regressions per the Wave 1b task brief for the split-budget
ablation baseline:

1. Budget conservation across all three reported splits — the returned
   tuple has exactly ``budget`` picks for every :data:`SPLITS_TO_REPORT`
   entry.
2. No duplicate node ids anywhere in the ``k_split`` output.
3. ``k_audit >= 1`` — the audit slot always receives at least one pick
   under a valid split, and a split that would leave ``k_audit < 1``
   raises :class:`ValueError` with a stable message.
4. Deterministic given ``(context, seed, splits)`` — two calls to
   :func:`k_split` with identical arguments return byte-identical
   tuples.
5. Ensemble variance is monotonically non-decreasing in perturbation
   size ``epsilon`` — a small ``epsilon`` yields a variance table
   whose sum is ``<=`` the sum at a larger ``epsilon``, and
   ``epsilon = 0`` collapses every candidate's variance onto ``0``.
"""

from __future__ import annotations

import pytest

from experiments.concern_gated_retrieval_e2.wave0.families import (
    delayed_commitments as dc_family,
)
from experiments.concern_gated_retrieval_e2.wave0.sealed_env import (
    EpisodeContext,
    SealedEnvironment,
)
from experiments.concern_gated_retrieval_e2.wave0.template_split import (
    TemplateBucket,
)
from experiments.concern_gated_retrieval_e2.wave1b.split_budget import (
    DEFAULT_ENSEMBLE_SIZE,
    SPLITS_TO_REPORT,
    SplitFractions,
    ensemble_variance_ranker,
    k_split,
)


# --------------------------------------------------------------------------- #
# Fixture helper                                                              #
# --------------------------------------------------------------------------- #


def _observe(seed: int = 100_000) -> EpisodeContext:
    """Return a sealed context view for a delayed_commitments calibration seed."""
    episode = dc_family.generate_episode(
        seed=seed, bucket=TemplateBucket.CALIBRATION
    )
    env = SealedEnvironment(episode, mode="calibration")
    return env.observe(seed=seed)


# --------------------------------------------------------------------------- #
# 1. Budget conservation across all three splits                              #
# --------------------------------------------------------------------------- #


def test_budget_conservation_across_all_splits() -> None:
    """The output tuple has exactly ``budget`` picks for every reported split.

    ``budget = 9`` sits at the delayed_commitments seed 100000
    candidate-set cardinality (9 candidates); every reported split
    partitions 9 into ``(k_care, k_uncertain, k_audit)`` with
    ``k_audit >= 1`` (70/20/10 -> 6/2/1, 50/30/20 -> 4/3/2,
    80/10/10 -> 7/1/1), so the ablation exercises the full candidate
    pool without a degenerate audit-slot fallback.
    """
    context = _observe()
    budget = 9
    assert len(context.candidate_nodes) >= budget, (
        "fixture regression: delayed_commitments seed 100000 no longer "
        f"produces >= {budget} candidates"
    )
    assert len(SPLITS_TO_REPORT) == 3  # sanity: the reported grid stays at 3
    for splits in SPLITS_TO_REPORT:
        picks = k_split(context, budget, splits)
        assert len(picks) == budget, (
            f"k_split lost picks under splits={splits}: got {len(picks)}, "
            f"expected {budget}"
        )


# --------------------------------------------------------------------------- #
# 2. No duplicates across the three slots                                     #
# --------------------------------------------------------------------------- #


def test_no_duplicates_across_slots() -> None:
    """The disjoint concatenation must never contain a duplicate node id."""
    context = _observe()
    budget = 9
    for splits in SPLITS_TO_REPORT:
        picks = k_split(context, budget, splits)
        assert len(set(picks)) == len(picks), (
            f"k_split emitted duplicates under splits={splits}: {picks!r}"
        )
        for node in picks:
            assert node in context.candidate_nodes, (
                f"k_split emitted node {node!r} outside candidate set under "
                f"splits={splits}"
            )


# --------------------------------------------------------------------------- #
# 3. k_audit >= 1 (positive-case audit contribution and negative-case raise)  #
# --------------------------------------------------------------------------- #


def test_k_audit_at_least_one_and_invalid_split_raises() -> None:
    """Every reported split leaves k_audit >= 1; an invalid split raises."""
    context = _observe()
    budget = 9

    # Positive: every reported split at budget=9 leaves k_audit >= 1
    # and the audit slot really contributes at least one node beyond
    # k_care + k_uncertain.
    for splits in SPLITS_TO_REPORT:
        k_care = int(round(splits.care * budget))
        k_uncertain = int(round(splits.uncertain * budget))
        k_audit = budget - k_care - k_uncertain
        assert k_audit >= 1, (
            f"reported split {splits} yields k_audit={k_audit} at budget=9; "
            "SPLITS_TO_REPORT must satisfy k_audit >= 1"
        )
        picks = k_split(context, budget, splits)
        # Audit picks are the tail after k_care + k_uncertain.
        audit_picks = picks[k_care + k_uncertain :]
        assert len(audit_picks) == k_audit >= 1

    # Negative: a split whose composition would leave k_audit == 0
    # (60/40/0 at budget=9 rounds to k_care=5, k_uncertain=4,
    # k_audit=0) raises ValueError with a k_audit-anchored message.
    with pytest.raises(ValueError, match="k_audit"):
        # SplitFractions itself accepts 0.0 for the audit fraction; the
        # composition guard in k_split fires when k_audit rounds below 1.
        k_split(context, budget, SplitFractions(0.60, 0.40, 0.00))


# --------------------------------------------------------------------------- #
# 4. Deterministic given (context, seed, splits)                              #
# --------------------------------------------------------------------------- #


def test_deterministic_given_context_seed_and_splits() -> None:
    """Two calls with the same ``(context, splits)`` produce byte-identical picks.

    ``seed`` is baked into ``context`` (both via ``context.seed`` and
    ``context.episode_id``); calling :func:`k_split` twice on the same
    frozen ``EpisodeContext`` must return the exact same tuple. A
    fresh :func:`_observe` at the same seed must also reproduce the
    result — determinism across processes is the receipt promise.
    """
    context_a = _observe(seed=100_000)
    context_b = _observe(seed=100_000)
    budget = 9
    for splits in SPLITS_TO_REPORT:
        first = k_split(context_a, budget, splits)
        second = k_split(context_a, budget, splits)
        assert first == second, (
            f"k_split non-deterministic within a process under splits={splits}"
        )
        cross_process = k_split(context_b, budget, splits)
        assert first == cross_process, (
            f"k_split non-deterministic across observations under splits="
            f"{splits}"
        )

    # A different split should yield a different pick tuple (weak
    # discrimination check; the audit sampler's salt embeds the split
    # fractions so two grid points differ on their audit slot even when
    # k_care and k_uncertain happen to coincide).
    picks_a = k_split(context_a, budget, SPLITS_TO_REPORT[0])
    picks_b = k_split(context_a, budget, SPLITS_TO_REPORT[1])
    assert picks_a != picks_b, (
        "k_split produced identical picks across two distinct reported "
        "splits; that would indicate the split fractions are not entering "
        "the composition."
    )


# --------------------------------------------------------------------------- #
# 5. Ensemble variance monotone in perturbation size                          #
# --------------------------------------------------------------------------- #


def test_ensemble_variance_monotone_in_epsilon() -> None:
    """Larger perturbation ``epsilon`` weakly increases the total variance.

    The perturbation is ``max(0, care + epsilon * z)`` with ``z`` a
    fixed per-episode Gaussian draw. Scaling ``epsilon`` therefore
    scales the underlying noise proportionally, and the induced PPR-
    score variance rises monotonically in ``epsilon`` (up to the ReLU
    clamp on the care map). ``epsilon = 0`` collapses every ensemble
    member onto the same ranking and yields zero variance for every
    candidate.
    """
    context = _observe()
    if len(context.candidate_nodes) < 2:
        pytest.skip("need at least 2 candidates for a meaningful variance test")

    def _total_variance(epsilon: float) -> float:
        ranker = ensemble_variance_ranker(
            context, n_ensemble=DEFAULT_ENSEMBLE_SIZE, epsilon=epsilon
        )
        # The ranker exposes ``.variances`` as a frozen dict.
        return float(sum(ranker.variances.values()))  # ty: ignore[unresolved-attribute]  # noqa

    var_zero = _total_variance(0.0)
    var_small = _total_variance(0.05)
    var_medium = _total_variance(0.25)
    var_large = _total_variance(1.0)

    # ε = 0 collapses every ensemble member onto the same PPR fixed
    # point, so every candidate's variance is exactly 0.
    assert var_zero == 0.0, (
        f"ensemble_variance_ranker at epsilon=0 returned nonzero total "
        f"variance {var_zero}"
    )
    # Monotonicity along the four sampled ε values. Weak inequalities
    # so numerical noise at the ε = 0 → ε > 0 boundary does not flip
    # the check; the strict inequality between the smallest positive
    # ε and the largest ε is the load-bearing invariant.
    assert var_zero <= var_small <= var_medium <= var_large, (
        f"variance not monotone in epsilon: 0->{var_zero}, "
        f"0.05->{var_small}, 0.25->{var_medium}, 1.0->{var_large}"
    )
    assert var_large > var_small, (
        "variance failed to strictly increase between epsilon=0.05 and "
        f"epsilon=1.0: {var_small} !< {var_large}"
    )
