#!/usr/bin/env python3
"""Figures for Paper 17A — Learning When Not to Act."""

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

FIG_DIR = ROOT / "papers" / "costly_null_probes" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

COND_COLORS = {
    "factorized_no_null": "#d62728",
    "factorized_null_passive": "#ff7f0e",
    "scheduled_null_anchor": "#1f77b4",
    "matched_random_null_anchor": "#9467bd",
    "learned_costly_null_probe": "#2ca02c",
    "oracle_uncertainty_probe": "#17becf",
    "oracle_source": "#7f7f7f",
}
COND_LABEL = {
    "factorized_no_null": "factorized\nno null\n(P16 fail)",
    "factorized_null_passive": "passive null\n(no anchor)",
    "scheduled_null_anchor": "scheduled\nnull anchor",
    "matched_random_null_anchor": "matched random\nnull anchor",
    "learned_costly_null_probe": "learned costly\nnull probe\n(HEADLINE)",
    "oracle_uncertainty_probe": "oracle\nuncertainty\nprobe",
    "oracle_source": "oracle source\nlabels",
}

ROLES = ["food", "poison", "medicine", "neutral"]


def load():
    return json.loads(
        (ROOT / "artifacts" / "costly_null_probes" / "sweep_v1.json").read_text()
    )


def group_by(rows, key):
    out = defaultdict(list)
    for r in rows:
        out[r[key]].append(r)
    return out


def filter_cost(rows, cost):
    return [r for r in rows if abs(r["cost"] - cost) < 1e-6]


def cells_for(rows, cond, cost=None):
    out = [r for r in rows if r["condition"] == cond]
    if cost is not None:
        out = [r for r in out if abs(r["cost"] - cost) < 1e-6]
    return out


