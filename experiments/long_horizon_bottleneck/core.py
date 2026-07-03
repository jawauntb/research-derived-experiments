"""Shared helpers for the long-horizon moved-bottleneck experiment.

The Modal runner owns model training. This module stays dependency-light so
local tests can verify the manifest, budget guard, and gate summaries without
importing Modal or Torch.
"""

from __future__ import annotations

import math
import random
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Iterable

DEFAULT_GPU = "L4"
GPU_RATES_PER_SECOND = {
    # Modal pricing page, checked 2026-07-02. These are GPU-only rates; Modal
    # also bills CPU/RAM. We keep the guard conservative by multiplying later.
    "T4": 0.000164,
    "L4": 0.000222,
    "A10": 0.000306,
    "A10G": 0.000306,
    "H100": 0.001097,
}


@dataclass(frozen=True)
class BudgetEstimate:
    cells: int
    gpu: str
    timeout_seconds: int
    raw_gpu_cost_usd: float
    conservative_cost_usd: float
    budget_usd: float
    within_budget: bool


def parse_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_int_csv(value: str) -> list[int]:
    return [int(item) for item in parse_csv(value)]


def gpu_rate_per_second(gpu: str) -> float:
    key = gpu.upper()
    if key not in GPU_RATES_PER_SECOND:
        known = ", ".join(sorted(GPU_RATES_PER_SECOND))
        raise ValueError(f"Unknown GPU {gpu!r}. Known rates: {known}")
    return GPU_RATES_PER_SECOND[key]


def estimate_modal_cost(
    *,
    cells: int,
    gpu: str = DEFAULT_GPU,
    timeout_seconds: int,
    budget_usd: float,
    overhead_multiplier: float = 1.35,
) -> BudgetEstimate:
    """Estimate worst-case Modal GPU spend if every cell hits timeout."""

    raw = cells * timeout_seconds * gpu_rate_per_second(gpu)
    conservative = raw * overhead_multiplier
    return BudgetEstimate(
        cells=cells,
        gpu=gpu.upper(),
        timeout_seconds=timeout_seconds,
        raw_gpu_cost_usd=raw,
        conservative_cost_usd=conservative,
        budget_usd=budget_usd,
        within_budget=conservative <= budget_usd,
    )


def build_cells(
    *,
    seeds: Iterable[int],
    architectures: Iterable[str],
    conditions: Iterable[str],
    critical_slots: Iterable[int],
    n_slots: int,
    sequence_length: int,
    slot_gap: int,
    train_steps: int,
    batch_size: int,
    eval_batches: int,
    metric_batches: int,
    hidden_size: int,
    base_seed: int,
) -> list[dict[str, Any]]:
    if n_slots <= 0:
        raise ValueError("n_slots must be positive")
    if slot_gap <= 0:
        raise ValueError("slot_gap must be positive")
    slot_positions = default_slot_positions(n_slots, slot_gap)
    if slot_positions[-1] >= sequence_length - 1:
        raise ValueError(
            "slot positions must leave the final sequence element for the query "
            f"(last slot={slot_positions[-1]}, sequence_length={sequence_length})"
        )
    cells: list[dict[str, Any]] = []
    for arch in architectures:
        for condition in conditions:
            for critical_slot in critical_slots:
                if not 0 <= critical_slot < n_slots:
                    raise ValueError(f"critical_slot={critical_slot} outside n_slots={n_slots}")
                for seed_index, seed in enumerate(seeds):
                    cells.append(
                        {
                            "architecture": arch,
                            "condition": condition,
                            "critical_slot": critical_slot,
                            "seed": base_seed + int(seed) + 1000 * seed_index,
                            "n_slots": n_slots,
                            "sequence_length": sequence_length,
                            "slot_positions": slot_positions,
                            "train_steps": train_steps,
                            "batch_size": batch_size,
                            "eval_batches": eval_batches,
                            "metric_batches": metric_batches,
                            "hidden_size": hidden_size,
                        }
                    )
    return cells


def build_horizon_cells(
    *,
    sequence_lengths: Iterable[int],
    seeds: Iterable[int],
    architectures: Iterable[str],
    conditions: Iterable[str],
    critical_slots: Iterable[int],
    n_slots: int,
    slot_gap: int,
    train_steps: int,
    batch_size: int,
    eval_batches: int,
    metric_batches: int,
    hidden_size: int,
    base_seed: int,
) -> list[dict[str, Any]]:
    sequence_values = list(sequence_lengths)
    seed_values = list(seeds)
    architecture_values = list(architectures)
    condition_values = list(conditions)
    slot_values = list(critical_slots)
    cells: list[dict[str, Any]] = []
    for sequence_index, sequence_length in enumerate(sequence_values):
        cells.extend(
            build_cells(
                seeds=seed_values,
                architectures=architecture_values,
                conditions=condition_values,
                critical_slots=slot_values,
                n_slots=n_slots,
                sequence_length=sequence_length,
                slot_gap=slot_gap,
                train_steps=train_steps,
                batch_size=batch_size,
                eval_batches=eval_batches,
                metric_batches=metric_batches,
                hidden_size=hidden_size,
                base_seed=base_seed + 100_000 * sequence_index,
            )
        )
    return cells


