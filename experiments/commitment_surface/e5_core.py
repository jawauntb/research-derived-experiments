"""Pure, testable design and analysis logic for E5.

The Modal runner imports this module, but this module intentionally has no
Modal, torch, transformers, or PEFT dependency.  In particular, supervised
exposures and consistency interventions are different types so a regularizer
cannot accidentally acquire held-out truth labels.
"""

from __future__ import annotations

import math
import random
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from enum import StrEnum


class E5Arm(StrEnum):
    G_REG = "G-reg"
    B_REF = "B-ref"
    W_REG = "W-reg"
    COV = "Cov"
    A_REF = "A-ref"


@dataclass(frozen=True)
class E5Config:
    modulus: int
    train_frac: float = 0.5
    train_shift_count: int = 3
    augmentation_multiplier: int = 3
    spectral_mass_fraction: float = 0.5
    seed: int = 20260709

    def __post_init__(self) -> None:
        if self.modulus < 5:
            raise ValueError("modulus must be at least 5")
        if not 0.0 < self.train_frac < 1.0:
            raise ValueError("train_frac must be strictly between zero and one")
        if not 1 <= self.train_shift_count < self.modulus - 1:
            raise ValueError("train_shift_count must leave at least one novel shift")
        if self.augmentation_multiplier < 1:
            raise ValueError("augmentation_multiplier must be positive")
        if not 0.0 < self.spectral_mass_fraction < 1.0:
            raise ValueError("spectral_mass_fraction must be in (0, 1)")


@dataclass(frozen=True)
class E5Split:
    train_inputs: tuple[int, ...]
    ood_inputs: tuple[int, ...]
    k_train: tuple[int, ...]
    k_novel: tuple[int, ...]

    def validate(self) -> None:
        if set(self.train_inputs) & set(self.ood_inputs):
            raise ValueError("train and OOD support overlap")
        if set(self.k_train) & set(self.k_novel):
            raise ValueError("training and novel shifts overlap")
        if not self.train_inputs or not self.ood_inputs:
            raise ValueError("both train and OOD support must be nonempty")
        if not self.k_train or not self.k_novel:
            raise ValueError("both training and novel shifts must be nonempty")


@dataclass(frozen=True)
class SupervisedExposure:
    input_id: int
    label: int
    source: str
    source_input: int | None = None
    intervention_id: int | None = None


@dataclass(frozen=True)
class ConsistencyExposure:
    source_input: int
    target_input: int
    output_permutation: tuple[int, ...]
    intervention_id: int


@dataclass(frozen=True)
class ExposurePlan:
    arm: E5Arm
    supervised: tuple[SupervisedExposure, ...]
    consistency: tuple[ConsistencyExposure, ...]


@dataclass(frozen=True)
class ExposureAudit:
    supervised_original_events: int
    supervised_heldout_events: int
    supervised_heldout_unique: int
    consistency_events: int
    consistency_outside_train: int
    used_intervention_ids: tuple[int, ...]


def make_split(config: E5Config) -> E5Split:
    rng = random.Random(config.seed)
    train_size = min(
        config.modulus - 1,
        max(2, int(round(config.modulus * config.train_frac))),
    )
    train = tuple(sorted(rng.sample(range(config.modulus), train_size)))
    train_set = set(train)
    ood = tuple(x for x in range(config.modulus) if x not in train_set)

    # Prefer shifts that yield many in-support consistency pairs. The ordering
    # is deterministic after the split and does not inspect any held-out label.
    shifts = list(range(1, config.modulus))
    rng.shuffle(shifts)
    shifts.sort(
        key=lambda k: sum((x + k) % config.modulus in train_set for x in train),
        reverse=True,
    )
    k_train = tuple(sorted(shifts[: config.train_shift_count]))
    k_novel = tuple(sorted(set(range(1, config.modulus)) - set(k_train)))
    split = E5Split(train, ood, k_train, k_novel)
    split.validate()
    return split


