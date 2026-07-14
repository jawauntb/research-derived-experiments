#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Generate all figures for the commitment-surface paper.

Reads:
- experiments/commitment_surface/results/e1_concern_weighted.json
- experiments/commitment_surface/results/e2_e3_neural.json
- experiments/commitment_surface/results/e4_pythia_lora_v2_appendix.json
  (with local raw/smoke artifacts as fallbacks)

Writes:
- papers/commitment_surface/figures/fig1_e1_selectors.png
- papers/commitment_surface/figures/fig2_e2_arms_ood.png
- papers/commitment_surface/figures/fig3_e3_readout_vs_patch.png
- papers/commitment_surface/figures/fig4_e4_pythia_arms.png
- papers/commitment_surface/figures/fig5_frame_taxonomy.png
- papers/commitment_surface/figures/fig6_e7_selective_subspace.png
- papers/commitment_surface/figures/summary_metrics.json
    (summary of headline numbers for the PDF builder)
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
PAPER_FIG = ROOT / "papers" / "commitment_surface" / "figures"
PAPER_FIG.mkdir(parents=True, exist_ok=True)

E1_JSON = ROOT / "experiments" / "commitment_surface" / "results" / "e1_concern_weighted.json"
E2E3_JSON = ROOT / "experiments" / "commitment_surface" / "results" / "e2_e3_neural.json"
E7_JSON = (
    ROOT / "experiments" / "commitment_surface" / "results"
    / "e7_selective_subspace_2026_07_13.json"
)
E4_JSON_CANDIDATES = [
    ROOT
    / "experiments"
    / "commitment_surface"
    / "results"
    / "e4_pythia_lora_v2_appendix.json",
    ROOT / "artifacts" / "commitment_surface" / "e4_pythia_lora_v2.json",
    ROOT / "artifacts" / "commitment_surface" / "e4_smoke.json",
]

PALETTE = {
    "A": "#c0392b",  # red -- readout arm
    "B": "#2b6cb0",  # blue -- compat aug (new frame winner)
    "C": "#7f8c8d",  # grey -- wrong-group control
    "D": "#e67e22",  # orange -- loss selector
    "unweighted": "#9aa6b2",
    "wellspec": "#2b6cb0",
    "misspec": "#c0392b",
    "loss": "#7f8c8d",
    "truth": "#2f9e44",
    "P_none": "#9aa6b2",
    "P_ewc": "#e67e22",
    "P_sub": "#2b6cb0",
    "P_wrong": "#7f8c8d",
}

plt.rcParams.update({
    "figure.dpi": 200, "savefig.dpi": 200, "font.size": 9,
    "font.family": "DejaVu Sans", "axes.edgecolor": "#444444",
    "axes.linewidth": 0.8, "axes.grid": True, "grid.color": "#d9dde3",
    "grid.linewidth": 0.6, "axes.axisbelow": True, "axes.titlesize": 10,
    "axes.titleweight": "bold", "legend.frameon": False, "figure.autolayout": True,
})


def _save(fig, path: Path) -> str:
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return str(path)


