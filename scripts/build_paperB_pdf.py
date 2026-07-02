#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Render Paper B after the 2026-07-02 Modal reward-deformation sweep.

Run:  python scripts/build_paperB_pdf.py
Out:  artifacts/papers/concern_deforms_metric.pdf
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paperkit as pk  # noqa: E402

FIG = "artifacts/papers/figs_paperB"
OUT = "artifacts/papers/concern_deforms_metric.pdf"

GEOS = ["aniso2d", "stripe", "point"]
ALPHA_A6 = [0.309, 0.302, 0.283]
ALPHA_A6_LO = [0.304, 0.298, 0.278]
ALPHA_A6_HI = [0.314, 0.307, 0.288]
PEAK = {
    "aniso2d": [1.300, 1.369, 1.443],
    "stripe": [1.289, 1.348, 1.428],
    "point": [1.319, 1.400, 1.515],
}


def fig_specificity(path: str) -> str:
    return pk.chart_hbar(
        path,
        ["reward@B specificity", "reward@A specificity", "reward@B deformation", "reward@A deformation"],
        [1.27, 0.65, 1.27, 0.65],
        highlight={"reward@B specificity", "reward@A specificity"},
        vmin=0,
        vmax=1.5,
        title="Original moved-location proof-of-concept: metric deformation tracks reward",
        xlabel="control-subtracted metric-density change",
        value_fmt="{:+.2f}",
        figsize=(6.2, 2.3),
    )


def fig_exponent(path: str) -> str:
    import matplotlib.pyplot as plt
    import numpy as np

    x = np.arange(len(GEOS))
    yerr = [[m - l for m, l in zip(ALPHA_A6, ALPHA_A6_LO)], [h - m for m, h in zip(ALPHA_A6, ALPHA_A6_HI)]]
    fig, ax = plt.subplots(figsize=(5.8, 3.2))
    ax.bar(x, ALPHA_A6, color=["#2b6cb0", "#2f9e44", "#e8a13a"], width=0.62)
    ax.errorbar(x, ALPHA_A6, yerr=yerr, fmt="none", ecolor="#222", capsize=4, lw=1.0)
    ax.axhline(1 / 3, color="#444", ls="--", lw=1.0, label="1-D prediction 1/3")
    ax.axhline(0.5, color="#c0392b", ls=":", lw=1.2, label="2-D prediction 1/2")
    ax.set_xticks(x)
    ax.set_xticklabels(["anisotropic 2-D", "stripe", "point"])
    ax.set_ylim(0.22, 0.54)
    ax.set_ylabel("area-density exponent α")
    ax.set_title("Modal Newton gate: aniso2d stays near 1/3, not 1/2")
    ax.legend(fontsize=7.5)
    ax.grid(axis="x", visible=False)
    fig.savefig(path, bbox_inches="tight", facecolor="white", dpi=220)
    plt.close(fig)
    return path


def fig_peak(path: str) -> str:
    import matplotlib.pyplot as plt

    amps = [3, 6, 12]
    colors = {"aniso2d": "#2b6cb0", "stripe": "#2f9e44", "point": "#e8a13a"}
    fig, ax = plt.subplots(figsize=(5.8, 3.1))
    for geo, vals in PEAK.items():
        ax.plot(amps, vals, marker="o", lw=1.8, color=colors[geo], label=geo)
    ax.set_xscale("log", base=2)
    ax.set_xticks(amps)
    ax.set_xticklabels([str(a) for a in amps])
    ax.set_xlabel("reward amplitude A")
    ax.set_ylabel("peak resolution ratio")
    ax.set_title("Reward increases local resolution monotonically with amplitude")
    ax.legend(fontsize=7.5)
    fig.savefig(path, bbox_inches="tight", facecolor="white", dpi=220)
    plt.close(fig)
    return path


