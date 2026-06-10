#!/usr/bin/env python3
"""Figures for the Passive→Active Geometry paper.

Three figures:
  fig1_cluster_tightening.png — same-orbit / diff-orbit cosines
    before vs after fine-tuning.
  fig2_intervention_curves.png — accuracy drop as a function of
    intervention strength α, with both ablation and wrong-direction
    perturbations for both phases.
  fig3_specific_effect.png — "specific paraphrase effect" =
    (paraphrase-axis drop) - (random-axis drop), passive vs active.
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
        (ROOT / "artifacts" / "passive_to_active" / "pythia_70m_v2.json").read_text()
    )
    p, a = data["passive"], data["active"]

    # Figure 1: cluster geometry
    fig, ax = plt.subplots(figsize=(8, 5))
    metrics = ["same-orbit cosine", "diff-orbit cosine", "gap (same − diff)"]
    passive_vals = [p["cluster_same_mean"], p["cluster_diff_mean"], p["cluster_gap"]]
    active_vals = [a["cluster_same_mean"], a["cluster_diff_mean"], a["cluster_gap"]]
    x = np.arange(len(metrics))
    w = 0.35
    ax.bar(x - w/2, passive_vals, w, label="passive (pretrained)", color="#1f77b4")
    ax.bar(x + w/2, active_vals, w, label="active (fine-tuned)", color="#2ca02c")
    for i, (pv, av) in enumerate(zip(passive_vals, active_vals)):
        ax.text(i - w/2, pv + 0.02, f"{pv:+.3f}", ha="center", fontsize=10)
        ax.text(i + w/2, av + 0.02, f"{av:+.3f}", ha="center", fontsize=10, fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels(metrics, fontsize=11)
    ax.set_ylabel("Centered cosine similarity", fontsize=11)
    ax.set_title("Cluster tightening under action coupling\n"
                 "(Pythia-70m, layer 5, paraphrase orbits)", fontsize=12)
    ax.axhline(0, color="black", linewidth=0.6)
    ax.legend(loc="upper right", fontsize=10)
    ax.grid(axis="y", linestyle=":", alpha=0.5)
    fig.tight_layout()
    out = FIG_DIR / "fig1_cluster_tightening.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # Figure 2: intervention curves (paraphrase ablate + wrong dir + random ablate)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    for ax, phase_name, phase_dict in [
        (axes[0], "passive (pretrained)", p),
        (axes[1], "active (fine-tuned)", a),
    ]:
        strengths = phase_dict["paraphrase_ablate"]["strengths"]
        ax.plot(strengths, phase_dict["paraphrase_ablate"]["drop"],
                "o-", color="#1f77b4", linewidth=2.2, markersize=7,
                label="ablate paraphrase axis")
        ax.plot(strengths, phase_dict["paraphrase_wrong_dir"]["drop"],
                "s-", color="#d62728", linewidth=2.2, markersize=7,
                label="push to wrong concept")
        ax.plot(strengths, phase_dict["random_ablate"]["drop"],
                "^--", color="#7f7f7f", linewidth=1.6, markersize=6,
                label="ablate random axis (control)")
        ax.set_xlabel("Intervention strength α", fontsize=11)
        ax.set_ylabel("Drop in classification accuracy", fontsize=11)
        ax.set_ylim(-0.05, 1.05)
        ax.set_title(phase_name, fontsize=12)
        ax.legend(loc="upper left", fontsize=9)
        ax.grid(linestyle=":", alpha=0.5)
    fig.suptitle("Causal interventions on the paraphrase axis (Pythia-70m layer 5)",
                 fontsize=13, y=1.02)
    fig.tight_layout()
    out = FIG_DIR / "fig2_intervention_curves.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # Figure 3: specific paraphrase effect at each α
    fig, ax = plt.subplots(figsize=(9, 5))
    strengths = p["paraphrase_ablate"]["strengths"]
    passive_specific = [
        p["paraphrase_ablate"]["drop"][i] - p["random_ablate"]["drop"][i]
        for i in range(len(strengths))
    ]
    active_specific = [
        a["paraphrase_ablate"]["drop"][i] - a["random_ablate"]["drop"][i]
        for i in range(len(strengths))
    ]
    ax.plot(strengths, passive_specific, "o-", color="#1f77b4",
            linewidth=2.2, markersize=7, label="passive (pretrained)")
    ax.plot(strengths, active_specific, "s-", color="#2ca02c",
            linewidth=2.2, markersize=7, label="active (fine-tuned)")
    ax.set_xlabel("Intervention strength α", fontsize=11)
    ax.set_ylabel(
        "Paraphrase-specific drop\n(= paraphrase-axis drop − random-axis drop)",
        fontsize=11,
    )
    ax.set_ylim(-0.1, 1.05)
    ax.set_title("Specific paraphrase-axis dependence grows 7× after action coupling\n"
                 "(controls for background subspace-removal effects)", fontsize=12)
    ax.legend(loc="upper left", fontsize=10)
    ax.grid(linestyle=":", alpha=0.5)
    ax.axhline(0, color="black", linewidth=0.6)
    # Annotate the headline ratio at α=5.0
    ax.annotate(
        f"+0.486 at α=5.0\n(active)",
        xy=(strengths[-1], active_specific[-1]),
        xytext=(strengths[-1] - 1.5, active_specific[-1] - 0.15),
        fontsize=10, color="#2ca02c", fontweight="bold",
        arrowprops=dict(arrowstyle="->", color="#2ca02c", lw=1.2),
    )
    ax.annotate(
        f"+0.069 at α=5.0\n(passive)",
        xy=(strengths[-1], passive_specific[-1]),
        xytext=(strengths[-1] - 1.5, passive_specific[-1] + 0.10),
        fontsize=10, color="#1f77b4",
        arrowprops=dict(arrowstyle="->", color="#1f77b4", lw=1.0),
    )
    fig.tight_layout()
    out = FIG_DIR / "fig3_specific_effect.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
