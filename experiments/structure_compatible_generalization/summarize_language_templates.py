#!/usr/bin/env python3
"""Summarize SCG language/template substitution payloads."""

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


def _load_payload(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _regularization_strength(row: DiagnosticRow) -> float | None:
    config = row.metadata.get("config")
    if not isinstance(config, dict):
        return None
    value = config.get("compatibility_regularization")
    return None if value is None else float(value)


def _augmentation(row: DiagnosticRow) -> str | None:
    config = row.metadata.get("config")
    if not isinstance(config, dict):
        return None
    value = config.get("augmentation")
    return value if isinstance(value, str) else None


def predictor_rows(rows: list[DiagnosticRow]) -> list[dict[str, Any]]:
    keep = [
        "compatibility_true",
        "compatibility_discovered",
        "compatibility_wrong",
        "id_validation_accuracy",
        "train_accuracy",
        "negative_train_loss",
        "negative_parameter_l2",
        "negative_abs_sharpness",
    ]
    out: list[dict[str, Any]] = []
    for domain in sorted({row.domain for row in rows if not row.domain.endswith("_exact")}):
        domain_rows = [row for row in rows if row.domain == domain]
        correlations = predictor_correlations(domain_rows)
        for predictor in keep:
            if predictor in correlations:
                out.append(
                    {
                        "domain": domain,
                        "predictor": predictor,
                        **correlations[predictor],
                    }
                )
    return out


def regularization_intervention(rows: list[DiagnosticRow]) -> list[dict[str, float]]:
    grouped: dict[float, list[DiagnosticRow]] = defaultdict(list)
    for row in rows:
        if row.domain != "language_template_substitution":
            continue
        strength = _regularization_strength(row)
        if strength is not None:
            grouped[strength].append(row)

    out: list[dict[str, float]] = []
    for strength, group in sorted(grouped.items()):
        high_id = [
            row
            for row in group
            if row.train_accuracy >= 0.95 and row.id_validation_accuracy >= 0.95
        ]
        discovered = [
            row.compatibility_discovered
            for row in group
            if row.compatibility_discovered is not None
        ]
        out.append(
            {
                "regularization": strength,
                "n": float(len(group)),
                "mean_train": mean(row.train_accuracy for row in group),
                "mean_id": mean(row.id_validation_accuracy for row in group),
                "mean_ood": mean(row.ood_accuracy for row in group),
                "mean_discovered": mean(discovered) if discovered else 0.0,
                "high_id_n": float(len(high_id)),
                "high_id_mean_ood": (
                    mean(row.ood_accuracy for row in high_id) if high_id else 0.0
                ),
                "high_id_mean_discovered": (
                    mean(row.compatibility_discovered or 0.0 for row in high_id)
                    if high_id
                    else 0.0
                ),
            }
        )
    return out


def augmentation_intervention(rows: list[DiagnosticRow]) -> list[dict[str, float | str]]:
    grouped: dict[str, list[DiagnosticRow]] = defaultdict(list)
    for row in rows:
        if row.domain != "language_template_substitution":
            continue
        augmentation = _augmentation(row)
        if augmentation is not None:
            grouped[augmentation].append(row)

    out: list[dict[str, float | str]] = []
    for augmentation, group in sorted(grouped.items()):
        out.append(
            {
                "augmentation": augmentation,
                "n": float(len(group)),
                "mean_train": mean(row.train_accuracy for row in group),
                "mean_ood": mean(row.ood_accuracy for row in group),
                "mean_discovered": mean(
                    row.compatibility_discovered or 0.0 for row in group
                ),
            }
        )
    return out


def language_template_summary(payload: dict[str, Any]) -> dict[str, Any]:
    rows = rows_from_records(payload["rows"])
    non_exact = [row for row in rows if not row.domain.endswith("_exact")]
    return {
        "n_rows": len(rows),
        "n_non_exact_rows": len(non_exact),
        "summary": summarize_rows(rows),
        "predictors": predictor_rows(rows),
        "regularization_intervention": regularization_intervention(rows),
        "augmentation_intervention": augmentation_intervention(rows),
        "selection": selection_analysis(non_exact),
    }


def write_figures(
    rows: list[DiagnosticRow],
    summary: dict[str, Any],
    figure_dir: Path,
) -> list[Path]:
    figure_dir.mkdir(parents=True, exist_ok=True)
    try:
        import matplotlib.pyplot as plt
    except ModuleNotFoundError:
        return []

    paths: list[Path] = []
    predictors = [
        item
        for item in summary["predictors"]
        if item["predictor"]
        in {"compatibility_true", "compatibility_discovered", "compatibility_wrong"}
    ]
    labels = [item["predictor"].replace("compatibility_", "") for item in predictors]
    values = [item["pearson"] for item in predictors]
    fig, ax = plt.subplots(figsize=(6.8, 3.8))
    ax.bar(range(len(values)), values, color="#2563eb")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=25, ha="right")
    ax.set_ylabel("Pearson r with OOD")
    ax.set_title("Language/template compatibility predictors")
    fig.tight_layout()
    path = figure_dir / "fig7_language_template_predictors.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    paths.append(path)

    intervention = summary["regularization_intervention"]
    augmentation = summary["augmentation_intervention"]
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.8))
    if intervention:
        strengths = [item["regularization"] for item in intervention]
        high_id_ood = [item["high_id_mean_ood"] for item in intervention]
        high_id_compat = [item["high_id_mean_discovered"] for item in intervention]
        axes[0].plot(strengths, high_id_ood, marker="o", label="OOD")
        axes[0].plot(
            strengths,
            high_id_compat,
            marker="s",
            label="learned compat",
        )
        axes[0].set_title("Regularization arm")
        axes[0].set_xlabel("Compatibility regularization")
        axes[0].set_ylim(0, 1)
        axes[0].legend(fontsize=8)
    if augmentation:
        regimes = [str(item["augmentation"]) for item in augmentation]
        oods = [float(item["mean_ood"]) for item in augmentation]
        axes[1].bar(regimes, oods, color="#0f766e")
        axes[1].set_title("Substitution data arm")
        axes[1].set_ylim(0, 1)
        axes[1].tick_params(axis="x", rotation=25)
    fig.tight_layout()
    path = figure_dir / "fig8_language_template_intervention.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    paths.append(path)
    return paths