def _truth(x: int, offset: int, modulus: int) -> int:
    return (x + offset) % modulus


def _cyclic_permutation(k: int, modulus: int) -> tuple[int, ...]:
    return tuple((value + k) % modulus for value in range(modulus))


def _wrong_permutation(modulus: int, seed: int) -> tuple[int, ...]:
    rng = random.Random(seed)
    cyclic = {_cyclic_permutation(k, modulus) for k in range(modulus)}
    while True:
        values = list(range(modulus))
        rng.shuffle(values)
        candidate = tuple(values)
        if candidate not in cyclic:
            return candidate


def _regularizer_pairs(
    split: E5Split,
    config: E5Config,
    *,
    wrong_generator: bool,
) -> tuple[ConsistencyExposure, ...]:
    train_set = set(split.train_inputs)
    wrong = _wrong_permutation(config.modulus, config.seed + 404)
    pairs: list[ConsistencyExposure] = []
    for repeat in range(config.augmentation_multiplier):
        for k in split.k_train:
            output_perm = wrong if wrong_generator else _cyclic_permutation(
                k, config.modulus
            )
            for x in split.train_inputs:
                target = wrong[x] if wrong_generator else (x + k) % config.modulus
                if target in train_set:
                    pairs.append(
                        ConsistencyExposure(
                            source_input=x,
                            target_input=target,
                            output_permutation=output_perm,
                            intervention_id=k,
                        )
                    )
    return tuple(pairs)


def _b_ref_exposures(
    split: E5Split, config: E5Config, offset: int
) -> tuple[SupervisedExposure, ...]:
    rows: list[SupervisedExposure] = [
        SupervisedExposure(x, _truth(x, offset, config.modulus), "original")
        for x in split.train_inputs
    ]
    for _ in range(config.augmentation_multiplier):
        for k in split.k_train:
            for x in split.train_inputs:
                target_input = (x + k) % config.modulus
                rows.append(
                    SupervisedExposure(
                        target_input,
                        _truth(target_input, offset, config.modulus),
                        "cyclic_augmentation",
                        source_input=x,
                        intervention_id=k,
                    )
                )
    return tuple(rows)


def _coverage_matched_exposures(
    split: E5Split,
    config: E5Config,
    offset: int,
    b_rows: Sequence[SupervisedExposure],
) -> tuple[SupervisedExposure, ...]:
    ood_set = set(split.ood_inputs)
    b_heldout = [row for row in b_rows if row.input_id in ood_set]
    unique_count = len({row.input_id for row in b_heldout})
    event_count = len(b_heldout)
    if unique_count > len(split.ood_inputs):
        raise ValueError("B-ref exposed more unique held-out inputs than exist")

    rng = random.Random(config.seed + 808)
    selected = sorted(rng.sample(list(split.ood_inputs), unique_count))
    heldout_ids = [selected[index % unique_count] for index in range(event_count)]
    rows = [
        SupervisedExposure(x, _truth(x, offset, config.modulus), "original")
        for x in split.train_inputs
    ]
    rows.extend(
        SupervisedExposure(
            x,
            _truth(x, offset, config.modulus),
            "coverage_matched",
        )
        for x in heldout_ids
    )
    # Match B-ref total row count without adding any further held-out coverage.
    while len(rows) < len(b_rows):
        x = split.train_inputs[(len(rows) - len(split.train_inputs)) % len(split.train_inputs)]
        rows.append(
            SupervisedExposure(x, _truth(x, offset, config.modulus), "volume_match")
        )
    return tuple(rows)


