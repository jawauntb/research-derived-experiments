#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Neural-model component of the symbolic weakness benchmark.

We train small MLPs on cyclic-prefix-shift tasks and check whether
*representation-level weakness* — the number of group elements under which
the learned function is approximately equivariant — predicts out-of-
distribution generalization better than training loss, sharpness, or
parameter norm.

The pipeline is purely synthetic and runs in seconds on CPU. The Modal
entrypoint is offered for scaling sweeps to thousands of models with no
behavioral change.
"""

from __future__ import annotations

import argparse
import json
import math
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean
from typing import Any

import torch
import torch.nn as nn
import torch.nn.functional as F

from experiments.symbolic_weakness.families import (
    cyclic_group,
    cyclic_prefix_trial,
    ground_truth_from_invariant,
)


@dataclass(frozen=True)
class ModelConfig:
    seed: int
    hidden_width: int
    depth: int
    init_scale: float
    learning_rate: float
    weight_decay: float
    epochs: int
    optimizer: str  # "adam" or "sgd"
    augmentation: str  # "none", "partial_cyclic", "full_cyclic", "wrong_reflection", "wrong_random"
    augmentation_count: int


@dataclass(frozen=True)
class TrainingArtifacts:
    config: ModelConfig
    final_train_loss: float
    train_accuracy: float
    held_out_validation_accuracy: float
    ood_accuracy: float
    parameter_l2: float
    weakness_oracle: int
    weakness_wrong_group: int
    weakness_random_label: int
    weakness_partial_cyclic: int
    sharpness_proxy: float
    full_function_table: tuple[int, ...]


class SimpleMLP(nn.Module):
    def __init__(self, *, n: int, hidden_width: int, depth: int, init_scale: float) -> None:
        super().__init__()
        layers: list[nn.Module] = []
        in_dim = n
        for _ in range(depth):
            linear = nn.Linear(in_dim, hidden_width)
            with torch.no_grad():
                linear.weight.mul_(init_scale)
            layers.append(linear)
            layers.append(nn.ReLU())
            in_dim = hidden_width
        head = nn.Linear(in_dim, n)
        with torch.no_grad():
            head.weight.mul_(init_scale)
        layers.append(head)
        self.net = nn.Sequential(*layers)
        self.n = n

    def forward(self, x_onehot: torch.Tensor) -> torch.Tensor:
        return self.net(x_onehot)


def _one_hot(values: list[int], n: int) -> torch.Tensor:
    out = torch.zeros(len(values), n)
    for row, value in enumerate(values):
        out[row, value] = 1.0
    return out


def _function_table(model: SimpleMLP, n: int) -> tuple[int, ...]:
    model.eval()
    with torch.no_grad():
        inputs = _one_hot(list(range(n)), n)
        logits = model(inputs)
        preds = logits.argmax(dim=-1).tolist()
    return tuple(int(p) for p in preds)


def _equivariance_count(predictions: tuple[int, ...], group_elements: tuple[tuple[int, ...], ...]) -> int:
    """Count elements g in the group such that there exists h in the group
    with predictions[g(x)] == h(predictions[x]) for all x.
    """
    n = len(predictions)
    count = 0
    for g in group_elements:
        induced = tuple(predictions[g[x]] for x in range(n))
        for h in group_elements:
            if all(h[predictions[x]] == induced[x] for x in range(n)):
                count += 1
                break
    return count


def _wrong_group(n: int, target_size: int, rng: random.Random) -> tuple[tuple[int, ...], ...]:
    cyclic_perms = {tuple((x + k) % n for x in range(n)) for k in range(n)}
    out: list[tuple[int, ...]] = []
    identity = tuple(range(n))
    out.append(identity)
    attempts = 0
    while len(out) < target_size and attempts < 200:
        p = list(range(n))
        rng.shuffle(p)
        cand = tuple(p)
        if cand not in cyclic_perms and cand not in out:
            out.append(cand)
        attempts += 1
    return tuple(out)


def _random_label_group(n: int, rng: random.Random) -> tuple[tuple[int, ...], ...]:
    """A control group that breaks the cyclic structure: each non-identity
    element is replaced by a random permutation (NOT a cyclic shift). This
    is the strongest "wrong group of comparable size" control because the
    elements are individually arbitrary permutations of the domain."""
    identity = tuple(range(n))
    out: list[tuple[int, ...]] = [identity]
    attempts = 0
    target = n  # same cardinality as Z_n
    cyclic_perms = {tuple((x + k) % n for x in range(n)) for k in range(n)}
    while len(out) < target and attempts < 200:
        p = list(range(n))
        rng.shuffle(p)
        cand = tuple(p)
        if cand not in cyclic_perms and cand not in out:
            out.append(cand)
        attempts += 1
    return tuple(out)


def _sharpness_proxy(model: SimpleMLP, inputs: torch.Tensor, targets: torch.Tensor) -> float:
    """Hutchinson-style trace estimate of the loss Hessian using a random
    Rademacher direction. Returns the squared norm of the directional
    second derivative as a fast proxy."""
    model.eval()
    params = [p for p in model.parameters() if p.requires_grad]
    # Sample a Rademacher vector for each parameter.
    vector = [torch.randint(0, 2, p.shape).float() * 2 - 1 for p in params]
    # Compute loss and gradient.
    model.zero_grad()
    logits = model(inputs)
    loss = F.cross_entropy(logits, targets)
    grads = torch.autograd.grad(loss, params, create_graph=True)
    # Compute H @ v as grad of (grads · v) wrt params.
    g_dot_v = sum((g * v).sum() for g, v in zip(grads, vector))
    hv = torch.autograd.grad(g_dot_v, params, retain_graph=False)
    sharpness = sum((h * v).sum().item() for h, v in zip(hv, vector))
    return float(sharpness)


def _augmented_examples(
    *,
    trial,
    truth: tuple[int, ...],
    modulus: int,
    augmentation: str,
    augmentation_count: int,
    rng: random.Random,
) -> tuple[list[int], list[int]]:
    """Return (x_list, y_list) of training inputs and targets after
    augmentation. The base set always includes the trial's prefix.

    Augmentation regimes:
      none           – just the prefix.
      partial_cyclic – add `count` examples drawn by shifting prefix examples
                       by random cyclic shifts (still consistent with truth).
      full_cyclic    – add every orbit completion (full Z_n coverage).
      wrong_reflection – add `count` (x, x) pairs that are consistent with the
                         identity rule but NOT with the truth (these are
                         label-noise examples in our setting).
      wrong_random   – add `count` random (x, y) pairs where y is uniform; we
                       discard examples that conflict with prefix.
    """
    xs = [ex.x for ex in trial.train_examples]
    ys = [ex.y for ex in trial.train_examples]
    base = set(zip(xs, ys))

    if augmentation == "full_cyclic":
        for x in range(modulus):
            if (x, truth[x]) not in base:
                xs.append(x)
                ys.append(truth[x])
        return xs, ys

    if augmentation == "none" or augmentation_count == 0:
        return xs, ys

    if augmentation == "partial_cyclic":
        candidates = [x for x in range(modulus) if (x, truth[x]) not in base]
        rng.shuffle(candidates)
        for x in candidates[:augmentation_count]:
            xs.append(x)
            ys.append(truth[x])
        return xs, ys

    if augmentation == "wrong_reflection":
        # Add identity pairs (x, x) for unseen inputs — these are NOT
        # consistent with the truth (except possibly at fixed points).
        candidates = [
            x for x in range(modulus)
            if (x, x) not in base and x != truth[x] and x not in xs
        ]
        rng.shuffle(candidates)
        for x in candidates[:augmentation_count]:
            xs.append(x)
            ys.append(x)
        return xs, ys

    if augmentation == "wrong_random":
        attempts = 0
        added = 0
        while added < augmentation_count and attempts < 200:
            x = rng.randrange(0, modulus)
            y = rng.randrange(0, modulus)
            if (x, y) not in base and x not in xs:
                xs.append(x)
                ys.append(y)
                added += 1
                base.add((x, y))
            attempts += 1
        return xs, ys

    raise ValueError(f"unknown augmentation: {augmentation}")


def train_one(
    *, trial_seed: int, modulus: int, train_window: int, config: ModelConfig
) -> TrainingArtifacts:
    torch.manual_seed(config.seed)
    py_rng = random.Random(config.seed)
    trial = cyclic_prefix_trial(
        rng=random.Random(trial_seed), modulus=modulus, train_window=train_window
    )
    truth = ground_truth_from_invariant(trial)

    aug_xs, aug_ys = _augmented_examples(
        trial=trial,
        truth=truth,
        modulus=modulus,
        augmentation=config.augmentation,
        augmentation_count=config.augmentation_count,
        rng=py_rng,
    )
    inputs = _one_hot(aug_xs, modulus)
    targets = torch.tensor(aug_ys, dtype=torch.long)

    model = SimpleMLP(
        n=modulus,
        hidden_width=config.hidden_width,
        depth=config.depth,
        init_scale=config.init_scale,
    )

    if config.optimizer == "adam":
        opt = torch.optim.Adam(
            model.parameters(),
            lr=config.learning_rate,
            weight_decay=config.weight_decay,
        )
    else:
        opt = torch.optim.SGD(
            model.parameters(),
            lr=config.learning_rate,
            weight_decay=config.weight_decay,
            momentum=0.9,
        )

    final_loss = math.inf
    for _ in range(config.epochs):
        model.train()
        opt.zero_grad()
        logits = model(inputs)
        loss = F.cross_entropy(logits, targets)
        loss.backward()
        opt.step()
        final_loss = float(loss.item())

    # Full function table for the learned function.
    table = _function_table(model, modulus)

    # Train accuracy.
    train_pred = [table[ex.x] for ex in trial.train_examples]
    train_acc = mean(int(p == ex.y) for p, ex in zip(train_pred, trial.train_examples))

    # Leave-one-out validation accuracy (re-uses the same trained model,
    # serving as a posterior-style check on a single held-out training pair).
    if len(trial.train_examples) >= 2:
        held = trial.train_examples[0]
        held_acc = float(table[held.x] == held.y)
    else:
        held_acc = 1.0

    # OOD accuracy on the unseen suffix.
    ood_correct = sum(int(table[x] == truth[x]) for x in trial.ood_inputs)
    ood_acc = ood_correct / max(1, len(trial.ood_inputs))

    # Equivariance counts under several candidate groups.
    group = cyclic_group(modulus)
    weakness_oracle = _equivariance_count(table, group.elements)
    wrong = _wrong_group(modulus, target_size=modulus, rng=py_rng)
    weakness_wrong = _equivariance_count(table, wrong)
    randomized = _random_label_group(modulus, py_rng)
    weakness_random = _equivariance_count(table, randomized)
    # Partial cyclic (only half the shifts): weaker prior; still informative.
    partial_cyclic = group.elements[: max(1, modulus // 2)]
    weakness_partial = _equivariance_count(table, partial_cyclic)

    # Parameter L2.
    param_l2 = math.sqrt(
        sum(float((p.detach() ** 2).sum().item()) for p in model.parameters())
    )

    # Sharpness via Hutchinson.
    sharpness = _sharpness_proxy(model, inputs, targets)

    return TrainingArtifacts(
        config=config,
        final_train_loss=float(final_loss),
        train_accuracy=float(train_acc),
        held_out_validation_accuracy=float(held_acc),
        ood_accuracy=float(ood_acc),
        parameter_l2=param_l2,
        weakness_oracle=int(weakness_oracle),
        weakness_wrong_group=int(weakness_wrong),
        weakness_random_label=int(weakness_random),
        weakness_partial_cyclic=int(weakness_partial),
        sharpness_proxy=float(sharpness),
        full_function_table=table,
    )


def run_sweep(
    *,
    n_models: int,
    modulus: int,
    train_window: int,
    base_seed: int,
    epochs: int,
    vary_task: bool = True,
) -> list[TrainingArtifacts]:
    rng = random.Random(base_seed)
    artifacts: list[TrainingArtifacts] = []
    for _ in range(n_models):
        augmentation = rng.choice(
            ["none", "partial_cyclic", "full_cyclic", "wrong_reflection", "wrong_random"]
        )
        augmentation_count = (
            0 if augmentation == "none" or augmentation == "full_cyclic"
            else rng.choice([2, 4, 6, 8])
        )
        if vary_task:
            trial_modulus = rng.choice([7, 11, 13])
            trial_window = rng.choice([2, 3, 4])
        else:
            trial_modulus = modulus
            trial_window = train_window
        config = ModelConfig(
            seed=rng.randrange(0, 2**31 - 1),
            hidden_width=rng.choice([16, 32, 64, 128]),
            depth=rng.choice([1, 2, 3]),
            init_scale=rng.choice([0.3, 0.7, 1.0, 1.5]),
            learning_rate=rng.choice([1e-3, 3e-3, 1e-2, 3e-2]),
            weight_decay=rng.choice([0.0, 1e-4, 1e-2]),
            epochs=epochs,
            optimizer=rng.choice(["adam", "sgd"]),
            augmentation=augmentation,
            augmentation_count=augmentation_count,
        )
        trial_seed = rng.randrange(0, 2**31 - 1)
        artifact = train_one(
            trial_seed=trial_seed,
            modulus=trial_modulus,
            train_window=trial_window,
            config=config,
        )
        artifacts.append(artifact)
    return artifacts


def _pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    mx = mean(xs)
    my = mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    denom = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
    if denom == 0:
        return 0.0
    return num / denom


def _spearman(xs: list[float], ys: list[float]) -> float:
    def _rank(values: list[float]) -> list[float]:
        order = sorted(range(len(values)), key=lambda i: values[i])
        ranks = [0.0] * len(values)
        i = 0
        while i < len(values):
            j = i
            while j + 1 < len(values) and values[order[j + 1]] == values[order[i]]:
                j += 1
            avg_rank = (i + j) / 2 + 1
            for k in range(i, j + 1):
                ranks[order[k]] = avg_rank
            i = j + 1
        return ranks

    rx = _rank(xs)
    ry = _rank(ys)
    return _pearson(rx, ry)


def summarize_sweep(arts: list[TrainingArtifacts]) -> dict[str, Any]:
    ood = [a.ood_accuracy for a in arts]
    metrics = {
        "final_train_loss": [a.final_train_loss for a in arts],
        "parameter_l2": [a.parameter_l2 for a in arts],
        "sharpness_proxy": [a.sharpness_proxy for a in arts],
        "abs_sharpness_proxy": [abs(a.sharpness_proxy) for a in arts],
        "weakness_oracle_norm": [
            float(a.weakness_oracle) / max(1, len(a.full_function_table))
            for a in arts
        ],
        "weakness_wrong_group_norm": [
            float(a.weakness_wrong_group) / max(1, len(a.full_function_table))
            for a in arts
        ],
        "weakness_random_label_norm": [
            float(a.weakness_random_label) / max(1, len(a.full_function_table))
            for a in arts
        ],
        "weakness_partial_cyclic_norm": [
            float(a.weakness_partial_cyclic) / max(1, len(a.full_function_table))
            for a in arts
        ],
        "weakness_oracle": [float(a.weakness_oracle) for a in arts],
        "weakness_wrong_group": [float(a.weakness_wrong_group) for a in arts],
        "weakness_random_label": [float(a.weakness_random_label) for a in arts],
        "weakness_partial_cyclic": [float(a.weakness_partial_cyclic) for a in arts],
        "held_out_validation_accuracy": [a.held_out_validation_accuracy for a in arts],
    }
    correlations: dict[str, dict[str, float]] = {}
    for name, vals in metrics.items():
        correlations[name] = {
            "pearson_with_ood": _pearson(vals, ood),
            "spearman_with_ood": _spearman(vals, ood),
        }
    return {
        "n_models": len(arts),
        "mean_ood_accuracy": mean(ood) if ood else 0.0,
        "fraction_with_perfect_ood": sum(1 for o in ood if o > 0.99) / max(1, len(ood)),
        "correlations": correlations,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-models", type=int, default=64)
    parser.add_argument("--modulus", type=int, default=11)
    parser.add_argument("--train-window", type=int, default=4)
    parser.add_argument("--epochs", type=int, default=300)
    parser.add_argument("--base-seed", type=int, default=20260609)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    arts = run_sweep(
        n_models=args.n_models,
        modulus=args.modulus,
        train_window=args.train_window,
        base_seed=args.base_seed,
        epochs=args.epochs,
    )
    summary = summarize_sweep(arts)
    payload = {
        "manifest": {
            "n_models": args.n_models,
            "modulus": args.modulus,
            "train_window": args.train_window,
            "epochs": args.epochs,
            "base_seed": args.base_seed,
        },
        "summary": summary,
        "artifacts": [
            {
                "config": asdict(a.config),
                "final_train_loss": a.final_train_loss,
                "train_accuracy": a.train_accuracy,
                "held_out_validation_accuracy": a.held_out_validation_accuracy,
                "ood_accuracy": a.ood_accuracy,
                "parameter_l2": a.parameter_l2,
                "weakness_oracle": a.weakness_oracle,
                "weakness_wrong_group": a.weakness_wrong_group,
                "weakness_random_label": a.weakness_random_label,
                "weakness_partial_cyclic": a.weakness_partial_cyclic,
                "sharpness_proxy": a.sharpness_proxy,
                "full_function_table": list(a.full_function_table),
            }
            for a in arts
        ],
    }
    text = json.dumps(payload, indent=2, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print("=== Neural Symbolic Weakness Sweep ===")
    print(f"n_models={summary['n_models']} mean_ood={summary['mean_ood_accuracy']:.3f}")
    print(f"fraction_perfect_ood={summary['fraction_with_perfect_ood']:.3f}")
    print("\nPredictors of OOD accuracy (Pearson, Spearman):")
    for name, stats in summary["correlations"].items():
        print(
            f"  {name:30s} pearson={stats['pearson_with_ood']:+.3f} "
            f"spearman={stats['spearman_with_ood']:+.3f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
