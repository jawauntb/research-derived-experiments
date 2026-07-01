# Capacity-Bottlenecked Exponent Test (2026-07-01)

Follow-up to `results/ratedistortion_2026_07_01.md`. The first test failed because nothing enforced
a capacity budget. Here the population state is projected onto a **unit sphere each step** (hard
finite-capacity manifold) and a **fixed-variance Gaussian channel** is added before decoding
(finite SNR, so resolution matters) — the two load-bearing assumptions of the rate-distortion
derivation ([notes/reward_deformation_ratedistortion.md](../../../notes/reward_deformation_ratedistortion.md)).
Predicted area-density exponent (d=2): **1/2**. Runner:
`experiments/grid_cell_weakness/capacity_bottleneck.py`. Raw JSON gitignored.

## Result — the capacity constraint is causal; exponent partially confirmed

| config | area exponent α | R² | vs no-constraint (0.07) |
| --- | ---: | ---: | --- |
| no capacity constraint (prior test) | **+0.07** | 0.15 | baseline |
| bottleneck (noise 0.15, 2500 steps, 3 seeds) | **+0.31** | 0.44 | **+0.24** |
| bottleneck (noise 0.25, 4000 steps, 2 seeds) | **+0.27** | 0.33 | +0.20 |

**Adding the capacity bottleneck is causal and large:** it moves the exponent ~4–5× toward the
prediction (0.07 → ~0.30) and roughly triples the log–log fit quality. This confirms the
**mechanism** of the law — a finite-capacity code is *forced* to trade resolution, and the
allocation follows a power of the reward field. The exponent is robust across seeds and does not
climb further with more training or stronger noise; it **plateaus at α ≈ 0.30**, below the 2-D
prediction of 0.50.

## Honest reading of the gap (0.30 vs 0.50)

The mechanism is confirmed; the *exact* 2-D exponent is not. Notably **α ≈ 0.30 is close to the
1-D rate-distortion prediction, 1/3 ≈ 0.33.** A plausible (post-hoc, untested) explanation: the
reward bump is radially symmetric, so the code may reallocate resolution mainly **along the reward
gradient (effectively 1-D)** rather than isotropically in 2-D, giving `d_eff ≈ 1` → exponent 1/3.
Alternative contributors: the grid/periodic code is not in the smooth high-resolution asymptotic
that `D ∝ ρ^{-2/d}` assumes; the unit-sphere is an imperfect `∫ρ = R`; 16×16 metric estimation is
noisy (R² ≈ 0.4).

This is a **partial confirmation**, stated as such: the law's causal assumption is validated and
the exponent is in the predicted family (positive power law, ~0.3–0.5), but the specific 2-D value
is not hit. It is a real step toward the "Newton" — not a claim of one.

## Next tests (to resolve 1/3 vs 1/2, without p-hacking)

1. **Measure effective dimension** of the reallocation (PCA of the metric deformation) and predict
   the exponent from the measured `d_eff`, rather than assuming 2.
2. **Anisotropic / 1-D reward** (a stripe): if the effective-1D hypothesis is right, a 1-D reward
   should still give ≈ 1/3; a genuinely 2-D reward field with 2-D reallocation should approach 1/2.
3. **Amplitude sweep** to test the `(1+A)^{d/(d+2)}` scaling independently of the local exponent.
4. **Explicit information bottleneck** (rate penalty) instead of the sphere, as a cleaner `∫ρ = R`.
