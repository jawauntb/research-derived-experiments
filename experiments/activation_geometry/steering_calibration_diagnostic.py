#!/usr/bin/env python3
"""Helpers for calibrating final-token activation steering directions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


OPTION_ORDERS = (
    ("source", "target", "distractor"),
    ("target", "distractor", "source"),
    ("distractor", "source", "target"),
)
DIRECTION_MODES = (
    "raw_target_minus_source",
    "raw_source_minus_target",
    "unit_target_minus_source",
    "random_same_norm",
)


def parse_csv(value: str) -> list[str]:
    values = [part.strip() for part in value.split(",") if part.strip()]
    if not values:
        raise ValueError("At least one value must be provided")
    return values


def parse_option_orders(value: str) -> list[tuple[str, str, str]]:
    aliases = {
        "std": ("source", "target", "distractor"),
        "tds": ("target", "distractor", "source"),
        "dst": ("distractor", "source", "target"),
    }
    rows = []
    for token in parse_csv(value):
        if token not in aliases:
            options = ", ".join(sorted(aliases))
            raise ValueError(f"Option order must be one of: {options}")
        rows.append(aliases[token])
    return rows


def parse_direction_modes(value: str) -> list[str]:
    modes = parse_csv(value)
    invalid = sorted(set(modes) - set(DIRECTION_MODES))
    if invalid:
        options = ", ".join(DIRECTION_MODES)
        raise ValueError(f"Direction modes must be chosen from: {options}")
    return modes


def option_order_key(order: tuple[str, str, str]) -> str:
    initials = {
        "source": "s",
        "target": "t",
        "distractor": "d",
    }
    return "".join(initials[role] for role in order)


def calibration_prompt(
    *,
    source_text: str,
    labels_by_role: dict[str, str],
    option_order: tuple[str, str, str],
) -> str:
    slots = ("A", "B", "C")
    lines = [
        source_text,
        "",
        "Choose the closest related concept.",
    ]
    for slot, role in zip(slots, option_order, strict=True):
        lines.append(f"{slot}. {labels_by_role[role]}")
    lines.append("Answer:")
    return "\n".join(lines)


def role_slots(option_order: tuple[str, str, str]) -> dict[str, str]:
    return {
        role: slot
        for slot, role in zip(("A", "B", "C"), option_order, strict=True)
    }


def target_margin(scores: dict[str, float]) -> float:
    return scores["target"] - ((scores["source"] + scores["distractor"]) / 2)


def summarize_delta(
    *,
    baseline_scores: dict[str, float],
    steered_scores: dict[str, float],
) -> dict[str, Any]:
    baseline_margin = target_margin(baseline_scores)
    steered_margin = target_margin(steered_scores)
    return {
        "baseline_target_margin": baseline_margin,
        "steered_target_margin": steered_margin,
        "target_margin_delta": steered_margin - baseline_margin,
        "target_minus_source_delta": (
            (steered_scores["target"] - steered_scores["source"])
            - (baseline_scores["target"] - baseline_scores["source"])
        ),
        "target_minus_distractor_delta": (
            (steered_scores["target"] - steered_scores["distractor"])
            - (baseline_scores["target"] - baseline_scores["distractor"])
        ),
    }


def aggregate_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in rows:
        key = (
            row["role"],
            row["layer"],
            row["kind"],
            row["pair"],
            row["direction_mode"],
        )
        grouped.setdefault(key, []).append(row)

    aggregates = []
    for (role, layer, kind, pair, direction_mode), group in grouped.items():
        deltas = [row["summary"]["target_margin_delta"] for row in group]
        pass_count = sum(1 for value in deltas if value > 0)
        mean_delta = sum(deltas) / len(deltas)
        aggregates.append(
            {
                "role": role,
                "layer": layer,
                "kind": kind,
                "pair": pair,
                "direction_mode": direction_mode,
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
            str(row["direction_mode"]),
        ),
    )


def gate_summaries(aggregates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries = []
    for mode in DIRECTION_MODES:
        selected = [row for row in aggregates if row["direction_mode"] == mode]
        primary_positive = [
            row for row in selected if row["role"] == "primary" and row["kind"] == "positive"
        ]
        backup_positive = [
            row for row in selected if row["role"] == "backup" and row["kind"] == "positive"
        ]
        primary_controls = [
            row for row in selected if row["role"] == "primary" and row["kind"] == "control"
        ]
        control_layer_positive = [
            row for row in selected if row["role"] == "control" and row["kind"] == "positive"
        ]
        summaries.append(
            {
                "direction_mode": mode,
                "primary_positive_pass_count": sum(
                    1 for row in primary_positive if row["robust_pass"]
                ),
                "primary_positive_total": len(primary_positive),
                "backup_positive_pass_count": sum(
                    1 for row in backup_positive if row["robust_pass"]
                ),
                "backup_positive_total": len(backup_positive),
                "primary_valence_control_pass_count": sum(
                    1 for row in primary_controls if row["robust_pass"]
                ),
                "primary_valence_control_total": len(primary_controls),
                "control_layer_positive_pass_count": sum(
                    1 for row in control_layer_positive if row["robust_pass"]
                ),
                "control_layer_positive_total": len(control_layer_positive),
            }
        )
    return summaries


def public_summary(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "manifest": payload["manifest"],
        "gate_summaries": payload["gate_summaries"],
        "aggregate_rows": payload["aggregate_rows"],
    }


def write_payload(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
