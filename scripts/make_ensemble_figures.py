#!/usr/bin/env python3
"""Figures for Paper 14b — Calibrated Ensemble Uncertainty."""

from __future__ import annotations

import json
import sys
import math
from pathlib import Path
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

FIG_DIR = ROOT / "papers" / "ensemble_uncertainty" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

COND_COLORS = {
    "single_head_greedy": "#7f7f7f",
    "ensemble_mean_greedy": "#1f77b4",
    "ensemble_LCB": "#2ca02c",
    "ensemble_UCB": "#ff7f0e",
    "ensemble_uncertainty_regulate": "#9467bd",
    "margin_confidence_planner": "#d62728",
    "oracle_boundary_feature": "#bcbd22",
}
COND_LABEL = {
    "single_head_greedy": "single head\ngreedy (P14)",
    "ensemble_mean_greedy": "ensemble\nmean greedy",
    "ensemble_LCB": "ensemble LCB\n(risk-averse)",
    "ensemble_UCB": "ensemble UCB\n(optimistic)",
    "ensemble_uncertainty_regulate": "uncertainty-\ntriggered regulate",
    "margin_confidence_planner": "margin-confidence\n(P14 failed)",
    "oracle_boundary_feature": "oracle 1[E<0.5]\n(upper bound)",
}


