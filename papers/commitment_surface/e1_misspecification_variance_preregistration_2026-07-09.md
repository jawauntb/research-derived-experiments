# E1 Follow-up Addendum — Misspecification Variance

**Frozen:** 2026-07-09 21:36 EDT (2026-07-10 01:36 UTC), before running the
follow-up harness.

**Relationship to the original plan.** This addendum does not alter or
reinterpret the gates frozen in `PLAN.md`. The original E1
misspecification-equivalence sub-gate remains a strict failure
(`-0.054159416947479166` versus the frozen `±0.05` band). This follow-up asks
why that realized miss occurred.

## Current frame and competing explanations

The in-expectation corollary says that a random reassignment of a fixed
concern-weight multiset gives every deployment position the same marginal
weight, so each candidate's expected misspecified score is proportional to
its unweighted extension mass. That score identity does not by itself commute
through `argmax`: finite candidate pools, ties, and selection can produce a
nonzero expected *selected-performance* gap.

- **V (random-assignment/selection variance):** the observed aggregate gap is
  typical when the original 96 candidate pools and true deployments are held
  fixed and only misspecified assignments are independently redrawn.
- **A (systematic anti-correlation):** the observed aggregate gap is too far
  into the lower tail of that conditional randomization distribution to be
  explained by random assignment plus selector nonlinearity.

## Frozen design

- Reconstruct the committed E1 structure exactly: moduli `{7, 11, 13}`, seeds
  `0..31`, `focus_fraction=0.25`, `focus_weight=10`,
  `n_candidates=300`, `train_window_frac=0.5`, and truth excluded.
- Freeze each cell's training/OOD split, well-specified deployment, candidate
  order, candidate correctness masks, unweighted pick, and evaluation
  accuracy. Do not regenerate these objects between null replicates.
- Run **2,048** experiment-level null replicates. In every replicate and cell,
  assign exactly the cell's original number of high weights uniformly without
  replacement over its OOD positions. Use base seed `202607092136`; derive a
  collision-free SHA-256 namespaced seed from
  `(base_seed, replicate, modulus, structural_seed)`.
- The primary statistic is
  `Delta_r = mean_cells(acc(misspec_pick_r; C_star) -
  acc(unweighted_pick; C_star))`, matching the aggregation of the observed
  `-0.054159416947479166`.
- Commit aggregate replicate gaps and compact diagnostics; omit per-candidate
  bulk.

## Frozen analysis

Report the null mean and standard deviation, a normal 95% CI for the null
mean, quantiles `{0.5%, 2.5%, 5%, 50%, 95%, 97.5%, 99.5%}`, and the empirical
one-sided probability
`P(Delta <= -0.054159416947479166)` with a Wilson 95% interval. Also report
per-modulus summaries.

The assumption audit must verify:

1. candidate/deployment structure is invariant across null replicates;
2. every assignment has the frozen high-weight cardinality and all derived
   RNG seeds are unique;
3. assignment is independent of candidate coverage and `C_star` by
   construction (the RNG key contains no candidate outcomes);
4. position inclusion frequencies are exchangeable within sampling error
   (maximum absolute standardized inclusion deviation `<= 5`);
5. overlap with the true high-concern set matches the corresponding
   hypergeometric mean within `4` pooled standard errors;
6. absolute lag-1 autocorrelation of experiment-level gaps is `<= 0.10`.

Fixed-cardinality weights are exchangeable but not independent across
positions; this is intentional and matches the original marginal-preserving
control. The corollary requires equal coordinate marginals, not iid weights.

## Gate and kill criteria

The assumption audit must pass before interpretation.

- If `P(Delta <= observed) >= 0.025`, verdict **CONSISTENT_WITH_RANDOM_ASSIGNMENT_VARIANCE**.
- If `P(Delta <= observed) < 0.025`, verdict
  **SYSTEMATIC_ANTICORRELATION_INDICATED**; this kills explanation V for the
  frozen E1 structures.
- If any assumption check fails, verdict **INCONCLUSIVE_ASSUMPTIONS_FAILED**.

This follow-up cannot retroactively pass the original frozen `±0.05` gate. It
only calibrates whether that failed realization is surprising under the
stated random-assignment mechanism.
