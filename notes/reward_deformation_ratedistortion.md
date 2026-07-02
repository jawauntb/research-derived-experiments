# A Rate-Distortion Law for Reward-Deformation (candidate local "Newton" for Paper B)

Date: 2026-07-01

Paper B shows *that* a reward deforms a learned code's induced metric (Kepler). This note
derives *why* it must, and — critically — predicts the **exact functional form** of the warp
from an objective, before measuring it. That parameter-free prediction is the Kepler→Newton
step: a law that generates a novel geometric prediction, testable on the existing setup.

## 1. Objects

- A code maps stimulus `x ∈ ℝ^d` (arena position, `d=2`) to a population vector `r(x) ∈ ℝ^N`.
- Its **induced (pullback) metric** is `g(x) = J(x)ᵀ J(x)`, `J = ∂r/∂x`. The local **volume
  element** `√det g(x)` is the *resolution/point-density* ρ(x): distinguishable code-states per
  unit area. The **linear stretch** (per axis, isotropic case) is `ℓ(x) = ρ(x)^{1/d}`.
- **Capacity is finite:** total code "mass" is bounded, `∫ ρ(x) dx = R` (finite units, bounded
  firing-rate/‖r‖ budget). This is the load-bearing constraint.
- **Concern = a value density** `w(x) ≥ 0`: how much decoding error at `x` costs. In the
  experiment `w(x) = 1 + A·exp(-‖x − x₀‖² / 2σ_r²)` (baseline 1 + a reward bump).

## 2. Objective

Minimise value-weighted decoding distortion under the capacity budget:

&nbsp;&nbsp;&nbsp;&nbsp;minimise&nbsp; `E = ∫ w(x) · D(x) dx` &nbsp;subject to&nbsp; `∫ ρ(x) dx = R`.

**Distortion–resolution relation (high-resolution / smooth-code regime).** A code with local
volume-density ρ tiles space into cells of volume `∝ ρ^{-1}`, so mean-squared decoding error per
cell scales as `(cell volume)^{2/d}`:

