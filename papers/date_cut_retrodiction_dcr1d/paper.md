# DCR1d: The T1 Matcher Fires on Newton — Which Means the Silence in 1904 Was Historical

**Human director:** Jawaun Brown
**Producing agent:** Claude Code, directed
**Program:** Date-Cut Retrodiction — DCR1d (positive control)
**Status:** P1, P2, P3 all **GO** — overall **GO**. DCR1c's T1 absence reads as historical, not instrumental.
**Date:** 2026-07-27

---

## Abstract

DCR1c passed every gate and reported one thing that did not fit: T1 — absolute
simultaneity, the facet Einstein actually deleted — matched **zero**
propositions at every cut, across all three sandboxed extractions. The paper
refused to decide between two readings. Either the matcher could not do the
job, or the commitment was not stated in the electrodynamics corpus.

This run decides. It adds one document — Newton's Scholium after the eight
Definitions in Book I of the *Principia* (Motte 1729 translation, 1846
Chittenden edition, 28,896 characters) — and runs the DCR1c pipeline on it,
unchanged.

**All three gates pass.** Three sandboxed extractions produced 51, 44 and 40
propositions. The 2-of-3 consensus retains 38. Quote fidelity is 100%.
Vocabulary residue is 3.4%. And **T1 fires three times** at the 1687 cut,
under both `target_v2` and `target_v3`, on the sentence the matcher was
written to catch.

That closes the DCR1c question in the direction it did not want to close in.
The T1 absence in 1865–1904 was not the instrument failing. The commitment
was there in 1687, stated explicitly by Newton in the vocabulary the matcher
tests for. By the electrodynamics era it had gone silent — presuppositions
have a life cycle, and the deletion Einstein made was available exactly
because absolute simultaneity had passed out of what physicists still wrote
down.

**One bonus finding.** T3 (local time as artifice) also fires on Newton, on
his "mathematical time." That is a false positive on T3 — Newton's
"mathematical time" is not Lorentz's auxiliary variable, and this pattern
looseness is a defect DCR1c never surfaced because the electrodynamics
corpus does not use that phrase. A successor should tighten T3. It does not
touch DCR1c's T3 hit (Lorentz on "local time"), which matches a different
alternative in the same pattern.

---

## 1. What DCR1c left unresolved

DCR1c reported:

> T1 — absolute simultaneity — matches **zero** propositions at every cut, under
> both v2 and v3, across all three passes. It is not that the matcher is too
> strict: v3's T1 was validated to fire on four genuine phrasings including
> "There is an absolute time common to all systems" and "The time is the same
> for a stationary observer as for an observer carried along in uniform motion."
> The corpus does not contain those sentences.

And it listed two readings, refusing to decide:

> 1. **A limit of extraction.** Unstated presuppositions need a different
>    instrument.
> 2. **A limit of the framework.** If the deletions that matter are the ones
>    nobody states, then deletion-repair nomination over an extracted set is
>    structurally unable to find them.

Both readings assume the matcher works. Neither reading is defensible until
the matcher has been shown to fire on the sentence it was written for.

DCR1d supplies that missing test.

## 2. What was added, and what was untouched

**Added.**

- One source, `newton_1687_scholium`. Fetched from Wikisource
  (`The Mathematical Principles of Natural Philosophy (1846)/Definitions`)
  through the same `_fetch_plain` used for the DCR1c corpus. Chrome removed
  structurally. SHA-256:
  `9b3d3a03c330371bc9fb0c866c92b96273824aaa0832f6ff22f7ba42c2da5c2d`.
  28,896 characters. The passage the matcher tests for lives at char 11,853:
  "Absolute, true, and mathematical time, of itself, and from its own nature,
  flows equably without regard to anything external."
- One cut, `Cut(year=1687, label="positive control", is_placebo=False)`.
- Three sandboxed subagent extractions, one per pass, using the DCR1c
  verbatim `EXTRACTION_PROMPT.md` with the pass-2 amendment forbidding any
  repository file access. Consensus is 2 of 3, unchanged from DCR1c.
- One runner, `run_dcr1d.py`, that imports `QUOTE_FIDELITY_GATE` and
  `RESIDUE_RATE_GATE` directly from `run_dcr1.py` so the thresholds cannot
  drift.

