#!/usr/bin/env python3
"""Helpers for label-free behavior-level patching gates."""

from __future__ import annotations

from typing import Any


PATCH_TEXT_REGIMES = (
    "definition",
    "definition_without_label",
    "neutral",
    "label_only",
    "blank_carrier",
    "shuffled_label",
)
PATCH_VECTOR_SURFACES = ("hidden_state", "hook_output")
PATCH_MODES = ("target", "distractor", "random", "source_noop")
OPTION_ROLES = ("source", "target", "distractor")
PROMPT_FRAMES = ("source_passage", "latent_choice")
SCORING_SURFACES = ("option_token", "full_label")
LABEL_SCORING_REGIMES = ("canonical", "alias")
DEFAULT_OPTION_ORDERS = (
    ("source", "target", "distractor"),
    ("target", "distractor", "source"),
    ("distractor", "source", "target"),
)


def neutral_carrier_text(*, label: str) -> str:
    return f"Concept label: {label}."


def label_only_text(*, label: str) -> str:
    return label


def blank_carrier_text() -> str:
    return "Concept label: [omitted]."


def definition_without_label_text(*, definition_text: str, label: str) -> str:
    stripped = definition_text.strip()
    prefix = f"{label}:"
    if stripped.lower().startswith(prefix.lower()):
        return stripped[len(prefix) :].strip()
    return stripped


def source_text_for_regime(
    *,
    definition_text: str,
    label: str,
    patch_text_regime: str,
    shuffled_label: str | None = None,
) -> str:
    if patch_text_regime == "definition":
        return definition_text
    if patch_text_regime == "definition_without_label":
        return definition_without_label_text(
            definition_text=definition_text,
            label=label,
        )
    if patch_text_regime == "neutral":
        return neutral_carrier_text(label=label)
    if patch_text_regime == "label_only":
        return label_only_text(label=label)
    if patch_text_regime == "blank_carrier":
        return blank_carrier_text()
    if patch_text_regime == "shuffled_label":
        if shuffled_label is None:
            raise ValueError("Shuffled-label regime requires shuffled_label")
        return neutral_carrier_text(label=shuffled_label)
    options = ", ".join(PATCH_TEXT_REGIMES)
    raise ValueError(f"Patch text regime must be one of: {options}")


def behavior_prompt(
    *,
    source_text: str,
    labels_by_role: dict[str, str],
    option_order: tuple[str, str, str],
    prompt_frame: str = "source_passage",
) -> str:
    if prompt_frame == "source_passage":
        lines = [
            "Read the passage and choose the concept it points to. Answer with only the letter.",
            "",
            f"Passage: {source_text}",
            "",
            "Options:",
        ]
    elif prompt_frame == "latent_choice":
        lines = [
            "Choose the concept most likely indicated by the model's current internal state. Answer with only the letter.",
            "",
            "Options:",
        ]
    else:
        options = ", ".join(PROMPT_FRAMES)
        raise ValueError(f"Prompt frame must be one of: {options}")
    for slot, role in zip(("A", "B", "C"), option_order, strict=True):
        lines.append(f"{slot}. {labels_by_role[role]}")
    lines.append("")
    lines.append("Answer:")
    return "\n".join(lines)


def full_label_prompt(
    *,
    source_text: str,
    prompt_frame: str = "source_passage",
) -> str:
    if prompt_frame == "source_passage":
        return "\n".join(
            [
                "Read the passage and name the concept it points to.",
                "",
                f"Passage: {source_text}",
                "",
                "Concept:",
            ]
        )
    if prompt_frame == "latent_choice":
        return "The concept most likely indicated by the model's current internal state is"
    options = ", ".join(PROMPT_FRAMES)
    raise ValueError(f"Prompt frame must be one of: {options}")


def target_margin(scores: dict[str, float]) -> float:
    return scores["target"] - ((scores["source"] + scores["distractor"]) / 2)


