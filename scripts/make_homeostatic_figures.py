#!/usr/bin/env python3
"""Figures for Paper 7 — Homeostatic Object Formation.

Five figures:

  fig1_returns.png             : episode-return rolling mean over RL
                                 training, by condition.
  fig2_axis_dominance.png      : final cluster gaps by axis (color /
                                 label / reward) per condition.
  fig3_los_pretrained_vs_final.png : per-cell scatter of pretrained
                                 color_gap (before RL) vs final
                                 reward_gap (after RL). Frozen-encoder
                                 cells should plateau at the pretrained
                                 color axis; full-FT cells should
                                 reorganize.
  fig4_pca.png                 : 2D PCA of final embeddings, colored
                                 by REWARD. Side-by-side conditions.
  fig5_headline.png            : bar chart, final reward_gap by
                                 condition, with task return overlaid.
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

FIG_DIR = ROOT / "papers" / "homeostatic_objects" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

COND_COLORS = {
    "rl_from_scratch": "#2ca02c",
    "rl_after_reconstruct": "#1f77b4",
    "rl_after_sensory": "#ff7f0e",
    "rl_after_valence": "#17becf",
    "rl_frozen_reconstruct": "#9467bd",
    "rl_frozen_sensory": "#d62728",
    "rl_frozen_valence": "#bcbd22",
}
COND_LABEL = {
    "rl_from_scratch": "RL from scratch (max slack)",
    "rl_after_reconstruct": "RL after reconstruct pretrain",
    "rl_after_sensory": "RL after sensory pretrain",
    "rl_after_valence": "RL after valence pretrain",
    "rl_frozen_reconstruct": "RL with frozen reconstruct encoder",
    "rl_frozen_sensory": "RL with frozen sensory encoder",
    "rl_frozen_valence": "RL with frozen valence encoder",
}


def pca_2d(X):
    Xc = X - X.mean(axis=0, keepdims=True)
    _, _, Vt = np.linalg.svd(Xc, full_matrices=False)
    return Xc @ Vt[:2].T


def main() -> int:
    data = json.loads(
        (ROOT / "artifacts" / "homeostatic_objects" / "sweep_v3.json").read_text()
    )
    results = data["results"]
    conditions = data["manifest"]["conditions"]
    reward_structures = data["manifest"]["reward_structures"]
    n_episodes = data["manifest"]["n_episodes"]

    by_cond = defaultdict(list)
    for r in results:
        by_cond[r["condition"]].append(r)

    # ============ Figure 1: episode returns ============
    fig, axes = plt.subplots(1, len(reward_structures), figsize=(7 * len(reward_structures), 5))
    if len(reward_structures) == 1:
        axes = [axes]
    for ax_idx, rs in enumerate(reward_structures):
        ax = axes[ax_idx]
        for cond in conditions:
            cells = [r for r in by_cond[cond] if r["reward_structure"] == rs]
            if not cells:
                continue
            # Average rolling-mean curves across seeds
            curves = []
            for r in cells:
                returns = r["episode_returns"]
                # rolling window of 20
                w = 20
                rolling = [float(np.mean(returns[max(0, i - w + 1):i + 1]))
                           for i in range(len(returns))]
                curves.append(rolling)
            arr = np.array(curves)
            mean = arr.mean(axis=0)
            std = arr.std(axis=0)
            xs = np.arange(len(mean))
            ax.plot(xs, mean, color=COND_COLORS[cond], linewidth=2.0,
                    label=COND_LABEL[cond] if ax_idx == 0 else None)
            ax.fill_between(xs, mean - std, mean + std,
                            color=COND_COLORS[cond], alpha=0.15)
        ax.set_xlabel("Episode", fontsize=10)
        ax.set_ylabel("Steps survived (rolling mean over 20 episodes)", fontsize=10)
        ax.set_title(f"reward = {rs}", fontsize=11)
        ax.grid(linestyle=":", alpha=0.4)
        ax.axhline(50, color="gray", linewidth=0.5, linestyle=":")
        ax.text(n_episodes * 0.05, 51, "T_max = 50 (perfect survival)",
                fontsize=8, color="gray")
    fig.legend(loc="upper center", bbox_to_anchor=(0.5, 1.04), ncol=3, fontsize=9)
    fig.suptitle(
        "Episodic survival under homeostatic dynamics — energy E ∈ [0,1], "
        "decay 0.04/step, T_max = 50",
        fontsize=12, y=1.10,
    )
    fig.tight_layout()
    out = FIG_DIR / "fig1_returns.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ============ Figure 2: final cluster gaps by axis × condition ============
    fig, ax = plt.subplots(figsize=(13, 5.5))
    axes_keys = [("color", "color"), ("label", "label"), ("reward", "reward")]
    x = np.arange(len(axes_keys))
    w = 0.14
    for i, cond in enumerate(conditions):
        cells = by_cond[cond]
        means = []
        stds = []
        for key, _ in axes_keys:
            vals = [r["final_cluster_gaps"][key] for r in cells]
            means.append(np.mean(vals))
            stds.append(np.std(vals))
        offset = (i - (len(conditions) - 1) / 2) * w
        bars = ax.bar(
            x + offset, means, w * 0.92, yerr=stds,
            color=COND_COLORS[cond], alpha=0.92, label=COND_LABEL[cond],
            edgecolor="black", linewidth=0.4,
        )
        # value labels
        for j, (m, bar) in enumerate(zip(means, bars)):
            yt = m + 0.04 if m >= 0 else m - 0.10
            ax.text(bar.get_x() + bar.get_width() / 2, yt,
                    f"{m:+.2f}", ha="center", fontsize=7,
                    fontweight="bold" if (j == 2 and cond == "rl_from_scratch")
                    else "normal")
    ax.set_xticks(x)
    ax.set_xticklabels(["color axis", "label axis", "reward axis"], fontsize=11)
    ax.set_ylabel("Final cluster gap (same − diff centered cosine)", fontsize=11)
    ax.axhline(0, color="black", linewidth=0.5)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    ax.legend(loc="upper left", fontsize=8.5)
    ax.set_title(
        "Final encoder geometry across Law-of-the-Stack conditions "
        "(mean ± std, 3 seeds × 2 reward structures = 6 cells / condition)",
        fontsize=12,
    )
    fig.tight_layout()
    out = FIG_DIR / "fig2_axis_dominance.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ============ Figure 3: LoS pretrained-vs-final scatter ============
    fig, ax = plt.subplots(figsize=(9, 7))
    for r in results:
        cond = r["condition"]
        if "after" not in cond and "frozen" not in cond:
            continue
        pre = r.get("pretrained_cluster_gaps")
        if pre is None:
            continue
        ax.scatter(
            pre["color"], r["final_cluster_gaps"]["reward"],
            s=180, color=COND_COLORS[cond], alpha=0.9,
            edgecolor="black", linewidth=0.7,
            label=COND_LABEL[cond] if r["seed"] == 20260610 and r["reward_structure"] == "xor" else None,
        )
        ax.annotate(
            r["reward_structure"][:3], xy=(pre["color"], r["final_cluster_gaps"]["reward"]),
            xytext=(4, 4), textcoords="offset points", fontsize=7, alpha=0.7,
        )
    # Also plot from-scratch cells horizontally at color_gap = 0
    for r in by_cond["rl_from_scratch"]:
        ax.scatter(
            0.0, r["final_cluster_gaps"]["reward"],
            s=180, color=COND_COLORS["rl_from_scratch"], alpha=0.9,
            edgecolor="black", linewidth=0.7,
            marker="*",
            label=COND_LABEL["rl_from_scratch"] if r["seed"] == 20260610 and r["reward_structure"] == "xor" else None,
        )
    ax.axhline(0, color="black", linewidth=0.4)
    ax.axvline(0, color="black", linewidth=0.4)
    ax.set_xlabel("Pretrained encoder's color_gap (before RL)", fontsize=11)
    ax.set_ylabel("Final encoder's reward_gap (after RL)", fontsize=11)
    ax.set_title(
        "Law of the Stack: pretrained representation caps reward-axis reorganization\n"
        "(higher pretrained color structure → lower achievable reward structure under frozen-encoder RL)",
        fontsize=11,
    )
    ax.legend(loc="upper right", fontsize=8.5)
    ax.grid(linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig3_los_pretrained_vs_final.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ============ Figure 4: PCA, colored by reward ============
    target_seed = min(r["seed"] for r in results)
    target_rs = "xor"
    cells_for_pca = [r for r in results
                     if r["seed"] == target_seed and r["reward_structure"] == target_rs]
    fig, axes = plt.subplots(1, len(cells_for_pca),
                             figsize=(3.2 * len(cells_for_pca), 4))
    if len(cells_for_pca) == 1:
        axes = [axes]
    for ax_idx, r in enumerate(sorted(cells_for_pca,
                                       key=lambda x: conditions.index(x["condition"]))):
        ax = axes[ax_idx]
        Z = np.array(r["test_embeddings"])
        proj = pca_2d(Z)
        rewards = np.array(r["test_rewards"])
        cmap = {-1: "#d62728", 1: "#2ca02c"}
        legend = {-1: "−1 (poison)", 1: "+1 (food)"}
        for v in np.unique(rewards):
            sel = rewards == v
            ax.scatter(
                proj[sel, 0], proj[sel, 1], s=15, alpha=0.55,
                color=cmap[v], edgecolor="white", linewidth=0.3,
                label=legend[v] if ax_idx == 0 else None,
            )
        ax.set_title(COND_LABEL[r["condition"]].replace("RL ", ""),
                     fontsize=9)
        ax.set_xticks([]); ax.set_yticks([])
        ax.set_xlabel("PC 1", fontsize=9); ax.set_ylabel("PC 2", fontsize=9)
    handles, lbls = axes[0].get_legend_handles_labels()
    fig.legend(handles, lbls, loc="upper center",
               bbox_to_anchor=(0.5, 1.04), ncol=2, fontsize=10)
    fig.suptitle(
        f"2D PCA of test embeddings (xor, seed {target_seed}), colored by REWARD",
        fontsize=11, y=1.07,
    )
    fig.tight_layout()
    out = FIG_DIR / "fig4_pca.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ============ Figure 5: headline — reward gap vs return ============
    fig, ax = plt.subplots(figsize=(11, 5.5))
    cond_means_reward = []
    cond_stds_reward = []
    cond_means_return = []
    cond_stds_return = []
    for cond in conditions:
        cells = by_cond[cond]
        rwds = [r["final_cluster_gaps"]["reward"] for r in cells]
        rets = [r["final_mean_return"] for r in cells]
        cond_means_reward.append(np.mean(rwds))
        cond_stds_reward.append(np.std(rwds))
        cond_means_return.append(np.mean(rets))
        cond_stds_return.append(np.std(rets))

    x = np.arange(len(conditions))
    w = 0.38
    b1 = ax.bar(x - w / 2, cond_means_reward, w, yerr=cond_stds_reward,
                color=[COND_COLORS[c] for c in conditions], alpha=0.92,
                edgecolor="black", linewidth=0.5,
                label="Final reward-axis cluster gap")
    for i, m in enumerate(cond_means_reward):
        ax.text(x[i] - w / 2, m + 0.03, f"{m:+.2f}", ha="center",
                fontsize=9, fontweight="bold")

    ax2 = ax.twinx()
    b2 = ax2.bar(x + w / 2, cond_means_return, w, yerr=cond_stds_return,
                 color="gray", alpha=0.55, edgecolor="black", linewidth=0.5,
                 label="Final mean episode return (steps)")
    for i, m in enumerate(cond_means_return):
        ax2.text(x[i] + w / 2, m + 0.5, f"{m:.1f}", ha="center", fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels([COND_LABEL[c].replace(" (", "\n(") for c in conditions],
                       fontsize=8.5)
    ax.set_ylabel("Reward-axis cluster gap (filled bars)", fontsize=10)
    ax2.set_ylabel("Mean episode return (gray bars)", fontsize=10)
    ax.axhline(0, color="black", linewidth=0.4)
    ax2.axhline(50, color="gray", linewidth=0.4, linestyle=":")
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    ax.set_title(
        "Headline: representational reorganization (reward axis) AND task return,\n"
        "by Law-of-the-Stack condition",
        fontsize=12,
    )
    fig.tight_layout()
    out = FIG_DIR / "fig5_headline.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ============ Emit summary stats ============
    summary = {}
    for cond in conditions:
        cells = by_cond[cond]
        summary[cond] = dict(
            n_cells=len(cells),
            mean_color_gap=float(np.mean([r["final_cluster_gaps"]["color"] for r in cells])),
            mean_label_gap=float(np.mean([r["final_cluster_gaps"]["label"] for r in cells])),
            mean_reward_gap=float(np.mean([r["final_cluster_gaps"]["reward"] for r in cells])),
            mean_episode_return=float(np.mean([r["final_mean_return"] for r in cells])),
        )
    out_path = ROOT / "artifacts" / "homeostatic_objects" / "summary_v1.json"
    out_path.write_text(json.dumps(summary, indent=2))
    print(f"\nsummary by condition:")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
