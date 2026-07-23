"""Wave 0 baseline slate regression tests.

The four tests below are the anti-leakage / promotion-harness / concern-
specificity / matched-capacity regression suite named by the Wave 0
build brief for
``experiments/concern_gated_retrieval_e2/wave0/baselines.py``:

* ``test_each_baseline_deterministic_on_fixed_seed`` — every baseline in
  the slate produces byte-identical output on repeated calls at a fixed
  seed.
* ``test_oracle_ceiling_refused_by_promotion_harness`` — the CEILING-ONLY
  ``oracle_ceiling`` baseline is refused by :func:`promotion_admit`;
  every other baseline is admitted.
* ``test_wrong_agent_concern_degrades_vs_correct`` — over a modest
  calibration batch, ``wrong_agent_concern`` retrieves the load-bearing
  target strictly less often than the candidate mechanism
  ``multiplicative_ppr``.
* ``test_learned_one_stage_matches_candidate_param_count`` — the
  frozen ``learned_one_stage`` MLP's parameter count sits within 5% of
  the declared ``CANDIDATE_MECHANISM_PARAM_COUNT`` reference.
"""

from __future__ import annotations

import pytest

from experiments.concern_gated_retrieval_e2.wave0.baselines import (
    BASELINES,
    CANDIDATE_MECHANISM_PARAM_COUNT,
    PromotionRefused,
    RankFn,
    learned_one_stage_parameter_count,
    multiplicative_ppr,
    oracle_ceiling,
    promotion_admit,
    wrong_agent_concern,
)
from experiments.concern_gated_retrieval_e2.wave0.families import (
    delayed_commitments as dc_family,
)
from experiments.concern_gated_retrieval_e2.wave0.sealed_env import (
    EpisodeContext,
    SealedEnvironment,
)
from experiments.concern_gated_retrieval_e2.wave0.template_split import TemplateBucket


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _observe(seed: int) -> tuple[EpisodeContext, tuple[str, ...]]:
    """Return a sealed context view for a delayed_commitments calibration seed.

    Also returns the sealed answer key from the underlying
    :class:`EpisodeSpec` so the test can score whether a ranker
    retrieved the load-bearing target. The answer key is
    evaluator-only; test code is allowed to read it because tests are
    part of the evaluator, not the policy.
    """
    episode = dc_family.generate_episode(seed=seed, bucket=TemplateBucket.CALIBRATION)
    env = SealedEnvironment(episode, mode="calibration")
    context = env.observe(seed=seed)
    return context, episode._answer_key


# ---------------------------------------------------------------------------
# (1) Determinism at a fixed seed
# ---------------------------------------------------------------------------


def test_each_baseline_deterministic_on_fixed_seed() -> None:
    context, _ = _observe(seed=100_000)
    for name, rank in BASELINES.items():
        first = rank(context, 2)
        second = rank(context, 2)
        assert first == second, (
            f"baseline {name!r} produced non-deterministic output at seed 100000: "
            f"{first!r} != {second!r}"
        )
        # Sanity: every non-empty output is a subset of the candidate set.
        for node in first:
            assert node in context.candidate_nodes, (
                f"baseline {name!r} produced node {node!r} not in candidate set"
            )
        # Sanity: no duplicate selections within a single rank output.
        assert len(set(first)) == len(first), (
            f"baseline {name!r} produced duplicate selections at seed 100000: {first!r}"
        )


# ---------------------------------------------------------------------------
# (2) oracle_ceiling refused by the promotion harness
# ---------------------------------------------------------------------------


def test_oracle_ceiling_refused_by_promotion_harness() -> None:
    # Sanity: the ceiling flag is present and truthy.
    assert getattr(oracle_ceiling, "is_ceiling_only", False) is True

    with pytest.raises(PromotionRefused, match="CEILING-ONLY"):
        promotion_admit(oracle_ceiling)

    # Every other baseline is admitted.
    for name, rank in BASELINES.items():
        if name == "oracle_ceiling":
            continue
        admitted = promotion_admit(rank)
        assert admitted is rank, (
            f"promotion_admit changed identity for baseline {name!r}"
        )


# ---------------------------------------------------------------------------
# (3) wrong_agent_concern degrades vs correct concern
# ---------------------------------------------------------------------------


def _hit_rate(rank: RankFn, seeds: range) -> float:
    """Return the fraction of episodes in ``seeds`` whose top-1 pick is the answer."""
    hits = 0
    total = 0
    for seed in seeds:
        context, answer = _observe(seed=seed)
        picks = rank(context, 1)
        total += 1
        if picks and picks[0] in answer:
            hits += 1
    return hits / max(total, 1)


def test_wrong_agent_concern_degrades_vs_correct() -> None:
    # Modest calibration window — 40 seeds is enough to separate the two
    # rankers deterministically without loading the test suite.
    seeds = range(100_000, 100_040)
    correct_hit = _hit_rate(multiplicative_ppr, seeds)
    wrong_hit = _hit_rate(wrong_agent_concern, seeds)
    assert wrong_hit < correct_hit, (
        f"wrong_agent_concern did not degrade against multiplicative_ppr: "
        f"wrong_hit={wrong_hit:.3f}, correct_hit={correct_hit:.3f}"
    )


# ---------------------------------------------------------------------------
# (4) learned_one_stage parameter count within 5% of the candidate mechanism
# ---------------------------------------------------------------------------


def test_learned_one_stage_matches_candidate_param_count() -> None:
    learned = learned_one_stage_parameter_count()
    target = CANDIDATE_MECHANISM_PARAM_COUNT
    assert target > 0, "CANDIDATE_MECHANISM_PARAM_COUNT must be positive"
    delta = abs(learned - target) / target
    assert delta <= 0.05, (
        f"learned_one_stage parameter count {learned} is not within 5% of "
        f"CANDIDATE_MECHANISM_PARAM_COUNT={target} (delta={delta:.3f})"
    )
