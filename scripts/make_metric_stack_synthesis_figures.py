#!/usr/bin/env python3
"""Synthesis-paper figures for the autonomous-probing arc (Papers 16b-25)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
FIG_DIR = ROOT / "papers" / "metric_stack_synthesis" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# Style
plt.rcParams.update({
    "font.size": 11,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
})


def safe_load(path):
    try:
        return json.loads(Path(path).read_text())
    except Exception as e:
        print(f"  could not load {path}: {e}")
        return None


def fig6_arc_food_attribution():
    """Figure 6: Food self_consume attribution across the autonomous-probing arc."""
    # Pull key conditions from saved sweeps
    points = []

    # P16b: factorized_null_anchor headline
    d = safe_load(ROOT / "artifacts/null_intervention/sweep_v1.json")
    if d:
        cells = [r for r in d["summary"]
                  if r["condition"] == "factorized_null_anchor"]
        food_preds = [c["pred_self_consume_food"] for c in cells]
        points.append({
            "paper": "P16b",
            "label": "16b\nnull anchor",
            "mean": float(np.mean(food_preds)) if food_preds else 0,
            "std": float(np.std(food_preds)) if len(food_preds) > 1 else 0,
        })

    # P19: learned_current_replay_audit
    d = safe_load(ROOT / "artifacts/current_error_calibration/sweep_v1.json")
    if d:
        cells = [r for r in d["summary"]
                  if r["condition"] == "learned_current_replay_audit_online"]
        food_preds = [c["pred_self_consume_food"] for c in cells]
        if food_preds:
            points.append({
                "paper": "P19",
                "label": "19\ncurrent_replay",
                "mean": float(np.mean(food_preds)),
                "std": float(np.std(food_preds)) if len(food_preds) > 1 else 0,
            })

    # P21A: norm_target_perdim_cost
    d = safe_load(ROOT / "artifacts/scale_normalized_vprobe/sweep_v1.json")
    if d:
        cells = [r for r in d["summary"]
                  if r["condition"] == "norm_target_perdim_cost"]
        food_preds = [c["pred_self_E_consume_food"] for c in cells]
        if food_preds:
            points.append({
                "paper": "P21A",
                "label": "21A\nscale-norm",
                "mean": float(np.mean(food_preds)),
                "std": float(np.std(food_preds)) if len(food_preds) > 1 else 0,
            })

    # P22: learned_scale_norm_current_replay (vector first-order self)
    d = safe_load(ROOT / "artifacts/world_responds/sweep_v1.json")
    if d:
        cells = [r for r in d["summary"]
                  if r["condition"] == "learned_scale_norm_current_replay"]
        food_preds = [c["pred_self_E_consume_food"] for c in cells]
        if food_preds:
            points.append({
                "paper": "P22",
                "label": "22\nthree-head",
                "mean": float(np.mean(food_preds)),
                "std": float(np.std(food_preds)) if len(food_preds) > 1 else 0,
            })

    # P23B: leaky_effort_integrator
    d = safe_load(ROOT / "artifacts/habituated_reengagement/sweep_v1.json")
    if d:
        cells = [r for r in d["summary"]
                  if r["condition"] == "leaky_effort_integrator"]
        food_preds = [c["pred_self_E_consume_food"] for c in cells]
        if food_preds:
            points.append({
                "paper": "P23B",
                "label": "23B\nmaintained\nboundary",
                "mean": float(np.mean(food_preds)),
                "std": float(np.std(food_preds)) if len(food_preds) > 1 else 0,
            })

    # P25: role_specific_contrast_twosided_lambda3 (HEADLINE)
    d = safe_load(ROOT / "artifacts/role_specific_identifiability/sweep_v1.json")
    if d:
        cells = [r for r in d["summary"]
                  if r["condition"] == "role_specific_contrast_twosided_lambda3"]
        food_preds = [c["pred_self_E_consume_food"] for c in cells]
        if food_preds:
            points.append({
                "paper": "P25",
                "label": "25\nrole-specific\n+ learned buckets",
                "mean": float(np.mean(food_preds)),
                "std": float(np.std(food_preds)) if len(food_preds) > 1 else 0,
            })

    fig, ax = plt.subplots(figsize=(10, 5.5))
    x = np.arange(len(points))
    means = [p["mean"] for p in points]
    stds = [p["std"] for p in points]
    colors = ["#1f77b4", "#2ca02c", "#2ca02c", "#1f77b4", "#2ca02c", "#7f7f7f"]
    ax.bar(x, means, 0.65, yerr=stds, color=colors[:len(x)],
            alpha=0.88, edgecolor="black", linewidth=0.5,
            error_kw={"linewidth": 1.2, "ecolor": "#444"})
    for i, p in enumerate(points):
        ax.text(i, p["mean"] + 0.04,
                f"{p['mean']:+.2f}",
                ha="center", fontsize=9.5, fontweight="bold")
    ax.axhline(0.96, color="green", linestyle="--", linewidth=1.5,
               alpha=0.6, label="true food self_consume = +0.96")
    ax.axhline(0, color="black", linewidth=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels([p["label"] for p in points], fontsize=9)
    ax.set_ylabel("Predicted food self_consume (cross-seed mean)", fontsize=11)
    ax.set_title("Figure 6. Food self attribution across the autonomous-probing arc\n"
                  "Each milestone closes a specific calibration failure named in §4",
                  fontsize=12)
    ax.set_ylim(-0.5, 1.4)
    ax.legend(loc="lower right", fontsize=9)
    ax.grid(axis="y", linestyle=":", alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig6_arc_food_attribution.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {FIG_DIR}/fig6_arc_food_attribution.png")


def fig2_correction_chain():
    """Visual: 8 named distinctions as a vertical cascade."""
    distinctions = [
        ("Paper 6-16", "behavior ≠ representation",
         "high return with wrong internal structure"),
        ("Paper 7-9", "representation ≠ competence",
         "trained encoders not exploited by policy"),
        ("Paper 14b", "uncertainty ≠ error",
         "ensemble variance uncorrelated with prediction error"),
        ("Paper 17A", "residual scale ≠ systematic error",
         "V_probe targets dominated by shock noise"),
        ("Paper 18 → 19", "historical EMA ≠ current error",
         "stored residuals stale by training time"),
        ("Paper 22", "current error ≠ value of probing",
         "high error not equal to high marginal MAE reduction"),
        ("Paper 23A → 23B", "re-engagement ≠ stable re-engagement",
         "anxiety without saturation; G6 catches false calm"),
        ("Paper 24-25", "total prediction ≠ component identifiability",
         "shared mediated head learns global h-response, not role-specific"),
    ]
    fig, ax = plt.subplots(figsize=(11, 7.2))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, len(distinctions) + 1)
    ax.axis("off")
    for i, (paper, dist, why) in enumerate(distinctions):
        y = len(distinctions) - i - 0.5
        # Paper label
        ax.text(0.3, y, paper, fontsize=10, fontweight="bold",
                color="#1f77b4", va="center")
        # Box with distinction
        box = FancyBboxPatch((2.5, y - 0.32), 8, 0.64,
                                boxstyle="round,pad=0.04",
                                facecolor="#f4f0e8", edgecolor="#888",
                                linewidth=1.0)
        ax.add_patch(box)
        ax.text(6.5, y + 0.1, dist, fontsize=11.5, fontweight="bold",
                ha="center", va="center", color="#222")
        ax.text(6.5, y - 0.18, why, fontsize=9, ha="center", va="center",
                style="italic", color="#555")
        # Arrow to next
        if i < len(distinctions) - 1:
            ax.annotate("", xy=(6.5, y - 0.5), xytext=(6.5, y - 0.34),
                         arrowprops=dict(arrowstyle="->", color="#888", lw=1.2))
    ax.text(6.5, len(distinctions) + 0.4,
            "The Correction Chain: Eight named distinctions the program forced",
            ha="center", fontsize=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig2_correction_chain.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {FIG_DIR}/fig2_correction_chain.png")


def fig5_maintained_boundary_cycle():
    """Figure 5: detect → probe → cool → quiet → detect again cycle."""
    fig, ax = plt.subplots(figsize=(11, 6.5))
    ax.set_xlim(-0.5, 10.5)
    ax.set_ylim(-1.5, 5.5)
    ax.axis("off")

    states = [
        (2, 4, "QUIET\n(probe rate low)", "#d9e9d9"),
        (5, 4, "WORLD CHANGES\n(non-null surprise rises)", "#ffe6cc"),
        (8, 4, "ALLOCATE PROBES\n(V_probe + shift signal)", "#ffb380"),
        (8, 1.5, "COOL DOWN\n(probe_effort builds,\nthreshold rises)", "#cce0ff"),
        (5, 1.5, "ATTRIBUTION\nRECOVERED", "#b3d9ff"),
        (2, 1.5, "QUIET AGAIN\n(re-engageable)", "#d9e9d9"),
    ]
    for x, y, label, color in states:
        box = FancyBboxPatch((x - 1.3, y - 0.55), 2.6, 1.1,
                                boxstyle="round,pad=0.05",
                                facecolor=color, edgecolor="#444",
                                linewidth=1.2)
        ax.add_patch(box)
        ax.text(x, y, label, ha="center", va="center", fontsize=9.5,
                fontweight="bold")
    arrows = [
        ((3.3, 4), (3.7, 4)),
        ((6.3, 4), (6.7, 4)),
        ((8, 3.45), (8, 2.05)),
        ((6.7, 1.5), (6.3, 1.5)),
        ((3.7, 1.5), (3.3, 1.5)),
        ((2, 2.05), (2, 3.45)),
    ]
    for (sx, sy), (ex, ey) in arrows:
        ax.annotate("", xy=(ex, ey), xytext=(sx, sy),
                     arrowprops=dict(arrowstyle="->", color="#444", lw=1.8))
    ax.text(5, 5.1, "Figure 5. The maintained-boundary mechanism (Paper 23B)",
            ha="center", fontsize=13, fontweight="bold")
    ax.text(5, -1.1,
             "The agent learns when to ask, when to stop asking, and how to ask again — "
             "without forgetting how to ask.\n"
             "(Vervaeke's relevance realization, operationalized at minimum scale.)",
             ha="center", fontsize=10, style="italic", color="#444")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig5_maintained_boundary_cycle.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {FIG_DIR}/fig5_maintained_boundary_cycle.png")


def fig3_p23b_goldilocks():
    """Figure 3: P23B's Goldilocks tradeoff: re-engagement vs anxiety."""
    d = safe_load(ROOT / "artifacts/habituated_reengagement/sweep_v1.json")
    if not d:
        print("  no P23B data — skipping fig4"); return
    rows = d["summary"]
    conds_show = [
        ("p22_learned_current_replay", "P22 baseline\n(self-silencing)"),
        ("two_timescale_vprobe", "two-timescale\n(no surprise)"),
        ("fixed_surprise_decrement", "fixed decrement\n(FALSE CALM)"),
        ("p23a_surprise_no_cooling", "surprise only\n(ANXIETY)"),
        ("leaky_effort_integrator", "decision cooling\n(HEADLINE)"),
        ("decision_refractory", "threshold refractory"),
        ("burst_then_refractory", "burst + cooldown"),
        ("scheduled_null_anchor", "scheduled (control)"),
        ("oracle_source", "oracle source"),
    ]
    psAUC_means = []; psAUC_stds = []; recoveries = []
    for cond, label in conds_show:
        cells = [r for r in rows if r["condition"] == cond]
        aucs = [r.get("post_shift1_auc", 0) for r in cells]
        tRecs = [r.get("time_to_recover") for r in cells]
        psAUC_means.append(float(np.mean(aucs)))
        psAUC_stds.append(float(np.std(aucs)) if len(aucs) > 1 else 0)
        recoveries.append(sum(1 for t in tRecs if t is not None and t > 0))
    fig, ax = plt.subplots(figsize=(13, 6))
    x = np.arange(len(conds_show))
    colors = ["#999999", "#bbbbbb", "#d62728", "#d62728",
                "#2ca02c", "#2ca02c", "#2ca02c", "#1f77b4", "#444444"]
    bars = ax.bar(x, psAUC_means, 0.65, yerr=psAUC_stds,
                    color=colors, alpha=0.88, edgecolor="black", linewidth=0.5,
                    error_kw={"linewidth": 1.1})
    for i, (m, r) in enumerate(zip(psAUC_means, recoveries)):
        ax.text(i, m + 0.15,
                f"AUC {m:.2f}\nrecover {r}/3",
                ha="center", fontsize=8.5, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([c[1] for c in conds_show], fontsize=8.5)
    ax.set_ylabel("Post-shift-1 AUC (lower = better recovery)", fontsize=11)
    ax.set_title("Figure 3. The Goldilocks: re-engagement vs anxiety vs false calm (Paper 23B)",
                  fontsize=12)
    # Legend
    handles = [
        patches.Patch(color="#999999", label="Pre-P23B (no surprise)"),
        patches.Patch(color="#d62728", label="Signal-layer fails: anxiety OR false calm"),
        patches.Patch(color="#2ca02c", label="Decision-layer wins"),
        patches.Patch(color="#1f77b4", label="Positive control"),
        patches.Patch(color="#444444", label="Oracle"),
    ]
    ax.legend(handles=handles, loc="upper right", fontsize=9)
    ax.grid(axis="y", linestyle=":", alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig3_p23b_goldilocks.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {FIG_DIR}/fig3_p23b_goldilocks.png")


def fig4_architectural_ceiling():
    """Figure 4: P25's structural finding: food vs medicine mediated predictions collapse."""
    d = safe_load(ROOT / "artifacts/role_specific_identifiability/sweep_v1.json")
    if not d:
        print("  no P25 data — skipping fig5"); return
    rows = d["summary"]
    conds_show = [
        ("p24_default_role_invariant_no_contrast", "P24 baseline\n(old env)"),
        ("role_specific_no_contrast", "P25 env\nno contrast"),
        ("role_specific_contrast_one_sided", "contrast\none-sided"),
        ("role_specific_contrast_twosided_lambda3", "HEADLINE\n(over-pinned)"),
        ("wrong_history_contrast_role_specific", "wrong-history\n(still helps!)"),
        ("fully_learned_buckets_with_contrast", "fully-learned\nbuckets"),
        ("oracle_source_role_specific", "oracle source"),
    ]
    food_means = []; food_stds = []
    med_means = []; med_stds = []
    for cond, label in conds_show:
        cells = [r for r in rows if r["condition"] == cond]
        food_v = [r.get("pred_mediated_E_contrast_food", 0) for r in cells]
        med_v = [r.get("pred_mediated_E_contrast_medicine", 0) for r in cells]
        food_means.append(float(np.mean(food_v))); food_stds.append(float(np.std(food_v)) if len(food_v) > 1 else 0)
        med_means.append(float(np.mean(med_v))); med_stds.append(float(np.std(med_v)) if len(med_v) > 1 else 0)
    fig, ax = plt.subplots(figsize=(13, 6))
    x = np.arange(len(conds_show))
    w_bar = 0.35
    ax.bar(x - w_bar/2, food_means, w_bar, yerr=food_stds,
            color="#d62728", alpha=0.85, edgecolor="black", linewidth=0.5,
            label="food bucket (true 0.150 at h=1)",
            error_kw={"linewidth": 1.0})
    ax.bar(x + w_bar/2, med_means, w_bar, yerr=med_stds,
            color="#1f77b4", alpha=0.85, edgecolor="black", linewidth=0.5,
            label="medicine bucket (true 0.060 at h=1)",
            error_kw={"linewidth": 1.0})
    for i, (f, m) in enumerate(zip(food_means, med_means)):
        ax.text(i - w_bar/2, f + 0.005, f"{f:.2f}",
                ha="center", fontsize=8.5, color="#700")
        ax.text(i + w_bar/2, m + 0.005, f"{m:.2f}",
                ha="center", fontsize=8.5, color="#003")
    ax.axhline(0.15, color="#d62728", linestyle="--", linewidth=1.2,
               alpha=0.5, label="true food mediated (h=1)")
    ax.axhline(0.06, color="#1f77b4", linestyle="--", linewidth=1.2,
               alpha=0.5, label="true medicine mediated (h=1)")
    ax.set_xticks(x)
    ax.set_xticklabels([c[1] for c in conds_show], fontsize=8.5)
    ax.set_ylabel("Predicted mediated E contrast (high_h - low_h)", fontsize=11)
    ax.set_title("Figure 4. The architectural ceiling (Paper 25): "
                  "shared mediated head produces near-identical predictions for food vs medicine\n"
                  "even under role-specific environment + two-sided gauge anchoring + learned buckets",
                  fontsize=11)
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(axis="y", linestyle=":", alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig4_architectural_ceiling.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {FIG_DIR}/fig4_architectural_ceiling.png")


def fig1_metric_stack():
    """Figure 1: vertical metric stack diagram."""
    layers = [
        ("Architectural ceiling", "shared heads can't disambiguate role-specific (P25)", "#e8b3b3"),
        ("Learned probe abstractions", "K-means over (z, E, D, hist) (P25)", "#d4e4d4"),
        ("Component identifiability", "interventional contrast (P24-25)", "#cce0ff"),
        ("Maintained boundary", "detect→probe→cool→re-engage (P23A-B)", "#cce0ff"),
        ("Per-dim cross-comparable uncertainty", "scale normalization (P21A)", "#cce0ff"),
        ("Probe-vs-current-error calibration", "current_replay (P19)", "#cce0ff"),
        ("Self/world identifiability", "active null intervention (P16b)", "#cce0ff"),
        ("Valence dimensionality", "vector ΔV (P15)", "#fff3cc"),
        ("Uncertainty calibration", "same-class fails at boundary (P14b)", "#fff3cc"),
        ("Planner robustness", "greedy + safe fallback (P14)", "#fff3cc"),
        ("Trajectory-weighted return", "vs pointwise accuracy (P13b)", "#fff3cc"),
        ("Regime-boundary representation", "smooth fails at singular point (P13b)", "#fff3cc"),
        ("State/sample coverage", "off-policy stability (P12-13a)", "#fff3cc"),
        ("Calibration / margin sign", "vs consume MSE alone (P11b)", "#fff3cc"),
        ("Action coverage", "conservative exploration (P11)", "#fff3cc"),
        ("Readout capacity", "nonlinear ΔE heads (P10)", "#ffd9b3"),
        ("Representation vs competence", "double dissociation (P7-9)", "#ffd9b3"),
        ("Valence geometry", "objects from concern (P6)", "#ffd9b3"),
        ("Repair / viability", "buffer, slack (P5)", "#ffd9b3"),
        ("Causal load-bearing", "passive→active (P4)", "#ffd9b3"),
        ("Geometry", "weakness/symmetry/OOD (P1-3)", "#ffd9b3"),
    ]
    fig, ax = plt.subplots(figsize=(13, 11))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, len(layers) + 1)
    ax.axis("off")
    for i, (name, why, color) in enumerate(layers):
        y = i + 0.5
        box = FancyBboxPatch((0.5, y - 0.35), 13, 0.7,
                                boxstyle="round,pad=0.04",
                                facecolor=color, edgecolor="#666",
                                linewidth=0.8)
        ax.add_patch(box)
        ax.text(1, y, name, fontsize=11, fontweight="bold",
                ha="left", va="center")
        ax.text(13, y, why, fontsize=9.5, ha="right", va="center",
                style="italic", color="#444")
    ax.text(7, len(layers) + 0.55,
            "Figure 1. The Metric Stack of Concern (read bottom-up)",
            ha="center", fontsize=14, fontweight="bold")
    ax.text(7, len(layers) + 0.1,
            "Each layer was added because the previous one had a specific empirical failure",
            ha="center", fontsize=10, style="italic", color="#444")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig1_metric_stack.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {FIG_DIR}/fig1_metric_stack.png")


def fig7_philosophical_correlates():
    """Diagram: traditions ↔ what they predicted ↔ which papers operationalized it."""
    traditions = [
        ("Heidegger", "world as field of relevance", "P6, P10, full arc"),
        ("Gibson", "perception = affordances", "P6 'objects from concern'"),
        ("Uexküll", "Umwelt — mattering-world", "P15 zero-shot reweighting"),
        ("Enactivism / Autopoiesis", "sense-making by self-maintenance", "P23B maintained boundary"),
        ("Cybernetics / Ashby", "regulation under disturbance", "P23B probe-effort cooling"),
        ("Active inference / Friston", "action can be epistemic", "P16b–P25 null probes"),
        ("Pragmatism / Dewey", "inquiry loop: disturbance → experiment → restoration", "P23A-B cycle"),
        ("Jonas", "vulnerability creates concern", "viability-driven framing"),
        ("Canguilhem", "life defines norms", "G6 'no false calm' gate"),
        ("Simondon", "individuation as process", "P23B G10 re-openability"),
        ("Vervaeke", "relevance realization", "P23B full cycle"),
    ]
    fig, ax = plt.subplots(figsize=(13, 8))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, len(traditions) + 1)
    ax.axis("off")
    ax.text(7, len(traditions) + 0.5,
             "Figure 7. Philosophical correlates and what the experiments operationalize",
             ha="center", fontsize=13, fontweight="bold")
    ax.text(7, len(traditions) + 0.1,
             "Traditions predicted the SHAPE; experiments identify mechanisms and failure modes",
             ha="center", fontsize=10, style="italic", color="#444")
    for i, (tradition, prediction, papers) in enumerate(traditions):
        y = len(traditions) - i - 0.5
        # tradition
        ax.text(0.3, y, tradition, fontsize=10.5, fontweight="bold",
                color="#1f77b4", va="center", ha="left")
        # arrow
        ax.text(3.5, y, "→", fontsize=14, color="#888", ha="center", va="center")
        # prediction
        ax.text(7, y, prediction, fontsize=10.5,
                ha="center", va="center", color="#333", style="italic")
        ax.text(10.5, y, "→", fontsize=14, color="#888", ha="center", va="center")
        # papers
        ax.text(13.6, y, papers, fontsize=9.5, color="#666",
                ha="right", va="center")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig7_philosophical_correlates.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {FIG_DIR}/fig7_philosophical_correlates.png")


def main():
    fig1_metric_stack()
    fig2_correction_chain()
    fig3_p23b_goldilocks()
    fig4_architectural_ceiling()
    fig5_maintained_boundary_cycle()
    fig6_arc_food_attribution()
    fig7_philosophical_correlates()


if __name__ == "__main__":
    main()
