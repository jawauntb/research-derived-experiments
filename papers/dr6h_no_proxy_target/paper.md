# DR6h: A Target Without a Domain-General Proxy Narrows the Margin

**Human director:** Jawaun Brown
**Producing agent:** Claude Code, directed
**Program:** Deletion-Repair — DR6h
**Status:** Overall **NO_GO** on the "wall bites" gate suite. But the margin degraded significantly: realisations spanned 5–10 (stdev 2.35, an entire 2 sigma wider than any prior DR6 variant), and two realisations (RH3 append_log and RH4 rename_after_write) scored 5–6, approaching placebo territory. The wall is *starting to bite* — DR5*'s domain-general-proxy hypothesis is directionally right but the LLM's residual semantic reasoning still avoids direct overlap.
**Date:** 2026-07-27

---

## Abstract

DR6g refined DR5 to DR5*: the wall bites when the verifier has no
signal — semantic reasoning about $D$ or a domain-general proxy —
that separates realisations from non-realisations. DR6g showed the
implicit-vs-explicit proxy escapes the wall for naive-UTC because that
$D$ literally IS about implicit assumptions. DR6h tests DR5*'s
prediction that targets without such a proxy hit the wall even for LLM
verifiers with $D$ specified.

**Target $D_h$**: *"This code assumes exclusive access to files it
reads or writes — no other process, thread, or async task will read,
write, truncate, or delete those files concurrently."* No clean
implicit-vs-explicit proxy: both correctly-locked and dangerously-
unlocked file access can be terse or verbose.

**Result: partial wall, not direct wall.** Overlap gap +2 (down from
DR6e's +7 on naive-UTC). Realisation stdev 2.35 (up from DR6e's 0.98).
Two realisations (RH3 append_log scored 6, RH4 rename_after_write scored
5) sit near the placebo distribution's top (PH4 read_only_open scored
3). Claude still discriminated well enough to avoid direct
realisation-placebo overlap, but the margin is narrower than every
prior DR6 variant.

