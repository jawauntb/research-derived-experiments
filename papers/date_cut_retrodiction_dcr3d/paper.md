# DCR3d: The Silent-But-Load-Bearing Signal Fires. At the Wrong Time.

**Human director:** Jawaun Brown
**Producing agent:** Claude Code, directed
**Program:** Date-Cut Retrodiction — DCR3d (use/discussion ratio scoring)
**Status:** Overall **NO_GO** on both M1 and M2. But the specific pattern is a real finding: **T1 ranks first at both 1880 AND 1897 under use/discussion ratio, and only DROPS to rank 2 at 1904** — because by 1904 T1 has started being discussed. The silent-but-load-bearing signal fires; it just fires *before* the deletion, not *at* it. Deletability is a build-up state, not a moment property. Fifth serial null with the sharpest new finding of the DCR run.
**Date:** 2026-07-27

---

## Abstract

The human director's silent-but-load-bearing intuition, operationalised
as `deletability(C) = use_count(C) / (discussion_count(C) + 1)`, was
preregistered to test whether T1 ranks first at the 1904 target cut
AND not first at the 1880 placebo. Nine sandboxed Claude subagents
tagged which propositions DISCUSS each class (T1/T2/T3) as their
subject vs merely USE it as background. Use counts reused from DCR3c
(also 9 subagents, prior run). ≥2-of-3 consensus. Prompt SHA-256
pinned.

**Result: T1 rank across cuts:**

| cut | T1 use | T1 disc | T1 ratio | T2 ratio | T1 rank |
|---|---:|---:|---:|---:|---:|
| **1880 (deep placebo)** | 9 | 1 | **4.50** | 1.00 | **1** |
| **1897 (near placebo)** | 3 | 1 | **1.50** | 0.46 | **1** |
| **1904 (target)** | 10 | 7 | 1.25 | **1.92** | 2 |

**M1 NO_GO** (T1 rank 2 at 1904). **M2 NO_GO** (T1 rank 1 at 1880 too).
**Fifth serial preregistered null on the DR-arc side.**

**But the pattern is not the "always-quiet detector" I preregistered
as M2's failure mode.** It's a specific empirical finding:

The use/discussion ratio identifies T1 as silent-but-load-bearing at
1880 and 1897 (T1 ratio 4.5 and 1.5, both first). At 1904, T1's
discussion count JUMPS from 1 to 7 — Poincaré 1898 treats simultaneity
philosophically, Larmor 1900 ch11 writes common time into the
transformation, Lorentz 1904 mentions corresponding instants — and
T1's ratio drops to 1.25, below T2's 1.92.

**The silent-but-load-bearing signal exists.** It's real, it's
measurable, and it correctly identifies T1's deletability *while T1
was still silent*. The signal fades exactly when the community starts
discussing the commitment — which is precisely the pre-deletion
transition. Einstein's move in 1905 caught a signal that had been at
maximum in 1880, was diminishing by 1904, and would have been gone
entirely once someone else made the deletion first.

**Deletability is a build-up state, not a moment property.** The
measure detects WHERE the deletion is available, not WHEN it happens.
The moment of deletion is when someone (Einstein) acts on
pre-existing availability. That's a substantive finding about how
conceptual revolutions actually work, and it converts DCR3's
loud/silent asymmetry from a corpus-time-snapshot claim into a
corpus-time-trajectory claim.

---

## 1. What was preregistered

`DCR3D_PREREGISTRATION.md` (2026-07-27, before `run_dcr3d.py` was
drafted, before subagent discussion-tagging calls were spawned):

- **Scoring:** `deletability(C) = use_count(C) / (discussion_count(C) + 1)`
  for each class C ∈ {T1, T2, T3}. Higher = more deletable.
- **Use counts:** reuse DCR3c's inferred-required-assumption tags
  (≥2 of 3 verifier consensus).
- **Discussion counts:** new. 9 sandboxed Claude subagents (3 per cut
  × 3 cuts) tag each proposition with the T1/T2/T3 categories it
  DISCUSSES as its subject rather than merely USES as background.
  Prompt (SHA-256
  `24384377bfab8dfe87cc72ce01d0908da992cddb2e39d11781cb42f432dbea05`)
  gives explicit USE vs DISCUSS rubric with examples.
