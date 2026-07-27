# DCR1e — Can Any Extraction Surface an Unstated Presupposition?

**Package:** `experiments/date_cut_retrodiction/` (presupposition-inferring extension)
**Predecessor:** DCR1d (positive control GO — T1 matcher validated on Newton; DCR1c's T1 absence is historical, not instrumental)
**Human director:** Jawaun Brown
**Date:** 2026-07-27
**Written:** BEFORE `run_dcr1e.py` is executed and BEFORE any extraction is spawned.

## 0. The question

DCR1c/d together left one question standing that neither can answer:

> If a load-bearing commitment is a presupposition too deep to state, can any
> extraction surface it? Or is nomination over extracted sets structurally
> blind to the deletions that matter?

DCR1e is the first experiment aimed directly at that question. It runs a
**different extraction prompt** — one that asks each document's reasoning
what it *requires* rather than what it *states* — against the same
corpus as DCR1c. If a presupposition-inferring extractor surfaces T1 from
documents that use light-travel-time-between-observers arguments (Michelson
1881 and later) *and* stays silent on the 1880 deep placebo, then extraction
can reach unstated presuppositions and DCR2 becomes meaningful. If it either
stays silent at 1897 or fires at 1880, the answer is different and this
paper says so.

## 1. What is added, and what is untouched

**Added:**

- **`EXTRACTION_PROMPT_PRESUPPOSITION.md`** — a new extraction prompt asking
  the model to reverse-engineer commitments from arguments. Sandboxed
  (read-only the named file) exactly as DCR1c's pass-2/3/4 prompts. The
  prompt names *multiple* facets to look at (time, space, measurement
  combination, coordinates) so no single target facet is pointed at. The
  1880 placebo is the check on whether those hints leak.
- One new module `dcr1e.py` defining the corpus (15 DCR1c docs + Newton as
  a sanity control), the pass directories (`extractions_presup_pass{1,2,3}`),
  and the consensus directory (`extractions_presup_consensus`).
- Three sandboxed subagent passes, one at a time, on each of the 16 documents
  = 48 sandboxed extractions. Consensus 2-of-3, same as DCR1c.
- A new runner `run_dcr1e.py` that imports every threshold from `run_dcr1.py`
  as a constant so nothing here can be threshold-fitted.

**Unchanged:** `SOURCES`, `CUTS`, `target_v2.py`, `target_v3.py`,
`residue_v2.py`, `consensus.py`, `EXTRACTION_PROMPT.md`, `run_dcr1.py`,
`run_dcr1b.py`, `run_dcr1c.py`, `run_dcr1d.py`. DCR1a/b/c/d reproduction
commands all produce their published numbers, byte-identical.

## 2. Gates

Six gates, all must decide GO for the overall verdict to be GO. The gates
are chosen so that a null result on Q3 is also a real finding — the
presupposition-extraction reading is falsifiable here, not just something to
confirm.

- **Q1 quote fidelity** ≥ 90% (imported constant, same as DCR1a/b/c)
- **Q2 vocabulary residue** < 5% at every cut (imported constant)
- **Q3 T1 fires at the 1897 cut** — the presupposition extractor surfaces
  absolute simultaneity from a corpus that never explicitly states it, at a
  cut where light-travel-time-between-observers arguments are all present
  (Michelson 1881, Michelson-Morley 1887, FitzGerald 1889, Larmor 1897, Lodge
  1897). This is the load-bearing gate.
- **Q4 T1 stays silent at the 1880 deep placebo** — Maxwell alone, no
  light-travel-time-between-observers arguments in the corpus. **Any T1 hit
  here indicates the extractor is projecting knowledge forward through the
  prompt's hints, and Q3 is uninterpretable.**
- **Q5 T1 hit at 1897 (if any) survives an individual read** — the quote
  must be a sentence whose interpretation actually requires absolute
  simultaneity, not a sentence that names it (else it would just be
  restating what DCR1c already knows). Adjudicated by hand, following DCR1b's
  read-every-hit discipline.
- **Q6 sanity control on Newton (1687)** — DCR1e should surface T1 on
  Newton's Scholium, since it both states and presupposes absolute time. If
  it fails here, the prompt is broken and everything else is uninterpretable.

## 3. Decision table — what each outcome licenses

| Q1–Q2 | Q3 | Q4 | Q5 | Q6 | verdict | licenses |
|---|---|---|---|---|---|---|
| GO | GO | GO | GO | GO | **Presupposition extraction works.** The framework can reach unstated commitments. | **DCR2** on the enriched consensus, with a real chance of measuring the deletion Einstein actually made. |
| GO | GO | **NO_GO** | any | any | **Extractor is projecting.** T1 fired at a cut where the arguments requiring it do not exist. | Prompt repair; DCR1e re-run with the leaking hint removed. Not a framework result. |
| GO | **NO_GO** | GO | n/a | GO | **DR2-shaped framework limit is real.** The prompt was strong enough to surface T1 on Newton but not on the electrodynamics corpus where the presupposition is used but not stated. | A theorem-shaped follow-up: prove or characterise what class of presuppositions is structurally unreachable to extraction-then-nomination. DCR2 becomes a much narrower question. |
| GO | GO | GO | **NO_GO** | GO | **Matcher fires but the hit is not a genuine presupposition surfacing.** | Report and treat as evidence for the framework-limit reading, weighed against Q3's GO. Depending on the specific failure mode, either repair the extractor's presupposition-surfacing target or accept the framework limit reading. |
| NO_GO on Q1 or Q2 | | | | | **Inconclusive** — extractor did not produce clean output. | Fix extraction, re-run. |
| any | any | any | any | **NO_GO** | **Prompt broken.** | Repair the prompt and re-run everything. |

The specific reading these gates license is the meaningful next step. That
reading is fixed here, before extraction, so the choice cannot drift once
results are in.

## 4. What DCR1e does not test

- Whether DCR1c's *stated* commitments are correct. That was DCR1c's
  question and it passed all six gates.
- Whether nomination-and-ranking works. That is DCR2's question. DCR1e only
  asks whether the candidate set can, in principle, contain the load-bearing
  deletion.
- Whether Newton's absolute time is the same thing as Einstein's absolute
  simultaneity. Historically continuous, philosophically distinct.
- Vocabulary extension. Still the standing ceiling of the whole framework.

## 5. Single-shot commitment

One three-pass extraction. One consensus. One matching. One adjudication of
any T1 hit at the 1897 or 1904 cut. Verdict written to
`results/dcr1e_verdict.json`. No replay knobs.

If Q3 is NO_GO, that is a real finding. Do not re-run with a stronger prompt
to convert it into a GO. If the DR2-shaped limit reading is licensed, the
next paper is a theorem, not a hint-tuning exercise.
