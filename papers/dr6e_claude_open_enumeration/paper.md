# DR6e: Claude Caught the Novel Realisation — Full 2×2 Confirmed

**Human director:** Jawaun Brown
**Producing agent:** Claude Code, directed
**Program:** Deletion-Repair — DR6e
**Status:** Overall **GO**. U6e GO (R6 consensus 10/10), W6 NO_GO (overlap gap +7). **Wall absent under open enumeration with semantic reasoning.** Completes the 2×2 truth table on DR5's sharpened antecedent.
**Date:** 2026-07-27

---

## Abstract

DR6d hit the wall using a regex verifier on an extended snippet set with
one novel realisation R6. Sharpened DR5 predicted a Claude verifier on
the same 11 snippets would NOT hit the wall, because condition (b)
(semantic reasoning) escapes even when condition (a) (open enumeration)
fails. DR6e ran that test.

**Result: three Claude verifiers all scored R6 = 10.** R6 was caught
semantically at the same strength as R1 and R5 (also 10). Realisation
distribution [10, 9, 8, 8, 10, 10], placebo distribution [1, 0, 0, 0, 0].
Overlap gap +7. **U6e GO. W6 NO_GO. Wall absent.**

**The full 2×2 truth table on the sharpened DR5 antecedent:**

| (a) enumeration open at test time? | (b) semantic reasoning available? | wall? |
|---|---|---|
| yes | no | **YES** (DCR1f physics, DR6d code) |
| yes | yes | NO (**DR6e**) |
| no | no | NO (DR6c) |
| no | yes | NO (DR6) |

The wall bites if and only if both antecedents fail. This is the theorem
operating exactly as DR5 claims, empirically confirmed on all four
corners across two subject-matter domains and two verifier architectures.

---

## 1. Setup

Same 11 snippets as DR6d (5 original realisations + 5 placebos + R6
novel). Three sandboxed Claude subagents, blind to each other and to
labels. Prompt byte-identical to DR6 except for pointing to the extended
snippet file. Consensus median.

## 2. Results

**Per-snippet Claude consensus scores:**

| snippet | kind | per verifier | consensus |
|---|---|---|---|
| R1_utcnow_direct | realisation | 10 / 10 / 10 | **10** |
| R2_replace_tzinfo_none | realisation | 9 / 9 / 9 | **9** |
| R3_time_fromtimestamp | realisation | 8 / 8 / 8 | **8** |
| R4_iso_parse_no_tz | realisation | 9 / 8 / 7 | **8** |
| R5_combine_utc_convention | realisation | 10 / 10 / 10 | **10** |
| **R6_json_field_no_tz** | **realisation** | **10 / 10 / 10** | ****10**** |
| P1_pytz_localize | placebo | 1 / 1 / 1 | **1** |
| P2_now_with_timezone_utc | placebo | 0 / 0 / 0 | **0** |
| P3_zoneinfo_user_tz | placebo | 0 / 0 / 0 | **0** |
| P4_no_datetime_arithmetic | placebo | 0 / 0 / 0 | **0** |
| P5_arrow_aware | placebo | 0 / 0 / 0 | **0** |

**Aggregate:**

- All 6 realisations (including R6): median 9.5, stdev 0.98, min 8, max 10.
- All 5 placebos: median 0, max 1.
- Overlap gap = min(realisation) − max(placebo) = 8 − 1 = **+7**.

## 3. Gate decisions

| gate | | |
|---|---|---|
| U6e R6 caught semantically | **GO** | consensus 10, threshold 6 |
| W1 verifier completeness | GO | |
| W2 realisation median ≥ 6 | GO | median 9.5 |
| W3 realisation stdev ≥ 1.5 | NO_GO (as expected) | 0.98 — realisations are uniform-good |
| W4 placebo median ≤ 3 | GO | median 0 |
| W5 placebo trigger | NO_GO | max placebo 1, no projection |
| W6 realisation-placebo overlap | NO_GO | gap +7 |

**Overall GO** on the DR6e question: U6e GO (semantic catch) + W6 NO_GO
(no overlap) = wall absent under open enumeration with semantic
reasoning. Licensed reading:

> wall_absent_under_open_enumeration_with_semantic_reasoning: sharpened
> DR5 confirmed on the (a)-open, (b)-satisfied corner. Claude caught R6
> semantically. Escape via condition (b) is real.

## 4. What DR6e establishes

- **Semantic reasoning does escape the wall under open enumeration.**
  R6's surface form was not represented in the DR6c regex label set;
  the regex verifier scored R6 = 0 (DR6d wall). Claude scored R6 = 10 by
  every verifier. The mechanism is semantic reasoning about $D$:
  Claude read the code, understood that `datetime(year=..., month=...,
  ...)` constructs a naive datetime interpreted by convention as UTC,
  and matched that against $D$'s natural-language description.
- **The 2×2 truth table on DR5's sharpened antecedent is now complete.**
  All four corners empirically observed. Wall bites iff (a) yes AND (b)
  no — exactly what the theorem's antecedent specifies.
- **Cross-corpus, cross-architecture agreement.** DCR1f (1900 physics,
  regex matcher) and DR6d (2026 Python, regex matcher) both hit the
  wall at the same corner. DR6 (Python, Claude), DR6c (Python, regex
  enum-closed), DR6e (Python, Claude enum-open) all escaped at the
  respective corners DR5 predicted.

## 5. What DR6e does not license

- **All LLM verifiers escape under all conditions.** Weaker LLMs may
  not reach R6 semantically. A different novel realisation (say,
  binary-encoded UTC timestamp deserialisation) may not be as
  recognisable to Claude.
- **DR5 is inescapable in the (a)-yes, (b)-no corner.** The theorem
  remains a structural claim; the empirical corner just confirms it.
  Class-aware nomination with a sound $g$ remains DR5's structural
  escape.
- **DR6f is now decided.** DR6f (Claude WITHOUT $D$ in the prompt) is
  a different experiment. Withholding $D$ may or may not preserve
  semantic reasoning; DR6f would test.

## 6. Next follow-ups

- **DR6f** — Claude verifier where $D$ is not stated in the prompt.
  Predicted: the wall reappears because the verifier cannot access
  the canonical form without knowing $D$.
- **DR7** — grouping-function correctness. If class-aware nomination
  requires an external $g$, what soundness/completeness properties
  must $g$ have to be trusted for $D$?
- **DCR2b** — multi-document coverage aggregation on the DCR corpus,
  now that DCR2a's cardinality-based rules were shown insufficient at
  the placebo.

---

## Appendix: reproduction

```
uv run --no-sync python -m experiments.dr6_code_correctness_corollary.run_dr6e
```

Reads three verifier JSON files (`verifier_ext_A/B/C.json`), aggregates
by median, applies the six W-gates plus U6e, writes
`results/dr6e_verdict.json`.

**Preregistration digest (SHA-256 of `DR6E_PREREGISTRATION.md`):**
`4a7e7720fd629a6eb85883e33e43bb80dd16038e4fb9d2c0a7e5a5645fb96402`.
