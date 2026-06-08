#!/usr/bin/env python3
"""Helpers for label-free readout basin diagnostics."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any


PATCH_TEXT_REGIMES = ("definition", "neutral")
BASIN_SOURCE_SWEEP = (
    ("attractor", "attractor_network", "prototype", "positive"),
    ("prototype", "attractor_network", "attractor", "source_family"),
    ("schema", "attractor_network", "attractor", "source_family"),
    ("conceptual_space", "attractor_network", "prototype", "source_family"),
    ("basin_of_attraction", "attractor_network", "attractor", "source_family"),
)
GENERIC_TRANSFER_CONTROLS = (
    ("valence", "activation_vector", "steering_vector", "generic_control"),
    ("valence", "steering_vector", "activation_vector", "generic_control"),
)


@dataclass(frozen=True)
class LabelFreeReadoutPair:
    id: str
    left: str
    right: str
    kind: str
    distractor: str


def pair_id(*, left: str, right: str, distractor: str) -> str:
    return f"{left}->{right}/d={distractor}"


def label_free_pair_specs() -> list[LabelFreeReadoutPair]:
    rows = []
    for left, right, distractor, kind in (
        *BASIN_SOURCE_SWEEP,
        *GENERIC_TRANSFER_CONTROLS,
    ):
        rows.append(
            LabelFreeReadoutPair(
                id=pair_id(left=left, right=right, distractor=distractor),
                left=left,
                right=right,
                kind=kind,
                distractor=distractor,
            )
        )
    return rows


def serializable_pair_specs(pairs: list[LabelFreeReadoutPair]) -> list[dict[str, Any]]:
    return [asdict(pair) for pair in pairs]


def neutral_carrier_text(*, label: str) -> str:
    return f"Concept label: {label}."


def source_text_for_regime(
    *,
    definition_text: str,
    label: str,
    patch_text_regime: str,
) -> str:
    if patch_text_regime == "definition":
        return definition_text
    if patch_text_regime == "neutral":
        return neutral_carrier_text(label=label)
    options = ", ".join(PATCH_TEXT_REGIMES)
    raise ValueError(f"Patch text regime must be one of: {options}")


def vector_mean(vectors: list[list[float]]) -> list[float]:
    if not vectors:
        raise ValueError("Cannot compute a mean over no vectors")
    dimensions = len(vectors[0])
    return [
        sum(vector[index] for vector in vectors) / len(vectors)
        for index in range(dimensions)
    ]


def subtract(left: list[float], right: list[float]) -> list[float]:
    return [left_value - right_value for left_value, right_value in zip(left, right)]


def normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return [0.0 for _ in vector]
    return [value / norm for value in vector]


def cosine(left: list[float], right: list[float]) -> float:
    return sum(left_value * right_value for left_value, right_value in zip(left, right))


def centroid(vectors: list[list[float]]) -> list[float]:
    return normalize(vector_mean(vectors))


def target_margin(scores: dict[str, float]) -> float:
    return scores["target"] - ((scores["source"] + scores["distractor"]) / 2)


def summarize_readout_delta(
    *,
    baseline_scores: dict[str, float],
    patched_scores: dict[str, float],
    patched_target_rank: int,
) -> dict[str, Any]:
    baseline_margin = target_margin(baseline_scores)
    patched_margin = target_margin(patched_scores)
    return {
        "baseline_target_margin": baseline_margin,
        "patched_target_margin": patched_margin,
        "target_margin_delta": patched_margin - baseline_margin,
        "target_score_delta": patched_scores["target"] - baseline_scores["target"],
        "source_score_delta": patched_scores["source"] - baseline_scores["source"],
        "distractor_score_delta": (
            patched_scores["distractor"] - baseline_scores["distractor"]
        ),
        "patched_target_rank": patched_target_rank,
        "patched_target_top3": patched_target_rank <= 3,
    }


def aggregate_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in rows:
        key = (
            row["kind"],
            row["pair"],
            row["injection_layer"],
            row["readout_layer"],
            row["patch_text_regime"],
            row["patch_mode"],
        )
        grouped.setdefault(key, []).append(row)

    aggregates = []
    for (
        kind,
        pair,
        injection_layer,
        readout_layer,
        patch_text_regime,
        patch_mode,
    ), group in grouped.items():
        deltas = [row["summary"]["target_margin_delta"] for row in group]
        top3_count = sum(1 for row in group if row["summary"]["patched_target_top3"])
        pass_count = sum(1 for value in deltas if value > 0)
        mean_delta = sum(deltas) / len(deltas)
        aggregates.append(
            {
                "kind": kind,
                "pair": pair,
                "injection_layer": injection_layer,
                "readout_layer": readout_layer,
                "patch_text_regime": patch_text_regime,
                "patch_mode": patch_mode,
                "mean_target_margin_delta": mean_delta,
                "min_target_margin_delta": min(deltas),
                "max_target_margin_delta": max(deltas),
                "pass_count": pass_count,
                "top3_count": top3_count,
                "total": len(group),
                "robust_pass": mean_delta > 0 and top3_count == len(group),
            }
        )
    return sorted(
        aggregates,
        key=lambda row: (
            str(row["patch_text_regime"]),
            str(row["kind"]),
            str(row["pair"]),
            int(row["injection_layer"]),
            int(row["readout_layer"]),
            str(row["patch_mode"]),
        ),
    )


def specificity_rows(aggregates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], dict[str, dict[str, Any]]] = {}
    control_modes = ("distractor", "random", "source_noop")
    for row in aggregates:
        key = (
            row["kind"],
            row["pair"],
            row["injection_layer"],
            row["readout_layer"],
            row["patch_text_regime"],
        )
        grouped.setdefault(key, {})[str(row["patch_mode"])] = row

    rows = []
    for (
        kind,
        pair,
        injection_layer,
        readout_layer,
        patch_text_regime,
    ), by_mode in grouped.items():
        if "target" not in by_mode:
            continue
        missing_controls = [mode for mode in control_modes if mode not in by_mode]
        if missing_controls:
            continue
        target = by_mode["target"]
        control_means = {
            mode: by_mode[mode]["mean_target_margin_delta"]
            for mode in control_modes
        }
        best_control_mode = max(control_means, key=control_means.__getitem__)
        best_control_delta = control_means[best_control_mode]
        target_advantage = target["mean_target_margin_delta"] - best_control_delta
        rows.append(
            {
                "kind": kind,
                "pair": pair,
                "injection_layer": injection_layer,
                "readout_layer": readout_layer,
                "patch_text_regime": patch_text_regime,
                "target_mean_target_margin_delta": target["mean_target_margin_delta"],
                "target_top3_count": target["top3_count"],
                "target_total": target["total"],
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
            str(row["patch_text_regime"]),
            str(row["kind"]),
            str(row["pair"]),
            int(row["injection_layer"]),
            int(row["readout_layer"]),
        ),
    )


def _mean_or_none(rows: list[dict[str, Any]], key: str) -> float | None:
    if not rows:
        return None
    return sum(float(row[key]) for row in rows) / len(rows)


def gate_summaries(specificity: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries = []
    for patch_text_regime in PATCH_TEXT_REGIMES:
        selected = [
            row for row in specificity if row["patch_text_regime"] == patch_text_regime
        ]
        for kind in ("positive", "source_family", "generic_control"):
            rows = [row for row in selected if row["kind"] == kind]
            summaries.append(
                {
                    "patch_text_regime": patch_text_regime,
                    "kind": kind,
                    "specific_pass_count": sum(
                        1 for row in rows if row["specific_target_pass"]
                    ),
                    "total": len(rows),
                    "mean_target_margin_delta": _mean_or_none(
                        rows,
                        "target_mean_target_margin_delta",
                    ),
                    "mean_advantage_over_best_control": _mean_or_none(
                        rows,
                        "target_advantage_over_best_control",
                    ),
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
