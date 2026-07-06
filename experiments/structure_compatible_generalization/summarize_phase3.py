#!/usr/bin/env python3
"""Summarize phase-three learned-generator transfer payloads."""

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


def _vision_regime(row: DiagnosticRow) -> str | None:
    value = row.metadata.get("regime")
    return value if isinstance(value, str) else None


def _base_unit(row: DiagnosticRow) -> int | None:
    value = row.metadata.get("base_unit")
    return int(value) if isinstance(value, int) else None


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


def modular_intervention(rows: list[DiagnosticRow]) -> list[dict[str, float]]:
    grouped: dict[float, list[DiagnosticRow]] = defaultdict(list)
    for row in rows:
        if row.domain != "modular_learned_generator":
            continue
        strength = _regularization_strength(row)
        if strength is not None:
            grouped[strength].append(row)

    out: list[dict[str, float]] = []
    for strength, group in sorted(grouped.items()):
        high_id = [row for row in group if row.train_accuracy >= 0.95]
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
                "mean_ood": mean(row.ood_accuracy for row in group),
                "mean_discovered": mean(discovered) if discovered else 0.0,
                "high_id_n": float(len(high_id)),
                "high_id_mean_ood": (
                    mean(row.ood_accuracy for row in high_id) if high_id else 0.0
                ),
            }
        )
    return out


def vision_intervention(rows: list[DiagnosticRow]) -> dict[str, Any]:
    vision_rows = [
        row for row in rows if row.domain == "vision_rotation_learned_generator"
    ]
    by_regime: dict[str, list[DiagnosticRow]] = defaultdict(list)
    for row in vision_rows:
        regime = _vision_regime(row)
        if regime is not None:
            by_regime[regime].append(row)

    regime_rows = []
    for regime, group in sorted(by_regime.items()):
        regime_rows.append(
            {
                "regime": regime,
                "n": float(len(group)),
                "mean_train": mean(row.train_accuracy for row in group),
                "mean_ood": mean(row.ood_accuracy for row in group),
                "mean_discovered": mean(
                    row.compatibility_discovered or 0.0 for row in group
                ),
            }
        )

    paired: dict[int, dict[str, DiagnosticRow]] = defaultdict(dict)
    for row in vision_rows:
        base = _base_unit(row)
        regime = _vision_regime(row)
        if base is not None and regime is not None:
            paired[base][regime] = row

    deltas: dict[str, list[float]] = defaultdict(list)
    for regimes in paired.values():
        baseline = regimes.get("none")
        if baseline is None:
            continue
        for regime in ("oracle_aug", "learned_aug", "random_aug"):
            if regime in regimes:
                deltas[regime].append(
                    regimes[regime].ood_accuracy - baseline.ood_accuracy
                )
    return {
        "by_regime": regime_rows,
        "paired_delta_vs_none": {
            regime: {
                "n": float(len(values)),
                "mean_delta": mean(values) if values else 0.0,
            }
            for regime, values in sorted(deltas.items())
        },
    }


def phase3_summary(payload: dict[str, Any]) -> dict[str, Any]:
    rows = rows_from_records(payload["rows"])
    non_exact = [row for row in rows if not row.domain.endswith("_exact")]
    return {
        "n_rows": len(rows),
        "n_non_exact_rows": len(non_exact),
        "summary": summarize_rows(rows),
        "predictors": predictor_rows(rows),
        "modular_intervention": modular_intervention(rows),
        "vision_intervention": vision_intervention(rows),
        "selection": selection_analysis(non_exact),
    }


