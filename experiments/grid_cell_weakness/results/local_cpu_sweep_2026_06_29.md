# Grid-Cell Weakness — Local CPU Sweep (2026-06-29)

Pre-registration: [papers/grid_cell_weakness/preregistration.md](../../../papers/grid_cell_weakness/preregistration.md).
Runner: `experiments/grid_cell_weakness/run_local.py`. Backend: local CPU.
Manifest: 3 conditions × 2 seeds = 6 nets; Ng=128, Np=100, T=20, steps=4000,
batch=128, activity_reg=2e-3. Wall time ≈ 1410 s. This is a **reduced** sweep
(RNN only, 2 seeds, no larger-arena OOD); the full Modal sweep evaluates all six
gates. Raw JSON is gitignored; this report is the committed summary.

## Per-network results

| condition | seed | weakness | toroidal score | β₁ | OOD acc (same-arena) | torus match |
|---|---:|---:|---:|---:|---:|:--:|
| full_translation | …628 | 0.754 | 0.307 | 2 | 0.950 | yes |
| full_translation | …728 | 0.839 | 0.229 | 3 | 0.950 | no |
| none | …628 | 0.234 | 0.000 | 16 | 0.967 | no |
| none | …728 | 0.489 | 0.000 | 29 | 0.981 | no |
| wrong_group | …628 | 0.000 | 0.005 | 6 | 0.973 | no |
| wrong_group | …728 | 0.012 | 0.004 | 6 | 0.979 | no |

## Gate signals

| Signal | Value | Reading |
|---|---:|---|
| G5 weakness ↔ spectral concentration (−Fourier PR) | ρ = +0.89 | **confirmed** |
| G6 causal: full-translation vs none (toroidal score) | 0.27 vs 0.00 | **confirmed** |
| G1 full-translation forms toroidal codes (β₁=2 + void) | 0.50 | partial (n=2) |
| G2 weakness ↔ toroidal score | ρ = +0.37 | weak-positive (n=6) |
| G3 weakness ↔ OOD accuracy | ρ = −0.60 | untestable at this scale |

## Reading

**Confirmed at CPU scale.**
- **Weakness separates the conditions cleanly:** full-translation 0.75–0.84 ≫ none 0.23–0.49 ≫
  wrong-group 0.00–0.01. The wrong-group null collapses weakness to ≈0 exactly as pre-registered.
- **Spectral leg (G5):** weakness tracks spectral concentration of the rate maps at ρ = +0.89 —
  high-weakness codes use few aligned Fourier modes, the irrep-selection prediction.
- **Topology causal contrast (G6):** translation augmentation produces toroidal structure
  (mean toroidal score 0.27) while the unaugmented and wrong-group conditions do not (0.00, ≈0.005).
  The single best net is a clean torus (β₁=2, weakness 0.754).

**Not testable at this scale (a proxy limitation, not a refutation).**
- **G3 weakness ↔ OOD:** all six nets decode held-out trajectories at 0.95–0.98 (std 0.013). The
  local OOD proxy is *same-arena* held-out trajectories — in-distribution geometry — so it saturates
  and carries no variance for weakness to predict; the ρ = −0.60 is noise on a flat axis. The
  pre-registered OOD metric is decoding in a *larger, never-seen arena* (the `--decode-arenas` sweep
  in the Modal worker), which the CPU runner omits. **G3/G4 require the Modal sweep.**
- **G2 weakness ↔ toroidal score** is positive but weak (ρ = +0.37) because one of the two
  full-translation nets formed a β₁=3 code rather than a clean torus; more seeds (Modal) are needed.

## Next

- Run the full Modal sweep (`modal_grid_cell_weakness_sweep.py`, `--seeds 8 --steps 4000
  --decode-arenas 1.0,1.25,1.5,2.0`) to test G2–G4 with real OOD geometry and more seeds.
- The emergence runbook's knobs (steps, activity_reg) should lift the β₁=2 match rate above the
  0.50 seen here before reading G1/G2 as final.
