# Constraint Swap — Intervention-Algebra Reanalysis Preregistration

**Package:** `experiments/constraint_swap_causal_geometry/` (reanalysis)
**Predecessor:** REJECT_CONSTRAINT_SPECIFIC_DEFORMATION (32-seed
registered run; all G1–G5 causal gates failed)
**Date:** 2026-07-27
**Written:** BEFORE the reanalysis is executed. No new training,
no new intervention data. Reanalysis uses the frozen 32-seed rows in
`results/registered_seed_rows.jsonl` only.

## 0. What this reanalysis tests

The registered run rejected the "constraint-specific reachability
geometry is causally relevant to behavior" claim on 32 seeds. The
human director's reframe (2026-07-27): perhaps the object doesn't
live inside the representation but in the **intervention algebra**
— the family of interventions under which behavior changes.

Under that reframe, the registered univariate G1–G5 tests (each
looking at a single intervention→behavior effect) may miss
constraint-specific structure that appears in the **joint
distribution** of intervention effects across seeds. Specifically:

- If the intervention effects are dominated by seed-level artifact
  (initialisation noise, training-run variance), the A-side and
  B-side effects should be **strongly correlated across seeds** —
  every seed's noise flips both directions similarly.
- If constraint-specific structure exists but is invisible to
  univariate means, A-side effects should be **weakly correlated
  with B-side effects** across seeds — each seed responds to the
  operative constraint independently.

This gives one specific preregistered test.

## 1. The test

Load `results/registered_seed_rows.jsonl`. For each seed, extract
four preregistered univariate intervention effects (the ones
G3/G4 tested):

- `undo_A_specific_harm` (primary topology)
- `undo_B_specific_harm` (primary topology)
- `rescue_A_specific_gain` (primary topology)
- `rescue_B_specific_gain` (primary topology)

Compute two Pearson correlations across 32 seeds:

1. `r_undo = corr(undo_A_specific_harm, undo_B_specific_harm)`
2. `r_rescue = corr(rescue_A_specific_gain, rescue_B_specific_gain)`

## 2. Gates

Three preregistered non-compensatory gates.

- **R1** — |r_undo| < 0.30. Undo-A and undo-B effects are
  approximately independent across seeds, consistent with each
  responding to a distinct latent constraint-specific structure.
- **R2** — |r_rescue| < 0.30. Same for rescue.
- **R3** — a permutation test rejects the null "|r| ≥ 0.30" at
  p < 0.05, computed by 10,000 seed-label shuffles.

**Overall GO** iff all three gates GO. GO would provide the first
empirical support for the intervention-algebra reframe on this data:
the intervention effects carry seed-independent, constraint-specific
structure that the univariate G1–G5 tests missed.

## 3. What GO would license

- The intervention-algebra reframe is empirically supported for this
  specific dataset, in the narrow sense that A-side and B-side
  intervention effects are approximately uncorrelated across seeds
  when they would be strongly correlated under a shared-artifact
  null.
- **A specific follow-up** would then be justified: repeat the
  32-seed experiment on a real vision-language model (rather than
  toy meta-GRU) to check whether the constraint-specific structure
  survives at larger scale.

## 4. What NO_GO would establish

- The intervention effects ARE correlated across seeds (shared
  artifact). Combined with the original G1–G5 failures, this is a
  stronger falsification of the constraint-specific-deformation
  claim: not only is the mean effect wrong, but the effects are
  driven by seed noise rather than constraint-specific mechanism.
- Combined with DCR3b (if that also returns null), three serial
  nulls on the "object lives in the intervention algebra" reframe
  and its DCR analogue. The reframe would then be another elegant
  unification that didn't survive.

## 5. Single-shot

One reanalysis pass, one verdict, no replay. The 0.30 threshold and
the permutation-test alpha of 0.05 are set here and cannot be
adjusted post-hoc. If R1 or R2 fails but a smaller |r| threshold
would pass, that is a failure — the threshold is committed.
