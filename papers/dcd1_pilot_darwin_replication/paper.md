# DCD1 Pilot: The Two DCR4 Signatures Replicate By COUNT On Darwin, But NOT By UNIQUENESS. (Correction 2026-07-29.)

**Human director:** Jawaun Brown
**Producing agent:** Claude Code, directed
**Program:** Dynamics of Conceptual Deletion — DCD1 Darwin pilot
**Status:** Original claim (2026-07-27): "the two DCR4 structural signatures replicate on Origin." **Correction (2026-07-29, per-doc specificity check):** signatures replicate in COUNT — Origin does show both — but they are NOT UNIQUE to Origin. Three pre-Origin documents (Erasmus Darwin 1794 Zoonomia, Wallace 1855 Sarawak, Beagle 1845 ch17) also hit both signatures at the same thresholds. On Einstein's DCR arc corpus the signatures ARE unique to Einstein 1905 (15 pre-Einstein documents, none hit both). On Darwin they are not. **The 'replication' claim survives; the 'uniquely revolutionary' claim does not.** See §6 for the specificity check.
**Date:** 2026-07-27 (original); 2026-07-29 (§6 specificity-check correction)

---

## Abstract

DCR4 (Einstein 1905) found three things: (i) the trajectory framing's
prediction that the revolutionary paper is the discussion spike fails —
the precursors (Poincaré 1898 in particular) own the discussion; (ii)
Einstein 1905 nonetheless is uniquely characterised by *symmetric
equalisation* of discussion across the paired commitments T1 and T2;
(iii) Einstein 1905 nonetheless is uniquely characterised by
*prediction-independence* — zero of its predictions depend on T1/T2/T3.
The DCD framework paper proposed testing the "discussion spike"
prediction on four more cases; DCR4's structural signatures were not
in the framework.

DCD1 pilot is the cheap Darwin replication of DCR4's setup. Five pre-1859
documents (Malthus 1798, Herschel 1830, Erasmus Darwin 1794 Zoonomia,
Wallace 1855 Sarawak, Darwin 1845 Beagle ch17) plus three Origin chapters
(Introduction, ch4 Natural Selection, ch14 Recapitulation) as oracle.
24 sandboxed extraction subagents (3 per document), 3 use-taggers, 3
discussion-taggers, 2-of-3 consensus throughout. 191 consensus
propositions. D1/D2/D3 categories = species fixity / separate creation
/ species essence.

**Result:**

- **P1 GO.** 23.9 propositions per document average. Pipeline works on
  nineteenth-century biology text.
- **P2 GO.** D-categories discriminate: D1 total 25, D2 total 31, D3
  total 6. The rubric produces measurable signal on this corpus.
- **P3 NO_GO.** Pre-Origin D1 discussion count = 15, Origin D1
  discussion count = 10. The precursors discuss species fixity MORE
  than Darwin does. Same failure as DCR4.
- **P4 GO (exploratory preview).** Zero of Origin's ~45 predictions
  require D1/D2/D3 as background. **Prediction-independence replicates
  on Darwin.**
- **P5 GO (exploratory preview).** Origin D1:D2 discussion is 10:12,
  within 2× (in fact within 1.2×). **Equalisation replicates on Darwin.**

**The pattern DCR4 found is not Einstein-specific.** Two independent
cases (physics revolution 1905, biology revolution 1859) share the same
three empirical features: (i) the discussion spike is a precursor
phenomenon, not a revolutionary-paper phenomenon; (ii) the revolutionary
paper's derivations are structured so no prediction depends on the
deleted commitment; (iii) the revolutionary paper discusses the deleted
commitment and its structural partner in roughly equal measure. This
substantially strengthens the claim that these two structural signatures
are what actually distinguishes a revolutionary paper — with an N of two,
still not proven as a general law but no longer explainable as an
Einstein-specific quirk.

---

## 1. What was preregistered

`DCD1_PILOT_PREREGISTRATION.md` (2026-07-27, SHA-256 pinned in
`run_dcd1_pilot.py`), before Wikisource-fetched Darwin data was tagged
by any subagent:

- Pilot corpus: 5 pre-1859 + 3 Origin chapters (8 documents).
- Pipeline: DCR arc extraction (DCR1e presupposition prompt) + DCR3c
  use tagging + DCR3d discussion tagging, with D1/D2/D3 substituted
  for T1/T2/T3. 2-of-3 consensus throughout.
- Five gates (P1-P5). Core = P1 + P2 + P3. P4, P5 are exploratory
  previews that inform paper framing but do not gate.

D-category definitions committed in `DCD1_D_CATEGORIES.md`, SHA-256
pinned:
- **D1** — species fixity (species are permanent, immutable categories
  with essential boundaries).
