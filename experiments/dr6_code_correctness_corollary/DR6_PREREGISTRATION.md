# DR6 — The DR5 Wall on Code Correctness

**Package:** `experiments/dr6_code_correctness_corollary/`
**Predecessor:** DR5 (theorem paper), DR5b (verification corollaries §2)
**Human director:** Jawaun Brown
**Date:** 2026-07-27
**Written:** BEFORE snippets are designed or verifiers spawned.

## 0. The question DR6 is designed to answer

DR5 is a structural theorem stated in the DCR arc's language (propositions,
matchers, corpora). DR5b §2 argued it extends to code correctness. DR6 is
the empirical test: does the DR5 wall show up when the target commitment,
the "propositions," and the "matcher" are respectively a code-level
semantic property, code snippets, and a language-model verifier?

**Target commitment $D$:** *"This Python code implicitly assumes that all
`datetime` values are timezone-naive and represent UTC."* This is a real,
widespread source of production bugs; the ground truth of whether a
specific snippet embodies it is unambiguous for the author but genuinely
ambiguous for a surface-level verifier.

## 1. The setup

**Realisation set (5 snippets that embody $D$).** Each snippet is a short
Python fragment that operates on datetime values assuming they are naive
UTC. Surface forms will differ:

1. `datetime.utcnow()` — direct use of naive UTC
2. `.replace(tzinfo=None)` — explicit timezone stripping
3. `time.time()` → `fromtimestamp` conversion (naive result)
4. ISO parse without timezone info
5. `datetime.combine(date, time)` where the input time is UTC by
   convention

Each will be a self-contained function (5-15 lines) that performs
non-trivial logic on the datetime, so the verifier has surrounding
context — not a one-liner that would be trivially matchable.

**Placebo set (5 snippets that do NOT embody $D$).** Explicit
timezone-awareness in different surface forms:

1. `pytz.utc.localize()` — explicit UTC via pytz
2. `datetime.now(timezone.utc)` — explicit stdlib timezone
3. `arrow.utcnow()` — third-party timezone-aware library
4. Arithmetic-only, no datetime at all — semantic placebo
5. Explicit user-supplied timezone via `zoneinfo`

**Verifier.** Three sandboxed Claude subagents, blind to each other's
outputs and to this preregistration. Each is given the same prompt
describing $D$ and asked to score each of the 10 snippets on a 0-10
integer scale for how likely it is that the snippet embodies $D$. The
prompt names the commitment ($D$) explicitly — the DR5 wall is not that
verifiers are blind to $D$; it is that verifiers cannot distinguish $D$
from its specific surface realisations even when told what $D$ is.

## 2. Gates

Six gates, all must decide GO for the overall verdict to be GO.
The gates jointly test whether the DR5 wall shows up in this domain.

- **W1 verifier ran to completion.** All 3 verifiers produced scores for
  all 10 snippets, no format errors.
- **W2 realisation recall.** Consensus (median across 3 verifiers) scores
  the realisation set at ≥ 6 (positive signal on average).
- **W3 realisation variability.** The standard deviation of consensus
  scores across the 5 realisations is ≥ 1.5, i.e., the verifier scores
  different realisations of the *same* commitment differently. This is
  the load-bearing "wall visible" signal.
- **W4 placebo rejection.** Consensus scores the placebo set at ≤ 3
  (verifier correctly identifies most placebos as not embodying $D$).
- **W5 at least one placebo triggers.** At least one placebo receives
  consensus score ≥ 5. If every placebo scores 0-2, the verifier is doing
  clean semantic differentiation and the DR5 wall may not apply here.
  W5 firing indicates the projection failure mode DR5 §5 predicts.
- **W6 placebo test insufficient.** There exists at least one realisation
  whose consensus score is *lower* than at least one placebo's consensus
  score. This is the strongest possible instance of the wall: the
  placebo-vs-positive delta cannot distinguish projection from
  realisation-diversity because the two distributions overlap.

**Overall GO** = the DR5 wall is empirically confirmed in code correctness
under this specific setup.

## 3. Decision table

| W1 | W2 | W3 | W4 | W5 | W6 | reading |
|---|---|---|---|---|---|---|
| GO | GO | GO | GO | GO | GO | **Wall confirmed.** DR5 operates in code correctness verification exactly as in DCR1f: verifier variability + projection failures + overlap between placebos and realisations. |
| GO | GO | GO | GO | NO_GO | NO_GO | **No projection observed.** Verifier is doing clean semantic differentiation. DR5 theorem still holds but this specific verifier is above the wall for this specific $D$. |
| GO | GO | GO | GO | GO | NO_GO | **Projection without overlap.** Placebo firings exist but do not exceed any realisation's score. Wall partially confirmed. |
| GO | GO | NO_GO | GO | any | any | **Verifier saturated.** Scores are too uniform across realisations. Different $D$ or different snippet difficulty required. |
| GO | NO_GO | any | any | any | any | **Verifier missed $D$ entirely.** Prompt design failure; redesign and re-run. |
| NO_GO on W1 | | | | | | **Verifier crash.** Report and re-run with format-tolerant prompt. |

## 4. What DR6 does not test

- Whether other target commitments in code (e.g., "assumes 0-based
  indexing," "assumes thread safety") show the same wall. That is a
  broader empirical program.
- Whether other verifier architectures (LLM judges, symbolic executors,
  learned classifiers) show the same wall. Testing all is out of scope.
- Whether class-aware nomination (a la DCR2a) escapes the wall on code.
  That would be DR7.

## 5. Single-shot commitment

One design of realisations + placebos, one verifier prompt, three
subagents scoring in parallel, one aggregation, one verdict. Verdict at
`results/dr6_verdict.json`. No replay knobs. If W2 fails (verifier missed
the target entirely), redraft the prompt and re-run with the same
snippets — do not tune snippets to the verifier.
