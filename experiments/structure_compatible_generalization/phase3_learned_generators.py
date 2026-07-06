#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Phase 3 learned-generator transfer for structure-compatible generalization.

Phase 2 inferred a supported modular shift family from observed train-label
overlaps. This module weakens that oracle further in two bounded ways:

1. Modular: learn an affine input/label transport family from observed
   consistency evidence, then use that learned family for compatibility scoring
   and train-time regularization.
2. Vision: infer a rotation generator from the training images and use it as
   an augmentation/intervention arm, compared against oracle and random groups.

Both arms emit the common SCG ``DiagnosticRow`` schema.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
import random
from typing import Any, Iterable

import numpy as np

from experiments.structure_compatible_generalization.core import (
    DiagnosticRow,
    rows_to_records,
    summarize_rows,
)
from experiments.structure_compatible_generalization.modular_domain import (
    ModularConfig,
    _load_torch,
    all_pairs,
    base_train_pairs,
    exact_accuracy,
    function_table,
    labels_for_pairs,
    make_model,
    ood_pairs,
    one_hot_pairs,
    pair_index,
    sharpness_proxy,
    shortcut_table,
    true_table,
    true_translation_compatibility,
    truth_value,
    wrong_permutation_compatibility,
    augment_pairs,
)


Pair = tuple[int, int]
AffineOffset = tuple[int, int, int]


@dataclass(frozen=True)
class AffineTransportEvidence:
    da: int
    db: int
    dy: int
    support: int
    violations: int
    admitted: bool

    @property
    def offset(self) -> AffineOffset:
        return (self.da, self.db, self.dy)

    def to_record(self) -> dict[str, int | bool]:
        return asdict(self)


@dataclass(frozen=True)
class LearnedAffineTransportFamily:
    modulus: int
    min_support: int
    max_transports: int
    evidence: tuple[AffineTransportEvidence, ...]

    @property
    def selected_offsets(self) -> tuple[AffineOffset, ...]:
        admitted = [item for item in self.evidence if item.admitted]
        identity = [item for item in admitted if item.offset == (0, 0, 0)]
        non_identity = [item for item in admitted if item.offset != (0, 0, 0)]
        non_identity.sort(
            key=lambda item: (
                -item.support,
                abs(item.da) + abs(item.db) + abs(item.dy),
                item.da,
                item.db,
                item.dy,
            )
        )
        kept = identity[:1] + non_identity[: max(0, self.max_transports - 1)]
        return tuple(item.offset for item in kept)

    @property
    def admitted_count(self) -> int:
        return sum(item.admitted for item in self.evidence)

    @property
    def non_identity_count(self) -> int:
        return sum(item.admitted and item.offset != (0, 0, 0) for item in self.evidence)

    def to_record(self) -> dict[str, Any]:
        return {
            "modulus": self.modulus,
            "min_support": self.min_support,
            "max_transports": self.max_transports,
            "selected_offsets": [list(offset) for offset in self.selected_offsets],
            "admitted_count": self.admitted_count,
            "non_identity_count": self.non_identity_count,
            "evidence": [item.to_record() for item in self.evidence],
        }


def affine_transform_pair(pair: Pair, offset: AffineOffset, modulus: int) -> Pair:
    a, b = pair
    da, db, _dy = offset
    return ((a + da) % modulus, (b + db) % modulus)


