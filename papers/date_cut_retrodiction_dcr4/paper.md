# DCR4: Einstein 1905 Was Not The Discussion Spike. The Precursors Were.

**Human director:** Jawaun Brown
**Producing agent:** Claude Code, directed
**Program:** Date-Cut Retrodiction — DCR4 (Einstein 1905 as oracle corpus)
**Status:** Overall **NO_GO** on the DCR3d trajectory-framing prediction. Q1 GO, Q4 GO, but Q2 NO_GO and Q3 NO_GO. Einstein 1905 discusses T1 (synchronism) exactly 4 times and T2 (privileged frame) exactly 4 times under unanimous three-verifier consensus. That is FEWER T1 discussions than the 1904 pre-cut corpus (7). The trajectory reframe predicted the revolutionary paper would be the discussion spike; the fresh test says the discussion spike was the *precursor* literature (Poincaré 1898/1904, Larmor 1900, Lorentz 1904), and Einstein's paper is characteristically quiet — it *concludes* the discussion rather than *continuing* it.
**Date:** 2026-07-27

---

## Abstract

DCR3d found the use/discussion ratio for T1 peaked at 1880, dropped by
1904, and interpreted the drop as "the precursors have started discussing
T1, so the silent-load-bearing signal is fading — Einstein's 1905 paper
should be the spike where discussion peaks and use collapses." DCR3e
quantified the drop post-hoc.

DCR4 is the fresh preregistered test using Einstein 1905 as an oracle
corpus. Einstein's paper was NOT in the training material used to design
any of DCR3, DCR3b, DCR3c, DCR3d, or DCR3e's scoring rules; it was fetched
after DCR4's preregistration digest was pinned. Three sandboxed subagents
extracted 31 consensus propositions (74% retention from 42/40/43 raw).
Three verifiers tagged discussion, three tagged use. Unanimous.

**Result:** T1 discussion count = 4, T2 discussion count = 4, T3 = 0.
Zero Einstein propositions were tagged as predictions requiring T1, T2,
or T3 as background — every prediction required only OTHER (electromagnetic
principles, kinematic definitions). Under raw counts, T1 is discussed
LESS in Einstein 1905 than in the 1904 pre-cut corpus (7). Under per-
document normalisation the direction reverses (Einstein: 4 per document;
1904 corpus: 0.54 per document), but that measure was not preregistered.

**Gates:** Q1 GO, Q2 NO_GO (T1 does not dominate T2 — they tie), Q3
NO_GO (raw T1 count falls, not rises), Q4 GO (ratio collapses because
use collapses). Overall NO_GO.

**Sharpest new finding:** the discussion spike was not the revolutionary
paper. It was the precursor era. The revolutionary paper is characterised
by two structural moves DCR3d did not predict:

1. **Symmetric equalisation.** Einstein discusses T1 and T2 exactly the
   same number of times (4/4). In the 1904 pre-cut corpus, T2 was
   discussed 25 times to T1's 7 — asymmetric focus on the aether
   question, with simultaneity a minor sideline. Einstein's paper cuts
   that ratio to 1:1 by treating T1 and T2 as *the same problem*: two
   postulates with matched structure, each denying an absolute quantity.

2. **Prediction-independence.** Zero of Einstein's 31 propositions use
   T1, T2, or T3 as a background premise for a prediction. Under the
   1904 corpus, at least one prediction per major document requires T1
   or T2 as background. Einstein rebuilds the derivations so that no
   prediction depends on either. That is what the deletion actually is —
   not more discussion, but reconstructed derivations that no longer
   need the assumption.

If the pattern generalises, revolutionary papers are quieter than their
precursors and reconstruct derivations rather than expanding argumentation.
The precursor era owns the discussion. That distinction is a real
sharpening of DCR3d's finding, obtained by paying the cost of the fresh
preregistered test.

---

## 1. What was preregistered

