#!/usr/bin/env python3
"""Shared P1 weakness metrics for the external-contact Pythia LoRA run.

The Modal worker is intentionally thin around these functions: it produces
function tables and classical predictors, while this module owns the same
acceptance logic used by the local tests and result summaries.
"""

from __future__ import annotations

import math
import random
from collections.abc import Mapping, Sequence
from typing import Any


def spearman(xs: Sequence[float], ys: Sequence[float]) -> float:
    """Spearman rank correlation with average ranks for ties."""
    if len(xs) != len(ys) or len(xs) < 2:
        return 0.0

    def rank(vals: Sequence[float]) -> list[float]:
        order = sorted(range(len(vals)), key=lambda i: vals[i])
        ranks = [0.0] * len(vals)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                ranks[order[k]] = avg
            i = j + 1
        return ranks

    rx, ry = rank(xs), rank(ys)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return num / den if den else 0.0


def cyclic_group(n: int) -> tuple[tuple[int, ...], ...]:
    if n < 2:
        raise ValueError("n must be at least 2")
    return tuple(tuple((x + shift) % n for x in range(n)) for shift in range(n))


def wrong_group(
    n: int,
    *,
    rng: random.Random,
    target_size: int | None = None,
    max_attempts: int = 5000,
) -> tuple[tuple[int, ...], ...]:
    """Random equal-cardinality control group excluding non-identity Z_n shifts."""
    if n < 2:
        raise ValueError("n must be at least 2")
    target = target_size if target_size is not None else n
    if target < 1:
        raise ValueError("target_size must be positive")

    identity = tuple(range(n))
    cyclic = set(cyclic_group(n))
    out: list[tuple[int, ...]] = [identity]
    attempts = 0
    while len(out) < target and attempts < max_attempts:
        perm = list(range(n))
        rng.shuffle(perm)
        candidate = tuple(perm)
        if candidate not in cyclic and candidate not in out:
            out.append(candidate)
        attempts += 1
    return tuple(out)


def equivariance_count(
    table: Sequence[int],
    group: Sequence[Sequence[int]],
) -> int:
    """Count input-group elements whose induced outputs match some group element."""
    n = len(table)
    if n < 2:
        raise ValueError("table must contain at least two outputs")
    if any(y < 0 or y >= n for y in table):
        raise ValueError("table outputs must be indices in the same finite set")

    count = 0
    for g in group:
        induced = tuple(table[g[x]] for x in range(n))
        for h in group:
            if all(h[table[x]] == induced[x] for x in range(n)):
                count += 1
                break
    return count


def _float(cell: Mapping[str, Any], key: str) -> float:
    value = cell.get(key)
    if isinstance(value, bool) or value is None:
        raise ValueError(f"{key} must be numeric")
    return float(value)


def _finite_cells(cells: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    return [cell for cell in cells if not math.isnan(_float(cell, "ood_accuracy"))]


def analyze_cells(cells: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Compute the preregistered P1 correlations and pass/kill verdicts."""
    valid = _finite_cells(cells)
    if not valid:
        return {"n_cells": 0, "P1_pass": None, "P1_hard_kill": None}

    ood = [_float(cell, "ood_accuracy") for cell in valid]
    weakness = [_float(cell, "weakness_oracle_norm") for cell in valid]
    wrong = [_float(cell, "weakness_wrong_group_norm") for cell in valid]
    loss = [_float(cell, "final_train_loss") for cell in valid]
    ood_nll = [_float(cell, "ood_nll") for cell in valid]
    param_count = [_float(cell, "pythia_param_count") for cell in valid]
    l2 = [_float(cell, "pythia_l2") for cell in valid]
    sharp = [_float(cell, "head_sharpness_proxy") for cell in valid]

    analysis: dict[str, Any] = {
        "n_cells": len(valid),
        "ood_unique_values": len(set(ood)),
        "P1_degenerate_ood_column": len(set(ood)) < 2,
        "rho_weakness_vs_ood": spearman(weakness, ood),
        "rho_wrong_group_vs_ood": spearman(wrong, ood),
        "rho_loss_vs_ood": spearman(loss, ood),
        "rho_ood_nll_vs_ood": spearman(ood_nll, ood),
        "rho_param_count_vs_ood": spearman(param_count, ood),
        "rho_l2_vs_ood": spearman(l2, ood),
        "rho_sharpness_vs_ood": spearman(sharp, ood),
    }

    rho_w = float(analysis["rho_weakness_vs_ood"])
    rival_keys = (
        "rho_loss_vs_ood",
        "rho_ood_nll_vs_ood",
        "rho_param_count_vs_ood",
        "rho_l2_vs_ood",
        "rho_sharpness_vs_ood",
    )
    rivals = [abs(float(analysis[key])) for key in rival_keys]
    best_rival = max(rivals) if rivals else 0.0
    analysis["best_classical_abs_rho"] = best_rival
    analysis["weakness_beats_best_classical_by_margin"] = abs(rho_w) - best_rival
    analysis["P1_pass"] = (
        rho_w >= 0.5
        and (abs(rho_w) - best_rival) >= 0.25
        and abs(float(analysis["rho_wrong_group_vs_ood"])) <= 0.15
    )
    analysis["P1_hard_kill"] = rho_w < 0.3 or any(abs(rho_w) - rival <= 0.10 for rival in rivals)
    analysis["P1_soft_kill_wrong_group"] = abs(float(analysis["rho_wrong_group_vs_ood"])) > 0.25
    return analysis
