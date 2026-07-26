# DCR1b — The Same Question, With Repaired Instruments

**Package:** `experiments/date_cut_retrodiction/` (v2 modules)
**Predecessor:** DCR1 (G1 GO, G2 NO_GO, G3 GO, G4 GO — overall NO_GO)
**Human director:** Jawaun Brown
**Date:** 2026-07-26

## 0. Freeze status, stated exactly

Disclosure matters more than usual here, because DCR1b re-runs a question whose
answer I have already partly seen. What was true when this document was written:

**Already seen.** DCR1's full results. The consensus extraction's size (383
propositions from 553). The v2 calibration in §3 — including v2's residue rates
and v2's facet counts at every cut. So **H2, H3 and H4 below are gates *carried
over unchanged* from DCR1, not gates freshly frozen against unseen data.** They
are honest only in the sense that their thresholds were not moved to fit; they
are not blind.

**Not yet computed when this was written.** H5's adjudication of the consensus
extraction's facet hits, and H6's cross-pass robustness comparison. Those two
are genuinely frozen in advance.

DCR1's §5 said not to report facet results under a G2 failure, and I read them
anyway. That is on the record in DCR1's paper, marked advisory. This document
does not get to quietly inherit those results as though they were confirmatory —
which is why H5 and H6 exist.

## 1. What is repaired, and what is deliberately not

DCR1 failed on G2 and carried three further defects. DCR1b repairs the
**instruments**; every threshold is carried over at its original value. That is
DR4's rule, and DR4 is the only paper in this arc that passed cleanly.

**Repair 1 — the residue measure (`residue_v2.py`).** DCR1's measure counted
`communicates` against a corpus containing `communicate`, `Abraham's` against
`Abraham`, and `poincare` against `Poincaré` because it folded the `æ` ligature
but not accents. v2 folds accents, strips possessives, and compares stems on
both sides. The relational definition — a term is residue iff the extractor
emits it and the corpus lacks it — is unchanged, and remains the part worth
keeping, because this corpus proved a blocklist wrong in both directions.

**Repair 2 — the T1 pattern (`target_v2.py`).** DCR1's pattern accepted
`(absolute|universal|same|common|true)` before a time word, so it matched the
ordinary English "the same time". All three of its T1 hits were false positives.
v2 requires either an explicit absoluteness word or a sameness claim tied to an
independence clause. Validated against twelve cases including the three known
false positives, four genuine phrasings, and Poincaré's statement of the
relativity principle — which v2 correctly **declines**, because stating the
principle is not the same as asserting absolute simultaneity.

Note what the v1 defect was not caused by: freezing early. The matcher was
frozen before any output was read, exactly as it should have been. Freezing
makes a matcher honest, not correct; catching this needed someone to read the
hits.

**Repair 3 — consensus extraction (`consensus.py`).** DCR1's accidental second
pass showed two runs of an identical prompt on an identical document agree on
only 67.7% of propositions. A proposition now survives only if a semantically
equivalent one appears in at least 2 of the 2 sandboxed passes. Pass 1 is
excluded entirely: its prompt did not forbid reading other files and at least
one agent read this repository's own code.

**Not repaired, deliberately:** the corpus, the cuts, the extraction prompt, the
quorum of 2, and every threshold. Changing those alongside the instruments would
make the comparison to DCR1 uninterpretable.

## 2. What DCR1b cannot fix

Two passes is a thin consensus. `SUPPORT_THRESHOLD = 2` of `k = 2` means every
surviving proposition appeared in both, which is strict, but it also means a
commitment missed by one pass is gone with no third vote to rescue it. With
k = 3 sandboxed passes the filter would be better posed. I ran three passes
total; one was unblinded and cannot be used. This is a real limitation and it
belongs in the results, not in a footnote.

## 3. Calibration, measured before these gates were written

Consensus extraction: 15 documents, 383 propositions (69.3% retention from 553).

| cut | props | residue v1 | residue v2 | facets v1 | facets v2 |
|---|---:|---:|---:|---|---|
| 1880 deep placebo | 85 | 6.31% | **3.80%** | — | — |
| 1897 near placebo | 196 | 4.96% | **2.30%** | T2 | T2 |
| 1904 target | 383 | 5.01% | **2.28%** | T1, T2, T3 | T2, T3 |
| 1904 no-risk | 331 | 4.98% | **2.44%** | T2, T3 | T2, T3 |

**Amended after a stemmer fix.** A regression test written for `residue_v2`
caught an asymmetry v1 had and v2 inherited: `communicates` stemmed to
`communicat` while `communicate` did not, so an inflected pair failed to match
and counted as residue — exactly the artefact v2 exists to remove. `stem_v2`
adds a trailing-`e` rule and the whole pipeline was recomputed. The consensus
set (383 propositions) and every facet count are **unchanged**; only the residue
rates moved, all downward, from 4.34/2.60/2.65/2.86%. The table above is the
recomputed one. The gate is untouched.

Matcher repair at 1904: T1 3 → **0**, T2 14 → 14, T3 1 → 1. The repair drops
exactly the three adjudicated false positives and touches nothing else.

The 5% residue threshold is therefore **reachable but not trivial** — the
tightest cut sits at 3.80%, a margin of 1.20 points. Had calibration shown 0.5%
or 12%, the gate would have been worthless in opposite directions, and this is
the check DR3 skipped.

## 4. Gates

- **H1 — quote fidelity.** ≥ 90% of consensus propositions carry a quote present
  in their source under whitespace normalisation. *Carried over from G1.*
- **H2 — vocabulary residue.** v2 residue < 5% at every cut. *Threshold carried
  over from G2 unchanged; only the measure is repaired.*
- **H3 — deep placebo silent.** The 1880 cut does not surface the target family
  under the v2 matcher. *Carried over from G3.*
- **H4 — target cut not silent.** The 1904 cut surfaces it. *Carried over from
  G4.*
- **H5 — matcher soundness (new, frozen in advance).** Every consensus
  proposition matched to a facet at the target cut is read individually and must
  actually state that facet. **Any false positive fails H5.** This is the gate
  DCR1 did not have, and its absence is why three spurious hits reached a
  published table.
- **H6 — robustness (new, frozen in advance).** The facet verdict at each cut
  must be identical under the consensus extraction and under each individual
  sandboxed pass taken alone. A conclusion that depends on which draw of the
  extractor you got is not a conclusion.

**Overall GO requires all six.** H3 remains the gate that carries the scientific
weight; H5 and H6 are the ones that decide whether the instrument can be
trusted to report H3 honestly.

## 5. What a GO licenses, and what it does not

A GO says the extraction pipeline measures the corpus rather than the model, on
a corrected instrument, with a candidate set stable enough to be worth ranking.
That licenses **DCR2** — nomination and ranking over the consensus proposition
set — which has been blocked since DCR1.

A GO does **not** say the nominators work on real material. That is DCR2's
question. Nor does it bear on vocabulary extension, the standing ceiling of the
entire framework: every deletion considered anywhere in this programme is over a
fixed proposition set.

A NO_GO on H5 or H6 means the instrument is still not trustworthy and DCR2 stays
blocked, regardless of how the placebo behaves.

Single-shot. No replay knobs. If a gate fires, it fires.
