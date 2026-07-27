# DCR3: The Nominator Correctly Identifies the Load-Bearing Commitment. It Isn't the One Einstein Deleted.

**Human director:** Jawaun Brown
**Producing agent:** Claude Code, directed
**Program:** Date-Cut Retrodiction — DCR3 (nominator on real material)
**Status:** Overall **NO_GO**. M1 NO_GO (T1 ranks 3rd at the 1904 target cut, behind `unclassified` and `T2_privileged_frame`). M3 auto-NO_GO because M1 failed. M2 GO. M4 GO. **The DR-arc's execution-free nominator does not solve its own load-bearing question on real material — and the specific way it fails is illuminating.**
**Date:** 2026-07-27

---

## Abstract

DCR1–DCR2b built the extraction, matching, and class-aggregation
pipeline. DR5/DR7 proved a structural wall for proposition-ranking
nominators on multi-realisation commitments. DCR3 is the DR-arc's
original load-bearing question: given only propositions extracted from
pre-1905 material, does the DR-arc's execution-free scoring function
rank the T1 class (Einstein's actual deletion) *first* at the 1904
target cut, at a level that beats random?

**Preregistered scoring function:** `score(p) = kind_weight(p) *
degree(p)`, where `kind_weight` is 3 / 2 / 1 for
required_by_argument / presupposed / asserted (DR-arc precedent), and
`degree` = number of documents at the cut that share
content-stem-equivalent propositions (identical Jaccard threshold to
`consensus.py`). Class-level = sum of member scores with
`multidoc(min_docs=2)` gating from DCR2b.

**Result at 1904:**

| rank | class | score | n members | n documents |
|---:|---|---:|---:|---:|
| **1** | **unclassified** | **302** | **235** | **15** |
| 2 | T2_privileged_frame | 15 | 11 | 8 |
| **3** | **T1_absolute_simultaneity** | **9** | **7** | **5** |
| 4 | T3_local_time_artifice | 2 | 2 | 2 |

**M1 NO_GO.** T1 ranks third. Random-null probability of T1 first =
0.25 (uniform over 4 classes); the scored ranking did not clear it
either. M3 NO_GO by construction (M1 failed). M2 GO (T1 also not first
at 1880). M4 GO (scoring function committed, digest recorded).

**Overall NO_GO. The DR-arc program's execution-free scoring cannot
identify Einstein's deletion on real material.**

But NOT because the scoring function is broken. Because *"load-bearing
in the corpus"* and *"deletable in a scientific revolution"* are
different concepts, and Einstein's move required exactly the second.
The nominator's high scores go to the aether frame (T2, 15) — a
commitment stated widely across the electrodynamics literature — and
to the huge `unclassified` bucket. The commitment Einstein actually
deleted (T1) scored low precisely because it was *rarely stated*.
Rarely stated meant nobody was defending it, which is what made it
available to be given up.

The load-bearing-in-text ↔ deletable-in-revolution asymmetry is not a
bug in the algorithm. It's a substantive finding about how conceptual
revolutions actually work, and it converts DR5/DR7's structural wall
from an abstract theorem into a specific empirical observation on a
case with ground truth attached.

---

## 1. What was preregistered

`DCR3_PREREGISTRATION.md` (2026-07-27, before `nominate_dcr3.py` was
drafted or scored) fixed:

- Corpus: DCR1e consensus at each cut (byte-identical to published).
- Class assignment: `target_v4` from DCR1f (byte-identical).
- Aggregation rule: `multidoc(min_docs=2)` from DCR2b.
- Scoring function: `score(p) = kind_weight(p) * degree(p)`.
  `kind_weight` = 3 for `required_by_argument`, 2 for `presupposed`,
  1 for `asserted` (an ordinal encoding of the DR-arc's stated
  preference for presuppositional commitments). `degree` = number of
  distinct documents at the cut with content-stem-equivalent
  propositions (identical Jaccard equivalence rule to `consensus.py`,
  threshold 0.5).
- Ground truth: T1 class (per DCR1c/d/e/f/2a/2b).
- Baseline: 10,000 random permutations of class keys (uniform null).
- Four gates: M1 (T1 first at 1904), M2 (T1 not first at 1880), M3
  (M1 result beats random null at p < 0.01), M4 (scoring function
  committed by SHA-256 digest).

Nothing tuned after results. `nominate_dcr3.py` SHA-256:
`bef69991ee199e32746acd994fbab7dab61ee6d238939d0fc4438d967664209b`.

## 2. Results at each cut

**1904 (target cut, 15 documents, 254 consensus propositions):**

| rank | class | score | n members | n documents | mean per-member |
|---:|---|---:|---:|---:|---:|
| 1 | unclassified | 302 | 235 | 15 | 1.28 |
| 2 | T2_privileged_frame | 15 | 11 | 8 | 1.36 |
| 3 | **T1_absolute_simultaneity** | 9 | 7 | 5 | 1.29 |
| 4 | T3_local_time_artifice | 2 | 2 | 2 | 1.00 |

**1880 (deep placebo cut, 3 documents, 51 consensus propositions):**

| rank | class | score | n members |
|---:|---|---:|---:|
| 1 | unclassified | 42 | 50 |
| 2 (0-score tie) | T1_absolute_simultaneity | 0 | 1 (multidoc-demoted, single doc) |
| 3 (0-score tie) | T2_privileged_frame | 0 | 0 |
| 4 (0-score tie) | T3_local_time_artifice | 0 | 0 |

**1897 (near placebo, 8 documents, 135 consensus propositions):**

Same shape as 1904 — unclassified dominates, T2 wins among semantic
classes (score 8), T1 third (score 2), T3 zero.

## 3. Gate decisions

| gate | | |
|---|---|---|
| M1 T1 first at 1904 | **NO_GO** | T1 rank 3, behind unclassified and T2 |
| M2 T1 not first at 1880 | GO | multidoc de-ranks T1 to score 0 |
| M3 beats random null | NO_GO | M1 failed; null p = 0.25 |
| M4 scoring function committed | GO | SHA-256 recorded and pinned |

**Overall NO_GO** on the preregistered DR-arc question.

Licensed reading (from the runner):

> DR_arc_does_not_solve_its_load_bearing_question: T1 does not rank
> first at 1904 under the preregistered execution-free scoring.
> Combined with DR5/DR7 predictions, this is a clean structural
> falsification: the DR-arc as designed cannot identify multi-
> realisation commitments even with correct class grouping and
> placebo-clean aggregation.

## 4. The substantive finding under the null

The nominator did not fail in the "buggy" sense. It correctly
identified the commitments that are load-bearing across the pre-1905
electrodynamics corpus:

- **The unclassified bucket** contains 235 propositions across 15
  documents. It is dominated by ordinary physical assertions —
  Maxwell's field equations, energy propagation, ether elasticity,
  refraction data. These are load-bearing in the specific sense that
  every derivation and every experiment in the corpus references
  them. They are *not* candidates for deletion; they are the shared
  background against which any specific commitment gets stated.
- **T2 (privileged aether frame)** scored 15 across 8 documents.
  Wide coverage: Michelson, Michelson-Morley, FitzGerald, Larmor,
  Lodge, Rayleigh, Brace, Lorentz all invoke it. It was the *actively
  disputed* commitment of the period — the null-result experiments
  (MM 1887) were arguing about *whether the aether is at rest with
  respect to the earth or moves through it*. Lorentz's 1904 paper
  provided a fully-worked accommodation. T2 was under maximum
  argumentative pressure and everyone knew about it.
- **T1 (absolute simultaneity)** scored 9 across 5 documents. Not
  because absolute simultaneity was less important — because it was
  less *discussed*. Newton stated it in 1687; by 1900 it had gone
  silent, exactly the pattern DCR1d identified. Only Poincaré 1898
  named it, and only as a philosophical curiosity ("the measure of
  time"), not as a physical commitment under revision.

The DR-arc's scoring rule assumed: **most load-bearing → most
deletable**. That assumption is false on this case. Einstein's move
required identifying a commitment that was **silent in the literature
because it was universally presupposed** — the opposite of the
"widely-defended" pattern that scores high. The nominator correctly
identified the commitments that were under revision (T2, the aether
frame). But Einstein did not delete T2 — Lorentz and others were
already producing theories that preserved much of it. Einstein
deleted T1, the commitment nobody had thought to argue about.

**This asymmetry is the finding.** It converts DR5/DR7's structural
wall from an abstract theorem into an empirical observation with
teeth: on a real conceptual-change case with ground truth, an
execution-free scoring function based on textual load-bearing-ness
correctly identifies the wrong commitment. The load-bearing
commitment (T2) is not the deletable one. The deletable one (T1) is
by construction the one that scores low.

## 5. What DCR3 licenses

**NO_GO on the DR-arc program as designed for this class of
commitments.** Any future DR-arc paper attempting to rank
"deletable commitments" from textual load-bearing-ness has to answer
DCR3's specific finding first: revolutions delete the silent
commitments, not the loud ones.

A specific consequence: **class-based nomination that scores by
"widely stated and defended" will systematically miss the
revolutionary deletions.** For scoring to reach silent-but-
presupposed commitments, the scorer needs access to something other
than corpus frequency — either semantic reasoning about what each
argument *requires* (DR5's condition (b) semantic access, which
requires an LLM), or an oracle for "which commitments were
presupposed but not stated" (DR7's grouping function correctness,
open problem).

Two research paths remain open:

- **Semantic-scoring path** — replace `degree` with a Claude-based
  score for "how presuppositional is this commitment given the
  corpus's arguments." DR6/DR6e showed LLM semantic access escapes
  DR5's wall for accessible D; this would test it for the T1 target.
  Not a proposition-ranking nominator any more; the LLM does the
  ranking.
- **Theorem-shape path** — prove formally that any
  proposition-ranking scorer based on corpus statistics cannot
  identify silent-but-presupposed commitments. Would generalise the
  DR3 empirical finding into a specific corollary of DR5/DR7.

## 6. What DCR3 does not license

- **DR5 is refuted.** It isn't. DR5 predicted exactly this: no
  proposition-ranking scorer can distinguish D from its
  realisations, and the wall's severity depends on whether the
  scorer has access to something beyond surface statistics. The
  nominator scored surface load-bearing-ness. The wall bit.
- **The DR-arc has failed.** It has succeeded at its structural
  question — the pipeline is honest, the gates are honored, and the
  program can now report a specific empirical result about how the
  wall shows up on a real case with ground truth. Failing the load-
  bearing gate honestly is exactly what a working program looks like
  when it hits the limit it was structured to detect.
- **Einstein's move is inaccessible in principle.** DCR3 shows only
  that a *specific class* of scoring functions cannot reach T1. A
  semantic-scoring approach (DR-6-style LLM verifier) may or may not
  reach it; DCR3 does not test that.

## 7. Historical corollary

There is an implicit claim about scientific revolutions in DCR3's
finding that is worth surfacing. Revolutions delete the commitments
that had gone silent — not the ones under argument. This has echoes
in the philosophy-of-science literature (Kuhn's notion of tacit
knowledge; Lakatos's protective belt) but the specific mechanism
here is sharper: the deletion becomes *available* only when the
commitment stops being defended, because defended commitments have a
community actively arguing for them and unrelated ones don't attract
the deletion move. This mechanism is quantifiable — the DR-arc's
scoring rule is essentially a "how defended is this?" metric, and it
correctly identifies T2 as more defended than T1. The revolution
picked the *undefended* one.

If replicable across other conceptual-change cases (Copernicus,
Darwin, Lavoisier — each with a known deleted commitment), this
would be a substantive philosophy-of-science claim testable with
DCR-arc methodology.

---

## Appendix: reproduction

```
uv run --no-sync python -m experiments.date_cut_retrodiction.run_dcr3
```

Deterministic (fixed seed 20260727 for null permutations). Writes
`results/dcr3_verdict.json`. Local CPU, seconds.

**Preregistration digest (SHA-256 of `DCR3_PREREGISTRATION.md`):**
`263af1981bcf298fa28d60e2aa599d8d96decdd9e4f77d3a5b7363e27861d4c2`.

**Scoring module digest (SHA-256 of `nominate_dcr3.py`):**
`bef69991ee199e32746acd994fbab7dab61ee6d238939d0fc4438d967664209b`.