def write_figures(
    rows: list[DiagnosticRow],
    phase3: dict[str, Any],
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
        for item in phase3["predictors"]
        if item["predictor"]
        in {"compatibility_true", "compatibility_discovered", "compatibility_wrong"}
    ]
    labels = [f"{item['domain']}\n{item['predictor']}" for item in predictors]
    values = [item["pearson"] for item in predictors]
    fig, ax = plt.subplots(figsize=(8.2, 4.2))
    ax.bar(range(len(values)), values, color="#2563eb")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=35, ha="right", fontsize=8)
    ax.set_ylabel("Pearson r with OOD")
    ax.set_title("Learned-generator compatibility predictors")
    fig.tight_layout()
    path = figure_dir / "fig5_learned_generator_predictors.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    paths.append(path)

    modular = phase3["modular_intervention"]
    vision = phase3["vision_intervention"]["by_regime"]
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.8))
    if modular:
        strengths = [item["regularization"] for item in modular]
        high_id_ood = [item["high_id_mean_ood"] for item in modular]
        axes[0].plot(strengths, high_id_ood, marker="o", color="#0f766e")
        axes[0].set_title("Modular learned generator")
        axes[0].set_xlabel("Regularization")
        axes[0].set_ylabel("High-ID mean OOD")
        axes[0].set_ylim(0, 1)
    if vision:
        regimes = [item["regime"] for item in vision]
        oods = [item["mean_ood"] for item in vision]
        axes[1].bar(regimes, oods, color="#7c3aed")
        axes[1].set_title("Vision learned augmentation")
        axes[1].set_ylabel("Mean OOD")
        axes[1].set_ylim(0, 1)
        axes[1].tick_params(axis="x", rotation=35)
    fig.tight_layout()
    path = figure_dir / "fig6_learned_generator_interventions.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    paths.append(path)
    return paths


