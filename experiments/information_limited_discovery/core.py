#!/usr/bin/env python3
"""Exact finite mechanics for obstruction-first discovery episodes."""

from __future__ import annotations

import itertools
from collections.abc import Hashable, Iterable
from dataclasses import dataclass
from fractions import Fraction
from typing import Literal, TypeAlias

from experiments.relative_identifiability.core import (
    FactorizationCertificate,
    FiniteExperimentSystem,
    FiniteTarget,
    identify_target,
)


Observation: TypeAlias = tuple[str, Hashable]
Transcript: TypeAlias = tuple[Observation, ...]
ExperimentPolicy: TypeAlias = Literal[
    "obstruction_first",
    "uncertainty_first",
    "fixed_order",
    "always_guess",
    "always_abstain",
]
EpisodeOutcome: TypeAlias = Literal[
    "recovered",
    "terminal_obstruction",
    "budget_exhausted",
    "guess",
    "unsupported_abstention",
]
ObstructionScope: TypeAlias = Literal["local", "terminal"]


@dataclass(frozen=True)
class DiscoveryProblem:
    """A public finite discovery task with one hidden actual realization."""

    problem_id: str
    pair_id: str
    variant: Literal["coarse", "rich"]
    domain: str
    system: FiniteExperimentSystem
    target: FiniteTarget
    allowed_family: tuple[str, ...]
    budget: int
    experiment_costs: tuple[int, ...]

    def __post_init__(self) -> None:
        for value, label in (
            (self.problem_id, "problem_id"),
            (self.pair_id, "pair_id"),
            (self.domain, "domain"),
        ):
            if not value:
                raise ValueError(f"{label} must be nonempty")
        if self.variant not in ("coarse", "rich"):
            raise ValueError("variant must be 'coarse' or 'rich'")
        normalized = self.system.normalize_family(self.allowed_family)
        object.__setattr__(self, "allowed_family", normalized)
        if len(self.target.values) != len(self.system.realizations):
            raise ValueError("target must have one value per realization")
        if self.budget < 0:
            raise ValueError("budget must be nonnegative")
        if len(self.experiment_costs) != len(self.system.experiments):
            raise ValueError("experiment costs must align with declared experiments")
        if any(
            isinstance(cost, bool) or not isinstance(cost, int) or cost <= 0
            for cost in self.experiment_costs
        ):
            raise ValueError("experiment costs must be positive integers")
        identify_target(self.system, self.target, ())

    def experiment_cost(self, experiment: str) -> int:
        try:
            index = self.system.experiments.index(experiment)
        except ValueError as error:
            raise ValueError(f"unknown experiment: {experiment}") from error
        return self.experiment_costs[index]


@dataclass(frozen=True)
class ScopedObstructionCertificate:
    """A target-distinct pair scoped to a current transcript and family."""

    problem_id: str
    scope: ObstructionScope
    left: str
    right: str
    target_values: tuple[Hashable, Hashable]
    observed_transcript: Transcript
    separating_experiments: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "problem_id": self.problem_id,
            "scope": self.scope,
            "pair": [self.left, self.right],
            "target_values": list(self.target_values),
            "observed_transcript": [
                {"experiment": experiment, "outcome": outcome}
                for experiment, outcome in self.observed_transcript
            ],
            "separating_experiments": list(self.separating_experiments),
        }


