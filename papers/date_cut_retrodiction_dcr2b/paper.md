# DCR2b: The Multi-Document Coverage Rule Fixes DCR2a's Placebo Failure

**Human director:** Jawaun Brown
**Producing agent:** Claude Code, directed
**Program:** Date-Cut Retrodiction — DCR2b (aggregation-rule repair)
**Status:** Overall **GO**. All six N-gates pass. Multidoc scoring de-ranks T1 at the 1880 deep placebo (single Maxwell hit → score 0) while preserving T1 at the 1904 target cut (5-document coverage). Class-based nomination on the DCR arc now has a placebo-clean scoring rule.
**Date:** 2026-07-27

---

## Abstract

DCR2a found that cardinality-based class scoring put the T1 class at
rank 2 at the 1880 deep placebo cut, because a single Maxwell 1865 hit
inflated a low-cardinality class. Its licensed reading explicitly
named the repair: *"aggregation rule must require multi-document
coverage."* DCR2b applies exactly that repair — the `multidoc` rule
de-ranks any class whose members come from fewer than a preregistered
threshold of distinct documents (`min_docs = 2`).

**Result: all six N-gates pass, overall GO.** T1 at 1904 keeps its
rank-3 position (with 5-document coverage under target_v4). T1 at 1880
scores 0 (correctly de-ranked). N3 GO: rank-3 beats proposition-blind
rank-4 (same one-position gain DCR2a reported). N4 GO: T1 at 1880 is
excluded from meaningful ranking. N6 GO: T1 at 1904 is not
over-demoted.

Licensed reading: *"multidoc_fixes_placebo_failure: DCR2a's N4 defect
is resolved. DCR2 pipeline can adopt multidoc as the aggregation
rule."*

DCR2b's contribution is small — a single-rule repair on a corpus of
existing results — but the loop it closes is load-bearing. DCR2a
opened the specific question *"can any class-scoring rule survive both
the target-cut and the placebo?"* and named the fix in advance. DCR2b
implements exactly the named fix and reports the outcome.

---

## 1. What was preregistered

`DCR2B_PREREGISTRATION.md` (2026-07-27, before `nominate_by_multidoc.py`
was drafted or `run_dcr2b.py` executed):

- One aggregation rule: `multidoc(min_docs=2)`. Score = class
  cardinality when the class covers at least 2 distinct documents;
  score = 0 otherwise.
- Reuse of DCR2a's classification (`target_v4`) and proposition-blind
  baseline (word-count scoring). No edits to `nominate_by_class.py` or
  any prior module.
- The full N-suite from DCR2a, plus one new gate:
  - **N4** (T1 silent at 1880) — must rank ≥ 3 **or** be de-ranked
    entirely (score 0). Preregistration explicitly allows either.
  - **N6** — multidoc must NOT demote T1 at 1904. Guards against a
    rule that is too restrictive.
- Single-shot commitment: no replay knobs, no sweep over `min_docs`.

## 2. Results

**Per-cut summary under `multidoc(min_docs=2)`:**

| cut | class | members | documents | multidoc score | rank |
|---|---|---:|---:|---:|---:|
| 1880 (placebo) | unclassified | 50 | 3 | 50 | 1 |
| 1880 | T1_absolute_simultaneity | 1 | 1 | **0** | (de-ranked) |
| 1880 | T2_privileged_frame | 0 | 0 | 0 | (empty) |
| 1880 | T3_local_time_artifice | 0 | 0 | 0 | (empty) |
| **1904 (target)** | **unclassified** | **235** | **15** | **235** | **1** |
| **1904** | **T2_privileged_frame** | **11** | **8** | **11** | **2** |
| **1904** | **T1_absolute_simultaneity** | **7** | **5** | **7** | **3** |
| **1904** | **T3_local_time_artifice** | **2** | **2** | **2** | **4** |

**Proposition-blind baseline at 1904:** best T1 realisation at rank 4
(same as DCR2a).

## 3. Gate decisions

