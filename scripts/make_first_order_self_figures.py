#!/usr/bin/env python3
"""Figures for Paper 16 — First-Order Self / Reafference."""

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

FIG_DIR = ROOT / "papers" / "first_order_self" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

COND_COLORS = {
    "total_dV_head": "#7f7f7f",
    "factorized_self_world": "#d62728",
    "oracle_source": "#2ca02c",
    "shuffled_source": "#9467bd",
}
COND_LABEL = {
    "total_dV_head": "total ΔV head\n(no factorization)",
    "factorized_self_world": "factorized self|world\n(HEADLINE — fails)",
    "oracle_source": "oracle source labels\n(upper bound)",
    "shuffled_source": "shuffled labels\n(control)",
}


def main() -> int:
    data = json.loads(
        (ROOT / "artifacts" / "first_order_self" / "sweep_v1.json").read_text()
    )
    rows = data["summary"]
    conds = data["manifest"]["conditions"]
    by_cond = defaultdict(list)
    for r in rows:
        by_cond[r["condition"]].append(r)

    # Figure 1: predictions per role across conditions
    # Show: pred_consume vs true_self vs true_total_in_dist vs true_total_shift
    fig, axes = plt.subplots(1, 4, figsize=(20, 5.5), sharey=True)
    roles = ["food", "poison", "medicine", "neutral"]
    for role_idx, role in enumerate(roles):
        ax = axes[role_idx]
        x = np.arange(len(conds))
        # For each condition, show predicted consume value
        for ci, cond in enumerate(conds):
            cells = by_cond[cond]
            preds = [r[f"pred_{role}_consume"] for r in cells]
            mean_pred = np.mean(preds)
            std_pred = np.std(preds) if len(preds) > 1 else 0
            ax.bar(ci, mean_pred, 0.7, yerr=std_pred, color=COND_COLORS[cond],
                   alpha=0.92, edgecolor="black", linewidth=0.4)
            ax.text(ci, mean_pred + 0.05 if mean_pred >= 0 else mean_pred - 0.1,
                    f"{mean_pred:+.2f}", ha="center", fontsize=9, fontweight="bold")
        # True self consume (action effect minus decay)
        true_self = rows[0][f"true_self_{role}_consume"]
        # True total in-dist
        true_total_in_dist = rows[0][f"true_total_in_dist_{role}_consume"]
        # True total shift
        true_total_shift = rows[0][f"true_total_shift_{role}_consume"]
        ax.axhline(true_self, color="green", linewidth=1.5, linestyle="--",
                   alpha=0.7, label=f"true self ({true_self:+.2f})")
        ax.axhline(true_total_in_dist, color="orange", linewidth=1.0, linestyle=":",
                   alpha=0.6, label=f"true total in-dist ({true_total_in_dist:+.2f})")
        if role in ("medicine", "food"):  # only show shift line where it differs
            ax.axhline(true_total_shift, color="red", linewidth=1.0, linestyle="-.",
                       alpha=0.6, label=f"true total shift ({true_total_shift:+.2f})")
        ax.set_xticks(x)
        ax.set_xticklabels([COND_LABEL[c] for c in conds], fontsize=7, rotation=15)
        ax.set_title(f"{role}", fontsize=11)
        ax.axhline(0, color="black", linewidth=0.3)
        ax.set_ylim(-2.0, 2.0)
        if role_idx == 0:
            ax.set_ylabel("Predicted self ΔE for consume", fontsize=10)
        ax.legend(loc="best", fontsize=7)
        ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.suptitle(
        "Predicted self ΔE per role × condition. Oracle (green) recovers true self component. "
        "Factorized (red) is gauge-symmetric: overshoots truth, world_head compensates.",
        fontsize=12, y=1.02,
    )
    fig.tight_layout()
    out = FIG_DIR / "fig1_predictions_per_role.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # Figure 2: return + acc by condition × distribution
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    for ax_idx, (key_base, ylabel, ylim) in enumerate([
        ("return", "Mean return", (0, 55)),
        ("acc", "Action accuracy", (0, 1.08)),
    ]):
        ax = axes[ax_idx]
        x = np.arange(len(conds))
        w = 0.4
        for dist_idx, (dist_key, dist_label) in enumerate([
            ("in_dist", "in-distribution"),
            ("shifted", "shifted"),
        ]):
            means = []
            for cond in conds:
                cells = by_cond[cond]
                vals = [r[f"{dist_key}_{key_base}"] for r in cells]
                means.append(np.mean(vals))
            offset = (dist_idx - 0.5) * w
            c = "#1f77b4" if dist_idx == 0 else "#d62728"
            ax.bar(x + offset, means, w, color=c, alpha=0.85,
                   label=dist_label if ax_idx == 0 else None,
                   edgecolor="black", linewidth=0.4)
            for i, m in enumerate(means):
                fmt = f"{m:.1f}" if key_base == "return" else f"{m:.2f}"
                offset_y = 1.0 if key_base == "return" else 0.015
                ax.text(x[i] + offset, m + offset_y, fmt,
                        ha="center", fontsize=8)
        ax.set_xticks(x)
        ax.set_xticklabels([COND_LABEL[c] for c in conds], fontsize=8)
        ax.set_ylabel(ylabel, fontsize=11)
        ax.set_ylim(ylim)
        if key_base == "return":
            ax.axhline(50, color="gray", linewidth=0.4, linestyle=":")
            ax.legend(loc="lower left", fontsize=10)
        else:
            ax.axhline(0.5, color="gray", linewidth=0.4, linestyle=":")
        ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.suptitle(
        "Return saturates at 50 across all conditions; action accuracy reflects action-difference preservation",
        fontsize=12, y=1.02,
    )
    fig.tight_layout()
    out = FIG_DIR / "fig2_return_and_accuracy.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # Figure 3: prediction error vs true_self
    # For each condition, plot mean (pred - true_self) per role
    fig, ax = plt.subplots(figsize=(11, 5.5))
    x = np.arange(len(roles))
    w = 0.18
    for ci, cond in enumerate(conds):
        cells = by_cond[cond]
        errors = []
        for role in roles:
            preds = np.array([r[f"pred_{role}_consume"] for r in cells])
            true_self = rows[0][f"true_self_{role}_consume"]
            errors.append(np.mean(preds - true_self))
        offset = (ci - (len(conds) - 1) / 2) * w
        ax.bar(x + offset, errors, w * 0.92, color=COND_COLORS[cond],
               alpha=0.92, label=COND_LABEL[cond],
               edgecolor="black", linewidth=0.4)
        for i, m in enumerate(errors):
            ax.text(x[i] + offset, m + 0.03 if m >= 0 else m - 0.06,
                    f"{m:+.2f}", ha="center", fontsize=8)
    ax.axhline(0, color="black", linewidth=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(roles, fontsize=10)
    ax.set_ylabel("Predicted self − true self", fontsize=11)
    ax.legend(loc="upper right", fontsize=9)
    ax.set_title(
        "Self-prediction error per role. Oracle ≈ 0 (recovers true self). "
        "Factorized ≠ 0 (gauge-symmetric overshoot).",
        fontsize=12,
    )
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig3_self_prediction_error.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # Summary
    summary = {}
    for cond in conds:
        cells = by_cond[cond]
        per_role = {}
        for role in roles:
            preds = np.array([r[f"pred_{role}_consume"] for r in cells])
            true_self = rows[0][f"true_self_{role}_consume"]
            per_role[role] = dict(
                mean_pred_consume=float(np.mean(preds)),
                true_self_consume=float(true_self),
                bias=float(np.mean(preds - true_self)),
            )
        summary[cond] = dict(
            in_dist_return=float(np.mean([r["in_dist_return"] for r in cells])),
            shifted_return=float(np.mean([r["shifted_return"] for r in cells])),
            in_dist_acc=float(np.mean([r["in_dist_acc"] for r in cells])),
            shifted_acc=float(np.mean([r["shifted_acc"] for r in cells])),
            per_role=per_role,
        )
    out_path = ROOT / "artifacts" / "first_order_self" / "summary_v1.json"
    out_path.write_text(json.dumps(summary, indent=2))
    print(f"\nsummary:")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
