#!/usr/bin/env python3
"""Figures for Paper 12 — State-Dependent Concern."""

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

FIG_DIR = ROOT / "papers" / "state_dependent_concern" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

COND_LABEL = {
    "state_aware_head_uniform": "state-aware\nuniform",
    "state_aware_head_mbes": "state-aware\nMBES",
    "state_aware_head_ensemble": "state-aware\nensemble-margin",
    "state_blind_head_uniform": "state-blind\nuniform (control)",
    "state_aware_head_random_E_start": "state-aware\nrandom-E start",
    "state_aware_head_random_E_start_mbes": "state-aware\nrandom-E + MBES",
}
ENV_LABEL = {"static_xor": "static XOR", "state_dep_inv_xor": "state-dep inverted XOR"}


def main() -> int:
    data = json.loads(
        (ROOT / "artifacts" / "state_dependent_concern" / "sweep_v1.json").read_text()
    )
    rows = data["summary"]
    conds = data["manifest"]["conditions"]
    envs = data["manifest"]["envs"]

    by_key = defaultdict(list)
    for r in rows:
        by_key[(r["condition"], r["env"])].append(r)

    # Figure 1: side-by-side return + accuracy per condition × env
    fig, axes = plt.subplots(1, 2, figsize=(16, 5.5))
    x = np.arange(len(conds))
    w = 0.4
    for ax_idx, (key, ylabel, ylim) in enumerate([
        ("mean_return", "Mean return (steps survived)", (0, 55)),
        ("action_accuracy", "Eval action accuracy", (0, 1.08)),
    ]):
        ax = axes[ax_idx]
        for env_idx, env in enumerate(envs):
            means = []; stds = []
            for cond in conds:
                cells = by_key.get((cond, env), [])
                vals = [r[key] for r in cells]
                means.append(np.mean(vals) if vals else 0)
                stds.append(np.std(vals) if len(vals) > 1 else 0)
            offset = (env_idx - 0.5) * w
            c = "#2ca02c" if env == "static_xor" else "#d62728"
            ax.bar(x + offset, means, w, yerr=stds, color=c, alpha=0.85,
                   label=ENV_LABEL[env], edgecolor="black", linewidth=0.4)
            for i, m in enumerate(means):
                fmt = f"{m:.1f}" if key == "mean_return" else f"{m:.2f}"
                offset_y = 1.0 if key == "mean_return" else 0.015
                ax.text(x[i] + offset, m + offset_y, fmt,
                        ha="center", fontsize=8, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels([COND_LABEL[c] for c in conds], fontsize=8)
        ax.set_ylabel(ylabel, fontsize=11)
        ax.set_ylim(ylim)
        if key == "mean_return":
            ax.axhline(50, color="gray", linewidth=0.4, linestyle=":")
        else:
            ax.axhline(0.5, color="gray", linewidth=0.4, linestyle=":")
            ax.axhline(0.9, color="black", linewidth=0.4, linestyle=":")
        ax.legend(loc="upper right", fontsize=9)
        ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.suptitle(
        "State-dependent XOR is a uniform-failure mode: every condition collapses to chance",
        fontsize=12, y=1.02,
    )
    fig.tight_layout()
    out = FIG_DIR / "fig1_summary.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # Figure 2: per-E breakdown (only state_dep_inv_xor)
    fig, ax = plt.subplots(figsize=(13, 5.5))
    E_grid = [0.2, 0.5, 0.8]
    x_e = np.arange(len(E_grid))
    w_e = 0.13
    for ci, cond in enumerate(conds):
        cells = by_key.get((cond, "state_dep_inv_xor"), [])
        means = []
        for E in E_grid:
            vals = [r[f"acc@E={E}"] for r in cells]
            means.append(np.mean(vals) if vals else 0)
        offset = (ci - (len(conds) - 1) / 2) * w_e
        ax.bar(x_e + offset, means, w_e * 0.9, alpha=0.85,
               label=COND_LABEL[cond].replace("\n", " "), edgecolor="black", linewidth=0.4)
    ax.set_xticks(x_e)
    ax.set_xticklabels([f"E = {E}" for E in E_grid], fontsize=10)
    ax.set_ylabel("Margin sign accuracy", fontsize=11)
    ax.set_ylim(0, 1.05)
    ax.axhline(0.5, color="gray", linewidth=0.4, linestyle=":")
    ax.legend(loc="upper right", fontsize=8)
    ax.set_title(
        "Margin sign accuracy by internal-state E on state-dep inverted XOR.\n"
        "All conditions hover at ~chance across E. No mechanism learns the E=0.5 inversion.",
        fontsize=11,
    )
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig2_per_E_breakdown.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # Figure 3: hungry vs sated bars per condition
    fig, ax = plt.subplots(figsize=(13, 5.5))
    x_c = np.arange(len(conds))
    w_c = 0.4
    cells_static_aware = [r for r in by_key.get(("state_aware_head_uniform", "static_xor"), [])]
    for category_idx, (cat, color) in enumerate([
        ("action_acc_hungry", "#1f77b4"),
        ("action_acc_sated", "#ff7f0e"),
    ]):
        means = []
        for cond in conds:
            cells = by_key.get((cond, "state_dep_inv_xor"), [])
            vals = [r[cat] for r in cells if r[cat] is not None]
            means.append(np.mean(vals) if vals else 0)
        offset = (category_idx - 0.5) * w_c
        label = "hungry (E<0.5)" if cat == "action_acc_hungry" else "sated (E≥0.5)"
        ax.bar(x_c + offset, means, w_c, color=color, alpha=0.85,
               label=label, edgecolor="black", linewidth=0.4)
        for i, m in enumerate(means):
            ax.text(x_c[i] + offset, m + 0.015, f"{m:.2f}", ha="center", fontsize=9)
    ax.set_xticks(x_c)
    ax.set_xticklabels([COND_LABEL[c] for c in conds], fontsize=8)
    ax.set_ylabel("Action accuracy", fontsize=11)
    ax.set_ylim(0, 1.08)
    ax.axhline(0.5, color="gray", linewidth=0.4, linestyle=":")
    ax.legend(loc="upper right", fontsize=10)
    ax.set_title(
        "On state-dep inverted XOR: hungry- and sated-regime accuracies "
        "both stay near chance for every condition",
        fontsize=12,
    )
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig3_hungry_vs_sated.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # Summary stats
    summary = {}
    for cond in conds:
        per_env = {}
        for env in envs:
            cells = by_key.get((cond, env), [])
            if not cells:
                continue
            per_env[env] = dict(
                mean_return=float(np.mean([r["mean_return"] for r in cells])),
                action_accuracy=float(np.mean([r["action_accuracy"] for r in cells])),
                action_acc_hungry=float(np.mean([r["action_acc_hungry"] for r in cells if r["action_acc_hungry"] is not None])),
                action_acc_sated=float(np.mean([r["action_acc_sated"] for r in cells if r["action_acc_sated"] is not None])),
                acc_at_E02=float(np.mean([r["acc@E=0.2"] for r in cells])),
                acc_at_E05=float(np.mean([r["acc@E=0.5"] for r in cells])),
                acc_at_E08=float(np.mean([r["acc@E=0.8"] for r in cells])),
            )
        summary[cond] = per_env
    out_path = ROOT / "artifacts" / "state_dependent_concern" / "summary_v1.json"
    out_path.write_text(json.dumps(summary, indent=2))
    print(f"\nsummary:")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