def infer_affine_transports(
    train_pairs: Iterable[Pair],
    train_labels: Iterable[int],
    *,
    modulus: int,
    min_support: int,
    max_transports: int = 16,
) -> LearnedAffineTransportFamily:
    """Infer finite affine input/label transports from observed overlaps.

    Candidate offsets have the form ``(a, b, y) -> (a+da, b+db, y+dy)``.
    The procedure does not assume ahead of time that only the first coordinate
    moves or that the label shift must match the input shift. It admits offsets
    whose observed overlaps are label-compatible.
    """
    observed = {
        pair: int(label) % modulus
        for pair, label in zip(train_pairs, train_labels)
    }
    evidence: list[AffineTransportEvidence] = []
    for da in range(modulus):
        for db in range(modulus):
            for dy in range(modulus):
                support = 0
                violations = 0
                offset = (da, db, dy)
                for pair, label in observed.items():
                    shifted = affine_transform_pair(pair, offset, modulus)
                    if shifted not in observed:
                        continue
                    support += 1
                    expected = (label + dy) % modulus
                    if observed[shifted] != expected:
                        violations += 1
                admitted = support >= min_support and violations == 0
                evidence.append(
                    AffineTransportEvidence(
                        da=da,
                        db=db,
                        dy=dy,
                        support=support,
                        violations=violations,
                        admitted=admitted,
                    )
                )

    if not any(item.admitted for item in evidence):
        identity_support = len(observed)
        evidence = [
            AffineTransportEvidence(
                da=0,
                db=0,
                dy=0,
                support=identity_support,
                violations=0,
                admitted=identity_support > 0,
            )
            if item.offset == (0, 0, 0)
            else item
            for item in evidence
        ]
    return LearnedAffineTransportFamily(
        modulus=modulus,
        min_support=min_support,
        max_transports=max_transports,
        evidence=tuple(evidence),
    )


def affine_table_compatibility(
    table: tuple[int, ...],
    *,
    modulus: int,
    offsets: Iterable[AffineOffset],
) -> float:
    materialized = tuple(offset for offset in offsets if offset != (0, 0, 0))
    if not materialized:
        return 0.0
    compatible = 0
    pairs = all_pairs(modulus)
    for offset in materialized:
        _da, _db, dy = offset
        ok = True
        for pair in pairs:
            shifted = affine_transform_pair(pair, offset, modulus)
            lhs = table[pair_index(shifted[0], shifted[1], modulus)]
            rhs = (table[pair_index(pair[0], pair[1], modulus)] + dy) % modulus
            if lhs != rhs:
                ok = False
                break
        compatible += int(ok)
    return compatible / len(materialized)


def learned_affine_compatibility(
    table: tuple[int, ...],
    train_pairs: list[Pair],
    train_labels: list[int],
    *,
    modulus: int,
    min_support: int,
    max_transports: int,
) -> tuple[float, dict[str, Any]]:
    family = infer_affine_transports(
        train_pairs,
        train_labels,
        modulus=modulus,
        min_support=min_support,
        max_transports=max_transports,
    )
    score = affine_table_compatibility(
        table,
        modulus=modulus,
        offsets=family.selected_offsets,
    )
    return score, family.to_record()


def wrong_affine_compatibility(
    table: tuple[int, ...],
    *,
    modulus: int,
    rng: random.Random,
    n_offsets: int,
) -> float:
    offsets: list[AffineOffset] = []
    attempts = 0
    while len(offsets) < n_offsets and attempts < 2000:
        da = rng.randrange(modulus)
        db = rng.randrange(modulus)
        dy = rng.randrange(modulus)
        # For modular addition, dy=(da+db) mod n is the compatible transport.
        if (da, db, dy) != (0, 0, 0) and dy != (da + db) % modulus:
            offsets.append((da, db, dy))
        attempts += 1
    return affine_table_compatibility(table, modulus=modulus, offsets=offsets)


def affine_transport_regularizer(
    model: Any,
    *,
    modulus: int,
    device: Any,
    offsets: tuple[AffineOffset, ...],
) -> Any:
    torch, _nn, F = _load_torch()
    non_identity = tuple(offset for offset in offsets if offset != (0, 0, 0))
    if not non_identity:
        return torch.zeros((), device=device)

    pairs = all_pairs(modulus)
    inputs = one_hot_pairs(pairs, modulus, device)
    base_logits = model(inputs)
    base_probs = F.softmax(base_logits, dim=-1).detach()

    losses = []
    for offset in non_identity:
        _da, _db, dy = offset
        shifted_pairs = [affine_transform_pair(pair, offset, modulus) for pair in pairs]
        shifted_logits = model(one_hot_pairs(shifted_pairs, modulus, device))
        shifted_targets = torch.roll(base_probs, shifts=dy, dims=-1)
        losses.append(
            F.kl_div(
                F.log_softmax(shifted_logits, dim=-1),
                shifted_targets,
                reduction="batchmean",
            )
        )
    return sum(losses) / len(losses)