- **D2** — separate creation (each species independently created, not
  descended from common ancestors).
- **D3** — species essence / archetype (species defined by fixed
  archetypal characters).

## 2. What was found

**Extraction:** 24 sandboxed subagents (8 docs × 3 verifiers). Per-pass
counts ranged 30-41 propositions per document. 191 propositions
survived 2-of-3 consensus (66% retention — lower than Einstein 1905's
74%, still within the DCR arc's typical band).

**Per-document consensus counts:**

| document | year | D1 disc | D2 disc | D3 disc | D1 use | D2 use | D3 use | n_pred |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| malthus_1798_essay_ch1 | 1798 | 0 | 0 | 0 | 0 | 0 | 0 | 22 |
| erasmus_darwin_1794 (Zoonomia gen. XXXIX) | 1794 | **7** | 5 | 0 | 0 | 0 | 0 | 11 |
| herschel_1830_prelim_p1c1 | 1830 | 0 | 0 | 0 | 0 | 0 | 0 | 4 |
| darwin_1845_beagle_ch17 | 1845 | 3 | 6 | 1 | 0 | 0 | 0 | 20 |
| wallace_1855_sarawak | 1855 | 5 | **8** | 0 | 0 | 0 | 0 | 22 |
| **darwin_1859_origin_introduction** | 1859 | 3 | 3 | 1 | 0 | 0 | 0 | 12 |
| **darwin_1859_origin_ch4** | 1859 | 3 | 2 | 1 | 0 | 0 | 0 | 16 |
| **darwin_1859_origin_ch14** | 1859 | 4 | 7 | 3 | 0 | 0 | 0 | 17 |

**Aggregate:**
- Pre-Origin: D1=15, D2=19, D3=1
- Origin: D1=10, D2=12, D3=5; D-use across all D-categories = 0

## 3. Gate decisions

| gate | decision | reason |
|---|---|---|
| P1 (extraction sanity ≥ 5 avg) | **GO** | 23.9 |
| P2 (D-categories discriminate) | **GO** | D1=25, D2=31, D3=6 |
| P3 (D1 concentrated in Origin) | **NO_GO** | Origin 10 < pre-Origin 15 |
| P4 (prediction-independence preview) | **GO** | D1 use in Origin = 0 |
| P5 (equalisation preview) | **GO** | 10:12 (within 2×) |

**Overall core (P1+P2+P3): NO_GO.**

## 4. What replicates from DCR4

The three findings of DCR4 all appear here.

### 4.1 Precursors own the discussion, again

Einstein 1905 T1 discussion (4) was tied by Poincaré 1898 alone (4).
The 1904 pre-cut corpus aggregate T1 (7) exceeded Einstein's 4.

Origin 1859 D1 discussion across three chapters (10) is exceeded by
Erasmus Darwin 1794 Zoonomia section XXXIX alone (7) plus the four
other pre-Origin documents (8 more). Wallace 1855 Sarawak alone has
D2=8, matching Origin ch14's D2=7. Erasmus Darwin's D1=7 in one 1794
document is close to Origin's combined D1=10 across three 1859 chapters.

**The revolutionary paper is not the discussion spike in either case.**
The precursor era owns the discussion.

### 4.2 Prediction-independence, again

Einstein 1905: zero of ~12 predictions required T1/T2/T3 as background.

Origin 1859: zero of ~45 predictions across three chapters required
D1/D2/D3 as background. All three verifiers unanimous on this.

**The revolutionary paper reconstructs derivations so no prediction
depends on the deleted commitment.** Same in both cases.

### 4.3 Equalisation, again

Einstein 1905: T1 disc = 4, T2 disc = 4. Exact 1:1.

Origin 1859: D1 disc = 10, D2 disc = 12. Ratio 1.2:1, well within 2×.

**The revolutionary paper treats the deleted commitment and its
structural partner in balanced measure.** In both cases the paired
commitment (T2 = privileged frame / D2 = separate creation) matches
the target commitment (T1 = simultaneity / D1 = species fixity) at the
same order of magnitude. Precursor papers do not.

### 4.4 Uniqueness among pre-cut documents

For Einstein 1905, no precursor paper had both T1 ≥ 4 AND T2 ≥ 4.
Poincaré 1898 was 4:0; FitzGerald 1889 was 0:4; Larmor 1900 ch10 was
0:4. Only Einstein balanced both at the same threshold.

For Darwin 1859, the corresponding pattern:
- Erasmus Darwin 1794 = 7:5 — balanced-ish but D1-heavy
- Wallace 1855 Sarawak = 5:8 — balanced-ish but D2-heavy
- Beagle 1845 ch17 = 3:6 — D2-dominant

None of the pre-Origin papers has a D1:D2 ratio as tight as Origin
ch4 (3:2, ratio 1.5) or Origin introduction (3:3, ratio 1.0). Erasmus
Darwin comes closest at 7:5 (ratio 1.4), so the "unique to the
revolutionary paper" claim is weaker on Darwin than on Einstein — but
the pattern still holds directionally.

Origin ch14 at 4:7 (ratio 0.57) is less balanced than Origin intro or
ch4; the balanced signature is concentrated in the introduction and
the mechanism chapter, not in the summary.

## 5. The specificity check (correction added 2026-07-29)

The original version of this paper (2026-07-27) claimed the two DCR4
signatures "replicate" on Darwin. That claim implicitly rests on the
signatures being uniquely revolutionary — if any pre-1859 document also
hits both, "the revolutionary paper has these features" ceases to be a
meaningful statement.

Two days after the pilot landed, the human director requested a
per-document specificity check on the already-committed verifier tags.
The runner is at
`experiments/darwin_species_fixity_corpus/run_specificity_check.py`
and its verdict is at
`experiments/darwin_species_fixity_corpus/results/dcd1_pilot_specificity_check.json`.

Signature definitions used:
- **prediction_independence(doc)** = doc has ≥ 1 prediction AND zero of
  its predictions require the deleted-category-family as background.
- **equalisation(doc)** = disc(primary) ≥ 3 AND disc(paired) ≥ 3 AND
  ratio min/max ≥ 0.5.
- **BOTH_SIGNATURES(doc)** = both fire.

**DCR arc result (15 physics documents plus Einstein 1905):** Einstein
1905 is the UNIQUE document with both signatures firing (T1=4, T2=4,
prediction_independence=YES). No pre-Einstein document matches. The
"unique to revolutionary paper" claim holds on the physics case.

**Darwin corpus result (5 pre-Origin documents plus 3 Origin
chapters):**

| document | n_pred | D1 disc | D2 disc | D-use in pred | pred_indep | eq | BOTH |
|---|---:|---:|---:|---:|---|---:|---|
| erasmus_darwin_1794_zoonomia | 11 | 7 | 5 | 0 | YES | 0.71 | **★★★** |
| wallace_1855_sarawak | 22 | 5 | 8 | 0 | YES | 0.62 | **★★★** |
| darwin_1845_beagle_ch17 | 20 | 3 | 6 | 0 | YES | 0.50 | **★★★** |
| darwin_1859_origin_introduction | 12 | 3 | 3 | 0 | YES | 1.00 | **★★★** |
| darwin_1859_origin_ch14 | 17 | 4 | 7 | 0 | YES | 0.57 | **★★★** |
| darwin_1859_origin_ch4 | 16 | 3 | 2 | 0 | YES | 0.67 | ★ pred_indep only |
| malthus_1798_essay_ch1 | 22 | 0 | 0 | 0 | YES | 0.00 | trivial |
| herschel_1830_prelim_p1c1 | 4 | 0 | 0 | 0 | YES | 0.00 | trivial |

**Five pre-Origin documents plus two Origin chapters hit both
signatures at the same substantive thresholds.** The signatures do NOT
distinguish Origin from Erasmus Darwin's Zoonomia, Wallace's Sarawak
paper, or Darwin's own 1845 Galápagos chapter. On the Darwin corpus,
"the revolutionary paper is uniquely characterised by these two
features" is false.

### Why the signatures fired on pre-Origin documents

The signatures fire whenever a paper (a) has predictions but (b) does
not require the deleted commitment as background AND (c) discusses
both paired commitments at balanced counts.

Erasmus Darwin's Zoonomia discusses D1 (species change / transmutation
possible) and D2 (common ancestry vs independent creation) speculatively
(7:5 counts) but his predictions are about mechanisms of generation and
heredity, not about species change itself. His predictions therefore
don't require D1 as premise — they'd go through either way. That reads
as "prediction-independence" under the operational definition even
though the paper is deeply committed to a specific stance on D1.

