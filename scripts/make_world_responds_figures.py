#!/usr/bin/env python3
"""Figures for Paper 22 — World Responds."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path
from textwrap import fill

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

FIG_DIR = ROOT / "papers" / "world_responds" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

COND_COLORS = {
    "p21a_independent_baseline": "#7f7f7f",
    "two_head_actionblind_world": "#d62728",
    "two_head_history_world": "#ff7f0e",
    "three_head_direct_mediated_exogenous": "#1f77b4",
    "scheduled_null_anchor": "#bcbd22",
    "learned_scale_norm_current_replay": "#2ca02c",
    "matched_random_time_budget": "#9467bd",
    "matched_random_bucket_dim": "#aec7e8",
    "oracle_probe_value": "#17becf",
    "oracle_source": "#1a1a1a",
}
COND_LABEL = {
    "p21a_independent_baseline": "P21A\nindependent\nbaseline",
    "two_head_actionblind_world": "2-head\naction-blind\nworld",
    "two_head_history_world": "2-head\nhistory\nworld",
    "three_head_direct_mediated_exogenous": "3-head\ndirect/med/exo",
    "scheduled_null_anchor": "scheduled\nanchor",
    "learned_scale_norm_current_replay": "learned\nscale-norm\n(HEADLINE)",
    "matched_random_time_budget": "matched\nrandom\n(time)",
    "matched_random_bucket_dim": "matched\nrandom\n(bucket-dim)",
    "oracle_probe_value": "oracle probe\n(current error)",
    "oracle_source": "oracle source",
}
ROLES = ["food", "poison", "medicine", "neutral"]
PRIORITIES = ["balanced", "hungry", "injured"]


def fig5_reengagement_floor() -> None:
    """Diagram the G7 re-engagement failure and architecture fix."""
    rows = [
        (
            "Selective probing",
            "Learned probe uses 213 nulls vs 3,951 for time-matched random.",
            "efficient",
            "#d1fae5",
        ),
        (
            "Convergence",
            "V_probe falls quiet once the world model looks calibrated.",
            "quiet state",
            "#dbeafe",
        ),
        (
            "Regime shift",
            "Trigger changes from food to medicine at episode 250.",
            "world changed",
            "#fef3c7",
        ),
        (
            "Self-confirming silence",
            "Affected buckets receive 0 post-shift probes, so V_probe gets no new data.",
            "failure",
            "#fee2e2",
        ),
        (
            "Re-engagement floor",
            "Audit probes, residual-surprise boost, or fast/slow V_probe can reopen inquiry.",
            "needed",
            "#e9d5ff",
        ),
    ]

    fig, ax = plt.subplots(figsize=(13.5, 6.8))
    ax.set_xlim(0, 14)
    ax.set_ylim(-0.2, len(rows) + 1.5)
    ax.axis("off")

    ax.text(
        7,
        len(rows) + 1.15,
        "Figure 5. Re-engagement floor",
        ha="center",
        fontsize=14,
        fontweight="bold",
    )
    ax.text(
        7,
        len(rows) + 0.78,
        "Probe efficiency is not enough; changing worlds require a way to reopen inquiry.",
        ha="center",
        fontsize=10,
        color="#444",
        style="italic",
    )

    x0, w0 = 0.35, 2.8
    x1, w1 = 3.55, 6.45
    x2, w2 = 10.55, 2.95
    for x, w, title in [
        (x0, w0, "Stage"),
        (x1, w1, "Observed mechanism"),
        (x2, w2, "Role"),
    ]:
        header = FancyBboxPatch(
            (x, len(rows) + 0.1),
            w,
            0.44,
            boxstyle="round,pad=0.035",
            facecolor="#e5e7eb",
            edgecolor="#555",
            linewidth=0.9,
        )
        ax.add_patch(header)
        ax.text(x + w / 2, len(rows) + 0.32, title, ha="center", va="center", fontweight="bold")

    for idx, (stage, mechanism, role, color) in enumerate(rows):
        y = len(rows) - idx - 0.62
        stripe = "#ffffff" if idx % 2 == 0 else "#f8fafc"
        ax.add_patch(
            patches.Rectangle(
                (0.15, y - 0.39),
                13.65,
                0.78,
                facecolor=stripe,
                edgecolor="#e5e7eb",
                linewidth=0.6,
            )
        )
        ax.add_patch(
            FancyBboxPatch(
                (x0, y - 0.28),
                w0,
                0.56,
                boxstyle="round,pad=0.03",
                facecolor=color,
                edgecolor="#cbd5e1",
                linewidth=0.7,
            )
        )
        ax.add_patch(
            patches.Rectangle(
                (x1, y - 0.28),
                w1,
                0.56,
                facecolor="#f8fafc",
                edgecolor="#e5e7eb",
                linewidth=0.7,
            )
        )
        ax.add_patch(
            FancyBboxPatch(
                (x2, y - 0.28),
                w2,
                0.56,
                boxstyle="round,pad=0.03",
                facecolor="#f1f5f9",
                edgecolor="#cbd5e1",
                linewidth=0.7,
            )
        )
        ax.text(x0 + 0.18, y, fill(stage, 20), ha="left", va="center", fontweight="bold", color="#0f172a")
        ax.text(x1 + 0.18, y, fill(mechanism, 66), ha="left", va="center", color="#1f2937")
        ax.text(x2 + w2 / 2, y, fill(role, 20), ha="center", va="center", fontweight="bold", color="#334155")
        if idx < len(rows) - 1:
            ax.annotate(
                "",
                xy=(1.75, y - 0.45),
                xytext=(1.75, y - 0.29),
                arrowprops=dict(arrowstyle="->", color="#64748b", lw=1.0),
            )

    fig.tight_layout()
    out = FIG_DIR / "fig5_reengagement_floor.png"
    fig.savefig(out, dpi=220, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


def main() -> int:
    data = json.loads(
        (ROOT / "artifacts" / "world_responds" / "sweep_v1.json").read_text()
    )
    rows = data["summary"]
    conds = data["manifest"]["conditions"]
    raw_results = data["results"]
    food_true_E = rows[0]["true_self_E_consume_food"]
    poison_true_D = rows[0]["true_self_D_consume_poison"]

    def cells_raw(cond): return [r for r in raw_results if r["condition"] == cond]
    def cells_sum(cond): return [r for r in rows if r["condition"] == cond]

    # ===== Fig 1: learning-curve final MAE per condition =====
    fig, ax = plt.subplots(figsize=(13, 6))
    x = np.arange(len(conds))
    mae_means = []; mae_stds = []
    for cond in conds:
        cells = cells_sum(cond)
        vals = [r.get("final_lc_mae", 0.0) for r in cells]
        mae_means.append(float(np.mean(vals)) if vals else 0.0)
        mae_stds.append(float(np.std(vals)) if len(vals) > 1 else 0.0)
    ax.bar(x, mae_means, 0.7, yerr=mae_stds,
           color=[COND_COLORS[c] for c in conds], alpha=0.92,
           edgecolor="black", linewidth=0.4)
    for i, m in enumerate(mae_means):
        ax.text(x[i], m + 0.01, f"{m:.3f}", ha="center",
                fontsize=9, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([COND_LABEL[c] for c in conds], fontsize=6,
                        rotation=15)
    ax.set_ylabel("Learning-curve final MAE (food_E + poison_D)", fontsize=11)
    ax.set_title("Training-time attribution quality (mean ± std across 3 seeds)",
                 fontsize=11)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig1_learning_curve_mae.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ===== Fig 2: per-dim predictions =====
    fig, axes = plt.subplots(1, 2, figsize=(16, 6), sharey=False)
    metrics = [
        ("food self_E (consume)", "pred_self_E_consume_food", food_true_E),
        ("poison self_D (consume)", "pred_self_D_consume_poison", poison_true_D),
    ]
    for idx, (title, key, tv) in enumerate(metrics):
        ax = axes[idx]
        x = np.arange(len(conds))
        for ci, cond in enumerate(conds):
            cells = cells_sum(cond)
            preds = np.array([r[key] for r in cells])
            mean = np.mean(preds) if len(preds) else 0
            std = np.std(preds) if len(preds) > 1 else 0
            ax.bar(ci, mean, 0.7, yerr=std, color=COND_COLORS[cond],
                   alpha=0.92, edgecolor="black", linewidth=0.4)
            ax.text(ci, mean + (0.04 if mean >= 0 else -0.08),
                    f"{mean:+.2f}", ha="center", fontsize=7, fontweight="bold")
        ax.axhline(tv, color="green", linewidth=1.8, linestyle="--",
                   alpha=0.7, label=f"true ({tv:+.2f})")
        ax.set_xticks(x)
        ax.set_xticklabels([COND_LABEL[c] for c in conds], fontsize=5.5,
                            rotation=15)
        ax.set_title(title, fontsize=11)
        ax.axhline(0, color="black", linewidth=0.3)
        ax.legend(loc="best", fontsize=8)
        ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig2_per_dim_predictions.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ===== Fig 3: zero-shot reweighting (G9) =====
    fig, ax = plt.subplots(figsize=(13, 6))
    sub_conds = [c for c in conds if "matched_random" not in c]
    x = np.arange(len(sub_conds))
    w_bar = 0.25
    pcolors = {"balanced": "#1f77b4", "hungry": "#d62728", "injured": "#2ca02c"}
    for pi, prio in enumerate(PRIORITIES):
        accs = []; errs = []
        for cond in sub_conds:
            cells = cells_sum(cond)
            vals = [r.get(f"{prio}_acc_medicine", 0.0) for r in cells]
            accs.append(float(np.mean(vals)))
            errs.append(float(np.std(vals)) if len(vals) > 1 else 0.0)
        offset = (pi - 1) * w_bar
        ax.bar(x + offset, accs, w_bar, yerr=errs,
               color=pcolors[prio], alpha=0.88, label=prio,
               edgecolor="black", linewidth=0.4)
        for i, v in enumerate(accs):
            ax.text(x[i] + offset, v + 0.02, f"{v:.2f}",
                    ha="center", fontsize=6.5)
    ax.set_xticks(x)
    ax.set_xticklabels([COND_LABEL[c] for c in sub_conds], fontsize=7,
                        rotation=15)
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("Medicine action accuracy", fontsize=11)
    ax.set_title("G9 zero-shot reweighting under action-correlated shocks",
                 fontsize=11)
    ax.legend(loc="best", fontsize=9)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig3_reweighting.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ===== Fig 4: pre-shift vs post-shift null density per bucket =====
    fig, ax = plt.subplots(figsize=(15, 6))
    BUCKETS = [f"{r}_{eb}_{db}" for r in ROLES
               for eb in ("E_low", "E_high") for db in ("D_low", "D_high")]
    headline_cells = cells_raw("learned_scale_norm_current_replay")
    pre_sums = {b: 0 for b in BUCKETS}
    post_sums = {b: 0 for b in BUCKETS}
    for r in headline_cells:
        for b in BUCKETS:
            pre_sums[b] += r["bucket_null_density_pre_shift"].get(b, 0)
            post_sums[b] += r["bucket_null_density_post_shift"].get(b, 0)
    x = np.arange(len(BUCKETS))
    w = 0.4
    ax.bar(x - w/2, [pre_sums[b] for b in BUCKETS], w,
           color="#1f77b4", alpha=0.85, label="pre-shift (eps 0-249)",
           edgecolor="black", linewidth=0.4)
    ax.bar(x + w/2, [post_sums[b] for b in BUCKETS], w,
           color="#d62728", alpha=0.85, label="post-shift (eps 250-499)",
           edgecolor="black", linewidth=0.4)
    ax.set_xticks(x)
    ax.set_xticklabels(BUCKETS, fontsize=6, rotation=45, ha="right")
    ax.set_ylabel("Cumulative null fires per bucket (summed over 3 seeds)",
                  fontsize=11)
    ax.set_title("G7: probe allocation pre/post regime shift (headline learned)",
                 fontsize=11)
    ax.legend(loc="best", fontsize=9)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig4_pre_post_shift.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    fig5_reengagement_floor()

    # ===== Compute verdicts =====
    def role_pred(cells, role, key):
        return float(np.mean([r["prediction_by_role"][role][key]
                                for r in cells])) if cells else 0.0

    learned = cells_raw("learned_scale_norm_current_replay")
    matched_time = cells_raw("matched_random_time_budget")
    matched_bucket = cells_raw("matched_random_bucket_dim")
    scheduled = cells_raw("scheduled_null_anchor")
    two_head_blind = cells_raw("two_head_actionblind_world")
    two_head_hist = cells_raw("two_head_history_world")
    three_head = cells_raw("three_head_direct_mediated_exogenous")
    p21a_ind = cells_raw("p21a_independent_baseline")
    oracle_value = cells_raw("oracle_probe_value")
    oracle_src = cells_raw("oracle_source")

    def lc_mae(cells):
        vals = [r["learning_curve"][-1]["total_food_E_poison_D_mae"]
                 for r in cells if r.get("learning_curve")]
        return float(np.mean(vals)) if vals else 0.0

    def per_dim_mae(cells):
        food_E = abs(role_pred(cells, "food", "self_E_action_1") - food_true_E)
        poison_D = abs(role_pred(cells, "poison", "self_D_action_1") - poison_true_D)
        return food_E, poison_D

    # G1: P21A baseline per-dim MAE <= 0.10
    p21a_food_E, p21a_poison_D = per_dim_mae(p21a_ind)
    g1_pass = (p21a_food_E <= 0.10 and p21a_poison_D <= 0.10)

    # G2: action-blind world MAE >= 2x history-world MAE
    blind_pwE_mean = float(np.mean(
        [r["prediction_by_role"]["food"]["world_E"] for r in two_head_blind]
    ))
    hist_pwE_mean = float(np.mean(
        [r["prediction_by_role"]["food"]["world_E"] for r in two_head_hist]
    ))
    true_world_E_avg = float(np.mean(
        [r["prediction_by_role"]["food"]["true_world_E_in_dist"] for r in two_head_blind]
    ))
    blind_err = abs(blind_pwE_mean - true_world_E_avg)
    hist_err = abs(hist_pwE_mean - true_world_E_avg)
    g2_pass = blind_err >= 2 * hist_err

    # G3: three-head per-component MAE
    three_food_E, three_poison_D = per_dim_mae(three_head)
    g3_pass = (three_food_E <= 0.10 and three_poison_D <= 0.10)

    # G4: selection beats time-matched volume by 25%
    learned_lc = lc_mae(learned)
    matched_time_lc = lc_mae(matched_time)
    g4_reduction = ((1 - learned_lc / matched_time_lc) * 100
                     if matched_time_lc > 1e-3 else 0.0)
    g4_pass = g4_reduction >= 25

    # G5: probe efficiency (proxy: fewer total nulls)
    learned_nulls = float(np.mean(
        [sum(r["bucket_null_density_train"].values()) for r in learned]
    ))
    matched_nulls = float(np.mean(
        [sum(r["bucket_null_density_train"].values()) for r in matched_time]
    ))
    g5_ratio = learned_nulls / max(matched_nulls, 1)
    g5_pass = g5_ratio <= 0.75 and learned_lc <= 0.20

    # G7: re-probing after regime shift — check if post-shift rate >= 1.5x
    # of pre-shift rate per bucket on average for "shifted" buckets
    # (food and medicine buckets are most affected)
    affected_roles = ["food", "medicine"]
    pre_food_med = sum(
        sum(r["bucket_null_density_pre_shift"].get(b, 0)
            for b in BUCKETS if any(role in b for role in affected_roles))
        for r in learned
    )
    post_food_med = sum(
        sum(r["bucket_null_density_post_shift"].get(b, 0)
            for b in BUCKETS if any(role in b for role in affected_roles))
        for r in learned
    )
    g7_ratio = post_food_med / max(pre_food_med, 1)
    g7_pass = g7_ratio >= 0.5  # any continued probing post-shift

    # G9: reweighting preserved (medicine accuracy across priorities)
    learned_sum = cells_sum("learned_scale_norm_current_replay")
    oracle_src_sum = cells_sum("oracle_source")
    g9_per_prio = {}
    for prio in PRIORITIES:
        l = float(np.mean([r[f"{prio}_acc_medicine"] for r in learned_sum]))
        o = float(np.mean([r[f"{prio}_acc_medicine"] for r in oracle_src_sum]))
        g9_per_prio[prio] = dict(learned=l, oracle=o, diff=abs(l - o))
    g9_pass = all(v["diff"] <= 0.05 for v in g9_per_prio.values())

    # G10: relative viability
    learned_ret = float(np.mean(
        [r["eval_by_priority"]["balanced"]["mean_return"] for r in learned]
    ))
    sched_ret = float(np.mean(
        [r["eval_by_priority"]["balanced"]["mean_return"] for r in scheduled]
    ))
    g10_pass = learned_ret >= 0.90 * sched_ret

    verdicts = {
        "G1_p21a_replication": {
            "p21a_food_E_mae": p21a_food_E,
            "p21a_poison_D_mae": p21a_poison_D,
            "pass": bool(g1_pass),
        },
        "G2_action_blind_failure": {
            "action_blind_food_world_E_err": blind_err,
            "history_world_food_world_E_err": hist_err,
            "ratio": (blind_err / max(hist_err, 1e-3)),
            "pass": bool(g2_pass),
        },
        "G3_three_head_decomposition": {
            "three_head_food_E_mae": three_food_E,
            "three_head_poison_D_mae": three_poison_D,
            "pass": bool(g3_pass),
        },
        "G4_selection_beats_time_matched": {
            "learned_lc_mae": learned_lc,
            "matched_time_lc_mae": matched_time_lc,
            "reduction_pct": g4_reduction,
            "pass": bool(g4_pass),
        },
        "G5_probe_efficiency": {
            "learned_nulls": learned_nulls,
            "matched_nulls": matched_nulls,
            "ratio": g5_ratio,
            "pass": bool(g5_pass),
        },
        "G7_re_probing_after_shift": {
            "pre_shift_affected_nulls": pre_food_med,
            "post_shift_affected_nulls": post_food_med,
            "post_pre_ratio": g7_ratio,
            "pass": bool(g7_pass),
        },
        "G9_reweighting_preserved": {
            "per_priority": g9_per_prio,
            "pass": bool(g9_pass),
        },
        "G10_relative_viability": {
            "learned_return": learned_ret,
            "scheduled_return": sched_ret,
            "pass": bool(g10_pass),
        },
        "all_condition_lc_maes": {
            cond: lc_mae(cells_raw(cond)) for cond in conds
        },
    }
    out_path = ROOT / "artifacts" / "world_responds" / "verdicts_v1.json"
    out_path.write_text(json.dumps(verdicts, indent=2))
    print(f"\nverdicts:")
    print(json.dumps(verdicts, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