def build_exposure_plans(
    split: E5Split, config: E5Config, offset: int
) -> dict[E5Arm, ExposurePlan]:
    split.validate()
    original = tuple(
        SupervisedExposure(x, _truth(x, offset, config.modulus), "original")
        for x in split.train_inputs
    )
    b_rows = _b_ref_exposures(split, config, offset)
    plans = {
        E5Arm.G_REG: ExposurePlan(
            E5Arm.G_REG,
            original,
            _regularizer_pairs(split, config, wrong_generator=False),
        ),
        E5Arm.B_REF: ExposurePlan(E5Arm.B_REF, b_rows, ()),
        E5Arm.W_REG: ExposurePlan(
            E5Arm.W_REG,
            original,
            _regularizer_pairs(split, config, wrong_generator=True),
        ),
        E5Arm.COV: ExposurePlan(
            E5Arm.COV,
            _coverage_matched_exposures(split, config, offset, b_rows),
            (),
        ),
        E5Arm.A_REF: ExposurePlan(E5Arm.A_REF, original, ()),
    }
    validate_exposure_plans(plans, split)
    return plans


def audit_exposure(plan: ExposurePlan, split: E5Split) -> ExposureAudit:
    train_set = set(split.train_inputs)
    ood_set = set(split.ood_inputs)
    heldout = [row for row in plan.supervised if row.input_id in ood_set]
    return ExposureAudit(
        supervised_original_events=sum(
            row.input_id in train_set for row in plan.supervised
        ),
        supervised_heldout_events=len(heldout),
        supervised_heldout_unique=len({row.input_id for row in heldout}),
        consistency_events=len(plan.consistency),
        consistency_outside_train=sum(
            pair.source_input not in train_set or pair.target_input not in train_set
            for pair in plan.consistency
        ),
        used_intervention_ids=tuple(
            sorted({pair.intervention_id for pair in plan.consistency})
        ),
    )


def validate_exposure_plans(
    plans: dict[E5Arm, ExposurePlan], split: E5Split
) -> None:
    split.validate()
    audits = {arm: audit_exposure(plan, split) for arm, plan in plans.items()}
    for arm in (E5Arm.G_REG, E5Arm.W_REG):
        audit = audits[arm]
        if audit.supervised_heldout_events:
            raise ValueError(f"{arm} received held-out truth labels")
        if audit.consistency_outside_train:
            raise ValueError(f"{arm} consistency escaped train support")
        if set(audit.used_intervention_ids) & set(split.k_novel):
            raise ValueError(f"{arm} used a novel intervention shift")
    b_audit, cov_audit = audits[E5Arm.B_REF], audits[E5Arm.COV]
    if (
        b_audit.supervised_heldout_events
        != cov_audit.supervised_heldout_events
        or b_audit.supervised_heldout_unique
        != cov_audit.supervised_heldout_unique
    ):
        raise ValueError("Cov does not match B-ref held-out label coverage")


def exposure_ledger(
    plans: dict[E5Arm, ExposurePlan], split: E5Split
) -> dict[str, dict[str, object]]:
    return {
        arm.value: asdict(audit_exposure(plan, split))
        for arm, plan in plans.items()
    }


def _mean(cells: Sequence[Mapping[str, object]], arm: E5Arm, metric: str) -> float:
    values: list[float] = []
    for cell in cells:
        value = cell.get(metric)
        if cell.get("arm") != arm.value or not isinstance(value, int | float):
            continue
        numeric = float(value)
        if math.isfinite(numeric):
            values.append(numeric)
    return sum(values) / len(values) if values else float("nan")


