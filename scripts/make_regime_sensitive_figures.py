#!/usr/bin/env python3
"""Figures for Paper 13b — Regime-Sensitive ΔE Models."""

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

FIG_DIR = ROOT / "papers" / "regime_sensitive_de" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

COND_COLORS = {
    "monolithic_head": "#7f7f7f",
    "oracle_boundary_feature": "#2ca02c",
    "learned_boundary_gate": "#1f77b4",
    "fourier_E_features": "#9467bd",
    "sign_loss": "#ff7f0e",
}
COND_LABEL = {
    "monolithic_head": "monolithic\n(13a baseline)",
    "oracle_boundary_feature": "oracle 1[E<0.5]\n(diagnostic)",
    "learned_boundary_gate": "learned MoE gate\n(autonomous)",
    "fourier_E_features": "Fourier E-features",
    "sign_loss": "sign-of-margin loss",
}


def main() -> int:
    data = json.loads(
        (ROOT / "artifacts" / "regime_sensitive_de" / "sweep_v1.json").read_text()
    )
    rows = data["summary"]
    conds = data["manifest"]["conditions"]
    envs = data["manifest"]["envs"]

    by_key = defaultdict(list)
    for r in rows:
        by_key[(r["condition"], r["env"])].append(r)

    # Figure 1: fine-grained per-E accuracy curves
    fig, ax = plt.subplots(figsize=(13, 5.5))
    E_grid = [0.1, 0.2, 0.3, 0.4, 0.45, 0.5, 0.55, 0.6, 0.7, 0.8, 0.9]
    for cond in conds:
        cells = by_key.get((cond, "state_dep_inv_xor"), [])
        means = []
        stds = []
        for E in E_grid:
            vals = [r[f"acc@E={E}"] for r in cells]
            means.append(np.mean(vals) if vals else 0)
            stds.append(np.std(vals) if len(vals) > 1 else 0)
        ax.plot(E_grid, means, "o-", color=COND_COLORS[cond], linewidth=2.2,
                markersize=7, label=COND_LABEL[cond])
        ax.fill_between(E_grid, [m - s for m, s in zip(means, stds)],
                        [m + s for m, s in zip(means, stds)],
                        color=COND_COLORS[cond], alpha=0.15)
    ax.axvline(0.5, color="black", linewidth=0.8, linestyle="--",
               alpha=0.5)
    ax.text(0.51, 0.55, "boundary (E=0.5)", fontsize=9, color="black")
    ax.set_xlabel("Internal state E", fontsize=11)
    ax.set_ylabel("Margin sign accuracy", fontsize=11)
    ax.set_ylim(0.3, 1.05)
    ax.axhline(0.5, color="gray", linewidth=0.4, linestyle=":")
    ax.legend(loc="lower right", fontsize=9)
    ax.set_title(
        "Per-E accuracy across architectures on state_dep_inv_xor.\n"
        "Oracle (green) is perfect everywhere. Fourier/sign_loss are perfect EXCEPT at exactly E=0.5 (measure-zero discontinuity).",
        fontsize=11,
    )
    ax.grid(linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig1_per_E_curves.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # Figure 2: return + sc_competence comparison
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.5))
    x = np.arange(len(conds))
    w = 0.4
    for ax_idx, (key, label, ylim) in enumerate([
        ("mean_return", "Mean return", (0, 55)),
        ("state_conditional_competence", "State-conditional competence", (0, 1.08)),
    ]):
        ax = axes[ax_idx]
        for env_idx, env in enumerate(envs):
            means = []
            stds = []
            for cond in conds:
                cells = by_key.get((cond, env), [])
                vals = [r[key] for r in cells if r[key] is not None]
                means.append(np.mean(vals) if vals else 0)
                stds.append(np.std(vals) if len(vals) > 1 else 0)
            offset = (env_idx - 0.5) * w
            c = "#2ca02c" if env == "static_xor" else "#d62728"
            ax.bar(x + offset, means, w, yerr=stds, color=c, alpha=0.85,
                   label=env if ax_idx == 0 else None,
                   edgecolor="black", linewidth=0.4)
            for i, m in enumerate(means):
                fmt = f"{m:.1f}" if key == "mean_return" else f"{m:.2f}"
                offset_y = 1.0 if key == "mean_return" else 0.015
                ax.text(x[i] + offset, m + offset_y, fmt,
                        ha="center", fontsize=8, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels([COND_LABEL[c] for c in conds], fontsize=8)
        ax.set_ylabel(label, fontsize=11)
        ax.set_ylim(ylim)
        if key == "mean_return":
            ax.axhline(50, color="gray", linewidth=0.4, linestyle=":")
            ax.legend(loc="upper right", fontsize=10)
        else:
            ax.axhline(0.5, color="gray", linewidth=0.4, linestyle=":")
            ax.axhline(0.9, color="black", linewidth=0.4, linestyle=":")
        ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.suptitle(
        "Oracle boundary feature closes the gap completely; learned alternatives "
        "achieve sc_comp 0.99 but trajectory-weighted returns lag",
        fontsize=12, y=1.02,
    )
    fig.tight_layout()
    out = FIG_DIR / "fig2_return_and_competence.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # Figure 3: boundary zoom
    fig, ax = plt.subplots(figsize=(11, 5.5))
    E_zoom = [0.4, 0.45, 0.5, 0.55, 0.6]
    x = np.arange(len(E_zoom))
    w = 0.15
    for ci, cond in enumerate(conds):
        cells = by_key.get((cond, "state_dep_inv_xor"), [])
        means = []
        for E in E_zoom:
            vals = [r[f"acc@E={E}"] for r in cells]
            means.append(np.mean(vals) if vals else 0)
        offset = (ci - (len(conds) - 1) / 2) * w
        ax.bar(x + offset, means, w * 0.9, color=COND_COLORS[cond],
               alpha=0.92, label=COND_LABEL[cond],
               edgecolor="black", linewidth=0.4)
        for i, m in enumerate(means):
            ax.text(x[i] + offset, m + 0.015, f"{m:.2f}",
                    ha="center", fontsize=7.5)
    ax.set_xticks(x)
    ax.set_xticklabels([f"E={E}" for E in E_zoom], fontsize=10)
    ax.set_ylabel("Margin sign accuracy", fontsize=11)
    ax.set_ylim(0, 1.08)
    ax.axhline(0.5, color="gray", linewidth=0.4, linestyle=":")
    ax.axhline(0.9, color="black", linewidth=0.4, linestyle=":")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15),
              ncol=3, fontsize=9)
    ax.set_title(
        "Boundary zoom: only the oracle handles exactly E=0.5; "
        "Fourier/sign_loss are perfect at E=0.45 and 0.55 but fail at the singular point",
        fontsize=12, y=1.15,
    )
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig3_boundary_zoom.png"
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
                acc_at_E_grid={f"E={E}": float(np.mean([r[f"acc@E={E}"] for r in cells]))
                               for E in [0.1, 0.2, 0.3, 0.4, 0.45, 0.5, 0.55, 0.6, 0.7, 0.8, 0.9]},
            )
        summary[cond] = per_env
    out_path = ROOT / "artifacts" / "regime_sensitive_de" / "summary_v1.json"
    out_path.write_text(json.dumps(summary, indent=2))
    print(f"\nsummary:")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
