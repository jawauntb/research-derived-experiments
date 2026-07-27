#!/usr/bin/env python3
"""Core world, geometry, transport, and gate logic for Constraint Swap."""

from __future__ import annotations

import hashlib
import itertools
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Sequence, TypeAlias

import numpy as np


Constraint: TypeAlias = Literal["A", "B", "D"]
Cell: TypeAlias = tuple[int, int]
DecisionUnit: TypeAlias = tuple[Cell, Cell]

MOVE_ACTIONS = ("north", "south", "east", "west", "stay")
BEHAVIOR_ACTIONS = ("reject", "accept")
ACTION_TO_INDEX = {action: index for index, action in enumerate(BEHAVIOR_ACTIONS)}


@dataclass(frozen=True)
class GridTopology:
    """Finite grid with torus or horizontal-cylinder boundary conditions."""

    kind: Literal["torus", "cylinder_x"]
    width: int
    height: int

    def __post_init__(self) -> None:
        if self.kind not in {"torus", "cylinder_x"}:
            raise ValueError(f"Unsupported topology: {self.kind}")
        if self.width < 3 or self.height < 3:
            raise ValueError("Grid dimensions must be at least three")

    @property
    def cells(self) -> tuple[Cell, ...]:
        return tuple(
            (x, y)
            for x in range(self.width)
            for y in range(self.height)
        )

    def step(self, cell: Cell, action: str) -> Cell:
        x, y = cell
        if action == "north":
            candidate = (x, y - 1)
        elif action == "south":
            candidate = (x, y + 1)
        elif action == "east":
            candidate = (x + 1, y)
        elif action == "west":
            candidate = (x - 1, y)
        elif action == "stay":
            return cell
        else:
            raise ValueError(f"Action does not move in the world: {action}")

        next_x, next_y = candidate
        next_x %= self.width
        if self.kind == "torus":
            next_y %= self.height
        else:
            next_y = min(max(next_y, 0), self.height - 1)
        return next_x, next_y

    def signed_delta(self, start: Cell, goal: Cell) -> tuple[int, int]:
        dx = _wrapped_signed_delta(start[0], goal[0], self.width)
        if self.kind == "torus":
            dy = _wrapped_signed_delta(start[1], goal[1], self.height)
        else:
            dy = goal[1] - start[1]
        return dx, dy

    def physical_distance(self, left: Cell, right: Cell) -> int:
        dx, dy = self.signed_delta(left, right)
        return abs(dx) + abs(dy)


def _wrapped_signed_delta(start: int, goal: int, size: int) -> int:
    raw = (goal - start) % size
    if raw > size // 2:
        raw -= size
    return int(raw)


@dataclass(frozen=True)
class ExperimentConfig:
    hidden_size: int
    transport_rank: int
    future_horizon: int
    mature_demonstrations: int
    early_swap_demonstrations: int
    probe_histories: int
    training_steps: int
    batch_size: int
    sequence_length: int
    learning_rate: float
    weight_decay: float
    smoke_seeds: tuple[int, ...]
    confirmatory_seeds: tuple[int, ...]
    bootstrap_resamples: int

    @classmethod
    def registered(cls) -> "ExperimentConfig":
        path = Path(__file__).with_name("registered_design.json")
        payload = json.loads(path.read_text(encoding="utf-8"))
        model = payload["model"]
        confirmatory = payload["confirmatory_seeds"]
        return cls(
            hidden_size=int(model["hidden_size"]),
            transport_rank=int(payload["transport"]["rank"]),
            future_horizon=int(payload["environment"]["future_horizon"]),
            mature_demonstrations=int(model["mature_demonstrations"]),
            early_swap_demonstrations=int(model["early_swap_demonstrations"]),
            probe_histories=int(model["probe_histories"]),
            training_steps=int(model["training_steps"]),
            batch_size=int(model["batch_size"]),
            sequence_length=int(model["sequence_length"]),
            learning_rate=float(model["learning_rate"]),
            weight_decay=float(model["weight_decay"]),
            smoke_seeds=tuple(int(seed) for seed in payload["implementation_smoke_seeds"]),
            confirmatory_seeds=tuple(
                range(int(confirmatory["start"]), int(confirmatory["stop_exclusive"]))
            ),
            bootstrap_resamples=int(payload["inference"]["bootstrap_resamples"]),
        )


def all_decision_units(topology: GridTopology) -> list[DecisionUnit]:
    return [
        (current, goal)
        for current in topology.cells
        for goal in topology.cells
    ]