def summarize_behavior_delta(
    *,
    baseline_scores: dict[str, float],
    patched_scores: dict[str, float],
) -> dict[str, float]:
    baseline_margin = target_margin(baseline_scores)
    patched_margin = target_margin(patched_scores)
    return {
        "baseline_target_margin": baseline_margin,
        "patched_target_margin": patched_margin,
        "target_margin_delta": patched_margin - baseline_margin,
        "target_logprob_delta": patched_scores["target"] - baseline_scores["target"],
        "source_logprob_delta": patched_scores["source"] - baseline_scores["source"],
        "distractor_logprob_delta": (
            patched_scores["distractor"] - baseline_scores["distractor"]
        ),
        "target_minus_source_delta": (
            (patched_scores["target"] - patched_scores["source"])
            - (baseline_scores["target"] - baseline_scores["source"])
        ),
        "target_minus_distractor_delta": (
            (patched_scores["target"] - patched_scores["distractor"])
            - (baseline_scores["target"] - baseline_scores["distractor"])
        ),
    }


def aggregate_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in rows:
        key = (
            row["kind"],
            row["pair"],
            row.get("prompt_frame", "source_passage"),
            row.get("scoring_surface", "option_token"),
            row.get("label_scoring_regime", "canonical"),
            row["injection_layer"],
            row.get("patch_alpha", 1.0),
            row.get("patch_vector_surface", "hook_output"),
            row["patch_text_regime"],
            row["patch_mode"],
        )
        grouped.setdefault(key, []).append(row)

    aggregates = []
    for (
        kind,
        pair,
        prompt_frame,
        scoring_surface,
        label_scoring_regime,
        injection_layer,
        patch_alpha,
        patch_vector_surface,
        patch_text_regime,
        patch_mode,
    ), group in grouped.items():
        deltas = [float(row["summary"]["target_margin_delta"]) for row in group]
        target_logprob_deltas = [
            float(row["summary"]["target_logprob_delta"]) for row in group
        ]
        pass_count = sum(1 for value in deltas if value > 0)
        mean_delta = sum(deltas) / len(deltas)
        robust_pass_threshold = min(2, len(group))
        aggregates.append(
            {
                "kind": kind,
                "pair": pair,
                "prompt_frame": prompt_frame,
                "scoring_surface": scoring_surface,
                "label_scoring_regime": label_scoring_regime,
                "injection_layer": injection_layer,
                "patch_alpha": patch_alpha,
                "patch_vector_surface": patch_vector_surface,
                "patch_text_regime": patch_text_regime,
                "patch_mode": patch_mode,
                "mean_target_margin_delta": mean_delta,
                "min_target_margin_delta": min(deltas),
                "max_target_margin_delta": max(deltas),
                "mean_target_logprob_delta": (
                    sum(target_logprob_deltas) / len(target_logprob_deltas)
                ),
                "score_surface_pass_count": pass_count,
                "score_surface_total": len(group),
                "robust_pass_threshold": robust_pass_threshold,
                "option_order_pass_count": pass_count,
                "option_order_total": len(group),
                "robust_pass": mean_delta > 0
                and pass_count >= robust_pass_threshold,
            }
        )
    return sorted(
        aggregates,
        key=lambda row: (
            str(row["patch_vector_surface"]),
            str(row["patch_text_regime"]),
            str(row["kind"]),
            str(row["pair"]),
            str(row.get("prompt_frame", "source_passage")),
            str(row.get("scoring_surface", "option_token")),
            str(row.get("label_scoring_regime", "canonical")),
            int(row["injection_layer"]),
            float(row["patch_alpha"]),
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
            row.get("prompt_frame", "source_passage"),
            row.get("scoring_surface", "option_token"),
            row.get("label_scoring_regime", "canonical"),
            row["injection_layer"],
            row.get("patch_alpha", 1.0),
            row.get("patch_vector_surface", "hook_output"),
            row["patch_text_regime"],
        )
        grouped.setdefault(key, {})[str(row["patch_mode"])] = row

    rows = []
    for (
        kind,
        pair,
        prompt_frame,
        scoring_surface,
        label_scoring_regime,
        injection_layer,
        patch_alpha,
        patch_vector_surface,
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
                "prompt_frame": prompt_frame,
                "scoring_surface": scoring_surface,
                "label_scoring_regime": label_scoring_regime,
                "injection_layer": injection_layer,
                "patch_alpha": patch_alpha,
                "patch_vector_surface": patch_vector_surface,
                "patch_text_regime": patch_text_regime,
                "target_mean_target_margin_delta": target[
                    "mean_target_margin_delta"
                ],
                "target_mean_target_logprob_delta": target[
                    "mean_target_logprob_delta"
                ],
                "target_option_order_pass_count": target[
                    "option_order_pass_count"
                ],
                "target_option_order_total": target["option_order_total"],
                "target_score_surface_pass_count": target[
                    "score_surface_pass_count"
                ],
                "target_score_surface_total": target["score_surface_total"],
                "target_robust_pass_threshold": target[
                    "robust_pass_threshold"
                ],
                "target_robust_pass": target["robust_pass"],
                "best_control_mode": best_control_mode,
                "best_control_mean_target_margin_delta": best_control_delta,
                "target_advantage_over_best_control": target_advantage,
                "specific_target_pass": target["robust_pass"]
                and target_advantage > 0,
            }
        )
    return sorted(
        rows,
        key=lambda row: (
            str(row["patch_vector_surface"]),
            str(row["patch_text_regime"]),
            str(row["kind"]),
            str(row["pair"]),
            str(row.get("prompt_frame", "source_passage")),
            str(row.get("scoring_surface", "option_token")),
            str(row.get("label_scoring_regime", "canonical")),
            int(row["injection_layer"]),
            float(row["patch_alpha"]),
        ),
    )


