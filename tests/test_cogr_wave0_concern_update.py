"""Tests for the Wave 0 concern-update off-policy learner.

Four unit tests, each anchored to a Wave 0 preregistration or roadmap
invariant:

1. ``test_probe_propensities_log_correctly`` — the propensity written on
   every :class:`ProbeReceipt` matches the closed-form epsilon-greedy
   logging-policy probability, over exploratory and greedy picks alike
   (roadmap §"L2 recovery: logged propensities").
2. ``test_ips_reduces_bias_vs_naive_update`` — on a synthetic
   wrong-prior toy where the logging policy oversamples an alarm
   anchor, the IPS-updated prior corrects the alarm/commitment ratio
   further toward the ground truth than a naive (propensity-blind)
   update does (roadmap §"Fatal gates by claim: L2 recovery").
3. ``test_influence_bound_holds`` — a single source's aggregate
   contribution magnitude never exceeds ``max_source_influence`` after
   the poisoning guard runs, even when that source dominates the receipt
   batch (PREREGISTRATION.md §4.4).
4. ``test_deterministic_given_seed_and_receipts`` — for a fixed seed and
   fixed receipt / outcome batch, both :class:`LoggedProbePolicy.select`
   and :func:`update_concern` are byte-stable (Wave 0 calibration
   determinism gate).
"""

from __future__ import annotations

import math
import random
from typing import Sequence

import pytest

from experiments.concern_gated_retrieval_e2.wave0.concern_update import (
    DEFAULT_EPSILON,
    DEFAULT_SOURCE_ID,
    LoggedProbePolicy,
    ProbeReceipt,
    update_concern,
)
from experiments.concern_gated_retrieval_e2.wave0.sealed_env import (
    EpisodeContext,
    SealedOutcome,
)


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #


def _make_context(
    *,
    episode_id: str,
    candidates: tuple[str, ...],
    care_anchors: dict[str, float] | None = None,
) -> EpisodeContext:
    """Return a policy-visible :class:`EpisodeContext` for the toy tests."""
    return EpisodeContext(
        episode_id=episode_id,
        template_family_split="calibration",
        family="delayed_commitments",
        seed=100_000,
        context_nodes=("ctx_a",),
        care_anchors=care_anchors or {c: 0.2 for c in candidates},
        candidate_nodes=candidates,
        budget=1,
    )


def _greedy_policy_picking(candidate: str):
    """Return a nomination policy whose top pick is ``candidate``."""
    def _nomination(context: EpisodeContext) -> tuple[str, ...]:
        head = candidate
        tail = tuple(c for c in context.candidate_nodes if c != head)
        return (head,) + tail
    return _nomination


def _sealed_outcome(reward: float) -> SealedOutcome:
    return SealedOutcome(
        realized_reward=float(reward),
        constraint_preserved=False,
        misretrieval_cost=0.0,
        wall_actions=1,
        template_family_split="calibration",
    )


# --------------------------------------------------------------------------- #
# Test 1: propensities log correctly
# --------------------------------------------------------------------------- #


def test_probe_propensities_log_correctly() -> None:
    candidates = ("A", "B", "C", "D")
    context = _make_context(episode_id="ep-log", candidates=candidates)
    epsilon = 0.2
    n = len(candidates)

    # Greedy pick is always "A"; the wrapped policy is deterministic.
    policy = LoggedProbePolicy(
        _greedy_policy_picking("A"), epsilon=epsilon, source_id="trusted"
    )

    rng = random.Random(12345)

    greedy_propensity = (1.0 - epsilon) + epsilon / n
    explore_propensity = epsilon / n

    # Draw a large batch so both branches are exercised.
    counts = {c: 0 for c in candidates}
    n_greedy_picks = 0
    n_explore_picks = 0
    for _ in range(2000):
        selected, receipt = policy.select(context, rng)
        counts[selected] += 1
        # The propensity is the total probability the *logging policy*
        # assigns to the *action* — this is what IPS divides by. It is
        # NOT conditional on the branch that produced the pick.
        if selected == "A":
            assert receipt.selection_propensity == pytest.approx(
                greedy_propensity
            ), (
                "A is the greedy pick, so its logging-policy propensity "
                "is (1 - eps) + eps/n regardless of which branch fired"
            )
            if receipt.exploratory:
                n_explore_picks += 1
            else:
                n_greedy_picks += 1
        else:
            assert receipt.exploratory is True, (
                "non-greedy selections must come from exploration"
            )
            assert receipt.selection_propensity == pytest.approx(
                explore_propensity
            ), "non-greedy candidates get pure exploration propensity"
            n_explore_picks += 1

        assert receipt.source_id == "trusted"
        assert receipt.template_family_split == "calibration"
        assert receipt.episode_id == "ep-log"

    # Sanity: non-greedy picks fire at empirical rate ≈ epsilon * (n-1)/n.
    # For (epsilon, n) = (0.2, 4) that expected rate is 0.15; permit
    # binomial slack of ±0.03 on 2000 draws.
    total = sum(counts.values())
    non_greedy = counts["B"] + counts["C"] + counts["D"]
    expected_rate = epsilon * (n - 1) / n
    empirical_rate = non_greedy / total
    assert abs(empirical_rate - expected_rate) < 0.03, (
        f"empirical non-greedy rate {empirical_rate} deviates from "
        f"expected {expected_rate}"
    )
    assert n_explore_picks > 0 and n_greedy_picks > 0


