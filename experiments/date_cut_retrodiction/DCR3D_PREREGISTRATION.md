# DCR3d — Use/Discussion Ratio: Silent-But-Load-Bearing Scoring

**Package:** `experiments/date_cut_retrodiction/`
**Predecessors:** DCR3 (frequency, NO_GO), DCR3b (in-corpus counterfactual, NO_GO), DCR3c (inferred required-assumption, T1 rank 3→2 but NO_GO)
**Date:** 2026-07-27
**Written:** BEFORE `nominate_dcr3d.py` is drafted, BEFORE subagent
discussion-tagging calls are spawned.

## 0. What DCR3d tests

DCR3c showed the identifiability reframe (score by inferred required
assumptions) moved T1 from rank 3 to rank 2 but couldn't invert
T2's dominance. Reason: T2 is BOTH more required by predictions AND
more explicitly cited in the corpus. Every corpus-respecting measure
preserves this ratio.

The human director's intuition (2026-07-27): score by **use divided
by discussion**. A silent-but-load-bearing commitment has many uses
(predictions requiring it) and few discussants (propositions
arguing for/against it, defining it, disputing its correct form).
T1 has ~10 uses and ~1 discussant (Poincaré 1898). T2 has ~50 uses
and ~11 discussants (Michelson/MM/FitzGerald/Larmor/Lodge/Rayleigh/
Brace all writing directly about aether-frame variants).

Ratio: T1 ≈ 10/2 = 5.0, T2 ≈ 50/12 = 4.2. T1 barely wins.

DCR3d is the preregistered test: does this ratio-based scoring rank
T1 first at 1904 AND not first at 1880, at a level that beats
random?

## 1. Setup

- **Use counts:** reuse DCR3c's `results/dcr3c/inferred_*.json` (≥2 of
  3 verifier consensus tags of required_categories). No new inference
  calls needed for use counts.
- **Discussion counts:** new. 9 sandboxed Claude subagents (3 per cut ×
  3 cuts) tag each proposition with `discussed_categories`: which of
  T1/T2/T3 (if any) the proposition takes as its SUBJECT (defends,
  disputes, defines, examines) rather than uses as background. Prompt
  committed at `DCR3D_PROMPT.md`, SHA-256 pinned in runner.
- **Consensus rule:** ≥2 of 3 verifiers must agree that a proposition
  discusses a category, for the discussion to count.
- **Scoring:** `deletability(C) = use_count(C) / (discussion_count(C) + 1)`
  per class C ∈ {T1, T2, T3}. Higher = more deletable.
- **Baseline:** 10,000 uniform random permutations of class keys.

No multidoc gating on discussion counts — a commitment being
discussed by a single author (Poincaré 1898 on simultaneity) is
exactly the "silent" signal we want to reward. Multidoc on use is
optional; we do apply it (from DCR3c) to keep the numerator
consistent with prior arcs.

## 2. Gates

Four preregistered M-gates:

- **M1** — T1 class first at 1904 under use/discussion ratio.
- **M2** — T1 class NOT first at 1880 (**the crucial gate**). If T1
  wins at 1880 too, the measure identifies "always-quiet" not
  "deletable-here." M2 is the specific check that the ratio picks
  up the revolution, not a T1 invariant.
- **M3** — M1 result beats random null at p < 0.01.
- **M4** — prompt SHA-256 committed.

Overall GO iff all four M-gates GO.

## 3. Decision table

| M1 | M2 | reading |
|---|---|---|
| GO | GO | **DR-arc program empirically validated.** Fifth attempt, first success. Use/discussion ratio identifies T1 first at the revolution cut and not at the placebo. Ratio-based scoring is a real principle for revolutionary-deletion detection. Extends to other conceptual-change cases (Copernicus, Darwin, Lavoisier). |
| GO | NO_GO | **Always-quiet detector, not revolution detector.** T1 wins at 1880 too because T1 was always quiet, not because 1904 was uniquely the moment to delete it. Ratio measure is real but doesn't answer DR-arc's question. Report as informative null. |
| NO_GO | any | **Fifth serial null.** Even the silent/loud ratio doesn't recover T1 at 1904. Structural implication: DR-arc-as-designed cannot identify silent-but-load-bearing commitments from corpus data alone. Points at a DR9-theorem or a fundamentally different corpus-lens (e.g., cross-corpus comparison with post-cut material). |

## 4. Single-shot

One prompt, one round of subagent calls, one scoring pass, one
verdict. No replay knobs. Prompt SHA-256 pinned. If M1 or M2 fails,
DO NOT reword the prompt or adjust the ratio formula. Report NO_GO.

## 5. What DCR3d does not license

- **Ratio scoring is the correct primitive in general.** DCR3d tests
  one specific operationalisation on one specific corpus.
- **T1 is or isn't identifiable in principle.** Only that this
  ratio-based measure works or doesn't on this data.
- **The full DR-arc pipeline works.** Even a GO on DCR3d would only
  establish that a specific scoring principle identifies the deletion;
  it wouldn't establish that the DR1-DR4 nominator infrastructure
  identifies it under multi-candidate ranking.
