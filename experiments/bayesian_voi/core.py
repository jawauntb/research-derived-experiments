"""Finite-state exact Bayesian VOI calculations.

The hidden state is which of two actions is optimal.  Each binary probe has an
assumed likelihood (used by the learner) and a true likelihood (used by the
oracle and the realized-regret audit).  Enumerating both outcomes makes EVSI,
mutual information, and regret reduction exact rather than Monte Carlo scores.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import log2
from typing import Literal, Mapping, TypedDict


STATES = ("A", "B")
OUTCOMES = (0, 1)

MetricName = Literal[
    "current_error",
    "posterior_variance",
    "error_squared_over_k_plus_one",
    "mutual_information",
    "assumed_evsi",
    "expected_regret_reduction",
    "oracle_evsi",
]
CorrelationMetricName = Literal[
    "current_error",
    "posterior_variance",
    "error_squared_over_k_plus_one",
    "mutual_information",
    "assumed_evsi",
    "expected_regret_reduction",
]
TopMetricName = Literal[
    "mutual_information",
    "assumed_evsi",
    "expected_regret_reduction",
    "oracle_evsi",
]

CORRELATION_METRICS: tuple[CorrelationMetricName, ...] = (
    "current_error",
    "posterior_variance",
    "error_squared_over_k_plus_one",
    "mutual_information",
    "assumed_evsi",
    "expected_regret_reduction",
)
TOP_METRICS: tuple[TopMetricName, ...] = (
    "mutual_information",
    "assumed_evsi",
    "expected_regret_reduction",
    "oracle_evsi",
)


class ProbeMetrics(TypedDict):
    probe: str
    current_error: float
    posterior_variance: float
    error_squared_over_k_plus_one: float
    mutual_information: float
    assumed_evsi: float
    expected_regret_reduction: float
    oracle_evsi: float


class ScenarioPayload(TypedDict):
    scenario: str
    prior: dict[str, float]
    sample_count: int
    probes: list[ProbeMetrics]
    top_by_metric: dict[TopMetricName, list[str]]
    spearman_vs_oracle_evsi: dict[CorrelationMetricName, float | None]


class BenchmarkPayload(TypedDict):
    experiment_id: str
    schema_version: str
    status: Literal["pass", "fail"]
    gates: dict[str, bool]
    scenarios: list[ScenarioPayload]


@dataclass(frozen=True)
class Probe:
    name: str
    assumed_likelihood: Mapping[str, float]
    true_likelihood: Mapping[str, float]


@dataclass(frozen=True)
class Scenario:
    name: str
    prior: Mapping[str, float]
    sample_count: int
    probes: tuple[Probe, ...]


def _validate_distribution(distribution: Mapping[str, float]) -> None:
    if set(distribution) != set(STATES):
        raise ValueError("state distribution must contain A and B")
    if any(probability < 0 or probability > 1 for probability in distribution.values()):
        raise ValueError("probabilities must be in [0, 1]")
    if abs(sum(distribution.values()) - 1.0) > 1e-12:
        raise ValueError("state distribution must sum to one")


def _validate_likelihood(likelihood: Mapping[str, float]) -> None:
    if set(likelihood) != set(STATES):
        raise ValueError("likelihood must contain A and B")
    if any(probability < 0 or probability > 1 for probability in likelihood.values()):
        raise ValueError("likelihood probabilities must be in [0, 1]")


def predictive_probability(prior: Mapping[str, float], likelihood: Mapping[str, float], outcome: int) -> float:
    return sum(
        prior[state] * (likelihood[state] if outcome == 1 else 1.0 - likelihood[state])
        for state in STATES
    )


def posterior(
    prior: Mapping[str, float], likelihood: Mapping[str, float], outcome: int
) -> dict[str, float]:
    probability = predictive_probability(prior, likelihood, outcome)
    if probability == 0.0:
        return dict(prior)
    return {
        state: prior[state]
        * (likelihood[state] if outcome == 1 else 1.0 - likelihood[state])
        / probability
        for state in STATES
    }


def choose_action(state_distribution: Mapping[str, float]) -> str:
    return max(STATES, key=lambda state: (state_distribution[state], state == "A"))


def classification_error(state_distribution: Mapping[str, float]) -> float:
    return min(state_distribution.values())


def entropy(probabilities: list[float]) -> float:
    return -sum(probability * log2(probability) for probability in probabilities if probability > 0.0)


def mutual_information(prior: Mapping[str, float], likelihood: Mapping[str, float]) -> float:
    predictive = [predictive_probability(prior, likelihood, outcome) for outcome in OUTCOMES]
    conditional_entropy = sum(
        prior[state] * entropy([likelihood[state], 1.0 - likelihood[state]]) for state in STATES
    )
    return entropy(predictive) - conditional_entropy


def exact_evsi(prior: Mapping[str, float], likelihood: Mapping[str, float]) -> float:
    baseline = classification_error(prior)
    expected_after = sum(
        predictive_probability(prior, likelihood, outcome)
        * classification_error(posterior(prior, likelihood, outcome))
        for outcome in OUTCOMES
    )
    return baseline - expected_after


def true_regret_reduction(
    prior: Mapping[str, float], assumed_likelihood: Mapping[str, float], true_likelihood: Mapping[str, float]
) -> float:
    """Expected true regret reduction when acting on the learner's posterior."""

    baseline_action = choose_action(prior)
    baseline_regret = prior["B" if baseline_action == "A" else "A"]
    after_regret = 0.0
    for outcome in OUTCOMES:
        action = choose_action(posterior(prior, assumed_likelihood, outcome))
        for state in STATES:
            outcome_probability = true_likelihood[state] if outcome == 1 else 1.0 - true_likelihood[state]
            if action != state:
                after_regret += prior[state] * outcome_probability
    return baseline_regret - after_regret


