"""Wave 1a E2a per-episode runner regression tests.

Scaffolding scope:

1. ``run_e2a_episode`` runs one confirmatory episode end-to-end and emits
   a well-formed :class:`E2aEpisodeResult`.
2. The sealed environment's ``evaluate()`` method is called exactly once
   per episode; the single-shot invariant is regression-checked via
   :attr:`E2aEpisodeResult.sealed_env_evaluate_calls` and a follow-up
   attempt to construct a second decision through the exposed API.
3. The oracle-ceiling condition is refused by the promotion harness
   (:func:`promotion_admit_condition`) — the runner may still execute
   the oracle for the diagnostic-ceiling report, but it must not enter a
   promotion contest.
"""

from __future__ import annotations

import pytest

from experiments.concern_gated_retrieval_e2.wave0.concern_update import ProbeReceipt
from experiments.concern_gated_retrieval_e2.wave0.families.delayed_commitments import (
    generate_episode,
)
from experiments.concern_gated_retrieval_e2.wave0.sealed_env import (
    RetrievalChoice,
    SealedEnvironment,
    SealedEvaluationError,
    SealedOutcome,
)
from experiments.concern_gated_retrieval_e2.wave0.template_split import (
    TemplateBucket,
)
from experiments.concern_gated_retrieval_e2.wave1a.conditions import (
    CONDITIONS,
    FROZEN_WRONG,
    ONLINE_IPS,
    ORACLE_CEILING,
    PromotionRefused,
    promotion_admit_condition,
)
from experiments.concern_gated_retrieval_e2.wave1a.e2a_runner import (
    E2aEpisodeResult,
    run_e2a_episode,
)


CONFIRMATORY_SEED = 200_000


def _one_confirmatory_episode():
    return generate_episode(
        seed=CONFIRMATORY_SEED, bucket=TemplateBucket.CONFIRMATION
    )


def test_run_e2a_episode_produces_a_wellformed_result():
    """One episode under the frozen-wrong baseline runs to a receipt."""
    episode = _one_confirmatory_episode()
    condition = CONDITIONS[FROZEN_WRONG]
    result = run_e2a_episode(episode, condition, rng_seed=1234)
    assert isinstance(result, E2aEpisodeResult)
    assert result.episode_id == episode.episode_id
    assert result.condition_name == FROZEN_WRONG
    assert result.family == episode.family
    assert result.template_family_split == "confirmatory"
    assert isinstance(result.receipt, ProbeReceipt)
    assert result.receipt.template_family_split == "confirmatory"
    assert result.receipt.selection_propensity > 0.0
    assert isinstance(result.outcome, SealedOutcome)
    assert result.integrity_audit_passed is True
    # Frozen-wrong: no update rule → concern_after is None.
    assert result.concern_after is None


def test_online_ips_condition_carries_updated_concern_marker():
    """An on-line-learned run exposes a post-outcome prior slot.

    The runner uses Wave 0's ``update_concern`` on calibration-tagged
    receipts and passes through the unchanged prior on confirmatory
    receipts; either way ``concern_after`` is populated with a mapping
    the sweep aggregator can join on.
    """
    episode = _one_confirmatory_episode()
    condition = CONDITIONS[ONLINE_IPS]
    result = run_e2a_episode(episode, condition, rng_seed=1234)
    assert result.condition_name == ONLINE_IPS
    assert result.concern_after is not None
    # concern_after shape matches concern_before shape (Wave 0
    # ``update_concern`` never grows the anchor set).
    assert set(result.concern_after.keys()) == set(result.concern_before.keys())


def test_runner_calls_sealed_env_evaluate_exactly_once():
    """The single-shot ``evaluate()`` invariant survives a full run.

    Regression check:

    * The result's ``sealed_env_evaluate_calls`` field is ``1``.
    * A fresh sealed environment on the same episode still refuses a
      second ``evaluate()`` call (invariant lives on Wave 0's env).
    """
    episode = _one_confirmatory_episode()
    condition = CONDITIONS[FROZEN_WRONG]
    result = run_e2a_episode(episode, condition, rng_seed=1234)
    assert result.sealed_env_evaluate_calls == 1

    # Independent check on the Wave 0 sealed-env single-shot rule: build
    # a fresh env, observe once, evaluate, then try to evaluate again.
    env = SealedEnvironment(episode, mode="confirmatory")
    env.observe(seed=0)
    env.evaluate(RetrievalChoice(selected=(), wall_actions=0))
    assert env.evaluated is True
    with pytest.raises(SealedEvaluationError):
        env.evaluate(RetrievalChoice(selected=(), wall_actions=0))


def test_oracle_condition_refused_by_promotion_harness():
    """The oracle runs for diagnostics but is refused by the promotion harness."""
    episode = _one_confirmatory_episode()
    oracle = CONDITIONS[ORACLE_CEILING]

    # 1. Promotion harness refuses the oracle up-front (never enters a
    #    Wave 1a screen or a Wave 1b promotion contest).
    with pytest.raises(PromotionRefused, match="oracle_ceiling"):
        promotion_admit_condition(oracle)

    # 2. The runner still executes the oracle for diagnostic reporting
    #    (Wave 1a §4 "Oracle is diagnostic"), producing a valid receipt
    #    that downstream ceiling-headroom rows can consume.
    result = run_e2a_episode(episode, oracle, rng_seed=1234)
    assert result.condition_name == ORACLE_CEILING
    assert isinstance(result.outcome, SealedOutcome)
    assert result.sealed_env_evaluate_calls == 1