def default_slot_positions(n_slots: int, slot_gap: int) -> list[int]:
    first = slot_gap
    return [first + i * slot_gap for i in range(n_slots)]


def mean(xs: Iterable[float]) -> float:
    vals = [float(x) for x in xs if math.isfinite(float(x))]
    return sum(vals) / len(vals) if vals else float("nan")


def bootstrap_mean_ci(xs: Iterable[float], *, n_boot: int = 2000, seed: int = 20260702) -> dict[str, Any]:
    vals = [float(x) for x in xs if math.isfinite(float(x))]
    if not vals:
        return {"mean": float("nan"), "se": float("nan"), "ci95": [float("nan"), float("nan")], "n": 0}
    if len(vals) == 1:
        return {"mean": vals[0], "se": 0.0, "ci95": [vals[0], vals[0]], "n": 1}
    rng = random.Random(seed)
    boots = []
    n = len(vals)
    for _ in range(n_boot):
        boots.append(sum(vals[rng.randrange(n)] for _ in range(n)) / n)
    boots.sort()
    lo = boots[int(0.025 * (n_boot - 1))]
    hi = boots[int(0.975 * (n_boot - 1))]
    mu = sum(vals) / n
    var = sum((x - mu) ** 2 for x in boots) / max(1, len(boots) - 1)
    return {"mean": mu, "se": math.sqrt(var), "ci95": [lo, hi], "n": n}


