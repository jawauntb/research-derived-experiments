# Passive-to-Active Phase Map Preregistration

Revision 2 recorded on 2026-07-14 after scientific review of the Revision 1
implementation. Revision 1 had resampled the two architecture rows within each
seed as if they were independent. Revision 2 corrects the independent unit to
the seed cluster, retains both architectures inside each resampled seed, and
replaces the logically asymmetric `continuous_crossover` failure label with
`bifurcation_not_supported`. No metric, threshold, seed, architecture, coupling
grid, training run, or raw cell changed; the committed summary was regenerated
and re-adjudicated under the corrected inference.

Revision 1 was frozen before the inferential local-CPU run. An earlier
implementation dry run was invalidated before interpretation because cells at
the same coupling had equal per-stage but unequal cumulative update budgets.
Those outputs were discarded. Revision 1 fixed that integrity defect without
changing any metric, threshold, seed, architecture, or coupling-grid decision.

This experiment is a bounded first tranche for `T-SYS-011` and `T-SYS-012`. It
tests a controlled synthetic mechanism and cannot establish a dynamical
attractor, biological criticality, or foundation-model generality.

## Hypotheses

1. Increasing action coupling produces a reproducible discontinuity, rather
   than a smooth crossover, in at least two independent order parameters.
2. Matched-budget forward and reverse coupling paths produce hysteresis that
   survives washout and disappears under reinitialization.

Failure of the first gate will be reported as **bifurcation not supported**;
failure alone is not positive evidence for a smooth crossover. Failure of the
second gate will be reported as **no registered hysteresis**. Visual inspection
cannot upgrade either verdict or establish its alternative.

## Frozen design

- Coupling grid: `0.0, 0.1, ..., 1.0` (11 points).
- Architectures: two trainable bottlenecks, `linear` (width 2) and `tanh`
  (width 4).
- Seeds: `0, 1, 2, 3, 4`.
- Samples per seed: 192 balanced synthetic examples.
- Phase-map budget: 80 full-batch updates from the identical seeded
  initialization at every coupling.
- Path budget: 11 monotone stages with 32 updates per stage (352 updates total)
  for every forward/reverse cell at every target coupling.
- Learning rate: 0.055.
- Bootstrap resamples: 1,000, deterministic bootstrap seed 101.
- Retention checkpoints after high-coupling training: `0, 8, 24, 48, 80`
  neutral-coupling updates.

The synthetic input has one task-relevant axis and higher-variance nuisance
axes. The model jointly optimizes reconstruction and a coupling-weighted binary
action loss. Coupling is the weight on the action objective.

## T-SYS-011 order parameters

- Causal specific effect: accuracy loss after ablating the task-aligned latent
  axis minus the loss after an orthogonal random-axis ablation.
- Perturbation failure rate: fraction of initially correct decisions broken by
  a registered task-axis perturbation.
- Viability buffer: normalized signed action-logit margin.
- Geometry gap: class-centroid distance divided by within-class latent scale.
- Return: `2 * accuracy - 1`.

For each architecture and seed, every coupling starts from the same seeded
initialization and sees identical data. Only coupling changes.

## Bifurcation gate

At each architecture, curve shape is fitted on four seeds and scored on the
held-out fifth seed. The discontinuous candidate is a piecewise-linear model
with a fitted step. Smooth nulls are a cubic polynomial and a bounded sigmoid
with fitted midpoint and steepness.

Call **bifurcation** only if all conditions hold:

1. The discontinuous model reduces held-out mean squared error by at least 10%
   relative to the best smooth null for at least two order parameters.
2. The causal-specific-effect critical coupling differs by no more than 20%
   across the two architectures, and at least 80% of architecture/seed critical
   estimates are within 20% of the pooled median.
3. At least two qualifying order parameters place their median critical point
   within one preregistered coupling-grid step.
4. Coverage includes both architectures and all five seeds.

Any failure yields `bifurcation_not_supported`. A separate positive crossover
criterion would be required to claim a continuous crossover.

## T-SYS-012 paths and controls

For each architecture, seed, and target coupling, a fresh model follows one of
two fixed-length, 11-stage monotone schedules. The forward schedule is linearly
spaced from coupling 0 to the target; the reverse schedule is linearly spaced
from coupling 1 to the target. Both therefore end at the same target after the
same 352 updates.

The three conditions are:

- Continuation: model state is carried across all 11 monotone stages.
- Reinitialization control: every stage restarts from the identical seeded
  initialization and receives the same 32 updates; only the final target stage
  can affect the measured model, while executed budgets remain direction
  matched.
- Washout control: before every stage after the first, both directions receive
  8 neutral-coupling updates, then the same 32 scheduled-coupling updates (432
  total updates per measured cell).

Thus every forward/reverse comparison at a given target has an exactly matched
cumulative update budget within its condition; washout history is also
symmetric between directions.

## Hysteresis gate

The registered hysteresis statistic is the paired forward-minus-reverse causal
specific effect. Seeds are the independent bootstrap units: resampling selects
whole seed clusters and retains both architecture-specific differences inside
each selected seed. Call **hysteresis** only if all conditions hold:

1. The paired bootstrap 95% interval excludes zero at two or more contiguous
   coupling points.
2. Absolute trapezoidal loop area is at least 0.02.
3. At least two contiguous significant points also survive the symmetric
   washout control.
4. Reinitialization has no contiguous significant points and loop area is at
   most 0.01.

Any failure yields `no_hysteresis`.

## Artifact policy

Per-seed phase, path, and retention cells are generated into
`artifacts/passive_active_phase_map/registered_cells.json` and remain
gitignored. Only aggregate curves, model comparisons, gate components, and
bounded conclusions are written to `results/`.
