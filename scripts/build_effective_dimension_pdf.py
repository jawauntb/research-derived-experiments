#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Render the standalone reward-deformation effective-dimension paper.

Run:  python scripts/build_effective_dimension_pdf.py
Out:  artifacts/papers/reward_deformation_effective_dimension_law.pdf
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paperkit as pk  # noqa: E402

FIG = "artifacts/papers/figs_effective_dimension"
OUT = "artifacts/papers/reward_deformation_effective_dimension_law.pdf"

PRIMARY_A = 6
ROWS = [
    ("aniso2d", 3, 0.3337, 0.3292, 0.3383, 1.004, 0.0023, 0.548),
    ("aniso2d", 6, 0.3089, 0.3040, 0.3136, 0.896, 0.0025, 0.528),
    ("aniso2d", 12, 0.3176, 0.3130, 0.3223, 0.933, 0.0023, 0.555),
    ("stripe", 3, 0.2967, 0.2914, 0.3021, 0.847, 0.0027, 0.525),
    ("stripe", 6, 0.3024, 0.2979, 0.3069, 0.869, 0.0023, 0.565),
    ("stripe", 12, 0.3182, 0.3142, 0.3221, 0.935, 0.0020, 0.668),
    ("point", 3, 0.3242, 0.3183, 0.3299, 0.963, 0.0029, 0.393),
    ("point", 6, 0.2831, 0.2781, 0.2880, 0.792, 0.0025, 0.417),
    ("point", 12, 0.2788, 0.2748, 0.2828, 0.775, 0.0020, 0.474),
]
GEOMETRY_LABELS = {
    "point": "point",
    "stripe": "stripe",
    "aniso2d": "anisotropic 2-D",
}


def d_eff(alpha: float) -> float:
    return 2 * alpha / (1 - alpha)


def reward_field(
    side: int,
    geometry: str,
    *,
    A: float = 6.0,
    sigma: float = 0.12,
    xy: tuple[float, float] = (0.5, 0.5),
) -> tuple[object, object, object]:
    import numpy as np

    xs = np.linspace(0.0, 1.0, side)
    x, y = np.meshgrid(xs, xs, indexing="ij")
    if geometry == "stripe":
        d2 = (x - xy[0]) ** 2 / (2 * sigma**2)
    elif geometry == "aniso2d":
        d2 = (x - xy[0]) ** 2 / (2 * sigma**2)
        d2 += (y - xy[1]) ** 2 / (2 * (2.2 * sigma) ** 2)
    else:
        d2 = ((x - xy[0]) ** 2 + (y - xy[1]) ** 2) / (2 * sigma**2)
    return x, y, 1.0 + A * np.exp(-d2)


def area_density_from_pop(pop, side: int):
    import numpy as np

    grid = pop.reshape(side, side, -1)
    dx = 1.0 / (side - 1)
    area = np.full((side, side), np.nan)
    for i in range(1, side - 1):
        for j in range(1, side - 1):
            du = (grid[i + 1, j] - grid[i - 1, j]) / (2 * dx)
            dv = (grid[i, j + 1] - grid[i, j - 1]) / (2 * dx)
            g00 = du @ du
            g11 = dv @ dv
            g01 = du @ dv
            area[i, j] = math.sqrt(max(0.0, g00 * g11 - g01 * g01))
    return area


def loglog_slope(w, rho) -> tuple[float, float, int]:
    import numpy as np

    mask = np.isfinite(w) & np.isfinite(rho) & (w > 0) & (rho > 0)
    lw = np.log(w[mask])
    lr = np.log(rho[mask])
    if lw.size < 8 or lw.std() < 1e-6:
        return float("nan"), float("nan"), int(mask.sum())
    xmat = np.vstack([lw, np.ones_like(lw)]).T
    slope, intercept = np.linalg.lstsq(xmat, lr, rcond=None)[0]
    pred = xmat @ [slope, intercept]
    ss_res = float(((lr - pred) ** 2).sum())
    ss_tot = float(((lr - lr.mean()) ** 2).sum()) or 1.0
    return float(slope), float(1 - ss_res / ss_tot), int(mask.sum())


