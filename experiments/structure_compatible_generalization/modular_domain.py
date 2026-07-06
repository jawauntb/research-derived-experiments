#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Modular algorithmic domain for structure-compatible generalization.

The task is a finite table version of modular addition:

    f(a, b) = a + b mod n

Training observes only a local prefix of the first coordinate. A local shortcut
can fit that prefix, but it fails when deployment translates the first
coordinate. The true rule is compatible with the translation family
`a -> a + k, y -> y + k`.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
import random
from typing import Any

from experiments.structure_compatible_generalization.core import (
    DiagnosticRow,
    rows_to_records,
    summarize_rows,
)


Pair = tuple[int, int]
Table = tuple[int, ...]


@dataclass(frozen=True)
class ModularConfig:
    seed: int
    modulus: int
    train_window: int
    hidden_width: int
    depth: int
    init_scale: float
    learning_rate: float
    weight_decay: float
    epochs: int
    optimizer: str
    augmentation: str
    augmentation_count: int


def pair_index(a: int, b: int, modulus: int) -> int:
    return a * modulus + b


def all_pairs(modulus: int) -> list[Pair]:
    return [(a, b) for a in range(modulus) for b in range(modulus)]


def truth_value(a: int, b: int, modulus: int) -> int:
    return (a + b) % modulus


def true_table(modulus: int) -> Table:
    return tuple(truth_value(a, b, modulus) for a, b in all_pairs(modulus))


def shortcut_table(modulus: int, train_window: int) -> Table:
    """A train-perfect local shortcut that defaults to the first coordinate.

    It agrees with the true rule only on the observed local rectangle when
    b=0, and more generally behaves like a prefix memorizer plus identity
    elsewhere.
    """
    values: list[int] = []
    for a, b in all_pairs(modulus):
        if a < train_window:
            values.append(truth_value(a, b, modulus))
        else:
            values.append(a)
    return tuple(values)


def base_train_pairs(modulus: int, train_window: int) -> list[Pair]:
    return [(a, b) for a in range(train_window) for b in range(modulus)]


def ood_pairs(modulus: int, train_window: int) -> list[Pair]:
    return [(a, b) for a in range(train_window, modulus) for b in range(modulus)]


def translated_pair(pair: Pair, shift: int, modulus: int) -> Pair:
    a, b = pair
    return ((a + shift) % modulus, b)


def augment_pairs(
    *,
    modulus: int,
    train_window: int,
    augmentation: str,
    augmentation_count: int,
    rng: random.Random,
) -> list[Pair]:
    base = base_train_pairs(modulus, train_window)
    if augmentation == "none" or augmentation_count == 0:
        return base
    if augmentation == "full_translation":
        return all_pairs(modulus)
    if augmentation == "partial_translation":
        shifts = [s for s in range(1, modulus)]
        rng.shuffle(shifts)
        kept = set(base)
        for shift in shifts[:augmentation_count]:
            for pair in base:
                kept.add(translated_pair(pair, shift, modulus))
        return sorted(kept)
    if augmentation == "wrong_identity":
        kept = set(base)
        candidates = ood_pairs(modulus, train_window)
        rng.shuffle(candidates)
        for pair in candidates[: augmentation_count * modulus]:
            kept.add(pair)
        return sorted(kept)
    raise ValueError(f"unknown augmentation: {augmentation}")


def labels_for_pairs(
    pairs: list[Pair],
    *,
    modulus: int,
    augmentation: str = "none",
    train_window: int,
) -> list[int]:
    labels: list[int] = []
    for a, b in pairs:
        if augmentation == "wrong_identity" and a >= train_window:
            labels.append(a)
        else:
            labels.append(truth_value(a, b, modulus))
    return labels


def exact_accuracy(table: Table, pairs: list[Pair], modulus: int) -> float:
    if not pairs:
        return 0.0
    correct = 0
    for a, b in pairs:
        correct += int(table[pair_index(a, b, modulus)] == truth_value(a, b, modulus))
    return correct / len(pairs)


def true_translation_compatibility(table: Table, modulus: int) -> float:
    compatible = 0
    pairs = all_pairs(modulus)
    for shift in range(modulus):
        ok = True
        for a, b in pairs:
            lhs = table[pair_index((a + shift) % modulus, b, modulus)]
            rhs = (table[pair_index(a, b, modulus)] + shift) % modulus
            if lhs != rhs:
                ok = False
                break
        compatible += int(ok)
    return compatible / modulus


