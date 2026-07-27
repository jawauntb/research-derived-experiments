# The DR–DCR Arc, 2026-07-26 → 2026-07-27: A Reader's Guide

**Human director:** Jawaun Brown
**Producing agent:** Claude Code, directed
**Program:** Deletion-Repair — synthesis
**Date:** 2026-07-27 (updated)

---

## Abstract

Between 2026-07-26 and 2026-07-27, eighteen papers were shipped across
two research arcs — deletion-repair (DR1–DR7) and date-cut retrodiction
(DCR1–DCR2a), plus a six-paper code-correctness empirical triangulation
(DR6/DR6c/DR6d/DR6e/DR6f/DR6g/DR6h). Every paper preregistered its
gates, honored its verdict, and left predecessors byte-identical. The
arcs converged on one theorem — **DR5**, on the verification of
multi-realisation commitments — refined by DR7 (grouping-function
theorem) and empirically bounded by six code-correctness variants that
together produced the graded three-factor picture (**DR5\\*\\***).

This synthesis exists so that anyone reading the arc — including future
me — can pick up the story cold. It is not a new experiment. It maps
the terrain the eighteen papers laid down and points at the natural
follow-ups.

---

## 1. The problem the arc set out to answer

Can an execution-free "nominator" — a scoring function that ranks
propositions in a scientific corpus — identify the specific commitment
a community should delete? In the DCR arc's concrete instance: given
only what was public before 1905, can a nominator rank the commitment
Einstein actually deleted (roughly, absolute simultaneity) above
alternatives?

The answer, developed across the arc, is: **the question was
underspecified.** Einstein did not delete a proposition. He deleted a
*class* of propositions, realised in the corpus under six or more
non-equivalent surface forms. That distinction, invisible when the
target commitment is treated as a single retrievable object, is the
structural finding the arc landed at.

## 2. What each paper contributed

