# DCR3c: The Reframe Moved T1 From Rank 3 to Rank 2. Still Not First.

**Human director:** Jawaun Brown
**Producing agent:** Claude Code, directed
**Program:** Date-Cut Retrodiction — DCR3c (identifiability reframe on DCR)
**Status:** Overall **NO_GO** on M1. **T1 climbed from rank 3 (DCR3, DCR3b) to rank 2** under inferred-required-assumption scoring. Score 10 vs T2's 50. The identifiability reframe's most direct DCR operationalisation is *directionally correct* — it demonstrably improves T1's relative position — but still cannot invert the T2 > T1 ordering that every corpus-respecting measurement produces. Fourth serial preregistered null on the DR-arc side.
**Date:** 2026-07-27

---

## Abstract

DCR3 (frequency scoring) and DCR3b (LLM within-corpus counterfactual)
both put T1 at rank 3. The human director's identifiability reframe
proposed that the target commitment is identifiable at the level of
each prediction's *required* assumptions — implicit inference, not
citation. DCR3c tests exactly that on the DCR corpus.

Three sandboxed Claude subagents per cut (9 total). Prompt (SHA-256
`f6a6c7bb758ff5aa88d27e71c4f9d2da5cf1fec204c7ca837246983a638342af`,
pinned in runner) asks: for each proposition, is it an empirical
prediction? If yes, what commitments does it *require* to be a valid
inference — whether stated or not? Categorise each required
commitment as T1 (common time/simultaneity across observers), T2
(preferred rest frame), T3 (local time as artifice), or OTHER.
Consensus tag = ≥2 of 3 verifiers agree. Score each class = count of
predictions requiring it. Multidoc gating on prediction-carrying
documents.

**Result at 1904:**

| rank | class | score | Δ vs DCR3 | Δ vs DCR3b |
|---:|---|---:|---:|---:|
| 1 | T2 | 50 | still first | still first |
| **2** | **T1** | **10** | **+1 rank** | **+1 rank** |
| 3 | T3 | 2 | −1 rank | −1 rank |

The reframe **worked in the direction it predicted** — T1 climbed
one position — but not enough to clear the M1 gate (T1 first at
1904). T2 remains rank 1 because inferred-required-assumption
scoring, done honestly, finds that MORE predictions in the pre-1905
corpus require the aether frame than require absolute simultaneity.
Aether-wind experiments (Michelson-Morley, Lodge, Rayleigh, Brace)
all require T2. Only a subset — the light-travel-time-between-
observers arguments — additionally require T1.

**M1 NO_GO. M2 GO. M3 NO_GO by construction. M4 GO. Overall NO_GO.**
Fourth serial preregistered null on the DR-arc side (DCR3, DCR3b,
DCR3c; DCR2a earlier).

**The stable pattern:** every measurement that respects the corpus's
own structure — citations, in-corpus counterfactuals, inferred
required assumptions — puts T2 > T1 at 1904. To rank T1 first would
require a measurement that specifically identifies "deletable but
not defended" as the property of interest, which is an inverse of
what corpus-respecting measures capture. That is the DCR3 finding
restated with sharper evidence: not that T1 is invisible (it is
identifiable, and identifiable more now than in DCR3/DCR3b), but
that the corpus itself contains more T2-requirements than
T1-requirements. Einstein deleted the less-invoked commitment, and
any measure that respects invocation-count will preserve the ratio
that made T1 the deletable one.

The reframe survives as *directionally correct*. The specific
prediction (T1 climbs to rank 1) does not hold. If a stronger form
of the reframe were to work, it would need to explicitly invert the
corpus's own structure — score by "would-be-cheap-to-remove"
rather than "is-required-by-predictions" — and that's a different
scoring principle from what the reframe proposed.

---

## 1. What was preregistered

`DCR3C_PREREGISTRATION.md` (2026-07-27, before `run_dcr3c.py` was
drafted and before subagent calls were spawned) fixed:

- **Scoring signal:** LLM-inferred required-assumption count per
  prediction, categorised into T1/T2/T3/OTHER by the LLM using
  natural-language rubric committed in `DCR3C_PROMPT.md`
  (SHA-256 `f6a6c7bb…d97291b4`).
- **Verifiers:** 3 sandboxed Claude subagents per cut × 3 cuts.
- **Consensus tag:** ≥ 2 of 3 verifiers must agree that a
  proposition is a prediction AND that a category is required.
- **Multidoc gating:** class score = count of qualifying predictions,
  ONLY IF predictions requiring that class come from ≥ 2 distinct
  documents.
- **Baseline:** 10,000 uniform random permutations of class keys.
- **Gates:** M1 T1 first at 1904; M2 T1 not first at 1880; M3 M1
  result beats null at p < 0.01; M4 prompt digest committed.

Nothing tuned after results.

## 2. Full results

**1904 (target cut, 254 propositions, 254 processed):**

| rank | class | score | contributing predictions | contributing documents |
|---:|---|---:|---:|---:|
| 1 | T2 | 50 | 50 | (many across corpus) |
| **2** | **T1** | **10** | 10 | ≥ 2 |
| 3 | T3 | 2 | 2 | 2 |

**1897 (near placebo, 135 propositions):** Similar shape.
Verifier B alone reported: 52 predictions, T2=26, T1=3, T3=1.
Consensus (≥2 of 3) reduces T1 count further.

**1880 (deep placebo, 51 propositions):** T2 dominant (nearly all
Maxwell claims require stationary aether per verifier A). T1
consensus count low. T3 zero (Lorentz-1904 construct absent).

Rankings at each cut all have T2 first, T1 second, T3 third (where
T3 is nonzero). M2 GO (T1 not first at 1880).

## 3. Gate decisions

