# DCD1 pilot — Darwin / species-fixity, cheap sanity check

**Package:** `experiments/darwin_species_fixity_corpus/`
**Companion program:** Dynamics of Conceptual Deletion (DCD) multi-case
test — this is the pilot for the Darwin case.
**Date:** 2026-07-27
**Written:** BEFORE any subagent is spawned for extraction or tagging.

## 0. What DCD1-pilot tests

Not the full P(t) trajectory claim. This is a cheap sanity check that:

1. The extraction pipeline works on nineteenth-century biology text
   (as opposed to the electrodynamics text it was designed for).
2. The D1 / D2 / D3 category rubric produces measurable signal on
   this corpus (non-zero tag counts across ≥ 2 documents each).
3. The two structural signatures DCR4 found for Einstein 1905 —
   symmetric equalisation of primary vs secondary commitment, and
   zero prediction-dependence on the deleted commitment — either
   appear or do not appear for Darwin 1859 on the pilot subset.

If (1) and (2) fail, the D-category rubric needs redesign before any
full DCD1 test is worth spending on. If (3) shows structural
signatures analogous to Einstein 1905, that is a preview supporting
the full run; if (3) shows nothing, the DCR4 signatures may be
Einstein-specific and the full run's cost is harder to justify.

## 1. D-categories (fixed here, will be re-used in full DCD1)

- **D1** — **species fixity**: species are permanent categories,
  their forms immutable across generations, natural kinds with
  essential boundaries. Discussing D1 = asserting or denying
  species change; defining species boundaries as fixed or fluid;
  arguing about whether varieties can cross species lines.
- **D2** — **separate creation**: each species was independently
  created (or came into being) as a discrete act. Discussing D2 =
  asserting or denying independent origin of species; discussing
  the plurality of creations vs common descent.
- **D3** — **species essence / archetype**: species have a fixed
  archetypal form (Platonic essence, ideal type). Discussing D3 =
  defining species by essential characters; discussing the type
  specimen as fixing species identity; arguing against nominal or
  fluid definitions.
- **OTHER** — everything else (methodology, geology, demography,
  natural theology when it appears, generation mechanisms, etc.).

## 2. Pilot corpus (8 documents)

**Pre-1859 (5 documents, each already fetched):**
- `malthus_1798_essay_ch1` — demography, D1 as background
- `herschel_1830_prelim_p1c1` — philosophy of science
- `erasmus_darwin_1794_zoonomia_generation_39` — biology of
  generation; expected rich in D1 discussion
- `wallace_1855_sarawak` — immediate pre-Darwin biogeography;
  expected rich in D1 discussion (the Sarawak law)
- `darwin_1845_beagle_ch17` — Darwin's own pre-Origin observational
  writing; provenance_risk flagged in corpus but included for the
  pilot because it is the closest pre-Origin Darwin material

**Oracle (3 chapters of Origin 1859):**
- `darwin_1859_origin_introduction` — sets the stakes
- `darwin_1859_origin_ch4` — Natural Selection; the mechanism
- `darwin_1859_origin_ch14` — Recapitulation and Conclusion

## 3. Pipeline

- **Extraction:** three sandboxed subagents per document with the
  DCR1e presupposition-inferring prompt (SHA-256 pinned;
  cross-domain — the prompt is generic enough to apply to biology).
  Consensus 2-of-3 by content-stem Jaccard.
- **Discussion tagging:** three sandboxed subagents with the DCR3d
  discussion prompt, but with T1/T2/T3 mapped to D1/D2/D3 in the
  category definitions block. Consensus 2-of-3.
- **Use tagging:** three sandboxed subagents with the DCR3c
  inferred-required-assumption prompt, D-categories substituted.
  Consensus 2-of-3.

The prompts themselves are DCR-arc prompts with a single per-run
category-definition block substituted; the SHA-256 of the base DCR
prompts is pinned, and the substituted D-definition block is
committed to `DCD1_D_CATEGORIES.md` and its SHA-256 is pinned in the
runner.

## 4. Pilot gates

- **P1 (sanity: extraction produces signal).** Consensus extraction
  yields ≥ 5 propositions per document, averaged across the 8 pilot
  documents.
- **P2 (D-signal exists).** Discussion counts across the pilot
  corpus: D1 count ≥ 3, D2 count ≥ 1, D3 count ≥ 1. Below any of
  these thresholds and the rubric doesn't discriminate.
- **P3 (D1 signal is Darwin-relevant).** D1 discussion count in the
  three Origin chapters combined > D1 discussion count in the five
  pre-1859 documents combined. Analogous to the DCR3d "spike
  approaches deletion" pattern, tested on a much smaller sample.
- **P4 (prediction-independence signature preview).** Sum across
  the three Origin chapters of D1-required predictions equals zero
  (Einstein-1905 analogue). No pre-registered threshold on the
  precursor documents.
- **P5 (equalisation signature preview).** The three Origin
  chapters' D1 discussion count is within a factor of 2 of the
  Origin D2 count. Einstein-1905 was exact 4:4 balance; on Darwin
  we allow within 2× because the chapters are of different focus
  and combined counts will be higher than the single Einstein 1905
  document.

## 5. Decision table

| P1 | P2 | P3 | reading |
|---|---|---|---|
| GO | GO | GO | Pilot supports full DCD1 replication. Proceed to full run on all 32 documents. |
| NO_GO | any | any | Extraction failing on biology text. Redesign extraction prompt for the domain before scaling. |
| GO | NO_GO | any | D-category rubric doesn't discriminate. Redesign categories. |
| GO | GO | NO_GO | D1 signal present but not concentrated in Origin. Weakens the DCD framework's prediction; consider whether the "spike concentrated in revolutionary work" claim survives. |

P4 and P5 are exploratory previews — their outcomes inform paper
framing but do not gate the full run.

## 6. Single-shot

One extraction pass on the pilot corpus, one tagging pass, one
verdict. If P1-P3 pass, proceed to full DCD1 with the same rubric.
If any of P1-P3 fails, STOP and diagnose.

## 7. What DCD1-pilot does not license

- The DCD framework is empirically supported. Pilot is a sanity
  check, not a fresh test of the framework's core claim.
- The full DCD1 outcome. That requires the full corpus.
- Cross-case generalisation. The pilot is one case, one subset.
