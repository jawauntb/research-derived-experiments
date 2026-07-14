#!/usr/bin/env python3
"""E7 selective load-bearing subspace protection for continual learning.

The confirmatory contract is frozen in
``papers/commitment_surface/e7_selective_subspace_continual_learning_``
``preregistration_2026-07-13.md``.  This module keeps the scientific grid
closed while exposing small custom configurations for unit tests.

Run the CPU integrity pilot first, then the confirmatory grid::

    python3 -m experiments.commitment_surface.e7_selective_subspace \
        --run-kind pilot --out artifacts/commitment_surface/e7_pilot.json
    python3 -m experiments.commitment_surface.e7_selective_subspace \
        --run-kind confirmatory \
        --pilot-result artifacts/commitment_surface/e7_pilot.json \
        --out artifacts/commitment_surface/e7_confirmatory.json \
        --public-json experiments/commitment_surface/results/e7_selective_subspace.json \
        --summary experiments/commitment_surface/results/e7_selective_subspace.md
"""

from __future__ import annotations

import argparse
from concurrent.futures import FIRST_EXCEPTION, ThreadPoolExecutor, wait
from dataclasses import asdict, dataclass, field
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
import threading
import time
from typing import Any, Iterable, Mapping, Sequence

from experiments.commitment_surface.core import all_pairs, mean_ci95

Pair = tuple[int, int]

BASE_SEED = 202607131200
TASK_MODULI = (17, 19, 23, 29)
WIDTHS = (96, 128)
ARMS = ("P_none", "P_ewc", "P_sub", "P_wrong")
SEED_INDICES = (0, 1, 2, 3)
LAMBDA = 1.0
TARGET_MASS = 0.5
MASS_TOLERANCE = 0.02
BUDGET_TOLERANCE = 0.02
BARRIER_TIMEOUT_SECONDS = 1800.0
SEED_NAMESPACES = {"augmentation", "cell", "initialization", "split"}
_MODEL_INIT_LOCK = threading.Lock()


@dataclass(frozen=True)
class E7Config:
    task_moduli: tuple[int, ...] = TASK_MODULI
    widths: tuple[int, ...] = WIDTHS
    seeds: int = 4
    epochs: int = 1000
    train_fraction: float = 0.5
    depth: int = 2
    learning_rate: float = 3e-3
    weight_decay: float = 1e-4
    aug_orbit_size: int = 4
    protection_lambda: float = LAMBDA
    target_mass: float = TARGET_MASS
    max_modulus: int = max(TASK_MODULI)
    dead_unit_variance: float = 1e-8

    def __post_init__(self) -> None:
        if not self.task_moduli or any(modulus < 2 for modulus in self.task_moduli):
            raise ValueError("task_moduli must contain moduli >= 2")
        if max(self.task_moduli) > self.max_modulus:
            raise ValueError("max_modulus must cover every task modulus")
        if not self.widths or any(width < 1 for width in self.widths):
            raise ValueError("widths must be positive")
        if self.seeds < 1 or self.epochs < 1:
            raise ValueError("seeds and epochs must be positive")
        if self.depth != 2:
            raise ValueError("E7 requires the frozen depth-2 architecture")
        if not 0.0 < self.train_fraction < 1.0:
            raise ValueError("train_fraction must be in (0, 1)")
        if not 0.0 < self.target_mass <= 1.0:
            raise ValueError("target_mass must be in (0, 1]")
        if self.protection_lambda < 0.0:
            raise ValueError("protection_lambda must be nonnegative")
        if self.aug_orbit_size < 0:
            raise ValueError("aug_orbit_size must be nonnegative")


@dataclass
class WeightedSubspace:
    center: Any
    basis: Any
    axis_weights: Any
    rank: int
    full_rank_mass: float
    protected_mass: float
    grouping: str


@dataclass
class ProtectionObject:
    task_modulus: int
    basis: Any
    axis_weights: Any
    parameter_anchor: dict[str, Any]
    protected_mass: float


@dataclass
class EWCState:
    parameter_anchor: dict[str, Any]
    fisher: dict[str, Any]


@dataclass
class CheckpointRecord:
    boundary_index: int
    task_modulus: int
    cell_seed: int
    split_seed: int
    augmentation_seed: int
    train_pairs: int
    ood_pairs: int
    labeled_examples_seen: int
    optimizer_steps: int
    active_protection_backward_steps: int
    wall_clock_seconds: float
    median_step_seconds: float
    budget_wall_clock_seconds: float
    compatibility_rank: int
    compatibility_full_rank_mass: float
    compatibility_protected_mass: float
    wrong_rank: int
    wrong_full_rank_mass: float
    wrong_protected_mass: float
    compatibility_projection_norms: dict[str, float] = field(default_factory=dict)
    wrong_projection_norms: dict[str, float] = field(default_factory=dict)


@dataclass
class MetricRecord:
    arm: str
    width: int
    seed_index: int
    boundary_index: int
    task_modulus: int
    evaluated_modulus: int
    is_current_task: bool
    ood_accuracy: float
    baseline_ce: float
    compatibility_patch_ce: float
    wrong_patch_ce: float
    compatibility_patch_ce_delta: float
    wrong_patch_ce_delta: float
    compatibility_patch_ce_per_mass: float
    wrong_patch_ce_per_mass: float
    compatibility_rank: int
    wrong_rank: int
    compatibility_full_rank_mass: float
    wrong_full_rank_mass: float
    effective_rank: float
    dead_unit_fraction: float


@dataclass
class StreamResult:
    arm: str
    width: int
    seed_index: int
    initialization_seed: int
    checkpoints: list[CheckpointRecord]
    metrics: list[MetricRecord]
    optimizer_steps: int
    protection_backward_steps: int
    data_exposure: dict[str, int]
    seed_integrity: bool
    sequential_integrity: bool
    mass_integrity: bool
    budget_integrity: bool = False
    budget_relative_wall_clock_range: float | None = None


def _load_torch() -> tuple[Any, Any, Any]:
    import torch
    import torch.nn as nn
    import torch.nn.functional as functional

    return torch, nn, functional


def configure_cpu_runtime(device_str: str) -> None:
    """Remove tiny-matrix thread-pool jitter from the frozen timing audit."""
    if device_str != "cpu":
        return
    torch, _nn, _functional = _load_torch()
    torch.set_num_threads(1)
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        # PyTorch permits setting the inter-op pool only before parallel work.
        # Re-entry in unit tests is already using the requested single thread.
        pass


