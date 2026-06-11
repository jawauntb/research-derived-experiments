#!/usr/bin/env python3
"""Figures for Paper 16b — Identifiability Through Intervention."""

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

FIG_DIR = ROOT / "papers" / "null_intervention" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

COND_COLORS = {
    "total_dV_head": "#7f7f7f",
    "factorized_no_null": "#d62728",
    "factorized_null_passive": "#ff7f0e",
    "factorized_null_anchor": "#2ca02c",
    "oracle_source": "#1f77b4",
}
COND_LABEL = {
    "total_dV_head": "total ΔV\n(no factorize)",
    "factorized_no_null": "factorized\nno null (P16 fail)",
    "factorized_null_passive": "factorized\n+ null passive",
    "factorized_null_anchor": "factorized\n+ null anchor\n(HEADLINE)",
    "oracle_source": "oracle source\n(upper bound)",
}


def main() -> int:
    data = json.loads(
        (ROOT / "artifacts" / "null_intervention" / "sweep_v1.json").read_text()
    )
    rows = data["summary"]
    conds = data["manifest"]["conditions"]
    by_cond = defaultdict(list)
    for r in rows:
        by_cond[r["condition"]].append(r)

    roles = ["food", "poison", "medicine", "neutral"]

    # Figure 1: per-role self_consume prediction with true reference
    fig, axes = plt.subplots(1, 4, figsize=(18, 5.5), sharey=True)
    for ri, role in enumerate(roles):
        ax = axes[ri]
        x = np.arange(len(conds))
        for ci, cond in enumerate(conds):
            cells = by_cond[cond]
            preds = np.array([r[f"pred_self_consume_{role}"] for r in cells])
            mean = np.mean(preds)
            std = np.std(preds) if len(preds) > 1 else 0
            ax.bar(ci, mean, 0.7, yerr=std, color=COND_COLORS[cond],
                   alpha=0.92, edgecolor="black", linewidth=0.4)
            ax.text(ci, mean + (0.05 if mean >= 0 else -0.1),
                    f"{mean:+.2f}", ha="center", fontsize=9, fontweight="bold")
        true_self = rows[0][f"true_self_consume_{role}"]
        ax.axhline(true_self, color="green", linewidth=1.8, linestyle="--",
                   alpha=0.7, label=f"true ({true_self:+.2f})")
        ax.set_xticks(x)
        ax.set_xticklabels([COND_LABEL[c] for c in conds], fontsize=7, rotation=10)
        ax.set_title(role, fontsize=11)
        if ri == 0:
            ax.set_ylabel("Predicted self ΔE (consume)", fontsize=10)
        ax.axhline(0, color="black", linewidth=0.3)
        ax.legend(loc="best", fontsize=8)
        ax.set_ylim(-2, 2)
        ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.suptitle(
        "Self-component predictions per role × condition. "
        "Null anchor (green) recovers truth; passive null fails worse than no-null.",
        fontsize=12, y=1.02,
    )
    fig.tight_layout()
    out = FIG_DIR / "fig1_self_predictions.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # Figure 2: world prediction per role
    fig, axes = plt.subplots(1, 4, figsize=(18, 5.5), sharey=True)
    factorized_conds = [c for c in conds if c != "total_dV_head"]
    for ri, role in enumerate(roles):
        ax = axes[ri]
        x = np.arange(len(factorized_conds))
        for ci, cond in enumerate(factorized_conds):
            cells = by_cond[cond]
            preds = [r.get(f"pred_world_{role}") for r in cells if r.get(f"pred_world_{role}") is not None]
            if not preds:
                continue
            mean = np.mean(preds)
            std = np.std(preds) if len(preds) > 1 else 0
            ax.bar(ci, mean, 0.7, yerr=std, color=COND_COLORS[cond],
                   alpha=0.92, edgecolor="black", linewidth=0.4)
            ax.text(ci, mean + (0.02 if mean >= 0 else -0.05),
                    f"{mean:+.3f}", ha="center", fontsize=9, fontweight="bold")
        true_world = rows[0][f"true_world_in_dist_{role}"]
        ax.axhline(true_world, color="green", linewidth=1.8, linestyle="--",
                   alpha=0.7, label=f"true in-dist ({true_world:+.3f})")
        true_world_shift = rows[0][f"true_world_shift_{role}"]
        ax.axhline(true_world_shift, color="orange", linewidth=1.0, linestyle=":",
                   alpha=0.6, label=f"true shifted ({true_world_shift:+.3f})")
        ax.set_xticks(x)
        ax.set_xticklabels([COND_LABEL[c] for c in factorized_conds],
                            fontsize=7, rotation=10)
        ax.set_title(role, fontsize=11)
        if ri == 0:
            ax.set_ylabel("Predicted world ΔE", fontsize=10)
        ax.axhline(0, color="black", linewidth=0.3)
        ax.legend(loc="best", fontsize=7)
        ax.set_ylim(-0.5, 0.5)
        ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.suptitle(
        "World-component predictions per role × condition. Null anchor matches true world expectation.",
        fontsize=12, y=1.02,
    )
    fig.tight_layout()
    out = FIG_DIR / "fig2_world_predictions.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # Figure 3: prediction error (overshoot) reduction
    fig, ax = plt.subplots(figsize=(11, 5.5))
    x = np.arange(len(roles))
    w = 0.18
    for ci, cond in enumerate(conds):
        cells = by_cond[cond]
        errors = []
        for role in roles:
            preds = np.array([r[f"pred_self_consume_{role}"] for r in cells])
            true_self = rows[0][f"true_self_consume_{role}"]
            errors.append(np.mean(preds - true_self))
        offset = (ci - (len(conds) - 1) / 2) * w
        ax.bar(x + offset, errors, w * 0.92, color=COND_COLORS[cond],
               alpha=0.92, label=COND_LABEL[cond],
               edgecolor="black", linewidth=0.4)
        for i, m in enumerate(errors):
            ax.text(x[i] + offset, m + 0.04 if m >= 0 else m - 0.08,
                    f"{m:+.2f}", ha="center", fontsize=7.5)
    ax.axhline(0, color="black", linewidth=0.6)
    ax.set_xticks(x)
    ax.set_xticklabels(roles, fontsize=10)
    ax.set_ylabel("Self prediction error (pred − true)", fontsize=11)
    ax.legend(loc="upper right", fontsize=8)
    ax.set_title(
        "Self prediction error per role. Null anchor (green) drives errors near 0; "
        "passive null is WORSE than no-null.",
        fontsize=12,
    )
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig3_self_prediction_error.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # Figure 4: false-credit reduction headline
    fig, ax = plt.subplots(figsize=(10, 5.5))
    # For food consume: pred - true_self
    x = np.arange(len(conds))
    food_overshoots = []
    for cond in conds:
        cells = by_cond[cond]
        preds = np.array([r["pred_self_consume_food"] for r in cells])
        true_self = rows[0]["true_self_consume_food"]
        food_overshoots.append(float(np.mean(preds - true_self)))
    ax.bar(x, food_overshoots, 0.6, color=[COND_COLORS[c] for c in conds],
           alpha=0.92, edgecolor="black", linewidth=0.4)
    for i, m in enumerate(food_overshoots):
        ax.text(x[i], m + 0.03 if m >= 0 else m - 0.07,
                f"{m:+.2f}", ha="center", fontsize=12, fontweight="bold")
    # Annotate the reduction
    p16_overshoot = next(o for c, o in zip(conds, food_overshoots) if c == "factorized_no_null")
    anchor_overshoot = next(o for c, o in zip(conds, food_overshoots) if c == "factorized_null_anchor")
    reduction = (1 - anchor_overshoot / p16_overshoot) * 100
    ax.axhline(0, color="black", linewidth=0.6)
    ax.set_xticks(x)
    ax.set_xticklabels([COND_LABEL[c] for c in conds], fontsize=9)
    ax.set_ylabel("Food self_consume overshoot (pred − +0.96 true)", fontsize=11)
    ax.set_title(
        f"Food self overshoot. Null anchor reduces P16's +{p16_overshoot:.2f} overshoot "
        f"to +{anchor_overshoot:.2f} ({reduction:.0f}% reduction)",
        fontsize=12,
    )
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig4_false_credit_reduction.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # Summary
    summary = {}
    for cond in conds:
        cells = by_cond[cond]
        per_role = {}
        for role in roles:
            preds_self = np.array([r[f"pred_self_consume_{role}"] for r in cells])
            true_self = rows[0][f"true_self_consume_{role}"]
            world_preds = [r.get(f"pred_world_{role}") for r in cells if r.get(f"pred_world_{role}") is not None]
            true_world = rows[0][f"true_world_in_dist_{role}"]
            per_role[role] = dict(
                mean_pred_self_consume=float(np.mean(preds_self)),
                true_self_consume=float(true_self),
                self_bias=float(np.mean(preds_self - true_self)),
                mean_pred_world=float(np.mean(world_preds)) if world_preds else None,
                true_world_in_dist=float(true_world),
                world_bias=float(np.mean(world_preds) - true_world) if world_preds else None,
            )
        summary[cond] = dict(
            in_dist_return=float(np.mean([r["in_dist_return"] for r in cells])),
            shifted_return=float(np.mean([r["shifted_return"] for r in cells])),
            in_dist_acc=float(np.mean([r["in_dist_acc"] for r in cells])),
            shifted_acc=float(np.mean([r["shifted_acc"] for r in cells])),
            per_role=per_role,
        )
    out_path = ROOT / "artifacts" / "null_intervention" / "summary_v1.json"
    out_path.write_text(json.dumps(summary, indent=2))
    print(f"\nsummary:")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