def exact_generator_rows(
    *,
    modulus: int = 11,
    train_window: int = 4,
    max_transports: int = 16,
) -> list[DiagnosticRow]:
    train = base_train_pairs(modulus, train_window)
    train_labels = [truth_value(a, b, modulus) for a, b in train]
    holdout = ood_pairs(modulus, train_window)
    rows: list[DiagnosticRow] = []
    for name, table in [
        ("true_rule", true_table(modulus)),
        ("local_shortcut", shortcut_table(modulus, train_window)),
    ]:
        learned_score, learned_record = learned_affine_compatibility(
            table,
            train,
            train_labels,
            modulus=modulus,
            min_support=modulus,
            max_transports=max_transports,
        )
        rows.append(
            DiagnosticRow(
                domain="modular_generator_exact",
                model_id=name,
                train_accuracy=exact_accuracy(table, train, modulus),
                id_validation_accuracy=exact_accuracy(table, train, modulus),
                ood_accuracy=exact_accuracy(table, holdout, modulus),
                compatibility_true=true_translation_compatibility(table, modulus),
                compatibility_wrong=wrong_affine_compatibility(
                    table,
                    modulus=modulus,
                    rng=random.Random(991),
                    n_offsets=max_transports,
                ),
                compatibility_discovered=learned_score,
                metadata={
                    "modulus": modulus,
                    "train_window": train_window,
                    "learned_generator": learned_record,
                },
            )
        )
    return rows


def train_one_modular_generator(
    config: ModularConfig,
    *,
    device: str | None = None,
    max_transports: int = 16,
) -> DiagnosticRow:
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
    learned_family = infer_affine_transports(
        train_pairs,
        train_labels,
        modulus=config.modulus,
        min_support=config.compatibility_min_support,
        max_transports=max_transports,
    )
    generator_offsets = learned_family.selected_offsets

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
    final_regularizer = 0.0
    for _ in range(config.epochs):
        model.train()
        opt.zero_grad()
        supervised_loss = F.cross_entropy(model(inputs), targets)
        if config.compatibility_regularization > 0.0:
            regularizer_loss = affine_transport_regularizer(
                model,
                modulus=config.modulus,
                device=torch_device,
                offsets=generator_offsets,
            )
        else:
            regularizer_loss = torch.zeros((), device=torch_device)
        loss = supervised_loss + config.compatibility_regularization * regularizer_loss
        loss.backward()
        opt.step()
        final_loss = float(supervised_loss.detach().cpu().item())
        final_regularizer = float(regularizer_loss.detach().cpu().item())

    table = function_table(model, modulus=config.modulus, device=torch_device)
    base_pairs = base_train_pairs(config.modulus, config.train_window)
    holdout_pairs = ood_pairs(config.modulus, config.train_window)
    param_l2 = math.sqrt(
        sum(float((p.detach().cpu() ** 2).sum().item()) for p in model.parameters())
    )
    sharp = sharpness_proxy(model, inputs, targets)
    learned_score = affine_table_compatibility(
        table,
        modulus=config.modulus,
        offsets=generator_offsets,
    )
    model_id = (
        f"modular-generator-{config.seed}-{config.augmentation}-"
        f"n{config.modulus}-w{config.train_window}-"
        f"reg{config.compatibility_regularization:g}"
    )
    return DiagnosticRow(
        domain="modular_learned_generator",
        model_id=model_id,
        train_accuracy=exact_accuracy(table, base_pairs, config.modulus),
        id_validation_accuracy=exact_accuracy(table, base_pairs, config.modulus),
        ood_accuracy=exact_accuracy(table, holdout_pairs, config.modulus),
        compatibility_true=true_translation_compatibility(table, config.modulus),
        compatibility_wrong=wrong_affine_compatibility(
            table,
            modulus=config.modulus,
            rng=random.Random(config.seed + 1777),
            n_offsets=max_transports,
        ),
        compatibility_discovered=learned_score,
        final_train_loss=final_loss,
        parameter_l2=param_l2,
        sharpness_proxy=sharp,
        metadata={
            "config": asdict(config),
            "table": list(table),
            "learned_generator": learned_family.to_record(),
            "regularizer_offsets": [list(offset) for offset in generator_offsets],
            "final_regularizer_loss": final_regularizer,
        },
    )


