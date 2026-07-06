#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Template-language substitution domain for SCG.

This benchmark turns the modular transport result into a rendered
language/template task. Examples are short text-like templates containing a
number word and an offset word. The label is still finite and known:

    f(a, b, template) = a + b mod n

Training observes only a local prefix of the first number-word slot. The
deployment shift substitutes held-out number words. A learned generator is
inferred from observed input/label overlaps, then used for compatibility
scoring and train-time regularization.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
import random
from typing import Any, Iterable

from experiments.structure_compatible_generalization.core import (
    DiagnosticRow,
    rows_to_records,
    summarize_rows,
)
from experiments.structure_compatible_generalization.modular_domain import (
    _load_torch,
    sharpness_proxy,
)


Example = tuple[int, int, int]
LanguageTable = tuple[int, ...]
LanguageTransform = tuple[str, int, int, int]

NUMBER_WORDS = (
    "zero",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "eleven",
    "twelve",
)

TEMPLATES = (
    "compute {a} plus {b}",
    "evaluate {a} with offset {b}",
    "return sum of {a} and {b}",
    "map {a} through shift {b}",
)


@dataclass(frozen=True)
class LanguageTemplateConfig:
    seed: int
    modulus: int
    train_window: int
    n_templates: int
    hidden_width: int
    depth: int
    init_scale: float
    learning_rate: float
    weight_decay: float
    epochs: int
    optimizer: str
    augmentation: str
    augmentation_count: int
    compatibility_regularization: float = 0.0
    compatibility_min_support: int = 1


@dataclass(frozen=True)
class LanguageTransformEvidence:
    kind: str
    source: int
    target: int
    dy: int
    support: int
    violations: int
    admitted: bool

    @property
    def transform(self) -> LanguageTransform:
        return (self.kind, self.source, self.target, self.dy)

    def to_record(self) -> dict[str, int | str | bool]:
        return asdict(self)


@dataclass(frozen=True)
class LearnedLanguageTransformFamily:
    modulus: int
    n_templates: int
    min_support: int
    max_transforms: int
    evidence: tuple[LanguageTransformEvidence, ...]

    @property
    def selected_transforms(self) -> tuple[LanguageTransform, ...]:
        admitted = [
            item for item in self.evidence if item.admitted and not _is_identity(item)
        ]
        priority = {"a_shift": 0, "b_shift": 1, "template_swap": 2}
        admitted.sort(
            key=lambda item: (
                priority.get(item.kind, 99),
                -int(item.dy != 0),
                -item.support,
                item.source,
                item.target,
                item.dy,
            )
        )
        return tuple(item.transform for item in admitted[: self.max_transforms])

    @property
    def admitted_count(self) -> int:
        return sum(item.admitted for item in self.evidence)

    @property
    def non_identity_count(self) -> int:
        return sum(item.admitted and not _is_identity(item) for item in self.evidence)

    def to_record(self) -> dict[str, Any]:
        return {
            "modulus": self.modulus,
            "n_templates": self.n_templates,
            "min_support": self.min_support,
            "max_transforms": self.max_transforms,
            "selected_transforms": [
                list(transform) for transform in self.selected_transforms
            ],
            "admitted_count": self.admitted_count,
            "non_identity_count": self.non_identity_count,
            "evidence": [item.to_record() for item in self.evidence],
        }


def _is_identity(item: LanguageTransformEvidence) -> bool:
    if item.kind in {"a_shift", "b_shift"}:
        return item.source == 0 and item.dy == 0
    return item.kind == "template_swap" and item.source == item.target and item.dy == 0


def example_index(example: Example, modulus: int, n_templates: int) -> int:
    a, b, template = example
    return (a * modulus + b) * n_templates + template


def all_examples(modulus: int, n_templates: int) -> list[Example]:
    return [
        (a, b, template)
        for a in range(modulus)
        for b in range(modulus)
        for template in range(n_templates)
    ]


