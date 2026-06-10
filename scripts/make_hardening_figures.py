#!/usr/bin/env python3
"""Figures for Paper 10b — Hardening the Loop.

Six figures:

  fig1_axis_ablation.png       : per-axis ablation drop in action
                                 accuracy and return. Headline: does
                                 reward-axis ablation hurt much more
                                 than color/label/random ablation?
  fig2_exploration_regimes.png : baseline return and accuracy under
                                 4 exploration regimes.
  fig3_head_capacity.png       : baseline return + reward_gap across
                                 5 ΔE head capacities.
  fig4_calibration_scatter.png : predicted ΔE vs true ΔE for
                                 consume/skip actions across items.
  fig5_harder_env.png          : standard vs hard env baseline +
                                 ablation results.
  fig6_headline.png            : single-figure synthesis.
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

FIG_DIR = ROOT / "papers" / "planning_hardening" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

ENV_LABEL = {"xor": "XOR", "additive_thresh": "additive_thresh"}


def main() -> int:
    data = json.loads(
        (ROOT / "artifacts" / "planning_hardening" / "sweep_v1.json").read_text()
    )
    rows = data["summary"]
    full_results = data["results"]

    # Group baseline-condition cells (exploration=uniform_random,
    # head_capacity=medium, env_hardness=std). These are the canonical
    # cells for axis-ablation analysis.
    baseline_cells = [r for r in rows
                      if r["exploration"] == "uniform_random"
                      and r["head_capacity"] == "medium"
                      and r["env_hardness"] == "std"]

    # ============ Figure 1: axis ablation ============
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    envs = ["xor", "additive_thresh"]
    axes_keys = ["random", "color", "label", "reward"]
    axis_colors = {"random": "#7f7f7f", "color": "#ff7f0e",
                   "label": "#9467bd", "reward": "#d62728"}

    for ax_idx, env in enumerate(envs):
        ax = axes[ax_idx]
        cells = [r for r in baseline_cells if r["env"] == env]
        baseline_acc = np.mean([r["baseline_acc"] for r in cells])
        means = []
        stds = []
        for ax_name in axes_keys:
            key = f"ablate_{ax_name}_acc"
            vals = [r[key] for r in cells]
            means.append(baseline_acc - np.mean(vals))  # drop from baseline
            stds.append(np.std(vals) if len(vals) > 1 else 0)
        x = np.arange(len(axes_keys))
        bars = ax.bar(x, means, 0.6, yerr=stds,
                      color=[axis_colors[k] for k in axes_keys],
                      alpha=0.92, edgecolor="black", linewidth=0.5)
        for i, m in enumerate(means):
            ax.text(x[i], m + 0.01 if m >= 0 else m - 0.02, f"{m:+.3f}",
                    ha="center", fontsize=10,
                    fontweight="bold" if axes_keys[i] == "reward" else "normal")
        ax.axhline(0, color="black", linewidth=0.5)
        ax.set_xticks(x)
        ax.set_xticklabels(axes_keys, fontsize=11)
        ax.set_xlabel("Ablated axis", fontsize=11)
        ax.set_ylabel("Drop in eval action accuracy from baseline", fontsize=10)
        ax.set_title(f"reward = {env} (baseline acc {baseline_acc:.3f})", fontsize=11)
        ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.suptitle(
        "Reward-axis ablation in the planning pipeline:\n"
        "removing the reward axis from z destroys model-based action accuracy on XOR",
        fontsize=12, y=1.02,
    )
    fig.tight_layout()
    out = FIG_DIR / "fig1_axis_ablation.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ============ Figure 2: exploration regime ============
    expl_rows = [r for r in rows if r["study"] == "exploration"]
    regimes = ["uniform_random", "biased_consume", "eps_greedy", "replay_balanced"]
    regime_label = {
        "uniform_random": "uniform random\n(baseline)",
        "biased_consume": "biased consume\n(always action=1)",
        "eps_greedy": "ε-greedy\n(50% explore)",
        "replay_balanced": "replay balanced\n(80% consume + balanced batch)",
    }

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5), sharey=False)
    for ax_idx, metric_key, metric_label in [
        (0, "baseline_return", "Eval mean return"),
        (1, "baseline_acc", "Eval action accuracy"),
    ]:
        ax = axes[ax_idx]
        x = np.arange(len(regimes))
        w = 0.38
        for env_idx, env in enumerate(envs):
            means = []
            stds = []
            for regime in regimes:
                cells = [r for r in expl_rows
                         if r["exploration"] == regime and r["env"] == env]
                vals = [r[metric_key] for r in cells]
                means.append(np.mean(vals) if vals else 0)
                stds.append(np.std(vals) if len(vals) > 1 else 0)
            offset = (env_idx - 0.5) * w
            c = "#2ca02c" if env == "xor" else "#1f77b4"
            ax.bar(x + offset, means, w, yerr=stds, color=c, alpha=0.85,
                   label=ENV_LABEL[env], edgecolor="black", linewidth=0.4)
            for i, m in enumerate(means):
                if metric_key == "baseline_return":
                    fmt = f"{m:.1f}"
                else:
                    fmt = f"{m:.3f}"
                ax.text(x[i] + offset, m + (1 if metric_key == "baseline_return" else 0.015),
                        fmt, ha="center", fontsize=8)
        ax.set_xticks(x)
        ax.set_xticklabels([regime_label[r] for r in regimes], fontsize=8)
        ax.set_ylabel(metric_label, fontsize=10)
        if metric_key == "baseline_return":
            ax.set_ylim(0, 55)
            ax.axhline(50, color="gray", linewidth=0.4, linestyle=":")
        else:
            ax.set_ylim(0, 1.08)
            ax.axhline(0.5, color="gray", linewidth=0.4, linestyle=":")
        ax.grid(axis="y", linestyle=":", alpha=0.4)
        if ax_idx == 0:
            ax.legend(loc="lower right", fontsize=9)
    fig.suptitle(
        "Exploration regime: does ΔE planning survive biased data collection?",
        fontsize=12, y=1.02,
    )
    fig.tight_layout()
    out = FIG_DIR / "fig2_exploration_regimes.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ============ Figure 3: head capacity ============
    cap_rows = [r for r in rows if r["study"] in ("capacity",)]
    # Add the medium case from exploration=uniform
    cap_rows_with_medium = list(cap_rows) + [
        r for r in baseline_cells
    ]
    capacities = ["linear", "small", "medium", "large", "raw_input"]
    cap_label = {
        "linear": "linear\n(no hidden)",
        "small": "small\n(8 hid)",
        "medium": "medium\n(32 hid, default)",
        "large": "large\n(128 hid)",
        "raw_input": "raw input\n(no encoder)",
    }

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    for ax_idx, metric_key, metric_label in [
        (0, "baseline_return", "Eval mean return"),
        (1, "reward_gap", "Final reward_gap"),
    ]:
        ax = axes[ax_idx]
        x = np.arange(len(capacities))
        w = 0.38
        for env_idx, env in enumerate(envs):
            means = []
            stds = []
            for cap in capacities:
                cells = [r for r in cap_rows_with_medium
                         if r["head_capacity"] == cap and r["env"] == env]
                vals = [r[metric_key] for r in cells]
                means.append(np.mean(vals) if vals else 0)
                stds.append(np.std(vals) if len(vals) > 1 else 0)
            offset = (env_idx - 0.5) * w
            c = "#2ca02c" if env == "xor" else "#1f77b4"
            ax.bar(x + offset, means, w, yerr=stds, color=c, alpha=0.85,
                   label=ENV_LABEL[env], edgecolor="black", linewidth=0.4)
            for i, m in enumerate(means):
                fmt = f"{m:.1f}" if metric_key == "baseline_return" else f"{m:+.2f}"
                ax.text(x[i] + offset, m + (1 if metric_key == "baseline_return" else 0.03),
                        fmt, ha="center", fontsize=8)
        ax.set_xticks(x)
        ax.set_xticklabels([cap_label[c] for c in capacities], fontsize=8)
        ax.set_ylabel(metric_label, fontsize=10)
        if metric_key == "baseline_return":
            ax.set_ylim(0, 55)
            ax.axhline(50, color="gray", linewidth=0.4, linestyle=":")
        else:
            ax.axhline(0, color="black", linewidth=0.4)
        ax.grid(axis="y", linestyle=":", alpha=0.4)
        if ax_idx == 0:
            ax.legend(loc="lower right", fontsize=9)
    fig.suptitle(
        "ΔE head capacity: when does the model-planning result depend on architecture?",
        fontsize=12, y=1.02,
    )
    fig.tight_layout()
    out = FIG_DIR / "fig3_head_capacity.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ============ Figure 4: ΔE calibration scatter ============
    # Aggregate calibration data from the canonical xor cells
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5), sharex=True, sharey=True)
    for ax_idx, env in enumerate(envs):
        ax = axes[ax_idx]
        pred_c = []
        pred_s = []
        true_c = []
        true_s = []
        for r in full_results:
            if (r["env"] == env and r["exploration"] == "uniform_random"
                    and r["head_capacity"] == "medium"
                    and r["env_hardness"] == "std"):
                pred_c.extend(r["calibration_pred_consume"])
                pred_s.extend(r["calibration_pred_skip"])
                true_c.extend(r["calibration_true_consume"])
                true_s.extend(r["calibration_true_skip"])
        pred_c = np.array(pred_c); pred_s = np.array(pred_s)
        true_c = np.array(true_c); true_s = np.array(true_s)
        ax.scatter(true_c, pred_c, s=15, alpha=0.45, color="#2ca02c",
                   label="consume (action=1)", edgecolor="white", linewidth=0.3)
        ax.scatter(true_s, pred_s, s=15, alpha=0.45, color="#d62728",
                   label="skip (action=0)", edgecolor="white", linewidth=0.3)
        lim = max(np.abs(np.concatenate([true_c, true_s, pred_c, pred_s]))) * 1.1
        ax.plot([-lim, lim], [-lim, lim], "k--", linewidth=0.5, alpha=0.5)
        ax.axhline(0, color="black", linewidth=0.3)
        ax.axvline(0, color="black", linewidth=0.3)
        ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim)
        ax.set_xlabel("True ΔE (at fixed E=0.5)", fontsize=10)
        if ax_idx == 0:
            ax.set_ylabel("Predicted ΔE", fontsize=10)
        ax.set_title(f"reward = {env}", fontsize=11)
        ax.legend(loc="upper left", fontsize=9)
        ax.grid(linestyle=":", alpha=0.4)
    fig.suptitle(
        "ΔE calibration: does the auxiliary head accurately predict viability changes?",
        fontsize=12, y=1.02,
    )
    fig.tight_layout()
    out = FIG_DIR / "fig4_calibration_scatter.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ============ Figure 5: harder env ============
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5), sharey=False)
    hardness_set = [("std", "standard\n(decay 0.04, cost 0)"),
                    ("hard", "hard\n(decay 0.08, cost 0.05)")]
    for ax_idx, metric_key, metric_label in [
        (0, "baseline_return", "Eval mean return"),
        (1, "baseline_acc", "Eval action accuracy"),
    ]:
        ax = axes[ax_idx]
        x = np.arange(len(hardness_set))
        w = 0.38
        for env_idx, env in enumerate(envs):
            means = []
            stds = []
            for hard_key, _ in hardness_set:
                if hard_key == "std":
                    cells = [r for r in baseline_cells if r["env"] == env]
                else:
                    cells = [r for r in rows
                             if r["study"] == "harder_env"
                             and r["env"] == env
                             and r["env_hardness"] == "hard"]
                vals = [r[metric_key] for r in cells]
                means.append(np.mean(vals) if vals else 0)
                stds.append(np.std(vals) if len(vals) > 1 else 0)
            offset = (env_idx - 0.5) * w
            c = "#2ca02c" if env == "xor" else "#1f77b4"
            ax.bar(x + offset, means, w, yerr=stds, color=c, alpha=0.85,
                   label=ENV_LABEL[env], edgecolor="black", linewidth=0.4)
            for i, m in enumerate(means):
                fmt = f"{m:.1f}" if metric_key == "baseline_return" else f"{m:.3f}"
                ax.text(x[i] + offset, m + (1 if metric_key == "baseline_return" else 0.015),
                        fmt, ha="center", fontsize=8)
        ax.set_xticks(x)
        ax.set_xticklabels([h[1] for h in hardness_set], fontsize=9)
        ax.set_ylabel(metric_label, fontsize=10)
        if metric_key == "baseline_return":
            ax.set_ylim(0, 55)
            ax.axhline(50, color="gray", linewidth=0.4, linestyle=":")
        else:
            ax.set_ylim(0, 1.08)
            ax.axhline(0.5, color="gray", linewidth=0.4, linestyle=":")
        ax.grid(axis="y", linestyle=":", alpha=0.4)
        if ax_idx == 0:
            ax.legend(loc="upper right", fontsize=9)
    fig.suptitle(
        "Harder environment: does the planning result survive faster decay + action cost?",
        fontsize=12, y=1.02,
    )
    fig.tight_layout()
    out = FIG_DIR / "fig5_harder_env.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ============ Summary stats ============
    summary = {}
    # Axis ablation drops
    for env in envs:
        cells = [r for r in baseline_cells if r["env"] == env]
        baseline_acc = float(np.mean([r["baseline_acc"] for r in cells]))
        summary.setdefault("axis_ablation", {})[env] = dict(
            baseline_acc=baseline_acc,
            drops={ax: float(np.mean([baseline_acc - r[f"ablate_{ax}_acc"] for r in cells]))
                   for ax in ["color", "label", "reward", "random"]},
        )
    # Exploration
    summary["exploration"] = {}
    for regime in ["uniform_random", "biased_consume", "eps_greedy", "replay_balanced"]:
        for env in envs:
            cells = [r for r in rows
                     if r["study"] == "exploration"
                     and r["exploration"] == regime and r["env"] == env]
            if cells:
                summary["exploration"][f"{regime}_{env}"] = dict(
                    mean_return=float(np.mean([r["baseline_return"] for r in cells])),
                    mean_acc=float(np.mean([r["baseline_acc"] for r in cells])),
                    mean_rg=float(np.mean([r["reward_gap"] for r in cells])),
                )
    # Capacity
    summary["capacity"] = {}
    cap_all = list(rows)
    for cap in ["linear", "small", "medium", "large", "raw_input"]:
        for env in envs:
            cells = [r for r in cap_all
                     if r["head_capacity"] == cap and r["env"] == env
                     and r["exploration"] == "uniform_random"
                     and r["env_hardness"] == "std"]
            if cells:
                summary["capacity"][f"{cap}_{env}"] = dict(
                    mean_return=float(np.mean([r["baseline_return"] for r in cells])),
                    mean_acc=float(np.mean([r["baseline_acc"] for r in cells])),
                    mean_rg=float(np.mean([r["reward_gap"] for r in cells])),
                )
    # Hardness
    summary["env_hardness"] = {}
    for env in envs:
        for hh in ["std", "hard"]:
            if hh == "std":
                cells = [r for r in baseline_cells if r["env"] == env]
            else:
                cells = [r for r in rows
                         if r["study"] == "harder_env" and r["env"] == env]
            if cells:
                summary["env_hardness"][f"{hh}_{env}"] = dict(
                    mean_return=float(np.mean([r["baseline_return"] for r in cells])),
                    mean_acc=float(np.mean([r["baseline_acc"] for r in cells])),
                )
    out_path = ROOT / "artifacts" / "planning_hardening" / "summary_v1.json"
    out_path.write_text(json.dumps(summary, indent=2))
    print(f"\nsummary:")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