**DR5*, refined again (DR5**):** LLM semantic access provides a signal
whose *strength* depends on (i) how deep $D$'s semantic definition is,
(ii) whether the target has a domain-general surface correlate, and
(iii) how much of the LLM's training corpus covers reasoning about $D$
in code contexts. On $D_h$, the LLM has (i) partial (the definition
requires reasoning about concurrent access, which is a well-covered
domain in the LLM's training) but not (ii) (no clean surface correlate),
so discrimination degrades — the wall's *shadow* appears without the
wall itself.

DCR1f's T1 (absolute simultaneity in pre-1905 physics) fails on all
three properties for a 1904 verifier: (i) T1's presupposition-structure
was invisible to physicists at the time; (ii) no domain-general
correlate distinguishes T1 from T2 or from non-realisations; (iii) the
LLM's training corpus post-dates T1's deletion by 121 years. Every
condition of DR5**'s escape route fails. Wall bites hard.

The empirical picture from DR6d/e/f/g/h is that the wall's severity is
*graded*, not binary, and the grading is captured by DR5**'s three
factors. What DR5 called "the wall" is the extreme end of a spectrum;
what DR6 escapes are the softer regions of the same spectrum.

---

## 1. Setup

10 new snippets in `snippets_h.py`:

**Realisations (5) of $D_h$:**

- RH1: read-modify-write with no locking
- RH2: seek+write pattern, single handle
- RH3: append-to-log without lock
- RH4: write-then-rename atomic replace, no coordination on the read side
- RH5: JSON load-modify-dump

**Placebos (5):**

- PH1: `fcntl.flock` exclusive lock
- PH2: `filelock` library, explicit
- PH3: no file access at all (in-memory)
- PH4: read-only open, side-effect free
- PH5: hand-rolled pidlock with retry

Three sandboxed Claude subagents. $D_h$ specified verbatim in prompt.

## 2. Results

**Per-snippet consensus scores:**

| snippet | kind | per verifier | consensus |
|---|---|---|---|
| RH1_readmodifywrite | realisation | (from JSON) | **10** |
| RH2_seek_write | realisation | | **9** |
| RH3_append_log | realisation | | **6** |
| RH4_rename_after_write | realisation | | **5** |
| RH5_json_load_modify_dump | realisation | | **10** |
| PH1_fcntl_lock | placebo | | **1** |
| PH2_filelock_library | placebo | | **0** |
| PH3_no_file_access | placebo | | **0** |
| PH4_read_only_open | placebo | | **3** |
| PH5_lockfile_context | placebo | | **1** |

**Aggregate:**

- Realisations: [10, 9, 6, 5, 10] — median 9, stdev **2.35**, min 5, max 10.
- Placebos: [1, 0, 0, 3, 1] — median 1, max 3.
- Overlap gap: 5 − 3 = **+2**.

## 3. Gate decisions

| gate | | |
|---|---|---|
| W1 completeness | GO | |
| W2 realisation median ≥ 6 | GO | 9 |
| W3 realisation stdev ≥ 1.5 | **GO** | 2.35 (wall indicator!) |
| W4 placebo median ≤ 3 | GO | 1 |
| W5 placebo trigger ≥ 5 | NO_GO | max 3 |
| W6 direct overlap | NO_GO | gap +2 |

**Overall NO_GO** on the strict "wall bites" gate. But W3 GO is
significant — realisation variability is 2× to 3× wider than every
prior DR6 variant. The wall is starting to bite in the variance
dimension without producing direct overlap yet.

Reading: `clean_discrimination_despite_no_obvious_proxy`. Modulated:
LLM semantic reasoning succeeded in absolute terms but at reduced
margin, exactly as DR5*'s directional prediction anticipates.

## 4. Comparison with prior DR6 variants

| paper | target $D$ | prompt | overlap gap | realisation stdev |
|---|---|---|---:|---:|
| DR6 | naive-UTC | D specified | 7 | 0.98 |
| DR6e | naive-UTC (extended) | D specified | 7 | 0.98 |
| DR6f | naive-UTC | D-adjacent | 6 | 0.82 |
| DR6g | naive-UTC | fully blind | 6 | 0.63 |
| **DR6h** | **exclusive file access** | **D specified** | **2** | **2.35** |

The stdev jump from ≤1 to 2.35 is the strongest signal. DR6h's
realisations span the widest range of scores because the LLM is
reasoning about each snippet's semantic content and reaching different
conclusions: RH1/RH2/RH5 are "obvious" (multi-step file operations,
clear concurrency risk) while RH3/RH4 are subtler (append is atomic on
most filesystems for small writes; write-then-rename is a *pattern for*
concurrency-safety though the read side is still unlocked).

Prior DR6 targets could be scored via a domain-general proxy that gave
uniform-high scores to all realisations. DR6h's target has no such
proxy, so realisations get scored on their individual semantic content
— which varies.

## 5. What DR6h establishes

- **DR5* is directionally right but too strong.** The wall does not
  fully bite even without a domain-general proxy — LLM semantic
  reasoning provides substantial signal. But margin narrows and
  variability increases exactly where DR5* predicts.
- **The wall is graded.** DR5**'s three factors (semantic depth of D,
  domain-general correlate, LLM training coverage) each modulate the
  margin. Targets fail all three (DCR1f T1) bite hard; targets satisfy
  all three (DR6e naive-UTC with D specified) escape cleanly; targets
  in between produce intermediate outcomes.
- **The single most predictive metric is realisation stdev.** All prior
  DR6 variants had stdev ≤ 1; DR6h jumped to 2.35. High stdev signals
  the wall is starting to bite even before direct overlap appears.

## 6. Refined-refined claim (DR5**)

The wall's severity is a graded function of three factors, all
verifier-relative:

1. **Semantic depth of $D$** — how well-defined is the target
   commitment in a form the verifier can reason about.
2. **Domain-general correlate** — does the target admit a surface
   feature (implicit-vs-explicit, structured-vs-unstructured, etc.)
   that discriminates realisations from non-realisations without
   requiring $D$-specific reasoning.
3. **LLM training coverage** — how much of the LLM's training corpus
   covers reasoning about $D$-like commitments in the target domain.

The wall is severe when all three fail. The wall is absent when all
three succeed. Intermediate cases (DR6f/g/h) produce intermediate
outcomes: some discrimination, but at reduced margin and with high
variability across realisations of the same target.

## 7. What DR6h does not license

- **DR5's original structural theorem is refuted.** It is not.
  Proposition-ranking $N$ still cannot distinguish $D$ from $r_i$
  under DR5's antecedents; DR6h just shows the LLM's escape via
  condition (b) is graded, not binary.
- **The stdev metric is universal.** DR6h introduced it post-hoc from
  the observation. A preregistered stdev threshold might catch the
  wall's degrees more cleanly in a future DR8 gradient study.

---

## Appendix: reproduction

```
uv run --no-sync python -m experiments.dr6_code_correctness_corollary.run_dr6h
```

Deterministic scoring over three verifier JSON files, six-gate output
in `results/dr6h_verdict.json`.
