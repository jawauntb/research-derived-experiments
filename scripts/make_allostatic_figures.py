#!/usr/bin/env python3
"""Figures for Paper 14 — Allostatic State Control."""

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

FIG_DIR = ROOT / "papers" / "allostatic_control" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

COND_COLORS = {
    "baseline_2action": "#7f7f7f",
    "4action_greedy": "#2ca02c",
    "4action_two_step": "#ff7f0e",
    "4action_uncertainty": "#1f77b4",
}
COND_LABEL = {
    "baseline_2action": "baseline (2-action,\ngreedy)",
    "4action_greedy": "4-action\ngreedy (WINNER)",
    "4action_two_step": "4-action\ntwo-step planner",
    "4action_uncertainty": "4-action\nuncertainty-aware",
}


def main() -> int:
    data = json.loads(
        (ROOT / "artifacts" / "allostatic_control" / "sweep_v1.json").read_text()
    )
    rows = data["summary"]
    conds = data["manifest"]["conditions"]
    boundaries = data["manifest"]["boundary_locations"]

    by_key = defaultdict(list)
    for r in rows:
        by_key[(r["condition"], r["boundary"])].append(r)

    # Figure 1: return per condition × boundary location
    fig, ax = plt.subplots(figsize=(13, 5.5))
    x = np.arange(len(boundaries))
    w = 0.20
    for ci, cond in enumerate(conds):
        means = []
        stds = []
        for b in boundaries:
            cells = by_key.get((cond, b), [])
            vals = [r["mean_return"] for r in cells]
            means.append(np.mean(vals) if vals else 0)
            stds.append(np.std(vals) if len(vals) > 1 else 0)
        offset = (ci - (len(conds) - 1) / 2) * w
        ax.bar(x + offset, means, w * 0.92, yerr=stds,
               color=COND_COLORS[cond], alpha=0.92,
               label=COND_LABEL[cond], edgecolor="black", linewidth=0.4)
        for i, m in enumerate(means):
            ax.text(x[i] + offset, m + 1.0, f"{m:.1f}",
                    ha="center", fontsize=8, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([f"boundary E = {b}" for b in boundaries], fontsize=10)
    ax.set_ylabel("Mean return", fontsize=11)
    ax.set_ylim(0, 55)
    ax.axhline(50, color="gray", linewidth=0.4, linestyle=":")
    ax.legend(loc="lower left", fontsize=9)
    ax.set_title(
        "At boundary E=0.5: greedy + regulate WINS (+18.0 vs baseline). "
        "Uncertainty-aware planner is WORSE than no regulate.",
        fontsize=12,
    )
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig1_return_by_boundary.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # Figure 2: regulate metrics — rate and specificity
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
    for ax_idx, (key, ylabel, ylim) in enumerate([
        ("regulate_rate", "Regulate action rate", (0, 1.0)),
        ("regulate_specificity",
         "Regulate specificity\n(fraction at below-median margin)", (0, 1.0)),
    ]):
        ax = axes[ax_idx]
        for ci, cond in enumerate(conds):
            if cond == "baseline_2action":
                continue  # has no regulate action
            means = []
            for b in boundaries:
                cells = by_key.get((cond, b), [])
                vals = [r[key] for r in cells if r[key] is not None and r[key] > 0]
                means.append(np.mean(vals) if vals else 0)
            offset = (ci - 0.5) * 0.20  # 3 non-baseline conditions
            ax.bar(np.arange(len(boundaries)) + offset, means, 0.18,
                   color=COND_COLORS[cond], alpha=0.92,
                   label=COND_LABEL[cond], edgecolor="black", linewidth=0.4)
            for i, m in enumerate(means):
                ax.text(i + offset, m + 0.015, f"{m:.2f}",
                        ha="center", fontsize=8)
        ax.set_xticks(np.arange(len(boundaries)))
        ax.set_xticklabels([f"E={b}" for b in boundaries], fontsize=10)
        ax.set_ylabel(ylabel, fontsize=10)
        ax.set_ylim(ylim)
        ax.axhline(0.65, color="black", linewidth=0.4, linestyle=":")
        ax.legend(loc="upper left", fontsize=9)
        ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.suptitle(
        "Regulate usage diagnostics: rate is high (~0.5+) but specificity is LOW (~0.15) — "
        "regulate is NOT used preferentially at uncertain states.",
        fontsize=12, y=1.02,
    )
    fig.tight_layout()
    out = FIG_DIR / "fig2_regulate_metrics.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # Figure 3: boundary occupancy
    fig, ax = plt.subplots(figsize=(11, 5.5))
    for ci, cond in enumerate(conds):
        means = []
        stds = []
        for b in boundaries:
            cells = by_key.get((cond, b), [])
            vals = [r["boundary_occupancy"] for r in cells]
            means.append(np.mean(vals) if vals else 0)
            stds.append(np.std(vals) if len(vals) > 1 else 0)
        offset = (ci - (len(conds) - 1) / 2) * 0.20
        ax.bar(np.arange(len(boundaries)) + offset, means, 0.18, yerr=stds,
               color=COND_COLORS[cond], alpha=0.92,
               label=COND_LABEL[cond], edgecolor="black", linewidth=0.4)
        for i, m in enumerate(means):
            ax.text(i + offset, m + 0.005, f"{m:.3f}",
                    ha="center", fontsize=8)
    ax.set_xticks(np.arange(len(boundaries)))
    ax.set_xticklabels([f"boundary E={b}" for b in boundaries], fontsize=10)
    ax.set_ylabel("Boundary occupancy\n(fraction of steps |E−boundary|<0.06)",
                  fontsize=10)
    ax.legend(loc="upper right", fontsize=9)
    ax.set_title(
        "Boundary occupancy is uniformly low (~0.04) across conditions. "
        "Allostatic mechanism is NOT working through 'avoid the boundary state'.",
        fontsize=11,
    )
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig3_boundary_occupancy.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # Figure 4: per-E margin sign accuracy at boundary E=0.5
    fig, ax = plt.subplots(figsize=(13, 5.5))
    E_grid = [0.1, 0.2, 0.3, 0.4, 0.45, 0.5, 0.55, 0.6, 0.7, 0.8, 0.9]
    for cond in conds:
        cells = by_key.get((cond, 0.5), [])
        means = []
        for E in E_grid:
            vals = [r[f"acc@E={E}"] for r in cells]
            means.append(np.mean(vals) if vals else 0)
        ax.plot(E_grid, means, "o-", color=COND_COLORS[cond], linewidth=2.2,
                markersize=7, label=COND_LABEL[cond])
    ax.axvline(0.5, color="black", linewidth=0.6, linestyle="--", alpha=0.5)
    ax.text(0.51, 0.55, "boundary", fontsize=9)
    ax.set_xlabel("Internal state E", fontsize=11)
    ax.set_ylabel("Margin sign accuracy", fontsize=11)
    ax.set_ylim(0.3, 1.05)
    ax.axhline(0.5, color="gray", linewidth=0.4, linestyle=":")
    ax.legend(loc="lower right", fontsize=9)
    ax.set_title(
        "Per-E calibration at boundary E=0.5: all conditions fail at exactly 0.5 (the boundary). "
        "Mechanism is NOT 'fix the singular point' — it's behavioral avoidance.",
        fontsize=11,
    )
    ax.grid(linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig4_per_E_at_boundary_05.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # Summary
    summary = {}
    for cond in conds:
        per_b = {}
        for b in boundaries:
            cells = by_key.get((cond, b), [])
            if not cells:
                continue
            rs_vals = [r["regulate_specificity"] for r in cells
                       if r["regulate_specificity"] is not None and r["regulate_specificity"] > 0]
            per_b[f"boundary={b}"] = dict(
                mean_return=float(np.mean([r["mean_return"] for r in cells])),
                action_accuracy=float(np.mean([r["action_accuracy"] for r in cells if r["action_accuracy"] is not None])),
                boundary_occupancy=float(np.mean([r["boundary_occupancy"] for r in cells])),
                regulate_rate=float(np.mean([r["regulate_rate"] for r in cells])),
                regulate_specificity=float(np.mean(rs_vals)) if rs_vals else None,
                consume_skip_accuracy=float(np.mean([r["consume_skip_accuracy"] for r in cells if r["consume_skip_accuracy"] is not None])),
                acc_at_boundary=float(np.mean([r[f"acc@E={b}"] for r in cells])),
            )
        summary[cond] = per_b
    out_path = ROOT / "artifacts" / "allostatic_control" / "summary_v1.json"
    out_path.write_text(json.dumps(summary, indent=2))
    print(f"\nsummary:")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
