#!/usr/bin/env python3
"""Figures for Paper 21A — Scale-Normalized V_probe Calibration."""

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

FIG_DIR = ROOT / "papers" / "scale_normalized_vprobe" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

COND_COLORS = {
    "raw_global_cost": "#d62728",
    "norm_target_global_cost": "#ff7f0e",
    "raw_target_perdim_cost": "#bcbd22",
    "norm_target_perdim_cost": "#2ca02c",
    "norm_target_dim_balanced_floor": "#1a8c1a",
    "matched_random_total": "#9467bd",
    "matched_random_bucket_balanced": "#aec7e8",
    "vector_scheduled_null_anchor": "#1f77b4",
    "vector_oracle_uncertainty_probe": "#17becf",
    "vector_oracle_source": "#7f7f7f",
}
COND_LABEL = {
    "raw_global_cost": "raw\nglobal\n(P20B)",
    "norm_target_global_cost": "norm\nglobal\n(H1)",
    "raw_target_perdim_cost": "raw\nper-dim\n(H2)",
    "norm_target_perdim_cost": "norm\nper-dim\n(HEADLINE)",
    "norm_target_dim_balanced_floor": "norm\nper-dim\n+audit",
    "matched_random_total": "matched\nrandom\n(total)",
    "matched_random_bucket_balanced": "matched\nrandom\n(balanced)",
    "vector_scheduled_null_anchor": "scheduled\nanchor",
    "vector_oracle_uncertainty_probe": "oracle\nuncertainty",
    "vector_oracle_source": "oracle\nsource",
}
ROLES = ["food", "poison", "medicine", "neutral"]
PRIORITIES = ["balanced", "hungry", "injured"]


def _spearman(a, b):
    a = np.asarray(a, dtype=float); b = np.asarray(b, dtype=float)
    if len(a) < 2 or np.std(a) == 0 or np.std(b) == 0:
        return float("nan")
    ar = np.argsort(np.argsort(a)); br = np.argsort(np.argsort(b))
    return float(np.corrcoef(ar, br)[0, 1])