def make_e1_figure(e1: dict) -> tuple[str, dict]:
    s = e1["summary"]
    labels = [
        "Concern-weighted\n(well-specified)",
        "Unweighted\nBennett",
        "Concern-weighted\n(misspecified)",
        "Train-loss\nselector",
        "Truth\n(upper bound)",
    ]
    keys = ["concern_wellspec", "unweighted", "concern_misspec", "loss", "truth"]
    means = [s[k]["mean"] for k in keys]
    lows = [s[k]["ci95_low"] for k in keys]
    highs = [s[k]["ci95_high"] for k in keys]
    err = [[m - lo, hi - m] for m, lo, hi in zip(means, lows, highs)]
    err = list(zip(*err))
    colors = [PALETTE["wellspec"], PALETTE["unweighted"], PALETTE["misspec"], PALETTE["loss"], PALETTE["truth"]]

    fig, ax = plt.subplots(figsize=(6.3, 3.5))
    ys = list(range(len(labels)))
    ax.barh(ys, means, xerr=err, color=colors, height=0.66,
            error_kw={"lw": 1.0, "capsize": 3, "ecolor": "#444"})
    ax.set_yticks(ys)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlabel("Concern-weighted deployment accuracy (higher is better)")
    ax.set_title("E1 — selectors on unequal-consequence deployment")
    ax.set_xlim(0, 1.05)
    for i, m in enumerate(means):
        ax.text(m + 0.01, i, f"{m:.3f}", va="center", ha="left",
                fontsize=8.5, color="#222")
    ax.axvline(s["unweighted"]["mean"], color="#8a8a8a", lw=0.8, ls=":",
               label=f'unweighted mean = {s["unweighted"]["mean"]:.3f}')
    ax.legend(fontsize=7.6, loc="lower right")
    path = PAPER_FIG / "fig1_e1_selectors.png"
    _save(fig, path)
    return str(path), {
        "n_cells": s["n_cells"],
        "gap_wellspec_vs_unweighted": s["gap_wellspec_vs_unweighted"],
        "gap_misspec_vs_unweighted": s["gap_misspec_vs_unweighted"],
        "wellspec_mean": s["concern_wellspec"]["mean"],
        "unweighted_mean": s["unweighted"]["mean"],
        "misspec_mean": s["concern_misspec"]["mean"],
        "loss_mean": s["loss"]["mean"],
    }


def make_e2_figure(e2: dict) -> tuple[str, dict]:
    s = e2["summary"]
    per_arm = s["per_arm"]
    arm_labels = {
        "A": "A — Readout selector\n(no augmentation)",
        "B": "B — Compat aug\n(true cyclic group)",
        "C": "C — Wrong-group aug\n(control)",
        "D": "D — Loss selector\n(no augmentation)",
    }
    arms = ["A", "B", "C", "D"]
    ood_means = [per_arm.get(a, {}).get("ood_accuracy", {}).get("mean", 0.0) for a in arms]
    ood_lo = [per_arm.get(a, {}).get("ood_accuracy", {}).get("ci95_low", 0.0) for a in arms]
    ood_hi = [per_arm.get(a, {}).get("ood_accuracy", {}).get("ci95_high", 0.0) for a in arms]
    patch_means = [per_arm.get(a, {}).get("patch_ce_delta", {}).get("mean", 0.0) for a in arms]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 3.3))
    xs = list(range(4))
    colors = [PALETTE[a] for a in arms]
    err = [[m - lo, hi - m] for m, lo, hi in zip(ood_means, ood_lo, ood_hi)]
    err = list(zip(*err))
    ax1.bar(xs, ood_means, yerr=err, color=colors, error_kw={"lw": 1, "capsize": 3, "ecolor": "#444"})
    ax1.set_xticks(xs)
    ax1.set_xticklabels([arm_labels[a] for a in arms], fontsize=7.5)
    ax1.set_ylabel("OOD accuracy (mean, 95% CI)")
    ax1.set_title("E2 — OOD accuracy by arm")
    ax1.set_ylim(0, 1.05)
    for x, m in zip(xs, ood_means):
        ax1.text(x, m + 0.02, f"{m:.3f}", ha="center", fontsize=8, color="#222")

    ax2.bar(xs, patch_means, color=colors)
    ax2.set_xticks(xs)
    ax2.set_xticklabels(arm_labels[a] for a in arms)  # noqa: E501
    ax2.set_xticklabels([arm_labels[a] for a in arms], fontsize=7.5)
    ax2.set_ylabel("Patch-CE Δ (mean)")
    ax2.set_title("E3 (companion) — patch-CE by arm")
    ax2.axhline(0, color="#444", lw=0.7)
    for x, m in zip(xs, patch_means):
        ax2.text(x, m + 0.02, f"{m:+.3f}", ha="center", fontsize=8, color="#222")

    path = PAPER_FIG / "fig2_e2_arms_ood.png"
    _save(fig, path)
    return str(path), {
        "gap_B_minus_A_ood": s["gap_B_minus_A_ood"],
        "gap_B_minus_A_patch_ce": s["gap_B_minus_A_patch_ce"],
        "gap_B_minus_C_patch_ce": s["gap_B_minus_C_patch_ce"],
        "rho_weakness_ood": s["rho_weakness_ood"],
        "rho_patch_ce_ood": s["rho_patch_ce_ood"],
        "per_arm_ood": {a: per_arm.get(a, {}).get("ood_accuracy", {}) for a in arms},
    }


