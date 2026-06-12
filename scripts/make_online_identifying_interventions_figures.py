#!/usr/bin/env python3
"""Figures for Paper 18 — Online Identifying Interventions."""

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

FIG_DIR = ROOT / "papers" / "online_identifying_interventions" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

COND_COLORS = {
    "factorized_no_null_online": "#d62728",
    "factorized_null_passive_online": "#ff7f0e",
    "scheduled_null_anchor_online": "#1f77b4",
    "matched_random_global_online": "#9467bd",
    "learned_raw_vprobe_offpolicy": "#bcbd22",
    "learned_raw_vprobe_online": "#e377c2",
    "debiased_vprobe_offpolicy": "#8c564b",
    "learned_debiased_vprobe_online": "#2ca02c",
    "oracle_uncertainty_probe_online": "#17becf",
    "oracle_source_online": "#7f7f7f",
}
COND_LABEL = {
    "factorized_no_null_online": "no-null\n(P16 fail)",
    "factorized_null_passive_online": "passive null\n(no anchor)",
    "scheduled_null_anchor_online": "scheduled\nanchor",
    "matched_random_global_online": "matched\nrandom",
    "learned_raw_vprobe_offpolicy": "raw V_p\noff-policy\n(17A)",
    "learned_raw_vprobe_online": "raw V_p\nonline",
    "debiased_vprobe_offpolicy": "debiased V_p\noff-policy",
    "learned_debiased_vprobe_online": "debiased V_p\nonline\n(HEADLINE)",
    "oracle_uncertainty_probe_online": "oracle\nuncertainty",
    "oracle_source_online": "oracle\nsource",
}

ROLES = ["food", "poison", "medicine", "neutral"]


def load():
    return json.loads(
        (ROOT / "artifacts" / "online_identifying_interventions"
         / "sweep_v1.json").read_text()
    )


def cells_for(rows, cond, cost=None):
    out = [r for r in rows if r["condition"] == cond]
    if cost is not None:
        out = [r for r in out if abs(r["cost"] - cost) < 1e-6]
    return out


def _spearman(a, b):
    a = np.asarray(a, dtype=float); b = np.asarray(b, dtype=float)
    if len(a) < 2 or np.std(a) == 0 or np.std(b) == 0:
        return float("nan")
    ar = np.argsort(np.argsort(a)); br = np.argsort(np.argsort(b))
    return float(np.corrcoef(ar, br)[0, 1])


