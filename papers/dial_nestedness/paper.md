# The dial's optimal rate falls; its cells need not nest

**Jawaun Brown** (human director) and **Claude Fable 5** (agent, under review)
**Date:** August 18, 2026
**Status:** Review item 2 on the intention essay is **settled at this
bound**. Verdict `nestedness_fails_generally`, with the nuance that a
chosen chain still nests. Not Paper G.

## Current frame

Theorem B of "Intention Is All You Need" trades description length
against task-relevant information. Its v3 prose said "as D grows the
cells coarsen" — implying the optima form a nested chain along the
budget. The reviewer flagged it: rate-distortion guarantees the rate
falls, not that the partitions nest. The corrections ledger withdrew
the wording; this instrument measures what is actually true.

## Severe experiment

Package: `experiments/dial_nestedness/`. Five worlds with task law
(0, ¼, ½, ¾, 1), worst-case within-cell law gap as the task-relative
distortion, rate = cell count, all 52 partitions enumerated, budgets
(0, ¼, ½, ¾, 1). Predictions registered before evaluation.

| Budget | Optimal rate | Optimizers |
|---|---|---|
| 0 | 5 | the level partition, uniquely |
| ¼ | 3 | adjacent-pair coverings |
| ½ | 2 | e.g. {012}{34} |
| ¾ | 2 | e.g. {0123}{4}, {012}{34} |
| 1 | 1 | the single cell |

Three facts, separated:

1. **The rate falls** (5, 3, 2, 2, 1) — general and safe: feasible
   sets nest, so the minimum can only drop. This is the only slogan
   the essay's rewrite exports.
2. **All-optimizer nesting fails**: the ¼-optimizer {01}{23}{4} does
   not refine the ½-optimizer {012}{34} — the cell {23} crosses the
   boundary. "The cells coarsen" is false as a claim about optimizer
   sets, exactly as the reviewer said.
3. **A chosen chain nests**: singletons → {0}{12}{34} → {012}{34} →
   {012}{34} → {01234}. Whether "the cells coarsen" along *your*
   dial depends on which optimizer you pick at each budget — nesting
   is a selection fact, and selection needs a disclosed rule. That is
   the third appearance of the same lesson in this program: κ_screen
   needed its total order, D13 needed its completion order, and the
   dial needs its chain choice.

## Claim boundary

**Supported.** On this registered world: the rate vector, the unique
D = 0 optimum (agreeing with the kernel-checked `DialZero.lean`), the
nesting failure with witness, and the existing chain.

**Not supported.** Any continuous or average-case rate-distortion
claim. A rescue of the withdrawn wording. Any claim beyond the
registered world and distortion.

**What would change the conclusion.** Nothing here is fragile: the
enumeration is exhaustive and exact. A different distortion (expected
rather than worst-case) is a different instrument, not a correction.

## Lean status

The D = 0 clause is kernel-checked and SafeVerify-passed
(`DialZero.lean`, `docs/lea/VERIFY_RECEIPT_2026-08-18.md`). The
positive-budget rows are this instrument's exact enumeration; they
are labeled python-enumerated and are finite-decidable if a later
wave wants them in the kernel.

## Provenance

`python3 experiments/dial_nestedness/experiment.py`;
`python3 -m unittest tests.test_dial_nestedness`. Human director:
Jawaun Brown. Agent: Claude Fable 5, session
`4adbd42d-0e99-41df-b0be-7d9d5b7e3caa`, under review.
