# Two Preregistered Nulls: The Loud Commitment vs the Silent One, and the Constraint Geometry That Wasn't

**Human director:** Jawaun Brown
**Producing agent:** Claude Code, directed
**Program:** Cross-arc joint synthesis
**Date:** 2026-07-27
**Scope:** DCR3 (DR-arc textual nominator on real material) + Constraint-Swap Causal Geometry (32-seed representational-deformation study, run independently by the human director).

---

## Abstract

Two independently designed load-bearing experiments were preregistered
and executed on 2026-07-27. Each targeted the strongest claim its
research arc could make on a case where the answer could be checked.
Each hit its stated gate. Each failed cleanly, in a way that was
predicted-in-principle by the arc's own theoretical work but not yet
demonstrated on real material.

**DCR3** asked whether the DR-arc's execution-free scoring function
ranks Einstein's actual 1905 deletion (the T1 = absolute-simultaneity
class) first on the pre-1905 electrodynamics corpus. Result: T1 came
in **third**, behind `unclassified` (rank 1) and `T2_privileged_frame`
(rank 2). The scoring function was not broken — it correctly
identified T2 as the most-defended commitment in the corpus, which
historically it was. But **the most-defended commitment is not the
deletable one.** Silent commitments are deletable precisely because
nobody is defending them, and Einstein's move required exactly that
asymmetry.

**Constraint-Swap Causal Geometry** asked whether a task constraint
that determines successful-future reachability causally deforms a
recurrent agent's hidden geometry, and whether targeted low-rank
transports of that geometry selectively reverse or accelerate the
corresponding behavior. Result: 32 seeds, all preregistered
non-compensatory gates G1–G5 failed. The agents were competent
(mature A/B/D accuracy = 1.000), the sham stayed at chance (0.509),
the injected-geometry recovery lift (0.907) confirmed the
intervention machinery works. But **constraint-specific reachability
geometry did not appear, swaps did not track, and rank-4 affine
transports did not selectively drive behavior.** In a controlled
regime with exactly enumerable reachable futures, the constraint→
geometry→behavior causal chain did not hold.

These are the honest results. They are also the strongest form of
each arc's claim that could be tested in a session with proper
discipline. Both fail. The failures constrain what the next attempt
would need to be.

---

## 1. What each experiment was designed to establish

**DCR3.** Preregistered scoring: score(p) = kind_weight(p) times
degree(p). Class-level sum with `multidoc(min_docs=2)` gating.
Ground truth: T1 class per DCR1c/d/e/f/2a/2b. Baseline: 10,000 random
permutations. Four non-compensatory gates (M1 T1-first-at-1904, M2
T1-not-first-at-1880, M3 beats-random-null, M4 scoring-committed).
The intended-positive outcome was the strongest empirical statement
the DR-arc could make: *"execution-free algorithmic nomination
identifies the commitment a scientific community deleted, on a real
case with ground truth."* First-of-its-kind if it landed.

**Constraint Swap.** Preregistered by the human director on
2026-07-27 03:41 EDT before implementation. Corrected once
(2026-07-27 03:48) after an F0 unit test rejected the initial
vertical/horizontal-fiber design as unable to distinguish metric
deformation from coordinate rename. Active design: 6×6 torus (7×7
horizontal cylinder for topology transfer) with two orthogonal
even-parity constraints (checkerboard C_A, horizontal-stripe C_B), a
learnable deterministic control C_D (vertical-stripe parity), and a
randomised sham. Frozen meta-GRU agents. Five non-compensatory gates
(G1 constraint-specific geometry, G2 swap tracking, G3 selective
impairment, G4 selective rescue, G5 topology transport), each
requiring both directions and preservation controls. The
intended-positive outcome: *"constraint-conditioned reachability-
aligned hidden subspace is causally relevant to behavior in this
controlled regime."*

Both are the strongest testable version of their arc's central claim.
Both are ground-truthed. Both preregistered non-compensatory gates
and honored the verdicts.

## 2. What each experiment established

### DCR3 result (from PR #442)

The DR-arc nominator scored 1904 as:

