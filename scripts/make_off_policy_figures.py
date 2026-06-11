#!/usr/bin/env python3
"""Figures for Paper 13a — Off-Policy State Coverage."""

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

FIG_DIR = ROOT / "papers" / "off_policy_state_coverage" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

COND_LABEL = {
    "off_policy_state_aware": "off-policy\nstate-aware (HEADLINE)",
    "off_policy_state_blind": "off-policy\nstate-blind (control)",
    "online_state_aware": "online state-aware\n(Paper 12 baseline)",
    "online_random_E_start": "online random-E start\n(Paper 12 attempted fix)",
}
ENV_LABEL = {"static_xor": "static XOR", "state_dep_inv_xor": "state-dep inverted XOR"}


def main() -> int:
    data = json.loads(
        (ROOT / "artifacts" / "off_policy_state_coverage" / "sweep_v1.json").read_text()
    )
    rows = data["summary"]
    conds = data["manifest"]["conditions"]
    envs = data["manifest"]["envs"]

    by_key = defaultdict(list)
    for r in rows:
        by_key[(r["condition"], r["env"])].append(r)

    # Figure 1: per-E accuracy bar chart
    fig, ax = plt.subplots(figsize=(13, 5.5))
    x_e = np.arange(3)
    w_e = 0.18
    E_keys = ["acc@E=0.2", "acc@E=0.5", "acc@E=0.8"]
    colors = {"off_policy_state_aware": "#2ca02c",
              "off_policy_state_blind": "#7f7f7f",
              "online_state_aware": "#d62728",
              "online_random_E_start": "#ff7f0e"}
    for ci, cond in enumerate(conds):
        cells = by_key.get((cond, "state_dep_inv_xor"), [])
        means = [np.mean([r[k] for r in cells]) if cells else 0 for k in E_keys]
        offset = (ci - (len(conds) - 1) / 2) * w_e
        ax.bar(x_e + offset, means, w_e * 0.9, color=colors[cond],
               alpha=0.92, label=COND_LABEL[cond],
               edgecolor="black", linewidth=0.4)
        for i, m in enumerate(means):
            ax.text(x_e[i] + offset, m + 0.015, f"{m:.2f}",
                    ha="center", fontsize=8)
    ax.set_xticks(x_e)
    ax.set_xticklabels(["E = 0.2 (hungry)", "E = 0.5 (boundary)", "E = 0.8 (sated)"],
                       fontsize=10)
    ax.set_ylabel("Margin sign accuracy", fontsize=11)
    ax.set_ylim(0, 1.08)
    ax.axhline(0.5, color="gray", linewidth=0.4, linestyle=":")
    ax.axhline(0.9, color="black", linewidth=0.4, linestyle=":")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=2, fontsize=9)
    ax.set_title(
        "Off-policy state-aware (green) succeeds at E=0.2 and E=0.8 but fails at the E=0.5 boundary\n"
        "Online conditions (red/orange) fail everywhere",
        fontsize=12, y=1.15,
    )
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig1_per_E_accuracy.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # Figure 2: hungry vs sated bars for state-dep
    fig, ax = plt.subplots(figsize=(12, 5.5))
    x_c = np.arange(len(conds))
    w_c = 0.4
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
    ax.axhline(0.9, color="black", linewidth=0.4, linestyle=":")
    ax.legend(loc="upper right", fontsize=10)
    ax.set_title(
        "On state-dep inverted XOR: off-policy succeeds in sated regime (E≥0.5);\n"
        "hungry regime accuracy is lower because boundary is hard to learn",
        fontsize=12,
    )
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig2_hungry_vs_sated.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # Figure 3: coverage diagnostic — high-E consume fraction
    fig, ax = plt.subplots(figsize=(11, 5.5))
    for env_idx, env in enumerate(envs):
        x_c = np.arange(len(conds))
        means = []
        for cond in conds:
            cells = by_key.get((cond, env), [])
            vals = [r["consume_high_E_frac"] for r in cells]
            means.append(np.mean(vals) if vals else 0)
        offset = (env_idx - 0.5) * 0.4
        c = "#2ca02c" if env == "static_xor" else "#d62728"
        ax.bar(x_c + offset, means, 0.4, color=c, alpha=0.85,
               label=ENV_LABEL[env], edgecolor="black", linewidth=0.4)
        for i, m in enumerate(means):
            ax.text(x_c[i] + offset, m + 0.015, f"{m:.3f}",
                    ha="center", fontsize=9)
    ax.set_xticks(x_c)
    ax.set_xticklabels([COND_LABEL[c] for c in conds], fontsize=8)
    ax.set_ylabel("Fraction of consume training data at E ≥ 0.5", fontsize=11)
    ax.set_ylim(0, 1.0)
    ax.axhline(0.5, color="black", linewidth=0.4, linestyle=":")
    ax.text(0, 0.51, "uniform = 0.5", fontsize=9, color="black")
    ax.legend(loc="upper right", fontsize=10)
    ax.set_title(
        "Coverage diagnostic: online conditions OVER-sample high-E consume (~0.75),\n"
        "not under-sample. Coverage was not the bottleneck.",
        fontsize=12,
    )
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig3_coverage_diagnostic.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # Figure 4: return + accuracy summary
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.5))
    x_c = np.arange(len(conds))
    w_c = 0.4
    for ax_idx, (key, ylabel, ylim) in enumerate([
        ("mean_return", "Mean return", (0, 55)),
        ("action_accuracy", "Action accuracy", (0, 1.08)),
    ]):
        ax = axes[ax_idx]
        for env_idx, env in enumerate(envs):
            means = []
            for cond in conds:
                cells = by_key.get((cond, env), [])
                vals = [r[key] for r in cells]
                means.append(np.mean(vals) if vals else 0)
            offset = (env_idx - 0.5) * w_c
            c = "#2ca02c" if env == "static_xor" else "#d62728"
            ax.bar(x_c + offset, means, w_c, color=c, alpha=0.85,
                   label=ENV_LABEL[env] if ax_idx == 0 else None,
                   edgecolor="black", linewidth=0.4)
            for i, m in enumerate(means):
                fmt = f"{m:.1f}" if key == "mean_return" else f"{m:.2f}"
                offset_y = 1.0 if key == "mean_return" else 0.015
                ax.text(x_c[i] + offset, m + offset_y, fmt,
                        ha="center", fontsize=8, fontweight="bold")
        ax.set_xticks(x_c)
        ax.set_xticklabels([COND_LABEL[c] for c in conds], fontsize=8)
        ax.set_ylabel(ylabel, fontsize=11)
        ax.set_ylim(ylim)
        if key == "mean_return":
            ax.axhline(50, color="gray", linewidth=0.4, linestyle=":")
        else:
            ax.axhline(0.5, color="gray", linewidth=0.4, linestyle=":")
            ax.axhline(0.9, color="black", linewidth=0.4, linestyle=":")
        if ax_idx == 0:
            ax.legend(loc="upper right", fontsize=10)
        ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.suptitle(
        "Headline: off-policy state-aware lifts state-dep accuracy from 0.47 to 0.96",
        fontsize=12, y=1.02,
    )
    fig.tight_layout()
    out = FIG_DIR / "fig4_headline.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # Summary
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
                state_conditional_competence=float(np.mean(
                    [r["state_conditional_competence"] for r in cells
                     if r["state_conditional_competence"] is not None]
                )) if any(r["state_conditional_competence"] is not None for r in cells) else None,
                acc_at_E02=float(np.mean([r["acc@E=0.2"] for r in cells])),
                acc_at_E05=float(np.mean([r["acc@E=0.5"] for r in cells])),
                acc_at_E08=float(np.mean([r["acc@E=0.8"] for r in cells])),
                consume_high_E_frac=float(np.mean([r["consume_high_E_frac"] for r in cells])),
            )
        summary[cond] = per_env
    out_path = ROOT / "artifacts" / "off_policy_state_coverage" / "summary_v1.json"
    out_path.write_text(json.dumps(summary, indent=2))
    print(f"\nsummary:")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
