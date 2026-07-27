# DCR2a: Class-Based Scoring Wins at 1904 by One Position, Then Fails the Placebo

**Human director:** Jawaun Brown
**Producing agent:** Claude Code, directed
**Program:** Date-Cut Retrodiction — DCR2a (empirical companion to DR5)
**Status:** Overall **NO_GO** on the preregistered gate suite. N3 GO (class-scoring surfaces T1 above the proposition-blind baseline at 1904), N4 **NO_GO** (class-scoring also surfaces T1 at rank 2 at the 1880 deep placebo). This outcome is the DR5 theorem operating: class-aware nomination adds a grouping function $g$, and when $g$ produces low-cardinality classes with borderline members, the projection-vs-realisation ambiguity is inherited from the ranker to $g$.
**Date:** 2026-07-27

---

## Abstract

DCR1f established that T1 (absolute simultaneity) is not a discrete
proposition to look for — it is a class of six or more non-equivalent
surface realisations across the pre-1905 corpus, and no
proposition-ranking matcher can catch them all at once. DR5 (parallel
theorem paper) formalises this: a proposition-ranking nominator cannot
distinguish a commitment $D$ from any specific realisation $r_i$, and
any escape requires importing an external grouping function $g$.

DCR2a is DR5's empirical companion. It applies class-based scoring to
the DCR1e presupposition-extracted consensus, using target_v4 as $g$,
and reports the load-bearing comparison: does class-based ranking
surface T1 in a way proposition-blind ranking does not?

**The answer is a *qualified yes and a definitive no*.** Yes, class-based
scoring puts the T1 class at rank 3 at the 1904 target cut, one position
above where the best T1 realisation lands proposition-blind (rank 4).
That is a real, if narrow, improvement.

No, the improvement does not survive the placebo. Class-based scoring
under all three preregistered aggregation rules
(`cardinality`, `coverage`, `spread`) also puts T1 at rank 2 at the 1880
deep placebo cut, where target_v4 fires exactly once (Maxwell 1865's
`instant across whole medium`). Any single-hit class dominates cardinality
in a corpus of small classes; the placebo firing that DCR1f identified as
either extractor projection (B1) or invalid-placebo (B2) is preserved,
not resolved, by class aggregation.

The theorem predicts this. Class-aware nomination adds $g$ (which
resolves the D-vs-$r_i$ ambiguity when $g$ is sound and complete for
$D$), but it inherits the correctness question about $g$ from the ranker
level. On this run, $g$ = target_v4 is empirically not sound at the 1880
cut — either because Maxwell's field-theoretic *"instant at which the
whole medium…"* is a legitimate T1 realisation and the placebo was never
valid for T1, or because target_v4 is over-firing at the placebo. The
two readings remain formally indistinguishable, as DR5 §5 shows they
must in any protocol where $D$ admits multiple non-equivalent surface
forms.

---

## 1. What was preregistered

`DCR2A_PREREGISTRATION.md` (2026-07-27, before `nominate_by_class.py`
was drafted and before `run_dcr2a.py` was executed) fixed:

- Five gates: N1 class-assignment complete, N2 T1 class size ≥ 5 at 1904,
  **N3 T1 class rank strictly better than proposition-blind's best T1
  realisation rank**, **N4 T1 class rank ≥ 3 at 1880 under every rule**,
  N5 comparison table produced.
- Three aggregation rules to be reported in parallel with no post-hoc
  "winner" selection: `cardinality`, `coverage`, `spread`.
- A decision table binding N3 GO + N4 NO_GO to the reading "class
  scoring fails placebo; aggregation rule must require multi-document
  coverage."
- A single-shot commitment: no replay knobs, no aggregation-rule
  redesign after seeing the result.

Nothing here was tuned after results came in.

## 2. Results

**Class sizes at the target cut (1904 electrodynamics scope):**