def constraint_admissible(unit: DecisionUnit, constraint: Constraint) -> bool:
    (x, y), (goal_x, goal_y) = unit
    if constraint == "A":
        return (x + y) % 2 == (goal_x + goal_y) % 2
    if constraint == "B":
        return x % 2 == goal_x % 2
    if constraint == "D":
        return y % 2 == goal_y % 2
    raise ValueError(f"Unknown constraint: {constraint}")


def future_language(
    topology: GridTopology,
    unit: DecisionUnit,
    constraint: Constraint,
    *,
    horizon: int,
) -> np.ndarray:
    """Enumerate the uniformly weighted successful open-loop suffix language."""

    if horizon < 1:
        raise ValueError("horizon must be positive")
    current, goal = unit
    scale = len(MOVE_ACTIONS) ** (-horizon / 2)
    values = np.zeros(len(MOVE_ACTIONS) ** horizon, dtype=np.float64)
    if not constraint_admissible(unit, constraint):
        return values
    for index, suffix in enumerate(itertools.product(MOVE_ACTIONS, repeat=horizon)):
        state = current
        for action in suffix:
            state = topology.step(state, action)
        if state == goal:
            values[index] = scale
    return values


def oracle_action(
    unit: DecisionUnit,
    constraint: Constraint,
) -> int:
    """Return the unique registered behavior target for a decision unit."""

    return ACTION_TO_INDEX["accept" if constraint_admissible(unit, constraint) else "reject"]


def action_histogram(
    units: Sequence[DecisionUnit],
    constraint: Constraint,
) -> tuple[int, ...]:
    counts = [0] * len(BEHAVIOR_ACTIONS)
    for unit in units:
        counts[oracle_action(unit, constraint)] += 1
    return tuple(counts)


