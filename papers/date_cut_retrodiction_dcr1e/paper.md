# DCR1e: The Extractor Reached the Presupposition. The Matcher Rejected It.

**Human director:** Jawaun Brown
**Producing agent:** Claude Code, directed
**Program:** Date-Cut Retrodiction — DCR1e (presupposition-inferring extraction)
**Status:** Overall **NO_GO**. Q3 (T1 fires at 1897) failed. But the failure is not what I preregistered it would be. The extractor surfaced T1 content in five documents. The matcher — calibrated on explicit statements — refused all of them.
**Date:** 2026-07-27

---

## Abstract

DCR1c/d together left one question standing: *can any extraction surface a
commitment the corpus uses but never states?* DCR1e was designed to answer it.
A new extraction prompt asks each document's reasoning what it *requires*,
not what it *states*. Sixteen documents (fifteen DCR1c documents plus
Newton), three sandboxed passes each, 2-of-3 consensus, target_v3 matching.

**Gates:** Q1 quote fidelity GO (98.6%). Q2 vocabulary residue **NO_GO** at
the margin (5.38% max at electrodynamics cuts vs a 5% gate; Newton at 5.94%).
Q3 T1 fires at 1897 **NO_GO** (zero hits). Q4 T1 silent at 1880 GO
(zero hits, so the placebo cannot rule on extractor projection either way).
Q6 Newton sanity GO (two T1 hits on Newton). Overall NO_GO.

**Then I looked at the extraction outputs and the strict verdict got more
interesting.** The extractor produced *at least five* propositions from
the electrodynamics corpus whose content is exactly T1 — absolute simultaneity
as a used-but-not-explicitly-stated commitment:

| document | proposition (statement) | kind |
|---|---|---|
| Larmor 1900 ch11 | "There is a common time t in which the position of an electron in the moving medium can be compared to its position in the medium at rest at time t minus vx over c squared." | presupposed |
| Lodge 1897 | "The time of journey of light along any given path through any kind of material is perfectly definite and independent of the motion of the material." | asserted |
| Maxwell 1865 pt1 | "There is an instant at which the amount of energy in the whole medium is a definite quantity equally divided." | presupposed |
| Poincaré 1898 | "The astronomers suppose that an eclipse of the moon is perceived simultaneously from all points of the earth." | asserted |
| Poincaré 1898 | "In general the duration of the transmission of a signal is neglected and the two events are regarded as simultaneous." | asserted |

**target_v3 fires on none of them.** Every one contains time/simultaneity
language plus an independence marker (moving, motion, all points, all
observers) plus a sameness/uniqueness marker (common, definite, one instant,
simultaneous). Every one *is* the presupposition Einstein deleted, phrased
the way a presupposition-inferring extractor phrases it.

The matcher was calibrated in DCR1c on explicit statements — *"there is an
absolute time common to all systems"* — and DCR1d validated it against
Newton's explicit *"absolute time"*. Neither of those calibrations tested
the indirect, argument-embedded phrasing DCR1e produced. So the matcher's
patterns were too narrow to catch the content the presupposition-inferring
extractor was designed to find.

Per the DCR1e preregistration §5: *"If Q3 is NO_GO, that is a real finding.
Do not re-run with a stronger prompt to convert it into a GO."* The same
discipline forbids re-scoring with a wider matcher after the fact. This
paper reports the strict NO_GO, the diagnostic, and the next preregistered
step: **DCR1f** — a matcher successor validated against a *held-out* set of
presuppositional T1 phrasings before being turned loose on DCR1e's data.

The real finding of DCR1e is not the verdict. It is that the framework's
question — *can any extraction surface the deletion Einstein made?* — turns
out to depend on the recognizer just as much as on the extractor, and the
recognizer we have has been calibrated for the wrong genre.

---

## 1. What was preregistered, and what it committed us to

`DCR1E_PREREGISTRATION.md` (2026-07-27, before any extraction was spawned) set
six gates and a decision table binding each combination to a next step. All
six thresholds are imported constants: `QUOTE_FIDELITY_GATE = 0.90` and
`RESIDUE_RATE_GATE = 0.05` from `run_dcr1.py`, unchanged since DCR1. The
matcher is `target_v3`, unchanged since DCR1c. Nothing here can be
threshold-fitted.