def gradient_covariance_diagnostic(field) -> str:
    import numpy as np

    gx, gy = np.gradient(np.log(field))
    grads = np.stack([gx.ravel(), gy.ravel()], axis=1)
    cov = np.cov(grads.T)
    evals = np.linalg.eigvalsh(cov)
    evals = np.maximum(evals, 0)
    if evals[-1] <= 0:
        ratio = 0.0
    else:
        ratio = float(evals[0] / evals[-1])
    rank = int((evals > 0.01 * evals[-1]).sum()) if evals[-1] > 0 else 0
    return f"gradient covariance rank {rank}, λ2/λ1={ratio:.2f}"


def synthetic_validation_rows() -> list[tuple[str, float, float, float, int]]:
    import numpy as np

    side = 16
    x = np.linspace(0.0, 1.0, side)
    dx = 1.0 / (side - 1)
    wx = 1.0 + 6.0 * np.exp(-((x - 0.45) ** 2) / (2 * 0.30**2))
    wy = 1.0 + 4.2 * np.exp(-((x - 0.62) ** 2) / (2 * 0.45**2))
    field = wx[:, None] * wy[None, :]
    rows: list[tuple[str, float, float, float, int]] = []
    for label, planted_alpha in (("planted 1-D family", 1 / 3), ("planted 2-D law", 1 / 2)):
        fx = wx**planted_alpha
        fy = wy**planted_alpha
        u = np.r_[0.0, np.cumsum(0.5 * (fx[:-1] + fx[1:]) * dx)]
        v = np.r_[0.0, np.cumsum(0.5 * (fy[:-1] + fy[1:]) * dx)]
        U, V = np.meshgrid(u, v, indexing="ij")
        pop = np.stack([U.ravel(), V.ravel()], axis=1)
        area = area_density_from_pop(pop, side)
        recovered, r2, n_bins = loglog_slope(field, area)
        rows.append((label, planted_alpha, recovered, r2, n_bins))
    return rows


def fig_value_fields(path: str) -> str:
    import matplotlib.pyplot as plt

    geos = ["point", "stripe", "aniso2d"]
    fig, axes = plt.subplots(1, 3, figsize=(6.6, 2.55), constrained_layout=True)
    for ax, geo in zip(axes, geos):
        x, y, field = reward_field(160, geo, A=PRIMARY_A)
        im = ax.imshow(field.T, origin="lower", extent=[0, 1, 0, 1], cmap="magma")
        ax.contour(x, y, field, colors="white", levels=7, linewidths=0.5, alpha=0.62)
        ax.set_title(GEOMETRY_LABELS[geo], fontsize=9.4, weight="bold")
        ax.set_xticks([0, 0.5, 1])
        ax.set_yticks([0, 0.5, 1])
        ax.tick_params(labelsize=7)
        diag = gradient_covariance_diagnostic(field)
        ax.text(
            0.5,
            -0.18,
            diag,
            transform=ax.transAxes,
            ha="center",
            va="top",
            fontsize=7.0,
            color="#2f3437",
        )
    cbar = fig.colorbar(im, ax=axes, shrink=0.82, pad=0.02)
    cbar.set_label("value weight w(x)", fontsize=8)
    fig.suptitle("Registered value-weight fields at A=6", fontsize=11, weight="bold")
    fig.savefig(path, bbox_inches="tight", facecolor="white", dpi=230)
    plt.close(fig)
    return path


