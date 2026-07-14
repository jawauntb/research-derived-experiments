#!/usr/bin/env python3
"""Coupling phase-map and hysteresis tests for passive-to-active geometry.

The harness is intentionally small and synthetic.  It trains a bottleneck
autoencoder with an action head while continuously varying the weight of the
action objective.  The experiment asks whether order parameters exhibit a
replicable discontinuity or only a continuous crossover, and whether matched
forward/reverse optimization paths retain regime memory.

Raw per-seed cells are written under ``artifacts/``.  Committed summaries only
contain aggregate curves, model-comparison scores, and strict gate verdicts.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np


ORDER_PARAMETERS = (
    "causal_specific_effect",
    "perturbation_failure_rate",
    "viability_buffer",
    "geometry_gap",
    "return",
)


@dataclass(frozen=True)
class ExperimentConfig:
    couplings: tuple[float, ...] = tuple(i / 10 for i in range(11))
    architectures: tuple[str, ...] = ("linear", "tanh")
    seeds: tuple[int, ...] = (0, 1, 2, 3, 4)
    samples: int = 192
    phase_updates: int = 80
    path_updates: int = 32
    washout_updates: int = 8
    retention_checkpoints: tuple[int, ...] = (0, 8, 24, 48, 80)
    learning_rate: float = 0.055
    bootstrap_samples: int = 1000

    def validate(self) -> None:
        if len(self.couplings) < 3 or tuple(sorted(self.couplings)) != self.couplings:
            raise ValueError("couplings must contain at least three sorted values")
        if self.couplings[0] < 0.0 or self.couplings[-1] > 1.0:
            raise ValueError("couplings must lie in [0, 1]")
        if len(set(self.couplings)) != len(self.couplings):
            raise ValueError("couplings must be unique")
        if set(self.architectures) != {"linear", "tanh"}:
            raise ValueError("architectures must be exactly ('linear', 'tanh')")
        if not self.seeds or len(set(self.seeds)) != len(self.seeds):
            raise ValueError("seeds must be non-empty and unique")
        if self.samples < 32 or self.samples % 2:
            raise ValueError("samples must be an even integer >= 32")
        if min(self.phase_updates, self.path_updates, self.bootstrap_samples) <= 0:
            raise ValueError("update and bootstrap counts must be positive")
        if self.washout_updates < 0:
            raise ValueError("washout_updates must be non-negative")
        if not self.retention_checkpoints or self.retention_checkpoints[0] != 0:
            raise ValueError("retention checkpoints must start at zero")
        if tuple(sorted(self.retention_checkpoints)) != self.retention_checkpoints:
            raise ValueError("retention checkpoints must be sorted")


PRESETS = {
    "smoke": ExperimentConfig(
        couplings=(0.0, 0.5, 1.0),
        seeds=(0, 1),
        samples=96,
        phase_updates=24,
        path_updates=12,
        washout_updates=4,
        retention_checkpoints=(0, 4, 8),
        bootstrap_samples=100,
    ),
    "registered": ExperimentConfig(),
}


@dataclass
class Model:
    encoder: np.ndarray
    encoder_bias: np.ndarray
    decoder: np.ndarray
    decoder_bias: np.ndarray
    head: np.ndarray
    head_bias: float
    architecture: str


def _rng(seed: int, salt: int) -> np.random.Generator:
    return np.random.default_rng(seed * 1_000_003 + salt)


def _sigmoid(values: np.ndarray) -> np.ndarray:
    clipped = np.clip(values, -30.0, 30.0)
    return 1.0 / (1.0 + np.exp(-clipped))


def make_dataset(seed: int, samples: int) -> tuple[np.ndarray, np.ndarray]:
    """Create a balanced semantic-action task with higher-variance nuisance axes."""

    rng = _rng(seed, 11)
    labels = np.repeat(np.array([0.0, 1.0]), samples // 2)
    rng.shuffle(labels)
    signed = labels * 2.0 - 1.0
    nuisance = rng.normal(0.0, 1.8, size=samples)
    inputs = np.column_stack(
        [
            0.72 * signed + rng.normal(0.0, 0.78, size=samples),
            nuisance,
            0.55 * nuisance + rng.normal(0.0, 0.92, size=samples),
            0.30 * signed * nuisance + rng.normal(0.0, 1.05, size=samples),
        ]
    )
    inputs = (inputs - inputs.mean(axis=0)) / (inputs.std(axis=0) + 1e-9)
    return inputs.astype(float), labels.astype(float)


def initialize_model(architecture: str, seed: int) -> Model:
    if architecture not in {"linear", "tanh"}:
        raise ValueError(f"unknown architecture: {architecture}")
    rng = _rng(seed, 23 if architecture == "linear" else 29)
    hidden = 2 if architecture == "linear" else 4
    scale = 0.16 if architecture == "linear" else 0.12
    return Model(
        encoder=rng.normal(0.0, scale, size=(4, hidden)),
        encoder_bias=np.zeros(hidden),
        decoder=rng.normal(0.0, scale, size=(hidden, 4)),
        decoder_bias=np.zeros(4),
        head=rng.normal(0.0, 0.035, size=hidden),
        head_bias=0.0,
        architecture=architecture,
    )


def _hidden(model: Model, inputs: np.ndarray) -> np.ndarray:
    preactivation = inputs @ model.encoder + model.encoder_bias
    if model.architecture == "tanh":
        return np.tanh(preactivation)
    return preactivation


def train_model(
    model: Model,
    inputs: np.ndarray,
    labels: np.ndarray,
    coupling: float,
    updates: int,
    learning_rate: float,
) -> None:
    """Apply a fixed full-batch update budget at one coupling value."""

    n, input_dim = inputs.shape
    l2 = 8e-4
    for _ in range(updates):
        hidden = _hidden(model, inputs)
        reconstruction = hidden @ model.decoder + model.decoder_bias
        logits = hidden @ model.head + model.head_bias
        probabilities = _sigmoid(logits)

        reconstruction_grad = 2.0 * (reconstruction - inputs) / (n * input_dim)
        logit_grad = coupling * (probabilities - labels) / n

        decoder_grad = hidden.T @ reconstruction_grad + l2 * model.decoder
        decoder_bias_grad = reconstruction_grad.sum(axis=0)
        head_grad = hidden.T @ logit_grad + l2 * model.head
        head_bias_grad = float(logit_grad.sum())
        hidden_grad = reconstruction_grad @ model.decoder.T + np.outer(logit_grad, model.head)
        if model.architecture == "tanh":
            hidden_grad *= 1.0 - hidden**2
        encoder_grad = inputs.T @ hidden_grad + l2 * model.encoder
        encoder_bias_grad = hidden_grad.sum(axis=0)

        gradients = (
            encoder_grad,
            encoder_bias_grad,
            decoder_grad,
            decoder_bias_grad,
            head_grad,
        )
        norm = math.sqrt(sum(float(np.vdot(gradient, gradient)) for gradient in gradients))
        scale = min(1.0, 5.0 / max(norm, 1e-12))
        model.encoder -= learning_rate * scale * encoder_grad
        model.encoder_bias -= learning_rate * scale * encoder_bias_grad
        model.decoder -= learning_rate * scale * decoder_grad
        model.decoder_bias -= learning_rate * scale * decoder_bias_grad
        model.head -= learning_rate * scale * head_grad
        model.head_bias -= learning_rate * scale * head_bias_grad


def measure_model(model: Model, inputs: np.ndarray, labels: np.ndarray, seed: int) -> dict[str, float]:
    hidden = _hidden(model, inputs)
    logits = hidden @ model.head + model.head_bias
    predictions = (logits >= 0.0).astype(float)
    accuracy = float(np.mean(predictions == labels))
    signed = labels * 2.0 - 1.0

    positive = hidden[labels == 1.0]
    negative = hidden[labels == 0.0]
    centroid_delta = positive.mean(axis=0) - negative.mean(axis=0)
    delta_norm = float(np.linalg.norm(centroid_delta))
    if delta_norm < 1e-12:
        target_axis = np.zeros(hidden.shape[1])
        target_axis[0] = 1.0
    else:
        target_axis = centroid_delta / delta_norm

    centered = hidden - hidden.mean(axis=0)
    ablated_target = hidden - np.outer(centered @ target_axis, target_axis)
    target_logits = ablated_target @ model.head + model.head_bias
    target_accuracy = float(np.mean((target_logits >= 0.0) == labels))

    rng = _rng(seed, 41 + hidden.shape[1])
    random_axis = rng.normal(size=hidden.shape[1])
    random_axis -= float(random_axis @ target_axis) * target_axis
    random_norm = float(np.linalg.norm(random_axis))
    if random_norm < 1e-12:
        random_axis = np.roll(target_axis, 1)
        random_norm = float(np.linalg.norm(random_axis))
    random_axis /= max(random_norm, 1e-12)
    ablated_random = hidden - np.outer(centered @ random_axis, random_axis)
    random_logits = ablated_random @ model.head + model.head_bias
    random_accuracy = float(np.mean((random_logits >= 0.0) == labels))

    target_effect = accuracy - target_accuracy
    random_effect = accuracy - random_accuracy
    causal_specific_effect = target_effect - random_effect

    positive_centered = positive - positive.mean(axis=0)
    negative_centered = negative - negative.mean(axis=0)
    within_scale = math.sqrt(
        0.5
        * (
            float(np.mean(np.sum(positive_centered**2, axis=1)))
            + float(np.mean(np.sum(negative_centered**2, axis=1)))
        )
    )
    geometry_gap = delta_norm / max(within_scale, 1e-9)

    perturbation = hidden - np.outer(signed, target_axis) * (0.75 * max(within_scale, 1e-6))
    perturbed_predictions = ((perturbation @ model.head + model.head_bias) >= 0.0).astype(float)
    originally_correct = predictions == labels
    if np.any(originally_correct):
        perturbation_failure_rate = float(
            np.mean(perturbed_predictions[originally_correct] != labels[originally_correct])
        )
    else:
        perturbation_failure_rate = 1.0

    viability_buffer = float(np.mean(signed * logits) / (float(np.std(logits)) + 1e-9))
    return {
        "accuracy": accuracy,
        "causal_target_effect": target_effect,
        "random_axis_effect": random_effect,
        "causal_specific_effect": causal_specific_effect,
        "perturbation_failure_rate": perturbation_failure_rate,
        "viability_buffer": viability_buffer,
        "geometry_gap": geometry_gap,
        "return": 2.0 * accuracy - 1.0,
    }


def _phase_rows(config: ExperimentConfig) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for architecture in config.architectures:
        for seed in config.seeds:
            inputs, labels = make_dataset(seed, config.samples)
            for coupling in config.couplings:
                model = initialize_model(architecture, seed)
                train_model(
                    model,
                    inputs,
                    labels,
                    coupling,
                    config.phase_updates,
                    config.learning_rate,
                )
                rows.append(
                    {
                        "architecture": architecture,
                        "seed": seed,
                        "coupling": coupling,
                        "updates": config.phase_updates,
                        **measure_model(model, inputs, labels, seed),
                    }
                )
    return rows


def _design_polynomial(values: np.ndarray, degree: int) -> np.ndarray:
    return np.column_stack([values**power for power in range(degree + 1)])


def _fit_predict(design: np.ndarray, targets: np.ndarray, evaluation: np.ndarray) -> np.ndarray:
    coefficients, *_ = np.linalg.lstsq(design, targets, rcond=None)
    return evaluation @ coefficients


def _smooth_prediction(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_eval: np.ndarray,
    model: str,
) -> np.ndarray:
    if model == "polynomial":
        degree = min(3, max(1, len(x_train) - 2))
        return _fit_predict(
            _design_polynomial(x_train, degree),
            y_train,
            _design_polynomial(x_eval, degree),
        )
    if model != "sigmoid":
        raise ValueError(model)
    candidates: list[tuple[float, float, float]] = []
    for midpoint in np.linspace(0.15, 0.85, 15):
        for steepness in (2.0, 4.0, 8.0, 16.0, 32.0):
            basis = _sigmoid(steepness * (x_train - midpoint))
            design = np.column_stack([np.ones(len(x_train)), x_train, basis])
            prediction = _fit_predict(design, y_train, design)
            candidates.append((float(np.mean((prediction - y_train) ** 2)), midpoint, steepness))
    _, midpoint, steepness = min(candidates, key=lambda item: item[0])
    train_basis = _sigmoid(steepness * (x_train - midpoint))
    eval_basis = _sigmoid(steepness * (x_eval - midpoint))
    return _fit_predict(
        np.column_stack([np.ones(len(x_train)), x_train, train_basis]),
        y_train,
        np.column_stack([np.ones(len(x_eval)), x_eval, eval_basis]),
    )


def _segmented_design(values: np.ndarray, critical: float) -> np.ndarray:
    above = (values >= critical).astype(float)
    return np.column_stack(
        [
            np.ones(len(values)),
            values,
            above,
            np.maximum(values - critical, 0.0),
        ]
    )


def _critical_candidates(values: np.ndarray) -> np.ndarray:
    unique = np.unique(values)
    if len(unique) <= 3:
        return np.array([float(np.median(unique))])
    return (unique[1:-1] + unique[2:]) / 2.0


def _segmented_prediction(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_eval: np.ndarray,
) -> tuple[np.ndarray, float]:
    fits: list[tuple[float, float]] = []
    for critical in _critical_candidates(x_train):
        design = _segmented_design(x_train, float(critical))
        prediction = _fit_predict(design, y_train, design)
        fits.append((float(np.mean((prediction - y_train) ** 2)), float(critical)))
    _, critical = min(fits, key=lambda item: item[0])
    prediction = _fit_predict(
        _segmented_design(x_train, critical),
        y_train,
        _segmented_design(x_eval, critical),
    )
    return prediction, critical


def _aggregate_curve(rows: list[dict[str, Any]], metric: str, architecture: str) -> tuple[np.ndarray, np.ndarray]:
    architecture_rows = [row for row in rows if row["architecture"] == architecture]
    couplings = np.array(sorted({float(row["coupling"]) for row in architecture_rows}))
    means = np.array(
        [
            np.mean(
                [float(row[metric]) for row in architecture_rows if float(row["coupling"]) == coupling]
            )
            for coupling in couplings
        ]
    )
    return couplings, means


def _cross_validated_error(
    rows: list[dict[str, Any]],
    metric: str,
    architecture: str,
    model: str,
) -> float:
    """Score curve shape on held-out seeds rather than held-out grid points.

    Leaving out a coupling makes a literal jump unidentifiable when the omitted
    point is adjacent to the boundary.  A seed-level split instead asks whether
    a curve shape estimated from independent initializations predicts a held-out
    initialization at every preregistered coupling.
    """

    architecture_rows = [row for row in rows if row["architecture"] == architecture]
    seeds = sorted({int(row["seed"]) for row in architecture_rows})
    if len(seeds) < 2:
        raise ValueError("out-of-sample model comparison requires at least two seeds")
    residuals: list[float] = []
    for held_out_seed in seeds:
        training_rows = [row for row in architecture_rows if int(row["seed"]) != held_out_seed]
        evaluation_rows = [row for row in architecture_rows if int(row["seed"]) == held_out_seed]
        x_train = np.array(sorted({float(row["coupling"]) for row in training_rows}))
        y_train = np.array(
            [
                np.mean(
                    [
                        float(row[metric])
                        for row in training_rows
                        if float(row["coupling"]) == coupling
                    ]
                )
                for coupling in x_train
            ]
        )
        evaluation_rows.sort(key=lambda row: float(row["coupling"]))
        x_eval = np.array([float(row["coupling"]) for row in evaluation_rows])
        y_eval = np.array([float(row[metric]) for row in evaluation_rows])
        if model == "segmented":
            prediction, _ = _segmented_prediction(x_train, y_train, x_eval)
        else:
            prediction = _smooth_prediction(x_train, y_train, x_eval, model)
        residuals.extend((prediction - y_eval) ** 2)
    return float(np.mean(residuals))


def _estimate_cell_critical(rows: list[dict[str, Any]], metric: str) -> float:
    x = np.array([float(row["coupling"]) for row in rows])
    y = np.array([float(row[metric]) for row in rows])
    _, critical = _segmented_prediction(x, y, x)
    return critical


def compare_transition_models(rows: list[dict[str, Any]], metric: str) -> dict[str, Any]:
    """Compare discontinuous segmented and smooth curves out of sample."""

    architectures = sorted({str(row["architecture"]) for row in rows})
    errors = {"segmented": [], "polynomial": [], "sigmoid": []}
    architecture_criticals: dict[str, float] = {}
    cell_criticals: dict[str, float] = {}
    for architecture in architectures:
        x, y = _aggregate_curve(rows, metric, architecture)
        for model in errors:
            errors[model].append(_cross_validated_error(rows, metric, architecture, model))
        _, critical = _segmented_prediction(x, y, x)
        architecture_criticals[architecture] = critical
        for seed in sorted({int(row["seed"]) for row in rows if row["architecture"] == architecture}):
            cell = [
                row
                for row in rows
                if row["architecture"] == architecture and int(row["seed"]) == seed
            ]
            cell_criticals[f"{architecture}:{seed}"] = _estimate_cell_critical(cell, metric)

    mean_errors = {name: float(np.mean(values)) for name, values in errors.items()}
    best_smooth_name = min(("polynomial", "sigmoid"), key=lambda name: mean_errors[name])
    best_smooth_error = mean_errors[best_smooth_name]
    segmented_error = mean_errors["segmented"]
    advantage = (best_smooth_error - segmented_error) / max(best_smooth_error, 1e-12)
    return {
        "metric": metric,
        "preferred_model": "segmented" if advantage >= 0.10 else "smooth",
        "segmented_advantage": advantage,
        "segmented_cv_mse": segmented_error,
        "best_smooth_model": best_smooth_name,
        "best_smooth_cv_mse": best_smooth_error,
        "critical_by_architecture": architecture_criticals,
        "critical_by_cell": cell_criticals,
    }


def _critical_stability(comparisons: dict[str, dict[str, Any]]) -> dict[str, Any]:
    primary = comparisons["causal_specific_effect"]
    architecture_values = list(primary["critical_by_architecture"].values())
    global_critical = float(np.median(architecture_values))
    architecture_spread = (
        max(architecture_values) - min(architecture_values)
    ) / max(abs(global_critical), 1e-9)
    cell_values = np.array(list(primary["critical_by_cell"].values()), dtype=float)
    cell_fraction = float(
        np.mean(np.abs(cell_values - global_critical) / max(abs(global_critical), 1e-9) <= 0.20)
    )
    return {
        "global_critical": global_critical,
        "architecture_relative_spread": architecture_spread,
        "cell_fraction_within_20_percent": cell_fraction,
        "pass": architecture_spread <= 0.20 and cell_fraction >= 0.80,
    }


def evaluate_bifurcation(rows: list[dict[str, Any]], config: ExperimentConfig) -> dict[str, Any]:
    comparisons = {metric: compare_transition_models(rows, metric) for metric in ORDER_PARAMETERS}
    segmented_metrics = [
        metric
        for metric, comparison in comparisons.items()
        if comparison["preferred_model"] == "segmented"
        and float(comparison["segmented_advantage"]) >= 0.10
    ]
    stability = _critical_stability(comparisons)
    selected_criticals = [
        float(np.median(list(comparisons[metric]["critical_by_architecture"].values())))
        for metric in segmented_metrics
    ]
    grid_spacing = float(np.min(np.diff(config.couplings))) if len(config.couplings) > 1 else 1.0
    colocated = len(selected_criticals) >= 2 and max(selected_criticals) - min(selected_criticals) <= grid_spacing
    coverage = len(config.architectures) >= 2 and len(config.seeds) >= 5
    passed = len(segmented_metrics) >= 2 and stability["pass"] and colocated and coverage
    return {
        "pass": passed,
        "verdict": "bifurcation" if passed else "bifurcation_not_supported",
        "criteria": (
            "segmented model beats smooth alternatives out of sample by >=10% for >=2 order "
            "parameters; critical coupling replicates within 20% across >=2 architectures and "
            ">=5 seeds; >=2 parameters change within one coupling-grid step"
        ),
        "segmented_metrics": segmented_metrics,
        "critical_stability": stability,
        "colocated_order_parameters": colocated,
        "coverage_pass": coverage,
        "model_comparisons": comparisons,
    }


def _direction_schedule(direction: str, target: float, stages: int) -> tuple[float, ...]:
    """Return a fixed-length monotone path from a passive or active endpoint."""

    if direction == "forward":
        values = np.linspace(0.0, target, stages)
    elif direction == "reverse":
        values = np.linspace(1.0, target, stages)
    else:
        raise ValueError(f"unknown direction: {direction}")
    return tuple(float(value) for value in values)


def _path_rows(config: ExperimentConfig) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    retention_rows: list[dict[str, Any]] = []
    for architecture in config.architectures:
        for seed in config.seeds:
            inputs, labels = make_dataset(seed, config.samples)
            for condition in ("continuation", "reinit", "washout"):
                for direction in ("forward", "reverse"):
                    for target in config.couplings:
                        schedule = _direction_schedule(direction, target, len(config.couplings))
                        model = initialize_model(architecture, seed)
                        applied_washout = 0
                        for stage, coupling in enumerate(schedule):
                            if condition == "reinit":
                                model = initialize_model(architecture, seed)
                            elif condition == "washout" and stage > 0 and config.washout_updates:
                                train_model(
                                    model,
                                    inputs,
                                    labels,
                                    0.0,
                                    config.washout_updates,
                                    config.learning_rate,
                                )
                                applied_washout += config.washout_updates
                            train_model(
                                model,
                                inputs,
                                labels,
                                coupling,
                                config.path_updates,
                                config.learning_rate,
                            )
                        rows.append(
                            {
                                "architecture": architecture,
                                "seed": seed,
                                "condition": condition,
                                "direction": direction,
                                "coupling": target,
                                "schedule": list(schedule),
                                "updates_per_stage": config.path_updates,
                                "total_updates": len(schedule) * config.path_updates + applied_washout,
                                "washout_updates": applied_washout,
                                **measure_model(model, inputs, labels, seed),
                            }
                        )

            retention_model = initialize_model(architecture, seed)
            train_model(
                retention_model,
                inputs,
                labels,
                1.0,
                config.phase_updates,
                config.learning_rate,
            )
            previous = 0
            for checkpoint in config.retention_checkpoints:
                additional = checkpoint - previous
                if additional:
                    train_model(
                        retention_model,
                        inputs,
                        labels,
                        0.0,
                        additional,
                        config.learning_rate,
                    )
                retention_rows.append(
                    {
                        "architecture": architecture,
                        "seed": seed,
                        "washout_updates": checkpoint,
                        **measure_model(retention_model, inputs, labels, seed),
                    }
                )
                previous = checkpoint
    return rows, retention_rows


def _seed_cluster_bootstrap_interval(
    values: np.ndarray,
    samples: int,
    rng: np.random.Generator,
) -> tuple[float, float]:
    """Bootstrap seed clusters while retaining every architecture within a seed."""

    if values.ndim != 2 or values.shape[0] == 0 or values.shape[1] == 0:
        return float("nan"), float("nan")
    if np.allclose(values, values.flat[0]):
        value = float(values.flat[0])
        return value, value
    seed_count = values.shape[0]
    indices = rng.integers(0, seed_count, size=(samples, seed_count))
    means = values[indices].mean(axis=(1, 2))
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def _paired_differences(rows: list[dict[str, Any]], condition: str) -> dict[float, np.ndarray]:
    condition_rows = [row for row in rows if row["condition"] == condition]
    architectures = sorted({str(row["architecture"]) for row in condition_rows})
    seeds = sorted({int(row["seed"]) for row in condition_rows})
    couplings = sorted({float(row["coupling"]) for row in condition_rows})
    if not architectures or not seeds or not couplings:
        return {}

    differences: dict[float, np.ndarray] = {}
    for coupling in couplings:
        seed_clusters: list[list[float]] = []
        for seed in seeds:
            architecture_differences: list[float] = []
            for architecture in architectures:
                matching = [
                    row
                    for row in condition_rows
                    if row["architecture"] == architecture
                    and int(row["seed"]) == seed
                    and float(row["coupling"]) == coupling
                ]
                if len(matching) != 2:
                    raise ValueError(
                        "each seed/architecture/coupling cell must contain exactly "
                        "one forward and one reverse row"
                    )
                pair = {
                    str(row["direction"]): float(row["causal_specific_effect"])
                    for row in matching
                }
                if set(pair) != {"forward", "reverse"}:
                    raise ValueError(
                        "each seed/architecture/coupling cell must contain forward and reverse rows"
                    )
                architecture_differences.append(pair["forward"] - pair["reverse"])
            seed_clusters.append(architecture_differences)
        differences[coupling] = np.asarray(seed_clusters, dtype=float)
    return differences


def _longest_contiguous(points: list[float], grid: list[float]) -> int:
    point_set = set(points)
    longest = current = 0
    for value in grid:
        if value in point_set:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def _mean_loop_area(differences: dict[float, np.ndarray]) -> float:
    couplings = sorted(differences)
    if len(couplings) < 2:
        return 0.0
    means = [abs(float(np.mean(differences[coupling]))) for coupling in couplings]
    area = 0.0
    for left, right, y_left, y_right in zip(couplings[:-1], couplings[1:], means[:-1], means[1:]):
        area += (right - left) * 0.5 * (y_left + y_right)
    return area


def _path_budgets_match(rows: list[dict[str, Any]]) -> bool:
    groups: dict[tuple[str, str, int, float], dict[str, int]] = {}
    for row in rows:
        if "total_updates" not in row:
            return False
        key = (
            str(row["condition"]),
            str(row["architecture"]),
            int(row["seed"]),
            float(row["coupling"]),
        )
        groups.setdefault(key, {})[str(row["direction"])] = int(row["total_updates"])
    return bool(groups) and all(
        set(pair) == {"forward", "reverse"}
        and pair["forward"] == pair["reverse"]
        for pair in groups.values()
    )


def evaluate_hysteresis(
    rows: list[dict[str, Any]],
    *,
    bootstrap_samples: int,
    bootstrap_seed: int,
) -> dict[str, Any]:
    rng = _rng(bootstrap_seed, 73)
    conditions: dict[str, Any] = {}
    all_couplings = sorted({float(row["coupling"]) for row in rows})
    for condition in ("continuation", "reinit", "washout"):
        differences = _paired_differences(rows, condition)
        pointwise = []
        significant = []
        for coupling in sorted(differences):
            values = differences[coupling]
            low, high = _seed_cluster_bootstrap_interval(
                values,
                bootstrap_samples,
                rng,
            )
            is_significant = low > 0.0 or high < 0.0
            if is_significant:
                significant.append(coupling)
            pointwise.append(
                {
                    "coupling": coupling,
                    "mean_forward_minus_reverse": float(np.mean(values)),
                    "ci95_low": low,
                    "ci95_high": high,
                    "significant": is_significant,
                    "n_seed_clusters": values.shape[0],
                    "architectures_per_seed": values.shape[1],
                }
            )
        conditions[condition] = {
            "loop_area": _mean_loop_area(differences),
            "contiguous_significant_points": _longest_contiguous(significant, all_couplings),
            "significant_couplings": significant,
            "pointwise": pointwise,
        }

    continuation = conditions["continuation"]
    washout = conditions["washout"]
    reinit = conditions["reinit"]
    budget_matched = _path_budgets_match(rows)
    continuation_points = set(continuation["significant_couplings"])
    surviving_points = sorted(continuation_points & set(washout["significant_couplings"]))
    survives_washout = _longest_contiguous(surviving_points, all_couplings) >= 2
    reinit_clear = reinit["contiguous_significant_points"] == 0 and reinit["loop_area"] <= 0.01
    passed = (
        budget_matched
        and continuation["contiguous_significant_points"] >= 2
        and continuation["loop_area"] >= 0.02
        and survives_washout
        and reinit_clear
    )
    return {
        "pass": passed,
        "verdict": "hysteresis" if passed else "no_hysteresis",
        "criteria": (
            "forward/reverse total updates match; bootstrap 95% CI excludes zero over >=2 "
            "contiguous couplings; loop area >=0.02; effect survives washout; and "
            "reinitialization control is clear"
        ),
        "budget_matched": budget_matched,
        "loop_area": continuation["loop_area"],
        "contiguous_significant_points": continuation["contiguous_significant_points"],
        "survives_washout": survives_washout,
        "reinit_control_clear": reinit_clear,
        "conditions": conditions,
    }


def summarize_retention(rows: list[dict[str, Any]]) -> dict[str, Any]:
    checkpoints = sorted({int(row["washout_updates"]) for row in rows})
    curve = []
    for checkpoint in checkpoints:
        values = [
            float(row["causal_specific_effect"])
            for row in rows
            if int(row["washout_updates"]) == checkpoint
        ]
        curve.append(
            {
                "washout_updates": checkpoint,
                "mean_causal_specific_effect": float(np.mean(values)),
                "std_causal_specific_effect": float(np.std(values, ddof=1)) if len(values) > 1 else 0.0,
                "n": len(values),
            }
        )
    half_lives: list[int] = []
    for architecture in sorted({str(row["architecture"]) for row in rows}):
        for seed in sorted({int(row["seed"]) for row in rows if row["architecture"] == architecture}):
            cell = sorted(
                [
                    row
                    for row in rows
                    if row["architecture"] == architecture and int(row["seed"]) == seed
                ],
                key=lambda row: int(row["washout_updates"]),
            )
            initial = max(float(cell[0]["causal_specific_effect"]), 0.0)
            threshold = initial * 0.5
            crossing = next(
                (
                    int(row["washout_updates"])
                    for row in cell[1:]
                    if float(row["causal_specific_effect"]) <= threshold
                ),
                None,
            )
            if crossing is not None:
                half_lives.append(crossing)
    return {
        "curve": curve,
        "median_half_life_updates": float(np.median(half_lives)) if half_lives else None,
        "half_life_observed_fraction": len(half_lives)
        / max(len({(row["architecture"], row["seed"]) for row in rows}), 1),
    }


def aggregate_phase_curve(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    curve: list[dict[str, Any]] = []
    for architecture in sorted({str(row["architecture"]) for row in rows}):
        for coupling in sorted({float(row["coupling"]) for row in rows}):
            cell = [
                row
                for row in rows
                if row["architecture"] == architecture and float(row["coupling"]) == coupling
            ]
            for metric in ORDER_PARAMETERS:
                values = [float(row[metric]) for row in cell]
                curve.append(
                    {
                        "architecture": architecture,
                        "coupling": coupling,
                        "order_parameter": metric,
                        "mean": float(np.mean(values)),
                        "std": float(np.std(values, ddof=1)) if len(values) > 1 else 0.0,
                        "n": len(values),
                    }
                )
    return curve


def run_experiment(config: ExperimentConfig) -> dict[str, Any]:
    config.validate()
    phase_rows = _phase_rows(config)
    path_rows, retention_rows = _path_rows(config)
    bifurcation = evaluate_bifurcation(phase_rows, config)
    hysteresis = evaluate_hysteresis(
        path_rows,
        bootstrap_samples=config.bootstrap_samples,
        bootstrap_seed=101,
    )
    retention = summarize_retention(retention_rows)
    verdicts = {
        (True, True): "bifurcation_with_hysteresis",
        (True, False): "bifurcation_without_hysteresis",
        (False, False): "bifurcation_not_supported_no_hysteresis",
        (False, True): "bifurcation_not_supported_with_path_dependence",
    }
    verdict = verdicts[(bool(bifurcation["pass"]), bool(hysteresis["pass"]))]
    return {
        "kind": "passive_active_phase_map",
        "manifest": {
            **asdict(config),
            "couplings": list(config.couplings),
            "architectures": list(config.architectures),
            "seeds": list(config.seeds),
            "retention_checkpoints": list(config.retention_checkpoints),
            "claim_tier": "controlled local-CPU mechanism diagnostic",
            "raw_artifact_policy": "per-seed cells remain under gitignored artifacts/",
        },
        "phase_rows": phase_rows,
        "hysteresis_rows": path_rows,
        "retention_rows": retention_rows,
        "phase_curve": aggregate_phase_curve(phase_rows),
        "summary": {
            "bifurcation": bifurcation,
            "hysteresis": hysteresis,
            "retention": retention,
            "overall_verdict": verdict,
        },
    }


def public_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": payload["kind"],
        "manifest": payload["manifest"],
        "phase_curve": payload["phase_curve"],
        "summary": payload["summary"],
    }


def _format(value: Any) -> str:
    if isinstance(value, bool):
        return "PASS" if value else "FAIL"
    if value is None:
        return "not observed"
    if isinstance(value, (int, float)):
        return f"{float(value):.4f}"
    return str(value)


def write_report(payload: dict[str, Any], path: Path) -> None:
    public = public_payload(payload)
    summary = public["summary"]
    bifurcation = summary["bifurcation"]
    hysteresis = summary["hysteresis"]
    lines = [
        "# Passive-to-Active Coupling Phase Map",
        "",
        "## Scope",
        "",
        "This is a controlled local-CPU mechanism diagnostic using a synthetic bottleneck",
        "autoencoder plus action head. It is not evidence of a dynamical attractor, biological",
        "criticality, or foundation-model generality.",
        "",
        "Raw per-seed phase, path, and retention cells are generated under",
        "`artifacts/passive_active_phase_map/` and are intentionally not committed.",
        "",
        "## Frozen Gate Verdicts",
        "",
        f"- Bifurcation: **{'PASS' if bifurcation['pass'] else 'FAIL'}** -> `{bifurcation['verdict']}`",
        f"- Hysteresis: **{'PASS' if hysteresis['pass'] else 'FAIL'}** -> `{hysteresis['verdict']}`",
        f"- Overall: **`{summary['overall_verdict']}`**",
        "",
        "A failed bifurcation gate is reported as bifurcation not supported, not as positive proof",
        "of a smooth crossover. A failed hysteresis gate is reported as no registered hysteresis;",
        "neither negative result is upgraded into its alternative by visual inspection.",
        "",
        "## Transition Model Comparison",
        "",
        "| Order parameter | Preferred | Segmented advantage | Critical estimates |",
        "| --- | --- | ---: | --- |",
    ]
    for metric in ORDER_PARAMETERS:
        comparison = bifurcation["model_comparisons"][metric]
        criticals = ", ".join(
            f"{architecture}={value:.3f}"
            for architecture, value in comparison["critical_by_architecture"].items()
        )
        lines.append(
            f"| `{metric}` | {comparison['preferred_model']} | "
            f"{comparison['segmented_advantage']:.3f} | {criticals} |"
        )
    lines.extend(
        [
            "",
            "## Bifurcation Gate Components",
            "",
            f"- Coverage (>=2 architectures, >=5 seeds): {_format(bifurcation['coverage_pass'])}",
            f"- Segmented metrics (need >=2): `{bifurcation['segmented_metrics']}`",
            f"- Critical stability: {_format(bifurcation['critical_stability']['pass'])}",
            f"- Co-located order parameters: {_format(bifurcation['colocated_order_parameters'])}",
            "",
            "## Hysteresis Gate Components",
            "",
            "- Independent bootstrap unit: seed cluster; both architecture rows remain grouped",
            f"- Forward/reverse total budgets matched: {_format(hysteresis['budget_matched'])}",
            f"- Continuation loop area: `{hysteresis['loop_area']:.4f}` (gate >=0.02)",
            f"- Contiguous significant couplings: `{hysteresis['contiguous_significant_points']}` (gate >=2)",
            f"- Survives washout: {_format(hysteresis['survives_washout'])}",
            f"- Reinitialization control clear: {_format(hysteresis['reinit_control_clear'])}",
            "",
            "## Retention",
            "",
            f"- Median half-life: `{_format(summary['retention']['median_half_life_updates'])}` updates",
            f"- Fraction with observed half-life: `{summary['retention']['half_life_observed_fraction']:.3f}`",
            "",
            "## Aggregate Coupling Curves",
            "",
        ]
    )
    for architecture in public["manifest"]["architectures"]:
        lines.extend(
            [
                f"### {architecture}",
                "",
                "| Coupling | Causal specificity | Perturbation failure | Buffer | Geometry gap | Return |",
                "| ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        curve = [row for row in public["phase_curve"] if row["architecture"] == architecture]
        for coupling in public["manifest"]["couplings"]:
            metrics = {
                row["order_parameter"]: row["mean"]
                for row in curve
                if float(row["coupling"]) == float(coupling)
            }
            lines.append(
                f"| {coupling:.2f} | {metrics['causal_specific_effect']:.3f} | "
                f"{metrics['perturbation_failure_rate']:.3f} | {metrics['viability_buffer']:.3f} | "
                f"{metrics['geometry_gap']:.3f} | {metrics['return']:.3f} |"
            )
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_outputs(
    payload: dict[str, Any],
    *,
    raw_output: Path,
    summary_output: Path,
    report_output: Path,
) -> None:
    raw_output.parent.mkdir(parents=True, exist_ok=True)
    summary_output.parent.mkdir(parents=True, exist_ok=True)
    raw_output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary_output.write_text(
        json.dumps(public_payload(payload), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_report(payload, report_output)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preset", choices=sorted(PRESETS), default="registered")
    parser.add_argument(
        "--raw-output",
        type=Path,
        default=Path("artifacts/passive_active_phase_map/registered_cells.json"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("experiments/passive_active_phase_map/results/registered_summary.json"),
    )
    parser.add_argument(
        "--report-output",
        type=Path,
        default=Path("experiments/passive_active_phase_map/results/registered_summary.md"),
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    payload = run_experiment(PRESETS[args.preset])
    write_outputs(
        payload,
        raw_output=args.raw_output,
        summary_output=args.summary_output,
        report_output=args.report_output,
    )
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    print(f"Wrote raw cells to {args.raw_output}")
    print(f"Wrote public summary to {args.summary_output} and {args.report_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
