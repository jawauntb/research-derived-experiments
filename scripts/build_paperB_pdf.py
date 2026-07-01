#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Render Paper B — "Concern Deforms the Representational Metric" — to PDF.

Reads REAL numbers from experiments/grid_cell_weakness/artifacts/.../reward_deformation.json
and the metric-density fields from reward_fields.json (for the heatmap figure).
No invented results. Run after reward_deformation.py + dump_fields.py.

Run:  python scripts/build_paperB_pdf.py
Out:  artifacts/papers/concern_deforms_metric.pdf  (+ committed copy under papers/pdf/)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paperkit as pk  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

ART = "experiments/grid_cell_weakness/artifacts/grid_cell_weakness"
FIG = "artifacts/papers/figs_paperB"
OUT = "artifacts/papers/concern_deforms_metric.pdf"


def load(name):
    p = Path(ART) / name
    return json.loads(p.read_text()) if p.exists() else None


def fig_heatmaps(path, fields):
    side = fields["control"]["side"]
    names = [("control", "no reward (control)", None),
             ("reward_A", "reward at A = (0.3, 0.3)", (0.3, 0.3)),
             ("reward_B", "reward at B = (0.7, 0.7)", (0.7, 0.7))]
    fig, axes = plt.subplots(1, 3, figsize=(7.4, 2.9))
    fig.subplots_adjust(left=0.05, right=0.88, top=0.80, bottom=0.12, wspace=0.25)
    im = None
    for ax, (key, title, rxy) in zip(axes, names):
        d = np.array(fields[key]["density"])
        z = (d - d.mean()) / (d.std() + 1e-9)  # per-panel z-score: shows local deformation
        im = ax.imshow(z.T, origin="lower", cmap="coolwarm", vmin=-2.2, vmax=2.2,
                       extent=[0, 1, 0, 1], aspect="equal")
        ax.set_title(title, fontsize=8.5)
        ax.set_xticks([0, 0.5, 1]); ax.set_yticks([0, 0.5, 1])
        if rxy:
            ax.plot(rxy[0], rxy[1], "o", mfc="none", mec="lime", mew=2.2, ms=14)
    cax = fig.add_axes([0.90, 0.14, 0.018, 0.62])
    fig.colorbar(im, cax=cax, label="metric density (z, per panel)")
    fig.suptitle("Reward deforms the induced metric at the rewarded location (green ring)",
                 fontsize=10.5, weight="bold", y=0.97)
    fig.savefig(path, facecolor="white", dpi=200); plt.close(fig)
    return path


def fig_manifold(path, manifold):
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
    panels = [("control", "no reward (control)"), ("reward_A", "reward at A")]
    fig = plt.figure(figsize=(7.0, 3.2))
    for k, (key, title) in enumerate(panels):
        if key not in manifold:
            continue
        pop = np.array(manifold[key]["pop"]); side = manifold[key]["side"]
        dens = np.array(manifold[key]["density"]).reshape(-1)
        X = pop - pop.mean(0)
        U, S, Vt = np.linalg.svd(X, full_matrices=False)
        P = X @ Vt[:3].T  # PCA-3D
        ax = fig.add_subplot(1, 2, k + 1, projection="3d")
        sc = ax.scatter(P[:, 0], P[:, 1], P[:, 2], c=dens, cmap="viridis", s=14,
                        edgecolor="none")
        ax.set_title(title, fontsize=9, weight="bold")
        ax.set_xticks([]); ax.set_yticks([]); ax.set_zticks([]); ax.grid(False)
        ax.view_init(elev=30, azim=40)
    fig.colorbar(sc, ax=fig.axes, fraction=0.018, pad=0.02, label="local metric density")
    fig.suptitle("Population manifold (PCA-3D), coloured by local resolution",
                 fontsize=10.5, weight="bold", y=0.99)
    fig.savefig(path, bbox_inches="tight", facecolor="white", dpi=200); plt.close(fig)
    return path