def run_modular_generator_sweep(
    *,
    n_configs: int,
    epochs: int,
    base_seed: int,
    device: str | None = None,
    regularization_values: tuple[float, ...] = (0.0, 0.05, 0.2),
    include_exact: bool = True,
    max_transports: int = 16,
) -> list[DiagnosticRow]:
    rng = random.Random(base_seed)
    rows = exact_generator_rows(max_transports=max_transports) if include_exact else []
    for _ in range(n_configs):
        augmentation = rng.choice(
            ["none", "partial_translation", "full_translation", "wrong_identity"]
        )
        count = (
            0
            if augmentation in ("none", "full_translation")
            else rng.choice([1, 2, 3, 4])
        )
        seed = rng.randrange(0, 2**31 - 1)
        modulus = rng.choice([7, 11, 13])
        train_window = rng.choice([2, 3, 4])
        common = {
            "seed": seed,
            "modulus": modulus,
            "train_window": train_window,
            "hidden_width": rng.choice([32, 64, 128]),
            "depth": rng.choice([1, 2, 3]),
            "init_scale": rng.choice([0.5, 1.0, 1.5]),
            "learning_rate": rng.choice([1e-3, 3e-3, 1e-2]),
            "weight_decay": rng.choice([0.0, 1e-4, 1e-3]),
            "epochs": epochs,
            "optimizer": rng.choice(["adam", "sgd"]),
            "augmentation": augmentation,
            "augmentation_count": count,
            "compatibility_min_support": modulus,
        }
        for strength in regularization_values:
            config = ModularConfig(
                **common,
                compatibility_regularization=strength,
            )
            rows.append(
                train_one_modular_generator(
                    config,
                    device=device,
                    max_transports=max_transports,
                )
            )
    return rows


def _rotate_batch(images: Any, degrees: float) -> Any:
    from experiments.rotation_weakness.dataset import rotate_image

    if degrees == 0.0:
        return images.clone()
    torch, _nn, _F = _load_torch()
    out = torch.zeros_like(images)
    for i in range(images.shape[0]):
        rotated = rotate_image(images[i, 0].detach().cpu().numpy(), degrees)
        out[i, 0] = torch.from_numpy(rotated)
    return out


def _augment_images(images: Any, labels: Any, angles: Iterable[float]) -> tuple[Any, Any]:
    torch, _nn, _F = _load_torch()
    chunks_x = [images]
    chunks_y = [labels]
    for angle in angles:
        if angle == 0.0:
            continue
        chunks_x.append(_rotate_batch(images, angle))
        chunks_y.append(labels)
    return torch.cat(chunks_x, dim=0), torch.cat(chunks_y, dim=0)


def _rotation_invariance(
    model: Any,
    eval_x: Any,
    *,
    angles: Iterable[float],
    device: Any,
) -> float:
    model.eval()
    eval_dev = eval_x.to(device)
    with _no_grad():
        base_pred = model(eval_dev).argmax(dim=-1).detach().cpu()
    agree = 0
    total = 0
    for angle in angles:
        if angle == 0.0:
            continue
        rotated = _rotate_batch(eval_x, angle).to(device)
        with _no_grad():
            rot_pred = model(rotated).argmax(dim=-1).detach().cpu()
        agree += int((rot_pred == base_pred).sum().item())
        total += int(rot_pred.shape[0])
    return agree / max(1, total)


def _no_grad() -> Any:
    torch, _nn, _F = _load_torch()
    return torch.no_grad()


