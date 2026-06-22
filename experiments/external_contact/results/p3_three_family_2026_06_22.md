# External Contact P3c-3way — Cross-Family Concept Geometry (GloVe + fastText)

Date: 2026-06-22
Code: `experiments/external_contact/p3_glove_probe.py` (extended for `--glove3` 3-family panel; commit prior to this report)
Fetcher: `scripts/fetch_fasttext_subset.py`
Pre-registration amendment: 3-family P3c — *frozen before fastText vectors were fetched and the panel was run* — requires the **minimum** pairwise RSA across all three external families >= 0.6. This strictly tightens the original P3c (which only required GloVe-300d vs GloVe-100d RSA >= 0.6).
Artifact: `artifacts/external_contact/p3_three_family.json` (gitignored)
Sources:

- Stanford GloVe 6B (Pennington, Socher, Manning 2014). Already used in the P3 result; subsets vendored at `experiments/external_contact/p3_glove_subset_{300,100}d.txt` (gitignored).
- fastText `wiki-news-300d-1M` (Bojanowski et al. 2017; Wikipedia + UMBC + statmt.org news, 1M words, 300d). Independent training corpus from GloVe. Subset vendored at `experiments/external_contact/p3_fasttext_subset_300d.txt` (gitignored).

## Question

P3 (GloVe, 2026-06-22) showed the lab's authored concept-geometry structure survives on a single external embedding family (GloVe), across its 300d and 100d dimensionalities. The cloud-agent's handoff explicitly noted this leaves the cross-substrate convergence claim with only **two within-family dimensionalities** rather than independent training pipelines, and pre-registered the upgrade: add a third external family (e.g. fastText) BEFORE running, and require the MINIMUM pairwise RSA across all three families >= 0.6. Does the concept-geometry pillar survive *cross-family* contact?

## Commands

```bash
python3 -m experiments.external_contact.p3_glove_probe --self-test   # math validation
python3 scripts/fetch_fasttext_subset.py                              # ~650 MB zip
python3 -m experiments.external_contact.p3_glove_probe \
    --glove experiments/external_contact/p3_glove_subset_300d.txt \
    --glove2 experiments/external_contact/p3_glove_subset_100d.txt --label2 glove-100d \
    --glove3 experiments/external_contact/p3_fasttext_subset_300d.txt --label3 fasttext-300d \
    --out artifacts/external_contact/p3_three_family.json
```

The fastText fetch covered 398/399 needed word types (missing: `underdetermining`, the same token already missing from GloVe). Crucially, fastText *does* have `autopoiesis`, which GloVe was missing — so the fastText-alone runs cover all 24 concepts (vs the 23/24 of the GloVe-only P3 run), and the 3-family RSA is computed over the 23 concepts shared by all three families.

## Result

| Gate | Pre-registered threshold | Result | Verdict |
|---|---|---:|---|
| **P3a centered within-across margin** (primary = GloVe-300d, 23/24 concepts) | >= 0.10 | 0.106 | PASS (unchanged from P3) |
| **P3a clustering NMI vs authored categories** (GloVe-300d) | >= 0.25 | 0.531 | PASS (unchanged) |
| **P3b centered paraphrase gap** (GloVe-300d) | >= 0.15 | 0.252 | PASS (unchanged) |
| **P3c-3way min pairwise RSA** (GloVe-300d, GloVe-100d, fastText-300d) | >= 0.60 | **0.346** | **FAIL** |
| P3c-3way mean pairwise RSA (for reference) | — | 0.546 | — |

### Pairwise RSA panel (23 shared concepts, off-diagonal cosine matrices, post centering)

| Pair | RSA | Notes |
|---|---:|---|
| GloVe-300d vs GloVe-100d | **0.747** | within-family (same training, different dim) — the original P3c result |
| GloVe-300d vs fastText-300d | **0.543** | cross-family, same dim, different corpus |
| GloVe-100d vs fastText-300d | **0.346** | cross-family, different dim, different corpus |

### fastText alone (P3a / P3b probe on a non-LLM substrate the lab did not build)

| Gate | Pre-registered threshold | fastText-300d result | Verdict |
|---|---|---:|---|
| P3a centered within-across margin | >= 0.10 | **0.073** | **FAIL** (below threshold by 0.027) |
| P3a clustering NMI vs authored categories | >= 0.25 | 0.539 | PASS |
| P3b centered paraphrase gap | >= 0.15 | 0.260 | PASS |

Raw-vs-centered for fastText:

| Metric | Raw | Centered |
|---|---:|---:|
| P3a within-across margin | 0.041 | 0.073 |
| P3b paraphrase gap | 0.042 | 0.260 |

## Interpretation — what was falsified, what survived

This is a **partial falsification** of the program's first external-load-bearing episode. The 3-family pre-registered upgrade was designed to be the strictest cross-substrate convergence test the lab has run; the result is honest and *should* shrink the allowed claim from P3.

