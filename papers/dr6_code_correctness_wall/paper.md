# DR6: The Wall Does Not Appear on This Target — Which Sharpens DR5

**Human director:** Jawaun Brown
**Producing agent:** Claude Code, directed
**Program:** Deletion-Repair — DR6 (empirical code-correctness corollary)
**Status:** Overall **NO_GO** on the preregistered "wall appears" gate suite. Reading (from the runner): *"no_projection_observed: verifier scored placebos cleanly. DR5 still holds but this specific verifier is above the wall for this specific D."*
**Date:** 2026-07-27

---

## Abstract

DR5b §2 named code correctness as the tractable domain for empirically
testing DR5's verification wall outside the DCR arc. DR6 ran that test.
Target commitment $D$ = *"this Python code implicitly assumes that all
`datetime` values are timezone-naive and represent UTC"* — a real
production-bug source whose specific instances admit multiple surface
forms. Five realisations (each embodying $D$ in a distinct surface
register: `datetime.utcnow()`, `.replace(tzinfo=None)`,
`time.time()→fromtimestamp`, ISO parse without timezone,
`datetime.combine` by convention). Five placebos (each explicitly
timezone-aware or datetime-free). Three sandboxed Claude subagents,
blind to each other and to labels, scored each snippet 0–10.

**The wall did not appear.** Consensus scores: realisations 8–10 (median
9, stdev 1.0). Placebos 0–1 (median 0, max 1). No realisation scored
below any placebo. No placebo triggered projection above 1. Per the
preregistered decision table, this outcome licenses the reading

> no_projection_observed: verifier scored placebos cleanly. DR5 still
> holds but this specific verifier is above the wall for this specific D.

