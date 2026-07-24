"""Tests for the Wave 1b ``maintenance_fault_v2`` procedural family.

Six properties, one test group each, matching the wave 1b family-module
build brief:

1. **Determinism.** ``generate_episode(seed, bucket, holdout)`` is a
   pure function of its inputs — the same tuple produces a byte-
   identical :class:`EpisodeSpec` and (via the module-level manifest
   registry) a byte-identical :class:`BundleManifest`.
2. **Anti-recency.** The load-bearing early observation sits at a
   non-recent stream position on the great majority of episodes across
   the 100-seed calibration sample the wave 1b pre-run assertion
   specifies. ``recency_load_bearing_correlation`` is strictly below
   0.5.
3. **Bundle-planting completeness.** A broad seed sweep produces
   :class:`BundleManifest` records that between them include every
   planted bundle type (useful singleton, contradictory pair,
   complementary pair, dangerous conjunction, isolation distractor).
   Each individual manifest names exactly one non-singleton bundle;
   the corresponding candidate nodes are present in the episode's
   candidate set and carry the correct role labels. The complementary
   pair specifically obeys the maintenance-domain twist: the "later
   reveal" member's stream position is strictly smaller than the
   "early reading" member's.
4. **Generic-signal oracle-recall audit.** For every generic-signal
   baseline the wave 1b pre-run assertion names, the family-local
   oracle-recall@k against the singleton answer key is strictly
   below 0.8 over a 100-seed calibration sample.
5. **Interaction-recovery audit.** For every generic-signal baseline,
   the fraction of episodes on which the top-k selection recovers
   *both* members of a planted complementary pair is strictly below
   0.5 over the 100-seed sample.
6. **Anti-leakage.** :func:`generate_episode` is
   :class:`IntegrityAudit`-clean. :func:`bundle_manifest` and
   :func:`recency_load_bearing_correlation` are deliberately NOT
   audit-clean (they access the sealed
   :attr:`EpisodeSpec._answer_key`); the tests document that
   evaluator-only expectation. Passing an :class:`EpisodeContext` to
   :func:`bundle_manifest` raises :class:`LeakageError`.

The wave 1b family is a v2 redesign of the wave 0 maintenance_fault
family; these tests re-check the wave 0 invariants (seed-range refusal,
non-ceiling clamp, wrong-prior shape, holdout honored) so a wave 1b
regression cannot slip through by borrowing a wave 0 guarantee.
"""

from __future__ import annotations



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
    SealedEnvironment,
)
from experiments.concern_gated_retrieval_e2.wave0.template_split import (
    TemplateBucket,
)
from experiments.concern_gated_retrieval_e2.wave1b.families import (
    maintenance_fault_v2 as mfv2,
)
from experiments.concern_gated_retrieval_e2.wave1b.families.maintenance_fault_v2 import (
    BUNDLE_TYPES,
    BUNDLE_USEFUL_SINGLETON,
    CALIBRATION_SEED_MAX,
    CALIBRATION_SEED_MIN,
    CONFIRMATION_SEED_MAX,
    CONFIRMATION_SEED_MIN,
    DEFAULT_BUDGET,
    FAMILY_NAME,
    MAX_UTILITY_DIFF,
    PARAPHRASE_FAMILIES,
    RECENT_POSITIONS,
    ROLE_ALARM,
    ROLE_COMPLEMENTARY,
    ROLE_CONTRADICTORY,
    ROLE_DANGEROUS,
    ROLE_ISOLATION,
    ROLE_LOAD_BEARING,
    ROLE_SEMANTIC_DECOY,
    TEMPLATES,
    W_ALARM_INIT,
    W_COMMIT_INIT,
    BundleManifest,
    bundle_manifest,
    clear_manifests,
    generate_episode,
    oracle_recall_at_k_for_baseline,
    recency_load_bearing_correlation,
)


# ---------------------------------------------------------------------------
# Template registry shape (structural precondition for the properties)
# ---------------------------------------------------------------------------


def test_registry_has_at_least_thirty_templates() -> None:
    assert len(TEMPLATES) >= 30
    cal = [t for t in TEMPLATES if t.bucket is TemplateBucket.CALIBRATION]
    conf = [t for t in TEMPLATES if t.bucket is TemplateBucket.CONFIRMATION]
    assert len(cal) == 30
    assert len(conf) == 35
    assert len({t.template_id for t in TEMPLATES}) == len(TEMPLATES)
    used = {t.paraphrase_family for t in TEMPLATES}
    assert used == set(PARAPHRASE_FAMILIES)
    # Every bundle type is represented in the calibration pool.
    cal_bundles = {t.primary_bundle_type for t in cal}
    assert cal_bundles == set(BUNDLE_TYPES)


