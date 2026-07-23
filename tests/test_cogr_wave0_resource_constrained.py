"""Tests for the Wave 0 ``resource_constrained`` procedural family.

Three property tests, one per invariant named by the Wave 0 build brief
and by ``experiments/concern_gated_retrieval_e2/wave0/PREREGISTRATION.md``:

1. **Slate size and shape.** :func:`calibration_slate` emits at least 30
   valid, calibration-tagged :class:`EpisodeSpec` rows whose seeds fall
   inside the family's declared calibration seed range.

2. **Adversarial wrong-prior misspecification.** For every calibration
   template, the concern prior places ``W_ALARM_INIT`` weight on a node
   whose sealed role is the alarm distractor and strictly less than the
   uniform baseline on at least one node whose sealed role is a true
   commitment (the load-bearing prior obligation) — matching
   PREREGISTRATION.md §5.

3. **Anti-ceiling holdout.** No policy-visible pass-through method reaches
   the oracle ceiling on any calibration seed. Concretely: a naive
   care-only ranker (rank the candidate set by the wrong prior) always
   prefers the alarm distractor to the load-bearing obligation, so the
   sealed reward for that policy is strictly worse than the oracle-answer
   reward; and calibration and confirmatory seed ranges are disjoint by
   construction.
"""

from __future__ import annotations

import pytest

from experiments.concern_gated_retrieval_e2.wave0.families import (
    resource_constrained as rc,
)
from experiments.concern_gated_retrieval_e2.wave0.sealed_env import (
    EpisodeSpec,
    RetrievalChoice,
    SealedEnvironment,
    SealedEvaluationError,
)
from experiments.concern_gated_retrieval_e2.wave0.template_split import (
    TemplateBucket,
)


# --------------------------------------------------------------------------- #
# Property 1 — slate size and shape
# --------------------------------------------------------------------------- #


def test_calibration_slate_has_at_least_thirty_valid_templates() -> None:
    slate = rc.calibration_slate()

    # Wave 0 build brief: 30+ templates per family.
    assert len(slate) >= 30

    seeds = [episode.seed for episode in slate]
    # Deterministic ascending order matches the calibration seeds helper.
    assert seeds == list(rc.calibration_seeds())
    # No duplicate seeds inside the slate.
    assert len(set(seeds)) == len(seeds)

    for episode in slate:
        assert isinstance(episode, EpisodeSpec)
        assert episode.family == rc.FAMILY_NAME
        assert episode.template_family_split == "calibration"
        assert rc.CALIBRATION_SEED_START <= episode.seed < rc.CALIBRATION_SEED_END
        assert episode.budget == rc.DEFAULT_BUDGET

        # Context and candidate sets are disjoint — the currently-active
        # pending actions are never candidates for off-context retrieval.
        assert set(episode.context_nodes).isdisjoint(episode.candidate_nodes)
        # And no duplicates within either set.
        assert len(set(episode.context_nodes)) == len(episode.context_nodes)
        assert len(set(episode.candidate_nodes)) == len(episode.candidate_nodes)

        # Care anchors cover every graph node; that is a Wave 0 invariant
        # so the concern-warp step in graph_learn.apply_concern_warp does
        # not raise on an unknown-node prior.
        care = dict(episode.care_anchors)
        assert set(care.keys()) >= set(episode.candidate_nodes)
        assert set(care.keys()) >= set(episode.context_nodes)

        # The calibration episode admits a SealedEnvironment in
        # ``calibration`` mode — this is the runtime family-split guard
        # exercised end-to-end for the family.
        env = SealedEnvironment(episode, mode="calibration")
        context = env.observe(seed=episode.seed)
        assert context.template_family_split == "calibration"
        assert context.family == rc.FAMILY_NAME


# --------------------------------------------------------------------------- #
# Property 2 — adversarial wrong-prior misspecification
# --------------------------------------------------------------------------- #


