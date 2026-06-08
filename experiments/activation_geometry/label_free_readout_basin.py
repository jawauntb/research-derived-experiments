#!/usr/bin/env python3
"""Helpers for label-free readout basin diagnostics."""

from __future__ import annotations

import math
import random
from dataclasses import asdict, dataclass
from typing import Any


PATCH_TEXT_REGIMES = ("definition", "neutral")
PAIR_SET_OPTIONS = ("focus", "baseline", "combined")
SUMMARY_KINDS = (
    "positive",
    "source_family",
    "generic_control",
    "baseline_same_category",
    "baseline_cross_category",
)
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


def focus_pair_ids() -> set[str]:
    return {row.id for row in label_free_pair_specs()}


def concept_id(row: Any) -> str:
    return str(row["id"] if isinstance(row, dict) else row.id)


def concept_category(row: Any) -> str:
    return str(row["category"] if isinstance(row, dict) else row.category)


def choose_baseline_distractor(
    concepts: list[Any],
    *,
    left: str,
    right: str,
    rng: random.Random,
) -> str:
    category_by_id = {concept_id(row): concept_category(row) for row in concepts}
    target_category = category_by_id[right]
    excluded = {left, right}
    same_target_category = [
        concept_id(row)
        for row in concepts
        if concept_id(row) not in excluded
        and category_by_id[concept_id(row)] == target_category
    ]
    pool = same_target_category or [
        concept_id(row) for row in concepts if concept_id(row) not in excluded
    ]
    if not pool:
        raise ValueError(f"No distractor candidates available for {left}->{right}")
    return pool[rng.randrange(len(pool))]


def sample_rows(
    rows: list[tuple[str, str, str]],
    *,
    count: int,
    rng: random.Random,
) -> list[tuple[str, str, str]]:
    shuffled = list(rows)
    rng.shuffle(shuffled)
    return shuffled[: min(count, len(shuffled))]