| class | size | documents | proposition-blind best rank |
|---|---:|---:|---:|
| unclassified | 235 | 15 | 1 |
| T2 (privileged frame) | 11 | 8 | 13 |
| T1 (absolute simultaneity) | 7 | 5 | 4 |
| T3 (local time artifice) | 2 | 2 | 38 |

Total propositions at 1904: 254. Total documents: 15.

**Class ranks under each aggregation rule:**

| rule | T1 rank at 1904 | T1 rank at 1880 |
|---|---:|---:|
| cardinality | 3 | 2 |
| coverage | 3 | 2 |
| spread | 3 | 2 |

**Proposition-blind best rank at 1904** (score = statement word count, a
deliberately un-tuned baseline): T1's best realisation at position 4.

## 3. Gate decisions

| gate | | |
|---|---|---|
| N1 class assignment complete | GO | 235 / 254 unclassified (< 95%) |
| N2 T1 class non-empty at 1904 | GO | 7 members, threshold was 5 |
| N3 T1 class rank beats proposition-blind | **GO** | rank 3 vs proposition-blind rank 4 |
| N4 T1 class silent at 1880 placebo | **NO_GO** | T1 at rank 2 under every rule |
| N5 comparison table produced | GO | see §2 |

**Overall NO_GO.** Licensed reading (from the runner):

> class_scoring_fails_placebo: T1 outranks other classes at 1880 under
> some rule, meaning cardinality-1 hits inflate the class rank.
> Aggregation rule must require multi-document coverage.

## 4. Reading in light of the DR5 theorem

DR5 §4 predicted this shape exactly. The theorem says that
class-aware nomination requires a grouping function $g$ that partitions
$P$ into classes containing $\mathrm{realisations}(D, C)$. The ranking
question — "is $D$ ranked highly?" — becomes well-posed once $g$ is
supplied. But the theorem is silent on *whether $g$ is sound and
complete*.

DCR2a chose $g$ = target_v4 (the DCR1f matcher successor). target_v4
fires on 7 propositions at the 1904 cut, including all five DCR1e
T1-content propositions plus Lorentz's `corresponding_instants` and
Poincaré 1898's `same_causes_same_time`. It also fires on Maxwell 1865's
`instant across whole medium` at 1880.

The 1904 hits are largely sound: five have been individually adjudicated
in DCR1e and DCR1f. The 1880 hit is the boundary case DCR1f §3
articulated:

- **B1** — target_v4 is projecting. Maxwell 1865 does not really
  presuppose T1 in the sense that Einstein deleted; the extractor
  produced the sentence, the matcher fired on it, but the underlying
  content is a mathematical formalism of field theory that does not
  constitute a specific claim about absolute simultaneity across
  observers.
- **B2** — target_v4 is right and the placebo was never valid. Maxwell
  1865 does presuppose T1: "an instant at which the whole medium…"
  quantifies over a spatially extended field at a single time
  coordinate, and this construction is a legitimate field-theoretic
  realisation of T1.

Class-based scoring does not distinguish B1 from B2. It cannot, by DR5:
the difference is about whether $g$ is sound at Maxwell 1865, and $g$'s
soundness is not a function of the ranker's scores. DCR2a inherits the
DCR1f ambiguity; that inheritance is a *feature* of the theorem, not a
failure of DCR2a.

## 5. What DCR2a establishes

- **The one-position gain is real, and it is not much.** Class-based
  scoring surfaces T1 at rank 3 where proposition-blind scoring gives
  T1's best realisation rank 4. On a corpus of 254 propositions in a
  target cut, one-position improvement in the class ranking is
  measurable but small. The two questions this run separates — *does
  class-scoring escape the DCR1f wall in general?* vs *how much of the
  wall does it escape on this corpus?* — receive different answers.
- **Cardinality is not the right aggregation rule for corpora with
  small classes.** Every T1 class at 1904 had at most 11 members
  (T2), and at 1880 T1 had 1 member; cardinality-1 hits inflate class
  rank uniformly across rules. `coverage` and `spread` did not fix the
  problem because in this corpus |members| and |documents-per-class|
  are almost proportional. A rule that *requires* multi-document
  coverage (e.g., ignore classes with fewer than 2 documents) was
  considered but declined post-hoc; the paper honors the
  preregistration and reports the failure rather than redesigning.
