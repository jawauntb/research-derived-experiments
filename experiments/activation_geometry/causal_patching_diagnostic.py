#!/usr/bin/env python3
"""Helpers for final-token causal patching diagnostics."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any


PATCH_MODES = ("target", "distractor", "random", "source_noop")
CONTROL_PATCH_MODES = ("distractor", "random", "source_noop")


def parse_csv(value: str) -> list[str]:
    values = [part.strip() for part in value.split(",") if part.strip()]
    if not values:
        raise ValueError("At least one value must be provided")
    return values


def parse_patch_modes(value: str) -> list[str]:
    modes = parse_csv(value)
    invalid = sorted(set(modes) - set(PATCH_MODES))
    if invalid:
        options = ", ".join(PATCH_MODES)
        raise ValueError(f"Patch modes must be chosen from: {options}")
    return modes


def target_margin(scores: dict[str, float]) -> float:
    return scores["target"] - ((scores["source"] + scores["distractor"]) / 2)


def summarize_delta(
    *,
    baseline_scores: dict[str, float],
    patched_scores: dict[str, float],
) -> dict[str, Any]:
    baseline_margin = target_margin(baseline_scores)
    patched_margin = target_margin(patched_scores)
    return {
        "baseline_target_margin": baseline_margin,
        "patched_target_margin": patched_margin,
        "target_margin_delta": patched_margin - baseline_margin,
        "target_minus_source_delta": (
            (patched_scores["target"] - patched_scores["source"])
            - (baseline_scores["target"] - baseline_scores["source"])
        ),
        "target_minus_distractor_delta": (
            (patched_scores["target"] - patched_scores["distractor"])
            - (baseline_scores["target"] - baseline_scores["distractor"])
        ),
    }


def choose_random_patch_concept(
    concepts: list[dict[str, Any]],
    pair: dict[str, Any],
    *,
    seed: int,
    pair_index: int,
) -> dict[str, str]:
    concept_ids = sorted(str(concept["id"]) for concept in concepts)
    category_by_id = {str(concept["id"]): str(concept["category"]) for concept in concepts}
    left = str(pair["left"])
    right = str(pair["right"])
    distractor = str(pair["distractor"])
    excluded = {left, right, distractor}
    target_category = category_by_id[right]
    same_category_pool = [
        concept_id
        for concept_id in concept_ids
        if concept_id not in excluded and category_by_id[concept_id] == target_category
    ]
    if same_category_pool:
        pool = same_category_pool
        scope = "target_category"
    else:
        pool = [concept_id for concept_id in concept_ids if concept_id not in excluded]
        scope = "all_categories_fallback"
    if not pool:
        raise ValueError(f"No random patch candidates available for {left}->{right}")
    rng = random.Random(seed + pair_index * 1009)
    return {
        "random_patch": pool[rng.randrange(len(pool))],
        "random_patch_scope": scope,
    }


def attach_random_patch_concepts(
    concepts: list[dict[str, Any]],
    pairs: list[dict[str, Any]],
    *,
    seed: int,
) -> list[dict[str, Any]]:
    patched_pairs = []
    for index, pair in enumerate(pairs):
        row = dict(pair)
        row.update(
            choose_random_patch_concept(
                concepts,
                pair,
                seed=seed,
                pair_index=index,
            )
        )
        patched_pairs.append(row)
    return patched_pairs


def aggregate_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in rows:
        key = (
            row["role"],
            row["layer"],
            row["kind"],
            row["pair"],
            row["patch_mode"],
        )
        grouped.setdefault(key, []).append(row)

    aggregates = []
    for (role, layer, kind, pair, patch_mode), group in grouped.items():
        deltas = [row["summary"]["target_margin_delta"] for row in group]
        pass_count = sum(1 for value in deltas if value > 0)
        mean_delta = sum(deltas) / len(deltas)
        aggregates.append(
            {
                "role": role,
                "layer": layer,
                "kind": kind,
                "pair": pair,
                "patch_mode": patch_mode,
                "mean_target_margin_delta": mean_delta,
                "min_target_margin_delta": min(deltas),
                "max_target_margin_delta": max(deltas),
                "option_order_pass_count": pass_count,
                "option_order_total": len(group),
                "robust_pass": mean_delta > 0 and pass_count >= 2,
            }
        )
    return sorted(
        aggregates,
        key=lambda row: (
            str(row["role"]),
            str(row["kind"]),
            str(row["pair"]),
            str(row["patch_mode"]),
        ),
    )


def specificity_rows(aggregates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], dict[str, dict[str, Any]]] = {}
    for row in aggregates:
        key = (
            row["role"],
            row["layer"],
            row["kind"],
            row["pair"],
        )
        grouped.setdefault(key, {})[str(row["patch_mode"])] = row

    rows = []
    for (role, layer, kind, pair), by_mode in grouped.items():
        if "target" not in by_mode:
            continue
        missing_controls = [
            mode for mode in CONTROL_PATCH_MODES if mode not in by_mode
        ]
        if missing_controls:
            continue
        target = by_mode["target"]
        control_means = {
            mode: by_mode[mode]["mean_target_margin_delta"]
            for mode in CONTROL_PATCH_MODES
        }
        best_control_mode = max(control_means, key=control_means.__getitem__)
        best_control_delta = control_means[best_control_mode]
        target_advantage = target["mean_target_margin_delta"] - best_control_delta
        rows.append(
            {
                "role": role,
                "layer": layer,
                "kind": kind,
                "pair": pair,
                "target_mean_target_margin_delta": target["mean_target_margin_delta"],
                "target_option_order_pass_count": target["option_order_pass_count"],
                "target_option_order_total": target["option_order_total"],
                "target_robust_pass": target["robust_pass"],
                "best_control_mode": best_control_mode,
                "best_control_mean_target_margin_delta": best_control_delta,
                "target_advantage_over_best_control": target_advantage,
                "specific_target_pass": target["robust_pass"] and target_advantage > 0,
            }
        )
    return sorted(
        rows,
        key=lambda row: (
            str(row["role"]),
            str(row["kind"]),
            str(row["pair"]),
        ),
    )


def gate_summaries(specificity: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries = []
    for role in ("primary", "backup", "control"):
        selected = [row for row in specificity if row["role"] == role]
        positives = [row for row in selected if row["kind"] == "positive"]
        controls = [row for row in selected if row["kind"] == "control"]
        exploratory = [row for row in selected if row["kind"] == "exploratory"]
        summaries.append(
            {
                "role": role,
                "positive_specific_pass_count": sum(
                    1 for row in positives if row["specific_target_pass"]
                ),
                "positive_total": len(positives),
                "valence_control_specific_pass_count": sum(
                    1 for row in controls if row["specific_target_pass"]
                ),
                "valence_control_total": len(controls),
                "exploratory_specific_pass_count": sum(
                    1 for row in exploratory if row["specific_target_pass"]
                ),
                "exploratory_total": len(exploratory),
            }
        )
    return summaries


def public_summary(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "manifest": payload["manifest"],
        "gate_summaries": payload["gate_summaries"],
        "specificity_rows": payload["specificity_rows"],
        "aggregate_rows": payload["aggregate_rows"],
    }


def write_payload(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
