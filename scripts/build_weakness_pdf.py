#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Render the flagship weakness paper to a polished PDF with charts.

Numbers are taken verbatim from papers/weakness_invariance_neurips/paper.md
(which reconcile with the committed result artifacts). No new results invented.

Run:  python scripts/build_weakness_pdf.py
Out:  artifacts/papers/weakness_predicts_ood.pdf
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paperkit as pk  # noqa: E402

FIG = "artifacts/papers/figs_weakness"
OUT = "artifacts/papers/weakness_predicts_ood.pdf"


def figures():
    Path(FIG).mkdir(parents=True, exist_ok=True)
    f = {}
    # Fig 1: symbolic separation (invariant-recovery rate), cyclic & dihedral
    f["sep"] = pk.chart_grouped_bar(
        f"{FIG}/fig1_symbolic_separation.png",
        groups=["cyclic  Z_n", "dihedral  D_n"],
        series={"weakness (oracle)": [1.000, 1.000],
                "weakness (data-inferred)": [1.000, 1.000],
                "classical baselines": [0.000, 0.000],
                "wrong-group control": [0.002, 0.018]},
        title="Symbolic benchmark: invariant-rule recovery (500 trials/family)",
        ylabel="P(recovers invariant)", ymax=1.08,
        colors_=["#2b6cb0", "#3b9c5a", "#9aa6b2", "#c0392b"], figsize=(6.0, 3.2))
    # Fig 2: neural predictor ranking (256-MLP sweep), Pearson r with OOD
    labels = ["weakness (true group)", "weakness (partial-cyclic)", "parameter L₂",
              "Hutchinson sharpness", "held-out validation", "training loss",
              "weakness (random-label ctrl)", "weakness (wrong-group ctrl)"]
    vals = [0.817, 0.804, 0.099, 0.129, 0.096, -0.031, -0.116, -0.129]
    f["neural"] = pk.chart_hbar(
        f"{FIG}/fig2_neural_predictors.png", labels, vals,
        highlight={"weakness (true group)"}, vmin=-0.3, vmax=1.0,
        title="Neural sweep (256 MLPs): correlation of each predictor with OOD accuracy",
        xlabel="Pearson r with OOD accuracy", figsize=(6.2, 3.2))
    # Fig 3: per-augmentation monotone gradient (4096 MLPs, 2026-07-02 Modal rescale)
    augs = ["", "", "", "partial\ncyclic", "full\ncyclic"]
    weak = [0.1157, 0.1315, 0.1230, 0.3678, 0.9545]
    ood = [0.0000, 0.0135, 0.0877, 0.6438, 0.9434]
    f["grad"] = pk.chart_scatter_gradient(
        f"{FIG}/fig3_augmentation_gradient.png", weak, ood, labels=augs,
        title="4096 MLPs: OOD rises with weakness",
        xlabel="mean weakness (normalized)", ylabel="mean OOD accuracy", figsize=(5.4, 3.4))
    # Fig 4: vision Z_8 predictor ranking
    vlabels = ["weakness (rotation)", "parameter L₂", "train accuracy",
               "Hutchinson sharpness", "training loss", "weakness (wrong-group ctrl)"]
    vvals = [0.672, 0.333, 0.332, 0.198, -0.319, -0.341]
    f["vision"] = pk.chart_hbar(
        f"{FIG}/fig4_vision_predictors.png", vlabels, vvals,
        highlight={"weakness (rotation)"}, vmin=-0.45, vmax=0.8,
        title="Vision ℤ₈ rotated strokes (96 models): predictor correlation with OOD",
        xlabel="Pearson r with OOD accuracy", figsize=(6.2, 2.6))
    # Fig 5: language paraphrase-orbit gap by layer (centered)
    layers = list(range(7))
    f["lang"] = pk.chart_line(
        f"{FIG}/fig5_language_gap.png", layers,
        {"same-orbit (paraphrase)": [0.400, 0.568, 0.565, 0.718, 0.742, 0.726, 0.700],
         "wrong-orbit (control)": [-0.038, -0.020, -0.030, 0.029, 0.008, -0.067, -0.014],
         "gap": [0.438, 0.588, 0.596, 0.689, 0.734, 0.793, 0.713]},
        title="Pythia-70M: paraphrase orbits cluster in centered latent space",
        xlabel="layer", ylabel="centered cosine", figsize=(5.6, 3.1))
    return f


