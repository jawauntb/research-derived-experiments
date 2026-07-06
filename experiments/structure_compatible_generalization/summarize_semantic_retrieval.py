#!/usr/bin/env python3
"""Summarize SCG semantic retrieval transfer payloads."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
from statistics import mean
from typing import Any

from experiments.structure_compatible_generalization.core import (
    DiagnosticRow,
    predictor_correlations,
    rows_from_records,
    selection_analysis,
    summarize_rows,
)


def _fmt(value: float | int | None, digits: int = 3) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, int):
        return str(value)
    return f"{value:.{digits}f}"


def _config_field(row: DiagnosticRow, key: str) -> Any:
    config = row.metadata.get("config")
    if isinstance(config, dict):
        return config.get(key)
    return None


def predictor_rows(rows: list[DiagnosticRow]) -> list[dict[str, Any]]:
    keep = [
        "compatibility_true",
        "compatibility_discovered",
        "compatibility_wrong",
        "id_validation_accuracy",
        "train_accuracy",
    ]
    out: list[dict[str, Any]] = []
    for domain in sorted({row.domain for row in rows if not row.domain.endswith("_exact")}):
        domain_rows = [row for row in rows if row.domain == domain]
        correlations = predictor_correlations(domain_rows)
        for predictor in keep:
            if predictor in correlations:
                out.append({"domain": domain, "predictor": predictor, **correlations[predictor]})
    return out


def by_encoder(rows: list[DiagnosticRow]) -> list[dict[str, Any]]:
    grouped: dict[str, list[DiagnosticRow]] = defaultdict(list)
    for row in rows:
        if row.domain != "semantic_retrieval_frozen_encoder":
            continue
        encoder = str(row.metadata.get("encoder_key", "unknown"))
        grouped[encoder].append(row)
    out = []
    for encoder, group in sorted(grouped.items()):
        discovered = [row.compatibility_discovered or 0.0 for row in group]
        out.append(
            {
                "encoder": encoder,
                "n": float(len(group)),
                "mean_train": mean(row.train_accuracy for row in group),
                "mean_id": mean(row.id_validation_accuracy for row in group),
                "mean_ood": mean(row.ood_accuracy for row in group),
                "mean_discovered": mean(discovered),
            }
        )
    return out


def by_family(rows: list[DiagnosticRow]) -> list[dict[str, Any]]:
    grouped: dict[str, list[DiagnosticRow]] = defaultdict(list)
    for row in rows:
        if row.domain != "semantic_retrieval_frozen_encoder":
            continue
        family = str(_config_field(row, "family") or "unknown")
        grouped[family].append(row)
    out = []
    for family, group in sorted(grouped.items()):
        out.append(
            {
                "family": family,
                "n": float(len(group)),
                "mean_train": mean(row.train_accuracy for row in group),
                "mean_id": mean(row.id_validation_accuracy for row in group),
                "mean_ood": mean(row.ood_accuracy for row in group),
                "mean_discovered": mean(row.compatibility_discovered or 0.0 for row in group),
            }
        )
    return out


def semantic_retrieval_summary(payload: dict[str, Any]) -> dict[str, Any]:
    rows = rows_from_records(payload["rows"])
    non_exact = [row for row in rows if not row.domain.endswith("_exact")]
    return {
        "n_rows": len(rows),
        "n_non_exact_rows": len(non_exact),
        "summary": summarize_rows(rows),
        "predictors": predictor_rows(rows),
        "by_encoder": by_encoder(rows),
        "by_family": by_family(rows),
        "selection": selection_analysis(non_exact),
    }


def write_figures(rows: list[DiagnosticRow], summary: dict[str, Any], figure_dir: Path) -> list[Path]:
    figure_dir.mkdir(parents=True, exist_ok=True)
    try:
        import matplotlib.pyplot as plt
    except ModuleNotFoundError:
        return []

    paths: list[Path] = []
    predictors = [
        item
        for item in summary["predictors"]
        if item["predictor"] in {"compatibility_true", "compatibility_discovered", "compatibility_wrong"}
    ]
    labels = [item["predictor"].replace("compatibility_", "") for item in predictors]
    values = [item["pearson"] for item in predictors]
    fig, ax = plt.subplots(figsize=(6.8, 3.8))
    ax.bar(range(len(values)), values, color="#2563eb")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=25, ha="right")
    ax.set_ylabel("Pearson r with OOD")
    ax.set_title("Semantic retrieval compatibility predictors")
    fig.tight_layout()
    path = figure_dir / "fig9_semantic_retrieval_predictors.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    paths.append(path)

    encoders = summary["by_encoder"]
    families = summary["by_family"]
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.8))
    if encoders:
        axes[0].bar([item["encoder"] for item in encoders], [item["mean_ood"] for item in encoders], color="#0f766e")
        axes[0].set_title("Frozen encoders")
        axes[0].set_ylim(0, 1)
        axes[0].tick_params(axis="x", rotation=25)
    if families:
        axes[1].bar([item["family"] for item in families], [item["mean_ood"] for item in families], color="#7c3aed")
        axes[1].set_title("Retrieval selectors")
        axes[1].set_ylim(0, 1)
        axes[1].tick_params(axis="x", rotation=35)
    fig.tight_layout()
    path = figure_dir / "fig10_semantic_retrieval_breakdowns.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    paths.append(path)
    return paths


def write_report(payload: dict[str, Any], summary: dict[str, Any], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    manifest = payload.get("manifest", {})
    lines = [
        "# Phase 5: Semantic Retrieval Transfer",
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
            "- Old regime: rendered templates supplied explicit substitution structure.",
            "- New operation: infer semantic paraphrase/entity orbits from frozen-encoder neighborhoods and test retrieval OOD.",
            "- Claim level: frozen-encoder semantic transfer, not arbitrary open-world paraphrase certification.",
            "",
            "## Predictor Correlations",
            "",
            "| Domain | Predictor | Pearson r | Spearman r | N |",
            "| --- | --- | ---: | ---: | ---: |",
        ]
    )
    for item in sorted(summary["predictors"], key=lambda row: (row["domain"], -row["pearson"])):
        lines.append(
            f"| `{item['domain']}` | `{item['predictor']}` | "
            f"{_fmt(item['pearson'])} | {_fmt(item['spearman'])} | {int(item['n'])} |"
        )
    lines.extend(["", "## Encoder Breakdown", "", "| Encoder | N | Mean train | Mean ID | Mean OOD | Mean learned compatibility |", "| --- | ---: | ---: | ---: | ---: | ---: |"])
    for item in summary["by_encoder"]:
        lines.append(
            f"| `{item['encoder']}` | {int(item['n'])} | {_fmt(item['mean_train'])} | "
            f"{_fmt(item['mean_id'])} | {_fmt(item['mean_ood'])} | {_fmt(item['mean_discovered'])} |"
        )
    lines.extend(["", "## Selector Family Breakdown", "", "| Family | N | Mean train | Mean ID | Mean OOD | Mean learned compatibility |", "| --- | ---: | ---: | ---: | ---: | ---: |"])
    for item in summary["by_family"]:
        lines.append(
            f"| `{item['family']}` | {int(item['n'])} | {_fmt(item['mean_train'])} | "
            f"{_fmt(item['mean_id'])} | {_fmt(item['mean_ood'])} | {_fmt(item['mean_discovered'])} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The semantic retrieval phase asks whether learned compatibility remains useful when the transformation family is inferred from actual frozen text-encoder neighborhoods rather than supplied as a finite symbolic substitution.",
        ]
    )
    out.write_text("\n".join(lines) + "\n")


def write_paper_markdown(payload: dict[str, Any], summary: dict[str, Any], paper_dir: Path, figure_paths: list[Path]) -> None:
    paper_dir.mkdir(parents=True, exist_ok=True)
    best = max(summary["predictors"], key=lambda item: (item["pearson"], item["spearman"]))
    lines = [
        "# Semantic Retrieval Transfer for Structure-Compatible Generalization",
        "",
        "**Jawaun Brown**",
        "",
        "## Abstract",
        "",
        "This phase moves structure-compatible generalization from rendered templates to short semantic retrieval cases. Actual frozen sentence encoders provide embeddings; nearest-neighbor structure infers candidate paraphrase and entity-substitution orbits; trained retrieval selectors are then evaluated on held-out semantic variants without using OOD labels.",
        "",
        "## 1. Result",
        "",
        f"The strongest semantic retrieval predictor was `{best['predictor']}` with Pearson r={_fmt(best['pearson'])}.",
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
            "The result is bounded to a finite semantic-retrieval corpus and public frozen text encoders. It does not certify arbitrary paraphrase invariance or production model behavior.",
            "",
        ]
    )
    (paper_dir / "semantic_retrieval_transfer.md").write_text("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="input", type=Path, required=True)
    parser.add_argument("--report-out", type=Path, default=Path("experiments/structure_compatible_generalization/results/semantic_retrieval_transfer_2026_07_06.md"))
    parser.add_argument("--paper-dir", type=Path, default=Path("papers/structure_compatible_generalization"))
    args = parser.parse_args()
    payload = json.loads(args.input.read_text())
    rows = rows_from_records(payload["rows"])
    summary = semantic_retrieval_summary(payload)
    payload["semantic_retrieval_summary"] = summary
    figures = write_figures(rows, summary, args.paper_dir / "figures")
    write_report(payload, summary, args.report_out)
    write_paper_markdown(payload, summary, args.paper_dir, figures)
    print(f"Wrote report to {args.report_out}")
    print(f"Wrote paper markdown to {args.paper_dir / 'semantic_retrieval_transfer.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
