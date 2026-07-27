#!/usr/bin/env python3
"""Frozen-weight meta-GRU and context-probe helpers for Constraint Swap."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Sequence, cast

import numpy as np
import torch
from torch import nn

from .core import (
    BEHAVIOR_ACTIONS,
    Constraint,
    DecisionUnit,
    ExperimentConfig,
    GridTopology,
    LowRankTransport,
    all_decision_units,
    observation,
    oracle_action,
)


TASKS: tuple[Constraint, ...] = ("A", "B", "D")


class MetaGRU(nn.Module):
    def __init__(self, observation_size: int, hidden_size: int) -> None:
        super().__init__()
        self.observation_size = observation_size
        self.hidden_size = hidden_size
        self.input_size = observation_size + len(BEHAVIOR_ACTIONS) + 1
        self.gru = nn.GRU(
            input_size=self.input_size,
            hidden_size=hidden_size,
            num_layers=1,
            batch_first=True,
        )
        self.action_head = nn.Linear(hidden_size, len(BEHAVIOR_ACTIONS))

    def forward(
        self,
        inputs: torch.Tensor,
        hidden: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        outputs, next_hidden = self.gru(inputs, hidden)
        return self.action_head(outputs), outputs, next_hidden

    def step(
        self,
        inputs: torch.Tensor,
        hidden: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        logits, outputs, next_hidden = self.forward(inputs[:, None, :], hidden)
        return logits[:, 0, :], next_hidden


@dataclass(frozen=True)
class ContextProbe:
    hidden: np.ndarray
    logits: np.ndarray
    labels: np.ndarray
    units: tuple[DecisionUnit, ...]

    @property
    def accuracy(self) -> float:
        predictions = self.logits.argmax(axis=-1)
        return float(np.mean(predictions == self.labels[:, None]))


def _set_determinism(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True)


def _world_arrays(
    topology: GridTopology,
) -> tuple[list[DecisionUnit], np.ndarray, dict[Constraint, np.ndarray]]:
    units = all_decision_units(topology)
    observations = np.stack([observation(topology, unit) for unit in units])
    labels = {
        constraint: np.asarray(
            [oracle_action(unit, constraint) for unit in units],
            dtype=np.int64,
        )
        for constraint in TASKS
    }
    return units, observations, labels


def _training_batch(
    *,
    rng: np.random.Generator,
    observations: np.ndarray,
    labels: dict[Constraint, np.ndarray],
    batch_size: int,
    sequence_length: int,
) -> tuple[torch.Tensor, torch.Tensor]:
    if batch_size % len(TASKS):
        raise ValueError(f"batch_size must be divisible by {len(TASKS)}")
    base_batch = batch_size // len(TASKS)
    indices = rng.integers(
        0,
        len(observations),
        size=(base_batch, sequence_length),
    )
    base_observations = observations[indices]
    task_observations = np.concatenate(
        [base_observations for _ in TASKS],
        axis=0,
    )
    targets = np.concatenate(
        [labels[constraint][indices] for constraint in TASKS],
        axis=0,
    )
    previous_actions = np.zeros(
        (batch_size, sequence_length, len(BEHAVIOR_ACTIONS)),
        dtype=np.float32,
    )
    previous_rewards = np.zeros((batch_size, sequence_length, 1), dtype=np.float32)
    if sequence_length > 1:
        rows = np.arange(batch_size)[:, None]
        times = np.arange(sequence_length - 1)[None, :]
        previous_actions[rows, times + 1, targets[:, :-1]] = 1.0
        previous_rewards[:, 1:, 0] = 1.0
    inputs = np.concatenate(
        [task_observations, previous_actions, previous_rewards],
        axis=-1,
    )
    return torch.from_numpy(inputs), torch.from_numpy(targets)


def train_model(
    *,
    seed: int,
    config: ExperimentConfig,
    topology: GridTopology,
) -> tuple[MetaGRU, dict[str, float | int]]:
    """Train one paired meta-agent on identical A/B/D observation schedules."""

    _set_determinism(seed)
    torch.set_num_threads(1)
    _, observations, labels = _world_arrays(topology)
    model = MetaGRU(observations.shape[1], config.hidden_size)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=config.learning_rate,
        weight_decay=config.weight_decay,
    )
    loss_fn = nn.CrossEntropyLoss()
    rng = np.random.default_rng(seed * 100_003 + 17)
    losses: list[float] = []
    warmup = min(3, config.sequence_length - 1)
    model.train()
    for _ in range(config.training_steps):
        inputs, targets = _training_batch(
            rng=rng,
            observations=observations,
            labels=labels,
            batch_size=config.batch_size,
            sequence_length=config.sequence_length,
        )
        optimizer.zero_grad(set_to_none=True)
        logits, _, _ = model(inputs)
        loss = loss_fn(
            logits[:, warmup:].reshape(-1, len(BEHAVIOR_ACTIONS)),
            targets[:, warmup:].reshape(-1),
        )
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        losses.append(float(loss.detach()))
    model.eval()
    return model, {
        "seed": seed,
        "steps": config.training_steps,
        "initial_loss": losses[0],
        "final_loss": losses[-1],
        "mean_tail_loss": float(np.mean(losses[-min(50, len(losses)) :])),
    }


def _input_row(
    topology: GridTopology,
    unit: DecisionUnit,
    previous_action: int | None,
    previous_reward: float,
) -> np.ndarray:
    action = np.zeros(len(BEHAVIOR_ACTIONS), dtype=np.float32)
    if previous_action is not None:
        action[previous_action] = 1.0
    return np.concatenate(
        [
            observation(topology, unit),
            action,
            np.asarray([previous_reward], dtype=np.float32),
        ]
    )


def collect_context(
    model: MetaGRU,
    topology: GridTopology,
    units: Sequence[DecisionUnit],
    *,
    prefix: tuple[Constraint, ...],
    demonstrations: tuple[int, ...],
    histories: int,
    seed: int,
) -> ContextProbe:
    """Collect query activations after one or more fixed task-context segments."""

    if len(prefix) != len(demonstrations) or not prefix:
        raise ValueError("prefix and demonstrations need the same non-zero length")
    if histories < 1 or any(count < 1 for count in demonstrations):
        raise ValueError("histories and demonstration counts must be positive")
    world_units = all_decision_units(topology)
    query_units = tuple(units)
    active_constraint = prefix[-1]
    labels = np.asarray(
        [oracle_action(unit, active_constraint) for unit in query_units],
        dtype=np.int64,
    )
    hidden_rows: list[np.ndarray] = []
    logit_rows: list[np.ndarray] = []

    with torch.no_grad():
        for history_index in range(histories):
            rng = np.random.default_rng(seed * 1009 + history_index * 9176 + 31)
            hidden: torch.Tensor | None = None
            previous_action: int | None = None
            previous_reward = 0.0
            for constraint, count in zip(prefix, demonstrations, strict=True):
                context_indices = rng.integers(0, len(world_units), size=count)
                for unit_index in context_indices:
                    demo_unit = world_units[int(unit_index)]
                    row = torch.from_numpy(
                        _input_row(
                            topology,
                            demo_unit,
                            previous_action,
                            previous_reward,
                        )
                    )[None, :]
                    _, hidden = model.step(row, hidden)
                    previous_action = oracle_action(demo_unit, constraint)
                    previous_reward = 1.0

            query_inputs = torch.from_numpy(
                np.stack(
                    [
                        _input_row(
                            topology,
                            unit,
                            previous_action,
                            previous_reward,
                        )
                        for unit in query_units
                    ]
                )
            )
            if hidden is None:
                raise RuntimeError("context did not produce a hidden state")
            repeated_hidden = hidden.repeat(1, len(query_units), 1)
            logits, query_hidden = model.step(query_inputs, repeated_hidden)
            hidden_rows.append(query_hidden[0].cpu().numpy())
            logit_rows.append(logits.cpu().numpy())

    return ContextProbe(
        hidden=np.stack(hidden_rows, axis=1),
        logits=np.stack(logit_rows, axis=1),
        labels=labels,
        units=query_units,
    )


def collect_random_context(
    model: MetaGRU,
    topology: GridTopology,
    units: Sequence[DecisionUnit],
    *,
    demonstrations: int,
    histories: int,
    seed: int,
) -> ContextProbe:
    """Collect an exactly balanced randomized-label sham context."""

    if demonstrations < 1 or histories < 1:
        raise ValueError("demonstrations and histories must be positive")
    world_units = all_decision_units(topology)
    query_units = tuple(units)
    label_rng = np.random.default_rng(seed * 4001 + 73)
    labels = np.tile(
        np.arange(len(BEHAVIOR_ACTIONS), dtype=np.int64),
        int(np.ceil(len(query_units) / len(BEHAVIOR_ACTIONS))),
    )[: len(query_units)]
    label_rng.shuffle(labels)
    hidden_rows: list[np.ndarray] = []
    logit_rows: list[np.ndarray] = []

    with torch.no_grad():
        for history_index in range(histories):
            rng = np.random.default_rng(seed * 1009 + history_index * 9176 + 31)
            hidden: torch.Tensor | None = None
            previous_action: int | None = None
            previous_reward = 0.0
            context_indices = rng.integers(0, len(world_units), size=demonstrations)
            balanced_actions = np.tile(
                np.arange(len(BEHAVIOR_ACTIONS), dtype=np.int64),
                int(np.ceil(demonstrations / len(BEHAVIOR_ACTIONS))),
            )[:demonstrations]
            rng.shuffle(balanced_actions)
            for unit_index, random_action in zip(
                context_indices,
                balanced_actions,
                strict=True,
            ):
                demo_unit = world_units[int(unit_index)]
                row = torch.from_numpy(
                    _input_row(
                        topology,
                        demo_unit,
                        previous_action,
                        previous_reward,
                    )
                )[None, :]
                _, hidden = model.step(row, hidden)
                previous_action = int(random_action)
                previous_reward = 1.0
            query_inputs = torch.from_numpy(
                np.stack(
                    [
                        _input_row(
                            topology,
                            unit,
                            previous_action,
                            previous_reward,
                        )
                        for unit in query_units
                    ]
                )
            )
            if hidden is None:
                raise RuntimeError("sham context did not produce a hidden state")
            logits, query_hidden = model.step(
                query_inputs,
                hidden.repeat(1, len(query_units), 1),
            )
            hidden_rows.append(query_hidden[0].cpu().numpy())
            logit_rows.append(logits.cpu().numpy())

    return ContextProbe(
        hidden=np.stack(hidden_rows, axis=1),
        logits=np.stack(logit_rows, axis=1),
        labels=labels,
        units=query_units,
    )


def select_probe_units(
    topology: GridTopology,
    *,
    count: int,
    seed: int,
) -> list[DecisionUnit]:
    """Select a deterministic label-combination-balanced probe set."""

    units = all_decision_units(topology)
    grouped: dict[tuple[int, int, int], list[DecisionUnit]] = {}
    for unit in units:
        key = cast(
            tuple[int, int, int],
            tuple(
                oracle_action(unit, constraint)
                for constraint in TASKS
            ),
        )
        grouped.setdefault(key, []).append(unit)
    if count < len(grouped):
        raise ValueError("count is too small to represent every label combination")
    rng = np.random.default_rng(seed)
    group_keys = sorted(grouped)
    base, remainder = divmod(count, len(group_keys))
    selected: list[DecisionUnit] = []
    for key_index, key in enumerate(group_keys):
        take = base + int(key_index < remainder)
        choices = grouped[key]
        indices = rng.choice(len(choices), size=take, replace=False)
        selected.extend(choices[int(index)] for index in indices)
    selected.sort()
    return selected


def evaluate_context_accuracy(
    model: MetaGRU,
    topology: GridTopology,
    *,
    constraints: tuple[Constraint, ...],
    demonstrations: int,
    histories: int,
    seed: int,
) -> dict[str, float]:
    units = all_decision_units(topology)
    return {
        constraint: collect_context(
            model,
            topology,
            units,
            prefix=(constraint,),
            demonstrations=(demonstrations,),
            histories=histories,
            seed=seed,
        ).accuracy
        for constraint in constraints
    }


def action_head_logits(model: MetaGRU, hidden: np.ndarray) -> np.ndarray:
    values = np.asarray(hidden, dtype=np.float32)
    flat = values.reshape(-1, values.shape[-1])
    with torch.no_grad():
        logits = model.action_head(torch.from_numpy(flat)).cpu().numpy()
    return logits.reshape(*values.shape[:-1], len(BEHAVIOR_ACTIONS))


def matched_random_transport(
    transport: LowRankTransport,
    *,
    calibration_hidden: np.ndarray,
    seed: int,
    candidates: int = 64,
) -> LowRankTransport:
    """Create a rank-, norm-, and induced-covariance-matched random control."""

    rng = np.random.default_rng(seed)
    source = np.asarray(calibration_hidden, dtype=np.float64).reshape(
        -1, transport.matrix.shape[0]
    )
    dimension = transport.matrix.shape[0]
    _, singular, _ = np.linalg.svd(transport.matrix, full_matrices=False)
    rank = min(transport.rank, int(np.sum(singular > 1e-12)))
    bias_norm = float(np.linalg.norm(transport.bias))

    def signature(candidate: LowRankTransport) -> np.ndarray:
        moved = candidate.apply(source)
        norm_change = abs(
            float(np.mean(np.linalg.norm(moved, axis=1)))
            / max(float(np.mean(np.linalg.norm(source, axis=1))), 1e-12)
            - 1.0
        )
        base_cov = np.cov(source, rowvar=False)
        moved_cov = np.cov(moved, rowvar=False)
        cov_change = float(
            np.linalg.norm(moved_cov - base_cov)
            / max(np.linalg.norm(base_cov), 1e-12)
        )
        return np.asarray([norm_change, cov_change])

    target_signature = signature(transport)
    best: LowRankTransport | None = None
    best_score = float("inf")
    for _ in range(candidates):
        if rank:
            left, _ = np.linalg.qr(rng.normal(size=(dimension, rank)))
            right, _ = np.linalg.qr(rng.normal(size=(dimension, rank)))
            matrix = (left[:, :rank] * singular[:rank]) @ right[:, :rank].T
        else:
            matrix = np.zeros_like(transport.matrix)
        bias = rng.normal(size=dimension)
        bias /= np.linalg.norm(bias) + 1e-12
        bias *= bias_norm
        candidate = LowRankTransport(
            bias=bias,
            matrix=matrix,
            rank=transport.rank,
            calibration_mse=float("nan"),
        )
        scale = np.maximum(target_signature, 1e-3)
        score = float(np.linalg.norm((signature(candidate) - target_signature) / scale))
        if score < best_score:
            best = candidate
            best_score = score
    if best is None:
        raise ValueError("candidates must be positive")
    return best