def test_wrong_prior_inflates_alarm_and_suppresses_a_true_commitment() -> None:
    for episode in rc.calibration_slate():
        care = dict(episode.care_anchors)
        role = dict(episode.role)

        # Alarm nodes: sealed role is the "recent large-transaction" alarm.
        alarm_nodes = [node for node, r in role.items() if r == rc.ROLE_ALARM]
        # Load-bearing prior obligation: exactly one per template.
        obligation_nodes = [
            node for node, r in role.items() if r == rc.ROLE_OBLIGATION
        ]
        assert len(alarm_nodes) == 1, (
            f"expected one alarm node per template; got {alarm_nodes!r}"
        )
        assert len(obligation_nodes) == 1, (
            f"expected one load-bearing obligation per template; got "
            f"{obligation_nodes!r}"
        )
        alarm = alarm_nodes[0]
        obligation = obligation_nodes[0]
        assert alarm != obligation

        # Adversarial inflation: alarm weight at the frozen `W_ALARM_INIT`.
        assert care[alarm] == pytest.approx(rc.W_ALARM_INIT)
        assert care[alarm] > rc.W_UNIFORM_INIT

        # Adversarial suppression: the load-bearing commitment is
        # strictly below the uniform baseline. This is what makes the
        # prior "actively wrong" rather than merely "uninformative".
        assert care[obligation] == pytest.approx(rc.W_COMMIT_SUPPRESSED_INIT)
        assert care[obligation] < rc.W_UNIFORM_INIT

        # At least one other true commitment region (the care-only global
        # obligation) is left at uniform, so the wrong prior is not a
        # total inversion. PREREGISTRATION.md §5(3).
        care_only_globals = [
            node for node, r in role.items() if r == rc.ROLE_CARE_GLOBAL
        ]
        assert care_only_globals, (
            "expected a care-only global obligation distractor per template"
        )
        for node in care_only_globals:
            assert care[node] == pytest.approx(rc.W_UNIFORM_INIT)


# --------------------------------------------------------------------------- #
# Property 3 — anti-ceiling holdout
# --------------------------------------------------------------------------- #


def _care_only_pick(episode: EpisodeSpec) -> tuple[str, ...]:
    """Rank the sealed candidate set by wrong-prior weight; pick top-budget.

    This is a *policy-visible* baseline: it reads only
    ``episode.candidate_nodes`` and ``episode.care_anchors`` (both are
    policy-visible per the sealed_env contract). It does not touch any
    evaluator-only field, so it is legal to run here even though this
    test file lives outside the sealed environment wrapper.

    Ties are broken by ascending node id so the pick is deterministic.
    """
    care = dict(episode.care_anchors)
    candidates = list(episode.candidate_nodes)
    ranked = sorted(candidates, key=lambda n: (-care.get(n, 0.0), n))
    return tuple(ranked[: episode.budget])


def _oracle_pick(episode: EpisodeSpec) -> tuple[str, ...]:
    """Ceiling policy: reveal the load-bearing obligation, pick it plus a
    zero-utility filler.

    Used only in this test — the test file is not policy code — to
    establish the ceiling reward for the anti-ceiling comparison.
    """
    role = dict(episode.role)
    obligation = next(n for n, r in role.items() if r == rc.ROLE_OBLIGATION)
    # Filler: pick a neutral note so the miss penalty is zero.
    utility = dict(episode.utility)
    filler = next(
        (
            n
            for n in episode.candidate_nodes
            if n != obligation and utility.get(n, 0.0) == 0.0
        ),
        None,
    )
    if filler is None:
        return (obligation,)
    return (obligation, filler)