The result **does not refute DR5**. It sharpens its scope. DR5's wall
applies when the verifier is proposition-independent in the strict sense
(regex, keyword, weak classifier scoring each snippet from surface form
alone). LLM-based verifiers doing semantic reasoning about a target with
a **canonical semantic form** can operate above the wall. The
distinguishing property of the DCR arc's T1 that made DR5's wall
inescapable — that "absolute simultaneity in the pre-1905 corpus" has no
canonical semantic form usable by any verifier available in 1904 —
is precisely what naive-UTC in Python code lacks. Naive-UTC has a
canonical semantic form ("uses datetime values without timezone info,
interpreting them as UTC by convention"); Claude can reason about that
form and correctly classify all five realisations without pattern-
matching any specific surface register.

**The sharpened DR5 claim:** the wall bites when $D$ has no canonical
semantic form, **or** when the verifier cannot access whatever canonical
form exists. It does not bite when both are false. DR6 is the null
result that this distinction can be operationalised on a concrete
non-linguistic corpus, with three independent verifiers, under a
preregistered protocol. That refines the theorem in exactly the way a
first empirical corollary is supposed to.

---

## 1. What was preregistered

`DR6_PREREGISTRATION.md` (2026-07-27, before snippets were designed or
verifiers spawned) fixed:

- $D$ = *"This Python code implicitly assumes that all `datetime`
  values are timezone-naive and represent UTC."*
- Five realisations, five placebos, hand-designed and committed to
  `snippets.py`. Ground truth in the module; only IDs and code go to
  the verifiers.
- Three sandboxed Claude subagents, each producing integer scores 0–10
  for each of the 10 snippets. Consensus is the median across
  verifiers.
- **Six wall gates:** W1 completeness, W2 realisation recall (median ≥
  6), W3 realisation variability (stdev ≥ 1.5), W4 placebo rejection
  (median ≤ 3), W5 at least one placebo triggers (score ≥ 5), W6
  overlap between realisation and placebo distributions.
- Overall GO = the DR5 wall is confirmed on this target.
- Decision table binding **W1 GO + W2 GO + W3 GO + W4 GO + W5 NO_GO + W6
  NO_GO** to the reading *"no projection observed; DR5 still holds but
  this verifier is above the wall for this D."*

Nothing here was tuned after results came in.

## 2. Results

**Per-snippet consensus scores:**

| snippet | kind | surface form | verifiers | consensus |
|---|---|---|---|---|
| R1 | realisation | `datetime.utcnow()` direct use | 10 / 10 / 10 | **10** |
| R2 | realisation | `.replace(tzinfo=None)` | 9 / 9 / 9 | **9** |
| R3 | realisation | `time.time()` → `fromtimestamp` | 8 / 8 / 8 | **8** |
| R4 | realisation | ISO parse without timezone | 8 / 7 / 9 | **8** |
| R5 | realisation | `datetime.combine` by convention | 10 / 9 / 10 | **10** |
| P1 | placebo | `pytz.utc.localize()` | 1 / 1 / 1 | **1** |
| P2 | placebo | `datetime.now(timezone.utc)` | 0 / 0 / 0 | **0** |
| P3 | placebo | `zoneinfo` user-supplied timezone | 0 / 0 / 0 | **0** |
| P4 | placebo | no datetime, arithmetic only | 0 / 0 / 0 | **0** |
| P5 | placebo | `arrow` timezone-aware | 0 / 0 / 0 | **0** |

**Aggregate:**

- Realisations: median 9, stdev 1.0, min 8, max 10.
- Placebos: median 0, max 1.
- Overlap gap = min(realisation) − max(placebo) = 8 − 1 = **7**.

## 3. Gate decisions

| gate | | |
|---|---|---|
| W1 verifier completeness | GO | 30 / 30 scores returned |
| W2 realisation median ≥ 6 | GO | median 9 |
| W3 realisation stdev ≥ 1.5 | **NO_GO** | stdev 1.0 |
| W4 placebo median ≤ 3 | GO | median 0 |
| W5 at least one placebo ≥ 5 | **NO_GO** | max placebo 1 |
| W6 realisation-placebo overlap | **NO_GO** | overlap gap = 7 |

Overall **NO_GO**. Licensed reading:

> no_projection_observed: verifier scored placebos cleanly. DR5 still
> holds but this specific verifier is above the wall for this specific
> D. Try a harder D or a weaker verifier.

## 4. What this outcome means for DR5

DR5 stated the wall for **proposition-ranking nominators** — scoring
functions $N: P \to \mathbb{R}$ where $N(p)$ depends only on $p$. The
theorem's proof relies on $N$ having no semantic access to $D$: it
scores each proposition from surface features alone, so multi-realisation
commitments necessarily produce distinct scores that cannot be
aggregated without an external $g$.

**Claude subagents are not proposition-ranking nominators in that strict
sense.** They are given $D$ in natural language, they reason about
each snippet's semantic content, and they produce a score that reflects
whether the snippet semantically embodies $D$ regardless of surface form.
When $D$ has a **canonical semantic form** — as naive-UTC does ("uses
datetime values without timezone info, interpreting them as UTC by
convention") — Claude can apply that form directly and classify all
realisations correctly.

DCR1f's target T1 lacked this. Absolute simultaneity in the 1900
physics literature has no canonical semantic form usable by any 1904
verifier. Newton asserts it metaphysically; Larmor encodes it as
$t \to t - vx/c^2$; Maxwell presupposes it in field-theoretic
quantification; Poincaré treats it as convention. There is no single
"absolute simultaneity" semantic definition that all four registers
share. A verifier that catches one register misses the others because
there is no canonical form to reason about — only surface forms.

**The sharpened DR5 claim.** The wall bites when either

- (a) $D$ has no canonical semantic form, **or**
- (b) the verifier cannot access whatever canonical form exists (because
  it operates on surface features alone).

The wall does not bite when both are false. DR6 has (a) false (naive-UTC
has a canonical form) and (b) false (Claude can reason about it), so no
wall.

## 5. What DR6 does not license

- **The wall is inescapable in general.** DR5 remains the correct
  statement of the structural limit for proposition-ranking $N$.
- **All LLM verifiers escape the wall.** DR6 tested Claude Sonnet-family
  subagents at a specific prompt design; weaker verifiers, or the same
  verifier on targets without canonical form, would still hit it.
- **The wall never applies to code correctness.** DR6 tested one $D$.
  Code targets without canonical form — "this code has a subtle race
  condition," "this code is thread-safe under some memory model,"
  "this code embodies the intended business logic" — likely still hit
  the wall. DR6b would test one such target.

## 6. The comparison table with DCR1f

DCR1f and DR6 both preregistered the wall to appear. DCR1f's wall
appeared; DR6's did not. The difference is exactly what DR5's proof
attributes to the theorem's antecedent.

| property | DCR1f | DR6 |
|---|---|---|
| target $D$ | absolute simultaneity (T1) | naive-UTC datetime handling |
| target has canonical semantic form? | **no** — T1 is a spectrum of registers | **yes** — "no timezone info, UTC by convention" |
| verifier | regex matcher (target_v3, target_v4) | LLM (Claude subagents) with semantic reasoning |
| verifier proposition-independent? | **yes** — matcher scores each prop alone | **partially** — verifier reasons about $D$ semantically |
| held-out validation R2 accuracy | 32.5% | 100% (all realisations scored ≥ 8) |
| placebo firing (W5 / R5) | yes: Maxwell 1865 at 1880 cut | no: max placebo score 1 |
| overlap gap | −1 (placebo above one realisation) | +7 (all realisations above all placebos) |
| licensed reading | Reading B (projection or invalid placebo) | above the wall for this $D$ |

**The comparison is the finding.** Both experiments preregistered the
wall to appear. DCR1f found it; DR6 did not. DR5 predicts exactly this
distribution.

## 7. Next work

Two candidates:

- **DR6b — a harder $D$ in code correctness.** *"This code assumes
  thread safety under the acquire-release memory model."* Or: *"This
  code embodies the business rule that refunds must be issued in the
  original currency."* Both admit multiple surface realisations
  without a single canonical semantic form. DR5 predicts the wall
  should reappear.
- **DR6c — a weaker verifier on the same $D$.** Rerun DR6 with a
  regex-based verifier scoring each snippet by pattern presence
  alone. DR5 predicts the wall should appear because the verifier is
  now genuinely proposition-independent.

Both would sharpen DR5 further and are cheaper than more DCR arc work.

---

## Appendix: reproduction

```
uv run --no-sync python -m experiments.dr6_code_correctness_corollary.run_dr6
```

Reads three verifier JSON files from
`experiments/dr6_code_correctness_corollary/results/`, aggregates by
median, applies the six preregistered gates, writes
`results/dr6_verdict.json`.

**Verifier prompts (three independent Claude subagents):**
sandboxed to reading only
`experiments/dr6_code_correctness_corollary/snippets_for_verifier.json`,
given $D$ in natural language, asked for integer scores 0–10 with a
one-sentence reason per snippet.

**Preregistration digest (SHA-256 of `DR6_PREREGISTRATION.md`):**
`9f248b526c35c802fbe63e77ed54c821b712c7bfbb1c674f41e638ad70f18cfe`.