def _train_rotation_model(
    config: Any,
    train_x: Any,
    train_y: Any,
    *,
    device: str | None,
) -> tuple[Any, float]:
    torch, _nn, F = _load_torch()
    from experiments.rotation_weakness.neural import make_model

    torch.manual_seed(config.seed)
    np.random.seed(config.seed)
    torch_device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
    model = make_model(config).to(torch_device)
    x_dev = train_x.to(torch_device)
    y_dev = train_y.to(torch_device)
    opt = (
        torch.optim.Adam(
            model.parameters(),
            lr=config.learning_rate,
            weight_decay=config.weight_decay,
        )
        if config.optimizer == "adam"
        else torch.optim.SGD(
            model.parameters(),
            lr=config.learning_rate,
            weight_decay=config.weight_decay,
            momentum=0.9,
        )
    )
    final_loss = math.inf
    for _ in range(config.epochs):
        model.train()
        opt.zero_grad()
        loss = F.cross_entropy(model(x_dev), y_dev)
        loss.backward()
        opt.step()
        final_loss = float(loss.detach().cpu().item())
    return model, final_loss


def _accuracy(model: Any, x: Any, y: Any, *, device: Any) -> float:
    model.eval()
    with _no_grad():
        pred = model(x.to(device)).argmax(dim=-1).detach().cpu()
    return float((pred == y).float().mean().item())


def run_vision_generator_unit(
    *,
    base_seed: int,
    epochs: int,
    n_rotations: int,
    train_per_class: int,
    candidates: int,
    threshold: float,
    device: str | None = None,
) -> list[DiagnosticRow]:
    torch, _nn, _F = _load_torch()
    from experiments.learned_symmetry.transform_generator import (
        infer_rotation_group_from_training,
        random_group_baseline,
    )
    from experiments.rotation_weakness.dataset import (
        make_partial_rotation_split,
        materialize_split,
        rotation_group_elements,
        to_tensors,
    )
    from experiments.rotation_weakness.neural import ModelConfig

    rng = random.Random(base_seed)
    config = ModelConfig(
        seed=rng.randrange(0, 2**31 - 1),
        architecture=rng.choice(["cnn", "mlp"]),
        hidden_width=rng.choice([16, 32, 64]),
        depth=rng.choice([1, 2]),
        init_scale=rng.choice([0.5, 1.0, 1.5]),
        learning_rate=rng.choice([1e-3, 3e-3, 1e-2]),
        weight_decay=rng.choice([0.0, 1e-4]),
        epochs=epochs,
        optimizer=rng.choice(["adam", "sgd"]),
        augmentation="none",
        augmentation_strength=0,
    )
    split_seed = rng.randrange(0, 2**31 - 1)
    split = make_partial_rotation_split(
        n_rotations=n_rotations,
        train_per_class=train_per_class,
        seed=split_seed,
    )
    train_samples, ood_samples = materialize_split(
        split,
        samples_per_class_rotation=8,
        seed=config.seed,
    )
    train_x, train_y = to_tensors(train_samples)
    ood_x, ood_y = to_tensors(ood_samples)
    learned = infer_rotation_group_from_training(
        train_x,
        train_y,
        n_candidates=candidates,
        threshold=threshold,
    )
    random_group = random_group_baseline(
        n_candidates=candidates,
        target_size=len(learned),
        rng=np.random.RandomState(config.seed),
    )
    oracle_angles = rotation_group_elements(n_rotations)
    learned_angles = list(learned.angles())
    random_angles = list(random_group.angles())
    regimes = {
        "none": [],
        "oracle_aug": [angle for angle in oracle_angles if angle != 0.0],
        "learned_aug": [angle for angle in learned_angles if angle != 0.0],
        "random_aug": [angle for angle in random_angles if angle != 0.0],
    }
    torch_device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
    rows: list[DiagnosticRow] = []
    for regime, angles in regimes.items():
        aug_x, aug_y = _augment_images(train_x, train_y, angles)
        model, final_loss = _train_rotation_model(
            config,
            aug_x,
            aug_y,
            device=device,
        )
        param_l2 = math.sqrt(
            sum(float((p.detach().cpu() ** 2).sum().item()) for p in model.parameters())
        )
        rows.append(
            DiagnosticRow(
                domain="vision_rotation_learned_generator",
                model_id=f"vision-generator-{base_seed}-{regime}",
                train_accuracy=_accuracy(model, train_x, train_y, device=torch_device),
                id_validation_accuracy=_accuracy(
                    model,
                    train_x,
                    train_y,
                    device=torch_device,
                ),
                ood_accuracy=_accuracy(model, ood_x, ood_y, device=torch_device),
                compatibility_true=_rotation_invariance(
                    model,
                    ood_x,
                    angles=oracle_angles,
                    device=torch_device,
                ),
                compatibility_wrong=_rotation_invariance(
                    model,
                    ood_x,
                    angles=random_angles,
                    device=torch_device,
                ),
                compatibility_discovered=_rotation_invariance(
                    model,
                    ood_x,
                    angles=learned_angles,
                    device=torch_device,
                ),
                final_train_loss=final_loss,
                parameter_l2=param_l2,
                metadata={
                    "regime": regime,
                    "base_unit": base_seed,
                    "split_seed": split_seed,
                    "config": asdict(config),
                    "learned_group": {
                        "angles": learned_angles,
                        "size": len(learned_angles),
                        "n_candidates": candidates,
                        "threshold": threshold,
                    },
                    "random_group": {
                        "angles": random_angles,
                        "size": len(random_angles),
                    },
                },
            )
        )
    return rows


