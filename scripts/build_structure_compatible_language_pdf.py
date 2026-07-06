#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Build the language-template SCG paper PDF."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import paperkit as pk  # noqa: E402
from reportlab.platypus import PageBreak  # noqa: E402

from experiments.structure_compatible_generalization.core import (  # noqa: E402
    rows_from_records,
)
from experiments.structure_compatible_generalization.summarize_language_templates import (  # noqa: E402
    language_template_summary,
    write_figures,
)


def _fmt(value: float | None, digits: int = 3) -> str:
    if value is None:
        return "n/a"
    return f"{value:.{digits}f}"


def _load_language(payload_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    payload = json.loads(payload_path.read_text())
    return payload, language_template_summary(payload)


def build(payload_path: Path, out: Path, figure_dir: Path) -> None:
    payload, summary = _load_language(payload_path)
    rows = rows_from_records(payload["rows"])
    figure_paths = write_figures(rows, summary, figure_dir)

    p = pk.Paper(str(out), str(figure_dir))
    p.title("Language-Template Substitution for Structure-Compatible Generalization")
    p.authors("Jawaun Brown")
    p.authors("Phase 4: finite text-template generator transfer")
    p.rule()
    p.abstract(
        "This phase tests structure-compatible generalization in a controlled "
        "finite text domain. Examples are rendered as short language templates "
        "with number words and offset words, while the deployment shift is "
        "precise: held-out number-word substitutions transport the label by "
        "the same offset. A finite generator is inferred from observed "
        "input/label-overlap evidence and used for OOD prediction and "
        "regularization without OOD labels."
    )

    manifest = payload.get("manifest", {})
    p.h1("1. Regime Transition")
    p.para(
        "Earlier SCG phases tested oracle groups, inferred modular shifts, "
        "learned affine transports, and vision rotations. This phase keeps "
        "the finite auditability but moves the surface form into rendered "
        "language templates."
    )
    p.table(
        [
            ["Field", "Value"],
            ["GPU", str(manifest.get("gpu", "n/a"))],
            ["configs", str(manifest.get("n_configs", "n/a"))],
            ["epochs", str(manifest.get("epochs", "n/a"))],
            ["regularization", str(manifest.get("regularization_values", "n/a"))],
            ["max transforms", str(manifest.get("max_transforms", "n/a"))],
            ["rows", str(summary["n_rows"])],
        ],
        caption="Table 1. Language-template Modal L4 manifest.",
        col_widths=[150, 320],
    )

    p.h1("2. Predictor Correlations")
    predictor_rows = [["Domain", "Predictor", "Pearson r", "Spearman r", "N"]]
    for item in sorted(
        summary["predictors"],
        key=lambda row: (row["domain"], -row["pearson"]),
    ):
        predictor_rows.append(
            [
                item["domain"],
                item["predictor"],
                _fmt(item["pearson"]),
                _fmt(item["spearman"]),
                str(int(item["n"])),
            ]
        )
    p.table(
        predictor_rows,
        caption="Table 2. Language-template predictors against OOD.",
        col_widths=[155, 165, 75, 75, 40],
    )

    for index, fig_path in enumerate(figure_paths, start=1):
        caption = (
            "Figure 1. Language-template compatibility predictors."
            if index == 1
            else "Figure 2. Language-template interventions."
        )
        p.figure(str(fig_path), caption, width_in=6.1)

    p.h1("3. Interventions")
    intervention_rows = [
        [
            "Reg",
            "N",
            "Mean train",
            "Mean ID",
            "Mean OOD",
            "High-ID N",
            "High-ID OOD",
        ]
    ]
    for item in summary["regularization_intervention"]:
        intervention_rows.append(
            [
                _fmt(item["regularization"]),
                str(int(item["n"])),
                _fmt(item["mean_train"]),
                _fmt(item["mean_id"]),
                _fmt(item["mean_ood"]),
                str(int(item["high_id_n"])),
                _fmt(item["high_id_mean_ood"]),
            ]
        )
    p.table(
        intervention_rows,
        caption="Table 3. Learned-substitution regularization arms.",
        col_widths=[55, 45, 80, 75, 75, 70, 85],
    )

    p.flow.append(PageBreak())
    augmentation_rows = [["Augmentation", "N", "Mean train", "Mean OOD", "Compat"]]
    for item in summary["augmentation_intervention"]:
        augmentation_rows.append(
            [
                str(item["augmentation"]),
                str(int(item["n"])),
                _fmt(float(item["mean_train"])),
                _fmt(float(item["mean_ood"])),
                _fmt(float(item["mean_discovered"])),
            ]
        )
    p.table(
        augmentation_rows,
        caption="Table 4. Data-substitution arms.",
        col_widths=[160, 45, 80, 80, 80],
    )

    p.h1("4. Scope")
    p.para(
        "The result is a controlled finite-language transfer test. It is not "
        "a claim about arbitrary natural-language paraphrase or semantic "
        "equivalence. The generator family is discovered inside an auditable "
        "template domain and evaluated on held-out number-word substitutions."
    )
    p.build()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="input", type=Path, required=True)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "papers/structure_compatible_generalization/"
            "language_template_substitution.pdf"
        ),
    )
    parser.add_argument(
        "--figure-dir",
        type=Path,
        default=Path("papers/structure_compatible_generalization/figures"),
    )
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    build(args.input, args.out, args.figure_dir)
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
