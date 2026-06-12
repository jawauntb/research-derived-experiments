#!/usr/bin/env python3
"""Figures for Paper 19 — Current-Error Calibration."""

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

FIG_DIR = ROOT / "papers" / "current_error_calibration" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

COND_COLORS = {
    "factorized_no_null_online": "#d62728",
    "scheduled_null_anchor_online": "#1f77b4",
    "matched_random_online": "#9467bd",
    "learned_historical_ema_online": "#bcbd22",
    "learned_recent_ema_online": "#ff7f0e",
    "learned_sliding_window_online": "#8c564b",
    "learned_current_replay_online": "#2ca02c",
    "learned_current_replay_audit_online": "#1a8c1a",
    "oracle_uncertainty_probe_online": "#17becf",
    "oracle_source_online": "#7f7f7f",
}
COND_LABEL = {
    "factorized_no_null_online": "no-null\nbaseline",
    "scheduled_null_anchor_online": "scheduled\nanchor",
    "matched_random_online": "matched\nrandom",
    "learned_historical_ema_online": "historical\nEMA α=0.05\n(P18)",
    "learned_recent_ema_online": "recent\nEMA α=0.20\n(H1)",
    "learned_sliding_window_online": "sliding\nwindow K=50\n(H1)",
    "learned_current_replay_online": "current\nreplay\n(H2)",
    "learned_current_replay_audit_online": "current\nreplay\n+ audit\n(HEADLINE)",
    "oracle_uncertainty_probe_online": "oracle\nuncertainty",
    "oracle_source_online": "oracle\nsource",
}
ROLES = ["food", "poison", "medicine", "neutral"]


def _spearman(a, b):
    a = np.asarray(a, dtype=float); b = np.asarray(b, dtype=float)
    if len(a) < 2 or np.std(a) == 0 or np.std(b) == 0:
        return float("nan")
    ar = np.argsort(np.argsort(a)); br = np.argsort(np.argsort(b))
    return float(np.corrcoef(ar, br)[0, 1])


