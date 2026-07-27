# DCR3b: LLM Counterfactual Dependence Also Puts T1 Third — And Now We Know Why

**Human director:** Jawaun Brown
**Producing agent:** Claude Code, directed
**Program:** Date-Cut Retrodiction — DCR3b (intervention-algebra reframe test)
**Status:** Overall **NO_GO**. M1 NO_GO (T1 rank 3 at 1904). M2 GO. M3 auto-NO_GO. M4 GO. The intervention-algebra reframe applied as LLM-based counterfactual dependence *within the corpus* also fails to reach T1. The failure is informative and consistent with DCR3: **whether you measure frequency or LLM-judged counterfactual weight, T2 (aether frame) always outscores T1 (simultaneity), because T2 is explicitly counterfactual-dependent in the corpus's own reasoning and T1 is not.**
**Date:** 2026-07-27

---

## Abstract

After DCR3 rejected the DR-arc's corpus-frequency nominator, the human
director proposed a reframe: the object of nomination lives in the
**intervention algebra**, not the corpus statistics. DCR3b tests the
DCR-arc version of that reframe: replace the DR3 scoring's `degree(p)`
(document count for content-equivalent propositions) with
`counterfactual_dependence(p)` — an LLM-judged score for "how many
other propositions in the same cut would become false or
underdetermined if this one were false." Everything else (target_v4
classification, multidoc aggregation, ground truth T1 class, random
null) identical to DCR3.

Three sandboxed Claude subagents per cut. 254 propositions at the 1904
target cut, 135 at 1897, 51 at 1880. Consensus by median.

**Result: NO_GO.** T1 still ranks third at 1904 under counterfactual
scoring:

| rank | class | LLM-counterfactual score | DCR3 (frequency) |
|---:|---|---:|---:|
| 1 | unclassified | 725 | 302 |
| 2 | T2_privileged_frame | 39 | 15 |
| **3** | **T1_absolute_simultaneity** | **20** | **9** |
| 4 | T3_local_time_artifice | 6 | 2 |

**The rank order is preserved from DCR3.** Both metrics agree: T2
(aether frame) is more counterfactually load-bearing in the corpus's
own reasoning than T1 (simultaneity). The LLM judgment isn't wrong —
it's *correct* about the corpus. Removing "the ether exists" cascades
through nearly every proposition. Removing "there's a common time t"
doesn't cascade through any proposition explicitly, because no
proposition in the corpus cites it as an explicit premise.

**That's the deep finding of DCR3b:** the intervention-algebra
reframe applied *within-the-corpus* fails for the same structural
reason DCR3 failed. Silent commitments are silent about their own
counterfactual weight too. The LLM asked "what depends on this?"
looks at the same corpus and finds the same answer: T2 has explicit
downstream consequences, T1 doesn't. Einstein's deletion was
available precisely because T1 had shed its explicit
counterfactual traces — no derivation *stated* that its validity
required absolute simultaneity, so no in-corpus counterfactual
measure can weight it correctly.

Third serial preregistered null on the DR-arc side (DCR3, DCR3b, and
implicit in DCR2a). The pattern: **every scoring method that operates
on the corpus's own visible content fails to reach the deletion.**
The reframe's abstract idea is right — the object is in counterfactual
dependence — but the operationalisation must be on the implicit
argument structure, not the explicit propositional content.

---

## 1. What was preregistered

`DCR3B_PREREGISTRATION.md` (2026-07-27, before `run_dcr3b.py` was
drafted, before subagent calls were spawned) fixed:

- **Scoring**: `score(p) = counterfactual_weight(p)`, LLM-judged.
- **Prompt** committed to `DCR3B_PROMPT.md`, SHA-256 pinned in the
  runner: `c5440337f71ebe54f5a941284831ea3c9bc47351d0a4045e0cc46229d97291b4`.
- **Verifiers**: three sandboxed Claude subagents per cut, blind to
  each other and to labels.
- **Consensus**: median across three.
- **Everything else identical to DCR3**: `target_v4` classification,
  `multidoc(min_docs=2)` aggregation, T1 ground truth, 10,000
  random-null permutations at seed 20260727.
- **Gates**: M1 (T1 first at 1904), M2 (T1 not first at 1880), M3
  (M1 beats random null at p < 0.01), M4 (prompt committed).

Nothing tuned after results.

## 2. Results

**1904 (target cut, 254 propositions):**

| rank | class | LLM-counterfactual score | members | documents |
|---:|---|---:|---:|---:|
| 1 | unclassified | 725 | 235 | 15 |
| 2 | T2_privileged_frame | 39 | 11 | 8 |
| 3 | **T1_absolute_simultaneity** | **20** | 7 | 5 |
| 4 | T3_local_time_artifice | 6 | 2 | 2 |

**1880 (deep placebo, 51 propositions):** T1 has 1 member from 1 doc
→ multidoc score 0. T1 rank position 2 in the raw output (alphabetic
tiebreak among 0-score classes), consistent with DCR3.

Verifier stability: the three LLM verifiers agreed strongly on which
propositions were high-dependence (ether-fills-space, propagation
finite velocity, ether-at-rest-relative-to-earth all scored 8-10 by
all three verifiers). No verifier disagreed by more than 3 points on
any load-bearing proposition. Consensus by median is stable.

## 3. Gate decisions

