#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Render Paper B after the 2026-07-02 Modal moved-location sweep.

Run:  python scripts/build_paperB_pdf.py
Out:  artifacts/papers/concern_deforms_metric.pdf
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paperkit as pk  # noqa: E402
from reportlab.platypus import PageBreak, Paragraph  # noqa: E402

FIG = "artifacts/papers/figs_paperB"
OUT = "artifacts/papers/concern_deforms_metric.pdf"

ARCH_ROWS = [
    {
        "arch": "JEPA",
        "lift": 0.6847,
        "lift_lo": 0.6476,
        "lift_hi": 0.7228,
        "lift_se": 0.0193,
        "spec": 0.9162,
        "spec_lo": 0.8890,
        "spec_hi": 0.9425,
        "spec_se": 0.0138,
        "rank": 0.832,
        "peak_error": 0.205,
        "area_lift": 0.0871,
        "area_lift_lo": 0.0334,
        "area_lift_hi": 0.1439,
        "area_spec": 0.3702,
        "area_spec_lo": 0.3364,
        "area_spec_hi": 0.4035,
    },
    {
        "arch": "RNN",
        "lift": 1.2013,
        "lift_lo": 1.1846,
        "lift_hi": 1.2179,
        "lift_se": 0.0085,
        "spec": 1.3572,
        "spec_lo": 1.3372,
        "spec_hi": 1.3774,
        "spec_se": 0.0103,
        "rank": 0.930,
        "peak_error": 0.069,
        "area_lift": 1.1867,
        "area_lift_lo": 1.1702,
        "area_lift_hi": 1.2031,
        "area_spec": 1.3393,
        "area_spec_lo": 1.3195,
        "area_spec_hi": 1.3595,
    },
    {
        "arch": "Transformer",
        "lift": 1.9507,
        "lift_lo": 1.9170,
        "lift_hi": 1.9843,
        "lift_se": 0.0173,
        "spec": 2.0053,
        "spec_lo": 1.9883,
        "spec_hi": 2.0218,
        "spec_se": 0.0086,
        "rank": 0.928,
        "peak_error": 0.082,
        "area_lift": 1.9457,
        "area_lift_lo": 1.9118,
        "area_lift_hi": 1.9793,
        "area_spec": 2.0072,
        "area_spec_lo": 1.9902,
        "area_spec_hi": 2.0236,
    },
]

EXPONENT_ROWS = [
    ("anisotropic 2-D", 0.3089, 0.3040, 0.3136),
    ("stripe", 0.3024, 0.2979, 0.3069),
    ("point", 0.2831, 0.2781, 0.2880),
]

LOC_LIFT = {
    "jepa": {
        (0.25, 0.25): 0.5649,
        (0.25, 0.50): 0.6885,
        (0.25, 0.75): 0.6438,
        (0.50, 0.25): 0.6181,
        (0.50, 0.50): 0.9981,
        (0.50, 0.75): 0.7188,
        (0.75, 0.25): 0.6480,
        (0.75, 0.50): 0.6321,
        (0.75, 0.75): 0.6497,
    },
    "rnn": {
        (0.25, 0.25): 1.2152,
        (0.25, 0.50): 1.2638,
        (0.25, 0.75): 1.2635,
        (0.50, 0.25): 1.1558,
        (0.50, 0.50): 1.1917,
        (0.50, 0.75): 1.1868,
        (0.75, 0.25): 1.1916,
        (0.75, 0.50): 1.1501,
        (0.75, 0.75): 1.1928,
    },
    "transformer": {
        (0.25, 0.25): 1.8336,
        (0.25, 0.50): 1.9277,
        (0.25, 0.75): 1.8591,
        (0.50, 0.25): 1.9340,
        (0.50, 0.50): 2.2167,
        (0.50, 0.75): 2.0214,
        (0.75, 0.25): 1.8368,
        (0.75, 0.50): 1.9952,
        (0.75, 0.75): 1.9321,
    },
}

SEMANTIC_ROWS = [
    {
        "family": "DistilBERT classifier",
        "short": "DistilBERT\nclassifier",
        "lift_u": -0.3982,
        "lift_u_lo": -0.4297,
        "lift_u_hi": -0.3671,
        "lift_u_se": 0.0160,
        "lift_r": -0.3960,
        "lift_r_lo": -0.4263,
        "lift_r_hi": -0.3665,
        "lift_r_se": 0.0152,
        "spec": -0.5309,
        "rank": 0.4729,
        "centroid": 0.3250,
        "purity": 0.3693,
        "erank": 0.5531,
        "f1": -0.0181,
    },
    {
        "family": "DistilBERT JEPA-like",
        "short": "DistilBERT\nJEPA-like",
        "lift_u": -0.3576,
        "lift_u_lo": -0.3887,
        "lift_u_hi": -0.3275,
        "lift_u_se": 0.0154,
        "lift_r": -0.3596,
        "lift_r_lo": -0.3878,
        "lift_r_hi": -0.3318,
        "lift_r_se": 0.0143,
        "spec": -0.4768,
        "rank": 0.4846,
        "centroid": 0.3094,
        "purity": 0.3160,
        "erank": 0.4434,
        "f1": -0.0140,
    },
    {
        "family": "MiniLM classifier",
        "short": "MiniLM\nclassifier",
        "lift_u": -0.5083,
        "lift_u_lo": -0.5336,
        "lift_u_hi": -0.4841,
        "lift_u_se": 0.0128,
        "lift_r": -0.5048,
        "lift_r_lo": -0.5308,
        "lift_r_hi": -0.4798,
        "lift_r_se": 0.0131,
        "spec": -0.6778,
        "rank": 0.4502,
        "centroid": 0.5419,
        "purity": 0.4561,
        "erank": 0.1037,
        "f1": -0.0189,
    },
    {
        "family": "MiniLM JEPA-like",
        "short": "MiniLM\nJEPA-like",
        "lift_u": -0.4989,
        "lift_u_lo": -0.5254,
        "lift_u_hi": -0.4735,
        "lift_u_se": 0.0133,
        "lift_r": -0.5049,
        "lift_r_lo": -0.5309,
        "lift_r_hi": -0.4795,
        "lift_r_se": 0.0129,
        "spec": -0.6652,
        "rank": 0.4524,
        "centroid": 0.5450,
        "purity": 0.4409,
        "erank": 0.1253,
        "f1": -0.0172,
    },
]

