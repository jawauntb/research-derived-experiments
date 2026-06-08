#!/usr/bin/env python3
"""Render Markdown summaries for label-free behavior gate payloads."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any

JsonRow = dict[str, Any]


def load_payloads(paths: list[str]) -> list[tuple[Path, JsonRow]]:
    return [(Path(path), json.loads(Path(path).read_text())) for path in paths]


def artifact_label(path: Path, manifest: JsonRow) -> str:
    seed = manifest.get("seed")
    if seed is not None:
        return f"seed {seed}"
    return path.stem


def fmt_number(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.3f}"


def fmt_rate(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.1f}%"


def table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def manifest_rows(payloads: list[tuple[Path, JsonRow]]) -> list[JsonRow]:
    rows = []
    for path, payload in payloads:
        manifest = payload["manifest"]
        rows.append(
            {
                "artifact": artifact_label(path, manifest),
                "model": manifest["model_id"],
                "seed": manifest["seed"],
                "surface": manifest.get("patch_vector_surface", "hook_output"),
                "prompt_frame": manifest.get("prompt_frame", "source_passage"),
                "scoring_surface": manifest.get("scoring_surface", "option_token"),
                "injection_layers": ",".join(map(str, manifest["injection_layers"])),
                "alphas": ",".join(map(str, manifest["patch_alphas"])),
                "regimes": ",".join(manifest["patch_text_regimes"]),
                "option_orders": len(manifest["option_orders"]),
                "baseline_n": manifest["baseline_sample_count"],
                "pairs": len(manifest["pairs"]),
            }
        )
    return rows


def all_pair_rows(payloads: list[tuple[Path, JsonRow]], regime: str) -> list[JsonRow]:
    grouped: dict[tuple[Any, ...], list[JsonRow]] = defaultdict(list)
    for path, payload in payloads:
        label = artifact_label(path, payload["manifest"])
        for row in payload["specificity_rows"]:
            if row["patch_text_regime"] != regime:
                continue
            key = (
                label,
                row["injection_layer"],
                row.get("prompt_frame", "source_passage"),
                row.get("scoring_surface", "option_token"),
                row.get("patch_alpha", 1.0),
            )
            grouped[key].append(row)

    rows = []
    for (label, injection, prompt_frame, scoring_surface, alpha), group in sorted(
        grouped.items()
    ):
        deltas = [float(row["target_mean_target_margin_delta"]) for row in group]
        advantages = [
            float(row["target_advantage_over_best_control"]) for row in group
        ]
        passes = sum(1 for row in group if row["specific_target_pass"])
        rows.append(
            {
                "artifact": label,
                "injection_layer": injection,
                "prompt_frame": prompt_frame,
                "scoring_surface": scoring_surface,
                "alpha": alpha,
                "passes": passes,
                "total": len(group),
                "pass_rate": passes / len(group),
                "mean_delta": mean(deltas),
                "median_delta": median(deltas),
                "mean_advantage": mean(advantages),
                "median_advantage": median(advantages),
            }
        )
    return rows


def gate_summary_rows(payloads: list[tuple[Path, JsonRow]]) -> list[JsonRow]:
    rows = []
    for path, payload in payloads:
        label = artifact_label(path, payload["manifest"])
        for row in payload["gate_summaries"]:
            rows.append({"artifact": label, **row})
    return rows


def render_manifest(rows: list[JsonRow]) -> str:
    return table(
        [
            "Artifact",
            "Model",
            "Seed",
            "Surface",
            "Prompt frame",
            "Scoring",
            "Injection layers",
            "Alphas",
            "Regimes",
            "Option orders",
            "Baseline N",
            "Pairs",
        ],
        [
            [
                row["artifact"],
                row["model"],
                str(row["seed"]),
                row["surface"],
                row["prompt_frame"],
                row["scoring_surface"],
                row["injection_layers"],
                row["alphas"],
                row["regimes"],
                str(row["option_orders"]),
                str(row["baseline_n"]),
                str(row["pairs"]),
            ]
            for row in rows
        ],
    )


def render_all_pair(rows: list[JsonRow]) -> str:
    return table(
        [
            "Artifact",
            "Layer",
            "Prompt frame",
            "Scoring",
            "Alpha",
            "Specific passes",
            "Pass rate",
            "Mean delta",
            "Median delta",
            "Mean advantage",
            "Median advantage",
        ],
        [
            [
                row["artifact"],
                str(row["injection_layer"]),
                row["prompt_frame"],
                row["scoring_surface"],
                fmt_number(float(row["alpha"])),
                f"{row['passes']}/{row['total']}",
                fmt_rate(row["pass_rate"]),
                fmt_number(row["mean_delta"]),
                fmt_number(row["median_delta"]),
                fmt_number(row["mean_advantage"]),
                fmt_number(row["median_advantage"]),
            ]
            for row in rows
        ],
    )


def render_gate_summaries(rows: list[JsonRow]) -> str:
    return table(
        [
            "Artifact",
            "Regime",
            "Prompt frame",
            "Scoring",
            "Layer",
            "Alpha",
            "Specific passes",
            "Mean delta",
            "Mean advantage",
        ],
        [
            [
                row["artifact"],
                row["patch_text_regime"],
                row.get("prompt_frame", "source_passage"),
                row.get("scoring_surface", "option_token"),
                str(row["injection_layer"]),
                fmt_number(float(row["patch_alpha"])),
                f"{row['specific_pass_count']}/{row['total']}",
                fmt_number(row["mean_target_margin_delta"]),
                fmt_number(row["mean_advantage_over_best_control"]),
            ]
            for row in rows
        ],
    )


def render_summary(payloads: list[tuple[Path, JsonRow]]) -> str:
    sections = [
        ("Manifest Sanity", render_manifest(manifest_rows(payloads))),
        ("Definition Behavior Specificity", render_all_pair(all_pair_rows(payloads, "definition"))),
        ("Neutral Behavior Specificity", render_all_pair(all_pair_rows(payloads, "neutral"))),
        ("Gate Summaries", render_gate_summaries(gate_summary_rows(payloads))),
    ]
    return "\n\n".join(
        f"## {title}\n\n{body}" for title, body in sections if body.strip()
    )


def main(argv: list[str]) -> int:
    if not argv:
        print(
            "Usage: summarize_label_free_behavior_gate.py <payload.json> [payload.json ...]",
            file=sys.stderr,
        )
        return 2
    print(render_summary(load_payloads(argv)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