def baseline_pair_specs(
    concepts: list[Any],
    *,
    sample_count: int,
    seed: int,
) -> list[LabelFreeReadoutPair]:
    if sample_count < 1:
        raise ValueError("sample_count must be at least 1")
    concept_ids = sorted(concept_id(row) for row in concepts)
    category_by_id = {concept_id(row): concept_category(row) for row in concepts}
    focus_ids = focus_pair_ids()
    focus_left_right = {
        (row.left, row.right)
        for row in label_free_pair_specs()
    }
    same_category_pairs = []
    cross_category_pairs = []
    distractor_rng = random.Random(seed + 17)
    for left in concept_ids:
        for right in concept_ids:
            if left == right:
                continue
            distractor = choose_baseline_distractor(
                concepts,
                left=left,
                right=right,
                rng=distractor_rng,
            )
            row = (left, right, distractor)
            if pair_id(left=left, right=right, distractor=distractor) in focus_ids:
                continue
            if (left, right) in focus_left_right:
                continue
            if category_by_id[left] == category_by_id[right]:
                same_category_pairs.append(row)
            else:
                cross_category_pairs.append(row)

    same_count = max(1, sample_count // 4)
    cross_count = sample_count - same_count
    sample_rng = random.Random(seed)
    sampled = [
        *sample_rows(same_category_pairs, count=same_count, rng=sample_rng),
        *sample_rows(cross_category_pairs, count=cross_count, rng=sample_rng),
    ]
    return [
        LabelFreeReadoutPair(
            id=pair_id(left=left, right=right, distractor=distractor),
            left=left,
            right=right,
            kind=(
                "baseline_same_category"
                if category_by_id[left] == category_by_id[right]
                else "baseline_cross_category"
            ),
            distractor=distractor,
        )
        for left, right, distractor in sampled
    ]


def pair_specs_for_set(
    concepts: list[Any],
    *,
    pair_set: str,
    sample_count: int,
    seed: int,
) -> list[LabelFreeReadoutPair]:
    if pair_set not in PAIR_SET_OPTIONS:
        options = ", ".join(PAIR_SET_OPTIONS)
        raise ValueError(f"pair_set must be one of: {options}")
    focus_pairs = label_free_pair_specs()
    baseline_pairs = baseline_pair_specs(
        concepts,
        sample_count=sample_count,
        seed=seed,
    )
    if pair_set == "focus":
        return focus_pairs
    if pair_set == "baseline":
        return baseline_pairs
    return [*focus_pairs, *baseline_pairs]


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
            row.get("patch_alpha", 1.0),
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
        patch_alpha,
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
                "patch_alpha": patch_alpha,
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
            float(row.get("patch_alpha", 1.0)),
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
            row.get("patch_alpha", 1.0),
            row["patch_text_regime"],
        )
        grouped.setdefault(key, {})[str(row["patch_mode"])] = row

    rows = []
    for (
        kind,
        pair,
        injection_layer,
        readout_layer,
        patch_alpha,
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
                "patch_alpha": patch_alpha,
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
            float(row.get("patch_alpha", 1.0)),
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
        for kind in SUMMARY_KINDS:
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


def mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def median(values: list[float]) -> float | None:
    if not values:
        return None
    sorted_values = sorted(values)
    midpoint = len(sorted_values) // 2
    if len(sorted_values) % 2:
        return sorted_values[midpoint]
    return (sorted_values[midpoint - 1] + sorted_values[midpoint]) / 2


def empirical_percentile(value: float, distribution: list[float]) -> float | None:
    if not distribution:
        return None
    return sum(1 for item in distribution if item <= value) / len(distribution)


def transfer_baseline_summaries(
    specificity: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    summaries = []
    comparison_kinds = ("positive", "source_family", "generic_control")
    for patch_text_regime in PATCH_TEXT_REGIMES:
        selected = [
            row for row in specificity if row["patch_text_regime"] == patch_text_regime
        ]
        baseline_rows = [
            row for row in selected if str(row["kind"]).startswith("baseline_")
        ]
        baseline_advantages = [
            float(row["target_advantage_over_best_control"])
            for row in baseline_rows
        ]
        baseline_deltas = [
            float(row["target_mean_target_margin_delta"])
            for row in baseline_rows
        ]
        summaries.append(
            {
                "patch_text_regime": patch_text_regime,
                "kind": "baseline_distribution",
                "count": len(baseline_rows),
                "specific_pass_count": sum(
                    1 for row in baseline_rows if row["specific_target_pass"]
                ),
                "specific_pass_rate": (
                    sum(1 for row in baseline_rows if row["specific_target_pass"])
                    / len(baseline_rows)
                    if baseline_rows
                    else None
                ),
                "mean_target_margin_delta": mean(baseline_deltas),
                "median_target_margin_delta": median(baseline_deltas),
                "mean_advantage_over_best_control": mean(baseline_advantages),
                "median_advantage_over_best_control": median(baseline_advantages),
            }
        )
        for kind in comparison_kinds:
            rows = [row for row in selected if row["kind"] == kind]
            advantages = [
                float(row["target_advantage_over_best_control"])
                for row in rows
            ]
            deltas = [
                float(row["target_mean_target_margin_delta"])
                for row in rows
            ]
            mean_advantage = mean(advantages)
            summaries.append(
                {
                    "patch_text_regime": patch_text_regime,
                    "kind": kind,
                    "count": len(rows),
                    "specific_pass_count": sum(
                        1 for row in rows if row["specific_target_pass"]
                    ),
                    "specific_pass_rate": (
                        sum(1 for row in rows if row["specific_target_pass"])
                        / len(rows)
                        if rows
                        else None
                    ),
                    "mean_target_margin_delta": mean(deltas),
                    "mean_advantage_over_best_control": mean_advantage,
                    "mean_advantage_percentile_vs_baseline": (
                        empirical_percentile(mean_advantage, baseline_advantages)
                        if mean_advantage is not None
                        else None
                    ),
                    "max_advantage_percentile_vs_baseline": (
                        empirical_percentile(max(advantages), baseline_advantages)
                        if advantages
                        else None
                    ),
                }
            )
    return summaries


def dose_response_summaries(
    specificity: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in specificity:
        key = (
            row["patch_text_regime"],
            row["kind"],
            row["injection_layer"],
            row["readout_layer"],
            row.get("patch_alpha", 1.0),
        )
        grouped.setdefault(key, []).append(row)

    summaries = []
    for (
        patch_text_regime,
        kind,
        injection_layer,
        readout_layer,
        patch_alpha,
    ), rows in grouped.items():
        deltas = [
            float(row["target_mean_target_margin_delta"])
            for row in rows
        ]
        advantages = [
            float(row["target_advantage_over_best_control"])
            for row in rows
        ]
        pass_count = sum(1 for row in rows if row["specific_target_pass"])
        summaries.append(
            {
                "patch_text_regime": patch_text_regime,
                "kind": kind,
                "injection_layer": injection_layer,
                "readout_layer": readout_layer,
                "patch_alpha": patch_alpha,
                "count": len(rows),
                "specific_pass_count": pass_count,
                "specific_pass_rate": pass_count / len(rows) if rows else None,
                "mean_target_margin_delta": mean(deltas),
                "median_target_margin_delta": median(deltas),
                "mean_advantage_over_best_control": mean(advantages),
                "median_advantage_over_best_control": median(advantages),
            }
        )
    return sorted(
        summaries,
        key=lambda row: (
            str(row["patch_text_regime"]),
            str(row["kind"]),
            int(row["injection_layer"]),
            int(row["readout_layer"]),
            float(row["patch_alpha"]),
        ),
    )


def public_summary(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "manifest": payload["manifest"],
        "gate_summaries": payload["gate_summaries"],
        "transfer_baseline_summaries": payload.get("transfer_baseline_summaries", []),
        "dose_response_summaries": payload.get("dose_response_summaries", []),
        "specificity_rows": payload["specificity_rows"],
        "aggregate_rows": payload["aggregate_rows"],
    }