def build():
    f = figures()
    p = pk.Paper(OUT, FIG)
    p.title("Symmetry-Compatible Hypothesis Volume Predicts "
            "Out-of-Distribution Generalization")
    p.authors("Jawaun Brown")
    p.authors("Weakness, not generic compression alone, in shortcut-compatible learning problems")
    p.authors("Research-Derived Experiments · preprint compiled from the project repository")
    p.rule()
    p.abstract(
        "We study finite-domain model selection where training data admits both a local shortcut "
        "and a globally symmetry-compatible rule. Loss and in-distribution validation cannot "
        "distinguish the completions, and generic simplicity or flatness proxies can prefer the "
        "shortcut. We define <b>weakness</b> as the number of transformations under which a "
        "candidate function remains equivariant up to an output action. On cyclic and dihedral "
        "symbolic families (500 trials each), weakness recovers the invariant rule in 100% of "
        "trials (Wilson 95% lower bound 0.992) while the tested train-loss, validation, "
        "description-length, MDL-style, compression, and flatness proxies recover it in 0% "
        "(upper bound 0.008). A <b>data-inferred</b> selector, built from circular-domain "
        "transformation enumeration plus training-pair consistency, matches the oracle without "
        "using the hidden offset or reflection parameter. Across 256, 1024, and 4096 trained "
        "MLPs, learned-function weakness under the true group is the strongest correlate of OOD "
        "accuracy (r = +0.817, +0.813, +0.8085). Vision gives the same ordering (ℤ₈ rotation, "
        "r = +0.672). Parity and S_n are honest negative cases; the Pythia-70M result is "
        "reported only as latent geometry, not behavioral evidence.")

    p.h1("1. Introduction")
    p.para(
        "Modern pipelines are often underspecified: many predictors have equivalent training or "
        "in-distribution validation performance but different deployment behavior. Shortcut "
        "learning is one familiar failure mode. Here we make the ambiguity explicit: the training "
        "data is compatible with both a local shortcut and a globally transportable rule. If the "
        "deployment distribution is generated by transformations, the relevant question is not "
        "only which hypothesis is shortest, but which hypothesis remains valid under those "
        "transformations. This paper tests Bennett-style <i>weakness</i> — compatible "
        "transformation volume — as a finite, measurable selection rule.")

    p.h1("2. Weakness")
    p.para(
        "Let f : X → X be a candidate function on a finite domain of size n, and let G act on X. "
        "We call f <i>compatible</i> with g ∈ G if there exists h ∈ G with f(g·x) = h·f(x) for all "
        "x (with-action equivariance; this generalizes strict equivariance h = g). Weakness is the "
        "count of compatible group elements:")
    p.para("<b>&nbsp;&nbsp;&nbsp;&nbsp;W_G(f) = | { g ∈ G : ∃ h ∈ G, ∀x, f(g·x) = h·f(x) } |.</b>")
    p.para(
        "W_G(f) = |G| means f is fully G-equivariant; W_G(f) = 1 means only the identity commutes. "
        "The <i>weakness selector</i> returns argmax_i W_Ĝ(f_i) over a candidate pool, ties broken "
        "by the same compression proxy used by the baselines. Selection principle: when training "
        "constrains only part of a transformation orbit, train-consistent hypotheses compatible "
        "with more deployment-generating transformations should cover more of the missing orbit.")

    p.h1("3. Symbolic separation")
    p.para(
        "We build four task families, each with a known transformation group and a training "
        "distribution that admits both a train-perfect local shortcut and the true invariant: "
        "<i>cyclic_prefix_shift</i> (ℤ_n), <i>dihedral_reflection</i> (D_n), <i>parity_coset</i> "
        "(ℤ₂), and <i>color_permutation</i> (S_n). We compare eleven selectors over 500 trials per "
        "family with Wilson 95% intervals.")
    p.figure(f["sep"],
             "Figure 1. On cyclic and dihedral families, only weakness-based selectors recover "
             "the invariant rule (1.000; Wilson LB 0.992); training loss, simplicity, MDL, "
             "compression, flatness, and validation all recover it 0.000 (UB 0.008). The "
             "data-inferred selector uses circular-domain enumeration plus training-pair "
             "consistency, not the hidden offset/reflection, and matches the oracle. The "
             "wrong-group control is near zero.", width_in=5.7)
    p.table(
        [["Family", "weakness (oracle)", "data-inferred", "classical baselines", "wrong-group"],
         ["cyclic Z_n", "1.000", "1.000", "0.000", "0.002"],
         ["dihedral D_n", "1.000", "1.000", "0.000", "0.018"],
         ["color S_n (partial)", "0.824", "0.138", "0.000", "0.000"],
         ["parity Z_2 (negative)", "0.000", "0.000", "0.000", "0.038"]],
        caption="Table 1. Invariant-recovery rate by selector and family. Cyclic and dihedral "
                "show a perfect, non-overlapping separation; S_n is a partial win; parity is a "
                "clean negative (|G|=2 too small to disambiguate).",
        col_widths=[120, 95, 80, 110, 80])

    p.h1("4. Neural weakness predicts OOD accuracy")
    p.para(
        "We train 256 small MLPs, replicate at 1024 models, and rescale to 4096 models via Modal "
        "on cyclic tasks with diverse depth, width, initialization, optimizer, learning rate, "
        "weight decay, and augmentation. From each model we extract the argmax function table and "
        "compute true-group weakness together with classical predictors, correlating each against "
        "held-out OOD accuracy.")
    p.figure(f["neural"],
             "Figure 2. Across 256 MLPs, weakness under the true group is the single strongest "
             "predictor of OOD accuracy (Pearson r = +0.817 locally, +0.813 at 1024 models, "
             "+0.8085 at 4096 models). Training loss, validation, parameter L₂, and sharpness are "
             "weaker; wrong-group and random-label controls are correctly negative.", width_in=5.9)
    p.figure(f["grad"],
             "Figure 3. The per-augmentation gradient is monotone in weakness: full-cyclic "
             "(orbit completion) reaches 94% OOD and 0.95 weakness, while none / "
             "wrong-reflection collapse to ≤1.4% OOD and ≤0.13 weakness. Augmentations that "
             "approximately respect the symmetry raise weakness and OOD together.", width_in=5.0)

    p.h1("5. Scaling: vision and language")
    p.para(
        "On a synthetic Z_8 rotated-stroke task (eight classes, 16×16, three of eight angles shown "
        "in training; a re-implementation of Perin and Deny's partial-orbit setup), weakness under "
        "the rotation group is again the dominant predictor across 96 models (r = +0.67), beating "
        "every classical predictor by ≥2×, with the pixel-permutation wrong-group control correctly "
        "anti-correlated (r = −0.34).")
    p.figure(f["vision"],
             "Figure 4. Vision (Z_8 rotation): weakness leads; the wrong-group (pixel-shuffle) "
             "control is anti-correlated, as expected of a model that has actually learned the "
             "rotation symmetry.", width_in=5.9)
    p.para(
        "In language, we extract per-layer mean-pooled Pythia-70M states for 24 concepts × 3 "
        "paraphrases. After per-layer centering (All-but-the-Top), same-orbit paraphrase cosine "
        "exceeds the wrong-orbit control by +0.44 to +0.79 (peak at layer 5): paraphrase orbits "
        "genuinely cluster. We report honestly that this latent clustering does <i>not</i> yet "
        "predict next-token behavioral consistency at this scale (per-concept |r| ≤ 0.35, N = 24) — "
        "the latent-geometry claim holds; the latent→behavior chain is unconfirmed at 70M.")
    p.figure(f["lang"],
             "Figure 5. Pythia-70M paraphrase orbits cluster strongly in centered latent space "
             "(gap peaks at +0.79, layer 5). This is a latent-geometry result only; the "
             "latent-to-behavior prediction is not confirmed at this scale.", width_in=5.2)

    p.h1("6. Operating regime and limitations")
    p.para(
        "Weakness ceases to discriminate when the candidate group is too small (parity, |G|=2) or "
        "too large/uninformative (full symmetric group, where wrong involutions have comparable "
        "centralizer-orbit sizes). This is a precise statement of when symmetry-volume is "
        "load-bearing, not a defect. Present limitations: small finite domains (n ≤ 13 symbolic, "
        "16×16 vision); intentionally simple MDL/compression/flatness proxies; the language "
        "latent→behavior chain unconfirmed; transformation discovery is still enumerative. The "
        "natural next steps are stronger compression/PAC-Bayes baselines, learned transformation "
        "generators, and training-time weakness regularization.")

    p.h1("7. Discussion")
    p.para(
        "The discriminating quantity between local shortcut and globally invariant rule — on "
        "families where both are train-perfect — is symmetry-compatible-hypothesis volume: a "
        "measurable, intervention-friendly, reparameterization-invariant quantity, not a "
        "parameter-space artifact. It operationalizes Bennett's weakness on neural function tables "
        "and bridges the manifold-hypothesis intuition (intelligence needs symmetry-preserving "
        "compression) with the practical question of which heuristic to trust when training loss is "
        "tied. The safe thesis is not that compression is wrong; it is that, in these "
        "shortcut-compatible symmetry tasks, the relevant compression is compatibility with the "
        "transformations that generate the missing cases.")

    p.references([
        "[1] Bennett, M. T. How to Create Conscious Machines. arXiv:2403.00644 (2024).",
        "[2] Bennett, M. T. Are Flat Minima an Illusion? arXiv:2605.05209 (2026).",
        "[3] Bronstein, M. M., Bruna, J., Cohen, T., Velickovic, P. Geometric Deep Learning. "
        "arXiv:2104.13478 (2021).",
        "[4] Cohen, T. and Welling, M. Group Equivariant Convolutional Networks. ICML (2016).",
        "[5] D'Amour, A. et al. Underspecification Presents Challenges for Credibility in Modern "
        "Machine Learning. JMLR (2022).",
        "[6] Dinh, L., Pascanu, R., Bengio, S., Bengio, Y. Sharp Minima Can Generalize for Deep "
        "Nets. ICML (2017).",
        "[7] Geirhos, R. et al. Shortcut Learning in Deep Neural Networks. Nature Machine "
        "Intelligence (2020).",
        "[8] Hochreiter, S. and Schmidhuber, J. Flat Minima. Neural Computation 9(1):1–42 (1997).",
        "[9] Hutter, M. Universal Artificial Intelligence. Springer (2005).",
        "[10] Keskar, N. S. et al. On Large-Batch Training for Deep Learning. ICLR (2017).",
        "[11] Kondor, R. and Trivedi, S. On the Generalization of Equivariance and Convolution in "
        "Neural Networks to the Action of Compact Groups. ICML (2018).",
        "[12] Liu, Z., Michaud, E. J., Tegmark, M. Omnigrok: Grokking Beyond Algorithmic Data. ICLR "
        "(2023).",
        "[13] Mu, J. and Viswanath, P. All-but-the-Top. ICLR (2018).",
        "[14] Perin, A. and Deny, S. On the Ability of Deep Networks to Learn Symmetries from Data. "
        "arXiv:2412.11521 "
        "(2024).",
        "[15] Power, A. et al. Grokking: Generalization Beyond Overfitting on Small Algorithmic "
        "Datasets. ICLR Workshop (2022).",
        "[16] Solomonoff, R. J. A Formal Theory of Inductive Inference, I & II. Information and "
        "Control 7 (1964).",
        "[17] Valle-Perez, G., Camargo, C. Q., Louis, A. A. Deep Learning Generalizes Because the "
        "Parameter–Function Map is Biased Towards Simple Functions. ICLR (2019).",
        "[18] van der Ouderaa, T. F. A., Immer, A., van der Wilk, M. Learning Layer-wise "
        "Equivariances Automatically using Gradients. NeurIPS (2023).",
    ])
    out = p.build()
    print(f"[weakness-pdf] wrote {out}")


if __name__ == "__main__":
    build()