def _rank(values: list[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda pair: pair[1])
    result = [0.0] * len(values)
    start = 0
    while start < len(indexed):
        end = start + 1
        while end < len(indexed) and indexed[end][1] == indexed[start][1]:
            end += 1
        rank = (start + 1 + end) / 2.0
        for index, _ in indexed[start:end]:
            result[index] = rank
        start = end
    return result


def spearman(values_a: list[float], values_b: list[float]) -> float | None:
    if len(values_a) != len(values_b) or len(values_a) < 2:
        raise ValueError("Spearman inputs must have equal length >= 2")
    ranks_a, ranks_b = _rank(values_a), _rank(values_b)
    mean_a, mean_b = sum(ranks_a) / len(ranks_a), sum(ranks_b) / len(ranks_b)
    centered_a = [value - mean_a for value in ranks_a]
    centered_b = [value - mean_b for value in ranks_b]
    denominator = sum(value * value for value in centered_a) * sum(value * value for value in centered_b)
    if denominator == 0.0:
        return None
    return sum(left * right for left, right in zip(centered_a, centered_b)) / denominator**0.5


def _probe_metrics(scenario: Scenario) -> list[ProbeMetrics]:
    _validate_distribution(scenario.prior)
    current_error = classification_error(scenario.prior)
    posterior_variance = scenario.prior["A"] * scenario.prior["B"]
    heuristic = current_error**2 / (scenario.sample_count + 1)
    rows: list[ProbeMetrics] = []
    for probe in scenario.probes:
        _validate_likelihood(probe.assumed_likelihood)
        _validate_likelihood(probe.true_likelihood)
        rows.append(
            {
                "probe": probe.name,
                "current_error": current_error,
                "posterior_variance": posterior_variance,
                "error_squared_over_k_plus_one": heuristic,
                "mutual_information": mutual_information(scenario.prior, probe.assumed_likelihood),
                "assumed_evsi": exact_evsi(scenario.prior, probe.assumed_likelihood),
                "expected_regret_reduction": true_regret_reduction(
                    scenario.prior, probe.assumed_likelihood, probe.true_likelihood
                ),
                "oracle_evsi": exact_evsi(scenario.prior, probe.true_likelihood),
            }
        )
    return rows


def _top(rows: list[ProbeMetrics], metric: MetricName) -> list[str]:
    maximum = max(float(row[metric]) for row in rows)
    return [str(row["probe"]) for row in rows if abs(float(row[metric]) - maximum) <= 1e-12]


def _scenario_payload(scenario: Scenario) -> ScenarioPayload:
    rows = _probe_metrics(scenario)
    oracle = [float(row["oracle_evsi"]) for row in rows]
    metrics = {
        metric: spearman([float(row[metric]) for row in rows], oracle)
        for metric in CORRELATION_METRICS
    }
    return {
        "scenario": scenario.name,
        "prior": dict(scenario.prior),
        "sample_count": scenario.sample_count,
        "probes": rows,
        "top_by_metric": {
            metric: _top(rows, metric)
            for metric in TOP_METRICS
        },
        "spearman_vs_oracle_evsi": metrics,
    }


def scenarios() -> tuple[Scenario, ...]:
    prior = {"A": 0.6, "B": 0.4}
    return (
        Scenario(
            "learnable_uncertainty",
            prior,
            4,
            (
                Probe("signal", {"A": 0.9, "B": 0.1}, {"A": 0.9, "B": 0.1}),
                Probe("weak_signal", {"A": 0.7, "B": 0.3}, {"A": 0.7, "B": 0.3}),
                Probe("noise", {"A": 0.5, "B": 0.5}, {"A": 0.5, "B": 0.5}),
            ),
        ),
        Scenario(
            "irreducible_noise",
            prior,
            4,
            tuple(
                Probe(name, {"A": 0.5, "B": 0.5}, {"A": 0.5, "B": 0.5})
                for name in ("high_error_probe", "repeat_noise", "unrelated_noise")
            ),
        ),
        Scenario(
            "model_misspecification",
            prior,
            4,
            (
                Probe("misleading_signal", {"A": 0.95, "B": 0.05}, {"A": 0.5, "B": 0.5}),
                Probe("robust_weak_signal", {"A": 0.7, "B": 0.3}, {"A": 0.7, "B": 0.3}),
                Probe("noise", {"A": 0.5, "B": 0.5}, {"A": 0.5, "B": 0.5}),
            ),
        ),
    )


def evaluate_benchmark() -> BenchmarkPayload:
    scenario_payloads = [_scenario_payload(scenario) for scenario in scenarios()]
    by_name = {scenario["scenario"]: scenario for scenario in scenario_payloads}
    learnable = by_name["learnable_uncertainty"]
    irreducible = by_name["irreducible_noise"]
    misspecified = by_name["model_misspecification"]
    learnable_mutual_information_rho = learnable["spearman_vs_oracle_evsi"]["mutual_information"]
    if learnable_mutual_information_rho is None:
        raise RuntimeError("learnable mutual-information rank correlation is undefined")
    gates = {
        "learnable_mutual_information_rho_ge_0_7": float(
            learnable_mutual_information_rho
        )
        >= 0.7,
        "learnable_oracle_signal_top": learnable["top_by_metric"]["oracle_evsi"] == ["signal"],
        "irreducible_oracle_evsi_zero": max(
            abs(float(row["oracle_evsi"])) for row in irreducible["probes"]
        )
        <= 1e-12,
        "irreducible_current_error_is_high": float(irreducible["probes"][0]["current_error"]) >= 0.3,
        "misspecification_preserves_failure": (
            misspecified["top_by_metric"]["mutual_information"] != misspecified["top_by_metric"]["oracle_evsi"]
            and misspecified["top_by_metric"]["expected_regret_reduction"] == ["robust_weak_signal"]
        ),
    }
    return {
        "experiment_id": "bayesian_voi",
        "schema_version": "1.0",
        "status": "pass" if all(gates.values()) else "fail",
        "gates": gates,
        "scenarios": scenario_payloads,
    }
