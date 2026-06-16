#!/usr/bin/env python3
"""Summarize Arc 2A Modal sweeps into a tracked markdown report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Any

METRICS: tuple[str, ...] = (
    "parse_accuracy_high_concern",
    "action_accuracy",
    "subtree_accuracy",
    "high_concern_probe_rate",
    "low_concern_probe_rate",
    "mean_regret",
)


def _mean(values: list[float]) -> float:
    return mean(values) if values else 0.0


def summarize_modal_payload(payload: dict[str, Any]) -> dict[str, dict[str, float]]:
    """Average selector metrics across Modal seed summaries."""

    results = payload.get("results", [])
    if not results:
        return {}

    selectors = sorted(results[0]["summary"])
    summary: dict[str, dict[str, float]] = {}
    for selector in selectors:
        stats: dict[str, float] = {}
        for metric in METRICS:
            values = [
                float(result["summary"][selector][metric])
                for result in results
            ]
            stats[metric] = _mean(values)
        gate_values = [
            float(result["summary"][selector]["gate_pass"])
            for result in results
        ]
        stats["gate_pass_rate"] = _mean(gate_values)
        summary[selector] = stats
    return summary


def write_modal_report(path: Path, payload: dict[str, Any]) -> None:
    manifest = payload["manifest"]
    summary = summarize_modal_payload(payload)
    seeds = manifest["seeds"]
    trials_per_seed = manifest["trials_per_seed"]
    total_trials = len(seeds) * trials_per_seed

    lines = [
        "# Concerned Syntax Modal Sweep",
        "",
        "Date: 2026-06-16",
        "",
        (
            f"Manifest: {len(seeds)} seeds x {trials_per_seed} trials "
            f"= {total_trials} shape trials."
        ),
        "",
        "Remote command:",
        "",
        "```bash",
        "doppler --scope /Users/jawaun/superoptimizers run -- \\",
        "  uvx --python 3.12 --from modal modal run \\",
        "  experiments/concerned_syntax/modal_concerned_syntax_sweep.py \\",
        f"  --trials {trials_per_seed}",
        "```",
        "",
        "## Gate Summary",
        "",
        (
            "| Selector | Parse high | Action | Subtree | High probe | "
            "Low probe | Mean regret | Gate pass rate |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for selector, stats in summary.items():
        lines.append(
            "| {selector} | {parse_high:.3f} | {action:.3f} | {subtree:.3f} | "
            "{high_probe:.3f} | {low_probe:.3f} | {regret:.3f} | "
            "{gate:.3f} |".format(
                selector=selector,
                parse_high=stats["parse_accuracy_high_concern"],
                action=stats["action_accuracy"],
                subtree=stats["subtree_accuracy"],
                high_probe=stats["high_concern_probe_rate"],
                low_probe=stats["low_concern_probe_rate"],
                regret=stats["mean_regret"],
                gate=stats["gate_pass_rate"],
            )
        )

    accepted = [
        selector
        for selector, stats in summary.items()
        if stats["gate_pass_rate"] == 1.0
    ]
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "`concerned_syntax` is accepted when it passes on every seed "
                "while the anti-cheat controls fail for different reasons: "
                "flat valence and compression do not recover causal "
                "constituency, and uncertainty-only inquiry over-probes "
                "low-concern ambiguity."
            ),
            "",
            "Accepted selectors: "
            + (", ".join(f"`{selector}`" for selector in accepted) or "none"),
            "",
            "Raw JSON remains local under `artifacts/concerned_syntax/`.",
        ]
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("artifacts/concerned_syntax/modal_sweep.json"),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("experiments/concerned_syntax/results/modal_sweep_2026_06_16.md"),
    )
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    write_modal_report(args.report, payload)
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