def make_e3_figure(e2e3: dict) -> tuple[str, dict]:
    rows = e2e3.get("all_rows", [])
    xs_w = [r["weakness_true"] for r in rows]
    xs_p = [r["patch_ce_delta"] for r in rows]
    ys = [r["ood_accuracy"] for r in rows]
    colors = [PALETTE.get(r["arm"], "#888") for r in rows]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.4, 3.4))
    ax1.scatter(xs_w, ys, c=colors, s=30, edgecolor="#222", linewidth=0.4)
    ax1.set_xlabel("Weakness (readout)")
    ax1.set_ylabel("OOD accuracy")
    ax1.set_title(f"Weakness vs OOD (ρ = {e2e3['summary']['rho_weakness_ood']:.2f})")
    ax1.set_ylim(-0.05, 1.05)

    ax2.scatter(xs_p, ys, c=colors, s=30, edgecolor="#222", linewidth=0.4)
    ax2.set_xlabel("Patch-CE Δ (causal)")
    ax2.set_ylabel("OOD accuracy")
    ax2.set_title(f"Patch-CE vs OOD (ρ = {e2e3['summary']['rho_patch_ce_ood']:.2f})")
    ax2.set_ylim(-0.05, 1.05)
    ax2.axvline(0, color="#444", lw=0.6, ls="--")

    # Add legend
    for arm, color in PALETTE.items():
        if arm in ("A", "B", "C", "D"):
            ax1.scatter([], [], c=color, s=30, edgecolor="#222", linewidth=0.4, label=f"Arm {arm}")
    ax1.legend(fontsize=7.6, loc="lower right")

    path = PAPER_FIG / "fig3_e3_readout_vs_patch.png"
    _save(fig, path)
    return str(path), {
        "rho_weakness_ood_all": e2e3["summary"]["rho_weakness_ood"],
        "rho_patch_ce_ood_all": e2e3["summary"]["rho_patch_ce_ood"],
        "n_cells": len(rows),
    }


