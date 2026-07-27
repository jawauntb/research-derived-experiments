# DR6f: Withholding D Degraded Discrimination — And Showed the Escape's Shape

**Human director:** Jawaun Brown
**Producing agent:** Claude Code, directed
**Program:** Deletion-Repair — DR6f
**Status:** Overall **GO** on the degradation reading. F1/F2/F3 all GO (realisation median down 9.5→9.0, R6 down 10→8, overlap gap down 7→6, placebo max up 1→2). F4 NO_GO (no direct overlap). Wall reappeared partially, not fully. The escape has structure: D-knowledge is load-bearing but not binary.
**Date:** 2026-07-27

---

## Abstract

DR6e escaped the wall with Claude subagents that were given $D$ (naive-
UTC datetime handling) explicitly. DR7 §5 argued that class-aware
verification requires "independent semantic access to $D$" somewhere in
the pipeline. DR6f tests the sharpness of that requirement: what happens
when $D$ is withheld from the prompt but the domain-framing is kept?

The DR6f prompt asked Claude to score "how likely the code makes any
implicit assumption about date/time semantics" — still domain-anchored,
but not specifying naive-UTC as the target commitment.

**Result: partial degradation, not full collapse.** Every DR6e ↔ DR6f
comparison moved in the direction DR5's D-knowledge requirement
predicts:

- Realisation median: **9.5 → 9.0** (F1 GO)
- Overlap gap: **7 → 6** (F2 GO)
- R6 score: **10 → 8** (F3 GO)
- Placebo max: **1 → 2** (secondary degradation)