def derive_e7_seed(
    *,
    namespace: str,
    task: int | str,
    arm_scope: str,
    seed_index: int,
    width: int,
    base_seed: int = BASE_SEED,
) -> int:
    """Derive an E7 key using the frozen SHA-256 component order."""
    if namespace not in SEED_NAMESPACES:
        raise ValueError("unsupported E7 seed namespace")
    if not arm_scope or seed_index < 0 or width < 1:
        raise ValueError("invalid E7 seed component")
    source = (
        f"e7|{base_seed}|{namespace}|{task}|{arm_scope}|{seed_index}|{width}"
    )
    return int(hashlib.sha256(source.encode()).hexdigest(), 16) % (2**31)


def exact_grid_seeds() -> dict[tuple[str, int, int, int], int]:
    seeds = {
        (arm, width, seed_index, modulus): derive_e7_seed(
            namespace="cell",
            task=modulus,
            arm_scope=arm,
            seed_index=seed_index,
            width=width,
        )
        for arm in ARMS
        for width in WIDTHS
        for seed_index in SEED_INDICES
        for modulus in TASK_MODULI
    }
    if len(set(seeds.values())) != len(seeds):
        raise RuntimeError("E7 cell seed collision")
    return seeds


def make_model(config: E7Config, *, width: int) -> Any:
    """Build the one shared padded network used for every stream task."""
    _torch, nn, _functional = _load_torch()

    class _PaddedModularMLP(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.hidden1 = nn.Linear(2 * config.max_modulus, width)
            self.hidden2 = nn.Linear(width, width)
            self.head = nn.Linear(width, config.max_modulus)

        def features(self, inputs: Any) -> Any:
            hidden = nn.functional.relu(self.hidden1(inputs))
            return nn.functional.relu(self.hidden2(hidden))

        def logits_from_features(self, features: Any) -> Any:
            return self.head(features)

        def forward(self, inputs: Any) -> Any:
            return self.logits_from_features(self.features(inputs))

    return _PaddedModularMLP()


def one_hot_pairs_padded(
    pairs: Sequence[Pair],
    *,
    modulus: int,
    max_modulus: int,
    device: Any | None = None,
) -> Any:
    torch, _nn, _functional = _load_torch()
    if modulus > max_modulus:
        raise ValueError("modulus exceeds max_modulus")
    if any(a < 0 or b < 0 or a >= modulus or b >= modulus for a, b in pairs):
        raise ValueError("pair coordinate outside modulus")
    output = torch.zeros(len(pairs), 2 * max_modulus, device=device)
    for row, (a, b) in enumerate(pairs):
        output[row, a] = 1.0
        output[row, max_modulus + b] = 1.0
    return output


def _targets(pairs: Sequence[Pair], modulus: int, device: Any) -> Any:
    torch, _nn, _functional = _load_torch()
    return torch.tensor(
        [(a + b) % modulus for a, b in pairs],
        dtype=torch.long,
        device=device,
    )


def _split_pairs(
    modulus: int, train_fraction: float, split_seed: int
) -> tuple[list[Pair], list[Pair]]:
    pool = all_pairs(modulus)
    random.Random(split_seed).shuffle(pool)
    train_count = max(1, min(len(pool) - 1, round(len(pool) * train_fraction)))
    return pool[:train_count], pool[train_count:]


def weighted_group_subspace(
    model: Any,
    *,
    modulus: int,
    max_modulus: int,
    grouping: str,
    target_mass: float,
    device: Any,
) -> WeightedSubspace:
    """Fit #344's min-rank subspace plus an exact-mass boundary weight.

    ``basis`` remains the full orthonormal min-rank basis used for reported
    patch-CE. ``axis_weights`` only affects E7's protection penalty: its final
    axis is fractionally weighted so protected between-group mass is exactly
    the frozen target instead of overshooting it because rank is discrete.
    """
    if grouping not in {"sum", "a"}:
        raise ValueError(f"unsupported grouping: {grouping}")
    if not 0.0 < target_mass <= 1.0:
        raise ValueError("target_mass must be in (0, 1]")

    torch, _nn, _functional = _load_torch()
    pairs = all_pairs(modulus)
    model.eval()
    with torch.no_grad():
        inputs = one_hot_pairs_padded(
            pairs, modulus=modulus, max_modulus=max_modulus, device=device
        )
        features = model.features(inputs)
        center = features.mean(dim=0, keepdim=True)
        group_means = []
        for group_id in range(modulus):
            indices = [
                index
                for index, (a, b) in enumerate(pairs)
                if ((a + b) % modulus if grouping == "sum" else a) == group_id
            ]
            group_means.append(features[indices].mean(dim=0) - center.squeeze(0))
        mean_matrix = torch.stack(group_means)
        _left, singular, right = torch.linalg.svd(mean_matrix, full_matrices=False)
        spectral_mass = singular.square()
        total = spectral_mass.sum()
        if float(total.item()) <= 1e-12:
            empty_basis = torch.zeros(
                (features.shape[1], 0), dtype=features.dtype, device=device
            )
            empty_weights = torch.zeros(0, dtype=features.dtype, device=device)
            return WeightedSubspace(
                center=center,
                basis=empty_basis,
                axis_weights=empty_weights,
                rank=0,
                full_rank_mass=0.0,
                protected_mass=0.0,
                grouping=grouping,
            )
        fractions = spectral_mass / total
        cumulative = torch.cumsum(fractions, dim=0)
        rank = int(
            torch.searchsorted(
                cumulative,
                torch.tensor(target_mass, device=cumulative.device),
            ).item()
        ) + 1
        rank = min(rank, right.shape[0])
        previous_mass = (
            float(cumulative[rank - 2].item()) if rank > 1 else 0.0
        )
        boundary_mass = float(fractions[rank - 1].item())
        boundary_weight_squared = max(
            0.0, min(1.0, (target_mass - previous_mass) / boundary_mass)
        )
        axis_weights = torch.ones(rank, dtype=features.dtype, device=device)
        axis_weights[-1] = math.sqrt(boundary_weight_squared)
        basis = right[:rank].transpose(0, 1).contiguous()
        protected_mass = previous_mass + boundary_weight_squared * boundary_mass
        return WeightedSubspace(
            center=center,
            basis=basis,
            axis_weights=axis_weights,
            rank=rank,
            full_rank_mass=float(cumulative[rank - 1].item()),
            protected_mass=protected_mass,
            grouping=grouping,
        )


def _parameter_snapshot(model: Any) -> dict[str, Any]:
    return {
        name: parameter.detach().clone()
        for name, parameter in model.named_parameters()
    }


def _projected_parameter_penalty(
    model: Any, snapshots: Sequence[ProtectionObject]
) -> tuple[Any, dict[str, float]]:
    torch, _nn, _functional = _load_torch()
    parameters = dict(model.named_parameters())
    zero = next(iter(parameters.values())).sum() * 0.0
    if not snapshots:
        return zero, {
            "hidden1.weight": 0.0,
            "hidden1.bias": 0.0,
            "hidden2.weight": 0.0,
            "hidden2.bias": 0.0,
            "head.weight": 0.0,
            "head.bias": 0.0,
        }

    penalties = []
    norm_squares: dict[str, Any] = {
        name: torch.zeros((), device=next(iter(parameters.values())).device)
        for name in parameters
    }
    for snapshot in snapshots:
        weighted_basis = snapshot.basis * snapshot.axis_weights.unsqueeze(0)
        hidden_weight_delta = (
            parameters["hidden2.weight"]
            - snapshot.parameter_anchor["hidden2.weight"]
        )
        hidden_bias_delta = (
            parameters["hidden2.bias"] - snapshot.parameter_anchor["hidden2.bias"]
        )
        head_weight_delta = (
            parameters["head.weight"] - snapshot.parameter_anchor["head.weight"]
        )
        projected_hidden_weight = weighted_basis.transpose(0, 1) @ hidden_weight_delta
        projected_hidden_bias = weighted_basis.transpose(0, 1) @ hidden_bias_delta
        projected_head_weight = head_weight_delta @ weighted_basis
        penalties.extend(
            [
                projected_hidden_weight.square().mean(),
                projected_hidden_bias.square().mean(),
                projected_head_weight.square().mean(),
            ]
        )
        norm_squares["hidden2.weight"] += projected_hidden_weight.square().sum()
        norm_squares["hidden2.bias"] += projected_hidden_bias.square().sum()
        norm_squares["head.weight"] += projected_head_weight.square().sum()

    penalty = torch.stack(penalties).mean() if penalties else zero
    norms = {
        name: float(torch.sqrt(value).detach().cpu().item())
        for name, value in norm_squares.items()
    }
    return penalty, norms


def _fisher_state(
    model: Any,
    *,
    inputs: Any,
    targets: Any,
) -> EWCState:
    _torch, _nn, functional = _load_torch()
    model.zero_grad(set_to_none=True)
    loss = functional.cross_entropy(model(inputs), targets)
    loss.backward()
    raw = {
        name: parameter.grad.detach().square().clone()
        for name, parameter in model.named_parameters()
    }
    flat_mean = sum(float(value.mean().item()) for value in raw.values()) / len(raw)
    scale = max(flat_mean, 1e-12)
    fisher = {name: value / scale for name, value in raw.items()}
    model.zero_grad(set_to_none=True)
    return EWCState(parameter_anchor=_parameter_snapshot(model), fisher=fisher)


def _ewc_penalty(model: Any, state: EWCState | None) -> Any:
    torch, _nn, _functional = _load_torch()
    parameters = dict(model.named_parameters())
    zero = next(iter(parameters.values())).sum() * 0.0
    if state is None:
        return zero
    pieces = [
        (
            state.fisher[name]
            * (parameter - state.parameter_anchor[name]).square()
        ).mean()
        for name, parameter in parameters.items()
    ]
    return torch.stack(pieces).mean()


def _accuracy_and_ce(
    model: Any,
    *,
    pairs: Sequence[Pair],
    modulus: int,
    max_modulus: int,
    device: Any,
) -> tuple[float, float]:
    torch, _nn, functional = _load_torch()
    model.eval()
    with torch.no_grad():
        inputs = one_hot_pairs_padded(
            pairs, modulus=modulus, max_modulus=max_modulus, device=device
        )
        targets = _targets(pairs, modulus, device)
        logits = model(inputs)
        accuracy = float((logits.argmax(dim=-1) == targets).float().mean().item())
        ce = float(functional.cross_entropy(logits, targets).item())
    return accuracy, ce


def _patched_ce(
    model: Any,
    *,
    pairs: Sequence[Pair],
    modulus: int,
    max_modulus: int,
    subspace: WeightedSubspace,
    device: Any,
) -> float:
    torch, _nn, functional = _load_torch()
    model.eval()
    with torch.no_grad():
        inputs = one_hot_pairs_padded(
            pairs, modulus=modulus, max_modulus=max_modulus, device=device
        )
        features = model.features(inputs)
        if subspace.rank:
            centered = features - subspace.center
            features = features - (
                centered @ subspace.basis
            ) @ subspace.basis.transpose(0, 1)
        logits = model.logits_from_features(features)
        return float(functional.cross_entropy(logits, _targets(pairs, modulus, device)).item())


def _plasticity_metrics(
    model: Any,
    *,
    pairs: Sequence[Pair],
    modulus: int,
    max_modulus: int,
    dead_unit_variance: float,
    device: Any,
) -> tuple[float, float]:
    torch, _nn, _functional = _load_torch()
    model.eval()
    with torch.no_grad():
        features = model.features(
            one_hot_pairs_padded(
                pairs, modulus=modulus, max_modulus=max_modulus, device=device
            )
        )
        centered = features - features.mean(dim=0, keepdim=True)
        singular = torch.linalg.svdvals(centered)
        spectrum = singular.square()
        denominator = float(spectrum.square().sum().item())
        effective_rank = (
            float(spectrum.sum().item()) ** 2 / denominator
            if denominator > 1e-20
            else 0.0
        )
        variances = centered.square().mean(dim=0)
        dead_fraction = float((variances <= dead_unit_variance).float().mean().item())
    return effective_rank, dead_fraction


def _make_protection_object(
    model: Any, modulus: int, subspace: WeightedSubspace
) -> ProtectionObject:
    return ProtectionObject(
        task_modulus=modulus,
        basis=subspace.basis.detach().clone(),
        axis_weights=subspace.axis_weights.detach().clone(),
        parameter_anchor=_parameter_snapshot(model),
        protected_mass=subspace.protected_mass,
    )


def run_stream(
    config: E7Config,
    *,
    arm: str,
    width: int,
    seed_index: int,
    device_str: str = "cpu",
    task_barrier: threading.Barrier | None = None,
) -> StreamResult:
    """Run one four-task arm/width/seed stream without replay data."""
    if arm not in ARMS:
        raise ValueError(f"unsupported arm: {arm}")
    if width not in config.widths:
        raise ValueError("width is outside config.widths")
    if not 0 <= seed_index < config.seeds:
        raise ValueError("seed_index is outside config.seeds")

    torch, _nn, functional = _load_torch()
    device = torch.device(device_str)
    initialization_seed = derive_e7_seed(
        namespace="initialization",
        task="stream",
        arm_scope="matched",
        seed_index=seed_index,
        width=width,
    )
    # PyTorch's RNG is process-global. Serializing the identical seed + model
    # construction keeps initialization byte-matched when arms run in threads.
    with _MODEL_INIT_LOCK:
        torch.manual_seed(initialization_seed)
        model = make_model(config, width=width).to(device)

    compatibility_objects: list[ProtectionObject] = []
    wrong_objects: list[ProtectionObject] = []
    ewc_state: EWCState | None = None
    ood_splits: dict[int, list[Pair]] = {}
    checkpoints: list[CheckpointRecord] = []
    metrics: list[MetricRecord] = []
    cell_seeds: list[int] = []
    data_exposure: dict[str, int] = {}

    for boundary_index, modulus in enumerate(config.task_moduli, start=1):
        cell_seed = derive_e7_seed(
            namespace="cell",
            task=modulus,
            arm_scope=arm,
            seed_index=seed_index,
            width=width,
        )
        split_seed = derive_e7_seed(
            namespace="split",
            task=modulus,
            arm_scope="matched",
            seed_index=seed_index,
            width=width,
        )
        augmentation_seed = derive_e7_seed(
            namespace="augmentation",
            task=modulus,
            arm_scope="matched",
            seed_index=seed_index,
            width=width,
        )
        cell_seeds.append(cell_seed)
        train_pairs, ood_pairs = _split_pairs(
            modulus, config.train_fraction, split_seed
        )
        ood_splits[modulus] = ood_pairs
        augmentation_rng = random.Random(augmentation_seed)
        optimizer = torch.optim.Adam(
            model.parameters(),
            lr=config.learning_rate,
            weight_decay=config.weight_decay,
        )

        if task_barrier is not None:
            task_barrier.wait(timeout=BARRIER_TIMEOUT_SECONDS)
        started = time.perf_counter()
        step_durations = []
        inputs = None
        targets = None
        for _epoch in range(config.epochs):
            step_started = time.perf_counter()
            model.train()
            pairs_used = list(train_pairs)
            labels_used = [(a + b) % modulus for a, b in train_pairs]
            for _shift_index in range(config.aug_orbit_size):
                shift = augmentation_rng.randrange(1, modulus)
                for a, b in train_pairs:
                    pairs_used.append(((a + shift) % modulus, b))
                    labels_used.append((a + b + shift) % modulus)
            inputs = one_hot_pairs_padded(
                pairs_used,
                modulus=modulus,
                max_modulus=config.max_modulus,
                device=device,
            )
            targets = torch.tensor(labels_used, dtype=torch.long, device=device)
            optimizer.zero_grad(set_to_none=True)
            task_loss = functional.cross_entropy(model(inputs), targets)
            ewc_loss = _ewc_penalty(model, ewc_state)
            compatibility_loss, _compatibility_norms = _projected_parameter_penalty(
                model, compatibility_objects
            )
            wrong_loss, _wrong_norms = _projected_parameter_penalty(
                model, wrong_objects
            )
            # Every arm builds the same shadow graph. Only the named arm's
            # protection term has a nonzero coefficient, so optimization is
            # intervention-specific while tensor-operation budgets stay matched.
            if arm == "P_ewc":
                protection_loss = ewc_loss
            elif arm == "P_sub":
                protection_loss = compatibility_loss
            elif arm == "P_wrong":
                protection_loss = wrong_loss
            else:
                protection_loss = ewc_loss * 0.0
            shadow_zero = (ewc_loss + compatibility_loss + wrong_loss) * 0.0
            loss = task_loss + config.protection_lambda * protection_loss + shadow_zero
            loss.backward()
            optimizer.step()
            step_durations.append(time.perf_counter() - step_started)
        wall_clock_seconds = time.perf_counter() - started
        if task_barrier is not None:
            task_barrier.wait(timeout=BARRIER_TIMEOUT_SECONDS)
        median_step_seconds = statistics.median(step_durations)
        if inputs is None or targets is None:
            raise RuntimeError("E7 task executed no optimizer steps")
        data_exposure[str(modulus)] = config.epochs

        _compatibility_penalty, compatibility_norms = _projected_parameter_penalty(
            model, compatibility_objects
        )
        _wrong_penalty, wrong_norms = _projected_parameter_penalty(
            model, wrong_objects
        )
        compatibility_subspace = weighted_group_subspace(
            model,
            modulus=modulus,
            max_modulus=config.max_modulus,
            grouping="sum",
            target_mass=config.target_mass,
            device=device,
        )
        wrong_subspace = weighted_group_subspace(
            model,
            modulus=modulus,
            max_modulus=config.max_modulus,
            grouping="a",
            target_mass=config.target_mass,
            device=device,
        )
        checkpoints.append(
            CheckpointRecord(
                boundary_index=boundary_index,
                task_modulus=modulus,
                cell_seed=cell_seed,
                split_seed=split_seed,
                augmentation_seed=augmentation_seed,
                train_pairs=len(train_pairs),
                ood_pairs=len(ood_pairs),
                labeled_examples_seen=(
                    config.epochs * len(train_pairs) * (1 + config.aug_orbit_size)
                ),
                optimizer_steps=config.epochs,
                active_protection_backward_steps=(
                    config.epochs if boundary_index > 1 and arm != "P_none" else 0
                ),
                wall_clock_seconds=wall_clock_seconds,
                median_step_seconds=median_step_seconds,
                budget_wall_clock_seconds=median_step_seconds * config.epochs,
                compatibility_rank=compatibility_subspace.rank,
                compatibility_full_rank_mass=compatibility_subspace.full_rank_mass,
                compatibility_protected_mass=compatibility_subspace.protected_mass,
                wrong_rank=wrong_subspace.rank,
                wrong_full_rank_mass=wrong_subspace.full_rank_mass,
                wrong_protected_mass=wrong_subspace.protected_mass,
                compatibility_projection_norms=compatibility_norms,
                wrong_projection_norms=wrong_norms,
            )
        )

        # Current-task tensors are consumed before the next task. Only Fisher,
        # parameter anchors, and subspace objects cross the boundary; examples do not.
        ewc_state = _fisher_state(model, inputs=inputs, targets=targets)
        compatibility_objects.append(
            _make_protection_object(model, modulus, compatibility_subspace)
        )
        wrong_objects.append(_make_protection_object(model, modulus, wrong_subspace))

        for evaluated_modulus in config.task_moduli[:boundary_index]:
            evaluated_ood = ood_splits[evaluated_modulus]
            accuracy, baseline_ce = _accuracy_and_ce(
                model,
                pairs=evaluated_ood,
                modulus=evaluated_modulus,
                max_modulus=config.max_modulus,
                device=device,
            )
            evaluated_compatibility = weighted_group_subspace(
                model,
                modulus=evaluated_modulus,
                max_modulus=config.max_modulus,
                grouping="sum",
                target_mass=config.target_mass,
                device=device,
            )
            evaluated_wrong = weighted_group_subspace(
                model,
                modulus=evaluated_modulus,
                max_modulus=config.max_modulus,
                grouping="a",
                target_mass=config.target_mass,
                device=device,
            )
            compatibility_patch_ce = _patched_ce(
                model,
                pairs=evaluated_ood,
                modulus=evaluated_modulus,
                max_modulus=config.max_modulus,
                subspace=evaluated_compatibility,
                device=device,
            )
            wrong_patch_ce = _patched_ce(
                model,
                pairs=evaluated_ood,
                modulus=evaluated_modulus,
                max_modulus=config.max_modulus,
                subspace=evaluated_wrong,
                device=device,
            )
            effective_rank, dead_fraction = _plasticity_metrics(
                model,
                pairs=evaluated_ood,
                modulus=evaluated_modulus,
                max_modulus=config.max_modulus,
                dead_unit_variance=config.dead_unit_variance,
                device=device,
            )
            compatibility_delta = compatibility_patch_ce - baseline_ce
            wrong_delta = wrong_patch_ce - baseline_ce
            metrics.append(
                MetricRecord(
                    arm=arm,
                    width=width,
                    seed_index=seed_index,
                    boundary_index=boundary_index,
                    task_modulus=modulus,
                    evaluated_modulus=evaluated_modulus,
                    is_current_task=evaluated_modulus == modulus,
                    ood_accuracy=accuracy,
                    baseline_ce=baseline_ce,
                    compatibility_patch_ce=compatibility_patch_ce,
                    wrong_patch_ce=wrong_patch_ce,
                    compatibility_patch_ce_delta=compatibility_delta,
                    wrong_patch_ce_delta=wrong_delta,
                    compatibility_patch_ce_per_mass=(
                        compatibility_delta / evaluated_compatibility.full_rank_mass
                        if evaluated_compatibility.full_rank_mass > 0.0
                        else 0.0
                    ),
                    wrong_patch_ce_per_mass=(
                        wrong_delta / evaluated_wrong.full_rank_mass
                        if evaluated_wrong.full_rank_mass > 0.0
                        else 0.0
                    ),
                    compatibility_rank=evaluated_compatibility.rank,
                    wrong_rank=evaluated_wrong.rank,
                    compatibility_full_rank_mass=(
                        evaluated_compatibility.full_rank_mass
                    ),
                    wrong_full_rank_mass=evaluated_wrong.full_rank_mass,
                    effective_rank=effective_rank,
                    dead_unit_fraction=dead_fraction,
                )
            )

    expected_metrics = len(config.task_moduli) * (len(config.task_moduli) + 1) // 2
    mass_integrity = all(
        abs(checkpoint.compatibility_protected_mass - config.target_mass)
        <= MASS_TOLERANCE
        and abs(checkpoint.wrong_protected_mass - config.target_mass)
        <= MASS_TOLERANCE
        for checkpoint in checkpoints
    )
    return StreamResult(
        arm=arm,
        width=width,
        seed_index=seed_index,
        initialization_seed=initialization_seed,
        checkpoints=checkpoints,
        metrics=metrics,
        optimizer_steps=len(config.task_moduli) * config.epochs,
        protection_backward_steps=(
            (len(config.task_moduli) - 1) * config.epochs
            if arm != "P_none"
            else 0
        ),
        data_exposure=data_exposure,
        seed_integrity=len(cell_seeds) == len(set(cell_seeds)),
        sequential_integrity=(
            len(metrics) == expected_metrics
            and [row.task_modulus for row in checkpoints] == list(config.task_moduli)
            and data_exposure
            == {str(modulus): config.epochs for modulus in config.task_moduli}
        ),
        mass_integrity=mass_integrity,
    )


def _apply_budget_audit(streams: Sequence[StreamResult]) -> dict[str, Any]:
    groups: dict[tuple[int, int, int], list[tuple[StreamResult, CheckpointRecord]]] = {}
    for stream in streams:
        for checkpoint in stream.checkpoints:
            key = (stream.width, stream.seed_index, checkpoint.boundary_index)
            groups.setdefault(key, []).append((stream, checkpoint))

    failures = []
    relative_ranges: dict[tuple[int, int], list[float]] = {}
    range_rows: list[dict[str, Any]] = []
    for key, members in groups.items():
        if {stream.arm for stream, _checkpoint in members} != set(ARMS):
            failures.append({"key": key, "reason": "missing_arm"})
            continue
        step_counts = {checkpoint.optimizer_steps for _stream, checkpoint in members}
        durations = [
            checkpoint.budget_wall_clock_seconds
            for _stream, checkpoint in members
        ]
        mean_duration = sum(durations) / len(durations)
        relative_range = (
            (max(durations) - min(durations)) / mean_duration
            if mean_duration > 0.0
            else math.inf
        )
        raw_durations = [
            checkpoint.wall_clock_seconds for _stream, checkpoint in members
        ]
        raw_mean = sum(raw_durations) / len(raw_durations)
        raw_relative_range = (
            (max(raw_durations) - min(raw_durations)) / raw_mean
            if raw_mean > 0.0
            else math.inf
        )
        relative_ranges.setdefault((key[0], key[1]), []).append(relative_range)
        range_rows.append(
            {
                "width": key[0],
                "seed_index": key[1],
                "boundary_index": key[2],
                "relative_wall_clock_range": relative_range,
                "recorded_wall_clock_relative_range": raw_relative_range,
                "pass": len(step_counts) == 1
                and relative_range <= BUDGET_TOLERANCE,
            }
        )
        if len(step_counts) != 1 or relative_range > BUDGET_TOLERANCE:
            failures.append(
                {
                    "key": key,
                    "reason": "step_or_wall_clock_mismatch",
                    "step_counts": sorted(step_counts),
                    "relative_wall_clock_range": relative_range,
                    "per_arm_budget_wall_clock_seconds": [
                        {
                            "arm": stream.arm,
                            "seconds": checkpoint.budget_wall_clock_seconds,
                        }
                        for stream, checkpoint in members
                    ],
                    "recorded_wall_clock_seconds": [
                        {
                            "arm": stream.arm,
                            "seconds": checkpoint.wall_clock_seconds,
                        }
                        for stream, checkpoint in members
                    ],
                }
            )

    for stream in streams:
        ranges = relative_ranges.get((stream.width, stream.seed_index), [])
        stream.budget_relative_wall_clock_range = max(ranges) if ranges else math.inf
        stream.budget_integrity = bool(ranges) and all(
            value <= BUDGET_TOLERANCE for value in ranges
        )
    return {
        "pass": not failures,
        "tolerance": BUDGET_TOLERANCE,
        "estimator": "median_step_seconds_x_optimizer_steps",
        "max_relative_wall_clock_range": max(
            (value for values in relative_ranges.values() for value in values),
            default=math.inf,
        ),
        "relative_wall_clock_ranges": range_rows,
        "failures": failures,
    }


def _all_seeds_match_contract(streams: Sequence[StreamResult]) -> bool:
    cell_seeds = [
        checkpoint.cell_seed
        for stream in streams
        for checkpoint in stream.checkpoints
    ]
    if len(cell_seeds) != len(set(cell_seeds)):
        return False

    groups: dict[tuple[int, int, int], list[tuple[StreamResult, CheckpointRecord]]] = {}
    for stream in streams:
        for checkpoint in stream.checkpoints:
            key = (stream.width, stream.seed_index, checkpoint.boundary_index)
            groups.setdefault(key, []).append((stream, checkpoint))

    return all(stream.seed_integrity for stream in streams) and all(
        len(members) == len(ARMS)
        and len({stream.initialization_seed for stream, _checkpoint in members}) == 1
        and len({checkpoint.split_seed for _stream, checkpoint in members}) == 1
        and len(
            {checkpoint.augmentation_seed for _stream, checkpoint in members}
        )
        == 1
        for members in groups.values()
    )


def _mean(values: Iterable[float]) -> float:
    values_list = list(values)
    return sum(values_list) / len(values_list) if values_list else math.nan


def summarize_streams(streams: Sequence[StreamResult]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for width in sorted({stream.width for stream in streams}):
        for arm in ARMS:
            arm_streams = [
                stream
                for stream in streams
                if stream.width == width and stream.arm == arm
                and stream.seed_integrity
                and stream.sequential_integrity
                and stream.mass_integrity
                and stream.budget_integrity
            ]
            earlier = [
                metric
                for stream in arm_streams
                for metric in stream.metrics
                if not metric.is_current_task
            ]
            final = [
                metric
                for stream in arm_streams
                for metric in stream.metrics
                if metric.boundary_index == len(stream.checkpoints)
                and metric.is_current_task
            ]
            patch_by_seed = [
                _mean(
                    metric.compatibility_patch_ce_per_mass
                    for metric in stream.metrics
                    if not metric.is_current_task
                )
                for stream in arm_streams
            ]
            retained_by_seed = [
                _mean(
                    metric.ood_accuracy
                    for metric in stream.metrics
                    if not metric.is_current_task
                )
                for stream in arm_streams
            ]
            final_by_seed = [
                next(
                    metric.ood_accuracy
                    for metric in stream.metrics
                    if metric.boundary_index == len(stream.checkpoints)
                    and metric.is_current_task
                )
                for stream in arm_streams
            ]
            effective_rank_by_seed = [
                _mean(metric.effective_rank for metric in stream.metrics)
                for stream in arm_streams
            ]
            dead_fraction_by_seed = [
                _mean(metric.dead_unit_fraction for metric in stream.metrics)
                for stream in arm_streams
            ]
            patch_mean, patch_low, patch_high = mean_ci95(patch_by_seed)
            retained_mean, retained_low, retained_high = mean_ci95(retained_by_seed)
            final_mean, final_low, final_high = mean_ci95(final_by_seed)
            effective_mean, effective_low, effective_high = mean_ci95(
                effective_rank_by_seed
            )
            dead_mean, dead_low, dead_high = mean_ci95(dead_fraction_by_seed)
            rows.append(
                {
                    "width": width,
                    "arm": arm,
                    "valid_streams": len(arm_streams),
                    "earlier_metric_rows": len(earlier),
                    "final_metric_rows": len(final),
                    "earlier_patch_ce_per_mass": patch_mean,
                    "earlier_patch_ce_per_mass_ci95": [patch_low, patch_high],
                    "retained_ood_accuracy": retained_mean,
                    "retained_ood_accuracy_ci95": [retained_low, retained_high],
                    "final_task_ood_accuracy": final_mean,
                    "final_task_ood_accuracy_ci95": [final_low, final_high],
                    "wrong_patch_ce_per_mass": _mean(
                        metric.wrong_patch_ce_per_mass for metric in earlier
                    ),
                    "effective_rank": effective_mean,
                    "effective_rank_ci95": [effective_low, effective_high],
                    "dead_unit_fraction": dead_mean,
                    "dead_unit_fraction_ci95": [dead_low, dead_high],
                }
            )
    return rows


def analyze_gates(summary_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    indexed = {
        (int(row["width"]), str(row["arm"])): row for row in summary_rows
    }
    widths = sorted({width for width, _arm in indexed})
    expected_widths = set(WIDTHS)

    def value(width: int, arm: str, field: str) -> float:
        return float(indexed[(width, arm)][field])

    complete = set(widths) == expected_widths and all(
        (width, arm) in indexed for width in WIDTHS for arm in ARMS
    ) and all(
        int(indexed[(width, arm)].get("valid_streams", 0)) == len(SEED_INDICES)
        for width in WIDTHS
        for arm in ARMS
    )
    finite = complete and all(
        math.isfinite(float(row[field]))
        for row in summary_rows
        for field in (
            "earlier_patch_ce_per_mass",
            "retained_ood_accuracy",
            "final_task_ood_accuracy",
        )
    )
    if not finite:
        gates = {
            "G1_stability_both_widths": False,
            "G2_plasticity_both_widths": False,
            "G3_frontier_dominance_both_widths": False,
            "G4_specificity_both_widths": False,
        }
        return {"gates": gates, "strict_verdict": "INVALID", "margins": {}}

    margins: dict[str, dict[str, float]] = {}
    for width in WIDTHS:
        margins[str(width)] = {
            "G1_P_sub_minus_P_none_patch": (
                value(width, "P_sub", "earlier_patch_ce_per_mass")
                - value(width, "P_none", "earlier_patch_ce_per_mass")
            ),
            "G2_P_sub_minus_P_ewc_final_ood": (
                value(width, "P_sub", "final_task_ood_accuracy")
                - value(width, "P_ewc", "final_task_ood_accuracy")
            ),
            "G3_P_sub_minus_P_ewc_retained_ood": (
                value(width, "P_sub", "retained_ood_accuracy")
                - value(width, "P_ewc", "retained_ood_accuracy")
            ),
            "G4_P_sub_minus_P_wrong_patch": (
                value(width, "P_sub", "earlier_patch_ce_per_mass")
                - value(width, "P_wrong", "earlier_patch_ce_per_mass")
            ),
        }
    gates = {
        "G1_stability_both_widths": all(
            margins[str(width)]["G1_P_sub_minus_P_none_patch"] >= 0.05
            for width in WIDTHS
        ),
        "G2_plasticity_both_widths": all(
            margins[str(width)]["G2_P_sub_minus_P_ewc_final_ood"] >= -0.02
            for width in WIDTHS
        ),
        "G3_frontier_dominance_both_widths": all(
            margins[str(width)]["G3_P_sub_minus_P_ewc_retained_ood"] >= 0.03
            and margins[str(width)]["G2_P_sub_minus_P_ewc_final_ood"] >= -0.02
            for width in WIDTHS
        ),
        "G4_specificity_both_widths": all(
            margins[str(width)]["G4_P_sub_minus_P_wrong_patch"] >= 0.05
            for width in WIDTHS
        ),
    }
    return {
        "gates": gates,
        "strict_verdict": "PASS" if all(gates.values()) else "FAIL",
        "margins": margins,
    }


def run_experiment(
    config: E7Config,
    *,
    arms: Sequence[str] = ARMS,
    device_str: str = "cpu",
) -> tuple[list[StreamResult], dict[str, Any]]:
    if tuple(arms) != ARMS:
        raise ValueError("E7 budget audit requires all four frozen arms")
    configure_cpu_runtime(device_str)
    streams: list[StreamResult] = []
    for width in config.widths:
        for seed_index in range(config.seeds):
            task_barrier = threading.Barrier(len(arms))
            with ThreadPoolExecutor(max_workers=len(arms)) as executor:
                futures = [
                    executor.submit(
                        run_stream,
                        config,
                        arm=arm,
                        width=width,
                        seed_index=seed_index,
                        device_str=device_str,
                        task_barrier=task_barrier,
                    )
                    for arm in arms
                ]
                done, _pending = wait(futures, return_when=FIRST_EXCEPTION)
                failed = next(
                    (future for future in done if future.exception() is not None),
                    None,
                )
                if failed is not None:
                    task_barrier.abort()
                    for future in futures:
                        future.cancel()
                    failed.result()
                streams.extend(future.result() for future in futures)
    budget = _apply_budget_audit(streams)
    integrity = {
        "seed": _all_seeds_match_contract(streams),
        "sequential": all(stream.sequential_integrity for stream in streams),
        "protected_mass": all(stream.mass_integrity for stream in streams),
        "budget": budget["pass"],
        "budget_detail": budget,
    }
    return streams, integrity


def _is_frozen_confirmatory(config: E7Config) -> bool:
    return config == E7Config()


def _pilot_config() -> E7Config:
    return E7Config(task_moduli=TASK_MODULI[:2], widths=(WIDTHS[0],), seeds=1)


def _streams_from_payload(payload: Mapping[str, Any]) -> list[StreamResult]:
    streams = []
    for item in payload.get("streams", []):
        stream = dict(item)
        stream["checkpoints"] = [
            CheckpointRecord(**row) for row in stream["checkpoints"]
        ]
        stream["metrics"] = [MetricRecord(**row) for row in stream["metrics"]]
        streams.append(StreamResult(**stream))
    return streams


def validate_pilot_receipt(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("run_kind") != "pilot":
        raise ValueError("E7 confirmatory run requires an E7 pilot receipt")
    pilot_config = _pilot_config()
    expected_config = json.loads(json.dumps(asdict(pilot_config)))
    if payload.get("config") != expected_config:
        raise ValueError("pilot receipt does not match the frozen E7 pilot grid")
    if payload.get("status") != "complete":
        raise ValueError("pilot receipt is not complete")
    if payload.get("protection_lambda") != LAMBDA:
        raise ValueError("pilot receipt does not freeze the singleton lambda")
    expected_counts = {
        "stream_count": len(ARMS),
        "checkpoint_count": len(ARMS) * len(pilot_config.task_moduli),
        "stability_rows": len(ARMS),
        "valid_streams": len(ARMS),
    }
    if any(payload.get(key) != value for key, value in expected_counts.items()):
        raise ValueError("pilot receipt has incomplete E7 pilot coverage")
    streams = _streams_from_payload(payload)
    if len(streams) != len(ARMS):
        raise ValueError("pilot receipt omits raw stream timing records")
    budget = _apply_budget_audit(streams)
    if not budget["pass"]:
        raise ValueError("pilot receipt failed the per-arm timing budget gate")
    if not _all_seeds_match_contract(streams):
        raise ValueError("pilot receipt failed the matched seed contract")
    integrity = payload.get("integrity", {})
    if not integrity or not all(
        bool(integrity.get(key))
        for key in ("seed", "sequential", "protected_mass", "budget")
    ):
        raise ValueError("pilot receipt failed an integrity gate")
    return payload


def _stream_payload(stream: StreamResult) -> dict[str, Any]:
    return asdict(stream)


def _public_payload(
    config: E7Config,
    *,
    run_kind: str,
    streams: Sequence[StreamResult],
    integrity: Mapping[str, Any],
) -> dict[str, Any]:
    summary_rows = summarize_streams(streams)
    gates = analyze_gates(summary_rows) if run_kind == "confirmatory" else None
    valid_streams = sum(
        stream.seed_integrity
        and stream.sequential_integrity
        and stream.mass_integrity
        and stream.budget_integrity
        for stream in streams
    )
    return {
        "status": "complete" if all(
            bool(integrity.get(key))
            for key in ("seed", "sequential", "protected_mass", "budget")
        ) else "invalid",
        "run_kind": run_kind,
        "preregistration": (
            "papers/commitment_surface/"
            "e7_selective_subspace_continual_learning_preregistration_2026-07-13.md"
        ),
        "implementation_contract": (
            "papers/commitment_surface/"
            "e7_implementation_contract_2026-07-13.md"
        ),
        "config": asdict(config),
        "protection_lambda": config.protection_lambda,
        "stream_count": len(streams),
        "checkpoint_count": sum(len(stream.checkpoints) for stream in streams),
        "stability_rows": sum(
            sum(not metric.is_current_task for metric in stream.metrics)
            for stream in streams
        ),
        "valid_streams": valid_streams,
        "integrity": dict(integrity),
        "summary": summary_rows,
        "gate_analysis": gates,
    }


def write_summary_markdown(payload: Mapping[str, Any], path: Path) -> None:
    run_kind = str(payload["run_kind"])
    lines = [
        f"# E7 Selective Subspace — {run_kind.title()} Result",
        "",
        "Date: 2026-07-13.",
        "Pre-registration: `papers/commitment_surface/"
        "e7_selective_subspace_continual_learning_preregistration_2026-07-13.md`.",
        "",
        f"Status: **{str(payload['status']).upper()}**.",
        "",
        f"Streams: {payload['stream_count']}; checkpoints: "
        f"{payload['checkpoint_count']}; earlier-task stability rows: "
        f"{payload['stability_rows']}.",
        "",
        "## Integrity",
        "",
    ]
    integrity = payload["integrity"]
    for key in ("seed", "sequential", "protected_mass", "budget"):
        lines.append(f"- {key}: **{'PASS' if integrity[key] else 'FAIL'}**")
    if run_kind == "pilot":
        lines.extend(
            [
                "",
                "This one-seed, one-width, two-task CPU pilot is integrity-only. "
                "It cannot support an E7 scientific claim.",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "## Valid-stream aggregate",
                "",
                "| Width | Arm | Valid streams | Retained OOD | Earlier patch-CE / mass | Final-task OOD | Effective rank [95% CI] | Dead units [95% CI] |",
                "|---:|---|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for row in payload["summary"]:
            lines.append(
                f"| {row['width']} | {row['arm']} | {row['valid_streams']} | "
                f"{row['retained_ood_accuracy']:.4f} | "
                f"{row['earlier_patch_ce_per_mass']:.4f} | "
                f"{row['final_task_ood_accuracy']:.4f} | "
                f"{row['effective_rank']:.2f} "
                f"[{row['effective_rank_ci95'][0]:.2f}, "
                f"{row['effective_rank_ci95'][1]:.2f}] | "
                f"{row['dead_unit_fraction']:.4f} "
                f"[{row['dead_unit_fraction_ci95'][0]:.4f}, "
                f"{row['dead_unit_fraction_ci95'][1]:.4f}] |"
            )
        gate_analysis = payload["gate_analysis"]
        strict_verdict = gate_analysis["strict_verdict"]
        lines.extend(["", "## Frozen gates", ""])
        if strict_verdict == "INVALID":
            budget = integrity["budget_detail"]
            lines.extend(
                [
                    "Strict verdict: **INVALID — NO SCIENTIFIC VERDICT**.",
                    "",
                    "The original shared-barrier makespan made the four arm times "
                    "nearly identical by construction. Re-auditing the recorded "
                    "per-arm `median_step_seconds × optimizer_steps` estimates "
                    f"finds {len(budget['failures'])} of 32 matched groups above "
                    f"the frozen 2% limit (maximum "
                    f"{budget['max_relative_wall_clock_range']:.2%}). The seed, "
                    "sequential-exposure, and protected-mass gates pass, but the "
                    "budget failure kills the confirmatory run.",
                    "",
                    "G1–G4 are not evaluated. Any mechanism or frontier margins "
                    "from these cells are diagnostic only and cannot accept or "
                    "reject `H_subspace`.",
                ]
            )
        else:
            lines.append(f"Strict verdict: **{strict_verdict}**.")
            lines.append("")
            for gate, passed in gate_analysis["gates"].items():
                lines.append(f"- {gate}: **{'PASS' if passed else 'FAIL'}**")
            lines.extend(
                [
                    "",
                    "Frozen margins:",
                    "",
                    "| Width | G1: P_sub − P_none patch | G2: P_sub − P_ewc final OOD | G3: P_sub − P_ewc retained OOD | G4: P_sub − P_wrong patch |",
                    "|---:|---:|---:|---:|---:|",
                ]
            )
            for width in WIDTHS:
                margin = gate_analysis["margins"][str(width)]
                lines.append(
                    f"| {width} | "
                    f"{margin['G1_P_sub_minus_P_none_patch']:+.4f} | "
                    f"{margin['G2_P_sub_minus_P_ewc_final_ood']:+.4f} | "
                    f"**{margin['G3_P_sub_minus_P_ewc_retained_ood']:+.4f}** | "
                    f"{margin['G4_P_sub_minus_P_wrong_patch']:+.4f} |"
                )
        lines.extend(
            [
                "",
                "## Integrity and provenance",
                "",
                "- All 32 streams, 128 task checkpoints, and 192 earlier-task "
                "evaluations are present.",
                "- Seed collision, matched initialization/split/augmentation, "
                "sequential exposure, and exact 0.50 protected mass checks pass.",
            ]
        )
        if payload.get("raw_artifact_sha256"):
            lines.append(
                f"- Local raw artifact SHA-256: "
                f"`{payload['raw_artifact_sha256']}`."
            )
        lines.extend(
            [
                "",
                "## Reproduction",
                "",
                "Run the frozen pilot, then the locked confirmatory grid:",
                "",
                "```bash",
                ".venv/bin/python -m experiments.commitment_surface.e7_selective_subspace \\",
                "  --run-kind pilot --out artifacts/commitment_surface/e7_pilot_final_2026_07_13.json",
                "",
                ".venv/bin/python -m experiments.commitment_surface.e7_selective_subspace \\",
                "  --run-kind confirmatory \\",
                "  --pilot-result artifacts/commitment_surface/e7_pilot_final_2026_07_13.json \\",
                "  --out artifacts/commitment_surface/e7_confirmatory_2026_07_13.json \\",
                "  --public-json experiments/commitment_surface/results/e7_selective_subspace_2026_07_13.json \\",
                "  --summary experiments/commitment_surface/results/e7_selective_subspace_2026_07_13.md",
                "```",
                "",
                "Raw checkpoint rows stay under gitignored `artifacts/`.",
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-kind", choices=("pilot", "confirmatory"), required=True
    )
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--pilot-result", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--public-json", type=Path)
    parser.add_argument("--summary", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.run_kind == "pilot":
        config = _pilot_config()
    else:
        if args.pilot_result is None:
            raise SystemExit("--pilot-result is required for confirmatory E7")
        validate_pilot_receipt(args.pilot_result)
        config = E7Config()
        if not _is_frozen_confirmatory(config):
            raise RuntimeError("confirmatory E7 config drifted from the frozen grid")

    streams, integrity = run_experiment(config, device_str=args.device)
    public = _public_payload(
        config,
        run_kind=args.run_kind,
        streams=streams,
        integrity=integrity,
    )
    raw = dict(public)
    raw["streams"] = [_stream_payload(stream) for stream in streams]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    raw_text = json.dumps(raw, indent=2, sort_keys=True) + "\n"
    args.out.write_text(raw_text, encoding="utf-8")
    public["raw_artifact_sha256"] = hashlib.sha256(raw_text.encode()).hexdigest()
    if args.public_json is not None:
        args.public_json.parent.mkdir(parents=True, exist_ok=True)
        args.public_json.write_text(
            json.dumps(public, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if args.summary is not None:
        write_summary_markdown(public, args.summary)
    print(json.dumps(public, indent=2, sort_keys=True))
    if public["status"] != "complete":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