def make_e4_figure(e4: dict) -> tuple[str, dict]:
    analysis = e4.get("analysis", {})
    per_arm = analysis.get("per_arm", {})
    arm_labels = {
        "A": "A — Readout",
        "B": "B — Compat aug",
        "C": "C — Wrong-group",
        "D": "D — Loss",
    }
    arms = [a for a in ("A", "B", "C", "D") if a in per_arm]
    ood_means = [per_arm[a]["ood_mean"] for a in arms]
    patch_means = [per_arm[a]["patch_ce_delta_mean"] for a in arms]
    weak_means = [per_arm[a]["weakness_mean"] for a in arms]
    ood_maxes = [per_arm[a]["ood_max"] for a in arms]
    ns = [per_arm[a]["n"] for a in arms]

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(9.4, 3.4))
    xs = list(range(len(arms)))
    colors = [PALETTE[a] for a in arms]
    ax1.bar(xs, ood_means, color=colors)
    ax1.set_xticks(xs)
    ax1.set_xticklabels([arm_labels[a] for a in arms])
    ax1.set_ylabel("OOD accuracy (mean)")
    ax1.set_title("E4 — OOD on Pythia LoRA modular addition")
    ax1.set_ylim(0, 1.05)
    for x, m, mx, n in zip(xs, ood_means, ood_maxes, ns):
        ax1.text(x, m + 0.02, f"{m:.2f}\nmax {mx:.2f}\nn={n}", ha="center",
                 fontsize=7.5, color="#222")

    ax2.bar(xs, patch_means, color=colors)
    ax2.set_xticks(xs)
    ax2.set_xticklabels([arm_labels[a] for a in arms])
    ax2.set_ylabel("Patch-CE Δ (LoRA-ablation OOD NLL)")
    ax2.set_title("E4 — LoRA is load-bearing when compat-augmented")
    ax2.axhline(0, color="#444", lw=0.7)
    for x, m in zip(xs, patch_means):
        ax2.text(x, m + 0.05 * (1 if m >= 0 else -1), f"{m:+.2f}", ha="center",
                 fontsize=8, color="#222")

    ax3.bar(xs, weak_means, color=colors)
    ax3.set_xticks(xs)
    ax3.set_xticklabels([arm_labels[a] for a in arms])
    ax3.set_ylabel("Cyclic-group weakness (readout)")
    ax3.set_title("Weakness (readout) does NOT track OOD")
    ax3.set_ylim(0, 1.05)
    for x, m in zip(xs, weak_means):
        ax3.text(x, m + 0.02, f"{m:.2f}", ha="center", fontsize=8, color="#222")

    path = PAPER_FIG / "fig4_e4_pythia_arms.png"
    _save(fig, path)
    return str(path), {
        "n_cells": analysis.get("n_cells", 0),
        "gap_B_minus_A_ood": analysis.get("gap_B_minus_A_ood", 0.0),
        "gap_B_minus_A_patch_ce": analysis.get("gap_B_minus_A_patch_ce", 0.0),
        "gap_B_minus_C_patch_ce": analysis.get("gap_B_minus_C_patch_ce", 0.0),
        "rho_weakness_ood_all_cells": analysis.get("rho_weakness_ood_all_cells", 0.0),
        "rho_patch_ce_ood_all_cells": analysis.get("rho_patch_ce_ood_all_cells", 0.0),
        "e4_new_frame_pass": analysis.get("e4_new_frame_pass", False),
        "e4_old_frame_pass": analysis.get("e4_old_frame_pass", False),
        "per_arm": per_arm,
    }


def make_frame_taxonomy_figure() -> str:
    """Schematic: old-frame taxonomy (footprint / selector / controller /
    anti-correlate) collapsed into the new-frame primitive: commitment-
    surface survival."""
    fig, ax = plt.subplots(figsize=(8.4, 3.6))
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    # Left column: old frame.
    ax.text(0.02, 0.92, "Old frame", fontsize=12, weight="bold", color="#1a1a1a")
    ax.text(0.02, 0.83, "availability of geometry / weakness ⇒ use",
            fontsize=9, color="#555", style="italic")
    ax.text(0.02, 0.70, "Structure present ⇒ ?", fontsize=9.5, color="#333")
    ax.text(0.02, 0.58, "footprint   — correlate, not cause",
            fontsize=8.8, color="#c0392b")
    ax.text(0.02, 0.48, "selector    — picks amongst hypotheses",
            fontsize=8.8, color="#e67e22")
    ax.text(0.02, 0.38, "controller  — actually used",
            fontsize=8.8, color="#2f9e44")
    ax.text(0.02, 0.28, "anti-correlate — present, opposite-signed to OOD",
            fontsize=8.8, color="#7f8c8d")

    # Arrow in the middle gap.
    ax.annotate(
        "",
        xy=(0.55, 0.55), xytext=(0.44, 0.55),
        arrowprops={"arrowstyle": "->", "lw": 1.4, "color": "#1a1a1a"},
    )

    # Right column: new frame. Start well past the arrow's tip.
    ax.text(0.58, 0.92, "New frame", fontsize=12, weight="bold", color="#1a1a1a")
    ax.text(0.58, 0.83, "commitment surface Σ = (G_dep, C, T)",
            fontsize=9, color="#555", style="italic")
    ax.text(0.58, 0.70, "Load-bearing at Σ iff:", fontsize=9.5, color="#333")
    ax.text(0.58, 0.58, "(i)  train-time compat intervention → OOD lift",
            fontsize=8.8, color="#2b6cb0")
    ax.text(0.58, 0.48, "(ii) causal patch → CE ≥ ε at commitment",
            fontsize=8.8, color="#2b6cb0")
    ax.text(0.58, 0.38, "(iii) effect survives transport t ∈ T",
            fontsize=8.8, color="#2b6cb0")

    # Bottom footer spanning the width.
    ax.text(0.5, 0.10,
            "Weakness recovered when G_probe ⊇ G_dep (Prop. 2).",
            fontsize=8.5, color="#555", style="italic",
            ha="center")
    path = PAPER_FIG / "fig5_frame_taxonomy.png"
    _save(fig, path)
    return str(path)


