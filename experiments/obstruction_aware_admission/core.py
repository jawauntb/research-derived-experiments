#!/usr/bin/env python3
"""Exact finite control for obstruction-aware experiment admission.

The controller treats experiment choice as a target-identification decision
tree. It returns an exact worst-case continuation cost, a next experiment on an
optimal branch, or a typed reason why no experiment should be admitted.
"""

from __future__ import annotations

import itertools
from collections.abc import Hashable, Iterable
from dataclasses import dataclass
from fractions import Fraction
from typing import Literal, TypeAlias

from experiments.information_limited_discovery.core import (
    DiscoveryProblem,
    Observation,
    ScopedObstructionCertificate,
    Transcript,
    candidate_worlds,
    determined_target,
    find_obstruction,
    target_is_determined,
)


AdmissionPolicy: TypeAlias = Literal[
    "exact",
    "greedy_target_pairs",
    "greedy_all_pairs",
    "fixed_order",
]
AdmissionStatus: TypeAlias = Literal[
    "recovered",
    "terminal_obstruction",
    "budget_infeasible",
    "admit",
]
EpisodeStatus: TypeAlias = Literal[
    "recovered",
    "terminal_obstruction",
    "budget_exhausted",
]
FiniteCost: TypeAlias = int | None


@dataclass(frozen=True)
class AdmissionDecision:
    """One fail-closed admission decision at a declared history."""

    problem_id: str
    status: AdmissionStatus
    experiment: str | None
    recovered_target: Hashable | None
    required_worst_case_cost: FiniteCost
    remaining_budget: int
    candidates: tuple[str, ...]
    certificate: ScopedObstructionCertificate | None

    def to_dict(self) -> dict[str, object]:
        return {
            "problem_id": self.problem_id,
            "status": self.status,
            "experiment": self.experiment,
            "recovered_target": self.recovered_target,
            "required_worst_case_cost": self.required_worst_case_cost,
            "remaining_budget": self.remaining_budget,
            "candidates": list(self.candidates),
            "certificate": (
                None if self.certificate is None else self.certificate.to_dict()
            ),
        }


@dataclass(frozen=True)
class PolicyEpisode:
    """One hidden-world trajectory under a registered admission policy."""

    problem_id: str
    policy: AdmissionPolicy
    actual_realization: str
    actual_target: Hashable
    outcome: EpisodeStatus
    predicted_target: Hashable | None
    observations: Transcript
    final_candidates: tuple[str, ...]
    total_cost: int
    certificate: ScopedObstructionCertificate | None

    def to_dict(self) -> dict[str, object]:
        return {
            "problem_id": self.problem_id,
            "policy": self.policy,
            "actual_realization": self.actual_realization,
            "actual_target": self.actual_target,
            "outcome": self.outcome,
            "predicted_target": self.predicted_target,
            "observations": [
                {"experiment": experiment, "outcome": outcome}
                for experiment, outcome in self.observations
            ],
            "final_candidates": list(self.final_candidates),
            "total_cost": self.total_cost,
            "certificate": (
                None if self.certificate is None else self.certificate.to_dict()
            ),
        }


def _target_map(problem: DiscoveryProblem) -> dict[str, Hashable]:
    return dict(
        zip(
            problem.system.realizations,
            problem.target.values,
            strict=True,
        )
    )


def _outcome(
    problem: DiscoveryProblem,
    realization: str,
    experiment: str,
) -> Hashable:
    return problem.system.transcript(realization, (experiment,))[0]


def remaining_experiments(
    problem: DiscoveryProblem,
    observations: Iterable[Observation],
) -> tuple[str, ...]:
    """Return permitted experiments not already present in the transcript."""

    performed = {experiment for experiment, _ in observations}
    return tuple(
        experiment
        for experiment in problem.allowed_family
        if experiment not in performed
    )


def _branches(
    problem: DiscoveryProblem,
    candidates: tuple[str, ...],
    experiment: str,
) -> tuple[tuple[str, ...], ...]:
    buckets: dict[Hashable, list[str]] = {}
    for realization in candidates:
        outcome = _outcome(problem, realization, experiment)
        buckets.setdefault(outcome, []).append(realization)
    return tuple(tuple(bucket) for bucket in buckets.values())


