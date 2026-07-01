# Rate-Distortion Exponent Test (2026-07-01)

Tests the parameter-free prediction of the Reward-Deformation Law
([notes/reward_deformation_ratedistortion.md](../../../notes/reward_deformation_ratedistortion.md)):
under value-weighted rate-distortion with a capacity constraint, the induced metric obeys
`√det g(x) ∝ w(x)^{d/(d+2)}` → **area-density exponent 1/2** (per-axis stretch 1/4) in the 2-D arena.

Runner: `experiments/grid_cell_weakness/ratedistortion_test.py` (2 seeds, Ng=96, 2000 CPU steps,
central reward A=6, σ=0.12). Raw JSON gitignored.

## Result — prediction NOT confirmed at this scale

| exponent | predicted | measured | R² |
| --- | ---: | ---: | ---: |
| area density `√det g` ∝ `w^α` | **0.50** | **+0.07** | 0.15 |
| per-axis stretch ∝ `w^α` | **0.25** | **+0.035** | 0.15 |

The **direction** matches Paper B (metric rises toward the reward → positive exponent), but the
**magnitude is ~7× below** the rate-distortion optimum and the log–log fit is weak. The trained RNN
**under-allocates** resolution relative to the optimal law; it is not at the rate-distortion optimum.

## Diagnosis (→ next steps to actually test the law)

1. **No hard capacity constraint** — the reward reweights the loss but nothing enforces `∫ρ = R`, so
   there is no pressure to *trade* resolution (the derivation's load-bearing assumption). Add a
   bottleneck / fixed-‖r‖ budget.
2. **Under-formed, periodic code** (Ng=96, 2000 CPU steps) violates the smooth high-resolution
   assumption. Scale units + training.
3. **Noisy metric estimation** on a 16×16 binned population; 2 seeds. More seeds + finer grid.
4. **Amplitude sweep** (vary A) to test the `(1+A)^{1/2}` scaling law, not just the local exponent.

## Status

The derived law is a **candidate**; its quantitative prediction is **unconfirmed**. This is an
honest negative for the attempted Kepler→Newton step — we have the warp (Kepler) and a derived
candidate law, but not a confirmed Newton. The value is the concrete test protocol above.