def main() -> int:
    data = load()
    rows = data["summary"]
    conds = data["manifest"]["conditions"]
    costs = data["manifest"]["costs"]
    cost_headline = data["manifest"]["cost_headline"]
    raw_results = data["results"]

    # =============== Figure 1: per-role self predictions at headline cost ===============
    headline_rows = filter_cost(rows, cost_headline)
    fig, axes = plt.subplots(1, 4, figsize=(20, 5.5), sharey=True)
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
                    f"{mean:+.2f}", ha="center", fontsize=8, fontweight="bold")
        true_self = rows[0][f"true_self_consume_{role}"]
        ax.axhline(true_self, color="green", linewidth=1.8, linestyle="--",
                   alpha=0.7, label=f"true ({true_self:+.2f})")
        ax.set_xticks(x)
        ax.set_xticklabels([COND_LABEL[c] for c in conds], fontsize=6.5, rotation=15)
        ax.set_title(role, fontsize=11)
        if ri == 0:
            ax.set_ylabel("Predicted self ΔE (consume)", fontsize=10)
        ax.axhline(0, color="black", linewidth=0.3)
        ax.legend(loc="best", fontsize=7)
        ax.set_ylim(-2, 2)
        ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.suptitle(
        f"Self-component predictions per role × condition at cost = {cost_headline} "
        "(headline). Learned probe (green) targets oracle-source quality.",
        fontsize=12, y=1.02,
    )
    fig.tight_layout()
    out = FIG_DIR / "fig1_self_predictions.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # =============== Figure 2: per-role world predictions ===============
    fig, axes = plt.subplots(1, 4, figsize=(20, 5.5), sharey=True)
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
                    f"{mean:+.3f}", ha="center", fontsize=8, fontweight="bold")
        true_world = rows[0][f"true_world_in_dist_{role}"]
        ax.axhline(true_world, color="green", linewidth=1.8, linestyle="--",
                   alpha=0.7, label=f"true in-dist ({true_world:+.3f})")
        ax.set_xticks(x)
        ax.set_xticklabels([COND_LABEL[c] for c in conds], fontsize=6.5, rotation=15)
        ax.set_title(role, fontsize=11)
        if ri == 0:
            ax.set_ylabel("Predicted world ΔE", fontsize=10)
        ax.axhline(0, color="black", linewidth=0.3)
        ax.legend(loc="best", fontsize=7)
        ax.set_ylim(-0.5, 0.5)
        ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.suptitle(
        f"World-component predictions per role × condition at cost = {cost_headline}.",
        fontsize=12, y=1.02,
    )
    fig.tight_layout()
    out = FIG_DIR / "fig2_world_predictions.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # =============== Figure 3: G1 / G2 headline — food self overshoot ===============
    fig, ax = plt.subplots(figsize=(12, 5.5))
    x = np.arange(len(conds))
    food_overshoots = []
    for cond in conds:
        cells = cells_for(headline_rows, cond, cost_headline)
        preds = np.array([r["pred_self_consume_food"] for r in cells])
        true_self = rows[0]["true_self_consume_food"]
        food_overshoots.append(
            float(np.mean(preds - true_self)) if len(preds) else 0.0
        )
    ax.bar(x, food_overshoots, 0.6, color=[COND_COLORS[c] for c in conds],
           alpha=0.92, edgecolor="black", linewidth=0.4)
    for i, m in enumerate(food_overshoots):
        ax.text(x[i], m + 0.03 if m >= 0 else m - 0.07,
                f"{m:+.2f}", ha="center", fontsize=11, fontweight="bold")
    no_null_overshoot = food_overshoots[conds.index("factorized_no_null")]
    learned_overshoot = food_overshoots[conds.index("learned_costly_null_probe")]
    matched_overshoot = food_overshoots[conds.index("matched_random_null_anchor")]
    if abs(no_null_overshoot) > 1e-3:
        reduction = (1 - learned_overshoot / no_null_overshoot) * 100
    else:
        reduction = 0
    ax.axhline(0, color="black", linewidth=0.6)
    ax.set_xticks(x)
    ax.set_xticklabels([COND_LABEL[c] for c in conds], fontsize=8)
    ax.set_ylabel("Food self_consume overshoot (pred − true)", fontsize=11)
    ax.set_title(
        f"Food self overshoot at cost = {cost_headline}.  "
        f"Learned probe: {learned_overshoot:+.2f} ({reduction:.0f}% reduction).  "
        f"Matched-random: {matched_overshoot:+.2f}.",
        fontsize=11,
    )
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig3_food_overshoot_headline.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # =============== Figure 4: cost-sensitivity sweep (G4/G5) ===============
    fig, axes = plt.subplots(1, 3, figsize=(16, 5.5))
    cost_relevant_conds = ["learned_costly_null_probe", "oracle_uncertainty_probe",
                            "matched_random_null_anchor"]
    cost_irrelevant_baselines = ["factorized_no_null", "scheduled_null_anchor",
                                  "oracle_source"]
    metrics = [
        ("food_overshoot", "Food self overshoot (pred − true)", -0.1, 1.0),
        ("null_rate", "Null action rate (in-dist eval)", 0, 1.0),
        ("return", "Mean return (in-dist eval)", 0, 55),
    ]
    for ax_idx, (metric_key, ylab, ylo, yhi) in enumerate(metrics):
        ax = axes[ax_idx]
        # Cost-irrelevant baselines as horizontal lines
        for cond in cost_irrelevant_baselines:
            cells = cells_for(rows, cond)
            if metric_key == "food_overshoot":
                preds = np.array([r["pred_self_consume_food"] for r in cells])
                true_self = rows[0]["true_self_consume_food"]
                val = float(np.mean(preds - true_self)) if len(preds) else 0.0
            elif metric_key == "null_rate":
                val = float(np.mean([r["in_dist_null_rate"] for r in cells]))
            else:
                val = float(np.mean([r["in_dist_return"] for r in cells]))
            ax.axhline(val, color=COND_COLORS[cond], linewidth=1.4,
                       linestyle="--", alpha=0.85,
                       label=COND_LABEL[cond].replace("\n", " "))
        for cond in cost_relevant_conds:
            ys = []
            for c in costs:
                cells = cells_for(rows, cond, c)
                if metric_key == "food_overshoot":
                    preds = np.array([r["pred_self_consume_food"] for r in cells])
                    true_self = rows[0]["true_self_consume_food"]
                    ys.append(float(np.mean(preds - true_self))
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
                    markersize=7, linewidth=2,
                    label=COND_LABEL[cond].replace("\n", " "))
            for cx, cy in zip(costs, ys):
                ax.text(cx, cy + (yhi - ylo) * 0.02,
                        f"{cy:.2f}", ha="center", fontsize=7,
                        color=COND_COLORS[cond])
        ax.axvline(cost_headline, color="gray", linewidth=0.5,
                   linestyle=":", alpha=0.7)
        ax.set_xlabel("Per-null cost", fontsize=10)
        ax.set_ylabel(ylab, fontsize=10)
        ax.set_xticks(costs)
        ax.set_ylim(ylo, yhi)
        ax.grid(axis="y", linestyle=":", alpha=0.4)
        if ax_idx == 0:
            ax.legend(loc="best", fontsize=7)
    fig.suptitle(
        f"Cost-sensitivity sweep. Dashed lines = cost-irrelevant baselines.  "
        f"Vertical line at headline cost = {cost_headline}.",
        fontsize=11, y=1.01,
    )
    fig.tight_layout()
    out = FIG_DIR / "fig4_cost_sensitivity.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # =============== Figure 5: G6 / G7 — calibrated probe placement ===============
    # For each (cost, seed) cell of learned and oracle conditions, get per-bucket
    # probe-fire rate and per-bucket oracle uncertainty.
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.5))
    bucket_order = []
    for role in ROLES:
        for eb in ("E_low", "E_high"):
            bucket_order.append(f"{role}_{eb}")

    def per_bucket_probe_rate(cells_subset):
        """Return dict bucket -> mean probe rate across cells."""
        agg_fires = defaultdict(list)
        agg_visits = defaultdict(list)
        for r in cells_subset:
            fires = r["in_dist_eval"]["probe_fires_by_bucket"]
            visits = r["in_dist_eval"]["state_visits_by_bucket"]
            for k in fires:
                agg_fires[k].append(fires[k])
                agg_visits[k].append(visits[k])
        result = {}
        for k in bucket_order:
            f = sum(agg_fires.get(k, []))
            v = sum(agg_visits.get(k, []))
            result[k] = (f / max(v, 1))
        return result

    def per_bucket_oracle_uncertainty(cells_subset):
        agg = defaultdict(list)
        for r in cells_subset:
            for k, b in r["bucket_diag"].items():
                agg[k].append(b["oracle_uncertainty"])
        return {k: float(np.mean(agg[k])) if agg[k] else 0.0 for k in bucket_order}

    # Headline cost
    learned_cells = [r for r in raw_results
                     if r["condition"] == "learned_costly_null_probe"
                     and abs(r["cost"] - cost_headline) < 1e-6]
    oracle_cells = [r for r in raw_results
                    if r["condition"] == "oracle_uncertainty_probe"
                    and abs(r["cost"] - cost_headline) < 1e-6]

    learned_rates = per_bucket_probe_rate(learned_cells)
    oracle_rates = per_bucket_probe_rate(oracle_cells)
    oracle_unc = per_bucket_oracle_uncertainty(learned_cells)

    # Left panel: learned vs oracle probe rate by bucket (scatter)
    ax = axes[0]
    xs = [oracle_rates[b] for b in bucket_order]
    ys = [learned_rates[b] for b in bucket_order]
    ax.scatter(xs, ys, s=80, c=[COND_COLORS["learned_costly_null_probe"]],
               edgecolor="black", alpha=0.85)
    for b, ox, oy in zip(bucket_order, xs, ys):
        ax.annotate(b, (ox, oy), fontsize=7,
                    xytext=(4, 4), textcoords="offset points")
    lim = max(max(xs + ys), 0.5) + 0.05
    ax.plot([0, lim], [0, lim], color="gray", linestyle=":", alpha=0.7,
            label="identity")
    # Spearman correlation (numpy-based; scipy not assumed)
    def _spearman(a, b):
        a = np.asarray(a, dtype=float); b = np.asarray(b, dtype=float)
        if len(a) < 2 or np.std(a) == 0 or np.std(b) == 0:
            return float("nan")
        ar = np.argsort(np.argsort(a))
        br = np.argsort(np.argsort(b))
        return float(np.corrcoef(ar, br)[0, 1])
    rho = _spearman(xs, ys)
    ax.set_xlim(0, lim); ax.set_ylim(0, lim)
    ax.set_xlabel("Oracle probe rate (per bucket)", fontsize=10)
    ax.set_ylabel("Learned probe rate (per bucket)", fontsize=10)
    ax.set_title(f"G6: Learned vs oracle probe rate.  Spearman ρ = {rho:.2f}",
                 fontsize=11)
    ax.legend(loc="best", fontsize=8)
    ax.grid(linestyle=":", alpha=0.4)

    # Right panel: top-quartile vs bottom-quartile fire rates (G7)
    ax = axes[1]
    sorted_buckets = sorted(bucket_order, key=lambda b: oracle_unc[b])
    n = len(sorted_buckets)
    q = max(1, n // 4)
    bot = sorted_buckets[:q]
    top = sorted_buckets[-q:]
    learned_bot = float(np.mean([learned_rates[b] for b in bot]))
    learned_top = float(np.mean([learned_rates[b] for b in top]))
    oracle_bot = float(np.mean([oracle_rates[b] for b in bot]))
    oracle_top = float(np.mean([oracle_rates[b] for b in top]))
    x = np.arange(2)
    w = 0.35
    ax.bar(x - w/2, [learned_bot, learned_top], w,
           color=COND_COLORS["learned_costly_null_probe"],
           alpha=0.9, label="learned", edgecolor="black", linewidth=0.4)
    ax.bar(x + w/2, [oracle_bot, oracle_top], w,
           color=COND_COLORS["oracle_uncertainty_probe"],
           alpha=0.9, label="oracle", edgecolor="black", linewidth=0.4)
    for xi, v in zip([0 - w/2, 1 - w/2, 0 + w/2, 1 + w/2],
                     [learned_bot, learned_top, oracle_bot, oracle_top]):
        ax.text(xi, v + 0.005, f"{v:.2f}", ha="center", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(["bottom quartile\n(low uncertainty)",
                         "top quartile\n(high uncertainty)"], fontsize=9)
    ax.set_ylabel("Mean probe rate", fontsize=10)
    enrich = learned_top / max(learned_bot, 1e-4)
    ax.set_title(
        f"G7: top/bottom enrichment.  Learned ratio = {enrich:.2f}× "
        f"(target ≥ 2×)",
        fontsize=11,
    )
    ax.legend(loc="best", fontsize=9)
    ax.grid(axis="y", linestyle=":", alpha=0.4)

    fig.tight_layout()
    out = FIG_DIR / "fig5_probe_calibration.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # =============== Compute gate verdicts ===============
    def cells_for_raw(cond, cost=None):
        out = [r for r in raw_results if r["condition"] == cond]
        if cost is not None:
            out = [r for r in out if abs(r["cost"] - cost) < 1e-6]
        return out

    def mean_metric(cells, fn):
        vals = [fn(r) for r in cells]
        return float(np.mean(vals)) if vals else 0.0

    food_true = rows[0]["true_self_consume_food"]
    food_world_true = rows[0]["true_world_in_dist_food"]

    learned_cells_h = cells_for_raw("learned_costly_null_probe", cost_headline)
    scheduled_cells = cells_for_raw("scheduled_null_anchor")
    no_null_cells = cells_for_raw("factorized_no_null")
    matched_cells_h = cells_for_raw("matched_random_null_anchor", cost_headline)

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

    g1_self = food_self_mae(learned_cells_h)
    g1_world = food_world_mae(learned_cells_h)
    g1_pass = (g1_self <= 0.12) and (g1_world <= 0.10)

    no_null_overshoot = food_overshoot_signed(no_null_cells)
    learned_overshoot = food_overshoot_signed(learned_cells_h)
    g2_reduction = (
        (1 - learned_overshoot / no_null_overshoot) * 100
        if abs(no_null_overshoot) > 1e-3 else 0.0
    )
    g2_pass = g2_reduction >= 70

    matched_total_mae = food_self_mae(matched_cells_h) + food_world_mae(matched_cells_h)
    learned_total_mae = g1_self + g1_world
    g3_reduction = (
        (1 - learned_total_mae / matched_total_mae) * 100
        if matched_total_mae > 1e-3 else 0.0
    )
    g3_pass = g3_reduction >= 25

    scheduled_overshoot = food_overshoot_signed(scheduled_cells)
    if abs(scheduled_overshoot - no_null_overshoot) > 1e-3:
        scheduled_gain = (no_null_overshoot - scheduled_overshoot)
        learned_gain = (no_null_overshoot - learned_overshoot)
        g4_ratio = learned_gain / scheduled_gain if scheduled_gain != 0 else 0.0
    else:
        g4_ratio = 0.0
    g4_null_rate = mean_metric(learned_cells_h,
                                lambda r: r["in_dist_eval"]["null_rate"])
    g4_pass = g4_ratio >= 0.80 and g4_null_rate <= 0.20

    learned_return = mean_metric(learned_cells_h,
                                  lambda r: r["in_dist_eval"]["mean_return"])
    scheduled_return = mean_metric(scheduled_cells,
                                    lambda r: r["in_dist_eval"]["mean_return"])
    g5_pass = (learned_return >= 0.90 * scheduled_return) and (learned_return >= 45)

    g6_pass = (not np.isnan(rho)) and (rho >= 0.5)
    g7_pass = enrich >= 2.0

    g8_pass = (g1_pass and g6_pass)

    verdicts = {
        "G1_active_identifiability": {
            "criterion": "food self MAE ≤ 0.12 AND food world MAE ≤ 0.10",
            "food_self_mae": g1_self,
            "food_world_mae": g1_world,
            "pass": bool(g1_pass),
        },
        "G2_false_credit_reduction": {
            "criterion": "≥70% reduction in food self overshoot vs no_null",
            "no_null_overshoot": no_null_overshoot,
            "learned_overshoot": learned_overshoot,
            "reduction_pct": g2_reduction,
            "pass": bool(g2_pass),
        },
        "G3_selection_beats_volume": {
            "criterion": "learned MAE ≥ 25% lower than matched_random MAE",
            "matched_total_mae": matched_total_mae,
            "learned_total_mae": learned_total_mae,
            "reduction_pct": g3_reduction,
            "pass": bool(g3_pass),
        },
        "G4_probe_efficiency": {
            "criterion": "≥80% of scheduled gain with ≤20% null rate",
            "ratio_to_scheduled_gain": g4_ratio,
            "null_rate": g4_null_rate,
            "pass": bool(g4_pass),
        },
        "G5_viability_preservation": {
            "criterion": "return ≥90% of scheduled AND ≥45/50 absolute",
            "learned_return": learned_return,
            "scheduled_return": scheduled_return,
            "pass": bool(g5_pass),
        },
        "G6_calibrated_placement": {
            "criterion": "Spearman ρ ≥ 0.5 of learned vs oracle probe rates",
            "spearman_rho": float(rho) if not np.isnan(rho) else None,
            "pass": bool(g6_pass),
        },
        "G7_top_risk_enrichment": {
            "criterion": "top-quartile probe rate ≥ 2× bottom-quartile",
            "top_quartile_rate": learned_top,
            "bottom_quartile_rate": learned_bot,
            "ratio": enrich,
            "pass": bool(g7_pass),
        },
        "G8_behavior_repr_split": {
            "criterion": "G1 + G6 must pass (mechanistic, not just behavioral)",
            "pass": bool(g8_pass),
        },
    }

    summary_out = ROOT / "artifacts" / "costly_null_probes" / "verdicts_v1.json"
    summary_out.write_text(json.dumps(verdicts, indent=2))
    print(f"\nverdicts:")
    print(json.dumps(verdicts, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
