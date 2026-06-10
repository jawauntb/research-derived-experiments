#!/usr/bin/env python3
"""Cluttered-MNIST sweep heatmap for When-Pixels-Beat-Embeddings §4.4."""

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

FIG_DIR = ROOT / "papers" / "neural_group_generator" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)


def main() -> int:
    data = json.loads(
        (ROOT / "artifacts" / "neural_group_generator" / "cluttered_mnist_v1.json").read_text()
    )
    results = data["results"]
    grids = sorted(set(r["manifest"]["grid_size"] for r in results))
    noises = sorted(set(r["manifest"]["noise_sigma"] for r in results))

    methods = [
        ("v1 pixel cosine", "v1_pixel_cosine", "#1f77b4"),
        ("Approach 3: encoder enumerative", "approach3_encoder_enumerative", "#9467bd"),
        ("Approach 2: encoder invariance", "approach2_encoder_invariance", "#ff7f0e"),
    ]

    # Build F1 matrices [n_grids, n_noises] per method.
    f1_matrices = {}
    recall_matrices = {}
    for label, key, _ in methods:
        f1 = np.zeros((len(grids), len(noises)))
        rec = np.zeros((len(grids), len(noises)))
        for r in results:
            g_idx = grids.index(r["manifest"]["grid_size"])
            n_idx = noises.index(r["manifest"]["noise_sigma"])
            best = r[key]["best"]  # (thr, kept, recall, precision, F1)
            f1[g_idx, n_idx] = best[4]
            rec[g_idx, n_idx] = best[2]
        f1_matrices[label] = f1
        recall_matrices[label] = rec

    fig, axes = plt.subplots(2, 3, figsize=(15, 7))
    # Row 0: F1 heatmaps
    for col, (label, _, _) in enumerate(methods):
        ax = axes[0, col]
        mat = f1_matrices[label]
        ax.imshow(mat, cmap="viridis", aspect="auto", vmin=0.45, vmax=0.55)
        ax.set_xticks(range(len(noises)))
        ax.set_xticklabels([f"σ={n:.2f}" for n in noises])
        ax.set_yticks(range(len(grids)))
        ax.set_yticklabels([f"{g}×{g}" for g in grids])
        ax.set_title(f"F1 — {label}", fontsize=10)
        for i in range(len(grids)):
            for j in range(len(noises)):
                ax.text(j, i, f"{mat[i, j]:.3f}", ha="center", va="center",
                        color="white" if mat[i, j] < 0.51 else "black", fontsize=10,
                        fontweight="bold")
        if col == 0:
            ax.set_ylabel("resolution", fontsize=10)
    # Row 1: Recall heatmaps
    for col, (label, _, _) in enumerate(methods):
        ax = axes[1, col]
        mat = recall_matrices[label]
        ax.imshow(mat, cmap="RdYlGn", aspect="auto", vmin=0.0, vmax=1.0)
        ax.set_xticks(range(len(noises)))
        ax.set_xticklabels([f"σ={n:.2f}" for n in noises])
        ax.set_yticks(range(len(grids)))
        ax.set_yticklabels([f"{g}×{g}" for g in grids])
        ax.set_title(f"Recall vs Z_8 — {label}", fontsize=10)
        for i in range(len(grids)):
            for j in range(len(noises)):
                ax.text(j, i, f"{mat[i, j]:.3f}", ha="center", va="center",
                        color="black", fontsize=10, fontweight="bold")
        if col == 0:
            ax.set_ylabel("resolution", fontsize=10)

    fig.suptitle(
        "Cluttered rotated-MNIST sweep: resolution × Gaussian noise σ\n"
        "Top row: best-F1 per method. Bottom row: best-F1 recall per method. "
        "Pixel cosine maintains recall = 1.0 across the entire sweep.",
        fontsize=11,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    out = FIG_DIR / "fig4_cluttered_mnist_sweep.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