# ---------------------------------------------------------------------------
# (1) Determinism
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("seed", [100_000, 100_042, 100_777, 100_999])
def test_generate_episode_is_deterministic(seed: int) -> None:
    a = generate_episode(seed=seed, bucket=TemplateBucket.CALIBRATION)
    b = generate_episode(seed=seed, bucket=TemplateBucket.CALIBRATION)

    assert isinstance(a, EpisodeSpec) and isinstance(b, EpisodeSpec)
    assert a.episode_id == b.episode_id
    assert a.family == b.family == FAMILY_NAME
    assert a.context_nodes == b.context_nodes
    assert a.candidate_nodes == b.candidate_nodes
    assert a.budget == b.budget
    assert dict(a.care_anchors) == dict(b.care_anchors)
    assert dict(a.role) == dict(b.role)
    assert dict(a.utility) == dict(b.utility)
    assert a._answer_key == b._answer_key


@pytest.mark.parametrize("seed", [100_000, 100_050, 100_500, 100_999])
def test_bundle_manifest_is_deterministic(seed: int) -> None:
    ep_a = generate_episode(seed=seed, bucket=TemplateBucket.CALIBRATION)
    manifest_a = bundle_manifest(ep_a)
    ep_b = generate_episode(seed=seed, bucket=TemplateBucket.CALIBRATION)
    manifest_b = bundle_manifest(ep_b)

    assert isinstance(manifest_a, BundleManifest)
    assert manifest_a.episode_id == manifest_b.episode_id
    assert manifest_a.seed == manifest_b.seed == seed
    assert manifest_a.primary_bundle_type == manifest_b.primary_bundle_type
    assert manifest_a.useful_singleton == manifest_b.useful_singleton
    assert manifest_a.contradictory_pair == manifest_b.contradictory_pair
    assert manifest_a.complementary_pair == manifest_b.complementary_pair
    assert manifest_a.dangerous_conjunction == manifest_b.dangerous_conjunction
    assert manifest_a.isolation_distractor == manifest_b.isolation_distractor
    assert manifest_a.semantic_decoy == manifest_b.semantic_decoy
    assert dict(manifest_a.stream_positions) == dict(manifest_b.stream_positions)
    assert manifest_a.load_bearing_position == manifest_b.load_bearing_position


def test_generate_episode_differs_across_seeds() -> None:
    a = generate_episode(seed=100_000, bucket=TemplateBucket.CALIBRATION)
    b = generate_episode(seed=100_001, bucket=TemplateBucket.CALIBRATION)
    assert a.episode_id != b.episode_id
    assert set(a.candidate_nodes).isdisjoint(set(b.candidate_nodes))


# ---------------------------------------------------------------------------
# (2) Anti-recency
# ---------------------------------------------------------------------------


def test_recency_load_bearing_correlation_below_half() -> None:
    corr = recency_load_bearing_correlation(
        list(range(CALIBRATION_SEED_MIN, CALIBRATION_SEED_MIN + 100))
    )
    assert corr < 0.5, (
        f"anti-recency: load-bearing sits in the top-3 recency slots on "
        f"{corr:.3f} of episodes; wave 1b PREREGISTRATION.md §4 requires "
        "< 0.5"
    )


def test_load_bearing_non_recent_on_broad_sweep_is_majority() -> None:
    non_recent = 0
    total = 0
    for seed in range(CALIBRATION_SEED_MIN, CALIBRATION_SEED_MIN + 200):
        episode = generate_episode(seed=seed, bucket=TemplateBucket.CALIBRATION)
        manifest = bundle_manifest(episode)
        if manifest.load_bearing_position not in set(RECENT_POSITIONS):
            non_recent += 1
        total += 1
    frac_non_recent = non_recent / total
    assert frac_non_recent >= 0.5, (
        f"load-bearing at a non-recent position on only {frac_non_recent:.3f} "
        "of episodes; wave 1b PREREGISTRATION.md §4 anti-recency (1) "
        "requires >= 0.5"
    )


