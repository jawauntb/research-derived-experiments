#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Build the phase-two inferred-transformations paper PDF."""

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
from experiments.structure_compatible_generalization.summarize_phase2 import (  # noqa: E402
    phase2_summary,
    write_figures,
)


def _fmt(value: float | None, digits: int = 3) -> str:
    if value is None:
        return "n/a"
    return f"{value:.{digits}f}"


def _load_phase2(payload_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    payload = json.loads(payload_path.read_text())
    return payload, phase2_summary(payload)


def build(payload_path: Path, out: Path, figure_dir: Path) -> None:
    payload, phase2 = _load_phase2(payload_path)
    rows = rows_from_records(payload["rows"])
    figure_paths = write_figures(rows, phase2, figure_dir)

    p = pk.Paper(str(out), str(figure_dir))
    p.title("Inferred Transformations for Structure-Compatible Generalization")
    p.authors("Jawaun Brown")
    p.authors("Phase 2: supported discovery plus compatibility-guided training")
    p.rule()
    p.abstract(
        "Phase one showed that oracle transformation compatibility predicts "
        "OOD behavior under underspecification. This phase weakens the oracle: "
        "candidate transformations are admitted only when observed train-label "
        "overlaps support the induced input and label action, then the "
        "discovered family is used as a train-time compatibility regularizer. "
        "The result is a finite-domain test of OOD prediction and control "
        "without using OOD labels for selection or training."
    )

    manifest = payload.get("manifest", {})
    p.h1("1. Regime Transition")
    p.para(
        "The old regime supplied the deployment group. The new regime infers "
        "supported modular shifts from training evidence, rejects vacuous "
        "non-identity transformations, and applies compatibility pressure to "
        "unlabeled finite-domain inputs."
    )
    p.table(
        [
            ["Field", "Value"],
            ["GPU", str(manifest.get("gpu", "n/a"))],
            ["configs", str(manifest.get("n_configs", "n/a"))],
            ["epochs", str(manifest.get("epochs", "n/a"))],
            ["regularization values", str(manifest.get("regularization_values", "n/a"))],
            ["rows", str(phase2["n_rows"])],
        ],
        caption="Table 1. Phase-two Modal L4 manifest.",
        col_widths=[150, 320],
    )

    p.h1("2. Predictor Correlations")
    predictor_rows = [["Predictor", "Pearson r", "Spearman r", "N"]]
    for item in sorted(
        phase2["predictors"],
        key=lambda row: (row["pearson"], row["spearman"]),
        reverse=True,
    ):
        predictor_rows.append(
            [
                item["predictor"],
                _fmt(item["pearson"]),
                _fmt(item["spearman"]),
                str(int(item["n"])),
            ]
        )
    p.table(
        predictor_rows,
        caption="Table 2. Phase-two predictors against OOD.",
        col_widths=[210, 90, 90, 60],
    )

    if figure_paths:
        p.figure(
            str(figure_paths[0]),
            "Figure 1. Discovered compatibility is compared with oracle, "
            "wrong-group, and standard training proxies.",
            width_in=6.0,
        )
    if len(figure_paths) > 1:
        p.figure(
            str(figure_paths[1]),
            "Figure 2. Compatibility-guided regularization is evaluated "
            "without OOD labels; OOD is measured only after training.",
            width_in=6.0,
        )

    p.h1("3. Intervention")
    intervention_rows = [
        ["Reg", "N", "Mean train", "Mean OOD", "High-ID N", "High-ID OOD"]
    ]
    for item in phase2["intervention"]:
        intervention_rows.append(
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
        intervention_rows,
        caption="Table 3. Regularization arms.",
        col_widths=[70, 50, 90, 90, 70, 100],
    )

    p.h1("4. Scope")
    p.para(
        "This is a finite modular-domain result. It supports the broader "
        "OOD-certifiability-lite program by showing the first discovery plus "
        "intervention path, but it does not yet solve learned transformation "
        "generation for vision or language."
    )
    p.para(
        "The next operation is to make the transformation generator learned "
        "rather than enumerated, then carry the same protocol to rotations and "
        "paraphrase/template substitutions."
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
            "inferred_transformations_intervention.pdf"
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
