# DCR3b — Counterfactual Dependence Scoring

**Package:** `experiments/date_cut_retrodiction/`
**Predecessor:** DCR3 (NO_GO — corpus-frequency scoring puts T1 rank 3)
**Date:** 2026-07-27
**Written:** BEFORE `nominate_dcr3b.py` is drafted or scored, BEFORE
subagent counterfactual-scoring calls are spawned.

## 0. The reframe under test

DCR3 failed because corpus-frequency scoring measures textual
load-bearing (T2 wins) rather than counterfactual dependence (T1
should win). The human director's reframe: the object lives in the
**intervention algebra** rather than the representation. DCR3b is the
direct empirical test of that reframe on the DCR corpus.

Replace DCR3's `degree(p)` with `counterfactual_dependence(p)`,
LLM-scored: for each proposition p at a cut, how many other propositions
in the same cut would become underdetermined or false if p were false?
Keep everything else identical to DCR3 (target_v4 classification,
multidoc aggregation, random-null baseline).

## 1. Setup

- **Corpus:** DCR1e consensus at each cut (unchanged from DCR3).
- **Class assignment:** `target_v4` (unchanged).
- **Aggregation:** `multidoc(min_docs=2)` (unchanged).
- **Scoring function:** `score(p) = counterfactual_weight(p)`, no
  kind-weight multiplier (DCR3's kind-weight was DR-arc precedent;
  DCR3b tests a different hypothesis and drops it).
- **Counterfactual weight measurement:** three sandboxed Claude
  subagents per cut. Each subagent receives the full set of
  propositions at the cut and returns a per-proposition integer
  0-10 for "how many other propositions at this cut would become
  false or underdetermined if this one were false." Consensus =
  median across the three.
- **Ground truth:** T1 class (unchanged).
- **Baseline:** 10,000 random-null permutations (same seed).

The counterfactual scoring prompt is **committed before subagent
calls are spawned** in `DCR3B_PROMPT.md`, and its SHA-256 is pinned
in the runner.

## 2. Gates

Same M-gate structure as DCR3:

- **M1** — T1 class ranks first at 1904 under counterfactual scoring.
- **M2** — T1 class not first at 1880 (placebo).
- **M3** — M1 result beats random null at p < 0.01.
- **M4** — scoring prompt SHA-256 committed and pinned.

Overall **GO** iff all four M-gates GO.

## 3. Decision table

| M1 | M2 | M3 | reading |
|---|---|---|---|
| GO | GO | GO | **Intervention-algebra reframe wins.** Counterfactual scoring identifies T1 first where corpus-frequency scoring identified T2 first. Direct empirical support for "the object lives in the intervention algebra, not the corpus statistics." Extends DR-arc program under new scoring primitive. |
| NO_GO (T1 still not first) | any | any | **Reframe fails the same test that killed DCR3.** LLM-based counterfactual scoring does not reach T1 either. Combined with DCR3, the loud/silent asymmetry is robust to changing the primitive. |
| GO | NO_GO | any | **Counterfactual scoring leaks at the placebo.** T1 ranks first at 1880 too, meaning the LLM subagent is projecting T1 as generically important rather than tracking corpus-specific dependence. |
| GO | GO | NO_GO | **Chance ranking.** Report as null. |

## 4. What DCR3b does not test

- Whether counterfactual dependence is the "correct" primitive in some
  general sense. DCR3b tests a specific operationalisation via LLM
  scoring on the DCR corpus.
- Whether the intervention-algebra reframe generalises to other
  domains (e.g., Constraint Swap). That is tested separately.

## 5. Single-shot

One prompt design, one round of subagent calls per cut, one scoring
pass, one verdict. No replay. If M1 fails, **do not reword the prompt
to raise T1's rank.** Report the NO_GO honestly.
