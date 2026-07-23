"""Tests for the Wave 0 delayed_commitments procedural family.

These tests exercise the three invariants named by the Wave 0 build
brief for :mod:`experiments.concern_gated_retrieval_e2.wave0.families.delayed_commitments`:

1. **Determinism.** ``(seed, bucket, holdout)`` uniquely determines the
   returned :class:`EpisodeSpec`.
2. **Holdout disjointness.** A held-out template (whole-template kind)
   or a held-out paraphrase family never appears in the calibration
   pool the generator surfaces.
3. **Non-trivial distractor difficulty.** Baselines built from
   :mod:`experiments.concern_gated_retrieval_e2.wave0.graph_learn` —
   personalized PageRank on the fixed withheld geometry starting from
   the active context, and from the wrong-prior care anchors — cannot
   trivially achieve hit@1 = 1 on every calibration seed.

The tests also spot-check the anti-leakage boundary the sealed
environment enforces on top of the family generator: the policy-visible
:class:`EpisodeContext` carries no role labels, no per-node utility, and
no answer key. Those regressions live alongside the sealed-env
regression suite in ``tests/test_cogr_wave0_sealed_env.py`` and are
duplicated here at the family boundary so a family-level regression
lands on this test.
"""

from __future__ import annotations

import pytest

from experiments.concern_gated_retrieval.graph import personalized_pagerank
from experiments.concern_gated_retrieval_e2.wave0.families.delayed_commitments import (
    CALIBRATION_SEED_MAX,
    CALIBRATION_SEED_MIN,
    CONFIRMATION_SEED_MAX,
    CONFIRMATION_SEED_MIN,
    DEFAULT_BUDGET,
    FAMILY_NAME,
    GRAPH_SIZE,
    PARAPHRASE_FAMILIES,
    TEMPLATE_IDS,
    TEMPLATES,
    calibration_template_ids,
    confirmatory_template_ids,
    generate_episode,
    paraphrase_family_of,
)
from experiments.concern_gated_retrieval_e2.wave0.graph_learn import (
    build_withheld_graph,
)
from experiments.concern_gated_retrieval_e2.wave0.sealed_env import (
    EpisodeSpec,
    RetrievalChoice,
    SealedEnvironment,
)
from experiments.concern_gated_retrieval_e2.wave0.template_split import (
    TemplateBucket,
)


# --------------------------------------------------------------------------- #
# Registry-level sanity
# --------------------------------------------------------------------------- #


def test_template_registry_meets_wave0_floor() -> None:
    """Wave 0 requires at least 30 distinct templates for this family."""
    assert len(TEMPLATES) >= 30
    assert len(TEMPLATE_IDS) == len(TEMPLATES)
    assert len(set(TEMPLATE_IDS)) == len(TEMPLATES)

    cal_ids = calibration_template_ids()
    conf_ids = confirmatory_template_ids()
    assert set(cal_ids).isdisjoint(set(conf_ids))
    assert set(cal_ids) | set(conf_ids) == set(TEMPLATE_IDS)


def test_paraphrase_family_of_covers_every_template() -> None:
    for tid in TEMPLATE_IDS:
        assert paraphrase_family_of(tid) in PARAPHRASE_FAMILIES
    with pytest.raises(KeyError):
        paraphrase_family_of("does-not-exist")


# --------------------------------------------------------------------------- #
# Determinism
# --------------------------------------------------------------------------- #


def test_generate_episode_is_deterministic_for_same_inputs() -> None:
    left = generate_episode(seed=100_042, bucket=TemplateBucket.CALIBRATION)
    right = generate_episode(seed=100_042, bucket=TemplateBucket.CALIBRATION)
    assert isinstance(left, EpisodeSpec)
    assert left.episode_id == right.episode_id
    assert left.context_nodes == right.context_nodes
    assert left.candidate_nodes == right.candidate_nodes
    assert dict(left.care_anchors) == dict(right.care_anchors)
    assert dict(left.role) == dict(right.role)
    assert dict(left.utility) == dict(right.utility)
    assert left._answer_key == right._answer_key


def test_generate_episode_varies_across_seeds() -> None:
    a = generate_episode(seed=100_000, bucket=TemplateBucket.CALIBRATION)
    b = generate_episode(seed=100_001, bucket=TemplateBucket.CALIBRATION)
    assert a.episode_id != b.episode_id
    # The withheld-graph node namespace is seed-scoped, so the candidate
    # sets are guaranteed to differ node-for-node.
    assert set(a.candidate_nodes).isdisjoint(set(b.candidate_nodes))