SEMANTIC_TARGET_LIFT = {
    "DistilBERT classifier": {
        "comp.graphics": -0.3289,
        "rec.sport.hockey": -0.5031,
        "sci.med": -0.3796,
        "sci.space": -0.3812,
    },
    "DistilBERT JEPA-like": {
        "comp.graphics": -0.3008,
        "rec.sport.hockey": -0.4130,
        "sci.med": -0.3431,
        "sci.space": -0.3735,
    },
    "MiniLM classifier": {
        "comp.graphics": -0.5026,
        "rec.sport.hockey": -0.4421,
        "sci.med": -0.5649,
        "sci.space": -0.5236,
    },
    "MiniLM JEPA-like": {
        "comp.graphics": -0.5080,
        "rec.sport.hockey": -0.4309,
        "sci.med": -0.5504,
        "sci.space": -0.5063,
    },
}


def fig_schematic_fields(path: str) -> str:
    import matplotlib.pyplot as plt
    import numpy as np

    n = 140
    xs = np.linspace(0, 1, n)
    x, y = np.meshgrid(xs, xs, indexing="ij")
    targets = [(0.30, 0.72), (0.74, 0.28)]
    fig, axes = plt.subplots(2, 2, figsize=(6.4, 5.0))
    cmaps = ["magma", "viridis"]
    titles = [
        "A. loss-weight field w(x)",
        "B. learned metric density",
        "C. moved loss-weight field",
        "D. moved metric density",
    ]
    for row, (tx, ty) in enumerate(targets):
        d2 = (x - tx) ** 2 + (y - ty) ** 2
        field = 1.0 + 6.0 * np.exp(-d2 / (2 * 0.12**2))
        ripple = 0.10 * np.sin(4 * np.pi * x) * np.cos(4 * np.pi * y)
        metric = 0.65 + 0.90 * np.exp(-d2 / (2 * 0.15**2)) + ripple
        for col, arr in enumerate([field, metric]):
            ax = axes[row, col]
            im = ax.imshow(arr.T, origin="lower", extent=[0, 1, 0, 1], cmap=cmaps[col])
            ax.contour(x, y, arr, levels=7, colors="white", linewidths=0.45, alpha=0.55)
            ax.scatter([tx], [ty], s=90, marker="*", color="#f8f9fa", edgecolor="#111", linewidth=0.7, zorder=4)
            ax.set_title(titles[row * 2 + col], fontsize=9.5, weight="bold")
            ax.set_xticks([0, 0.5, 1])
            ax.set_yticks([0, 0.5, 1])
            ax.tick_params(labelsize=7)
            for spine in ax.spines.values():
                spine.set_linewidth(0.8)
                spine.set_edgecolor("#2f3437")
            fig.colorbar(im, ax=ax, fraction=0.046, pad=0.02)
    fig.suptitle("Schematic intervention: move the priority field, test whether metric density moves", fontsize=11, weight="bold")
    fig.savefig(path, bbox_inches="tight", facecolor="white", dpi=230)
    plt.close(fig)
    return path


def fig_location_map(path: str) -> str:
    import matplotlib.pyplot as plt
    import matplotlib.patheffects as pe
    import numpy as np

    arch_order = ["jepa", "rnn", "transformer"]
    labels = ["JEPA", "RNN", "Transformer"]
    fig, axes = plt.subplots(1, 3, figsize=(6.6, 2.65), constrained_layout=True)
    vmax = 2.25
    for ax, arch, label in zip(axes, arch_order, labels):
        mat = np.zeros((3, 3))
        for i, x in enumerate([0.25, 0.50, 0.75]):
            for j, y in enumerate([0.25, 0.50, 0.75]):
                mat[j, i] = LOC_LIFT[arch][(x, y)]
        im = ax.imshow(mat, origin="lower", cmap="viridis", vmin=0, vmax=vmax)
        ax.set_title(label, fontsize=9.5, weight="bold")
        ax.set_xticks([0, 1, 2])
        ax.set_yticks([0, 1, 2])
        ax.set_xticklabels([".25", ".50", ".75"], fontsize=7)
        ax.set_yticklabels([".25", ".50", ".75"], fontsize=7)
        ax.set_xlabel("x", fontsize=7)
        if ax is axes[0]:
            ax.set_ylabel("y", fontsize=7)
        for i in range(3):
            for j in range(3):
                val = mat[j, i]
                ax.text(i, j, f"{val:.2f}", ha="center", va="center",
                        fontsize=7.4, color="white", weight="bold",
                        path_effects=[pe.withStroke(linewidth=1.4, foreground="#111")])
        ax.set_xticks(np.arange(-.5, 3, 1), minor=True)
        ax.set_yticks(np.arange(-.5, 3, 1), minor=True)
        ax.grid(which="minor", color="white", linewidth=1.0)
        ax.tick_params(which="minor", bottom=False, left=False)
    cbar = fig.colorbar(im, ax=axes, shrink=0.82, pad=0.02)
    cbar.set_label("control-subtracted lift z", fontsize=8)
    fig.suptitle("Registered moved-location lift across all nine concern targets", fontsize=11, weight="bold")
    fig.savefig(path, bbox_inches="tight", facecolor="white", dpi=230)
    plt.close(fig)
    return path