| gate | | |
|---|---|---|
| N1 class assignment complete | GO | 235 / 254 unclassified at 1904 (< 95%) |
| N2 T1 class non-empty at 1904 | GO | 7 members ≥ 5 |
| N3 multidoc beats proposition-blind | GO | rank 3 vs 4 (one-position gain, same as DCR2a) |
| N4 T1 de-ranked at 1880 | **GO** | multidoc score 0 (singleton document) |
| N5 comparison table produced | GO | this section |
| N6 T1 at 1904 not over-demoted | GO | coverage 5 ≥ 2 |

**Overall GO.**

## 4. What the result says

The DCR2a defect was that cardinality-based scoring gave any nonempty
class a strictly positive score, so a class with a single misfiring
member could still outrank empty or near-empty classes at the placebo
cut. The `multidoc` rule exchanges cardinality-of-members for
cardinality-of-documents: score is cardinality only if the class covers
at least `min_docs = 2` distinct documents, otherwise zero. Two
consequences:

- **At the placebo cut (1880)**, the T1 class has one member from one
  document (Maxwell 1865). Multidoc gives it a score of 0. It is
  correctly excluded from meaningful ranking.
- **At the target cut (1904)**, the T1 class has 7 members from 5
  distinct documents. Multidoc gives it a score of 7. It ranks 3, one
  position higher than the best proposition-blind T1 realisation ranks.

The rank-2 position T1 receives at 1880 in the raw output is an
alphabetical tiebreak among 0-score classes (T1 < T2 < T3), not a
substantive ranking. Under any principled tiebreak or under the natural
"exclude 0-score classes" reading, T1 is not ahead of anything at
1880.

## 5. What DCR2b establishes and does not establish

**Establishes:**

- The DCR2a-preregistered repair works exactly as anticipated. The
  T1 class is placebo-clean under multidoc without losing its
  positive result at the target cut.
- Class-based nomination on the DCR arc has, for the first time in
  the DCR series, a scoring rule that satisfies all six N-gates
  simultaneously.

**Does not establish:**

- **Whether class-based nomination solves the DR5 wall on this
  corpus.** DR7 showed the wall relocates from N to g; multidoc is
  a rule on top of an already-imported g (= target_v4). DR7's
  soundness-completeness gap on open realisation sets is not
  addressed by any aggregation rule.
- **Whether DCR2 (the full deletion-repair nomination pipeline) can
  now be run.** DCR2b tested only the class-scoring layer, not the
  DR1–DR4 nominator pipeline. DCR2 remains open.
- **Whether the rule generalises to targets without natural
  multi-document coverage.** Some legitimate targets in some corpora
  may have single-document realisations (e.g., a unique canonical
  statement of a mathematical convention appearing in exactly one
  paper). Multidoc would incorrectly de-rank them. For the DCR corpus,
  where T1 realisations are distributed across the electrodynamics
  literature by design, the rule fits.

## 6. Next work

- **DCR2c** — the presupposition-inferring extractor used as $g$
  directly, rather than as an intermediate step feeding target_v4.
  Would test whether a semantic-classifier grouping function catches
  T1 realisations target_v4 misses.
- **DCR3** — run the DR-arc deletion-repair nominator over the DCR1e
  consensus with multidoc as the aggregation rule, and score against
  ground truth (Einstein's 1905 deletion). This is DCR2's original
  question, now with the aggregation rule fixed.

Both are DCR-arc extensions. Neither is required to close DCR2b's
loop; both are natural follow-ups DCR2b's GO opens.

---

## Appendix: reproduction

```
uv run --no-sync python -m experiments.date_cut_retrodiction.run_dcr2b
```

Reads the DCR1e presupposition-extraction consensus, applies
`nominate_by_multidoc.score_multidoc` at each of the three DCR cuts,
compares to the proposition-blind baseline, writes
`results/dcr2b_verdict.json`. Local CPU, milliseconds.

**Preregistration digest (SHA-256 of `DCR2B_PREREGISTRATION.md`):**
`547b5164361b648928b1aafcd09556e6468bc6224c9ba26eb22163304a886a78`.
