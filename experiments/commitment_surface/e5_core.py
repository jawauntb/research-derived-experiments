"""Pure, testable design and analysis logic for E5.

The Modal runner imports this module, but this module intentionally has no
Modal, torch, transformers, or PEFT dependency.  In particular, supervised
exposures and consistency interventions are different types so a regularizer
cannot accidentally acquire held-out truth labels.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from enum import StrEnum
from itertools import product
from typing import Any


class E5Arm(StrEnum):
    G_REG = "G-reg"
    B_REF = "B-ref"
    W_REG = "W-reg"
    COV = "Cov"
    A_REF = "A-ref"


class E5RunKind(StrEnum):
    SMOKE = "smoke"
    DEVELOPMENT = "development"
    CONFIRMATORY = "confirmatory"


E5_GATE_METRICS = (
    "canonical_ood_accuracy",
    "paraphrase_ood_accuracy",
    "novel_k_equivariance_accuracy",
    "canonical_normalized_patch_ce",
    "paraphrase_normalized_patch_ce",
)
E5_ACCURACY_METRICS = frozenset(E5_GATE_METRICS[:3])


@dataclass(frozen=True)
class E5GridSpec:
    sizes: tuple[str, ...]
    moduli: tuple[int, ...]
    seeds: tuple[int, ...]
    arms: tuple[str, ...]

    def __post_init__(self) -> None:
        for name, values in (
            ("sizes", self.sizes),
            ("moduli", self.moduli),
            ("seeds", self.seeds),
            ("arms", self.arms),
        ):
            if not values:
                raise ValueError(f"{name} must be nonempty")
            if len(values) != len(set(values)):
                raise ValueError(f"{name} must not contain duplicates")

    def expected_keys(self) -> tuple[tuple[str, int, int, str], ...]:
        return tuple(product(self.sizes, self.moduli, self.seeds, self.arms))


E5_CONFIRMATORY_GRID = E5GridSpec(
    sizes=("70m", "160m", "410m"),
    moduli=(13, 17, 23),
    seeds=(20260709, 20260809, 20260909),
    arms=tuple(arm.value for arm in E5Arm),
)
E5_RUN_PROTOCOL_VERSION = "e5-generator-vs-coverage-v1-20260710"

E5_CONFIRMATORY_PARAMETERS: dict[str, object] = {
    "sizes": E5_CONFIRMATORY_GRID.sizes,
    "moduli": E5_CONFIRMATORY_GRID.moduli,
    "seeds": E5_CONFIRMATORY_GRID.seeds,
    "arms": E5_CONFIRMATORY_GRID.arms,
    "train_frac": 0.5,
    "train_shift_count": 3,
    "augmentation_multiplier": 3,
    "epochs": 160,
    "consistency_weight": 1.0,
    "lora_rank": 8,
    "lora_alpha": 16,
    "lora_dropout": 0.05,
    "lora_lr": 5e-4,
    "weight_decay": 0.0,
    "grad_clip": 1.0,
    "spectral_mass_fraction": 0.5,
}


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


def _wrong_permutation(
    modulus: int,
    seed: int,
    preserved_support: Sequence[int],
) -> tuple[int, ...]:
    """Build a non-cyclic permutation that maps train support onto itself."""
    rng = random.Random(seed)
    cyclic = {_cyclic_permutation(k, modulus) for k in range(modulus)}
    support = tuple(preserved_support)
    complement = tuple(value for value in range(modulus) if value not in support)
    while True:
        support_targets = list(support)
        complement_targets = list(complement)
        rng.shuffle(support_targets)
        rng.shuffle(complement_targets)
        values = list(range(modulus))
        for source, target in zip(support, support_targets):
            values[source] = target
        for source, target in zip(complement, complement_targets):
            values[source] = target
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
    wrong = _wrong_permutation(
        config.modulus,
        config.seed + 404,
        split.train_inputs,
    )
    pairs: list[ConsistencyExposure] = []
    for _ in range(config.augmentation_multiplier):
        for k in split.k_train:
            output_perm = wrong if wrong_generator else _cyclic_permutation(
                k, config.modulus
            )
            for x in split.train_inputs:
                cyclic_target = (x + k) % config.modulus
                if cyclic_target not in train_set:
                    continue
                target = wrong[x] if wrong_generator else cyclic_target
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
    g_plan, w_plan = plans[E5Arm.G_REG], plans[E5Arm.W_REG]
    if g_plan.supervised != w_plan.supervised:
        raise ValueError("W-reg does not match G-reg supervised exposure")
    g_schedule = Counter(
        (pair.source_input, pair.intervention_id) for pair in g_plan.consistency
    )
    w_schedule = Counter(
        (pair.source_input, pair.intervention_id) for pair in w_plan.consistency
    )
    if g_schedule != w_schedule:
        raise ValueError("W-reg does not volume-match G-reg consistency exposure")


def exposure_ledger(
    plans: dict[E5Arm, ExposurePlan], split: E5Split
) -> dict[str, dict[str, object]]:
    return {
        arm.value: asdict(audit_exposure(plan, split))
        for arm, plan in plans.items()
    }


def _sequence_value(value: object, field: str) -> tuple[object, ...]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise ValueError(f"{field} must be a sequence")
    return tuple(value)


def _int_sequence_value(value: object, field: str) -> tuple[int, ...]:
    values = _sequence_value(value, field)
    result: list[int] = []
    for item in values:
        if not isinstance(item, int):
            raise ValueError(f"{field} must contain only integers")
        result.append(item)
    return tuple(result)


def confirmatory_config_mismatches(config: Mapping[str, object]) -> tuple[str, ...]:
    """Return launch fields that drift from the frozen E5 grid."""
    mismatches: list[str] = []
    for field, expected in E5_CONFIRMATORY_PARAMETERS.items():
        actual = config.get(field)
        if isinstance(expected, tuple):
            try:
                actual = _sequence_value(actual, field)
            except ValueError:
                mismatches.append(field)
                continue
        if actual != expected:
            mismatches.append(field)
    return tuple(mismatches)


def build_run_manifest(
    config: Mapping[str, object],
    *,
    run_kind: str | E5RunKind,
    implementation_fingerprint: str = E5_RUN_PROTOCOL_VERSION,
    execution_environment: Mapping[str, object] | None = None,
) -> dict[str, Any]:
    """Build a deterministic per-cell launch manifest.

    Only an exact match to the timestamped frozen configuration can be marked
    confirmatory. Smoke and development manifests remain scientifically
    non-confirmatory even if they happen to contain three seeds per arm.
    """
    try:
        kind = E5RunKind(run_kind)
    except ValueError as error:
        raise ValueError(
            "run_kind must be smoke, development, or confirmatory"
        ) from error
    if not implementation_fingerprint:
        raise ValueError("implementation_fingerprint must be nonempty")
    mismatches = confirmatory_config_mismatches(config)
    if kind is E5RunKind.CONFIRMATORY and mismatches:
        fields = ", ".join(mismatches)
        raise ValueError(f"confirmatory launch drifts from frozen fields: {fields}")

    sizes = tuple(str(value) for value in _sequence_value(config.get("sizes"), "sizes"))
    moduli = _int_sequence_value(config.get("moduli"), "moduli")
    seeds = _int_sequence_value(config.get("seeds"), "seeds")
    arms = tuple(str(value) for value in _sequence_value(config.get("arms"), "arms"))
    grid = E5GridSpec(sizes=sizes, moduli=moduli, seeds=seeds, arms=arms)
    cells = [
        {
            "cell_id": f"{size}__n{modulus}__seed{seed}__{arm}",
            "size": size,
            "n": modulus,
            "seed": seed,
            "arm": arm,
        }
        for size, modulus, seed, arm in grid.expected_keys()
    ]
    fingerprint_source = {
        "protocol_version": E5_RUN_PROTOCOL_VERSION,
        "implementation_fingerprint": implementation_fingerprint,
        "execution_environment": dict(execution_environment or {}),
        "run_kind": kind.value,
        "config": dict(config),
        "cells": cells,
    }
    manifest_id = hashlib.sha256(
        json.dumps(
            fingerprint_source,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return {
        "manifest_id": manifest_id,
        "protocol_version": E5_RUN_PROTOCOL_VERSION,
        "implementation_fingerprint": implementation_fingerprint,
        "execution_environment": dict(execution_environment or {}),
        "run_kind": kind.value,
        "confirmatory_config_pass": not mismatches,
        "confirmatory_config_mismatches": list(mismatches),
        "expected_cell_count": len(cells),
        "cells": cells,
    }


def grid_spec_for_run_kind(
    run_kind: str | E5RunKind,
) -> E5GridSpec | None:
    """Route only confirmatory runs to the frozen scientific grid gate."""
    kind = E5RunKind(run_kind)
    return E5_CONFIRMATORY_GRID if kind is E5RunKind.CONFIRMATORY else None


def lease_record_is_active(record: object, *, now_unix: float) -> bool:
    """Return whether a launcher lease record has a valid future expiry."""
    if not isinstance(record, Mapping):
        return False
    expires = record.get("expires_at_unix")
    return (
        not isinstance(expires, bool)
        and isinstance(expires, int | float)
        and math.isfinite(float(expires))
        and float(expires) > now_unix
    )


def _is_valid_metric(metric: str, value: object) -> bool:
    if (
        isinstance(value, bool)
        or not isinstance(value, int | float)
        or not math.isfinite(float(value))
    ):
        return False
    return metric not in E5_ACCURACY_METRICS or 0.0 <= float(value) <= 1.0


def cell_is_reusable(
    cell: Mapping[str, object], manifest_id: str, cell_id: str
) -> bool:
    """Return whether a checkpoint is safe to reuse without GPU work."""
    if (
        cell.get("run_manifest_id") != manifest_id
        or cell.get("cell_id") != cell_id
        or cell.get("integrity_pass") is not True
    ):
        return False
    parts = cell_id.split("__")
    if len(parts) != 4:
        return False
    size, modulus_text, seed_text, arm = parts
    try:
        modulus = int(modulus_text.removeprefix("n"))
        seed = int(seed_text.removeprefix("seed"))
    except ValueError:
        return False
    if (
        not modulus_text.startswith("n")
        or not seed_text.startswith("seed")
        or cell.get("size") != size
        or cell.get("n") != modulus
        or cell.get("seed") != seed
        or cell.get("arm") != arm
    ):
        return False
    for metric in E5_GATE_METRICS:
        if not _is_valid_metric(metric, cell.get(metric)):
            return False
    return True


def prioritize_launch_cells(
    cells: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    """Submit likely-long cells first while preserving reconstructable IDs."""
    size_priority = {"410m": 0, "160m": 1, "70m": 2}
    arm_priority = {
        E5Arm.G_REG.value: 0,
        E5Arm.W_REG.value: 1,
        E5Arm.B_REF.value: 2,
        E5Arm.COV.value: 3,
        E5Arm.A_REF.value: 4,
    }
    return sorted(
        (dict(cell) for cell in cells),
        key=lambda cell: (
            size_priority.get(str(cell.get("size")), len(size_priority)),
            arm_priority.get(str(cell.get("arm")), len(arm_priority)),
            str(cell.get("cell_id", "")),
        ),
    )


def _format_cell_key(key: tuple[str, int, int, str]) -> str:
    size, modulus, seed, arm = key
    return f"{size}/n={modulus}/seed={seed}/{arm}"


def audit_e5_grid(
    cells: Sequence[Mapping[str, object]], spec: E5GridSpec
) -> dict[str, object]:
    """Audit exact Cartesian-grid completeness before applying science gates."""
    expected = set(spec.expected_keys())
    actual: list[tuple[str, int, int, str]] = []
    invalid_rows: list[int] = []
    invalid_metric_rows: list[dict[str, object]] = []
    integrity_failed_rows: list[int] = []
    for index, cell in enumerate(cells):
        size = cell.get("size")
        modulus = cell.get("n")
        seed = cell.get("seed")
        arm = cell.get("arm")
        if (
            not isinstance(size, str)
            or isinstance(modulus, bool)
            or not isinstance(modulus, int)
            or isinstance(seed, bool)
            or not isinstance(seed, int)
            or not isinstance(arm, str)
        ):
            invalid_rows.append(index)
        else:
            actual.append((size, modulus, seed, arm))
        invalid_metrics = [
            metric
            for metric in E5_GATE_METRICS
            if not _is_valid_metric(metric, cell.get(metric))
        ]
        if invalid_metrics:
            invalid_metric_rows.append(
                {"row": index, "metrics": invalid_metrics}
            )
        if cell.get("integrity_pass") is not True:
            integrity_failed_rows.append(index)

    counts = Counter(actual)
    actual_set = set(actual)
    missing = sorted(expected - actual_set)
    unexpected = sorted(actual_set - expected)
    duplicates = sorted(key for key, count in counts.items() if count > 1)
    grid_complete = (
        not missing
        and not unexpected
        and not duplicates
        and not invalid_rows
        and len(actual) == len(expected)
    )
    cell_data_complete = not invalid_metric_rows and not integrity_failed_rows
    return {
        "required": True,
        "expected_cell_count": len(expected),
        "observed_row_count": len(cells),
        "observed_unique_cell_count": len(actual_set),
        "missing_cells": [_format_cell_key(key) for key in missing],
        "unexpected_cells": [_format_cell_key(key) for key in unexpected],
        "duplicate_cells": [_format_cell_key(key) for key in duplicates],
        "invalid_key_rows": invalid_rows,
        "invalid_metric_rows": invalid_metric_rows,
        "integrity_failed_rows": integrity_failed_rows,
        "grid_complete": grid_complete,
        "cell_data_complete": cell_data_complete,
    }


def _mean(cells: Sequence[Mapping[str, object]], arm: E5Arm, metric: str) -> float:
    values: list[float] = []
    for cell in cells:
        value = cell.get(metric)
        if cell.get("arm") != arm.value or not _is_valid_metric(metric, value):
            continue
        assert isinstance(value, int | float)
        values.append(float(value))
    return sum(values) / len(values) if values else float("nan")


def analyze_e5(
    cells: Sequence[Mapping[str, object]],
    *,
    grid_spec: E5GridSpec | None = None,
) -> dict[str, Any]:
    """Apply the frozen E5 gates to raw cell summaries."""
    metrics = E5_GATE_METRICS
    per_arm = {
        arm.value: {metric: _mean(cells, arm, metric) for metric in metrics}
        for arm in E5Arm
        if any(cell.get("arm") == arm.value for cell in cells)
    }
    required = (E5Arm.G_REG.value, E5Arm.COV.value, E5Arm.A_REF.value)
    complete = all(arm in per_arm for arm in required)
    grid_audit = (
        audit_e5_grid(cells, grid_spec)
        if grid_spec is not None
        else {
            "required": False,
            "expected_cell_count": None,
            "observed_row_count": len(cells),
            "grid_complete": False,
            "cell_data_complete": False,
        }
    )
    integrity_pass = bool(cells) and all(
        cell.get("integrity_pass") is True for cell in cells
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
            "grid_audit": grid_audit,
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
    confirmatory_finite_pass = all(
        arm.value in per_arm
        and all(math.isfinite(float(per_arm[arm.value][metric])) for metric in metrics)
        for arm in E5Arm
    )
    confirmatory_ready = bool(
        grid_spec is not None
        and grid_audit["grid_complete"]
        and grid_audit["cell_data_complete"]
        and integrity_pass
        and confirmatory_finite_pass
    )
    verdict = "pending_confirmatory_grid"
    if confirmatory_ready:
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
        "grid_audit": grid_audit,
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