# --------------------------------------------------------------------------- #
# Test 2: IPS reduces bias vs a naive update on a wrong-prior toy
# --------------------------------------------------------------------------- #


def _naive_update(
    prior: dict[str, float],
    receipts: Sequence[ProbeReceipt],
    outcomes: Sequence[SealedOutcome],
    *,
    eta: float,
    weight_clip: float,
) -> dict[str, float]:
    """A deliberately biased comparator: aggregates raw rewards.

    Does not divide by propensity. Uses the same multiplicative
    mirror-descent step as :func:`update_concern` so the two updates are
    directly comparable at fixed ``eta`` and ``weight_clip``.
    """
    n = len(receipts)
    per_anchor: dict[str, float] = {a: 0.0 for a in prior}
    for receipt, outcome in zip(receipts, outcomes):
        if receipt.candidate in per_anchor:
            per_anchor[receipt.candidate] += float(outcome.realized_reward) / n
    updated: dict[str, float] = {}
    for anchor, w in prior.items():
        v = per_anchor.get(anchor, 0.0)
        w_new = w * math.exp(eta * v)
        updated[anchor] = max(0.0, min(weight_clip, w_new))
    return updated


def test_ips_reduces_bias_vs_naive_update() -> None:
    """Wrong-prior toy: alarm (A) picked most of the time, commitment (B) rarely.

    Ground truth: choosing A yields negative reward (chronic alarm cost);
    choosing B yields positive reward (load-bearing commitment). A
    perfectly aligned learner should push B/A up substantially. A
    propensity-blind aggregator undercorrects because A dominates the
    sample.
    """
    prior = {"A": 1.0, "B": 0.05, "neutral": 0.20}
    # Wrong-prior logging: greedy always picks A.
    epsilon = 0.10
    n_candidates = 2
    p_A = (1.0 - epsilon) + epsilon / n_candidates
    p_B = epsilon / n_candidates
    r_A = -0.5
    r_B = +0.5

    # Simulate 1000 receipts using the true logging-policy propensities.
    # The exact counts are the expectations under p_A / p_B; keeping
    # them exact removes stochastic noise from the assertion.
    n_total = 1000
    n_A = int(round(p_A * n_total))
    n_B = n_total - n_A
    receipts: list[ProbeReceipt] = []
    outcomes: list[SealedOutcome] = []
    for i in range(n_A):
        receipts.append(
            ProbeReceipt(
                episode_id=f"ep-{i:04d}",
                candidate="A",
                selection_propensity=p_A,
                source_id="trusted",
                template_family_split="calibration",
                exploratory=False,
            )
        )
        outcomes.append(_sealed_outcome(r_A))
    for i in range(n_B):
        receipts.append(
            ProbeReceipt(
                episode_id=f"ep-{n_A + i:04d}",
                candidate="B",
                selection_propensity=p_B,
                source_id="trusted",
                template_family_split="calibration",
                exploratory=True,
            )
        )
        outcomes.append(_sealed_outcome(r_B))

    eta = 0.10
    weight_clip = 8.0
    # Relax the poisoning guard so the toy exercises the estimator
    # rather than the guard; a dedicated test covers the guard.
    ips_updated = update_concern(
        prior,
        receipts,
        outcomes,
        estimator="ips",
        eta=eta,
        max_source_influence=100.0,
        weight_clip=weight_clip,
    )
    naive_updated = _naive_update(
        prior,
        receipts,
        outcomes,
        eta=eta,
        weight_clip=weight_clip,
    )

    def _ratio(w: dict[str, float]) -> float:
        return w["B"] / w["A"]

    prior_ratio = _ratio(prior)
    ips_ratio = _ratio(ips_updated)
    naive_ratio = _ratio(naive_updated)

    # IPS must strictly improve B/A relative to the wrong prior.
    assert ips_ratio > prior_ratio, (
        f"IPS should raise B/A from {prior_ratio} but produced {ips_ratio}"
    )
    # And do so more than the propensity-blind aggregator, because the
    # naive aggregator downweights the (rare, informative) B receipts by
    # their sampling frequency.
    assert ips_ratio > naive_ratio, (
        "IPS should push B/A further than the propensity-blind naive "
        f"aggregator (ips={ips_ratio}, naive={naive_ratio})"
    )
    # And the neutral anchor is untouched (no receipts probed it).
    assert naive_updated["neutral"] == pytest.approx(prior["neutral"])
    assert ips_updated["neutral"] == pytest.approx(prior["neutral"])


