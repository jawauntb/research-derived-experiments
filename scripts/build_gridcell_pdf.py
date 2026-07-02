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
from reportlab.platypus import PageBreak, Paragraph  # noqa: E402

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
TORUS_MATCH_WILSON = {
    "full translation": "[0.61, 0.83]",
    "partial": "[0.00, 0.06]",
    "random shift": "[0.00, 0.06]",
    "none": "[0.00, 0.06]",
    "wrong group": "[0.00, 0.06]",
}
METRIC_CI = {
    "full translation": {
        "weakness": "0.768 [0.723, 0.808]",
        "toroidal": "0.357 [0.317, 0.396]",
        "fourier": "4.472 [4.188, 4.773]",
        "ood": "0.949 [0.946, 0.953]",
    },
    "partial translation": {
        "weakness": "0.416 [0.363, 0.467]",
        "toroidal": "0.007 [0.006, 0.009]",
        "fourier": "7.557 [7.094, 8.038]",
        "ood": "0.732 [0.725, 0.738]",
    },
    "random shift": {
        "weakness": "0.400 [0.368, 0.433]",
        "toroidal": "0.000 [0.000, 0.000]",
        "fourier": "8.778 [8.200, 9.354]",
        "ood": "0.615 [0.597, 0.628]",
    },
    "none": {
        "weakness": "0.446 [0.409, 0.481]",
        "toroidal": "0.000 [0.000, 0.000]",
        "fourier": "8.324 [7.791, 8.899]",
        "ood": "0.484 [0.473, 0.495]",
    },
    "wrong group": {
        "weakness": "0.048 [0.033, 0.064]",
        "toroidal": "0.009 [0.007, 0.011]",
        "fourier": "14.634 [14.128, 15.180]",
        "ood": "0.489 [0.479, 0.499]",
    },
}
OOD_CI = {
    "full translation": ["0.947 [0.944, 0.949]", "0.949 [0.946, 0.952]", "0.948 [0.945, 0.951]", "0.949 [0.946, 0.953]"],
    "partial translation": ["0.913 [0.909, 0.918]", "0.793 [0.786, 0.800]", "0.706 [0.697, 0.715]", "0.732 [0.725, 0.738]"],
    "random shift": ["0.976 [0.958, 0.987]", "0.910 [0.890, 0.923]", "0.778 [0.756, 0.793]", "0.615 [0.597, 0.628]"],
    "none": ["0.984 [0.980, 0.987]", "0.805 [0.794, 0.815]", "0.655 [0.645, 0.665]", "0.484 [0.473, 0.495]"],
    "wrong group": ["0.985 [0.983, 0.987]", "0.808 [0.797, 0.818]", "0.659 [0.650, 0.669]", "0.489 [0.479, 0.499]"],
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
        "generalization should be different measurements of one event. The sweep was designed to "
        "make that strong triangle falsifiable. We therefore present the result as an empirical "
        "note and negative mediation result, not as a broad confirmation of the weakness program.")

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
        "<b>Statistics.</b> Unless otherwise stated, rho denotes Spearman rank correlation with "
        "average-rank tie handling. G2 and G3 report signed rho values, while the registered "
        "2x baseline comparisons use absolute rho for classical predictors. The loss baseline is "
        "raw final training loss, not negative loss; its positive rho with OOD reflects the fact "
        "that the translation-augmented condition is harder to fit but generalizes better.")
    p.para(
        "<b>Topology.</b> Hidden states are sampled from fresh trajectories, averaged into a "
        "16 x 16 spatial grid, and treated as a point cloud in hidden-state space. Empty spatial "
        "bins, when present, are filled with the global mean so the grid is complete; the Modal "
        "cells report coverage. Persistent homology is computed with a Vietoris-Rips complex "
        "(Gudhi backend, max simplex dimension 3, edge cap at the 45th percentile of pairwise "
        "distances), yielding H0, H1, and H2 persistence intervals. A torus should have Betti "
        "signature (1,2,1): one component, two loops, and one void. The continuous toroidal score "
        "combines the second H1 bar above the third-bar noise floor with the strongest H2 void; "
        "`betti_match_torus` requires two estimated H1 loops and a nontrivial H2 bar. Torus match "
        "is the fraction of networks in a condition satisfying this Boolean criterion.")

    p.h1("4. Results")
    p.figure(f_cond, "Figure 2. Condition means. Full translation is the only condition that reliably forms a torus and preserves OOD decoding at arena scale 2.0.", width_in=6.3)
    p.figure(f_ood, "Figure 3. Larger-arena OOD curves. Full translation remains stable as the arena doubles; controls degrade sharply.", width_in=6.0)
    p.table(
        [["Condition", "n", "weakness", "toroidal", "torus match", "Wilson 95%", "OOD @2.0"],
         ["full translation", "64", "0.768", "0.357", "0.734", TORUS_MATCH_WILSON["full translation"], "0.949"],
         ["partial translation", "64", "0.416", "0.007", "0.000", TORUS_MATCH_WILSON["partial"], "0.732"],
         ["random shift", "64", "0.400", "0.000", "0.000", TORUS_MATCH_WILSON["random shift"], "0.615"],
         ["none", "64", "0.446", "0.000", "0.000", TORUS_MATCH_WILSON["none"], "0.484"],
         ["wrong group", "64", "0.048", "0.009", "0.000", TORUS_MATCH_WILSON["wrong group"], "0.489"]],
        caption="Table 2. Condition means. Wilson intervals apply only to the torus-match fraction. Full translation is the positive intervention; random shift and wrong group are controls. Weakness is not monotone with toroidal score outside the full-translation condition.",
        col_widths=[115, 34, 62, 62, 70, 76, 62])
    p.para(
        "The recovered raw-cell export also supports seed-level uncertainty for the continuous "
        "metrics. Appendix B reports percentile bootstrap intervals for weakness, toroidal score, "
        "Fourier participation ratio, and each OOD arena.")
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

    p.flow += [PageBreak()]
    p.h1("Appendix A. Implementation Details")
    p.table(
        [["Component", "Vanilla RNN cell", "GRU cell"],
         ["recurrent update", "torch RNNCell, ReLU", "torch GRUCell + ReLU hidden"],
         ["hidden size", "128", "128"],
         ["input at t", "2-D velocity", "2-D velocity"],
         ["initial state", "linear encoder of initial place code", "same"],
         ["output", "100 place-cell logits", "same"],
         ["loss", "KL divergence to target place-cell code + 1e-3 activity penalty", "same"],
         ["optimizer", "Adam, lr 1e-3, weight decay 1e-4", "same"],
         ["training", "4000 steps, batch 200, trajectory length 20", "same"]],
        caption="Table A1. Architecture and training hyperparameters used in every Modal cell.",
        col_widths=[95, 205, 205])
    p.para(
        "<b>Path-integration task.</b> Each training trajectory starts with x0 sampled uniformly "
        "from the interior [0.1B, 0.9B]^2 of a square box of side B. Heading is initialized "
        "uniformly and perturbed each step by Normal(0, 0.4); velocity is 0.06(cos theta, "
        "sin theta). Positions update as x(t+1) = x(t) + v(t) with reflecting boundaries. Training "
        "uses B=1.0. Place targets are softmax-normalized Gaussian activations over a 10 x 10 "
        "unit-square place-cell grid with sigma=0.10.")
    a2_rows = [
        ("none", "no augmentation"),
        (
            "full translation",
            "sample offset u~Uniform([0,1]^2); add u to positions and initial position "
            "modulo 1; velocities unchanged",
        ),
        (
            "partial translation",
            "sample offset u~Uniform([0,0.3]^2); add u modulo 1; velocities unchanged",
        ),
        (
            "random shift",
            "sample offset epsilon~Normal(0,0.05); add to positions and initial position, "
            "clipped to the current box",
        ),
        ("wrong group", "swap the two velocity coordinates while leaving target positions unchanged"),
        (
            "null predictor",
            "separate wrong-group metric: replace wrapped translations by a fixed random bin "
            "permutation in the weakness calculation",
        ),
    ]
    p.table(
        [["Condition", "Exact intervention in the worker"]]
        + [[Paragraph(condition, p.s_small), Paragraph(intervention, p.s_small)] for condition, intervention in a2_rows],
        caption="Table A2. Training conditions and the separate wrong-group null predictor.",
        col_widths=[115, 390])
    p.para(
        "<b>OOD decoding.</b> Evaluation generates fresh trajectories with B in {1.0, 1.25, "
        "1.5, 2.0}. The model's place-cell argmax is counted correct when its center lies within "
        "one unit-square place-cell spacing of the target argmax. The primary OOD score is the "
        "largest scale, B=2.0. The same condition-specific preprocessing is used at decode time; "
        "therefore the result should be read as larger-trajectory/arena-scale OOD in this harness, "
        "not as an unbounded coordinate extrapolation claim.")
    p.para(
        "<b>Fourier participation ratio.</b> Hidden activity is averaged into 16 x 16 spatial "
        "rate maps per unit. After subtracting each map's mean and dropping the DC Fourier bin, "
        "power is normalized over spatial frequencies and PR = 1 / sum_k p_k^2 is averaged over "
        "units. Lower PR means fewer effective Fourier modes; G5 correlates weakness with -PR.")
    p.para(
        "<b>Topology and uncertainty status.</b> The committed result report stores condition "
        "means and gate correlations; the recovered raw per-cell JSON has now been exported to "
        "committed CSVs and supports seed-level bootstrap intervals for scalar metrics. It does "
        "not store the hidden-state populations needed to reconstruct topology robustness over "
        "bin counts, Vietoris-Rips edge caps, empty-bin handling, or sampling density. The Modal "
        "runner now supports that robustness export for reruns, but the present PDF does not "
        "treat robustness as completed evidence.")

    p.flow += [PageBreak()]
    p.h1("Appendix B. Conference Evidence Exports")
    p.para(
        "The raw 320-cell Modal JSON was recovered locally and exported with "
        "`scripts/analyze_gridcell_conference_evidence.py` into per-cell and aggregate CSVs under "
        "`experiments/grid_cell_weakness/results`. Continuous intervals are percentile bootstrap "
        "95% intervals from 5000 resamples within condition; torus-match intervals are Wilson "
        "95% intervals for the Boolean `betti_match_torus` fraction.")
    p.table(
        [["Condition", "weakness", "toroidal", "Fourier PR", "OOD @2.0"],
         ["full translation", METRIC_CI["full translation"]["weakness"], METRIC_CI["full translation"]["toroidal"], METRIC_CI["full translation"]["fourier"], METRIC_CI["full translation"]["ood"]],
         ["partial translation", METRIC_CI["partial translation"]["weakness"], METRIC_CI["partial translation"]["toroidal"], METRIC_CI["partial translation"]["fourier"], METRIC_CI["partial translation"]["ood"]],
         ["random shift", METRIC_CI["random shift"]["weakness"], METRIC_CI["random shift"]["toroidal"], METRIC_CI["random shift"]["fourier"], METRIC_CI["random shift"]["ood"]],
         ["none", METRIC_CI["none"]["weakness"], METRIC_CI["none"]["toroidal"], METRIC_CI["none"]["fourier"], METRIC_CI["none"]["ood"]],
         ["wrong group", METRIC_CI["wrong group"]["weakness"], METRIC_CI["wrong group"]["toroidal"], METRIC_CI["wrong group"]["fourier"], METRIC_CI["wrong group"]["ood"]]],
        caption="Table B1. Scalar metric means with 95% intervals. Fourier PR is included because the spectral leg is the surviving weakness-aligned measurement.",
        col_widths=[105, 100, 100, 105, 100])
    p.table(
        [["Condition", "1.0", "1.25", "1.5", "2.0"],
         ["full translation", *OOD_CI["full translation"]],
         ["partial translation", *OOD_CI["partial translation"]],
         ["random shift", *OOD_CI["random shift"]],
         ["none", *OOD_CI["none"]],
         ["wrong group", *OOD_CI["wrong group"]]],
        caption="Table B2. OOD decoding curves with bootstrap 95% intervals.",
        col_widths=[105, 100, 100, 100, 100])
    p.para(
        "<b>Within-toroidal subset.</b> Among the 47 already-toroidal full-translation models, "
        "weakness does not explain additional OOD variation after torus formation: "
        "rho(weakness, OOD) = -0.198 with bootstrap 95% CI [-0.518, 0.136]. Within this subset, "
        "weakness also anticorrelates with continuous toroidal score (rho = -0.335, CI "
        "[-0.577, -0.063]) and with -Fourier PR (rho = -0.356, CI [-0.585, -0.071]). No control "
        "condition has enough torus-matching models for the same analysis.")
    p.para(
        "<b>Topology robustness.</b> The recovered scalar raw JSON cannot reconstruct robustness "
        "over bin counts, edge caps, empty-bin handling, or sampling density because it does not "
        "store hidden-state populations. The runner now emits `topology_robustness` rows when "
        "rerun with robustness enabled; until then, robustness remains the next required "
        "conference-review evidence item.")

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
        "Zomorodian, A., Carlsson, G. Computing Persistent Homology. Discrete & Computational Geometry 33, 249-274 (2005).",
        "Maria, C., Boissonnat, J.-D., Glisse, M., Yvinec, M. The Gudhi Library: Simplicial Complexes and Persistent Homology. ICMS (2014).",
        "Imai, K., Keele, L., Tingley, D. A General Approach to Causal Mediation Analysis. Psychological Methods 15(4), 309-334 (2010).",
        "Bennett, M. T. How to Create Conscious Machines. arXiv:2403.00644 (2024).",
    ])
    out = p.build()
    print(f"[gridcell-pdf] wrote {out}")


if __name__ == "__main__":
    build()