def fig_arch_forest(path: str) -> str:
    import matplotlib.pyplot as plt
    import numpy as np

    labels = []
    vals = []
    lows = []
    highs = []
    colors = []
    for row in ARCH_ROWS:
        labels.extend([f"{row['arch']} lift", f"{row['arch']} specificity"])
        vals.extend([row["lift"], row["spec"]])
        lows.extend([row["lift_lo"], row["spec_lo"]])
        highs.extend([row["lift_hi"], row["spec_hi"]])
        colors.extend(["#2b6cb0", "#2f9e44"])

    y = np.arange(len(labels))[::-1]
    xerr = [[v - lo for v, lo in zip(vals, lows)], [hi - v for v, hi in zip(vals, highs)]]
    fig, ax = plt.subplots(figsize=(6.6, 3.7))
    ax.errorbar(vals, y, xerr=xerr, fmt="none", ecolor="#1f2933", capsize=3, lw=1.0)
    ax.scatter(vals, y, s=54, c=colors, edgecolor="#1f2933", linewidth=0.5, zorder=3)
    ax.axvline(0, color="#444", lw=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlim(0, 2.16)
    ax.set_xlabel("z-scored neighbor-stretch metric-density effect")
    ax.set_title("Moved concern increases metric density at the moved target")
    ax.grid(axis="y", visible=False)
    for x, yy in zip(vals, y):
        ax.text(x + 0.035, yy, f"{x:.2f}", va="center", fontsize=7.6, color="#222")
    fig.savefig(path, bbox_inches="tight", facecolor="white", dpi=230)
    plt.close(fig)
    return path


def fig_gate_audit(path: str) -> str:
    import matplotlib.pyplot as plt
    import numpy as np

    cols = ["lift CI>0", "spec CI>0", "rank>.5", "2% SE", "1% SE"]
    mat = []
    for row in ARCH_ROWS:
        mat.append([
            row["lift_lo"] > 0,
            row["spec_lo"] > 0,
            row["rank"] > 0.5,
            row["lift_se"] <= 0.02 and row["spec_se"] <= 0.02,
            row["lift_se"] <= 0.01 and row["spec_se"] <= 0.01,
        ])
    arr = np.array(mat, dtype=float)
    fig, ax = plt.subplots(figsize=(6.3, 2.45))
    ax.imshow(arr, cmap=plt.matplotlib.colors.ListedColormap(["#c0392b", "#2f9e44"]), vmin=0, vmax=1)
    ax.set_xticks(range(len(cols)))
    ax.set_xticklabels(cols, rotation=22, ha="right")
    ax.set_yticks(range(len(ARCH_ROWS)))
    ax.set_yticklabels([r["arch"] for r in ARCH_ROWS])
    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            ax.text(j, i, "met" if arr[i, j] else "not met", ha="center", va="center",
                    color="white", fontsize=8, weight="bold")
    ax.tick_params(length=0)
    ax.set_title("Gate audit: 2% report threshold met; frozen 1% audit not met")
    fig.savefig(path, bbox_inches="tight", facecolor="white", dpi=230)
    plt.close(fig)
    return path


def fig_area_companion(path: str) -> str:
    import matplotlib.pyplot as plt
    import numpy as np

    x = np.arange(len(ARCH_ROWS))
    width = 0.34
    primary = [r["lift"] for r in ARCH_ROWS]
    area = [r["area_lift"] for r in ARCH_ROWS]
    primary_err = [[r["lift"] - r["lift_lo"] for r in ARCH_ROWS],
                   [r["lift_hi"] - r["lift"] for r in ARCH_ROWS]]
    area_err = [[r["area_lift"] - r["area_lift_lo"] for r in ARCH_ROWS],
                [r["area_lift_hi"] - r["area_lift"] for r in ARCH_ROWS]]
    fig, ax = plt.subplots(figsize=(6.3, 3.25))
    ax.bar(x - width / 2, primary, width, yerr=primary_err, capsize=3,
           label="neighbor-stretch primary", color="#2b6cb0")
    ax.bar(x + width / 2, area, width, yerr=area_err, capsize=3,
           label="area-density companion", color="#e8a13a")
    ax.axhline(0, color="#444", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels([r["arch"] for r in ARCH_ROWS])
    ax.set_ylabel("control-subtracted lift z")
    ax.set_title("The primary metric generalizes; area density is architecture-sensitive")
    ax.legend(fontsize=7.6)
    ax.grid(axis="x", visible=False)
    fig.savefig(path, bbox_inches="tight", facecolor="white", dpi=230)
    plt.close(fig)
    return path


def fig_exponent_gate(path: str) -> str:
    import matplotlib.pyplot as plt
    import numpy as np

    labels = [r[0] for r in EXPONENT_ROWS]
    vals = [r[1] for r in EXPONENT_ROWS]
    lows = [r[2] for r in EXPONENT_ROWS]
    highs = [r[3] for r in EXPONENT_ROWS]
    x = np.arange(len(labels))
    yerr = [[v - l for v, l in zip(vals, lows)], [h - v for v, h in zip(vals, highs)]]
    fig, ax = plt.subplots(figsize=(5.8, 3.2))
    ax.errorbar(x, vals, yerr=yerr, fmt="o", ms=8, capsize=4, color="#2b6cb0")
    ax.axhline(1 / 3, color="#444", ls="--", lw=1.0, label="1-D prediction 1/3")
    ax.axhline(0.5, color="#c0392b", ls=":", lw=1.2, label="2-D prediction 1/2")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0.25, 0.53)
    ax.set_ylabel("area-density exponent alpha at A=6")
    ax.set_title("Effective-dimension audit: 1/2 is not observed")
    ax.legend(fontsize=7.5)
    ax.grid(axis="x", visible=False)
    fig.savefig(path, bbox_inches="tight", facecolor="white", dpi=230)
    plt.close(fig)
    return path


def fig_semantic_gate(path: str) -> str:
    import matplotlib.pyplot as plt
    import numpy as np

    labels = []
    vals = []
    lows = []
    highs = []
    colors = []
    for row in SEMANTIC_ROWS:
        labels.extend([f"{row['family']} vs uniform", f"{row['family']} vs random"])
        vals.extend([row["lift_u"], row["lift_r"]])
        lows.extend([row["lift_u_lo"], row["lift_r_lo"]])
        highs.extend([row["lift_u_hi"], row["lift_r_hi"]])
        colors.extend(["#b23a48", "#7b2cbf"])
    y = np.arange(len(labels))[::-1]
    xerr = [[v - lo for v, lo in zip(vals, lows)], [hi - v for v, hi in zip(vals, highs)]]
    fig, ax = plt.subplots(figsize=(6.6, 4.25))
    ax.errorbar(vals, y, xerr=xerr, fmt="none", ecolor="#1f2933", lw=0.9, capsize=3)
    ax.scatter(vals, y, s=48, c=colors, edgecolor="#1f2933", linewidth=0.5, zorder=3)
    ax.axvline(0, color="#111", lw=0.9)
    ax.axvspan(-0.58, 0, color="#f7d9dd", alpha=0.45, zorder=0)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=7.2)
    ax.set_xlim(-0.58, 0.06)
    ax.set_xlabel("semantic-margin lift z")
    ax.set_title("Appendix gate: naive semantic transport is negative")
    for x, yy in zip(vals, y):
        ax.text(x - 0.018, yy, f"{x:.2f}", ha="right", va="center", fontsize=7.2)
    ax.grid(axis="y", visible=False)
    fig.savefig(path, bbox_inches="tight", facecolor="white", dpi=230)
    plt.close(fig)
    return path


