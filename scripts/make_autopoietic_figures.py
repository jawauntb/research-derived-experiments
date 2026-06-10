#!/usr/bin/env python3
"""Figures for Paper 5b — Autopoietic Control.

Six figures:

  fig1_trajectory.png            : cluster gap + paraphrase-specific drop +
                                   buffer accuracy vs fine-tuning epoch,
                                   for the full_ft variant. Answers: does
                                   geometry lead causal dependence?
  fig2_los_trajectories.png      : same axes but overlaying full_ft /
                                   frozen_early / frozen_encoder. Shows
                                   that lower-layer slack caps the
                                   transition speed and ceiling.
  fig3_buffer_vs_specific.png    : per-cell (buffer accuracy,
                                   paraphrase-specific drop), passive vs
                                   active. Shows the buffer-causal
                                   coupling Bennett's formalism predicts.
  fig4_repair_curves.png         : recovery accuracy vs K test-time
                                   updates, faceted by sigma; full_ft
                                   (autopoietic) vs frozen_encoder
                                   (no-encoder-slack). Direct
                                   homeostatic→homeodynamic test.
  fig5_los_repair_bars.png       : recovery rate after K=10 across LoS
                                   variants. Single-glance Law-of-the-
                                   Stack bar chart.
  fig6_two_signature_summary.png : single side-by-side summary: passive
                                   vs active buffer, passive vs active
                                   specific. The headline.
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

FIG_DIR = ROOT / "papers" / "autopoietic_control" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

LOS_COLORS = {
    "full_ft": "#2ca02c",
    "frozen_early": "#ff7f0e",
    "frozen_encoder": "#d62728",
}
LOS_LABEL = {
    "full_ft": "full fine-tune (high slack)",
    "frozen_early": "frozen early half (med slack)",
    "frozen_encoder": "frozen encoder (no encoder slack)",
}


def model_short(m):
    return "Pythia-70M" if "pythia" in m else "GPT-2"


def main() -> int:
    data = json.loads(
        (ROOT / "artifacts" / "autopoietic_control" / "sweep_v1.json").read_text()
    )
    results = data["results"]
    snapshot_epochs = data["manifest"]["snapshot_epochs"]
    repair_sigmas = data["manifest"]["repair_sigmas"]
    repair_K = data["manifest"]["repair_K_steps"]

    # Group cells by (model, los_variant)
    by_group = defaultdict(list)
    for r in results:
        if "error" in r or not r.get("trajectory"):
            continue
        key = (r["model_id"], r["los_variant"])
        by_group[key].append(r)

    # ============ Figure 1: trajectory (full_ft only) ============
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    metrics = [
        ("cluster_gap", "Cluster gap (same − diff cosine)", axes[0]),
        ("specific_at_max", "Paraphrase-specific drop", axes[1]),
        ("heldout_buffer_acc", "Held-out buffer accuracy", axes[2]),
    ]
    MODEL_LINES = [
        ("EleutherAI/pythia-70m-deduped", "-"),
        ("openai-community/gpt2", "--"),
    ]
    for model_id, sim in MODEL_LINES:
        cells = by_group.get((model_id, "full_ft"), [])
        for metric_key, _, ax in metrics:
            # Mean over seeds at each snapshot epoch
            all_curves = []
            for r in cells:
                # epoch 0 = passive
                vals = [r["passive"][metric_key]]
                for snap in r["trajectory"]:
                    vals.append(snap[metric_key])
                all_curves.append(vals)
            if not all_curves:
                continue
            arr = np.array(all_curves)
            mean_curve = arr.mean(axis=0)
            std_curve = arr.std(axis=0)
            xs = [0] + snapshot_epochs
            color = "#1f77b4" if "pythia" in model_id else "#9467bd"
            ax.plot(xs, mean_curve, sim, color=color, linewidth=2.2,
                    marker="o", markersize=6, label=model_short(model_id))
            ax.fill_between(
                xs, mean_curve - std_curve, mean_curve + std_curve,
                alpha=0.18, color=color,
            )
    for metric_key, ylabel, ax in metrics:
        ax.set_xscale("symlog", linthresh=1)
        ax.set_xlabel("Fine-tuning epoch (log scale)", fontsize=10)
        ax.set_ylabel(ylabel, fontsize=10)
        ax.grid(linestyle=":", alpha=0.4)
        ax.legend(loc="best", fontsize=9)
        ax.axvline(0, color="gray", linewidth=0.5, alpha=0.5)
    axes[0].set_title("Cluster geometry tightens", fontsize=11)
    axes[1].set_title("Causal dependence emerges", fontsize=11)
    axes[2].set_title("Viability buffer grows", fontsize=11)
    fig.suptitle(
        "Trajectory of the passive→active transition under full fine-tune "
        "(mean ± std across 3 seeds)",
        fontsize=12, y=1.02,
    )
    fig.tight_layout()
    out = FIG_DIR / "fig1_trajectory.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ============ Figure 2: LoS trajectories overlay ============
    MODEL_LINES_OVERLAY = [
        ("EleutherAI/pythia-70m-deduped", "-"),
        ("openai-community/gpt2", "--"),
    ]
    fig, axes = plt.subplots(2, 3, figsize=(15, 9))
    for row, (model_id, _) in enumerate(MODEL_LINES_OVERLAY):
        for col, (metric_key, ylabel, _) in enumerate(metrics):
            ax = axes[row, col]
            for los, color in LOS_COLORS.items():
                cells = by_group.get((model_id, los), [])
                if not cells:
                    continue
                all_curves = []
                for r in cells:
                    vals = [r["passive"][metric_key]]
                    for snap in r["trajectory"]:
                        vals.append(snap[metric_key])
                    all_curves.append(vals)
                if not all_curves:
                    continue
                arr = np.array(all_curves)
                mean_curve = arr.mean(axis=0)
                std_curve = arr.std(axis=0)
                xs = [0] + snapshot_epochs
                ax.plot(xs, mean_curve, color=color, linewidth=2.0,
                        marker="o", markersize=5,
                        label=LOS_LABEL[los] if row == 0 and col == 0 else None)
                ax.fill_between(
                    xs, mean_curve - std_curve, mean_curve + std_curve,
                    alpha=0.15, color=color,
                )
            ax.set_xscale("symlog", linthresh=1)
            ax.grid(linestyle=":", alpha=0.4)
            if row == 1:
                ax.set_xlabel("Epoch (log)", fontsize=10)
            if col == 0:
                ax.set_ylabel(f"{model_short(model_id)}\n\n{ylabel}", fontsize=10)
            else:
                ax.set_ylabel(ylabel, fontsize=10)
    fig.legend(loc="upper center", bbox_to_anchor=(0.5, 1.02), ncol=3, fontsize=10)
    fig.suptitle(
        "Law of the Stack: lower-layer slack caps the passive→active transition",
        fontsize=12, y=1.04,
    )
    fig.tight_layout()
    out = FIG_DIR / "fig2_los_trajectories.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ============ Figure 3: buffer vs specific scatter ============
    fig, ax = plt.subplots(figsize=(9, 6))
    for r in results:
        if "error" in r or not r.get("trajectory"):
            continue
        is_pythia = "pythia" in r["model_id"]
        is_full = r["los_variant"] == "full_ft"
        if not is_full:
            continue
        color = "#1f77b4" if is_pythia else "#d62728"
        passive_b = r["passive"]["heldout_buffer_acc"]
        passive_s = r["passive"]["specific_at_max"]
        active_b = r["trajectory"][-1]["heldout_buffer_acc"]
        active_s = r["trajectory"][-1]["specific_at_max"]
        ax.annotate(
            "", xy=(active_b, active_s), xytext=(passive_b, passive_s),
            arrowprops=dict(arrowstyle="->", color=color, lw=1.6, alpha=0.85),
        )
        ax.scatter([passive_b], [passive_s], s=70, color=color, alpha=0.45,
                   edgecolor=color, linewidth=1.0, marker="o", zorder=3)
        ax.scatter([active_b], [active_s], s=150, color=color, alpha=0.95,
                   edgecolor="black", linewidth=0.8, marker="*", zorder=4)
    ax.axhline(0, color="black", linewidth=0.5)
    ax.axvline(1.0 / 24, color="gray", linewidth=0.5, linestyle=":",
               alpha=0.7)
    ax.text(1.0 / 24, ax.get_ylim()[0] * 0.95, "chance",
            ha="left", va="bottom", fontsize=8, color="gray")
    from matplotlib.lines import Line2D
    ax.legend(handles=[
        Line2D([], [], marker="o", color="w", markerfacecolor="#1f77b4",
               markersize=8, alpha=0.7, label="Pythia-70M passive"),
        Line2D([], [], marker="*", color="w", markerfacecolor="#1f77b4",
               markersize=14, markeredgecolor="black", label="Pythia-70M active"),
        Line2D([], [], marker="o", color="w", markerfacecolor="#d62728",
               markersize=8, alpha=0.7, label="GPT-2 passive"),
        Line2D([], [], marker="*", color="w", markerfacecolor="#d62728",
               markersize=14, markeredgecolor="black", label="GPT-2 active"),
    ], loc="best", fontsize=9)
    ax.set_xlabel("Viability buffer (held-out paraphrase accuracy)", fontsize=11)
    ax.set_ylabel("Paraphrase-specific causal drop", fontsize=11)
    ax.set_title(
        "Action coupling grows the buffer AND the causal axis simultaneously\n"
        "(every full_ft cell moves up and right)",
        fontsize=12,
    )
    ax.grid(linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig3_buffer_vs_specific.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ============ Figure 4: repair curves ============
    fig, axes = plt.subplots(1, len(repair_sigmas), figsize=(4 * len(repair_sigmas), 4.5),
                             sharey=True)
    for s_idx, sigma in enumerate(repair_sigmas):
        ax = axes[s_idx] if len(repair_sigmas) > 1 else axes
        for los, color in LOS_COLORS.items():
            cells_full = [r for r in results
                          if "error" not in r and r.get("trajectory")
                          and r["los_variant"] == los]
            if not cells_full:
                continue
            curves = []
            for r in cells_full:
                rep = {(rec["sigma"], rec["K"]): rec for rec in r["repair"]}
                ys = []
                for k in repair_K:
                    rec = rep.get((sigma, k))
                    if rec is None:
                        ys.append(np.nan)
                    else:
                        ys.append(rec["acc_after"])
                curves.append(ys)
            arr = np.array(curves)
            mean = np.nanmean(arr, axis=0)
            std = np.nanstd(arr, axis=0)
            ax.plot(repair_K, mean, "o-", color=color,
                    linewidth=2.0, markersize=6,
                    label=LOS_LABEL[los] if s_idx == 0 else None)
            ax.fill_between(repair_K, mean - std, mean + std,
                            alpha=0.15, color=color)
        ax.set_title(f"σ = {sigma}", fontsize=11)
        ax.set_xlabel("Test-time update steps K", fontsize=10)
        if s_idx == 0:
            ax.set_ylabel("Held-out accuracy after repair", fontsize=10)
        ax.set_ylim(-0.02, 1.05)
        ax.grid(linestyle=":", alpha=0.4)
        ax.axhline(1.0 / 24, color="gray", linewidth=0.5, linestyle=":")
    handles, labels = axes[0].get_legend_handles_labels() if len(repair_sigmas) > 1 else axes.get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center",
               bbox_to_anchor=(0.5, 1.04), ncol=3, fontsize=10)
    fig.suptitle(
        "Repair under viability breach: noise classifier head with σ, "
        "then K test-time updates on held-out paraphrases",
        fontsize=12, y=1.10,
    )
    fig.tight_layout()
    out = FIG_DIR / "fig4_repair_curves.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ============ Figure 5: LoS repair bars at K=10, sigma=0.2 ============
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    target_sigma = 0.2
    target_K = 10
    for ax_idx, (model_id, _) in enumerate(MODEL_LINES_OVERLAY):
        ax = axes[ax_idx]
        per_los_recovery = {}
        per_los_immediate = {}
        for los in LOS_COLORS:
            cells = by_group.get((model_id, los), [])
            recov = []
            imm = []
            for r in cells:
                rec = next((x for x in r["repair"]
                            if x["sigma"] == target_sigma and x["K"] == target_K),
                           None)
                rec0 = next((x for x in r["repair"]
                             if x["sigma"] == target_sigma and x["K"] == 0),
                            None)
                if rec and rec0:
                    recov.append(rec["acc_after"])
                    imm.append(rec0["acc_immediate"])
            per_los_recovery[los] = recov
            per_los_immediate[los] = imm

        x = np.arange(len(LOS_COLORS))
        w = 0.36
        means_imm = [np.mean(per_los_immediate[los]) if per_los_immediate[los] else 0
                     for los in LOS_COLORS]
        means_rec = [np.mean(per_los_recovery[los]) if per_los_recovery[los] else 0
                     for los in LOS_COLORS]
        stds_imm = [np.std(per_los_immediate[los]) if len(per_los_immediate[los]) > 1 else 0
                    for los in LOS_COLORS]
        stds_rec = [np.std(per_los_recovery[los]) if len(per_los_recovery[los]) > 1 else 0
                    for los in LOS_COLORS]
        ax.bar(x - w / 2, means_imm, w, yerr=stds_imm,
               color=[LOS_COLORS[k] for k in LOS_COLORS], alpha=0.4,
               edgecolor="black", linewidth=0.5,
               label="immediate post-noise" if ax_idx == 0 else None)
        ax.bar(x + w / 2, means_rec, w, yerr=stds_rec,
               color=[LOS_COLORS[k] for k in LOS_COLORS],
               edgecolor="black", linewidth=0.5,
               label=f"after K={target_K} updates" if ax_idx == 0 else None)
        for i, (im, re) in enumerate(zip(means_imm, means_rec)):
            ax.text(x[i] - w / 2, im + 0.02, f"{im:.2f}", ha="center", fontsize=9)
            ax.text(x[i] + w / 2, re + 0.02, f"{re:.2f}", ha="center",
                    fontsize=9, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels([LOS_LABEL[k].replace(" (", "\n(") for k in LOS_COLORS],
                           fontsize=9)
        ax.set_title(f"{model_short(model_id)}", fontsize=11)
        if ax_idx == 0:
            ax.set_ylabel(f"Held-out accuracy (σ={target_sigma}, K=0 vs K={target_K})",
                          fontsize=10)
        ax.set_ylim(0, 1.05)
        ax.axhline(1.0 / 24, color="gray", linewidth=0.5, linestyle=":")
        ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.legend(loc="upper center", bbox_to_anchor=(0.5, 1.02), ncol=2, fontsize=10)
    fig.suptitle(
        f"Repair after viability breach (σ={target_sigma}): "
        "high lower-layer slack repairs further with same K updates",
        fontsize=12, y=1.06,
    )
    fig.tight_layout()
    out = FIG_DIR / "fig5_los_repair_bars.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ============ Figure 6: two-signature summary ============
    full_cells = [r for r in results
                  if "error" not in r and r.get("trajectory")
                  and r["los_variant"] == "full_ft"]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    metrics_pair = [
        ("specific_at_max", "Paraphrase-specific causal drop",
         "passive_specific", "active_specific"),
        ("heldout_buffer_acc", "Viability buffer (held-out accuracy)",
         "passive_buffer", "active_buffer"),
    ]
    for ax_idx, (mkey, label, _, _) in enumerate(metrics_pair):
        ax = axes[ax_idx]
        cell_labels = []
        passive_vals = []
        active_vals = []
        for r in full_cells:
            cell_labels.append(
                f"{model_short(r['model_id'])}\ns={r['seed']}"
            )
            passive_vals.append(r["passive"][mkey])
            active_vals.append(r["trajectory"][-1][mkey])
        x = np.arange(len(cell_labels))
        w = 0.36
        ax.bar(x - w / 2, passive_vals, w, color="#1f77b4",
               alpha=0.85, label="passive")
        ax.bar(x + w / 2, active_vals, w, color="#2ca02c",
               alpha=0.85, label="active (full_ft)")
        for i, (pv, av) in enumerate(zip(passive_vals, active_vals)):
            ax.text(i - w / 2, pv + 0.012 if pv >= 0 else pv - 0.04,
                    f"{pv:+.3f}" if ax_idx == 0 else f"{pv:.2f}",
                    ha="center", fontsize=8)
            ax.text(i + w / 2, av + 0.012,
                    f"{av:+.3f}" if ax_idx == 0 else f"{av:.2f}",
                    ha="center", fontsize=8, fontweight="bold")
        ax.axhline(0, color="black", linewidth=0.5)
        ax.set_xticks(x)
        ax.set_xticklabels(cell_labels, fontsize=9)
        ax.set_ylabel(label, fontsize=10)
        ax.legend(loc="upper left", fontsize=9)
        ax.grid(axis="y", linestyle=":", alpha=0.4)
        if ax_idx == 1:
            ax.axhline(1.0 / 24, color="gray", linewidth=0.5, linestyle=":")
            ax.text(0, 1.0 / 24, " chance", fontsize=8, color="gray", va="bottom")
    fig.suptitle(
        "Headline: action coupling grows BOTH causal load-bearing AND viability buffer",
        fontsize=12, y=1.01,
    )
    fig.tight_layout()
    out = FIG_DIR / "fig6_two_signature_summary.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ============ Emit summary stats for paper ============
    summary = {}
    for los in LOS_COLORS:
        all_cells = [r for r in results
                     if "error" not in r and r.get("trajectory")
                     and r["los_variant"] == los]
        passive_spec = [r["passive"]["specific_at_max"] for r in all_cells]
        active_spec = [r["trajectory"][-1]["specific_at_max"] for r in all_cells]
        passive_buf = [r["passive"]["heldout_buffer_acc"] for r in all_cells]
        active_buf = [r["trajectory"][-1]["heldout_buffer_acc"] for r in all_cells]
        # K=10 sigma=0.2 repair averages
        recovery_at_10 = []
        for r in all_cells:
            rec = next((x for x in r["repair"]
                       if x["sigma"] == 0.2 and x["K"] == 10), None)
            if rec:
                recovery_at_10.append(rec["acc_after"])
        summary[los] = dict(
            n_cells=len(all_cells),
            passive_specific_mean=float(np.mean(passive_spec)) if passive_spec else None,
            active_specific_mean=float(np.mean(active_spec)) if active_spec else None,
            passive_buffer_mean=float(np.mean(passive_buf)) if passive_buf else None,
            active_buffer_mean=float(np.mean(active_buf)) if active_buf else None,
            recovery_at_K10_sigma02_mean=(
                float(np.mean(recovery_at_10)) if recovery_at_10 else None
            ),
        )
    out_path = ROOT / "artifacts" / "autopoietic_control" / "summary_v1.json"
    out_path.write_text(json.dumps(summary, indent=2))
    print(f"\nsummary by LoS variant:")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
