"""Pure runtime planning contracts for the E6 Modal/L4 runner."""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any

from experiments.commitment_surface.e6_core import (
    E6_ARM_VALUES,
    E6_BASE_SEED,
    E6_BOOTSTRAP_EPOCHS,
    E6_CANDIDATE_PROPOSER,
    E6_GENERATIONS_PER_INPUT,
    E6_ROUNDS,
    E6_SELECTION_FRACTION,
    E6Arm,
    E6Config,
    E6RunKind,
)

GPU_TYPE = "L4"
GPU_MEMORY_MIB = 24_576
GPU_TIMEOUT_SECONDS = 6 * 60 * 60
GPU_MAX_CONTAINERS = 12
CELL_LEASE_TTL_SECONDS = GPU_TIMEOUT_SECONDS + 15 * 60
PYTORCH_CUDA_ALLOC_CONF = "expandable_segments:True"


@dataclass(frozen=True)
class E6ModalRunConfig:
    sizes: tuple[str, ...]
    moduli: tuple[int, ...]
    seed_slots: tuple[int, ...]
    arms: tuple[str, ...]
    base_seed: int = E6_BASE_SEED
    rounds: int = E6_ROUNDS
    train_frac: float = 0.5
    train_shift_count: int = 3
    bootstrap_epochs: int = E6_BOOTSTRAP_EPOCHS
    generations_per_input: int = E6_GENERATIONS_PER_INPUT
    candidate_proposer: str = E6_CANDIDATE_PROPOSER
    generation_temperature: float = 0.8
    round_epochs: int = 40
    selection_fraction: float = E6_SELECTION_FRACTION
    lora_rank: int = 8
    lora_alpha: int = 16
    lora_dropout: float = 0.05
    lora_lr: float = 5e-4
    weight_decay: float = 0.0
    grad_clip: float = 1.0
    spectral_mass_fraction: float = 0.5
    patch_ce_threshold: float = 0.05
    collapse_tolerance: float = 0.05
    patch_dip_tolerance: float = 0.01
    transport_retention_fraction: float = 0.75
    generator_coverage_margin: float = 0.10
    candidate_batch_size: int = 32

    def __post_init__(self) -> None:
        for name, values in (
            ("sizes", self.sizes),
            ("moduli", self.moduli),
            ("seed_slots", self.seed_slots),
            ("arms", self.arms),
        ):
            if not values:
                raise ValueError(f"{name} must be nonempty")
            if len(values) != len(set(values)):
                raise ValueError(f"{name} must not contain duplicates")
        if any(not size for size in self.sizes):
            raise ValueError("sizes must be nonempty strings")
        if any(slot < 0 for slot in self.seed_slots):
            raise ValueError("seed_slots must be nonnegative")
        validate_runtime_arms(self.arms, run_kind=E6RunKind.DEVELOPMENT)
        for modulus in self.moduli:
            E6Config(
                modulus=modulus,
                seed_slot=self.seed_slots[0],
                base_seed=self.base_seed,
                rounds=self.rounds,
                train_frac=self.train_frac,
                train_shift_count=self.train_shift_count,
                bootstrap_epochs=self.bootstrap_epochs,
                generations_per_input=self.generations_per_input,
                candidate_proposer=self.candidate_proposer,
                generation_temperature=self.generation_temperature,
                round_epochs=self.round_epochs,
                selection_fraction=self.selection_fraction,
                spectral_mass_fraction=self.spectral_mass_fraction,
                patch_ce_threshold=self.patch_ce_threshold,
                collapse_tolerance=self.collapse_tolerance,
                patch_dip_tolerance=self.patch_dip_tolerance,
                transport_retention_fraction=self.transport_retention_fraction,
                generator_coverage_margin=self.generator_coverage_margin,
            )
        if self.lora_rank < 1 or self.lora_alpha < 1:
            raise ValueError("LoRA rank and alpha must be positive")
        if not math.isfinite(self.lora_dropout) or not 0.0 <= self.lora_dropout < 1.0:
            raise ValueError("lora_dropout must be finite and in [0, 1)")
        if not math.isfinite(self.lora_lr) or self.lora_lr <= 0.0:
            raise ValueError("lora_lr must be finite and positive")
        if not math.isfinite(self.weight_decay) or self.weight_decay < 0.0:
            raise ValueError("weight_decay must be finite and nonnegative")
        if not math.isfinite(self.grad_clip) or self.grad_clip < 0.0:
            raise ValueError("grad_clip must be finite and nonnegative")
        if self.candidate_batch_size < 1:
            raise ValueError("candidate_batch_size must be positive")

    def scientific_config(self) -> dict[str, object]:
        return asdict(self)


def validate_runtime_arms(
    arms: Sequence[str], *, run_kind: str | E6RunKind
) -> None:
    kind = E6RunKind(run_kind)
    values = tuple(arms)
    unknown = sorted(set(values) - E6_ARM_VALUES)
    if unknown:
        raise ValueError("unknown E6 arms: " + ", ".join(unknown))
    if len(values) != len(set(values)):
        raise ValueError("arms must not contain duplicates")
    if not {E6Arm.SC.value, E6Arm.CS.value} <= set(values):
        raise ValueError("E6 execution requires the coupled SC and CS arms")
    if kind is E6RunKind.SMOKE and E6Arm.A_REF.value not in values:
        raise ValueError("E6 smoke requires A-ref")
    if kind is E6RunKind.CONFIRMATORY and set(values) != E6_ARM_VALUES:
        raise ValueError("confirmatory execution requires all four E6 arms")


