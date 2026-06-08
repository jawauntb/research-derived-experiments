#!/usr/bin/env python3
"""Helpers for focused attractor-pocket patching diagnostics."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


PROMPT_FRAMES = {
    "closest": "Choose the closest related concept.",
    "dynamics": "Choose the concept most directly linked to stable-state dynamics.",
}
ATTRACTOR_DISTRACTORS = (
    "prototype",
    "schema",
    "conceptual_space",
    "representation_manifold",
)
ATTRACTOR_TARGET_CONTROLS = (
    ("attractor", "prototype", "attractor_network"),
    ("attractor", "schema", "attractor_network"),
)
ATTRACTOR_SOURCE_CONTROLS = (
    ("prototype", "attractor_network", "attractor"),
    ("schema", "attractor_network", "attractor"),
)
ATTRACTOR_KINDS = (
    "positive",
    "target_near_control",
    "source_near_control",
)


@dataclass(frozen=True)
class AttractorPocketPair:
    id: str
    left: str
    right: str
    kind: str
    distractor: str
    prompt_frame: str


def pair_id(*, frame: str, left: str, right: str, distractor: str) -> str:
    return f"{frame}:{left}->{right}/d={distractor}"


def attractor_pair_specs() -> list[AttractorPocketPair]:
    rows = []
    for frame in PROMPT_FRAMES:
        for distractor in ATTRACTOR_DISTRACTORS:
            rows.append(
                AttractorPocketPair(
                    id=pair_id(
                        frame=frame,
                        left="attractor",
                        right="attractor_network",
                        distractor=distractor,
                    ),
                    left="attractor",
                    right="attractor_network",
                    kind="positive",
                    distractor=distractor,
                    prompt_frame=frame,
                )
            )
        for left, right, distractor in ATTRACTOR_TARGET_CONTROLS:
            rows.append(
                AttractorPocketPair(
                    id=pair_id(
                        frame=frame,
                        left=left,
                        right=right,
                        distractor=distractor,
                    ),
                    left=left,
                    right=right,
                    kind="target_near_control",
                    distractor=distractor,
                    prompt_frame=frame,
                )
            )
        for left, right, distractor in ATTRACTOR_SOURCE_CONTROLS:
            rows.append(
                AttractorPocketPair(
                    id=pair_id(
                        frame=frame,
                        left=left,
                        right=right,
                        distractor=distractor,
                    ),
                    left=left,
                    right=right,
                    kind="source_near_control",
                    distractor=distractor,
                    prompt_frame=frame,
                )
            )
    return rows


def serializable_pair_specs(pairs: list[AttractorPocketPair]) -> list[dict[str, Any]]:
    return [asdict(pair) for pair in pairs]


def prompt_instruction(frame: str) -> str:
    if frame not in PROMPT_FRAMES:
        options = ", ".join(sorted(PROMPT_FRAMES))
        raise ValueError(f"Prompt frame must be one of: {options}")
    return PROMPT_FRAMES[frame]


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


def _mean_or_none(rows: list[dict[str, Any]], key: str) -> float | None:
    if not rows:
        return None
    return sum(float(row[key]) for row in rows) / len(rows)


def attractor_gate_summaries(specificity: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Summarize the focused attractor-pocket acceptance gate by layer role."""

    summaries = []
    for role in ("primary", "backup", "control"):
        selected = [row for row in specificity if row["role"] == role]
        positives = [row for row in selected if row["kind"] == "positive"]
        target_controls = [
            row for row in selected if row["kind"] == "target_near_control"
        ]
        source_controls = [
            row for row in selected if row["kind"] == "source_near_control"
        ]
        positive_specific_pass_count = sum(
            1 for row in positives if row["specific_target_pass"]
        )
        target_control_pass_count = sum(
            1 for row in target_controls if row["specific_target_pass"]
        )
        source_control_pass_count = sum(
            1 for row in source_controls if row["specific_target_pass"]
        )
        near_control_pass_count = target_control_pass_count + source_control_pass_count
        summaries.append(
            {
                "role": role,
                "positive_specific_pass_count": positive_specific_pass_count,
                "positive_total": len(positives),
                "target_near_control_specific_pass_count": target_control_pass_count,
                "target_near_control_total": len(target_controls),
                "source_near_control_specific_pass_count": source_control_pass_count,
                "source_near_control_total": len(source_controls),
                "near_control_specific_pass_count": near_control_pass_count,
                "near_control_total": len(target_controls) + len(source_controls),
                "positive_mean_target_margin_delta": _mean_or_none(
                    positives,
                    "target_mean_target_margin_delta",
                ),
                "positive_mean_advantage_over_best_control": _mean_or_none(
                    positives,
                    "target_advantage_over_best_control",
                ),
                "positive_sweep_specific_pass": (
                    bool(positives)
                    and positive_specific_pass_count == len(positives)
                ),
                "near_controls_clear": near_control_pass_count == 0,
                "focused_gate_pass": (
                    bool(positives)
                    and positive_specific_pass_count == len(positives)
                    and near_control_pass_count == 0
                ),
            }
        )
    return summaries