def _informative_experiments(
    problem: DiscoveryProblem,
    candidates: tuple[str, ...],
    remaining: tuple[str, ...],
) -> tuple[str, ...]:
    return tuple(
        experiment
        for experiment in remaining
        if len(_branches(problem, candidates, experiment)) > 1
    )


def _optimal_cost(
    problem: DiscoveryProblem,
    candidates: tuple[str, ...],
    remaining: tuple[str, ...],
    memo: dict[tuple[tuple[str, ...], tuple[str, ...]], FiniteCost],
) -> FiniteCost:
    key = candidates, remaining
    if key in memo:
        return memo[key]
    if target_is_determined(problem, candidates):
        memo[key] = 0
        return 0

    best: FiniteCost = None
    for experiment in _informative_experiments(
        problem,
        candidates,
        remaining,
    ):
        after = tuple(item for item in remaining if item != experiment)
        branch_costs: list[int] = []
        feasible = True
        for branch in _branches(problem, candidates, experiment):
            continuation = _optimal_cost(problem, branch, after, memo)
            if continuation is None:
                feasible = False
                break
            branch_costs.append(continuation)
        if not feasible:
            continue
        candidate_cost = problem.experiment_cost(experiment) + max(branch_costs)
        if best is None or candidate_cost < best:
            best = candidate_cost
    memo[key] = best
    return best


def optimal_worst_case_cost(
    problem: DiscoveryProblem,
    candidates: tuple[str, ...] | None = None,
    remaining: tuple[str, ...] | None = None,
) -> FiniteCost:
    """Return the exact minimum worst-case cost, or ``None`` if impossible."""

    active_candidates = (
        problem.system.realizations if candidates is None else candidates
    )
    active_remaining = problem.allowed_family if remaining is None else remaining
    if not active_candidates:
        raise ValueError("candidate set must be nonempty")
    if not set(active_candidates).issubset(problem.system.realizations):
        raise ValueError("candidate set contains an unknown realization")
    if not set(active_remaining).issubset(problem.allowed_family):
        raise ValueError("remaining experiments must be permitted")
    return _optimal_cost(problem, active_candidates, active_remaining, {})


def independent_optimal_cost(
    problem: DiscoveryProblem,
    candidates: tuple[str, ...] | None = None,
    remaining: tuple[str, ...] | None = None,
) -> FiniteCost:
    """Independently enumerate decision trees without memoization."""

    active_candidates = (
        problem.system.realizations if candidates is None else candidates
    )
    active_remaining = problem.allowed_family if remaining is None else remaining
    if target_is_determined(problem, active_candidates):
        return 0

    costs: list[int] = []
    for experiment in _informative_experiments(
        problem,
        active_candidates,
        active_remaining,
    ):
        after = tuple(item for item in active_remaining if item != experiment)
        branch_costs: list[int] = []
        for branch in _branches(problem, active_candidates, experiment):
            continuation = independent_optimal_cost(problem, branch, after)
            if continuation is None:
                break
            branch_costs.append(continuation)
        else:
            costs.append(
                problem.experiment_cost(experiment) + max(branch_costs)
            )
    return min(costs) if costs else None


def _separated_pair_count(
    problem: DiscoveryProblem,
    candidates: tuple[str, ...],
    experiment: str,
    *,
    target_only: bool,
) -> int:
    targets = _target_map(problem)
    return sum(
        1
        for left, right in itertools.combinations(candidates, 2)
        if (not target_only or targets[left] != targets[right])
        and _outcome(problem, left, experiment)
        != _outcome(problem, right, experiment)
    )


def choose_policy_experiment(
    problem: DiscoveryProblem,
    candidates: tuple[str, ...],
    remaining: tuple[str, ...],
    policy: AdmissionPolicy,
) -> str | None:
    """Choose a next informative experiment under a registered policy."""

    informative = _informative_experiments(problem, candidates, remaining)
    if not informative:
        return None
    if policy == "fixed_order":
        return informative[0]
    if policy == "exact":
        optimum = optimal_worst_case_cost(problem, candidates, remaining)
        if optimum is None:
            return None
        for experiment in informative:
            after = tuple(item for item in remaining if item != experiment)
            branch_costs = [
                optimal_worst_case_cost(problem, branch, after)
                for branch in _branches(problem, candidates, experiment)
            ]
            if any(cost is None for cost in branch_costs):
                continue
            finite_branch_costs = [cost for cost in branch_costs if cost is not None]
            cost = problem.experiment_cost(experiment) + max(finite_branch_costs)
            if cost == optimum:
                return experiment
        raise AssertionError("finite optimum has no realizing first experiment")
    if policy not in ("greedy_target_pairs", "greedy_all_pairs"):
        raise ValueError(f"unknown admission policy: {policy}")
    target_only = policy == "greedy_target_pairs"

    def score(experiment: str) -> tuple[Fraction, int, int]:
        separated = _separated_pair_count(
            problem,
            candidates,
            experiment,
            target_only=target_only,
        )
        index = problem.system.experiments.index(experiment)
        return (
            Fraction(separated, problem.experiment_cost(experiment)),
            separated,
            -index,
        )

    return max(informative, key=score)


