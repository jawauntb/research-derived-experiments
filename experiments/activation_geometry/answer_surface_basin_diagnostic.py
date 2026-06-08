#!/usr/bin/env python3
"""Helpers for answer-surface basin patching diagnostics."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


PROMPT_FRAMES = {
    "dynamics": "Choose the concept most directly linked to stable-state dynamics.",
}
PATCH_TEXT_REGIMES = ("definition", "neutral")
LABEL_REGIMES = ("canonical", "alias", "symbol")
BASIN_SOURCE_SWEEP = (
    ("attractor", "attractor_network", "prototype", "positive"),
    ("prototype", "attractor_network", "attractor", "source_family"),
    ("schema", "attractor_network", "attractor", "source_family"),
    ("conceptual_space", "attractor_network", "prototype", "source_family"),
    ("basin_of_attraction", "attractor_network", "attractor", "source_family"),
)
ALIAS_LABELS = {
    "attractor": "stable-state basin",
    "attractor_network": "recurrent stable-state network",
    "basin_of_attraction": "convergence region",
    "conceptual_space": "geometric meaning space",
    "prototype": "central example pattern",
    "schema": "structured expectation pattern",
}
SYMBOL_LABELS = {
    "attractor": "signal alpha",
    "attractor_network": "signal beta",
    "basin_of_attraction": "signal gamma",
    "conceptual_space": "signal delta",
    "prototype": "signal epsilon",
    "schema": "signal zeta",
}


@dataclass(frozen=True)
class AnswerSurfacePair:
    id: str
    left: str
    right: str
    kind: str
    distractor: str
    prompt_frame: str


def pair_id(*, frame: str, left: str, right: str, distractor: str) -> str:
    return f"{frame}:{left}->{right}/d={distractor}"


def answer_surface_pair_specs() -> list[AnswerSurfacePair]:
    rows = []
    for frame in PROMPT_FRAMES:
        for left, right, distractor, kind in BASIN_SOURCE_SWEEP:
            rows.append(
                AnswerSurfacePair(
                    id=pair_id(
                        frame=frame,
                        left=left,
                        right=right,
                        distractor=distractor,
                    ),
                    left=left,
                    right=right,
                    kind=kind,
                    distractor=distractor,
                    prompt_frame=frame,
                )
            )
    return rows


def serializable_pair_specs(pairs: list[AnswerSurfacePair]) -> list[dict[str, Any]]:
    return [asdict(pair) for pair in pairs]


def prompt_instruction(frame: str) -> str:
    if frame not in PROMPT_FRAMES:
        options = ", ".join(sorted(PROMPT_FRAMES))
        raise ValueError(f"Prompt frame must be one of: {options}")
    return PROMPT_FRAMES[frame]


def concept_label(
    *,
    concept_id: str,
    canonical_label: str,
    label_regime: str,
) -> str:
    if label_regime == "canonical":
        return canonical_label
    if label_regime == "alias":
        return ALIAS_LABELS.get(concept_id, canonical_label)
    if label_regime == "symbol":
        return SYMBOL_LABELS.get(concept_id, f"signal {concept_id.replace('_', '-')}")
    options = ", ".join(LABEL_REGIMES)
    raise ValueError(f"Label regime must be one of: {options}")


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


def calibration_prompt(
    *,
    source_text: str,
    labels_by_role: dict[str, str],
    option_order: tuple[str, str, str],
    prompt_frame: str,
) -> str:
    lines = [
        source_text,
        "",
        prompt_instruction(prompt_frame),
    ]
    for slot, role in zip(("A", "B", "C"), option_order, strict=True):
        lines.append(f"{slot}. {labels_by_role[role]}")
    lines.append("Answer:")
    return "\n".join(lines)


def aggregate_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in rows:
        key = (
            row["role"],
            row["layer"],
            row["kind"],
            row["pair"],
            row["label_regime"],
            row["patch_text_regime"],
            row["patch_mode"],
        )
        grouped.setdefault(key, []).append(row)

    aggregates = []
    for (
        role,
        layer,
        kind,
        pair,
        label_regime,
        patch_text_regime,
        patch_mode,
    ), group in grouped.items():
        deltas = [row["summary"]["target_margin_delta"] for row in group]
        pass_count = sum(1 for value in deltas if value > 0)
        mean_delta = sum(deltas) / len(deltas)
        aggregates.append(
            {
                "role": role,
                "layer": layer,
                "kind": kind,
                "pair": pair,
                "label_regime": label_regime,
                "patch_text_regime": patch_text_regime,
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
            str(row["label_regime"]),
            str(row["patch_text_regime"]),
            str(row["kind"]),
            str(row["pair"]),
            str(row["patch_mode"]),
        ),
    )


def specificity_rows(aggregates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], dict[str, dict[str, Any]]] = {}
    control_modes = ("distractor", "random", "source_noop")
    for row in aggregates:
        key = (
            row["role"],
            row["layer"],
            row["kind"],
            row["pair"],
            row["label_regime"],
            row["patch_text_regime"],
        )
        grouped.setdefault(key, {})[str(row["patch_mode"])] = row

    rows = []
    for (
        role,
        layer,
        kind,
        pair,
        label_regime,
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
                "role": role,
                "layer": layer,
                "kind": kind,
                "pair": pair,
                "label_regime": label_regime,
                "patch_text_regime": patch_text_regime,
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
            str(row["label_regime"]),
            str(row["patch_text_regime"]),
            str(row["kind"]),
            str(row["pair"]),
        ),
    )


def _mean_or_none(rows: list[dict[str, Any]], key: str) -> float | None:
    if not rows:
        return None
    return sum(float(row[key]) for row in rows) / len(rows)


def gate_summaries(specificity: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries = []
    for role in ("primary", "control"):
        for label_regime in LABEL_REGIMES:
            for patch_text_regime in PATCH_TEXT_REGIMES:
                selected = [
                    row
                    for row in specificity
                    if row["role"] == role
                    and row["label_regime"] == label_regime
                    and row["patch_text_regime"] == patch_text_regime
                ]
                positives = [row for row in selected if row["kind"] == "positive"]
                family_rows = [row for row in selected if row["kind"] == "source_family"]
                summaries.append(
                    {
                        "role": role,
                        "label_regime": label_regime,
                        "patch_text_regime": patch_text_regime,
                        "positive_specific_pass_count": sum(
                            1 for row in positives if row["specific_target_pass"]
                        ),
                        "positive_total": len(positives),
                        "source_family_specific_pass_count": sum(
                            1 for row in family_rows if row["specific_target_pass"]
                        ),
                        "source_family_total": len(family_rows),
                        "all_specific_pass_count": sum(
                            1 for row in selected if row["specific_target_pass"]
                        ),
                        "all_total": len(selected),
                        "mean_target_margin_delta": _mean_or_none(
                            selected,
                            "target_mean_target_margin_delta",
                        ),
                        "mean_advantage_over_best_control": _mean_or_none(
                            selected,
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