def test_recent_distractors_dominate_load_bearing_on_non_recent_variants() -> None:
    # On every seed whose template is NOT a load_bearing_recent variant,
    # at least three candidates sit at strictly lower stream position
    # (higher recency) than the load-bearing early observation. The
    # non_recent bulk is what the anti-recency contract is about.
    for seed in range(CALIBRATION_SEED_MIN, CALIBRATION_SEED_MIN + 30):
        episode = generate_episode(seed=seed, bucket=TemplateBucket.CALIBRATION)
        manifest = bundle_manifest(episode)
        template_id = episode.episode_id.split("::", 1)[0]
        template = next(t for t in TEMPLATES if t.template_id == template_id)
        if template.load_bearing_recent:
            # These variants deliberately put the load-bearing in the
            # recent window; skip them for this check (the aggregate
            # non-recent-majority test above covers the ensemble
            # invariant).
            continue
        lb_pos = manifest.load_bearing_position
        assert lb_pos not in RECENT_POSITIONS
        earlier = [
            pos
            for pos in manifest.stream_positions.values()
            if pos < lb_pos
        ]
        assert len(earlier) >= 3, (
            f"seed {seed}: only {len(earlier)} candidates dominate the "
            f"load-bearing early observation on recency; wave 1b "
            "requires >= 3 recent distractors"
        )


# ---------------------------------------------------------------------------
# (3) Bundle-planting completeness
# ---------------------------------------------------------------------------


def test_every_bundle_type_present_across_seed_sweep() -> None:
    seen: set[str] = set()
    for seed in range(CALIBRATION_SEED_MIN, CALIBRATION_SEED_MIN + 100):
        episode = generate_episode(seed=seed, bucket=TemplateBucket.CALIBRATION)
        manifest = bundle_manifest(episode)
        seen.add(manifest.primary_bundle_type)
    assert seen == set(BUNDLE_TYPES), (
        f"bundle-planting incomplete: saw {sorted(seen)}, missing "
        f"{sorted(set(BUNDLE_TYPES) - seen)}"
    )


def test_each_manifest_names_exactly_one_non_singleton_bundle() -> None:
    for seed in range(CALIBRATION_SEED_MIN, CALIBRATION_SEED_MIN + 30):
        episode = generate_episode(seed=seed, bucket=TemplateBucket.CALIBRATION)
        manifest = bundle_manifest(episode)
        non_singleton_slots = [
            manifest.contradictory_pair,
            manifest.complementary_pair,
            manifest.dangerous_conjunction,
            manifest.isolation_distractor,
        ]
        filled = [s for s in non_singleton_slots if s is not None]
        if manifest.primary_bundle_type == BUNDLE_USEFUL_SINGLETON:
            assert len(filled) == 0
        else:
            assert len(filled) == 1, (
                f"seed {seed}: manifest for {manifest.primary_bundle_type} "
                f"has {len(filled)} filled non-singleton slots; expected 1"
            )
        # Useful singleton is always the load-bearing early observation.
        (load_bearing,) = episode._answer_key
        assert manifest.useful_singleton == load_bearing


def test_bundle_members_are_candidate_nodes_with_correct_role_labels() -> None:
    for seed in range(CALIBRATION_SEED_MIN, CALIBRATION_SEED_MIN + 30):
        episode = generate_episode(seed=seed, bucket=TemplateBucket.CALIBRATION)
        manifest = bundle_manifest(episode)
        candidates = set(episode.candidate_nodes)

        assert manifest.useful_singleton in candidates
        assert episode.role[manifest.useful_singleton] == ROLE_LOAD_BEARING

        if manifest.contradictory_pair is not None:
            a, b = manifest.contradictory_pair
            assert a in candidates and b in candidates
            assert a != b
            assert episode.role[a] == ROLE_CONTRADICTORY
            assert episode.role[b] == ROLE_CONTRADICTORY
        if manifest.complementary_pair is not None:
            early_reading, later_reveal = manifest.complementary_pair
            assert early_reading in candidates and later_reveal in candidates
            assert early_reading != later_reveal
            assert episode.role[early_reading] == ROLE_COMPLEMENTARY
            assert episode.role[later_reveal] == ROLE_COMPLEMENTARY
            # Maintenance-domain twist: the later reveal is more recent
            # (smaller stream_pos) than the early reading.
            pos_early = manifest.stream_positions[early_reading]
            pos_reveal = manifest.stream_positions[later_reveal]
            assert pos_reveal < pos_early, (
                f"seed {seed}: complementary pair violates the "
                f"maintenance-domain twist: reveal_pos={pos_reveal} "
                f"should be < early_reading_pos={pos_early}"
            )
        if manifest.dangerous_conjunction is not None:
            aa, bb, cc = manifest.dangerous_conjunction
            trio = {aa, bb, cc}
            assert len(trio) == 3
            for node in trio:
                assert node in candidates
                assert episode.role[node] == ROLE_DANGEROUS
        if manifest.isolation_distractor is not None:
            node = manifest.isolation_distractor
            assert node in candidates
            assert episode.role[node] == ROLE_ISOLATION

        # Semantic decoy is always present and always has its labelled
        # role.
        assert manifest.semantic_decoy in candidates
        assert episode.role[manifest.semantic_decoy] == ROLE_SEMANTIC_DECOY