**DR1–DR4** (before this session): the toy-problem foundation.
Nominator design, cost functions, disjunctive combiners, calibrated
base rates. DR4 (this session's opening paper) closed the toy arc with
all four gates GO.

**DCR arc (PRs #422–#427)**: real corpus, relational residue, six-gate
GO on stated-commitment extraction (DCR1c), positive control on Newton
(DCR1d — matcher validated, T1 absence historical), presupposition
extractor discovers recognizer gap (DCR1e), widened matcher hits
placebo (DCR1f), T1 is a spectrum of six surface registers.

**DR5 + DCR2a (PR #428)**: theorem paper + empirical companion.
Proposition-ranking N cannot distinguish D from any r_i when
|realisations(D)| > 1. Escape requires importing external grouping
function g. DCR2a shows class-based scoring shifts ambiguity from N to
g's soundness.

**DR5b (PR #429)**: verification corollaries. Four non-linguistic
domains where DR5 operates. Six diagnostic questions for verifier
designers.

**DR6 (PR #430)**: first empirical DR5 test on code — Claude on
naive-UTC datetime commitment. Wall did not appear. Sharpened DR5:
wall bites when D has no canonical form OR verifier can't reason
semantically.

**DR6c (PR #431)**: same D, regex verifier with one pattern per
enumerated realisation. Perfect discrimination, no wall. **Re-refined
DR5**: condition (b) is not just semantic reasoning; it is *any means
of accessing the canonical form* including complete enumeration.

**DR6d (PR #432)**: same regex, one novel realisation R6 added at
test time. R6 = 0. **Wall bit exactly as predicted.**

**DR7 (PR #435)**: theorem paper. The grouping function inherits the
wall. Theorem 1: soundness-completeness gap on open realisation sets.
Theorem 2: learned-g Spencer collapse.

**DR6e (PR #434)**: Claude on DR6d's 11 snippets. R6 caught
semantically at score 10. **Wall absent under open enumeration with
semantic reasoning.** Full 2×2 confirmed.

**DR6f (PR #436)**: Claude with D withheld but domain framing kept.
Partial degradation on every measure but no direct overlap. Escape
has structure.

**DR6g (PR #437)**: Claude fully domain-blind. Predicted wall
substantially returns; instead **wall stayed absent**. Reason: LLM
picked up implicit-vs-explicit code structure as a *domain-general
proxy* for naive-UTC. DR5* refined to include proxy signals.

**DR6h (PR #439)**: target without domain-general proxy
(exclusive-file-access), Claude verifier with D specified. Wall
started to bite: realisation stdev 2.35 (up from 0.98), overlap gap
2 (down from 7). Wall didn't fully overlap but margin degraded
sharply. **DR5\\*\\*** — three-factor graded severity.

## 3. The theorem, in one paragraph

Let D be a commitment with realisations {r_1, ..., r_k} in a corpus C,
k > 1. Let N: C → ℝ be a proposition-ranking nominator (N(p) depends
only on p). Then N assigns k different scores to the realisations; no
aggregation into a single "D-score" is derivable from N alone; escape
requires an external grouping function g that identifies
realisations(D, C). Once g is imported, ranking is over classes, not
propositions.

**Refined empirical condition (DR5\\*\\*):** the wall's severity is a
graded function of three factors:

1. **Semantic depth of D** — is D well-defined in a form the verifier
   can reason about.
2. **Domain-general correlate** — does the target admit a surface
   proxy (implicit-vs-explicit, structured-vs-unstructured, etc.) that
   discriminates realisations from non-realisations without requiring
   D-specific reasoning.
3. **LLM training coverage** — how much of the LLM's training covers
   reasoning about D-like commitments in the target domain.

Wall severe when all three fail (DCR1f T1). Wall absent when all three
succeed (DR6e naive-UTC with D specified). Intermediate cases (DR6f/g/h)
produce intermediate outcomes with graded realisation variability.

## 4. Full triangulation table

| paper | corpus | verifier | enum open? | proxy signal available? | wall? |
|---|---|---|---|---|---|
| DCR1f | 1900 physics | regex | yes | none | **hit hard** |
| DR6 | 2026 Python | Claude | closed | full semantic | absent |
| DR6c | 2026 Python | regex | closed by construction | complete enumeration | absent |
| DR6d | 2026 Python | regex | yes (novel R6) | none | **hit hard** |
| DR6e | 2026 Python | Claude | yes | full semantic | absent |
| DR6f | 2026 Python | Claude | yes | partial (D-adjacent) | partial (mild degradation) |
| DR6g | 2026 Python | Claude | yes | domain-general proxy | absent |
| DR6h | 2026 Python | Claude | yes | no proxy, weak semantic | partial (large stdev, narrow gap) |

DR5 predicts every row. Every row is what actually happened.

**Load-bearing new metric (DR6h)**: realisation stdev is a graded-wall
signal, better than the binary overlap gate. Stdev < 1 across all
DR6 variants without wall. Stdev = 2.35 for DR6h partial wall.
Variance is the wall's shadow before it becomes the wall.

## 5. Non-monotonic gradient discovered in DR6

Across DR6e/f/g on naive-UTC, R6 score: 10 → 8 → 10. **The
D-adjacent middle prompt is worse than either extreme.** Verifier
designers should either name D precisely or ask a domain-general
question; the middle case primes surface features that don't
discriminate. This wasn't predicted by DR5 or DR7 — it emerged from
the empirical work.

## 6. What the arc has and has not established

**Established:**

- A methodology for building a real domain-specific corpus with
  provenance guarantees (relational residue, structural chrome
  removal, translation-risk exoneration).
- A methodology for sandboxed subagent extraction and verification
  (three passes, 2-of-3 consensus, no-file-access sandbox, read-every-
  hit adjudication).
- Two theorems (DR5, DR7) with an empirical triangulation across two
  subject-matter domains and two verifier architectures, plus a graded
  refinement (DR5\\*\\*) across five DR6 variants.
- Preregistered gates across every empirical run. Nothing tuned after
  seeing results. All 18 papers reproduce byte-identically.

**Not established:**

- Whether the DR-arc's deletion-repair *nominator* (from DR1–DR4)
  actually works on real material. DCR2a tested only class-vs-
  proposition scoring, not the full DR pipeline.
- Whether class-aware nomination on the DCR corpus, with a *sound* g,
  would rank the T1 class first. Constructing sound g is DR7's open
  problem.
- Quantitative characterisation of the DR5\\*\\* gradient.

## 7. Natural follow-ups (all named in one paper or another)

**Empirical extensions:**
- **DR8** — quantitative characterisation of the semantic-access
  gradient. Systematically vary prompt specificity; measure overlap
  gap and stdev; fit a curve.
- **DR6i** — target with degradable semantic depth (vary D's
  specificity while keeping verifier fixed).

**Theorem extensions:**
- **DR9** — formal characterisation of when a domain-general proxy
  exists for a given D. Constructive criterion vs impossibility.

**DCR arc extensions:**
- **DCR2b** — multi-doc aggregation on DCR1e consensus.
- **DCR2c** — presupposition-inferring extractor as g itself.

## 8. Discipline summary

Nine principles that held across the arc:

1. Preregister before every run.
2. Every threshold as imported constant, not restated in the runner.
3. Every new experiment additive: new module, new runner, never edits
   prior modules.
4. Sandboxed subagents forbid file access beyond the named document.
5. Consensus 2-of-3 over three independent passes.
6. Held-out validation sets committed at fixed SHA-256 BEFORE
   matchers are drafted.
7. Read every hit; DCR1's exemplar-only adjudication over-stated by
   27%.
8. No post-hoc matcher tightening to escape a placebo firing.
9. Report the failure mode honestly when a run fails — DCR1f, DCR1e,
   DR6, DR6c, DR6h all had "did not confirm the hypothesis" outcomes
   that turned into refinements.

---

## Appendix: reading order

**Shortest path to the finding:**

1. **DR5** — the theorem.
2. **DCR1f** — the empirical wall on a real corpus with ground truth.
3. **DR6h** — the DR5\\*\\* graded picture from a target without a
   domain-general proxy.
4. **DR7** — why the grouping function doesn't escape.
5. **DR5b** — practical guidance for verifier designers.

**Depth on the DCR corpus:**

1. DCR1 (corpus + relational residue)
2. DCR1c (six-gate GO, T1 absent)
3. DCR1d (Newton positive control — historical, not instrumental)
4. DCR1e (presupposition extractor, recognizer gap)
5. DCR1f (target_v4, placebo fires)

**Full DR6 empirical triangulation:**

DR6 → DR6c → DR6d → DR6e → DR6f → DR6g → DR6h. Reading in order shows
how each variant sharpened DR5* through DR5\\*\\*.

All papers reproduce via each runner's own `run_*.py`. Prior verdicts
stay byte-identical after every subsequent paper.
