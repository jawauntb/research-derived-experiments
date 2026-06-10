#!/usr/bin/env python3
"""Figures for Paper 6 v1 — Valence-Induced Object Formation.

Four figures:

  fig1_axis_dominance.png   : per-condition cluster gap by axis
                              (color / label / reward), mean ± std
                              across seeds × reward structures.
                              The headline: which axis the encoder
                              clusters by.
  fig2_pca_projection.png   : 2D PCA of held-out embeddings, faceted by
                              condition × reward structure, points
                              colored by REWARD. Visual confirmation.
  fig3_pca_colored_by_color.png : same projection, colored by COLOR.
                              Pairs with fig2; shows that
                              valence_coupled "loses" the color axis
                              while sensory "loses" the reward axis.
  fig4_pareto.png           : per-cell scatter of (color_gap,
                              reward_gap). Conditions occupy different
                              quadrants.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

FIG_DIR = ROOT / "papers" / "valence_object_formation" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

COND_COLORS = {
    "reconstruct": "#1f77b4",
    "sensory": "#ff7f0e",
    "valence_coupled": "#2ca02c",
}
COND_LABEL = {
    "reconstruct": "reconstruct (autoencoder)",
    "sensory": "sensory (predict color)",
    "valence_coupled": "valence-coupled (predict optimal action)",
}


def pca_2d(X):
    Xc = X - X.mean(axis=0, keepdims=True)
    U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
    return Xc @ Vt[:2].T


def main() -> int:
    data = json.loads(
        (ROOT / "artifacts" / "valence_object_formation" / "sweep_v1.json").read_text()
    )
    results = data["results"]
    conditions = data["manifest"]["conditions"]
    reward_structures = data["manifest"]["reward_structures"]

    # Group by (condition,) for axis-dominance figure
    by_cond = defaultdict(list)
    for r in results:
        by_cond[r["condition"]].append(r)

    # ============ Figure 1: axis dominance bars ============
    fig, ax = plt.subplots(figsize=(11, 5.5))
    axes_keys = [("color_gap", "color"), ("label_gap", "label"), ("reward_gap", "reward")]
    x = np.arange(len(axes_keys))
    w = 0.27
    for i, cond in enumerate(conditions):
        cells = by_cond[cond]
        means = []
        stds = []
        for key, _ in axes_keys:
            vals = [r[key] for r in cells]
            means.append(np.mean(vals))
            stds.append(np.std(vals))
        ax.bar(
            x + (i - 1) * w, means, w, yerr=stds,
            color=COND_COLORS[cond], alpha=0.92,
            label=COND_LABEL[cond],
            edgecolor="black", linewidth=0.5,
        )
        for j, m in enumerate(means):
            ax.text(
                x[j] + (i - 1) * w, m + 0.005 if m >= 0 else m - 0.025,
                f"{m:+.3f}", ha="center", fontsize=8,
                fontweight="bold" if (i == 2 and j == 2) else "normal",
            )
    ax.set_xticks(x)
    ax.set_xticklabels(["color axis", "label axis", "reward axis"], fontsize=11)
    ax.set_ylabel("Cluster gap (same − diff centered cosine)", fontsize=11)
    ax.axhline(0, color="black", linewidth=0.5)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    ax.legend(loc="upper right", fontsize=10)
    ax.set_title(
        "Which axis does the encoder cluster by? "
        "(mean ± std over 3 seeds × 2 reward structures = 6 cells/condition)",
        fontsize=12,
    )
    fig.tight_layout()
    out = FIG_DIR / "fig1_axis_dominance.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ============ Figure 2 & 3: PCA projections ============
    # Pick one seed (smallest) for visualization. Faceted by condition × rs.
    target_seed = min(r["seed"] for r in results)
    cells_by_key = {(r["condition"], r["reward_structure"]): r
                    for r in results if r["seed"] == target_seed}

    for color_by, fname, title_suffix in [
        ("reward", "fig2_pca_projection.png",
         "colored by REWARD — valence-coupled encoder separates rewards"),
        ("color", "fig3_pca_colored_by_color.png",
         "colored by COLOR — reconstruct/sensory encoders separate colors"),
    ]:
        fig, axes = plt.subplots(len(reward_structures), len(conditions),
                                 figsize=(4.2 * len(conditions),
                                          3.8 * len(reward_structures)))
        if len(reward_structures) == 1:
            axes = axes[None, :]
        if len(conditions) == 1:
            axes = axes[:, None]
        for ri, rs in enumerate(reward_structures):
            for ci, cond in enumerate(conditions):
                ax = axes[ri, ci]
                cell = cells_by_key.get((cond, rs))
                if cell is None:
                    ax.set_visible(False)
                    continue
                Z = np.array(cell["test_embeddings"])
                proj = pca_2d(Z)
                if color_by == "reward":
                    labels = np.array(cell["test_rewards"])
                    cmap = {-1: "#d62728", 1: "#2ca02c"}
                    legend_label = {-1: "−1 (poison)", 1: "+1 (food)"}
                else:
                    labels = np.array(cell["test_colors"])
                    cmap = {0: "#1f77b4", 1: "#ff7f0e", 2: "#9467bd", 3: "#8c564b"}
                    legend_label = {k: f"color {k}" for k in cmap}
                for v in np.unique(labels):
                    sel = labels == v
                    ax.scatter(
                        proj[sel, 0], proj[sel, 1],
                        s=14, alpha=0.55, color=cmap[v],
                        edgecolor="white", linewidth=0.3,
                        label=legend_label[v] if ri == 0 and ci == 0 else None,
                    )
                if ri == 0:
                    ax.set_title(COND_LABEL[cond], fontsize=10)
                if ci == 0:
                    ax.set_ylabel(f"{rs}\n\nPC 2", fontsize=10)
                else:
                    ax.set_ylabel("PC 2", fontsize=9)
                ax.set_xlabel("PC 1", fontsize=9)
                ax.set_xticks([])
                ax.set_yticks([])
        handles, lbls = axes[0, 0].get_legend_handles_labels()
        if handles:
            fig.legend(handles, lbls, loc="upper center",
                       bbox_to_anchor=(0.5, 1.04),
                       ncol=len(handles), fontsize=10)
        fig.suptitle(f"2D PCA of test embeddings, {title_suffix}",
                     fontsize=12, y=1.06)
        fig.tight_layout()
        out = FIG_DIR / fname
        fig.savefig(out, dpi=200, bbox_inches="tight")
        plt.close(fig)
        print(f"wrote {out}")

    # ============ Figure 4: per-cell (color, reward) scatter ============
    fig, ax = plt.subplots(figsize=(8, 7))
    for cond in conditions:
        cells = by_cond[cond]
        xs = [r["color_gap"] for r in cells]
        ys = [r["reward_gap"] for r in cells]
        ax.scatter(xs, ys, s=140, color=COND_COLORS[cond], alpha=0.9,
                   edgecolor="black", linewidth=0.7, marker="o",
                   label=COND_LABEL[cond])
        for x_, y_, r in zip(xs, ys, cells):
            ax.annotate(
                r["reward_structure"][:3],
                xy=(x_, y_), xytext=(3, 3), textcoords="offset points",
                fontsize=7, alpha=0.6,
            )
    # diagonal reference (color_gap == reward_gap)
    lim = 1.05
    ax.plot([-0.05, lim], [-0.05, lim], "k--", linewidth=0.5, alpha=0.4)
    ax.text(lim * 0.95, lim * 0.95, "y = x", fontsize=8, color="gray",
            ha="right", va="top")
    ax.axhline(0, color="black", linewidth=0.4)
    ax.axvline(0, color="black", linewidth=0.4)
    ax.set_xlabel("Color-axis cluster gap", fontsize=11)
    ax.set_ylabel("Reward-axis cluster gap", fontsize=11)
    ax.set_title(
        "Per-cell axis trade-off:\n"
        "valence-coupled cells live in the top, sensory/reconstruct on the right",
        fontsize=12,
    )
    ax.legend(loc="lower right", fontsize=9)
    ax.grid(linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig4_pareto.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ============ Emit summary stats ============
    summary = {}
    for cond in conditions:
        cells = by_cond[cond]
        summary[cond] = {
            "n_cells": len(cells),
            "color_gap_mean": float(np.mean([r["color_gap"] for r in cells])),
            "label_gap_mean": float(np.mean([r["label_gap"] for r in cells])),
            "reward_gap_mean": float(np.mean([r["reward_gap"] for r in cells])),
            "task_acc_mean": (
                float(np.mean([r["task_acc"] for r in cells if r["task_acc"] is not None]))
                if any(r["task_acc"] is not None for r in cells) else None
            ),
        }
    out_path = ROOT / "artifacts" / "valence_object_formation" / "summary_v1.json"
    out_path.write_text(json.dumps(summary, indent=2))
    print(f"\nsummary by condition:")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