def make_e7_figure(e7: dict) -> tuple[str, dict]:
    """Show E7's integrity verdict or, for a valid run, its gate result."""
    if e7["status"] == "invalid":
        budget = e7["integrity"]["budget_detail"]
        timing_rows = sorted(
            budget["relative_wall_clock_ranges"],
            key=lambda row: (
                row["width"], row["seed_index"], row["boundary_index"]
            ),
        )
        xs = list(range(1, len(timing_rows) + 1))
        percentages = [100.0 * row["relative_wall_clock_range"] for row in timing_rows]
        colors = ["#c53030" if not row["pass"] else "#718096" for row in timing_rows]
        failed_groups = sum(not row["pass"] for row in timing_rows)
        valid_streams = int(e7["valid_streams"])

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.6, 3.5))
        ax1.bar(xs, percentages, color=colors, width=0.78)
        ax1.axhline(2.0, color="#2b6cb0", linestyle="--", linewidth=1.2)
        ax1.set_xlabel("Matched width/seed/task group")
        ax1.set_ylabel("Per-arm timing range (%)")
        ax1.set_title("6/32 groups exceed the frozen 2% gate")

        ax2.bar(
            ["Matched\ngroups", "Streams"],
            [len(timing_rows) - failed_groups, valid_streams],
            color="#718096",
            label="valid",
        )
        ax2.bar(
            ["Matched\ngroups", "Streams"],
            [failed_groups, int(e7["stream_count"]) - valid_streams],
            bottom=[len(timing_rows) - failed_groups, valid_streams],
            color="#c53030",
            label="invalid",
        )
        ax2.set_ylim(0, 32)
        ax2.set_ylabel("Count")
        ax2.set_title("Budget failure withholds G1–G4")
        ax2.legend(fontsize=8)

        path = PAPER_FIG / "fig6_e7_selective_subspace.png"
        _save(fig, path)
        return str(path), {
            "status": "invalid",
            "scientific_disposition": "INVALID_NO_SCIENTIFIC_VERDICT",
            "failed_matched_groups": failed_groups,
            "total_matched_groups": len(timing_rows),
            "valid_streams": valid_streams,
            "max_relative_wall_clock_range": budget[
                "max_relative_wall_clock_range"
            ],
        }

    rows = {(row["width"], row["arm"]): row for row in e7["summary"]}
    arms = ["P_none", "P_ewc", "P_sub", "P_wrong"]
    labels = ["None", "EWC", "Compat\nsubspace", "Wrong\nsubspace"]
    widths = [96, 128]
    xs = list(range(len(arms)))
    bar_width = 0.36

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.6, 3.5))
    for offset_index, width in enumerate(widths):
        offset = (offset_index - 0.5) * bar_width
        patch_values = [
            rows[(width, arm)]["earlier_patch_ce_per_mass"] for arm in arms
        ]
        retained_values = [
            rows[(width, arm)]["retained_ood_accuracy"] for arm in arms
        ]
        ax1.bar(
            [x + offset for x in xs],
            patch_values,
            width=bar_width,
            color=[PALETTE[arm] for arm in arms],
            alpha=1.0 if width == 96 else 0.55,
            edgecolor="#333333",
            linewidth=0.5,
            label=f"width {width}",
        )
        ax2.bar(
            [x + offset for x in xs],
            retained_values,
            width=bar_width,
            color=[PALETTE[arm] for arm in arms],
            alpha=1.0 if width == 96 else 0.55,
            edgecolor="#333333",
            linewidth=0.5,
            label=f"width {width}",
        )

    ax1.set_xticks(xs)
    ax1.set_xticklabels(labels, fontsize=8)
    ax1.axhline(0.0, color="#333333", lw=0.8)
    ax1.set_ylabel("Earlier-task patch-CE / realized mass")
    ax1.set_title("Mechanism metric separates P_sub")
    ax1.legend(fontsize=7.5)

    ax2.set_xticks(xs)
    ax2.set_xticklabels(labels, fontsize=8)
    ax2.set_ylim(0.45, 0.57)
    ax2.set_ylabel("Retained earlier-task OOD accuracy")
    ax2.set_title("Behavioral frontier does not separate")
    ax2.legend(fontsize=7.5)

    path = PAPER_FIG / "fig6_e7_selective_subspace.png"
    _save(fig, path)
    return str(path), {
        "strict_verdict": e7["gate_analysis"]["strict_verdict"],
        "gates": e7["gate_analysis"]["gates"],
        "margins": e7["gate_analysis"]["margins"],
        "checkpoint_count": e7["checkpoint_count"],
        "stability_rows": e7["stability_rows"],
    }