def base_train_examples(
    modulus: int,
    train_window: int,
    n_templates: int,
) -> list[Example]:
    return [
        (a, b, template)
        for a in range(train_window)
        for b in range(modulus)
        for template in range(n_templates)
    ]


def ood_examples(modulus: int, train_window: int, n_templates: int) -> list[Example]:
    return [
        (a, b, template)
        for a in range(train_window, modulus)
        for b in range(modulus)
        for template in range(n_templates)
    ]


def truth_value(a: int, b: int, modulus: int) -> int:
    return (a + b) % modulus


def render_example(example: Example, modulus: int) -> str:
    a, b, template = example
    if modulus > len(NUMBER_WORDS):
        raise ValueError("modulus exceeds available number words")
    return TEMPLATES[template].format(a=NUMBER_WORDS[a], b=NUMBER_WORDS[b])


def default_min_support(modulus: int, train_window: int, n_templates: int) -> int:
    return modulus * min(train_window, n_templates)


def true_language_table(modulus: int, n_templates: int) -> LanguageTable:
    return tuple(
        truth_value(a, b, modulus)
        for a, b, _template in all_examples(modulus, n_templates)
    )


def local_template_shortcut_table(
    modulus: int,
    train_window: int,
    n_templates: int,
) -> LanguageTable:
    values: list[int] = []
    for a, b, template in all_examples(modulus, n_templates):
        if a < train_window:
            values.append(truth_value(a, b, modulus))
        else:
            values.append((a * (template + 1)) % modulus)
    return tuple(values)


def exact_accuracy(
    table: LanguageTable,
    examples: list[Example],
    modulus: int,
    n_templates: int,
) -> float:
    if not examples:
        return 0.0
    correct = 0
    for example in examples:
        a, b, _template = example
        correct += int(
            table[example_index(example, modulus, n_templates)]
            == truth_value(a, b, modulus)
        )
    return correct / len(examples)


def apply_transform(
    example: Example,
    transform: LanguageTransform,
    modulus: int,
) -> Example | None:
    kind, source, target, _dy = transform
    a, b, template = example
    if kind == "a_shift":
        return ((a + source) % modulus, b, template)
    if kind == "b_shift":
        return (a, (b + source) % modulus, template)
    if kind == "template_swap":
        if template != source:
            return None
        return (a, b, target)
    raise ValueError(f"unknown transform kind: {kind}")


def candidate_transforms(modulus: int, n_templates: int) -> list[LanguageTransform]:
    candidates: list[LanguageTransform] = []
    for shift in range(modulus):
        for dy in range(modulus):
            candidates.append(("a_shift", shift, 0, dy))
            candidates.append(("b_shift", shift, 0, dy))
    for src in range(n_templates):
        for dst in range(n_templates):
            for dy in range(modulus):
                candidates.append(("template_swap", src, dst, dy))
    return candidates


def infer_language_transforms(
    train_examples_: Iterable[Example],
    train_labels: Iterable[int],
    *,
    modulus: int,
    n_templates: int,
    min_support: int,
    max_transforms: int = 24,
) -> LearnedLanguageTransformFamily:
    observed = {
        example: int(label) % modulus
        for example, label in zip(train_examples_, train_labels)
    }
    evidence: list[LanguageTransformEvidence] = []
    for transform in candidate_transforms(modulus, n_templates):
        kind, source, target, dy = transform
        support = 0
        violations = 0
        for example, label in observed.items():
            transformed = apply_transform(example, transform, modulus)
            if transformed is None or transformed not in observed:
                continue
            support += 1
            expected = (label + dy) % modulus
            if observed[transformed] != expected:
                violations += 1
        evidence.append(
            LanguageTransformEvidence(
                kind=kind,
                source=source,
                target=target,
                dy=dy,
                support=support,
                violations=violations,
                admitted=support >= min_support and violations == 0,
            )
        )
    return LearnedLanguageTransformFamily(
        modulus=modulus,
        n_templates=n_templates,
        min_support=min_support,
        max_transforms=max_transforms,
        evidence=tuple(evidence),
    )