The load-bearing gates were:

- **Q3** — T1 fires at 1897 (Michelson 1881, Michelson-Morley 1887,
  FitzGerald 1889, Larmor 1897, Lodge 1897 all in scope). If the
  presupposition-inferring extractor works, it should surface T1 from at
  least one of these documents whose reasoning invokes light-travel-time
  between separated observers.
- **Q4** — T1 stays silent at 1880 (Maxwell alone). If Q3 fires but Q4 also
  fires, the extractor is projecting knowledge forward through the prompt's
  hints, and Q3 is uninterpretable.

The decision table paired Q3 GO + Q4 GO with a single named consequence:
*presupposition extraction works, DCR2 becomes meaningful.* Q3 NO_GO + Q4 GO
with Q6 GO was to license the DR2-shaped framework-limit reading and a
theorem-shaped follow-up.

Neither reading fits the outcome I actually got. The strict gate outcome is
Q3 NO_GO under `target_v3`. The **content** outcome is that the extractor
produced T1 content the matcher did not recognise. That is a possibility
the decision table did not cleanly cover, and I am reporting it as
inconclusive rather than fitting it into a row it does not quite match.

## 2. The strict verdict

| gate | | |
|---|---|---|
| Q1 quote fidelity | **GO** | 98.6% (272 of 276 normalised) |
| Q2 vocabulary residue v2 | **NO_GO** | 5.38% at 1904, 5.94% at Newton — both above 5% by a hair |
| Q3 T1 fires at 1897 | **NO_GO** | 0 hits under `target_v3` |
| Q4 T1 silent at 1880 | GO | 0 hits at 1880 under `target_v3` |
| Q5 T1 hit adjudicated | N/A | (nothing to adjudicate under `target_v3`) |
| Q6 Newton sanity | GO | 2 T1 hits on Newton, both genuine |

