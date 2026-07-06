#!/usr/bin/env python3
"""Summarize a structure-compatible generalization suite payload."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from experiments.structure_compatible_generalization.core import (
    rows_from_records,
    summarize_rows,
)


def _fmt(value: float | int | None, digits: int = 3) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, int):
        return str(value)
    return f"{value:.{digits}f}"


def _load_payload(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _summary(payload: dict[str, Any]) -> dict[str, Any]:
    rows = rows_from_records(payload["rows"])
    return summarize_rows(rows)


def write_figures(summary: dict[str, Any], figure_dir: Path) -> list[Path]:
    figure_dir.mkdir(parents=True, exist_ok=True)
    try:
        import matplotlib.pyplot as plt
    except ModuleNotFoundError:
        return []

    paths: list[Path] = []

    domains = list(summary["by_domain"])
    true_vals = [
        summary["by_domain"][domain]["correlations"]
        .get("compatibility_true", {})
        .get("pearson", 0.0)
        for domain in domains
    ]
    wrong_vals = [
        summary["by_domain"][domain]["correlations"]
        .get("compatibility_wrong", {})
        .get("pearson", 0.0)
        for domain in domains
    ]
    val_vals = [
        summary["by_domain"][domain]["correlations"]
        .get("id_validation_accuracy", {})
        .get("pearson", 0.0)
        for domain in domains
    ]

    fig, ax = plt.subplots(figsize=(7.0, 3.6))
    x = range(len(domains))
    width = 0.25
    ax.bar([i - width for i in x], true_vals, width=width, label="true compatibility")
    ax.bar(list(x), wrong_vals, width=width, label="wrong compatibility")
    ax.bar([i + width for i in x], val_vals, width=width, label="ID validation")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(list(x), domains, rotation=20, ha="right")
    ax.set_ylabel("Pearson r with OOD")
    ax.set_title("OOD predictor correlations by domain")
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    path = figure_dir / "fig1_domain_predictors.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    paths.append(path)

    aggregate = summary["selection"]["aggregate"]
    predictors = sorted(
        aggregate,
        key=lambda name: aggregate[name]["mean_selected_ood"],
        reverse=True,
    )[:8]
    values = [aggregate[name]["mean_selected_ood"] for name in predictors]
    fig, ax = plt.subplots(figsize=(7.0, 3.6))
    ax.barh(list(reversed(predictors)), list(reversed(values)), color="#2b6cb0")
    ax.set_xlim(0, 1)
    ax.set_xlabel("Mean selected OOD accuracy")
    ax.set_title("Model selection without OOD labels")
    fig.tight_layout()
    path = figure_dir / "fig2_selection_without_ood.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    paths.append(path)

    return paths


def write_report(payload: dict[str, Any], summary: dict[str, Any], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append("# Structure-Compatible Generalization L4 Suite")
    lines.append("")
    lines.append("## Manifest")
    lines.append("")
    manifest = payload.get("manifest", {})
    for key in sorted(manifest):
        value = manifest[key]
        if key == "budget_estimate":
            continue
        lines.append(f"- **{key}:** `{value}`")
    if "budget_estimate" in manifest:
        estimate = manifest["budget_estimate"]
        lines.append(
            "- **budget:** "
            f"{estimate.get('cells')} L4 cells, "
            f"conservative ${_fmt(float(estimate.get('conservative_cost_usd', 0.0)), 2)} "
            f"against ${_fmt(float(estimate.get('budget_usd', 0.0)), 2)}"
        )
    lines.append("")
    lines.append("## Headline")
    lines.append("")
    lines.append(
        "The diagnostic suite evaluates whether compatibility with the "
        "deployment-generating transformation family predicts OOD accuracy "
        "among finite models whose train/ID evidence is similar."
    )
    lines.append("")
    lines.append("## Domain Predictor Rankings")
    lines.append("")
    for domain, domain_summary in summary["by_domain"].items():
        lines.append(f"### {domain}")
        lines.append("")
        lines.append(
            f"- Rows: {domain_summary['n_rows']}; "
            f"mean train {domain_summary['mean_train_accuracy']:.3f}; "
            f"mean ID {domain_summary['mean_id_validation_accuracy']:.3f}; "
            f"mean OOD {domain_summary['mean_ood_accuracy']:.3f}"
        )
        lines.append("")
        lines.append("| Rank | Predictor | Pearson r | Spearman r | N |")
        lines.append("| ---: | --- | ---: | ---: | ---: |")
        for rank, item in enumerate(domain_summary["predictor_ranking"][:8], start=1):
            lines.append(
                f"| {rank} | `{item['predictor']}` | "
                f"{_fmt(item['pearson'])} | {_fmt(item['spearman'])} | {item['n']} |"
            )
        lines.append("")

    lines.append("## Selection Without OOD Labels")
    lines.append("")
    aggregate = summary["selection"]["aggregate"]
    lines.append("| Predictor | Domains | Mean selected OOD |")
    lines.append("| --- | ---: | ---: |")
    for predictor, stats in sorted(
        aggregate.items(),
        key=lambda item: item[1]["mean_selected_ood"],
        reverse=True,
    ):
        lines.append(
            f"| `{predictor}` | {int(stats['domains'])} | "
            f"{_fmt(stats['mean_selected_ood'])} |"
        )
    lines.append("")
    lines.append("## Regime Audit")
    lines.append("")
    lines.append(
        "- Old regime: Paper 3's oracle-group symbolic/MLP/vision weakness "
        "diagnostics."
    )
    lines.append(
        "- Transition: one common cross-domain diagnostic schema plus an "
        "additional modular algorithmic domain."
    )
    lines.append(
        "- Residual finding: compare the top-ranked predictors and OOD-free "
        "selection behavior across domains; do not claim full certification."
    )
    lines.append(
        "- Allowed claim: structure-compatible diagnostics for finite "
        "underspecified tasks with known deployment transformations."
    )
    lines.append("")
    out.write_text("\n".join(lines) + "\n")


def write_paper_markdown(
    payload: dict[str, Any],
    summary: dict[str, Any],
    paper_dir: Path,
    figure_paths: list[Path],
) -> None:
    paper_dir.mkdir(parents=True, exist_ok=True)
    path = paper_dir / "structure_compatible_generalization.md"
    top_lines = []
    for domain, domain_summary in summary["by_domain"].items():
        top = domain_summary["predictor_ranking"][0]
        top_lines.append(
            f"- `{domain}`: top predictor `{top['predictor']}` "
            f"(Pearson r={_fmt(top['pearson'])})."
        )

    selection = summary["selection"]["aggregate"].get("compatibility_true", {})
    selected_ood = selection.get("mean_selected_ood")
    lines = [
        "# Structure-Compatible Generalization",
        "",
        "**Jawaun Brown**",
        "",
        "## Abstract",
        "",
        "Modern learning systems are underspecified: many finite models can fit "
        "the same training data and pass the same in-distribution checks while "
        "behaving differently under deployment shifts. This paper reports a "
        "controlled diagnostic suite testing whether the transformation "
        "structure a learned function preserves predicts OOD behavior better "
        "than loss, ID validation, norm, or sharpness proxies. The suite "
        "combines cyclic symbolic MLPs, rotated visual objects, and a modular "
        "algorithmic table task under one schema. The claim is intentionally "
        "bounded: for finite domains where deployment shift is generated by a "
        "known transformation family, compatibility is an OOD diagnostic and "
        "model-selection signal, not a universal certification theorem.",
        "",
        "## 1. Problem",
        "",
        "The practical question is which model to trust when train loss and "
        "ID validation do not identify the transportable rule. The diagnostic "
        "tested here measures compatibility with the transformations expected "
        "to generate deployment cases.",
        "",
        "## 2. Suite",
        "",
        "The suite uses three controlled domains:",
        "",
        "- symbolic cyclic prefix tasks from the existing weakness benchmark;",
        "- rotated 16x16 visual-object tasks from the existing rotation weakness benchmark;",
        "- modular addition tasks where local prefix shortcuts and global translation rules are both train-compatible.",
        "",
        "Every trained model emits the same row schema: train accuracy, ID "
        "validation accuracy, OOD accuracy, true compatibility, wrong-group "
        "compatibility, loss, parameter norm, and sharpness when available.",
        "",
        "## 3. Results",
        "",
        *top_lines,
        "",
        "Selection by true compatibility without OOD labels reached mean selected "
        f"OOD accuracy {_fmt(selected_ood) if selected_ood is not None else 'n/a'} "
        "across domains where that selector was available.",
        "",
    ]
    if figure_paths:
        lines.extend(["## Figures", ""])
        for fig_path in figure_paths:
            rel = fig_path.relative_to(paper_dir)
            lines.append(f"![{fig_path.stem}]({rel})")
            lines.append("")
    lines.extend(
        [
            "## 4. Scope",
            "",
        "The result does not claim all OOD generalization is solved. It "
        "identifies a precise operating regime: finite or structured "
        "domains where the deployment shift is generated by a candidate "
        "transformation family and ID evidence underdetermines shortcut "
        "and rule-like completions.",
        "",
        "## 5. Architecture Lesson",
        "",
        "The simple architecture change is to make the expected deployment "
        "transformation an explicit selection surface. Instead of choosing "
        "among ID-equivalent models by loss, norm, or validation alone, score "
        "whether the learned input-output map preserves the transformation "
        "that will carry the task into deployment. This does not certify open "
        "world behavior, but it turns a global OOD stress into a local, "
        "auditable model-selection pressure.",
        "",
        "## 6. Next Step",
        "",
        "The next regime transition is learned or weakly inferred "
        "transformation discovery, followed by compatibility-guided "
            "regularization and active data acquisition.",
            "",
        ]
    )
    path.write_text("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="input", type=Path, required=True)
    parser.add_argument(
        "--report-out",
        type=Path,
        default=Path(
            "experiments/structure_compatible_generalization/results/"
            "structure_compatible_l4_2026_07_06.md"
        ),
    )
    parser.add_argument(
        "--paper-dir",
        type=Path,
        default=Path("papers/structure_compatible_generalization"),
    )
    args = parser.parse_args()

    payload = _load_payload(args.input)
    summary = _summary(payload)
    payload["summary"] = summary
    figure_paths = write_figures(summary, args.paper_dir / "figures")
    write_report(payload, summary, args.report_out)
    write_paper_markdown(payload, summary, args.paper_dir, figure_paths)
    print(f"Wrote report to {args.report_out}")
    print(
        "Wrote paper markdown to "
        f"{args.paper_dir / 'structure_compatible_generalization.md'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
