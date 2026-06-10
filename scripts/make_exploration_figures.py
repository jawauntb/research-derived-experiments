#!/usr/bin/env python3
"""Figures for Paper 11 — Epistemic Exploration.

Five figures:

  fig1_return_grid.png        : eval return per condition × env.
  fig2_action_accuracy.png    : action accuracy per condition × env.
  fig3_calibration_vs_success.png : (calibration MSE, action accuracy)
                                scatter per cell.
  fig4_rg_vs_accuracy.png     : (reward_gap, action accuracy) scatter.
  fig5_headline.png           : single side-by-side summary.
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

FIG_DIR = ROOT / "papers" / "epistemic_exploration" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

COND_COLORS = {
    "biased_only": "#7f7f7f",
    "eps_greedy_decay": "#1f77b4",
    "pred_error_curiosity": "#ff7f0e",
    "ensemble_disagree": "#d62728",
    "expected_info_gain": "#2ca02c",
    "uniform_random": "#9467bd",
}
COND_LABEL = {
    "biased_only": "biased_only\n(no exploration)",
    "eps_greedy_decay": "eps_greedy_decay\n(ε: 1.0 → 0.05)",
    "pred_error_curiosity": "pred_error_curiosity\n(ICM-style)",
    "ensemble_disagree": "ensemble_disagree\n(bootstrap-DQN)",
    "expected_info_gain": "expected_info_gain\n(margin-based)",
    "uniform_random": "uniform_random\n(positive baseline)",
}
ENV_LABEL = {"xor": "XOR", "additive_thresh": "additive_thresh"}


def main() -> int:
    data = json.loads(
        (ROOT / "artifacts" / "epistemic_exploration" / "sweep_v1.json").read_text()
    )
    rows = data["summary"]
    conditions = data["manifest"]["conditions"]
    envs = data["manifest"]["envs"]
    bias_p = data["manifest"]["bias_p_consume"]

    by_key = defaultdict(list)
    for r in rows:
        by_key[(r["condition"], r["env"])].append(r)

    # ============ Figure 1: return ============
    fig, ax = plt.subplots(figsize=(12, 5.5))
    x = np.arange(len(conditions))
    w = 0.38
    for env_idx, env in enumerate(envs):
        means = []; stds = []
        for cond in conditions:
            cells = by_key.get((cond, env), [])
            vals = [r["mean_return"] for r in cells]
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
    ax.set_xticklabels([COND_LABEL[c] for c in conditions], fontsize=8)
    ax.set_ylabel("Eval mean return (50 episodes)", fontsize=11)
    ax.axhline(50, color="gray", linewidth=0.4, linestyle=":")
    ax.set_ylim(0, 55)
    ax.legend(loc="upper right", fontsize=9)
    ax.set_title(
        f"Eval return from biased initial policy (p_consume={bias_p}).\n"
        "Two intrinsic mechanisms close the gap to uniform_random; two do not.",
        fontsize=12,
    )
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig1_return_grid.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ============ Figure 2: action accuracy ============
    fig, ax = plt.subplots(figsize=(12, 5.5))
    for env_idx, env in enumerate(envs):
        means = []; stds = []
        for cond in conditions:
            cells = by_key.get((cond, env), [])
            vals = [r["action_accuracy"] for r in cells]
            means.append(np.mean(vals) if vals else 0)
            stds.append(np.std(vals) if len(vals) > 1 else 0)
        offset = (env_idx - 0.5) * w
        c = "#2ca02c" if env == "xor" else "#1f77b4"
        ax.bar(x + offset, means, w, yerr=stds, color=c, alpha=0.85,
               label=ENV_LABEL[env], edgecolor="black", linewidth=0.4)
        for i, m in enumerate(means):
            ax.text(x[i] + offset, m + 0.015, f"{m:.3f}",
                    ha="center", fontsize=8, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([COND_LABEL[c] for c in conditions], fontsize=8)
    ax.set_ylabel("Eval action accuracy", fontsize=11)
    ax.set_ylim(0, 1.08)
    ax.axhline(0.5, color="gray", linewidth=0.4, linestyle=":")
    ax.axhline(0.9, color="black", linewidth=0.4, linestyle=":")
    ax.legend(loc="upper right", fontsize=9)
    ax.set_title("Action accuracy. Pre-registered G3 gate at 0.90 (dotted).", fontsize=12)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig2_action_accuracy.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ============ Figure 3: calibration MSE vs action accuracy ============
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5), sharex=True, sharey=True)
    for ax_idx, env in enumerate(envs):
        ax = axes[ax_idx]
        for cond in conditions:
            cells = by_key.get((cond, env), [])
            if not cells:
                continue
            xs = [r["calibration_consume_mse"] for r in cells]
            ys = [r["action_accuracy"] for r in cells]
            ax.scatter(xs, ys, s=140, color=COND_COLORS[cond], alpha=0.9,
                       edgecolor="black", linewidth=0.5,
                       label=COND_LABEL[cond].replace("\n", " ") if ax_idx == 0 else None)
        ax.set_xlabel("ΔE consume calibration MSE", fontsize=10)
        if ax_idx == 0:
            ax.set_ylabel("Eval action accuracy", fontsize=10)
        ax.set_title(f"reward = {env}", fontsize=11)
        ax.set_xscale("symlog", linthresh=0.01)
        ax.set_ylim(0, 1.05)
        ax.axhline(0.5, color="gray", linewidth=0.4, linestyle=":")
        ax.grid(linestyle=":", alpha=0.4)
    handles, lbls = axes[0].get_legend_handles_labels()
    fig.legend(handles, lbls, loc="upper center", bbox_to_anchor=(0.5, 1.06),
               ncol=3, fontsize=8)
    fig.suptitle(
        "Calibration vs accuracy: failures cluster at high calibration MSE",
        fontsize=12, y=1.10,
    )
    fig.tight_layout()
    out = FIG_DIR / "fig3_calibration_vs_success.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ============ Figure 4: rg vs accuracy ============
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5), sharex=True, sharey=True)
    for ax_idx, env in enumerate(envs):
        ax = axes[ax_idx]
        for cond in conditions:
            cells = by_key.get((cond, env), [])
            if not cells:
                continue
            xs = [r["reward_gap"] for r in cells]
            ys = [r["action_accuracy"] for r in cells]
            ax.scatter(xs, ys, s=140, color=COND_COLORS[cond], alpha=0.9,
                       edgecolor="black", linewidth=0.5,
                       label=COND_LABEL[cond].replace("\n", " ") if ax_idx == 0 else None)
        ax.set_xlabel("Final reward_gap", fontsize=10)
        if ax_idx == 0:
            ax.set_ylabel("Eval action accuracy", fontsize=10)
        ax.set_title(f"reward = {env}", fontsize=11)
        ax.set_ylim(0, 1.05)
        ax.axhline(0.5, color="gray", linewidth=0.4, linestyle=":")
        ax.axvline(0, color="black", linewidth=0.4)
        ax.grid(linestyle=":", alpha=0.4)
    handles, lbls = axes[0].get_legend_handles_labels()
    fig.legend(handles, lbls, loc="upper center", bbox_to_anchor=(0.5, 1.06),
               ncol=3, fontsize=8)
    fig.suptitle(
        "reward_gap is not sufficient: biased_only has rg +1.82 but acc 0.47 on XOR",
        fontsize=12, y=1.10,
    )
    fig.tight_layout()
    out = FIG_DIR / "fig4_rg_vs_accuracy.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ============ Figure 5: headline ============
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.5))
    for ax_idx, (metric_key, ylabel, ylim) in enumerate([
        ("action_accuracy", "Eval action accuracy", (0, 1.08)),
        ("calibration_consume_mse", "ΔE consume calibration MSE (log)", None),
    ]):
        ax = axes[ax_idx]
        for env_idx, env in enumerate(envs):
            means = []
            for cond in conditions:
                cells = by_key.get((cond, env), [])
                vals = [r[metric_key] for r in cells]
                means.append(np.mean(vals) if vals else 0)
            offset = (env_idx - 0.5) * w
            c = "#2ca02c" if env == "xor" else "#1f77b4"
            ax.bar(x + offset, means, w, color=c, alpha=0.85,
                   label=ENV_LABEL[env] if ax_idx == 0 else None,
                   edgecolor="black", linewidth=0.4)
        ax.set_xticks(x)
        ax.set_xticklabels([COND_LABEL[c] for c in conditions], fontsize=7.5)
        ax.set_ylabel(ylabel, fontsize=10)
        if metric_key == "calibration_consume_mse":
            ax.set_yscale("symlog", linthresh=0.01)
        if ylim:
            ax.set_ylim(ylim)
            ax.axhline(0.5, color="gray", linewidth=0.4, linestyle=":")
            ax.axhline(0.9, color="black", linewidth=0.4, linestyle=":")
        ax.grid(axis="y", linestyle=":", alpha=0.4)
        if ax_idx == 0:
            ax.legend(loc="upper right", fontsize=9)
    fig.suptitle(
        "Epistemic exploration from biased prior: action accuracy and ΔE calibration",
        fontsize=12, y=1.02,
    )
    fig.tight_layout()
    out = FIG_DIR / "fig5_headline.png"
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
                mean_return=float(np.mean([r["mean_return"] for r in cells])),
                mean_acc=float(np.mean([r["action_accuracy"] for r in cells])),
                mean_rg=float(np.mean([r["reward_gap"] for r in cells])),
                mean_cal_consume_mse=float(np.mean([r["calibration_consume_mse"] for r in cells])),
                mean_cal_skip_mse=float(np.mean([r["calibration_skip_mse"] for r in cells])),
            )
        summary[cond] = per_env
    out_path = ROOT / "artifacts" / "epistemic_exploration" / "summary_v1.json"
    out_path.write_text(json.dumps(summary, indent=2))
    print(f"\nsummary:")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
