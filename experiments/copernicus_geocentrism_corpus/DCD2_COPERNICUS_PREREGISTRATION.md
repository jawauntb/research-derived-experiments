# DCD2 — Copernicus / geocentrism: the first frozen-primary-gate test of S1 and S2

**Package:** `experiments/copernicus_geocentrism_corpus/`
**Program:** Dynamics of Conceptual Deletion (DCD). Copernicus is **Case 1** in
the framework's case list (`papers/dynamics_of_conceptual_deletion/paper.md` §5),
and the **third case built** after Einstein (DCR4) and Darwin (DCD1).
**Date:** 2026-07-28
**Written:** BEFORE any subagent tags any document, and given the knowledge —
from this package's own committed fetch (`results/fetch_summary.json`) — that the
oracle is not yet available (see §1).

## 0. Why this study exists, and what makes it different

DCR4 (Einstein 1905) and DCD1 (Darwin 1859) each *replicated* two structural
signatures of the revolutionary paper — **S1 equalisation** and **S2
prediction-independence**. But:

- In neither study were S1/S2 the preregistered **primary** gate (post-hoc in
  DCR4; exploratory previews P4/P5 in DCD1). So they are a replicated *post-hoc*
  pattern, not a confirmed preregistered result.
- The DCD1 **specificity check** (PR #463,
  `experiments/darwin_species_fixity_corpus/run_specificity_check.py`) then found
  the signatures are **Einstein-unique in the physics corpus but NOT unique to
  Origin in Darwin**: three pre-Origin documents (Erasmus Darwin 1794, Wallace
  1855, Beagle 1845 ch17) fire *both* signatures at the same thresholds. Under the
  operational definition, any paper that discusses the paired commitments without
  leaning on either for a prediction fires both signatures — including speculative
  precursors. **On Darwin the "unique to the revolutionary paper" claim failed.**

DCD2 is the study that turns S1 and S2 into **frozen primary gates with an
explicit uniqueness clause**, on a *fresh* case, precisely to test the question
#463 opened: does the revolutionary paper's structural signature ever hold
*uniquely* outside physics, or is Einstein the only case where it does? The
oracle — Copernicus's *De revolutionibus* Book I — was not used to design S1 or
S2 (those come from Einstein 1905, frozen after Darwin).

## 1. Oracle-availability caveat (load-bearing — the run is currently blocked)

This package's committed fetch (`results/fetch_summary.json`) records that the
oracle, `copernicus_1543_de_revolutionibus_book1`, **fetched 0 characters**: there
is no public-domain English transcription of *De revolutionibus* Book I on
Wikisource main namespace (`n_oracle_substantive: 0`). The precursor corpus that
*did* fetch is cosmological-philosophical (Aristotle *On the Heavens* I–IV,
Maimonides *Guide*, Boethius *Consolation*, Chaucer *Astrolabe*), because the
technical geocentric texts (Ptolemy's *Almagest*, Sacrobosco's *De sphaera*) are
also absent in public-domain English.

Therefore the C0 gate below **STOPs** and DCD2 cannot be scored until a
public-domain English *De revolutionibus* Book I is sourced from outside
Wikisource (Internet Archive / HathiTrust scan of a pre-1928 translation) under a
fresh, dated fetch note. This preregistration + `run_dcd2_copernicus.py` are the
frozen instrument that runs the moment that oracle text exists — exactly the
"downstream P(t) test [that] must be sourced outside Wikisource" the corpus module
docstring anticipates. Freezing the gates now, before the oracle exists, is the
point of a preregistration.

## 2. C-categories (frozen; full text in `DCD2_C_CATEGORIES.md`, SHA-256 pinned)

- **C1 — geocentric position** (Earth central; place privileged). T1 / D1 analogue — the deleted commitment.
- **C2 — geostatic rest** (Earth immobile). T2 / D2 analogue — the paired partner.
- **C3 — celestial/terrestrial essence** (incorruptible circular heavens vs corruptible rectilinear sublunary). T3 / D3 analogue.
- **OTHER** — technique, observation, calendar, incidental theology, etc.

## 3. Corpus

- **Oracle:** `copernicus_1543_de_revolutionibus_book1` (Book I: sphericity of
  universe and Earth; whether/where the Earth moves; the order of the spheres with
  the Sun central). Currently unavailable — see §1.
- **Precursor corpus:** the substantive, non-leak documents in
  `experiments.copernicus_geocentrism_corpus.corpus.SOURCES` — Aristotle *De
  caelo* Books I–IV, Maimonides *Guide* Part I / Part II chapters / Part II
  propositions, Chaucer *Astrolabe*. These are the fetched geocentric-tradition
  texts; the partition is taken from `fetch_summary.json` at score time.