def _mean_or_none(rows: list[dict[str, Any]], key: str) -> float | None:
    if not rows:
        return None
    return sum(float(row[key]) for row in rows) / len(rows)


def gate_summaries(specificity: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries = []
    surfaces = sorted(
        {str(row.get("patch_vector_surface", "hook_output")) for row in specificity}
        or {"hook_output"}
    )
    prompt_frames = sorted(
        {str(row.get("prompt_frame", "source_passage")) for row in specificity}
        or {"source_passage"}
    )
    scoring_surfaces = sorted(
        {str(row.get("scoring_surface", "option_token")) for row in specificity}
        or {"option_token"}
    )
    label_scoring_regimes = sorted(
        {str(row.get("label_scoring_regime", "canonical")) for row in specificity}
        or {"canonical"}
    )
    layers = sorted({int(row["injection_layer"]) for row in specificity})
    alphas = sorted({float(row.get("patch_alpha", 1.0)) for row in specificity})
    for patch_vector_surface in surfaces:
        surface_rows = [
            row
            for row in specificity
            if str(row.get("patch_vector_surface", "hook_output"))
            == patch_vector_surface
        ]
        for prompt_frame in prompt_frames:
            frame_rows = [
                row
                for row in surface_rows
                if str(row.get("prompt_frame", "source_passage")) == prompt_frame
            ]
            for scoring_surface in scoring_surfaces:
                score_rows = [
                    row
                    for row in frame_rows
                    if str(row.get("scoring_surface", "option_token"))
                    == scoring_surface
                ]
                for label_scoring_regime in label_scoring_regimes:
                    label_rows = [
                        row
                        for row in score_rows
                        if str(row.get("label_scoring_regime", "canonical"))
                        == label_scoring_regime
                    ]
                    for patch_text_regime in PATCH_TEXT_REGIMES:
                        regime_rows = [
                            row
                            for row in label_rows
                            if row["patch_text_regime"] == patch_text_regime
                        ]
                        for injection_layer in layers:
                            layer_rows = [
                                row
                                for row in regime_rows
                                if int(row["injection_layer"]) == injection_layer
                            ]
                            for patch_alpha in alphas:
                                rows = [
                                    row
                                    for row in layer_rows
                                    if float(row.get("patch_alpha", 1.0))
                                    == patch_alpha
                                ]
                                summaries.append(
                                    {
                                        "patch_vector_surface": patch_vector_surface,
                                        "prompt_frame": prompt_frame,
                                        "scoring_surface": scoring_surface,
                                        "label_scoring_regime": label_scoring_regime,
                                        "patch_text_regime": patch_text_regime,
                                        "injection_layer": injection_layer,
                                        "patch_alpha": patch_alpha,
                                        "specific_pass_count": sum(
                                            1
                                            for row in rows
                                            if row["specific_target_pass"]
                                        ),
                                        "total": len(rows),
                                        "mean_target_margin_delta": _mean_or_none(
                                            rows,
                                            "target_mean_target_margin_delta",
                                        ),
                                        "mean_advantage_over_best_control": (
                                            _mean_or_none(
                                                rows,
                                                "target_advantage_over_best_control",
                                            )
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
