#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Render Paper A from the 2026-07-02 Modal gate sweep.

The raw JSON remains gitignored. This builder uses the committed result report
numbers from experiments/grid_cell_weakness/results/modal_grid_cell_weakness_sweep_2026_07_02.md.

Run:  python scripts/build_gridcell_pdf.py
Out:  artifacts/papers/weakness_predicts_topology.pdf
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paperkit as pk  # noqa: E402
from reportlab.platypus import PageBreak  # noqa: E402

FIG = "artifacts/papers/figs_gridcell"
OUT = "artifacts/papers/weakness_predicts_topology.pdf"

CONDS = ["full_translation", "partial_translation", "random_shift", "none", "wrong_group"]
LABELS = ["full translation", "partial", "random shift", "none", "wrong group"]
WEAKNESS = [0.768, 0.416, 0.400, 0.446, 0.048]
TOPO = [0.357, 0.007, 0.000, 0.000, 0.009]
TORUS = [0.734, 0.000, 0.000, 0.000, 0.000]
OOD = [0.949, 0.732, 0.615, 0.484, 0.489]
OOD_CURVES = {
    "full translation": [0.947, 0.949, 0.948, 0.949],
    "partial": [0.913, 0.793, 0.706, 0.732],
    "random shift": [0.976, 0.910, 0.778, 0.615],
    "none": [0.984, 0.805, 0.655, 0.484],
    "wrong group": [0.985, 0.808, 0.659, 0.489],
}


def fig_gate_matrix(path: str) -> str:
    import matplotlib.pyplot as plt
    import numpy as np

    gates = ["G1 torus", "G2 W-topo", "G3 W-OOD", "G4 mediate", "G5 spectrum", "G6 causal", "null"]
    vals = np.array([[1, 0, 0, 0, 1, 1, 1]], dtype=float)
    fig, ax = plt.subplots(figsize=(6.6, 1.6))
    ax.imshow(vals, cmap=plt.matplotlib.colors.ListedColormap(["#c0392b", "#2f9e44"]), vmin=0, vmax=1)
    ax.set_xticks(range(len(gates)))
    ax.set_xticklabels(gates, rotation=25, ha="right")
    ax.set_yticks([0])
    ax.set_yticklabels(["Modal\n320 nets"])
    for j, v in enumerate(vals[0]):
        ax.text(j, 0, "pass" if v else "fail", ha="center", va="center", color="white", fontsize=8, weight="bold")
    ax.set_title("Pre-registered gate verdicts: causal/spectral legs pass; mediation fails")
    ax.tick_params(length=0)
    fig.savefig(path, bbox_inches="tight", facecolor="white", dpi=220)
    plt.close(fig)
    return path


def fig_condition_bars(path: str) -> str:
    import matplotlib.pyplot as plt
    import numpy as np

    x = np.arange(len(LABELS))
    width = 0.26
    fig, ax = plt.subplots(figsize=(6.8, 3.2))
    ax.bar(x - width, WEAKNESS, width, label="weakness", color="#2b6cb0")
    ax.bar(x, TOPO, width, label="toroidal score", color="#2f9e44")
    ax.bar(x + width, OOD, width, label="OOD @2.0", color="#e8a13a")
    ax.set_xticks(x)
    ax.set_xticklabels(LABELS, rotation=20, ha="right")
    ax.set_ylim(0, 1.02)
    ax.set_ylabel("mean value")
    ax.set_title("Condition means across 320 Modal-trained path-integration RNNs")
    ax.legend(fontsize=8)
    ax.grid(axis="x", visible=False)
    fig.savefig(path, bbox_inches="tight", facecolor="white", dpi=220)
    plt.close(fig)
    return path


def fig_ood_curves(path: str) -> str:
    import matplotlib.pyplot as plt

    xs = [1.0, 1.25, 1.5, 2.0]
    colors = ["#2b6cb0", "#2f9e44", "#8a63d2", "#9aa6b2", "#c0392b"]
    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    for (name, vals), color in zip(OOD_CURVES.items(), colors):
        ax.plot(xs, vals, marker="o", lw=1.8, label=name, color=color)
    ax.set_xlabel("arena scale at decode time")
    ax.set_ylabel("decode accuracy")
    ax.set_ylim(0.35, 1.02)
    ax.set_title("Full translation preserves OOD path integration in larger arenas")
    ax.legend(fontsize=7.4, ncol=2)
    fig.savefig(path, bbox_inches="tight", facecolor="white", dpi=220)
    plt.close(fig)
    return path


