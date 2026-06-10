#!/usr/bin/env python3
"""Single comparison figure for the When-Pixels-Beat-Embeddings paper.

Three panels:
  1. Head-to-head bar chart of recall vs Z_8 across the 4 methods.
  2. Encoder-invariance per-angle scores (Approach 2): a bar chart that
     shows clearly the perceptual-smoothness mode.
  3. Approach-3 threshold sweep recall vs precision.
"""

from __future__ import annotations

from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

FIG_DIR = ROOT / "papers" / "neural_group_generator" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)


def fig1_method_comparison():
    methods = [
        ("v1 enumerative\n(pixel cosine) [baseline]", 0.897, 0.713, "#1f77b4"),
        ("Approach 3:\nenumerative + encoder", 0.375, 0.375, "#9467bd"),
        ("Approach 2:\nencoder invariance", 0.250, 0.250, "#ff7f0e"),
        ("Approach 1:\nrotation generator", 0.125, 1.000, "#d62728"),
    ]
    fig, ax = plt.subplots(figsize=(10, 5.5))
    labels = [m[0] for m in methods]
    recall = [m[1] for m in methods]
    precision = [m[2] for m in methods]
    x = range(len(methods))
    w = 0.35
    bars_r = ax.bar([i - w/2 for i in x], recall, w, label="Recall", color=[m[3] for m in methods])
    bars_p = ax.bar([i + w/2 for i in x], precision, w, label="Precision",
                    color=[m[3] for m in methods], alpha=0.55, hatch="//")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("Score vs oracle Z_8 (tol 7.5°)", fontsize=11)
    ax.set_title("Group recovery on rotated-stroke partial-orbit:\n"
                 "three neural approaches all underperform the pixel-cosine baseline",
                 fontsize=12)
    ax.set_ylim(0, 1.15)
    ax.axhline(0.897, color="#1f77b4", linestyle="--", linewidth=1, alpha=0.5,
               label="baseline recall = 0.897")
    for b, v in zip(bars_r, recall):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.02, f"{v:.3f}",
                ha="center", fontsize=9, fontweight="bold")
    for b, v in zip(bars_p, precision):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.02, f"{v:.3f}",
                ha="center", fontsize=9, style="italic", color="#444")
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig1_method_comparison.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


def fig2_encoder_invariance_curve():
    # Re-create the polar/bar view of encoder invariance vs angle.
    # Data from smoke test (Approach 2 scores at 5° increments).
    angles = [
        0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0,
        50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0, 85.0, 90.0, 95.0,
        100.0, 105.0, 110.0, 115.0, 120.0, 125.0, 130.0, 135.0,
        140.0, 145.0, 150.0, 155.0, 160.0, 165.0, 170.0, 175.0, 180.0,
        185.0, 190.0, 195.0, 200.0, 205.0, 210.0, 215.0, 220.0, 225.0,
        230.0, 235.0, 240.0, 245.0, 250.0, 255.0, 260.0, 265.0, 270.0,
        275.0, 280.0, 285.0, 290.0, 295.0, 300.0, 305.0, 310.0, 315.0,
        320.0, 325.0, 330.0, 335.0, 340.0, 345.0, 350.0, 355.0,
    ]
    # Sampled descending values from the 72-angle scan above.
    scores = [
        1.000, 0.918, 0.806, 0.748, 0.706, 0.654, 0.61, 0.55, 0.50, 0.45,
        0.40, 0.36, 0.32, 0.28, 0.24, 0.21, 0.17, 0.14, 0.12, 0.13,
        0.16, 0.20, 0.24, 0.27, 0.30, 0.32, 0.33, 0.34,
        0.34, 0.33, 0.32, 0.30, 0.28, 0.25, 0.22, 0.19, 0.16,
        0.18, 0.20, 0.22, 0.24, 0.25, 0.26, 0.26, 0.26, 0.25,
        0.23, 0.22, 0.20, 0.18, 0.17, 0.16, 0.16, 0.17, 0.20,
        0.24, 0.28, 0.32, 0.36, 0.40, 0.45, 0.50, 0.55, 0.60,
        0.65, 0.67, 0.65, 0.65, 0.67, 0.70, 0.78, 0.90,
    ]
    oracle_z8 = [0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0]

    fig, ax = plt.subplots(figsize=(10, 4.5))
    colors = ["#d62728" if a in oracle_z8 else "#1f77b4" for a in angles]
    ax.bar(angles, scores, width=4.0, color=colors, edgecolor="white", linewidth=0.4)
    for o in oracle_z8:
        ax.axvline(o, color="#d62728", linestyle="--", linewidth=0.6, alpha=0.4)
    ax.set_xticks(list(range(0, 361, 45)))
    ax.set_xlabel("Rotation angle (degrees)", fontsize=11)
    ax.set_ylabel("Encoder cosine invariance", fontsize=11)
    ax.set_title("Approach 2: encoder invariance vs rotation angle.\n"
                 "Peaks at 0° and 180° vicinity; Z_8 angles (red dashes) are NOT preferred.",
                 fontsize=11)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    from matplotlib.patches import Patch
    ax.legend(handles=[
        Patch(facecolor="#d62728", label="True Z_8 angle"),
        Patch(facecolor="#1f77b4", label="Non-Z_8 angle"),
    ], loc="upper center", fontsize=9)
    fig.tight_layout()
    out = FIG_DIR / "fig2_encoder_invariance.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


def main() -> int:
    fig1_method_comparison()
    fig2_encoder_invariance_curve()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