def _repo_relative(path: str) -> str:
    return str(Path(path).relative_to(ROOT))


def main() -> None:
    summary = {"figures": {}, "headline": {}}

    if E1_JSON.exists():
        e1 = json.loads(E1_JSON.read_text())
        fig1_path, e1_meta = make_e1_figure(e1)
        summary["figures"]["fig1"] = _repo_relative(fig1_path)
        summary["headline"]["e1"] = e1_meta
    else:
        print(f"skip E1 fig (missing {E1_JSON})")

    if E2E3_JSON.exists():
        e2 = json.loads(E2E3_JSON.read_text())
        fig2_path, e2_meta = make_e2_figure(e2)
        fig3_path, e3_meta = make_e3_figure(e2)
        summary["figures"]["fig2"] = _repo_relative(fig2_path)
        summary["figures"]["fig3"] = _repo_relative(fig3_path)
        summary["headline"]["e2"] = e2_meta
        summary["headline"]["e3"] = e3_meta
    else:
        print(f"skip E2/E3 figs (missing {E2E3_JSON})")

    e4_json = next((p for p in E4_JSON_CANDIDATES if p.exists()), None)
    if e4_json is not None:
        e4 = json.loads(e4_json.read_text())
        fig4_path, e4_meta = make_e4_figure(e4)
        summary["figures"]["fig4"] = _repo_relative(fig4_path)
        summary["headline"]["e4"] = e4_meta
        summary["headline"]["e4"]["source"] = str(e4_json.relative_to(ROOT))
    else:
        print("skip E4 fig (no artifact found)")

    fig5_path = make_frame_taxonomy_figure()
    summary["figures"]["fig5"] = _repo_relative(fig5_path)

    if E7_JSON.exists():
        e7 = json.loads(E7_JSON.read_text())
        fig6_path, e7_meta = make_e7_figure(e7)
        summary["figures"]["fig6"] = _repo_relative(fig6_path)
        summary["headline"]["e7"] = e7_meta
    else:
        print(f"skip E7 fig (missing {E7_JSON})")

    out = PAPER_FIG / "summary_metrics.json"
    out.write_text(json.dumps(summary, indent=2))
    print(f"wrote {out}")
    print(json.dumps(summary["headline"], indent=2))


if __name__ == "__main__":
    main()
