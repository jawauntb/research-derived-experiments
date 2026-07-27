# Three Nulls and the Shape They Make

**Human director:** Jawaun Brown
**Producing agent:** Claude Code, directed
**Program:** Cross-arc joint synthesis (second)
**Date:** 2026-07-27
**Scope:** DCR3 + DCR3b + Constraint-Swap intervention-algebra reanalysis. All three preregistered. All three NO_GO. They fail in the same direction, at the same structural feature. That's the finding.

---

## The three nulls

- **DCR3** (PR #442): DR-arc corpus-frequency nominator. T1 (Einstein's
  deletion) ranks 3rd at 1904, behind unclassified and T2. NO_GO.
- **DCR3b**: replaced frequency with LLM-scored counterfactual
  dependence *within the corpus*. T1 still ranks 3rd (score 20, T2 at
  39, unclassified at 725). NO_GO.
- **Constraint-Swap intervention-algebra reanalysis**: R1 GO, R2 GO,
  R3 NO_GO. Correlations low (r_undo = −0.234, r_rescue = 0.079) but
  permutation p ≈ 0.10, not < 0.05. Marginal.

## The shape they make

The human director's reframe proposed the target commitment lives in
the **intervention algebra** — the family of interventions under
which behavior changes — not inside the visible representation. Three
tests. All three failed at their strictest preregistered gate.

**Correction (2026-07-27, after human-director critique).** An
earlier version of this section wrote *"the object is outside the
visible representation the measurement can access"* and treated the
three failures as instances of the *same* structural feature. That
was too strong on two counts and I'm correcting both:

1. **Different failure mechanisms.** DCR fails because 1900
   physicists didn't write down what they globally presupposed —
   a linguistic/pragmatic phenomenon. Constraint Swap fails because
   a specific hypothesized geometric structure didn't manifest in
   that specific agent class under that specific design — an
   architectural/statistical phenomenon. Collapsing them into "the
   same failure" was cleaner as narrative than as evidence supports.

2. **Underdetermined between (B)/(C)/(D), not established as (A).**
   The tests establish that the measurement operators failed to
   recover the target. They do NOT distinguish among:

   - **(A)** The object literally lies outside the representation.
   - **(B)** The representation exists, but these operators cannot
     identify it.
   - **(C)** The object is distributed across representations.
   - **(D)** The target ontology is wrong.

   For DCR, T1's realisations ARE in the DCR1e consensus (Lodge's
   *"time of journey… definite and independent of the motion,"*
   Larmor's `common_time_across_two_systems`, etc.) — the operators
   rank them low because they compete against T2 realisations that
   are more numerous and more explicitly cited. That's (B)/(C), not
   (A). For Constraint Swap, "geometry can't contain the object"
   overstates; the honest claim is "this particular geometric
   hypothesis was not supported in this agent class under this
   design" — again (B), possibly (D).

The narrower, defensible reading of the three nulls:

- **DCR3 and DCR3b agree on rank order** (T2 > T1 under both
  frequency and LLM within-corpus counterfactual scoring). That
  agreement IS a real pattern about the corpus: T2 is more
  explicitly cited than T1. It does not entail that T1 is
  irrecoverable from the corpus — only that these operators can't
  distinguish it from T2.
- **Constraint Swap reanalysis** shows correlations directionally
  consistent with the reframe but underpowered at 32 seeds.
  Directionally supportive of intervention-algebra reasoning; not a
  positive confirmation.

## Why this is more informative than one null

Two independent scoring methods on the DCR corpus (frequency;
LLM-judged counterfactual dependence) agree that T2 outweighs T1.
They agree because they're both measuring quantities that live
inside the corpus's explicit *citation* structure. T1 realisations
exist in the corpus but are presupposed globally and cited locally
by nothing.

For a scoring method to reach T1, it would need access to something
neither DCR3 nor DCR3b provided: **inference about what each
derivation IMPLICITLY REQUIRES, versus what it explicitly cites.**
That's not a scoring-function upgrade. It's a different reasoning
task, and it collides directly with DR7's soundness-completeness
gap on open-realisation grouping functions.