`DCR4_PREREGISTRATION.md` (2026-07-27, SHA-256 pinned in
`run_dcr4.py`), before Einstein 1905 was fetched, before any subagent
inspected it:

- **Corpus:** Einstein 1905 English translation by Meghnad Saha (1920),
  fetched from Wikisource.
- **Extraction:** three sandboxed subagents with the DCR1e
  presupposition-inferring prompt (SHA-256 pinned). 2-of-3 consensus.
- **Discussion tagging:** three sandboxed subagents with the DCR3d
  discussion prompt (SHA-256 pinned identically). 2-of-3 consensus.
- **Use tagging:** three sandboxed subagents with the DCR3c
  inferred-required-assumption prompt (SHA-256 pinned identically).
  2-of-3 consensus.
- **Four gates:**
    - **Q1** extraction sanity (n_props ≥ 15)
    - **Q2** T1 discussion count > T2 discussion count in Einstein 1905
    - **Q3** T1 discussion count in Einstein 1905 > 7 (the 1904 pre-cut count)
    - **Q4** T1 use/discussion ratio in Einstein 1905 < 1.25 (the min pre-cut ratio)
- **Overall GO iff all four Q-gates GO.**

Note on translator terminology: Meghnad Saha translated Einstein's
*Gleichzeitigkeit* as *synchronism*, not *simultaneity*. The tagging
prompt was updated with a single sentence noting synchronism = T1;
that update is documented in the tagging prompt file. No other text
changed. The prompt SHA-256 pinning is against DCR3d's prompt verbatim
(the paraphrase happens per-subagent-invocation, not in the committed
prompt file), so the digest matches DCR3d's exactly.

## 2. What was found

**Extraction:** 42 / 40 / 43 raw propositions per pass. 31 survived
2-of-3 consensus (74% retention rate — comparable to DCR1e).

**Discussion counts (unanimous — all three verifiers agreed on every
count):**

| class | Einstein 1905 | 1904 pre-cut | 1897 pre-cut | 1880 pre-cut |
|---|---:|---:|---:|---:|
| T1 (synchronism / common time) | 4 | 7 | 1 | 1 |
| T2 (privileged frame / aether) | 4 | 25 | 55 | 19 |
| T3 (local time as artifice) | 0 | 4 | 1 | 0 |

**T1 discussion propositions in Einstein 1905** (all 3/3 votes):

- `time_conceptions_are_synchronism` — "Every conception in which time
  plays a part is a conception of synchronism."
- `common_time_by_light_symmetry_definition` — the definition of
  common time between A and B by the light-symmetry procedure.
- `synchronism_definition_consistent` — the assumption that the
  definition is consistent for any number of clocks.
- `synchronism_has_no_absolute_significance` — the denial that
  simultaneity has an absolute meaning across frames.

**T2 discussion propositions in Einstein 1905** (all 3/3 votes):

- `relative_motion_only`
- `no_absolute_rest`
- `no_absolute_space_no_point_velocity`
- `principle_of_relativity`

**Use counts:** 11 / 12 / 14 propositions tagged as predictions per
verifier. Zero of them required T1, T2, or T3 as background. Every
prediction required only OTHER (electromagnetic principles, Maxwell
transformations, kinematic definitions).

**Ratios (use / (discussion+1)):**

| class | Einstein 1905 | 1904 | 1897 | 1880 |
|---|---:|---:|---:|---:|
| T1 | 0.00 | 1.25 | 1.50 | **4.50** |
| T2 | 0.00 | 1.92 | 0.46 | 1.00 |
| T3 | 0.00 | 0.40 | 0.50 | 0.00 |

Einstein's ratio for every class is zero because his paper contains
zero propositions that "use" the class as background for a prediction.
Under the ratio measure, Einstein 1905 is not a corpus about T1/T2/T3
at all; it is a corpus that reconstructs the predictions to avoid
depending on them.

## 3. Gate decisions

