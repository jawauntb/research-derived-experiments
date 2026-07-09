#!/usr/bin/env python3
"""E1 -- Unequal-Consequence Concern-Weighted Selector.

Pre-registered discriminator for M2 (concern portability) vs the new
commitment-first frame. Compares four selectors amongst train-perfect
hypotheses on cyclic modular addition with an unequal-consequence
deployment slice.

Selectors:
- unweighted weakness (uniform Bennett)
- concern-weighted weakness with well-specified kappa
- concern-weighted weakness with misspecified (random) kappa (same
  marginal weight distribution)
- loss / train-perfect selector (baseline)

Prediction (commitment-first):
- concern-weighted (well-spec) > unweighted iff well-spec kappa aligns
  with deployment generator.
- misspec == unweighted (concern only helps when aligned).

Falsifier (G2 in PLAN.md): concern-weighted-wellspec matches unweighted
under alignment, or misspec beats unweighted.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean

from experiments.commitment_surface.core import (
    E1CellResult,
    mean_ci95,
    run_e1_cell,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--moduli", type=str, default="7,11,13,17")
    p.add_argument("--seeds", type=int, default=32)
    p.add_argument("--focus-fraction", type=float, default=0.25)
    p.add_argument("--focus-weight", type=float, default=10.0)
    p.add_argument("--n-candidates", type=int, default=400)
    p.add_argument("--train-window-frac", type=float, default=0.5)
    p.add_argument(
        "--out", type=Path,
        default=Path("experiments/commitment_surface/results/e1_concern_weighted.json"),
    )
    p.add_argument(
        "--summary", type=Path,
        default=Path("experiments/commitment_surface/results/e1_concern_weighted.md"),
    )
    return p.parse_args()


def summarize_cells(cells: list[E1CellResult]) -> dict:
    def _col(field: str) -> list[float]:
        return [getattr(c, field) for c in cells]

    m_unw, lo_unw, hi_unw = mean_ci95(_col("unweighted_selector_acc"))
    m_well, lo_well, hi_well = mean_ci95(_col("concern_wellspec_selector_acc"))
    m_mis, lo_mis, hi_mis = mean_ci95(_col("concern_misspec_selector_acc"))
    m_loss, lo_loss, hi_loss = mean_ci95(_col("loss_selector_acc"))
    m_truth, lo_truth, hi_truth = mean_ci95(_col("truth_selector_acc"))

    gap_wellspec_vs_unweighted = m_well - m_unw
    gap_misspec_vs_unweighted = m_mis - m_unw
    return {
        "n_cells": len(cells),
        "unweighted": {"mean": m_unw, "ci95_low": lo_unw, "ci95_high": hi_unw},
        "concern_wellspec": {"mean": m_well, "ci95_low": lo_well, "ci95_high": hi_well},
        "concern_misspec": {"mean": m_mis, "ci95_low": lo_mis, "ci95_high": hi_mis},
        "loss": {"mean": m_loss, "ci95_low": lo_loss, "ci95_high": hi_loss},
        "truth": {"mean": m_truth, "ci95_low": lo_truth, "ci95_high": hi_truth},
        "gap_wellspec_vs_unweighted": gap_wellspec_vs_unweighted,
        "gap_misspec_vs_unweighted": gap_misspec_vs_unweighted,
        "commitment_first_pass_wellspec_beats_unweighted": (
            gap_wellspec_vs_unweighted >= 0.05
        ),
        "commitment_first_pass_misspec_matches_unweighted": (
            abs(gap_misspec_vs_unweighted) <= 0.05
        ),
    }


def write_markdown(summary: dict, cells: list[E1CellResult], path: Path) -> None:
    lines = [
        "# E1 — Unequal-Consequence Concern-Weighted Selector",
        "",
        f"Cells: {summary['n_cells']}",
        "",
        "## Selector accuracies on the well-specified deployment slice",
        "",
        "| Selector | Mean | 95% CI |",
        "|---|---:|---|",
    ]
    for name, key in [
        ("Unweighted weakness", "unweighted"),
        ("Concern-weighted (well-spec)", "concern_wellspec"),
        ("Concern-weighted (misspec random)", "concern_misspec"),
        ("Train-loss selector", "loss"),
        ("Truth (upper bound)", "truth"),
    ]:
        s = summary[key]
        lines.append(
            f"| {name} | {s['mean']:.3f} | [{s['ci95_low']:.3f}, {s['ci95_high']:.3f}] |"
        )
    lines.extend(
        [
            "",
            "## Gates",
            "",
            (
                "- Commitment-first pass (wellspec beats unweighted by ≥0.05): "
                f"**{summary['commitment_first_pass_wellspec_beats_unweighted']}** "
                f"(gap={summary['gap_wellspec_vs_unweighted']:.3f})"
            ),
            (
                "- Commitment-first pass (misspec matches unweighted within 0.05): "
                f"**{summary['commitment_first_pass_misspec_matches_unweighted']}** "
                f"(gap={summary['gap_misspec_vs_unweighted']:.3f})"
            ),
            "",
            "## Per-modulus breakdown",
            "",
            "| Modulus | # cells | Unweighted | Wellspec | Misspec | Loss |",
            "|---:|---:|---:|---:|---:|---:|",
        ]
    )

    by_mod: dict[int, list[E1CellResult]] = {}
    for c in cells:
        by_mod.setdefault(c.modulus, []).append(c)
    for m in sorted(by_mod):
        group = by_mod[m]
        lines.append(
            f"| {m} | {len(group)} | "
            f"{mean(c.unweighted_selector_acc for c in group):.3f} | "
            f"{mean(c.concern_wellspec_selector_acc for c in group):.3f} | "
            f"{mean(c.concern_misspec_selector_acc for c in group):.3f} | "
            f"{mean(c.loss_selector_acc for c in group):.3f} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    moduli = [int(x) for x in args.moduli.split(",") if x.strip()]

    cells: list[E1CellResult] = []
    for modulus in moduli:
        for seed in range(args.seeds):
            cells.append(
                run_e1_cell(
                    modulus=modulus,
                    seed=seed,
                    focus_fraction=args.focus_fraction,
                    focus_weight=args.focus_weight,
                    n_candidates=args.n_candidates,
                    train_window_frac=args.train_window_frac,
                )
            )

    summary = summarize_cells(cells)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as fh:
        json.dump(
            {
                "summary": summary,
                "cells": [c.__dict__ for c in cells],
                "config": vars(args) | {"out": str(args.out), "summary": str(args.summary)},
            },
            fh,
            indent=2,
            default=str,
        )
    write_markdown(summary, cells, args.summary)
    print(f"E1 done: {len(cells)} cells; wrote {args.out} and {args.summary}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
