#!/usr/bin/env python3
"""Pure-Python helpers for learned behavior-aligned direction pilots."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DIRECTION_MODES = (
    "target_learned",
    "source_learned",
    "distractor_learned",
    "random_same_norm",
)
OBJECTIVE_ROLES = ("target", "source", "distractor")


def parse_csv(value: str) -> list[str]:
    values = [part.strip() for part in value.split(",") if part.strip()]
    if not values:
        raise ValueError("At least one value must be provided")
    return values


def parse_direction_modes(value: str) -> list[str]:
    modes = parse_csv(value)
    invalid = sorted(set(modes) - set(DIRECTION_MODES))
    if invalid:
        options = ", ".join(DIRECTION_MODES)
        raise ValueError(f"Direction modes must be chosen from: {options}")
    return modes


def target_margin(scores: dict[str, float]) -> float:
    return scores["target"] - ((scores["source"] + scores["distractor"]) / 2)


def role_margin(scores: dict[str, float], role: str) -> float:
    if role not in OBJECTIVE_ROLES:
        options = ", ".join(OBJECTIVE_ROLES)
        raise ValueError(f"Role margin must use one of: {options}")
    others = [name for name in OBJECTIVE_ROLES if name != role]
    return scores[role] - sum(scores[name] for name in others) / len(others)


def summarize_behavior_delta(
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
        "target_logprob_delta": steered_scores["target"] - baseline_scores["target"],
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
            row["scale"],
        )
        grouped.setdefault(key, []).append(row)

    aggregates = []
    for (role, layer, kind, pair, direction_mode, scale), group in grouped.items():
        deltas = [row["summary"]["target_margin_delta"] for row in group]
        target_logprob_deltas = [row["summary"]["target_logprob_delta"] for row in group]
        pass_count = sum(1 for value in deltas if value > 0)
        mean_delta = sum(deltas) / len(deltas)
        aggregates.append(
            {
                "role": role,
                "layer": layer,
                "kind": kind,
                "pair": pair,
                "direction_mode": direction_mode,
                "scale": scale,
                "mean_target_margin_delta": mean_delta,
                "min_target_margin_delta": min(deltas),
                "max_target_margin_delta": max(deltas),
                "mean_target_logprob_delta": (
                    sum(target_logprob_deltas) / len(target_logprob_deltas)
                ),
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
            float(row["scale"]),
            str(row["direction_mode"]),
        ),
    )


def gate_summaries(aggregates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries = []
    for scale in sorted({float(row["scale"]) for row in aggregates}):
        for mode in DIRECTION_MODES:
            selected = [
                row
                for row in aggregates
                if float(row["scale"]) == scale and row["direction_mode"] == mode
            ]
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
                    "scale": scale,
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


def alignment_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in rows:
        key = (row["role"], row["layer"], row["kind"], row["pair"])
        grouped.setdefault(key, []).append(row)

    summaries = []
    for (role, layer, kind, pair), group in grouped.items():
        alignments = [row.get("learned_alignment", {}) for row in group]
        source_values = [
            alignment["target_source_cosine"]
            for alignment in alignments
            if alignment.get("target_source_cosine") is not None
        ]
        distractor_values = [
            alignment["target_distractor_cosine"]
            for alignment in alignments
            if alignment.get("target_distractor_cosine") is not None
        ]
        if not source_values and not distractor_values:
            continue
        summary: dict[str, Any] = {
            "role": role,
            "layer": layer,
            "kind": kind,
            "pair": pair,
        }
        if source_values:
            summary["mean_target_source_cosine"] = sum(source_values) / len(source_values)
        if distractor_values:
            summary["mean_target_distractor_cosine"] = (
                sum(distractor_values) / len(distractor_values)
            )
        summaries.append(summary)
    return sorted(
        summaries,
        key=lambda row: (str(row["role"]), str(row["kind"]), str(row["pair"])),
    )


def public_summary(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "manifest": payload["manifest"],
        "gate_summaries": payload["gate_summaries"],
        "alignment_summary": payload["alignment_summary"],
        "aggregate_rows": payload["aggregate_rows"],
    }


def write_payload(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