def build() -> None:
    Path(FIG).mkdir(parents=True, exist_ok=True)
    f_gate = fig_gate_matrix(f"{FIG}/fig1_gate_matrix.png")
    f_cond = fig_condition_bars(f"{FIG}/fig2_condition_means.png")
    f_ood = fig_ood_curves(f"{FIG}/fig3_ood_curves.png")

    p = pk.Paper(OUT, FIG)
    p.title("Translation Augmentation Produces Toroidal Codes and Larger-Arena Generalization in Path-Integration RNNs")
    p.authors("Jawaun Brown")
    p.authors("Research-Derived Experiments · empirical note and negative mediation result")
    p.rule()
    p.abstract(
        "This note tests a pre-registered strong claim about path-integration RNNs: <b>weakness</b>, "
        "a held-out linear equivariance score for wrapped translations, should govern whether a "
        "learned population code forms a toroidal manifold, and toroidal topology should mediate "
        "larger-arena generalization. The result is a useful negative mediation result. In a "
        "320-network Modal H100 sweep, full translation augmentation reliably induces toroidal "
        "codes (G1 pass; torus match 0.734), preserves decoding when the arena doubles (OOD 0.949 "
        "versus 0.484 for no augmentation), and produces the causal condition contrast specified "
        "before the sweep (G6 pass). Weakness also tracks spectral concentration (G5 pass; "
        "rho = +0.635). But the central triangle fails: weakness only weakly predicts toroidal "
        "score (G2 fail; rho = +0.197), does not beat final loss on larger-arena OOD by the "
        "pre-registered 2x margin (G3 fail; weakness rho = +0.617, loss rho = +0.652), and "
        "topology does not mediate the weakness-OOD relation (G4 fail). The surviving claim is "
        "therefore bounded: in this artificial RNN harness, translation-structured training "
        "causally produces toroidal, OOD-generalizing codes, while weakness measures one spectral "
        "aspect of the learned translation structure rather than serving as the governing scalar "
        "of torus formation.")

    p.h1("1. Framing")
    p.para(
        "Biological grid-cell population activity has been shown, using topological data analysis, "
        "to lie on a toroidal manifold, and path-integration RNNs can learn grid-like spatial "
        "codes. This experiment asks a bridge question: when toroidal codes and larger-arena "
        "generalization appear in a learned path integrator, are they governed by the same "
        "substrate-general weakness quantity that predicted OOD behavior in the symbolic and "
        "vision experiments, or are they more directly caused by the translation-structured "
        "training condition itself?")
    p.para(
        "The strong version predicted a triangle: high weakness, low Fourier participation ratio "
        "(few aligned frequency modes), clean toroidal topology, and larger-arena OOD "
        "generalization should be different measurements of one event. This sweep was designed to "
        "test that strong triangle and let it fail. The published posture should therefore be an "
        "empirical note, not a broad confirmation paper.")

    p.h1("2. Pre-Registered Test")
    p.para(
        "The gates were specified in the project repository before the Modal sweep "
        "(`papers/grid_cell_weakness/preregistration.md`, frozen 2026-06-28). The registration "
        "was project-level rather than an external registry filing. It asked whether a single "
        "translation-compatibility scalar predicts both population topology and OOD accuracy, and "
        "whether topology carries the weakness-to-OOD relation.")
    p.flow += [PageBreak()]
    p.table(
        [["Gate", "Pre-registered criterion", "Modal result", "Verdict"],
         ["G1 manifold", "full translation torus match >= 0.60", "0.734", "pass"],
         ["G2 weakness-topology", "rho >= 0.5 and >= 2x best baseline", "rho +0.197; loss +0.431", "fail"],
         ["G3 weakness-OOD", "rho >= 0.5 and >= 2x best baseline", "rho +0.617; loss +0.652", "fail"],
         ["G4 mediation", "partial rho drops by >= 50%", "partial rho +0.623; no drop", "fail"],
         ["G5 spectrum", "rho(weakness, -Fourier PR) >= 0.5", "+0.635", "pass"],
         ["G6 causal", "full translation beats none/random shift", "topology and OOD both lift", "pass"],
         ["wrong-group null", "wrong-group predictor null or negative", "tie-aware rho 0.000", "pass"]],
        caption="Table 1. Locked gates and outcomes. The decisive failure is not auxiliary: G2-G4 reject the registered mediation triangle.",
        col_widths=[105, 180, 130, 45])
    p.figure(f_gate, "Figure 1. Gate verdicts from the pre-registered Modal sweep. The causal and spectral legs pass; the topology-governing and mediation claims fail.", width_in=6.2)

    p.h1("3. Methods")
    p.para(
        "We trained 320 velocity-driven path-integration RNNs on Modal H100 workers: five training "
        "conditions, two recurrent architectures, and 32 seeds. Each network predicts a place-cell "
        "code from velocity sequences. Conditions vary the augmentation regime: full translations, "
        "partial translations, random shifts, no augmentation, and a wrong-group control. For each "
        "trained code we measure weakness, persistent-homology toroidal score, Fourier participation "
        "ratio, and decoding accuracy in held-out arenas of scale 1.0, 1.25, 1.5, and 2.0. The "
        "largest arena is the pre-registered OOD metric.")
    p.para(
        "<b>Weakness.</b> For a binned hidden-state population code H(x) and a held-out wrapped "
        "translation tau, fit one least-squares linear operator A_tau on half the spatial bins and "
        "evaluate it on held-out bins: W = E_tau R^2[H(x + tau), A_tau H(x)]. Translations are "
        "wrapped modulo the 16 x 16 bin grid, one operator is fit per translation, R^2 is computed "
        "over hidden units and held-out positions, and the reported weakness is the mean clipped "
        "R^2 across the registered shifts. The metric is computed on hidden activity, not on the "
        "decoded position or place-cell target.")
    p.para(
        "<b>Topology.</b> Hidden states are sampled from fresh trajectories, averaged into a "
        "16 x 16 spatial grid, and treated as a point cloud in hidden-state space. Empty spatial "
        "bins, when present, are filled with the global mean so the grid is complete; the Modal "
        "cells report coverage. Persistent homology is computed with a Vietoris-Rips complex "
        "(Gudhi backend, max simplex dimension 3, edge cap at the 45th percentile of pairwise "
        "distances), yielding H0, H1, and H2 persistence intervals. A torus should have Betti "
        "signature (1,2,1): one component, two loops, and one void. The continuous toroidal score "
        "combines the second H1 bar above the third-bar noise floor with the strongest H2 void; "
        "`betti_match_torus` requires two estimated H1 loops and a nontrivial H2 bar.")

    p.h1("4. Results")
    p.figure(f_cond, "Figure 2. Condition means. Full translation is the only condition that reliably forms a torus and preserves OOD decoding at arena scale 2.0.", width_in=6.3)
    p.figure(f_ood, "Figure 3. Larger-arena OOD curves. Full translation remains stable as the arena doubles; controls degrade sharply.", width_in=6.0)
    p.table(
        [["Condition", "n", "weakness", "toroidal", "torus match", "OOD @2.0"],
         ["full translation", "64", "0.768", "0.357", "0.734", "0.949"],
         ["partial translation", "64", "0.416", "0.007", "0.000", "0.732"],
         ["random shift", "64", "0.400", "0.000", "0.000", "0.615"],
         ["none", "64", "0.446", "0.000", "0.000", "0.484"],
         ["wrong group", "64", "0.048", "0.009", "0.000", "0.489"]],
        caption="Table 2. Condition means. Full translation is the positive intervention; random shift and wrong group are controls. Weakness is not monotone with toroidal score outside the full-translation condition.",
        col_widths=[130, 42, 70, 70, 80, 70])
    p.para(
        "The positive result is clean at the condition level. Full translation augmentation is the "
        "only condition that reliably produces a torus, and it preserves decoding accuracy as the "
        "arena doubles. Partial translation and random shifts lift OOD relative to no augmentation, "
        "but they do not produce the torus match. The wrong-group control has near-zero weakness "
        "under the registered translation metric and does not lift topology or OOD.")
    p.para(
        "The negative result is equally important. Across individual networks, weakness does not "
        "explain toroidal score strongly enough to pass the registered gate, does not outperform "
        "final loss on OOD by the required margin, and leaves the weakness-OOD association intact "
        "after controlling for topology. These are not wording problems; they falsify the strongest "
        "version of the theory tested here.")

    p.h1("5. Interpretation")
    p.para(
        "The result should not be polished into a full confirmation. It is better than that: it "
        "marks the boundary of the weakness program on a task where topology is genuinely "
        "load-bearing. Translation augmentation is the experimentally manipulated variable that "
        "produces toroidal topology and larger-arena generalization in this harness. Weakness is "
        "still useful as a spectral and OOD-associated measurement, but it is not the scalar that "
        "governs torus formation here.")
    p.para(
        "A plausible reading is that the augmentation condition itself is the strongest causal "
        "variable: it directly supplies the group structure needed for both topology and OOD. "
        "Weakness measures part of that event, especially its spectral footprint, but it is not "
        "sufficiently specific to explain topology variance after training loss and condition "
        "effects are present. The failed gates are not auxiliary failures; they reject the strongest "
        "claim. The surviving claim is not that weakness governs toroidal topology, but that "
        "translation-structured training produces toroidal, OOD-generalizing codes while weakness "
        "tracks one spectral aspect of learned translation structure.")

    p.h1("6. Scope and Limitations")
    p.para(
        "This remains an artificial RNN path-integration task, not a biological replication. The "
        "paper should not claim to explain biological grid cells. Its claim is narrower: a learned "
        "path-integration model, inspired by the grid-cell/topology literature, responds to a "
        "translation-augmentation intervention by forming toroidal hidden-state structure and "
        "generalizing to larger arenas. The topology metric uses binned hidden activity and "
        "Vietoris-Rips persistent homology; both can be sensitive to sampling density, binning, "
        "edge thresholds, and seeds. The wrong-group null in the first Modal summary was "
        "miscomputed by a rank helper that did not average ties; the corrected tie-aware Spearman "
        "is reported here and in the result report. The raw cell measurements did not change.")
    p.para(
        "Future tests should separate condition effects from within-condition variation by "
        "sampling a larger family of already-toroidal codes, perturbing trained codes rather than "
        "only training regimes, and checking topology robustness under multiple bin counts, point "
        "sampling strategies, and persistent-homology backends. A biological extension would be a "
        "new confirmatory study on public grid-cell recordings, not an interpretation of the RNN "
        "result itself.")

    p.references([
        "Gardner, R. J. et al. Toroidal topology of population activity in grid cells. Nature 602, 123-128 (2022).",
        "McNaughton, B. L., Battaglia, F. P., Jensen, O., Moser, E. I., Moser, M.-B. Path integration and the neural basis of the cognitive map. Nature Reviews Neuroscience 7, 663-678 (2006).",
        "Fuhs, M. C., Touretzky, D. S. A spin glass model of path integration in rat medial entorhinal cortex. Journal of Neuroscience 26, 4266-4276 (2006).",
        "Burak, Y., Fiete, I. R. Accurate path integration in continuous attractor network models of grid cells. PLoS Computational Biology 5, e1000291 (2009).",
        "Cueva, C. J., Wei, X.-X. Emergence of grid-like representations by training recurrent neural networks to perform spatial localization. arXiv:1803.07770 (2018).",
        "Banino, A. et al. Vector-based navigation using grid-like representations in artificial agents. Nature 557, 429-433 (2018).",
        "Sorscher, B., Mel, G. C., Ganguli, S., Ocko, S. A. A unified theory for the origin of grid cells through the lens of pattern formation. NeurIPS (2019).",
        "Xu, D., Gao, R., Zhang, W.-H., Wei, X.-X., Wu, Y. N. Emergence of grid-like representations by training recurrent networks with conformal normalization. arXiv:2310.19192 (2023).",
        "Cohen, T., Welling, M. Group Equivariant Convolutional Networks. ICML (2016).",
        "Gruver, N., Finzi, M., Goldblum, M., Wilson, A. G. The Lie Derivative for Measuring Learned Equivariance. ICLR (2023).",
        "Xu, M., Song, F., Si, B., Qin, S. The Principle of Isomorphism: A Theory of Population Activity in Grid Cells and Beyond. arXiv:2510.02853 (2025).",
        "Bennett, M. T. How to Create Conscious Machines. arXiv:2403.00644 (2024).",
    ])
    out = p.build()
    print(f"[gridcell-pdf] wrote {out}")


if __name__ == "__main__":
    build()