# --------------------------------------------------------------------------- #
# Test 3: poisoning-guard single-source influence bound
# --------------------------------------------------------------------------- #


def test_influence_bound_holds() -> None:
    """A single source cannot dominate the aggregated update.

    Constructs a batch where one ``untrusted`` source produces very
    high-magnitude IPS contributions (small propensity, large reward),
    then verifies that the multiplicative update on any anchor stays
    inside ``exp(eta * max_source_influence)``.
    """
    prior = {"A": 1.0, "B": 1.0, "C": 1.0}

    # A tiny propensity blows the raw IPS estimate up to r / p = 20.
    poisoned = [
        ProbeReceipt(
            episode_id=f"poisoned-{i}",
            candidate=anchor,
            selection_propensity=0.05,
            source_id="untrusted_feed",
            template_family_split="calibration",
            exploratory=True,
        )
        for i, anchor in enumerate(("A", "B", "C") * 3)
    ]
    poisoned_outcomes = [_sealed_outcome(1.0)] * len(poisoned)

    # A single benign trusted receipt.
    trusted = [
        ProbeReceipt(
            episode_id="trusted-0",
            candidate="A",
            selection_propensity=0.9,
            source_id="trusted",
            template_family_split="calibration",
            exploratory=False,
        )
    ]
    trusted_outcomes = [_sealed_outcome(0.1)]

    receipts = poisoned + trusted
    outcomes = poisoned_outcomes + trusted_outcomes

    eta = 0.5
    msi = 0.25  # deliberately tight
    updated = update_concern(
        prior,
        receipts,
        outcomes,
        estimator="ips",
        eta=eta,
        max_source_influence=msi,
        weight_clip=1e6,
    )

    # Under the poisoning guard, no anchor can move by more than a
    # factor of exp(eta * msi) relative to its prior.
    max_factor = math.exp(eta * msi)
    for anchor, w_prior in prior.items():
        w_new = updated[anchor]
        ratio = w_new / w_prior
        assert 1.0 / max_factor - 1e-9 <= ratio <= max_factor + 1e-9, (
            f"anchor {anchor} moved by ratio {ratio} outside "
            f"[{1.0 / max_factor}, {max_factor}]"
        )
    # Sanity: without the guard the update would blow past this bound,
    # so the assertion is not vacuous. Re-run with a massive msi and
    # confirm at least one anchor's ratio exceeds max_factor.
    unguarded = update_concern(
        prior,
        receipts,
        outcomes,
        estimator="ips",
        eta=eta,
        max_source_influence=1e6,
        weight_clip=1e12,
    )
    assert any(
        unguarded[a] / prior[a] > max_factor + 1e-3 for a in prior
    ), "the toy must exceed the tight bound when the guard is disabled"


# --------------------------------------------------------------------------- #
# Test 4: determinism given seed + receipts
# --------------------------------------------------------------------------- #


def test_deterministic_given_seed_and_receipts() -> None:
    """Two independent runs with matched seeds must produce identical outputs."""
    candidates = ("A", "B", "C", "D")

    def _run(seed: int) -> tuple[list[str], list[ProbeReceipt], dict[str, float]]:
        context = _make_context(episode_id="ep-det", candidates=candidates)
        policy = LoggedProbePolicy(
            _greedy_policy_picking("A"),
            epsilon=DEFAULT_EPSILON,
            source_id=DEFAULT_SOURCE_ID,
        )
        rng = random.Random(seed)
        picks: list[str] = []
        receipts: list[ProbeReceipt] = []
        for _ in range(64):
            selected, receipt = policy.select(context, rng)
            picks.append(selected)
            receipts.append(receipt)
        # Assign a deterministic reward per candidate.
        rewards = {"A": -0.2, "B": +0.5, "C": +0.1, "D": -0.1}
        outcomes = [_sealed_outcome(rewards[r.candidate]) for r in receipts]
        prior = {"A": 1.0, "B": 0.05, "C": 0.2, "D": 0.2}
        updated = update_concern(
            prior,
            receipts,
            outcomes,
            estimator="dr",
            eta=0.05,
            max_source_influence=1.0,
            weight_clip=4.0,
        )
        return picks, receipts, updated

    picks_1, receipts_1, updated_1 = _run(seed=98765)
    picks_2, receipts_2, updated_2 = _run(seed=98765)

    assert picks_1 == picks_2, "selection sequence must be deterministic"
    assert receipts_1 == receipts_2, "receipts must be byte-identical"
    for anchor, w in updated_1.items():
        assert updated_2[anchor] == pytest.approx(w, rel=0, abs=0), (
            f"anchor {anchor} update drifted between seeded runs"
        )

    # A different seed must actually produce a different trajectory,
    # otherwise the determinism assertion above is trivially satisfied.
    picks_alt, _, _ = _run(seed=13579)
    assert picks_alt != picks_1, (
        "determinism test is vacuous if all seeds produce identical picks"
    )
