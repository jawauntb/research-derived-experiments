#!/usr/bin/env python3
"""Summarize Arc 2B Modal sweeps into a tracked markdown report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Any

METRICS: tuple[str, ...] = (
    "viable",
    "concerned_syntax_score",
    "train_return",
    "formal_valid",
    "anti_cheat",
    "resource_cost",
)


def _mean(values: list[float]) -> float:
    return mean(values) if values else 0.0


def summarize_modal_payload(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Average final architecture metrics across Modal strategy/seed cells."""

    grouped: dict[str, list[dict[str, Any]]] = {}
    for result in payload.get("results", []):
        grouped.setdefault(result["strategy"], []).append(result["final"])

    summary: dict[str, dict[str, Any]] = {}
    for strategy, rows in sorted(grouped.items()):
        stats: dict[str, Any] = {}
        for metric in METRICS:
            values = [float(row[metric]) for row in rows]
            stats[metric] = _mean(values)
        best = max(
            rows,
            key=lambda row: (
                int(row["viable"]),
                float(row["concerned_syntax_score"]),
                float(row["anti_cheat"]),
                float(row["train_return"]),
            ),
        )
        stats["best_architecture"] = best["architecture"]
        stats["n_seeds"] = len(rows)
        stats["gate_pass"] = bool(
            stats["viable"] >= 0.75
            and stats["concerned_syntax_score"] >= 0.80
            and stats["formal_valid"] >= 1.0
        )
        summary[strategy] = stats
    return summary


def write_modal_report(path: Path, payload: dict[str, Any]) -> None:
    manifest = payload["manifest"]
    summary = summarize_modal_payload(payload)
    seeds = manifest["seeds"]
    generations = manifest["generations"]
    population = manifest["population"]

    lines = [
        "# Viable Computational Bodies Modal Sweep",
        "",
        "Date: 2026-06-16",
        "",
        (
            f"Manifest: {len(seeds)} seeds per strategy, "
            f"{generations} generations, population {population}."
        ),
        "",
        "Remote command:",
        "",
        "```bash",
        "doppler --scope /Users/jawaun/superoptimizers run -- \\",
        "  uvx --python 3.12 --from modal modal run \\",
        "  experiments/viable_computational_bodies/modal_body_evolution_sweep.py \\",
        f"  --generations {generations} --population {population}",
        "```",
        "",
        "## Gate Summary",
        "",
        (
            "| Strategy | Viable rate | Syntax score | Train return | "
            "Formal valid | Anti-cheat | Cost | Best architecture | Gate |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for strategy, stats in summary.items():
        lines.append(
            "| {strategy} | {viable:.3f} | {syntax:.3f} | {train:.3f} | "
            "{formal:.3f} | {anti:.3f} | {cost:.3f} | `{best}` | "
            "{gate} |".format(
                strategy=strategy,
                viable=stats["viable"],
                syntax=stats["concerned_syntax_score"],
                train=stats["train_return"],
                formal=stats["formal_valid"],
                anti=stats["anti_cheat"],
                cost=stats["resource_cost"],
                best=stats["best_architecture"],
                gate="PASS" if stats["gate_pass"] else "fail",
            )
        )

    accepted = [
        strategy
        for strategy, stats in summary.items()
        if stats["gate_pass"]
    ]
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "`viability_guided` is accepted when it repeatedly discovers "
                "formal, resource-bounded, syntax-bearing bodies. "
                "Reward-only search remains a shortcut control; novelty-only "
                "search is informative but does not reliably satisfy the full "
                "viability gate."
            ),
            "",
            "Accepted strategies: "
            + (", ".join(f"`{strategy}`" for strategy in accepted) or "none"),
            "",
            "Raw JSON remains local under `artifacts/viable_computational_bodies/`.",
        ]
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("artifacts/viable_computational_bodies/modal_sweep.json"),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path(
            "experiments/viable_computational_bodies/results/"
            "modal_sweep_2026_06_16.md"
        ),
    )
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    write_modal_report(args.report, payload)
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
