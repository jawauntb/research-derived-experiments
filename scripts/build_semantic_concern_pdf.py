#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Render the semantic-concern follow-up paper from committed numbers.

Run:  python scripts/build_semantic_concern_pdf.py
Out:  artifacts/papers/semantic_concern_geometry_boundary.pdf
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paperkit as pk  # noqa: E402

FIG = "artifacts/papers/figs_semantic_concern"
OUT = "artifacts/papers/semantic_concern_geometry_boundary.pdf"

FAMILY_ROWS = [
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
        "spec_lo": -0.6099,
        "spec_hi": -0.4485,
        "rank": 0.4729,
        "centroid": 0.3250,
        "purity": 0.3693,
        "erank": 0.5531,
        "f1": -0.0181,
        "acc": -0.0083,
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
        "spec_lo": -0.5571,
        "spec_hi": -0.3943,
        "rank": 0.4846,
        "centroid": 0.3094,
        "purity": 0.3160,
        "erank": 0.4434,
        "f1": -0.0140,
        "acc": -0.0064,
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
        "spec_lo": -0.7632,
        "spec_hi": -0.5923,
        "rank": 0.4502,
        "centroid": 0.5419,
        "purity": 0.4561,
        "erank": 0.1037,
        "f1": -0.0189,
        "acc": -0.0099,
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
        "spec_lo": -0.7504,
        "spec_hi": -0.5800,
        "rank": 0.4524,
        "centroid": 0.5450,
        "purity": 0.4409,
        "erank": 0.1253,
        "f1": -0.0172,
        "acc": -0.0089,
    },
]

TARGET_LIFT = {
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


def fig_gate_forest(path: str) -> str:
    import matplotlib.pyplot as plt
    import numpy as np

    labels = []
    vals = []
    lows = []
    highs = []
    colors = []
    for row in FAMILY_ROWS:
        labels.extend([f"{row['family']} vs uniform", f"{row['family']} vs random"])
        vals.extend([row["lift_u"], row["lift_r"]])
        lows.extend([row["lift_u_lo"], row["lift_r_lo"]])
        highs.extend([row["lift_u_hi"], row["lift_r_hi"]])
        colors.extend(["#b23a48", "#7b2cbf"])
    y = np.arange(len(labels))[::-1]
    xerr = [[v - lo for v, lo in zip(vals, lows)], [hi - v for v, hi in zip(vals, highs)]]
    fig, ax = plt.subplots(figsize=(6.7, 4.4))
    ax.errorbar(vals, y, xerr=xerr, fmt="none", ecolor="#1f2933", lw=0.9, capsize=3)
    ax.scatter(vals, y, s=50, c=colors, edgecolor="#1f2933", linewidth=0.5, zorder=3)
    ax.axvline(0, color="#111", lw=0.9)
    ax.axvspan(-0.58, 0, color="#f7d9dd", alpha=0.45, zorder=0)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=7.4)
    ax.set_xlim(-0.58, 0.06)
    ax.set_xlabel("pre-registered semantic-margin lift z")
    ax.set_title("Confirmatory semantic gate: all families move opposite the Paper B prediction")
    for x, yy in zip(vals, y):
        ax.text(x - 0.018, yy, f"{x:.2f}", ha="right", va="center", fontsize=7.3)
    ax.grid(axis="y", visible=False)
    fig.savefig(path, bbox_inches="tight", facecolor="white", dpi=230)
    plt.close(fig)
    return path


def fig_split_geometry(path: str) -> str:
    import matplotlib.pyplot as plt
    import numpy as np

    labels = [r["short"] for r in FAMILY_ROWS]
    x = np.arange(len(labels))
    width = 0.19
    series = [
        ("margin gate", [r["lift_u"] for r in FAMILY_ROWS], "#b23a48"),
        ("centroid", [r["centroid"] for r in FAMILY_ROWS], "#2b6cb0"),
        ("kNN purity", [r["purity"] for r in FAMILY_ROWS], "#2f9e44"),
        ("eff. rank", [r["erank"] for r in FAMILY_ROWS], "#e8a13a"),
    ]
    fig, ax = plt.subplots(figsize=(6.8, 4.05))
    for i, (name, vals, color) in enumerate(series):
        ax.bar(x + (i - 1.5) * width, vals, width, label=name, color=color)
    ax.axhline(0, color="#111", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=7.6)
    ax.set_ylabel("z-lift vs uniform")
    ax.set_title("Geometry changes, but the registered margin goes negative", pad=10)
    ax.legend(fontsize=7.5, ncol=4, loc="lower center", bbox_to_anchor=(0.5, -0.31))
    ax.grid(axis="x", visible=False)
    fig.subplots_adjust(bottom=0.26)
    fig.savefig(path, bbox_inches="tight", facecolor="white", dpi=230)
    plt.close(fig)
    return path