def test_calibration_and_confirmatory_seed_ranges_are_disjoint() -> None:
    calibration = set(rc.calibration_seeds())
    confirmatory = set(rc.confirmatory_seeds())
    assert calibration.isdisjoint(confirmatory)
    # And every calibration seed lives in the master calibration block
    # 100_000..100_999 declared by PREREGISTRATION.md §10.
    assert min(calibration) >= 100_000
    assert max(calibration) < 101_000
    # And every confirmatory seed lives in the master 200_000..201_999.
    assert min(confirmatory) >= 200_000
    assert max(confirmatory) < 202_000


def test_generator_refuses_confirmatory_seed_range_in_calibration_bucket() -> None:
    # A seed drawn from the confirmatory range is a range-mismatch and
    # must be refused at construction time — otherwise a caller could
    # smuggle a confirmatory row into a calibration entry point without
    # tripping the sealed-env family-split guard.
    with pytest.raises(ValueError):
        rc.generate_episode(
            seed=rc.CONFIRMATORY_SEED_START,
            bucket=TemplateBucket.CALIBRATION,
        )
    with pytest.raises(ValueError):
        rc.generate_episode(
            seed=rc.CALIBRATION_SEED_START,
            bucket=TemplateBucket.CONFIRMATION,
        )


def test_no_wrong_prior_pass_through_reaches_ceiling_on_any_seed() -> None:
    for episode in rc.calibration_slate():
        env = SealedEnvironment(episode, mode="calibration")
        env.observe(seed=episode.seed)

        care_only_selection = _care_only_pick(episode)
        oracle_selection = _oracle_pick(episode)

        # The wrong-prior pass-through always prefers the alarm to the
        # load-bearing obligation. This is what "adversarially wrong"
        # means at the policy level: without a corrective mechanism,
        # the retrieval decision is actively bad.
        role = dict(episode.role)
        obligation = next(n for n, r in role.items() if r == rc.ROLE_OBLIGATION)
        alarm = next(n for n, r in role.items() if r == rc.ROLE_ALARM)
        assert alarm in care_only_selection
        assert obligation not in care_only_selection

        # And the sealed environment scores it strictly below the oracle
        # policy: non-ceiling headroom is preserved per PREREGISTRATION.md
        # §6 and §8. We compare on two matched-family sealed environments
        # because SealedEnvironment.evaluate is single-shot per instance.
        env_care = SealedEnvironment(episode, mode="calibration")
        env_care.observe(seed=episode.seed)
        care_outcome = env_care.evaluate(
            RetrievalChoice(selected=care_only_selection)
        )

        env_oracle = SealedEnvironment(episode, mode="calibration")
        env_oracle.observe(seed=episode.seed)
        oracle_outcome = env_oracle.evaluate(
            RetrievalChoice(selected=oracle_selection)
        )

        # Anti-ceiling: oracle reward strictly beats the wrong-prior
        # pass-through by at least 0.30 on every calibration seed. The
        # calibration receipt reports the exact per-seed spread; this
        # test only asserts that the spread is materially positive.
        assert oracle_outcome.realized_reward - care_outcome.realized_reward >= 0.30
        # And the oracle policy's realized reward is bounded strictly
        # below the reward-domain ceiling of +1.0 — no method starts at
        # ceiling on this family per PREREGISTRATION.md §6.
        assert oracle_outcome.realized_reward < 1.0
        # And the wrong-prior policy fails the constraint gate.
        assert oracle_outcome.constraint_preserved is True
        assert care_outcome.constraint_preserved is False


# --------------------------------------------------------------------------- #
# Bonus: single-shot sealed evaluation surfaces correctly for this family
# --------------------------------------------------------------------------- #


def test_sealed_environment_single_shot_gate_holds_for_family() -> None:
    episode = next(iter(rc.calibration_slate()))
    env = SealedEnvironment(episode, mode="calibration")
    env.observe(seed=episode.seed)
    env.evaluate(RetrievalChoice(selected=_care_only_pick(episode)))
    with pytest.raises(SealedEvaluationError):
        env.evaluate(RetrievalChoice(selected=_care_only_pick(episode)))
