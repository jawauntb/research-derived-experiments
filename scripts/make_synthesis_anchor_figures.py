#!/usr/bin/env python3
"""Per-anchor-experiment figures for the synthesis paper.

These supplement the 7 synthesis-overview figures with detailed
per-experiment results so the synthesis is self-contained.
"""

from __future__ import annotations

import json
from pathlib import Path
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
FIG_DIR = ROOT / "papers" / "metric_stack_synthesis" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.size": 10.5,
    "axes.titlesize": 11.5,
    "axes.labelsize": 11,
    "xtick.labelsize": 9.5,
    "ytick.labelsize": 9.5,
    "legend.fontsize": 9.5,
    "axes.spines.top": False,
    "axes.spines.right": False,
})


def safe_load(path):
    try:
        return json.loads(Path(path).read_text())
    except Exception as e:
        print(f"  could not load {path}: {e}")
        return None


def fig_a1_p16b_null_intervention():
    """P16b: food self overshoot across 5 conditions."""
    d = safe_load(ROOT / "artifacts/null_intervention/sweep_v1.json")
    if not d:
        return
    rows = d["summary"]
    conds = ["total_dV_head", "factorized_no_null", "factorized_null_passive",
             "factorized_null_anchor", "oracle_source"]
    labels = ["total ΔV\n(no factorize)", "factorized\nno null\n(P16 fail)",
              "passive\nnull", "null anchor\n(HEADLINE)", "oracle\nsource"]
    food_true = rows[0]["true_self_consume_food"]
    means, stds = [], []
    for c in conds:
        cells = [r for r in rows if r["condition"] == c]
        preds = [r["pred_self_consume_food"] - food_true for r in cells]
        means.append(float(np.mean(preds)) if preds else 0)
        stds.append(float(np.std(preds)) if len(preds) > 1 else 0)
    fig, ax = plt.subplots(figsize=(11, 5.5))
    x = np.arange(len(conds))
    colors = ["#888", "#d62728", "#ff7f0e", "#2ca02c", "#444"]
    ax.bar(x, means, 0.6, yerr=stds, color=colors, alpha=0.88,
           edgecolor="black", linewidth=0.5)
    for i, m in enumerate(means):
        ax.text(i, m + 0.04 if m >= 0 else m - 0.08,
                f"{m:+.2f}", ha="center", fontsize=10, fontweight="bold")
    ax.axhline(0, color="green", linestyle="--", linewidth=1.5, alpha=0.7,
               label="true food self_consume (no overshoot)")
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel("Food self_consume overshoot (pred − true)", fontsize=11)
    ax.set_title("Figure A1 (Paper 16b). Active null-anchored intervention "
                 "breaks the gauge symmetry that defeats architectural self/world factorization.\n"
                 "Takeaway: passive null fails WORSE than no-null; null anchor (green) recovers "
                 "true self attribution (82% false-credit reduction).",
                 fontsize=11)
    ax.legend(loc="upper right", fontsize=9.5)
    ax.grid(axis="y", linestyle=":", alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_a1_p16b_null_intervention.png",
                dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {FIG_DIR}/fig_a1_p16b_null_intervention.png")


def fig_a2_p17a_v_probe_saturation():
    """P17A: saturation failure — V_probe outputs above all cost thresholds."""
    d = safe_load(ROOT / "artifacts/costly_null_probes/sweep_v1.json")
    if not d:
        return
    rows = d["summary"]
    conds = ["learned_costly_null_probe", "matched_random_null_anchor",
             "scheduled_null_anchor", "oracle_uncertainty_probe", "oracle_source"]
    labels = ["learned\nprobe\n(HEADLINE)", "matched\nrandom", "scheduled\nanchor",
              "oracle\nuncertainty", "oracle\nsource"]
    # Use null rate as the saturation signature
    headline = 0.025
    rate_means, rate_stds = [], []
    for c in conds:
        cells = [r for r in rows if r["condition"] == c
                  and abs(r["cost"] - headline) < 1e-6]
        nrs = [r.get("in_dist_null_rate", 0) * 100 for r in cells]
        rate_means.append(float(np.mean(nrs)) if nrs else 0)
        rate_stds.append(float(np.std(nrs)) if len(nrs) > 1 else 0)
    fig, ax = plt.subplots(figsize=(11, 5.5))
    x = np.arange(len(conds))
    colors = ["#d62728", "#9467bd", "#1f77b4", "#17becf", "#444"]
    ax.bar(x, rate_means, 0.6, yerr=rate_stds, color=colors, alpha=0.88,
           edgecolor="black", linewidth=0.5)
    for i, m in enumerate(rate_means):
        ax.text(i, m + 2, f"{m:.0f}%", ha="center", fontsize=10, fontweight="bold")
    ax.axhline(20, color="green", linestyle="--", linewidth=1.5, alpha=0.7,
               label="G4 target: ≤20% null rate")
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel("Eval-time null rate (%)", fontsize=11)
    ax.set_ylim(0, 115)
    ax.set_title("Figure A2 (Paper 17A). V_probe saturation: per-sample residual targets "
                 "exceed every cost threshold so the probe fires 100% always.\n"
                 "Takeaway: residual scale ≠ systematic error. Per-sample magnitudes are "
                 "dominated by Bernoulli shock noise.",
                 fontsize=11)
    ax.legend(loc="lower right", fontsize=9.5)
    ax.grid(axis="y", linestyle=":", alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_a2_p17a_v_probe_saturation.png",
                dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {FIG_DIR}/fig_a2_p17a_v_probe_saturation.png")


def fig_a3_p19_current_replay():
    """P19: H1 vs H2 vs H3 decomposition — current_replay closes the gap."""
    d = safe_load(ROOT / "artifacts/current_error_calibration/sweep_v1.json")
    if not d:
        return
    rows = d["summary"]
    conds = ["learned_historical_ema_online", "learned_recent_ema_online",
             "learned_sliding_window_online", "learned_current_replay_audit_online",
             "matched_random_time_budget", "oracle_source_online"]
    labels = ["historical\nEMA\n(P18 baseline)", "recent\nEMA\n(H1)",
              "sliding\nwindow\n(H1)", "current\nreplay\n(H2, HEADLINE)",
              "matched\nrandom", "oracle\nsource"]
    food_true = rows[0]["true_self_consume_food"]
    means, stds = [], []
    for c in conds:
        cells = [r for r in rows if r["condition"] == c]
        preds = [r["pred_self_consume_food"] for r in cells]
        means.append(float(np.mean(preds)) if preds else 0)
        stds.append(float(np.std(preds)) if len(preds) > 1 else 0)
    fig, ax = plt.subplots(figsize=(12, 5.5))
    x = np.arange(len(conds))
    colors = ["#bcbd22", "#ff7f0e", "#8c564b", "#2ca02c", "#9467bd", "#444"]
    ax.bar(x, means, 0.65, yerr=stds, color=colors, alpha=0.88,
           edgecolor="black", linewidth=0.5)
    for i, m in enumerate(means):
        ax.text(i, m + 0.04, f"{m:+.2f}", ha="center", fontsize=10, fontweight="bold")
    ax.axhline(food_true, color="green", linestyle="--", linewidth=1.5, alpha=0.7,
               label=f"true food self ({food_true:+.2f})")
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=9.5)
    ax.set_ylabel("Predicted food self_consume", fontsize=11)
    ax.set_ylim(-0.3, 1.3)
    ax.set_title("Figure A3 (Paper 19). Three hypotheses decomposed: lag vs staleness vs structural.\n"
                 "Takeaway: H1 (recency alone) makes attribution WORSE (negative values); H2 (current_replay) "
                 "is decisive — recomputing residuals against the CURRENT model closes the calibration gap (78% MAE reduction vs best stale variant).",
                 fontsize=10.5)
    ax.legend(loc="lower right", fontsize=9.5)
    ax.grid(axis="y", linestyle=":", alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_a3_p19_current_replay.png",
                dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {FIG_DIR}/fig_a3_p19_current_replay.png")


def fig_a4_p22_world_responds():
    """P22: learning-curve MAE under action-correlated env."""
    d = safe_load(ROOT / "artifacts/world_responds/sweep_v1.json")
    if not d:
        return
    rows = d["summary"]
    conds = ["p21a_independent_baseline", "two_head_actionblind_world",
             "two_head_history_world", "three_head_direct_mediated_exogenous",
             "learned_scale_norm_current_replay", "matched_random_time_budget",
             "oracle_probe_value", "oracle_source"]
    labels = ["P21A\nbaseline", "2-head\naction-blind", "2-head\nhistory",
              "3-head\n(architectural\nwin)", "learned\nscale-norm\n(HEADLINE)",
              "matched\nrandom", "oracle probe\n(current err)\n(BROKEN)", "oracle\nsource"]
    means, stds = [], []
    for c in conds:
        cells = [r for r in rows if r["condition"] == c]
        vals = [r.get("final_lc_mae", 0) for r in cells]
        means.append(float(np.mean(vals)) if vals else 0)
        stds.append(float(np.std(vals)) if len(vals) > 1 else 0)
    fig, ax = plt.subplots(figsize=(13, 5.5))
    x = np.arange(len(conds))
    colors = ["#888", "#d62728", "#ff7f0e", "#1f77b4", "#2ca02c", "#9467bd",
              "#17becf", "#444"]
    ax.bar(x, means, 0.65, yerr=stds, color=colors, alpha=0.88,
           edgecolor="black", linewidth=0.5)
    for i, m in enumerate(means):
        ax.text(i, m + 0.015, f"{m:.3f}", ha="center", fontsize=9.5, fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=8.5)
    ax.set_ylabel("Final learning-curve MAE (food_E + poison_D)", fontsize=11)
    ax.set_title("Figure A4 (Paper 22). When the world responds to the agent: three-head is the right architecture.\n"
                 "Takeaway: oracle_probe_value using CURRENT ERROR is 5× worse than learned probing — current "
                 "error ≠ value of probing. Three-head decomposition matches the headline.",
                 fontsize=10.5)
    ax.grid(axis="y", linestyle=":", alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_a4_p22_world_responds.png",
                dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {FIG_DIR}/fig_a4_p22_world_responds.png")


def fig_a5_p24_contrast_anti_cheats():
    """P24: contrast loss + anti-cheat result."""
    d = safe_load(ROOT / "artifacts/interventional_contrast/sweep_v1.json")
    if not d:
        return
    rows = d["summary"]
    conds = ["p23b_default_no_contrast_oracle_buckets",
             "contrast_loss_learned_pairs_oracle",
             "matched_random_contrast_pairs",
             "shuffled_contrast_pairs",
             "wrong_history_contrast",
             "learned_buckets_with_contrast",
             "oracle_source"]
    labels = ["P23B baseline\nno contrast", "contrast\nlearned\n(HEADLINE)",
              "matched\nrandom\npairs",
              "shuffled\n(G6 ✓\nanti-cheat\nworks)",
              "wrong-history\n(G7 ✗\nstill helps)",
              "learned\nbuckets\n+ contrast", "oracle\nsource"]
    # Use mediated_E contrast for food
    means, stds = [], []
    for c in conds:
        cells = [r for r in rows if r["condition"] == c]
        vals = [r.get("pred_mediated_E_contrast_food", 0) for r in cells]
        means.append(float(np.mean(vals)) if vals else 0)
        stds.append(float(np.std(vals)) if len(vals) > 1 else 0)
    fig, ax = plt.subplots(figsize=(13, 5.5))
    x = np.arange(len(conds))
    colors = ["#888", "#2ca02c", "#9467bd", "#1f77b4", "#d62728",
              "#1a8c1a", "#444"]
    ax.bar(x, means, 0.65, yerr=stds, color=colors, alpha=0.88,
           edgecolor="black", linewidth=0.5)
    for i, m in enumerate(means):
        ax.text(i, m + 0.005, f"{m:.3f}", ha="center", fontsize=9.5, fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=8.5)
    ax.set_ylabel("Predicted mediated_E contrast (food bucket)", fontsize=11)
    ax.set_title("Figure A5 (Paper 24). Interventional contrast loss + anti-cheat controls.\n"
                 "Takeaway: contrast helps; shuffled (G6) FAILS as designed (semantic correctness matters); "
                 "wrong-history (G7) STILL HELPS — reveals environment under-constraint (mediated structure is role-invariant).",
                 fontsize=10.5)
    ax.grid(axis="y", linestyle=":", alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_a5_p24_contrast_anti_cheats.png",
                dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {FIG_DIR}/fig_a5_p24_contrast_anti_cheats.png")


def fig_a6_p23b_re_engagement_dynamics():
    """P23B: per-phase null density showing re-engagement after second shift."""
    d = safe_load(ROOT / "artifacts/habituated_reengagement/sweep_v1.json")
    if not d:
        return
    raw = d["results"]
    BUCKETS_AFFECTED = [b for b in
                         [f"{r}_{eb}_{db}" for r in ["food", "poison", "medicine", "neutral"]
                          for eb in ("E_low", "E_high") for db in ("D_low", "D_high")]
                         if b.startswith(("food_", "medicine_"))]
    conds_show = [
        ("p22_learned_current_replay", "P22 baseline\n(self-silencing)", "#888"),
        ("p23a_surprise_no_cooling", "P23A surprise\n(ANXIETY)", "#d62728"),
        ("leaky_effort_integrator", "P23B HEADLINE\n(decision cool)", "#2ca02c"),
        ("decision_refractory", "decision\nrefractory", "#2ca02c"),
        ("burst_then_refractory", "burst+\nrefractory", "#2ca02c"),
        ("oracle_source", "oracle source", "#444"),
    ]
    pre_s1 = []; post_s1 = []; pre_s2 = []; post_s2 = []
    for cond, lab, col in conds_show:
        cells = [r for r in raw if r["condition"] == cond]
        if not cells:
            pre_s1.append(0); post_s1.append(0); pre_s2.append(0); post_s2.append(0); continue
        pre1 = float(np.mean([sum(r["bucket_null_pre_shift1"].get(b, 0)
                                   for b in BUCKETS_AFFECTED) for r in cells]))
        post1 = float(np.mean([sum(r["bucket_null_post_shift1_early"].get(b, 0)
                                    + r["bucket_null_post_shift1_late"].get(b, 0)
                                    for b in BUCKETS_AFFECTED) for r in cells]))
        pre2 = float(np.mean([sum(r["bucket_null_pre_shift2"].get(b, 0)
                                   for b in BUCKETS_AFFECTED) for r in cells]))
        post2 = float(np.mean([sum(r["bucket_null_post_shift2"].get(b, 0)
                                    for b in BUCKETS_AFFECTED) for r in cells]))
        pre_s1.append(pre1); post_s1.append(post1); pre_s2.append(pre2); post_s2.append(post2)
    fig, ax = plt.subplots(figsize=(13, 5.5))
    x = np.arange(len(conds_show))
    w_bar = 0.20
    ax.bar(x - 1.5*w_bar, pre_s1, w_bar, label="pre-shift1 (eps 0-249)",
            color="#cce0ff", edgecolor="black", linewidth=0.4)
    ax.bar(x - 0.5*w_bar, post_s1, w_bar, label="post-shift1 (eps 250-399)",
            color="#1f77b4", edgecolor="black", linewidth=0.4)
    ax.bar(x + 0.5*w_bar, pre_s2, w_bar, label="pre-shift2 (eps 350-399)",
            color="#ffd9b3", edgecolor="black", linewidth=0.4)
    ax.bar(x + 1.5*w_bar, post_s2, w_bar, label="post-shift2 (eps 400-500)",
            color="#d62728", edgecolor="black", linewidth=0.4)
    ax.set_xticks(x); ax.set_xticklabels([c[1] for c in conds_show], fontsize=9.5)
    ax.set_ylabel("Mean affected-bucket null count (food + medicine)", fontsize=11)
    ax.set_title("Figure A6 (Paper 23B). Re-engagement after the SECOND regime shift — "
                 "the maintained-boundary signature.\n"
                 "Takeaway: P22 baseline self-silences post-shift (red bars ≈ 0); P23A surprise has anxiety "
                 "(post-shift WAY higher than pre); decision-layer cooling re-engages on shift 2 (red bars rise above pre-shift-2 baseline) WITHOUT permanent anxiety.",
                 fontsize=10.5)
    ax.legend(loc="upper left", fontsize=9.5, ncol=2)
    ax.grid(axis="y", linestyle=":", alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_a6_p23b_re_engagement_dynamics.png",
                dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {FIG_DIR}/fig_a6_p23b_re_engagement_dynamics.png")


def fig_a7_alternative_explanations():
    """Table-as-figure: alternative explanations for each main claim."""
    rows = [
        ("Maintained-boundary cycle",
         "Just threshold dynamics; no real epistemic loop",
         "G6 'no false calm' gate + G10 re-openability after 2nd shift"),
        ("Learned bucket abstraction",
         "k-means trivially recovers role labels",
         "Test on richer obs; current claim is 'preserves mechanism', not 'recovers semantics'"),
        ("Mediated/exogenous decomposition",
         "Total world prediction correct; component split arbitrary",
         "P25 architectural ceiling acknowledges this limit explicitly"),
        ("Probe selectivity beats random",
         "Volume alone would suffice given enough nulls",
         "matched-random-time + matched-random-bucket-balanced controls; in some seeds RANDOM ≈ LEARNED"),
        ("Calibrated uncertainty signal",
         "Variance / residual / EMA / current error",
         "P14b, P17A, P18, P22 falsify these one by one; current_replay (P19) is the right form for SCALAR case"),
        ("Vector ΔV reweighting",
         "Scalar drive with priorities learned at train time",
         "P15 scalar_drive baseline catastrophically fails hungry priority"),
        ("Self/world identifiability",
         "Architectural factorization alone",
         "P16 shows architecture alone is gauge-symmetric; P16b active null intervention required"),
        ("Philosophical relevance",
         "Post-hoc story imposed on numerical results",
         "Mapped only as correlates, not proof; not claiming consciousness"),
    ]
    fig, ax = plt.subplots(figsize=(13, 7))
    ax.set_xlim(0, 14); ax.set_ylim(0, len(rows) + 2)
    ax.axis("off")
    # Header
    ax.text(2.5, len(rows) + 0.5, "Intended claim", fontsize=11.5,
            fontweight="bold", ha="center")
    ax.text(7, len(rows) + 0.5, "Strongest alternative explanation",
            fontsize=11.5, fontweight="bold", ha="center")
    ax.text(11.5, len(rows) + 0.5, "Control / acknowledged limit",
            fontsize=11.5, fontweight="bold", ha="center")
    # Header rule
    ax.plot([0.5, 13.5], [len(rows) + 0.2, len(rows) + 0.2],
            color="#444", linewidth=0.8)
    for i, (claim, alt, ctrl) in enumerate(rows):
        y = len(rows) - i - 0.5
        row_color = "#f9f7f0" if i % 2 == 0 else "#ffffff"
        ax.add_patch(plt.Rectangle((0.5, y - 0.45), 13, 0.9,
                                    facecolor=row_color, edgecolor="none"))
        ax.text(2.5, y, claim, fontsize=9.5, ha="center", va="center",
                fontweight="bold")
        ax.text(7, y, alt, fontsize=9.5, ha="center", va="center",
                color="#700", style="italic")
        ax.text(11.5, y, ctrl, fontsize=9, ha="center", va="center",
                color="#070")
    ax.text(7, len(rows) + 1.4,
            "Figure A7. Alternative-explanations red-team table",
            ha="center", fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_a7_alternative_explanations.png",
                dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {FIG_DIR}/fig_a7_alternative_explanations.png")


def main():
    fig_a1_p16b_null_intervention()
    fig_a2_p17a_v_probe_saturation()
    fig_a3_p19_current_replay()
    fig_a4_p22_world_responds()
    fig_a5_p24_contrast_anti_cheats()
    fig_a6_p23b_re_engagement_dynamics()
    fig_a7_alternative_explanations()


if __name__ == "__main__":
    main()