def analyze_e5(cells: Sequence[Mapping[str, object]]) -> dict[str, object]:
    """Apply the frozen E5 gates to raw cell summaries."""
    metrics = (
        "canonical_ood_accuracy",
        "paraphrase_ood_accuracy",
        "novel_k_equivariance_accuracy",
        "canonical_normalized_patch_ce",
        "paraphrase_normalized_patch_ce",
    )
    per_arm = {
        arm.value: {metric: _mean(cells, arm, metric) for metric in metrics}
        for arm in E5Arm
        if any(cell.get("arm") == arm.value for cell in cells)
    }
    required = (E5Arm.G_REG.value, E5Arm.COV.value, E5Arm.A_REF.value)
    complete = all(arm in per_arm for arm in required)
    integrity_pass = bool(cells) and all(
        bool(cell.get("integrity_pass", False)) for cell in cells
    )
    finite_pass = complete and all(
        math.isfinite(float(per_arm[arm][metric]))
        for arm in required
        for metric in metrics
    )
    smoke_pass = integrity_pass and finite_pass
    if not complete:
        return {
            "n_cells": len(cells),
            "per_arm": per_arm,
            "integrity_pass": integrity_pass,
            "smoke_pass": False,
            "confirmatory_ready": False,
            "verdict": "incomplete",
        }

    g, cov, a = (per_arm[arm] for arm in required)
    canonical_lift = g["canonical_ood_accuracy"] - a["canonical_ood_accuracy"]
    paraphrase_lift = (
        g["paraphrase_ood_accuracy"] - a["paraphrase_ood_accuracy"]
    )
    retained = (
        paraphrase_lift / canonical_lift if canonical_lift > 0 else float("-inf")
    )
    generator_gate = (
        g["canonical_ood_accuracy"] - cov["canonical_ood_accuracy"] >= 0.10
        and canonical_lift >= 0.20
        and g["novel_k_equivariance_accuracy"]
        - a["novel_k_equivariance_accuracy"]
        >= 0.10
        and g["canonical_normalized_patch_ce"] >= 0.05
        and g["paraphrase_normalized_patch_ce"] >= 0.05
    )
    coverage_gate = (
        cov["canonical_ood_accuracy"] - g["canonical_ood_accuracy"] >= 0.10
        and (
            canonical_lift < 0.10
            or g["canonical_normalized_patch_ce"] < 0.05
        )
    )
    mixed_gate = (
        canonical_lift >= 0.20
        and cov["canonical_ood_accuracy"] - a["canonical_ood_accuracy"] >= 0.20
        and abs(g["canonical_ood_accuracy"] - cov["canonical_ood_accuracy"]) < 0.10
        and g["canonical_normalized_patch_ce"] > 0
        and g["paraphrase_normalized_patch_ce"] > 0
        and cov["canonical_normalized_patch_ce"] > 0
        and cov["paraphrase_normalized_patch_ce"] > 0
    )
    transport_gate = (
        retained >= 0.75 and g["paraphrase_normalized_patch_ce"] >= 0.05
    )
    group_specificity: bool | None = None
    if E5Arm.W_REG.value in per_arm:
        w = per_arm[E5Arm.W_REG.value]
        group_specificity = (
            g["canonical_ood_accuracy"] - w["canonical_ood_accuracy"] >= 0.10
            and g["novel_k_equivariance_accuracy"]
            - w["novel_k_equivariance_accuracy"]
            >= 0.10
        )
    confirmatory_ready = all(
        sum(cell.get("arm") == arm for cell in cells) >= 3
        for arm in (member.value for member in E5Arm)
    )
    verdict = "pending_confirmatory_grid"
    if confirmatory_ready and integrity_pass:
        if generator_gate and transport_gate and group_specificity:
            verdict = "generator_learning"
        elif coverage_gate:
            verdict = "coverage"
        elif mixed_gate and transport_gate:
            verdict = "mixed"
        else:
            verdict = "kill_or_draw"
    return {
        "n_cells": len(cells),
        "per_arm": per_arm,
        "integrity_pass": integrity_pass,
        "smoke_pass": smoke_pass,
        "confirmatory_ready": confirmatory_ready,
        "canonical_G_minus_A": canonical_lift,
        "canonical_G_minus_Cov": (
            g["canonical_ood_accuracy"] - cov["canonical_ood_accuracy"]
        ),
        "novel_k_G_minus_A": (
            g["novel_k_equivariance_accuracy"]
            - a["novel_k_equivariance_accuracy"]
        ),
        "paraphrase_lift_retained": retained,
        "generator_learning_gate": generator_gate,
        "coverage_gate": coverage_gate,
        "mixed_gate": mixed_gate,
        "group_specificity_gate": group_specificity,
        "transport_gate": transport_gate,
        "verdict": verdict,
    }