def wrong_permutation_compatibility(
    table: Table,
    modulus: int,
    *,
    rng: random.Random,
    n_perms: int | None = None,
) -> float:
    target = n_perms or modulus
    perms = [tuple(range(modulus))]
    attempts = 0
    while len(perms) < target and attempts < 500:
        p = list(range(modulus))
        rng.shuffle(p)
        cand = tuple(p)
        if cand not in perms and not _is_translation(cand):
            perms.append(cand)
        attempts += 1

    pairs = all_pairs(modulus)
    compatible = 0
    for perm in perms:
        ok = True
        for a, b in pairs:
            lhs = table[pair_index(perm[a], b, modulus)]
            rhs = perm[table[pair_index(a, b, modulus)]]
            if lhs != rhs:
                ok = False
                break
        compatible += int(ok)
    return compatible / max(1, len(perms))


def inferred_translation_compatibility(
    table: Table,
    train_pairs: list[Pair],
    train_labels: list[int],
    modulus: int,
) -> float:
    """Weakly infer admissible translations from observed training pairs."""
    observed = {pair: label for pair, label in zip(train_pairs, train_labels)}
    admitted_shifts: list[int] = []
    for shift in range(modulus):
        ok = True
        for pair, label in observed.items():
            translated = translated_pair(pair, shift, modulus)
            if translated in observed:
                expected = (label + shift) % modulus
                if observed[translated] != expected:
                    ok = False
                    break
        if ok:
            admitted_shifts.append(shift)

    if not admitted_shifts:
        return 0.0
    compatible = 0
    pairs = all_pairs(modulus)
    for shift in admitted_shifts:
        ok = True
        for a, b in pairs:
            lhs = table[pair_index((a + shift) % modulus, b, modulus)]
            rhs = (table[pair_index(a, b, modulus)] + shift) % modulus
            if lhs != rhs:
                ok = False
                break
        compatible += int(ok)
    return compatible / len(admitted_shifts)


def _is_translation(perm: tuple[int, ...]) -> bool:
    if not perm:
        return True
    modulus = len(perm)
    shift = (perm[0] - 0) % modulus
    return all(perm[x] == (x + shift) % modulus for x in range(modulus))


def exact_rows(modulus: int = 11, train_window: int = 4) -> list[DiagnosticRow]:
    rows: list[DiagnosticRow] = []
    train = base_train_pairs(modulus, train_window)
    ood = ood_pairs(modulus, train_window)
    for name, table in [
        ("true_rule", true_table(modulus)),
        ("local_shortcut", shortcut_table(modulus, train_window)),
    ]:
        rows.append(
            DiagnosticRow(
                domain="modular_exact",
                model_id=name,
                train_accuracy=exact_accuracy(table, train, modulus),
                id_validation_accuracy=exact_accuracy(table, train, modulus),
                ood_accuracy=exact_accuracy(table, ood, modulus),
                compatibility_true=true_translation_compatibility(table, modulus),
                compatibility_wrong=wrong_permutation_compatibility(
                    table, modulus, rng=random.Random(1234)
                ),
                compatibility_inferred=inferred_translation_compatibility(
                    table,
                    train,
                    [truth_value(a, b, modulus) for a, b in train],
                    modulus,
                ),
                metadata={"modulus": modulus, "train_window": train_window},
            )
        )
    return rows


def _load_torch() -> tuple[Any, Any, Any]:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    return torch, nn, F


