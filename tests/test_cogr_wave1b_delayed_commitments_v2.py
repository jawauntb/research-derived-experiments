"""Tests for the Wave 1b redesigned ``delayed_commitments_v2`` family.

The v2 redesign lands two Wave 1a-KILL correctives at the family
generator layer:

1. **Recency != oracle.** The load-bearing memory is placed at a random
   non-recent event-stream position on the great majority of episodes,
   so no generic-signal baseline (recency, embedding_sim, care_only,
   freq_only, salience, value, priority) reaches ``oracle_recall_at_k
   >= 0.8`` on a calibration sample.

2. **Bundle planting.** Each episode plants a
   :class:`BundleManifest` recording which of the five combinatorial
   bundle types the episode carries — useful singletons, contradictory
   pairs, complementary pairs, dangerous conjunctions, isolation
   distractors. The manifest is evaluator-only and unreachable from any
   policy path.

The tests here exercise both correctives at the family boundary and
duplicate the Wave 0 non-ceiling + holdout-disjointness regressions on
the v2 family to catch a family-level regression that would silently
loosen the wave1b promotion contract.
"""

from __future__ import annotations

from typing import Callable, Sequence

import pytest

from experiments.concern_gated_retrieval_e2.wave0.baselines import (
    care_only_ppr,
    context_only_ppr,
    embedding_similarity,
    freq_only,
    info_matched_priority,
    info_matched_recency,
    info_matched_value,
)
from experiments.concern_gated_retrieval_e2.wave0.sealed_env import (
    EpisodeSpec,
    IntegrityAudit,
    LeakageError,
    RetrievalChoice,
    SealedEnvironment,
)
from experiments.concern_gated_retrieval_e2.wave0.template_split import (
    TemplateBucket,
)
from experiments.concern_gated_retrieval_e2.wave1b.families.delayed_commitments_v2 import (
    BUNDLE_COMPLEMENTARY_PAIR,
    BUNDLE_CONTRADICTORY_PAIR,
    BUNDLE_DANGEROUS_CONJUNCTION,
    BUNDLE_ISOLATION_DISTRACTOR,
    BUNDLE_TYPES,
    BUNDLE_USEFUL_SINGLETON,
    BundleManifest,
    CALIBRATION_SEED_MIN,
    DEFAULT_BUDGET,
    PARAPHRASE_FAMILIES,
    RECENT_POSITIONS,
    bundle_manifest,
    calibration_template_ids,
    generate_episode,
    oracle_recall_at_k_for_baseline,
    paraphrase_family_of,
    recency_load_bearing_correlation,
)


# --------------------------------------------------------------------------- #
# Baseline slate used by the oracle-recall pre-run assertion.
# --------------------------------------------------------------------------- #


#: The generic-signal baselines Wave 1b's §4 pre-run assertion covers.
#: Each ``(label, callable)`` maps a Spencer echo-chamber name to the
#: closest matching wave0 baseline:
#:
#: * ``recency`` -> ``info_matched_recency``
#: * ``embedding_sim`` -> ``embedding_similarity``
#: * ``care_only`` -> ``care_only_ppr``
#: * ``freq_only`` -> ``freq_only``
#: * ``salience`` -> ``context_only_ppr``   (current-view diffusion)
#: * ``value`` -> ``info_matched_value``
#: * ``priority`` -> ``info_matched_priority``
_GENERIC_SIGNAL_BASELINES: tuple[tuple[str, Callable[..., Sequence[str]]], ...] = (
    ("recency", info_matched_recency),
    ("embedding_sim", embedding_similarity),
    ("care_only", care_only_ppr),
    ("freq_only", freq_only),
    ("salience", context_only_ppr),
    ("value", info_matched_value),
    ("priority", info_matched_priority),
)


# --------------------------------------------------------------------------- #
# 1. Anti-recency: load-bearing not at a recent position on most episodes.
# --------------------------------------------------------------------------- #


def test_recency_load_bearing_correlation_below_half() -> None:
    """Wave 1b pre-run assertion: correlation between recency and
    load-bearing membership stays under 0.5 on a 100-seed calibration
    sample."""
    seeds = range(CALIBRATION_SEED_MIN, CALIBRATION_SEED_MIN + 100)
    corr = recency_load_bearing_correlation(list(seeds))
    assert corr < 0.5, (
        f"recency_load_bearing_correlation = {corr:.3f} is at or above the "
        "wave1b 0.5 floor; the anti-recency layout is not honest"
    )


# --------------------------------------------------------------------------- #
# 2. Pre-run assertion: no generic-signal baseline reaches oracle_recall >= 0.8
# --------------------------------------------------------------------------- #


def test_no_generic_signal_reaches_oracle_recall_08() -> None:
    """Every wave0 generic-signal baseline stays strictly below the
    ``oracle_recall_at_k >= 0.8`` pre-run floor on a 60-seed
    calibration sample. Reproducing this floor on the confirmatory
    sweep would recreate the Wave 1a KILL.
    """
    seeds = list(range(CALIBRATION_SEED_MIN, CALIBRATION_SEED_MIN + 60))
    for label, baseline in _GENERIC_SIGNAL_BASELINES:
        recall = oracle_recall_at_k_for_baseline(
            baseline, seeds, k=DEFAULT_BUDGET
        )
        assert recall < 0.8, (
            f"generic-signal baseline {label!r} reached oracle_recall = "
            f"{recall:.3f} >= 0.8 on {len(seeds)} v2 seeds; the family is "
            "not anti-recency-honest"
        )