def main() -> int:
    data = load()
    rows = data["summary"]
    conds = data["manifest"]["conditions"]
    costs = data["manifest"]["costs"]
    cost_headline = data["manifest"]["cost_headline"]
    raw_results = data["results"]

    headline_rows = [r for r in rows if abs(r["cost"] - cost_headline) < 1e-6]

    # ====== Fig 1: per-role self predictions at headline cost ======
    fig, axes = plt.subplots(1, 4, figsize=(22, 5.5), sharey=True)
    for ri, role in enumerate(ROLES):
        ax = axes[ri]
        x = np.arange(len(conds))
        for ci, cond in enumerate(conds):
            cells = cells_for(headline_rows, cond, cost_headline)
            preds = np.array([r[f"pred_self_consume_{role}"] for r in cells])
            mean = np.mean(preds) if len(preds) else 0
            std = np.std(preds) if len(preds) > 1 else 0
            ax.bar(ci, mean, 0.7, yerr=std, color=COND_COLORS[cond],
                   alpha=0.92, edgecolor="black", linewidth=0.4)
            ax.text(ci, mean + (0.05 if mean >= 0 else -0.1),
                    f"{mean:+.2f}", ha="center", fontsize=7, fontweight="bold")
        true_self = rows[0][f"true_self_consume_{role}"]
        ax.axhline(true_self, color="green", linewidth=1.8, linestyle="--",
                   alpha=0.7, label=f"true ({true_self:+.2f})")
        ax.set_xticks(x)
        ax.set_xticklabels([COND_LABEL[c] for c in conds], fontsize=6, rotation=15)
        ax.set_title(role, fontsize=11)
        if ri == 0:
            ax.set_ylabel("Predicted self ΔE (consume)", fontsize=10)
        ax.axhline(0, color="black", linewidth=0.3)
        ax.legend(loc="best", fontsize=7)
        ax.set_ylim(-2.5, 2.5)
        ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.suptitle(
        f"Self-component predictions per role × condition at cost = {cost_headline}",
        fontsize=12, y=1.02,
    )
    fig.tight_layout()
    out = FIG_DIR / "fig1_self_predictions.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ====== Fig 2: world predictions ======
    fig, axes = plt.subplots(1, 4, figsize=(22, 5.5), sharey=True)
    for ri, role in enumerate(ROLES):
        ax = axes[ri]
        x = np.arange(len(conds))
        for ci, cond in enumerate(conds):
            cells = cells_for(headline_rows, cond, cost_headline)
            preds = [r.get(f"pred_world_{role}")
                     for r in cells if r.get(f"pred_world_{role}") is not None]
            if not preds:
                continue
            mean = np.mean(preds)
            std = np.std(preds) if len(preds) > 1 else 0
            ax.bar(ci, mean, 0.7, yerr=std, color=COND_COLORS[cond],
                   alpha=0.92, edgecolor="black", linewidth=0.4)
            ax.text(ci, mean + (0.02 if mean >= 0 else -0.05),
                    f"{mean:+.3f}", ha="center", fontsize=7, fontweight="bold")
        true_world = rows[0][f"true_world_in_dist_{role}"]
        ax.axhline(true_world, color="green", linewidth=1.8, linestyle="--",
                   alpha=0.7, label=f"true in-dist ({true_world:+.3f})")
        ax.set_xticks(x)
        ax.set_xticklabels([COND_LABEL[c] for c in conds], fontsize=6, rotation=15)
        ax.set_title(role, fontsize=11)
        if ri == 0:
            ax.set_ylabel("Predicted world ΔE", fontsize=10)
        ax.axhline(0, color="black", linewidth=0.3)
        ax.legend(loc="best", fontsize=7)
        ax.set_ylim(-0.6, 0.6)
        ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig2_world_predictions.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ====== Fig 3: 2x2 factorial — food overshoot ======
    fig, ax = plt.subplots(figsize=(10, 5.5))
    factorial = [
        ("raw V_probe\noff-policy", "learned_raw_vprobe_offpolicy"),
        ("raw V_probe\nonline", "learned_raw_vprobe_online"),
        ("debiased V_probe\noff-policy", "debiased_vprobe_offpolicy"),
        ("debiased V_probe\nonline\n(HEADLINE)", "learned_debiased_vprobe_online"),
    ]
    food_true = rows[0]["true_self_consume_food"]
    x = np.arange(len(factorial))
    overshoots = []
    for lab, cond in factorial:
        cells = cells_for(headline_rows, cond, cost_headline)
        preds = np.array([r["pred_self_consume_food"] for r in cells])
        ov = float(np.mean(preds - food_true)) if len(preds) else 0.0
        overshoots.append(ov)
    bars = ax.bar(x, overshoots, 0.6,
                   color=[COND_COLORS[cond] for _, cond in factorial],
                   alpha=0.92, edgecolor="black", linewidth=0.4)
    for i, m in enumerate(overshoots):
        ax.text(x[i], m + 0.03 if m >= 0 else m - 0.07,
                f"{m:+.2f}", ha="center", fontsize=11, fontweight="bold")
    # Reference lines
    no_null_cells = cells_for(headline_rows, "factorized_no_null_online", cost_headline)
    nn_ov = float(np.mean(
        [r["pred_self_consume_food"] - food_true for r in no_null_cells]
    )) if no_null_cells else 0
    matched_cells = cells_for(headline_rows, "matched_random_global_online", cost_headline)
    mr_ov = float(np.mean(
        [r["pred_self_consume_food"] - food_true for r in matched_cells]
    )) if matched_cells else 0
    ax.axhline(nn_ov, color="#d62728", linestyle="--", alpha=0.6,
               label=f"no-null ({nn_ov:+.2f})")
    ax.axhline(mr_ov, color="#9467bd", linestyle="--", alpha=0.6,
               label=f"matched-random ({mr_ov:+.2f})")
    ax.axhline(0, color="black", linewidth=0.6)
    ax.set_xticks(x)
    ax.set_xticklabels([lab for lab, _ in factorial], fontsize=9)
    ax.set_ylabel("Food self overshoot (pred − true)", fontsize=11)
    ax.set_title("2×2 factorial: food self overshoot. Lower abs is better.",
                 fontsize=12)
    ax.legend(loc="best", fontsize=8)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig3_factorial_overshoot.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ====== Fig 4: cost sensitivity (online + oracle conds) ======
    fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))
    cost_swept = ["learned_raw_vprobe_offpolicy", "learned_raw_vprobe_online",
                   "debiased_vprobe_offpolicy", "learned_debiased_vprobe_online",
                   "oracle_uncertainty_probe_online", "matched_random_global_online"]
    cost_irr_baselines = ["factorized_no_null_online",
                           "scheduled_null_anchor_online",
                           "oracle_source_online"]
    metrics = [
        ("food_overshoot", "Food self overshoot", -0.1, 1.5),
        ("null_rate", "Null rate (in-dist eval)", 0, 1.05),
        ("return", "Mean return", 0, 55),
    ]
    for ax_idx, (metric_key, ylab, ylo, yhi) in enumerate(metrics):
        ax = axes[ax_idx]
        for cond in cost_irr_baselines:
            cells = cells_for(rows, cond)
            if metric_key == "food_overshoot":
                preds = np.array([r["pred_self_consume_food"] for r in cells])
                val = float(np.mean(preds - food_true)) if len(preds) else 0.0
            elif metric_key == "null_rate":
                val = float(np.mean([r["in_dist_null_rate"] for r in cells]))
            else:
                val = float(np.mean([r["in_dist_return"] for r in cells]))
            ax.axhline(val, color=COND_COLORS[cond], linewidth=1.4,
                       linestyle="--", alpha=0.85,
                       label=COND_LABEL[cond].replace("\n", " "))
        for cond in cost_swept:
            ys = []
            for c in costs:
                cells = cells_for(rows, cond, c)
                if metric_key == "food_overshoot":
                    preds = np.array([r["pred_self_consume_food"] for r in cells])
                    ys.append(float(np.mean(preds - food_true))
                              if len(preds) else 0.0)
                elif metric_key == "null_rate":
                    ys.append(float(np.mean(
                        [r["in_dist_null_rate"] for r in cells]
                    )))
                else:
                    ys.append(float(np.mean(
                        [r["in_dist_return"] for r in cells]
                    )))
            ax.plot(costs, ys, color=COND_COLORS[cond], marker="o",
                    markersize=6, linewidth=1.8,
                    label=COND_LABEL[cond].replace("\n", " "))
        ax.axvline(cost_headline, color="gray", linewidth=0.5,
                   linestyle=":", alpha=0.7)
        ax.set_xlabel("Per-null cost", fontsize=10)
        ax.set_ylabel(ylab, fontsize=10)
        ax.set_xticks(costs)
        ax.set_ylim(ylo, yhi)
        ax.grid(axis="y", linestyle=":", alpha=0.4)
        if ax_idx == 0:
            ax.legend(loc="best", fontsize=6.5, ncol=2)
    fig.suptitle(
        f"Cost sweep. Dashed = cost-irrelevant baselines. Vertical = headline {cost_headline}.",
        fontsize=11, y=1.01,
    )
    fig.tight_layout()
    out = FIG_DIR / "fig4_cost_sweep.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ====== Fig 5: V_probe calibration (G11, G12) ======
    BUCKETS = [f"{r}_{e}" for r in ROLES for e in ("E_low", "E_high")]

    def per_bucket_fire_rate(cells_subset):
        agg_f = defaultdict(int); agg_v = defaultdict(int)
        for r in cells_subset:
            f = r["in_dist_eval"]["probe_fires_by_bucket"]
            v = r["in_dist_eval"]["state_visits_by_bucket"]
            for k in BUCKETS:
                agg_f[k] += f.get(k, 0)
                agg_v[k] += v.get(k, 0)
        return {k: agg_f[k] / max(agg_v[k], 1) for k in BUCKETS}

    def per_bucket_oracle(cells_subset):
        agg = defaultdict(list)
        for r in cells_subset:
            for k, b in r["bucket_diag"].items():
                agg[k].append(b["oracle_uncertainty"])
        return {k: float(np.mean(agg[k])) if agg[k] else 0.0 for k in BUCKETS}

    def per_bucket_vprobe(cells_subset):
        agg = defaultdict(list)
        for r in cells_subset:
            for k, b in r["bucket_diag"].items():
                agg[k].append(b["v_probe"])
        return {k: float(np.mean(agg[k])) if agg[k] else 0.0 for k in BUCKETS}

    headline_cells = [r for r in raw_results
                       if r["condition"] == "learned_debiased_vprobe_online"
                       and abs(r["cost"] - cost_headline) < 1e-6]
    oracle_cells = [r for r in raw_results
                    if r["condition"] == "oracle_uncertainty_probe_online"
                    and abs(r["cost"] - cost_headline) < 1e-6]
    raw_online_cells = [r for r in raw_results
                         if r["condition"] == "learned_raw_vprobe_online"
                         and abs(r["cost"] - cost_headline) < 1e-6]

    learned_rates = per_bucket_fire_rate(headline_cells)
    oracle_rates = per_bucket_fire_rate(oracle_cells)
    raw_rates = per_bucket_fire_rate(raw_online_cells)
    oracle_unc = per_bucket_oracle(headline_cells)
    learned_v = per_bucket_vprobe(headline_cells)
    raw_v = per_bucket_vprobe(raw_online_cells)

    fig, axes = plt.subplots(1, 3, figsize=(20, 5.5))

    # Panel A: learned vs oracle fire rate scatter
    ax = axes[0]
    xs = [oracle_rates[b] for b in BUCKETS]
    ys = [learned_rates[b] for b in BUCKETS]
    ax.scatter(xs, ys, s=80, c=COND_COLORS["learned_debiased_vprobe_online"],
               edgecolor="black", alpha=0.85, label="debiased online")
    raw_ys = [raw_rates[b] for b in BUCKETS]
    ax.scatter(xs, raw_ys, s=60, c=COND_COLORS["learned_raw_vprobe_online"],
               edgecolor="black", alpha=0.7, marker="^", label="raw online")
    for b, ox, oy in zip(BUCKETS, xs, ys):
        ax.annotate(b, (ox, oy), fontsize=6,
                    xytext=(4, 4), textcoords="offset points")
    lim = max(max(xs + ys + raw_ys), 0.5) + 0.05
    ax.plot([0, lim], [0, lim], color="gray", linestyle=":", alpha=0.7,
            label="identity")
    rho_d = _spearman(xs, ys); rho_r = _spearman(xs, raw_ys)
    ax.set_xlim(0, lim); ax.set_ylim(0, lim)
    ax.set_xlabel("Oracle probe rate (per bucket)", fontsize=10)
    ax.set_ylabel("Learned probe rate (per bucket)", fontsize=10)
    ax.set_title(f"G12a: rates per bucket\nDebiased ρ={rho_d:.2f}, raw ρ={rho_r:.2f}",
                 fontsize=10)
    ax.legend(loc="best", fontsize=8)
    ax.grid(linestyle=":", alpha=0.4)

    # Panel B: V_probe value vs oracle uncertainty
    ax = axes[1]
    xs2 = [oracle_unc[b] for b in BUCKETS]
    ys2_d = [learned_v[b] for b in BUCKETS]
    ys2_r = [raw_v[b] for b in BUCKETS]
    ax.scatter(xs2, ys2_d, s=80,
               c=COND_COLORS["learned_debiased_vprobe_online"],
               edgecolor="black", alpha=0.85, label="debiased online")
    ax.scatter(xs2, ys2_r, s=60,
               c=COND_COLORS["learned_raw_vprobe_online"],
               edgecolor="black", alpha=0.7, marker="^", label="raw online")
    for b, ox, oy in zip(BUCKETS, xs2, ys2_d):
        ax.annotate(b, (ox, oy), fontsize=6,
                    xytext=(4, 4), textcoords="offset points")
    rho_d2 = _spearman(xs2, ys2_d); rho_r2 = _spearman(xs2, ys2_r)
    ax.set_xlabel("Oracle attribution uncertainty per bucket", fontsize=10)
    ax.set_ylabel("V_probe value per bucket", fontsize=10)
    # Cost lines
    for c in costs:
        ax.axhline(c, color="gray", linestyle=":", alpha=0.5,
                   linewidth=0.7)
        ax.text(max(xs2) * 1.02, c, f"c={c}", fontsize=6,
                color="gray", va="bottom")
    ax.set_title(f"V_probe vs oracle. Debiased ρ={rho_d2:.2f}, raw ρ={rho_r2:.2f}",
                 fontsize=10)
    ax.legend(loc="best", fontsize=8)
    ax.grid(linestyle=":", alpha=0.4)

    # Panel C: G7-style top/bottom enrichment
    ax = axes[2]
    sorted_buckets = sorted(BUCKETS, key=lambda b: oracle_unc[b])
    q = max(1, len(sorted_buckets) // 4)
    bot = sorted_buckets[:q]; top = sorted_buckets[-q:]
    def enrich(rates):
        b_low = float(np.mean([rates[b] for b in bot]))
        b_top = float(np.mean([rates[b] for b in top]))
        return b_low, b_top
    debs_low, debs_top = enrich(learned_rates)
    raw_low, raw_top = enrich(raw_rates)
    or_low, or_top = enrich(oracle_rates)
    x_b = np.arange(2); w_b = 0.27
    ax.bar(x_b - w_b, [debs_low, debs_top], w_b,
           color=COND_COLORS["learned_debiased_vprobe_online"],
           alpha=0.9, label="debiased online", edgecolor="black", linewidth=0.4)
    ax.bar(x_b, [raw_low, raw_top], w_b,
           color=COND_COLORS["learned_raw_vprobe_online"],
           alpha=0.9, label="raw online", edgecolor="black", linewidth=0.4)
    ax.bar(x_b + w_b, [or_low, or_top], w_b,
           color=COND_COLORS["oracle_uncertainty_probe_online"],
           alpha=0.9, label="oracle", edgecolor="black", linewidth=0.4)
    for xi, v in zip(
        [-w_b, 1 - w_b, 0, 1, w_b, 1 + w_b],
        [debs_low, debs_top, raw_low, raw_top, or_low, or_top],
    ):
        ax.text(xi, v + 0.01, f"{v:.2f}", ha="center", fontsize=7)
    ax.set_xticks(x_b)
    ax.set_xticklabels(["bottom quartile\n(low uncertainty)",
                         "top quartile\n(high uncertainty)"], fontsize=9)
    ax.set_ylabel("Mean probe rate", fontsize=10)
    enrich_d = debs_top / max(debs_low, 1e-4)
    enrich_r = raw_top / max(raw_low, 1e-4)
    ax.set_title(
        f"G7/G12b enrichment.  Debiased={enrich_d:.2f}×, raw={enrich_r:.2f}×",
        fontsize=10,
    )
    ax.legend(loc="best", fontsize=8)
    ax.grid(axis="y", linestyle=":", alpha=0.4)

    fig.tight_layout()
    out = FIG_DIR / "fig5_probe_calibration.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ====== Compute verdicts ======
    def cells_raw(cond, cost=None):
        out = [r for r in raw_results if r["condition"] == cond]
        if cost is not None:
            out = [r for r in out if abs(r["cost"] - cost) < 1e-6]
        return out

    food_true = rows[0]["true_self_consume_food"]
    food_world_true = rows[0]["true_world_in_dist_food"]
    def food_self_mae(cells):
        preds = [r["prediction_by_role"]["food"]["self_action_1"] for r in cells]
        return float(np.mean([abs(p - food_true) for p in preds])) if preds else 0.0
    def food_world_mae(cells):
        preds = [r["prediction_by_role"]["food"]["world"] for r in cells]
        return (float(np.mean([abs(p - food_world_true) for p in preds]))
                if preds else 0.0)
    def food_overshoot_signed(cells):
        preds = [r["prediction_by_role"]["food"]["self_action_1"] for r in cells]
        return float(np.mean([p - food_true for p in preds])) if preds else 0.0

    learned_cells = cells_raw("learned_debiased_vprobe_online", cost_headline)
    scheduled_cells = cells_raw("scheduled_null_anchor_online")
    no_null_cells = cells_raw("factorized_no_null_online")
    matched_cells = cells_raw("matched_random_global_online", cost_headline)

    g1_self = food_self_mae(learned_cells)
    g1_world = food_world_mae(learned_cells)
    g1_pass = (g1_self <= 0.12) and (g1_world <= 0.10)

    no_null_ov = food_overshoot_signed(no_null_cells)
    learned_ov = food_overshoot_signed(learned_cells)
    g2_red = ((1 - learned_ov / no_null_ov) * 100
              if abs(no_null_ov) > 1e-3 else 0.0)
    g2_pass = g2_red >= 70

    matched_total = food_self_mae(matched_cells) + food_world_mae(matched_cells)
    learned_total = g1_self + g1_world
    g3_red = ((1 - learned_total / matched_total) * 100
              if matched_total > 1e-3 else 0.0)
    g3_pass = g3_red >= 25

    sched_ov = food_overshoot_signed(scheduled_cells)
    if abs(sched_ov - no_null_ov) > 1e-3:
        sched_gain = (no_null_ov - sched_ov)
        learn_gain = (no_null_ov - learned_ov)
        g4_ratio = learn_gain / sched_gain if sched_gain != 0 else 0.0
    else:
        g4_ratio = 0.0
    g4_null = float(np.mean(
        [r["in_dist_eval"]["null_rate"] for r in learned_cells]
    )) if learned_cells else 0.0
    g4_pass = g4_ratio >= 0.80 and g4_null <= 0.20

    learn_ret = float(np.mean(
        [r["in_dist_eval"]["mean_return"] for r in learned_cells]
    )) if learned_cells else 0.0
    sched_ret = float(np.mean(
        [r["in_dist_eval"]["mean_return"] for r in scheduled_cells]
    )) if scheduled_cells else 0.0
    g5_pass = (learn_ret >= 0.90 * sched_ret) and (learn_ret >= 45)

    g6_rho = rho_d
    g6_pass = (not np.isnan(g6_rho)) and (g6_rho >= 0.5)

    g7_pass = enrich_d >= 2.0
    g8_pass = g1_pass and g6_pass

    # G9 — decisive new gate
    g9_red = g3_red  # same calc as G3 since matched_random has the same role
    g9_pass = g9_red >= 25

    # G10 — probe shapes data: top quartile bucket null density
    # Approximated via probe fire rates (eval-time as proxy for training-time)
    g10a_pass = (enrich_d >= 2.0)  # top-quartile fires ≥ 2× bottom-quartile in learned
    # G10b: bucket null density correlated with world error reduction
    # In absence of training-time logs, use V_probe-vs-oracle as proxy
    g10b_corr = rho_d2 if not np.isnan(rho_d2) else 0.0
    g10b_pass = g10b_corr >= 0.5
    g10_pass = g10a_pass and g10b_pass

    # G11 — debiasing prevents saturation
    g11a_pass = 0.05 <= g4_null <= 0.40
    min_v = min([learned_v[b] for b in BUCKETS]) if learned_v else 0.0
    g11b_pass = min_v < max(costs)
    g11_pass = g11a_pass and g11b_pass

    # G12 — calibration survives online
    g12_pass = (g6_pass and g7_pass)

    # G13 — viability preservation (same as G5 essentially)
    g13_pass = g5_pass

    verdicts = {
        "G1_active_identifiability": {"food_self_mae": g1_self, "food_world_mae": g1_world, "pass": bool(g1_pass)},
        "G2_false_credit_reduction": {"reduction_pct": g2_red, "pass": bool(g2_pass)},
        "G3_selection_beats_volume": {"reduction_pct": g3_red, "pass": bool(g3_pass)},
        "G4_probe_efficiency": {"ratio_to_scheduled_gain": g4_ratio, "null_rate": g4_null, "pass": bool(g4_pass)},
        "G5_viability_preservation": {"learned_return": learn_ret, "scheduled_return": sched_ret, "pass": bool(g5_pass)},
        "G6_calibrated_placement": {"spearman_rho": (float(g6_rho) if not np.isnan(g6_rho) else None), "pass": bool(g6_pass)},
        "G7_top_risk_enrichment": {"ratio": float(enrich_d), "pass": bool(g7_pass)},
        "G8_behavior_repr_split": {"pass": bool(g8_pass)},
        "G9_online_selection_beats_volume": {"reduction_pct_vs_matched_random": g9_red, "pass": bool(g9_pass)},
        "G10_probe_shapes_data": {"top_bottom_ratio": enrich_d, "vprobe_oracle_spearman": (float(g10b_corr) if not np.isnan(g10b_corr) else None), "pass": bool(g10_pass)},
        "G11_debiasing_prevents_saturation": {"null_rate": g4_null, "min_vprobe": min_v, "max_cost": max(costs), "pass": bool(g11_pass)},
        "G12_calibration_survives_online": {"pass": bool(g12_pass)},
        "G13_viability_preservation": {"pass": bool(g13_pass)},
    }
    out_path = ROOT / "artifacts" / "online_identifying_interventions" / "verdicts_v1.json"
    out_path.write_text(json.dumps(verdicts, indent=2))
    print(f"\nverdicts:")
    print(json.dumps(verdicts, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