- **Leak-risk texts** (`provenance_risk=True`, excluded from the primary precursor
  set and analysed only in a separate include/exclude pass): the Boethius
  *Consolation* metra/prose that state the heliocentric-adjacent "true Sun"
  imagery.

## 4. Pipeline (identical discipline to DCD1 and DCR4)

- **Extraction:** three sandboxed subagents per document, DCR1e presupposition
  prompt (`experiments/date_cut_retrodiction/EXTRACTION_PROMPT_PRESUPPOSITION.md`,
  used cross-domain as-is, as in DCD1), 2-of-3 consensus by content-stem Jaccard.
- **Discussion tagging:** three subagents, DCR3d prompt, category block replaced by
  the C1/C2/C3 definitions of `DCD2_C_CATEGORIES.md` (SHA-256 pinned). 2-of-3.
- **Use tagging:** three subagents, DCR3c prompt, C-categories substituted. 2-of-3.

Single-shot; all quotes verified verbatim against fetched text.

## 5. Gates

### 5.1 Pre-tagging STOP gates

- **C0 — corpus coverage.** The oracle resolves to substantive English text
  (≥ 2000 chars) AND ≥ 3 substantive non-leak precursor documents. **Currently
  NO_GO** (oracle unavailable, §1). Do not run extraction until C0 is GO.
- **P1 — extraction sanity.** ≥ 5 consensus propositions per document averaged
  across the run corpus.
- **P2 — C-signal exists.** Corpus-wide discussion counts C1 ≥ 3, C2 ≥ 3, C3 ≥ 1.

### 5.2 PRIMARY gates

- **S1 — equalisation.** GO iff **both**: (balance) oracle C1 disc ≥ 3 AND oracle
  C2 disc ≥ 3 AND the two within a factor of 2; and (uniqueness) **no** precursor
  document has both C1 disc ≥ τ AND C2 disc ≥ τ, τ = min(oracle C1, oracle C2).
  The uniqueness clause is the crux #463 identified: it *held* on Einstein and
  *failed* on Darwin. This is the clause DCD2 exists to test on a third case.
- **S2 — prediction-independence.** GO iff **both**: (independence) oracle
  prediction-marked propositions using C1/C2/C3 = 0; and (uniqueness) every
  precursor has a strictly positive C-use fraction (oracle uniquely
  prediction-independent). Pre-committed relaxation, only if the oracle has ≥ 20
  predictions: replace "= 0" with "≤ 10%".

**Case verdict.** S1 GO ∧ S2 GO ⇒ Copernicus is a *third* case where both
signatures hold *uniquely* — which, after #463, would be the first evidence that
uniqueness generalises beyond Einstein. A split (the most likely outcome — see
§7) is itself the finding: it tells us which signature, if any, is
revolutionary-paper-specific outside physics.

### 5.3 NEGATIVE CONTROL (expected to fail)

- **N1 — discussion spike (superseded v1 prediction).** Oracle C1 disc (raw) >
  precursor aggregate C1 disc. Expected NO_GO. A surprise GO — plausible because
  *De revolutionibus* Book I argues the Earth's motion intensely — reopens v1's
  discussion-spike reading *for this case* and is reported, not suppressed.

## 6. Normalisation and variance (frozen)

- Report raw and per-1000-character discussion/use counts. S1/S2 read raw counts
  but must be checked to not flip under normalisation; any flip is reported. N1 is
  raw-count by definition.
- Report per-verifier raw counts alongside 2-of-3 consensus. Any gate whose
  decision flips under substituting a single verifier is flagged **UNSTABLE** and
  is not counted as passed.

## 7. What DCD2 will and will not license

**Will (on S1 GO ∧ S2 GO with the uniqueness clause holding):** the first case
after Einstein where the revolutionary paper's structural signature is *unique* in
its corpus, promoting the signature from "Einstein-only-unique" toward a
regularity.

**Will not:**
- A general law (N would be 3, all natural sciences).
- Anything if C0 fails — an unavailable oracle yields no verdict.
- Rescue of S1's uniqueness if it fails here too: S1 NO_GO on Darwin (#463) plus
  S1 NO_GO on Copernicus would confine the unique structural signature to physics.

## 8. Single-shot

One extraction pass, one tagging pass, one verdict once C0 is GO. If C0/P1/P2
fail, STOP and diagnose before reading S1/S2/N1. The gate thresholds are frozen
and must not be adjusted after any tag is seen.