| rank | class | score | members | documents |
|---:|---|---:|---:|---:|
| 1 | unclassified | 302 | 235 | 15 |
| 2 | T2_privileged_frame | 15 | 11 | 8 |
| **3** | **T1_absolute_simultaneity** | **9** | **7** | **5** |
| 4 | T3_local_time_artifice | 2 | 2 | 2 |

M1 NO_GO (T1 rank 3 ≠ 1). M2 GO. M3 NO_GO by construction. M4 GO.
Overall NO_GO.

**Substantive finding:** T2 (aether frame) outscored T1 (simultaneity)
because T2 was more widely stated and defended across the
electrodynamics literature — exactly what the scoring rule measures.
Einstein did not delete T2. He deleted T1, and T1 scored low because
absolute simultaneity had gone silent in the physics community by
1900 (as DCR1d showed on Newton's Scholium). *Silent = undefended =
deletable.* The DR-arc's assumption "load-bearing in text ⇒
deletable in a revolution" runs backward on this case.

### Constraint Swap result (from PREREGISTRATION + summary.md)

32 preregistered confirmatory seeds, 10,000 bootstrap resamples,
active 6×6 torus + transfer 7×7 cylinder.

| gate | verdict |
|---|---|
| F0 integrity + identifiability | **PASS** (registered component tests) |
| F1 competence + measurement sensitivity | **PASS** (A, B, D all 1.000; sham 0.509; injected-geometry recovery lift 0.907) |
| G1 constraint-specific geometry | **FAIL** (A-specific −0.363, B-specific −0.237) |
| G2 swap tracking | **FAIL** (A→B −0.594, B→A −0.593) |
| G3 selective impairment | **FAIL** (undo-B −0.187, undo-A −0.225) |
| G4 selective rescue | **FAIL** (impose-B −0.057, impose-A −0.014) |
| G5 topology transport | **FAIL** (all transfer sub-gates) |

Decision: `REJECT_CONSTRAINT_SPECIFIC_DEFORMATION`.

**The controls are the load-bearing part of the failure.** F0
identifiability passed, F1 competence + measurement sensitivity
passed, sham stayed at chance, and the positive-control geometry
injection was recovered with lift 0.907. So the failure of G1–G5 is
not "the intervention didn't work" or "the agent couldn't learn the
task" — it is: **the agent solved the task, the interventions on
constructed geometry worked, but the geometry the interventions were
supposed to target does not appear to carry the constraint-specific
information in the way the hypothesis predicted.** Under this
implementation, in this controlled regime, the causal chain does not
hold.

## 3. What the joint reading is

Both arcs' strongest testable claims failed in exactly the direction
each arc's theoretical machinery said they might.

- **DR5 / DR7** predicted that proposition-ranking nominators cannot
  distinguish a commitment $D$ from any specific realisation
  when $D$ has multiple non-equivalent surface forms. DCR3 confirms
  this on real material: T1's 6-register spectrum (DCR1f) is
  distributed across the corpus in a way that surface-based scoring
  systematically underweights.
- **DR5\\*\\*** predicted that verifiers with weak access to $D$'s
  canonical form hit a graded wall whose severity depends on
  domain-general proxies. Constraint Swap tested a version of this
  in a different modality: an agent's *internal* representation
  under task-constraint variation. The result is even sharper — no
  proxy signal was found either. The active reachability geometry
  did not track the active constraint, even in a controlled world
  where reachability was exactly enumerable.

The two arcs together map a **specific failure surface**: on real
conceptual-change material with ground truth (DCR3) *and* in a
controlled agent-representation regime with ground truth (Constraint
Swap), the strongest currently-testable versions of both
"algorithmic identification of the target deletion" and "causal
constraint→geometry→behavior chain" do not hold.

This is not "nothing works." It is *"here are two specific
architectural approaches that were tested with proper discipline and
did not clear their load-bearing gates."* Both results are
publishable-shaped, both are informative, and both constrain what the
next serious attempt has to look like.

## 4. What survives

- **The methodology.** Both arcs demonstrate that scientific
  computational-verification questions CAN be operationalised with
  preregistered gates, single-shot verdicts, and honest reporting of
  the null. DCR3 followed DCR1's discipline (preregistration written
  first, scoring function SHA-256-pinned). Constraint Swap followed
  its own more stringent discipline (F0 unit tests rejected the
  first design *before any training*; the pivot to balanced
  parity-based constraints was recorded as an amendment).