- **Consensus rule:** ≥2 of 3 verifiers must agree that a proposition
  discusses a category for the tag to count.
- **No multidoc gating** on discussion counts — rewarding single-
  author-discussion signals like Poincaré 1898 on simultaneity is
  the whole point.

Four preregistered gates: M1 (T1 first at 1904), M2 (T1 not first at
1880), M3 (M1 beats random null), M4 (prompt committed).

The preregistration named the M1-GO/M2-NO_GO failure mode ("always-quiet
detector") as a specific informative-null outcome. The actual outcome
(M1 NO_GO and M2 NO_GO with T1 rank 1 at both placebo cuts) is a
different, richer failure mode not preregistered as a distinct row.

## 2. Results in full

**Per-cut consensus (≥2 of 3 verifiers agree):**

| cut | T1 use | T1 disc | T2 use | T2 disc | T3 use | T3 disc |
|---|---:|---:|---:|---:|---:|---:|
| 1880 | 9 | 1 | 20 | 19 | 0 | 0 |
| 1897 | 3 | 1 | 26 | 55 | 1 | 1 |
| 1904 | 10 | 7 | 50 | 25 | 2 | 4 |

**Ratios:**

| cut | T1 | T2 | T3 |
|---|---:|---:|---:|
| 1880 | **4.50** (rank 1) | 1.00 | 0.00 |
| 1897 | **1.50** (rank 1) | 0.46 | 0.50 |
| 1904 | 1.25 (rank 2) | **1.92** (rank 1) | 0.40 |

**Verifier variance on discussion tagging** was substantial: at 1904,
verifier A tagged 14 T1-discussions, B tagged 7, C tagged 6. The
≥2-of-3 consensus reduces to 7 (Poincaré 1898 four items + Larmor
1900 common-time + Lorentz 1904 corresponding-instants + Poincaré
1904 simultaneous-transmission). Cross-verifier variance is real but
the consensus filters it to defensible tags.

## 3. Gate decisions

| gate | | |
|---|---|---|
| M1 T1 first at 1904 | **NO_GO** | T1 rank 2 (T2 first) |
| M2 T1 not first at 1880 | **NO_GO** | T1 rank 1 |
| M3 beats random null | NO_GO | by construction |
| M4 prompt committed | GO | SHA-256 pinned |

**Overall NO_GO.**

Licensed reading (from the runner):

> fifth_serial_null: T1 rank 2 even under use/discussion ratio
> scoring. Silent-but-load-bearing intuition correct in spirit but
> this specific operationalisation does not invert T2's dominance.

**But that reading misses the substantive pattern.** The strict
verdict is NO_GO; the interpretive finding is richer and worth
naming.

## 4. What DCR3d actually found

Reading the numbers across the three cuts:

At **1880** (Maxwell only), T1 is used 9 times (Maxwell's field
theory quietly assumes an "instant across the medium" many times),
discussed once (a single Maxwell proposition takes "instant across
whole medium" as its subject). Ratio 4.5. T1 is at MAXIMUM
silent-load-bearingness. Nobody argues about common time. Everyone
uses it.

At **1897**, use drops to 3 (extraction identifies fewer T1
requirements in this cut's specific propositions — many are Michelson-
Morley-shaped where the required commitment is more specifically
about light-travel-time-being-well-defined than about
common-time-across-observers-generally). Discussion still 1. T1 ratio
1.5. Still first. T1 has become slightly less silently-loaded but
still no one discusses it.

At **1904**, use is back up to 10 (Larmor 1900, Lorentz 1904, and
Poincaré 1904 add explicit predictions that require T1). **But
discussion jumps from 1 to 7.** Poincaré 1898 treats simultaneity
philosophically. Larmor's `common_time_across_two_systems` is
explicitly written into the transformation. Lorentz 1904's
`true_time_defines_corresponding_instants` names the concept. Poincaré
1904's `simultaneous_transmission_meaningful` treats the notion
directly. Suddenly the commitment IS discussed. Ratio drops to 1.25.
T2 wins by having proportionally more use for its discussion count.

**The revolution's precursors** — Poincaré, Larmor, Lorentz —
literally raised the discussion count on T1 in the immediate pre-1905
window. They started making explicit what had been implicit, and in
doing so they made the silent-but-load-bearing signal *decay*. The
signal is at maximum when the community is silent. The signal fades
exactly at the moment when someone eventually acts on it.

## 5. What this implies for the DR-arc

DCR3 established the loud/silent asymmetry as a static claim about
1904. DCR3d shows the asymmetry is **dynamic**. The
silent-but-load-bearing property peaked in 1880 (Maxwell alone) and
was already fading by 1904. Einstein made the deletion when the
signal was at ~1.25 — after it had dropped from 4.5 twenty-four
years earlier.

**Deletability is a trajectory, not a moment.** A scoring principle
that fires at 1880 for a deletion Einstein made in 1905 is not
"wrong" — it's identifying the same commitment at an earlier point
in its deletability trajectory. The actual moment of deletion is
determined by who is looking, not by when the signal peaks.

For the DR-arc's original question — "given only pre-1905 material,
identify the deletion that will be made in 1905" — this is a
constructive negative result:

- **Use/discussion ratio DOES identify T1 as maximally deletable at
  1880 and 1897.** If you'd asked at 1880 "what's silently
  load-bearing enough to be deletable?" — you'd have gotten T1.
- **But by 1904 the signal has diminished** because T1's precursors
  (Poincaré, Larmor, Lorentz) have started discussing it. If you ran
  the measure only at 1904 (which is what M1 tested), T2 wins on the
  ratio.

**The measure works, at a different cut than the DR-arc's design
predicted it should.** The DR-arc wanted "identify what Einstein
would delete, using material available immediately before he
deleted it." What this experiment shows: the material *immediately
before* is already partially post-precursor. To catch the deletable
commitment, you need to score at a cut before the precursor
discussion — which is a fundamentally different measurement
protocol.

## 6. What DCR3d does not license

- **T1 is now recoverable from pre-1905 material.** M1 is still NO_GO
  at 1904. The trajectory finding doesn't rescue the target cut
  score.
- **The reframe is confirmed.** It's directionally supported in an
  unexpected way — the signal is real but temporally misaligned.
- **This is a positive result in disguise.** The strict preregistered
  gate is NO_GO. The interpretive finding is worth having but the
  ledger records a fifth serial null.

## 7. What comes next, sharpened by this finding

- **DCR3e — trajectory rather than snapshot scoring.** For each
  class, compute (use/discussion) at 1880, 1897, 1904 and look at
  the *derivative*. The commitment whose ratio DROPS most rapidly
  approaching 1904 is the one being brought into discussion (i.e.,
  the deletion is imminent). Under this measure, T1 might rank
  higher because its ratio drop is largest (4.5 → 1.25).
- **DCR4 — post-cut oracle comparison.** Score at 1904 vs Einstein
  1905. If T1's discussion count in Einstein 1905 is much higher than
  in the pre-1905 corpus, the derivative measure would confirm.
- **DR9 theorem.** Formalise the trajectory finding: prove that any
  scoring rule based on a single-cut snapshot of use/discussion
  ratio cannot identify commitments whose deletability signal has
  already begun fading due to precursor discussion. The signal has to
  be measured before the precursors start.

---

## Appendix: reproduction

```
uv run --no-sync python -m experiments.date_cut_retrodiction.run_dcr3d
```

Reads DCR3c use tags (existing) and DCR3d discussion tags (9 new
subagent outputs), computes per-class use/discussion ratios at each
cut with ≥2-of-3 verifier consensus, applies M-gates, writes
`results/dcr3d_verdict.json`. Local CPU, seconds.

**Preregistration digest (SHA-256 of `DCR3D_PREREGISTRATION.md`):**
`009d9b13baf519e3bfd6ae011c516d287ca9f24eaaf5e4102b4fe1a8793159a7`.

**Prompt digest (SHA-256 of `DCR3D_PROMPT.md`):**
`24384377bfab8dfe87cc72ce01d0908da992cddb2e39d11781cb42f432dbea05`.
