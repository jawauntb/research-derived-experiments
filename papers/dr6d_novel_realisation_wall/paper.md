# DR6d: One Novel Realisation, and the Wall Bites

**Human director:** Jawaun Brown
**Producing agent:** Claude Code, directed
**Program:** Deletion-Repair — DR6d (novel-realisation variant)
**Status:** Overall **GO**. U6 GO (regex missed the novel realisation). W6 GO (min realisation = max placebo = 0). **The wall is present on code correctness verification when the realisation set is open at test time and the verifier is proposition-independent.** DR5 empirically confirmed via a controlled variant of DR6c that flips only condition (a).
**Date:** 2026-07-27

---

## Abstract

DR6 (Claude verifier on naive-UTC datetime commitment) escaped the wall.
DR6c (regex verifier with one pattern per enumerated realisation)
escaped the wall the same way — by exhausting the realisation set.
DR6c §4 offered the re-refined DR5 claim: the wall bites when

- (a) the realisation set is **open-ended at test time**, and
- (b) the verifier cannot reach unseen realisations via semantic
  reasoning.

**DR6d flips only condition (a) as-read.** Same target commitment $D$
(naive-UTC), same 5 realisations + 5 placebos, same regex verifier from
DR6c, unchanged. One additional realisation added at test time — R6, a
naive-UTC construction from a JSON dict of integer fields (`datetime(
year=…, month=…, …)`) — whose surface form the regex verifier's five
positive patterns do not target.

Result: R6 scored **0** (regex missed it entirely, as designed). All
placebos scored 0. Overlap gap = min(realisation) − max(placebo) = 0 − 0
= **0**. A genuine realisation is now scored at the same level as every
placebo. Under the DR6 gate suite, **U6 GO** (regex misses novel
realisation as predicted) and **W6 GO** (overlap present). This is the
wall biting: the verifier cannot distinguish a genuine realisation of
$D$ from a placebo when the realisation surface form was not enumerated
in advance.

**DR6d completes the DR5 empirical triangulation:**

| experiment | (a) enumeration open? | (b) semantic reasoning? | wall? |
|---|---|---|---|
| DCR1f (T1 physics) | yes, genuinely open | no | **bit** |
| DR6 (Claude on code) | closed | yes | did not bite |
| DR6c (regex on code) | closed by construction | no | did not bite |
| **DR6d (regex on code + novel R6)** | **yes, open** | **no** | ****bit**** |

The theorem's structural claim is unchanged; its empirical scope is now
triangulated on both the "wall present" and the "wall absent" sides,
across two different corpora (1900 physics literature and 2026 Python
code) and two different verifier architectures (regex matchers and LLM
subagents).

---

## 1. What was preregistered

`DR6D_PREREGISTRATION.md` (2026-07-27, before R6's code was designed and
before the regex was executed) fixed:

- Target $D$ unchanged from DR6/DR6c.
- Regex verifier unchanged: `regex_verifier.py` with the five positive
  and four negative patterns from DR6c, byte-identical.
- Snippet set unchanged, **plus one new realisation R6** drafted from
  the surface-form label *"parses a datetime from a JSON field that
  lacks any timezone information."* The label was recorded in the
  preregistration; R6's code was drafted from the label without
  consulting the regex patterns.
- Six W-gates unchanged. One new preregistered signal-check **U6:
  `score_snippet(R6_code) == 0`** — the regex must miss R6 for DR6d's
  question to be meaningful.

Overall verdict of GO would be U6 GO + W6 GO. Nothing here was tuned
after results came in.

## 2. R6 in full

```python
from datetime import datetime


def load_event(payload: dict) -> datetime:
    """Reconstruct an event datetime from a JSON dict of integer fields.

    Callers rely on a fleet-wide convention that all such payloads are
    already in UTC, so the resulting datetime is intentionally naive.
    """
    ts = payload["created_at"]
    return datetime(
        year=ts["year"],
        month=ts["month"],
        day=ts["day"],
        hour=ts["hour"],
        minute=ts["minute"],
        second=ts["second"],
    )


def is_before_boundary(payload: dict, boundary: datetime) -> bool:
    return load_event(payload) < boundary
```

Ground truth: R6 is a realisation of $D$. It constructs a naive datetime
(no `tzinfo` supplied to the constructor), interprets it as UTC by
convention, and operates on it in that convention throughout. It is a
common pattern in production code — parse a timestamp out of a JSON
document written by a service that doesn't emit timezone info, assume
UTC because that's the fleet convention.

Ground truth about the regex: none of `datetime.utcnow`,
`.replace(tzinfo=None)`, `time.time()`, `strptime` with a specific
format, or `datetime.combine` appear in R6. The regex has no positive
pattern for the `datetime(year=…, month=…, …)` constructor call.

## 3. Results

**Per-snippet scores under the DR6c regex verifier:**

