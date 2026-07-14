# E7 Pre-run Implementation Contract

**Frozen: 2026-07-13 (America/Los_Angeles), after the E7 preregistration and
before any E7 pilot or confirmatory result was run.**

This note resolves implementation details that the E7 preregistration leaves
implicit. It does not change the task order, arms, model widths, seed count,
epoch budget, metrics, margins, or kill criteria in
`e7_selective_subspace_continual_learning_preregistration_2026-07-13.md`.

## Shared architecture across different moduli

One continual model must accept all four moduli. The depth-2 MLP therefore has
a fixed input of `2 × max(T) = 58` one-hot coordinates and a fixed 29-class
head. Task `n` uses the first `n` coordinates of each input half and targets
classes `0..n-1`; unused coordinates/classes are neither relabeled nor
collapsed. Width remains exactly 96 or 128. Adam is reset at each task
boundary for every arm while model parameters persist.

## Matched seeds

Cell seeds follow the frozen component order:

```text
SHA-256("e7|base_seed|namespace|task|arm_scope|seed_index|width") mod 2^31
```

The 128 checkpoint-cell keys use `namespace=cell` and the literal arm, so they
are collision-checked and unique. Objects that must be matched across arms use
an explicit `arm_scope=matched`: one initialization seed per `(seed_index,
width)` and one frozen split seed per `(task, seed_index, width)`. This resolves
the apparent conflict between arm-namespaced cell keys and the preregistered
requirement that initialization and task splits be identical across arms.

## Single frozen protection strength

The CPU pilot has a singleton allowed coefficient set, `{λ = 1.0}`. Thus it
validates scale, execution, and integrity but cannot select a favorable value
from outcome data. EWC's diagonal Fisher is normalized to unit mean across
parameter tensors before applying the shared coefficient. Each selective
penalty is a mean squared projected parameter displacement. No arm- or
cell-specific coefficient is permitted.

## Replay-free selective protection

Only current-task labeled examples enter optimization. At a task boundary the
harness stores tensors, not examples:

- diagonal Fisher and a parameter anchor for EWC;
- the between-orbit basis, boundary-axis mass weight, and parameter anchor for
  selective protection;
- the corresponding `a`-only tensors for the wrong-subspace control.

For a protected last-hidden basis `B`, the selective penalty anchors
`BᵀΔW₂`, `BᵀΔb₂`, and `ΔW_head B`. The first hidden matrix and output bias are
complementary directions and remain unprotected. Bases from every previous
task are retained, and their penalties are averaged. This is the
preregistration's replay-free “projection of the update onto the accumulated
protected subspace” implementation. Earlier-task splits are used only for
boundary evaluation; no earlier examples enter a later task's loss.

## Exact protected mass versus reported #344 patch

The minimum SVD rank whose cumulative between-group mass reaches 0.50 can
overshoot 0.50 by more than the separate ±0.02 validity tolerance. E7 keeps
that complete orthonormal min-rank basis for the reported #344 patch-CE and
normalizes patch-CE by its realized full-rank mass, exactly as #344 did.

For the *protection penalty only*, the final selected axis receives weight

```text
sqrt((0.50 - cumulative_mass_before_axis) / axis_mass)
```

so its realized protected spectral mass is exactly 0.50. Selected rank,
full-rank mass, weighted protected mass, and per-matrix projection norms are
all recorded. This makes the frozen mass-validity rule executable without
changing the inherited causal-patch measurement.

## Compute and timing audit

Every arm constructs the same EWC, correct-subspace, and wrong-subspace shadow
graphs at each step. Only the named arm's term has a nonzero coefficient;
`P_none` has none. This preserves the scientific intervention while matching
tensor-operation shapes and the 1,000 optimizer steps. The harness also records
measured per-task wall time and applies the frozen 2% relative-range gate over
each matched `(width, seed, task-boundary)` four-arm group. Any failure makes
the affected streams invalid rather than relaxing the gate.

## Confirmatory lock

The confirmatory CLI accepts no scientific hyperparameter overrides and
requires a machine-readable pilot receipt with passing seed, sequential-data,
protected-mass, and budget integrity. The pilot remains one seed, width 96,
two tasks, and all four arms; it cannot support a scientific claim.
