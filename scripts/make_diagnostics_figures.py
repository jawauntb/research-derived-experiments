#!/usr/bin/env python3
"""Figures for Paper 11b — Exploration Diagnostics."""

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

FIG_DIR = ROOT / "papers" / "exploration_diagnostics" / "figures"
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
    "biased_only": "biased_only",
    "eps_greedy_decay": "eps_greedy_decay",
    "pred_error_curiosity": "pred_error_curiosity",
    "ensemble_disagree": "ensemble_disagree",
    "expected_info_gain": "MBES\n(expected_info_gain)",
    "uniform_random": "uniform_random",
}
VARIANT_LABEL = {
    "clean_default": "clean (σ=0.15)",
    "wrong_init": "wrong-init",
    "high_noise": "σ=0.50",
}


def main() -> int:
    data = json.loads(
        (ROOT / "artifacts" / "exploration_diagnostics" / "sweep_v1.json").read_text()
    )
    rows = data["summary"]
    conds = data["manifest"]["conditions"]
    variants = data["manifest"]["variants"]

    by_key = defaultdict(list)
    for r in rows:
        by_key[(r["condition"], r["variant"])].append(r)

    # ============ Figure 1: calibration table-as-figure ============
    # Heatmap of margin_sign_acc per condition × variant
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.5), sharey=True)
    for ax_idx, (metric_key, title) in enumerate([
        ("margin_sign_acc", "Margin sign accuracy (1.0 = always picks optimal)"),
        ("action_accuracy", "Eval action accuracy"),
    ]):
        ax = axes[ax_idx]
        mat = np.zeros((len(conds), len(variants)))
        for ci, cond in enumerate(conds):
            for vi, variant in enumerate(variants):
                cells = by_key.get((cond, variant), [])
                vals = [r[metric_key] for r in cells]
                mat[ci, vi] = np.mean(vals) if vals else 0
        im = ax.imshow(mat, cmap="RdYlGn", aspect="auto", vmin=0.4, vmax=1.0)
        for ci in range(len(conds)):
            for vi in range(len(variants)):
                ax.text(vi, ci, f"{mat[ci, vi]:.3f}", ha="center", va="center",
                        fontsize=10, fontweight="bold",
                        color="black" if mat[ci, vi] > 0.65 else "white")
        ax.set_xticks(range(len(variants)))
        ax.set_xticklabels([VARIANT_LABEL[v] for v in variants], fontsize=10)
        ax.set_yticks(range(len(conds)))
        ax.set_yticklabels([COND_LABEL[c].replace("\n", " ") for c in conds], fontsize=9)
        ax.set_title(title, fontsize=11)
        plt.colorbar(im, ax=ax, fraction=0.04)
    fig.suptitle(
        "Extended diagnostic table: margin-sign accuracy cleanly separates working from failing methods",
        fontsize=12, y=1.02,
    )
    fig.tight_layout()
    out = FIG_DIR / "fig1_calibration_table.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ============ Figure 2: wrong-init vs clean ============
    fig, ax = plt.subplots(figsize=(12, 5.5))
    x = np.arange(len(conds))
    w = 0.4
    for vi, variant in enumerate(["clean_default", "wrong_init"]):
        means = []
        stds = []
        for cond in conds:
            cells = by_key.get((cond, variant), [])
            vals = [r["action_accuracy"] for r in cells]
            means.append(np.mean(vals) if vals else 0)
            stds.append(np.std(vals) if len(vals) > 1 else 0)
        offset = (vi - 0.5) * w
        c = "#2ca02c" if variant == "clean_default" else "#d62728"
        ax.bar(x + offset, means, w, yerr=stds, color=c, alpha=0.85,
               label=VARIANT_LABEL[variant], edgecolor="black", linewidth=0.4)
        for i, m in enumerate(means):
            ax.text(x[i] + offset, m + 0.015, f"{m:.3f}",
                    ha="center", fontsize=9, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([COND_LABEL[c] for c in conds], fontsize=8)
    ax.set_ylabel("Eval action accuracy", fontsize=11)
    ax.axhline(0.5, color="gray", linewidth=0.4, linestyle=":")
    ax.axhline(0.9, color="black", linewidth=0.4, linestyle=":")
    ax.set_ylim(0, 1.08)
    ax.legend(loc="lower right", fontsize=10)
    ax.set_title(
        "Wrong-init test: MBES (expected_info_gain) and uniform_random "
        "partially recover; ε-greedy collapses",
        fontsize=12,
    )
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig2_wrong_init_vs_clean.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ============ Figure 3: high noise ============
    fig, ax = plt.subplots(figsize=(12, 5.5))
    for vi, variant in enumerate(["clean_default", "high_noise"]):
        means = []
        stds = []
        for cond in conds:
            cells = by_key.get((cond, variant), [])
            vals = [r["action_accuracy"] for r in cells]
            means.append(np.mean(vals) if vals else 0)
            stds.append(np.std(vals) if len(vals) > 1 else 0)
        offset = (vi - 0.5) * w
        c = "#2ca02c" if variant == "clean_default" else "#d62728"
        ax.bar(x + offset, means, w, yerr=stds, color=c, alpha=0.85,
               label=VARIANT_LABEL[variant], edgecolor="black", linewidth=0.4)
        for i, m in enumerate(means):
            ax.text(x[i] + offset, m + 0.015, f"{m:.3f}",
                    ha="center", fontsize=9, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([COND_LABEL[c] for c in conds], fontsize=8)
    ax.set_ylabel("Eval action accuracy", fontsize=11)
    ax.axhline(0.5, color="gray", linewidth=0.4, linestyle=":")
    ax.set_ylim(0, 1.08)
    ax.legend(loc="upper right", fontsize=10)
    ax.set_title(
        "High noise (σ=0.50): every mechanism collapses — encoder-capacity limit, not exploration limit",
        fontsize=12,
    )
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig3_high_noise.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ============ Summary ============
    summary = {}
    for cond in conds:
        per_variant = {}
        for variant in variants:
            cells = by_key.get((cond, variant), [])
            if not cells:
                continue
            per_variant[variant] = dict(
                action_accuracy=float(np.mean([r["action_accuracy"] for r in cells])),
                margin_sign_acc=float(np.mean([r["margin_sign_acc"] for r in cells])),
                consume_mse=float(np.mean([r["consume_mse"] for r in cells])),
                skip_mse=float(np.mean([r["skip_mse"] for r in cells])),
                margin_mse=float(np.mean([r["margin_mse"] for r in cells])),
                reward_gap=float(np.mean([r["reward_gap"] for r in cells])),
            )
        summary[cond] = per_variant
    out_path = ROOT / "artifacts" / "exploration_diagnostics" / "summary_v1.json"
    out_path.write_text(json.dumps(summary, indent=2))
    print(f"\nsummary:")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
