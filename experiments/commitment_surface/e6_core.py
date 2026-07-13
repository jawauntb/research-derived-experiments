"""Pure protocol, reward, and matched-exposure contracts for E6.

This module intentionally has no Modal, torch, transformers, or PEFT dependency.
The GPU runner can therefore import the frozen E6 contract while CPU tests prove
that candidate rewards and matched exposure cannot silently drift. Manifest,
trajectory, and verdict gates live in :mod:`e6_analysis`.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from itertools import product


class E6Arm(StrEnum):
    SC = "SC"
    CS = "CS"
    GT = "GT"
    A_REF = "A-ref"


class E6RunKind(StrEnum):
    SMOKE = "smoke"
    DEVELOPMENT = "development"
    CONFIRMATORY = "confirmatory"


E6_SEED_NAMESPACES = frozenset(
    {"split", "candidate", "generation", "subspace", "transport"}
)
E6_GATE_METRICS = (
    "canonical_ood_accuracy",
    "paraphrase_ood_accuracy",
    "novel_k_equivariance_accuracy",
    "canonical_normalized_patch_ce",
    "transported_normalized_patch_ce",
    "generator_gain",
    "coverage_gain",
)
E6_ACCURACY_METRICS = frozenset(E6_GATE_METRICS[:3])
E6_ROUND_INTEGRITY_FIELDS = (
    "split_integrity_pass",
    "reward_leakage_pass",
    "patch_integrity_pass",
)
E6_RUN_PROTOCOL_VERSION = "e6-commitment-reward-v1-20260713"
E6_BASE_SEED = 20260713
E6_ROUNDS = 6
E6_GENERATIONS_PER_INPUT = 8
E6_SELECTION_FRACTION = 0.5
E6_PATCH_CE_THRESHOLD = 0.05
E6_COLLAPSE_TOLERANCE = 0.05
E6_PATCH_DIP_TOLERANCE = 0.01
E6_TRANSPORT_RETENTION_FRACTION = 0.75
E6_GENERATOR_COVERAGE_MARGIN = 0.10
E6_ARM_VALUES = frozenset(arm.value for arm in E6Arm)


@dataclass(frozen=True)
class E6GridSpec:
    sizes: tuple[str, ...]
    moduli: tuple[int, ...]
    seed_slots: tuple[int, ...]
    arms: tuple[str, ...]

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

    def expected_keys(self) -> tuple[tuple[str, int, int, str], ...]:
        return tuple(
            product(self.sizes, self.moduli, self.seed_slots, self.arms)
        )


E6_CONFIRMATORY_GRID = E6GridSpec(
    sizes=("70m", "160m", "410m"),
    moduli=(13, 17, 23),
    seed_slots=(0, 1, 2),
    arms=tuple(arm.value for arm in E6Arm),
)

E6_CONFIRMATORY_PARAMETERS: dict[str, object] = {
    "sizes": E6_CONFIRMATORY_GRID.sizes,
    "moduli": E6_CONFIRMATORY_GRID.moduli,
    "seed_slots": E6_CONFIRMATORY_GRID.seed_slots,
    "arms": E6_CONFIRMATORY_GRID.arms,
    "base_seed": E6_BASE_SEED,
    "rounds": E6_ROUNDS,
    "train_frac": 0.5,
    "train_shift_count": 3,
    "generations_per_input": E6_GENERATIONS_PER_INPUT,
    "generation_temperature": 0.8,
    "round_epochs": 40,
    "selection_fraction": E6_SELECTION_FRACTION,
    "lora_rank": 8,
    "lora_alpha": 16,
    "lora_dropout": 0.05,
    "lora_lr": 5e-4,
    "weight_decay": 0.0,
    "grad_clip": 1.0,
    "spectral_mass_fraction": 0.5,
    "patch_ce_threshold": E6_PATCH_CE_THRESHOLD,
    "collapse_tolerance": E6_COLLAPSE_TOLERANCE,
    "patch_dip_tolerance": E6_PATCH_DIP_TOLERANCE,
    "transport_retention_fraction": E6_TRANSPORT_RETENTION_FRACTION,
    "generator_coverage_margin": E6_GENERATOR_COVERAGE_MARGIN,
    "candidate_batch_size": 32,
}


@dataclass(frozen=True)
class E6Config:
    modulus: int
    seed_slot: int
    base_seed: int = E6_BASE_SEED
    rounds: int = E6_ROUNDS
    train_frac: float = 0.5
    train_shift_count: int = 3
    generations_per_input: int = E6_GENERATIONS_PER_INPUT
    generation_temperature: float = 0.8
    round_epochs: int = 40
    selection_fraction: float = E6_SELECTION_FRACTION
    spectral_mass_fraction: float = 0.5
    patch_ce_threshold: float = E6_PATCH_CE_THRESHOLD
    collapse_tolerance: float = E6_COLLAPSE_TOLERANCE
    patch_dip_tolerance: float = E6_PATCH_DIP_TOLERANCE
    transport_retention_fraction: float = E6_TRANSPORT_RETENTION_FRACTION
    generator_coverage_margin: float = E6_GENERATOR_COVERAGE_MARGIN

    def __post_init__(self) -> None:
        if self.modulus < 5:
            raise ValueError("modulus must be at least 5")
        if self.seed_slot < 0:
            raise ValueError("seed_slot must be nonnegative")
        if self.rounds != E6_ROUNDS:
            raise ValueError("E6 requires exactly six rounds")
        numeric_fields = (
            self.train_frac,
            self.generation_temperature,
            self.selection_fraction,
            self.spectral_mass_fraction,
            self.patch_ce_threshold,
            self.collapse_tolerance,
            self.patch_dip_tolerance,
            self.transport_retention_fraction,
            self.generator_coverage_margin,
        )
        if not all(math.isfinite(value) for value in numeric_fields):
            raise ValueError("E6 floating-point configuration must be finite")
        if not 0.0 < self.train_frac < 1.0:
            raise ValueError("train_frac must be strictly between zero and one")
        if not 1 <= self.train_shift_count < self.modulus - 1:
            raise ValueError("train_shift_count must leave a novel shift")
        if self.generations_per_input < 2:
            raise ValueError("generations_per_input must be at least two")
        if self.generation_temperature <= 0.0:
            raise ValueError("generation_temperature must be positive")
        if self.round_epochs < 1:
            raise ValueError("round_epochs must be positive")
        for name, value in (
            ("selection_fraction", self.selection_fraction),
            ("spectral_mass_fraction", self.spectral_mass_fraction),
            ("transport_retention_fraction", self.transport_retention_fraction),
        ):
            if not 0.0 < value < 1.0:
                raise ValueError(f"{name} must be in (0, 1)")
        for name, value in (
            ("patch_ce_threshold", self.patch_ce_threshold),
            ("collapse_tolerance", self.collapse_tolerance),
            ("patch_dip_tolerance", self.patch_dip_tolerance),
            ("generator_coverage_margin", self.generator_coverage_margin),
        ):
            if value < 0.0:
                raise ValueError(f"{name} must be nonnegative")


@dataclass(frozen=True)
class Candidate:
    """Reward-neutral candidate identity.

    Correctness is deliberately absent. Ground-truth and commitment-surface
    signals use separate typed records so the CS reward path cannot acquire an
    OOD truth-label field by convenience.
    """

    candidate_id: str
    order: int
    input_id: int
    generation: int

    def __post_init__(self) -> None:
        if not self.candidate_id:
            raise ValueError("candidate_id must be nonempty")
        if self.order < 0:
            raise ValueError("candidate order must be nonnegative")


@dataclass(frozen=True)
class CandidatePool:
    round_index: int
    candidates: tuple[Candidate, ...]

    def __post_init__(self) -> None:
        if self.round_index < 1:
            raise ValueError("round_index must be positive")
        if not self.candidates:
            raise ValueError("candidate pool must be nonempty")
        ids = [candidate.candidate_id for candidate in self.candidates]
        orders = [candidate.order for candidate in self.candidates]
        if len(ids) != len(set(ids)):
            raise ValueError("candidate_id values must be unique")
        if len(orders) != len(set(orders)):
            raise ValueError("candidate order values must be unique")
        if orders != sorted(orders):
            raise ValueError("candidates must be stored in frozen order")

    def digest(self) -> str:
        payload = {
            "round": self.round_index,
            "candidates": [
                {
                    "candidate_id": candidate.candidate_id,
                    "order": candidate.order,
                    "input_id": candidate.input_id,
                    "generation": candidate.generation,
                }
                for candidate in self.candidates
            ],
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()


def _require_finite_number(value: object, name: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, int | float)
        or not math.isfinite(float(value))
    ):
        raise ValueError(f"{name} must be finite")
    return float(value)


@dataclass(frozen=True)
class CommitmentSurfaceSignal:
    candidate_id: str
    canonical_patch_ce: float
    transported_patch_ce: float

    def __post_init__(self) -> None:
        if not self.candidate_id:
            raise ValueError("candidate_id must be nonempty")
        _require_finite_number(self.canonical_patch_ce, "canonical_patch_ce")
        _require_finite_number(self.transported_patch_ce, "transported_patch_ce")


@dataclass(frozen=True)
class GroundTruthSignal:
    candidate_id: str
    correct: bool

    def __post_init__(self) -> None:
        if not self.candidate_id:
            raise ValueError("candidate_id must be nonempty")
        if not isinstance(self.correct, bool):
            raise ValueError("correct must be boolean")


@dataclass(frozen=True)
class RoundSelection:
    arm: E6Arm
    round_index: int
    pool_digest: str
    candidate_count: int
    selected_candidate_ids: tuple[str, ...]
    selected_rewards: tuple[float, ...]

    @property
    def selected_candidate_count(self) -> int:
        return len(self.selected_candidate_ids)


@dataclass(frozen=True)
class RoundPlan:
    round_index: int
    selections: tuple[RoundSelection, ...]

    def selection_for(self, arm: E6Arm | str) -> RoundSelection:
        expected = E6Arm(arm)
        for selection in self.selections:
            if selection.arm is expected:
                return selection
        raise KeyError(expected.value)


def derive_e6_seed(
    *,
    base_seed: int,
    namespace: str,
    size: str,
    modulus: int,
    arm_scope: str,
    round_index: int,
    seed_slot: int,
) -> int:
    """Derive the frozen collision-resistant E6 RNG key.

    Callers use ``arm_scope="SC-CS"`` for candidate/generation assets that
    must be byte-identical across the two reward arms.
    """
    if namespace not in E6_SEED_NAMESPACES:
        raise ValueError(
            "namespace must be one of " + ", ".join(sorted(E6_SEED_NAMESPACES))
        )
    if not size or not arm_scope:
        raise ValueError("size and arm_scope must be nonempty")
    if modulus < 2 or round_index < 0 or seed_slot < 0:
        raise ValueError("modulus, round_index, and seed_slot must be valid")
    source = (
        f"e6|{base_seed}|{namespace}|{size}|{modulus}|{arm_scope}|"
        f"{round_index}|{seed_slot}"
    )
    return int.from_bytes(hashlib.sha256(source.encode()).digest()[:8], "big")


def _signal_map(
    values: Sequence[CommitmentSurfaceSignal | GroundTruthSignal],
    pool: CandidatePool,
    name: str,
) -> dict[str, CommitmentSurfaceSignal | GroundTruthSignal]:
    mapped = {value.candidate_id: value for value in values}
    if len(mapped) != len(values):
        raise ValueError(f"{name} contains duplicate candidate_id values")
    expected = {candidate.candidate_id for candidate in pool.candidates}
    if set(mapped) != expected:
        raise ValueError(f"{name} must cover the candidate pool exactly")
    return mapped


def _selection_count(pool: CandidatePool, config: E6Config) -> int:
    return max(1, math.floor(len(pool.candidates) * config.selection_fraction))


def _ranked_selection(
    *,
    arm: E6Arm,
    pool: CandidatePool,
    pool_digest: str,
    rewards: Mapping[str, float],
    eligible_ids: set[str] | None,
    selected_count: int,
) -> RoundSelection:
    candidates = [
        candidate
        for candidate in pool.candidates
        if eligible_ids is None or candidate.candidate_id in eligible_ids
    ]
    if len(candidates) < selected_count:
        raise ValueError(
            f"need {selected_count} eligible {arm.value} candidates, "
            f"found {len(candidates)}"
        )
    ranked = sorted(
        candidates,
        key=lambda candidate: (-rewards[candidate.candidate_id], candidate.order),
    )[:selected_count]
    return RoundSelection(
        arm=arm,
        round_index=pool.round_index,
        pool_digest=pool_digest,
        candidate_count=len(pool.candidates),
        selected_candidate_ids=tuple(item.candidate_id for item in ranked),
        selected_rewards=tuple(float(rewards[item.candidate_id]) for item in ranked),
    )


def _self_consistency_rewards(pool: CandidatePool) -> dict[str, float]:
    by_input: dict[int, list[Candidate]] = defaultdict(list)
    for candidate in pool.candidates:
        by_input[candidate.input_id].append(candidate)
    rewards: dict[str, float] = {}
    for candidates in by_input.values():
        counts = Counter(candidate.generation for candidate in candidates)
        first_order: dict[int, int] = {}
        for candidate in candidates:
            first_order.setdefault(candidate.generation, candidate.order)
        majority = min(
            counts,
            key=lambda generation: (-counts[generation], first_order[generation]),
        )
        rewards.update(
            {
                candidate.candidate_id: float(candidate.generation == majority)
                for candidate in candidates
            }
        )
    return rewards


def plan_round(
    pool: CandidatePool,
    config: E6Config,
    *,
    cs_signals: Sequence[CommitmentSurfaceSignal],
    gt_signals: Sequence[GroundTruthSignal],
) -> RoundPlan:
    """Score one frozen pool under all arms and select matched training volume."""
    if pool.round_index > config.rounds:
        raise ValueError("round_index exceeds configured E6 rounds")
    generation_counts = Counter(
        candidate.input_id for candidate in pool.candidates
    )
    if any(
        count != config.generations_per_input
        for count in generation_counts.values()
    ):
        raise ValueError(
            "each candidate-pool input requires exactly "
            f"{config.generations_per_input} generations"
        )
    selected_count = _selection_count(pool, config)
    sc_rewards = _self_consistency_rewards(pool)
    raw_cs = _signal_map(cs_signals, pool, "cs_signals")
    raw_gt = _signal_map(gt_signals, pool, "gt_signals")
    cs_values = {
        candidate_id: signal
        for candidate_id, signal in raw_cs.items()
        if isinstance(signal, CommitmentSurfaceSignal)
    }
    gt_values = {
        candidate_id: signal
        for candidate_id, signal in raw_gt.items()
        if isinstance(signal, GroundTruthSignal)
    }
    if len(cs_values) != len(pool.candidates) or len(gt_values) != len(pool.candidates):
        raise TypeError("reward signals have the wrong typed record")

    cs_eligible = {
        candidate_id
        for candidate_id, signal in cs_values.items()
        if signal.canonical_patch_ce >= config.patch_ce_threshold
        and signal.transported_patch_ce >= config.patch_ce_threshold
    }
    cs_rewards = {
        candidate_id: (
            signal.canonical_patch_ce if candidate_id in cs_eligible else 0.0
        )
        for candidate_id, signal in cs_values.items()
    }
    gt_rewards = {
        candidate_id: float(signal.correct)
        for candidate_id, signal in gt_values.items()
    }
    digest = pool.digest()
    selections = (
        _ranked_selection(
            arm=E6Arm.SC,
            pool=pool,
            pool_digest=digest,
            rewards=sc_rewards,
            eligible_ids=None,
            selected_count=selected_count,
        ),
        _ranked_selection(
            arm=E6Arm.CS,
            pool=pool,
            pool_digest=digest,
            rewards=cs_rewards,
            eligible_ids=cs_eligible,
            selected_count=selected_count,
        ),
        _ranked_selection(
            arm=E6Arm.GT,
            pool=pool,
            pool_digest=digest,
            rewards=gt_rewards,
            eligible_ids=None,
            selected_count=selected_count,
        ),
        RoundSelection(
            arm=E6Arm.A_REF,
            round_index=pool.round_index,
            pool_digest=digest,
            candidate_count=len(pool.candidates),
            selected_candidate_ids=(),
            selected_rewards=(),
        ),
    )
    round_plan = RoundPlan(pool.round_index, selections)
    if (
        round_plan.selection_for(E6Arm.SC).pool_digest
        != round_plan.selection_for(E6Arm.CS).pool_digest
        or round_plan.selection_for(E6Arm.SC).selected_candidate_count
        != round_plan.selection_for(E6Arm.CS).selected_candidate_count
    ):
        raise AssertionError("SC/CS candidate exposure mismatch")
    return round_plan


def plan_self_training_loop(
    pools: Sequence[CandidatePool],
    config: E6Config,
    *,
    cs_signals_by_round: Mapping[int, Sequence[CommitmentSurfaceSignal]],
    gt_signals_by_round: Mapping[int, Sequence[GroundTruthSignal]],
) -> tuple[RoundPlan, ...]:
    """Build the exact R=6 reward/selection ledger before any fine-tuning."""
    expected_rounds = tuple(range(1, config.rounds + 1))
    observed_rounds = tuple(pool.round_index for pool in pools)
    if observed_rounds != expected_rounds:
        raise ValueError("E6 loop requires exactly rounds 1..6 in order")
    if tuple(sorted(cs_signals_by_round)) != expected_rounds:
        raise ValueError("cs_signals_by_round must cover exactly rounds 1..6")
    if tuple(sorted(gt_signals_by_round)) != expected_rounds:
        raise ValueError("gt_signals_by_round must cover exactly rounds 1..6")
    return tuple(
        plan_round(
            pool,
            config,
            cs_signals=cs_signals_by_round[pool.round_index],
            gt_signals=gt_signals_by_round[pool.round_index],
        )
        for pool in pools
    )


def audit_matched_rounds(rounds: Sequence[RoundPlan]) -> dict[str, object]:
    mismatches: list[dict[str, object]] = []
    for round_plan in rounds:
        sc = round_plan.selection_for(E6Arm.SC)
        cs = round_plan.selection_for(E6Arm.CS)
        fields = []
        if sc.pool_digest != cs.pool_digest:
            fields.append("pool_digest")
        if sc.candidate_count != cs.candidate_count:
            fields.append("candidate_count")
        if sc.selected_candidate_count != cs.selected_candidate_count:
            fields.append("selected_candidate_count")
        if fields:
            mismatches.append(
                {"round": round_plan.round_index, "fields": fields}
            )
    return {
        "matched_round_count": len(rounds) - len(mismatches),
        "mismatches": mismatches,
        "pass": bool(rounds) and not mismatches,
    }


def collapse_trajectory(
    accuracies: Sequence[float], *, tolerance: float = 0.05
) -> tuple[bool, ...]:
    tolerance = _require_finite_number(tolerance, "tolerance")
    if tolerance < 0.0:
        raise ValueError("tolerance must be nonnegative")
    peak = float("-inf")
    result: list[bool] = []
    for accuracy in accuracies:
        value = _require_finite_number(accuracy, "accuracy")
        peak = max(peak, value)
        result.append(value < peak - tolerance)
    return tuple(result)
