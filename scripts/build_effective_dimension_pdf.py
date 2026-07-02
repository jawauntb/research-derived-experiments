#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Render the standalone reward-deformation effective-dimension paper.

Run:  python scripts/build_effective_dimension_pdf.py
Out:  artifacts/papers/reward_deformation_effective_dimension_law.pdf
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paperkit as pk  # noqa: E402

FIG = "artifacts/papers/figs_effective_dimension"
OUT = "artifacts/papers/reward_deformation_effective_dimension_law.pdf"

ROWS = [
    ("aniso2d", 3, 0.3337, 0.3292, 0.3383, 1.004),
    ("aniso2d", 6, 0.3089, 0.3040, 0.3136, 0.896),
    ("aniso2d", 12, 0.3176, 0.3130, 0.3223, 0.933),
    ("stripe", 3, 0.2967, 0.2914, 0.3021, 0.847),
    ("stripe", 6, 0.3024, 0.2979, 0.3069, 0.869),
    ("stripe", 12, 0.3182, 0.3142, 0.3221, 0.935),
    ("point", 3, 0.3242, 0.3183, 0.3299, 0.963),
    ("point", 6, 0.2831, 0.2781, 0.2880, 0.792),
    ("point", 12, 0.2788, 0.2748, 0.2828, 0.775),
]


def fig_landscape(path: str) -> str:
    import matplotlib.pyplot as plt
    import numpy as np

    geos = ["aniso2d", "stripe", "point"]
    amps = [3, 6, 12]
    mat = np.array([[next(r[2] for r in ROWS if r[0] == g and r[1] == a) for a in amps] for g in geos])
    fig, ax = plt.subplots(figsize=(5.6, 2.8))
    im = ax.imshow(mat, cmap="viridis", vmin=0.27, vmax=0.34)
    ax.set_xticks(range(len(amps)))
    ax.set_xticklabels([f"A={a}" for a in amps])
    ax.set_yticks(range(len(geos)))
    ax.set_yticklabels(["anisotropic 2-D", "stripe", "point"])
    for i in range(len(geos)):
        for j in range(len(amps)):
            ax.text(j, i, f"{mat[i, j]:.3f}", ha="center", va="center", color="white", weight="bold", fontsize=8)
    fig.colorbar(im, ax=ax, label="area exponent α", fraction=0.046, pad=0.04)
    ax.set_title("Measured exponent landscape: all cells stay near the 1-D family")
    fig.savefig(path, bbox_inches="tight", facecolor="white", dpi=220)
    plt.close(fig)
    return path


def fig_gate(path: str) -> str:
    import matplotlib.pyplot as plt
    import numpy as np

    labels = ["aniso2d α", "stripe α", "point α"]
    vals = [0.3089, 0.3024, 0.2831]
    lo = [0.3040, 0.2979, 0.2781]
    hi = [0.3136, 0.3069, 0.2880]
    x = np.arange(3)
    yerr = [[v - l for v, l in zip(vals, lo)], [h - v for v, h in zip(vals, hi)]]
    fig, ax = plt.subplots(figsize=(5.4, 3.0))
    ax.errorbar(x, vals, yerr=yerr, fmt="o", ms=8, capsize=4, color="#2b6cb0")
    ax.axhline(1 / 3, color="#444", ls="--", label="1/3")
    ax.axhline(0.5, color="#c0392b", ls=":", label="1/2")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0.25, 0.53)
    ax.set_ylabel("α at A=6")
    ax.set_title("Preregistered Newton gate: 1/2 is decisively excluded")
    ax.legend(fontsize=8)
    fig.savefig(path, bbox_inches="tight", facecolor="white", dpi=220)
    plt.close(fig)
    return path


