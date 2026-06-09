#!/usr/bin/env python3
"""Neural-model sweep on the rotated-stroke benchmark.

For each model we measure:

- training loss / accuracy
- held-out OOD accuracy on rotations not seen during training
- learned-function weakness under the rotation group:
    fraction of test inputs for which `argmax f(rotate(x, g))` agrees with
    the "rotation-consistent" prediction `argmax f(x)` for each g in Z_n;
    averaged into a normalized invariance score in [0, 1].
- a wrong-group control: same invariance score under random pixel
  permutations of equal cardinality.
- parameter L2 norm, Hutchinson sharpness proxy, leave-one-out train pair
  accuracy.

We then compute Pearson and Spearman correlations of every predictor with
OOD accuracy, replicating the symbolic-weakness paper's experimental
template at image scale.
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

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from experiments.rotation_weakness.dataset import (
    N_CLASSES,
    RotationSplit,
    make_partial_rotation_split,
    materialize_split,
    rotate_image,
    rotation_group_elements,
    to_tensors,
)


@dataclass(frozen=True)
class ModelConfig:
    seed: int
    architecture: str  # "mlp" or "cnn"
    hidden_width: int
    depth: int
    init_scale: float
    learning_rate: float
    weight_decay: float
    epochs: int
    optimizer: str
    augmentation: str  # "none", "partial_rotation", "full_rotation", "wrong_permute"
    augmentation_strength: int


@dataclass(frozen=True)
class ModelArtifact:
    config: ModelConfig
    final_train_loss: float
    train_accuracy: float
    ood_accuracy: float
    weakness_rotation_norm: float
    weakness_wrong_group_norm: float
    parameter_l2: float
    sharpness_proxy: float


class SmallCNN(nn.Module):
    def __init__(self, *, hidden: int, depth: int, init_scale: float) -> None:
        super().__init__()
        layers: list[nn.Module] = []
        in_ch = 1
        for _ in range(depth):
            conv = nn.Conv2d(in_ch, hidden, kernel_size=3, padding=1)
            with torch.no_grad():
                conv.weight.mul_(init_scale)
            layers.extend([conv, nn.ReLU(), nn.MaxPool2d(2)])
            in_ch = hidden
        self.feature = nn.Sequential(*layers)
        # GRID_SIZE / 2^depth × GRID_SIZE / 2^depth × hidden
        grid = 16 // (2 ** depth)
        if grid < 1:
            grid = 1
        head = nn.Linear(max(1, grid * grid) * hidden, N_CLASSES)
        with torch.no_grad():
            head.weight.mul_(init_scale)
        self.head = head

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        f = self.feature(x)
        f = f.flatten(start_dim=1)
        return self.head(f)


class SmallMLP(nn.Module):
    def __init__(self, *, hidden: int, depth: int, init_scale: float) -> None:
        super().__init__()
        layers: list[nn.Module] = []
        in_dim = 16 * 16
        for _ in range(depth):
            lin = nn.Linear(in_dim, hidden)
            with torch.no_grad():
                lin.weight.mul_(init_scale)
            layers.extend([lin, nn.ReLU()])
            in_dim = hidden
        head = nn.Linear(in_dim, N_CLASSES)
        with torch.no_grad():
            head.weight.mul_(init_scale)
        layers.append(head)
        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x.flatten(start_dim=1))


def make_model(config: ModelConfig) -> nn.Module:
    if config.architecture == "cnn":
        return SmallCNN(
            hidden=config.hidden_width,
            depth=config.depth,
            init_scale=config.init_scale,
        )
    if config.architecture == "mlp":
        return SmallMLP(
            hidden=config.hidden_width,
            depth=config.depth,
            init_scale=config.init_scale,
        )
    raise ValueError(f"unknown arch {config.architecture}")


def _rotate_batch_tensor(images: torch.Tensor, degrees: float) -> torch.Tensor:
    """Rotate a batch of [B, 1, H, W] tensors by `degrees`, via scipy ndimage
    on each example. Slow for large batches but adequate at 16×16."""
    if degrees == 0.0:
        return images
    out = torch.zeros_like(images)
    for i in range(images.shape[0]):
        rotated = rotate_image(images[i, 0].cpu().numpy(), degrees)
        out[i, 0] = torch.from_numpy(rotated)
    return out


def _augment(
    images: torch.Tensor,
    labels: torch.Tensor,
    *,
    augmentation: str,
    strength: int,
    n_rotations: int,
    rng: random.Random,
) -> tuple[torch.Tensor, torch.Tensor]:
    if augmentation == "none" or strength == 0:
        return images, labels
    if augmentation == "full_rotation":
        all_angles = rotation_group_elements(n_rotations)
        chunks_x = [images]
        chunks_y = [labels]
        for deg in all_angles[1:]:
            chunks_x.append(_rotate_batch_tensor(images, deg))
            chunks_y.append(labels)
        return torch.cat(chunks_x, dim=0), torch.cat(chunks_y, dim=0)
    if augmentation == "partial_rotation":
        all_angles = rotation_group_elements(n_rotations)
        chosen = rng.sample(all_angles[1:], min(strength, n_rotations - 1))
        chunks_x = [images]
        chunks_y = [labels]
        for deg in chosen:
            chunks_x.append(_rotate_batch_tensor(images, deg))
            chunks_y.append(labels)
        return torch.cat(chunks_x, dim=0), torch.cat(chunks_y, dim=0)
    if augmentation == "wrong_permute":
        # Apply `strength` random pixel permutations as wrong augmentations
        # — these should NOT improve OOD on the rotation task.
        chunks_x = [images]
        chunks_y = [labels]
        for _ in range(strength):
            perm = torch.randperm(16 * 16)
            flat = images.flatten(start_dim=2)
            shuffled = flat[:, :, perm].reshape_as(images)
            chunks_x.append(shuffled)
            chunks_y.append(labels)
        return torch.cat(chunks_x, dim=0), torch.cat(chunks_y, dim=0)
    raise ValueError(augmentation)


def _accuracy(model: nn.Module, x: torch.Tensor, y: torch.Tensor) -> float:
    model.eval()
    with torch.no_grad():
        preds = model(x).argmax(dim=-1)
    return float((preds == y).float().mean().item())


def _rotation_weakness(
    model: nn.Module,
    eval_x: torch.Tensor,
    *,
    n_rotations: int,
) -> float:
    """Fraction of (sample, rotation) pairs for which the model's
    prediction is invariant under rotation. 1.0 = fully equivariant
    (predictions never change when input is rotated). 1/n = predictions
    flip uniformly. We normalize to [0, 1]."""
    model.eval()
    with torch.no_grad():
        base_pred = model(eval_x).argmax(dim=-1)
    angles = rotation_group_elements(n_rotations)
    agree = 0
    total = 0
    for deg in angles:
        if deg == 0.0:
            continue
        rotated = _rotate_batch_tensor(eval_x, deg)
        with torch.no_grad():
            rot_pred = model(rotated).argmax(dim=-1)
        agree += int((rot_pred == base_pred).sum().item())
        total += int(rot_pred.shape[0])
    return agree / max(1, total)


def _wrong_group_invariance(
    model: nn.Module,
    eval_x: torch.Tensor,
    *,
    n_perms: int,
    rng: random.Random,
) -> float:
    """Compute prediction-invariance under `n_perms` random pixel
    permutations. This is the wrong-group control: if the model has
    learned the rotation symmetry, this should be LOW (random perms
    destroy class identity)."""
    model.eval()
    with torch.no_grad():
        base_pred = model(eval_x).argmax(dim=-1)
    flat = eval_x.flatten(start_dim=2)
    agree = 0
    total = 0
    for _ in range(n_perms):
        perm = torch.tensor(rng.sample(range(16 * 16), 16 * 16))
        shuffled = flat[:, :, perm].reshape_as(eval_x)
        with torch.no_grad():
            shuf_pred = model(shuffled).argmax(dim=-1)
        agree += int((shuf_pred == base_pred).sum().item())
        total += int(shuf_pred.shape[0])
    return agree / max(1, total)


def _sharpness_proxy(model: nn.Module, x: torch.Tensor, y: torch.Tensor) -> float:
    model.eval()
    params = [p for p in model.parameters() if p.requires_grad]
    vector = [torch.randint(0, 2, p.shape).float() * 2 - 1 for p in params]
    model.zero_grad()
    loss = F.cross_entropy(model(x), y)
    grads = torch.autograd.grad(loss, params, create_graph=True)
    g_dot_v = sum((g * v).sum() for g, v in zip(grads, vector))
    hv = torch.autograd.grad(g_dot_v, params, retain_graph=False)
    return float(sum((h * v).sum().item() for h, v in zip(hv, vector)))


def train_one(
    *,
    split: RotationSplit,
    config: ModelConfig,
    samples_per_class_rotation: int = 8,
) -> ModelArtifact:
    torch.manual_seed(config.seed)
    py_rng = random.Random(config.seed)
    np.random.seed(config.seed)

    train_samples, ood_samples = materialize_split(
        split,
        samples_per_class_rotation=samples_per_class_rotation,
        seed=config.seed,
    )
    train_x, train_y = to_tensors(train_samples)
    ood_x, ood_y = to_tensors(ood_samples)

    aug_x, aug_y = _augment(
        train_x,
        train_y,
        augmentation=config.augmentation,
        strength=config.augmentation_strength,
        n_rotations=split.n_rotations,
        rng=py_rng,
    )

    model = make_model(config)
    opt = (
        torch.optim.Adam(model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay)
        if config.optimizer == "adam"
        else torch.optim.SGD(model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay, momentum=0.9)
    )

    final_loss = math.inf
    for _ in range(config.epochs):
        model.train()
        opt.zero_grad()
        logits = model(aug_x)
        loss = F.cross_entropy(logits, aug_y)
        loss.backward()
        opt.step()
        final_loss = float(loss.item())

    train_acc = _accuracy(model, train_x, train_y)
    ood_acc = _accuracy(model, ood_x, ood_y)
    weakness_rot = _rotation_weakness(model, ood_x, n_rotations=split.n_rotations)
    weakness_wrong = _wrong_group_invariance(
        model, ood_x, n_perms=split.n_rotations - 1, rng=py_rng
    )
    param_l2 = math.sqrt(
        sum(float((p.detach() ** 2).sum().item()) for p in model.parameters())
    )
    sharp = _sharpness_proxy(model, aug_x, aug_y)

    return ModelArtifact(
        config=config,
        final_train_loss=final_loss,
        train_accuracy=train_acc,
        ood_accuracy=ood_acc,
        weakness_rotation_norm=weakness_rot,
        weakness_wrong_group_norm=weakness_wrong,
        parameter_l2=param_l2,
        sharpness_proxy=sharp,
    )


def run_sweep(
    *,
    n_models: int,
    n_rotations: int,
    train_per_class: int,
    epochs: int,
    base_seed: int,
) -> list[ModelArtifact]:
    rng = random.Random(base_seed)
    artifacts: list[ModelArtifact] = []
    for _ in range(n_models):
        split = make_partial_rotation_split(
            n_rotations=n_rotations,
            train_per_class=train_per_class,
            seed=rng.randrange(0, 2**31 - 1),
        )
        arch = rng.choice(["cnn", "mlp"])
        augmentation = rng.choice(
            ["none", "partial_rotation", "full_rotation", "wrong_permute"]
        )
        strength = 0 if augmentation in ("none", "full_rotation") else rng.choice([2, 4, 6])
        config = ModelConfig(
            seed=rng.randrange(0, 2**31 - 1),
            architecture=arch,
            hidden_width=rng.choice([16, 32, 64]),
            depth=rng.choice([1, 2]),
            init_scale=rng.choice([0.5, 1.0, 1.5]),
            learning_rate=rng.choice([1e-3, 3e-3, 1e-2]),
            weight_decay=rng.choice([0.0, 1e-4]),
            epochs=epochs,
            optimizer=rng.choice(["adam", "sgd"]),
            augmentation=augmentation,
            augmentation_strength=strength,
        )
        artifacts.append(train_one(split=split, config=config))
    return artifacts


def _pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    mx, my = mean(xs), mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    denom = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
    return 0.0 if denom == 0 else num / denom


def _spearman(xs: list[float], ys: list[float]) -> float:
    def rank(vals: list[float]) -> list[float]:
        order = sorted(range(len(vals)), key=lambda i: vals[i])
        r = [0.0] * len(vals)
        i = 0
        while i < len(vals):
            j = i
            while j + 1 < len(vals) and vals[order[j + 1]] == vals[order[i]]:
                j += 1
            rk = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = rk
            i = j + 1
        return r
    return _pearson(rank(xs), rank(ys))


def summarize(arts: list[ModelArtifact]) -> dict[str, Any]:
    ood = [a.ood_accuracy for a in arts]
    fields = {
        "final_train_loss": [a.final_train_loss for a in arts],
        "parameter_l2": [a.parameter_l2 for a in arts],
        "sharpness_proxy": [a.sharpness_proxy for a in arts],
        "weakness_rotation_norm": [a.weakness_rotation_norm for a in arts],
        "weakness_wrong_group_norm": [a.weakness_wrong_group_norm for a in arts],
        "train_accuracy": [a.train_accuracy for a in arts],
    }
    corrs = {
        name: {
            "pearson": _pearson(values, ood),
            "spearman": _spearman(values, ood),
        }
        for name, values in fields.items()
    }
    return {
        "n_models": len(arts),
        "mean_ood": mean(ood) if ood else 0.0,
        "fraction_perfect_ood": sum(1 for o in ood if o > 0.99) / max(1, len(ood)),
        "correlations": corrs,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-models", type=int, default=64)
    parser.add_argument("--n-rotations", type=int, default=8)
    parser.add_argument("--train-per-class", type=int, default=3)
    parser.add_argument("--epochs", type=int, default=200)
    parser.add_argument("--base-seed", type=int, default=20260609)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    arts = run_sweep(
        n_models=args.n_models,
        n_rotations=args.n_rotations,
        train_per_class=args.train_per_class,
        epochs=args.epochs,
        base_seed=args.base_seed,
    )
    summary = summarize(arts)
    payload = {
        "manifest": {
            "n_models": args.n_models,
            "n_rotations": args.n_rotations,
            "train_per_class": args.train_per_class,
            "epochs": args.epochs,
            "base_seed": args.base_seed,
        },
        "summary": summary,
        "artifacts": [asdict(a) for a in arts],
    }
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2, sort_keys=True))
    print(f"n_models={summary['n_models']} mean_ood={summary['mean_ood']:.3f} "
          f"fraction_perfect={summary['fraction_perfect_ood']:.3f}")
    print("\nPredictors of OOD accuracy:")
    for name, stats in summary["correlations"].items():
        print(f"  {name:30s} pearson={stats['pearson']:+.3f} spearman={stats['spearman']:+.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
