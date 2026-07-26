# DCR1c — The Two Repairs DCR1b Named

**Package:** `experiments/date_cut_retrodiction/` (v3 modules)
**Predecessor:** DCR1b (H1–H4 GO, H5 NO_GO, H6 GO — overall NO_GO)
**Human director:** Jawaun Brown
**Date:** 2026-07-26

## 0. Freeze status — the weakest of the three, stated plainly

This document was written **after** `run_dcr1c.py` was executed. That is the DR3
slip, and I am not going to dress it up.

What makes it defensible, and the reader should judge whether it does:

- **No gate was invented, moved, or renamed.** H1–H6 are byte-identical in
  definition to DCR1b's, including every threshold. `run_dcr1c.py` imports
  `QUOTE_FIDELITY_GATE` and `RESIDUE_RATE_GATE` directly from `run_dcr1.py`
  rather than restating them, so they cannot drift.
- **The repairs were specified in advance, in DCR1b's published paper**, §6:
  a polarity and referent test on T2, and a third sandboxed pass so consensus is
  2-of-3. DCR1c implements exactly those two and nothing else.
- **`target_v3` was validated before use** against DCR1b's adjudicated set — the
  four false positives it must reject and the ten genuine hits it must keep —
  and that validation is a committed regression test, not a claim.

What that does **not** buy: DCR1c is a confirmatory run of a hypothesis whose
answer I already suspected, executed by someone who had seen every prior result.
Treat the GO accordingly. The one thing it cannot be is threshold-fitted, since
the thresholds are imported constants.

## 1. What changed from DCR1b

**Repair 1 — `target_v3`.** DCR1b's H5 failed on four T2 hits, in three distinct
failure modes:

| mode | example |
|---|---|
| polarity | "The hypothesis of a stationary ether is shown to be **incorrect**." |
| referent | "…the ether at the earth's surface to be at rest **with regard to the earth's surface**" — the dragged-ether rival |
| label | "…in comparison with the **fixed system**" — a coordinate label |

v3 adds a polarity veto on targeted refutation markers, a referent veto on rest
claims made relative to the earth, and drops `fixed system`/`fixed frame` from
the pattern while keeping `fixed aether`.

The polarity veto deliberately does **not** fire on bare negation. Larmor's "It
has *not* been found possible to construct a system of dynamics which has
respect only to the relative positions of moving bodies" is a negative sentence
whose content is precisely the absolute-space commitment, and a naive negation
veto would delete it.

Vetoes apply to **T2 only**. T1 and T3 produced no false positives under
adjudication, and applying an untested veto to a clean facet would be changing
something that is not broken.

**Repair 2 — consensus 2-of-3.** A third sandboxed pass was run. Consensus now
requires agreement in 2 of 3 passes rather than 2 of 2. Pass 1 remains excluded:
its prompt did not forbid reading other repository files and one agent read this
repository's own code.

**Unchanged:** the corpus, the cuts, the extraction prompt, the quorum, every
threshold, and `residue_v2`. DCR1b's modules are not edited, so its published
numbers remain reproducible.

## 2. Gates

Identical to DCR1b's. Reproduced so this document stands alone.

- **H1** quote fidelity ≥ 90%
- **H2** v2 vocabulary residue < 5% at every cut
- **H3** the 1880 deep placebo does not surface the target family
- **H4** the 1904 target cut does
- **H5** every facet hit at the target cut survives an individual read; **any
  false positive fails**
- **H6** the facet verdict is identical under the consensus and under each
  sandboxed pass taken alone

**Overall GO requires all six.** A GO licenses DCR2 — nomination and ranking over
the consensus proposition set — which has been blocked since DCR1.

## 3. What a GO does not license

Not that the nominators work on real material; that is DCR2's question. Not
anything about vocabulary extension, the standing ceiling of the whole
framework. And not a claim that the corpus contains Einstein's deletion: T1,
absolute simultaneity, is matched **zero** times at every cut under both v2 and
v3. The corpus surfaces the privileged frame and local time; it does not surface
the simultaneity commitment as an explicit proposition. That is a fact about the
corpus and the extraction, and it deserves to be reported rather than smoothed
over, because it is the facet Einstein actually deleted.

One fragility no gate measures: T3 rests on a single proposition, so the target
cut clears quorum by a margin of one. A successor should either widen T3 or
introduce a margin gate.

Single-shot. No replay knobs.
