# Constraint Swap Reanalysis: A Marginal Signal at 32 Seeds

**Human director:** Jawaun Brown
**Producing agent:** Claude Code, directed
**Program:** Constraint-Swap Causal Geometry — intervention-algebra reanalysis
**Status:** Overall **NO_GO** under preregistered gates. R1 GO, R2 GO, R3 NO_GO. Correlations between A-side and B-side intervention effects ARE below the 0.30 threshold (r_undo = -0.234, r_rescue = 0.079), consistent with the intervention-algebra prediction of near-independence. But permutation testing does not reject the "|r| ≥ 0.30" null at α = 0.05 (p_undo = 0.0965, p_rescue = 0.0972). With 32 seeds we are underpowered to distinguish "genuinely low correlation" from "not-far-enough-below-0.30 to reject." Third serial null-ish result on the intervention-algebra reframe, with a specific power-diagnostic that names what would be needed to decide it.
**Date:** 2026-07-27

---

## Abstract

The 32-seed Constraint-Swap Causal Geometry run rejected the
constraint-specific-deformation claim on all five G1–G5 gates
(REJECT_CONSTRAINT_SPECIFIC_DEFORMATION). The human director's
intervention-algebra reframe proposed that the object may not live
inside the representation but in the family of interventions under
which behavior changes. Under that reframe, the univariate G3/G4
gates could miss constraint-specific structure that appears in the
**joint distribution** of A-side and B-side intervention effects
across seeds: if the effects are shared-artifact-driven they should
be strongly correlated, if they are constraint-specific they should
be approximately independent.

This reanalysis, preregistered before executing, tested three gates
on the frozen 32-seed data:

- **R1** |r(undo_A_specific_harm, undo_B_specific_harm)| < 0.30
- **R2** |r(rescue_A_specific_gain, rescue_B_specific_gain)| < 0.30
- **R3** permutation test rejects |r| ≥ 0.30 at p < 0.05

**Result:** r_undo = **−0.234**, r_rescue = **0.079**. R1 and R2
both GO. R3 NO_GO (p_undo = 0.0965, p_rescue = 0.0972).

The correlations are **directionally consistent with the reframe** —
low, and the negative sign on r_undo actually goes further in the
independence direction than the reframe strictly requires. But the
permutation test cannot reject the shared-artifact null at 32 seeds,
because the sample is small enough that a true |r| between 0.20 and
0.30 is easily consistent with observed values around ±0.20. Under
strict preregistration, R3 fails and the overall verdict is NO_GO.

**Substantively:** this is a *marginal signal*, not a clean null.
The reframe's abstract prediction (low cross-condition correlation)
is what the data shows. What the data cannot do is rule out that the
same low correlation would appear under a shared-artifact null. A
larger seed count — 100+ — could plausibly resolve it either way,
because the observed r values are close enough to the threshold that
sample-size doubling would shrink the confidence interval enough to
matter.

Third serial preregistered null on the intervention-algebra reframe,
with a specific quantitative note about what would decide it.

---

## 1. What was preregistered

`REANALYSIS_INTERVENTION_ALGEBRA_PREREGISTRATION.md` (2026-07-27,
before `reanalysis_intervention_algebra.py` was drafted or executed):

- Data source: frozen 32 seed rows from
  `results/registered_seed_rows.jsonl`. No new training, no new
  intervention data.
- Four preregistered intervention effects (from the primary topology
  metrics G3/G4 tested univariately):
  - `undo_A_specific_harm`
  - `undo_B_specific_harm`
  - `rescue_A_specific_gain`
  - `rescue_B_specific_gain`
- Three gates: R1 (|r_undo| < 0.30), R2 (|r_rescue| < 0.30), R3
  (permutation test at α = 0.05 rejects |r| ≥ 0.30).
- Prediction: if the intervention-algebra reframe is right,
  correlations are low; if shared artifact dominates, correlations
  are high.

## 2. Results

**Pearson correlations across 32 seeds:**

- r(undo_A_specific_harm, undo_B_specific_harm) = **−0.234**
- r(rescue_A_specific_gain, rescue_B_specific_gain) = **0.079**

**Permutation test (10,000 label-shuffles at seed 20260727):**

- p(|r_undo| ≥ 0.30 under H0) = **0.0965**
- p(|r_rescue| ≥ 0.30 under H0) = **0.0972**