def main() -> int:
    data = json.loads(
        (ROOT / "artifacts" / "scale_normalized_vprobe" / "sweep_v1.json").read_text()
    )
    rows = data["summary"]
    conds = data["manifest"]["conditions"]
    raw_results = data["results"]
    food_true_E = rows[0]["true_self_E_consume_food"]
    poison_true_D = rows[0]["true_self_D_consume_poison"]
    food_world_E_true = rows[0]["true_world_E_food"]
    poison_world_D_true = rows[0]["true_world_D_poison"]

    def cells_raw(cond): return [r for r in raw_results if r["condition"] == cond]
    def cells_sum(cond): return [r for r in rows if r["condition"] == cond]

    # ====== Fig 1: per-dim predictions ======
    fig, axes = plt.subplots(2, 2, figsize=(18, 10))
    metrics = [
        ("food self_E (consume)", "pred_self_E_consume_food", food_true_E),
        ("food world_E", "pred_world_E_food", food_world_E_true),
        ("poison self_D (consume)", "pred_self_D_consume_poison", poison_true_D),
        ("poison world_D", "pred_world_D_poison", poison_world_D_true),
    ]
    for idx, (title, key, true_val) in enumerate(metrics):
        ax = axes[idx // 2, idx % 2]
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
        ax.axhline(true_val, color="green", linewidth=1.8, linestyle="--",
                   alpha=0.7, label=f"true ({true_val:+.2f})")
        ax.set_xticks(x)
        ax.set_xticklabels([COND_LABEL[c] for c in conds], fontsize=6,
                            rotation=15)
        ax.set_title(title, fontsize=11)
        ax.axhline(0, color="black", linewidth=0.3)
        ax.legend(loc="best", fontsize=8)
        ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig1_per_dim_predictions.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ====== Fig 2: factorial 2x2 — total MAE ======
    fig, ax = plt.subplots(figsize=(11, 6))
    factorial_conds = [
        "raw_global_cost",
        "norm_target_global_cost",
        "raw_target_perdim_cost",
        "norm_target_perdim_cost",
    ]
    x = np.arange(len(factorial_conds))
    total_maes = []
    for cond in factorial_conds:
        cells = cells_raw(cond)
        if not cells:
            total_maes.append(0); continue
        f_E = np.mean([c["prediction_by_role"]["food"]["self_E_action_1"] for c in cells])
        f_E_w = np.mean([c["prediction_by_role"]["food"]["world_E"] for c in cells])
        p_D = np.mean([c["prediction_by_role"]["poison"]["self_D_action_1"] for c in cells])
        p_D_w = np.mean([c["prediction_by_role"]["poison"]["world_D"] for c in cells])
        total_maes.append(abs(f_E - food_true_E) + abs(f_E_w - food_world_E_true)
                           + abs(p_D - poison_true_D) + abs(p_D_w - poison_world_D_true))
    bars = ax.bar(x, total_maes, 0.6,
                   color=[COND_COLORS[c] for c in factorial_conds],
                   alpha=0.92, edgecolor="black", linewidth=0.4)
    for i, m in enumerate(total_maes):
        ax.text(x[i], m + 0.005, f"{m:.3f}", ha="center", fontsize=10,
                fontweight="bold")
    # Reference lines
    mr_cells = cells_raw("matched_random_total")
    if mr_cells:
        f_E = np.mean([c["prediction_by_role"]["food"]["self_E_action_1"] for c in mr_cells])
        f_E_w = np.mean([c["prediction_by_role"]["food"]["world_E"] for c in mr_cells])
        p_D = np.mean([c["prediction_by_role"]["poison"]["self_D_action_1"] for c in mr_cells])
        p_D_w = np.mean([c["prediction_by_role"]["poison"]["world_D"] for c in mr_cells])
        mr_mae = (abs(f_E - food_true_E) + abs(f_E_w - food_world_E_true)
                   + abs(p_D - poison_true_D) + abs(p_D_w - poison_world_D_true))
        ax.axhline(mr_mae, color="#9467bd", linestyle="--", alpha=0.7,
                   label=f"matched_random_total ({mr_mae:.3f})")
    or_cells = cells_raw("vector_oracle_source")
    if or_cells:
        f_E = np.mean([c["prediction_by_role"]["food"]["self_E_action_1"] for c in or_cells])
        f_E_w = np.mean([c["prediction_by_role"]["food"]["world_E"] for c in or_cells])
        p_D = np.mean([c["prediction_by_role"]["poison"]["self_D_action_1"] for c in or_cells])
        p_D_w = np.mean([c["prediction_by_role"]["poison"]["world_D"] for c in or_cells])
        or_mae = (abs(f_E - food_true_E) + abs(f_E_w - food_world_E_true)
                   + abs(p_D - poison_true_D) + abs(p_D_w - poison_world_D_true))
        ax.axhline(or_mae, color="#7f7f7f", linestyle=":", alpha=0.7,
                   label=f"oracle_source ({or_mae:.3f})")
    ax.set_xticks(x)
    ax.set_xticklabels([COND_LABEL[c] for c in factorial_conds], fontsize=9)
    ax.set_ylabel("Total component MAE", fontsize=11)
    ax.set_title("2×2 factorial: target × threshold normalization", fontsize=12)
    ax.legend(loc="best", fontsize=9)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig2_factorial.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ====== Fig 3: dim-wise calibration ======
    BUCKETS = [f"{r}_{eb}_{db}" for r in ROLES
               for eb in ("E_low", "E_high") for db in ("D_low", "D_high")]

    def per_bucket_fire_rate(cells_subset, dist="balanced"):
        agg_f = defaultdict(int); agg_v = defaultdict(int)
        for r in cells_subset:
            ev = r["eval_by_priority"][dist]
            f = ev["probe_fires_by_bucket"]; v = ev["state_visits_by_bucket"]
            for k in BUCKETS:
                agg_f[k] += f.get(k, 0); agg_v[k] += v.get(k, 0)
        return {k: agg_f[k] / max(agg_v[k], 1) for k in BUCKETS}

    def per_bucket_metric(cells_subset, key):
        agg = defaultdict(list)
        for r in cells_subset:
            for k, b in r["bucket_diag"].items():
                agg[k].append(b.get(key, 0.0))
        return {k: float(np.mean(agg[k])) if agg[k] else 0.0 for k in BUCKETS}

    headline = cells_raw("norm_target_perdim_cost")
    p20b_repro = cells_raw("raw_global_cost")
    oracle_unc_E = per_bucket_metric(headline, "oracle_unc_E")
    oracle_unc_D = per_bucket_metric(headline, "oracle_unc_D")
    v_probe_E_b = per_bucket_metric(headline, "v_probe_E")
    v_probe_D_b = per_bucket_metric(headline, "v_probe_D")
    p20b_v_probe_E = per_bucket_metric(p20b_repro, "v_probe_E")
    p20b_v_probe_D = per_bucket_metric(p20b_repro, "v_probe_D")

    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    for ax_idx, dim in enumerate(["E", "D"]):
        ax = axes[ax_idx]
        oracle = oracle_unc_E if dim == "E" else oracle_unc_D
        headline_v = v_probe_E_b if dim == "E" else v_probe_D_b
        repro_v = p20b_v_probe_E if dim == "E" else p20b_v_probe_D
        xs = [oracle[b] for b in BUCKETS]
        ys_h = [headline_v[b] for b in BUCKETS]
        ys_r = [repro_v[b] for b in BUCKETS]
        ax.scatter(xs, ys_h, s=70, c=COND_COLORS["norm_target_perdim_cost"],
                   edgecolor="black", alpha=0.85, label="HEADLINE norm+perdim")
        ax.scatter(xs, ys_r, s=50, c=COND_COLORS["raw_global_cost"],
                   edgecolor="black", alpha=0.7, marker="^", label="P20B (raw+global)")
        for b, ox, oy in zip(BUCKETS, xs, ys_h):
            ax.annotate(b, (ox, oy), fontsize=5, xytext=(3, 3),
                        textcoords="offset points")
        rho_h = _spearman(xs, ys_h); rho_r = _spearman(xs, ys_r)
        ax.set_xlabel(f"Oracle current attribution error ({dim} dim)", fontsize=10)
        ax.set_ylabel(f"V_probe_{dim}", fontsize=10)
        ax.set_title(f"{dim} dim: ρ_headline={rho_h:.2f}  ρ_P20B={rho_r:.2f}",
                     fontsize=11)
        ax.legend(loc="best", fontsize=8)
        ax.grid(linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig3_dim_calibration.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ====== Fig 4: total MAE all conditions ======
    fig, ax = plt.subplots(figsize=(14, 6))
    x = np.arange(len(conds))
    total_maes_all = []
    for cond in conds:
        cells = cells_raw(cond)
        if not cells:
            total_maes_all.append(0); continue
        f_E = np.mean([c["prediction_by_role"]["food"]["self_E_action_1"] for c in cells])
        f_E_w = np.mean([c["prediction_by_role"]["food"]["world_E"] for c in cells])
        p_D = np.mean([c["prediction_by_role"]["poison"]["self_D_action_1"] for c in cells])
        p_D_w = np.mean([c["prediction_by_role"]["poison"]["world_D"] for c in cells])
        total_maes_all.append(abs(f_E - food_true_E) + abs(f_E_w - food_world_E_true)
                                + abs(p_D - poison_true_D) + abs(p_D_w - poison_world_D_true))
    ax.bar(x, total_maes_all, 0.7,
           color=[COND_COLORS[c] for c in conds], alpha=0.92,
           edgecolor="black", linewidth=0.4)
    for i, m in enumerate(total_maes_all):
        ax.text(x[i], m + 0.005, f"{m:.3f}", ha="center", fontsize=8,
                fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([COND_LABEL[c] for c in conds], fontsize=6,
                        rotation=15)
    ax.set_ylabel("Total component MAE", fontsize=10)
    ax.set_title("Total attribution MAE per condition", fontsize=11)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig4_total_mae.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ====== Verdicts ======
    def role_pred(cells, role, key):
        return float(np.mean([r["prediction_by_role"][role][key]
                                for r in cells])) if cells else 0.0

    def total_mae(cells):
        if not cells: return 0.0
        f_E = role_pred(cells, "food", "self_E_action_1")
        f_E_w = role_pred(cells, "food", "world_E")
        p_D = role_pred(cells, "poison", "self_D_action_1")
        p_D_w = role_pred(cells, "poison", "world_D")
        return (abs(f_E - food_true_E) + abs(f_E_w - food_world_E_true)
                + abs(p_D - poison_true_D) + abs(p_D_w - poison_world_D_true))

    learned = cells_raw("norm_target_perdim_cost")
    matched_total_cells = cells_raw("matched_random_total")
    scheduled = cells_raw("vector_scheduled_null_anchor")
    oracle_src = cells_raw("vector_oracle_source")

    food_self_E_mae = abs(role_pred(learned, "food", "self_E_action_1") - food_true_E)
    food_world_E_mae = abs(role_pred(learned, "food", "world_E") - food_world_E_true)
    poison_self_D_mae = abs(role_pred(learned, "poison", "self_D_action_1") - poison_true_D)
    poison_world_D_mae = abs(role_pred(learned, "poison", "world_D") - poison_world_D_true)
    g1_pass = all(m <= 0.10 for m in [food_self_E_mae, food_world_E_mae,
                                       poison_self_D_mae, poison_world_D_mae])

    p20b_food_E_overshoot = role_pred(p20b_repro, "food", "self_E_action_1") - food_true_E
    p20b_poison_D_overshoot = role_pred(p20b_repro, "poison", "self_D_action_1") - poison_true_D
    learn_food_E_over = role_pred(learned, "food", "self_E_action_1") - food_true_E
    learn_poison_D_over = role_pred(learned, "poison", "self_D_action_1") - poison_true_D
    food_E_red = ((1 - learn_food_E_over / p20b_food_E_overshoot) * 100
                   if abs(p20b_food_E_overshoot) > 1e-3 else 0.0)
    poison_D_red = ((1 - learn_poison_D_over / p20b_poison_D_overshoot) * 100
                     if abs(p20b_poison_D_overshoot) > 1e-3 else 0.0)
    g2_pass = food_E_red >= 70 and poison_D_red >= 70

    headline_rates = per_bucket_fire_rate(headline, "balanced")
    rho_E = _spearman([oracle_unc_E[b] for b in BUCKETS],
                       [headline_rates[b] for b in BUCKETS])
    rho_D = _spearman([oracle_unc_D[b] for b in BUCKETS],
                       [headline_rates[b] for b in BUCKETS])
    g14_pass = ((not np.isnan(rho_D)) and rho_D >= 0.5)
    g17_E_pass = ((not np.isnan(rho_E)) and rho_E >= 0.2)

    learned_total = total_mae(learned)
    matched_total = total_mae(matched_total_cells)
    g15_red = ((1 - learned_total / matched_total) * 100
                if matched_total > 1e-3 else 0.0)
    g15_pass = g15_red >= 25

    p_D_pred = role_pred(learned, "poison", "self_D_action_1")
    p_D_w_pred = role_pred(learned, "poison", "world_D")
    learn_D_mae = (abs(p_D_pred - poison_true_D)
                    + abs(p_D_w_pred - poison_world_D_true))
    m_p_D = role_pred(matched_total_cells, "poison", "self_D_action_1")
    m_p_D_w = role_pred(matched_total_cells, "poison", "world_D")
    matched_D_mae = (abs(m_p_D - poison_true_D)
                      + abs(m_p_D_w - poison_world_D_true))
    g16_red = ((1 - learn_D_mae / matched_D_mae) * 100
                if matched_D_mae > 1e-3 else 0.0)
    g16_pass = g16_red >= 25

    sorted_buckets_E = sorted(BUCKETS, key=lambda b: oracle_unc_E[b])
    sorted_buckets_D = sorted(BUCKETS, key=lambda b: oracle_unc_D[b])
    q = max(1, len(BUCKETS) // 4)
    def enrich(sorted_b):
        bot = float(np.mean([headline_rates[b] for b in sorted_b[:q]]))
        top = float(np.mean([headline_rates[b] for b in sorted_b[-q:]]))
        return top / max(bot, 1e-4), top, bot
    g19_E, top_E, bot_E = enrich(sorted_buckets_E)
    g19_D, top_D, bot_D = enrich(sorted_buckets_D)
    g19_pass = g19_E >= 2.0 and g19_D >= 2.0

    g18_pass = ((max(food_self_E_mae, food_world_E_mae, poison_self_D_mae, poison_world_D_mae)
                  <= 2 * min(food_self_E_mae, food_world_E_mae, poison_self_D_mae, poison_world_D_mae))
                 or (max(food_self_E_mae, food_world_E_mae, poison_self_D_mae, poison_world_D_mae) <= 0.07))

    learned_null = float(np.mean(
        [r["eval_by_priority"]["balanced"]["null_rate"] for r in learned]
    )) if learned else 0.0
    g20_pass = 0.001 <= learned_null <= 0.40

    learned_ret = float(np.mean(
        [r["eval_by_priority"]["balanced"]["mean_return"] for r in learned]
    )) if learned else 0.0
    sched_ret = float(np.mean(
        [r["eval_by_priority"]["balanced"]["mean_return"] for r in scheduled]
    )) if scheduled else 0.0
    g22_pass = (learned_ret >= 0.90 * sched_ret)

    learned_sum = cells_sum("norm_target_perdim_cost")
    oracle_src_sum = cells_sum("vector_oracle_source")
    g21_per_prio = {}
    for prio in PRIORITIES:
        l = float(np.mean([r[f"{prio}_acc_medicine"] for r in learned_sum]))
        o = float(np.mean([r[f"{prio}_acc_medicine"] for r in oracle_src_sum]))
        g21_per_prio[prio] = dict(learned=l, oracle=o, diff=abs(l - o))
    g21_pass = all(v["diff"] <= 0.05 for v in g21_per_prio.values())

    g23_pass = g14_pass and g15_pass

    verdicts = {
        "G1_per_dim_attribution": {
            "food_self_E_mae": food_self_E_mae,
            "food_world_E_mae": food_world_E_mae,
            "poison_self_D_mae": poison_self_D_mae,
            "poison_world_D_mae": poison_world_D_mae,
            "pass": bool(g1_pass),
        },
        "G2_false_credit_reduction": {
            "food_E_reduction_pct": food_E_red,
            "poison_D_reduction_pct": poison_D_red,
            "pass": bool(g2_pass),
        },
        "G14_D_calibration_restored": {
            "spearman_D": float(rho_D) if not np.isnan(rho_D) else None,
            "pass": bool(g14_pass),
        },
        "G15_selection_beats_volume": {
            "learned_total_mae": learned_total,
            "matched_random_total_mae": matched_total,
            "reduction_pct": g15_red,
            "pass": bool(g15_pass),
        },
        "G16_D_selection_beats_volume": {
            "learned_D_mae": learn_D_mae,
            "matched_D_mae": matched_D_mae,
            "reduction_pct": g16_red,
            "pass": bool(g16_pass),
        },
        "G17_no_E_regression": {
            "spearman_E": float(rho_E) if not np.isnan(rho_E) else None,
            "pass": bool(g17_E_pass),
        },
        "G18_cross_dim_balance": {
            "worse_dim_mae": max(food_self_E_mae, food_world_E_mae,
                                   poison_self_D_mae, poison_world_D_mae),
            "better_dim_mae": min(food_self_E_mae, food_world_E_mae,
                                    poison_self_D_mae, poison_world_D_mae),
            "pass": bool(g18_pass),
        },
        "G19_top_bottom_enrichment": {
            "E_ratio": g19_E, "D_ratio": g19_D,
            "pass": bool(g19_pass),
        },
        "G20_no_saturation": {
            "null_rate": learned_null,
            "pass": bool(g20_pass),
        },
        "G21_reweighting_preserved": {
            "per_priority": g21_per_prio,
            "pass": bool(g21_pass),
        },
        "G22_relative_viability": {
            "learned_return": learned_ret,
            "scheduled_return": sched_ret,
            "pass": bool(g22_pass),
        },
        "G23_mechanism_gate": {
            "pass": bool(g23_pass),
        },
    }
    out_path = ROOT / "artifacts" / "scale_normalized_vprobe" / "verdicts_v1.json"
    out_path.write_text(json.dumps(verdicts, indent=2))
    print(f"\nverdicts:")
    print(json.dumps(verdicts, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
