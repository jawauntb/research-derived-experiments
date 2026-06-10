#!/usr/bin/env python3
"""Causal validation: does training with the learned-group as data
augmentation actually improve OOD generalization, or is the correlation
between learned-group weakness and OOD spurious?

For each of N base seeds, we train the SAME architecture/init/optimizer
under FOUR augmentation regimes:

  1. `none`           — no augmentation; train on the biased prefix only.
  2. `oracle_aug`     — augment with rotations from the true Z_n group
                        (upper bound; uses oracle access).
  3. `learned_aug`    — augment with rotations from the data-inferred
                        group; NO oracle access.
  4. `random_aug`     — augment with the same number of randomly-chosen
                        rotations from the candidate set (control).

Per-model deltas of OOD accuracy isolate the causal effect of *which*
augmentation regime was applied, with everything else held constant.

The headline claim is `learned_aug` lifts OOD comparably to `oracle_aug`,
both clearly above `none` and `random_aug`.
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
    infer_rotation_group_from_training,
    random_group_baseline,
)
from experiments.rotation_weakness.dataset import (
    make_partial_rotation_split,
    materialize_split,
    rotate_image,
    rotation_group_elements,
    to_tensors,
)
from experiments.rotation_weakness.neural import (
    ModelConfig,
    _accuracy,
    make_model,
)


@dataclass(frozen=True)
class CausalRow:
    base_seed: int
    config_name: str
    architecture: str
    hidden_width: int
    depth: int
    init_scale: float
    learning_rate: float
    optimizer: str
    regime: str  # "none" | "oracle_aug" | "learned_aug" | "random_aug"
    train_accuracy: float
    ood_accuracy: float
    final_train_loss: float


def _rotate_batch(images: torch.Tensor, degrees: float) -> torch.Tensor:
    if degrees == 0.0:
        return images
    out = torch.zeros_like(images)
    for i in range(images.shape[0]):
        out[i, 0] = torch.from_numpy(rotate_image(images[i, 0].cpu().numpy(), degrees))
    return out


def _augment_with_angles(
    images: torch.Tensor, labels: torch.Tensor, *, angles: list[float]
) -> tuple[torch.Tensor, torch.Tensor]:
    """Augment by applying every angle in `angles` (excluding identity)."""
    chunks_x = [images]
    chunks_y = [labels]
    for deg in angles:
        if deg == 0.0:
            continue
        chunks_x.append(_rotate_batch(images, deg))
        chunks_y.append(labels)
    return torch.cat(chunks_x, dim=0), torch.cat(chunks_y, dim=0)


def _train_with_aug(
    *,
    config: ModelConfig,
    aug_x: torch.Tensor,
    aug_y: torch.Tensor,
) -> tuple[torch.nn.Module, float]:
    torch.manual_seed(config.seed)
    np.random.seed(config.seed)
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
    return model, final_loss


def run_causal_unit(
    *,
    config: ModelConfig,
    n_rotations: int,
    train_per_class: int,
    split_seed: int,
    candidates: int,
    threshold: float,
) -> list[CausalRow]:
    """For one architecture/split, train under all 4 regimes and return rows."""
    split = make_partial_rotation_split(
        n_rotations=n_rotations, train_per_class=train_per_class, seed=split_seed
    )
    train_samples, ood_samples = materialize_split(
        split, samples_per_class_rotation=8, seed=config.seed
    )
    train_x, train_y = to_tensors(train_samples)
    ood_x, ood_y = to_tensors(ood_samples)

    learned = infer_rotation_group_from_training(
        train_x, train_y, n_candidates=candidates, threshold=threshold
    )
    rng_np = np.random.RandomState(config.seed)
    random_grp = random_group_baseline(
        n_candidates=candidates, target_size=len(learned), rng=rng_np
    )

    oracle_angles = rotation_group_elements(n_rotations)
    learned_angles = list(learned.angles())
    random_angles = list(random_grp.angles())

    regimes = {
        "none": [],
        "oracle_aug": [a for a in oracle_angles if a != 0.0],
        "learned_aug": [a for a in learned_angles if a != 0.0],
        "random_aug": [a for a in random_angles if a != 0.0],
    }

    rows: list[CausalRow] = []
    for name, angles in regimes.items():
        aug_x, aug_y = _augment_with_angles(train_x, train_y, angles=angles)
        model, final_loss = _train_with_aug(config=config, aug_x=aug_x, aug_y=aug_y)
        train_acc = _accuracy(model, train_x, train_y)
        ood_acc = _accuracy(model, ood_x, ood_y)
        rows.append(
            CausalRow(
                base_seed=split_seed,
                config_name=f"{config.architecture}_h{config.hidden_width}_d{config.depth}_{config.optimizer}_lr{config.learning_rate}",
                architecture=config.architecture,
                hidden_width=config.hidden_width,
                depth=config.depth,
                init_scale=config.init_scale,
                learning_rate=config.learning_rate,
                optimizer=config.optimizer,
                regime=name,
                train_accuracy=float(train_acc),
                ood_accuracy=float(ood_acc),
                final_train_loss=float(final_loss),
            )
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-base", type=int, default=24)
    parser.add_argument("--n-rotations", type=int, default=8)
    parser.add_argument("--train-per-class", type=int, default=3)
    parser.add_argument("--epochs", type=int, default=250)
    parser.add_argument("--candidates", type=int, default=24)
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--base-seed", type=int, default=20260609)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    rng = random.Random(args.base_seed)
    all_rows: list[CausalRow] = []
    for _ in range(args.n_base):
        config = ModelConfig(
            seed=rng.randrange(0, 2**31 - 1),
            architecture=rng.choice(["cnn", "mlp"]),
            hidden_width=rng.choice([16, 32, 64]),
            depth=rng.choice([1, 2]),
            init_scale=rng.choice([0.5, 1.0, 1.5]),
            learning_rate=rng.choice([1e-3, 3e-3, 1e-2]),
            weight_decay=rng.choice([0.0, 1e-4]),
            epochs=args.epochs,
            optimizer=rng.choice(["adam", "sgd"]),
            augmentation="none",  # unused in causal unit; we apply augs directly
            augmentation_strength=0,
        )
        split_seed = rng.randrange(0, 2**31 - 1)
        rows = run_causal_unit(
            config=config,
            n_rotations=args.n_rotations,
            train_per_class=args.train_per_class,
            split_seed=split_seed,
            candidates=args.candidates,
            threshold=args.threshold,
        )
        all_rows.extend(rows)

    by_regime: dict[str, list[float]] = {}
    for r in all_rows:
        by_regime.setdefault(r.regime, []).append(r.ood_accuracy)

    # Paired per-base deltas: aug regime minus `none` regime.
    deltas_vs_none: dict[str, list[float]] = {
        "oracle_aug": [],
        "learned_aug": [],
        "random_aug": [],
    }
    by_base = {}
    for r in all_rows:
        by_base.setdefault(r.base_seed, {})[r.regime] = r
    for base, regimes in by_base.items():
        if "none" not in regimes:
            continue
        baseline = regimes["none"].ood_accuracy
        for reg in deltas_vs_none:
            if reg in regimes:
                deltas_vs_none[reg].append(regimes[reg].ood_accuracy - baseline)

    summary = {
        "n_units": args.n_base,
        "mean_ood_by_regime": {k: mean(v) if v else 0.0 for k, v in by_regime.items()},
        "mean_delta_vs_none": {k: mean(v) if v else 0.0 for k, v in deltas_vs_none.items()},
    }
    payload = {
        "manifest": {
            "n_base": args.n_base,
            "n_rotations": args.n_rotations,
            "train_per_class": args.train_per_class,
            "epochs": args.epochs,
            "candidates": args.candidates,
            "threshold": args.threshold,
            "base_seed": args.base_seed,
        },
        "summary": summary,
        "rows": [asdict(r) for r in all_rows],
    }
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2, sort_keys=True))

    print("Mean OOD by regime:")
    for k, v in summary["mean_ood_by_regime"].items():
        print(f"  {k:14s} {v:+.4f}")
    print("\nMean per-model delta vs none:")
    for k, v in summary["mean_delta_vs_none"].items():
        print(f"  {k:14s} {v:+.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
