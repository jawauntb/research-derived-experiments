# Reward-Deformation Newton Sweep — Modal Results (2026-07-02)

Pre-registration: [papers/grid_cell_weakness/preregistration.md](../../../papers/grid_cell_weakness/preregistration.md),
frozen addendum "Reward-Deformation Exponent Gate" (2026-07-02). Runner:
`experiments/grid_cell_weakness/modal_reward_deformation_sweep.py`. Backend:
Modal H100 workers. Raw JSON is gitignored; combined artifact:
`artifacts/grid_cell_weakness/reward_deformation_sweep_2026_07_02_combined.json`.

Manifest: 3 reward geometries × 3 amplitudes × 64 seeds = **576 trained
capacity-bottleneck RNNs**; Ng=256, Np=256, T=20, steps=8000, batch=128,
noise_std=0.15. The 64 seeds were run as four non-overlapping 16-seed shards to
avoid Modal runner heartbeat timeouts.

## Primary Gate Verdict

The preregistered 2-D rate-distortion law is **not confirmed**. At the primary
amplitude `A=6`, the genuinely 2-D `aniso2d` geometry does **not** approach
`alpha = 1/2`; it remains near the same effective-1D exponent family as the
stripe condition.

| Geometry | A | area exponent α | 95% bootstrap CI | bootstrap SE | implied d_eff | mean R² |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| aniso2d | 6 | **+0.309** | [0.304, 0.314] | **0.0025** | 0.896 | 0.528 |
| stripe | 6 | **+0.302** | [0.298, 0.307] | **0.0023** | 0.869 | 0.565 |
| point | 6 | **+0.283** | [0.278, 0.288] | **0.0025** | 0.792 | 0.417 |

All primary standard errors are far below the preregistered `<= 0.02` precision
target. The `aniso2d` 95% CI excludes both `1/2` and `1/3`; however, it is much
closer to `1/3` than `1/2`, and the aniso2d-vs-stripe exponent difference at
`A=6` is small: Δ = +0.0065 with bootstrap 95% CI [−0.0003, +0.0132], not a
decisive separation.

## Full Exponent Table

| Geometry | A=3 α | A=6 α | A=12 α | Reading |
| --- | ---: | ---: | ---: | --- |
| aniso2d | +0.334 [0.329, 0.338] | +0.309 [0.304, 0.314] | +0.318 [0.313, 0.322] | near d_eff≈0.9–1.0, not 2 |
| stripe | +0.297 [0.291, 0.302] | +0.302 [0.298, 0.307] | +0.318 [0.314, 0.322] | near d_eff≈0.85–0.94 |
| point | +0.324 [0.318, 0.330] | +0.283 [0.278, 0.288] | +0.279 [0.275, 0.283] | weaker radial allocation, d_eff≈0.8 |

Peak-resolution ratios increase monotonically with amplitude in all three
geometries (e.g. point 1.319→1.400→1.515; stripe 1.289→1.348→1.428; aniso2d
1.300→1.369→1.443), confirming that reward/concern increases local resolution.
The exponent governing that reallocation is not the predicted 2-D value.

## Reading

**Confirmed.** The capacity-bottleneck mechanism is real and highly powered:
reward weighting reliably produces a positive log-log relation between value
density and induced area-density, with tight uncertainty and R² around
0.4–0.7. The measured effective dimension is consistently near 1.

**Falsified as stated.** The proposed 2-D parameter-free law
`sqrt(det g) ∝ w^(1/2)` does not survive the decisive geometry sweep. Even a
genuinely 2-D anisotropic reward field remains near `alpha≈0.31`, not `0.5`,
and it does not separate cleanly from the stripe condition. The honest Newton
paper is therefore not "we confirmed the 2-D law"; it is "finite-capacity
reward deformation obeys a measured effective-dimension law near d_eff≈1 in
this grid/RNN harness."

**Scope caveat for Paper B.** This Modal entrypoint resolves the exponent and
amplitude-scaling question at big n. It does not rerun the original moved-location
A/B specificity design from `reward_deformation.py`; that older location-tracking
claim remains the n=3 CPU proof-of-concept until a dedicated moved-reward Modal
entrypoint is run. Do not inflate this result into a moved-location specificity
replication.