def make_model(
    *,
    modulus: int,
    hidden_width: int,
    depth: int,
    init_scale: float,
) -> Any:
    torch, nn, _F = _load_torch()

    class _ModularMLP(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            layers: list[Any] = []
            input_dim = 2 * modulus
            for _ in range(depth):
                linear = nn.Linear(input_dim, hidden_width)
                with torch.no_grad():
                    linear.weight.mul_(init_scale)
                layers.extend([linear, nn.ReLU()])
                input_dim = hidden_width
            head = nn.Linear(input_dim, modulus)
            with torch.no_grad():
                head.weight.mul_(init_scale)
            layers.append(head)
            self.net = nn.Sequential(*layers)

        def forward(self, x: Any) -> Any:
            return self.net(x)

    return _ModularMLP()


def one_hot_pairs(pairs: list[Pair], modulus: int, device: Any) -> Any:
    torch, _nn, _F = _load_torch()
    out = torch.zeros(len(pairs), 2 * modulus, device=device)
    for row, (a, b) in enumerate(pairs):
        out[row, a] = 1.0
        out[row, modulus + b] = 1.0
    return out


def function_table(
    model: Any,
    *,
    modulus: int,
    device: Any,
) -> Table:
    torch, _nn, _F = _load_torch()
    pairs = all_pairs(modulus)
    model.eval()
    with torch.no_grad():
        preds = model(one_hot_pairs(pairs, modulus, device)).argmax(dim=-1)
    return tuple(int(x) for x in preds.detach().cpu().tolist())


def sharpness_proxy(
    model: Any,
    inputs: Any,
    targets: Any,
) -> float:
    torch, _nn, F = _load_torch()
    model.eval()
    params = [p for p in model.parameters() if p.requires_grad]
    vectors = [
        torch.randint(0, 2, p.shape, device=p.device, dtype=p.dtype) * 2 - 1
        for p in params
    ]
    model.zero_grad()
    loss = F.cross_entropy(model(inputs), targets)
    grads = torch.autograd.grad(loss, params, create_graph=True)
    dot = sum((g * v).sum() for g, v in zip(grads, vectors))
    hv = torch.autograd.grad(dot, params, retain_graph=False)
    return float(sum((h * v).sum().detach().cpu().item() for h, v in zip(hv, vectors)))


def train_one(config: ModularConfig, *, device: str | None = None) -> DiagnosticRow:
    torch, _nn, F = _load_torch()
    rng = random.Random(config.seed)
    torch.manual_seed(config.seed)
    torch_device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))

    train_pairs = augment_pairs(
        modulus=config.modulus,
        train_window=config.train_window,
        augmentation=config.augmentation,
        augmentation_count=config.augmentation_count,
        rng=rng,
    )
    train_labels = labels_for_pairs(
        train_pairs,
        modulus=config.modulus,
        augmentation=config.augmentation,
        train_window=config.train_window,
    )

    inputs = one_hot_pairs(train_pairs, config.modulus, torch_device)
    targets = torch.tensor(train_labels, dtype=torch.long, device=torch_device)
    model = make_model(
        modulus=config.modulus,
        hidden_width=config.hidden_width,
        depth=config.depth,
        init_scale=config.init_scale,
    ).to(torch_device)

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
        loss = F.cross_entropy(model(inputs), targets)
        loss.backward()
        opt.step()
        final_loss = float(loss.detach().cpu().item())

    table = function_table(model, modulus=config.modulus, device=torch_device)
    base_pairs = base_train_pairs(config.modulus, config.train_window)
    holdout_pairs = ood_pairs(config.modulus, config.train_window)
    param_l2 = math.sqrt(
        sum(float((p.detach().cpu() ** 2).sum().item()) for p in model.parameters())
    )
    sharp = sharpness_proxy(model, inputs, targets)
    model_id = (
        f"modular-{config.seed}-{config.augmentation}-"
        f"n{config.modulus}-w{config.train_window}"
    )
    return DiagnosticRow(
        domain="modular_neural",
        model_id=model_id,
        train_accuracy=exact_accuracy(table, base_pairs, config.modulus),
        id_validation_accuracy=exact_accuracy(table, base_pairs, config.modulus),
        ood_accuracy=exact_accuracy(table, holdout_pairs, config.modulus),
        compatibility_true=true_translation_compatibility(table, config.modulus),
        compatibility_wrong=wrong_permutation_compatibility(
            table, config.modulus, rng=random.Random(config.seed + 991)
        ),
        compatibility_inferred=inferred_translation_compatibility(
            table, train_pairs, train_labels, config.modulus
        ),
        final_train_loss=final_loss,
        parameter_l2=param_l2,
        sharpness_proxy=sharp,
        metadata={"config": asdict(config), "table": list(table)},
    )


def run_sweep(
    *,
    n_models: int,
    epochs: int,
    base_seed: int,
    device: str | None = None,
    include_exact: bool = True,
) -> list[DiagnosticRow]:
    rng = random.Random(base_seed)
    rows = exact_rows() if include_exact else []
    for _ in range(n_models):
        augmentation = rng.choice(
            ["none", "partial_translation", "full_translation", "wrong_identity"]
        )
        count = 0 if augmentation in ("none", "full_translation") else rng.choice([1, 2, 3, 4])
        config = ModularConfig(
            seed=rng.randrange(0, 2**31 - 1),
            modulus=rng.choice([7, 11, 13]),
            train_window=rng.choice([2, 3, 4]),
            hidden_width=rng.choice([32, 64, 128]),
            depth=rng.choice([1, 2, 3]),
            init_scale=rng.choice([0.5, 1.0, 1.5]),
            learning_rate=rng.choice([1e-3, 3e-3, 1e-2]),
            weight_decay=rng.choice([0.0, 1e-4, 1e-3]),
            epochs=epochs,
            optimizer=rng.choice(["adam", "sgd"]),
            augmentation=augmentation,
            augmentation_count=count,
        )
        rows.append(train_one(config, device=device))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-models", type=int, default=32)
    parser.add_argument("--epochs", type=int, default=250)
    parser.add_argument("--base-seed", type=int, default=20260706)
    parser.add_argument("--device", choices=["cpu", "cuda"], default=None)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    rows = run_sweep(
        n_models=args.n_models,
        epochs=args.epochs,
        base_seed=args.base_seed,
        device=args.device,
    )
    payload = {
        "kind": "modular algorithmic compatibility sweep",
        "manifest": {
            "n_models": args.n_models,
            "epochs": args.epochs,
            "base_seed": args.base_seed,
            "device": args.device,
        },
        "summary": summarize_rows(rows),
        "rows": rows_to_records(rows),
    }
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
