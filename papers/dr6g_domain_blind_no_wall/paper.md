# DR6g: The Fully Domain-Blind Verifier Also Escaped — And Refines DR5 Again

**Human director:** Jawaun Brown
**Producing agent:** Claude Code, directed
**Program:** Deletion-Repair — DR6g
**Status:** Overall **NO_GO** on the "further degradation" gate suite. R6 actually scored *higher* (10 vs DR6f's 8). Realisation-placebo separation preserved. Prediction refuted — LLM verifier escapes the wall on a *domain-general* signal (implicit-vs-explicit code structure), not on D-specific semantic reasoning.
**Date:** 2026-07-27

---

## Abstract

DR6f showed partial wall degradation when $D$ was withheld from the
prompt but domain framing was kept. Extrapolating to a fully
domain-blind prompt, I predicted DR6g would see the wall substantially
return — the semantic-access escape route requires knowledge of $D$'s
domain, or so DR7's independent-semantic-access reasoning suggested.

**The prediction was wrong.** With a prompt that only asked *"how likely
does this code make any implicit assumption about how the world works
that isn't explicit in its imports, types, or comments,"* Claude
verifiers scored realisations at 8–10 (median 9.0) and placebos at 0–2
(median 2, max 2). Overlap gap = 6. R6 scored **10** (higher than
DR6f's 8). Wall did not reappear.

**What Claude was doing:** picking up a domain-general signal —
implicit-vs-explicit code structure — that correlates with the naive-UTC
target commitment because the target commitment IS an implicit
assumption. Code that uses `pytz.utc.localize()` reveals its assumption
explicitly. Code that uses `datetime.utcnow()` or `datetime(year=...,
...)` hides its assumption. The LLM can distinguish these without
knowing that the specific assumption is about UTC.

**The refined-refined DR5 claim:** semantic access to $D$ (DR5 condition
(b)) can be *proxied* by any signal that correlates with $D$'s surface
structure — including domain-general signals like "this code is
implicit rather than explicit." For naive-UTC, the implicit-vs-explicit
axis correlates strongly enough with $D$ that the verifier escapes the
wall via the proxy alone.

**Consequence.** The wall's bite depends not just on semantic access to
$D$ specifically, but on any accessible signal that discriminates
$D$-realisations from non-realisations. For code correctness targets
that align with implicit-vs-explicit structure — a large class — even
domain-blind LLM verifiers escape. For code correctness targets that
*don't* align with any domain-general signal (say, "this code has a
subtle deadlock" — no reliable implicit/explicit correlate), the wall
should still bite.

---

## 1. Setup

Same 11 snippets as DR6d/DR6e/DR6f. Three sandboxed Claude subagents.
Prompt strips all domain-specific framing:

> For each Python code snippet, score how likely it is that the code
> makes ANY implicit assumption about how the world works — a fact
> about the runtime environment, external systems, data conventions, or
> user context — that is not explicit in its imports, types, or
> comments.

No mention of datetime, timezone, UTC, or naive-UTC. Domain-blind.

## 2. Results

**Per-snippet consensus scores across three verifiers:**

| snippet | kind | DR6e (D given) | DR6f (D-adjacent) | **DR6g (blind)** |
|---|---|---:|---:|---:|
| R1_utcnow_direct | realisation | 10 | 10 | **9** |
| R2_replace_tzinfo_none | realisation | 9 | 10 | **9** |
| R3_time_fromtimestamp | realisation | 8 | 9 | **9** |
| R4_iso_parse_no_tz | realisation | 8 | 9 | **8** |
| R5_combine_utc_convention | realisation | 10 | 8 | **9** |
| R6_json_field_no_tz | realisation | 10 | 8 | **10** |
| P1_pytz_localize | placebo | 1 | 2 | **2** |
| P2_now_with_timezone_utc | placebo | 0 | 1 | **1** |
| P3_zoneinfo_user_tz | placebo | 0 | 1 | **2** |
| P4_no_datetime_arithmetic | placebo | 0 | 0 | **0** |
| P5_arrow_aware | placebo | 0 | 1 | **2** |

**Aggregate:**

- DR6g realisations: median 9.0, min 8, max 10.
- DR6g placebos: median 2, max 2.
- Overlap gap: **8 − 2 = 6** (same as DR6f).

## 3. Gate decisions

| gate | | |
|---|---|---|
| G1 median below DR6f | NO_GO | 9.0 = 9.0 |
| G2 gap below DR6f | NO_GO | 6 = 6 |
| G3 R6 below DR6f | NO_GO | 10 > 8 |
| G4 wall present direct | NO_GO | overlap gap +6 |

**Overall NO_GO.** Licensed reading:

> domain_blind_still_discriminates: Claude preserved discrimination
> even without domain framing. LLM verifier is doing more than semantic
> reasoning about D — possibly recognising implicit-vs-explicit style
> as a domain-independent signal.

## 4. What DR6g refines about DR5

DR7's independent-semantic-access requirement can be satisfied by
**proxy signals** that don't specifically encode $D$'s semantic content.

For naive-UTC (the DR6 target), the proxy is *implicit-vs-explicit code
structure*. Realisations of naive-UTC are, by definition, code that
does not carry explicit timezone information. Placebos are code that
does. Any verifier that can distinguish implicit from explicit code —
which any competent LLM can, and which is a domain-general skill —
escapes the wall on the naive-UTC target *even without knowing what
naive-UTC is*.

**The re-refined-refined DR5 (call this DR5*):**

> The wall bites when
>
> (a) the realisation set is open-ended at test time, AND
> (b) the verifier has no signal — semantic reasoning about $D$, or
>     domain-general proxy correlated with $D$'s realisation structure
>     — that discriminates realisations from non-realisations.

Condition (b) is now weaker than "verifier reasons semantically about
$D$." It is "verifier has *any* signal that separates realisations from
non-realisations, whether or not it knows $D$."

This weakening does not vacate the theorem. Many $D$'s have no
domain-general proxy — DCR1f's T1 (absolute simultaneity in 1900
physics) is exactly such a $D$, because implicit-vs-explicit is not a
distinction that separates T1-realisations from T2-realisations or from
non-realisations. The wall bites on T1 precisely because no proxy
signal works.

**Consequence: the wall's applicability depends on the $D$–proxy
correlation structure of the target commitment, not just on whether the
verifier "knows $D$."** DR5*'s condition (b) collapses to DR5's
condition (b) when no proxy exists; it is weaker when one does.

## 5. The updated gradient

Across DR6e/f/g, plotting R6 score against prompt specificity:

| prompt | R6 score | overlap gap |
|---|---:|---:|
| D-specified (DR6e) | 10 | 7 |
| D-adjacent domain (DR6f) | 8 | 6 |
| Fully domain-blind (DR6g) | 10 | 6 |

The gradient is **non-monotonic**. DR6f dips below DR6g because the
D-adjacent prompt is worse than either extreme: it primes datetime
attention without giving the specific commitment, so Claude might reach
for surface features that don't quite capture $D$ (e.g., "does this use
datetime?" — which fires on both realisations and placebos). The
domain-blind prompt is cleaner because Claude reverts to the
domain-general implicit-vs-explicit heuristic, which happens to
correlate strongly with $D$ on the DR6 snippet set.

**Practical consequence for verifier designers:** the prompt shape
matters non-monotonically. A specific description of $D$ works. A
domain-general question about implicit assumptions may also work — for
targets that align with the implicit-vs-explicit axis. A prompt that
sits in between, naming the domain but not the target, may work
*worse* than either extreme because it primes surface features that
don't discriminate.

## 6. What DR6g does not license

- **The wall is easy to escape for all code targets.** DR6g's target
  (naive-UTC) aligns with the implicit-vs-explicit axis by construction.
  A target that does NOT align — say, "this code assumes exclusive
  file access" — may not be catchable by domain-blind LLM verifiers,
  because both correct and incorrect implementations may be equally
  implicit or explicit about it.
- **The DR6 gradient is universal.** DR6e/f/g measured one target on
  one snippet set with one LLM. The non-monotonic dip may not
  reproduce for other targets or on other verifiers.
- **DR5's condition (a) is now optional.** Open enumeration still
  matters — DR6d showed regex hits the wall under open enumeration.
  DR6g shows the wall can be escaped even under open enumeration for
  targets with strong domain-general proxies.

## 7. Next follow-ups

- **DR6h — a target without a domain-general proxy.** Try "this code
  assumes exclusive file access" or "this code assumes the caller
  holds a lock." Predicted: fully domain-blind LLM verifier hits the
  wall because no implicit-vs-explicit correlate exists.
- **DR8 — quantitative gradient study.** Vary the prompt's D-
  specificity systematically; measure overlap gap; fit a curve.

Neither is required for the main DR5* claim. Both would fill in the
graded picture DR6f/g opened.

---

## Appendix: reproduction

```
uv run --no-sync python -m experiments.dr6_code_correctness_corollary.run_dr6g
```

Reads three `verifier_full_blind_A/B/C.json` files, aggregates by
median, applies the four G-gates, writes `results/dr6g_verdict.json`.