def fig_target_heatmap(path: str) -> str:
    import matplotlib.pyplot as plt
    import numpy as np

    families = [r["family"] for r in FAMILY_ROWS]
    targets = ["comp.graphics", "rec.sport.hockey", "sci.med", "sci.space"]
    mat = np.array([[TARGET_LIFT[f][t] for t in targets] for f in families])
    fig, ax = plt.subplots(figsize=(6.7, 3.15))
    im = ax.imshow(mat, cmap="RdBu_r", vmin=-0.65, vmax=0.65, aspect="auto")
    ax.set_yticks(range(len(families)))
    ax.set_yticklabels(families, fontsize=7.5)
    ax.set_xticks(range(len(targets)))
    ax.set_xticklabels(targets, rotation=18, ha="right", fontsize=7.5)
    ax.set_title("Per-target audit: no semantic class carries a positive primary lift")
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            ax.text(j, i, f"{mat[i, j]:.2f}", ha="center", va="center", fontsize=7.3, color="#111")
    cbar = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cbar.set_label("lift vs uniform", fontsize=7.5)
    fig.savefig(path, bbox_inches="tight", facecolor="white", dpi=230)
    plt.close(fig)
    return path


def fig_behavior(path: str) -> str:
    import matplotlib.pyplot as plt
    import numpy as np

    labels = [r["short"] for r in FAMILY_ROWS]
    x = np.arange(len(labels))
    width = 0.34
    fig, ax = plt.subplots(figsize=(6.3, 3.1))
    ax.bar(x - width / 2, [r["f1"] for r in FAMILY_ROWS], width, label="target F1", color="#b23a48")
    ax.bar(x + width / 2, [r["acc"] for r in FAMILY_ROWS], width, label="overall accuracy", color="#9aa6b2")
    ax.axhline(0, color="#111", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=7.5)
    ax.set_ylabel("absolute lift vs uniform")
    ax.set_title("Behavioral check: the weighting intervention slightly harms held-out classification")
    ax.legend(fontsize=7.6)
    ax.grid(axis="x", visible=False)
    fig.savefig(path, bbox_inches="tight", facecolor="white", dpi=230)
    plt.close(fig)
    return path


def fig_schematic(path: str) -> str:
    import matplotlib.pyplot as plt
    import numpy as np

    fig, ax = plt.subplots(figsize=(6.5, 3.4))
    pts = {
        "space": (0.15, 0.70),
        "medicine": (0.37, 0.32),
        "hockey": (0.65, 0.70),
        "graphics": (0.85, 0.34),
    }
    edges = [("space", "medicine"), ("space", "hockey"), ("medicine", "graphics"), ("hockey", "graphics")]
    for a, b in edges:
        xa, ya = pts[a]
        xb, yb = pts[b]
        ax.plot([xa, xb], [ya, yb], color="#c6ccd5", lw=1.2, zorder=1)
    for name, (x, y) in pts.items():
        circ = plt.Circle((x, y), 0.075, color="#f8f9fa", ec="#1f2933", lw=1.2, zorder=3)
        ax.add_patch(circ)
        ax.text(x, y, name, ha="center", va="center", fontsize=8, weight="bold", zorder=4)
    ax.annotate(
        "loss-weight target moves",
        xy=pts["medicine"],
        xytext=(0.14, 0.12),
        arrowprops=dict(arrowstyle="->", lw=1.2, color="#7b2cbf"),
        fontsize=8.5,
        color="#2f3437",
    )
    ax.annotate(
        "registered margin does not follow",
        xy=pts["hockey"],
        xytext=(0.52, 0.10),
        arrowprops=dict(arrowstyle="->", lw=1.2, color="#b23a48"),
        fontsize=8.5,
        color="#2f3437",
    )
    ax.text(
        0.5,
        0.94,
        "Semantic follow-up: a real-text moved-target test, not a spatial coordinate bump",
        ha="center",
        va="center",
        fontsize=10,
        weight="bold",
    )
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.savefig(path, bbox_inches="tight", facecolor="white", dpi=230)
    plt.close(fig)
    return path