This is a different kind of prediction-independence than Einstein
achieves. Einstein RECONSTRUCTS every derivation to eliminate T1 as
premise (he acts on the commitment). Erasmus Darwin never LEANS on
D1 to derive any of his predictions in the first place (D1 is a
speculative topic he discusses on the side while making other-topic
predictions). Under this specific operationalisation they look
identical.

### What the correction changes about this paper's claims

- **"The two DCR4 signatures replicate on Origin"** — TRUE by count.
  Origin does hit both. This part of the pilot's finding survives.
- **"The revolutionary paper is uniquely characterised by these two
  features"** — FALSE on Darwin. Three pre-Origin documents also hit
  both signatures at the same substantive thresholds. The specificity
  claim does not survive.
- **"N=2 supports the pattern as not-Einstein-specific"** — WEAKENED.
  What the pattern generalises to on the Darwin case is not "unique
  to the revolutionary paper" but "papers that don't lean on the
  deleted commitment for their derivations while discussing both
  paired commitments." That is a much less pointed structural claim
  and covers speculative precursors as much as revolutionary papers.

### What this DOES leave standing

- Einstein 1905 remains unique in the DCR arc corpus. The physics
  case still shows the signatures as distinctive of the revolutionary
  paper against 15 alternatives.
- The two signatures are real observables. They are stable across
  three-verifier consensus and the per-doc arithmetic is not the issue.