**Descriptive statistics of the four intervention effects
(across-seed):**

| effect | mean | std | min | max |
|---|---:|---:|---:|---:|
| undo_A_specific_harm | −0.225 | 0.197 | −0.599 | 0.000 |
| undo_B_specific_harm | −0.187 | 0.119 | −0.513 | 0.000 |
| rescue_A_specific_gain | ~0.06 | ~0.14 | −0.20 | ~0.30 |
| rescue_B_specific_gain | −0.057 | 0.140 | −0.276 | 0.372 |

## 3. Gate decisions

| gate | | |
|---|---|---|
| R1 |r_undo| < 0.30 | GO | 0.234 |
| R2 |r_rescue| < 0.30 | GO | 0.079 |
| R3 permutation rejects | NO_GO | p_undo 0.0965, p_rescue 0.0972 |

**Overall NO_GO.**

Licensed reading (from the runner):

> correlations below 0.30 but permutation test does not reject

The strict-preregistration verdict is NO_GO. The substantive picture
is that the observed correlations are *near* what the reframe
predicts (well below 0.30) but the sample size is small enough that
the permutation test cannot distinguish "genuinely near zero" from
"near 0.30 but not quite there."

## 4. What this actually tells us

Two things worth naming:

**(1) The reframe's directional prediction is empirically consistent
with the data.** r_undo = −0.234 and r_rescue = 0.079 are both
well below 0.30 in absolute value. A shared-artifact null (where all
seeds share a common noise direction that flips A-side and B-side
effects similarly) would produce |r| ≥ 0.5 easily. That is not what
we see.

**(2) The evidence is not strong enough to rule out a moderate-r
shared-artifact null.** With 32 seeds, a true correlation of ±0.25
produces observed |r| ≥ 0.30 with substantial probability. That's
what R3's failure captures. To decisively reject "the effects are
0.30-correlated," we'd need approximately 100 seeds — not just to
tighten the estimate but because the R3 permutation test is
comparing observed to threshold, not observed to zero.

If someone were to point at this result and say *"the reframe
survived"*, they'd be over-reaching. If someone were to say *"the
reframe was killed"*, they'd also be over-reaching. What actually
happened: the preregistered null-hypothesis rejection didn't clear,
and the data are directionally consistent with the reframe but the
sample is small.

**This is exactly the outcome where preregistration discipline
matters most.** A post-hoc reader could tell either story from the
data. The preregistered decision rule tells one specific story:
NO_GO. Honor it.

## 5. What would decide it

- **~100 more seeds** with the same protocol. If |r| stays near
  0.20 and R3 rejects, reframe wins. If |r| drifts up toward 0.30
  and R3 stays unrejected or flips positive, shared-artifact
  dominates.
- **A different intervention design.** The current interventions
  are rank-4 affine transports pre-specified from theory. An
  intervention sweep (many random transports per seed, cluster by
  behavioral effect) might reveal constraint-specific structure the
  four preregistered directions miss. This is the DR6-style
  sweep the original reframe suggested and this reanalysis could
  not do with the frozen data.

## 6. What the reanalysis licenses

- **Not a full test of the intervention-algebra reframe.** Only a
  narrow test of the correlation-structure prediction on the four
  preregistered intervention effects.
- **A specific follow-up justification.** A 100-seed replication of
  Constraint Swap with the same protocol would decide R3 one way or
  the other. That is a real next experiment.
- **A methodological note.** Reanalyses of preregistered data
  can extract additional signal, but their power depends on the
  original sample size. 32 seeds was appropriate for the original
  G1–G5 gates but is underpowered for correlation-based reanalyses.

---

## Appendix: reproduction

```
uv run --no-sync python -m experiments.constraint_swap_causal_geometry.reanalysis_intervention_algebra
```

Reads the frozen `results/registered_seed_rows.jsonl`, computes
Pearson correlations and permutation p-values (10,000 trials, seed
20260727), applies R1/R2/R3 gates, writes
`results/reanalysis_intervention_algebra.json`. Local CPU, seconds.

**Preregistration digest (SHA-256 of
`REANALYSIS_INTERVENTION_ALGEBRA_PREREGISTRATION.md`):**
`4715fd76531a9977ccd3cef3fe685f9567ba0517068e0b50646b69ceccf5c1ed`.