def fig_landscape(path: str) -> str:
    import matplotlib.pyplot as plt
    import numpy as np

    geos = ["aniso2d", "stripe", "point"]
    amps = [3, 6, 12]
    mat = np.array([[next(r[2] for r in ROWS if r[0] == g and r[1] == a) for a in amps] for g in geos])
    fig, ax = plt.subplots(figsize=(5.95, 2.8))
    im = ax.imshow(mat, cmap="viridis", vmin=0.27, vmax=0.34)
    ax.set_xticks(range(len(amps)))
    ax.set_xticklabels([f"A={a}" for a in amps])
    ax.set_yticks(range(len(geos)))
    ax.set_yticklabels([GEOMETRY_LABELS[g] for g in geos])
    for i in range(len(geos)):
        for j in range(len(amps)):
            ax.text(j, i, f"{mat[i, j]:.3f}", ha="center", va="center",
                    color="white", weight="bold", fontsize=8)
    fig.colorbar(im, ax=ax, label="area-density exponent α", fraction=0.046, pad=0.04)
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
    fig, ax = plt.subplots(figsize=(5.5, 3.0))
    ax.errorbar(x, vals, yerr=yerr, fmt="o", ms=8, capsize=4, color="#2b6cb0")
    ax.axhline(1 / 3, color="#444", ls="--", label="1/3 effective 1-D")
    ax.axhline(0.5, color="#c0392b", ls=":", label="1/2 physical 2-D")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0.25, 0.53)
    ax.set_ylabel("α at A=6")
    ax.set_title("Preregistered gate: 1/2 is decisively excluded")
    ax.legend(fontsize=8)
    fig.savefig(path, bbox_inches="tight", facecolor="white", dpi=220)
    plt.close(fig)
    return path


def fig_synthetic_validation(path: str) -> str:
    import matplotlib.pyplot as plt

    rows = synthetic_validation_rows()
    planted = [row[1] for row in rows]
    recovered = [row[2] for row in rows]
    labels = ["1/3", "1/2"]
    fig, ax = plt.subplots(figsize=(4.55, 3.0))
    ax.plot([0.28, 0.53], [0.28, 0.53], color="#444", ls="--", lw=1, label="ideal recovery")
    ax.scatter(planted, recovered, s=72, color="#2b6cb0", edgecolor="#111", linewidth=0.5, zorder=3)
    for label, x, y in zip(labels, planted, recovered):
        ax.annotate(f"planted {label}\nrecovered {y:.3f}", (x, y), xytext=(8, -10),
                    textcoords="offset points", fontsize=7.8)
    ax.set_xlim(0.28, 0.53)
    ax.set_ylim(0.28, 0.53)
    ax.set_xlabel("planted exponent")
    ax.set_ylabel("estimated exponent")
    ax.set_title("Estimator sanity check at the experiment's 16x16 grid")
    ax.legend(fontsize=8)
    fig.savefig(path, bbox_inches="tight", facecolor="white", dpi=220)
    plt.close(fig)
    return path


