#!/usr/bin/env python3
"""Figures for Paper 9 — Two Bottlenecks.

Four figures:

  fig1_return_by_condition.png : eval mean return per condition × env,
                                 with reward_gap overlay. Headline: if
                                 delta_e_then_freeze_sup_policy reaches
                                 high return, the encoder bottleneck is
                                 real and the ΔE aux solves it.
  fig2_pre_vs_final_rg.png     : per-cell scatter of pre-policy
                                 reward_gap vs final reward_gap, by
                                 condition. Shows which conditions
                                 preserve the encoder's pretrained
                                 axis.
  fig3_decoupling_landscape.png : 2D (encoder_quality, policy_quality)
                                 plot per condition × env.
  fig4_headline_grid.png        : single grid of (condition × env) ->
                                 final return + final rg.
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

FIG_DIR = ROOT / "papers" / "two_bottlenecks" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

COND_COLORS = {
    "delta_e_then_freeze_sup_policy": "#2ca02c",
    "delta_e_then_freeze_rl_policy": "#17becf",
    "valence_then_freeze_sup_policy": "#9467bd",
    "random_freeze_sup_policy": "#7f7f7f",
    "scratch_joint_sup_policy": "#1f77b4",
    "sensory_then_freeze_sup_policy": "#d62728",
}
COND_LABEL = {
    "delta_e_then_freeze_sup_policy": "ΔE-aux encoder + supervised policy (HEADLINE)",
    "delta_e_then_freeze_rl_policy": "ΔE-aux encoder + REINFORCE policy",
    "valence_then_freeze_sup_policy": "Supervised valence encoder + supervised policy (upper bound)",
    "random_freeze_sup_policy": "Random encoder + supervised policy (lower bound)",
    "scratch_joint_sup_policy": "Joint encoder+policy supervised (Paper 6 baseline)",
    "sensory_then_freeze_sup_policy": "Sensory encoder + supervised policy (proxy control)",
}
ENV_LABEL = {"xor": "XOR", "additive_thresh": "additive_thresh"}


def main() -> int:
    data = json.loads(
        (ROOT / "artifacts" / "two_bottlenecks" / "sweep_v1.json").read_text()
    )
    results = data["results"]
    conditions = data["manifest"]["conditions"]
    envs = data["manifest"]["envs"]

    by_key = defaultdict(list)
    for r in results:
        by_key[(r["condition"], r["env"])].append(r)

    # ============ Figure 1: return per condition × env ============
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.5), sharey=True)
    for ax_idx, env in enumerate(envs):
        ax = axes[ax_idx]
        cond_means_return = []
        cond_stds_return = []
        cond_means_rg = []
        cond_stds_rg = []
        for cond in conditions:
            cells = by_key.get((cond, env), [])
            rets = [r["eval_mean_return"] for r in cells]
            rgs = [r["final_cluster_gaps"]["reward"] for r in cells]
            cond_means_return.append(np.mean(rets) if rets else 0)
            cond_stds_return.append(np.std(rets) if len(rets) > 1 else 0)
            cond_means_rg.append(np.mean(rgs) if rgs else 0)
            cond_stds_rg.append(np.std(rgs) if len(rgs) > 1 else 0)
        x = np.arange(len(conditions))
        w = 0.36
        b1 = ax.bar(x - w/2, cond_means_return, w, yerr=cond_stds_return,
                    color=[COND_COLORS[c] for c in conditions], alpha=0.92,
                    edgecolor="black", linewidth=0.5,
                    label="Eval mean return")
        for i, m in enumerate(cond_means_return):
            ax.text(x[i] - w/2, m + 1, f"{m:.1f}",
                    ha="center", fontsize=8, fontweight="bold")
        ax2 = ax.twinx()
        b2 = ax2.bar(x + w/2, cond_means_rg, w, yerr=cond_stds_rg,
                     color=[COND_COLORS[c] for c in conditions], alpha=0.45,
                     edgecolor="black", linewidth=0.5, hatch="//",
                     label="Final reward_gap")
        for i, m in enumerate(cond_means_rg):
            ax2.text(x[i] + w/2, m + 0.05 if m >= 0 else m - 0.12,
                     f"{m:+.2f}", ha="center", fontsize=8)
        ax.set_xticks(x)
        ax.set_xticklabels([COND_LABEL[c].split(" (")[0].replace(" + ", "\n+ ")
                            for c in conditions],
                           fontsize=7.5, rotation=0)
        ax.set_ylabel("Eval mean return (filled bars)", fontsize=10)
        ax2.set_ylabel("Final reward_gap (hatched bars)", fontsize=10)
        ax.axhline(50, color="gray", linewidth=0.4, linestyle=":")
        ax.set_ylim(0, 55)
        ax2.set_ylim(-0.5, 2.5)
        ax.set_title(f"reward = {env}", fontsize=11)
        ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.suptitle(
        "Two-bottlenecks: eval return + final reward_gap by condition × env\n"
        "(headline: does ΔE-aux encoder + supervised policy match the supervised upper bound?)",
        fontsize=12, y=1.02,
    )
    fig.tight_layout()
    out = FIG_DIR / "fig1_return_by_condition.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ============ Figure 2: pre vs final reward_gap ============
    fig, axes = plt.subplots(1, 2, figsize=(13, 6), sharey=True)
    for ax_idx, env in enumerate(envs):
        ax = axes[ax_idx]
        for cond in conditions:
            cells = by_key.get((cond, env), [])
            if not cells:
                continue
            xs = [r["pretrained_cluster_gaps"]["reward"] for r in cells]
            ys = [r["final_cluster_gaps"]["reward"] for r in cells]
            ax.scatter(xs, ys, s=140, color=COND_COLORS[cond], alpha=0.9,
                       edgecolor="black", linewidth=0.6,
                       label=COND_LABEL[cond] if ax_idx == 0 else None)
        ax.plot([-0.5, 2.5], [-0.5, 2.5], "k--", linewidth=0.4, alpha=0.4)
        ax.axhline(0, color="black", linewidth=0.4)
        ax.axvline(0, color="black", linewidth=0.4)
        ax.set_xlabel("Pre-policy-training reward_gap", fontsize=10)
        if ax_idx == 0:
            ax.set_ylabel("Post-policy-training reward_gap", fontsize=10)
        ax.set_title(f"reward = {env}", fontsize=11)
        ax.grid(linestyle=":", alpha=0.4)
    handles, lbls = axes[0].get_legend_handles_labels()
    fig.legend(handles, lbls, loc="upper center",
               bbox_to_anchor=(0.5, 1.06), ncol=3, fontsize=8)
    fig.suptitle(
        "Encoder geometry stability: does the policy-training stage preserve "
        "the encoder's pretrained reward axis?",
        fontsize=12, y=1.12,
    )
    fig.tight_layout()
    out = FIG_DIR / "fig2_pre_vs_final_rg.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ============ Figure 3: decoupling landscape ============
    fig, ax = plt.subplots(figsize=(10, 7))
    for cond in conditions:
        for env in envs:
            cells = by_key.get((cond, env), [])
            if not cells:
                continue
            xs = [r["final_cluster_gaps"]["reward"] for r in cells]
            ys = [r["eval_mean_return"] for r in cells]
            marker = "o" if env == "xor" else "s"
            ax.scatter(xs, ys, s=150, color=COND_COLORS[cond], alpha=0.85,
                       edgecolor="black", linewidth=0.7, marker=marker)
    # ideal point
    ax.scatter([1.9], [50], s=400, color="gold", alpha=0.7, marker="*",
               edgecolor="black", linewidth=1.0, zorder=2,
               label="Ideal: high rg, high return")
    ax.axhline(50, color="gray", linewidth=0.4, linestyle=":")
    ax.axvline(0, color="black", linewidth=0.4)
    ax.set_xlabel("Final reward_gap (encoder organized by reward axis)", fontsize=11)
    ax.set_ylabel("Eval mean return (policy competent)", fontsize=11)
    ax.set_title(
        "Decoupling landscape: (encoder quality, policy quality) per cell\n"
        "Circles = XOR, squares = additive_thresh",
        fontsize=12,
    )
    # build legend manually
    from matplotlib.lines import Line2D
    handles = [Line2D([], [], marker="o", color="w",
                       markerfacecolor=COND_COLORS[c], markersize=10,
                       markeredgecolor="black", label=COND_LABEL[c].split(" (")[0])
               for c in conditions]
    ax.legend(handles=handles, loc="lower right", fontsize=8.5)
    ax.grid(linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig3_decoupling_landscape.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ============ Figure 4: headline grid ============
    fig, ax = plt.subplots(figsize=(11, 5.5))
    x = np.arange(len(conditions))
    w = 0.36
    for env_idx, env in enumerate(envs):
        means = []
        for cond in conditions:
            cells = by_key.get((cond, env), [])
            rets = [r["eval_mean_return"] for r in cells]
            means.append(np.mean(rets) if rets else 0)
        offset = (env_idx - 0.5) * w
        c = "#2ca02c" if env == "xor" else "#1f77b4"
        ax.bar(x + offset, means, w, color=c, alpha=0.85,
               label=ENV_LABEL[env], edgecolor="black", linewidth=0.4)
        for i, m in enumerate(means):
            ax.text(x[i] + offset, m + 1.0, f"{m:.1f}",
                    ha="center", fontsize=8, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([COND_LABEL[c].split(" (")[0].replace(" + ", "\n+ ")
                        for c in conditions], fontsize=8)
    ax.set_ylabel("Eval mean return", fontsize=11)
    ax.axhline(50, color="gray", linewidth=0.4, linestyle=":")
    ax.set_ylim(0, 55)
    ax.legend(loc="upper right", fontsize=9)
    ax.set_title(
        "Headline: eval mean return per condition × reward env",
        fontsize=12,
    )
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig4_headline_grid.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # Summary stats
    summary = {}
    for cond in conditions:
        per_env = {}
        for env in envs:
            cells = by_key.get((cond, env), [])
            if not cells:
                continue
            per_env[env] = dict(
                n_cells=len(cells),
                mean_pre_rg=float(np.mean([r["pretrained_cluster_gaps"]["reward"] for r in cells])),
                mean_final_rg=float(np.mean([r["final_cluster_gaps"]["reward"] for r in cells])),
                mean_return=float(np.mean([r["eval_mean_return"] for r in cells])),
            )
        summary[cond] = per_env
    out_path = ROOT / "artifacts" / "two_bottlenecks" / "summary_v1.json"
    out_path.write_text(json.dumps(summary, indent=2))
    print(f"\nsummary:")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
