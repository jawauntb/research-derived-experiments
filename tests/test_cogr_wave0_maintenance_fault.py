"""Tests for the Wave 0 ``maintenance_fault`` procedural family.

These tests exercise the three invariants named by the Wave 0 build brief
for a family module:

1. **Determinism.** ``generate_episode(seed, bucket, holdout)`` is a pure
   function of its inputs — the same tuple produces a byte-identical
   :class:`EpisodeSpec`.
2. **Adversarial wrong prior (PREREGISTRATION.md §5).** The care anchors
   overweight the chronic alarm region and suppress the load-bearing
   early-observation region; the load-bearing target is off-context
   (present in ``candidate_nodes``, absent from ``context_nodes``).
3. **Holdout honored (PREREGISTRATION.md §6.2).** When a paraphrase
   family id is passed as ``holdout``, no episode is produced whose
   selected template belonged to that paraphrase family.

Two supporting invariants — the non-ceiling utility differential cap
(PREREGISTRATION.md §6) and the seed-range refusal (PREREGISTRATION.md
§10) — are also covered so the Wave 0 promotion contract's G0 / G4
gate receipts can point at a single test file.

These tests only read the policy-visible fields plus the sealed
``EpisodeSpec`` fields the evaluator itself is allowed to read; they do
not import any Wave 1 (confirmatory) code path.
"""

from __future__ import annotations


import pytest

from experiments.concern_gated_retrieval_e2.wave0.families import maintenance_fault
from experiments.concern_gated_retrieval_e2.wave0.families.maintenance_fault import (
    CALIBRATION_SEED_MAX,
    CALIBRATION_SEED_MIN,
    CONFIRMATION_SEED_MAX,
    CONFIRMATION_SEED_MIN,
    FAMILY_NAME,
    MAX_UTILITY_DIFF,
    PARAPHRASE_FAMILIES,
    TEMPLATES,
    W_ALARM_INIT,
    W_COMMIT_INIT,
    generate_episode,
)
from experiments.concern_gated_retrieval_e2.wave0.sealed_env import EpisodeSpec
from experiments.concern_gated_retrieval_e2.wave0.template_split import TemplateBucket


# ---------------------------------------------------------------------------
# Template registry shape
# ---------------------------------------------------------------------------


def test_at_least_thirty_templates_are_declared() -> None:
    # PREREGISTRATION.md §6.2 declares 16 calibration + 32 confirmatory
    # maintenance_fault templates; the Wave 0 build brief requires >= 30.
    assert len(TEMPLATES) >= 30
    cal = [t for t in TEMPLATES if t.bucket is TemplateBucket.CALIBRATION]
    conf = [t for t in TEMPLATES if t.bucket is TemplateBucket.CONFIRMATION]
    assert len(cal) == 16
    assert len(conf) == 32
    # All template ids are unique.
    assert len({t.template_id for t in TEMPLATES}) == len(TEMPLATES)
    # Every declared paraphrase family is used at least once.
    used = {t.paraphrase_family for t in TEMPLATES}
    assert used == set(PARAPHRASE_FAMILIES)


# ---------------------------------------------------------------------------
# (1) determinism
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("seed", [100_000, 100_042, 100_777, 100_999])
def test_generate_episode_is_deterministic_given_seed(seed: int) -> None:
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


def test_generate_episode_differs_across_seeds() -> None:
    a = generate_episode(seed=100_000, bucket=TemplateBucket.CALIBRATION)
    b = generate_episode(seed=100_001, bucket=TemplateBucket.CALIBRATION)
    assert a.episode_id != b.episode_id
    # The node namespace is seed-prefixed, so candidate sets are disjoint.
    assert set(a.candidate_nodes).isdisjoint(set(b.candidate_nodes))