- **The characterisation.** DR5 + DR7 + DR5b + the DR6 empirical
  triangulation now stand as a coherent theoretical framework whose
  empirical predictions have been tested twice, with both tests
  producing the predicted class of null. That is not "the framework
  is wrong" — that is "the framework correctly predicted the shape
  of the wall in advance."
- **The specific new finding from DCR3.** The loud/silent asymmetry
  (defended commitments are protected, silent commitments are
  deletable) is a substantive claim about how conceptual
  revolutions happen. It is testable on other cases (Copernicus,
  Darwin, Lavoisier — each with known deletions) and would extend
  the DR-arc's empirical scope if replicated.

## 5. What does not survive

- **The DR-arc's assumption that textual load-bearing predicts
  deletability.** DCR3 shows this is false in the direction that
  matters for revolutions.
- **The "meaning is constraint-induced deformation of reachable
  possibility" grand principle, in its unmodified form.** Constraint
  Swap tested a specific empirical claim that would follow from the
  principle if it were true of learned recurrent agents in
  controlled worlds, and rejected the claim on 32 seeds. The
  principle may still be right in some broader sense — as the other
  agent noted, unifying principles are always at risk of surviving as
  evocative metaphors — but as a mechanistic claim it has been
  tested here and did not survive.

## 6. What comes next (both arcs' honest continuations)

**DR-arc.** Two paths:

- **Semantic-scoring DCR3b.** Replace `degree` with a Claude-based
  score for "how presuppositional is this commitment given the
  corpus's arguments." DR6/DR6e showed LLM semantic access escapes
  DR5's wall for accessible $D$; this would test whether it reaches
  T1 on the electrodynamics corpus. Not a proposition-ranking
  nominator any more — the LLM does the ranking. Preregister the
  scoring prompt before running.
- **Theorem-shape DR8.** Prove formally that any proposition-ranking
  scorer based on corpus statistics cannot identify
  silent-but-presupposed commitments. Would generalise DCR3's
  empirical finding into a specific corollary of DR5/DR7.

**Constraint-swap arc.** Two paths:

- **Real-network Constraint Swap.** The 32-seed rejection was in a
  toy meta-GRU on a 6×6 torus. The same experiment on a real
  vision-language model with activation-patching interventions
  would be a much larger test. Predicted based on the toy result:
  probably still fails, but the failure would be in a regime that
  interpretability researchers already care about.
- **Weaker "descriptive geometry" claim.** Drop the causal
  intervention gates (G3–G5) and just ask whether the geometry
  *correlates* with the constraint. Constraint Swap's own metrics
  (G1 A-specific −0.363) suggest the answer is no even at this
  weaker level — but a re-designed metric might catch a residual
  correlation. This would be a descriptive claim, not the
  mechanistic claim the original was aimed at.

## 7. Honest answer to "is this major?"

No, and now I have a specific reason to say so beyond the earlier
"not-yet" framing.

Both load-bearing tests failed. That is not "major-and-negative" in
the sense of a paradigm-shifting refutation of a widely-held claim.
It is: two well-scoped attempts hit their scoped limits. The
DR-arc's textual approach does not reach the deletion Einstein
made; the constraint-geometry approach does not establish the
causal chain in a controlled toy regime.

What this session's work IS, if honestly labelled:

- A working methodology for preregistered verification of
  computational-scientific claims that would otherwise slip.
- Two theorems (DR5, DR7) with an empirical triangulation across
  two domains and two verifier architectures.
- Two clean nulls on the strongest load-bearing versions of two
  independent research programs' central claims.
- One substantive empirical claim (the DCR3 loud/silent asymmetry)
  that would extend if replicated.

That is a real and honest contribution. It is not major in the
"changes what the field thinks" sense. Being clear about what a
result IS is more useful than inflating it.

---

## Appendix: reproduction

**DCR3:**
```
uv run --no-sync python -m experiments.date_cut_retrodiction.run_dcr3
```

**Constraint Swap:**
See `experiments/constraint_swap_causal_geometry/README.md` for
`run_experiment.py` invocation and 32-seed configuration.

Both experiments' preregistrations, gate verdicts, and raw data
committed to the repository. All prior arcs unchanged.