def _policy_cost(
    problem: DiscoveryProblem,
    candidates: tuple[str, ...],
    remaining: tuple[str, ...],
    policy: AdmissionPolicy,
    memo: dict[tuple[tuple[str, ...], tuple[str, ...]], FiniteCost],
) -> FiniteCost:
    key = candidates, remaining
    if key in memo:
        return memo[key]
    if target_is_determined(problem, candidates):
        memo[key] = 0
        return 0
    experiment = choose_policy_experiment(
        problem,
        candidates,
        remaining,
        policy,
    )
    if experiment is None:
        memo[key] = None
        return None
    after = tuple(item for item in remaining if item != experiment)
    branch_costs: list[int] = []
    for branch in _branches(problem, candidates, experiment):
        continuation = _policy_cost(problem, branch, after, policy, memo)
        if continuation is None:
            memo[key] = None
            return None
        branch_costs.append(continuation)
    result = problem.experiment_cost(experiment) + max(branch_costs)
    memo[key] = result
    return result


def policy_worst_case_cost(
    problem: DiscoveryProblem,
    policy: AdmissionPolicy,
    candidates: tuple[str, ...] | None = None,
    remaining: tuple[str, ...] | None = None,
) -> FiniteCost:
    """Return one registered policy's exact worst-case identification cost."""

    active_candidates = (
        problem.system.realizations if candidates is None else candidates
    )
    active_remaining = problem.allowed_family if remaining is None else remaining
    if policy == "exact":
        return optimal_worst_case_cost(
            problem,
            active_candidates,
            active_remaining,
        )
    return _policy_cost(
        problem,
        active_candidates,
        active_remaining,
        policy,
        {},
    )


def decide_admission(
    problem: DiscoveryProblem,
    observations: Iterable[Observation] = (),
    *,
    spent_cost: int = 0,
) -> AdmissionDecision:
    """Return the exact next action or a typed stopping reason."""

    normalized = tuple(observations)
    if spent_cost < 0 or spent_cost > problem.budget:
        raise ValueError("spent_cost must lie within the declared budget")
    observed_cost = sum(
        problem.experiment_cost(experiment)
        for experiment, _ in normalized
    )
    if spent_cost != observed_cost:
        raise ValueError("spent_cost must equal the cost of the transcript")
    candidates = candidate_worlds(problem, normalized)
    if not candidates:
        raise ValueError("observations are inconsistent with every world")
    remaining_budget = problem.budget - spent_cost
    if target_is_determined(problem, candidates):
        return AdmissionDecision(
            problem_id=problem.problem_id,
            status="recovered",
            experiment=None,
            recovered_target=determined_target(problem, candidates),
            required_worst_case_cost=0,
            remaining_budget=remaining_budget,
            candidates=candidates,
            certificate=None,
        )

    remaining = remaining_experiments(problem, normalized)
    required = optimal_worst_case_cost(problem, candidates, remaining)
    if required is None:
        certificate = find_obstruction(
            problem,
            normalized,
            require_terminal=True,
        )
        if certificate is None:
            raise AssertionError("infinite exact cost lacks a terminal obstruction")
        return AdmissionDecision(
            problem_id=problem.problem_id,
            status="terminal_obstruction",
            experiment=None,
            recovered_target=None,
            required_worst_case_cost=None,
            remaining_budget=remaining_budget,
            candidates=candidates,
            certificate=certificate,
        )
    if required > remaining_budget:
        local = find_obstruction(problem, normalized)
        if local is None:
            raise AssertionError("ambiguous target lacks a local obstruction")
        return AdmissionDecision(
            problem_id=problem.problem_id,
            status="budget_infeasible",
            experiment=None,
            recovered_target=None,
            required_worst_case_cost=required,
            remaining_budget=remaining_budget,
            candidates=candidates,
            certificate=local,
        )
    experiment = choose_policy_experiment(
        problem,
        candidates,
        remaining,
        "exact",
    )
    if experiment is None:
        raise AssertionError("finite positive cost lacks an admitted experiment")
    return AdmissionDecision(
        problem_id=problem.problem_id,
        status="admit",
        experiment=experiment,
        recovered_target=None,
        required_worst_case_cost=required,
        remaining_budget=remaining_budget,
        candidates=candidates,
        certificate=None,
    )


