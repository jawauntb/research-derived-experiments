#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Build the phase-three learned-generators paper PDF."""

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

from experiments.structure_compatible_generalization.core import (  # noqa: E402
    rows_from_records,
)
from experiments.structure_compatible_generalization.summarize_phase3 import (  # noqa: E402
    phase3_summary,
    write_figures,
)


def _fmt(value: float | None, digits: int = 3) -> str:
    if value is None:
        return "n/a"
    return f"{value:.{digits}f}"


def _load_phase3(payload_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    payload = json.loads(payload_path.read_text())
    return payload, phase3_summary(payload)


def build(payload_path: Path, out: Path, figure_dir: Path) -> None:
    payload, phase3 = _load_phase3(payload_path)
    rows = rows_from_records(payload["rows"])
    figure_paths = write_figures(rows, phase3, figure_dir)

    p = pk.Paper(str(out), str(figure_dir))
    p.title("Learned Generators for Structure-Compatible Generalization")
    p.authors("Jawaun Brown")
    p.authors("Phase 3: finite generator discovery plus transfer")
    p.rule()
    p.abstract(
        "Earlier structure-compatible generalization results used oracle "
        "deployment transformations or finite shifts inferred from observed "
        "overlaps. Phase three learns finite generator families from data: "
        "modular affine input/label transports and vision rotations selected "
        "by training-set self-consistency. The result is a bounded test of OOD "
        "prediction and intervention without OOD labels, not an open-world "
        "transformation-discovery theorem."
    )

    manifest = payload.get("manifest", {})
    p.h1("1. Regime Transition")
    p.para(
        "The old regime supplied the transformation parameterization. The new "
        "operation learns candidate transports from data and evaluates whether "
        "the learned family predicts or controls OOD behavior under "
        "ID-equivalent training evidence."
    )
    p.table(
        [
            ["Field", "Value"],
            ["GPU", str(manifest.get("gpu", "n/a"))],
            ["modular configs", str(manifest.get("modular_configs", "n/a"))],
            ["vision base units", str(manifest.get("vision_base", "n/a"))],
            ["modular epochs", str(manifest.get("modular_epochs", "n/a"))],
            ["vision epochs", str(manifest.get("vision_epochs", "n/a"))],
            ["rows", str(phase3["n_rows"])],
        ],
        caption="Table 1. Phase-three Modal L4 manifest.",
        col_widths=[150, 320],
    )

    p.h1("2. Predictor Correlations")
    predictor_rows = [["Domain", "Predictor", "Pearson r", "Spearman r", "N"]]
    for item in sorted(
        phase3["predictors"],
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
        caption="Table 2. Phase-three predictors against OOD.",
        col_widths=[145, 165, 75, 75, 40],
    )

    for index, fig_path in enumerate(figure_paths, start=1):
        caption = (
            "Figure 1. Learned-generator compatibility predictors."
            if index == 1
            else "Figure 2. Learned-generator interventions."
        )
        p.figure(str(fig_path), caption, width_in=6.1)

    p.h1("3. Interventions")
    modular_rows = [
        ["Reg", "N", "Mean train", "Mean OOD", "High-ID N", "High-ID OOD"]
    ]
    for item in phase3["modular_intervention"]:
        modular_rows.append(
            [
                _fmt(item["regularization"]),
                str(int(item["n"])),
                _fmt(item["mean_train"]),
                _fmt(item["mean_ood"]),
                str(int(item["high_id_n"])),
                _fmt(item["high_id_mean_ood"]),
            ]
        )
    p.table(
        modular_rows,
        caption="Table 3. Modular learned-generator regularization arms.",
        col_widths=[70, 50, 90, 90, 70, 100],
    )

    vision_rows = [["Regime", "N", "Mean train", "Mean OOD", "Learned compat"]]
    for item in phase3["vision_intervention"]["by_regime"]:
        vision_rows.append(
            [
                item["regime"],
                str(int(item["n"])),
                _fmt(item["mean_train"]),
                _fmt(item["mean_ood"]),
                _fmt(item["mean_discovered"]),
            ]
        )
    p.table(
        vision_rows,
        caption="Table 4. Vision rotation transfer arms.",
        col_widths=[150, 50, 90, 90, 100],
    )

    p.h1("4. Scope")
    p.para(
        "The result is a learned finite-generator transfer result. It is "
        "stronger than hand-given oracle groups, but the generator classes are "
        "still chosen by the experimenter. Language/template substitution is "
        "the next unclaimed transfer step."
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
            "learned_generators_transfer.pdf"
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
