"""Experiment-relative equivalence and live hypothesis classes."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence

from experiments.ident.schemas import ObservationValue, PriorObservation


def matches_observations(
    hypothesis_id: str,
    prior_observations: Sequence[PriorObservation],
    observed_responses: Mapping[str, Mapping[str, ObservationValue]],
) -> bool:
    """Return True iff hypothesis reproduces every prior observation outcome."""
    responses = observed_responses.get(hypothesis_id)
    if responses is None:
        return False
    for obs in prior_observations:
        if obs.experiment_id not in responses:
            # Prior observation may be outside the candidate intervention menu.
            # Generators must supply matching via metadata table keyed by experiment_id.
            return False
        if responses[obs.experiment_id] != obs.outcome:
            return False
    return True


def equivalence_class(
    hypotheses: Sequence[str],
    prior_observations: Sequence[PriorObservation],
    observed_responses: Mapping[str, Mapping[str, ObservationValue]],
) -> list[str]:
    """Hypotheses indistinguishable under the observations performed so far."""
    return [
        h
        for h in hypotheses
        if matches_observations(h, prior_observations, observed_responses)
    ]


def partition_by_outcome(
    live: Sequence[str],
    intervention_id: str,
    response_table: Mapping[str, Mapping[str, ObservationValue]],
) -> dict[ObservationValue, list[str]]:
    buckets: dict[ObservationValue, list[str]] = {}
    for hypothesis_id in live:
        outcome = response_table[hypothesis_id][intervention_id]
        buckets.setdefault(outcome, []).append(hypothesis_id)
    return buckets


def entropy_uniform(labels: Iterable[str]) -> float:
    items = list(labels)
    n = len(items)
    if n <= 1:
        return 0.0
    # Uniform prior over remaining live hypotheses.
    from math import log2

    return log2(n)


def information_gain(
    live: Sequence[str],
    intervention_id: str,
    response_table: Mapping[str, Mapping[str, ObservationValue]],
) -> float:
    """Expected entropy reduction under a uniform prior over the live class."""
    if len(live) <= 1:
        return 0.0
    before = entropy_uniform(live)
    partitions = partition_by_outcome(live, intervention_id, response_table)
    n = len(live)
    expected_after = 0.0
    for members in partitions.values():
        p = len(members) / n
        expected_after += p * entropy_uniform(members)
    return before - expected_after