def fig_semantic_split(path: str) -> str:
    import matplotlib.pyplot as plt
    import numpy as np

    labels = [r["short"] for r in SEMANTIC_ROWS]
    x = np.arange(len(labels))
    width = 0.19
    series = [
        ("margin gate", [r["lift_u"] for r in SEMANTIC_ROWS], "#b23a48"),
        ("centroid", [r["centroid"] for r in SEMANTIC_ROWS], "#2b6cb0"),
        ("kNN purity", [r["purity"] for r in SEMANTIC_ROWS], "#2f9e44"),
        ("eff. rank", [r["erank"] for r in SEMANTIC_ROWS], "#e8a13a"),
    ]
    fig, ax = plt.subplots(figsize=(6.5, 3.9))
    for i, (name, vals, color) in enumerate(series):
        ax.bar(x + (i - 1.5) * width, vals, width, label=name, color=color)
    ax.axhline(0, color="#111", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=7.5)
    ax.set_ylabel("z-lift vs uniform")
    ax.set_title("Geometry changes, but not as local margin-density transport")
    ax.legend(fontsize=7.3, ncol=4, loc="lower center", bbox_to_anchor=(0.5, -0.31))
    ax.grid(axis="x", visible=False)
    fig.subplots_adjust(bottom=0.26)
    fig.savefig(path, bbox_inches="tight", facecolor="white", dpi=230)
    plt.close(fig)
    return path


def fig_semantic_target_heatmap(path: str) -> str:
    import matplotlib.pyplot as plt
    import numpy as np

    families = [r["family"] for r in SEMANTIC_ROWS]
    targets = ["comp.graphics", "rec.sport.hockey", "sci.med", "sci.space"]
    mat = np.array([[SEMANTIC_TARGET_LIFT[f][t] for t in targets] for f in families])
    fig, ax = plt.subplots(figsize=(6.2, 2.75))
    im = ax.imshow(mat, cmap="RdBu_r", vmin=-0.65, vmax=0.65, aspect="auto")
    ax.set_yticks(range(len(families)))
    ax.set_yticklabels(families, fontsize=7.1)
    ax.set_xticks(range(len(targets)))
    ax.set_xticklabels(targets, rotation=18, ha="right", fontsize=7.1)
    ax.set_title("Per-target semantic audit: no class carries a positive primary lift")
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            ax.text(j, i, f"{mat[i, j]:.2f}", ha="center", va="center", fontsize=7.0, color="#111")
    cbar = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cbar.set_label("lift vs uniform", fontsize=7.2)
    fig.savefig(path, bbox_inches="tight", facecolor="white", dpi=230)
    plt.close(fig)
    return path