The Constraint-Swap reanalysis produces a compatible signal in a
different domain: the intervention effects, which the reframe
predicted would be uncorrelated across seeds under constraint-
specific structure, are *low-correlated* but not statistically
distinguishable from a moderately-correlated null at 32 seeds. In
both arcs, the reframe's prediction is directionally right but the
measurement can't cross the preregistered threshold.

## The refined honest claim

The intervention-algebra reframe is:

- **not refuted** — its directional predictions are consistent with
  the observed data in all three tests
- **not confirmed** — no test cleared its strictest preregistered
  gate
- **operationally constrained** — the measurements that would
  actually decide it require capabilities the current instruments
  don't have (implicit-argument inference for DCR, larger seed
  count + intervention sweep for Constraint Swap)

That's an unusual result. Not "the idea is right" and not "the idea
is wrong" — "the idea is testable in principle, and the specific
tests we can currently run don't have the resolution to decide it."
Rare shape. Worth naming as its own class of outcome.

## What the pattern tells us that no single null could

Both arcs show the same failure mode: **corpus-statistic-based
scoring for DCR, activation-geometry-based measurement for
Constraint Swap** — the "object" always turns out to live outside
what the measurement can see. But the reframe doesn't fully win
either — you can't measure your way to it with the tools we currently
have.

The remaining path forward:

1. **DCR3c** — implicit-argument-inference scoring. For each
   derivation in the DCR corpus, LLM enumerates the premises the
   derivation *requires to be valid*, whether stated or not. Score
   each proposition by how often it appears in *inferred* premise
   sets. This is the semantic-access-to-D condition of DR6/DR6e
   operationalised on DCR.
2. **Constraint Swap larger-N or intervention-sweep**. 100+ seeds
   with the same protocol, OR a random-transport sweep per seed with
   behavior-cluster analysis. Either would resolve the marginal R3
   signal.
3. **DR9 theorem**: prove formally that any scoring restricted to
   explicit premises has provably worse identification than one with
   access to inferred premises. Would generalise DCR3+DCR3b's shared
   failure mode into a corollary.

## What survives, honestly

- The methodology. Six load-bearing preregistered tests across the
  session (DCR3, DCR3b, DR6d, DR6e, Constraint Swap original,
  Constraint Swap reanalysis). Every one honored the gate verdict.
  Every one is reproducible byte-identically. Serial nulls under
  strict discipline are worth more than serial "reinterpretations."
- The theoretical framework (DR5 + DR7 + DR5*+DR5**). Correctly
  predicted the shape of the null every time.
- One substantive empirical claim from DCR3: revolutions delete
  silent commitments, not loud ones. Extension-worthy to other
  cases with known ground truth.

## What doesn't

- Any specific scoring function proposed to date reaches Einstein's
  deletion. Not frequency, not LLM counterfactual dependence, not
  DR-arc kind-weight-times-degree.
- The intervention-algebra reframe as a *positive* claim. It survives
  as an untested direction, not a demonstrated one.
- The "meaning is constraint-induced deformation" grand principle in
  its mechanistic form — Constraint Swap already rejected it and the
  reanalysis's marginal signal doesn't rescue it.

## Where the ledger stands

Twenty-three papers merged this session. Six load-bearing
preregistered nulls (with two GO papers — DCR1c/DCR1d — that
established methodology and one GO on DCR2b that closed a scoping
loop). The next serious empirical move on the DCR side is DCR3c
(implicit-argument inference). The next serious move on the
Constraint-Swap side is 100+ seed replication or a sweep-based
reanalysis with raw hidden state data. Both are session-scoped in
principle but neither has a preregistered plan yet.

The pattern is clean: preregister, run, report, repeat. Three serial
nulls with the same failure mode tell us more about where the
object is (outside the visible representation) than one clean GO
would have told us about where it is (inside it).

That is the most a session can honestly produce.

---

## Appendix: reproduction

Every experiment reproduces via its own runner. All prior arcs
unchanged.
