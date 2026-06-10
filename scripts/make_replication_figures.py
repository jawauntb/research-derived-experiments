#!/usr/bin/env python3
"""Replication figures for the Passive→Active Geometry paper, v2.

Two figures:
  fig4_replication_bars.png — per-cell paraphrase-specific drop, passive
    vs active, 3 seeds x 2 models. Shows the direction is the same in
    every cell.
  fig5_replication_cluster_intervention.png — paired scatter of cluster
    gap vs paraphrase-specific drop per cell, before vs after action
    coupling. Each cell is one (model, seed); arrow shows direction.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

FIG_DIR = ROOT / "papers" / "passive_to_active_geometry" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)


def main() -> int:
    data = json.loads(
        (ROOT / "artifacts" / "passive_to_active" / "replication_v1.json").read_text()
    )
    cells = data["cells"]

    # short display labels
    def short_model(m):
        return "Pythia-70M" if "pythia" in m else "GPT-2"

    labels = [f"{short_model(c['model_id'])}\nseed={c['seed']}" for c in cells]
    p_spec = [c["passive_specific"] for c in cells]
    a_spec = [c["active_specific"] for c in cells]
    deltas = [a - p for a, p in zip(a_spec, p_spec)]

    # ---- Figure 4: replication bars ----
    fig, ax = plt.subplots(figsize=(12, 5.5))
    x = np.arange(len(cells))
    w = 0.36

    b1 = ax.bar(x - w / 2, p_spec, w, label="passive (pretrained)",
                color="#1f77b4", alpha=0.85)
    b2 = ax.bar(x + w / 2, a_spec, w, label="active (fine-tuned)",
                color="#2ca02c", alpha=0.85)
    for bar, v in zip(b1, p_spec):
        ax.text(bar.get_x() + bar.get_width() / 2,
                v + (0.025 if v >= 0 else -0.05),
                f"{v:+.3f}", ha="center", fontsize=9, color="#1f4068")
    for bar, v in zip(b2, a_spec):
        ax.text(bar.get_x() + bar.get_width() / 2,
                v + 0.025,
                f"{v:+.3f}", ha="center", fontsize=9, color="#1d6d1d",
                fontweight="bold")

    ax.axhline(0, color="black", linewidth=0.8)
    ax.axhspan(-0.05, 0.05, color="gray", alpha=0.08,
               label="≈ no effect band")
    # 3x-equivalent gate (cleaner restatement)
    ax.axhline(0.30, color="#888", linestyle=":", linewidth=1.0,
               label="active-effect gate (+0.30)")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel(
        "Paraphrase-specific drop\n(paraphrase ablate − random ablate)",
        fontsize=11,
    )
    ax.set_ylim(-0.72, 0.72)
    ax.set_title(
        "Replication across 3 seeds × {Pythia-70M, GPT-2}: "
        "active specific effect dominates passive in every cell",
        fontsize=12,
    )
    ax.legend(loc="lower right", fontsize=9)
    ax.grid(axis="y", linestyle=":", alpha=0.4)

    # vertical separator between model families
    ax.axvline(2.5, color="black", linewidth=0.5, alpha=0.35)
    ax.text(1, -0.68, "Pythia-70M-deduped", ha="center",
            fontsize=10, fontstyle="italic", color="#444")
    ax.text(4, -0.68, "GPT-2 (124M)", ha="center",
            fontsize=10, fontstyle="italic", color="#444")

    fig.tight_layout()
    out = FIG_DIR / "fig4_replication_bars.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ---- Figure 5: paired arrows in (cluster gap, specific drop) space ----
    fig, ax = plt.subplots(figsize=(9, 6.5))

    for c in cells:
        is_pythia = "pythia" in c["model_id"]
        color = "#1f77b4" if is_pythia else "#d62728"
        x0, y0 = c["passive_cluster_gap"], c["passive_specific"]
        x1, y1 = c["active_cluster_gap"], c["active_specific"]
        ax.annotate(
            "", xy=(x1, y1), xytext=(x0, y0),
            arrowprops=dict(arrowstyle="->", color=color, lw=1.6,
                            alpha=0.85, shrinkA=4, shrinkB=4),
        )
        ax.scatter([x0], [y0], s=70, color=color, alpha=0.4,
                   edgecolor=color, linewidth=1.0, marker="o", zorder=3)
        ax.scatter([x1], [y1], s=140, color=color, alpha=0.95,
                   edgecolor="black", linewidth=0.8, marker="*", zorder=4)
        # tiny label of seed near active end
        ax.text(x1 + 0.012, y1 + 0.012, f"s={c['seed']}",
                fontsize=7.5, color=color, alpha=0.8)

    # legend handles
    from matplotlib.lines import Line2D
    legend_items = [
        Line2D([], [], marker="o", color="w", markerfacecolor="#1f77b4",
               markersize=8, alpha=0.7, label="Pythia-70M passive"),
        Line2D([], [], marker="*", color="w", markerfacecolor="#1f77b4",
               markersize=14, markeredgecolor="black",
               label="Pythia-70M active"),
        Line2D([], [], marker="o", color="w", markerfacecolor="#d62728",
               markersize=8, alpha=0.7, label="GPT-2 passive"),
        Line2D([], [], marker="*", color="w", markerfacecolor="#d62728",
               markersize=14, markeredgecolor="black",
               label="GPT-2 active"),
    ]
    ax.legend(handles=legend_items, loc="lower right", fontsize=9)

    ax.axhline(0, color="black", linewidth=0.6)
    ax.axvline(0, color="black", linewidth=0.6)
    ax.set_xlabel("Centered-cosine cluster gap (same − diff)", fontsize=11)
    ax.set_ylabel(
        "Paraphrase-specific drop\n(paraphrase ablate − random ablate)",
        fontsize=11,
    )
    ax.set_title(
        "Action coupling moves every cell to the upper-right:\n"
        "tighter clusters AND larger paraphrase-specific causal effect",
        fontsize=12,
    )
    ax.grid(linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig5_replication_cluster_intervention.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ---- emit a small summary stats file for the paper ----
    summary = {
        "n_cells": len(cells),
        "n_active_specific_gte_0.3": sum(1 for v in a_spec if v >= 0.30),
        "n_delta_gte_0.3": sum(1 for d in deltas if d >= 0.30),
        "mean_passive_specific": float(np.mean(p_spec)),
        "mean_active_specific": float(np.mean(a_spec)),
        "mean_delta": float(np.mean(deltas)),
        "min_active_specific": float(np.min(a_spec)),
        "min_delta": float(np.min(deltas)),
        "active_specific_per_cell": a_spec,
        "passive_specific_per_cell": p_spec,
        "delta_per_cell": deltas,
        "cell_labels": labels,
    }
    out_path = ROOT / "artifacts" / "passive_to_active" / "replication_v1_summary.json"
    out_path.write_text(json.dumps(summary, indent=2))
    print(f"wrote {out_path}")

    print("\nHeadline gate (clean restatement):")
    print(f"  active specific ≥ 0.30 in : {summary['n_active_specific_gte_0.3']}/{summary['n_cells']} cells")
    print(f"  delta ≥ 0.30 in           : {summary['n_delta_gte_0.3']}/{summary['n_cells']} cells")
    print(f"  min active specific       : {summary['min_active_specific']:+.4f}")
    print(f"  min delta                 : {summary['min_delta']:+.4f}")
    print(f"  mean passive specific     : {summary['mean_passive_specific']:+.4f}")
    print(f"  mean active specific      : {summary['mean_active_specific']:+.4f}")
    print(f"  mean delta                : {summary['mean_delta']:+.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
