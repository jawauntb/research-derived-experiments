"""MX1 Part A — the within-episode verify->repair loop.

MIDAS repairs *within one problem*: attempt, verify, and on a reasoning fault
re-attempt with the failure fed back, up to ``max_reasoning_attempts``. Its
``difficulty_signal`` is per-trajectory. The faithful port is therefore a
within-episode loop, which needs no persistent cross-episode memory.

Every policy here spends an identical budget: ``MAX_ATTEMPTS`` attempts of
``k`` picks each, and no attempt re-picks a candidate an earlier attempt
already tried. The policies differ only in how they choose attempt *n+1*
after attempt *n* fails:

``concern_sequential``
    Abandons both failed picks and walks down the concern ranking.
``repair_guided``
    **Retains one failed pick and re-pairs it** with the best untried
    candidate, hypothesising that a pick scoring about zero *alone* may be one
    half of a super-additive pair rather than worthless. Care-independent: the
    decision is driven by observed task failure, never by concern weights.
``random_sequential``
    Walks down a seeded random permutation. Control.

The policy observes only :class:`AttemptFeedback` — how many of its picks were
load-bearing, and the fault kind. It never learns *which* pick hit, and never
sees roles, utilities, or the answer key.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Final, Sequence

from experiments.concern_gated_retrieval_e2.wave0.baselines import multiplicative_ppr
from experiments.concern_gated_retrieval_e2.wave0.sealed_env import (
    EpisodeContext,
    EpisodeSpec,
)
from experiments.concern_gated_retrieval_e2.wave1b.sealed_env_ext import (
    compute_set_delta,
)

from experiments.concern_gated_retrieval_e2.mx1_repair_prior.verifier_split import (
    FaultKind,
)


__all__ = [
    "MAX_ATTEMPTS",
    "SUCCESS_DELTA_THRESHOLD",
    "POLICIES",
    "AttemptFeedback",
    "EpisodeRun",
    "run_episode",
]


#: Frozen in PREREGISTRATION.md section 5.
MAX_ATTEMPTS: Final[int] = 3
SUCCESS_DELTA_THRESHOLD: Final[float] = 0.0

POLICIES: Final[tuple[str, ...]] = (
    "concern_sequential",
    "repair_guided",
    "random_sequential",
)


@dataclass(frozen=True)
class AttemptFeedback:
    """All a policy learns from one attempt.

    ``hit_count`` is standard bandit-style outcome feedback (how many of the
    ``k`` picks were load-bearing), not the identity of the hit. MIDAS's
    repair prompt receives strictly more than this -- it is told *which* step
    failed -- so this is a conservative port.
    """

    attempt_index: int
    picks: tuple[str, ...]
    hit_count: int
    fault_kind: FaultKind
    delta_task: float


@dataclass(frozen=True)
class EpisodeRun:
    """One policy's full trajectory on one episode."""

    policy: str
    seed: int
    attempts: tuple[AttemptFeedback, ...]
    attempts_to_success: int
    best_delta: float
    succeeded: bool


def _concern_ranking(context: EpisodeContext) -> tuple[str, ...]:
    """Full candidate ranking under the (Wave 1b-falsified) care mechanism."""
    budget = len(context.candidate_nodes)
    ranked = multiplicative_ppr(context, budget)
    # multiplicative_ppr returns at most ``budget`` picks; backfill any
    # candidate it omitted so every policy can always spend its full budget.
    remainder = [c for c in context.candidate_nodes if c not in set(ranked)]
    return tuple(ranked) + tuple(remainder)


def _random_ranking(context: EpisodeContext, seed: int) -> tuple[str, ...]:
    order = list(context.candidate_nodes)
    random.Random(seed).shuffle(order)
    return tuple(order)


def _take(ranking: Sequence[str], tried: set[str], k: int) -> tuple[str, ...]:
    """Top ``k`` of ``ranking`` skipping anything already tried."""
    out: list[str] = []
    for node in ranking:
        if node in tried:
            continue
        out.append(node)
        if len(out) == k:
            break
    return tuple(out)


def _next_picks(
    policy: str,
    *,
    ranking: Sequence[str],
    tried: set[str],
    k: int,
    last: AttemptFeedback | None,
) -> tuple[str, ...]:
    """Choose the next attempt's picks for ``policy``."""
    if last is None or policy != "repair_guided":
        return _take(ranking, tried, k)

    # repair_guided: a VERIFIER_FAULT carries no evidence about those picks,
    # so do not treat them as refuted -- retry the same region.
    if last.fault_kind is FaultKind.VERIFIER_FAULT:
        return last.picks

    # REASONING_FAULT with no hit: the picks were not load-bearing *alone*.
    # Retain one and re-pair it, in case it is half of a super-additive pair.
    if last.hit_count == 0 and last.picks:
        retained = last.picks[0]
        partners = _take(ranking, tried, k - 1)
        if partners:
            return (retained,) + partners
    return _take(ranking, tried, k)


def run_episode(episode: EpisodeSpec, context: EpisodeContext, policy: str) -> EpisodeRun:
    """Run one policy's verify->repair trajectory on one episode."""
    k = max(1, int(episode.budget))
    if policy == "random_sequential":
        ranking = _random_ranking(context, episode.seed)
    else:
        ranking = _concern_ranking(context)

    answer_key = set(episode._answer_key)  # EVALUATOR-side, for hit_count only.

    tried: set[str] = set()
    attempts: list[AttemptFeedback] = []
    best_delta = float("-inf")
    attempts_to_success = MAX_ATTEMPTS + 1
    last: AttemptFeedback | None = None

    for index in range(MAX_ATTEMPTS):
        picks = _next_picks(policy, ranking=ranking, tried=tried, k=k, last=last)
        if not picks:
            break
        outcome = compute_set_delta(episode, picks)
        delta = float(outcome.delta_task)
        best_delta = max(best_delta, delta)
        feedback = AttemptFeedback(
            attempt_index=index,
            picks=tuple(picks),
            hit_count=sum(1 for p in picks if p in answer_key),
            fault_kind=FaultKind.REASONING_FAULT,
            delta_task=delta,
        )
        attempts.append(feedback)
        tried.update(picks)
        last = feedback
        if delta > SUCCESS_DELTA_THRESHOLD:
            attempts_to_success = index + 1
            break

    return EpisodeRun(
        policy=policy,
        seed=int(episode.seed),
        attempts=tuple(attempts),
        attempts_to_success=attempts_to_success,
        best_delta=best_delta if attempts else 0.0,
        succeeded=attempts_to_success <= MAX_ATTEMPTS,
    )