# --------------------------------------------------------------------------- #
# Seed range and bucket boundary
# --------------------------------------------------------------------------- #


def test_seed_range_enforced_for_calibration() -> None:
    with pytest.raises(ValueError):
        generate_episode(
            seed=CALIBRATION_SEED_MIN - 1, bucket=TemplateBucket.CALIBRATION
        )
    with pytest.raises(ValueError):
        generate_episode(
            seed=CALIBRATION_SEED_MAX + 1, bucket=TemplateBucket.CALIBRATION
        )
    # A calibration seed passed to the confirmatory bucket is refused.
    with pytest.raises(ValueError):
        generate_episode(
            seed=CALIBRATION_SEED_MIN, bucket=TemplateBucket.CONFIRMATION
        )


def test_seed_range_enforced_for_confirmatory() -> None:
    with pytest.raises(ValueError):
        generate_episode(
            seed=CONFIRMATION_SEED_MIN - 1, bucket=TemplateBucket.CONFIRMATION
        )
    with pytest.raises(ValueError):
        generate_episode(
            seed=CONFIRMATION_SEED_MAX + 1, bucket=TemplateBucket.CONFIRMATION
        )


def test_bucket_tag_matches_bucket() -> None:
    cal = generate_episode(seed=100_100, bucket=TemplateBucket.CALIBRATION)
    conf = generate_episode(seed=200_100, bucket=TemplateBucket.CONFIRMATION)
    assert cal.template_family_split == "calibration"
    assert conf.template_family_split == "confirmatory"


# --------------------------------------------------------------------------- #
# Holdout disjointness
# --------------------------------------------------------------------------- #


def _template_id_of(episode: EpisodeSpec) -> str:
    """Recover the human-readable template id from the episode id."""
    return episode.episode_id.split("::", 1)[0]


def test_paraphrase_family_holdout_disjointness() -> None:
    held_family = PARAPHRASE_FAMILIES[0]
    seeds = range(CALIBRATION_SEED_MIN, CALIBRATION_SEED_MIN + 200)

    hit_held = False
    hit_kept = False
    for seed in seeds:
        ep = generate_episode(
            seed=seed,
            bucket=TemplateBucket.CALIBRATION,
            holdout=held_family,
        )
        template_id = _template_id_of(ep)
        family = paraphrase_family_of(template_id)
        # Held-out paraphrase family must never surface.
        assert family != held_family
        if family in (f for f in PARAPHRASE_FAMILIES if f != held_family):
            hit_kept = True
    assert hit_kept, "at least one non-held paraphrase family must be reached"
    assert not hit_held  # trivially satisfied


def test_whole_template_holdout_disjointness() -> None:
    held_template = calibration_template_ids()[0]
    seeds = range(CALIBRATION_SEED_MIN, CALIBRATION_SEED_MIN + 200)

    for seed in seeds:
        ep = generate_episode(
            seed=seed,
            bucket=TemplateBucket.CALIBRATION,
            holdout=held_template,
        )
        assert _template_id_of(ep) != held_template


def test_unknown_holdout_is_rejected() -> None:
    with pytest.raises(ValueError):
        generate_episode(
            seed=100_000,
            bucket=TemplateBucket.CALIBRATION,
            holdout="not-a-real-holdout-name",
        )


# --------------------------------------------------------------------------- #
# Anti-leakage boundary at the family / sealed-env interface
# --------------------------------------------------------------------------- #


def test_episode_context_carries_no_sealed_fields() -> None:
    """A policy view exposes no role, no utility, no answer key.

    Duplicated at the family boundary from the sealed_env regression
    suite so a family-level regression that widens the policy view lands
    on this test file too.
    """
    episode = generate_episode(seed=100_007, bucket=TemplateBucket.CALIBRATION)
    env = SealedEnvironment(episode)
    context = env.observe(seed=100_007)

    assert not hasattr(context, "role")
    assert not hasattr(context, "utility")
    assert not hasattr(context, "_answer_key")

    # Positive coverage — the policy sees the expected fields and only
    # those fields.
    assert context.family == FAMILY_NAME
    assert context.budget == DEFAULT_BUDGET
    assert context.candidate_nodes == episode.candidate_nodes
    assert context.context_nodes == episode.context_nodes