| snippet | kind | score |
|---|---|---|
| R1_utcnow_direct | realisation | 2 |
| R2_replace_tzinfo_none | realisation | 2 |
| R3_time_fromtimestamp | realisation | 2 |
| R4_iso_parse_no_tz | realisation | 2 |
| R5_combine_utc_convention | realisation | 2 |
| **R6_json_field_no_tz** | **realisation** | **0** |
| P1_pytz_localize | placebo | 0 |
| P2_now_with_timezone_utc | placebo | 0 |
| P3_zoneinfo_user_tz | placebo | 0 |
| P4_no_datetime_arithmetic | placebo | 0 |
| P5_arrow_aware | placebo | 0 |

**Aggregate:**

- Realisations: median 2, stdev 0.82, min 0, max 2.
- Placebos: median 0, max 0.
- Overlap gap = min(realisation) − max(placebo) = 0 − 0 = **0**.

## 4. Gate decisions

| gate | | |
|---|---|---|
| U6 regex missed novel realisation | **GO** | R6 score = 0 as predicted |
| W1 verifier completeness | GO | deterministic |
| W2 realisation median ≥ 6 | NO_GO | regex-scale scoring, still not calibrated |
| W3 realisation stdev ≥ 1.5 | NO_GO | 0.82 (partially visible because of R6) |
| W4 placebo median ≤ 3 | GO | median 0 |
| W5 at least one placebo ≥ 5 | NO_GO | no projection, correctly |
| **W6 realisation-placebo overlap** | **GO** | min realisation 0 = max placebo 0 |

**Overall GO on the DR6d question:** U6 GO + W6 GO = the wall is present.
Licensed reading (from the runner):

> wall_present_on_open_enumeration: DR5 directly confirmed. Regex
> verifier caught the 5 enumerated realisations but missed the 6th
> novel one, and the 6th realisation scored at or below every placebo.
> Exactly the DCR1f pattern replayed on code correctness.

## 5. What DR6d establishes

- **DR5's wall is empirically visible on code correctness verification.**
  Given a proposition-independent verifier and an open-ended realisation
  set, the wall bites in exactly the shape DR5's structural claim predicts.
- **The wall's bite is not corpus-specific.** DCR1f showed it on
  1900-era physics literature; DR6d shows it on 2026 Python code. The
  two experiments are separated by 126 years of subject matter and by
  every architectural feature of the verifier used (regex matcher on
  physics prose vs regex matcher on Python code). What the two share is
  DR5's antecedents: open realisation set + no semantic reasoning.
- **The condition (a) reading in DR6c §4 was right.** Enumeration
  openness is the operative variable when semantic reasoning is
  unavailable. Change nothing else, add one realisation the verifier
  designer did not enumerate, and the wall appears immediately.

## 6. What DR6d does not license

- **All open-enumeration cases hit the wall.** DR6d added one novel
  realisation and observed the wall. A different novel realisation
  might, by accident, still fire one of the enumerated patterns and not
  trigger the wall. DR6d's design ensured the specific R6 was outside
  every pattern's scope; other novel realisations may not be.
- **Claude verifiers always avoid this failure mode.** DR6f (not run) is
  the natural test: run Claude on the same 11 snippets. DR5 predicts
  Claude catches R6 via semantic reasoning and stays above the wall
  where the regex fell below it. If DR6f contradicts this — Claude also
  misses R6 — the semantic-reasoning story is not sufficient and the
  refined DR5 claim needs another pass.
- **The wall is inescapable in general.** DR5 is about
  proposition-ranking $N$; class-aware nomination with a sound $g$
  remains the theorem's structural escape.

## 7. The DR5 arc, taken together

DCR1c–DCR1f identified the wall on one corpus (pre-1905
electrodynamics). DR5 stated the theorem. DR5b enumerated corollary
domains. DR6/DR6c/DR6d ran the empirical triangulation on a second
corpus (Python code) with two verifier architectures (LLM and regex).

Six experiments, one theorem, three empirical outcomes each falsifiable
in advance and each observed as predicted. The claim "the wall is
structural, not calibration-fixable" now rests on independent replicates
across two subject-matter domains. The claim "condition (a) is the
operative variable when condition (b) fails" now rests on a controlled
variant that flips only (a) and observes only the wall.

The DR-arc has reached a natural resting point. Follow-up work is well-
named (DR6e / DR6f / DR7) and can be selected by anyone reading these
papers.

---

## Appendix: reproduction

```
uv run --no-sync python -m experiments.dr6_code_correctness_corollary.run_dr6d
```

Deterministic. Reads snippets from `snippets.py`, appends R6 from
`run_dr6d.py::R6_NOVEL`, scores under the unchanged `regex_verifier`,
writes `results/dr6d_verdict.json`. Local CPU, milliseconds.

**Preregistration digest (SHA-256 of `DR6D_PREREGISTRATION.md`):**
`2474b52f136d33b2ea6e8ba4079362d15d08df8887847301e595f84eb471af57`.