# --------------------------------------------------------------------------- #
# 3. Non-ceiling: neither care-only nor context-only PPR trivially hits.
# --------------------------------------------------------------------------- #


def test_non_ceiling_care_only_and_context_only_ppr() -> None:
    """Both wave0 single-source PPR baselines miss on at least 10% of a
    100-seed calibration sample. Mirrors the wave0 v1 non-ceiling
    regression at the v2 boundary."""
    total = 100
    care_misses = 0
    ctx_misses = 0
    for seed in range(CALIBRATION_SEED_MIN, CALIBRATION_SEED_MIN + total):
        episode = generate_episode(
            seed=seed, bucket=TemplateBucket.CALIBRATION
        )
        env = SealedEnvironment(episode)
        context = env.observe(seed=seed)

        care_pick = care_only_ppr(context, DEFAULT_BUDGET)
        ctx_pick = context_only_ppr(context, DEFAULT_BUDGET)

        care_env = SealedEnvironment(
            generate_episode(seed=seed, bucket=TemplateBucket.CALIBRATION)
        )
        care_env.observe(seed=seed)
        care_out = care_env.evaluate(
            RetrievalChoice(selected=tuple(care_pick), wall_actions=0)
        )
        if not care_out.constraint_preserved:
            care_misses += 1

        ctx_env = SealedEnvironment(
            generate_episode(seed=seed, bucket=TemplateBucket.CALIBRATION)
        )
        ctx_env.observe(seed=seed)
        ctx_out = ctx_env.evaluate(
            RetrievalChoice(selected=tuple(ctx_pick), wall_actions=0)
        )
        if not ctx_out.constraint_preserved:
            ctx_misses += 1

        # Silence the unused observation of the first env; the assert
        # only needs the per-baseline environments above.
        del context, env

    assert care_misses >= 10, (
        f"care_only_ppr too strong on v2: only {care_misses}/{total} misses"
    )
    assert ctx_misses >= 10, (
        f"context_only_ppr too strong on v2: only {ctx_misses}/{total} misses"
    )


# --------------------------------------------------------------------------- #
# 4. Holdout disjointness — paraphrase-family and whole-template.
# --------------------------------------------------------------------------- #


def _template_id_of(episode: EpisodeSpec) -> str:
    return episode.episode_id.split("::", 1)[0]


def test_holdout_disjointness_paraphrase_and_template() -> None:
    """A paraphrase-family holdout and a whole-template holdout each
    remove their target from the calibration selection pool across a
    200-seed sweep."""
    held_family = PARAPHRASE_FAMILIES[0]
    seeds = range(CALIBRATION_SEED_MIN, CALIBRATION_SEED_MIN + 200)

    saw_other_family = False
    for seed in seeds:
        ep = generate_episode(
            seed=seed,
            bucket=TemplateBucket.CALIBRATION,
            holdout=held_family,
        )
        template_id = _template_id_of(ep)
        family = paraphrase_family_of(template_id)
        assert family != held_family, (
            f"paraphrase-family holdout {held_family!r} surfaced on seed "
            f"{seed} (template {template_id!r})"
        )
        if family != held_family:
            saw_other_family = True
    assert saw_other_family, "no non-held paraphrase family reached in sweep"

    held_template = calibration_template_ids()[0]
    for seed in seeds:
        ep = generate_episode(
            seed=seed,
            bucket=TemplateBucket.CALIBRATION,
            holdout=held_template,
        )
        assert _template_id_of(ep) != held_template


# --------------------------------------------------------------------------- #
# 5. Bundle-type coverage across a 100-seed sample.
# --------------------------------------------------------------------------- #


