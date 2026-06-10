#!/usr/bin/env python3
"""Threshold-sweep figure for the rotated MNIST extension."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

FIG_DIR = ROOT / "papers" / "neural_group_generator" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)


def angle_match(a, b, tol=7.5):
    d = abs(a - b)
    d = min(d, 360 - d)
    return d < tol


def metrics(scores, thr, oracle):
    kept = [a for a, s in scores.items() if s >= thr]
    if 0.0 not in kept:
        kept = [0.0] + kept
    tp_r = sum(1 for o in oracle if any(angle_match(o, k) for k in kept))
    tp_p = sum(1 for k in kept if any(angle_match(o, k) for o in oracle))
    return len(kept), tp_r / len(oracle), tp_p / max(1, len(kept))


def main() -> int:
    data = json.loads(
        (ROOT / "artifacts" / "neural_group_generator" / "rotated_mnist_v1.json").read_text()
    )
    res = data["results"]
    oracle = set(k * (360.0 / 8) for k in range(8))

    methods = [
        ("v1 pixel cosine", res["v1_pixel_cosine"], "#1f77b4"),
        ("Approach 3: encoder enumerative", res["approach3_encoder_enumerative"], "#9467bd"),
        ("Approach 2: encoder invariance", res["approach2_encoder_invariance"], "#ff7f0e"),
    ]

    thresholds = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.8))

    for name, m, color in methods:
        scores = {float(k): v for k, v in m["scores"].items()}
        recalls, precisions = [], []
        for thr in thresholds:
            _, r, p = metrics(scores, thr, oracle)
            recalls.append(r)
            precisions.append(p)
        ax1.plot(thresholds, recalls, "o-", color=color, label=name, linewidth=2, markersize=6)
        ax2.plot(thresholds, precisions, "s-", color=color, label=name, linewidth=2, markersize=6)

    ax1.set_xlabel("Score threshold τ", fontsize=11)
    ax1.set_ylabel("Recall vs oracle Z_8", fontsize=11)
    ax1.set_title("Group recovery on rotated MNIST: recall vs threshold", fontsize=11)
    ax1.set_ylim(0, 1.1)
    ax1.legend(loc="lower left", fontsize=9)
    ax1.grid(linestyle=":", alpha=0.5)

    ax2.set_xlabel("Score threshold τ", fontsize=11)
    ax2.set_ylabel("Precision vs oracle Z_8", fontsize=11)
    ax2.set_title("Group recovery on rotated MNIST: precision vs threshold", fontsize=11)
    ax2.set_ylim(0, 1.1)
    ax2.legend(loc="upper left", fontsize=9)
    ax2.grid(linestyle=":", alpha=0.5)

    fig.tight_layout()
    out = FIG_DIR / "fig3_rotated_mnist_threshold_sweep.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