# ---------------------------------------------------------------------------
# (4) Generic-signal oracle-recall audit
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "baseline_name,baseline",
    [
        ("info_matched_recency", info_matched_recency),
        ("info_matched_value", info_matched_value),
        ("info_matched_priority", info_matched_priority),
        ("care_only_ppr", care_only_ppr),
        ("context_only_ppr", context_only_ppr),
        ("freq_only", freq_only),
        ("embedding_similarity", embedding_similarity),
    ],
)
def test_generic_baseline_oracle_recall_below_threshold(
    baseline_name: str, baseline
) -> None:
    seeds = list(range(CALIBRATION_SEED_MIN, CALIBRATION_SEED_MIN + 100))
    recall = oracle_recall_at_k_for_baseline(
        baseline, seeds, k=DEFAULT_BUDGET, bucket=TemplateBucket.CALIBRATION
    )
    assert recall < 0.8, (
        f"generic baseline {baseline_name!r} recalls the load-bearing "
        f"early observation at oracle_recall@{DEFAULT_BUDGET} = "
        f"{recall:.3f}; wave 1b PREREGISTRATION.md §4 requires < 0.8"
    )


# ---------------------------------------------------------------------------
# (5) Interaction-recovery audit
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "baseline_name,baseline",
    [
        ("info_matched_recency", info_matched_recency),
        ("info_matched_value", info_matched_value),
        ("info_matched_priority", info_matched_priority),
        ("care_only_ppr", care_only_ppr),
        ("context_only_ppr", context_only_ppr),
        ("freq_only", freq_only),
        ("embedding_similarity", embedding_similarity),
    ],
)
def test_generic_baseline_interaction_recovery_below_half(
    baseline_name: str, baseline
) -> None:
    # Compute interaction recovery locally: for each seed whose planted
    # bundle is a complementary pair, check whether the baseline's
    # top-k selection contains both members.
    hits = 0
    total = 0
    for seed in range(CALIBRATION_SEED_MIN, CALIBRATION_SEED_MIN + 100):
        episode = generate_episode(seed=seed, bucket=TemplateBucket.CALIBRATION)
        manifest = bundle_manifest(episode)
        if manifest.complementary_pair is None:
            continue
        env = SealedEnvironment(episode, mode="calibration")
        context = env.observe(seed=seed)
        selected = frozenset(baseline(context, DEFAULT_BUDGET))
        a, b = manifest.complementary_pair
        if a in selected and b in selected:
            hits += 1
        total += 1
    if total == 0:
        pytest.skip("no complementary-pair episodes in sample")
    frac = hits / total
    assert frac < 0.5, (
        f"generic baseline {baseline_name!r} recovers a complementary "
        f"pair on {frac:.3f} of complementary-pair episodes; wave 1b "
        "PREREGISTRATION.md §4 requires < 0.5"
    )


# ---------------------------------------------------------------------------
# (6) Anti-leakage
# ---------------------------------------------------------------------------


def test_generate_episode_is_integrity_audit_clean() -> None:
    IntegrityAudit.assert_clean(generate_episode, recurse=True)


def test_bundle_manifest_deliberately_trips_integrity_audit() -> None:
    # bundle_manifest is EVALUATOR-ONLY. It reads episode._answer_key
    # deliberately so IntegrityAudit flags any policy path that references
    # it. This regression test documents that expectation.
    with pytest.raises(LeakageError):
        IntegrityAudit.assert_clean(bundle_manifest, recurse=True)


def test_recency_correlation_deliberately_trips_integrity_audit() -> None:
    with pytest.raises(LeakageError):
        IntegrityAudit.assert_clean(
            recency_load_bearing_correlation, recurse=True
        )


def test_bundle_manifest_refuses_non_episode_spec() -> None:
    # Passing a stand-in "policy-visible" object (or anything else that
    # is not an EpisodeSpec) raises LeakageError.
    with pytest.raises(LeakageError):
        bundle_manifest("not_an_episode")  # ty: ignore[invalid-argument-type]  # noqa


