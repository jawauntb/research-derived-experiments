# DCR1d — Positive Control: Does the T1 Matcher Fire on Newton's Scholium?

**Package:** `experiments/date_cut_retrodiction/` (positive-control extension)
**Predecessor:** DCR1c (H1–H6 GO, DCR2 licensed; T1 matched zero at every cut)
**Human director:** Jawaun Brown
**Date:** 2026-07-27
**Written:** BEFORE `run_dcr1d.py` is executed (repairs the DR3 slip)

## 0. The question this run answers, and only this one

DCR1c passed every gate and reported one thing that did not fit: T1 (absolute
simultaneity) matched **zero** propositions at every cut, under both v2 and v3,
across all three sandboxed extractions. The corpus surfaces the privileged
aether frame in many ways and Lorentz's local time in one. It does not surface
"time is the same for everybody" as an explicit commitment. Two readings, and
DCR1c refused to decide between them:

1. **The matcher can't do the job.** The T1 pattern is too strict, or the
   extractor doesn't emit propositions in a shape the pattern accepts.
2. **The commitment isn't stated in the corpus.** The electrodynamics-era
   physics literature had internalised absolute simultaneity to the point of not
   writing it down, and that silence is why the deletion was available for
   Einstein to make.

DCR1d is the single experiment that discriminates them. It uses a document that
**does** state absolute time and space as explicit commitments in the exact
words the matcher was built to catch — Newton's Scholium to the Definitions
in *Principia Mathematica* (Motte 1729 translation), 1687.

If the matcher works, T1 must fire on Newton. If it doesn't, reading 2 has no
purchase — it would just be excusing a broken instrument.

## 1. What is added, and what is untouched

**Added:**

- One source, `newton_1687_scholium`, fetched from Wikisource
  (Motte 1729 translation, 1846 Chittenden edition) into the same data
  directory as the DCR1c corpus.
- One cut, `Cut(year=1687, kind="positive_control")`, evaluated only by the
  DCR1d runner. `CUTS` in `cuts.py` is not edited so DCR1c's numbers do not
  drift.
- Three sandboxed subagent passes on Newton, one at a time, using the
  DCR1c-verbatim `EXTRACTION_PROMPT.md` with the pass-2 amendment forbidding
  any repository file access. Consensus is 2 of 3, same as DCR1c.
- A new runner, `run_dcr1d.py`, that scores only the 1687 cut.

**Not changed:**

- `target_v3.py`, `target_v2.py`, `residue_v2.py`, `consensus.py`,
  `corpus.py` (except for appending one SourceSpec), `cuts.py` (unchanged),
  `run_dcr1.py`, `run_dcr1b.py`, `run_dcr1c.py`. DCR1c's published
  reproduction command produces DCR1c's published numbers, byte-identical.

The corpus of record for DCR1a/b/c is unaffected by anything DCR1d does.

## 2. Gates

Three gates. All three must decide GO for the matcher to be validated.

- **P1** quote fidelity on Newton ≥ 90% (same threshold as H1)
- **P2** vocabulary residue on Newton < 5% (same threshold as H2, with
  `residue_v2`; a period-appropriate baseline for 1687 English)
- **P3** T1 fires at least once at the 1687 cut under either `target_v2` or
  `target_v3`, with the matched proposition surviving an individual read

**P3 is the load-bearing gate.** P1 and P2 are hygiene: they say the extraction
worked at all on unfamiliar (17th-century) prose. If they fail, P3 is
uninterpretable and the run is inconclusive rather than negative.

## 3. Decision table — what each outcome licenses

| P1 | P2 | P3 | verdict | licenses |
|---|---|---|---|---|
| GO | GO | GO | **Matcher validated.** DCR1c's T1 absence is a fact about the electrodynamics corpus, not the instrument. | DCR1e — a presupposition-inferring extractor targeting the electrodynamics corpus. DCR2 remains licensed but becomes a narrower question. |
| GO | GO | NO_GO | **Matcher bug.** The pattern does not fire on the sentence it was built for. | An immediate matcher repair; nothing else runs on the current matcher until fixed. DCR2 is de-licensed pending repair. |
| NO_GO on P1 or P2 | | | **Inconclusive.** The extractor did not produce clean output on 17th-century prose; P3 is uninterpretable. | Fix extraction on Newton (better prompt for the register, or a different source), then re-run. |

The one thing this run **cannot** license is a claim about historical presupposition dynamics on general grounds. It only says whether the matcher does its stated job.

## 4. What DCR1d does not test

- Whether an extractor asked "what does this reasoning *require*?" surfaces
  presuppositions from the electrodynamics corpus. That is DCR1e's question.
- Whether Newton's absolute simultaneity is *the same* commitment Einstein
  deleted. Absolute time in the scholium is a metaphysical statement about
  duration; Einstein's deletion is about simultaneity across separated
  observers. They are related but not identical. This run only asks whether
  the matcher fires on the sentence it was written to catch.
- Anything about the DCR1c corpus of record. Its numbers are frozen.

## 5. Single-shot commitment

One extraction run. One matching run. One adjudication of P3 if it fires. The
result is written to `results/dcr1d_verdict.json` and reported as-is.

No replay knobs. If P3 fails, the next step is repair, not re-scoring.