def observation(topology: GridTopology, unit: DecisionUnit) -> np.ndarray:
    """Constraint-free, topology-aware observation of a decision unit."""

    (x, y), (goal_x, goal_y) = unit
    dx, dy = topology.signed_delta((x, y), (goal_x, goal_y))
    width_scale = max(topology.width - 1, 1)
    height_scale = max(topology.height - 1, 1)
    return np.asarray(
        [
            x / width_scale,
            y / height_scale,
            goal_x / width_scale,
            goal_y / height_scale,
            dx / max(topology.width // 2, 1),
            dy / max(topology.height - 1 if topology.kind == "cylinder_x" else topology.height // 2, 1),
            float(x == goal_x),
            float(y == goal_y),
            float(y == 0),
            float(y == topology.height - 1),
            float(goal_y == 0),
            float(goal_y == topology.height - 1),
            float((x + y) % 2),
            float((goal_x + goal_y) % 2),
            float(x % 2),
            float(goal_x % 2),
            float(y % 2),
            float(goal_y % 2),
            float(constraint_admissible(unit, "A")),
            float(constraint_admissible(unit, "B")),
            float(constraint_admissible(unit, "D")),
        ],
        dtype=np.float32,
    )


def reachability_rdm(
    topology: GridTopology,
    units: Sequence[DecisionUnit],
    constraint: Constraint,
    *,
    horizon: int,
) -> tuple[np.ndarray, np.ndarray]:
    features = np.stack(
        [
            future_language(topology, unit, constraint, horizon=horizon)
            for unit in units
        ]
    )
    squared_norm = np.sum(features * features, axis=1)
    distances = (
        squared_norm[:, None]
        + squared_norm[None, :]
        - 2.0 * features @ features.T
    )
    distances = np.maximum(distances, 0.0)
    np.fill_diagonal(distances, 0.0)
    return distances, squared_norm


def fit_crossnobis_precision(hidden: np.ndarray, *, shrinkage: float) -> np.ndarray:
    """Fit the registered shrinkage precision matrix on calibration probes."""
    values = np.asarray(hidden, dtype=np.float64)
    if values.ndim != 3:
        raise ValueError("hidden must have shape (units, repeats, features)")
    n_units, n_repeats, n_features = values.shape
    if n_units < 2 or n_repeats < 4 or n_repeats % 2:
        raise ValueError("crossnobis needs >=2 units and an even >=4 repeat count")
    if not 0.0 <= shrinkage <= 1.0:
        raise ValueError("shrinkage must lie in [0, 1]")

    half = n_repeats // 2
    mean_one = values[:, :half].mean(axis=1)
    mean_two = values[:, half:].mean(axis=1)
    residuals = values - values.mean(axis=1, keepdims=True)
    flat_residuals = residuals.reshape(-1, n_features)
    covariance = np.cov(flat_residuals, rowvar=False)
    if n_features == 1:
        covariance = np.asarray([[float(covariance)]])
    scale = float(np.trace(covariance) / n_features)
    shrunk = (1.0 - shrinkage) * covariance + shrinkage * scale * np.eye(n_features)
    return np.linalg.pinv(shrunk + 1e-8 * np.eye(n_features))


def crossnobis_rdm(hidden: np.ndarray, *, precision: np.ndarray) -> np.ndarray:
    """Estimate a split crossnobis RDM using a frozen precision matrix."""

    values = np.asarray(hidden, dtype=np.float64)
    if values.ndim != 3:
        raise ValueError("hidden must have shape (units, repeats, features)")
    n_units, n_repeats, n_features = values.shape
    if n_units < 2 or n_repeats < 4 or n_repeats % 2:
        raise ValueError("crossnobis needs >=2 units and an even >=4 repeat count")
    inverse = np.asarray(precision, dtype=np.float64)
    if inverse.shape != (n_features, n_features):
        raise ValueError("precision must match the hidden feature dimension")

    half = n_repeats // 2
    mean_one = values[:, :half].mean(axis=1)
    mean_two = values[:, half:].mean(axis=1)
    distances = np.zeros((n_units, n_units), dtype=np.float64)
    for left in range(n_units):
        difference_one = mean_one[left] - mean_one
        difference_two = mean_two[left] - mean_two
        distances[left] = np.einsum(
            "ij,jk,ik->i",
            difference_one,
            inverse,
            difference_two,
        )
    distances = 0.5 * (distances + distances.T)
    np.fill_diagonal(distances, 0.0)
    return distances


def _upper_triangle(matrix: np.ndarray) -> np.ndarray:
    values = np.asarray(matrix, dtype=np.float64)
    if values.ndim != 2 or values.shape[0] != values.shape[1]:
        raise ValueError("RDMs must be square matrices")
    indices = np.triu_indices(values.shape[0], k=1)
    return values[indices]


def partial_alignment(
    hidden_rdm: np.ndarray,
    target_rdm: np.ndarray,
    nuisance_rdms: np.ndarray,
) -> dict[str, Any]:
    """Residualize target and hidden RDMs against fixed nuisances."""

    hidden_vector = _upper_triangle(hidden_rdm)
    target_vector = _upper_triangle(target_rdm)
    nuisance = np.asarray(nuisance_rdms, dtype=np.float64)
    if nuisance.ndim == 2:
        nuisance = nuisance[..., None]
    if nuisance.ndim != 3 or nuisance.shape[:2] != hidden_rdm.shape:
        raise ValueError("nuisance RDMs must have shape (units, units, nuisances)")
    nuisance_vectors = np.column_stack(
        [_upper_triangle(nuisance[..., index]) for index in range(nuisance.shape[-1])]
    )
    design = np.column_stack([np.ones(len(hidden_vector)), nuisance_vectors])
    rank = int(np.linalg.matrix_rank(design))
    full_rank = rank == design.shape[1]
    pseudoinverse = np.linalg.pinv(design)
    residual_hidden = hidden_vector - design @ (pseudoinverse @ hidden_vector)
    residual_target = target_vector - design @ (pseudoinverse @ target_vector)
    hidden_norm = float(np.linalg.norm(residual_hidden))
    target_norm = float(np.linalg.norm(residual_target))
    if hidden_norm < 1e-12 or target_norm < 1e-12:
        correlation = 0.0
    else:
        correlation = float(np.corrcoef(residual_hidden, residual_target)[0, 1])
    return {
        "correlation": correlation,
        "residual_hidden_norm": hidden_norm,
        "residual_target_norm": target_norm,
        "design_rank": rank,
        "design_columns": int(design.shape[1]),
        "full_rank": full_rank,
    }


@dataclass(frozen=True)
class LowRankTransport:
    bias: np.ndarray
    matrix: np.ndarray
    rank: int
    calibration_mse: float

    def apply(self, hidden: np.ndarray, *, dose: float = 1.0) -> np.ndarray:
        if dose < 0:
            raise ValueError("dose must be non-negative")
        values = np.asarray(hidden, dtype=np.float64)
        return values + dose * (self.bias + values @ self.matrix)


def fit_low_rank_transport(
    source: np.ndarray,
    target: np.ndarray,
    *,
    rank: int,
    ridge: float,
) -> LowRankTransport:
    """Fit a state-independent low-rank affine delta map."""

    source_values = np.asarray(source, dtype=np.float64)
    target_values = np.asarray(target, dtype=np.float64)
    if source_values.shape != target_values.shape or source_values.ndim != 2:
        raise ValueError("source and target must be same-shaped 2D matrices")
    if not 0 <= rank <= source_values.shape[1]:
        raise ValueError("rank must fit the hidden dimension")
    if ridge < 0:
        raise ValueError("ridge must be non-negative")

    delta = target_values - source_values
    design = np.column_stack([np.ones(len(source_values)), source_values])
    penalty = ridge * np.eye(design.shape[1])
    penalty[0, 0] = 0.0
    coefficients = np.linalg.solve(
        design.T @ design + penalty,
        design.T @ delta,
    )
    bias = coefficients[0]
    full_matrix = coefficients[1:]
    if rank == 0:
        matrix = np.zeros_like(full_matrix)
    else:
        left, singular, right = np.linalg.svd(full_matrix, full_matrices=False)
        matrix = (left[:, :rank] * singular[:rank]) @ right[:rank]
    predicted = source_values + bias + source_values @ matrix
    mse = float(np.mean((predicted - target_values) ** 2))
    return LowRankTransport(
        bias=bias,
        matrix=matrix,
        rank=rank,
        calibration_mse=mse,
    )


def stable_unit_split(
    units: Sequence[DecisionUnit],
    *,
    calibration_fraction: float,
    salt: str,
) -> tuple[np.ndarray, np.ndarray]:
    if not 0.0 < calibration_fraction < 1.0:
        raise ValueError("calibration_fraction must lie in (0, 1)")
    scores = []
    for index, unit in enumerate(units):
        digest = hashlib.sha256(f"{salt}:{unit}".encode()).digest()
        score = int.from_bytes(digest[:8], "big") / 2**64
        scores.append((index, score))
    calibration = np.asarray(
        [index for index, score in scores if score < calibration_fraction],
        dtype=int,
    )
    test = np.asarray(
        [index for index, score in scores if score >= calibration_fraction],
        dtype=int,
    )
    if len(calibration) == 0 or len(test) == 0:
        raise ValueError("stable split produced an empty partition")
    return calibration, test


def paired_bootstrap_interval(
    values: Sequence[float],
    *,
    samples: int,
    seed: int,
    lower_quantile: float = 0.05,
    upper_quantile: float = 0.95,
) -> dict[str, float]:
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 1 or len(array) < 2:
        raise ValueError("bootstrap needs at least two independent values")
    if samples < 1:
        raise ValueError("samples must be positive")
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(array), size=(samples, len(array)))
    means = array[indices].mean(axis=1)
    return {
        "mean": float(array.mean()),
        "lower": float(np.quantile(means, lower_quantile)),
        "upper": float(np.quantile(means, upper_quantile)),
        "n": int(len(array)),
    }


GATE_ORDER = (
    "F0_integrity_identifiability",
    "F1_competence_measurement_sensitivity",
    "G1_constraint_specific_geometry",
    "G2_swap_tracking",
    "G3_selective_impairment",
    "G4_selective_rescue",
    "G5_topology_transport",
)


def evaluate_gates(gates: dict[str, dict[str, Any]]) -> dict[str, Any]:
    missing = [gate for gate in GATE_ORDER if gate not in gates]
    if missing:
        raise ValueError(f"Missing gate verdicts: {missing}")
    unknown = [gate for gate in GATE_ORDER if gates[gate].get("pass") is None]
    failed = [gate for gate in GATE_ORDER if gates[gate].get("pass") is False]
    if unknown:
        decision = "WITHHELD_UNKNOWN_FATAL_GATE"
    elif any(gate in failed for gate in GATE_ORDER[:2]):
        decision = "WITHHELD_INVALID_TEST"
    elif "G1_constraint_specific_geometry" in failed:
        decision = "REJECT_CONSTRAINT_SPECIFIC_DEFORMATION"
    elif "G2_swap_tracking" in failed:
        decision = "REJECT_SWAP_TRACKING"
    elif any(gate in failed for gate in GATE_ORDER[4:6]):
        decision = "REJECT_GEOMETRY_TO_BEHAVIOR_CAUSAL_CHAIN"
    elif "G5_topology_transport" in failed:
        decision = "ACCEPT_PRIMARY_REJECT_TOPOLOGY_TRANSPORT"
    else:
        decision = "ACCEPT_SCOPED_CAUSAL_CLAIM"
    return {
        "decision": decision,
        "all_pass": not unknown and not failed,
        "failed_gates": failed,
        "unknown_gates": unknown,
        "gates": gates,
    }


def finite_number(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False