def run_vision_generator_sweep(
    *,
    n_base: int,
    epochs: int,
    base_seed: int,
    n_rotations: int = 8,
    train_per_class: int = 3,
    candidates: int = 24,
    threshold: float = 0.5,
    device: str | None = None,
) -> list[DiagnosticRow]:
    rows: list[DiagnosticRow] = []
    for i in range(n_base):
        rows.extend(
            run_vision_generator_unit(
                base_seed=base_seed + i * 100_003,
                epochs=epochs,
                n_rotations=n_rotations,
                train_per_class=train_per_class,
                candidates=candidates,
                threshold=threshold,
                device=device,
            )
        )
    return rows


def run_phase3_suite(
    *,
    modular_configs: int,
    vision_base: int,
    modular_epochs: int,
    vision_epochs: int,
    base_seed: int,
    device: str | None = None,
    regularization_values: tuple[float, ...] = (0.0, 0.05, 0.2),
    max_transports: int = 16,
    include_exact: bool = True,
) -> list[DiagnosticRow]:
    rows = run_modular_generator_sweep(
        n_configs=modular_configs,
        epochs=modular_epochs,
        base_seed=base_seed,
        device=device,
        regularization_values=regularization_values,
        include_exact=include_exact,
        max_transports=max_transports,
    )
    rows.extend(
        run_vision_generator_sweep(
            n_base=vision_base,
            epochs=vision_epochs,
            base_seed=base_seed + 44_444,
            device=device,
        )
    )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--modular-configs", type=int, default=24)
    parser.add_argument("--vision-base", type=int, default=8)
    parser.add_argument("--modular-epochs", type=int, default=250)
    parser.add_argument("--vision-epochs", type=int, default=160)
    parser.add_argument("--base-seed", type=int, default=20260706)
    parser.add_argument("--device", choices=["cpu", "cuda"], default=None)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    rows = run_phase3_suite(
        modular_configs=args.modular_configs,
        vision_base=args.vision_base,
        modular_epochs=args.modular_epochs,
        vision_epochs=args.vision_epochs,
        base_seed=args.base_seed,
        device=args.device,
    )
    payload = {
        "kind": "structure-compatible phase3 learned generators",
        "manifest": {
            "modular_configs": args.modular_configs,
            "vision_base": args.vision_base,
            "modular_epochs": args.modular_epochs,
            "vision_epochs": args.vision_epochs,
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