&nbsp;&nbsp;&nbsp;&nbsp;`D(x) ∝ ρ(x)^{-2/d}` &nbsp;(Bennett's quantization law; Ganguli–Simoncelli efficient coding).

## 3. Variational solution

Lagrangian `L = ∫ [ w ρ^{-2/d} − μ ρ ] dx`. Stationarity `∂L/∂ρ = 0`:

&nbsp;&nbsp;&nbsp;&nbsp;`−(2/d) w ρ^{-2/d − 1} − μ = 0 ⇒ ρ^{-(2/d+1)} ∝ w ⇒`

> **Reward-Deformation Law.** &nbsp; `ρ*(x) = √det g(x) ∝ w(x)^{ d/(d+2) }.`

Equivalently the linear stretch `ℓ*(x) = ρ*^{1/d} ∝ w(x)^{1/(d+2)}`, and the residual distortion
`D*(x) ∝ w(x)^{-2/(d+2)}`.

**Dimension table (the prediction):**

| quantity measured | exponent α in `∝ w^α` | d=1 | **d=2 (arena)** |
| --- | --- | ---: | ---: |
| volume element `√det g` (area density) | `d/(d+2)` | 1/3 | **1/2** |
| linear stretch `‖Δr‖/‖Δx‖` (per-axis) | `1/(d+2)` | 1/3 | **1/4** |
| residual distortion `D` | `−2/(d+2)` | −2/3 | **−1/2** |

The two code-geometry rows are the same object; which exponent you see depends on whether you
measure the area density (`½`) or the per-axis stretch (`¼`). Paper B's `metric_density`
(`mean ‖Δr‖/‖Δx‖`) is the **per-axis stretch → predicted α = 1/4**; the area density
(det of the 2-D Jacobian) → **predicted α = 1/2**.

## 4. Corollaries (unifying Paper B's three observations)

1. **The warp localises at the reward and tracks it** — because ρ* is a monotone function of w,
   which is peaked at x₀. (Paper B: specificity +0.65/+1.27, control flat.)
2. **Weakness is spent, quantitatively.** A flat ρ is maximally translation-symmetric (max
   weakness). The law forces `ρ ∝ w^{d/(d+2)}`, so the *non-uniformity* — hence the local weakness
   deficit — is a fixed power of the reward field. Weakness spent `∝ Var[log w]·(d/(d+2))²` to
   leading order.
3. **Global generalisation must degrade — by a predicted amount.** Capacity is conserved
   (`∫ρ = R`), so pulling ρ toward x₀ starves elsewhere; mean distortion rises as
   `∫ w^{-2/(d+2)}`. This is the quantitative form of Paper B's OOD drop (0.60 → 0.41–0.45), and it
   predicts the *whole* OOD-vs-reward-amplitude curve, not just one point.

## 5. Out-of-sample predictions (parameter-free, testable on the current setup)

1. **Exponent.** Regress `log ρ(x)` on `log w(x)` across the arena → slope **≈ 1/2** for the area
   density (or **1/4** for the per-axis stretch). No fit parameters.
2. **Amplitude scaling.** Sweep reward amplitude A → peak resolution ratio `∝ (1+A)^{d/(d+2)}`.
3. **Width.** The metric-bump width tracks σ_r (through the power transform), not the network's
   intrinsic scale.
4. **OOD cost curve.** Larger-arena decode error rises as `∫ w^{-2/(d+2)}`; sweeping A traces a
   predicted OOD-vs-A curve whose one measured point is Paper B's 0.60→0.41.

## 6. Assumptions & honest caveats

- **High-resolution / smooth-code regime.** `D ∝ ρ^{-2/d}` assumes many units and locally smooth,
  space-filling tuning. Grid codes are **periodic/modular**, so the effective allocation dimension
  and the exponent can shift; the clean `d/(d+2)` is the leading-order prediction, and a measured
  deviation is itself informative (it would say the modular code allocates differently).
- **Isotropy** is assumed when relating `√det g` to the per-axis stretch; anisotropic warps need
  the full Jacobian (the test below uses it).
- This is a **variational/statistical** law (rate-distortion / efficient-coding family), not an
  `F = ma`. That matches the earlier assessment that intelligence's "Newton" is more likely a
  variational principle than a mechanical one.

## 7. Why this is the Kepler→Newton step

The program has never made a geometric prediction *before* measuring it; every result so far is a
retrodiction or a bounded correlation. This law generates a **parameter-free number** (α ≈ 1/2)
for a quantity Paper B already measures. If the measured exponent matches, that is the program's
first confirmed out-of-sample geometric prediction — the concrete signal that separates Kepler
(observing the warp) from Newton (deriving it). Test harness:
`experiments/grid_cell_weakness/ratedistortion_test.py`.

## 8. First test result — honest: NOT confirmed at toy scale

Ran `ratedistortion_test.py` (2 seeds, Ng=96, 2000 CPU steps, central reward A=6, σ=0.12):

| exponent | predicted | measured | R² |
| --- | ---: | ---: | ---: |
| area density `√det g` | **0.50** | **+0.07** | 0.15 |
| per-axis stretch | **0.25** | **+0.035** | 0.15 |

**The parameter-free prediction fails at this scale.** The sign is right — the metric does
increase toward the reward (consistent with Paper B's positive specificity) — but the magnitude is
~7× below the rate-distortion optimum and the log–log fit is weak (R² ≈ 0.15). Read plainly: the
trained RNN **under-allocates** resolution to the reward relative to the optimal law; it is not at
the rate-distortion optimum.

Honest diagnosis of why (each is a concrete next step, not an excuse):
1. **Not capacity-constrained.** The reward here reweights the *loss*, but nothing enforces a hard
   `∫ρ = R` budget, so the network has no pressure to *trade* resolution — the derivation's
   load-bearing constraint is absent. A bottleneck / fixed-‖r‖ budget is needed to test the law.
2. **Not high-resolution / periodic code.** Ng=96, 2000 CPU steps → the code is under-formed and
   grid-periodic, violating the smooth space-filling assumption behind `D ∝ ρ^{-2/d}`.
3. **Noisy metric estimation** on a 16×16 binned population (R² ≈ 0.15), 2 seeds — underpowered.

**Status (first test):** unconfirmed at toy scale — see the follow-up below.

### 8a. Follow-up with a capacity bottleneck — mechanism confirmed, exponent ≈ 0.30

The first test lacked the derivation's load-bearing constraint. Adding it — projecting the code
onto a **unit sphere** (hard finite capacity) plus a **fixed-variance channel** (finite SNR) —
changes the picture (`capacity_bottleneck.py`; `results/capacity_bottleneck_2026_07_01.md`):

| config | area exponent α | R² |
| --- | ---: | ---: |
| no capacity constraint | +0.07 | 0.15 |
| **+ capacity bottleneck** | **+0.30** | **0.44** |

**The capacity constraint is causal:** it moves α ~4–5× toward the predicted 0.5 (0.07 → 0.30) and
triples the fit quality — exactly the derivation's prediction that a *finite-capacity* code is
forced to trade resolution. But α **plateaus at ≈ 0.30**, below the 2-D value 0.5, robustly across
seeds and deeper training. Intriguingly **0.30 ≈ 1/3**, the *1-D* rate-distortion exponent — a
(post-hoc, untested) sign that a radially-symmetric reward drives effectively-1-D reallocation
(`d_eff ≈ 1`). Net: **partial confirmation** — the law's mechanism is validated and the exponent is
in the predicted power-law family, but the specific 2-D value is not hit. We have Kepler (the warp),
a derived candidate law, and now causal evidence for its key assumption — not yet a confirmed
Newton. Next: measure `d_eff`, test a 1-D (stripe) reward, and run the amplitude sweep.

### 8b. Modal geometry sweep — 2-D exponent falsified; measured d_eff ≈ 1

Ran the decisive Modal sweep on 2026-07-02
(`modal_reward_deformation_sweep.py`; 3 geometries × 3 amplitudes × 64 seeds,
Ng=256, Np=256, 8000 steps, capacity bottleneck, H100 workers). The sweep was
pre-registered in `papers/grid_cell_weakness/preregistration.md` before dispatch.

Primary `A=6` area-density exponents:

| reward geometry | measured α | 95% bootstrap CI | SE | implied d_eff |
| --- | ---: | ---: | ---: | ---: |
| aniso2d (genuinely 2-D field) | **+0.309** | [0.304, 0.314] | 0.0025 | 0.90 |
| stripe (1-D field) | **+0.302** | [0.298, 0.307] | 0.0023 | 0.87 |
| point (radial field) | **+0.283** | [0.278, 0.288] | 0.0025 | 0.79 |

This resolves the open question against the clean 2-D law as stated. The
`aniso2d` geometry does **not** approach `α = 1/2`; its CI excludes 0.5 by a wide
margin, and its difference from the stripe exponent is small (Δ=+0.0065,
bootstrap 95% CI [−0.0003, +0.0132]). All primary standard errors are below the
pre-registered 0.02 precision target, so this is not an underpowered ambiguity.

Honest conclusion: the capacity constraint and value-driven metric deformation
are real, but the trained grid/RNN harness reallocates representational
resolution with a measured effective dimension near 1, even under a 2-D reward
field. The "Newton" claim must therefore be revised from "confirmed
parameter-free 2-D exponent" to "a measured finite-capacity effective-dimension
law, with d_eff≈1 in this architecture." The 2-D variational law remains a
normative high-resolution prediction, not the empirical law of this system.

## 9. Prior art anchoring

- Bennett (1948), high-resolution quantization: optimal point density `∝ p^{1/3}` (1D).
- Ganguli & Simoncelli (2014), *Efficient sensory encoding and Bayesian inference*: neural
  resource allocation `∝ prior^{power}`; the d-dimensional generalisation used here.
- Sorscher, Mel, Ganguli, Ocko (2019): grid/torus codes as the optimum of an efficiency objective
  — the substrate on which this reward-conditioned version is tested.
