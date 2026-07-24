"""Regression tests for the MX1 de-risk probe.

MX1 is a single-shot GO/NO-GO probe, so these tests pin the things that would
silently invalidate its verdict rather than the verdict itself:

1. the verifier-fault split declines exactly on planted interactions and never
   on cleanly-scorable singletons (Part B's two GO conditions);
2. the marginal verifier really is wrong on a super-additive pair -- if it were
   not, Part B would be measuring nothing;
3. every policy spends an identical attempt budget and never re-picks a
   candidate an earlier attempt already tried (Part A's matched-budget claim);
4. the bootstrap CI helper is deterministic under its frozen seed.
"""

from __future__ import annotations

import pytest

from experiments.concern_gated_retrieval_e2.wave0.sealed_env import SealedEnvironment
from experiments.concern_gated_retrieval_e2.wave0.template_split import TemplateBucket
from experiments.concern_gated_retrieval_e2.wave1b.families import (
    delayed_commitments_v2 as family,
)
from experiments.concern_gated_retrieval_e2.wave1b.sealed_env_ext import (
    compute_set_delta,
)

from experiments.concern_gated_retrieval_e2.mx1_repair_prior.repair_loop import (
    MAX_ATTEMPTS,
    POLICIES,
    run_episode,
)
from experiments.concern_gated_retrieval_e2.mx1_repair_prior.run_mx1 import (
    bootstrap_mean_diff_ci,
)
from experiments.concern_gated_retrieval_e2.mx1_repair_prior.verifier_split import (
    FaultKind,
    marginal_verifier,
    planted_interaction_members,
    split_verifier,
)


CALIBRATION_SEEDS = range(100_000, 100_060)


def _episode(seed: int):
    return family.generate_episode(seed=seed, bucket=TemplateBucket.CALIBRATION)


def _first_complementary_episode():
    for seed in CALIBRATION_SEEDS:
        episode = _episode(seed)
        manifest = family.bundle_manifest(episode)
        if getattr(manifest, "complementary_pair", None):
            return episode, manifest
    pytest.skip("no complementary pair in the sampled calibration seeds")


def test_marginal_verifier_is_wrong_on_a_super_additive_pair() -> None:
    """Part B measures nothing unless the marginal model really does fail."""
    episode, manifest = _first_complementary_episode()
    pair = manifest.complementary_pair
    assert pair is not None
    a, b = pair

    joint = compute_set_delta(episode, (a, b)).delta_task
    marginal = marginal_verifier(episode, (a, b)).value

    assert joint > 0.0, "planted complementary pair should be jointly useful"
    assert marginal is not None
    assert marginal < joint, (
        "the marginal verifier must undervalue a super-additive pair; "
        f"marginal={marginal!r} joint={joint!r}"
    )


def test_split_verifier_declines_on_planted_interactions() -> None:
    episode, manifest = _first_complementary_episode()
    groups = planted_interaction_members(manifest)

    out = split_verifier(episode, manifest.complementary_pair, groups)

    assert out.fault_kind is FaultKind.VERIFIER_FAULT
    assert out.value is None, "a declined verdict must carry no value, not a zero"


def test_split_verifier_never_false_faults_on_singletons() -> None:
    """Part B GO condition 2: precision 1.0 on cleanly-scorable singletons."""
    checked = 0
    for seed in CALIBRATION_SEEDS:
        episode = _episode(seed)
        groups = planted_interaction_members(family.bundle_manifest(episode))
        for node in episode.candidate_nodes:
            checked += 1
            out = split_verifier(episode, [node], groups)
            assert out.fault_kind is FaultKind.REASONING_FAULT, (
                f"singleton {node!r} wrongly raised VERIFIER_FAULT"
            )
    assert checked > 0


@pytest.mark.parametrize("policy", POLICIES)
def test_policies_share_a_matched_budget_and_never_repick(policy: str) -> None:
    """Part A's matched-budget claim, enforced rather than asserted post hoc."""
    for seed in (100_000, 100_017, 100_042):
        episode = _episode(seed)
        context = SealedEnvironment(episode).observe()
        run = run_episode(episode, context, policy)

        assert len(run.attempts) <= MAX_ATTEMPTS
        assert 1 <= run.attempts_to_success <= MAX_ATTEMPTS + 1

        # A successful run stops early; an unsuccessful one spends every attempt.
        if not run.succeeded:
            assert len(run.attempts) == MAX_ATTEMPTS

        # No attempt may introduce a candidate a previous attempt already tried,
        # except repair_guided's deliberately retained pick.
        seen: set[str] = set()
        for attempt in run.attempts:
            fresh = [p for p in attempt.picks if p not in seen]
            retained = [p for p in attempt.picks if p in seen]
            if policy == "repair_guided":
                assert len(retained) <= 1, "at most one pick may be retained"
            else:
                assert not retained, f"{policy} re-picked {retained!r}"
            assert fresh or retained
            seen.update(attempt.picks)


def test_bootstrap_ci_is_deterministic_and_ordered() -> None:
    left = [3.0, 2.0, 3.0, 1.0, 2.0, 3.0]
    right = [2.0, 2.0, 1.0, 1.0, 3.0, 2.0]

    first = bootstrap_mean_diff_ci(left, right)
    second = bootstrap_mean_diff_ci(left, right)

    assert first == second, "frozen seed must make the CI reproducible"
    assert first[0] <= first[1]