def language_table_compatibility(
    table: LanguageTable,
    *,
    modulus: int,
    n_templates: int,
    transforms: Iterable[LanguageTransform],
) -> float:
    materialized = list(transforms)
    if not materialized:
        return 0.0
    examples = all_examples(modulus, n_templates)
    compatible = 0
    for transform in materialized:
        _kind, _source, _target, dy = transform
        ok = True
        checked = 0
        for example in examples:
            transformed = apply_transform(example, transform, modulus)
            if transformed is None:
                continue
            checked += 1
            lhs = table[example_index(transformed, modulus, n_templates)]
            rhs = (table[example_index(example, modulus, n_templates)] + dy) % modulus
            if lhs != rhs:
                ok = False
                break
        compatible += int(ok and checked > 0)
    return compatible / len(materialized)


def true_language_transforms(
    modulus: int,
    n_templates: int,
) -> tuple[LanguageTransform, ...]:
    numeric = [
        ("a_shift", shift, 0, shift)
        for shift in range(1, modulus)
    ] + [
        ("b_shift", shift, 0, shift)
        for shift in range(1, modulus)
    ]
    templates = [
        ("template_swap", src, dst, 0)
        for src in range(n_templates)
        for dst in range(n_templates)
        if src != dst
    ]
    return tuple(numeric + templates)


def true_language_compatibility(
    table: LanguageTable,
    modulus: int,
    n_templates: int,
) -> float:
    return language_table_compatibility(
        table,
        modulus=modulus,
        n_templates=n_templates,
        transforms=true_language_transforms(modulus, n_templates),
    )


def discovered_language_compatibility(
    table: LanguageTable,
    train_examples_: list[Example],
    train_labels: list[int],
    *,
    modulus: int,
    n_templates: int,
    min_support: int,
    max_transforms: int,
) -> tuple[float, dict[str, Any]]:
    family = infer_language_transforms(
        train_examples_,
        train_labels,
        modulus=modulus,
        n_templates=n_templates,
        min_support=min_support,
        max_transforms=max_transforms,
    )
    score = language_table_compatibility(
        table,
        modulus=modulus,
        n_templates=n_templates,
        transforms=family.selected_transforms,
    )
    return score, family.to_record()


def wrong_language_compatibility(
    table: LanguageTable,
    *,
    modulus: int,
    n_templates: int,
    rng: random.Random,
    n_transforms: int,
) -> float:
    wrong: list[LanguageTransform] = []
    attempts = 0
    while len(wrong) < n_transforms and attempts < 5000:
        kind = rng.choice(["a_shift", "b_shift", "template_swap"])
        if kind == "template_swap":
            src = rng.randrange(n_templates)
            dst = rng.randrange(n_templates)
            dy = rng.randrange(1, modulus)
            if src != dst:
                wrong.append((kind, src, dst, dy))
        else:
            shift = rng.randrange(1, modulus)
            dy = rng.randrange(modulus)
            if dy != shift:
                wrong.append((kind, shift, 0, dy))
        attempts += 1
    return language_table_compatibility(
        table,
        modulus=modulus,
        n_templates=n_templates,
        transforms=wrong,
    )


def augment_examples(
    *,
    modulus: int,
    train_window: int,
    n_templates: int,
    augmentation: str,
    augmentation_count: int,
    rng: random.Random,
) -> list[Example]:
    base = base_train_examples(modulus, train_window, n_templates)
    if augmentation == "none" or augmentation_count == 0:
        return base
    if augmentation == "partial_a_substitution":
        shifts = [shift for shift in range(1, modulus)]
        rng.shuffle(shifts)
        kept = set(base)
        for shift in shifts[:augmentation_count]:
            for example in base:
                transformed = apply_transform(
                    example,
                    ("a_shift", shift, 0, shift),
                    modulus,
                )
                if transformed is not None:
                    kept.add(transformed)
        return sorted(kept)
    if augmentation == "wrong_substitution":
        shifts = [shift for shift in range(1, modulus)]
        rng.shuffle(shifts)
        kept = set(base)
        for shift in shifts[:augmentation_count]:
            for a, b, template in base:
                kept.add(((a + shift) % modulus, b, template))
        return sorted(kept)
    raise ValueError(f"unknown augmentation: {augmentation}")


