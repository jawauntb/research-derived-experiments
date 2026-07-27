# DR6f — Claude Without D in the Prompt

**Package:** `experiments/dr6_code_correctness_corollary/`
**Predecessor:** DR6e (Claude escaped the wall under open enumeration + D in prompt)
**Date:** 2026-07-27

## 0. Question

DR6e escaped the wall with Claude subagents on DR6d's 11 snippets.
DR6/DR6e prompts named $D$ explicitly ("this Python code implicitly
assumes datetime values are timezone-naive UTC"). DR7 Theorem 2 argues
$g$ must have independent semantic access to $D$; DR5's sharpened
condition (b) was "semantic reasoning about $D$."

DR6f flips one variable: **remove $D$ from the prompt.** Ask Claude to
score each snippet on how likely it "makes an implicit assumption
about how to handle date/time values that isn't explicit in its imports
or types," with no specification of which assumption. Prediction: Claude
can no longer score by "does this embody $D$" because it doesn't know
which $D$. Semantic escape route disabled; wall should reappear.

## 1. Setup

Same 11 snippets as DR6d/DR6e. Three sandboxed Claude subagents. Prompt
identical to DR6/DR6e except the $D$-specification line is replaced by
a $D$-blind version: *"score whether this code makes any implicit
assumption about date/time semantics."*

## 2. Gates

Same six W-gates. Plus:

- **F6**: consensus score on R6 falls below the DR6e level (specifically
  ≤ 6 rather than = 10). If Claude scores R6 low without $D$, semantic
  escape depends on $D$-knowledge.
- **F-realisations**: without $D$, realisation median should drop from
  DR6e's 9.5 toward the placebo distribution.

## 3. Prediction

Without $D$, Claude will score most snippets that touch datetime as
"makes assumptions" — including placebos that also make assumptions
(P1 pytz, P2 timezone.utc). Realisation-placebo separation should
degrade. R6 in particular may score lower because the assumption it
makes is not surfaced by any keyword.

**Predicted overall verdict:** wall present (W6 GO: overlap or reduced
gap). This confirms semantic escape requires $D$-knowledge.

If prediction fails (Claude still separates cleanly), then the LLM
verifier is doing something more than semantic reasoning about $D$ —
possibly stylistic pattern-matching that correlates with $D$ without
requiring it in the prompt.

## 4. Single-shot

Three verifiers, one aggregation, one verdict. No replay.
