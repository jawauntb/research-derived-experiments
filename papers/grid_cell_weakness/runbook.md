# Paper A Runbook — Grid-Cell Weakness Sweep

Operational companion to [preregistration.md](preregistration.md). Covers dispatch, the
larger-arena OOD sweep, and grid-cell **emergence tuning** — the one thing that can make the
whole sweep null if it is off, since the gates require networks that actually form a torus.

Harness: `experiments/grid_cell_weakness/{core,pilot,modal_grid_cell_weakness_sweep}.py`.

## Dispatch

No Modal auth in the web session; dispatch from a Modal-authed machine.

```
# 1) smoke (1 seed, short) — confirms the worker runs on Modal end to end
doppler --scope /Users/jawaun/superoptimizers run -- \
  uvx --python 3.12 --from modal modal run \
    experiments/grid_cell_weakness/modal_grid_cell_weakness_sweep.py \
    --seeds 1 --steps 400 --conditions full_translation,none

# 2) emergence probe (1–2 seeds, full steps, full_translation only) — see below
doppler --scope /Users/jawaun/superoptimizers run -- \
  uvx --python 3.12 --from modal modal run \
    experiments/grid_cell_weakness/modal_grid_cell_weakness_sweep.py \
    --seeds 2 --steps 4000 --conditions full_translation \
    --out artifacts/grid_cell_weakness/emergence_probe.json

# 3) full sweep (5 conditions × 2 archs × 8 seeds), with the arena OOD sweep
doppler --scope /Users/jawaun/superoptimizers run -- \
  uvx --python 3.12 --from modal modal run \
    experiments/grid_cell_weakness/modal_grid_cell_weakness_sweep.py \
    --seeds 8 --steps 4000 --decode-arenas 1.0,1.25,1.5,2.0 \
    --out artifacts/grid_cell_weakness/sweep.json
```

## Larger-arena OOD sweep (`--decode-arenas`)

`--decode-arenas` is a comma list of arena scales at which the trained net is asked to path-
integrate. Scale `1.0` is the training arena (in-distribution, reported as `id_accuracy`); any
scale `> 1.0` is never-seen geometry. The **primary OOD metric used by gates G3/G6 is the largest
scale** (per the prereg's "held-out larger arena" definition); every scale's accuracy is recorded
per cell under `ood_by_arena`. A grid code should path-integrate into a larger arena gracefully;
a memorized place-code should fall off a cliff — so the `ood_by_arena` curve is itself a diagnostic
of *how* generalization fails, not just whether.

## Grid-cell emergence tuning (do this BEFORE trusting any gate)

The pre-registered gates assume the `full_translation` condition produces toroidal nets
(β₁=2 + a persistent H₂ void). If the **emergence probe** (dispatch step 2) shows
`betti_match_torus = False` for most nets and `toroidal_score ≈ 0`, the network never formed a
grid — the gates would then be measuring noise. **This is a harness-tuning state, not a result.**
Turn these knobs, in order, and re-run the probe until `betti_match_torus` appears in ≥ ~60% of
`full_translation` nets:

1. **Steps.** Grid emergence is slow. Go `4000 → 8000 → 15000`. Cheapest first move.
2. **Activity regularization** (`--activity-reg`, default `1e-3`). This penalizes mean squared
   hidden activity and is the main driver of *localized, periodic* codes (Sorscher–Ganguli use an
   activity/metabolic cost). Sweep `1e-3 → 3e-3 → 1e-2`. Too high → dead units; too low → no grid.
3. **Weight decay** (`--weight-decay`, default `1e-4`). Sweep `1e-4 → 1e-3`. Couples with (2).
4. **Hidden size** (`--ng`, default `128`). Grids need headroom for multiple periods/orientations;
   try `128 → 256`. Place-cell count (`--np`, default `100`) sets target resolution; `144`/`196`
   sharpen it.
5. **Sigma** (`--sigma`, default `0.10`) — place-cell width. Narrower (`0.08`) sharpens the target
   manifold but is harder to fit; wider (`0.12`) is easier but blurs topology.
6. **Trajectory length** `--t` (default `20`). Longer paths give the recurrence more integration
   signal; `20 → 30`.

Re-run only the cheap `full_translation` emergence probe between changes. Lock the first
configuration that clears the β₁=2 bar, record it here, then launch the full sweep with those
values. **Do not** tune against the gate correlations themselves — tune only against
`betti_match_torus` in the `full_translation` condition (emergence is a precondition, not the
hypothesis).

## Anti-cheat reminders

- `wrong_group` weakness (permuted-bin "translations") is the null-control predictor: its
  correlation with OOD must stay `|ρ| ≤ 0.15` (`gates.wrong_group_null_ok`). If it creeps up, the
  population binning is leaking position into the predictor.
- `random_shift` is a *soft* null; it may lift OOD modestly but must stay below `full_translation`
  on `toroidal_score` (part of G6).
- If `coverage` (fraction of spatial bins visited) is low (< ~0.8), increase trajectory count or
  `T` before reading topology — an undersampled manifold fakes broken homology.

## What "done" looks like

A committed `results/sweep_<date>.md` with: the G1–G6 pass table, `ρ(weakness, toroidal_score)`,
`ρ(weakness, OOD)`, the G4 partial-correlation drop, the `ood_by_arena` curves per condition, and
a gate-margin heatmap (controls failing visibly). Then the reward-deformation follow-up (Paper B)
and the PAC-Bayes sketch.