**Not changed.** `SOURCES`, `CUTS`, `target_v2.py`, `target_v3.py`,
`residue_v2.py`, `consensus.py`, `run_dcr1.py`, `run_dcr1b.py`,
`run_dcr1c.py`. The DCR1a/b/c corpus of record is byte-identical to before,
and DCR1c's published reproduction command still produces DCR1c's published
numbers.

Two committed regression tests guard the isolation:
`test_dcr1d_positive_control_is_not_in_main_sources` and
`test_dcr1d_positive_control_cut_is_not_in_main_cuts`. If Newton ever leaks
into `SOURCES` or 1687 into `CUTS`, the test suite fails before anything
runs.

## 3. Freeze status

`DCR1D_PREREGISTRATION.md` was written **before** `run_dcr1d.py` was executed.
That repairs the DR3 slip that DCR1c openly carried. The preregistration
declared three gates, an outcome table binding each combination of P1/P2/P3
to a decision, and a single-shot commitment with no replay knobs.

The one thing the preregistration could not do was fit the matcher: `target_v2`
and `target_v3` are unchanged, and the runner imports the two numeric
thresholds. The imported constant is the guarantee.

## 4. Results

| gate | | |
|---|---|---|
| **P1** quote fidelity | **GO** | 100% (38/38) vs threshold 90% |
| **P2** vocabulary residue | **GO** | 3.4% vs threshold 5% |
| **P3** T1 fires at 1687 | **GO** | 3 hits under `target_v2`, 3 under `target_v3` |

**Overall GO.**

**Extraction sizes.** Three sandboxed passes returned 51, 44 and 40 propositions.
Consensus 2-of-3 retains 38 — a 74.5% retention rate, in the same band as
DCR1c's 79.7% on the electrodynamics corpus. The extractor works on
seventeenth-century English at the same reliability it does on nineteenth-.

**Vocabulary residue.** 3.4% flagged tokens: `altitudes`, `goes`, `maybe`,
`needs`, `per`, `reveals`, `scales`, `stay`, `straight`, `transient`. Each
is a modern paraphrase word the extractor introduced. None is post-cut
physics vocabulary — no `relativity`, no `simultaneity`, no `frame`. The
matcher is not being fed 20th-century terms through the back door.

**T1 hits.** All three, verbatim from the consensus:

| pass | statement |
|---|---|
| pass 1 | *Absolute, true, and mathematical time, of itself and from its own nature, flows equably without regard to anything external, and by another name is called duration.* |
| pass 1 | *All motions may be accelerated and retarded, but the true or equable progress of absolute time is liable to no change.* |
| pass 2 | *Absolute, true, and mathematical time flows equably of itself without regard to anything external, and is by another name called duration.* |

Every hit is Newton stating absolute time as an explicit commitment. All
three fire on the leading alternative in `target_v2`'s T1 pattern —
`(absolute|universal)\s+(time|clock…|simultaneit…|duration)` — the exact
alternative that also fires on the four validation phrasings tested in DCR1c
(e.g. "There is an absolute time common to all systems").

**T2 hits.** Two: Newton's *"Absolute space, in its own nature, without
regard to anything external, remains always similar and immovable"* and
his *"Absolute motion is the translation of a body from one absolute place
into another, and relative motion is the translation from one relative
place into another."* T2 is not what P3 tested and both hits are genuine.

## 5. What the outcome means for DCR1c

DCR1c's preregistration decision table binds this run to one specific
consequence:

> **P1 GO, P2 GO, P3 GO → Matcher validated. DCR1c's T1 absence is a fact
> about the electrodynamics corpus, not the instrument. Licenses DCR1e — a
> presupposition-inferring extractor targeting the electrodynamics corpus.
> DCR2 remains licensed but becomes a narrower question.**

That reading is now the one to hold. DCR1c's §6 was correct to worry: the
commitment Einstein deleted is not surfaced by nomination over the DCR1c
consensus, and DCR2 run as specified would answer a narrower question than
the programme aims at.

The follow-up work has a specific shape:

