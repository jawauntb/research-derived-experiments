#!/usr/bin/env python3
"""Pure-Python helpers for learned behavior-aligned direction pilots."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


DIRECTION_MODES = (
    "target_learned",
    "source_learned",
    "distractor_learned",
    "target_resid_sd",
    "target_resid_control",
    "target_resid_all",
    "target_penalty_hard_1_0",
    "target_penalty_hard_2_0",
    "target_penalty_control_mean_1_0",
    "target_penalty_controls_0_5",
    "target_penalty_controls_1_0",
    "target_penalty_controls_2_0",
    "target_binary_controls_0_5",
    "target_binary_controls_1_0",
    "target_binary_controls_2_0",
    "target_binary_controls_4_0",
    "target_binary_pc1_resid",
    "target_binary_pc3_resid",
    "target_binary_pc1_whiten",
    "target_binary_pc3_whiten",
    "target_binary_strict_opt_8",
    "target_binary_strict_opt_16",
    "target_binary_readout_span_opt_8",
    "target_binary_feature_mask_opt_8",
    "target_binary_state_gate_opt_8",
    "target_binary_relation_state_gate_opt_8",
    "target_binary_multiclass_state_gate_opt_8",
    "target_binary_relation_multiclass_state_gate_opt_8",
    "target_binary_relation_multiclass_holdout_source_opt_8",
    "target_binary_relation_multiclass_holdout_target_opt_8",
    "target_binary_relation_multiclass_holdout_overlap_opt_8",
    "target_binary_relation_pair_multiclass_state_gate_opt_8",
    "target_binary_positive_family_opt_8",
    "caa_target_contrast",
    "caa_target_minus_source",
    "caa_target_minus_distractor",
    "random_same_norm",
)
OBJECTIVE_ROLES = ("target", "source", "distractor")
PROMPT_FRAMES = (
    "source_passage",
    "latent_choice",
    "source_short_answer",
    "latent_short_answer",
)
SCORING_SURFACES = (
    "option_token",
    "full_label",
    "binary_relation",
    "generation_match",
    "generation_readout",
)
SINGLE_LABEL_SCORING_REGIMES = ("canonical", "alias", "alias_0", "alias_1", "alias_2")
LABEL_SCORING_REGIMES = SINGLE_LABEL_SCORING_REGIMES


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


def relation_control_class_from_name(control_name: str) -> str | None:
    """Extract the stratified control class encoded in a relation-control name."""
    prefix = "relation_control:"
    if not control_name.startswith(prefix):
        return None
    parts = control_name.split(":")
    if len(parts) < 2 or not parts[1]:
        return None
    return parts[1]


def relation_control_pair_from_name(control_name: str) -> str | None:
    """Extract the relation pair encoded in a relation-control name."""
    prefix = "relation_control:"
    if not control_name.startswith(prefix):
        return None
    parts = control_name.split(":")
    if len(parts) < 3 or not parts[2]:
        return None
    return parts[2]


def relation_control_group_name(
    control_name: str,
    *,
    relation_grouping: str = "class",
) -> str:
    """Return the prototype group used for relation-control gate classes."""
    if not control_name.startswith("relation_control:"):
        if control_name.startswith("random_null_"):
            return "random_null"
        return control_name
    if relation_grouping == "class":
        control_class = relation_control_class_from_name(control_name)
        if control_class is not None:
            return f"relation_control:{control_class}"
    elif relation_grouping == "pair":
        control_class = relation_control_class_from_name(control_name)
        control_pair = relation_control_pair_from_name(control_name)
        if control_class is not None and control_pair is not None:
            return f"relation_control:{control_class}:{control_pair}"
    else:
        raise ValueError(f"Unknown relation control grouping: {relation_grouping}")
    return control_name


def filter_relation_control_prompts(
    prompts_by_regime: dict[str, list[tuple[str, str]]],
    *,
    include_classes: tuple[str, ...] = (),
    exclude_classes: tuple[str, ...] = (),
) -> dict[str, list[tuple[str, str]]]:
    """Filter relation-control prompts by their encoded stratified class."""
    include_set = set(include_classes)
    exclude_set = set(exclude_classes)
    filtered: dict[str, list[tuple[str, str]]] = {}
    for regime, prompts in prompts_by_regime.items():
        kept = []
        for control_name, prompt in prompts:
            control_class = relation_control_class_from_name(control_name)
            if control_class is None:
                continue
            if include_set and control_class not in include_set:
                continue
            if control_class in exclude_set:
                continue
            kept.append((control_name, prompt))
        filtered[regime] = kept
    return filtered


def parse_values(value: str, *, allowed: tuple[str, ...], name: str) -> list[str]:
    values = parse_csv(value)
    invalid = sorted(set(values) - set(allowed))
    if invalid:
        options = ", ".join(allowed)
        raise ValueError(f"{name} must be chosen from: {options}")
    return values


def label_scoring_regime_parts(
    regime: str,
    *,
    allow_groups: bool,
) -> list[str]:
    parts = [part.strip() for part in regime.split("+") if part.strip()]
    if not parts:
        raise ValueError("Label scoring regime cannot be empty")
    if len(parts) > 1 and not allow_groups:
        raise ValueError(f"Grouped label scoring regime is not allowed here: {regime}")
    invalid = sorted(set(parts) - set(SINGLE_LABEL_SCORING_REGIMES))
    if invalid:
        options = ", ".join(SINGLE_LABEL_SCORING_REGIMES)
        raise ValueError(f"Label scoring regime parts must be chosen from: {options}")
    return parts


def parse_label_scoring_regimes(
    value: str,
    *,
    name: str,
    allow_groups: bool = False,
) -> list[str]:
    regimes = parse_csv(value)
    for regime in regimes:
        label_scoring_regime_parts(regime, allow_groups=allow_groups)
    return regimes


def target_margin(scores: dict[str, float]) -> float:
    return scores["target"] - ((scores["source"] + scores["distractor"]) / 2)


def normalize_generated_text(text: str) -> str:
    normalized = text.lower().replace("_", " ")
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def generated_text_matches_label(*, generated_text: str, label: str) -> bool:
    text = normalize_generated_text(generated_text)
    normalized_label = normalize_generated_text(label)
    if not text or not normalized_label:
        return False
    return re.search(rf"(?<!\w){re.escape(normalized_label)}(?!\w)", text) is not None


def generation_match_scores(
    *,
    generated_text: str,
    labels_by_role: dict[str, list[str]],
) -> dict[str, float]:
    return {
        role: 1.0
        if any(
            generated_text_matches_label(generated_text=generated_text, label=label)
            for label in labels
        )
        else 0.0
        for role, labels in labels_by_role.items()
    }


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


def binary_specificity_controls(scores: dict[str, Any]) -> dict[str, float]:
    controls = {
        str(name): float(value)
        for name, value in scores.get("binary_control_margins", {}).items()
    }
    carrier_margins = scores.get("binary_carrier_margins", {})
    if "always_false" in carrier_margins:
        controls["always_false"] = float(carrier_margins["always_false"])
    return controls


def summarize_binary_specificity(
    *,
    baseline_scores: dict[str, Any],
    steered_scores: dict[str, Any],
) -> dict[str, Any] | None:
    baseline_controls = binary_specificity_controls(baseline_scores)
    steered_controls = binary_specificity_controls(steered_scores)
    shared_controls = sorted(set(baseline_controls) & set(steered_controls))
    if not shared_controls:
        return None

    control_deltas = {
        control: steered_controls[control] - baseline_controls[control]
        for control in shared_controls
    }
    target_delta = float(steered_scores["target"]) - float(baseline_scores["target"])
    max_control_delta_name = max(control_deltas, key=control_deltas.__getitem__)
    max_control_steered_name = max(
        shared_controls,
        key=lambda control: steered_controls[control],
    )
    always_false_steered = steered_controls.get("always_false")
    return {
        "target_delta": target_delta,
        "target_steered_margin": float(steered_scores["target"]),
        "max_control_delta_name": max_control_delta_name,
        "max_control_delta": control_deltas[max_control_delta_name],
        "max_control_steered_name": max_control_steered_name,
        "max_control_steered_margin": steered_controls[max_control_steered_name],
        "target_delta_over_max_control_delta": (
            target_delta - control_deltas[max_control_delta_name]
        ),
        "target_steered_over_max_control_steered": (
            float(steered_scores["target"])
            - steered_controls[max_control_steered_name]
        ),
        "always_false_steered_margin": always_false_steered,
        "control_deltas": control_deltas,
        "steered_control_margins": {
            control: steered_controls[control] for control in shared_controls
        },
    }


def row_passes_behavior_gate(row: dict[str, Any]) -> bool:
    if float(row["summary"]["target_margin_delta"]) <= 0:
        return False
    scoring_surface = str(row.get("scoring_surface", "option_token"))
    if scoring_surface == "generation_match":
        steered_scores = row.get("scores", {}).get("steered", {})
        return float(steered_scores.get("target", 0.0)) > 0
    if scoring_surface == "generation_readout":
        steered_scores = row.get("scores", {}).get("steered", {})
        return (
            float(row["summary"]["target_logprob_delta"]) > 0
            and str(steered_scores.get("best_role", "")) == "target"
        )
    if scoring_surface == "binary_relation":
        scores = row.get("scores", {})
        baseline_scores = scores.get("baseline", {})
        steered_scores = scores.get("steered", {})
        basic_pass = (
            float(row["summary"]["target_logprob_delta"]) > 0
            and float(steered_scores.get("target", 0.0)) > 0
        )
        binary_specificity = summarize_binary_specificity(
            baseline_scores=baseline_scores,
            steered_scores=steered_scores,
        )
        if binary_specificity is None:
            return basic_pass
        always_false_steered = binary_specificity.get("always_false_steered_margin")
        always_false_pass = (
            always_false_steered is None or float(always_false_steered) <= 0.0
        )
        return (
            basic_pass
            and float(binary_specificity["target_delta_over_max_control_delta"]) > 0
            and float(binary_specificity["target_steered_over_max_control_steered"]) > 0
            and always_false_pass
        )
    return True


def aggregate_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in rows:
        key = (
            row.get("scoring_surface", "option_token"),
            row.get("prompt_frame", "source_passage"),
            row.get("objective_label_scoring_regime", "canonical"),
            row.get("eval_label_scoring_regime", "canonical"),
            row["role"],
            row["layer"],
            row["kind"],
            row.get("control_class", ""),
            row["pair"],
            row["direction_mode"],
            row["scale"],
        )
        grouped.setdefault(key, []).append(row)

    aggregates = []
    for (
        scoring_surface,
        prompt_frame,
        objective_label_scoring_regime,
        eval_label_scoring_regime,
        role,
        layer,
        kind,
        control_class,
        pair,
        direction_mode,
        scale,
    ), group in grouped.items():
        deltas = [row["summary"]["target_margin_delta"] for row in group]
        target_logprob_deltas = [row["summary"]["target_logprob_delta"] for row in group]
        binary_specificity_rows = [
            summary
            for row in group
            if (
                summary := summarize_binary_specificity(
                    baseline_scores=row.get("scores", {}).get("baseline", {}),
                    steered_scores=row.get("scores", {}).get("steered", {}),
                )
            )
            is not None
        ]
        pass_count = sum(1 for row in group if row_passes_behavior_gate(row))
        mean_delta = sum(deltas) / len(deltas)
        robust_pass_threshold = min(2, len(group))
        aggregate = {
            "scoring_surface": scoring_surface,
            "prompt_frame": prompt_frame,
            "objective_label_scoring_regime": objective_label_scoring_regime,
            "eval_label_scoring_regime": eval_label_scoring_regime,
            "role": role,
            "layer": layer,
            "kind": kind,
            "control_class": control_class,
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
            "score_surface_pass_count": pass_count,
            "score_surface_total": len(group),
            "robust_pass_threshold": robust_pass_threshold,
            "robust_pass": mean_delta > 0
            and pass_count >= robust_pass_threshold,
        }
        if binary_specificity_rows:
            aggregate.update(
                {
                    "mean_binary_target_delta": (
                        sum(float(row["target_delta"]) for row in binary_specificity_rows)
                        / len(binary_specificity_rows)
                    ),
                    "mean_binary_target_delta_over_max_control_delta": (
                        sum(
                            float(row["target_delta_over_max_control_delta"])
                            for row in binary_specificity_rows
                        )
                        / len(binary_specificity_rows)
                    ),
                    "mean_binary_target_steered_over_max_control_steered": (
                        sum(
                            float(row["target_steered_over_max_control_steered"])
                            for row in binary_specificity_rows
                        )
                        / len(binary_specificity_rows)
                    ),
                    "mean_binary_always_false_steered_margin": (
                        sum(
                            float(row.get("always_false_steered_margin") or 0.0)
                            for row in binary_specificity_rows
                        )
                        / len(binary_specificity_rows)
                    ),
                }
            )
        aggregates.append(aggregate)
    return sorted(
        aggregates,
        key=lambda row: (
            str(row.get("scoring_surface", "option_token")),
            str(row.get("prompt_frame", "source_passage")),
            str(row.get("objective_label_scoring_regime", "canonical")),
            str(row.get("eval_label_scoring_regime", "canonical")),
            str(row["role"]),
            str(row["kind"]),
            str(row.get("control_class", "")),
            str(row["pair"]),
            float(row["scale"]),
            str(row["direction_mode"]),
        ),
    )


def control_class_label(row: dict[str, Any]) -> str:
    control_class = str(row.get("control_class", "")).strip()
    return control_class if control_class else "unclassified"


def control_pass_counts_by_class(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        control_class: sum(
            1
            for row in rows
            if control_class_label(row) == control_class and row["robust_pass"]
        )
        for control_class in sorted({control_class_label(row) for row in rows})
    }


def control_totals_by_class(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        control_class: sum(
            1 for row in rows if control_class_label(row) == control_class
        )
        for control_class in sorted({control_class_label(row) for row in rows})
    }


def gate_summaries(aggregates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries = []
    scoring_surfaces = sorted(
        {str(row.get("scoring_surface", "option_token")) for row in aggregates}
        or {"option_token"}
    )
    prompt_frames = sorted(
        {str(row.get("prompt_frame", "source_passage")) for row in aggregates}
        or {"source_passage"}
    )
    objective_label_scoring_regimes = sorted(
        {
            str(row.get("objective_label_scoring_regime", "canonical"))
            for row in aggregates
        }
        or {"canonical"}
    )
    eval_label_scoring_regimes = sorted(
        {str(row.get("eval_label_scoring_regime", "canonical")) for row in aggregates}
        or {"canonical"}
    )
    for scoring_surface in scoring_surfaces:
        surface_rows = [
            row
            for row in aggregates
            if str(row.get("scoring_surface", "option_token")) == scoring_surface
        ]
        for prompt_frame in prompt_frames:
            frame_rows = [
                row
                for row in surface_rows
                if str(row.get("prompt_frame", "source_passage")) == prompt_frame
            ]
            for objective_label_scoring_regime in objective_label_scoring_regimes:
                objective_rows = [
                    row
                    for row in frame_rows
                    if str(row.get("objective_label_scoring_regime", "canonical"))
                    == objective_label_scoring_regime
                ]
                for eval_label_scoring_regime in eval_label_scoring_regimes:
                    eval_rows = [
                        row
                        for row in objective_rows
                        if str(row.get("eval_label_scoring_regime", "canonical"))
                        == eval_label_scoring_regime
                    ]
                    for scale in sorted({float(row["scale"]) for row in eval_rows}):
                        for mode in DIRECTION_MODES:
                            selected = [
                                row
                                for row in eval_rows
                                if float(row["scale"]) == scale
                                and row["direction_mode"] == mode
                            ]
                            primary_positive = [
                                row
                                for row in selected
                                if row["role"] == "primary"
                                and row["kind"] == "positive"
                            ]
                            backup_positive = [
                                row
                                for row in selected
                                if row["role"] == "backup"
                                and row["kind"] == "positive"
                            ]
                            primary_controls = [
                                row
                                for row in selected
                                if row["role"] == "primary"
                                and row["kind"] == "control"
                            ]
                            control_layer_positive = [
                                row
                                for row in selected
                                if row["role"] == "control"
                                and row["kind"] == "positive"
                            ]
                            primary_control_passes_by_class = (
                                control_pass_counts_by_class(primary_controls)
                            )
                            primary_control_totals_by_class = control_totals_by_class(
                                primary_controls
                            )
                            summaries.append(
                                {
                                    "scoring_surface": scoring_surface,
                                    "prompt_frame": prompt_frame,
                                    "objective_label_scoring_regime": (
                                        objective_label_scoring_regime
                                    ),
                                    "eval_label_scoring_regime": (
                                        eval_label_scoring_regime
                                    ),
                                    "scale": scale,
                                    "direction_mode": mode,
                                    "primary_positive_pass_count": sum(
                                        1
                                        for row in primary_positive
                                        if row["robust_pass"]
                                    ),
                                    "primary_positive_total": len(primary_positive),
                                    "backup_positive_pass_count": sum(
                                        1
                                        for row in backup_positive
                                        if row["robust_pass"]
                                    ),
                                    "backup_positive_total": len(backup_positive),
                                    "primary_valence_control_pass_count": sum(
                                        1
                                        for row in primary_controls
                                        if row["robust_pass"]
                                    ),
                                    "primary_valence_control_total": len(
                                        primary_controls
                                    ),
                                    "primary_control_pass_count_by_class": (
                                        primary_control_passes_by_class
                                    ),
                                    "primary_control_total_by_class": (
                                        primary_control_totals_by_class
                                    ),
                                    "control_layer_positive_pass_count": sum(
                                        1
                                        for row in control_layer_positive
                                        if row["robust_pass"]
                                    ),
                                    "control_layer_positive_total": len(
                                        control_layer_positive
                                    ),
                                }
                            )
    return summaries


def alignment_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in rows:
        key = (
            row.get("scoring_surface", "option_token"),
            row.get("prompt_frame", "source_passage"),
            row.get("objective_label_scoring_regime", "canonical"),
            row.get("eval_label_scoring_regime", "canonical"),
            row["role"],
            row["layer"],
            row["kind"],
            row["pair"],
        )
        grouped.setdefault(key, []).append(row)

    summaries = []
    for (
        scoring_surface,
        prompt_frame,
        objective_label_scoring_regime,
        eval_label_scoring_regime,
        role,
        layer,
        kind,
        pair,
    ), group in grouped.items():
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
            "scoring_surface": scoring_surface,
            "prompt_frame": prompt_frame,
            "objective_label_scoring_regime": objective_label_scoring_regime,
            "eval_label_scoring_regime": eval_label_scoring_regime,
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
    summary = {
        "manifest": payload["manifest"],
        "gate_summaries": payload["gate_summaries"],
        "alignment_summary": payload["alignment_summary"],
        "aggregate_rows": payload["aggregate_rows"],
    }
    if "binary_gradient_geometry" in payload:
        summary["binary_gradient_geometry"] = payload["binary_gradient_geometry"]
    return summary


def write_payload(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
