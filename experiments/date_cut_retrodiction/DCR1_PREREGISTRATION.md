# DCR1 — Is the Extractor Leaking?

**Package:** `experiments/date_cut_retrodiction/`
**Predecessor:** DR4 (all four gates GO, opening the retrodiction)
**Human director:** Jawaun Brown
**Date:** 2026-07-25

## 0. Freeze status

Written while the fifteen extraction agents were running and **before any
extraction output was read**. `target.py`, which defines what counts as a hit,
was committed in the same state. The corpus was fetched, audited and frozen
beforehand; §3 records what that audit found, including one thing that would
have invalidated the whole experiment had it gone unnoticed.

DR3 froze gates in code and wrote its document afterwards. DR4 fixed the order.
DCR1 keeps it.

## 1. What DCR1 is and is not

DCR1 is **not** the retrodiction. It is the precondition check that decides
whether the retrodiction is worth running at all.

The retrodiction asks whether an execution-free nominator, given only what was
public before Einstein's June 1905 submission, ranks the deletion history
actually made. Its obvious failure mode is that the *extractor* — a language
model that has read the twentieth century — already knows the answer and hands
it over dressed as a candidate. That is Spencer's candidate-selection
circularity, and it is what killed COGR Wave 1a: `info_matched_recency`
reproduced an oracle ceiling byte-for-byte because load-bearing memory happened
to be systematically most recent.

If the extractor leaks, nomination ranking measures nothing. So DCR1 runs the
extractor and asks one question: **does it surface the target family because the
corpus contains it, or because the model does?**

## 2. Design

**Extraction is per-document and cut-blind.** Each of the fifteen documents is
extracted exactly once, by an agent that is never told the year, never told
which cut the document belongs to, never shown another document, and never told
what the research question is. The prompt is recorded verbatim in
`EXTRACTION_PROMPT.md` and is byte-identical across all fifteen.

Cuts are composed **afterwards**, from per-document outputs. This is the design's
main structural guarantee: the extractor cannot tailor its behaviour to a cut,
so whatever hindsight it imports, it imports equally at 1880, 1897 and 1904.
That is precisely the condition under which a placebo comparison is diagnostic.

**Three cuts** (`cuts.py`):

| year | role | why |
|---|---|---|
| 1880 | deep placebo | Maxwell only. No ether-drift null result exists yet. Nothing poses the problem the target deletion answers. |
| 1897 | near placebo | Null results are in; FitzGerald has proposed contraction. Lorentz 1904 and Poincaré 1904 are absent. |
| 1904 | target | Everything public before June 1905. Both halves of the tension present; deletion not made. |

**The target family** (`target.py`, fixed before any output was read): T1
absolute simultaneity, T2 privileged aether frame, T3 local time as artifice. A
cut surfaces the target when propositions matching **at least two of three**
facets are present. Matching is regex over `name` and `statement` only, never
over `quote` — a document must not score by discussing a topic, only by the
extractor having isolated a commitment.

## 3. What the corpus audit already found

Three results, all obtained before extraction and all consequential.

**The corpus arrived contaminated.** Wikisource's header template links every
one of these papers to `Portal:Relativity`. Eleven of fifteen documents carried
post-cut vocabulary in their first line. Fixed structurally — the fetcher now
takes the Proofread-Page body container and drops navigation chrome — not by
keyword, for the reason immediately below.

**A keyword filter would have been wrong in both directions.** Larmor 1897's
"any *special theory* of the constitution of matter" is innocent period English.
Poincaré's St Louis lecture of September 1904 states "The principle of
*relativity*, according to which the laws of physical phenomena must be the same
for a stationary observer as for an observer carried along in a uniform motion
of translation" — he coined the phrase, pre-cut. A blocklist deletes the real
thing and keeps the fake. Residue is therefore defined relationally in
`residue.py`: a term is residue iff the extractor emits it and the corpus at
that cut does not contain it.

**Every sentinel term at the 1904 cut rides on two documents.**
`relativity`, `postulate`, `simultaneity`, `simultaneous` appear only in the two
Poincaré texts, both reached through Halsted's 1913 English compilation. Drop
them and the target vocabulary vanishes:

| cut | docs | chars | sentinels present |
|---|---:|---:|---|
| 1880 | 3 | 82,321 | — |
| 1897 | 8 | 266,186 | — |
| 1904 | 15 | 495,516 | relativity, postulate, simultaneity, simultaneous |
| 1904 without the two risky docs | 13 | 456,837 | — |

A 1913 translator knew about 1905. Checked against the French originals
(`provenance_check.py`): *La mesure du temps* (1898) has `simultanéité` ×8,
`simultané` ×17, `postulat` ×10; *La Valeur de la Science* ch. VIII has
`principe de relativité` ×5, `temps local` ×2, `éther` ×16. **The translation is
exonerated.** Every analysis nonetheless runs twice, with and without those two
documents — clearing lexical risk does not clear editorial framing, and the dual
run costs nothing.

## 4. Gates

- **G1 — quote fidelity.** At least 90% of extracted propositions carry a quote
  that appears in its source document under whitespace normalisation. Below
  that, the extractor is confabulating and nothing downstream is trustworthy.
- **G2 — vocabulary residue.** Residue rate below 5% of output word types at
  every cut. The prompt forbids vocabulary the document lacks; this measures
  compliance.
- **G3 — deep placebo is silent.** The 1880 cut does **not** surface the target
  family. A hit at 1880, where Michelson had not yet run his first experiment,
  cannot be anything but the model supplying what the corpus does not.
- **G4 — target cut is not silent.** The 1904 cut **does** surface the target
  family. Without this there is no signal to rank and the retrodiction is moot.

**G3 is the gate that matters.** G1 and G2 are hygiene; G4 only establishes
that something is there to measure. G3 is the one that can tell us the entire
programme is measuring the model rather than the corpus.

## 5. Outcomes and what each licenses

- **G1–G4 all pass.** The extractor tracks the corpus. DCR2 — nomination
  ranking over the real proposition set — is licensed.
- **G3 fails (1880 surfaces the target).** The extractor is leaking. DCR2 is
  **not** licensed by any repair to the ranking machinery, because the defect is
  upstream of ranking. The honest response is to report the leak and redesign
  extraction, exactly as Wave 1a's KILL forced a redesign rather than a retune.
- **G4 fails (1904 silent).** Either extraction is too coarse or the corpus is
  too thin. This is a finding about instrumentation, not about the framework,
  and it names its own repair.
- **G1 or G2 fails.** Extraction is unreliable; fix it before reading anything
  else, and do not report facet results from an unreliable extraction.

The 1897 near-placebo has **no gate**. It is nested between the other two and is
recorded as a graded observation, not a pass/fail. Placing a threshold on it
would be inventing a criterion for a quantity I have no calibrated expectation
for — the DR3 mistake.

## 6. Scope

Fifteen documents, one language model as extractor, one regex matcher for
scoring. DCR1 says nothing about whether concern-gated or weakness-based
nomination works on real material. It says only whether the pipeline that would
feed such a test is measuring the corpus or the model.

Single-shot. No replay knobs. If a gate fires, it fires.