def build() -> None:
    Path(FIG).mkdir(parents=True, exist_ok=True)
    f_schema = fig_schematic(f"{FIG}/fig0_semantic_schematic.png")
    f_gate = fig_gate_forest(f"{FIG}/fig1_gate_forest.png")
    f_split = fig_split_geometry(f"{FIG}/fig2_split_geometry.png")
    f_heat = fig_target_heatmap(f"{FIG}/fig3_target_heatmap.png")
    f_behavior = fig_behavior(f"{FIG}/fig4_behavior.png")

    p = pk.Paper(OUT, FIG)
    p.title("A Semantic Boundary for Concern-Weighted Metric Deformation in Pretrained Transformers")
    p.authors("Jawaun Brown")
    p.authors("Research-Derived Experiments · Paper B Externality Follow-up")
    p.rule()
    p.abstract(
        "Paper B found that a movable spatial loss-weight field, operationally called concern, "
        "causally moves metric-density deformation in path-integration RNN, Transformer, and "
        "JEPA-style models. This follow-up tests the strongest immediate limitation: does the "
        "effect generalize to real text semantics in pretrained transformer encoders? We "
        "pre-registered a 20 Newsgroups moved-target experiment with two pretrained encoders "
        "(DistilBERT and all-MiniLM-L6-v2), two objectives (classifier and JEPA-like predictive "
        "latent training), four semantic targets, random-matched weighting controls, and a 2% "
        "standard-error gate on primary causal effects. Across 9,216 Modal H200/H100 fine-tuning "
        "cells and 4,096 paired effects, the confirmatory gate fails decisively: the pooled "
        "semantic-margin lift is -0.441 vs uniform [ -0.455, -0.427 ], SE 0.007, and -0.441 vs "
        "random-matched controls [ -0.455, -0.428 ], SE 0.007. Every family is negative with "
        "primary SE below 2%. Companion probes show real geometric movement--centroid separation, "
        "kNN purity, and often effective rank increase--but held-out target F1 and the registered "
        "local semantic margin decrease. The honest conclusion is not that Paper B is wrong; it is "
        "that the spatial metric-density claim does not yet transport to a pretrained text setting. "
        "This is a publishable boundary condition and a better foundation for the next paper than "
        "an overbroad generalization claim.")

    p.h1("1. Why This Follow-up Exists")
    p.para(
        "The original Paper B result is causal and clean inside its domain: move an external "
        "loss-weight field in a spatial path-integration task, and the learned metric-density peak "
        "moves with it. But the remaining reviewer objection is obvious and fair. The task is "
        "synthetic and spatial. Architecture variants named Transformer and JEPA do not by "
        "themselves prove that pretrained language or general AI systems allocate semantic "
        "resolution in the same way.")
    p.para(
        "This experiment was designed to attack that limitation directly. The target is no longer a "
        "coordinate in a square arena. It is one of four real text classes: comp.graphics, "
        "rec.sport.hockey, sci.med, and sci.space from 20 Newsgroups. The intervention is still "
        "external and causal: upweight the training loss for one registered semantic class, move "
        "which class receives that weight, and test whether the representation-geometry change "
        "moves to that class.")
    p.figure(f_schema, "Figure 1. Schematic only. The semantic experiment moves a loss-weight target over text classes rather than over physical coordinates. The registered question is whether the local semantic margin follows that target.", width_in=5.9)

    p.h1("2. Pre-registered Gate")
    p.para(
        "Concern is used here only as operational shorthand for a scalar loss weight. The primary "
        "metric is local semantic margin in the learned latent: mean k-nearest different-class "
        "cosine distance minus mean k-nearest same-class cosine distance, z-scored across classes "
        "inside the same model. A family passes only if the concern-target margin lift is positive "
        "against both a uniform model and a random-matched weighting control, the specificity "
        "interval is positive, the primary standard errors are at most 0.02, the target margin rank "
        "is above chance, and the run uses real 20 Newsgroups data rather than a synthetic fallback.")
    p.para(
        "The model families are DistilBERT and all-MiniLM-L6-v2, each with a classifier objective "
        "and a JEPA-like text objective. The JEPA-like variant predicts the stop-gradient latent of "
        "another same-class text example. It is a joint-embedding predictive analogue, not a claim "
        "to reproduce the official I-JEPA vision architecture.")

    p.h1("3. Main Result: The Gate Fails")
    p.figure(f_gate, "Figure 2. Primary confirmatory result. All four pretrained text families move opposite the registered Paper B semantic-margin prediction, against both uniform and random-matched controls. Error bars are bootstrap 95% intervals over seed-target effects.", width_in=6.15)
    p.table(
        [
            ["Family", "lift vs uniform", "SE", "lift vs random", "SE", "rank", "gate"],
            ["DistilBERT classifier", "-0.398 [-0.430,-0.367]", "0.016", "-0.396 [-0.426,-0.366]", "0.015", "0.473", "fail"],
            ["DistilBERT JEPA-like", "-0.358 [-0.389,-0.327]", "0.015", "-0.360 [-0.388,-0.332]", "0.014", "0.485", "fail"],
            ["MiniLM classifier", "-0.508 [-0.534,-0.484]", "0.013", "-0.505 [-0.531,-0.480]", "0.013", "0.450", "fail"],
            ["MiniLM JEPA-like", "-0.499 [-0.525,-0.474]", "0.013", "-0.505 [-0.531,-0.480]", "0.013", "0.452", "fail"],
        ],
        caption="Table 1. Confirmatory gate. All primary standard errors are below the accepted 2% threshold, but all signs are negative.",
        col_widths=[116, 105, 34, 105, 34, 38, 34],
    )
    p.para(
        "The architecture-balanced pooled primary effect is -0.441 vs uniform with SE 0.007 and "
        "-0.441 vs random-matched controls with SE 0.007. The real-dataset gate passes; the "
        "causal semantic-margin gate does not. This is a precise negative result, not an ambiguous "
        "underpowered null.")
    p.figure(f_heat, "Figure 3. Per-target audit. No registered semantic class carries a positive primary lift; the result is not caused by one difficult topic.", width_in=6.05)

    p.h1("4. Companion Geometry: A Split, Not a Vacuum")
    p.figure(f_split, "Figure 4. Companion metrics reveal a split geometry. Upweighting increases centroid separation and neighborhood purity, and often effective rank, even while the registered local semantic-margin gate becomes negative.", width_in=6.2)
    p.figure(f_behavior, "Figure 5. Behavioral check. The same intervention slightly reduces held-out target F1 and overall accuracy, so the companion geometry should not be rebranded as a successful task-performance effect.", width_in=5.85)
    p.para(
        "This split matters. A careless analysis could have replaced the failed primary metric with "
        "the positive centroid or purity probes and declared victory. The pre-registration prevents "
        "that. What we can say is narrower and more useful: semantic loss weighting does reorganize "
        "the latent space, but in these pretrained text encoders it does not increase the registered "
        "local margin around the valued class. It appears closer to class-level re-centering or "
        "cluster sharpening, with a small behavioral cost, than to the spatial metric-density "
        "allocation observed in Paper B.")

    p.h1("5. Consequences for Paper B")
    p.para(
        "This result strengthens Paper B by limiting it. The spatial finding remains a robust causal "
        "mechanism result: within finite-capacity path integration, a moved value field moves the "
        "learned metric. But it should not be marketed as already established in pretrained language "
        "models or foundation-model settings. The correct NeurIPS/ACL-ready posture is: the spatial "
        "mechanism is real, the semantic transformer generalization is not yet confirmed, and the "
        "first large externality test found a boundary condition.")
    p.para(
        "The next experiment should therefore not merely add more seeds. It should change the "
        "semantic task so that 'resolution' has a task-native meaning: retrieval under asymmetric "
        "cost, pairwise paraphrase discrimination inside the target class, or a contrastive corpus "
        "where valued examples require finer distinctions rather than broader class separation. "
        "Only then should a new confirmatory gate be frozen.")

    p.h1("6. Limitations")
    p.para(
        "The experiment uses four 20 Newsgroups topics, two compact pretrained encoders, and a "
        "JEPA-like text objective rather than a production-scale language model or official I-JEPA. "
        "The primary metric is a plausible semantic analogue of local metric density, but the "
        "positive companion results show that geometry has multiple non-equivalent notions. The "
        "result therefore rejects one transported claim, not all possible semantic concern "
        "hypotheses.")

    p.references([
        "Lang, K. NewsWeeder: Learning to filter netnews. ICML (1995).",
        "The 20 Newsgroups data set. URL: https://qwone.com/~jason/20Newsgroups/.",
        "Devlin, J., Chang, M.-W., Lee, K., Toutanova, K. BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding. NAACL (2019).",
        "Sanh, V., Debut, L., Chaumond, J., Wolf, T. DistilBERT, a distilled version of BERT: smaller, faster, cheaper and lighter. arXiv:1910.01108 (2019).",
        "Wang, W., Wei, F., Dong, L., Bao, H., Yang, N., Zhou, M. MiniLM: Deep Self-Attention Distillation for Task-Agnostic Compression of Pre-Trained Transformers. NeurIPS (2020).",
        "Reimers, N., Gurevych, I. Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks. EMNLP-IJCNLP (2019).",
        "Kriegeskorte, N., Mur, M., Bandettini, P. Representational similarity analysis: connecting the branches of systems neuroscience. Frontiers in Systems Neuroscience (2008).",
        "Vaswani, A. et al. Attention Is All You Need. NeurIPS (2017).",
        "LeCun, Y. A Path Towards Autonomous Machine Intelligence. OpenReview (2022).",
        "Assran, M. et al. Self-Supervised Learning from Images with a Joint-Embedding Predictive Architecture. CVPR (2023).",
    ])
    out = p.build()
    print(f"[semantic-concern-pdf] wrote {out}")


if __name__ == "__main__":
    build()