def labels_for_examples(
    examples: list[Example],
    *,
    modulus: int,
    train_window: int,
    augmentation: str = "none",
) -> list[int]:
    labels: list[int] = []
    for a, b, template in examples:
        if augmentation == "wrong_substitution" and a >= train_window:
            labels.append((a * (template + 1)) % modulus)
        else:
            labels.append(truth_value(a, b, modulus))
    return labels


def one_hot_examples(
    examples: list[Example],
    modulus: int,
    n_templates: int,
    device: Any,
) -> Any:
    torch, _nn, _F = _load_torch()
    out = torch.zeros(len(examples), 2 * modulus + n_templates, device=device)
    for row, (a, b, template) in enumerate(examples):
        out[row, a] = 1.0
        out[row, modulus + b] = 1.0
        out[row, 2 * modulus + template] = 1.0
    return out


def make_language_model(
    *,
    modulus: int,
    n_templates: int,
    hidden_width: int,
    depth: int,
    init_scale: float,
) -> Any:
    torch, nn, _F = _load_torch()

    class _LanguageTemplateMLP(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            layers: list[Any] = []
            input_dim = 2 * modulus + n_templates
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

    return _LanguageTemplateMLP()


def function_table(
    model: Any,
    *,
    modulus: int,
    n_templates: int,
    device: Any,
) -> LanguageTable:
    torch, _nn, _F = _load_torch()
    examples = all_examples(modulus, n_templates)
    model.eval()
    with torch.no_grad():
        preds = model(
            one_hot_examples(examples, modulus, n_templates, device)
        ).argmax(dim=-1)
    return tuple(int(x) for x in preds.detach().cpu().tolist())


def make_regularizer_batch(
    *,
    modulus: int,
    n_templates: int,
    device: Any,
    transforms: tuple[LanguageTransform, ...],
) -> tuple[Any, Any, Any] | None:
    torch, _nn, _F = _load_torch()
    if not transforms:
        return None

    source_examples: list[Example] = []
    target_examples: list[Example] = []
    dy_values: list[int] = []
    examples = all_examples(modulus, n_templates)
    for transform in transforms:
        _kind, _source, _target, dy = transform
        for example in examples:
            transformed = apply_transform(example, transform, modulus)
            if transformed is None:
                continue
            source_examples.append(example)
            target_examples.append(transformed)
            dy_values.append(dy)
    if not source_examples:
        return None
    source_inputs = one_hot_examples(source_examples, modulus, n_templates, device)
    target_inputs = one_hot_examples(target_examples, modulus, n_templates, device)
    dy_tensor = torch.tensor(dy_values, dtype=torch.long, device=device)
    return source_inputs, target_inputs, dy_tensor


def language_transform_regularizer(
    model: Any,
    *,
    modulus: int,
    device: Any,
    regularizer_batch: tuple[Any, Any, Any] | None,
) -> Any:
    torch, _nn, F = _load_torch()
    if regularizer_batch is None:
        return torch.zeros((), device=device)

    source_inputs, target_inputs, dy_tensor = regularizer_batch
    source_probs = F.softmax(model(source_inputs), dim=-1).detach()
    target_logits = model(target_inputs)
    classes = torch.arange(modulus, device=device).unsqueeze(0)
    gather_index = (classes - dy_tensor.unsqueeze(1)) % modulus
    target_probs = source_probs.gather(1, gather_index)
    return F.kl_div(
        F.log_softmax(target_logits, dim=-1),
        target_probs,
        reduction="batchmean",
    )


def exact_language_rows(
    *,
    modulus: int = 11,
    train_window: int = 4,
    n_templates: int = 4,
    max_transforms: int = 24,
) -> list[DiagnosticRow]:
    train = base_train_examples(modulus, train_window, n_templates)
    train_labels = [truth_value(a, b, modulus) for a, b, _template in train]
    holdout = ood_examples(modulus, train_window, n_templates)
    rows: list[DiagnosticRow] = []
    for name, table in [
        ("true_rule", true_language_table(modulus, n_templates)),
        ("local_template_shortcut", local_template_shortcut_table(
            modulus,
            train_window,
            n_templates,
        )),
    ]:
        learned_score, learned_record = discovered_language_compatibility(
            table,
            train,
            train_labels,
            modulus=modulus,
            n_templates=n_templates,
            min_support=default_min_support(modulus, train_window, n_templates),
            max_transforms=max_transforms,
        )
        rows.append(
            DiagnosticRow(
                domain="language_template_exact",
                model_id=name,
                train_accuracy=exact_accuracy(
                    table,
                    train,
                    modulus,
                    n_templates,
                ),
                id_validation_accuracy=exact_accuracy(
                    table,
                    train,
                    modulus,
                    n_templates,
                ),
                ood_accuracy=exact_accuracy(
                    table,
                    holdout,
                    modulus,
                    n_templates,
                ),
                compatibility_true=true_language_compatibility(
                    table,
                    modulus,
                    n_templates,
                ),
                compatibility_wrong=wrong_language_compatibility(
                    table,
                    modulus=modulus,
                    n_templates=n_templates,
                    rng=random.Random(6021),
                    n_transforms=max_transforms,
                ),
                compatibility_discovered=learned_score,
                metadata={
                    "modulus": modulus,
                    "train_window": train_window,
                    "n_templates": n_templates,
                    "learned_generator": learned_record,
                    "rendered_example": render_example(train[0], modulus),
                },
            )
        )
    return rows


def train_one_language_template(
    config: LanguageTemplateConfig,
    *,
    device: str | None = None,
    max_transforms: int = 24,
) -> DiagnosticRow:
    torch, _nn, F = _load_torch()
    rng = random.Random(config.seed)
    torch.manual_seed(config.seed)
    torch_device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))

    train = augment_examples(
        modulus=config.modulus,
        train_window=config.train_window,
        n_templates=config.n_templates,
        augmentation=config.augmentation,
        augmentation_count=config.augmentation_count,
        rng=rng,
    )
    train_labels = labels_for_examples(
        train,
        modulus=config.modulus,
        train_window=config.train_window,
        augmentation=config.augmentation,
    )
    learned_family = infer_language_transforms(
        train,
        train_labels,
        modulus=config.modulus,
        n_templates=config.n_templates,
        min_support=config.compatibility_min_support,
        max_transforms=max_transforms,
    )
    transforms = learned_family.selected_transforms
    inputs = one_hot_examples(
        train,
        config.modulus,
        config.n_templates,
        torch_device,
    )
    targets = torch.tensor(train_labels, dtype=torch.long, device=torch_device)
    regularizer_batch = make_regularizer_batch(
        modulus=config.modulus,
        n_templates=config.n_templates,
        device=torch_device,
        transforms=transforms,
    )
    model = make_language_model(
        modulus=config.modulus,
        n_templates=config.n_templates,
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
            regularizer_loss = language_transform_regularizer(
                model,
                modulus=config.modulus,
                device=torch_device,
                regularizer_batch=regularizer_batch,
            )
        else:
            regularizer_loss = torch.zeros((), device=torch_device)
        loss = supervised_loss + config.compatibility_regularization * regularizer_loss
        loss.backward()
        opt.step()
        final_loss = float(supervised_loss.detach().cpu().item())
        final_regularizer = float(regularizer_loss.detach().cpu().item())

    table = function_table(
        model,
        modulus=config.modulus,
        n_templates=config.n_templates,
        device=torch_device,
    )
    base = base_train_examples(
        config.modulus,
        config.train_window,
        config.n_templates,
    )
    holdout = ood_examples(
        config.modulus,
        config.train_window,
        config.n_templates,
    )
    param_l2 = math.sqrt(
        sum(float((p.detach().cpu() ** 2).sum().item()) for p in model.parameters())
    )
    sharp = sharpness_proxy(model, inputs, targets)
    discovered_score = language_table_compatibility(
        table,
        modulus=config.modulus,
        n_templates=config.n_templates,
        transforms=transforms,
    )
    model_id = (
        f"language-template-{config.seed}-{config.augmentation}-"
        f"n{config.modulus}-w{config.train_window}-"
        f"reg{config.compatibility_regularization:g}"
    )
    return DiagnosticRow(
        domain="language_template_substitution",
        model_id=model_id,
        train_accuracy=exact_accuracy(
            table,
            base,
            config.modulus,
            config.n_templates,
        ),
        id_validation_accuracy=exact_accuracy(
            table,
            base,
            config.modulus,
            config.n_templates,
        ),
        ood_accuracy=exact_accuracy(
            table,
            holdout,
            config.modulus,
            config.n_templates,
        ),
        compatibility_true=true_language_compatibility(
            table,
            config.modulus,
            config.n_templates,
        ),
        compatibility_wrong=wrong_language_compatibility(
            table,
            modulus=config.modulus,
            n_templates=config.n_templates,
            rng=random.Random(config.seed + 8851),
            n_transforms=max_transforms,
        ),
        compatibility_discovered=discovered_score,
        final_train_loss=final_loss,
        parameter_l2=param_l2,
        sharpness_proxy=sharp,
        metadata={
            "config": asdict(config),
            "table": list(table),
            "learned_generator": learned_family.to_record(),
            "regularizer_transforms": [list(transform) for transform in transforms],
            "final_regularizer_loss": final_regularizer,
            "rendered_example": render_example(base[0], config.modulus),
        },
    )


def run_language_template_sweep(
    *,
    n_configs: int,
    epochs: int,
    base_seed: int,
    device: str | None = None,
    regularization_values: tuple[float, ...] = (0.0, 0.05, 0.2, 0.5),
    include_exact: bool = True,
    max_transforms: int = 24,
) -> list[DiagnosticRow]:
    rng = random.Random(base_seed)
    rows = exact_language_rows(max_transforms=max_transforms) if include_exact else []
    for _ in range(n_configs):
        augmentation = rng.choice(
            ["none", "partial_a_substitution", "wrong_substitution"]
        )
        count = 0 if augmentation == "none" else rng.choice([1, 2])
        seed = rng.randrange(0, 2**31 - 1)
        modulus = rng.choice([7, 11, 13])
        train_window = rng.choice([2, 3, 4])
        common = {
            "seed": seed,
            "modulus": modulus,
            "train_window": train_window,
            "n_templates": 4,
            "hidden_width": rng.choice([32, 64, 128]),
            "depth": rng.choice([1, 2, 3]),
            "init_scale": rng.choice([0.5, 1.0, 1.5]),
            "learning_rate": rng.choice([1e-3, 3e-3, 1e-2]),
            "weight_decay": rng.choice([0.0, 1e-4, 1e-3]),
            "epochs": epochs,
            "optimizer": rng.choice(["adam", "sgd"]),
            "augmentation": augmentation,
            "augmentation_count": count,
            "compatibility_min_support": default_min_support(
                modulus,
                train_window,
                4,
            ),
        }
        for strength in regularization_values:
            rows.append(
                train_one_language_template(
                    LanguageTemplateConfig(
                        **common,
                        compatibility_regularization=strength,
                    ),
                    device=device,
                    max_transforms=max_transforms,
                )
            )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-configs", type=int, default=24)
    parser.add_argument("--epochs", type=int, default=240)
    parser.add_argument("--base-seed", type=int, default=20260706)
    parser.add_argument("--device", choices=["cpu", "cuda"], default=None)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    rows = run_language_template_sweep(
        n_configs=args.n_configs,
        epochs=args.epochs,
        base_seed=args.base_seed,
        device=args.device,
    )
    payload = {
        "kind": "template-language substitution compatibility sweep",
        "manifest": {
            "n_configs": args.n_configs,
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