def build() -> None:
    Path(FIG).mkdir(parents=True, exist_ok=True)
    f_land = fig_landscape(f"{FIG}/fig1_landscape.png")
    f_gate = fig_gate(f"{FIG}/fig2_gate.png")

    p = pk.Paper(OUT, FIG)
    p.title("A Measured Effective-Dimension Law for Value-Driven Metric Deformation")
    p.authors("Jawaun Brown")
    p.authors("Research-Derived Experiments · standalone Newton-gate paper")
    p.rule()
    p.abstract(
        "A value-weighted rate-distortion derivation predicts that a finite-capacity 2-D code should "
        "allocate local area density as sqrt(det g) ∝ w^{1/2}. Before measuring, we preregistered a "
        "decisive geometry sweep: a 1-D stripe reward should give α≈1/3, while a genuinely 2-D "
        "anisotropic reward should give α≈1/2 if the normative 2-D law governs the trained code. "
        "The experiment falsifies the 2-D law as an empirical claim for this RNN/grid harness. Across "
        "576 H100-trained capacity-bottleneck networks, aniso2d at A=6 gives α=0.309 [0.304,0.314], "
        "stripe gives α=0.302 [0.298,0.307], and point reward gives α=0.283 [0.278,0.288]. Standard "
        "errors are <0.003. The measured law is instead an effective-dimension law: the code behaves "
        "as though representational capacity is reallocated along d_eff≈0.8–1.0 degrees of freedom. "
        "This is a negative result for the desired Newton step, but a positive result for scientific "
        "measurement: the exponent reveals the allocation dimension of the learned code.")

    p.h1("1. The Prediction")
    p.para(
        "Let r(x) be a population code and g(x)=J(x)^T J(x) its induced metric. The local area "
        "density sqrt(det g) measures how many distinguishable code states the representation "
        "allocates per unit physical area. Under high-resolution quantization, distortion scales as "
        "rho^{-2/d}. Minimizing value-weighted distortion ∫w(x)D(x)dx subject to a finite capacity "
        "budget ∫rho(x)dx=R gives rho*(x) ∝ w(x)^{d/(d+2)}. Thus d=2 predicts α=1/2, while d=1 "
        "predicts α=1/3.")
    p.para(
        "The previous CPU bottleneck test validated the mechanism qualitatively: adding a capacity "
        "constraint moved α from about +0.07 to about +0.30. But +0.30 is suspiciously close to "
        "1/3. The pre-registered question was whether a 2-D value field would lift the exponent to "
        "1/2, or whether the learned code reallocates through an effectively 1-D bottleneck.")

    p.h1("2. Experiment")
    p.para(
        "We trained 576 capacity-bottleneck path-integration RNNs on Modal H100 workers: three reward "
        "geometries (point, stripe, anisotropic 2-D), three amplitudes (3, 6, 12), and 64 seeds per "
        "cell. Each network used Ng=256 hidden units, Np=256 place cells, 8000 training steps, unit "
        "sphere state normalization, and fixed channel noise. The primary estimand was the log-log "
        "slope α of area density against reward weight at A=6.")
    p.figure(f_land, "Figure 1. Full exponent landscape. The values are precise and stable, but they cluster around the 1-D family rather than the 2-D prediction.", width_in=5.5)

    p.h1("3. Result")
    p.figure(f_gate, "Figure 2. Primary preregistered gate. The anisotropic 2-D reward does not approach 1/2 and does not cleanly separate from stripe.", width_in=5.2)
    p.table(
        [["Geometry", "A", "α", "95% CI", "d_eff"],
         ["aniso2d", "6", "0.309", "[0.304, 0.314]", "0.90"],
         ["stripe", "6", "0.302", "[0.298, 0.307]", "0.87"],
         ["point", "6", "0.283", "[0.278, 0.288]", "0.79"]],
        caption="Table 1. Primary A=6 result. The 2-D exponent 1/2 is not within any interval.",
        col_widths=[80, 35, 55, 110, 55])
    p.para(
        "The aniso2d-vs-stripe difference is Δ=+0.0065 with bootstrap 95% CI [−0.0003,+0.0132]. "
        "That is not the expected separation between 1/3 and 1/2. The exponent landscape is therefore "
        "not a noisy confirmation of the 2-D law; it is a precise falsification of that law as the "
        "empirical description of this architecture.")

    p.h1("4. What Was Learned")
    p.para(
        "The experiment confirms the finite-capacity intuition but revises the law. Reward/concern "
        "does increase local resolution, and the increase follows a stable power law. But the power "
        "law's exponent measures the representation's effective allocation dimension, not simply "
        "the physical dimension of the arena. In this harness, d_eff≈1 even when the reward field "
        "is two-dimensional.")
    p.para(
        "This matters because it changes what future theory must explain. The missing ingredient is "
        "not more precision; the standard errors are already below 0.003. The missing ingredient is "
        "an architectural account of why recurrent grid-like codes spend capacity through a narrow "
        "degree of freedom. Possible explanations include radial-gradient allocation, modular grid "
        "periodicity, the unit-sphere bottleneck, and decoder geometry. Each is now testable.")

    p.h1("5. Negative Result Discipline")
    p.para(
        "The title deliberately says measured effective-dimension law rather than rate-distortion "
        "law. The derivation remains valuable as a normative target, but the preregistered empirical "
        "gate did not confirm its d=2 exponent. This is not a failure to find structure. It is a "
        "more exact structure than the one we hoped for.")

    p.references([
        "Bennett, W. R. Spectra of quantized signals. Bell System Technical Journal (1948).",
        "Ganguli, D., Simoncelli, E. P. Efficient sensory encoding and Bayesian inference with heterogeneous neural populations. Neural Computation (2014).",
        "Sorscher, B., Mel, G. C., Ganguli, S., Ocko, S. A. A unified theory for the origin of grid cells through the lens of pattern formation. NeurIPS (2019).",
        "Gardner, R. J. et al. Toroidal topology of population activity in grid cells. Nature 602 (2022).",
        "Cueva, C. J., Wei, X.-X. Emergence of grid-like representations by training recurrent neural networks to perform spatial localization. ICLR (2018).",
        "Banino, A. et al. Vector-based navigation using grid-like representations in artificial agents. Nature 557 (2018).",
    ])
    out = p.build()
    print(f"[effective-dimension-pdf] wrote {out}")


if __name__ == "__main__":
    build()