def write_report(payload: dict[str, Any], summary: dict[str, Any], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    manifest = payload.get("manifest", {})
    lines: list[str] = [
        "# Phase 4: Language/Template Substitution Generator",
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
            "- Old regime: modular and vision generators tested finite transport "
            "families outside open-ended text.",
            "- New operation: render finite addition examples as language-like "
            "templates and infer number-word/template substitutions from "
            "observed label-transport overlaps.",
            "- Claim level: controlled language/template substitution, not broad "
            "natural-language paraphrase discovery.",
            "",
            "## Predictor Correlations",
            "",
            "| Domain | Predictor | Pearson r | Spearman r | N |",
            "| --- | --- | ---: | ---: | ---: |",
        ]
    )
    for item in sorted(
        summary["predictors"],
        key=lambda row: (row["domain"], -row["pearson"]),
    ):
        lines.append(
            f"| `{item['domain']}` | `{item['predictor']}` | "
            f"{_fmt(item['pearson'])} | {_fmt(item['spearman'])} | "
            f"{int(item['n'])} |"
        )
    lines.extend(
        [
            "",
            "## Regularization Intervention",
            "",
            "| Regularization | N | Mean train | Mean ID | Mean OOD | "
            "Mean learned compatibility | High-ID N | High-ID OOD |",
            "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for item in summary["regularization_intervention"]:
        lines.append(
            f"| {_fmt(item['regularization'])} | {int(item['n'])} | "
            f"{_fmt(item['mean_train'])} | {_fmt(item['mean_id'])} | "
            f"{_fmt(item['mean_ood'])} | {_fmt(item['mean_discovered'])} | "
            f"{int(item['high_id_n'])} | {_fmt(item['high_id_mean_ood'])} |"
        )
    lines.extend(
        [
            "",
            "## Augmentation Arm",
            "",
            "| Augmentation | N | Mean train | Mean OOD | Mean learned compatibility |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for item in summary["augmentation_intervention"]:
        lines.append(
            f"| `{item['augmentation']}` | {int(item['n'])} | "
            f"{_fmt(float(item['mean_train']))} | "
            f"{_fmt(float(item['mean_ood']))} | "
            f"{_fmt(float(item['mean_discovered']))} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The language/template suite is the finite-text bridge requested by the "
            "SCG program: it asks whether learned substitution compatibility "
            "predicts held-out number-word transport when ordinary train and "
            "ID checks are tied.",
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
    predictors = summary["predictors"]
    best = max(predictors, key=lambda item: (item["pearson"], item["spearman"]))
    interventions = summary["regularization_intervention"]
    base = next(
        (item for item in interventions if item["regularization"] == 0.0),
        None,
    )
    best_intervention = (
        max(interventions, key=lambda item: item["high_id_mean_ood"])
        if interventions
        else None
    )
    delta = None
    if base is not None and best_intervention is not None:
        delta = (
            best_intervention["high_id_mean_ood"]
            - base["high_id_mean_ood"]
        )

    lines = [
        "# Language-Template Substitution for Structure-Compatible Generalization",
        "",
        "**Jawaun Brown**",
        "",
        "## Abstract",
        "",
        "This phase tests structure-compatible generalization in a controlled "
        "finite text domain. Examples are rendered as short templates with "
        "number words and offset words, but the deployment shift is precise: "
        "held-out number-word substitutions should transport the label by the "
        "same offset. A finite generator is inferred from observed "
        "input/label-overlap evidence and used for OOD prediction, model "
        "selection, and compatibility regularization without OOD labels.",
        "",
        "## 1. Regime Transition",
        "",
        "Earlier phases tested oracle groups, inferred modular shifts, learned "
        "affine transports, and vision rotations. This phase moves the same "
        "diagnostic into a language-like template surface while keeping the "
        "deployment transformations auditable.",
        "",
        "## 2. Result",
        "",
        f"The strongest language-template predictor was `{best['predictor']}` "
        f"with Pearson r={_fmt(best['pearson'])}.",
        "",
    ]
    if best_intervention is not None:
        lines.append(
            "The best high-ID regularization arm was "
            f"{_fmt(best_intervention['regularization'])}, with high-ID mean "
            f"OOD {_fmt(best_intervention['high_id_mean_ood'])}. "
            f"Delta versus zero regularization: {_fmt(delta)}."
        )
        lines.append("")
    if figure_paths:
        lines.extend(["## Figures", ""])
        for fig_path in figure_paths:
            rel = fig_path.relative_to(paper_dir)
            lines.append(f"![{fig_path.stem}]({rel})")
            lines.append("")
    lines.extend(
        [
            "## 3. Scope",
            "",
            "This is not a claim about arbitrary natural-language paraphrases. "
            "It is a controlled finite-language result: the syntax is rendered "
            "as text, the deployment family is number-word substitution, and "
            "the inferred generator is judged by held-out substitution OOD.",
            "",
            "## 4. Next Operation",
            "",
            "The next step is to connect this controlled text result to either "
            "semantic paraphrase or retrieval-template shifts, while preserving "
            "the no-OOD-label selection protocol.",
            "",
        ]
    )
    (paper_dir / "language_template_substitution.md").write_text("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="input", type=Path, required=True)
    parser.add_argument(
        "--report-out",
        type=Path,
        default=Path(
            "experiments/structure_compatible_generalization/results/"
            "language_template_substitution_2026_07_06.md"
        ),
    )
    parser.add_argument(
        "--paper-dir",
        type=Path,
        default=Path("papers/structure_compatible_generalization"),
    )
    args = parser.parse_args()

    payload = _load_payload(args.input)
    rows = rows_from_records(payload["rows"])
    summary = language_template_summary(payload)
    payload["language_template_summary"] = summary
    figure_paths = write_figures(rows, summary, args.paper_dir / "figures")
    write_report(payload, summary, args.report_out)
    write_paper_markdown(payload, summary, args.paper_dir, figure_paths)
    print(f"Wrote report to {args.report_out}")
    print(
        "Wrote paper markdown to "
        f"{args.paper_dir / 'language_template_substitution.md'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