def build() -> None:
    Path(FIG).mkdir(parents=True, exist_ok=True)
    f_fields = fig_value_fields(f"{FIG}/fig1_value_fields.png")
    f_land = fig_landscape(f"{FIG}/fig2_landscape.png")
    f_gate = fig_gate(f"{FIG}/fig3_gate.png")
    f_synth = fig_synthetic_validation(f"{FIG}/fig4_synthetic_validation.png")
    synth_rows = synthetic_validation_rows()

    p = pk.Paper(OUT, FIG)
    p.title("A Measured Effective-Dimension Law for Value-Weighted Metric Deformation in Path-Integration RNNs")
    p.authors("Jawaun Brown")
    p.authors("Research-Derived Experiments · Preregistered Geometry Sweep")
    p.rule()
    p.abstract(
        "A value-weighted rate-distortion derivation predicts that a finite-capacity 2-D code "
        "should allocate local area density as √det g ∝ w^{1/2}. We preregistered "
        "a geometry sweep designed to distinguish this physical 2-D law from an effectively 1-D "
        "allocation law: a stripe value field should give α near 1/3, while an anisotropic value "
        "field varying along both arena axes should give α near 1/2 if the 2-D law governs the "
        "trained code. The experiment rejects that d=2, α=1/2 prediction as a description of "
        "this path-integration RNN harness. Across 576 H100-trained capacity-bottleneck networks, "
        "anisotropic 2-D at A=6 gives α=0.309 [0.304, 0.314], stripe gives α=0.302 [0.298, 0.307], "
        "and point gives α=0.283 [0.278, 0.288]. The measured exponent therefore reports an "
        "effective allocation dimension near one, not the physical dimension of the arena."
    )

    p.h1("1. Claim and Scope")
    p.para(
        "The object of study is a learned population code r(x) for position x in a unit square. "
        "Its pullback metric is g(x)=J(x)^T J(x), where J is the Jacobian of the population state "
        "with respect to position. The local area element sqrt(det g(x)) is the code's area density: "
        "how much representational resolution is allocated per unit physical area."
    )
    p.para(
        "The value weight w(x) is an externally specified loss-weight field, not a learned RL reward. "
        "It makes decoding errors at some positions count more in the supervised path-integration "
        "objective. This note asks whether finite capacity makes the learned metric allocate area "
        "density as a power law in that externally supplied w(x)."
    )
    p.para(
        "The result is intentionally framed as a negative and positive measurement. It is negative "
        "for the naive physical 2-D exponent α=1/2. It is positive for a stable effective-dimension "
        "law: the exponent reveals the dimension through which this architecture reallocates capacity."
    )

    p.h1("2. Theory: From Rate-Distortion to Effective Dimension")
    p.para(
        "High-resolution quantization gives local distortion D(x) proportional to rho(x)^(-2/d), "
        "where rho(x) is local code density and d is the allocation dimension. Minimizing "
        "the value-weighted objective integral w(x)D(x) dx subject to a finite density budget "
        "integral rho(x) dx = R yields rho*(x) proportional to w(x)^(d/(d+2)). For an actual "
        "two-dimensional allocation, the area-density exponent is α=d/(d+2)=1/2; for a one-dimensional "
        "allocation, α=1/3."
    )
    p.para(
        "This also gives the inversion used in the result tables: α=d/(d+2), so "
        "d_eff=2α/(1-α). The three primary exponents imply d_eff values of approximately 0.90, "
        "0.87, and 0.79 for anisotropic 2-D, stripe, and point value fields respectively."
    )

    p.h1("3. Preregistered Geometry Gate")
    p.figure(
        f_fields,
        "Figure 1. Registered value-weight fields w(x). The stripe condition varies along one "
        "coordinate. The anisotropic 2-D condition has nonzero gradients along both arena axes; "
        "the plotted gradient-covariance diagnostic is rank 2 with λ2/λ1=0.16. Thus the failed "
        "1/2 prediction is not explained by accidentally using a one-dimensional field.",
        width_in=6.25,
    )
    p.para(
        "The project-preregistered gate was frozen before the large Modal sweep. The primary estimand is the slope α from "
        "ordinary least squares regression of log sqrt(det g(x)) on log w(x), over spatial bins with "
        "finite positive area density. The primary comparison is at amplitude A=6, with A in {3,6,12} "
        "used to check stability and amplitude scaling."
    )
    p.para(
        "Confirmation of the 2-D law required an anisotropic 2-D mean closer to 1/2 than 1/3, a "
        "bootstrap standard error at or below 0.02, a stripe result near 1/3, and a nonzero "
        "aniso2d-vs-stripe gap. Failure of aniso2d to separate from stripe was preregistered as "
        "rejection of the d=2 gate; the effective-dimension interpretation was the planned diagnostic "
        "for such a failure."
    )

    p.h1("4. Experiment")
    p.para(
        "We trained 576 capacity-bottleneck path-integration RNNs on Modal H100 workers: three "
        "value-field geometries (point, stripe, anisotropic 2-D), three amplitudes (3, 6, 12), and "
        "64 seeds per cell. Each network used Ng=256 hidden units, Np=256 place cells, T=20 rollout "
        "steps, batch size 128, 8000 optimization steps, Adam with learning rate 1e-3 and weight "
        "decay 1e-4, unit-sphere hidden-state normalization at every recurrent step, and Gaussian "
        "channel noise with standard deviation 0.15 before decoding. Training weights were "
        "mean-normalized within each batch, so the intervention changes the spatial allocation of "
        "loss rather than the global loss scale."
    )
    p.para(
        "Each condition-level α is the mean of 64 seed-level OLS slopes, not a pooled regression "
        "over all bins from all networks. Evaluation uses 20,480 sampled positions per model before "
        "16x16 binning; finite-positive interior-bin fitting and empty-bin handling are reported "
        "in Appendix A.5."
    )
    p.figure(
        f_land,
        "Figure 2. Full exponent landscape. Values are precise and stable, but they cluster around "
        "the 1-D family rather than the 2-D prediction.",
        width_in=4.15,
    )

    p.h1("5. Results")
    p.figure(
        f_gate,
        "Figure 3. Primary preregistered gate. The anisotropic 2-D value field does not approach "
        "1/2 and does not cleanly separate from stripe.",
        width_in=5.25,
    )
    p.table(
        [
            ["Geometry", "A", "α", "95% CI", "SE", "d_eff", "R²"],
            ["aniso2d", "6", "0.309", "[0.304, 0.314]", "0.0025", "0.90", "0.528"],
            ["stripe", "6", "0.302", "[0.298, 0.307]", "0.0023", "0.87", "0.565"],
            ["point", "6", "0.283", "[0.278, 0.288]", "0.0025", "0.79", "0.417"],
        ],
        caption="Table 1. Primary A=6 result. The 2-D exponent 1/2 is not within any interval.",
        col_widths=[72, 28, 45, 92, 44, 48, 42],
    )
    p.para(
        "The aniso2d-vs-stripe difference is Δ=+0.0065 with bootstrap 95% CI "
        "[-0.0003,+0.0132]. That is not the expected separation between 1/3 and 1/2. The exponent "
        "landscape is therefore not a noisy confirmation of the 2-D prediction; it rejects the "
        "d=2, α=1/2 prediction as the empirical description of this architecture."
    )
    p.table(
        [
            ["Geometry", "A=3 α", "A=6 α", "A=12 α", "Reading"],
            ["aniso2d", "0.334 [0.329,0.338]", "0.309 [0.304,0.314]", "0.318 [0.313,0.322]", "d_eff near 0.9-1.0"],
            ["stripe", "0.297 [0.291,0.302]", "0.302 [0.298,0.307]", "0.318 [0.314,0.322]", "d_eff near 0.85-0.94"],
            ["point", "0.324 [0.318,0.330]", "0.283 [0.278,0.288]", "0.279 [0.275,0.283]", "weaker radial allocation"],
        ],
        caption="Table 2. Full amplitude sweep. The exponent stays near the effective-1-D family.",
        col_widths=[62, 88, 88, 88, 118],
    )
    p.para(
        "Peak-resolution ratios increase monotonically with amplitude in all three geometries "
        "(point 1.319 to 1.400 to 1.515; stripe 1.289 to 1.348 to 1.428; anisotropic 2-D 1.300 "
        "to 1.369 to 1.443). Thus value weighting really does increase local resolution. The "
        "revised conclusion concerns the dimension and exponent governing that reallocation."
    )

    p.h1("6. Estimator Sanity Check")
    p.figure(
        f_synth,
        "Figure 4. Synthetic estimator validation. A separable 2-D synthetic embedding with known "
        "area density rho(x) proportional to w(x)^α was evaluated with the same 16x16 central "
        "finite-difference area-density estimator and log-log slope fitter used on trained models.",
        width_in=4.65,
    )
    p.table(
        [
            ["Synthetic field", "planted α", "estimated α", "R²", "bins"],
            [synth_rows[0][0], f"{synth_rows[0][1]:.3f}", f"{synth_rows[0][2]:.3f}", f"{synth_rows[0][3]:.4f}", str(synth_rows[0][4])],
            [synth_rows[1][0], f"{synth_rows[1][1]:.3f}", f"{synth_rows[1][2]:.3f}", f"{synth_rows[1][3]:.4f}", str(synth_rows[1][4])],
        ],
        caption="Table 3. The estimator does not collapse a planted 1/2 law to the observed 0.30 range.",
        col_widths=[116, 68, 74, 60, 48],
    )
    p.para(
        "This check is not evidence that the trained RNN should realize the 2-D optimum. It only "
        "addresses the simplest methodological objection: the area-density estimator and slope "
        "fitter, at the same 16x16 grid resolution, can recover planted 1/2 behavior and do not "
        "mechanically force slopes toward 1/3."
    )

    p.h1("7. Interpretation")
    p.para(
        "The exponent is not measuring the physical dimension of the arena. It is measuring the "
        "effective allocation dimension of the learned code. In this harness, d_eff is near one even "
        "when the externally specified value field varies along both physical dimensions."
    )
    p.para(
        "The result changes the target for future theory. The missing ingredient is not precision: "
        "the primary standard errors are below 0.003. The missing ingredient is an architectural "
        "account of why recurrent grid-like codes spend capacity through a narrow degree of freedom. "
        "Possible explanations include radial-gradient allocation, modular grid periodicity, the "
        "unit-sphere bottleneck, and decoder geometry."
    )

    p.h1("8. Limitations and NeurIPS-Scale Extensions")
    p.para(
        "This standalone note is intentionally narrow. It establishes the preregistered negative "
        "gate and gives enough methodological detail to be auditable, but it does not yet claim "
        "universality across architectures or metric estimators. A full conference version should "
        "add capacity sweeps over Ng, noise, and normalization; architecture sweeps beyond this "
        "RNN harness; alternative metric estimators such as neighbor stretch, Frobenius norm, area "
        "density, and Fisher information; an ablation of unit-sphere normalization; and a decoder "
        "geometry ablation separating code geometry from readout geometry."
    )

    p.h1("Appendix A. Methods")
    p.h2("A.1 Environment and Trajectories")
    p.para(
        "The arena is the unit square [0,1]^2 with reflecting boundaries. Each batch starts at a "
        "uniform random position in [0.1,0.9]^2. Heading is initialized uniformly on [0,2π], perturbed "
        "at each step by Gaussian noise with standard deviation 0.4 radians, and moved at nominal "
        "speed 0.06 before reflection. Reflection flips out-of-bounds coordinates back into the "
        "arena and adds π to the heading for reflected particles. Rollout length is T=20."
    )
    p.h2("A.2 Place-Cell Targets and Training Loss")
    p.para(
        "Np=256 place cells form a 16x16 grid of centers over the arena. The target place code is a "
        "softmax of negative squared distance to centers with sigma 0.09. The model receives the "
        "initial place code and velocity sequence, and predicts a place-code distribution at each "
        "step. The per-sample loss is KL(target || predicted), multiplied by the mean-normalized "
        "value weight w(x), and then averaged over batch and time."
    )
    p.h2("A.3 Value-Weight Fields")
    p.para(
        "All conditions use w(x)=1+A exp(-q(x)) before mean normalization inside each training "
        "batch. For point, q is squared Euclidean distance from (0.5,0.5) divided by 2σ^2. For "
        "stripe, q uses only the x-coordinate distance. For anisotropic 2-D, q is the sum of an "
        "x term with width σ and a y term with width 2.2σ. The sweep used σ=0.12 and amplitudes "
        "A in {3,6,12}."
    )
    p.h2("A.4 Model and Capacity Bottleneck")
    p.para(
        "The model is a single RNNCell with ReLU recurrence. A linear encoder maps the initial place "
        "code into Ng=256 hidden units, the RNNCell integrates 2-D velocity inputs, and a linear "
        "decoder maps hidden states back to Np place logits. After every recurrent update the hidden "
        "state is divided by its Euclidean norm plus 1e-6, placing it on a unit sphere. During "
        "training, Gaussian channel noise with standard deviation 0.15 is added to hidden states "
        "before decoding. This unit-sphere plus finite-SNR channel is the finite-capacity bottleneck."
    )
    p.h2("A.5 Area-Density Estimator")
    p.para(
        "After training, each model is evaluated without channel noise on 1024 fresh trajectories. "
        "Hidden states are binned by position into the 16x16 place grid and averaged per bin, with "
        "empty bins filled by the mean occupied hidden state. For interior bins, central differences "
        "estimate the two positional derivatives du and dv from neighboring grid bins over 2Δx. The "
        "estimated area density is sqrt((du dot du)(dv dot dv)-(du dot dv)^2), exactly the square "
        "root of the determinant of the local pullback metric."
    )
    p.para(
        "At this 20,480-position evaluation scale, the 64 sweep seeds occupy all 256 spatial bins "
        "under the trajectory generator; mean occupied bins are 256/256 and interior occupancy is "
        "100% (196/196 interior bins)."
    )
    p.h2("A.6 Slope Fitting and Bootstrap")
    p.para(
        "For each trained network, α is the ordinary least squares slope in log area density versus "
        "log w(x), restricted to finite positive interior bins. Each condition summary is the mean "
        "of 64 seed-level slopes. Confidence intervals and standard errors use 2000 bootstrap "
        "resamples of the seed-level rows within condition. The reported d_eff is computed from the "
        "condition mean using d_eff=2α/(1-α)."
    )
    p.h2("A.7 Provenance")
    p.para(
        "The gate was preregistered in the frozen 2026-07-02 addendum to the grid-cell weakness "
        "preregistration. The committed runner is modal_reward_deformation_sweep.py, and the committed "
        "result report is reward_deformation_sweep_2026_07_02.md. Raw JSON artifacts are gitignored; "
        "the report records the manifest, summary statistics, and interpretation."
    )

    p.references([
        "Bennett, W. R. Spectra of quantized signals. Bell System Technical Journal (1948).",
        "Gersho, A. and Gray, R. M. Vector Quantization and Signal Compression. Kluwer Academic Publishers (1992).",
        "Berger, T. Rate Distortion Theory: A Mathematical Basis for Data Compression. Prentice-Hall (1971).",
        "Cover, T. M. and Thomas, J. A. Elements of Information Theory. Wiley (2006).",
        "Ganguli, D. and Simoncelli, E. P. Efficient sensory encoding and Bayesian inference with heterogeneous neural populations. Neural Computation (2014).",
        "Wei, X.-X. and Stocker, A. A. A Bayesian observer model constrained by efficient coding can explain anti-Bayesian percepts. Nature Neuroscience 18, 1509-1517 (2015).",
        "Sorscher, B., Mel, G. C., Ganguli, S., and Ocko, S. A. A unified theory for the origin of grid cells through the lens of pattern formation. NeurIPS (2019).",
        "Cueva, C. J. and Wei, X.-X. Emergence of grid-like representations by training recurrent neural networks to perform spatial localization. ICLR (2018).",
        "Banino, A. et al. Vector-based navigation using grid-like representations in artificial agents. Nature 557, 429-433 (2018).",
        "Gardner, R. J. et al. Toroidal topology of population activity in grid cells. Nature 602, 123-128 (2022).",
        "Boccara, C. N., Nardin, M., Stella, F., O'Neill, J., and Csicsvari, J. The entorhinal cognitive map is attracted to goals. Science 363, 1443-1447 (2019).",
        "Butler, W. N., Hardcastle, K., and Giocomo, L. M. Remembered reward locations restructure entorhinal spatial maps. Science 363, 1447-1452 (2019).",
        "Ocko, S. A., Hardcastle, K., Giocomo, L. M., and Ganguli, S. Emergent elasticity in the neural code for space. PNAS 115, E11798-E11806 (2018).",
        "Brunel, N. and Nadal, J.-P. Mutual information, Fisher information, and population coding. Neural Computation 10, 1731-1757 (1998).",
        "Amari, S. Information Geometry and Its Applications. Springer (2016).",
    ])
    out = p.build()
    print(f"[effective-dimension-pdf] wrote {out}")


if __name__ == "__main__":
    build()
