# Grid-Cell Weakness (Paper A scale-up)

Tests whether **weakness** predicts the **toroidal topology** and **OOD generalization** of a
learned population code on a path-integration task — scaling the symbolic weakness flagship onto
the substrate where brains and RNNs both produce a torus (Gardner et al. 2022; Sorscher–Ganguli).

Pre-registration: [`papers/grid_cell_weakness/preregistration.md`](../../papers/grid_cell_weakness/preregistration.md).
Runbook (dispatch + emergence tuning): [`papers/grid_cell_weakness/runbook.md`](../../papers/grid_cell_weakness/runbook.md).
Strategy: [`notes/weakness_topology_program_synthesis.md`](../../notes/weakness_topology_program_synthesis.md).

## Files

- `core.py` — canonical harness: path-integration RNN + task, and the four metrics
  (`weakness_translation`, `toroidal_score`, `fourier_participation_ratio`, OOD), plus synthetic
  torus/plane/sphere samplers for metric validation. Homology via `gudhi` (fallback `ripser`).
- `pilot.py` — local CPU design pilot: (1) metric-discrimination check on synthetic manifolds,
  (2) end-to-end RNN smoke. Run: `python experiments/grid_cell_weakness/pilot.py`.
- `modal_grid_cell_weakness_sweep.py` — self-contained Modal sweep (one net per cell), evaluates
  gates G1–G6. Worker helpers are inlined to match the house pattern.
- `results/pilot_2026_06_28.md` — committed pilot report.

## Key design point

Weakness is measured under **wrapped (periodic) grid translations**. This is load-bearing: a
toroidal (periodic) code stays equivariant under wrapped translation, while a merely
translation-equivariant *plane* code breaks at the wrap seam. The pilot confirms the separation
(torus weakness 0.998 vs plane 0.300; torus β₁=2 + void vs none for plane/sphere).

## Running the Modal sweep (from a Modal-authed machine)

This environment has no Modal auth; dispatch from your laptop as with the other sweeps:

```
# smoke first
doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
        experiments/grid_cell_weakness/modal_grid_cell_weakness_sweep.py \
        --seeds 1 --steps 400 --conditions full_translation,none

# full sweep (5 conditions x 2 archs x 8 seeds), with the larger-arena OOD sweep
doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
        experiments/grid_cell_weakness/modal_grid_cell_weakness_sweep.py \
        --seeds 8 --steps 4000 --decode-arenas 1.0,1.25,1.5,2.0 \
        --out artifacts/grid_cell_weakness/sweep.json
```

`--decode-arenas` is a comma list of arena scales; `1.0` is in-distribution (`id_accuracy`),
scales `> 1.0` are never-seen geometry, and the **largest** is the primary OOD metric for gates
G3/G6 (per-cell `ood_by_arena` records all of them). The entrypoint prints
`ρ(weakness,topology)`, `ρ(weakness,OOD)`, the G4 partial correlation, and the G1–G6 pass flags,
and writes the full per-cell JSON.

**Before trusting gates:** run the emergence probe in the
[runbook](../../papers/grid_cell_weakness/runbook.md) — if the `full_translation` nets don't form
a torus (`betti_match_torus`), tune steps / activity-reg / hidden size first. Emergence is a
precondition, not the hypothesis.
