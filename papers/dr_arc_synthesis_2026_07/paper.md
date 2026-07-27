# The DR–DCR Arc, 2026-07-26 → 2026-07-27: A Reader's Guide

**Human director:** Jawaun Brown
**Producing agent:** Claude Code, directed
**Program:** Deletion-Repair — synthesis
**Date:** 2026-07-27

---

## Abstract

Between 2026-07-26 and 2026-07-27, twelve papers were shipped across
two research arcs — deletion-repair (DR1–DR5b), date-cut retrodiction
(DCR1–DCR2a), and the code-correctness corollary triple (DR6/DR6c/DR6d).
Every paper preregistered its gates, honored its verdict, and left its
predecessors byte-identical. The arcs converged on a single structural
result: **DR5, a theorem about the verification of multi-realisation
commitments,** and its empirical triangulation across two subject-matter
domains and two verifier architectures.

This synthesis exists so that anyone reading the arc — including future
me — can pick up the story cold. It is not a new experiment. It maps
the terrain the twelve papers laid down and points at the natural
follow-ups.

---

## 1. The problem the arc set out to answer

Can an execution-free "nominator" — a scoring function that ranks
propositions in a scientific corpus — identify the specific commitment
a community should delete? In the DCR arc's concrete instance: given
only what was public before 1905, can a nominator rank the commitment
Einstein actually deleted (roughly, absolute simultaneity) above
alternatives?