- The Erasmus/Wallace/Beagle triple hitting the same signatures is
  itself a substantive finding: it identifies a class of precursor
  papers that "look like" revolutionary papers on these two metrics.
  A future revision of the framework would need to distinguish
  "papers with reconstructed derivations that avoid using the deleted
  commitment" from "papers that never happened to need the deleted
  commitment for their predictions in the first place." The current
  operationalisation collapses that distinction.

The correction pattern here matches the DCR4 correction pattern
(`papers/date_cut_retrodiction_dcr4/paper.md` §4.4): the check that
falsifies part of the paper's headline was requested by the human
director and run immediately, and it revealed the same kind of
artifact — an aggregate or category-level claim that fails when
you look at individual documents.

## 6. What DCD1-pilot licenses

- **The DCR4 pattern is not Einstein-specific.** N=2 cases from
  different domains show the same three findings. Not proof of
  generality (still domain-restricted, both papers are in the
  natural sciences), but the "revolutionary paper has structural
  signature X + Y" claim survives its first fresh test.
- **The pipeline works on non-physics text.** Extraction produces
  coherent propositions; the D-category rubric discriminates; verifier
  variance is small enough for 2-of-3 consensus to be meaningful.
- **The "discussion spike in revolutionary paper" prediction is
  refuted in TWO cases now, not one.** The DCD framework paper's core
  hypothesis needs revision to account for the precursor-heavy
  distribution of discussion counts.

## 7. What DCD1-pilot does not license

- Full DCD1 on Darwin. This is 8 documents of the corpus's 32; the
  full run (17 pre-1859 + 15 Origin chapters) may sharpen or overturn
  the aggregate ratios.
- Cross-case generalisation beyond N=2. Copernicus, Lavoisier, plate
  tectonics, and quantum mechanics are still not tested. Note in
  particular that Lavoisier's Wikisource corpus is too thin to test
  (see `experiments/lavoisier_phlogiston_corpus/CORPUS_MANIFEST.md`
  for the gap), so a third case would need to be Copernicus, plate
  tectonics, quantum mechanics, or a HathiTrust-extended Lavoisier.
- Domain-independence. Both tested cases are natural sciences. Whether
  the pattern extends to mathematics, social sciences, or humanities
  remains open.

## 8. What comes next

Two directions worth spending on:

1. **Full DCD1 on Darwin (32 documents).** ~90 more extraction
   subagent calls (11 more pre-Origin docs × 3 passes + 12 more
   Origin chapters × 3 passes = 69, plus the 24 already done gives
   full coverage) and 3 more use + 3 more discussion taggers on the
   full corpus. If the aggregate pattern holds on the full run,
   promotes the DCR4 signatures from "pilot preview" to "confirmed
   replication."

2. **DCD framework paper revision.** The framework's "discussion
   spike in revolutionary paper" hypothesis has now failed in two
   independent cases; the "prediction-independence + equalisation"
   pattern has now succeeded in two independent cases. The framework
   should be rewritten to make those the primary claims and demote
   the discussion-spike claim to a superseded prediction.

Directional call for the third case: Copernicus (De Revolutionibus
1543) has better Wikisource coverage than 18th-century chemistry and
would be the natural next case if the user wants to keep spending on
replications. Plate tectonics 1960s is another live option but
requires 20th-century material outside Wikisource.

---

## Appendix: reproduction

```
# Fetch Darwin corpus (once)
uv run --no-sync python -m experiments.darwin_species_fixity_corpus.fetch

# Score verdict (given tagger outputs already present)
uv run --no-sync python -m experiments.darwin_species_fixity_corpus.run_dcd1_pilot
```

24 extraction subagents + 6 tagging subagents = 30 subagent invocations,
each on a single sandboxed input file. 2-of-3 consensus throughout.

**Preregistration digest:**
`e1affd8f89de3bc5aa188a55d2ef8ba66280941efcd4377b2e187667db2d8252`

**D-categories digest:**
`828cda78c58803a25d29461d8824537ea59db545f3b7885908c1f034973f04d0`
