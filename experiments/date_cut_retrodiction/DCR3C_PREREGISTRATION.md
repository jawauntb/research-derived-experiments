# DCR3c — Identifiability Reframe: Score By Inferred Required Assumptions

**Package:** `experiments/date_cut_retrodiction/`
**Predecessors:** DCR3 (frequency), DCR3b (LLM within-corpus counterfactual). Both NO_GO.
**Date:** 2026-07-27
**Written:** BEFORE `nominate_dcr3c.py` is drafted, BEFORE subagent
inference calls are spawned.

## 0. What DCR3c tests

DCR3 and DCR3b both score by quantities visible in the corpus's
**explicit citation structure**. Both put T1 rank 3. The identifiability
reframe (human director, 2026-07-27) proposes the target commitment
is identifiable at the level of the corpus's **prediction structure**
— what each derived experimental prediction *requires* to be a valid
inference, whether or not the requirement is stated.

DCR3c operationalises the reframe:

- LLM identifies which propositions state empirical predictions
- LLM lists what each prediction *requires* to be valid (implicit
  inference, not explicit citation)
- Score each target-class by counting predictions whose required-
  assumption list invokes that class

Same target_v4 class definitions, same multidoc gating, same
random-null baseline as DCR3/DCR3b. Only the scoring signal changes:
from citation-frequency (DCR3) or within-corpus counterfactual
(DCR3b) to **inferred-required-assumption count** (DCR3c).

## 1. Setup

- **Corpus:** DCR1e consensus at each cut (unchanged from DCR3/DCR3b).
- **Class definitions:** T1 = commitments invoking common
  time/simultaneity across separated observers; T2 = commitments
  invoking a preferred rest frame / stationary aether; T3 = local
  time as artifice. Verbal definitions committed in the prompt
  (below); no `target_v4` regex used here — the LLM applies the
  categorical rubric directly per required-assumption.
- **Verifiers:** three sandboxed Claude subagents per cut. Each
  receives the full proposition list at the cut, identifies
  predictions, infers required assumptions, tags each requirement
  as T1/T2/T3/OTHER.
- **Consensus:** class score = median across three verifiers.
- **Multidoc gating:** class score = 0 if predictions requiring
  that class come from fewer than 2 distinct documents.
- **Random-null baseline:** 10,000 permutations of class keys.

Prompt SHA-256 committed and pinned in the runner.

## 2. Gates

- **M1** — T1 class first at 1904 under inferred-required-assumption
  scoring.
- **M2** — T1 class not first at 1880 (placebo).
- **M3** — M1 result beats random null at p < 0.01.
- **M4** — prompt SHA-256 committed and pinned.

Overall **GO** iff all four M-gates GO.

## 3. Decision table

| M1 | M2 | M3 | reading |
|---|---|---|---|
| GO | GO | GO | **Identifiability reframe empirically supported on DCR.** Inferred-required-assumption scoring identifies T1 first where citation-frequency (DCR3) and within-corpus counterfactual (DCR3b) put T1 third. Direct test of the reframe: the LLM's implicit-inference step recovers what explicit measures miss. Extends DR-arc under new scoring primitive. |
| NO_GO (T1 still not first) | any | any | **Fourth serial null on DCR side.** Inferred-required-assumption scoring ALSO does not recover T1. Combined with DCR3, DCR3b, and Constraint-Swap reanalysis, four serial preregistered nulls. Identifiability reframe fails under its most direct DCR operationalisation. |
| GO | NO_GO | any | **Placebo leak.** The LLM's inference process projects T1 as universal even at the 1880 cut where the relevant predictions don't exist. Instrument failure, not reframe evidence. |
| GO | GO | NO_GO | **Chance ranking** (T1 happens to score first but null probability high). Report as null. |

## 4. What DCR3c does not test

- The identifiability reframe as a general primitive across all
  domains. DCR3c tests one specific operationalisation on the DCR
  corpus.
- The Constraint-Swap side of the identifiability reframe. That
  would require a different measurement pipeline on the frozen
  32-seed data or a fresh larger-N run.
- Whether the LLM's inference is *correct* about what each
  prediction requires. The LLM might infer wrong assumptions and
  still rank T1 first, or infer right ones and rank T1 second. The
  gate checks ranking, not inference accuracy directly.

## 5. Single-shot

One prompt design, one round of subagent calls per cut, one scoring
pass, one verdict. No replay knobs. If M1 fails, **do not reword the
prompt to raise T1's rank.** Report NO_GO. Fourth null in the
sequence would tell us more about the reframe than a tuned GO would.