# ---------------------------------------------------------------------------
# (2) adversarially misspecified wrong prior
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "seed",
    [100_000, 100_007, 100_123, 100_512, 100_999],
)
def test_wrong_prior_overweights_alarm_and_suppresses_commit(seed: int) -> None:
    episode = generate_episode(seed=seed, bucket=TemplateBucket.CALIBRATION)

    # The load-bearing target is off-context (candidate, not context)
    # and is the only element of the sealed answer key.
    (load_bearing,) = episode._answer_key
    assert load_bearing in episode.candidate_nodes
    assert load_bearing not in episode.context_nodes

    # Wrong prior invariants (PREREGISTRATION.md §5):
    #   (1) at least one chronic alarm region sits at ``W_ALARM_INIT``.
    alarm_weight = W_ALARM_INIT
    commit_weight = W_COMMIT_INIT
    alarms = [
        node
        for node, w in episode.care_anchors.items()
        if w == pytest.approx(alarm_weight)
        and episode.role.get(node) == "chronic_alarm_distractor"
    ]
    assert alarms, "wrong prior must inflate the chronic alarm region"

    #   (2) the load-bearing commitment region is suppressed below uniform.
    assert episode.care_anchors[load_bearing] == pytest.approx(commit_weight)

    #   (3) the prior is not a total inversion — at least one non-alarm,
    #       non-commit node sits at the uniform baseline (strictly
    #       between suppression and inflation).
    baseline_nodes = [
        node
        for node, w in episode.care_anchors.items()
        if commit_weight < w < alarm_weight
    ]
    assert baseline_nodes, (
        "wrong prior must leave at least one region at uniform baseline; "
        "otherwise a well-designed method has no surface to grip on"
    )


def test_non_ceiling_utility_differential_is_bounded() -> None:
    # PREREGISTRATION.md §6: the load-bearing target's expected reward
    # differential over the best distractor must not exceed 0.6, so no
    # reasonable two-sided method can start at ceiling on this family.
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


# ---------------------------------------------------------------------------
# (3) holdout honored
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("holdout", list(PARAPHRASE_FAMILIES))
def test_holdout_excludes_paraphrase_family(holdout: str) -> None:
    # Sweep a broad sample of calibration seeds; none may resolve to a
    # template whose paraphrase family is the held-out one.
    for seed in range(100_000, 100_100):
        episode = generate_episode(
            seed=seed,
            bucket=TemplateBucket.CALIBRATION,
            holdout=holdout,
        )
        # Recover the template id from the episode_id prefix.
        template_id = episode.episode_id.split("::", 1)[0]
        template = next(t for t in TEMPLATES if t.template_id == template_id)
        assert template.paraphrase_family != holdout
        assert template.bucket is TemplateBucket.CALIBRATION


def test_holdout_none_uses_full_pool() -> None:
    # With no holdout, a broad seed sweep must reach every paraphrase
    # family present in the calibration bucket.
    reached: set[str] = set()
    for seed in range(100_000, 100_200):
        episode = generate_episode(seed=seed, bucket=TemplateBucket.CALIBRATION)
        template_id = episode.episode_id.split("::", 1)[0]
        template = next(t for t in TEMPLATES if t.template_id == template_id)
        reached.add(template.paraphrase_family)
    assert reached == set(PARAPHRASE_FAMILIES)


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


# ---------------------------------------------------------------------------
# Supporting invariant: seed-range refusal (PREREGISTRATION.md §10)
# ---------------------------------------------------------------------------


def test_calibration_bucket_refuses_out_of_range_seed() -> None:
    for bad_seed in (
        CALIBRATION_SEED_MIN - 1,
        CALIBRATION_SEED_MAX + 1,
        200_000,
        0,
        -1,
    ):
        with pytest.raises(ValueError):
            generate_episode(seed=bad_seed, bucket=TemplateBucket.CALIBRATION)


def test_confirmation_bucket_refuses_out_of_range_seed() -> None:
    for bad_seed in (
        CONFIRMATION_SEED_MIN - 1,
        CONFIRMATION_SEED_MAX + 1,
        100_000,
        0,
    ):
        with pytest.raises(ValueError):
            generate_episode(seed=bad_seed, bucket=TemplateBucket.CONFIRMATION)


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


# ---------------------------------------------------------------------------
# Cross-check: the family constant matches the module import path
# ---------------------------------------------------------------------------


def test_family_name_matches_module() -> None:
    assert FAMILY_NAME == "maintenance_fault"
    assert maintenance_fault.FAMILY_NAME == "maintenance_fault"
