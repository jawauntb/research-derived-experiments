#!/usr/bin/env python3
"""Headline sweep for the Track-A paper.

For each model: train ONCE, then score weakness under (i) the oracle group,
(ii) a group inferred from training data alone, (iii) a random-group control,
all using the same trained model. Then correlate every predictor with OOD.

The headline claim is that `weakness_learned` predicts OOD generalization
nearly as well as `weakness_oracle`, both far better than `weakness_random`,
parameter L_2, sharpness, and train accuracy — demonstrating that weakness
under a *data-inferred* group is a valid stand-in for oracle access on
Perin & Deny 2024's partial-orbit setup.
"""

from __future__ import annotations

import argparse
import json
import math
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean

import numpy as np
import torch
import torch.nn.functional as F

from experiments.learned_symmetry.transform_generator import (
    LearnedGroup,
    infer_rotation_group_from_training,
    learned_group_invariance,
    random_group_baseline,
)
from experiments.rotation_weakness.dataset import (
    RotationSplit,
    make_partial_rotation_split,
    materialize_split,
    rotation_group_elements,
    to_tensors,
)
from experiments.rotation_weakness.neural import (
    ModelConfig,
    _accuracy,
    _augment,
    _rotation_weakness,
    _sharpness_proxy,
    make_model,
)


@dataclass(frozen=True)
class Artifact:
    config: ModelConfig
    n_rotations: int
    train_per_class: int
    ood_accuracy: float
    train_accuracy: float
    parameter_l2: float
    sharpness_proxy: float
    final_train_loss: float
    weakness_oracle: float
    weakness_learned: float
    weakness_random: float
    learned_group_size: int
    learned_group_recall: float
    learned_group_precision: float


def _train_and_score(
    *,
    config: ModelConfig,
    split: RotationSplit,
    candidates: int,
    threshold: float,
) -> Artifact:
    torch.manual_seed(config.seed)
    py_rng = random.Random(config.seed)
    np.random.seed(config.seed)

    train_samples, ood_samples = materialize_split(
        split, samples_per_class_rotation=8, seed=config.seed
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
        loss = F.cross_entropy(model(aug_x), aug_y)
        loss.backward()
        opt.step()
        final_loss = float(loss.item())

    # Score everything against the SAME trained model.
    train_acc = _accuracy(model, train_x, train_y)
    ood_acc = _accuracy(model, ood_x, ood_y)
    weakness_oracle = _rotation_weakness(model, ood_x, n_rotations=split.n_rotations)

    learned = infer_rotation_group_from_training(
        train_x, train_y, n_candidates=candidates, threshold=threshold
    )
    weakness_learned = learned_group_invariance(model, ood_x, learned_group=learned)

    rng_np = np.random.RandomState(config.seed)
    random_group = random_group_baseline(
        n_candidates=candidates, target_size=len(learned), rng=rng_np
    )
    weakness_random = learned_group_invariance(model, ood_x, learned_group=random_group)

    param_l2 = math.sqrt(
        sum(float((p.detach() ** 2).sum().item()) for p in model.parameters())
    )
    sharp = _sharpness_proxy(model, aug_x, aug_y)

    recall, precision = _group_recall_precision(
        learned, set(rotation_group_elements(split.n_rotations))
    )

    return Artifact(
        config=config,
        n_rotations=split.n_rotations,
        train_per_class=len(next(iter(split.train_rotations_per_class.values()))),
        ood_accuracy=float(ood_acc),
        train_accuracy=float(train_acc),
        parameter_l2=param_l2,
        sharpness_proxy=float(sharp),
        final_train_loss=final_loss,
        weakness_oracle=float(weakness_oracle),
        weakness_learned=float(weakness_learned),
        weakness_random=float(weakness_random),
        learned_group_size=len(learned),
        learned_group_recall=float(recall),
        learned_group_precision=float(precision),
    )


def _angle_match(a: float, b: float, tol: float = 7.5) -> bool:
    diff = abs(a - b)
    diff = min(diff, 360.0 - diff)
    return diff < tol


def _group_recall_precision(
    learned: LearnedGroup, oracle: set[float], tol: float = 7.5
) -> tuple[float, float]:
    learned_angles = list(learned.angles())
    if not oracle:
        return 0.0, 0.0
    tp = sum(
        1
        for o in oracle
        if any(_angle_match(o, learned, tol) for learned in learned_angles)
    )
    recall = tp / max(1, len(oracle))
    denom = len(learned_angles)
    if denom > 0:
        tp_p = sum(
            1
            for learned in learned_angles
            if any(_angle_match(o, learned, tol) for o in oracle)
        )
        precision = tp_p / denom
    else:
        precision = 0.0
    return recall, precision


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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-models", type=int, default=48)
    parser.add_argument("--n-rotations", type=int, default=8)
    parser.add_argument("--train-per-class", type=int, default=3)
    parser.add_argument("--epochs", type=int, default=200)
    parser.add_argument("--candidates", type=int, default=24)
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--base-seed", type=int, default=20260609)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    rng = random.Random(args.base_seed)
    artifacts: list[Artifact] = []
    for _ in range(args.n_models):
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
            epochs=args.epochs,
            optimizer=rng.choice(["adam", "sgd"]),
            augmentation=augmentation,
            augmentation_strength=strength,
        )
        seed = rng.randrange(0, 2**31 - 1)
        split = make_partial_rotation_split(
            n_rotations=args.n_rotations,
            train_per_class=args.train_per_class,
            seed=seed,
        )
        artifacts.append(
            _train_and_score(
                config=config,
                split=split,
                candidates=args.candidates,
                threshold=args.threshold,
            )
        )

    ood = [a.ood_accuracy for a in artifacts]
    predictors = {
        "weakness_oracle": [a.weakness_oracle for a in artifacts],
        "weakness_learned": [a.weakness_learned for a in artifacts],
        "weakness_random": [a.weakness_random for a in artifacts],
        "parameter_l2": [a.parameter_l2 for a in artifacts],
        "sharpness_proxy": [a.sharpness_proxy for a in artifacts],
        "train_accuracy": [a.train_accuracy for a in artifacts],
        "final_train_loss": [a.final_train_loss for a in artifacts],
    }
    correlations = {
        name: {"pearson": _pearson(v, ood), "spearman": _spearman(v, ood)}
        for name, v in predictors.items()
    }
    summary = {
        "n_models": len(artifacts),
        "mean_ood": mean(ood) if ood else 0.0,
        "mean_learned_group_size": mean(a.learned_group_size for a in artifacts),
        "mean_learned_group_recall": mean(a.learned_group_recall for a in artifacts),
        "mean_learned_group_precision": mean(a.learned_group_precision for a in artifacts),
        "correlations": correlations,
    }
    payload = {
        "manifest": {
            "n_models": args.n_models,
            "n_rotations": args.n_rotations,
            "train_per_class": args.train_per_class,
            "epochs": args.epochs,
            "candidates": args.candidates,
            "threshold": args.threshold,
            "base_seed": args.base_seed,
        },
        "summary": summary,
        "artifacts": [asdict(a) for a in artifacts],
    }
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str))

    print(f"n_models={summary['n_models']} mean_ood={summary['mean_ood']:.3f}")
    print(f"learned-group: size={summary['mean_learned_group_size']:.1f} "
          f"recall={summary['mean_learned_group_recall']:.3f} "
          f"precision={summary['mean_learned_group_precision']:.3f}")
    print("\nPredictors of OOD accuracy:")
    for name, stats in correlations.items():
        print(f"  {name:25s} pearson={stats['pearson']:+.3f} spearman={stats['spearman']:+.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