| gate | | |
|---|---|---|
| M1 T1 first at 1904 | **NO_GO** | rank 3 |
| M2 T1 not first at 1880 | GO | multidoc de-ranks singleton |
| M3 beats random null | NO_GO | by construction (M1 failed) |
| M4 prompt committed | GO | SHA-256 pinned |

**Overall NO_GO.**

Licensed reading (from the runner):

> counterfactual_scoring_still_missed_T1: even LLM-based
> counterfactual dependence puts T1 at rank 3. Third serial null on
> the intervention-algebra reframe on this arc.

## 4. Why the LLM scoring didn't rescue T1

The LLMs agreed with the frequency scorer that T2 outweighs T1. That
agreement is the finding.

Consider the top counterfactual-weight propositions at 1904, per
verifier consensus:

- Maxwell's `ethereal_medium_fills_space` (9–10)
- Michelson's `ether_at_rest_earth_moves` (7–9)
- Michelson's `ether_fills_all_space` (8–9)
- Larmor's `absolute_space_is_aether` (7–8)
- Maxwell's `propagation_finite_velocity` (7–8)

All of these are T2 (aether-frame) commitments. Every one is
explicitly cited by other propositions in the corpus — Michelson-
Morley's derivation depends on Maxwell's ether-fills-space; Lorentz's
1904 paper depends on Larmor's absolute-space-as-aether; every
null-result argument depends on the ether being at rest relative to
some frame. The LLMs correctly identified these as
counterfactual-load-bearing because they *are*.

Now consider the T1 propositions (5 documents, 7 members):

- Larmor's `common_time_across_two_systems`
- Lodge's `time_of_journey_perfectly_definite`
- Maxwell's `instant_across_whole_medium`
- Poincaré's `eclipse_perceived_simultaneously_over_earth`
- Poincaré's `regarded_as_simultaneous`
- Lorentz's `corresponding_instants`
- Poincaré's `same_causes_same_time`

Each is a genuine simultaneity commitment. But *no other proposition
in the corpus cites any of them as a premise*. Michelson-Morley
doesn't say "and by the way this requires absolute simultaneity."
It says "the time required for light to pass from one point to
another depends on the direction," treating "the time required" as
if it were a well-defined operational quantity. Larmor's derivation
of the transformation doesn't say "presupposing a common time t";
it introduces t as a variable and uses it. Poincaré 1898 discusses
simultaneity as a *philosophical* topic without ever citing it as
a premise for another physical claim in the corpus.

The counterfactual scorer measures dependence in the corpus's
*explicit* argument structure. T1 propositions live outside that
structure — they are presupposed globally rather than cited locally.
So the counterfactual scorer correctly reports low dependence.

**The intervention-algebra reframe's abstract claim is correct** —
"the object is in counterfactual dependence, not in frequency" — but
the operationalisation as LLM-scored within-corpus dependence is
constrained by the same structural feature that made T1 invisible in
the first place. To reach T1, you'd need counterfactual scoring on
the *implicit* argument structure — inferring "what would this
derivation require to be true even if the derivation doesn't say
so?" That's a much stronger inference task than DCR3b's LLM
performed, and it collides directly with DR7's soundness-completeness
gap on open-realisation g functions.

## 5. What DCR3b does not license

- **The reframe is refuted in general.** DCR3b tested one specific
  operationalisation of one specific claim on one specific corpus.
  Other operationalisations may work.
- **LLM counterfactual scoring never works.** It works fine here —
  on the propositions it can see, it correctly identifies
  counterfactual dependence. The failure is that the target commitment
  is systematically absent from the propositions it can see.
- **The DR-arc is unable to identify T1.** DCR3b only shows the
  intervention-algebra reframe, in its within-corpus form, doesn't
  reach it. A stronger operationalisation (implicit-argument-
  inference) remains untested.

## 6. Next work

- **DCR3c** — implicit-argument-inference scoring. For each derivation
  in the corpus (identified by a subagent), ask the subagent to list
  the premises the derivation *requires to be valid*, whether or not
  those premises are stated. Score each proposition by how often it
  appears in inferred premise sets. This is DR7's semantic-access-to-
  D condition: the LLM has to reason about what the derivation
  requires, not what it says. Predicted-in-principle by DR6/DR6e to
  work when Claude has real semantic access; predicted-in-principle
  by DR7 to have its own g-soundness issues.

- **Theorem DR9** — formalise the corpus-explicit vs implicit
  argument structure distinction: prove that any scoring function
  restricted to explicit premises has provably worse identification
  than one with access to inferred premises. Would generalise DCR3
  + DCR3b into a specific corollary.

---

## Appendix: reproduction

```
uv run --no-sync python -m experiments.date_cut_retrodiction.run_dcr3b
```

Reads nine `scores_<YEAR>_<A/B/C>.json` files from
`results/dcr3b/`, aggregates by median, applies same class
assignment (target_v4) and multidoc gating as DCR3, computes M-gates,
writes `results/dcr3b_verdict.json`. Local CPU, seconds.

**Preregistration digest (SHA-256 of `DCR3B_PREREGISTRATION.md`):**
`34ab193dc2766a1ac90314c47b7ce2868ebb927cfc1f7401154d669aee6801e1`.

**Prompt digest (SHA-256 of `DCR3B_PROMPT.md`):**
`c5440337f71ebe54f5a941284831ea3c9bc47351d0a4045e0cc46229d97291b4`.