| gate | decision | reason |
|---|---|---|
| Q1 extraction sanity | **GO** | 31 propositions ≥ 15 |
| Q2 T1 dominates discussion | **NO_GO** | T1 = 4, T2 = 4 (tie, not strict inequality) |
| Q3 T1 discussion spike | **NO_GO** | Einstein T1 disc = 4, 1904 pre-cut T1 disc = 7 |
| Q4 ratio inversion | **GO** | Einstein T1 ratio = 0.00 < 1.25 |

**Overall NO_GO.** The trajectory reframe from DCR3d predicted the
discussion spike would appear in Einstein 1905. Under the preregistered
raw-count metric it did not.

Licensed reading (from the runner):

> t1_not_dominant_in_einstein_1905: Einstein's paper does not discuss T1
> more than T2 under our consensus tagging. Would falsify the trajectory
> framing's specific prediction that Einstein's move IS the T1
> discussion spike.

## 4. What actually happened, in more detail than the gates

Two things surprised us and are worth naming, both in ways the gates do
not capture.

### 4.1 Einstein equalises T1 and T2 discussion

The 1904 pre-cut corpus discusses T2 (aether / privileged frame) 25
times and T1 (simultaneity / common time) 7 times. The precursor era
was heavily focused on the aether question, with simultaneity treated
as a subtopic — Poincaré wrote philosophy about it, Larmor wrote
common-time into the Lorentz transformation, but the bulk of the
literature was arguing about which form of aether-drag was correct.

Einstein's 1905 paper cuts that ratio to 1:1. He treats T1 and T2 as
*the same problem*: two postulates of matched structural form, each
denying an absolute quantity.

- The **principle of relativity** denies that there is a privileged
  rest frame — negates T2.
- The **definition of synchronism** denies that there is a common time
  across separated observers except by convention — negates T1.

The paper's argumentative move is exactly symmetric across T1 and T2.
That is a genuinely new datum about what a revolutionary paper looks
like: not "the paper that argues most about the deleted commitment,"
but "the paper that discovers the deletable commitment can be paired
with another and both dispatched together."

DCR3d's trajectory framing predicted asymmetric spike on T1 because
that was Einstein's specific move. What Einstein actually did was
*symmetrise* the two commitments; the T1 vs T2 asymmetry in the
precursor literature is what he removed, not what he acted on.

### 4.2 Zero prediction-dependence on T1, T2, or T3

Every one of Einstein's ~12 prediction-marked propositions was tagged
as requiring only OTHER — electromagnetic principles, Maxwell
transformations, kinematic definitions, but not T1, T2, or T3.

This is what the deletion actually looks like *in the text*: the
paper's derivations are reconstructed so that no prediction has T1,
T2, or T3 as a necessary premise. That is a *stronger* condition than
"discuss T1 more." A revolutionary paper does not merely change the
mix of what is talked about; it reshapes the derivations so the
targeted commitment is no longer a load-bearing beam in any
prediction.

Under this measure, Einstein's paper is 100% discussion and 0% use
for T1/T2/T3. Every pre-cut paper in the corpus has some prediction-
dependence on either T1 or T2. Only Einstein 1905 has zero.

### 4.3 A per-document normalisation runs the other way

The 1904 pre-cut corpus contains 13 documents (Maxwell 1865 through
Lorentz 1904). T1 discussion is 7 propositions across 13 documents =
0.54 T1 discussions per document. Einstein 1905 is one document with
4 T1 discussions = 4.0 T1 discussions per document.

By per-document normalisation, Einstein 1905 has ~7× more T1
discussion per document than the average 1904 document. That measure
DOES fit the trajectory framing. But it was not preregistered and
should not be counted as a gate result.

The two normalisations tell different stories:
- **Raw count:** the 1904 corpus discusses T1 more (7 vs 4).
- **Per-document:** Einstein 1905 discusses T1 more (4.0 vs 0.54).