def build() -> None:
    Path(FIG).mkdir(parents=True, exist_ok=True)
    f_spec = fig_specificity(f"{FIG}/fig1_specificity.png")
    f_exp = fig_exponent(f"{FIG}/fig2_exponent_gate.png")
    f_peak = fig_peak(f"{FIG}/fig3_peak_resolution.png")

    p = pk.Paper(OUT, FIG)
    p.title("Concern Deforms a Learned Metric, But Its Finite-Capacity Exponent Is Effectively One-Dimensional")
    p.authors("Jawaun Brown")
    p.authors("Research-Derived Experiments · Paper B")
    p.rule()
    p.abstract(
        "A goal or concern signal should not merely label a representation; it should reshape the "
        "metric by allocating resolution where errors matter. This paper reports two results. First, "
        "the original moved-location experiment remains a causal proof-of-concept: a reward at A or "
        "B locally increases the induced metric at the rewarded location, control-subtracted "
        "specificity is positive (+0.65 and +1.27), and larger-arena OOD decoding falls as local "
        "resolution is purchased. Second, a new 576-network Modal H100 sweep tests a derived "
        "rate-distortion exponent. The finite-capacity mechanism is confirmed, but the clean 2-D "
        "law is falsified as stated: at A=6, an anisotropic 2-D reward gives α=+0.309 [0.304,0.314], "
        "a stripe gives α=+0.302 [0.298,0.307], and a point reward gives α=+0.283 [0.278,0.288]. "
        "All SEs are <0.003, far below the preregistered 0.02 target. The honest conclusion is that "
        "concern deforms the metric, but this RNN/grid harness reallocates capacity with measured "
        "effective dimension d_eff≈0.8–1.0, not the normative 2-D exponent.")

    p.h1("1. What Is Being Tested")
    p.para(
        "The induced metric of a code r(x) is the pullback metric J(x)^T J(x): it says how much the "
        "population vector changes per unit movement in stimulus space. High metric density means "
        "fine local resolution. A reward-weighted path-integration objective asks the network to "
        "reduce errors near valuable locations. The causal question is whether that independent "
        "reward signal warps the learned metric.")
    p.para(
        "The stronger theoretical question is quantitative. A high-resolution rate-distortion "
        "derivation predicts sqrt(det g) ∝ w^{d/(d+2)} under a finite capacity constraint. In a "
        "2-D arena this gives α=1/2; in an effectively 1-D allocation it gives α=1/3. The Modal "
        "sweep was preregistered to decide between those possibilities.")

    p.h1("2. Causal Metric Deformation")
    p.figure(f_spec, "Figure 1. The original moved-location experiment (n=3 seeds) is the non-circular anchor: moving the reward moves the metric deformation. This specific A/B result was not rerun in the Modal exponent sweep.", width_in=5.8)
    p.para(
        "The proof-of-concept remains important because the reward location is an independent "
        "variable, not a post-hoc label extracted from the representation. Reward@A raises metric "
        "density at A more than B; reward@B reverses the asymmetry. A no-reward control is flat. "
        "This establishes that concern can deform the learned metric, while leaving open how that "
        "deformation scales under capacity.")

    p.h1("3. Modal Exponent Sweep")
    p.figure(f_exp, "Figure 2. At the primary amplitude A=6, all geometries stay near the 1-D exponent family. The 2-D prediction α=1/2 is decisively excluded.", width_in=5.6)
    p.figure(f_peak, "Figure 3. Peak resolution increases monotonically with reward amplitude, confirming value-driven reallocation even though the exponent is not 2-D.", width_in=5.6)
    p.table(
        [["Geometry", "α at A=6", "95% CI", "SE", "d_eff", "R²"],
         ["aniso2d", "+0.309", "[0.304, 0.314]", "0.0025", "0.90", "0.528"],
         ["stripe", "+0.302", "[0.298, 0.307]", "0.0023", "0.87", "0.565"],
         ["point", "+0.283", "[0.278, 0.288]", "0.0025", "0.79", "0.417"]],
        caption="Table 1. Primary preregistered exponent gate. Aniso2d does not separate from stripe and is much closer to 1/3 than 1/2.",
        col_widths=[85, 70, 100, 50, 50, 50])

    p.h1("4. Discussion")
    p.para(
        "The right conclusion is a measured law, not the desired one. Capacity is load-bearing: "
        "without it the exponent was near +0.07; with it, reward density reliably predicts metric "
        "density with α around +0.3. But the code does not use a full two-dimensional allocation "
        "even when the value field is two-dimensional. The architecture appears to move resolution "
        "along an effectively one-dimensional bottleneck or gradient-like degree of freedom.")
    p.para(
        "This result is scientifically useful because it narrows the phenomenon. The paper should "
        "not claim a confirmed 2-D Newton law. It should claim: a concern signal causally warps a "
        "learned metric; a finite-capacity bottleneck turns that warp into a stable power law; and "
        "the measured exponent reveals the effective allocation dimension of the learned code.")

    p.h1("5. Limitations")
    p.para(
        "The moved-location A/B specificity result is still n=3. The 576-network Modal run resolves "
        "the exponent and amplitude question, not the moved-location design. The reward is a loss "
        "weight, not a full reinforcement-learning value head. The derivation remains a normative "
        "high-resolution efficient-coding law; this paper measures how a particular RNN/grid harness "
        "departs from it.")

    p.references([
        "Bennett, W. R. Spectra of quantized signals. Bell System Technical Journal (1948).",
        "Ganguli, D., Simoncelli, E. P. Efficient sensory encoding and Bayesian inference with heterogeneous neural populations. Neural Computation (2014).",
        "Gardner, R. J. et al. Toroidal topology of population activity in grid cells. Nature 602 (2022).",
        "Sorscher, B., Mel, G. C., Ganguli, S., Ocko, S. A. A unified theory for the origin of grid cells through the lens of pattern formation. NeurIPS (2019).",
        "Cueva, C. J., Wei, X.-X. Emergence of grid-like representations by training recurrent neural networks to perform spatial localization. ICLR (2018).",
        "Banino, A. et al. Vector-based navigation using grid-like representations in artificial agents. Nature 557 (2018).",
        "Hollup, S. A. et al. Accumulation of hippocampal place fields at the goal location. Journal of Neuroscience (2001).",
        "Boccara, C. N. et al. The entorhinal cognitive map is attracted to goals. Science (2019).",
        "Butler, W. N., Hardcastle, K., Giocomo, L. M. Remembered reward locations restructure entorhinal spatial maps. Science (2019).",
    ])
    out = p.build()
    print(f"[paperB] wrote {out}")


if __name__ == "__main__":
    build()