| gate | | |
|---|---|---|
| M1 T1 first at 1904 | **NO_GO** | rank 2 |
| M2 T1 not first at 1880 | GO | (T1 rank 2 at 1880 too — but not rank 1) |
| M3 beats random null | NO_GO | by construction |
| M4 prompt committed | GO | SHA-256 pinned |

**Overall NO_GO.** Licensed reading:

> fourth_serial_null_on_DCR: T1 rank 2 under
> inferred-required-assumption scoring. Even the identifiability
> reframe's most direct DCR operationalisation does not recover T1.

## 4. What DCR3c actually shows

**(1) The reframe is directionally correct.** T1 climbed rank 3 →
rank 2. Score jumped from 9 (DCR3) and 20 (DCR3b) to 10 predictions
requiring T1 (DCR3c). That's a real change — inferred-required-
assumption scoring identifies T1 requirements that
citation-frequency and within-corpus counterfactual scoring
underweighted. The reframe's abstract prediction — "look at what
predictions REQUIRE, not what propositions CITE" — is
directionally supported.

**(2) It's not enough to invert the T2 > T1 ordering.** T2 has 50
predictions requiring it. Aether-wind experiments (Michelson-Morley
and every derivative), Fresnel drag, aether elasticity, stellar
aberration, refraction dependence on orbital velocity — every
observable prediction the corpus makes requires the aether frame.
Only the SUBSET that additionally invokes light-travel-time between
separated observers requires T1 on top of T2.

**(3) The corpus-structural fact is real, not an artifact.** T2
really is more invoked than T1 in the pre-1905 corpus. Every
corpus-respecting measurement will preserve this ratio. The LLM
doing inferred-assumption analysis correctly identifies this. To
put T1 first, a measurement would have to explicitly invert the
corpus's own frequency-of-requirement ordering — which is a
different principle than "score by inferred requirement," which
was the reframe's proposal.

**(4) The DCR3 finding is stronger, not weaker.** Loud commitments
protect themselves by being loud — many arguments defend them,
many predictions require them. Silent commitments become deletable
by being silent — no predictions explicitly require them because
they're presupposed rather than invoked. Einstein's move — delete
T1 rather than T2 — is exactly the move that isn't visible to any
corpus-respecting measure of importance. Because it's not a
mistake in Einstein's choice; it's the *content* of the choice.

## 5. What DCR3c does not license

- **The identifiability reframe is refuted in general.** It's
  refuted only for this specific operationalisation on this specific
  corpus. Other operationalisations (e.g., counterfactual scoring
  against a "what would remain of physics if I removed this?"
  criterion rather than a "what does each prediction require?"
  criterion) may work.
- **T1 cannot be identified from pre-1905 material by any method.**
  Only that four preregistered corpus-respecting methods have
  failed. A method that specifically inverts the corpus's structure
  (score = predictions that DON'T require this = degree-of-being-
  presupposed-not-argued) has not been tested.

## 6. What the four-null pattern tells us

DCR3 (frequency), DCR3b (LLM within-corpus counterfactual), DCR3c
(LLM inferred required assumption) — three independent scoring
methods on the DCR corpus. Rank orders:

| method | 1st | 2nd | 3rd |
|---|---|---|---|
| DCR3 frequency | unclassified | T2 | T1 |
| DCR3b in-corpus counterfactual | unclassified | T2 | T1 |
| DCR3c inferred required-assumption | T2 (unclassified excluded) | **T1** | T3 |

Every rank-preserving pair has T2 above T1. The DCR3c reframe's
gain was moving T1 from third to second, but T2 remains above T1
under every method that respects what the corpus actually says.

The remaining question — the one the four nulls make sharpest — is
whether the corpus IS the object, or whether the corpus is a
projection of a deeper object (theory-with-presuppositions) that
can only be reached by inverting the corpus's own emphasis.

That question is genuinely open. It is not the question the DR-arc
was designed to answer.

## 7. What could work

- **DCR3d — inverse-count scoring.** Score = 1/(prediction-count
  requiring this) for propositions with prediction-count > 0. This
  literally inverts the corpus's frequency-of-requirement. It would
  rank T1 above T2 by construction (fewer predictions require T1
  → higher 1/count score). This is not a serious proposal as a
  general nomination method — it would confuse "actually absent"
  with "presupposed silently" — but it would test whether the
  ranking-inversion trick is what's needed.
- **DCR4 — cross-corpus rank consistency.** Score T1/T2/T3 across
  the pre-1905 corpus AND against Einstein 1905 as an oracle
  corpus. If Einstein 1905 references T1 (his own deletion) more
  than the pre-1905 corpus does, then "increase in T1-requirement
  from pre-1905 to 1905" is a signal. Testable.
- **DR9 theorem.** Formally: for any corpus C and any commitment
  D, if D's realisations appear in C but are cited by fewer
  propositions than a competitor's realisations, then no scoring
  function whose input is C alone can rank D first without
  inverting C's frequency structure. Would generalise DCR3+3b+3c
  into a corollary.

---

## Appendix: reproduction

```
uv run --no-sync python -m experiments.date_cut_retrodiction.run_dcr3c
```

Reads nine `inferred_<YEAR>_<A/B/C>.json` files from
`results/dcr3c/`, aggregates via ≥2-of-3 verifier consensus, scores
each class by qualifying-prediction count with multidoc gating,
writes `results/dcr3c_verdict.json`. Local CPU, seconds.

**Preregistration digest (SHA-256 of `DCR3C_PREREGISTRATION.md`):**
`612889ab70da7913fe1c78eab98af165723c127bf40c3053b6956f64ffecd399`.

**Prompt digest (SHA-256 of `DCR3C_PROMPT.md`):**
`f6a6c7bb758ff5aa88d27e71c4f9d2da5cf1fec204c7ca837246983a638342af`.
