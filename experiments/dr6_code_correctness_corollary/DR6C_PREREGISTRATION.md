# DR6c — Regex Verifier on the Same D

**Package:** `experiments/dr6_code_correctness_corollary/` (regex-verifier variant)
**Predecessor:** DR6 (LLM verifier, wall did not appear)
**Human director:** Jawaun Brown
**Date:** 2026-07-27
**Written:** BEFORE `regex_verifier.py` is drafted or executed.

## 0. The question DR6c answers

DR6 tested DR5's wall in code correctness verification with Claude
subagents as verifiers and found the wall did NOT appear. The sharpened
DR5 claim (DR6 §4) says the wall bites when (a) $D$ has no canonical
semantic form OR (b) the verifier cannot access whatever canonical form
exists. DR6 had (a) false (naive-UTC has canonical form) and (b) false
(Claude reasons semantically), so no wall.

**DR6c changes (b) alone.** Same target commitment $D$, same 10 snippets,
same gate scheme. Only the verifier changes: a regex-based scorer that
matches Python patterns (e.g., `datetime.utcnow\s*\(`, `tzinfo\s*=\s*None`).
This is proposition-independent in the strict DR5 sense — it scores each
snippet by surface feature counts alone, cannot reason about $D$
semantically.

The prediction: DR6c triggers the wall. If DR5's sharpened claim is
right, changing only condition (b) should flip the outcome from
DR6's "no wall" to DR6c's "wall present."

## 1. What is added

- `regex_verifier.py` — deterministic regex-based scorer producing 0–10
  integer scores per snippet using patterns hand-picked to match the
  surface forms of $D$'s canonical realisations. Deliberately narrow:
  each pattern catches one surface form and not others. **The regex
  patterns are drafted from the 5 realisation surface-form labels
  committed in DR6_PREREGISTRATION.md**, without looking at the actual
  code snippets. This mirrors DCR1f's discipline: the recogniser is
  drafted from the class definition, not from the extractor's output.
- `run_dr6c.py` — reuses DR6's gate suite (W1–W6, identical thresholds),
  producing an equivalent verdict artifact.

## 2. Gates (identical to DR6)

- **W1** verifier ran to completion.
- **W2** consensus median score across realisations ≥ 6.
- **W3** realisation stdev ≥ 1.5.
- **W4** placebo median ≤ 3.
- **W5** at least one placebo ≥ 5.
- **W6** min(realisation scores) < max(placebo scores).

Overall GO = wall present (which is what DR5 predicts for a
proposition-independent verifier).

## 3. Decision table

| W3 | W5 | W6 | reading |
|---|---|---|---|
| GO | GO | GO | **Wall confirmed on same D under regex verifier.** DR5's sharpened claim confirmed on the (a)-holds, (b)-fails corner. |
| NO_GO | any | any | **Regex verifier is unexpectedly uniform.** Snippets designed for LLM discrimination may be too clean for regex sensitivity — but this itself is a finding. |
| GO | GO | NO_GO | **Projection without overlap.** Regex fires on placebos but does not exceed any realisation's score; wall partially confirmed. |
| GO | NO_GO | NO_GO | **Regex too narrow.** Fires cleanly on realisations, cleanly rejects placebos. Same outcome as DR6 despite different verifier — would refute the sharpened claim. |

## 4. Single-shot commitment

The regex verifier is drafted based on the 5 realisation LABELS (surface
form descriptions) committed in DR6_PREREGISTRATION.md, not from reading
the actual snippet code. It is executed once. No replay knobs. If W3
fails (regex uniform), report and stop.

The point of drafting from labels is to mimic what a matcher designer
would build knowing only the class definition ("this D has these five
surface forms; here are the patterns for each"). A designer with access
to the actual snippets would over-fit trivially and DR6c's result would
be uninformative.
