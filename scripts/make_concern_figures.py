#!/usr/bin/env python3
"""Figures for Paper 8 — Concern Bootstrap.

Five figures:

  fig1_return_trajectories.png : episode-return curves per condition,
                                 faceted by env. Vertical line at the
                                 ecological shift for add_to_xor_shift.
  fig2_reward_gap_by_env.png   : final reward_gap by condition × env.
                                 The headline: does delta_e_aux reach
                                 ≥+1.0 on xor_stable without supervised
                                 labels?
  fig3_adaptation_after_shift.png : adaptation speed in the second
                                 phase of add_to_xor_shift (post-shift
                                 rolling-mean returns).
  fig4_pca_per_condition.png   : 2D PCA of test embeddings on
                                 xor_stable, colored by reward.
  fig5_headline.png            : per-condition (reward_gap, return)
                                 paired bars across envs.
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

FIG_DIR = ROOT / "papers" / "concern_bootstrap" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

COND_COLORS = {
    "rl_scratch": "#7f7f7f",
    "rl_delta_e_aux": "#2ca02c",
    "rl_curriculum": "#17becf",
    "rl_after_valence": "#9467bd",
    "rl_frozen_sensory": "#d62728",
}
COND_LABEL = {
    "rl_scratch": "RL from scratch",
    "rl_delta_e_aux": "RL + ΔE auxiliary (headline)",
    "rl_curriculum": "RL with additive→XOR curriculum",
    "rl_after_valence": "RL after supervised valence pretrain",
    "rl_frozen_sensory": "RL with frozen sensory encoder",
}
ENV_LABEL = {
    "xor_stable": "XOR (stable)",
    "additive_stable": "additive (stable)",
    "add_to_xor_shift": "additive → XOR (eco shift)",
}


def pca_2d(X):
    Xc = X - X.mean(axis=0, keepdims=True)
    _, _, Vt = np.linalg.svd(Xc, full_matrices=False)
    return Xc @ Vt[:2].T


def main() -> int:
    data = json.loads(
        (ROOT / "artifacts" / "concern_bootstrap" / "sweep_v1.json").read_text()
    )
    results = data["results"]
    conditions = data["manifest"]["conditions"]
    envs = data["manifest"]["envs"]
    n_episodes = data["manifest"]["n_episodes"]

    by_key = defaultdict(list)
    for r in results:
        by_key[(r["condition"], r["env_config"])].append(r)

    # ============ Figure 1: episode returns per env ============
    fig, axes = plt.subplots(1, len(envs), figsize=(6 * len(envs), 5),
                             sharey=True)
    for ax_idx, env in enumerate(envs):
        ax = axes[ax_idx]
        for cond in conditions:
            cells = by_key.get((cond, env), [])
            if not cells:
                continue
            curves = []
            for r in cells:
                returns = r["episode_returns"]
                w = 30
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
        if env == "add_to_xor_shift":
            ax.axvline(n_episodes // 2, color="black", linewidth=0.8,
                       linestyle="--", alpha=0.7)
            ax.text(n_episodes // 2 + 50, 5, "← shift", fontsize=9,
                    color="black")
        ax.set_xlabel("Episode", fontsize=10)
        if ax_idx == 0:
            ax.set_ylabel("Steps survived (rolling mean over 30 eps)", fontsize=10)
        ax.set_title(ENV_LABEL[env], fontsize=11)
        ax.set_ylim(0, 55)
        ax.axhline(50, color="gray", linewidth=0.4, linestyle=":")
        ax.grid(linestyle=":", alpha=0.4)
    fig.legend(loc="upper center", bbox_to_anchor=(0.5, 1.04), ncol=3, fontsize=9)
    fig.suptitle(
        "Episode return trajectories under homeostatic RL (E ∈ [0,1], decay 0.04/step, T_max = 50)",
        fontsize=12, y=1.10,
    )
    fig.tight_layout()
    out = FIG_DIR / "fig1_return_trajectories.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ============ Figure 2: final reward_gap by condition × env ============
    fig, ax = plt.subplots(figsize=(13, 5.5))
    x = np.arange(len(envs))
    w = 0.16
    for i, cond in enumerate(conditions):
        means = []
        stds = []
        for env in envs:
            cells = by_key.get((cond, env), [])
            if not cells:
                means.append(0); stds.append(0); continue
            vals = [r["final_cluster_gaps"]["reward"] for r in cells]
            means.append(np.mean(vals)); stds.append(np.std(vals))
        offset = (i - (len(conditions) - 1) / 2) * w
        bars = ax.bar(
            x + offset, means, w * 0.92, yerr=stds,
            color=COND_COLORS[cond], alpha=0.92, label=COND_LABEL[cond],
            edgecolor="black", linewidth=0.4,
        )
        for j, m in enumerate(means):
            yt = m + 0.04 if m >= 0 else m - 0.10
            ax.text(x[j] + offset, yt, f"{m:+.2f}",
                    ha="center", fontsize=7.5)
    ax.set_xticks(x)
    ax.set_xticklabels([ENV_LABEL[e] for e in envs], fontsize=10)
    ax.set_ylabel("Final reward-axis cluster gap", fontsize=11)
    ax.axhline(0, color="black", linewidth=0.5)
    ax.axhline(1.0, color="gray", linewidth=0.5, linestyle=":",
               label="self-organization gate")
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    ax.legend(loc="upper right", fontsize=8.5)
    ax.set_title(
        "Final reward-axis cluster gap by condition × env (mean ± std, 3 seeds)\n"
        "Self-organization gate: ΔE auxiliary reaches +1.0 on xor_stable WITHOUT supervised labels",
        fontsize=12,
    )
    fig.tight_layout()
    out = FIG_DIR / "fig2_reward_gap_by_env.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ============ Figure 3: adaptation after shift ============
    fig, ax = plt.subplots(figsize=(11, 5.5))
    env = "add_to_xor_shift"
    shift = n_episodes // 2
    for cond in conditions:
        cells = by_key.get((cond, env), [])
        if not cells:
            continue
        curves = []
        for r in cells:
            returns = r["episode_returns"]
            # take post-shift window
            post = returns[shift:]
            w = 30
            rolling = [float(np.mean(post[max(0, i - w + 1):i + 1]))
                       for i in range(len(post))]
            curves.append(rolling)
        arr = np.array(curves)
        mean = arr.mean(axis=0)
        std = arr.std(axis=0)
        xs = np.arange(len(mean))
        ax.plot(xs, mean, color=COND_COLORS[cond], linewidth=2.0,
                label=COND_LABEL[cond])
        ax.fill_between(xs, mean - std, mean + std,
                        color=COND_COLORS[cond], alpha=0.15)
    ax.set_xlabel("Episodes after ecological shift", fontsize=11)
    ax.set_ylabel("Post-shift steps survived (rolling mean over 30)", fontsize=11)
    ax.set_title(
        "Adaptation after the additive → XOR ecological shift "
        "(reward function changed at episode 1500)",
        fontsize=12,
    )
    ax.axhline(50, color="gray", linewidth=0.4, linestyle=":")
    ax.set_ylim(0, 55)
    ax.grid(linestyle=":", alpha=0.4)
    ax.legend(loc="upper right", fontsize=9)
    fig.tight_layout()
    out = FIG_DIR / "fig3_adaptation_after_shift.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ============ Figure 4: PCA per condition on xor_stable ============
    target_env = "xor_stable"
    target_seed = min(r["seed"] for r in results)
    cells_for_pca = [r for r in results
                     if r["env_config"] == target_env and r["seed"] == target_seed]
    cells_for_pca.sort(key=lambda r: conditions.index(r["condition"]))
    fig, axes = plt.subplots(1, len(cells_for_pca),
                             figsize=(3.2 * len(cells_for_pca), 4))
    if len(cells_for_pca) == 1:
        axes = [axes]
    for ax_idx, r in enumerate(cells_for_pca):
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
        ax.set_title(COND_LABEL[r["condition"]].replace(" (headline)", ""),
                     fontsize=9)
        ax.set_xticks([]); ax.set_yticks([])
    handles, lbls = axes[0].get_legend_handles_labels()
    fig.legend(handles, lbls, loc="upper center",
               bbox_to_anchor=(0.5, 1.04), ncol=2, fontsize=10)
    fig.suptitle(
        f"2D PCA of test embeddings on xor_stable (seed {target_seed}), "
        f"colored by reward",
        fontsize=11, y=1.06,
    )
    fig.tight_layout()
    out = FIG_DIR / "fig4_pca_per_condition.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ============ Figure 5: headline summary ============
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.5))

    # Left: reward gap per condition × env
    ax = axes[0]
    x = np.arange(len(envs))
    w = 0.16
    for i, cond in enumerate(conditions):
        means = []
        for env in envs:
            cells = by_key.get((cond, env), [])
            vals = [r["final_cluster_gaps"]["reward"] for r in cells]
            means.append(np.mean(vals) if vals else 0)
        offset = (i - (len(conditions) - 1) / 2) * w
        ax.bar(x + offset, means, w * 0.92, color=COND_COLORS[cond],
               alpha=0.92, label=COND_LABEL[cond], edgecolor="black",
               linewidth=0.4)
    ax.set_xticks(x)
    ax.set_xticklabels([ENV_LABEL[e] for e in envs], fontsize=9)
    ax.set_ylabel("Final reward-axis cluster gap", fontsize=10)
    ax.axhline(0, color="black", linewidth=0.5)
    ax.axhline(1.0, color="gray", linewidth=0.5, linestyle=":")
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    ax.set_title("Representation: final reward_gap", fontsize=11)

    # Right: episode return per condition × env
    ax = axes[1]
    for i, cond in enumerate(conditions):
        means = []
        for env in envs:
            cells = by_key.get((cond, env), [])
            vals = [r["final_mean_return"] for r in cells]
            means.append(np.mean(vals) if vals else 0)
        offset = (i - (len(conditions) - 1) / 2) * w
        ax.bar(x + offset, means, w * 0.92, color=COND_COLORS[cond],
               alpha=0.92, label=COND_LABEL[cond], edgecolor="black",
               linewidth=0.4)
    ax.set_xticks(x)
    ax.set_xticklabels([ENV_LABEL[e] for e in envs], fontsize=9)
    ax.set_ylabel("Final mean episode return", fontsize=10)
    ax.axhline(50, color="gray", linewidth=0.4, linestyle=":")
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    ax.legend(loc="upper left", fontsize=8.5)
    ax.set_title("Competence: final episode return", fontsize=11)
    fig.suptitle(
        "Concern Bootstrap headline: ΔE auxiliary develops valence geometry "
        "self-organized from viability interaction",
        fontsize=12, y=1.02,
    )
    fig.tight_layout()
    out = FIG_DIR / "fig5_headline.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ============ Summary stats ============
    summary = {}
    for cond in conditions:
        per_env = {}
        for env in envs:
            cells = by_key.get((cond, env), [])
            if not cells:
                continue
            per_env[env] = dict(
                n_cells=len(cells),
                mean_reward_gap=float(np.mean([r["final_cluster_gaps"]["reward"] for r in cells])),
                mean_color_gap=float(np.mean([r["final_cluster_gaps"]["color"] for r in cells])),
                mean_label_gap=float(np.mean([r["final_cluster_gaps"]["label"] for r in cells])),
                mean_return=float(np.mean([r["final_mean_return"] for r in cells])),
            )
        summary[cond] = per_env
    out_path = ROOT / "artifacts" / "concern_bootstrap" / "summary_v1.json"
    out_path.write_text(json.dumps(summary, indent=2))
    print(f"\nsummary by condition × env:")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
