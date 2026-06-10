#!/usr/bin/env python3
"""Figures for Paper 10 — Planning from Concern.

Five figures:

  fig1_return_grid.png         : eval mean return per condition × env.
                                 Headline: does model-based planning
                                 match supervised baseline?
  fig2_action_accuracy.png     : eval action accuracy per condition × env.
                                 More sensitive metric than return.
  fig3_rg_vs_return.png        : (final reward_gap, eval return) scatter
                                 per cell. Encoder vs policy quality
                                 landscape.
  fig4_distillation_pipeline.png : direct comparison of model_plan vs
                                 distilled_policy vs delta_e+supervised.
  fig5_headline_table.png      : single-figure summary of all 6
                                 conditions × envs with return + rg.
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

FIG_DIR = ROOT / "papers" / "planning_from_concern" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

COND_COLORS = {
    "model_plan_delta_e": "#2ca02c",
    "model_plan_random_encoder": "#7f7f7f",
    "model_plan_sensory_encoder": "#d62728",
    "model_plan_valence_encoder": "#9467bd",
    "distilled_policy_from_model": "#17becf",
    "delta_e_then_supervised_policy": "#bcbd22",
}
COND_LABEL = {
    "model_plan_delta_e": "ΔE planning (HEADLINE: no labels, no policy gradient)",
    "model_plan_random_encoder": "Random encoder + ΔE planning (lower bound)",
    "model_plan_sensory_encoder": "Sensory encoder + ΔE planning",
    "model_plan_valence_encoder": "Valence encoder + ΔE planning (upper bound)",
    "distilled_policy_from_model": "Distilled policy (model labels itself)",
    "delta_e_then_supervised_policy": "ΔE encoder + supervised policy (Paper 9)",
}
ENV_LABEL = {"xor": "XOR", "additive_thresh": "additive_thresh"}


def main() -> int:
    data = json.loads(
        (ROOT / "artifacts" / "planning_from_concern" / "sweep_v1.json").read_text()
    )
    results = data["results"]
    conditions = data["manifest"]["conditions"]
    envs = data["manifest"]["envs"]

    by_key = defaultdict(list)
    for r in results:
        by_key[(r["condition"], r["env"])].append(r)

    # ============ Figure 1: return grid ============
    fig, ax = plt.subplots(figsize=(12, 5.5))
    x = np.arange(len(conditions))
    w = 0.38
    for env_idx, env in enumerate(envs):
        means = []
        stds = []
        for cond in conditions:
            cells = by_key.get((cond, env), [])
            vals = [r["eval_mean_return"] for r in cells]
            means.append(np.mean(vals) if vals else 0)
            stds.append(np.std(vals) if len(vals) > 1 else 0)
        offset = (env_idx - 0.5) * w
        c = "#2ca02c" if env == "xor" else "#1f77b4"
        ax.bar(x + offset, means, w, yerr=stds, color=c, alpha=0.85,
               label=ENV_LABEL[env], edgecolor="black", linewidth=0.4)
        for i, m in enumerate(means):
            ax.text(x[i] + offset, m + 1.0, f"{m:.1f}",
                    ha="center", fontsize=9, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([COND_LABEL[c].split(" (")[0].replace(" + ", "\n+ ")
                        for c in conditions], fontsize=8)
    ax.set_ylabel("Eval mean return (50 episodes)", fontsize=11)
    ax.axhline(50, color="gray", linewidth=0.4, linestyle=":")
    ax.set_ylim(0, 55)
    ax.legend(loc="upper right", fontsize=9)
    ax.set_title(
        "Planning from Concern: ΔE-organized encoder + argmax_a ΔE_head reaches "
        "supervised-baseline return on XOR\n(no optimal-action labels, no policy gradient)",
        fontsize=12,
    )
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig1_return_grid.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ============ Figure 2: action accuracy grid ============
    fig, ax = plt.subplots(figsize=(12, 5.5))
    for env_idx, env in enumerate(envs):
        means = []
        stds = []
        for cond in conditions:
            cells = by_key.get((cond, env), [])
            vals = [r["eval_action_accuracy"] for r in cells]
            means.append(np.mean(vals) if vals else 0)
            stds.append(np.std(vals) if len(vals) > 1 else 0)
        offset = (env_idx - 0.5) * w
        c = "#2ca02c" if env == "xor" else "#1f77b4"
        ax.bar(x + offset, means, w, yerr=stds, color=c, alpha=0.85,
               label=ENV_LABEL[env], edgecolor="black", linewidth=0.4)
        for i, m in enumerate(means):
            ax.text(x[i] + offset, m + 0.015, f"{m:.3f}",
                    ha="center", fontsize=8.5, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([COND_LABEL[c].split(" (")[0].replace(" + ", "\n+ ")
                        for c in conditions], fontsize=8)
    ax.set_ylabel("Eval action accuracy (fraction optimal actions)", fontsize=11)
    ax.set_ylim(0, 1.08)
    ax.axhline(0.5, color="gray", linewidth=0.4, linestyle=":")
    ax.text(0, 0.51, "random = 0.5", fontsize=8, color="gray")
    ax.legend(loc="lower right", fontsize=9)
    ax.set_title("Eval action accuracy (per-step optimal action rate)", fontsize=12)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig2_action_accuracy.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ============ Figure 3: scatter rg vs return ============
    fig, axes = plt.subplots(1, 2, figsize=(13, 6), sharey=True)
    for ax_idx, env in enumerate(envs):
        ax = axes[ax_idx]
        for cond in conditions:
            cells = by_key.get((cond, env), [])
            if not cells:
                continue
            xs = [r["final_cluster_gaps"]["reward"] for r in cells]
            ys = [r["eval_mean_return"] for r in cells]
            ax.scatter(xs, ys, s=140, color=COND_COLORS[cond], alpha=0.9,
                       edgecolor="black", linewidth=0.5,
                       label=COND_LABEL[cond].split(" (")[0] if ax_idx == 0 else None)
        ax.axhline(50, color="gray", linewidth=0.4, linestyle=":")
        ax.axvline(0, color="black", linewidth=0.4)
        ax.set_xlabel("Final reward_gap", fontsize=10)
        if ax_idx == 0:
            ax.set_ylabel("Eval mean return", fontsize=10)
        ax.set_title(f"reward = {env}", fontsize=11)
        ax.grid(linestyle=":", alpha=0.4)
    handles, lbls = axes[0].get_legend_handles_labels()
    fig.legend(handles, lbls, loc="upper center",
               bbox_to_anchor=(0.5, 1.05), ncol=3, fontsize=8)
    fig.suptitle(
        "Encoder quality vs task return: model planning recovers competence\n"
        "from a ΔE-organized encoder without policy training",
        fontsize=12, y=1.12,
    )
    fig.tight_layout()
    out = FIG_DIR / "fig3_rg_vs_return.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ============ Figure 4: three-way comparison ============
    fig, ax = plt.subplots(figsize=(11, 5.5))
    cmp_conds = ["model_plan_delta_e", "distilled_policy_from_model", "delta_e_then_supervised_policy"]
    x_cmp = np.arange(len(cmp_conds))
    for env_idx, env in enumerate(envs):
        means = []
        for cond in cmp_conds:
            cells = by_key.get((cond, env), [])
            vals = [r["eval_mean_return"] for r in cells]
            means.append(np.mean(vals) if vals else 0)
        offset = (env_idx - 0.5) * 0.36
        c = "#2ca02c" if env == "xor" else "#1f77b4"
        bars = ax.bar(x_cmp + offset, means, 0.36, color=c, alpha=0.85,
                      label=ENV_LABEL[env], edgecolor="black", linewidth=0.4)
        for bar, m in zip(bars, means):
            ax.text(bar.get_x() + bar.get_width() / 2, m + 1, f"{m:.1f}",
                    ha="center", fontsize=10, fontweight="bold")
    ax.set_xticks(x_cmp)
    ax.set_xticklabels([
        "model_plan_delta_e\n(no labels, no policy)",
        "distilled_policy\n(self-labeled from model)",
        "delta_e + supervised\n(oracle labels, Paper 9)",
    ], fontsize=9)
    ax.set_ylabel("Eval mean return", fontsize=11)
    ax.set_ylim(0, 55)
    ax.axhline(50, color="gray", linewidth=0.4, linestyle=":")
    ax.legend(loc="lower right", fontsize=9)
    ax.set_title(
        "Three routes to competence from a ΔE-organized encoder\n"
        "(model planning ≈ self-distillation ≈ supervised baseline)",
        fontsize=12,
    )
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig4_distillation_pipeline.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ============ Figure 5: headline table-as-figure ============
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.5), sharey=False)
    for ax_idx, (metric_key, metric_label) in enumerate([
        ("eval_mean_return", "Eval mean return"),
        ("final_reward_gap", "Final reward_gap"),
    ]):
        ax = axes[ax_idx]
        for env_idx, env in enumerate(envs):
            means = []
            for cond in conditions:
                cells = by_key.get((cond, env), [])
                if metric_key == "final_reward_gap":
                    vals = [r["final_cluster_gaps"]["reward"] for r in cells]
                else:
                    vals = [r[metric_key] for r in cells]
                means.append(np.mean(vals) if vals else 0)
            offset = (env_idx - 0.5) * 0.36
            c = "#2ca02c" if env == "xor" else "#1f77b4"
            ax.bar(x + offset, means, 0.36, color=c, alpha=0.85,
                   label=ENV_LABEL[env] if ax_idx == 0 else None,
                   edgecolor="black", linewidth=0.4)
        ax.set_xticks(x)
        ax.set_xticklabels([COND_LABEL[c].split(" (")[0].replace(" + ", "\n+ ")
                            for c in conditions], fontsize=7.5)
        ax.set_ylabel(metric_label, fontsize=10)
        if metric_key == "eval_mean_return":
            ax.set_ylim(0, 55)
            ax.axhline(50, color="gray", linewidth=0.4, linestyle=":")
        else:
            ax.axhline(0, color="black", linewidth=0.4)
        ax.grid(axis="y", linestyle=":", alpha=0.4)
        if ax_idx == 0:
            ax.legend(loc="upper right", fontsize=9)
    fig.suptitle(
        "Planning from Concern: headline = ΔE planning matches supervised baseline "
        "without optimal-action labels",
        fontsize=12, y=1.02,
    )
    fig.tight_layout()
    out = FIG_DIR / "fig5_headline_table.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ============ Summary ============
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
                mean_return=float(np.mean([r["eval_mean_return"] for r in cells])),
                mean_action_accuracy=float(np.mean([r["eval_action_accuracy"] for r in cells])),
            )
        summary[cond] = per_env
    out_path = ROOT / "artifacts" / "planning_from_concern" / "summary_v1.json"
    out_path.write_text(json.dumps(summary, indent=2))
    print(f"\nsummary:")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