def write_report(payload: dict[str, Any], phase3: dict[str, Any], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append("# Phase 3: Learned Generators and Transfer")
    lines.append("")
    lines.append("## Manifest")
    lines.append("")
    manifest = payload.get("manifest", {})
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
    lines.append("")
    lines.append("## Discovery-Regime Audit")
    lines.append("")
    lines.append(
        "- Old regime: supported modular shifts supplied the transformation "
        "parameterization."
    )
    lines.append(
        "- New operation: learn candidate input/label transports from observed "
        "overlap evidence, then transfer the same compatibility/intervention "
        "logic to data-inferred vision rotations."
    )
    lines.append(
        "- Claim level: finite generator-transfer diagnostic, not open-ended "
        "transformation discovery."
    )
    lines.append("")
    lines.append("## Predictor Correlations")
    lines.append("")
    lines.append("| Domain | Predictor | Pearson r | Spearman r | N |")
    lines.append("| --- | --- | ---: | ---: | ---: |")
    for item in sorted(
        phase3["predictors"],
        key=lambda row: (row["domain"], -row["pearson"]),
    ):
        lines.append(
            f"| `{item['domain']}` | `{item['predictor']}` | "
            f"{_fmt(item['pearson'])} | {_fmt(item['spearman'])} | "
            f"{int(item['n'])} |"
        )
    lines.append("")
    lines.append("## Modular Intervention")
    lines.append("")
    lines.append(
        "| Regularization | N | Mean train | Mean OOD | "
        "Mean learned compatibility | High-ID N | High-ID OOD |"
    )
    lines.append("| ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for item in phase3["modular_intervention"]:
        lines.append(
            f"| {_fmt(item['regularization'])} | {int(item['n'])} | "
            f"{_fmt(item['mean_train'])} | {_fmt(item['mean_ood'])} | "
            f"{_fmt(item['mean_discovered'])} | {int(item['high_id_n'])} | "
            f"{_fmt(item['high_id_mean_ood'])} |"
        )
    lines.append("")
    lines.append("## Vision Transfer")
    lines.append("")
    lines.append("| Regime | N | Mean train | Mean OOD | Mean learned compatibility |")
    lines.append("| --- | ---: | ---: | ---: | ---: |")
    for item in phase3["vision_intervention"]["by_regime"]:
        lines.append(
            f"| `{item['regime']}` | {int(item['n'])} | "
            f"{_fmt(item['mean_train'])} | {_fmt(item['mean_ood'])} | "
            f"{_fmt(item['mean_discovered'])} |"
        )
    lines.append("")
    lines.append("| Regime | Paired N | Mean OOD delta vs none |")
    lines.append("| --- | ---: | ---: |")
    for regime, stats in phase3["vision_intervention"][
        "paired_delta_vs_none"
    ].items():
        lines.append(
            f"| `{regime}` | {int(stats['n'])} | {_fmt(stats['mean_delta'])} |"
        )
    lines.append("")
    lines.append("## Residual Finding")
    lines.append("")
    lines.append(
        "The phase-three residual is whether learned generators can both "
        "predict and control OOD outside the hand-specified modular shift "
        "schema. The vision arm is the first transfer test; language/template "
        "substitution remains the next unclaimed step."
    )
    out.write_text("\n".join(lines) + "\n")


def write_paper_markdown(
    payload: dict[str, Any],
    phase3: dict[str, Any],
    paper_dir: Path,
    figure_paths: list[Path],
) -> None:
    paper_dir.mkdir(parents=True, exist_ok=True)
    predictors = phase3["predictors"]
    best = max(predictors, key=lambda item: (item["pearson"], item["spearman"]))
    modular = phase3["modular_intervention"]
    base_mod = next((item for item in modular if item["regularization"] == 0.0), None)
    best_mod = max(modular, key=lambda item: item["high_id_mean_ood"]) if modular else None
    mod_delta = None
    if base_mod is not None and best_mod is not None:
        mod_delta = best_mod["high_id_mean_ood"] - base_mod["high_id_mean_ood"]
    vision_delta = phase3["vision_intervention"]["paired_delta_vs_none"].get(
        "learned_aug",
        {},
    ).get("mean_delta")

    lines = [
        "# Learned Generators for Structure-Compatible Generalization",
        "",
        "**Jawaun Brown**",
        "",
        "## Abstract",
        "",
        "Earlier structure-compatible generalization results used either oracle "
        "deployment transformations or supported finite shifts inferred from "
        "observed overlaps. This phase tests a stricter protocol: learn a "
        "finite generator family from input/label transport evidence, use it "
        "for compatibility scoring and regularization in the modular domain, "
        "then transfer the same diagnostic shape to vision rotations inferred "
        "from training images. The claim is bounded: learned generators can "
        "support OOD prediction and intervention in controlled finite domains, "
        "not arbitrary open-world transformation discovery.",
        "",
        "## 1. Regime Transition",
        "",
        "The old regime supplied the transformation parameterization. The new "
        "operation learns candidate transports from data: modular offsets of "
        "the form `(a,b,y)->(a+da,b+db,y+dy)` and vision rotations selected by "
        "training-set self-consistency.",
        "",
        "## 2. Result",
        "",
        f"The strongest phase-three predictor was `{best['predictor']}` on "
        f"`{best['domain']}` (Pearson r={_fmt(best['pearson'])}).",
        "",
    ]
    if best_mod is not None:
        lines.append(
            "The best modular high-ID regularization arm was "
            f"{_fmt(best_mod['regularization'])}, with high-ID mean OOD "
            f"{_fmt(best_mod['high_id_mean_ood'])}. "
            f"Delta versus zero regularization: {_fmt(mod_delta)}."
        )
        lines.append("")
    if vision_delta is not None:
        lines.append(
            "In the vision transfer arm, learned augmentation produced mean "
            f"paired OOD delta {_fmt(vision_delta)} versus no augmentation."
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
            "This is a learned finite-generator transfer result. It is stronger "
            "than hand-given oracle groups, but weaker than open-ended "
            "transformation discovery. The generator classes are still chosen "
            "by the experimenter.",
            "",
            "## 4. Next Operation",
            "",
            "The next operation is a language/template substitution generator "
            "with strict controls: learned substitutions should improve OOD "
            "over no augmentation and beat random substitutions of matched "
            "size without using OOD labels.",
            "",
        ]
    )
    (paper_dir / "learned_generators_transfer.md").write_text("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="input", type=Path, required=True)
    parser.add_argument(
        "--report-out",
        type=Path,
        default=Path(
            "experiments/structure_compatible_generalization/results/"
            "phase3_learned_generators_2026_07_06.md"
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
    phase3 = phase3_summary(payload)
    payload["phase3_summary"] = phase3
    figure_paths = write_figures(rows, phase3, args.paper_dir / "figures")
    write_report(payload, phase3, args.report_out)
    write_paper_markdown(payload, phase3, args.paper_dir, figure_paths)
    print(f"Wrote report to {args.report_out}")
    print(
        "Wrote paper markdown to "
        f"{args.paper_dir / 'learned_generators_transfer.md'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