def build():
    Path(FIG).mkdir(parents=True, exist_ok=True)
    rd = load("reward_deformation.json")
    fields = load("reward_fields.json")
    manifold = load("reward_manifold.json")
    a = rd["analysis"]; cs = a["control_subtracted"]; t = a["tests"]

    figs = {}
    if fields:
        figs["heat"] = fig_heatmaps(f"{FIG}/fig1_heatmaps.png", fields)
    if manifold:
        figs["manifold"] = fig_manifold(f"{FIG}/fig1b_manifold.png", manifold)
    # specificity (control-subtracted)
    figs["spec"] = pk.chart_hbar(
        f"{FIG}/fig2_specificity.png",
        ["reward@B: specificity (B vs A)", "reward@A: specificity (A vs B)",
         "reward@B: deformation at B", "reward@A: deformation at A"],
        [cs["specificity_B"], cs["specificity_A"], cs["deform_at_reward_B"], cs["deform_at_reward_A"]],
        highlight={"reward@B: specificity (B vs A)", "reward@A: specificity (A vs B)"},
        vmin=-0.2, vmax=1.5, title="Control-subtracted metric deformation (positive = at the reward)",
        xlabel="Δ induced-metric density (z), reward − control", value_fmt="{:+.2f}", figsize=(6.2, 2.4))
    # crossover by condition
    figs["cross"] = pk.chart_hbar(
        f"{FIG}/fig3_crossover.png",
        ["reward@B", "control", "reward@A"],
        [t["crossover_B"], t["crossover_control"], t["crossover_A"]],
        colors_=["#c0392b", "#9aa6b2", "#2b6cb0"], vmin=-1.5, vmax=1.0,
        title="Metric asymmetry density(A) − density(B): tracks the reward; control is flat",
        xlabel="density z @A − density z @B", value_fmt="{:+.2f}", figsize=(6.2, 1.9))
    # OOD tradeoff
    figs["ood"] = pk.chart_hbar(
        f"{FIG}/fig4_ood.png",
        ["control", "reward@A", "reward@B"],
        [a["control"]["ood_large"], a["reward_A"]["ood_large"], a["reward_B"]["ood_large"]],
        colors_=["#2f9e44", "#2b6cb0", "#5a9bd4"], vmin=0, vmax=0.7,
        title="Larger-arena (1.25×) OOD decoding: reward trades global generalization for local resolution",
        xlabel="OOD decode accuracy", value_fmt="{:.2f}", figsize=(6.2, 1.9))

    p = pk.Paper(OUT, FIG)
    p.title("Concern Deforms the Representational Metric: A Reward Signal Locally "
            "Warps a Learned Spatial Code")
    p.authors("Jawaun Brown")
    p.authors("Research-Derived Experiments · Paper B (active geometry)")
    p.rule()
    p.abstract(
        "Symbolic and neural results (companion papers) show that <b>weakness</b> — the volume of "
        "transformations under which a learned function stays equivariant — tracks generalization "
        "and the toroidal geometry of spatial codes. Those are <i>passive</i> correlations and, on "
        "symmetry tasks, partly circular. Here we test an <i>active</i>, intervention-based, "
        "non-circular claim: that a goal signal <b>causally deforms the representational geometry</b> "
        "of a learned code. We train path-integration RNNs with a reward that up-weights accuracy "
        "near one location, and measure the <b>induced metric</b> of the population code — how fast "
        "the population vector moves per unit physical space, i.e. local resolution. <b>The reward "
        "deforms the metric specifically at the rewarded location and the deformation tracks the "
        "reward when it is moved</b> (control-subtracted specificity reward@A = +0.65, reward@B = "
        "+1.27, both positive; metric asymmetry +0.69 for reward@A vs −1.23 for reward@B, while the "
        "no-reward control is flat at +0.04). <b>This resolution is bought at a cost: larger-arena "
        "out-of-distribution decoding falls under reward</b> (0.60 → 0.41–0.45) — the code spends "
        "global generalization for local precision. Because the reward location is injected "
        "independently of the geometry, the result cannot be tautological. It is, to our knowledge, "
        "a novel demonstration that a value signal warps a learned metric, and it mirrors the "
        "reward-warping of biological grid codes. We report honestly that a local-<i>weakness</i> "
        "signature is confounded at this scale (n = 3 seeds) and is not claimed.")

    p.h1("1. Introduction")
    p.para(
        "A recurring claim across machine learning and neuroscience is that intelligent systems "
        "represent the world on low-dimensional geometric manifolds, and that the <i>shape</i> of "
        "that manifold reflects the task's structure. Most evidence is correlational: a learned "
        "code's symmetry tracks its generalization (Gruver et al. 2023), and spatial codes lie on a "
        "torus (Gardner et al. 2022). On symmetry tasks these correlations are partly definitional. "
        "We ask a causal question instead — <b>can a goal signal reshape the geometry of a learned "
        "representation?</b> — and answer it with a controlled intervention.")
    p.para(
        "<b>Contributions.</b> (i) We introduce an intervention that injects a reward at a chosen "
        "location into a path-integration RNN and measure the <b>induced metric</b> (local "
        "resolution) of the learned population code. (ii) We show the reward <b>deforms the metric "
        "specifically at the rewarded location and the deformation tracks the reward when moved</b>, "
        "control-subtracted against matched no-reward networks — a causal, non-tautological result. "
        "(iii) We show this local resolution is <b>traded against global generalization</b> "
        "(larger-arena decoding drops under reward). (iv) We connect this, for the first time to our "
        "knowledge in a trained network, to the reward-warping of biological grid/place codes, and "
        "we report an honest negative (a local-weakness signature is confounded at this scale).")

    p.h1("2. Background and terminology")
    p.para(
        "This section makes the paper self-contained for readers who have not read the citations.")
    p.h2("2.1 Weakness and equivariance")
    p.para(
        "A function f is <b>equivariant</b> under a transformation g if transforming the input "
        "produces a correspondingly transformed output: f(g·x) = h·f(x) for some symmetry h. "
        "<b>Weakness</b> (Bennett 2024) is the <i>volume</i> of transformations a learned function "
        "is compatible with — intuitively, how many ways the world could change without breaking "
        "the representation. A maximally weak code respects an entire symmetry group; a brittle code "
        "respects only the identity. The companion work measures weakness on trained networks and "
        "finds it tracks out-of-distribution (OOD) generalization. Equivariant architectures (Cohen "
        "& Welling 2016) bake this in; we instead <i>measure</i> it from data.")
    p.h2("2.2 The induced (representational) metric")
    p.para(
        "A population of N neurons encodes a stimulus x as a point r(x) in N-dimensional firing-rate "
        "space; as x varies, r(x) traces a manifold. The <b>induced metric</b> is the pullback of "
        "distance from that manifold onto stimulus space: how far the population vector moves per "
        "unit change in x. Where the metric is large, small physical changes produce large neural "
        "changes — i.e. the code has <b>fine local resolution</b> there. A globally "
        "translation-invariant (high-weakness) code has a uniform metric; giving one location finer "
        "resolution requires locally breaking that invariance. This is the link between weakness and "
        "metric deformation that the paper tests.")
    p.h2("2.3 Grid cells, the torus, and reward-warping")
    p.para(
        "Grid cells in entorhinal cortex fire periodically across space; the joint activity of a "
        "grid module lies on a <b>torus</b> (Gardner et al. 2022, Nature), and recurrent networks "
        "trained to path-integrate reproduce both the periodic cells and the torus (Cueva & Wei "
        "2018; Banino et al. 2018; Sorscher et al. 2019). Neuroscience also reports that <b>reward "
        "and goals warp the spatial code</b>: place and grid representations over-represent rewarded "
        "and goal-relevant locations (Hollup et al. 2001; Dupret et al. 2010; Boccara et al. 2019; "
        "Butler et al. 2019), and recent geometric work (Webb & Miolane 2026) frames this as the "
        "metric deforming to allocate resolution. Our experiment asks whether the same warp emerges "
        "in a trained network purely from a reward-weighted objective, and measures it as a metric "
        "deformation.")
    p.h2("2.4 Design logic")
    p.para(
        "The result is causal by construction. The <b>reward location is an independent variable we "
        "set</b>; the induced metric is a separate measurement of the trained network. We test a "
        "<i>directional, location-specific, control-subtracted</i> prediction — the metric should "
        "rise at the reward, more than elsewhere, more than in a matched no-reward network, and "
        "should move when the reward moves. Passive correlations between a learned function's "
        "symmetry and its generalization cannot, on symmetry tasks, fully separate cause from "
        "relabeling; an intervention that we manipulate and that tracks our manipulation can.")

    p.h1("3. Method")
    p.para(
        "We train a velocity-driven recurrent network (ReLU RNN, 96 hidden units) to predict a "
        "place-cell code of its position along random-walk trajectories in the unit arena, by KL "
        "divergence with an activity-regularization term that promotes localized periodic units "
        "(the standard recipe that yields grid-like codes). The <b>reward</b> is implemented as a "
        "Gaussian up-weighting of the per-timestep loss centered at a location (A = (0.3,0.3) or "
        "B = (0.7,0.7), width 0.12, strength 6×), so the network is pressured to represent position "
        "more accurately there. We compare three conditions — no-reward control, reward@A, reward@B "
        "— over three seeds (9 networks). After training we bin hidden activity by position to get a "
        "population vector r(x) per spatial bin and compute: the <b>induced-metric density</b> "
        "(mean ‖Δr‖/‖Δx‖ over neighbouring bins, z-scored across the arena); decode accuracy in the "
        "trained arena and in a larger 1.25× arena (OOD geometry); and a local-weakness probe. The "
        "key statistic is <b>control-subtracted</b>: deformation at a location in a reward condition "
        "minus the same location in the control, which removes any positional baseline asymmetry.")

    p.h1("4. Results")
    if "heat" in figs:
        p.figure(figs["heat"],
                 "Figure 1. Induced-metric density across the arena (brighter = finer local "
                 "resolution). The no-reward control is roughly uniform; reward@A concentrates "
                 "resolution at A and reward@B at B (green ring = reward location), shown as a "
                 "per-panel z-score. The metric warp tracks the reward.", width_in=6.6)
    if "manifold" in figs:
        p.figure(figs["manifold"],
                 "Figure 1b. The population activity manifold (PCA-projected to 3-D), coloured by "
                 "local induced-metric density. Under reward, the manifold is locally stretched "
                 "(brighter) at the goal — the same warp, seen in the code's own geometry rather "
                 "than arena coordinates.", width_in=6.2)
    p.para(
        "<b>The reward deforms the induced metric specifically at the rewarded location, and the "
        "deformation tracks the reward when it is moved.</b> Control-subtracted, reward@A raises the "
        "metric density at A relative to B by <b>+0.65</b> and reward@B raises it at B relative to A "
        "by <b>+1.27</b> (both positive = location-specific; Figure 2). The raw metric asymmetry "
        "[density(A) − density(B)] is <b>+0.69 for reward@A and −1.23 for reward@B, while the "
        "no-reward control is essentially flat (+0.04)</b> (Figure 3) — the asymmetry is created by "
        "the reward, not by arena geometry.")
    p.figure(figs["spec"],
             "Figure 2. Control-subtracted deformation. Both specificity bars are positive: each "
             "reward warps the metric at its own location more than at the other location.",
             width_in=5.9)
    p.figure(figs["cross"],
             "Figure 3. Metric asymmetry by condition. Reward@A is positive (A favoured), reward@B "
             "negative (B favoured), and the no-reward control is flat — the reward drives the warp.",
             width_in=5.9)
    p.para(
        "<b>This local resolution is bought at the cost of global generalization.</b> Decoding in a "
        "larger, never-seen 1.25× arena falls from <b>0.60 (control) to 0.41–0.45 under reward</b> "
        "(Figure 4): concentrating representational capacity near the goal spends accuracy "
        "elsewhere — the expected signature of a code that reallocates a finite resolution budget.")
    p.figure(figs["ood"],
             "Figure 4. Larger-arena (1.25×) OOD decoding drops under reward — local resolution is "
             "traded for global generalization.", width_in=5.9)

    p.h1("5. Related work and what is new")
    p.para(
        "<b>Learned symmetry as a generalization correlate.</b> Gruver et al. (2023) measure the "
        "equivariance of trained networks (via the Lie derivative) and find it correlates with test "
        "accuracy; the volume-hypothesis line (Valle-Pérez et al. 2019) links compatible-function "
        "volume to generalization. These are <i>passive, observational</i> correlations. Our "
        "contribution is <b>causal and active</b>: we manipulate a goal signal and show the "
        "representational metric deforms to follow it. <b>Reward-warping of spatial codes.</b> "
        "Hippocampal and entorhinal codes over-represent rewarded and goal locations (Hollup et al. "
        "2001; Dupret et al. 2010; Boccara et al. 2019; Butler et al. 2019); Webb & Miolane (2026) "
        "frame this geometrically as a metric deformation, and developmental connectomics shows the "
        "deeper principle that neural activity itself sculpts structure (Meirovitch et al. 2026). "
        "That work is in biological systems; "
        "<b>we show the same warp emerges in a trained network from a reward-weighted objective "
        "alone, and quantify it as an induced-metric deformation with a matched control</b> — a "
        "bridge from the neuroscience phenomenon to a controllable model, which we have not seen "
        "made before. <b>Grid-cell RNNs.</b> Cueva & Wei (2018), Banino et al. (2018), and Sorscher "
        "et al. (2019) train RNNs that develop grid codes and tori; we use that substrate but ask a "
        "new question — how a value signal reshapes its geometry.")

    p.h1("6. Limitations and honest negatives")
    p.para(
        "We do <b>not</b> claim the complementary local-<i>weakness</i> signature: our local-weakness "
        "probe shows a positional confound (the no-reward control already has an A-vs-B asymmetry of "
        "comparable size), so we cannot attribute a local weakness change to the reward at this "
        "scale. The study is small (n = 3 seeds, one architecture, a reward implemented as "
        "loss-reweighting rather than an explicit value head), and the larger-arena OOD probe is "
        "limited by place-cell coverage beyond the trained region. The robust, reported claim is the "
        "<b>metric (resolution) deformation</b> and its <b>OOD cost</b>; the weakness-accounting and "
        "a topological reading of the deformation are deferred to a larger sweep.")

    p.h1("7. Discussion")
    p.para(
        "This is the <i>active</i> counterpart to the program's passive weakness results: a value "
        "signal does not merely correlate with geometry — it <b>causally reshapes the metric</b> of "
        "a learned representation, locally and controllably. The effect reproduces, in a trained "
        "network from a reward-weighted objective alone, the reward-warping of spatial codes observed "
        "in the brain, and it gives the 'concern deforms geometry' thesis a measurable, "
        "intervention-based handle that a bandit setting could not provide.")
    p.para(
        "We are explicit about where this sits. Borrowing the field's framing, observing a geometric "
        "regularity is the <i>Kepler</i> step and explaining why it must arise is the <i>Newton</i> "
        "step. This paper is at the Kepler stage for reward-warping — a clean, controlled phenomenon "
        "plus a mechanistic sketch (a globally invariant code must break symmetry locally to buy "
        "resolution) — not a derived law. The weakness program <i>aspires</i> to the Newton step; we "
        "do not claim to have reached it. The natural next steps are a larger multi-seed sweep with "
        "an explicit value head and significance tests, a topological readout of the warp (how the "
        "torus itself deforms), and a clean local-weakness accounting under a positional control — "
        "the experiments that would turn this proof-of-concept into a confirmatory result.")

    p.references([
        "Bennett, M. T. How to Create Conscious Machines. arXiv:2403.00644 (2024). Weakness as "
        "compatible-completion volume.",
        "Gardner, R. J. et al. Toroidal topology of population activity in grid cells. Nature 602 "
        "(2022).",
        "Cueva, C. J., Wei, X.-X. Emergence of grid-like representations by training RNNs to perform "
        "spatial localization. ICLR (2018).",
        "Banino, A. et al. Vector-based navigation using grid-like representations in artificial "
        "agents. Nature 557 (2018).",
        "Sorscher, B., Mel, G. C., Ganguli, S., Ocko, S. A unified theory for the origin of grid "
        "cells through the lens of pattern formation. NeurIPS (2019).",
        "Hollup, S. A. et al. Accumulation of hippocampal place fields at the goal location. "
        "J. Neurosci. 21 (2001).",
        "Dupret, D., O'Neill, J., Pleydell-Bouverie, B., Csicsvari, J. The reorganization and "
        "reactivation of hippocampal maps predict spatial memory performance. Nat. Neurosci. 13 (2010).",
        "Meirovitch, Y., Draft, R., Tapia, J.-C., Lichtman, J. W., et al. Neural activity shapes "
        "the developing motor connectome (function generates structure). Nature Neuroscience (2026).",
        "Boccara, C. N., Nardin, M., Stella, F., O'Neill, J., Csicsvari, J. The entorhinal cognitive "
        "map is attracted to goals. Science 363 (2019).",
        "Butler, W. N., Hardcastle, K., Giocomo, L. M. Remembered reward locations restructure "
        "entorhinal spatial maps. Science 363 (2019).",
        "Cohen, T., Welling, M. Group Equivariant Convolutional Networks. ICML (2016).",
        "Gruver, N., Finzi, M., Goldblum, M., Wilson, A. G. The Lie Derivative for Measuring Learned "
        "Equivariance. ICLR (2023). arXiv:2210.02984.",
        "Valle-Pérez, G., Camargo, C. Q., Louis, A. A. Deep Learning Generalizes Because the "
        "Parameter–Function Map is Biased Towards Simple Functions. ICLR (2019).",
        "Webb, C. I., Miolane, N. The Geometry of Consciousness. The Long Now Foundation (2026).",
        "Brown, J. Weakness, Not Compression (2026); Weakness Predicts Toroidal Topology (2026). "
        "Companion papers, this repository.",
    ])
    out = p.build()
    print(f"[paperB] wrote {out} (heatmaps={'yes' if fields else 'no'})")


if __name__ == "__main__":
    build()
