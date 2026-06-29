# Reward Deformation (Experiment ① + ③) — CPU Results (2026-06-29)

Runner: `experiments/grid_cell_weakness/reward_deformation.py` (3 conditions × 3 seeds,
Ng=96, steps=2500). The non-circular test: a reward is an injected, independent variable;
we measure whether the learned code's **induced metric** (local resolution) deforms
specifically at the reward and tracks it when moved, control-subtracted against matched
no-reward networks. Paper: `papers/pdf/concern_deforms_metric.pdf`. Raw JSON gitignored.

## Headline result (confirmed)

**A reward signal deforms the induced metric specifically at the rewarded location, and the
deformation tracks the reward when it is moved.**

| Test | Value | Reading |
|---|---:|---|
| control-subtracted specificity, reward@A (A vs B) | **+0.65** | metric warps at A |
| control-subtracted specificity, reward@B (B vs A) | **+1.27** | metric warps at B |
| metric asymmetry density(A)−density(B), reward@A | **+0.69** | A favoured |
| metric asymmetry density(A)−density(B), reward@B | **−1.23** | B favoured |
| metric asymmetry, no-reward control | **+0.04** | flat (reward drives the warp) |

Both specificities are positive → each reward warps the metric at *its own* location more
than at the other; the control is flat, so the asymmetry is created by the reward, not arena
geometry. Because reward location is injected independently of the geometry, this is a causal,
non-tautological result (unlike the passive weakness↔generalization correlations).

## Supporting result

**Local resolution is bought at the cost of global generalization.** Larger-arena (1.25×) OOD
decoding falls from **0.60 (control) to 0.41–0.45 under reward** — the code reallocates a finite
resolution budget toward the goal at the expense of accuracy elsewhere.

## Honest negative

The complementary **local-weakness** signature is **not claimed**: the local-weakness probe
shows a positional confound (the no-reward control already has an A-vs-B asymmetry of comparable
size; weakness-trade A/B/control = +0.55 / +0.61 / +0.33), so a local weakness change cannot be
attributed to the reward at this scale.

## Scope

n = 3 seeds, one architecture, reward as loss-reweighting (not an explicit value head); the
larger-arena OOD probe is limited by place-cell coverage beyond the trained region. This is a
**proof-of-concept**, at the Kepler (phenomenon) stage — not a derived law and not yet
main-track strength. Next: larger multi-seed sweep with a value head and significance tests, a
topological readout of the warp, and a positional-control local-weakness accounting.