def paired_proposer_schedule(generations_per_input: int) -> tuple[str, ...]:
    if generations_per_input < 2 or generations_per_input % 2:
        raise ValueError("paired proposer generation count must be even and at least two")
    return tuple(
        E6Arm.SC.value if index % 2 == 0 else E6Arm.CS.value
        for index in range(generations_per_input)
    )


def candidate_input_ids(
    *,
    train_inputs: Sequence[int],
    ood_inputs: Sequence[int],
    novel_shifts: Sequence[int],
    modulus: int,
) -> tuple[int, ...]:
    if modulus < 2:
        raise ValueError("modulus must be at least two")
    values = {int(value) % modulus for value in ood_inputs}
    values.update(
        (int(value) + int(shift)) % modulus
        for value in train_inputs
        for shift in novel_shifts
    )
    if not values:
        raise ValueError("candidate input support must be nonempty")
    return tuple(sorted(values))


def build_execution_strata(
    cells: Sequence[Mapping[str, object]],
) -> tuple[dict[str, Any], ...]:
    grouped: dict[tuple[str, int, int], list[Mapping[str, object]]] = defaultdict(list)
    for cell in cells:
        size = cell.get("size")
        modulus = cell.get("n")
        seed_slot = cell.get("seed_slot")
        arm = cell.get("arm")
        cell_id = cell.get("cell_id")
        if (
            not isinstance(size, str)
            or isinstance(modulus, bool)
            or not isinstance(modulus, int)
            or isinstance(seed_slot, bool)
            or not isinstance(seed_slot, int)
            or not isinstance(arm, str)
            or not isinstance(cell_id, str)
        ):
            raise ValueError("manifest cells require typed size/n/seed_slot/arm/cell_id")
        if arm not in E6_ARM_VALUES:
            raise ValueError(f"unknown E6 arm in manifest: {arm}")
        grouped[(size, modulus, seed_slot)].append(cell)

    arm_order = {arm.value: index for index, arm in enumerate(E6Arm)}
    strata: list[dict[str, Any]] = []
    for (size, modulus, seed_slot), members in grouped.items():
        arms = [str(member["arm"]) for member in members]
        if len(arms) != len(set(arms)):
            raise ValueError("manifest contains duplicate arm cells in a stratum")
        ordered = sorted(members, key=lambda member: arm_order[str(member["arm"])])
        strata.append(
            {
                "stratum_id": f"{size}__n{modulus}__slot{seed_slot}",
                "size": size,
                "n": modulus,
                "seed_slot": seed_slot,
                "arms": tuple(str(member["arm"]) for member in ordered),
                "cell_ids": tuple(str(member["cell_id"]) for member in ordered),
            }
        )
    return tuple(strata)


def validate_stratum_result(
    result: object,
    *,
    expected_cell_ids: Sequence[str],
) -> tuple[dict[str, Any], ...]:
    expected = tuple(expected_cell_ids)
    if not expected or len(expected) != len(set(expected)):
        raise ValueError("expected stratum cell IDs must be nonempty and unique")
    if not isinstance(result, list):
        raise TypeError("stratum result must be a list of cell payloads")
    cells: list[dict[str, Any]] = []
    observed: list[str] = []
    for cell in result:
        if not isinstance(cell, Mapping):
            raise TypeError("stratum result cells must be mappings")
        if any(not isinstance(key, str) for key in cell):
            raise ValueError("stratum result cell keys must be strings")
        cell_id = cell.get("cell_id")
        if not isinstance(cell_id, str):
            raise ValueError("stratum result cells require string cell_id values")
        observed.append(cell_id)
        cells.append(
            {
                key: value
                for key, value in cell.items()
                if isinstance(key, str)
            }
        )
    if tuple(observed) != expected:
        raise ValueError(
            "stratum result cell IDs must exactly match the requested order: "
            f"expected {expected}, observed {tuple(observed)}"
        )
    return tuple(cells)


def prioritize_strata(
    strata: Sequence[Mapping[str, object]],
) -> tuple[dict[str, Any], ...]:
    def size_value(value: object) -> int:
        text = str(value).lower().removesuffix("m")
        try:
            return int(text)
        except ValueError:
            return -1

    return tuple(
        dict(stratum)
        for stratum in sorted(
            strata,
            key=lambda item: (
                -size_value(item.get("size")),
                -int(item.get("n", -1)),
                int(item.get("seed_slot", -1)),
            ),
        )
    )


def lease_record_is_active(record: object, *, now_unix: float) -> bool:
    if not isinstance(record, Mapping):
        return False
    expires = record.get("expires_at_unix")
    return (
        not isinstance(expires, bool)
        and isinstance(expires, int | float)
        and math.isfinite(float(expires))
        and float(expires) > now_unix
    )