- **DCR1e** — build an extractor whose task is not "list every commitment
  the text asserts" but "list every commitment the text's reasoning requires
  to go through." Score it against the same 15 documents. If it can produce
  a proposition equivalent to "there is an absolute time common to all
  systems" from Michelson 1881 — whose "the time required for light to pass"
  is uninterpretable without absolute simultaneity — then extraction can
  surface presuppositions and DCR2 becomes worth running on the enriched
  consensus.
- **DCR2, deferred until after DCR1e.** Nomination on the current consensus
  can only measure whether the nominators find the *stated* commitments the
  corpus does surface (the privileged aether frame and local time). That is
  worth measuring, but only after DCR1e's outcome is in — otherwise DCR2's
  result would be indistinguishable from a limit its design cannot see.

## 6. A defect the positive control surfaced

T3 (local time as artifice) also fires on Newton — on the same sentence T1
fires on:

> *Absolute, true, and mathematical time, of itself and from its own nature,
> flows equably without regard to anything external.*

The T3 pattern includes an alternative
`(auxiliar…|mathematical|fictitious|artificial|merely)\s+\w*\s*(time|variable|quantit…)`.
Newton's "mathematical time" matches that alternative. It is a **false
positive on T3.** Newton is not saying time is a mathematical artifice — he
is naming the philosophically absolute kind of time to distinguish it from
sensible, apparent, common time. The word `mathematical` is doing the
opposite of what the pattern was written to catch.

This defect existed all through DCR1a/b/c and was invisible because the
electrodynamics corpus does not use the phrase "mathematical time." It is
only visible now because a document that does use it entered the pipeline.

Three things to note about the defect:

1. **It does not touch DCR1c's T3 hit.** DCR1c matched on the alternative
   `local\s+time` — Lorentz's *"the transformed time variable t' may be
   called the local time"*. That is genuine and unaffected by the
   `mathematical` alternative's looseness.
2. **It does touch this run's P3 decision if a stricter reading is taken.**
   P3 as preregistered asks specifically about T1, and T1 fires three times.
   If the question were "does *any* facet fire soundly?", T2 (two genuine
   hits) still passes. T3 alone would be counted a false-positive here. This
   is why the preregistered P3 was the T1 gate, not a facet-quorum gate.
3. **It licenses a matcher tightening.** A successor should narrow T3 to the
   `local\s+time` and `auxiliar…` alternatives, or add a polarity/context
   veto for the `mathematical` alternative. DCR1c's numbers stay reproducible
   under any such change — the `target_v2`/`v3` modules are frozen and the
   repair happens in `target_v4`.

Reporting the defect is not a hedge on the P3 decision. It is what the
positive control was for.

## 7. Scope

DCR1d does not answer whether extraction can surface unstated presuppositions.
It only says the T1 matcher fires on the sentence it was built for, which
means DCR1c's T1 absence is not the instrument's failure. Whether extraction
can be extended to catch what physicists in 1900 had stopped writing down is
DCR1e's question and is not touched here.

It does not test whether Newton's absolute simultaneity is *the same*
commitment Einstein deleted. Newton's scholium is about the metaphysical
character of duration; Einstein's deletion is about the coordination of
distant clocks. The two are historically continuous but not identical. The
match here says only that the matcher fires on documents that state
absolute time as a metaphysical commitment — enough for P3, not more.

It does not disturb DCR1c's numbers. The corpus, the cuts, the consensus
directories, and every matcher module used by DCR1a/b/c are untouched.
DCR1c's published reproduction command still produces DCR1c's published
verdict.

---

## Appendix: reproduction

```
uv run --no-sync python -m experiments.date_cut_retrodiction.run_dcr1d
```

Local CPU, seconds. Reads the three cached sandboxed passes, rebuilds the
2-of-3 consensus, verifies quotes, computes residue, matches under v2 and
v3, and writes `results/dcr1d_verdict.json`. The document itself is at
`data/newton_1687_scholium.txt`; SHA-256 is in the manifest.

Preregistration digest (SHA-256 of `DCR1D_PREREGISTRATION.md`):
`ebe4b9368064cbc5cae002d4c31e1525d24ae8e39607d083379b63dbc8b06721`.
