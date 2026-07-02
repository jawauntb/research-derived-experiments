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
        title="Vision Z_8 rotated strokes (96 models): predictor correlation with OOD",
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
        "accuracy (r = +0.817, +0.813, +0.8085; 4096 CI +0.798 to +0.819), and an "
        "augmentation-fixed-effect check remains positive (residual r = +0.488). Vision gives "
        "the same ordering (Z_8 rotation, r = +0.672). Parity is a clean negative case, and "
        "S_n is a large-group boundary case: oracle weakness helps, but data-inferred group "
        "discovery degrades. Pythia-70M is reported only in an appendix as latent geometry, "
        "not behavioral evidence.")

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
    p.para(
        "Tiny proposition: if deployment inputs are completed from observed examples by a subset "
        "S of G, then every compatible g in S transports observed labels along its orbit without "
        "contradiction. More compatible transformations therefore cover more of the missing orbit, "
        "provided the candidate group is aligned with the deployment shift.")

    p.h1("3. Symbolic separation")
    p.para(
        "We build four task families, each with a known transformation group and a training "
        "distribution that admits both a train-perfect local shortcut and the true invariant: "
        "<i>cyclic_prefix_shift</i> (ℤ_n), <i>dihedral_reflection</i> (D_n), <i>parity_coset</i> "
        "(Z_2), and <i>color_permutation</i> (S_n). We compare eleven selectors over 500 trials per "
        "family with Wilson 95% intervals. Candidate pools are explicit: cyclic has K=n+1 "
        "(8/12/14 here), dihedral K=3, parity K=4, and color-permutation K=3..6 in the reported "
        "seeded run.")
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
        "on cyclic tasks with n in {7,11,13}, train window w in {2,3,4}, diverse depth, width, "
        "initialization, optimizer, learning rate, weight decay, and augmentation. From each model "
        "we extract the argmax function table and "
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
             "approximately respect the symmetry raise weakness and OOD together; after "
             "augmentation fixed effects, residual r remains +0.488.", width_in=5.0)

    p.h1("5. Scaling: vision")
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
        "The language probe is moved to Appendix C and treated as exploratory latent geometry only; "
        "it is not used as behavioral OOD evidence.")

    p.h1("6. Operating regime and limitations")
    p.para(
        "Weakness ceases to discriminate when the candidate group is too small (parity, |G|=2) or "
        "too large/uninformative (full symmetric group, where wrong involutions have comparable "
        "centralizer-orbit sizes). This is a precise statement of when symmetry-volume is "
        "load-bearing, not a defect. Present limitations: small finite domains (n ≤ 13 symbolic, "
        "16×16 vision); intentionally simple MDL/compression/completion-volume and sharpness "
        "proxies; the language "
        "latent→behavior chain unconfirmed; transformation discovery is still enumerative. The "
        "natural next steps are stronger compression/PAC-Bayes baselines, learned transformation "
        "generators, and training-time weakness regularization.")

    p.h1("7. Discussion")
    p.para(
        "The discriminating quantity between local shortcut and globally invariant rule — on "
        "families where both are train-perfect — is symmetry-compatible-hypothesis volume: a "
        "measurable, intervention-friendly, reparameterization-invariant quantity, not a "
        "parameter-space artifact. It operationalizes Bennett's weakness on neural function tables "
        "and answers the practical question of which heuristic to trust when training loss is "
        "tied. The safe thesis is not that compression is wrong; it is that, in these "
        "shortcut-compatible symmetry tasks, the relevant compression is compatibility with the "
        "transformations that generate the missing cases.")

    p.h1("Appendix A. Methods and statistics")
    p.para(
        "Symbolic families are exact finite tasks. Cyclic uses X=Z_n, n in {7,11,13}, truth "
        "f_b(x)=x+b mod n, a prefix train window, and a suffix OOD set. Dihedral uses X=Z_n, "
        "n in {7,9,11,13}, truth f_b(x)=b-x mod n, and D_n rotations/reflections. Parity uses "
        "an even domain and f(x)=x xor 1 with one parity coset held out. Color-permutation uses "
        "S_n, n in {4,5,6}, a sampled non-identity permutation, sparse training inputs, and "
        "unobserved inputs as OOD.")
    p.table(
        [["Selector", "Score", "Tie-break", "Group access"],
         ["train_loss", "train accuracy", "shorter form", "none"],
         ["validation", "leave-one-observed-pair accuracy", "shorter form", "none"],
         ["simplicity", "shorter form_length", "random exact tie", "none"],
         ["compression", "form_length + 20*train_errors", "random exact tie", "none"],
         ["mdl_program", "2^-form_length", "shorter form", "none"],
         ["flatness_proxy", "completion-volume proxy, not Hessian flatness", "shorter form", "none"],
         ["weakness_oracle", "W_G(f)", "compression", "true task group"],
         ["weakness_wrong_group", "W under random perms", "compression", "wrong control"],
         ["weakness_noisy_group", "W under noisy subset", "compression", "noisy true group"],
         ["weakness_data_inferred", "W under inferred G_hat", "compression", "train pairs only"],
         ["random", "uniform train-perfect candidate", "-", "none"]],
        caption="Appendix Table A1. Exact selector definitions. Classical baselines are the first "
                "six rows; validation is in-distribution only.",
        col_widths=[105, 165, 95, 105])
    p.para(
        "Data-inferred group discovery enumerates a family-specific domain prior (Z_n shifts for "
        "cyclic, D_n rotations/reflections for dihedral, parity swap for parity, and a small cyclic "
        "heuristic for S_n), then keeps every input-side transformation g for which some output-side "
        "transformation h is non-contradictory on observed training pairs. It uses training inputs, "
        "training outputs, and the domain prior only: no test labels, hidden offset, hidden "
        "reflection, sampled permutation, or invariant-candidate identity.")
    p.table(
        [["Statistic", "Value"],
         ["4096 true-group Pearson r", "+0.8085 (95% CI +0.7976 to +0.8189)"],
         ["4096 partial-cyclic Pearson r", "+0.7940 (95% CI +0.7824 to +0.8051)"],
         ["4096 validation Pearson r", "+0.0924 (95% CI +0.0620 to +0.1227)"],
         ["4096 parameter L2 Pearson r", "+0.2533 (95% CI +0.2244 to +0.2818)"],
         ["4096 fixed-effect residual r", "+0.4883 (95% CI +0.4647 to +0.5113)"],
         ["Fixed-effect beta", "+0.3652 (95% CI +0.3452 to +0.3853)"]],
        caption="Appendix Table A2. Fisher-z intervals and augmentation fixed-effect check. "
                "The headline effect is partly augmentation-mediated, but a within-condition "
                "learned-function signal remains.",
        col_widths=[180, 270])

    p.h1("Appendix C. Exploratory language check")
    p.para(
        "Pythia-70M hidden states for 24 concepts x 3 paraphrases show centered same-orbit "
        "cosine gaps of +0.44 to +0.79 after All-but-the-Top centering, but per-concept "
        "next-token behavioral consistency is not predicted at this scale (Pearson range "
        "-0.35 to -0.13, N=24). This supports only a latent-geometry statement: paraphrase "
        "orbits cluster in centered representation space.")
    p.figure(f["lang"],
             "Appendix Figure C1. Pythia-70M paraphrase orbits cluster in centered latent space "
             "(gap peaks at +0.79, layer 5). This is a latent-geometry result only.", width_in=5.2)

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
        "[19] Arjovsky, M., Bottou, L., Gulrajani, I., Lopez-Paz, D. Invariant Risk Minimization. "
        "arXiv:1907.02893 (2019).",
        "[20] Zhou, K., Liu, Z., Qiao, Y., Xiang, T., Loy, C. C. Domain Generalization: A Survey. "
        "arXiv:2103.02503 (2021).",
        "[21] Rissanen, J. Modeling by Shortest Data Description. Automatica 14(5):465-471 (1978).",
        "[22] Grunwald, P. D. The Minimum Description Length Principle. MIT Press (2007).",
        "[23] Mingard, C. et al. Neural Networks are a Priori Biased Towards Boolean Functions "
        "with Low Entropy. arXiv:1909.11522 (2019).",
    ])
    out = p.build()
    print(f"[weakness-pdf] wrote {out}")


if __name__ == "__main__":
    build()