def build() -> None:
    Path(FIG).mkdir(parents=True, exist_ok=True)
    f_schema = fig_schematic_fields(f"{FIG}/fig0_schematic_fields.png")
    f_loc = fig_location_map(f"{FIG}/fig1_location_map.png")
    f_forest = fig_arch_forest(f"{FIG}/fig1_moved_location_forest.png")
    f_gate = fig_gate_audit(f"{FIG}/fig2_gate_audit.png")
    f_area = fig_area_companion(f"{FIG}/fig3_area_companion.png")
    f_exp = fig_exponent_gate(f"{FIG}/fig4_exponent_gate.png")
    f_sem_gate = fig_semantic_gate(f"{FIG}/figA1_semantic_gate.png")
    f_sem_heat = fig_semantic_target_heatmap(f"{FIG}/figA2_semantic_targets.png")
    f_sem_split = fig_semantic_split(f"{FIG}/figA3_semantic_split.png")

    p = pk.Paper(OUT, FIG)
    p.title("Value-Weighted Training Deforms Learned Metrics Across RNN, Transformer, and JEPA-Style Spatial Models")
    p.authors("Jawaun Brown")
    p.authors("Research-Derived Experiments · Paper B")
    p.rule()
    formula_style = p.s_small.clone("formula")
    formula_style.alignment = 0
    formula_style.fontName = "Courier"
    formula_style.leftIndent = 14
    formula_style.rightIndent = 14
    formula_style.spaceAfter = 4
    p.abstract(
        "If a representation is used to act, valuable regions should not merely receive labels; they "
        "should receive resolution. This paper tests a bounded version of that claim by injecting a "
        "movable loss-weight field, called concern here only as operational shorthand, into a "
        "path-integration task and asking whether the learned representational metric moves with it. "
        "A Modal H200/H100 sweep trains 1,920 finite-capacity spatial models: three architecture "
        "families (RNN, causal Transformer, and JEPA-style predictive latent model), 64 seeds per "
        "family, nine registered concern locations, and matched uniform controls. The primary "
        "observable is neighbor-stretch metric density, the mean latent displacement induced by a "
        "unit physical displacement. Under a 2% bootstrap-SE report threshold, all three architectures "
        "show positive moved-location lift and specificity: JEPA lift +0.685 [0.648,0.723], specificity "
        "+0.916 [0.889,0.943]; RNN lift +1.201 [1.185,1.218], specificity +1.357 [1.337,1.377]; "
        "Transformer lift +1.951 [1.917,1.984], specificity +2.005 [1.988,2.022]. The frozen stricter "
        "1% precision audit is retained and is not claimed to meet. A companion rate-distortion sweep "
        "falsifies the hoped-for 2-D exponent alpha=1/2 and instead measures an effective allocation "
        "dimension near one. The bounded conclusion is therefore: within this synthetic spatial setup, "
        "moving an externally specified priority field reliably moves local representational metric "
        "density across model families, while the scaling law reveals an architecture-dependent "
        "capacity bottleneck. A pretrained text-encoder boundary check fails to reproduce the effect "
        "under a semantic-margin metric, so we present the result as a controlled spatial mechanism "
        "rather than a claim about foundation-model generality.")

    p.h1("1. Claim and Definitions")
    p.para(
        "A learned code r(x) induces a metric on the task space: nearby inputs x and x+dx are far "
        "apart in representation when r(x) changes rapidly. Formally, if J is the Jacobian of the "
        "code, the pullback metric is J(x)^T J(x). In plain terms, high metric density means the "
        "model has allocated more representational resolution to that part of the world.")
    p.para(
        "Here <b>concern</b> has a narrow operational meaning: a scalar priority field w(x) in the "
        "training loss, w(x)=1+A exp(-||x-c||^2/(2 sigma^2)). It is equivalent to a loss-weight, "
        "cost, or value field that says errors near c matter more. The experiment asks whether "
        "moving c moves the representational metric. The primary observable is neighbor-stretch "
        "density, the average latent displacement per unit physical displacement. Area density, "
        "sqrt(det J^T J), is reported separately as a rate-distortion companion but is not substituted "
        "for the original moved-location claim.")
    p.table(
        [[
            "Scope boundary",
            Paragraph(
                "This paper does not claim consciousness, subjective concern, biological realism, or "
                "foundation-model generality. Concern denotes only an externally specified loss-weight, "
                "cost, or priority field inside this controlled training task.",
                p.s_small,
            ),
        ]],
        header=False,
        col_widths=[88, 360],
    )
    p.figure(f_schema, "Figure 1. Schematic only, not raw data: the intervention is a movable loss-weight field, and the interventional question is whether the learned metric-density peak follows that field. The measured statistics below test this with matched controls and nine registered target locations.", width_in=6.0)

    p.h1("2. Formal Prediction")
    p.para(
        "<b>Idealized theorem (weighted finite-capacity allocation).</b> In a high-resolution local "
        "rate-distortion approximation, suppose a d-dimensional task variable x is encoded with "
        "local representational density rho(x), weighted distortion L[rho]=int w(x)D(x) dx, and fixed "
        "capacity int rho(x) dx=C. If local distortion scales as D(x)=K rho(x)^(-2/d), the minimizing "
        "allocation obeys rho*(x) proportional to w(x)^{d/(d+2)}. Therefore, for a translated priority "
        "field w_c(x)=w_0(x-c), the ideal density rho*_c(x) translates with c.")
    p.para(
        "<b>Proof sketch.</b> Minimize int K w(x) rho(x)^(-2/d) dx + lambda int rho(x) dx. The "
        "Euler-Lagrange first-order condition gives rho(x)^(-(d+2)/d) proportional to 1/w(x), hence "
        "rho*(x) proportional to w(x)^{d/(d+2)} after normalization by the capacity constraint. "
        "Translation equivariance follows because the objective and constraint contain no fixed "
        "location other than the translated field.")
    p.para(
        "This theorem is an idealized target, not the empirical conclusion. The moved-location "
        "sweep tests whether trained finite networks show the translated-density corollary in their "
        "learned neighbor-stretch metric, while the companion exponent sweep asks whether the "
        "measured power law matches the nominal d=2 prediction or a lower effective dimension.")

    p.h1("3. Positioning Against Prior Work")
    p.h2("Efficient Coding and Rate-Distortion")
    p.para(
        "Efficient coding and high-resolution rate-distortion theory (Bennett; Gersho and Gray; "
        "Cover and Thomas; Ganguli and Simoncelli; Wei and Stocker) explain why finite codes should "
        "allocate more resolution where errors are frequent or costly. This paper tests that allocation "
        "logic with an externally moved cost field rather than a post-hoc salience measure.")
    p.h2("Learned Metrics and Representation Geometry")
    p.para(
        "Information geometry, latent-space Riemannian metrics, and representational similarity analysis "
        "(Amari; Kriegeskorte et al.; Arvanitidis et al.; Kornblith et al.) supply the language of an "
        "induced metric. The primary statistic here is deliberately local: the latent displacement "
        "caused by a fixed physical displacement near a registered target.")
    p.h2("Spatial Codes and Value-Dependent Remapping")
    p.para(
        "Grid-cell RNN work (Cueva and Wei; Banino et al.; Sorscher et al.) provides a tractable spatial "
        "substrate where metric density can be measured. Goal-dependent remapping and elastic spatial-code "
        "deformation (Ocko et al.; Boccara et al.; Butler et al.) motivate the possibility that value can "
        "reshape spatial codes.")
    p.h2("Contribution")
    p.para(
        "The contribution here is the direct moved-location intervention: a known external priority "
        "field is moved before training, and the induced metric is tested at the moved target against "
        "matched controls and unrewarded registered locations.")
    p.para(
        "This positioning bounds the claim. The experiment is synthetic and spatial. The RNN, Transformer, "
        "and JEPA variants show that the mechanism is not idiosyncratic to one recurrent cell, but they "
        "do not establish generality to production language models or open-world agents. For peer review, "
        "the result should be read as a controlled representational-geometry finding with clear next "
        "baselines, not as a claim of generality beyond this setting.")

    p.h1("4. Experiment and Estimators")
    p.para(
        "Each model performs 2-D path integration. It receives velocity sequences and predicts a "
        "place-cell-like code over a square arena. For each seed and architecture, we train one "
        "matched uniform-control model and one concern-weighted model for each of nine registered "
        "locations on a 3x3 grid. All models use a finite-capacity normalized latent state and noisy "
        "readout. The confirmatory architecture set is: an RNN path-integration baseline, a causal "
        "Transformer over velocity tokens, and a JEPA-style model that predicts future latent states "
        "against a stop-gradient target encoder.")
    p.para(
        "Task generation is identical across concern and control conditions. The arena is [0,1]^2 "
        "with reflective boundaries. Initial position is sampled uniformly from [0.1,0.9]^2; heading "
        "is initialized uniformly, updated by Gaussian angular noise with standard deviation 0.4, and "
        "advanced with speed 0.06 for T=20 steps. Place-cell targets use a 16x16 grid of centers "
        "(Np=256) and a softmax-normalized Gaussian field with sigma_p=0.09.")
    p.para(
        "The concern intervention changes only the loss weight, not trajectory sampling. For target "
        "location c, w_c(x)=1+6 exp(-||x-c||^2/(2*0.12^2)); for each batch the weights are divided "
        "by their batch mean before multiplying the KL loss. Thus the intervention reallocates gradient "
        "pressure spatially without changing the global loss scale. Models train for 4,000 AdamW steps "
        "with learning rate 1e-3, weight decay 1e-4, batch size 128, latent dimension Ng=256, L2-normalized "
        "latent states, and readout noise standard deviation 0.15. Evaluation uses 1,024 trajectories.")
    p.para(
        "Architecture details are fixed across the sweep. The RNN encodes the initial place code to "
        "Ng and updates a ReLU RNNCell from velocity. The Transformer uses velocity and initial-place "
        "projections, learned positional embeddings, two causal Transformer encoder layers, four heads, "
        "GELU activations, no dropout, and feed-forward width 4Ng. The JEPA-style model uses an MLP "
        "place encoder and an MLP latent predictor conditioned on velocity; an auxiliary stop-gradient "
        "target-latent loss is added with weight 0.5.")
    p.h2("Metric Definitions")
    p.para(
        "For evaluation, latent states r(x) are averaged into a 16x16 spatial grid. At each interior "
        "grid cell, let N={+e_x,-e_x,+e_y,-e_y} be the one-step spatial neighbors with spacing dx. "
        "The finite-difference neighbor-stretch estimand is:")
    p.flow.append(Paragraph("s(x) = |N|^-1 sum_{delta in N} ||r(x+delta)-r(x)||_2 / ||delta||_2", formula_style))
    p.para(
        "In code this is the central-difference equivalent, with du and dv estimated from the two "
        "coordinate axes:")
    p.flow.append(Paragraph("du=(r_{i+1,j}-r_{i-1,j})/(2dx),  dv=(r_{i,j+1}-r_{i,j-1})/(2dx)", formula_style))
    p.flow.append(Paragraph("s(x)=0.5(||du||_2+||dv||_2)", formula_style))
    p.flow.append(Paragraph("a(x)=sqrt(max(0, ||du||^2 ||dv||^2 - (du dot dv)^2))", formula_style))
    p.para(
        "All primary statistics use the log neighbor-stretch field z-scored over finite spatial bins: "
        "z_s(x)=(log s(x)-mean_x log s(x))/sd_x(log s(x)), computed within each model over finite "
        "interior bins. The target statistic Z_m(c) is the mean z_s over a radius-2 bin neighborhood "
        "around the registered location c in model m:")
    p.flow.append(Paragraph("Delta_lift = Z_reward(c) - Z_control(c)", formula_style))
    p.flow.append(Paragraph("Delta_spec = Z_reward(c) - mean_{c' != c} Z_reward(c')", formula_style))
    p.para(
        "The control is the seed-matched uniform-loss model evaluated at the same location. The "
        "specificity mean ranges over the other eight registered locations in the same trained "
        "concern model.")
    p.para(
        "The built-in negative controls are important. Lift subtracts a seed-matched uniform-control "
        "model at the same location. Specificity compares the rewarded location with the other eight "
        "registered locations inside the same trained model. A result therefore cannot meet the criterion merely by "
        "making the whole representation high-resolution, by favoring the arena center, or by exploiting "
        "one fixed probe location.")
    p.h2("Statistics")
    p.para(
        "The nine concern targets are fixed registered probes at coordinates {0.25,0.50,0.75}^2. "
        "Architecture-level intervals use 5,000 bootstrap resamples over the seed x registered-location "
        "paired row as the resampling unit: 64 seeds x 9 locations = 576 reward-control pairs per "
        "architecture after matched subtraction. The architecture-balanced pooled estimate resamples "
        "rows within each architecture, computes one mean per architecture, and averages those three "
        "means. Reported SE is the bootstrap standard deviation; intervals are percentile 95% intervals.")
    p.h2("Reviewer-Facing Controls")
    p.table(
        [
            ["Control", "What it rules out"],
            [
                "Loss-scale",
                Paragraph(
                    "Concern weights are divided by their batch mean before multiplying the KL loss, "
                    "so the intervention redistributes gradient pressure rather than increasing the "
                    "global objective scale.",
                    p.s_small,
                ),
            ],
            [
                "Visitation",
                Paragraph(
                    "The trajectory sampler is independent of c and identical for concern and control "
                    "conditions. There is no learned policy whose state visitation can chase the weighted "
                    "region.",
                    p.s_small,
                ),
            ],
            [
                "Location",
                Paragraph(
                    "All nine registered targets are tested. Figure 2 shows positive lift across the "
                    "3x3 grid, while specificity compares the target against the other eight locations "
                    "inside the same model.",
                    p.s_small,
                ),
            ],
            [
                "Localization",
                Paragraph(
                    "Reward-rank percentiles are above chance for all architectures, and mean peak error "
                    "is 0.205 (JEPA), 0.069 (RNN), and 0.082 (Transformer), so the measured metric field "
                    "is spatially localized rather than a uniform expansion.",
                    p.s_small,
                ),
            ],
        ],
        caption="Table 1. Main spatial controls available from the committed aggregate rows and runner design.",
        col_widths=[88, 360],
    )
    p.figure(f_loc, "Figure 2. Data-backed target map. Each cell is the mean control-subtracted lift when the concern field is centered at that registered location. Positive lift appears across the whole 3x3 grid, not only at one convenient target.", width_in=6.2)
    p.figure(f_forest, "Figure 3. Primary moved-location result. Lift is the rewarded-location metric z-score minus the matched uniform-control z-score. Specificity is the rewarded-location z-score minus unrewarded registered locations in the same model. Error bars are bootstrap 95% intervals.", width_in=6.2)
    p.figure(f_gate, "Figure 4. Gate audit. The 2% report threshold is met for all three architectures; the originally frozen 1% precision audit is not met. This distinction is retained in the report and should remain in any submission.", width_in=5.8)

    p.h1("5. Results")
    p.table(
        [["Architecture", "lift z (95% CI)", "SE", "specificity z (95% CI)", "SE", "rank", "2% report"],
         ["JEPA", "+0.685 [0.648,0.723]", "0.019", "+0.916 [0.889,0.943]", "0.014", "0.832", "met"],
         ["RNN", "+1.201 [1.185,1.218]", "0.009", "+1.357 [1.337,1.377]", "0.010", "0.930", "met"],
         ["Transformer", "+1.951 [1.917,1.984]", "0.017", "+2.005 [1.988,2.022]", "0.009", "0.928", "met"]],
        caption="Table 2. Primary moved-location metric-deformation summary, 64 seeds per architecture and nine registered concern locations. All intervals exclude zero by a wide margin.",
        col_widths=[78, 106, 35, 126, 35, 42, 48])
    p.para(
        "The architecture-balanced pooled lift is +1.279 with bootstrap SE 0.009; pooled specificity "
        "is +1.426 with SE 0.006. Thus the pooled cross-architecture estimate is already below the "
        "original 1% precision target, while the per-architecture 1% audit remains failed for at least "
        "one metric in every architecture. The report therefore treats the moved-location effect as "
        "positive and stable under the revised 2% report threshold and keeps the stricter 1% audit "
        "as a visible non-passing precision check.")

    p.h1("6. Companion Rate-Distortion Result")
    p.figure(f_area, "Figure 5. Companion area-density diagnostic. JEPA's area-density lift is positive but smaller; the cross-architecture claim is the neighbor-stretch metric.", width_in=5.05)
    p.figure(f_exp, "Figure 6. The separate exponent sweep rejects the desired 2-D rate-distortion exponent. All primary A=6 geometries cluster near the one-dimensional family rather than alpha=1/2.", width_in=5.2)
    p.para(
        "The rate-distortion derivation predicts sqrt(det g(x)) proportional to w(x)^{d/(d+2)} under "
        "a finite-capacity constraint, giving alpha=1/2 for a full 2-D allocation and alpha=1/3 for "
        "an effectively 1-D allocation. The large Modal exponent sweep does not confirm the 2-D law: "
        "anisotropic 2-D gives alpha=0.309 [0.304,0.314], stripe gives 0.302 [0.298,0.307], and point "
        "reward gives 0.283 [0.278,0.288]. This is a precise negative result for the hoped-for "
        "2-D rate-distortion account and a positive measurement of an effective-dimension bottleneck.")

    p.flow.append(PageBreak())
    p.h1("7. Interpretation")
    p.para(
        "The core scientific value is non-circularity. The concern field is specified externally "
        "before training rather than inferred from the trained representation. When that field moves, "
        "the metric deformation moves with it. That is stronger than discovering a salient region "
        "after the representation is trained. It supports the narrower claim that a value-like "
        "training signal can allocate local resolution in the geometry of the learned code.")
    p.para(
        "The result should still be framed as a spatial mechanism result. It establishes a "
        "reproducible representational effect in artificial spatial learners: value-weighted "
        "prediction reshapes the induced metric. The natural next tests are language and vision "
        "analogues, where the concern field is semantic or task-value weighted rather than spatial.")
    p.para(
        "Appendix A reports one such boundary check in pretrained text encoders. It is intentionally "
        "secondary: a naive class-upweighting analogue changes semantic geometry, but it fails the "
        "registered local semantic-margin transport gate and lowers target F1. This supports the "
        "bounded reading rather than broadening the claim.")
    p.para(
        "The strongest future baseline is a non-spatial analogue in a real transformer: for example, "
        "upweight a controlled semantic region, syntactic construction, or retrieval-relevant document "
        "cluster, then test whether local representation geometry changes specifically there while "
        "matched controls do not. That would convert this paper from a spatial mechanism result into "
        "a broader AI-systems result.")

    p.h1("8. Code and Data Availability")
    p.para(
        "Code, preregistration text, aggregate result reports, and the PDF builder are available at "
        "https://github.com/jawauntb/research-derived-experiments. The relevant audit trail is the "
        "Paper B moved-location preregistration, the Modal runner, the 2026-07-02 aggregate result "
        "report, and scripts/build_paperB_pdf.py. Committed per-row aggregate CSV snapshots in "
        "data/paper_b/ reproduce the reported spatial and semantic bootstrap summaries with "
        "python scripts/reproduce_paperB_stats.py. Raw Modal JSON and worker logs remain gitignored "
        "under the repository artifact policy, but the paper's aggregate statistics no longer require "
        "rerunning the full Modal sweep.")

    p.h1("9. Limitations")
    p.para(
        "The 2% report threshold was accepted after the first-wave results were visible; the frozen "
        "1% audit is therefore retained rather than rewritten. The task is synthetic path integration. "
        "The JEPA area-density companion is positive but much smaller than the stretch result. The "
        "Transformer and JEPA variants are architecture-family probes, not claims about production "
        "foundation models. The result is scoped to controlled spatial learners rather than language, "
        "vision, or open-world systems, and it does not establish consciousness, subjective concern, "
        "agency, or biological realism. Capacity/noise ablations beyond the fixed Ng=256 and readout-noise "
        "setting are the next robustness layer, not part of the current confirmatory claim.")

    p.flow.append(PageBreak())
    p.h1("Appendix A. Semantic Transformer Boundary Check")
    p.para(
        "This appendix tests the most direct non-spatial analogue without making it the paper's main "
        "story. The target is one of four 20 Newsgroups classes: comp.graphics, rec.sport.hockey, "
        "sci.med, and sci.space. The intervention upweights the training loss for one registered class, "
        "moves which class receives that weight, and compares against both uniform and random-matched "
        "weighting controls.")
    p.para(
        "The pre-registered primary metric is local semantic margin in the learned latent: mean "
        "k-nearest different-class cosine distance minus mean k-nearest same-class cosine distance, "
        "z-scored across classes inside the same model. The run used pretrained DistilBERT and "
        "all-MiniLM-L6-v2 encoders, classifier and JEPA-like predictive latent objectives, two "
        "128-seed Modal waves for 256 seeds per family, and the same 2% standard-error report rule.")
    p.figure(
        f_sem_gate,
        "Figure A1. Primary semantic boundary check. Every pretrained text family moves opposite "
        "the registered semantic-margin prediction, against both uniform and random-matched controls. "
        "Error bars are bootstrap 95% intervals over seed-target effects.",
        width_in=6.0,
    )
    p.table(
        [
            ["Family", "lift vs uniform", "SE", "lift vs random", "SE", "rank", "gate"],
            ["DistilBERT classifier", "-0.398 [-0.430,-0.367]", "0.016", "-0.396 [-0.426,-0.366]", "0.015", "0.473", "not met"],
            ["DistilBERT JEPA-like", "-0.358 [-0.389,-0.327]", "0.015", "-0.360 [-0.388,-0.332]", "0.014", "0.485", "not met"],
            ["MiniLM classifier", "-0.508 [-0.534,-0.484]", "0.013", "-0.505 [-0.531,-0.480]", "0.013", "0.450", "not met"],
            ["MiniLM JEPA-like", "-0.499 [-0.525,-0.474]", "0.013", "-0.505 [-0.531,-0.480]", "0.013", "0.452", "not met"],
        ],
        caption="Table A1. Confirmatory semantic gate. All primary standard errors are below 2%, but every primary sign is negative.",
        col_widths=[116, 105, 34, 105, 34, 38, 45],
    )
    p.para(
        "The architecture-balanced primary effect is -0.441 vs uniform with SE 0.007 and -0.441 vs "
        "random-matched controls with SE 0.007. The real-dataset requirement is met; the semantic "
        "margin transport gate is not. This is a boundary condition, not an underpowered null.")
    p.figure(
        f_sem_heat,
        "Figure A2. Per-target audit. No registered semantic class carries a positive primary lift, "
        "so the failed gate is not caused by one difficult topic.",
        width_in=5.55,
    )
    p.figure(
        f_sem_split,
        "Figure A3. Companion probes reveal non-null geometry. Upweighting increases centroid "
        "separation and kNN purity, and often effective rank, even while the registered local "
        "semantic-margin gate becomes negative.",
        width_in=5.9,
    )
    p.para(
        "The semantic result therefore narrows rather than weakens the main paper. It does not say "
        "that semantic loss weighting leaves transformer geometry unchanged. It says the naive "
        "class-upweighting analogue in pretrained text encoders is closer to class-level re-centering "
        "or cluster sharpening, with slightly lower target F1, than to the local spatial "
        "metric-density transport confirmed in the main experiment.")

    p.h1("Appendix B. Spatial Methods and Reproducibility")
    p.h2("Task Dynamics")
    p.para(
        "The spatial task is 2-D path integration in [0,1]^2 with reflective boundaries. Initial "
        "positions are sampled uniformly from [0.1,0.9]^2, headings uniformly from [0,2pi), and "
        "headings are updated each step by Gaussian angular noise with standard deviation 0.4. The "
        "agent advances at speed 0.06 for T=20 steps. Targets are softmax-normalized Gaussian place "
        "codes over a 16x16 grid with sigma_p=0.09.")
    p.h2("Loss, Normalization, and Training")
    p.para(
        "The loss is KL divergence to the place-code target, multiplied by w_c(x)=1+6 exp(-||x-c||^2/"
        "(2*0.12^2)) for the concern condition. Each batch's weights are divided by their batch mean "
        "before the KL multiplication. Uniform controls set w=1 and are matched by architecture, seed, "
        "and registered evaluation location. All models use Ng=256 latent units, L2-normalized latent "
        "states, readout noise standard deviation 0.15, AdamW with learning rate 1e-3 and weight decay "
        "1e-4, batch size 128, 4,000 training steps, and 1,024 evaluation trajectories.")
    p.h2("Architecture Table")
    p.table(
        [
            ["Family", "Architecture details"],
            ["RNN", Paragraph("Initial place-code projection to Ng, ReLU RNNCell update from velocity, linear noisy place readout.", p.s_small)],
            ["Transformer", Paragraph("Velocity and initial-place projections, learned positional embeddings, two causal Transformer encoder layers, four heads, GELU activations, no dropout, and feed-forward width 4Ng.", p.s_small)],
            ["JEPA-style", Paragraph("MLP place encoder, MLP latent predictor conditioned on velocity, stop-gradient target encoder, and auxiliary target-latent loss with weight 0.5.", p.s_small)],
        ],
        caption="Table B1. Spatial model families used in the confirmatory sweep.",
        col_widths=[80, 370],
    )
    p.h2("Estimator and Bootstrap")
    p.para(
        "The latent metric estimator averages latent states into a 16x16 grid, computes central "
        "differences at interior bins, converts log neighbor-stretch to within-model z-scores, then "
        "averages a radius-2 neighborhood around the registered target. Bootstrap resampling uses the "
        "seed x registered-location reward-control pair as the unit. This is the unit preserved in "
        "data/paper_b/reward_location_sweep_2026_07_02_rows.csv.")
    p.h2("Compute and Aggregate Data Format")
    p.para(
        "The confirmatory spatial sweep ran on Modal H200/H100 workers and trained 1,920 models: "
        "three architectures, 64 seeds, nine concern locations, and one matched uniform control per "
        "architecture/seed. The committed CSV snapshot has one row per model-condition-location record "
        "with architecture, condition, seed, reward_x, reward_y, final loss, coverage, primary stretch "
        "statistics, companion area-density statistics, rank, peak error, top-10 center-of-mass error, "
        "and reward-field correlation. The PDF itself is regenerated from committed aggregate numbers; "
        "the CSV reproduction script independently recomputes the reported bootstrap summaries.")

    p.references([
        "Bennett, W. R. Spectra of quantized signals. Bell System Technical Journal (1948).",
        "Gersho, A., Gray, R. M. Vector Quantization and Signal Compression. Kluwer Academic Publishers (1992).",
        "Cover, T. M., Thomas, J. A. Elements of Information Theory. Wiley (1991).",
        "Amari, S. Natural gradient works efficiently in learning. Neural Computation (1998).",
        "Ganguli, D., Simoncelli, E. P. Efficient sensory encoding and Bayesian inference with heterogeneous neural populations. Neural Computation (2014).",
        "Kriegeskorte, N., Mur, M., Bandettini, P. A. Representational similarity analysis - connecting the branches of systems neuroscience. Frontiers in Systems Neuroscience (2008).",
        "Arvanitidis, G., Hansen, L. K., Hauberg, S. Latent space oddity: on the curvature of deep generative models. ICLR (2018).",
        "Kornblith, S., Norouzi, M., Lee, H., Hinton, G. Similarity of neural network representations revisited. ICML (2019).",
        "Wei, X.-X., Stocker, A. A. A Bayesian observer model constrained by efficient coding can explain 'anti-Bayesian' percepts. Nature Neuroscience (2015).",
        "Cueva, C. J., Wei, X.-X. Emergence of grid-like representations by training recurrent neural networks to perform spatial localization. ICLR (2018).",
        "Banino, A. et al. Vector-based navigation using grid-like representations in artificial agents. Nature 557 (2018).",
        "Sorscher, B., Mel, G. C., Ganguli, S., Ocko, S. A. A unified theory for the origin of grid cells through the lens of pattern formation. NeurIPS (2019).",
        "Gardner, R. J. et al. Toroidal topology of population activity in grid cells. Nature 602 (2022).",
        "Ocko, S. A., Hardcastle, K., Giocomo, L. M., Ganguli, S. Emergent elasticity in the neural code for space. PNAS 115 (2018).",
        "Boccara, C. N. et al. The entorhinal cognitive map is attracted to goals. Science (2019).",
        "Butler, W. N., Hardcastle, K., Giocomo, L. M. Remembered reward locations restructure entorhinal spatial maps. Science (2019).",
        "Vaswani, A. et al. Attention is all you need. NeurIPS (2017).",
        "Assran, M. et al. Self-supervised learning from images with a joint-embedding predictive architecture. CVPR (2023).",
        "LeCun, Y. A path towards autonomous machine intelligence. OpenReview (2022).",
        "Lang, K. NewsWeeder: Learning to filter netnews. ICML (1995).",
        "Devlin, J., Chang, M.-W., Lee, K., Toutanova, K. BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding. NAACL (2019).",
        "Sanh, V., Debut, L., Chaumond, J., Wolf, T. DistilBERT, a distilled version of BERT: smaller, faster, cheaper and lighter. arXiv:1910.01108 (2019).",
        "Wang, W. et al. MiniLM: Deep Self-Attention Distillation for Task-Agnostic Compression of Pre-Trained Transformers. NeurIPS (2020).",
    ])
    out = p.build()
    print(f"[paperB] wrote {out}")


if __name__ == "__main__":
    build()
