#!/usr/bin/env python3
"""Figures for Paper 15 — Tapestry of Valence."""

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

FIG_DIR = ROOT / "papers" / "valence_tapestry" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

COND_COLORS = {
    "vector_dV_head": "#2ca02c",
    "scalar_drive_head": "#d62728",
    "energy_only_head": "#1f77b4",
    "damage_only_head": "#9467bd",
    "oracle_role_labels": "#bcbd22",
}
COND_LABEL = {
    "vector_dV_head": "vector ΔV head\n(HEADLINE)",
    "scalar_drive_head": "scalar drive head\n(collapses dims)",
    "energy_only_head": "energy-only head",
    "damage_only_head": "damage-only head",
    "oracle_role_labels": "oracle role labels\n(upper bound)",
}
CTX_LABEL = {
    "balanced": "balanced\nw_E=1, w_D=1",
    "hungry_priority": "hungry priority\nw_E=2, w_D=1",
    "injured_priority": "injured priority\nw_E=1, w_D=2",
}
ROLE_LABEL = {"food": "food", "poison": "poison",
              "medicine": "medicine", "neutral": "neutral"}


def main() -> int:
    data = json.loads(
        (ROOT / "artifacts" / "valence_tapestry" / "sweep_v1.json").read_text()
    )
    rows = data["summary"]
    conds = data["manifest"]["conditions"]

    by_cond = defaultdict(list)
    for r in rows:
        by_cond[r["condition"]].append(r)

    # Figure 1: return + accuracy per condition × context
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.5))
    contexts = ["balanced", "hungry_priority", "injured_priority"]
    x = np.arange(len(contexts))
    w = 0.18
    for ax_idx, (metric_suffix, ylabel, ylim) in enumerate([
        ("_return", "Mean return", (0, 55)),
        ("_accuracy", "Action accuracy", (0, 1.08)),
    ]):
        ax = axes[ax_idx]
        for ci, cond in enumerate(conds):
            means = []; stds = []
            for ctx in contexts:
                cells = by_cond[cond]
                vals = [r[f"{ctx}{metric_suffix}"] for r in cells]
                means.append(np.mean(vals) if vals else 0)
                stds.append(np.std(vals) if len(vals) > 1 else 0)
            offset = (ci - (len(conds) - 1) / 2) * w
            ax.bar(x + offset, means, w * 0.92, yerr=stds,
                   color=COND_COLORS[cond], alpha=0.92,
                   label=COND_LABEL[cond], edgecolor="black", linewidth=0.4)
            for i, m in enumerate(means):
                fmt = f"{m:.1f}" if metric_suffix == "_return" else f"{m:.2f}"
                offset_y = 1.0 if metric_suffix == "_return" else 0.015
                ax.text(x[i] + offset, m + offset_y, fmt,
                        ha="center", fontsize=7)
        ax.set_xticks(x)
        ax.set_xticklabels([CTX_LABEL[c] for c in contexts], fontsize=9)
        ax.set_ylabel(ylabel, fontsize=11)
        ax.set_ylim(ylim)
        if metric_suffix == "_return":
            ax.axhline(50, color="gray", linewidth=0.4, linestyle=":")
        else:
            ax.axhline(0.5, color="gray", linewidth=0.4, linestyle=":")
        if ax_idx == 1:
            ax.legend(loc="lower left", fontsize=8)
        ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.suptitle(
        "Return and accuracy across weight contexts. Vector head has stable accuracy across shifts.",
        fontsize=12, y=1.02,
    )
    fig.tight_layout()
    out = FIG_DIR / "fig1_return_and_accuracy.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # Figure 2: per-role accuracy under each context
    fig, axes = plt.subplots(1, 3, figsize=(18, 5.5), sharey=True)
    roles = ["food", "poison", "medicine", "neutral"]
    x_r = np.arange(len(roles))
    w_r = 0.18
    for ctx_idx, ctx in enumerate(contexts):
        ax = axes[ctx_idx]
        for ci, cond in enumerate(conds):
            cells = by_cond[cond]
            means = []
            for role in roles:
                key = f"{ctx}_role_{role}_acc"
                vals = [r[key] for r in cells if r[key] is not None]
                means.append(np.mean(vals) if vals else 0)
            offset = (ci - (len(conds) - 1) / 2) * w_r
            ax.bar(x_r + offset, means, w_r * 0.92, color=COND_COLORS[cond],
                   alpha=0.92, label=COND_LABEL[cond] if ctx_idx == 0 else None,
                   edgecolor="black", linewidth=0.4)
            for i, m in enumerate(means):
                ax.text(x_r[i] + offset, m + 0.02, f"{m:.2f}",
                        ha="center", fontsize=7)
        ax.set_xticks(x_r)
        ax.set_xticklabels([ROLE_LABEL[r] for r in roles], fontsize=10)
        if ctx_idx == 0:
            ax.set_ylabel("Action accuracy", fontsize=11)
        ax.set_title(CTX_LABEL[ctx].replace("\n", " "), fontsize=11)
        ax.set_ylim(0, 1.15)
        ax.axhline(0.5, color="gray", linewidth=0.4, linestyle=":")
        ax.grid(axis="y", linestyle=":", alpha=0.4)
    handles, lbls = axes[0].get_legend_handles_labels()
    fig.legend(handles, lbls, loc="upper center",
               bbox_to_anchor=(0.5, 1.06), ncol=5, fontsize=8)
    fig.suptitle(
        "Per-role accuracy by context. KEY: vector handles medicine context-sensitively "
        "(0.46→0.82→0.73); scalar's medicine handling INVERTS (0.54→0.27→0.72).",
        fontsize=11, y=1.12,
    )
    fig.tight_layout()
    out = FIG_DIR / "fig2_per_role_per_context.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # Figure 3: medicine accuracy zoom (the headline)
    fig, ax = plt.subplots(figsize=(11, 5.5))
    x_c = np.arange(len(contexts))
    w_c = 0.16
    for ci, cond in enumerate(conds):
        cells = by_cond[cond]
        means = []; stds = []
        for ctx in contexts:
            key = f"{ctx}_role_medicine_acc"
            vals = [r[key] for r in cells if r[key] is not None]
            means.append(np.mean(vals) if vals else 0)
            stds.append(np.std(vals) if len(vals) > 1 else 0)
        offset = (ci - (len(conds) - 1) / 2) * w_c
        ax.bar(x_c + offset, means, w_c * 0.92, yerr=stds,
               color=COND_COLORS[cond], alpha=0.92,
               label=COND_LABEL[cond], edgecolor="black", linewidth=0.4)
        for i, m in enumerate(means):
            ax.text(x_c[i] + offset, m + 0.02, f"{m:.2f}",
                    ha="center", fontsize=8.5, fontweight="bold")
    ax.set_xticks(x_c)
    ax.set_xticklabels([CTX_LABEL[c] for c in contexts], fontsize=10)
    ax.set_ylabel("Medicine consume accuracy", fontsize=11)
    ax.set_ylim(0, 1.1)
    ax.axhline(0.5, color="gray", linewidth=0.4, linestyle=":")
    ax.legend(loc="upper left", fontsize=9)
    ax.set_title(
        "Medicine handling under weight shifts: vector head adapts (0.46→0.82→0.73); "
        "scalar head INVERTS (0.54→0.27→0.72).",
        fontsize=11,
    )
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig3_medicine_handling.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # Figure 4: RSA correlation per condition
    fig, ax = plt.subplots(figsize=(9, 5))
    means = []; stds = []
    for cond in conds:
        cells = by_cond[cond]
        rsa_vals = [r["rsa_correlation"] for r in cells
                    if r["rsa_correlation"] is not None and not math.isnan(r["rsa_correlation"])]
        means.append(np.mean(rsa_vals) if rsa_vals else 0)
        stds.append(np.std(rsa_vals) if len(rsa_vals) > 1 else 0)
    x_r = np.arange(len(conds))
    ax.bar(x_r, means, 0.65, yerr=stds,
           color=[COND_COLORS[c] for c in conds], alpha=0.92,
           edgecolor="black", linewidth=0.4)
    for i, m in enumerate(means):
        ax.text(x_r[i], m + 0.015, f"{m:+.2f}",
                ha="center", fontsize=10, fontweight="bold")
    ax.set_xticks(x_r)
    ax.set_xticklabels([COND_LABEL[c] for c in conds], fontsize=8)
    ax.set_ylabel("Effect-vector RSA correlation\n(latent dist vs effect-vec dist)",
                  fontsize=10)
    ax.set_ylim(-0.1, 0.6)
    ax.axhline(0.5, color="black", linewidth=0.4, linestyle=":")
    ax.axhline(0, color="black", linewidth=0.4)
    ax.set_title("Tapestry geometry (RSA): no condition cleanly hits the 0.5 gate. "
                 "Latent geometry is more diffuse than effect-vector structure.",
                 fontsize=11)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig4_rsa_correlation.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # Summary
    summary = {}
    for cond in conds:
        cells = by_cond[cond]
        per_ctx = {}
        for ctx in contexts:
            per_ctx[ctx] = dict(
                mean_return=float(np.mean([r[f"{ctx}_return"] for r in cells])),
                action_accuracy=float(np.mean([r[f"{ctx}_accuracy"] for r in cells])),
                per_role_acc={
                    role: float(np.mean([r[f"{ctx}_role_{role}_acc"] for r in cells
                                          if r[f"{ctx}_role_{role}_acc"] is not None]))
                    for role in ["food", "poison", "medicine", "neutral"]
                },
            )
        rsa_vals = [r["rsa_correlation"] for r in cells
                    if r["rsa_correlation"] is not None and not math.isnan(r["rsa_correlation"])]
        summary[cond] = dict(
            contexts=per_ctx,
            rsa_correlation=float(np.mean(rsa_vals)) if rsa_vals else None,
        )
    out_path = ROOT / "artifacts" / "valence_tapestry" / "summary_v1.json"
    out_path.write_text(json.dumps(summary, indent=2))
    print(f"\nsummary:")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
