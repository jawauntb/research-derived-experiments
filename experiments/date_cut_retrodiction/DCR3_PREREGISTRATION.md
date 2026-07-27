# DCR3 — Does the DR Nominator Rank Einstein's Deletion on the Real Corpus?

**Package:** `experiments/date_cut_retrodiction/`
**Predecessor:** DCR2b (multidoc aggregation rule works — placebo clean, one-position gain at target)
**Human director:** Jawaun Brown
**Date:** 2026-07-27
**Written:** BEFORE `nominate_dcr3.py` is drafted or scored.

## 0. The load-bearing DR-arc question

DR1–DR4 built the deletion-repair nominator on toy problems. DCR1–DCR2b
built the extraction, matching, and class-aggregation pipeline on a real
pre-1905 electrodynamics corpus with ground truth attached (Einstein's
1905 deletion → the T1 class).

**DCR3 is the original question the whole arc was built to answer:** does
an execution-free scoring function, given only propositions extracted
from pre-1905 material, rank the T1 (absolute simultaneity) class
*first* at the 1904 target cut and *not-first* at the 1880 deep placebo
cut, at a level that beats a random null at p < 0.01?

The answer decides two things simultaneously:

- **GO:** the DR-arc program is empirically validated on a real
  conceptual-change case with ground truth. This would be, to my
  knowledge, the first algorithmic hit on such a case.
- **NO_GO:** the DR-arc as designed cannot solve its own load-bearing
  question on real material. Combined with DR5/DR7, this converts an
  empirical wall into a structural falsification of the algorithmic
  program.

Both outcomes are worth having.

## 1. Setup

- **Corpus:** DCR1e consensus propositions at each cut (1880, 1897,
  1904). Byte-identical to DCR1e's published output.
- **Class assignment:** `target_v4` from DCR1f (unchanged).
- **Aggregation rule:** `multidoc(min_docs=2)` from DCR2b (unchanged).
- **Scoring function** (the DR3 novelty): execution-free
  `nominate_dcr3`. Score each proposition by an execution-free
  quantity meant to capture "how load-bearing is this commitment for
  the framework's arguments" — computed only from the proposition
  itself and the corpus at the cut, with no access to Einstein's 1905
  paper or any post-cut material.
- **Ground truth:** the T1 class, per DCR1c/d/e/f/2a/2b analysis.
- **Baseline:** 10,000 random rankings of the class set at each cut
  (permutation baseline; each permutation is a uniformly random
  ordering of the class keys).

## 2. The scoring function

Per-proposition scoring rule, execution-free (deliberately simple; the
DR-arc's DR1–DR4 nominators used similar per-proposition scores):

```
score(p) = kind_weight(p) * degree(p)
```

where

- `kind_weight(p)` = 3 if `p.kind == "required_by_argument"`, 2 if
  `"presupposed"`, 1 if `"asserted"`. Rationale: DR-arc's precedent —
  the deletion-repair framework specifically nominates
  presuppositional / argument-required commitments over asserted
  ones.
- `degree(p)` = number of documents in the cut that USE the same content
  as `p` — computed by content-stem Jaccard ≥ 0.5 over the cut's other
  propositions (identical to `consensus.py`'s equivalence rule). This
  captures how widely the proposition is shared across the corpus at
  the cut, without any post-cut information.

Class-level score = sum of member scores (with multidoc gating: score = 0
if class covers fewer than 2 documents).

**No tuning.** The kind-weights are ordinal (3 > 2 > 1) and reflect the
DR-arc's stated preference for presupposition-flavored commitments.
`degree` is defined identically to the DCR1c consensus equivalence rule.
No parameters chosen with knowledge of the outcome.

## 3. Gates

Four preregistered non-compensatory gates:

- **M1** — **T1 class ranks first at 1904 (target cut).** The class with
  the highest multidoc-weighted score at 1904 is `T1_absolute_simultaneity`.
- **M2** — **T1 class is not ranked first at 1880 (deep placebo cut).**
  The 1880 ranking under the same rule does not put T1 first.
- **M3** — **The M1 result beats random null at p < 0.01.** Under 10,000
  random permutations of the class keys, T1 lands at position 1 with
  frequency < 0.01. (Baseline probability under uniform random = 1/N
  where N = number of classes at 1904, so if 4 classes then p = 0.25;
  we need the actual scored ranking to be substantially better than
  chance.)
- **M4** — **The scoring function is not tuned to the outcome.** The
  paper commits to reporting the scoring function unchanged in the
  runner, and to a regression test that pins the kind_weight tuple and
  the degree definition byte-for-byte.

Overall **GO** = all four M-gates GO. Any single NO_GO is a real result.

## 4. Decision table

| M1 | M2 | M3 | verdict | licenses |
|---|---|---|---|---|
| GO | GO | GO | **DR-arc program empirically validated.** Execution-free nominator ranks Einstein's actual deletion first on real pre-1905 material with ground truth, beating random at p < 0.01. | Extension to other corpora (Copernicus, Darwin, Lavoisier — each with known deletions), and publication as an AI-for-science result. |
| GO | NO_GO | any | **Nominator fires at target AND placebo — leakage.** T1 ranks first at 1880 too, meaning the nominator is picking up something about the corpus structure rather than the specific commitment. | Trace the leak; likely an artifact of the degree computation or class-aggregation. |
| **NO_GO** | any | any | **DR-arc as designed does not solve its load-bearing question.** Consistent with DR5/DR7 predictions on multi-realisation targets. | Clean structural falsification; the program has to redesign the scoring primitive, not tune it. |
| GO | GO | **NO_GO** | **Ranking not statistically distinguishable from random.** M1's "T1 first" was a chance outcome. | Report as null; run with more classes or richer scoring before concluding. |

## 5. Single-shot commitment

One nominator, one scoring pass at each of three cuts, one random-null
permutation test, one verdict. No replay knobs.

If the verdict is NO_GO, **do not tune the scoring function to raise T1's
rank.** That would collapse the load-bearing DR-arc question into a
fitting exercise. Report the NO_GO honestly and let DR5/DR7 explain it.