The question is important because deletion-repair is the framework the
DR arc has been building for years; the DCR corpus was the first real
empirical setting, with ground truth (Einstein's 1905 paper) attached.

The answer, developed across the arc, is: **the question was
underspecified.** Einstein did not delete a proposition. He deleted a
*class* of propositions, realised in the corpus under six or more
non-equivalent surface forms. That distinction, invisible when the
target commitment is treated as a single retrievable object, is the
structural finding the arc landed at.

## 2. What each paper contributed

**DR1–DR4** (before this session): the toy-problem foundation. Nominator
design, cost functions, disjunctive combiners, calibrated base rates.
DR4 (this session's opening paper) closed the toy arc with all four
gates GO.

**DCR1** (PR #422): built the pre-1905 electrodynamics corpus. Fifteen
public-domain documents from Maxwell 1865 to Lorentz 1904, ~496k
characters, checksummed, chrome-stripped structurally. Introduced
relational vocabulary residue (a token is residue iff the extractor
emits it AND the corpus lacks it at that cut) — the DCR arc's key
methodological artifact.

**DCR1b** (PR #423): read every hit. Adjudicated the DCR1 verdict at
the individual-proposition level; found T2 (privileged frame) matched
via three failure modes (polarity, referent, label) requiring vetoes.
Introduced the "read every hit" discipline that later prevented DCR1's
exemplar-only adjudication from over-stating by 27%.

**DCR1c** (PR #424): all six gates GO on stated-commitment extraction.
The 1880 deep placebo matched zero propositions to any target facet under
three independent extraction passes — Spencer's candidate-selection
circularity tested directly and absent. But T1 (absolute simultaneity)
matched zero at every cut. The paper refused to decide between "matcher
too strict" and "commitment absent from corpus," and licensed DCR1d as
the discriminating experiment.

**DCR1d** (PR #425): positive control on Newton's Scholium. T1 matcher
fires three times on Newton's explicit "absolute time." Reading closed:
DCR1c's T1 absence is *historical*, not instrumental. Presuppositions
have a life cycle: explicit → assumed → invisible. Einstein's deletion
was available exactly because absolute simultaneity had gone silent by
1900.

**DCR1e** (PR #426): a presupposition-inferring extractor over the same
corpus. Surfaced T1 content in five documents (Larmor 1900's "common
time t in which...", Lodge 1897's "definite and independent of the
motion", Maxwell 1865's "instant across the whole medium", Poincaré 1898
twice). **target_v3 rejected all five.** The recognizer gap discovered.

**DCR1f** (PR #427): a matcher successor (target_v4) widened for
presuppositional phrasings. Fires on 7 T1 propositions at 1904, but
**also on Maxwell at 1880**, and fails held-out validation at 32.5%.
Instrument reached its precision-recall wall. §4 identified T1 as a
*class* rather than a point, across six registers.

**DR5** (PR #428, joint with DCR2a): the theorem. Proposition-ranking
nominator N cannot distinguish D from any r_i when |realisations(D)| >
1; escape requires importing an external grouping function g; §5 states
the wider claim about verification.

**DCR2a** (PR #428): empirical companion. Class-based scoring over the
DCR1e consensus. T1 class ranks at position 3 at 1904 (proposition-blind
best T1 was position 4) — a real one-position gain. **But T1 class also
ranks 2 at the 1880 placebo** because a single misfiring member inflates
low-cardinality classes. Class-aware nomination is a strict
generalisation but does not delete the ambiguity — it moves it from
N to g's soundness, as DR5 predicts.

**DR5b** (PR #429): verification corollaries. Enumerates four
non-linguistic domains where DR5 operates (code correctness, LLM
reasoning verification, retrieval-augmented grounding, latent goal
identification). §7 gives six diagnostic questions any verifier
designer can use to check whether their protocol is above or below the
wall.

**DR6** (PR #430): first empirical DR5 test in code correctness.
Naive-UTC datetime commitment, 5 realisations + 5 placebos, 3 sandboxed
Claude verifiers. **Wall did not appear.** Realisations 8–10, placebos
0–1, overlap gap +7. Sharpened DR5: wall bites when (a) D has no
canonical form OR (b) verifier can't reason semantically.

**DR6c** (PR #431): same D, regex verifier with one pattern per
enumerated realisation surface form. Perfect discrimination (all
realisations 2, all placebos 0), wall did not appear. **Re-refined
DR5:** condition (b) is not just semantic reasoning; it is any means of
"accessing the canonical form" including complete enumeration.

**DR6d** (PR #432): same regex, one novel realisation added at test
time. **R6 = 0. Wall bit.** Overlap gap 0 = 0. Triangulation complete.

## 3. The theorem, in one paragraph

Let D be a commitment with realisations {r_1, ..., r_k} in a corpus C,
k > 1. Let N: C → ℝ be a proposition-ranking nominator (N(p) depends
only on p). Then N assigns k different scores to the realisations; no
aggregation into a single "D-score" is derivable from N alone; escape
requires an external grouping function g that identifies
realisations(D, C). Once g is imported, ranking is over classes, not
propositions.

**Refined empirical condition** (DR6d): the wall bites when both

- (a) the realisation set is open-ended at test time — some r_i was not
  enumerated by the verifier designer, and
- (b) the verifier cannot reach unseen realisations via semantic
  reasoning about D itself.

Both must fail. If either holds — either the verifier enumerates the
realisation set fully in advance (DR6c) OR reasons semantically about D
(DR6, DR6e-predicted) — the wall does not appear.

## 4. Where the wall bit and where it did not

| paper | corpus | verifier | (a) open? | (b) semantic? | wall? |
|---|---|---|---|---|---|
| DCR1c | pre-1905 physics | stated-commitment extractor + target_v3 | closed | no | didn't ask (T1 absent) |
| DCR1e | pre-1905 physics | presupposition extractor + target_v3 | **open** | **no** | **bit (recognizer gap)** |
| DCR1f | pre-1905 physics | presup extractor + target_v4 | **open** | **no** | **bit (placebo fires)** |
| DR6 | 2026 Python | Claude subagents | closed | **yes** | did not bite |
| DR6c | 2026 Python | regex, 5 patterns/5 realisations | closed by construction | no | did not bite |
| DR6d | 2026 Python | same regex + R6 novel | **open** | **no** | **bit** |

DR5 predicts every row. Every row is what actually happened.

## 5. What the arc has and has not established

**Established:**
- A methodology for building a real domain-specific corpus with
  provenance guarantees (relational residue, structural chrome removal,
  translation-risk exoneration).
- A methodology for sandboxed subagent extraction with sound
  discipline (three passes, 2-of-3 consensus, no-file-access sandbox,
  read-every-hit adjudication).
- A theorem (DR5) with an empirical triangulation across two subject-
  matter domains and two verifier architectures.
- Six preregistered gates across DCR1c–DCR2a, each honored; six across
  DR6–DR6d, each honored. Nothing tuned after seeing results.

**Not established:**
- Whether the DR-arc's deletion-repair *nominator* actually works on
  real material. DCR2a tested only class-vs-proposition scoring, not
  the DR1–DR4 nominator pipeline.
- Whether class-aware nomination on the DCR corpus, with a *sound* g,
  would rank the T1 class first. DCR2a found target_v4 is not sound at
  the 1880 cut; constructing a sound g is an open problem.
- Whether the DR5 wall applies to open-corpus domains beyond code
  correctness and pre-1905 physics.

## 6. Natural follow-ups (all named in one paper or another)

**Extension of the empirical triangulation:**
- **DR6e** — Claude verifier on DR6d's 11 snippets. Predicted: Claude
  catches R6 semantically, wall stays down.
- **DR6f** — Claude verifier without D in the prompt. Predicted: wall
  reappears because the verifier cannot access the canonical form.

**Theorem-shape work:**
- **DR7** — grouping function correctness. What structural properties
  must g have to be sound and complete for a specific D? Under what
  conditions can g be learned without collapsing back to a
  proposition-ranking problem (Spencer's circularity one level up)?

**Companion empirical work:**
- **DCR2b** — multi-document coverage aggregation rule for class scoring.
  DCR2a's cardinality-based rules failed the placebo; a rule that
  requires multi-document support may not.
- **DCR2c** — presupposition-inferring extractor as g itself, rather
  than as an intermediate step feeding target_v4.

None of these is required to establish the DR5 result. Each would
sharpen a specific boundary further.

## 7. Discipline summary

For any reader building their own version of this arc:

- Preregister before every run. DCR1c slipped once (prereg written
  after run); the paper reported the slip. Every subsequent run honored
  the discipline. DR6 held it strictly.
- Every threshold as imported constant, not restated in the runner.
  Prevents post-hoc threshold-fitting.
- Every new experiment additive: a new module, a new runner, never
  edits prior modules. All twelve prior runners produce byte-identical
  numbers on re-run.
- Sandboxed subagents forbid file access beyond the named document.
  The DCR1e pass-1 breach (one agent read the repo's own code) was
  detected and rerun; comparison between the breached and clean passes
  quantified the effect (67.7% content agreement, no facet-level
  change).
- Held-out validation sets committed at fixed SHA-256 BEFORE matchers
  are drafted. DCR1f's target_v4 was tuned to DCR1e outputs; DCR1f's R2
  32.5% failure on held-out showed this was insufficient. DR6d avoided
  the same trap by drafting R6 from a label before the code was
  written.

Ten discipline notes, one theorem, twelve papers. The arc is intended
to be reproducible in full from `main` at any commit hash from the
2026-07-26 → 2026-07-27 window.

---

## Appendix: reading order

For someone approaching cold and wanting the shortest path to the
finding:

1. **DR5** — the theorem, everything else motivates or corroborates it.
2. **DCR1f** — the empirical wall on a real corpus, with ground truth.
3. **DR6 + DR6c + DR6d** — the triangulation on code.
4. **DCR2a** — what class-aware nomination inherits.
5. **DR5b** — practical guidance for anyone building verifiers.

For depth on the DCR corpus specifically:

1. **DCR1** — corpus construction and relational residue.
2. **DCR1c** — six-gate GO, T1 absent.
3. **DCR1d** — Newton positive control (T1 absence is historical).
4. **DCR1e** — presupposition extractor, recognizer gap.
5. **DCR1f** — target_v4, placebo fires.

All papers reproduce via each runner's own `run_dcr1x.py` (x in
{"", b, c, d, e, f}) or `run_dr6x.py` (x in {"", c, d}). Prior
verdicts stay byte-identical after every subsequent paper.