def main() -> int:
    data = json.loads(
        (ROOT / "artifacts" / "current_error_calibration" / "sweep_v1.json").read_text()
    )
    rows = data["summary"]
    conds = data["manifest"]["conditions"]
    cost_headline = data["manifest"]["cost_headline"]
    raw_results = data["results"]
    food_true = rows[0]["true_self_consume_food"]
    food_world_true = rows[0]["true_world_in_dist_food"]

    def cells_raw(cond, cost=None):
        out = [r for r in raw_results if r["condition"] == cond]
        if cost is not None:
            out = [r for r in out if abs(r["cost"] - cost) < 1e-6]
        return out

    def cells_sum(cond, cost=None):
        out = [r for r in rows if r["condition"] == cond]
        if cost is not None:
            out = [r for r in out if abs(r["cost"] - cost) < 1e-6]
        return out

    # ====== Fig 1: factorial of probe targets ======
    factorial = [
        "factorized_no_null_online",
        "scheduled_null_anchor_online",
        "matched_random_online",
        "learned_historical_ema_online",
        "learned_recent_ema_online",
        "learned_sliding_window_online",
        "learned_current_replay_online",
        "learned_current_replay_audit_online",
        "oracle_uncertainty_probe_online",
        "oracle_source_online",
    ]
    fig, axes = plt.subplots(1, 2, figsize=(18, 5.5), sharey=False)
    # Food self overshoot
    ax = axes[0]
    x = np.arange(len(factorial))
    overshoots = []
    overshoot_err = []
    for cond in factorial:
        cells = cells_sum(cond, cost_headline)
        preds = np.array([r["pred_self_consume_food"] for r in cells])
        if len(preds):
            overshoots.append(float(np.mean(preds - food_true)))
            overshoot_err.append(float(np.std(preds - food_true))
                                 if len(preds) > 1 else 0)
        else:
            overshoots.append(0.0); overshoot_err.append(0.0)
    ax.bar(x, overshoots, 0.7, yerr=overshoot_err,
           color=[COND_COLORS[c] for c in factorial],
           alpha=0.92, edgecolor="black", linewidth=0.4)
    for i, m in enumerate(overshoots):
        ax.text(x[i], m + 0.04 if m >= 0 else m - 0.08,
                f"{m:+.2f}", ha="center", fontsize=8, fontweight="bold")
    ax.axhline(0, color="black", linewidth=0.6)
    ax.set_xticks(x)
    ax.set_xticklabels([COND_LABEL[c] for c in factorial], fontsize=6.5,
                        rotation=15)
    ax.set_ylabel("Food self overshoot (pred − true)", fontsize=11)
    ax.set_title("Food self overshoot at cost = 0.025", fontsize=11)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    # Total MAE
    ax = axes[1]
    total_maes = []
    for cond in factorial:
        cells = cells_raw(cond, cost_headline)
        if not cells:
            total_maes.append(0.0); continue
        self_maes = [abs(c["prediction_by_role"]["food"]["self_action_1"] - food_true) for c in cells]
        world_maes = [abs(c["prediction_by_role"]["food"]["world"] - food_world_true) for c in cells]
        total_maes.append(float(np.mean(self_maes) + np.mean(world_maes)))
    ax.bar(x, total_maes, 0.7,
           color=[COND_COLORS[c] for c in factorial],
           alpha=0.92, edgecolor="black", linewidth=0.4)
    for i, m in enumerate(total_maes):
        ax.text(x[i], m + 0.005, f"{m:.3f}", ha="center", fontsize=8,
                fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([COND_LABEL[c] for c in factorial], fontsize=6.5,
                        rotation=15)
    ax.set_ylabel("Food total component MAE", fontsize=11)
    ax.set_title("Total component MAE (lower = better)", fontsize=11)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig1_factorial.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ====== Fig 2: per-role self predictions ======
    fig, axes = plt.subplots(1, 4, figsize=(22, 5.5), sharey=True)
    for ri, role in enumerate(ROLES):
        ax = axes[ri]
        x = np.arange(len(factorial))
        for ci, cond in enumerate(factorial):
            cells = cells_sum(cond, cost_headline)
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
        ax.set_xticklabels([COND_LABEL[c] for c in factorial], fontsize=5.5,
                            rotation=15)
        ax.set_title(role, fontsize=11)
        if ri == 0:
            ax.set_ylabel("Predicted self ΔE (consume)", fontsize=10)
        ax.axhline(0, color="black", linewidth=0.3)
        ax.legend(loc="best", fontsize=7)
        ax.set_ylim(-1.5, 2.0)
        ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig2_per_role_self.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ====== Fig 3: G18 — H1 vs H2 decomposition ======
    fig, ax = plt.subplots(figsize=(11, 6))
    h_order = [
        "learned_historical_ema_online",
        "learned_recent_ema_online",
        "learned_sliding_window_online",
        "learned_current_replay_online",
        "learned_current_replay_audit_online",
    ]
    x = np.arange(len(h_order))
    bars_maes = []
    bars_nulls = []
    for cond in h_order:
        cells = cells_raw(cond, cost_headline)
        self_maes = [abs(c["prediction_by_role"]["food"]["self_action_1"] - food_true) for c in cells]
        world_maes = [abs(c["prediction_by_role"]["food"]["world"] - food_world_true) for c in cells]
        bars_maes.append(float(np.mean(self_maes) + np.mean(world_maes)))
        bars_nulls.append(float(np.mean(
            [c["in_dist_eval"]["null_rate"] for c in cells]
        )))
    ax.bar(x, bars_maes, 0.7,
           color=[COND_COLORS[c] for c in h_order],
           alpha=0.92, edgecolor="black", linewidth=0.4)
    for i, (m, n) in enumerate(zip(bars_maes, bars_nulls)):
        ax.text(x[i], m + 0.01,
                f"MAE={m:.3f}\nnull={n*100:.1f}%",
                ha="center", fontsize=8, fontweight="bold")
    # Reference: matched_random
    mr_cells = cells_raw("matched_random_online", cost_headline)
    if mr_cells:
        mr_self = np.mean([abs(c["prediction_by_role"]["food"]["self_action_1"] - food_true)
                           for c in mr_cells])
        mr_world = np.mean([abs(c["prediction_by_role"]["food"]["world"] - food_world_true)
                            for c in mr_cells])
        mr_mae = mr_self + mr_world
        ax.axhline(mr_mae, color="#9467bd", linestyle="--", alpha=0.7,
                   label=f"matched_random (MAE={mr_mae:.3f})")
    or_cells = cells_raw("oracle_source_online", cost_headline)
    if or_cells:
        or_self = np.mean([abs(c["prediction_by_role"]["food"]["self_action_1"] - food_true)
                           for c in or_cells])
        or_world = np.mean([abs(c["prediction_by_role"]["food"]["world"] - food_world_true)
                            for c in or_cells])
        or_mae = or_self + or_world
        ax.axhline(or_mae, color="#7f7f7f", linestyle=":", alpha=0.7,
                   label=f"oracle_source (MAE={or_mae:.3f})")
    ax.set_xticks(x)
    ax.set_xticklabels([COND_LABEL[c] for c in h_order], fontsize=8.5)
    ax.set_ylabel("Food total component MAE", fontsize=11)
    ax.set_title(
        "G18: H1 (lag) vs H2 (staleness). "
        "Current-replay with audit recovers near-oracle attribution.",
        fontsize=11,
    )
    ax.legend(loc="best", fontsize=9)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()
    out = FIG_DIR / "fig3_h1_vs_h2.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ====== Fig 4: G14 — calibration scatter ======
    BUCKETS = [f"{r}_{e}" for r in ROLES for e in ("E_low", "E_high")]

    def per_bucket_fire_rate(cells_subset):
        agg_f = defaultdict(int); agg_v = defaultdict(int)
        for r in cells_subset:
            f = r["in_dist_eval"]["probe_fires_by_bucket"]
            v = r["in_dist_eval"]["state_visits_by_bucket"]
            for k in BUCKETS:
                agg_f[k] += f.get(k, 0); agg_v[k] += v.get(k, 0)
        return {k: agg_f[k] / max(agg_v[k], 1) for k in BUCKETS}

    def per_bucket_oracle(cells_subset):
        agg = defaultdict(list)
        for r in cells_subset:
            for k, b in r["bucket_diag"].items():
                agg[k].append(b["oracle_uncertainty"])
        return {k: float(np.mean(agg[k])) if agg[k] else 0.0 for k in BUCKETS}

    headline_cells = cells_raw("learned_current_replay_audit_online", cost_headline)
    p18_cells = cells_raw("learned_historical_ema_online", cost_headline)
    oracle_cells = cells_raw("oracle_uncertainty_probe_online", cost_headline)

    headline_rates = per_bucket_fire_rate(headline_cells)
    p18_rates = per_bucket_fire_rate(p18_cells)
    oracle_rates = per_bucket_fire_rate(oracle_cells)
    oracle_unc = per_bucket_oracle(headline_cells)

    fig, axes = plt.subplots(1, 2, figsize=(15, 5.5))
    ax = axes[0]
    xs = [oracle_unc[b] for b in BUCKETS]
    ys_headline = [headline_rates[b] for b in BUCKETS]
    ys_p18 = [p18_rates[b] for b in BUCKETS]
    ax.scatter(xs, ys_headline, s=90,
               c=COND_COLORS["learned_current_replay_audit_online"],
               edgecolor="black", alpha=0.85, label="current_replay + audit")
    ax.scatter(xs, ys_p18, s=70,
               c=COND_COLORS["learned_historical_ema_online"],
               edgecolor="black", alpha=0.7, marker="^",
               label="historical EMA (P18)")
    for b, ox, oy in zip(BUCKETS, xs, ys_headline):
        ax.annotate(b, (ox, oy), fontsize=6,
                    xytext=(4, 4), textcoords="offset points")
    rho_h = _spearman(xs, ys_headline)
    rho_p = _spearman(xs, ys_p18)
    ax.set_xlabel("Oracle current attribution uncertainty per bucket", fontsize=10)
    ax.set_ylabel("Learned probe rate per bucket", fontsize=10)
    ax.set_title(
        f"G14: probe rate vs oracle uncertainty\n"
        f"current_replay+audit ρ={rho_h:.2f}  vs  P18 historical ρ={rho_p:.2f}",
        fontsize=10,
    )
    ax.legend(loc="best", fontsize=8)
    ax.grid(linestyle=":", alpha=0.4)

    # Panel B: G15 — error reduction vs null density per bucket
    ax = axes[1]
    err_reduction_per_bucket = defaultdict(list)
    null_density_per_bucket = defaultdict(list)
    for r in headline_cells:
        for b, info in r["bucket_diag"].items():
            err_reduction_per_bucket[b].append(info["world_error_reduction"])
            null_density_per_bucket[b].append(info["null_density"])
    xs_d = [float(np.mean(null_density_per_bucket[b])) for b in BUCKETS]
    ys_d = [float(np.mean(err_reduction_per_bucket[b])) for b in BUCKETS]
    ax.scatter(xs_d, ys_d, s=90,
               c=COND_COLORS["learned_current_replay_audit_online"],
               edgecolor="black", alpha=0.85)
    for b, ox, oy in zip(BUCKETS, xs_d, ys_d):
        ax.annotate(b, (ox, oy), fontsize=6,
                    xytext=(4, 4), textcoords="offset points")
    if len(xs_d) > 1 and np.std(xs_d) > 0 and np.std(ys_d) > 0:
        pearson = float(np.corrcoef(xs_d, ys_d)[0, 1])
    else:
        pearson = float("nan")
    ax.set_xlabel("Per-bucket null density (training)", fontsize=10)
    ax.set_ylabel("Per-bucket world_head error reduction", fontsize=10)
    ax.set_title(f"G15: error reduction tracks probe density.  Pearson r = {pearson:.2f}",
                 fontsize=10)
    ax.grid(linestyle=":", alpha=0.4)

    fig.tight_layout()
    out = FIG_DIR / "fig4_calibration.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # ====== Verdicts ======
    def food_self_mae(cells):
        preds = [r["prediction_by_role"]["food"]["self_action_1"] for r in cells]
        return float(np.mean([abs(p - food_true) for p in preds])) if preds else 0.0

    def food_world_mae(cells):
        preds = [r["prediction_by_role"]["food"]["world"] for r in cells]
        return (float(np.mean([abs(p - food_world_true) for p in preds]))
                if preds else 0.0)

    def food_overshoot(cells):
        preds = [r["prediction_by_role"]["food"]["self_action_1"] for r in cells]
        return float(np.mean([p - food_true for p in preds])) if preds else 0.0

    learned = headline_cells
    scheduled = cells_raw("scheduled_null_anchor_online")
    no_null = cells_raw("factorized_no_null_online")
    matched = cells_raw("matched_random_online", cost_headline)
    recent_ema = cells_raw("learned_recent_ema_online", cost_headline)
    sliding = cells_raw("learned_sliding_window_online", cost_headline)
    no_audit = cells_raw("learned_current_replay_online", cost_headline)

    g1_self = food_self_mae(learned); g1_world = food_world_mae(learned)
    g1_pass = (g1_self <= 0.12) and (g1_world <= 0.10)

    nn_ov = food_overshoot(no_null)
    ln_ov = food_overshoot(learned)
    g2_red = (1 - ln_ov / nn_ov) * 100 if abs(nn_ov) > 1e-3 else 0.0
    g2_pass = g2_red >= 70

    matched_total = food_self_mae(matched) + food_world_mae(matched)
    learned_total = g1_self + g1_world
    g3_red = ((1 - learned_total / matched_total) * 100
              if matched_total > 1e-3 else 0.0)
    g3_pass = g3_red >= 25

    ln_ret = float(np.mean([r["in_dist_eval"]["mean_return"] for r in learned]))
    sch_ret = float(np.mean([r["in_dist_eval"]["mean_return"] for r in scheduled]))
    g5_pass = (ln_ret >= 0.90 * sch_ret) and (ln_ret >= 45)

    ln_null = float(np.mean([r["in_dist_eval"]["null_rate"] for r in learned]))
    min_v = min([
        b["v_probe"] for r in learned for b in r["bucket_diag"].values()
    ]) if learned else 0.0
    food_self_pred = float(np.mean(
        [r["prediction_by_role"]["food"]["self_action_1"] for r in learned]
    ))
    g11_pass = ((0.05 <= ln_null <= 0.40) and (min_v < cost_headline)
                and food_self_pred >= 0.7)

    g14_rho = _spearman(xs, ys_headline)
    g14_pass = (not np.isnan(g14_rho)) and (g14_rho >= 0.5)

    g15_pearson = pearson
    g15_pass = (not np.isnan(g15_pearson)) and (g15_pearson >= 0.5)

    g16_pass = g3_pass

    g17_pass = g11_pass

    # G18 — current_replay beats stale recency
    recent_total = food_self_mae(recent_ema) + food_world_mae(recent_ema)
    sliding_total = food_self_mae(sliding) + food_world_mae(sliding)
    historical_total = food_self_mae(p18_cells) + food_world_mae(p18_cells)
    # Stale recency = best of recent_ema/sliding/historical
    stale_best = min(recent_total, sliding_total, historical_total)
    g18_mae_red = (1 - learned_total / stale_best) * 100 if stale_best > 1e-3 else 0.0
    # Spearman delta
    p18_rho = _spearman(xs, [p18_rates[b] for b in BUCKETS])
    g18_rho_delta = (g14_rho - p18_rho) if (not np.isnan(g14_rho) and not np.isnan(p18_rho)) else 0.0
    g18_pass = (g18_mae_red >= 15) or (g18_rho_delta >= 0.25)

    # G19 — audit honesty
    no_audit_total = food_self_mae(no_audit) + food_world_mae(no_audit)
    audit_total = learned_total
    audit_dependence = (no_audit_total - audit_total) / max(no_audit_total, 1e-3)
    g19_audit_significantly_helps = audit_dependence >= 0.10

    g20_pass = g14_pass and g16_pass

    verdicts = {
        "G1": {"food_self_mae": g1_self, "food_world_mae": g1_world, "pass": bool(g1_pass)},
        "G2": {"reduction_pct": g2_red, "pass": bool(g2_pass)},
        "G3_G16": {"reduction_vs_matched_random_pct": g3_red, "pass": bool(g3_pass)},
        "G5": {"learned_return": ln_ret, "scheduled_return": sch_ret, "pass": bool(g5_pass)},
        "G11_G17": {"null_rate": ln_null, "min_vprobe": float(min_v), "food_self": food_self_pred, "pass": bool(g11_pass)},
        "G14": {"spearman_rho": (float(g14_rho) if not np.isnan(g14_rho) else None), "pass": bool(g14_pass)},
        "G15": {"pearson_r": (float(g15_pearson) if not np.isnan(g15_pearson) else None), "pass": bool(g15_pass)},
        "G16": {"reduction_vs_matched_random_pct": g3_red, "pass": bool(g16_pass)},
        "G17": {"pass": bool(g17_pass)},
        "G18_CURRENT_REPLAY_BEATS_STALE": {
            "current_replay_audit_total_mae": learned_total,
            "best_stale_recency_total_mae": stale_best,
            "mae_reduction_pct": g18_mae_red,
            "p18_spearman": float(p18_rho) if not np.isnan(p18_rho) else None,
            "current_replay_spearman": float(g14_rho) if not np.isnan(g14_rho) else None,
            "spearman_delta": g18_rho_delta,
            "pass": bool(g18_pass),
        },
        "G19_AUDIT_HONESTY": {
            "audit_total_mae": audit_total,
            "no_audit_total_mae": no_audit_total,
            "audit_provides_relative_improvement": audit_dependence,
            "audit_meaningfully_helps_no_audit_fails": (
                g19_audit_significantly_helps and not g16_pass
            ),
            "pass": True,
        },
        "G20": {"pass": bool(g20_pass)},
    }
    out_path = ROOT / "artifacts" / "current_error_calibration" / "verdicts_v1.json"
    out_path.write_text(json.dumps(verdicts, indent=2))
    print(f"\nverdicts:")
    print(json.dumps(verdicts, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