def test_all_bundle_types_reached_in_100_seed_sample() -> None:
    """Types (i)–(v) each appear at least once in a 100-seed calibration
    sample:

    * (i)   useful_singleton
    * (ii)  contradictory_pair
    * (iii) complementary_pair
    * (iv)  dangerous_conjunction
    * (v)   isolation_distractor

    The useful singleton is planted every episode (the load-bearing
    memory), so its presence is trivial; the other four types are
    planted per template and must each surface at least once under
    uniform template selection.
    """
    seen_primary: set[str] = set()
    seen_useful_singleton = False
    seen_contradictory_pair = False
    seen_complementary_pair = False
    seen_dangerous_conjunction = False
    seen_isolation_distractor = False

    for seed in range(CALIBRATION_SEED_MIN, CALIBRATION_SEED_MIN + 100):
        episode = generate_episode(
            seed=seed, bucket=TemplateBucket.CALIBRATION
        )
        manifest = bundle_manifest(episode)
        assert isinstance(manifest, BundleManifest)
        seen_primary.add(manifest.primary_bundle_type)

        # Every episode plants a useful singleton (the load-bearing).
        assert manifest.useful_singleton, (
            "useful_singleton plant missing on seed"
        )
        seen_useful_singleton = True

        if manifest.contradictory_pair is not None:
            seen_contradictory_pair = True
            assert len(manifest.contradictory_pair) == 2
            assert manifest.contradictory_pair[0] != manifest.contradictory_pair[1]
        if manifest.complementary_pair is not None:
            seen_complementary_pair = True
            assert len(manifest.complementary_pair) == 2
            assert manifest.complementary_pair[0] != manifest.complementary_pair[1]
        if manifest.dangerous_conjunction is not None:
            seen_dangerous_conjunction = True
            assert len(manifest.dangerous_conjunction) == 3
            assert len(set(manifest.dangerous_conjunction)) == 3
        if manifest.isolation_distractor is not None:
            seen_isolation_distractor = True

    # Every one of the five types must have been reached.
    assert seen_useful_singleton, "type (i) useful_singleton missing"
    assert seen_contradictory_pair, "type (ii) contradictory_pair missing"
    assert seen_complementary_pair, "type (iii) complementary_pair missing"
    assert seen_dangerous_conjunction, "type (iv) dangerous_conjunction missing"
    assert seen_isolation_distractor, "type (v) isolation_distractor missing"

    # Primary-bundle-type coverage sanity — every bundle type from the
    # canonical list must show up as at least one episode's primary
    # plant. (For a 100-seed uniform sample this is highly likely.)
    assert set(BUNDLE_TYPES).issubset(seen_primary), (
        "primary_bundle_type distribution missing some types: "
        f"{sorted(set(BUNDLE_TYPES) - seen_primary)}"
    )


# --------------------------------------------------------------------------- #
# 6. BundleManifest is refused by any policy path.
# --------------------------------------------------------------------------- #


def test_bundle_manifest_refused_by_policy_paths() -> None:
    """Policy paths cannot reach the manifest:

    * :class:`EpisodeContext` never carries the manifest or any sealed
      field.
    * A policy that dereferences ``episode._answer_key`` fails
      :meth:`IntegrityAudit.assert_clean` at import time.
    * :func:`bundle_manifest` refuses an :class:`EpisodeContext`
      argument with a :class:`LeakageError`.
    * A legitimate evaluator call with the sealed :class:`EpisodeSpec`
      returns the manifest.
    """
    episode = generate_episode(
        seed=CALIBRATION_SEED_MIN, bucket=TemplateBucket.CALIBRATION
    )
    env = SealedEnvironment(episode)
    context = env.observe(seed=CALIBRATION_SEED_MIN)

    # (a) EpisodeContext carries no evaluator-only field at all.
    assert not hasattr(context, "role")
    assert not hasattr(context, "utility")
    assert not hasattr(context, "_answer_key")
    assert not hasattr(context, "bundle_manifest")

    # (b) A policy that touches _answer_key fails the AST audit.
    def _leaky_policy_reads_answer_key(ctx: object) -> object:
        return ctx._answer_key  # ty: ignore[unresolved-attribute]  # noqa

    with pytest.raises(LeakageError):
        IntegrityAudit.assert_clean(_leaky_policy_reads_answer_key)

    # (c) bundle_manifest refuses to accept an EpisodeContext.
    with pytest.raises(LeakageError):
        bundle_manifest(context)  # ty: ignore[invalid-argument-type]  # noqa

    # (d) bundle_manifest also refuses a non-episode object.
    with pytest.raises(LeakageError):
        bundle_manifest(object())  # ty: ignore[invalid-argument-type]  # noqa

    # (e) A legitimate evaluator call returns the planted manifest and
    # exposes the recent-positions convention consistently with the
    # public constant used by the wave1b assertion helper.
    manifest = bundle_manifest(episode)
    assert isinstance(manifest, BundleManifest)
    assert manifest.recent_positions == RECENT_POSITIONS
    assert manifest.load_bearing_position >= 0
    assert manifest.useful_singleton == episode._answer_key[0]
    assert manifest.primary_bundle_type in BUNDLE_TYPES
    # The primary_bundle_type non-singleton members must be consistent:
    # for the non-singleton four, the corresponding field is set; for
    # the singleton, all four non-singleton fields are None.
    if manifest.primary_bundle_type == BUNDLE_USEFUL_SINGLETON:
        assert manifest.contradictory_pair is None
        assert manifest.complementary_pair is None
        assert manifest.dangerous_conjunction is None
        assert manifest.isolation_distractor is None
    elif manifest.primary_bundle_type == BUNDLE_CONTRADICTORY_PAIR:
        assert manifest.contradictory_pair is not None
    elif manifest.primary_bundle_type == BUNDLE_COMPLEMENTARY_PAIR:
        assert manifest.complementary_pair is not None
    elif manifest.primary_bundle_type == BUNDLE_DANGEROUS_CONJUNCTION:
        assert manifest.dangerous_conjunction is not None
    elif manifest.primary_bundle_type == BUNDLE_ISOLATION_DISTRACTOR:
        assert manifest.isolation_distractor is not None
