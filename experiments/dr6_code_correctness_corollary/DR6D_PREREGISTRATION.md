# DR6d — Add a Novel Realisation, Predict the Wall

**Package:** `experiments/dr6_code_correctness_corollary/` (novel-realisation variant)
**Predecessor:** DR6c (regex verifier escaped the wall via complete enumeration)
**Human director:** Jawaun Brown
**Date:** 2026-07-27
**Written:** BEFORE the novel realisation is designed or scored.

## 0. What DR6d tests

DR6c showed the regex verifier does not hit the wall when it has one
pattern per realisation surface form drawn from a fixed 5-element
enumeration. The re-refined DR5 (DR6c §4) predicts the wall bites when
**both**

(a) realisation set is open-ended at test time (there is at least one
realisation the verifier-designer did not enumerate), **and**

(b) verifier cannot reach the unseen realisation via semantic reasoning.

DR6d flips (a) to open. Same target commitment $D$ (naive-UTC datetime
handling), same regex verifier as DR6c (`regex_verifier.py`, unchanged),
same 5 realisations + 5 placebos as DR6c, **plus one new realisation**
whose surface form was not represented in the DR6c label set.

The new realisation, `R6_json_field_no_tz`, parses a datetime from a
JSON field that lacks any timezone information. The `regex_verifier.py`
positive patterns target `datetime.utcnow`, `.replace(tzinfo=None)`,
`time.time()`, `strptime` with a specific format, and `datetime.combine`
— none of them catch parsing from a JSON dict field named e.g.
`"created_at"` via a helper that constructs a naive datetime.

## 1. Prediction

The regex verifier will produce:

- R1–R5: same scores as DR6c (2 each).
- **R6: 0 (regex misses the novel realisation).**
- P1–P5: 0 (unchanged, negative patterns still fire correctly on
  placebos containing pytz/timezone.utc/zoneinfo/arrow).

Under the DR6 gate suite (unchanged), R6 = 0 forces:

- **W6 (realisation-placebo overlap): GO** — min(realisations) = 0 ≤ max(placebos) = 0. Overlap gap = 0. Realisation R6 is scored at or below every placebo.

Under DR5's sharpened claim, this is the **wall present** outcome. The
strict gate verdict is still NO_GO on W2/W3/W5 (regex-scale scoring, no
projection because the verifier is deterministic and correctly rejects
placebos). But the load-bearing signal — a genuine realisation scoring
at the placebo level — is exactly the failure mode DR5 predicts.

## 2. Gates

Same six W-gates as DR6/DR6c. Additionally, a preregistered signal-check:

- **U6 novel realisation missed by regex.** `score_snippet(R6_code) = 0`.
  If this fails (regex somehow catches R6), the wall is not present for
  this specific novel surface form and DR6d licenses no claim.

## 3. Decision table

| U6 | W6 | reading |
|---|---|---|
| GO | GO | **Wall present on code correctness under open-ended realisation.** Direct empirical confirmation of DR5's structural prediction. |
| GO | NO_GO | **Regex missed R6 but W6 still failed** — impossible given the scoring rule (R6 = 0, placebos ≤ 0), so this row is a bug check. |
| NO_GO | any | **Novel realisation not novel enough.** The regex caught R6 despite the designer's intent. Redraft R6 with a surface form the patterns truly miss. |

## 4. Single-shot

One design of R6, one score, one verdict artifact at
`results/dr6d_verdict.json`. No replay knobs. R6 is drafted from a
surface form label ("parses a datetime from a JSON field that lacks any
timezone information") without looking at the regex patterns, so the
"the designer avoided the patterns" cheat is not possible.