1. **The within-family concept-geometry signal survived again.** P3a (margin + NMI) and P3b (paraphrase gap) still pass on GloVe-300d unchanged. The original P3 result is not retracted.
2. **The cross-substrate convergence claim weakens significantly.** RSA between independently-trained embedding families (GloVe vs fastText, different corpora) drops to 0.35–0.54, *below* the pre-registered 0.6 threshold. The 0.747 between GloVe-300d and GloVe-100d was largely a within-family effect, not a Platonic-convergence signature.
3. **fastText alone gives a mixed signal:** clustering NMI (0.539) still recovers the lab's authored categories well, the paraphrase gap (0.260) still beats the wrong-orbit control comfortably, but the per-pair within-across margin (0.073) falls short of the >= 0.10 threshold. The categorical block structure exists in fastText, but the *per-pair* signal is closer to noise.
4. **The honest direction:** the concept-geometry pillar is not as substrate-independent as the original P3 result suggested. It survives external contact with one non-lab embedding family (GloVe) cleanly. It survives external contact with a second non-lab family (fastText) *partially* (NMI + paraphrase yes; per-pair margin no). It does **not** survive the strict 3-family cross-substrate RSA threshold.

### Allowed claim (post-amendment)

The original P3 (2026-06-22) claim was **mechanism -> regime transition / external load-bearing**. After the 3-family amendment that claim narrows: **regime transition / partial external load-bearing (substrate-sensitive)**. The clean version of the field claim — "the lab's authored concept geometry is a substrate-independent Platonic-convergent structure" — does *not* survive contact with fastText. The lab's geometry is real in one external substrate (GloVe) and *partially* real in a second (fastText categorical structure yes, per-pair margin no), with cross-family RSA weak.

This is not the program's first hard kill, but it is the program's first clear **threshold-narrowing falsification** under external contact: the kill is in the direction the cloud-agent's handoff anticipated ("one external pass is 'the concept-geometry pillar isn't an OpenAI/self-built artifact' — genuinely good, but a single point").

## Discovery-Regime Audit

- **Old regime:** P3 (2026-06-22 GloVe result) established the concept-geometry signal on a single external family (GloVe), across two dimensionalities. Allowed claim: mechanism -> regime transition; cross-substrate convergence ASSUMED to extend from the within-family RSA.
- **Transition:** the same frozen concept/paraphrase artifacts were tested against a third independent embedding family (fastText `wiki-news-300d-1M`) AND the pre-registered 3-way RSA threshold (min pairwise >= 0.6) was applied. The fastText subset was fetched cleanly (398/399 word types) and pooled identically to GloVe (mean-pool over alphabetic tokens, All-but-the-Top centering).
- **Transported evidence:** P3a/P3b thresholds (margin, NMI, paraphrase gap), All-but-the-Top centering, wrong-orbit paraphrase control, and the cross-model RSA over the *shared 23 concepts* (since GloVe was missing `autopoiesis`). The new P3c-3way threshold and the fastText fetch infrastructure are deterministic and committed BEFORE the panel run.
- **Rejected alternatives:** "the GloVe-300d vs GloVe-100d RSA = 0.747 reflects a Platonic-convergent cross-substrate signal" is rejected by the cross-family RSA collapse to 0.35–0.54.
- **Residual finding:** within-family (GloVe-300d) P3a/P3b pass cleanly; within-family RSA across dimensionalities is high; *cross-family* RSA across independent training corpora is weak; fastText alone gives a mixed P3a (margin fail, NMI pass) and P3b pass.
- **Readiness:** P3a/P3b on GloVe unchanged (PASS); P3c-3way FAIL; fastText P3a margin FAIL but NMI/paraphrase PASS.
- **Allowed claim (post-amendment):** **regime transition / partial external load-bearing, substrate-sensitive** — strictly narrower than the original P3's "mechanism -> regime transition". The cross-substrate Platonic-convergence reading is *not* warranted by this 3-family panel.
- **Next operation:** (a) add a fourth independent family (e.g. open-weights MiniLM sentence embeddings) to see whether cross-family RSA recovers when going from static word vectors to contextual; (b) revisit whether the 24-concept set itself is biased toward GloVe's lexical neighborhood (some concepts like "basin of attraction" multi-token pool, which may favor one tokenizer's conventions over another's); (c) the strongest remaining external pillar candidate is P2b (the BatchBALD methodological replication on Kirsch curves) — which is already a clean directional pass.

## Note on the discovery_ews v1 rubric

The "Rejected alternatives" and "is rejected by" language used above is the lab's *positive*-discipline audit convention (alternative hypotheses considered and ruled out by the data) and will continue to trip v1's `\brejected\b` FAILURE regex. Per the discipline established with the P2 report, the regex is left alone (retuning it to flip the verdict would be exactly the metric-gaming the EWS exists to detect). This is the second result in three days where the v1 rubric's regex-over-markdown apophenia flips the verdict away from what the data says; the structured-provenance v2 rewrite remains the clean fix.