def run_policy_episode(
    problem: DiscoveryProblem,
    actual_realization: str,
    policy: AdmissionPolicy = "exact",
) -> PolicyEpisode:
    """Run one hidden world without exposing it to the admission policy."""

    if actual_realization not in problem.system.realizations:
        raise ValueError(f"unknown actual realization: {actual_realization}")
    targets = _target_map(problem)
    observations: Transcript = ()
    total_cost = 0
    while True:
        candidates = candidate_worlds(problem, observations)
        if target_is_determined(problem, candidates):
            predicted = determined_target(problem, candidates)
            return PolicyEpisode(
                problem_id=problem.problem_id,
                policy=policy,
                actual_realization=actual_realization,
                actual_target=targets[actual_realization],
                outcome="recovered",
                predicted_target=predicted,
                observations=observations,
                final_candidates=candidates,
                total_cost=total_cost,
                certificate=None,
            )

        terminal = find_obstruction(
            problem,
            observations,
            require_terminal=True,
        )
        if terminal is not None:
            return PolicyEpisode(
                problem_id=problem.problem_id,
                policy=policy,
                actual_realization=actual_realization,
                actual_target=targets[actual_realization],
                outcome="terminal_obstruction",
                predicted_target=None,
                observations=observations,
                final_candidates=candidates,
                total_cost=total_cost,
                certificate=terminal,
            )

        remaining = remaining_experiments(problem, observations)
        if policy == "exact":
            decision = decide_admission(
                problem,
                observations,
                spent_cost=total_cost,
            )
            if decision.status == "budget_infeasible":
                return PolicyEpisode(
                    problem_id=problem.problem_id,
                    policy=policy,
                    actual_realization=actual_realization,
                    actual_target=targets[actual_realization],
                    outcome="budget_exhausted",
                    predicted_target=None,
                    observations=observations,
                    final_candidates=candidates,
                    total_cost=total_cost,
                    certificate=decision.certificate,
                )
            if decision.status != "admit" or decision.experiment is None:
                raise AssertionError("exact episode received an invalid decision")
            exact_experiment = decision.experiment
        else:
            exact_experiment = None
        affordable = tuple(
            experiment
            for experiment in remaining
            if problem.experiment_cost(experiment) + total_cost <= problem.budget
        )
        if not affordable:
            local = find_obstruction(problem, observations)
            if local is None:
                raise AssertionError("ambiguous target lacks a local obstruction")
            return PolicyEpisode(
                problem_id=problem.problem_id,
                policy=policy,
                actual_realization=actual_realization,
                actual_target=targets[actual_realization],
                outcome="budget_exhausted",
                predicted_target=None,
                observations=observations,
                final_candidates=candidates,
                total_cost=total_cost,
                certificate=local,
            )

        experiment = (
            exact_experiment
            if exact_experiment is not None
            else choose_policy_experiment(
                problem,
                candidates,
                affordable,
                policy,
            )
        )
        if experiment is None:
            local = find_obstruction(problem, observations)
            if local is None:
                raise AssertionError("ambiguous target lacks a local obstruction")
            return PolicyEpisode(
                problem_id=problem.problem_id,
                policy=policy,
                actual_realization=actual_realization,
                actual_target=targets[actual_realization],
                outcome="budget_exhausted",
                predicted_target=None,
                observations=observations,
                final_candidates=candidates,
                total_cost=total_cost,
                certificate=local,
            )
        observed = _outcome(problem, actual_realization, experiment)
        observations = (*observations, (experiment, observed))
        total_cost += problem.experiment_cost(experiment)