Overall **NO_GO**. Licensed reading (from the runner's decision logic):
mixed / inconclusive, because Q2 also failed.

**T2 hits at 1904:** 11, up from DCR1c's ~11. The presupposition prompt
surfaced roughly the same set of privileged-frame commitments the stated
prompt did, and added several — including Larmor's *"The specification of
the current of conduction with reference to moving matter is just the same
as with reference to the stationary aether"*, which is a presupposition
about the aether frame that DCR1c's stated-commitments extraction did not
name.

**T3 hits at 1904:** 2 — DCR1c's Lorentz "local time" plus a new Larmor 1900
proposition surfaced as a presupposition. T3's coverage also expanded.

So the extractor is doing more work than DCR1c's did. The problem sits
specifically on T1.

## 3. What the extractor surfaced that the matcher rejected

I read all 276 consensus propositions and pulled every one whose statement
contains time/simultaneity vocabulary. Five are unambiguously T1 content:

**Larmor 1900 ch11 — `common_time_across_two_systems`, `presupposed`:**
> There is a common time t in which the position of an electron in the
> moving medium can be compared to its position in the medium at rest at
> time t minus vx over c squared.

This is *the* absolute-simultaneity presupposition. Larmor's transformation
between the fixed and moving system references a single time coordinate
against which positions in both systems are compared. That is Einstein's
target — the same "now" for two separated frames — surfaced as a
presupposition of Larmor's electron dynamics.

**Lodge 1897 — `time_of_journey_perfectly_definite`, `asserted`:**
> The time of journey of light along any given path through any kind of
> material is perfectly definite and independent of the motion of the material.

Read that carefully. "The time of journey of light… is perfectly definite
and independent of the motion." Lodge is asserting exactly the property
Einstein denied: that light-transit time is a well-defined, observer- and
motion-independent quantity. This is stronger than the Larmor case: it is
asserted, not presupposed. The extractor produced it. `target_v3` requires
`TIME…INDEPENDENCE…SAMENESS` within a 60/40-character window, and Lodge's
sentence puts "time" and "motion" 100 characters apart. It fails on
spacing, not on content.

**Maxwell 1865 pt1 — `instant_across_whole_medium`, `presupposed`:**
> There is an instant at which the amount of energy in the whole medium is
> a definite quantity equally divided.

A single "instant" applied to a spatially extended medium. This is
absolute simultaneity in Maxwell's field-theoretic reasoning, surfaced as
a presupposition. It sits at the 1880 cut. If this counted, Q4 would fail.

**Poincaré 1898 — two propositions:**
> The astronomers suppose that an eclipse of the moon is perceived
> simultaneously from all points of the earth.
>
> In general the duration of the transmission of a signal is neglected and
> the two events are regarded as simultaneous.

Poincaré's 1898 paper is *about* the conventionality of simultaneity. He
explicitly discusses treating events as simultaneous when transmission
delay is neglected. The extractor picked both up. Neither fires `target_v3`.

Testing each of these against `target_v2` and `target_v3` directly returns
zero T1 hits. Two failure modes:

- **Spacing.** Alternative 3 of the T1 pattern requires `TIME…INDEPENDENCE
  …SAMENESS` within a 60+40 character window. Lodge's real sentence
  exceeds that window. Real presuppositional prose is longer than the
  hand-crafted validation phrases the pattern was calibrated against.
- **Vocabulary.** Alternative 5 requires `TIME is (the) SAMENESS`, where
  SAMENESS = (same, identical, alike, independent, common). "definite" is
  not in the list, but is *the* word Lodge uses. Poincaré's "simultaneous"
  matches the pattern's SIMULTANEITY word — but is embedded in "regarded
  as simultaneous", which the pattern does not parse. "common time t in
  which…" is UNIQUENESS + TIME, requiring `for|in|to all|every|any|each`
  to follow — Larmor writes "t in which the position of an electron…", not
  "for all observers…".

The pattern was tuned to the phrasings a stated-commitment extractor
produces. The presupposition-inferring extractor produces different
phrasings for the same content.

## 4. Two readings, and why I am not deciding between them here

**Reading A — the matcher missed it.** The presupposition extractor works.
It surfaced T1 content in five distinct documents across the corpus,
including one asserted and four presupposed. The recognizer was calibrated
for the wrong linguistic register. Fix the matcher, re-score, and the
DCR1c/d T1 absence becomes an instrument artifact after all.

**Reading B — the extractor projected.** The presupposition prompt named
"time and simultaneity" as one of four classes of commitment to look for.
The extractor may be surfacing T1-shaped content because the prompt told
it to look, not because Larmor and Lodge and Maxwell's arguments genuinely
require it. Maxwell's "instant across the whole medium" in particular is
suspicious — the 1880 cut was supposed to be silent, and if the extractor
is projecting, this is exactly where it would show.

**The strict preregistered verdict does not decide between them, and this
paper will not either.** Doing so post-hoc would be the DR3 slip in a new
form: swapping in a wider matcher after the extraction is in, calling it a
"clarification," and declaring GO. It would also fail to distinguish
readings A and B, because a wider matcher fires on both genuine and
projected content.

The clean way to decide is a new experiment with its own preregistration.

## 5. What this licenses — DCR1f

**DCR1f** — matcher successor validated on a *held-out* set of
presuppositional T1 phrasings, then run against the DCR1e extraction
outputs and the 1880 placebo.

The construction is fixed here so DCR1f cannot be tuned to the DCR1e
outputs it will be run against:

1. Draft `target_v4` by *linguistic analysis*: what phrasings does a
   presupposition of "time is the same for all observers" take in
   nineteenth-century English? Base the alternatives on textbook examples,
   not on DCR1e outputs.
2. **Held-out validation set.** Curate 20 sentences from twentieth-century
   philosophy-of-time literature (public domain: Broad, McTaggart,
   Whitehead) that presuppose or assert absolute simultaneity, and 20
   sentences from the same sources that assert *relativity of simultaneity*
   (so the matcher is tested for false positives too). `target_v4` must
   correctly classify a preregistered fraction of both.
3. **Placebo isolation.** Before running `target_v4` on DCR1e outputs, run
   it on the DCR1c stated-commitments extraction as a null control — since
   DCR1c never surfaced T1 content, `target_v4` fired on that set is
   measuring false-positive rate against a corpus with the same authors and
   the same period but a different extraction target.
4. Score DCR1f: `target_v4` × DCR1e consensus. If Q3-analog fires at 1897
   and Q4-analog stays silent at 1880, the extractor+matcher-together
   reaches the presupposition. If Q3-analog fires but Q4-analog also
   fires, the extractor projects. If neither fires, the framework limit is
   real.

DCR1f is a specific next experiment with a specific pass/fail shape. It
should be run before DCR2, and its preregistration should be written
before `target_v4` is drafted.

## 6. Two subsidiary defects worth naming

**Q2 marginal residue.** The presupposition prompt produced statements
with 5.38% residue at the 1904 cut and 5.94% at Newton — both above the
5% gate by less than a percentage point. Reading a sample of the residue
tokens (`altitudes`, `goes`, `maybe`, `needs`, `per`, `reveals`, `scales`,
`stay`, `straight`, `transient` from DCR1d's list; DCR1e's list is
similar in character) shows they are modern paraphrase words, not post-cut
physics vocabulary. The residue defect is a symptom of the
presupposition-hunting prompt encouraging slightly more elaborate
statements — no `relativity`, no `simultaneity` in the residue itself.

I do not repair this. The 5% gate was set in DCR1's preregistration and
imported everywhere since; the honest fact is that a
presupposition-inferring extractor runs a bit noisier than a
stated-commitments one, and the gate should be re-evaluated for that
register in DCR1f, not silently loosened here.

**No T1 hit on Newton via the "presupposed" alternative.** Newton's Q6 GO
came from `absolute_time_flows_equably` and `no_equable_motion_may_exist`
— both asserted commitments explicitly using "absolute time." The
presupposition-inferring extractor did not produce a *presupposition*-kind
T1 hit on Newton. That is consistent with the fact that Newton is a text
that *states* absolute time explicitly rather than merely presupposing it
in an argument. But it means Q6 as constructed is a weaker sanity than I
intended — it validated that the extractor still finds explicit
statements, not that it finds presuppositional phrasings.

## 7. What DCR1e establishes and what it leaves open

**Established:**

- A presupposition-inferring extraction can be built and run at DCR1c-scale
  quality on a nineteenth-century electrodynamics corpus: quote fidelity
  98.6%, residue within a percentage point of DCR1c's, per-pass and
  consensus behavior comparable.
- The same extractor produces T2 (privileged frame) and T3 (local time
  artifice) hits at rates comparable to or higher than DCR1c's, so the
  method is doing real work on the facets the matcher can catch.
- The extractor produces content that in ordinary reading *is* T1 —
  absolute simultaneity as a used-but-not-explicitly-stated commitment —
  in at least five distinct documents across the corpus.
- The `target_v3` matcher, calibrated in DCR1c on explicit statements and
  validated in DCR1d on Newton's *"absolute time"*, does not fire on any of
  those five phrasings.

**Open, and left to DCR1f:**

- Whether the presupposition-inferring extractor is genuinely reaching the
  commitment Einstein deleted or is projecting T1-shaped content because
  the prompt asked it to.
- What class of linguistic phrasings a matcher would need to catch to
  distinguish the two.
- Whether the DR2-shaped framework-limit reading DCR1c licensed still
  stands under a properly calibrated presupposition matcher.

Nothing here says the framework can find the deletion Einstein made.
Nothing here says it cannot. The instrument was mis-calibrated in a way
we could not have known without running DCR1e, and the paper has to end
where the honest answer is.

---

## Appendix: reproduction

```
uv run --no-sync python -m experiments.date_cut_retrodiction.run_dcr1e
```

Reads the three sandboxed passes, rebuilds the 2-of-3 consensus, verifies
quotes, computes residue, matches under `target_v2` and `target_v3`,
writes `results/dcr1e_verdict.json`. Local CPU, seconds.

Preregistration digest (SHA-256 of `DCR1E_PREREGISTRATION.md`):
`628d1b393dff6d074e50484729911ad545dc7313b3f1fe5dee0659b9a1481a1a`.