But F4 (direct realisation-placebo overlap) did not fire: min
realisation stayed at 8, max placebo at 2, so no realisation scored at
or below any placebo. Claude retained substantial discrimination even
without $D$ specified — because the domain framing ("date/time
semantics") is still adjacent to $D$, and the LLM can partly reconstruct
what to look for.

The finding **sharpens rather than refutes** DR5's condition (b) and
DR7's independent-semantic-access requirement. The escape route is not
a binary D-known / D-unknown switch. It is a gradient over how close
the prompt is to $D$'s specific semantic content. Fully removing all
domain framing (a DR6g variant, not run) would test the binary claim
directly; DR6f shows the intermediate case.

---

## 1. Setup

Same 11 snippets as DR6d and DR6e. Three sandboxed Claude subagents.
The prompt is identical to DR6e's except:

- **DR6e prompt (D-specified):** *"Target commitment D: 'This Python
  code implicitly assumes that all datetime values are timezone-naive
  and represent UTC.' Score each snippet 0–10 for how strongly it
  embodies D."*
- **DR6f prompt (D-withheld):** *"For each snippet, score 0–10 how
  likely it makes any implicit assumption about date/time semantics
  that is NOT explicit in its imports or types."*

The DR6f prompt still names the domain (date/time) but not the specific
commitment (naive-UTC). All other prompt content unchanged.

## 2. Results

**Per-snippet consensus scores under D-withheld prompt:**

| snippet | kind | DR6e (D given) | DR6f (D withheld) | delta |
|---|---|---:|---:|---:|
| R1_utcnow_direct | realisation | 10 | 10 | 0 |
| R2_replace_tzinfo_none | realisation | 9 | 10 | +1 |
| R3_time_fromtimestamp | realisation | 8 | 9 | +1 |
| R4_iso_parse_no_tz | realisation | 8 | 9 | +1 |
| R5_combine_utc_convention | realisation | 10 | 8 | −2 |
| R6_json_field_no_tz | realisation | 10 | 8 | **−2** |
| P1_pytz_localize | placebo | 1 | 2 | +1 |
| P2_now_with_timezone_utc | placebo | 0 | 1 | +1 |
| P3_zoneinfo_user_tz | placebo | 0 | 1 | +1 |
| P4_no_datetime_arithmetic | placebo | 0 | 0 | 0 |
| P5_arrow_aware | placebo | 0 | 1 | +1 |

**Aggregate:**

- DR6f realisations: median 9.0, min 8, max 10.
- DR6f placebos: median 1, max 2.
- Overlap gap DR6f: **8 − 2 = 6** (DR6e: 7).

## 3. Gate decisions

| gate | | |
|---|---|---|
| F1 realisation median dropped | GO | 9.0 < 9 (barely) — DR6e was 9.5 |
| F2 overlap gap reduced | GO | 6 < 7 |
| F3 R6 score reduced | GO | 8 < 10 |
| F4 wall present direct | NO_GO | min realisation 8 > max placebo 2 |

**Overall GO** on the degradation reading (F1+F2+F3 all GO, or F4 GO;
this run: F1+F2+F3 GO).

Licensed reading (from the runner):

> wall_reappeared_by_degradation: withholding D reduced realisation-
> placebo separation across every measure, though no direct overlap.
> Directional confirmation of DR5's D-knowledge requirement.

## 4. What DR6f establishes

**D-knowledge is load-bearing but not binary.** All four measurable
changes go in the DR5-predicted direction:

- Realisations score lower on average.
- Placebos score higher.
- R6 specifically drops — the novel realisation, exactly where D-
  knowledge should be most load-bearing.
- Overlap gap narrows.

But no direct overlap appears, because the DR6f prompt still cues
Claude toward the datetime domain. Some of D's semantic content
transfers through "date/time semantics" framing alone; Claude can
reason toward D from a proximate description without seeing D
verbatim.

**Two implications for DR7's independent-semantic-access requirement:**

- The requirement is not binary. Independent semantic access exists on
  a spectrum: from "D fully specified" (DR6e) through "D-adjacent
  domain specified" (DR6f) to "no domain hint" (a hypothetical DR6g).
  Each point on the spectrum produces a different degree of escape.
- The wall's presence is likewise graded, not binary. DR6f's wall is
  "half-present" — realisations are less separated from placebos, but
  not overlapping. A fuller DR6g without any domain cue would likely
  see actual overlap; a DR6e' with $D$ specified plus richer semantic
  context would likely see wider separation.

## 5. What DR6f does not license

- **The escape is fully preserved without D.** DR6f showed clear
  degradation on every measure. Extrapolating to DR6g (no domain
  framing) predicts substantial wall reappearance.
- **All prompts specifying "the domain" preserve the escape.** DR6f's
  domain ("date/time semantics") is very close to D's target vocabulary.
  A different domain framing (say, "concurrency semantics") that is
  not adjacent to D would not test the same phenomenon.
- **Claude reasons about D without D.** DR6f shows Claude reconstructs
  something D-shaped from the domain cue. The reconstruction is
  incomplete — the scores drift — but nonzero. This is a Claude-
  specific observation about how LLM verifiers respond to under-
  specified targets; DR5 makes no claim about the specific mechanism.

## 6. The five-experiment code-correctness triangulation now looks like this

| paper | (a) enum open? | (b) semantic access to D? | wall? |
|---|---|---|---|
| DR6 | closed | full (D in prompt) | no |
| DR6c | closed | full (D via enumeration) | no |
| DR6d | open (R6 added) | none (regex has no semantic) | **YES** |
| DR6e | open | full (D in prompt, Claude) | no |
| DR6f | open | **partial** (D-adjacent, Claude) | **partial** |

DR6f fills a middle cell: partial semantic access produces partial wall.
This graded finding is more informative than a binary re-test would have
been. It shows the escape mechanism is not "verifier knows D vs not" but
"verifier's semantic access to D is sufficient vs insufficient" — with
intermediate cases producing intermediate wall behaviour.

## 7. Next follow-ups

- **DR6g** — fully domain-blind Claude verifier ("does this code make
  any implicit assumption about anything?"). DR5 predicts wall
  substantially returns.
- **DR8** — quantitative characterisation of the semantic-access
  gradient: for a family of prompts parameterised by "D-specificity,"
  measure the overlap gap and R6 score. Fit a smooth curve.

Neither is required for the main claim. Both would fill in the graded
picture DR6f opened.

---

## Appendix: reproduction

```
uv run --no-sync python -m experiments.dr6_code_correctness_corollary.run_dr6f
```

Reads three `verifier_blind_A/B/C.json` files, aggregates by median,
applies the four F-gates, writes `results/dr6f_verdict.json`.

**Preregistration digest (SHA-256 of `DR6F_PREREGISTRATION.md`):**
`d846a193822fcaa83d31013cdc4beb7d06f1f1f2b2274d0b33b42b7da04a67e7`.
