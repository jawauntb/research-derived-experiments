# DCR2a — Nominate by Class, Not by Proposition

**Package:** `experiments/date_cut_retrodiction/` (nomination extension)
**Predecessor:** DCR1f (NO_GO, T1 is a spectrum of realisations)
**Human director:** Jawaun Brown
**Date:** 2026-07-27
**Written:** BEFORE `nominate_by_class.py` is drafted or `run_dcr2a.py` is executed.

## 0. The specific question DCR2a can answer

DCR1f established that T1 (absolute simultaneity) is not a discrete
proposition to look for — it is a class of realisations. Proposition-ranking
matchers (target_v3, target_v4) each fit one register at the expense of
others. The DR5 theorem paper (parallel run) formalises the structural
limit: a proposition-ranking nominator cannot distinguish a commitment D
from any specific realisation r_i.

DCR2a is the empirical companion to that theorem: **does class-based
scoring surface T1 in a way proposition-based scoring cannot?**

If class-based scoring puts T1 in a top-3 rank on the DCR1e consensus,
then class-aware nomination is a strictly better instrument for
multi-realisation commitments. If T1 falls below other classes even under
class-based scoring, then either (i) T1 really is subordinate to other
commitments in this corpus (an interesting historical claim), or (ii)
class-based scoring alone is insufficient and further structure is needed.

## 1. What is added

- `nominate_by_class.py` — a class-based scoring rule. Given the DCR1e
  consensus and target_v4's class assignment, computes a class score
  under three aggregation rules:
  - **cardinality**: `|C|`
  - **coverage**: `|{documents contributing to C}|`
  - **spread**: `|C| × |{documents contributing to C}|` (rewards classes
    that are both frequent and cross-document)
- `run_dcr2a.py` — scores each class per rule, ranks, and produces a
  comparison table against proposition-blind scoring (rank each
  proposition by the same underlying score and report where T1
  realisations fall individually).

## 2. Gates

Five gates, all must decide GO for the overall verdict to be GO.

- **N1 class assignment complete.** Every proposition in the DCR1e 1904
  consensus receives a class assignment (T1, T2, T3, or "unclassified").
  Rejection of "unclassified" > 90% would indicate the class scheme is too
  narrow — a sanity check.
- **N2 T1 class non-empty at 1904.** target_v4's T1 class contains at
  least 5 propositions at the 1904 cut (matches DCR1f's observed 7,
  discounted slightly for robustness).
- **N3 T1 class rank higher than any single T1 realisation would get
  proposition-blind.** Under proposition-blind ranking, the highest-scored
  T1 realisation appears at some position P_prop. Under class-based
  ranking, T1 as a class appears at position P_class. **DCR2a requires
  P_class < P_prop (lower rank = higher position).** This is the
  load-bearing gate.
- **N4 placebo T1 class silent at 1880.** Under target_v4 the 1880 cut
  had one T1 hit (Maxwell's "instant across whole medium"). N4 asks
  whether the class-based ranking demotes T1 to a low rank at 1880 (T1
  ranks below rank-2 among all classes). A single hit should not
  dominate class scoring; if it does, class-based ranking is
  cardinality-dominated and the aggregation rule needs adjustment.
- **N5 comparison table produced.** The verdict artifact contains a
  side-by-side of class-rank(T1, T2, T3) vs proposition-rank(highest
  member of T1, T2, T3) at each cut, so any reader can verify the
  claim.

**Overall GO** requires all five. A GO licenses the specific claim
*"class-based scoring surfaces T1 in a way proposition-based scoring
does not on this corpus."* It does **not** license DCR2 (the full
deletion-repair nomination pipeline). That is a separate question.

## 3. Decision table

| N1 | N2 | N3 | N4 | N5 | verdict | licenses |
|---|---|---|---|---|---|---|
| GO | GO | GO | GO | GO | **DR5 empirical companion confirmed on this corpus.** Class-based scoring solves what proposition-based cannot. | A follow-up experiment applying class-based scoring to the DR-arc's deletion-repair nominator. |
| GO | GO | NO_GO | any | GO | **Class-based scoring does not surface T1 above proposition-based baseline.** T1 is subordinate to other classes in this corpus even at the class level, or the aggregation rule was wrong. | Diagnostic re-run with a different aggregation rule; report which. |
| GO | GO | GO | NO_GO | GO | **Placebo failed under class-based scoring too.** Cardinality dominates; a single Maxwell hit inflates the T1 class rank at 1880. | Redraft the aggregation rule to require at least 2 distinct documents per class. |
| any | NO_GO | any | any | any | **T1 class too small.** target_v4 hits at 1904 dropped below the preregistered threshold. | Not a class-scoring failure — an extractor/matcher regression. Investigate. |
| any | any | any | any | NO_GO | **No comparison table.** Verdict is uninterpretable. | Fix reporter and re-run. |

## 4. What DCR2a does not test

- Whether the DR-arc's full deletion-repair nominator (DR1-DR4 style)
  works under class scoring.
- Whether the T1 class corresponds to any specific commitment Einstein
  deleted. DCR2a only asks whether class-based ranking makes T1 visible
  where proposition-based ranking makes it invisible; the historical
  correspondence to Einstein's deletion is a separate question DCR1c/d
  argued for.
- Whether the DR5 theorem is correct. That is DR5's job. DCR2a is the
  empirical companion.

## 5. Single-shot commitment

One class assignment, one ranking under each of three aggregation rules,
one comparison table, one verdict. No replay knobs. If N3 fails, the
right response is either to redraft the aggregation rule (and re-run once)
or to report N3 NO_GO honestly.

The three aggregation rules are reported **in parallel**. The paper does
not pick a "winner" based on which one supports the desired conclusion;
it reports all three and lets the comparison stand on its own.
