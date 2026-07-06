#!/usr/bin/env python3
"""Summarize semantic selection-control payloads."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Any

from experiments.structure_compatible_generalization.core import rows_from_records
from experiments.structure_compatible_generalization.semantic_selection_control import (
    SelectionRecord,
    selection_records_from_dicts,
    summarize_selection_records,
)


SELECTOR_ORDER = [
    "random_candidate",
    "id_validation_accuracy",
    "train_accuracy",
    "compatibility_wrong",
    "compatibility_discovered",
    "compatibility_true",
    "ood_oracle",
]


def _fmt(value: float | int | None, digits: int = 3) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, int):
        return str(value)
    return f"{value:.{digits}f}"


def _ordered_selector_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    rows = list(summary["by_selector"])
    order = {selector: idx for idx, selector in enumerate(SELECTOR_ORDER)}
    return sorted(rows, key=lambda row: order.get(str(row["selector"]), 999))


def semantic_selection_summary(payload: dict[str, Any]) -> dict[str, Any]:
    if "selection_records" in payload:
        records = selection_records_from_dicts(payload["selection_records"])
        return summarize_selection_records(records)
    rows = rows_from_records(payload["rows"])
    from experiments.structure_compatible_generalization.semantic_selection_control import (
        selection_records,
    )

    return summarize_selection_records(selection_records(rows))


def write_figures(
    records: list[SelectionRecord],
    summary: dict[str, Any],
    figure_dir: Path,
) -> list[Path]:
    figure_dir.mkdir(parents=True, exist_ok=True)
    try:
        import matplotlib.pyplot as plt
    except ModuleNotFoundError:
        return []

    paths: list[Path] = []
    rows = _ordered_selector_rows(summary)
    labels = [str(row["selector"]).replace("_", "\n") for row in rows]
    oods = [float(row["mean_selected_ood"]) for row in rows]
    colors = [
        "#64748b",
        "#475569",
        "#475569",
        "#dc2626",
        "#2563eb",
        "#0f766e",
        "#111827",
    ][: len(rows)]
    fig, ax = plt.subplots(figsize=(8.2, 4.1))
    ax.bar(range(len(rows)), oods, color=colors)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Mean selected OOD")
    ax.set_title("OOD-free semantic model selection")
    ax.set_xticks(range(len(rows)))
    ax.set_xticklabels(labels, rotation=0)
    fig.tight_layout()
    path = figure_dir / "fig11_semantic_selection_ood.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    paths.append(path)

    regrets = [float(row["mean_regret"]) for row in rows]
    fig, ax = plt.subplots(figsize=(8.2, 4.1))
    ax.bar(range(len(rows)), regrets, color=colors)
    ax.set_ylim(0, max(0.05, max(regrets) * 1.15))
    ax.set_ylabel("Mean regret vs OOD oracle")
    ax.set_title("Selection regret under ID-equivalence")
    ax.set_xticks(range(len(rows)))
    ax.set_xticklabels(labels, rotation=0)
    fig.tight_layout()
    path = figure_dir / "fig12_semantic_selection_regret.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    paths.append(path)
    return paths


def _threshold_table(records: list[SelectionRecord]) -> list[dict[str, Any]]:
    grouped: dict[tuple[float, str], list[SelectionRecord]] = {}
    for record in records:
        if record.selector not in {
            "compatibility_discovered",
            "id_validation_accuracy",
            "compatibility_wrong",
        }:
            continue
        grouped.setdefault((record.discovered_threshold, record.selector), []).append(record)
    rows = []
    for (threshold, selector), group in sorted(grouped.items()):
        rows.append(
            {
                "threshold": threshold,
                "selector": selector,
                "n": len(group),
                "mean_selected_ood": mean(record.selected_ood for record in group),
                "mean_lift_vs_random": mean(record.lift_vs_random for record in group),
            }
        )
    return rows


def write_report(
    payload: dict[str, Any],
    summary: dict[str, Any],
    out: Path,
) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    manifest = payload.get("manifest", {})
    records = selection_records_from_dicts(payload["selection_records"])
    lines = [
        "# Phase 6: Semantic Selection Control",
        "",
        "## Manifest",
        "",
    ]
    for key in sorted(manifest):
        value = manifest[key]
        if key == "budget_estimate":
            continue
        lines.append(f"- **{key}:** `{value}`")
    estimate = manifest.get("budget_estimate")
    if isinstance(estimate, dict):
        lines.append(
            "- **budget:** "
            f"{estimate.get('cells')} L4 cells, "
            f"conservative ${_fmt(float(estimate.get('conservative_cost_usd', 0.0)), 2)} "
            f"against ${_fmt(float(estimate.get('budget_usd', 0.0)), 2)}"
        )
    lines.extend(
        [
            "",
            "## Discovery-Regime Audit",
            "",
            "- Current regime: frozen-encoder semantic retrieval rows with learned candidate transformation pairs.",
            "- New operation: OOD-free model-zoo selection inside high train/ID candidate sets.",
            "- Gate: learned compatibility must beat train/ID selectors and random "
            "selection, while wrong compatibility fails.",
            "- Claim level: finite semantic retrieval model selection, not universal paraphrase certification.",
            "",
            "## Gate Status",
            "",
            "| Gate | Passed |",
            "| --- | ---: |",
        ]
    )
    for key, value in summary["gates"].items():
        lines.append(f"| `{key}` | `{bool(value)}` |")
    lines.extend(
        [
            "",
            "## Selector Results",
            "",
            "| Selector | Zoos | Mean candidates | Selected OOD | Regret | Lift vs random | Mean ties |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in _ordered_selector_rows(summary):
        lines.append(
            f"| `{row['selector']}` | {int(row['n_zoos'])} | "
            f"{_fmt(row['mean_candidates'])} | {_fmt(row['mean_selected_ood'])} | "
            f"{_fmt(row['mean_regret'])} | {_fmt(row['mean_lift_vs_random'])} | "
            f"{_fmt(row['mean_tied_count'])} |"
        )
    lines.extend(
        [
            "",
            "## Threshold Stress Test",
            "",
            "| Threshold | Selector | Zoos | Selected OOD | Lift vs random |",
            "| ---: | --- | ---: | ---: | ---: |",
        ]
    )
    for row in _threshold_table(records):
        lines.append(
            f"| {_fmt(row['threshold'], 2)} | `{row['selector']}` | "
            f"{row['n']} | {_fmt(row['mean_selected_ood'])} | "
            f"{_fmt(row['mean_lift_vs_random'])} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This phase tests the deployable version of the semantic retrieval "
            "claim: when train and ID validation are insufficient to choose "
            "among candidates, learned compatibility is used as the selector "
            "before OOD labels are inspected.",
        ]
    )
    out.write_text("\n".join(lines) + "\n")


def write_paper_markdown(
    payload: dict[str, Any],
    summary: dict[str, Any],
    paper_dir: Path,
    figure_paths: list[Path],
) -> None:
    paper_dir.mkdir(parents=True, exist_ok=True)
    lookup = {row["selector"]: row for row in summary["by_selector"]}
    discovered = lookup["compatibility_discovered"]
    id_baseline = lookup["id_validation_accuracy"]
    wrong = lookup["compatibility_wrong"]
    lines = [
        "# Semantic Selection Control for Structure-Compatible Generalization",
        "",
        "**Jawaun Brown**",
        "",
        "## Abstract",
        "",
        "This phase turns semantic retrieval compatibility from a predictor "
        "into an OOD-free model-selection protocol. Candidate retrieval models "
        "are grouped into encoder-threshold seed zoos, filtered to high train "
        "and ID validation performance, selected by learned compatibility or "
        "baseline selectors, and evaluated only afterward on held-out semantic "
        "variants.",
        "",
        "## 1. Result",
        "",
        "Learned compatibility selected mean OOD "
        f"{_fmt(discovered['mean_selected_ood'])}, compared with ID validation "
        f"selection at {_fmt(id_baseline['mean_selected_ood'])} and "
        f"wrong-compatibility control at {_fmt(wrong['mean_selected_ood'])}.",
        "",
    ]
    if figure_paths:
        lines.extend(["## Figures", ""])
        for fig_path in figure_paths:
            lines.append(f"![{fig_path.stem}]({fig_path.relative_to(paper_dir)})")
            lines.append("")
    lines.extend(
        [
            "## 2. Scope",
            "",
            "The protocol selects among finite semantic retrieval candidates "
            "generated by public frozen encoders. It is an "
            "OOD-certifiability-lite result for this structured setting, not a "
            "full behavioral guarantee for open-ended language systems.",
            "",
        ]
    )
    (paper_dir / "semantic_selection_control.md").write_text("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="input", type=Path, required=True)
    parser.add_argument(
        "--report-out",
        type=Path,
        default=Path(
            "experiments/structure_compatible_generalization/results/"
            "semantic_selection_control_2026_07_06.md"
        ),
    )
    parser.add_argument(
        "--paper-dir",
        type=Path,
        default=Path("papers/structure_compatible_generalization"),
    )
    args = parser.parse_args()
    payload = json.loads(args.input.read_text())
    records = selection_records_from_dicts(payload["selection_records"])
    summary = semantic_selection_summary(payload)
    figures = write_figures(records, summary, args.paper_dir / "figures")
    write_report(payload, summary, args.report_out)
    write_paper_markdown(payload, summary, args.paper_dir, figures)
    print(f"Wrote report to {args.report_out}")
    print(f"Wrote paper markdown to {args.paper_dir / 'semantic_selection_control.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
