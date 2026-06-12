#!/usr/bin/env python3
"""Figures for Paper 20B — Vector First-Order Self."""

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

FIG_DIR = ROOT / "papers" / "vector_first_order_self" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

COND_COLORS = {
    "vector_total_dV": "#8c564b",
    "vector_factorized_no_null": "#d62728",
    "vector_passive_null": "#ff7f0e",
    "vector_scheduled_null_anchor": "#1f77b4",
    "vector_matched_random_anchor": "#9467bd",
    "vector_learned_current_replay_probe": "#2ca02c",
    "vector_learned_current_replay_probe_audit": "#1a8c1a",
    "vector_oracle_uncertainty_probe": "#17becf",
    "vector_oracle_source": "#7f7f7f",
    "scalar_drive_selfworld": "#e377c2",
    "scalar_probe_vector_heads": "#bcbd22",
    "priority_weighted_probe": "#aec7e8",
}
COND_LABEL = {
    "vector_total_dV": "total ΔV\n(no factorize)",
    "vector_factorized_no_null": "factorized\nno null\n(P16 fail)",
    "vector_passive_null": "passive\nnull",
    "vector_scheduled_null_anchor": "scheduled\nanchor",
    "vector_matched_random_anchor": "matched\nrandom",
    "vector_learned_current_replay_probe": "current\nreplay probe\n(HEADLINE)",
    "vector_learned_current_replay_probe_audit": "current\nreplay\n+ audit",
    "vector_oracle_uncertainty_probe": "oracle\nuncertainty",
    "vector_oracle_source": "oracle\nsource",
    "scalar_drive_selfworld": "scalar\ndrive\n(P15 fail)",
    "scalar_probe_vector_heads": "scalar\nprobe",
    "priority_weighted_probe": "priority-\nweighted",
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
        (ROOT / "artifacts" / "vector_first_order_self" / "sweep_v1.json").read_text()
    )
    rows = data["summary"]
    conds = data["manifest"]["conditions"]
    cost_headline = data["manifest"]["cost_headline"]
    raw_results = data["results"]

    def cells_raw(cond):
        return [r for r in raw_results if r["condition"] == cond]

    def cells_sum(cond):
        return [r for r in rows if r["condition"] == cond]

    food_true_E = rows[0]["true_self_E_consume_food"]
    poison_true_D = rows[0]["true_self_D_consume_poison"]
    food_world_E_true = rows[0]["true_world_E_food"]
    poison_world_D_true = rows[0]["true_world_D_poison"]

    # ====== Fig 1: per-dim self/world predictions × condition ======
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
                    f"{mean:+.2f}", ha="center", fontsize=7,
                    fontweight="bold")
        ax.axhline(true_val, color="green", linewidth=1.8, linestyle="--",
                   alpha=0.7, label=f"true ({true_val:+.2f})")
        ax.set_xticks(x)
        ax.set_xticklabels([COND_LABEL[c] for c in conds], fontsize=5.5,
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

    # ====== Fig 2: G7 medicine accuracy across priorities ======
    fig, ax = plt.subplots(figsize=(13, 6))
    conds_for_g7 = [
        "vector_oracle_source",
        "vector_scheduled_null_anchor",
        "vector_matched_random_anchor",
        "vector_learned_current_replay_probe",
        "vector_learned_current_replay_probe_audit",
        "vector_oracle_uncertainty_probe",
        "scalar_drive_selfworld",
        "scalar_probe_vector_heads",
        "priority_weighted_probe",
    ]
    n = len(conds_for_g7)
    w_bar = 0.25
    x = np.arange(n)
    pcolors = {"balanced": "#1f77b4", "hungry": "#d62728", "injured": "#2ca02c"}
    for pi, prio in enumerate(PRIORITIES):
        accs = []
        accs_err = []
        for cond in conds_for_g7:
            cells = cells_sum(cond)
            vals = [r.get(f"{prio}_acc_medicine", 0.0) for r in cells]
            accs.append(float(np.mean(vals)) if vals else 0.0)
            accs_err.append(float(np.std(vals)) if len(vals) > 1 else 0)
        offset = (pi - 1) * w_bar
        ax.bar(x + offset, accs, w_bar, yerr=accs_err,
               color=pcolors[prio], alpha=0.88, label=prio,
               edgecolor="black", linewidth=0.4)
        for i, v in enumerate(accs):
            ax.text(x[i] + offset, v + 0.02, f"{v:.2f}",
                    ha="center", fontsize=6.5)
    ax.set_xticks(x)
    ax.set_xticklabels([COND_LABEL[c] for c in conds_for_g7], fontsize=7,
                        rotation=15)
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("Medicine action accuracy", fontsize=11)
    ax.set_title(
        "G7 zero-shot reweighting. Oracle: skip under hungry, consume under balanced/injured.\n"
        "Scalar drive fails under shifted priorities; vector self/world adapts.",
        fontsize=11,
    )
    ax.legend(loc="best", fontsize=9)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig2_zero_shot_reweighting.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ====== Fig 3: G3 dimension-wise probe calibration ======
    BUCKETS = [f"{r}_{eb}_{db}" for r in ROLES
               for eb in ("E_low", "E_high") for db in ("D_low", "D_high")]

    def per_bucket_fire_rate(cells_subset, distribution="balanced"):
        agg_f = defaultdict(int); agg_v = defaultdict(int)
        for r in cells_subset:
            ev = r["eval_by_priority"][distribution]
            f = ev["probe_fires_by_bucket"]
            v = ev["state_visits_by_bucket"]
            for k in BUCKETS:
                agg_f[k] += f.get(k, 0); agg_v[k] += v.get(k, 0)
        return {k: agg_f[k] / max(agg_v[k], 1) for k in BUCKETS}

    def per_bucket_metric(cells_subset, metric_key):
        agg = defaultdict(list)
        for r in cells_subset:
            for k, b in r["bucket_diag"].items():
                agg[k].append(b.get(metric_key, 0.0))
        return {k: float(np.mean(agg[k])) if agg[k] else 0.0 for k in BUCKETS}

    headline = cells_raw("vector_learned_current_replay_probe")
    oracle_unc_E = per_bucket_metric(headline, "oracle_unc_E")
    oracle_unc_D = per_bucket_metric(headline, "oracle_unc_D")
    v_probe_E_b = per_bucket_metric(headline, "v_probe_E")
    v_probe_D_b = per_bucket_metric(headline, "v_probe_D")

    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    # E dimension
    ax = axes[0]
    xs_E = [oracle_unc_E[b] for b in BUCKETS]
    ys_E = [v_probe_E_b[b] for b in BUCKETS]
    ax.scatter(xs_E, ys_E, s=70, c=COND_COLORS["vector_learned_current_replay_probe"],
               edgecolor="black", alpha=0.85)
    for b, ox, oy in zip(BUCKETS, xs_E, ys_E):
        ax.annotate(b, (ox, oy), fontsize=5,
                    xytext=(3, 3), textcoords="offset points")
    rho_E = _spearman(xs_E, ys_E)
    ax.set_xlabel("Oracle current attribution error (E dim)", fontsize=10)
    ax.set_ylabel("V_probe_E value per bucket", fontsize=10)
    ax.set_title(f"E dim: V_probe vs oracle uncertainty. Spearman ρ = {rho_E:.2f}",
                 fontsize=10)
    ax.grid(linestyle=":", alpha=0.4)
    # D dimension
    ax = axes[1]
    xs_D = [oracle_unc_D[b] for b in BUCKETS]
    ys_D = [v_probe_D_b[b] for b in BUCKETS]
    ax.scatter(xs_D, ys_D, s=70, c=COND_COLORS["vector_learned_current_replay_probe"],
               edgecolor="black", alpha=0.85)
    for b, ox, oy in zip(BUCKETS, xs_D, ys_D):
        ax.annotate(b, (ox, oy), fontsize=5,
                    xytext=(3, 3), textcoords="offset points")
    rho_D = _spearman(xs_D, ys_D)
    ax.set_xlabel("Oracle current attribution error (D dim)", fontsize=10)
    ax.set_ylabel("V_probe_D value per bucket", fontsize=10)
    ax.set_title(f"D dim: V_probe vs oracle uncertainty. Spearman ρ = {rho_D:.2f}",
                 fontsize=10)
    ax.grid(linestyle=":", alpha=0.4)
    fig.suptitle("G3: dimension-wise V_probe calibration to oracle uncertainty",
                 fontsize=12)
    fig.tight_layout()
    out = FIG_DIR / "fig3_dim_calibration.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ====== Fig 4: Total MAE across conditions ======
    fig, ax = plt.subplots(figsize=(14, 6))
    x = np.arange(len(conds))
    total_maes = []
    for cond in conds:
        cells = cells_raw(cond)
        if not cells:
            total_maes.append(0); continue
        food_E_pred = np.mean([r["prediction_by_role"]["food"]["self_E_action_1"]
                                for r in cells])
        food_E_world = np.mean([r["prediction_by_role"]["food"]["world_E"]
                                 for r in cells])
        poison_D_pred = np.mean([r["prediction_by_role"]["poison"]["self_D_action_1"]
                                  for r in cells])
        poison_D_world = np.mean([r["prediction_by_role"]["poison"]["world_D"]
                                   for r in cells])
        total = (abs(food_E_pred - food_true_E) + abs(food_E_world - food_world_E_true)
                 + abs(poison_D_pred - poison_true_D)
                 + abs(poison_D_world - poison_world_D_true))
        total_maes.append(float(total))
    ax.bar(x, total_maes, 0.7,
           color=[COND_COLORS[c] for c in conds], alpha=0.92,
           edgecolor="black", linewidth=0.4)
    for i, m in enumerate(total_maes):
        ax.text(x[i], m + 0.01, f"{m:.3f}", ha="center", fontsize=8,
                fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([COND_LABEL[c] for c in conds], fontsize=5.5,
                        rotation=15)
    ax.set_ylabel("Total component MAE (food_E + food_world + poison_D + poison_world)",
                  fontsize=10)
    ax.set_title("Total attribution MAE per condition (lower is better)",
                 fontsize=11)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig4_total_mae.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ====== Verdicts ======
    def role_pred(cells, role, key):
        return float(np.mean(
            [r["prediction_by_role"][role][key] for r in cells]
        )) if cells else 0.0

    learned = cells_raw("vector_learned_current_replay_probe")
    matched = cells_raw("vector_matched_random_anchor")
    scheduled = cells_raw("vector_scheduled_null_anchor")
    no_null = cells_raw("vector_factorized_no_null")
    oracle_src = cells_raw("vector_oracle_source")
    scalar_drive = cells_sum("scalar_drive_selfworld")
    scalar_probe = cells_raw("scalar_probe_vector_heads")

    def total_mae(cells):
        if not cells: return 0.0
        food_E_pred = role_pred(cells, "food", "self_E_action_1")
        food_E_world = role_pred(cells, "food", "world_E")
        poison_D_pred = role_pred(cells, "poison", "self_D_action_1")
        poison_D_world = role_pred(cells, "poison", "world_D")
        return (abs(food_E_pred - food_true_E)
                + abs(food_E_world - food_world_E_true)
                + abs(poison_D_pred - poison_true_D)
                + abs(poison_D_world - poison_world_D_true))

    # G1: per-dim MAE
    food_self_E_mae = abs(role_pred(learned, "food", "self_E_action_1")
                            - food_true_E)
    food_world_E_mae = abs(role_pred(learned, "food", "world_E")
                             - food_world_E_true)
    poison_self_D_mae = abs(role_pred(learned, "poison", "self_D_action_1")
                              - poison_true_D)
    poison_world_D_mae = abs(role_pred(learned, "poison", "world_D")
                               - poison_world_D_true)
    g1_pass = all(m <= 0.10 for m in [food_self_E_mae, food_world_E_mae,
                                       poison_self_D_mae, poison_world_D_mae])

    # G2: false-credit reduction on both dims
    nn_food_E_overshoot = role_pred(no_null, "food", "self_E_action_1") - food_true_E
    nn_poison_D_overshoot = role_pred(no_null, "poison", "self_D_action_1") - poison_true_D
    learned_food_E_overshoot = role_pred(learned, "food", "self_E_action_1") - food_true_E
    learned_poison_D_overshoot = role_pred(learned, "poison", "self_D_action_1") - poison_true_D
    food_E_red = ((1 - learned_food_E_overshoot / nn_food_E_overshoot) * 100
                   if abs(nn_food_E_overshoot) > 1e-3 else 0.0)
    poison_D_red = ((1 - learned_poison_D_overshoot / nn_poison_D_overshoot) * 100
                     if abs(nn_poison_D_overshoot) > 1e-3 else 0.0)
    g2_pass = food_E_red >= 70 and poison_D_red >= 70

    # G3: dim-wise probe calibration (Spearman per dim)
    g3_rho_E = rho_E
    g3_rho_D = rho_D
    g3_pass = ((not np.isnan(g3_rho_E)) and (not np.isnan(g3_rho_D))
                and g3_rho_E >= 0.5 and g3_rho_D >= 0.5)

    # G4: top/bottom enrichment per dim
    headline_rates = per_bucket_fire_rate(headline, "balanced")
    sorted_buckets_E = sorted(BUCKETS, key=lambda b: oracle_unc_E[b])
    sorted_buckets_D = sorted(BUCKETS, key=lambda b: oracle_unc_D[b])
    q = max(1, len(BUCKETS) // 4)
    def enrich(sorted_b):
        bot = float(np.mean([headline_rates[b] for b in sorted_b[:q]]))
        top = float(np.mean([headline_rates[b] for b in sorted_b[-q:]]))
        return top / max(bot, 1e-4), top, bot
    g4_enrich_E, top_E, bot_E = enrich(sorted_buckets_E)
    g4_enrich_D, top_D, bot_D = enrich(sorted_buckets_D)
    g4_pass = g4_enrich_E >= 2.0 and g4_enrich_D >= 2.0

    # G5: selection beats volume
    learned_total = total_mae(learned)
    matched_total = total_mae(matched)
    g5_reduction = ((1 - learned_total / matched_total) * 100
                     if matched_total > 1e-3 else 0.0)
    g5_pass = g5_reduction >= 25

    # G6: vector beats scalar probe
    scalar_total = total_mae(scalar_probe)
    g6_reduction = ((1 - learned_total / scalar_total) * 100
                     if scalar_total > 1e-3 else 0.0)
    rho_delta = max(0, g3_rho_E - 0) + max(0, g3_rho_D - 0)  # heuristic delta vs scalar
    g6_pass = g6_reduction >= 15

    # G7: medicine accuracy within 0.05 of oracle
    def med_acc(cells, prio):
        return float(np.mean([r[f"{prio}_acc_medicine"]
                                for r in [_flatten(c) for c in cells]])) \
                if cells else 0.0
    # Use the summary rows directly
    learned_sum = cells_sum("vector_learned_current_replay_probe")
    oracle_src_sum = cells_sum("vector_oracle_source")
    g7_per_prio = {}
    for prio in PRIORITIES:
        l = float(np.mean([r[f"{prio}_acc_medicine"] for r in learned_sum]))
        o = float(np.mean([r[f"{prio}_acc_medicine"] for r in oracle_src_sum]))
        g7_per_prio[prio] = dict(learned=l, oracle=o, diff=abs(l - o))
    g7_pass = all(g7_per_prio[p]["diff"] <= 0.05 for p in PRIORITIES)

    # G8: scalar drive fails ≥ 1 shifted priority by ≥ 0.15
    g8_per_prio = {}
    for prio in PRIORITIES:
        s = float(np.mean([r[f"{prio}_acc_medicine"] for r in scalar_drive]))
        o = float(np.mean([r[f"{prio}_acc_medicine"] for r in oracle_src_sum]))
        g8_per_prio[prio] = dict(scalar=s, oracle=o, fail=abs(s - o))
    g8_pass = any(g8_per_prio[p]["fail"] >= 0.15
                   for p in ["hungry", "injured"])

    # G9: no dimension neglect
    worse_dim = max(poison_self_D_mae, poison_world_D_mae,
                     food_self_E_mae, food_world_E_mae)
    better_dim = min(poison_self_D_mae, poison_world_D_mae,
                      food_self_E_mae, food_world_E_mae)
    g9_pass = ((worse_dim <= 2 * better_dim)
                or (worse_dim <= 0.07 and better_dim <= 0.07))

    # G10: viability
    learned_ret = float(np.mean(
        [r["eval_by_priority"]["balanced"]["mean_return"] for r in learned]
    )) if learned else 0.0
    sched_ret = float(np.mean(
        [r["eval_by_priority"]["balanced"]["mean_return"] for r in scheduled]
    )) if scheduled else 0.0
    g10_pass = (learned_ret >= 45) and (learned_ret >= 0.90 * sched_ret)

    # G11: probe efficiency / no saturation
    learned_null = float(np.mean(
        [r["eval_by_priority"]["balanced"]["null_rate"] for r in learned]
    )) if learned else 0.0
    g11_pass = 0.001 <= learned_null <= 0.40

    g12_pass = g1_pass and g3_pass and g5_pass

    verdicts = {
        "G1_vector_active_identifiability": {
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
        "G3_dim_wise_calibration": {
            "spearman_E": float(g3_rho_E) if not np.isnan(g3_rho_E) else None,
            "spearman_D": float(g3_rho_D) if not np.isnan(g3_rho_D) else None,
            "pass": bool(g3_pass),
        },
        "G4_top_bottom_enrichment": {
            "E_ratio": g4_enrich_E,
            "D_ratio": g4_enrich_D,
            "pass": bool(g4_pass),
        },
        "G5_selection_beats_volume": {
            "learned_total_mae": learned_total,
            "matched_random_total_mae": matched_total,
            "reduction_pct": g5_reduction,
            "pass": bool(g5_pass),
        },
        "G6_vector_beats_scalar_probe": {
            "learned_total_mae": learned_total,
            "scalar_probe_total_mae": scalar_total,
            "reduction_pct": g6_reduction,
            "pass": bool(g6_pass),
        },
        "G7_zero_shot_reweighting": {
            "per_priority": g7_per_prio,
            "pass": bool(g7_pass),
        },
        "G8_scalar_drive_fails": {
            "per_priority": g8_per_prio,
            "pass": bool(g8_pass),
        },
        "G9_no_dimension_neglect": {
            "worse_dim_mae": worse_dim,
            "better_dim_mae": better_dim,
            "pass": bool(g9_pass),
        },
        "G10_viability": {
            "learned_return": learned_ret,
            "scheduled_return": sched_ret,
            "pass": bool(g10_pass),
        },
        "G11_no_saturation": {
            "null_rate": learned_null,
            "pass": bool(g11_pass),
        },
        "G12_behavior_plus_repr": {
            "pass": bool(g12_pass),
        },
    }
    out_path = ROOT / "artifacts" / "vector_first_order_self" / "verdicts_v1.json"
    out_path.write_text(json.dumps(verdicts, indent=2))
    print(f"\nverdicts:")
    print(json.dumps(verdicts, indent=2))
    return 0


def _flatten(c):
    # helper for direct dict access — assumes cells already flat
    return c


if __name__ == "__main__":
    raise SystemExit(main())