def main() -> int:
    data = json.loads(
        (ROOT / "artifacts" / "ensemble_uncertainty" / "sweep_v1.json").read_text()
    )
    rows = data["summary"]
    full_results = data["results"]
    conds = data["manifest"]["conditions"]

    by_cond = defaultdict(list)
    for r in rows:
        by_cond[r["condition"]].append(r)

    # Figure 1: return + accuracy per condition
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.5))
    x = np.arange(len(conds))
    for ax_idx, (key, label, ylim) in enumerate([
        ("mean_return", "Mean return", (0, 55)),
        ("action_accuracy", "Eval action accuracy", (0, 1.08)),
    ]):
        ax = axes[ax_idx]
        means = []; stds = []
        for cond in conds:
            cells = by_cond[cond]
            vals = [r[key] for r in cells if r[key] is not None]
            means.append(np.mean(vals) if vals else 0)
            stds.append(np.std(vals) if len(vals) > 1 else 0)
        ax.bar(x, means, 0.7, yerr=stds,
               color=[COND_COLORS[c] for c in conds], alpha=0.92,
               edgecolor="black", linewidth=0.4)
        for i, m in enumerate(means):
            fmt = f"{m:.1f}" if key == "mean_return" else f"{m:.2f}"
            ax.text(x[i], m + (1.0 if key == "mean_return" else 0.02), fmt,
                    ha="center", fontsize=9, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels([COND_LABEL[c] for c in conds], fontsize=8)
        ax.set_ylabel(label, fontsize=11)
        ax.set_ylim(ylim)
        if key == "mean_return":
            ax.axhline(50, color="gray", linewidth=0.4, linestyle=":")
        else:
            ax.axhline(0.5, color="gray", linewidth=0.4, linestyle=":")
            ax.axhline(0.9, color="black", linewidth=0.4, linestyle=":")
        ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.suptitle(
        "Headline: ensemble averaging gives small lift over single head; "
        "LCB slightly beats mean; UCB hurts. None rescue to oracle level.",
        fontsize=12, y=1.02,
    )
    fig.tight_layout()
    out = FIG_DIR / "fig1_return_and_acc.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # Figure 2: variance vs E (the key calibration plot)
    # Aggregate calibration records per condition
    fig, ax = plt.subplots(figsize=(13, 5.5))
    for cond in conds:
        # Get cells with K>1 ensembles only
        cells = [r for r in full_results if r["condition"] == cond and r.get("K", 1) > 1]
        if not cells:
            continue
        # Each cell has cal_records: list of dicts with E_grid, mean_item_var
        # Aggregate across cells
        per_E_vars = defaultdict(list)
        for cell in cells:
            for rec in cell["cal_records"]:
                per_E_vars[rec["E_grid"]].append(rec["mean_item_var"])
        E_sorted = sorted(per_E_vars.keys())
        means = [np.mean(per_E_vars[e]) for e in E_sorted]
        stds = [np.std(per_E_vars[e]) if len(per_E_vars[e]) > 1 else 0 for e in E_sorted]
        ax.plot(E_sorted, means, "o-", color=COND_COLORS[cond],
                linewidth=2.0, markersize=6, label=COND_LABEL[cond])
        ax.fill_between(E_sorted, [m - s for m, s in zip(means, stds)],
                        [m + s for m, s in zip(means, stds)],
                        color=COND_COLORS[cond], alpha=0.15)
    ax.axvline(0.5, color="black", linewidth=0.6, linestyle="--", alpha=0.5)
    ax.text(0.51, ax.get_ylim()[1] * 0.95, "boundary", fontsize=9)
    ax.set_xlabel("Internal state E", fontsize=11)
    ax.set_ylabel("Mean per-item ensemble variance (K=5)", fontsize=11)
    ax.legend(loc="upper right", fontsize=9)
    ax.set_title(
        "G1 falsified: ensemble variance is FLAT across E. The 5 heads agree at E=0.5 — "
        "they all converge to the same smoothed wrong answer.",
        fontsize=11,
    )
    ax.grid(linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig2_variance_vs_E.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # Figure 3: error vs variance scatter (G2 falsification)
    fig, ax = plt.subplots(figsize=(11, 5.5))
    all_errors = []
    all_vars = []
    for cell in full_results:
        if cell.get("K", 1) <= 1:
            continue
        for rec in cell["cal_records"]:
            err = 1.0 - rec["margin_sign_acc"]
            all_errors.append(err)
            all_vars.append(rec["mean_item_var"])
    ax.scatter(all_vars, all_errors, s=30, alpha=0.5, color="#1f77b4",
               edgecolor="white", linewidth=0.5)
    if len(all_vars) > 1 and np.std(all_vars) > 0:
        corr = np.corrcoef(all_vars, all_errors)[0, 1]
        # Add trendline
        z = np.polyfit(all_vars, all_errors, 1)
        p = np.poly1d(z)
        xs = np.linspace(min(all_vars), max(all_vars), 100)
        ax.plot(xs, p(xs), "k--", linewidth=1.2, alpha=0.6,
                label=f"correlation r = {corr:+.3f}")
    ax.set_xlabel("Ensemble variance (mean per-item)", fontsize=11)
    ax.set_ylabel("Margin sign error (1 - acc)", fontsize=11)
    ax.legend(loc="upper right", fontsize=10)
    ax.set_title(
        "G2 falsified: error and variance are essentially UNCORRELATED. "
        "The ensemble is overconfident-wrong as a whole, not uncertain where it's wrong.",
        fontsize=11,
    )
    ax.grid(linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig3_error_vs_variance.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # Figure 4: per-E accuracy across conditions
    fig, ax = plt.subplots(figsize=(13, 5.5))
    for cond in conds:
        cells = [r for r in full_results if r["condition"] == cond]
        if not cells:
            continue
        per_E_acc = defaultdict(list)
        for cell in cells:
            for rec in cell["cal_records"]:
                per_E_acc[rec["E_grid"]].append(rec["margin_sign_acc"])
        E_sorted = sorted(per_E_acc.keys())
        means = [np.mean(per_E_acc[e]) for e in E_sorted]
        ax.plot(E_sorted, means, "o-", color=COND_COLORS[cond],
                linewidth=2.0, markersize=6, label=COND_LABEL[cond])
    ax.axvline(0.5, color="black", linewidth=0.6, linestyle="--", alpha=0.5)
    ax.set_xlabel("Internal state E", fontsize=11)
    ax.set_ylabel("Margin sign accuracy", fontsize=11)
    ax.set_ylim(0.3, 1.05)
    ax.axhline(0.5, color="gray", linewidth=0.4, linestyle=":")
    ax.legend(loc="lower right", fontsize=9)
    ax.set_title(
        "Per-E calibration: oracle (gold) is perfect; all ensembles still fail at exactly E=0.5",
        fontsize=11,
    )
    ax.grid(linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig4_per_E_accuracy.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # Summary
    summary = {}
    for cond in conds:
        cells = by_cond[cond]
        if not cells:
            continue
        evc_vals = [r["error_variance_correlation"] for r in cells
                    if r["error_variance_correlation"] is not None and not math.isnan(r["error_variance_correlation"])]
        rh_vals = [r["regulate_high_var_specificity"] for r in cells
                   if r["regulate_high_var_specificity"] is not None and r["regulate_high_var_specificity"] > 0]
        summary[cond] = dict(
            mean_return=float(np.mean([r["mean_return"] for r in cells])),
            action_accuracy=float(np.mean([r["action_accuracy"] for r in cells if r["action_accuracy"] is not None])),
            var_at_E05=float(np.mean([r["var_at_E05"] for r in cells])),
            var_ratio_05_vs_neighbors=float(np.mean([r["var_ratio_05_vs_neighbors"] for r in cells])),
            error_variance_correlation=float(np.mean(evc_vals)) if evc_vals else None,
            regulate_high_var_specificity=float(np.mean(rh_vals)) if rh_vals else None,
            mean_regulate_events=float(np.mean([r["n_regulate_events"] for r in cells])),
        )
    out_path = ROOT / "artifacts" / "ensemble_uncertainty" / "summary_v1.json"
    out_path.write_text(json.dumps(summary, indent=2))
    print(f"\nsummary:")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