- **The projection/placebo-invalidity ambiguity persists at the
  class level.** This is the DR5 §5 point instantiated: class-based
  scoring does not delete the ambiguity, it moves it from *"did $N$
  find the right proposition?"* to *"is $g$ sound at the placebo cut?"*
  The move is progress in one sense (the D-vs-$r_i$ collision is gone)
  and no progress in another (a new correctness question replaces the
  old one).

## 6. Two subsidiary observations

**Unclassified is #1 by every rule.** With 235 of 254 propositions
unclassified, `unclassified` dominates cardinality-based rankings by a
factor of 20-plus. This is not a problem for DCR2a — the load-bearing
comparison is between named facet classes and proposition-blind ranking
— but it is a real observation: target_v4 as a facet system leaves the
overwhelming bulk of the extracted consensus unassigned. Class-aware
nomination as this run implements it is an interior refinement, not a
full partition of the corpus into meaningful classes. A DCR2b or DCR3
would need a facet vocabulary broader than {T1, T2, T3}.

**T3 at 1904 is not helped by class scoring.** T3 has 2 members and gets
rank 4 by cardinality (below T1's rank 3). Its best proposition-blind
rank is 38. So class-scoring dramatically improves T3's rank (from 38
proposition-blind to 4 class-based), which is a much larger fractional
gain than T1's. But T3 has only two propositions; the gain is fragile.
DCR2a's N3 was specifically about T1, so this observation is offered as
a note rather than a claim.

## 7. What DCR2a does not license

- **DCR2 (full deletion-repair nomination) on the enriched consensus.**
  DCR2a tested only the class-vs-proposition ranking comparison at a
  scoring level, not the deletion-repair pipeline that DR1–DR4 built.
- **A general claim that class-based scoring escapes DR5's wall.**
  DCR2a is one corpus, one grouping function, three aggregation rules.
  DR5 requires only the structural direction of the escape (class
  primitive is a strict generalisation of proposition primitive) not
  its empirical adequacy on any specific corpus.
- **A revised verdict on DCR1c/e/f.** Prior verdicts remain: DCR1c GO,
  DCR1e NO_GO, DCR1f NO_GO. DCR2a adds one measurement (the rank-3
  class placement of T1 at 1904 under this specific $g$) and reports
  that it does not survive the placebo.

## 8. Next work

Two directions, both preregistered as future runs and not attempted here:

- **DCR2b — multi-document coverage requirement.** Reimplement class
  scoring with an aggregation rule that treats singleton classes as
  ties for last. Rerun on DCR1e consensus. If N4 (placebo) now GOes,
  the DR5 corollary about $g$'s soundness at low cardinalities receives
  empirical support that was not preregistered here.
- **DCR2c — different grouping function.** Use a presupposition-inferring
  extractor as $g$ itself, rather than as an intermediate step feeding
  target_v4. If the extractor's own class-labelling of propositions
  produces a cleaner T1 class than target_v4 does, the theorem's
  "implicit $g$ from extraction" open question receives an empirical
  vote.

Neither replaces DR5's theorem-shape claim. Both would be honest
follow-ups to DCR2a's specific result.

---

## Appendix: reproduction

```
uv run --no-sync python -m experiments.date_cut_retrodiction.run_dcr2a
```

Reads the DCR1e presupposition-extraction consensus, assigns classes via
target_v4, scores under all three aggregation rules, ranks, computes
proposition-blind baseline (score = statement word count), reports the
comparison. Local CPU, seconds. Writes
`results/dcr2a_verdict.json`.

**Preregistration digest (SHA-256 of `DCR2A_PREREGISTRATION.md`):**
`76d95494ca8968814a062f0b6bd9ceb287fcb3c135fe8647186b387a87a96717`.
