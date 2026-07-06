#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Build the semantic retrieval SCG paper PDF."""

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

from experiments.structure_compatible_generalization.core import rows_from_records  # noqa: E402
from experiments.structure_compatible_generalization.summarize_semantic_retrieval import (  # noqa: E402
    semantic_retrieval_summary,
    write_figures,
)
from reportlab.platypus import PageBreak  # noqa: E402


def _fmt(value: float | None, digits: int = 3) -> str:
    if value is None:
        return "n/a"
    return f"{value:.{digits}f}"


def _load(payload_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    payload = json.loads(payload_path.read_text())
    return payload, semantic_retrieval_summary(payload)


def build(payload_path: Path, out: Path, figure_dir: Path) -> None:
    payload, summary = _load(payload_path)
    rows = rows_from_records(payload["rows"])
    figure_paths = write_figures(rows, summary, figure_dir)

    p = pk.Paper(str(out), str(figure_dir))
    p.title("Semantic Retrieval Transfer for Structure-Compatible Generalization")
    p.authors("Jawaun Brown")
    p.authors("Phase 5: frozen-encoder semantic transfer")
    p.rule()
    p.abstract(
        "This phase moves structure-compatible generalization from rendered "
        "templates to short semantic retrieval cases. Actual frozen sentence "
        "encoders provide embeddings; nearest-neighbor structure infers "
        "candidate paraphrase and entity-substitution orbits; trained "
        "retrieval selectors are evaluated on held-out semantic variants "
        "without OOD labels."
    )

    manifest = payload.get("manifest", {})
    p.h1("1. Manifest")
    p.table(
        [
            ["Field", "Value"],
            ["GPU", str(manifest.get("gpu", "n/a"))],
            ["encoders", str(manifest.get("encoder_keys", "n/a"))],
            ["configs per encoder", str(manifest.get("n_configs", "n/a"))],
            ["rows", str(summary["n_rows"])],
        ],
        caption="Table 1. Semantic retrieval Modal L4 manifest.",
        col_widths=[150, 320],
    )

    p.h1("2. Predictor Correlations")
    predictor_rows = [["Domain", "Predictor", "Pearson r", "Spearman r", "N"]]
    for item in sorted(summary["predictors"], key=lambda row: (row["domain"], -row["pearson"])):
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
        caption="Table 2. Semantic retrieval predictors against OOD.",
        col_widths=[155, 165, 75, 75, 40],
    )

    for idx, fig_path in enumerate(figure_paths, start=1):
        caption = (
            "Figure 1. Semantic retrieval compatibility predictors."
            if idx == 1
            else "Figure 2. Encoder and selector breakdowns."
        )
        p.figure(str(fig_path), caption, width_in=6.1)

    p.h1("3. Breakdowns")
    encoder_rows = [["Encoder", "N", "Mean train", "Mean ID", "Mean OOD", "Compat"]]
    for item in summary["by_encoder"]:
        encoder_rows.append(
            [
                item["encoder"],
                str(int(item["n"])),
                _fmt(item["mean_train"]),
                _fmt(item["mean_id"]),
                _fmt(item["mean_ood"]),
                _fmt(item["mean_discovered"]),
            ]
        )
    p.table(
        encoder_rows,
        caption="Table 3. Frozen encoder rows.",
        col_widths=[145, 45, 80, 75, 75, 75],
    )

    p.flow.append(PageBreak())
    family_rows = [["Family", "N", "Mean train", "Mean ID", "Mean OOD", "Compat"]]
    for item in summary["by_family"]:
        family_rows.append(
            [
                item["family"],
                str(int(item["n"])),
                _fmt(item["mean_train"]),
                _fmt(item["mean_id"]),
                _fmt(item["mean_ood"]),
                _fmt(item["mean_discovered"]),
            ]
        )
    p.table(
        family_rows,
        caption="Table 4. Retrieval selector families.",
        col_widths=[145, 45, 80, 75, 75, 75],
    )

    p.h1("4. Scope")
    p.para(
        "The result is bounded to a finite semantic-retrieval corpus and "
        "public frozen text encoders. It does not certify arbitrary paraphrase "
        "invariance or production model behavior."
    )
    p.build()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="input", type=Path, required=True)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("papers/structure_compatible_generalization/semantic_retrieval_transfer.pdf"),
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