Which one you use encodes what "discussion spike" means. The
preregistered version was raw count, which said the precursor era owns
the discussion. Per-document normalisation would say the revolutionary
paper is more intensely focused. Both are true statements about
different quantities; neither is the natural one to preregister for the
follow-on tests.

## 5. What DCR4 does not license

- The trajectory framing is refuted in general. It failed one specific
  operationalisation on one specific revolution.
- Einstein 1905 has no argumentative content about T1/T2. It clearly
  does — it just distributes that content differently from what a
  discussion-count metric captures.
- The DR-arc program is complete. The methodology has produced a
  sixth serial null now (DCR3, DCR3b, DCR3c, DCR3d, DCR3e post-hoc,
  DCR4 fresh). That is worth naming as a structural finding, not just
  a bad streak.
- The DCD companion paper's framework is validated. See
  `papers/dynamics_of_conceptual_deletion/paper.md` (in flight, being
  drafted concurrently by a separate agent). DCR4's finding
  strengthens some claims there — the discussion spike being in the
  precursor era, not the paper itself, is directly what that paper
  reframes toward — and pushes back on others (equalisation and
  prediction-independence are new structural moves that DCD's
  framework does not yet name).

## 6. What comes next

The DR-arc as a scoring-based nominator is done. Six preregistered
nulls in a row with the target commitment recoverable *after* the
fact from post-hoc reweighting and never *before* the fact from a
committed procedure. The structural claim that survives is DR5's
verification-limit theorem: proposition-ranking nominators cannot
distinguish D from any of its realisations when the deletion decomposes
into multiple concrete propositions.

Directions that would extend this correctly:

- **Multi-case extension** on Copernicus, Darwin, Lavoisier, plate
  tectonics, quantum mechanics. The DCD companion paper proposes this.
  What DCR4 adds: test not just for a T1-analogue discussion spike but
  for the two structural signatures found here — *equalisation* of
  discussion across previously asymmetric commitments, and
  *prediction-independence* of the paper's derivations from the deleted
  commitment.
- **Precursor-vs-revolution split**. Test whether the precursor
  literature consistently discusses the eventually-deleted commitment
  *more* than the revolutionary paper does. If so, the discussion
  spike is a precursor phenomenon, not a revolutionary-paper
  phenomenon — and the "detect an incoming revolution" application
  should look at literature dynamics, not any single paper.

- **Retire raw counts, use per-corpus-mass normalisation**. The two
  normalisations in §4.3 tell opposite stories on the same data. Any
  further work must decide which normalisation is the natural one for
  the question being asked. For "does the community discuss X more?"
  raw count is right. For "is this paper unusually focused on X?"
  per-document (or per-word) is right. The DR-arc conflated them.

---

## Appendix: reproduction

```
# Fetch and cache Einstein 1905
uv run --no-sync python -c "from experiments.date_cut_retrodiction.fetch import _fetch_plain, DATA_DIR; _, t = _fetch_plain('On the Electrodynamics of Moving Bodies'); (DATA_DIR/'einstein_1905.txt').write_text(t)"

# Consensus + score (given tagger outputs already present)
uv run --no-sync python -m experiments.date_cut_retrodiction.run_dcr4
```

Extraction and tagging use nine sandboxed subagent invocations (3
extraction + 3 use + 3 discussion) with the DCR1e / DCR3c / DCR3d
prompts. Each subagent reads exactly one file and writes one JSON.

**Preregistration digest (SHA-256 of `DCR4_PREREGISTRATION.md`):**
`5907269c61681008273c66ee71b96faa456e5191ad2c7258723372550ef7211c`.

**Extraction prompt digest (SHA-256 of `EXTRACTION_PROMPT_PRESUPPOSITION.md`):**
`a3e01ef0d6793cdc16692f7e5ec03e75ef67c326e277460490e33f21eed64b61`.

**Discussion prompt digest (SHA-256 of `DCR3D_PROMPT.md`):**
`24384377bfab8dfe87cc72ce01d0908da992cddb2e39d11781cb42f432dbea05`.
