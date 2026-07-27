# DCR2b — Multi-Document Coverage Aggregation Rule

**Package:** `experiments/date_cut_retrodiction/`
**Predecessor:** DCR2a (class-scoring NO_GO on N4: T1 class ranked 2 at 1880 placebo due to a single misfiring Maxwell hit)
**Date:** 2026-07-27
**Written:** BEFORE `nominate_by_multidoc.py` is drafted or scored.

## 0. Question

DCR2a's three aggregation rules (`cardinality`, `coverage`, `spread`)
all put the T1 class at rank 2 at the 1880 deep placebo cut. The
runner's licensed reading was:

> class_scoring_fails_placebo: T1 outranks other classes at 1880 under
> some rule, meaning cardinality-1 hits inflate the class rank.
> Aggregation rule must require multi-document coverage.

DCR2b implements exactly that repair as a new aggregation rule and
tests whether N4 (T1 silent at placebo) now passes.

## 1. Setup

- `nominate_by_multidoc.py` — new scoring rule `multidoc(min_docs=2)`:
  a class is eligible for ranking only if it has members from at least
  2 distinct documents. Singleton-document classes are demoted to a
  score of 0 regardless of member count.
- `run_dcr2b.py` — reuses DCR2a's classification (target_v4) and
  proposition-blind baseline. Adds the new rule as a fourth aggregation
  option alongside `cardinality`, `coverage`, `spread`.
- No edits to `nominate_by_class.py` or any prior module.

## 2. Gates

The full N-suite from DCR2a, re-scored under the new rule:

- **N1** class assignment complete (unchanged; sanity)
- **N2** T1 class ≥ 5 members at 1904 (unchanged)
- **N3** class rank at 1904 (under `multidoc`) beats proposition-blind rank
- **N4** T1 class silent at 1880 (**the load-bearing repair test**):
  under `multidoc`, T1 at 1880 must rank ≥ 3 or be de-ranked entirely
- **N5** comparison table produced (structural)

Plus one new gate:

- **N6** — `multidoc` correctly demotes ONLY singleton-document classes.
  At 1904, T1 has coverage across ≥ 2 documents (7 hits from 5
  documents per DCR2a), so `multidoc` should NOT demote T1 at 1904.
  Verify T1's 1904 rank under `multidoc` is unchanged from `spread`.

Overall GO = all six N-gates GO.

## 3. Decision table

| N4 | N6 | reading |
|---|---|---|
| GO | GO | **multidoc fixes DCR2a's placebo failure without breaking DCR2a's positive result.** DCR2 can proceed with `multidoc` as the aggregation rule. |
| GO | NO_GO | multidoc demoted T1 at 1904 too — the rule is too restrictive |
| NO_GO | any | multidoc still ranks T1 highly at 1880 — the placebo issue is deeper than singleton-cardinality |

## 4. Single-shot

One implementation, one run over the DCR1e consensus, one verdict.
`multidoc` uses a fixed `min_docs=2`. No sweep, no replay.

If N4 fails, the failure is a real finding about the placebo: even
requiring 2-document coverage doesn't demote T1 at 1880, which would
mean the placebo assumption (1880 T1 = leak) is structurally wrong and
DCR1c's placebo test was never valid for T1.