def test_wrong_prior_matches_preregistration() -> None:
    """The care anchor weights match PREREGISTRATION.md §5's magnitudes.

    Alarm nodes carry ``w_alarm_init = 1.0``, the load-bearing
    commitment carries ``w_commit_init = 0.05``, and every other node
    carries a positive uniform baseline strictly between those.
    """
    episode = generate_episode(seed=100_013, bucket=TemplateBucket.CALIBRATION)
    answer_key_node = episode._answer_key[0]
    prior = dict(episode.care_anchors)

    # Load-bearing commitment is suppressed.
    assert prior[answer_key_node] == pytest.approx(0.05)

    # At least one alarm node is inflated.
    alarm_nodes = [
        node
        for node, role in episode.role.items()
        if role == "current_day_trending"
    ]
    assert alarm_nodes, "at least one alarm-role node must be present"
    for node in alarm_nodes:
        assert prior[node] == pytest.approx(1.0)

    # Every other node sits at the uniform baseline strictly between the
    # suppressed and inflated weights.
    for node, weight in prior.items():
        if node == answer_key_node or node in alarm_nodes:
            continue
        assert 0.05 < weight < 1.0


# --------------------------------------------------------------------------- #
# Non-trivial distractor difficulty (baselines from graph_learn)
# --------------------------------------------------------------------------- #


def _rank_candidates_by_ppr(episode: EpisodeSpec, restart: dict) -> list[str]:
    """Rank the episode's candidates by PPR mass on the withheld graph."""
    graph = build_withheld_graph(
        seed=episode.seed, size=GRAPH_SIZE, family=FAMILY_NAME
    )
    ppr = personalized_pagerank(graph, restart)
    return sorted(
        episode.candidate_nodes,
        key=lambda node: ppr.scores.get(node, 0.0),
        reverse=True,
    )


def test_context_only_ppr_fails_on_non_trivial_slice() -> None:
    """A plain context-only PPR baseline built from graph_learn primitives
    does not trivially achieve hit@1 = 1 on every calibration seed.

    We evaluate 100 calibration seeds and require at least 10 misses.
    That 10% floor is generous — the family's zone geometry places the
    commitment zone many chain hops away from the active-context window,
    so the actual miss rate is much higher; we assert the low floor to
    keep the regression stable under future minor edits.
    """
    misses = 0
    total = 100
    for seed in range(
        CALIBRATION_SEED_MIN, CALIBRATION_SEED_MIN + total
    ):
        episode = generate_episode(
            seed=seed, bucket=TemplateBucket.CALIBRATION
        )
        restart = {node: 1.0 for node in episode.context_nodes}
        ranked = _rank_candidates_by_ppr(episode, restart)
        top1 = ranked[0]

        env = SealedEnvironment(episode)
        env.observe(seed=seed)
        outcome = env.evaluate(
            RetrievalChoice(selected=(top1,), wall_actions=0)
        )
        if not outcome.constraint_preserved:
            misses += 1
    assert misses >= 10, (
        f"context-only PPR too strong: only {misses}/{total} misses; "
        "family distractor density is not honest"
    )


def test_care_only_ppr_fails_on_non_trivial_slice() -> None:
    """A care-only PPR baseline seeded from the wrong prior cannot
    trivially achieve hit@1 = 1 on every calibration seed.

    The wrong prior brightens the alarm zone by design, so care-only
    PPR is expected to preferentially select alarm-region candidates
    over the load-bearing commitment. We assert at least 10 misses in
    100 seeds as a stable lower bound.
    """
    misses = 0
    total = 100
    for seed in range(
        CALIBRATION_SEED_MIN, CALIBRATION_SEED_MIN + total
    ):
        episode = generate_episode(
            seed=seed, bucket=TemplateBucket.CALIBRATION
        )
        restart = dict(episode.care_anchors)
        ranked = _rank_candidates_by_ppr(episode, restart)
        top1 = ranked[0]

        env = SealedEnvironment(episode)
        env.observe(seed=seed)
        outcome = env.evaluate(
            RetrievalChoice(selected=(top1,), wall_actions=0)
        )
        if not outcome.constraint_preserved:
            misses += 1
    assert misses >= 10, (
        f"care-only PPR too strong: only {misses}/{total} misses; "
        "the wrong prior is not adversarial enough"
    )