def test_bundle_manifest_registry_survives_clear_and_regenerate() -> None:
    # clear_manifests drops registered manifests; re-generating the
    # same seed re-registers the manifest so bundle_manifest still
    # resolves.
    ep = generate_episode(seed=100_100, bucket=TemplateBucket.CALIBRATION)
    _ = bundle_manifest(ep)
    clear_manifests()
    with pytest.raises(KeyError):
        bundle_manifest(ep)
    _ = generate_episode(seed=100_100, bucket=TemplateBucket.CALIBRATION)
    manifest = bundle_manifest(ep)
    assert manifest.seed == 100_100


# ---------------------------------------------------------------------------
# Wave 0 invariants preserved (regression coverage)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("seed", [100_000, 100_007, 100_512, 100_999])
def test_wrong_prior_shape(seed: int) -> None:
    episode = generate_episode(seed=seed, bucket=TemplateBucket.CALIBRATION)
    (load_bearing,) = episode._answer_key
    assert load_bearing in episode.candidate_nodes
    assert load_bearing not in episode.context_nodes

    alarms = [
        node
        for node, w in episode.care_anchors.items()
        if w == pytest.approx(W_ALARM_INIT)
        and episode.role.get(node) in (ROLE_ALARM, ROLE_ISOLATION)
    ]
    assert alarms, "wrong prior must inflate at least one alarm-like region"

    assert episode.care_anchors[load_bearing] == pytest.approx(W_COMMIT_INIT)

    baseline_nodes = [
        node
        for node, w in episode.care_anchors.items()
        if W_COMMIT_INIT < w < W_ALARM_INIT
    ]
    assert baseline_nodes, "wrong prior must leave a uniform baseline region"


def test_non_ceiling_utility_differential_bounded() -> None:
    for seed in (100_000, 100_050, 100_500, 100_999):
        episode = generate_episode(seed=seed, bucket=TemplateBucket.CALIBRATION)
        (load_bearing,) = episode._answer_key
        best_distractor = max(
            episode.utility[n]
            for n in episode.candidate_nodes
            if n != load_bearing
        )
        assert (
            episode.utility[load_bearing] - best_distractor
            <= MAX_UTILITY_DIFF + 1e-9
        )


def test_holdout_excludes_paraphrase_family() -> None:
    for holdout in PARAPHRASE_FAMILIES:
        for seed in range(100_000, 100_050):
            episode = generate_episode(
                seed=seed,
                bucket=TemplateBucket.CALIBRATION,
                holdout=holdout,
            )
            template_id = episode.episode_id.split("::", 1)[0]
            template = next(t for t in TEMPLATES if t.template_id == template_id)
            assert template.paraphrase_family != holdout
            assert template.bucket is TemplateBucket.CALIBRATION


def test_unknown_holdout_is_refused() -> None:
    with pytest.raises(ValueError):
        generate_episode(
            seed=100_000,
            bucket=TemplateBucket.CALIBRATION,
            holdout="answer_key",
        )
    with pytest.raises(TypeError):
        generate_episode(
            seed=100_000,
            bucket=TemplateBucket.CALIBRATION,
            holdout=42,  # ty: ignore[invalid-argument-type]  # noqa
        )


def test_calibration_bucket_refuses_out_of_range_seed() -> None:
    for bad in (
        CALIBRATION_SEED_MIN - 1,
        CALIBRATION_SEED_MAX + 1,
        200_000,
        0,
        -1,
    ):
        with pytest.raises(ValueError):
            generate_episode(seed=bad, bucket=TemplateBucket.CALIBRATION)


def test_confirmation_bucket_refuses_out_of_range_seed() -> None:
    for bad in (
        CONFIRMATION_SEED_MIN - 1,
        CONFIRMATION_SEED_MAX + 1,
        100_000,
        0,
    ):
        with pytest.raises(ValueError):
            generate_episode(seed=bad, bucket=TemplateBucket.CONFIRMATION)


def test_non_int_seed_and_bad_bucket_are_rejected() -> None:
    with pytest.raises(TypeError):
        generate_episode(
            seed=1.0,  # ty: ignore[invalid-argument-type]  # noqa
            bucket=TemplateBucket.CALIBRATION,
        )
    with pytest.raises(TypeError):
        generate_episode(
            seed=True,  # noqa
            bucket=TemplateBucket.CALIBRATION,
        )
    with pytest.raises(TypeError):
        generate_episode(
            seed=100_000,
            bucket="calibration",  # ty: ignore[invalid-argument-type]  # noqa
        )


def test_family_name_matches_wave0() -> None:
    assert FAMILY_NAME == "maintenance_fault"
    assert mfv2.FAMILY_NAME == "maintenance_fault"
