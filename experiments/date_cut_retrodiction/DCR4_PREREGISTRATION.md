# DCR4 — Does Einstein 1905's Discussion Structure Confirm the Trajectory Finding?

**Package:** `experiments/date_cut_retrodiction/`
**Predecessors:** DCR3d (silent-load-bearing signal peaks at 1880, fades by 1904 as precursors discuss T1), DCR3e (post-hoc trajectory quantification — T1 drop 3.25, largest)
**Date:** 2026-07-27
**Written:** BEFORE Einstein 1905 is fetched, BEFORE any subagent inspects it.

## 0. What DCR4 tests

DCR3d found that T1's use/discussion ratio peaks at 1880 and drops by
1904 because precursors (Poincaré, Larmor, Lorentz) start bringing T1
into discussion. Under DCR3d's interpretation, **the deletion happens
when discussion spikes further** — Einstein's 1905 paper is the moment
the community starts discussing T1 explicitly as a convention rather
than as an unstated background.

DCR4 tests this directly on a data set I have not seen: Einstein's
1905 *"On the Electrodynamics of Moving Bodies"* as an oracle corpus.
If DCR3d's interpretation is right, Einstein 1905 should show:

- T1 discussed a LOT (Einstein literally defines simultaneity in §1)
- T1 discussed more than T2 (Einstein's move is on T1, not T2)
- T1 discussion count HIGHER in Einstein 1905 than in the 1904
  pre-cut corpus (the discussion spike)

If DCR3d's interpretation is wrong, one or more of these will fail.

## 1. Setup

- **Corpus:** Einstein 1905 ("Zur Elektrodynamik bewegter Körper", Perrett-Jeffery
  1923 English translation, public domain). Fetched from Wikisource
  via existing `fetch.py` machinery.
- **Extraction:** three sandboxed Claude subagents with the same
  DCR1e presupposition-inferring prompt used across the DCR arc.
  Consensus 2-of-3.
- **Discussion tagging:** three sandboxed subagents with the DCR3d
  discussion prompt (SHA-256 pinned identically).
- **Use tagging:** three sandboxed subagents with the DCR3c
  inferred-required-assumption prompt (SHA-256 pinned identically).
- **Consensus rule:** ≥2 of 3 verifiers agree on a category tag.

No new prompts. All three phases reuse DCR arc prompts verbatim.

## 2. Gates

Four preregistered gates:

- **Q1 — Extraction sanity.** Einstein 1905 produces ≥ 15 consensus
  propositions. If fewer, extraction failed and the rest is moot.
- **Q2 — T1 discussion dominance.** In Einstein 1905, T1 discussion
  count > T2 discussion count. (Einstein's paper is about T1
  specifically; he keeps most of T2 intact and modifies its
  formulation.)
- **Q3 — T1 discussion spike.** T1 discussion count in Einstein 1905
  > T1 discussion count in the 1904 pre-cut corpus (which was 7).
- **Q4 — Ratio inversion.** T1's use/discussion ratio in Einstein
  1905 is LOWER than any pre-cut year's T1 ratio (T1 discussion has
  spiked so much that the silent-load-bearing signal has fully
  collapsed).

**Overall GO** iff all four Q-gates GO. GO = DCR3d's trajectory
interpretation empirically confirmed on Einstein 1905.

## 3. Decision table

| Q2 | Q3 | Q4 | reading |
|---|---|---|---|
| GO | GO | GO | **DCR3d trajectory interpretation confirmed on Einstein 1905.** T1 discussion spikes in Einstein 1905, the silent-load-bearing signal fully collapses, and T1 is discussed more than T2 (matching the deletion Einstein made). Substantive empirical support for the trajectory framing of deletability. |
| NO_GO | any | any | **T1 not the dominant subject of Einstein 1905.** Would falsify the specific claim that Einstein's move IS the T1 discussion spike. Would require re-examining which commitment Einstein actually deleted (T2 or something else). |
| GO | NO_GO | any | **No T1 discussion spike.** T1 discussion in Einstein 1905 is not higher than in the 1904 pre-cut corpus. Trajectory interpretation weakened — Einstein just used the existing discussion level. |
| GO | GO | NO_GO | **T1 ratio didn't collapse.** T1 use in Einstein 1905 rose proportionally with discussion, so ratio didn't drop. Nuanced finding: Einstein DISCUSSED T1 more but ALSO USED it more (perhaps in the version he was deleting). Requires interpretation. |

## 4. Single-shot

One extraction, one tagging pass, one comparison, one verdict. No
replay. If Q1 fails, redraft extraction prompt (this is instrument
failure, not scientific failure).

## 5. What DCR4 does not test

- Whether the trajectory interpretation extends to other conceptual
  revolutions (Copernicus, Darwin, Lavoisier). One-corpus test.
- Whether the DR-arc nominator could actually predict this in advance.
  DCR4 uses Einstein 1905 as an oracle after the fact.
- Whether a class-scoring pipeline with derivative measurement would
  identify Einstein's deletion. DCR3e already computed the derivative
  post-hoc; DCR4's fresh test is only about whether the discussion
  spike appears where DCR3d predicts it should.