def summarize_rows(rows: list[dict[str, Any]], *, n_boot: int = 2000) -> dict[str, Any]:
    """Summarize Modal cell rows into preregistered gate statistics."""

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    horizon_grouped: dict[tuple[str, str, int], list[dict[str, Any]]] = defaultdict(list)
    by_slot: dict[tuple[str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (str(row["condition"]), str(row["architecture"]))
        grouped[key].append(row)
        if "sequence_length" in row:
            horizon_grouped[(key[0], key[1], int(row["sequence_length"]))].append(row)
        by_slot[(key[0], key[1], int(row["critical_slot"]))].append(row)

    out: dict[str, Any] = {"n_rows": len(rows), "groups": {}, "horizon_groups": {}, "slot_groups": {}}
    for (condition, arch), group_rows in sorted(grouped.items()):
        out["groups"][f"{condition}/{arch}"] = summarize_gate_group(
            group_rows,
            visible_control=condition == "visible_control",
            n_boot=n_boot,
        )

    for (condition, arch, sequence_length), group_rows in sorted(horizon_grouped.items()):
        out["horizon_groups"][f"{condition}/{arch}/length_{sequence_length}"] = summarize_gate_group(
            group_rows,
            visible_control=condition == "visible_control",
            n_boot=n_boot,
        )

    for (condition, arch, slot), group_rows in sorted(by_slot.items()):
        out["slot_groups"][f"{condition}/{arch}/slot_{slot}"] = {
            "accuracy": bootstrap_mean_ci([r["accuracy"] for r in group_rows], n_boot=n_boot, seed=20260705),
            "memory_specificity_z": bootstrap_mean_ci(
                [r["memory_specificity_z"] for r in group_rows],
                n_boot=n_boot,
                seed=20260706,
            ),
        }

    transport_groups = [
        item
        for key, item in out["groups"].items()
        if key.startswith("bottleneck/")
    ]
    if transport_groups:
        out["pooled_bottleneck"] = {
            "accuracy": bootstrap_mean_ci(
                [r["accuracy"] for r in rows if r["condition"] == "bottleneck"],
                n_boot=n_boot,
                seed=20260707,
            ),
            "memory_specificity_z": bootstrap_mean_ci(
                [r["memory_specificity_z"] for r in rows if r["condition"] == "bottleneck"],
                n_boot=n_boot,
                seed=20260708,
            ),
            "memory_rank_percentile": bootstrap_mean_ci(
                [r["memory_rank_percentile"] for r in rows if r["condition"] == "bottleneck"],
                n_boot=n_boot,
                seed=20260709,
            ),
        }
        pooled = out["pooled_bottleneck"]
        pooled["gate"] = {
            "behavior_acc_ge_0_90": pooled["accuracy"]["mean"] >= 0.90,
            "specificity_positive": pooled["memory_specificity_z"]["ci95"][0] > 0.0,
            "rank_above_chance": pooled["memory_rank_percentile"]["mean"] > 0.5,
        }
        pooled["gate"]["pass"] = all(pooled["gate"].values())

    return out


def summarize_gate_group(
    rows: list[dict[str, Any]],
    *,
    visible_control: bool,
    n_boot: int = 2000,
) -> dict[str, Any]:
    spec = [r["memory_specificity_z"] for r in rows]
    acc = [r["accuracy"] for r in rows]
    rank = [r["memory_rank_percentile"] for r in rows]
    spec_stat = bootstrap_mean_ci(spec, n_boot=n_boot, seed=20260702)
    acc_stat = bootstrap_mean_ci(acc, n_boot=n_boot, seed=20260703)
    rank_stat = bootstrap_mean_ci(rank, n_boot=n_boot, seed=20260704)
    gate = {
        "behavior_acc_ge_0_90": acc_stat["mean"] >= 0.90,
        "specificity_positive": spec_stat["ci95"][0] > 0.0,
        "rank_above_chance": rank_stat["mean"] > 0.5,
    }
    if visible_control:
        gate = {
            "behavior_acc_ge_0_90": acc_stat["mean"] >= 0.90,
            "specificity_not_strong_positive": spec_stat["mean"] < 0.5,
        }
    gate["pass"] = all(gate.values())
    return {
        "accuracy": acc_stat,
        "memory_specificity_z": spec_stat,
        "memory_rank_percentile": rank_stat,
        "gate": gate,
    }


def summarize_tool_rows(rows: list[dict[str, Any]], *, n_boot: int = 2000) -> dict[str, Any]:
    """Summarize tool-commitment rows with behavior and commitment gates."""

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    by_slot: dict[tuple[str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (str(row["condition"]), str(row["architecture"]))
        grouped[key].append(row)
        by_slot[(key[0], key[1], int(row["critical_slot"]))].append(row)

    out: dict[str, Any] = {"n_rows": len(rows), "groups": {}, "slot_groups": {}}
    for (condition, arch), group_rows in sorted(grouped.items()):
        out["groups"][f"{condition}/{arch}"] = summarize_tool_gate_group(
            group_rows,
            visible_control=condition == "visible_control",
            n_boot=n_boot,
        )

    for (condition, arch, slot), group_rows in sorted(by_slot.items()):
        out["slot_groups"][f"{condition}/{arch}/slot_{slot}"] = summarize_tool_gate_group(
            group_rows,
            visible_control=condition == "visible_control",
            n_boot=n_boot,
        )

    bottleneck_rows = [r for r in rows if r["condition"] == "tool_bottleneck"]
    if bottleneck_rows:
        out["pooled_tool_bottleneck"] = summarize_tool_gate_group(
            bottleneck_rows,
            visible_control=False,
            n_boot=n_boot,
        )

    return out


def summarize_tool_gate_group(
    rows: list[dict[str, Any]],
    *,
    visible_control: bool,
    n_boot: int = 2000,
) -> dict[str, Any]:
    final_key = "closed_loop_final_accuracy" if all("closed_loop_final_accuracy" in r for r in rows) else "final_accuracy"
    final_acc = bootstrap_mean_ci([r[final_key] for r in rows], n_boot=n_boot, seed=20260710)
    teacher_forced_acc = None
    if all("teacher_forced_final_accuracy" in r for r in rows):
        teacher_forced_acc = bootstrap_mean_ci(
            [r["teacher_forced_final_accuracy"] for r in rows],
            n_boot=n_boot,
            seed=20260716,
        )
    tool_slot_acc = bootstrap_mean_ci([r["tool_slot_accuracy"] for r in rows], n_boot=n_boot, seed=20260711)
    memory_spec = bootstrap_mean_ci([r["memory_specificity_z"] for r in rows], n_boot=n_boot, seed=20260712)
    memory_rank = bootstrap_mean_ci([r["memory_rank_percentile"] for r in rows], n_boot=n_boot, seed=20260713)
    tool_value_spec = bootstrap_mean_ci([r["tool_value_specificity_z"] for r in rows], n_boot=n_boot, seed=20260714)

    gate = {
        f"{final_key}_ge_0_90": final_acc["mean"] >= 0.90,
        "tool_slot_acc_ge_0_90": tool_slot_acc["mean"] >= 0.90,
        "memory_specificity_positive": memory_spec["ci95"][0] > 0.0,
        "tool_value_specificity_positive": tool_value_spec["ci95"][0] > 0.0,
        "rank_above_chance": memory_rank["mean"] > 0.5,
    }
    tool_value_acc = None
    if visible_control:
        gate = {
            f"{final_key}_ge_0_90": final_acc["mean"] >= 0.90,
            "tool_slot_null_acc_ge_0_90": tool_slot_acc["mean"] >= 0.90,
            "memory_specificity_not_strong_positive": memory_spec["mean"] < 0.5,
        }
    else:
        tool_value_acc = bootstrap_mean_ci([r["tool_value_accuracy"] for r in rows], n_boot=n_boot, seed=20260715)
        gate["tool_value_acc_ge_0_90"] = tool_value_acc["mean"] >= 0.90
    gate["pass"] = all(gate.values())

    item = {
        "final_metric": final_key,
        "final_accuracy": final_acc,
        "tool_slot_accuracy": tool_slot_acc,
        "memory_specificity_z": memory_spec,
        "memory_rank_percentile": memory_rank,
        "tool_value_specificity_z": tool_value_spec,
        "gate": gate,
    }
    if tool_value_acc is not None:
        item["tool_value_accuracy"] = tool_value_acc
    if teacher_forced_acc is not None:
        item["teacher_forced_final_accuracy"] = teacher_forced_acc
    return item