@dataclass(frozen=True)
class EpisodeResult:
    """One policy run for one hidden world."""

    problem_id: str
    pair_id: str
    variant: str
    policy: ExperimentPolicy
    actual_realization: str
    actual_target: Hashable
    outcome: EpisodeOutcome
    predicted_target: Hashable | None
    observations: Transcript
    final_candidates: tuple[str, ...]
    certificate: ScopedObstructionCertificate | None
    total_cost: int

    @property
    def steps(self) -> int:
        return len(self.observations)

    def to_dict(self) -> dict[str, object]:
        return {
            "problem_id": self.problem_id,
            "pair_id": self.pair_id,
            "variant": self.variant,
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
            "certificate": (
                None if self.certificate is None else self.certificate.to_dict()
            ),
            "steps": self.steps,
            "total_cost": self.total_cost,
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


def _normalize_observations(
    problem: DiscoveryProblem,
    observations: Iterable[Observation],
) -> Transcript:
    normalized = tuple(observations)
    experiment_names = tuple(experiment for experiment, _ in normalized)
    if len(set(experiment_names)) != len(experiment_names):
        raise ValueError("observed experiments must be unique")
    if not set(experiment_names).issubset(problem.allowed_family):
        raise ValueError("observations must use only permitted experiments")
    for experiment, observed_outcome in normalized:
        index = problem.system.experiments.index(experiment)
        declared_types = {
            type(row[index]) for row in problem.system.outcomes
        }
        if declared_types and type(observed_outcome) not in declared_types:
            raise ValueError(
                f"outcome for experiment {experiment!r} has the wrong type"
            )
    return normalized


def candidate_worlds(
    problem: DiscoveryProblem,
    observations: Iterable[Observation],
) -> tuple[str, ...]:
    """Return worlds consistent with an exact partial transcript."""

    normalized = _normalize_observations(problem, observations)
    return tuple(
        realization
        for realization in problem.system.realizations
        if all(
            _outcome(problem, realization, experiment) == observed_outcome
            for experiment, observed_outcome in normalized
        )
    )


def target_is_determined(
    problem: DiscoveryProblem,
    candidates: Iterable[str],
) -> bool:
    """Whether all remaining candidates share one target value."""

    targets = _target_map(problem)
    values = {targets[candidate] for candidate in candidates}
    return len(values) == 1


def determined_target(
    problem: DiscoveryProblem,
    candidates: Iterable[str],
) -> Hashable:
    """Return the common target value, rejecting empty or ambiguous spaces."""

    candidate_tuple = tuple(candidates)
    if not candidate_tuple:
        raise ValueError("candidate set must be nonempty")
    if not target_is_determined(problem, candidate_tuple):
        raise ValueError("target is not determined by the candidate set")
    return _target_map(problem)[candidate_tuple[0]]


def _separating_experiments(
    problem: DiscoveryProblem,
    left: str,
    right: str,
) -> tuple[str, ...]:
    return tuple(
        experiment
        for experiment in problem.allowed_family
        if _outcome(problem, left, experiment)
        != _outcome(problem, right, experiment)
    )


def find_obstruction(
    problem: DiscoveryProblem,
    observations: Iterable[Observation] = (),
    *,
    require_terminal: bool = False,
) -> ScopedObstructionCertificate | None:
    """Return a current target collision, preferring a terminal pair."""

    normalized = _normalize_observations(problem, observations)
    candidates = candidate_worlds(problem, normalized)
    targets = _target_map(problem)
    local: ScopedObstructionCertificate | None = None
    for left, right in itertools.combinations(candidates, 2):
        if targets[left] == targets[right]:
            continue
        separators = _separating_experiments(problem, left, right)
        scope: ObstructionScope = "terminal" if not separators else "local"
        certificate = ScopedObstructionCertificate(
            problem_id=problem.problem_id,
            scope=scope,
            left=left,
            right=right,
            target_values=(targets[left], targets[right]),
            observed_transcript=normalized,
            separating_experiments=separators,
        )
        if scope == "terminal":
            return certificate
        if local is None:
            local = certificate
    return None if require_terminal else local


def validate_obstruction(
    problem: DiscoveryProblem,
    certificate: ScopedObstructionCertificate,
) -> bool:
    """Fail closed unless every certificate field matches the public task."""

    if certificate.problem_id != problem.problem_id:
        return False
    if certificate.scope not in ("local", "terminal"):
        return False
    if certificate.left == certificate.right:
        return False
    if certificate.left not in problem.system.realizations:
        return False
    if certificate.right not in problem.system.realizations:
        return False
    try:
        normalized = _normalize_observations(
            problem,
            certificate.observed_transcript,
        )
    except ValueError:
        return False
    candidates = candidate_worlds(problem, normalized)
    if certificate.left not in candidates or certificate.right not in candidates:
        return False
    targets = _target_map(problem)
    expected_targets = (targets[certificate.left], targets[certificate.right])
    if expected_targets[0] == expected_targets[1]:
        return False
    if certificate.target_values != expected_targets:
        return False
    expected_separators = _separating_experiments(
        problem,
        certificate.left,
        certificate.right,
    )
    if certificate.separating_experiments != expected_separators:
        return False
    expected_scope = "terminal" if not expected_separators else "local"
    return certificate.scope == expected_scope


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


def choose_experiment(
    problem: DiscoveryProblem,
    candidates: tuple[str, ...],
    remaining: tuple[str, ...],
    policy: ExperimentPolicy,
) -> str:
    """Select the next experiment with stable declared-order tie breaking."""

    if not remaining:
        raise ValueError("remaining experiment set must be nonempty")
    if policy == "fixed_order":
        return remaining[0]
    if policy not in ("obstruction_first", "uncertainty_first"):
        raise ValueError(f"policy does not select experiments: {policy}")
    target_only = policy == "obstruction_first"

    def score(experiment: str) -> tuple[Fraction, int, int]:
        separated = _separated_pair_count(
            problem,
            candidates,
            experiment,
            target_only=target_only,
        )
        cost = problem.experiment_cost(experiment)
        declared_index = problem.system.experiments.index(experiment)
        return Fraction(separated, cost), separated, -declared_index

    return max(remaining, key=score)


def run_episode(
    problem: DiscoveryProblem,
    actual_realization: str,
    policy: ExperimentPolicy = "obstruction_first",
) -> EpisodeResult:
    """Run one exact episode without exposing the hidden realization."""

    if actual_realization not in problem.system.realizations:
        raise ValueError(f"unknown actual realization: {actual_realization}")
    targets = _target_map(problem)
    actual_target = targets[actual_realization]
    observations: Transcript = ()
    candidates = candidate_worlds(problem, observations)

    if policy == "always_guess":
        return EpisodeResult(
            problem_id=problem.problem_id,
            pair_id=problem.pair_id,
            variant=problem.variant,
            policy=policy,
            actual_realization=actual_realization,
            actual_target=actual_target,
            outcome="guess",
            predicted_target=targets[candidates[0]],
            observations=(),
            final_candidates=candidates,
            certificate=None,
            total_cost=0,
        )
    if policy == "always_abstain":
        return EpisodeResult(
            problem_id=problem.problem_id,
            pair_id=problem.pair_id,
            variant=problem.variant,
            policy=policy,
            actual_realization=actual_realization,
            actual_target=actual_target,
            outcome="unsupported_abstention",
            predicted_target=None,
            observations=(),
            final_candidates=candidates,
            certificate=None,
            total_cost=0,
        )
    if policy not in ("obstruction_first", "uncertainty_first", "fixed_order"):
        raise ValueError(f"unknown policy: {policy}")

    total_cost = 0
    while True:
        candidates = candidate_worlds(problem, observations)
        if not candidates:
            raise AssertionError("realizable episode produced an empty version space")
        if target_is_determined(problem, candidates):
            return EpisodeResult(
                problem_id=problem.problem_id,
                pair_id=problem.pair_id,
                variant=problem.variant,
                policy=policy,
                actual_realization=actual_realization,
                actual_target=actual_target,
                outcome="recovered",
                predicted_target=determined_target(problem, candidates),
                observations=observations,
                final_candidates=candidates,
                certificate=None,
                total_cost=total_cost,
            )

        terminal = find_obstruction(
            problem,
            observations,
            require_terminal=True,
        )
        if terminal is not None:
            return EpisodeResult(
                problem_id=problem.problem_id,
                pair_id=problem.pair_id,
                variant=problem.variant,
                policy=policy,
                actual_realization=actual_realization,
                actual_target=actual_target,
                outcome="terminal_obstruction",
                predicted_target=None,
                observations=observations,
                final_candidates=candidates,
                certificate=terminal,
                total_cost=total_cost,
            )

        performed = {experiment for experiment, _ in observations}
        affordable = tuple(
            experiment
            for experiment in problem.allowed_family
            if experiment not in performed
            and total_cost + problem.experiment_cost(experiment) <= problem.budget
        )
        if not affordable:
            local = find_obstruction(problem, observations)
            if local is None:
                raise AssertionError("ambiguous target lacks a local obstruction")
            return EpisodeResult(
                problem_id=problem.problem_id,
                pair_id=problem.pair_id,
                variant=problem.variant,
                policy=policy,
                actual_realization=actual_realization,
                actual_target=actual_target,
                outcome="budget_exhausted",
                predicted_target=None,
                observations=observations,
                final_candidates=candidates,
                certificate=local,
                total_cost=total_cost,
            )

        experiment = choose_experiment(
            problem,
            candidates,
            affordable,
            policy,
        )
        outcome = _outcome(problem, actual_realization, experiment)
        observations = (*observations, (experiment, outcome))
        total_cost += problem.experiment_cost(experiment)


def recoverable_within_budget(problem: DiscoveryProblem) -> bool:
    """Whether one non-adaptive permitted family identifies within budget."""

    for size in range(len(problem.allowed_family) + 1):
        for family in itertools.combinations(problem.allowed_family, size):
            if sum(problem.experiment_cost(item) for item in family) > problem.budget:
                continue
            if isinstance(
                identify_target(problem.system, problem.target, family),
                FactorizationCertificate,
            ):
                return True
    return False
