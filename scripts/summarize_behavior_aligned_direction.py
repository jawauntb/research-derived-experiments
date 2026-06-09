#!/usr/bin/env python3
"""Render compact Markdown summaries for behavior-aligned direction payloads."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

JsonRow = dict[str, Any]


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else float("nan")


def selected_aggregates(
    payload: dict[str, Any],
    *,
    scale: float,
    role: str,
) -> list[JsonRow]:
    return [
        row
        for row in payload["aggregate_rows"]
        if float(row["scale"]) == scale and str(row["role"]) == role
    ]


def grouped_summary(payload: dict[str, Any], *, scale: float, role: str) -> list[JsonRow]:
    groups: dict[tuple[str, str, str, str], list[JsonRow]] = {}
    for row in selected_aggregates(payload, scale=scale, role=role):
        key = (
            str(row["prompt_frame"]),
            str(row["objective_label_scoring_regime"]),
            str(row["eval_label_scoring_regime"]),
            str(row["direction_mode"]),
        )
        groups.setdefault(key, []).append(row)

    summaries = []
    for (
        prompt_frame,
        objective_label_scoring_regime,
        eval_label_scoring_regime,
        direction_mode,
    ), rows in sorted(groups.items()):
        positives = [row for row in rows if row["kind"] == "positive"]
        controls = [row for row in rows if row["kind"] == "control"]
        summaries.append(
            {
                "prompt_frame": prompt_frame,
                "objective_label_scoring_regime": objective_label_scoring_regime,
                "eval_label_scoring_regime": eval_label_scoring_regime,
                "direction_mode": direction_mode,
                "positive_pass_count": sum(1 for row in positives if row["robust_pass"]),
                "positive_total": len(positives),
                "positive_mean": mean(
                    [float(row["mean_target_margin_delta"]) for row in positives]
                ),
                "control_pass_count": sum(1 for row in controls if row["robust_pass"]),
                "control_total": len(controls),
                "control_mean": mean(
                    [float(row["mean_target_margin_delta"]) for row in controls]
                ),
            }
        )
        summaries[-1]["specificity_score"] = (
            summaries[-1]["positive_mean"] - summaries[-1]["control_mean"]
        )
    return summaries


def pair_failures(
    payload: dict[str, Any],
    *,
    scale: float,
    role: str,
    kind: str,
) -> list[JsonRow]:
    rows = [
        row
        for row in selected_aggregates(payload, scale=scale, role=role)
        if str(row["kind"]) == kind and not bool(row["robust_pass"])
    ]
    return sorted(
        rows,
        key=lambda row: (
            str(row["prompt_frame"]),
            str(row["eval_label_scoring_regime"]),
            str(row["direction_mode"]),
            str(row["pair"]),
        ),
    )


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _header in headers) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def render_payload(path: Path, payload: dict[str, Any], *, scale: float, role: str) -> str:
    manifest = payload["manifest"]
    summaries = grouped_summary(payload, scale=scale, role=role)
    summary_rows = [
        [
            row["prompt_frame"],
            row["objective_label_scoring_regime"],
            row["eval_label_scoring_regime"],
            row["direction_mode"],
            f"{row['positive_pass_count']}/{row['positive_total']}",
            f"{row['positive_mean']:.3f}",
            f"{row['control_pass_count']}/{row['control_total']}",
            f"{row['control_mean']:.3f}",
            f"{row['specificity_score']:.3f}",
        ]
        for row in summaries
    ]
    failure_rows = [
        [
            str(row["prompt_frame"]),
            str(row["eval_label_scoring_regime"]),
            str(row["direction_mode"]),
            str(row["pair"]),
            f"{float(row['mean_target_margin_delta']):.3f}",
        ]
        for row in pair_failures(payload, scale=scale, role=role, kind="positive")
    ]
    sections = [
        f"## {path.name}",
        "",
        f"- Model: `{manifest['model_id']}`",
        f"- Pair set: `{manifest.get('pair_set', 'promoted')}`",
        f"- Scale: `{scale}`",
        f"- Role: `{role}`",
        "",
        markdown_table(
            [
                "Prompt",
                "Objective",
                "Eval",
                "Direction",
                "Positive passes",
                "Positive mean",
                "Control passes",
                "Control mean",
                "Specificity",
            ],
            summary_rows,
        ),
    ]
    if failure_rows:
        sections.extend(
            [
                "",
                "### Positive Failures",
                "",
                markdown_table(
                    ["Prompt", "Eval", "Direction", "Pair", "Mean delta"],
                    failure_rows,
                ),
            ]
        )
    return "\n".join(sections)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("payloads", nargs="+", type=Path)
    parser.add_argument("--scale", type=float, default=1.0)
    parser.add_argument("--role", default="primary")
    args = parser.parse_args()

    rendered = []
    for path in args.payloads:
        payload = json.loads(path.read_text(encoding="utf-8"))
        rendered.append(render_payload(path, payload, scale=args.scale, role=args.role))
    print("\n\n".join(rendered))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
