# The Dynamics of Conceptual Deletion: From Identifying Revolutions to Detecting Conceptual Susceptibility

**Human director:** Jawaun Brown
**Producing agent:** Claude Code, directed
**Program:** Framework pivot from the DR / DCR arc
**Status:** Framework paper. Original version (2026-07-27) named a candidate hypothesis and a multi-case test. Post-publication updates (2026-07-27 to 2026-07-28) report what happened when the multi-case test began to run: the paper's original central hypothesis (a discussion spike in the revolutionary paper) failed on TWO independent cases; two different structural signatures (prediction-independence and equalisation) fired on both. **See §10 for the update; the original text is preserved as written.**
**Date:** 2026-07-27 (original); 2026-07-28 (§10 update)

---

## Abstract

The Deletion-Repair (DR) and Date-Cut Retrodiction (DCR) arcs were built around one question: given only pre-1905 physics text, can an execution-free scoring function identify the specific commitment Einstein deleted in 1905? Five serial preregistered nulls (DCR3, DCR3b, DCR3c, DCR2a, DCR3d) show that under every scoring rule so far tested the answer is no. But DCR3d, the last of the five, incidentally measured a different quantity worth naming. The ratio of implicit use to explicit discussion for the eventually-deleted commitment is 4.5 at 1880, 1.5 at 1897, and 1.25 at 1904, with the deletion occurring in 1905. In this single case the signal peaks roughly twenty-five years before the deletion and is well into decay by the year of the deletion itself. This paper pivots the research program's framing. The DR/DCR arc's target ("which commitment gets deleted at THIS cut?") is a moment question; DCR3d appears to have measured a state question ("which commitment is under maximum latent pressure?"). We propose reframing from deletability tracking to susceptibility tracking, introduce P(t) as a candidate observable, and name the multi-case retrospective test — Copernicus, Darwin, Lavoisier, plate tectonics, quantum mechanics — that would be required to promote this from a single-case candidate hypothesis into a supported claim about the general shape of pre-revolutionary conceptual dynamics. Nothing here is established as a general law. One case, one operationalisation, one narrow scientific domain: a candidate observable, not a theory.

---

## 1. What DCR3d actually measured

DCR3d's preregistered target was M1 — that T1 (absolute simultaneity, the commitment Einstein deleted in 1905) rank first at the 1904 cut under a scoring rule that rewards commitments used many times but discussed rarely. That gate failed. T1 ranked second at 1904, behind T2 (privileged rest frame). It was the fifth serial preregistered null on the DR-arc side of the program.

The scoring rule was:

    deletability(C) = use_count(C) / (discussion_count(C) + 1)

Use and discussion were tagged by nine sandboxed Claude subagents (three per cut across three cuts) at the proposition level, with a preregistered rubric distinguishing propositions that USE a commitment as background from propositions that treat it as their SUBJECT. Tag consensus required agreement from at least two of three verifiers.

The result across the three cuts:

| cut | T1 use | T1 disc | T1 ratio | T2 ratio | T3 ratio | T1 rank |
|---|---:|---:|---:|---:|---:|---:|
| 1880 (deep placebo) | 9 | 1 | 4.50 | 1.00 | 0.00 | 1 |
| 1897 (near placebo) | 3 | 1 | 1.50 | 0.46 | 0.50 | 1 |
| 1904 (target) | 10 | 7 | 1.25 | 1.92 | 0.40 | 2 |

T1's ratio at 1880 (Maxwell only, before any ether-drift null result) is 4.5. By 1897 it has fallen to 1.5. By 1904 it is 1.25 and T2 has passed it. The eventually-deleted commitment is at its measured maximum a quarter-century before the deletion, and is well into decline in the year immediately preceding it.

The trajectory is what changes the reading. If we had only the 1904 cut we would report: "the scoring rule does not identify T1." With the trajectory, we can report something different: at 1904 T1's use count is at its highest observed level (10, up from 3 at 1897 and 9 at 1880) — but T1's discussion count has jumped from 1 to 7. The 1904 numbers are the numbers of a commitment that is being pulled from silence into speech.

Poincare 1898 treated simultaneity philosophically. Larmor 1900 wrote common time across two systems into the transformation. Lorentz 1904 named true-time-defines-corresponding-instants. Poincare 1904 wrote about simultaneous transmission. These are the four documents that produced the jump in discussion tags. The signal fades because the pre-revolutionary conversation has already begun. Einstein 1905 arrives immediately after the fade.

We set out to identify T1 at the deletion cut. What we found instead is a signal that peaks well before the deletion cut, in this one case.

## 2. The reframe: from deletability to susceptibility

The DR/DCR arc treated deletability as a property of a commitment AT a moment in the corpus: "given this cut, which commitment is most eligible for deletion?" That is a moment question. Its instrument is a single-cut ranking.

DCR3d's numbers, read as a trajectory, invite a different framing. Instead of asking "which commitment gets deleted at this cut?" one can ask "which commitment is currently under maximum latent conceptual pressure?" That is a state question. It has no unique moment attached to it. The state can persist for decades. The moment of deletion is when SOMEONE acts on pre-existing state — the state does not itself pick the moment.

Introduce a candidate observable:

    P(t) = implicit_use(t) / (explicit_discussion(t) + 1)

where implicit_use counts propositions in the corpus that presuppose a commitment as background, and explicit_discussion counts propositions that take the commitment as their subject. P(t) is high when a community depends heavily on a commitment without arguing about it. It is low when the community either does not use it or is arguing about it explicitly.

On general grounds P(t) should peak BEFORE a revolution, not AT one. Two curves are in play. Implicit dependence on a load-bearing commitment saturates early — once field theories require an instant-across-the-medium in order to derive anything, every derivation uses it. Growth in implicit dependence flattens. Explicit discussion, on the other hand, grows LATE — a commitment is not argued about while it works. It becomes discussed when its consequences begin to strain (Michelson-Morley, Lorentz's ad-hoc transformations, philosophical worries from Mach and Poincare). Because implicit dependence saturates while explicit discussion is still climbing, their ratio is mechanically driven to a peak BEFORE the revolution.

This is a MECHANISTIC HYPOTHESIS about the ORIGIN of the pattern DCR3d observed. It is not something DCR3d itself established. DCR3d observed the pattern once. The mechanism proposed here explains why one might expect the pattern in general, but "one might expect this on general grounds" is worth exactly what such arguments are ever worth: it is a hypothesis about extrapolation, not evidence for it.

## 3. Susceptibility versus deletability

The vocabulary matters, because it clarifies what the measurement is measuring.

Deletability, as the DCR arc used the word, is a moment property. It asks: at cut T, which commitment is most eligible to be deleted next? The instrument is a snapshot ranking at T. The pass criterion is that the top-ranked commitment be the one actually deleted immediately after T.

Susceptibility, as we mean it here, is a state property. It asks: at cut T, which commitment is currently under maximum latent conceptual pressure? The instrument is a trajectory of P(t) values across multiple cuts. The pass criterion is that the eventually-deleted commitment carries a distinctive P(t) trajectory relative to the others — for example, that its P(t) peak precedes the deletion.

The loose analogy is to critical phenomena. Near a phase transition, susceptibility (the system's response to small perturbations) diverges before the transition happens, and the correlation length grows. The system becomes hypersensitive well before it flips. The word "susceptibility" carries the right connotation for what P(t) may be measuring — a build-up of latent pressure that peaks before, not at, the qualitative change.

We flag this analogy as heuristic and refuse to smuggle in the mathematical apparatus. There is no free-energy functional here. There is no order parameter with a fluctuation-dissipation relation. There is no scaling law to test. The analogy is a vocabulary loan, not a formal identification. Anyone tempted to write down a Ginzburg-Landau-style expansion for P(t) should first do the multi-case test.

## 4. What this does NOT establish

A dedicated section, because the honest limits of the finding are as much of the paper as the finding itself.

- N=1. This paper's empirical base is DCR3d's numbers on one revolution, in one corpus, at three cuts, with one operationalisation of the use / discussion split. Every conclusion here that concerns "conceptual deletions in general" is a candidate hypothesis, not a supported claim. The word "in this case" belongs before every claim about P(t)'s trajectory that could be misread as general.

- One operationalisation of one signal. The use / discussion decomposition depends on a semantic judgment about what counts as USE (using a commitment as unspoken background) versus DISCUSSION (treating a commitment as the subject of a proposition). DCR3d's rubric had documented inter-verifier variance: at the 1904 cut, verifier A tagged 14 T1-discussions, verifier B tagged 7, verifier C tagged 6. The consensus rule (≥2 of 3) filtered to 7 defensible tags, but the raw variance is large. Different rubrics may yield different P(t) trajectories.

- One narrow scientific domain. Late-nineteenth-century physics is a specific structural type of science: highly mathematised, small community, publication conventions that make load-bearing assumptions visible to close reading. The pattern may be a special feature of this kind of science and not generalise to broader scientific revolutions, let alone to non-scientific conceptual transitions.

- One language, one corpus. The DCR corpus is 15 documents, English-and-translated-English, published in a specific set of venues over about forty years. Corpus construction was cut-blind, but corpus SELECTION was not: the documents were chosen because they are the canonical pre-Einstein physics literature.

- No claim is made here that P(t) BY ITSELF predicts which specific commitment will be deleted. The claim is only that P(t) may be higher for the eventually-deleted commitment than for the alternatives, and that its peak may precede the deletion. Even that claim is a candidate hypothesis from a single case.

- Even the trajectory reading is partly post-hoc. The DCR3e verdict file, which quantifies the ratio drop across cuts, explicitly labels itself post-hoc: its scoring rule was chosen after DCR3d's ratios were known. DCR4 is the pre-registered companion that would test the trajectory reading against fresh material (Einstein 1905 as an oracle). Until DCR4 lands, the trajectory finding stands as post-hoc pattern recognition on one case.

The safer summary of what DCR3d shows is: THIS operationalisation of ONE signal on ONE revolution behaves LIKE a build-up state. It is consistent with the idea that susceptibility peaks before deletion. It does not establish that all conceptual deletions have this temporal profile. The step from "consistent with" to "establishes" is the multi-case test.

## 5. The multi-case test that would settle it

If P(t) really does behave like a susceptibility that peaks before a revolution, the pattern should replicate across independent revolutions. The following five cases are the obvious targets. In each, one can identify a commitment that a specific revolution deleted, and construct a pre-revolutionary corpus with multiple cuts to compute P(t) trajectories against.

1. Copernicus, De revolutionibus (1543). Deleted commitment: geocentric priority — that the Earth's location is dynamically distinguished. Pre-revolutionary corpus: Ptolemaic astronomy 1400–1543, plus Renaissance mathematical astronomers (Regiomontanus, Peurbach, early Copernicans). The target commitment is background in every Almagest-derived calculation and rarely discussed as such until Copernicus.

2. Darwin, Origin (1859). Deleted commitment: species fixity — that species are natural kinds with essential boundaries. Pre-revolutionary corpus: eighteenth- and early-nineteenth-century natural history (Linnaeus onward), plus geological and paleontological literature 1800–1859. Species-as-fixed-kind is presupposed in every classification and only argued about after Lamarck and the pre-Darwin transmutationists.

3. Lavoisier, chemical revolution (1783–89). Deleted commitment: phlogiston — the substance-of-combustion picture. Pre-revolutionary corpus: eighteenth-century chemistry (Stahl, Priestley, Cavendish, Scheele) up to Lavoisier's Traite. Phlogiston is silently load-bearing in every combustion account until Lavoisier attacks it directly.

4. Wegener / plate tectonics (1960s consolidation). Deleted commitment: continental fixity — that continents are permanent fixtures of an otherwise-rigid crust. Pre-revolutionary corpus: geology 1920s–1960s, including Wegener's original 1912 proposal and its dismissal, through Hess, Vine-Matthews, Wilson. Continental fixity is background in mid-twentieth-century structural geology and gets discussed as the paleomagnetic evidence accumulates.

5. Heisenberg / Schrodinger / Born, quantum mechanics (1925–27). Deleted commitment: joint position-momentum determinacy — that a particle simultaneously has both. Pre-revolutionary corpus: classical mechanics literature 1900–1925, plus early quantum theory (Planck, Bohr, Sommerfeld). Joint determinacy is presupposed in every classical derivation and gets discussed as the old quantum theory's ad-hoc quantisation rules pile up.

For each case, the multi-case test asks whether P(t) for the eventually-deleted commitment peaks BEFORE the revolution, and whether that peak is distinctive relative to the other commitments in the same corpus.

A "yes" would look like: P(t) for the target commitment peaks at least a decade before the revolution, is decaying at the revolution's date, and is higher at its peak than any other candidate commitment in the corpus. Replicated across at least four of five cases, this would raise the DCR3d pattern from a single-case candidate to a supported empirical regularity.

A "no" would look like: P(t) for the target commitment fails to peak before the revolution in two or more cases; OR peaks but with no distinctive height relative to non-deleted commitments; OR peaks after the revolution rather than before. Any of these would refute the general reading and confine DCR3d's pattern to a special feature of the Einstein case.

A partial or mixed result — say, "yes" for physics revolutions (Einstein, quantum) but "no" for others (Darwin, Lavoisier) — would be its own finding: the pattern is real but domain-restricted. That would sharpen the framework without either establishing or refuting it.

None of these tests is run in this paper. The paper's contribution is the framework and the naming of the test that would decide it.

## 6. Application: a scientometric early-warning system

If P(t) really does track something like conceptual susceptibility, and if the pattern generalises across scientific revolutions, then the same signal is in principle computable in real time on a live corpus. The application is scientometric: an early-warning system for scientific revolutions.

The corpus candidates are the obvious ones. arXiv preprints. OpenReview submissions. Patent filings. GitHub commits and issue threads. Legal opinions (a domain that has its own deletions — precedent overturns). Philosophy journals (a slower-moving domain, but with clear precedent for conceptual deletions). The instrument extracts commitments from each document, tags each proposition for USE versus DISCUSSION relative to those commitments, and computes P(t) over rolling windows. The output is a ranked list: "these commitments have unusually high latent dependence in the current window, and their explicit-discussion count is rising fast."

Framed as speculation: IF the pattern generalises, this is what such a system would look like. Nothing in this paper claims that it would work. The instrument itself would need to be built and validated.

The obvious ground-truth problem is that waiting for actual scientific revolutions to occur takes decades and is not a practical validation loop. The accessible validation path is retrospective: run the instrument on historical corpora with known revolutions (the five cases above and more), and check whether P(t) trajectories on those corpora replicate the DCR3d pattern. This is exactly the multi-case test proposed in section 5. If the multi-case test passes, the same instrument can then be run forward on live corpora, with predictions to be evaluated over years to decades. If the multi-case test fails, the forward application is a non-starter.

There is also a weaker use case that does not require the strong generalisation claim. Even under the reading that P(t) is a domain-restricted signal (works in physics, unclear elsewhere), a live P(t) monitor on physics preprints could function as an attention-directing tool: not a prediction of revolutions, but a filter over which currently-load-bearing commitments are unusually silently-held and beginning to be argued about. That is a hypothesis-generation tool, not a prediction system. It requires less to be true and delivers less accordingly.

## 7. What was AI, and what is scientometrics

This paper has drifted, deliberately, from where the program started.

The program's origin question was an AI-capability question: given only pre-1905 physics text, can an execution-free scoring function operating on LLM-extracted commitments identify the specific commitment Einstein deleted? That is a small question. It asks whether a specific class of AI instruments can recover a specific historical fact. Its answer, at the end of five serial preregistered nulls, is: not with any scoring function so far tested.

The pivot question is a scientometric question: given text-dynamic data from a scientific community, can one detect that a commitment is under increasing latent conceptual pressure — regardless of what specific commitment will eventually be deleted or when? That is a bigger question. It asks whether a class of measurements on published-text dynamics can reveal something about the state of a discipline that the discipline's participants may not themselves see.

The AI-recovery question is a much smaller and less interesting question than the susceptibility question. Recovering ONE historical fact is a benchmark; detecting the SHAPE of pre-revolutionary conceptual dynamics is a scientific claim about how disciplines change. The DR/DCR arc's serial nulls do not answer the susceptibility question. They may, if DCR3d's incidental finding is read the way this paper reads it, have set up the tools to ask it.

## 8. Cautions and open questions

- The trajectory finding is post-hoc. The DCR3e file, which quantifies the ratio drop, is labelled by its own runner as a post-hoc analytic quantification of DCR3d's cross-cut ratios. Any confirmatory reading has to come from the pre-registered companion (DCR4, in flight) or, better, from the multi-case retrospective test.

- Verifier variance is substantial. DCR3d's discussion-count tagging at 1904 varied across verifiers by roughly a factor of two before consensus filtering. Under single-verifier tagging the P(t) trajectory could easily invert. The signal survives only under consensus, and the consensus rule itself is a preregistered choice that could have gone another way. Any multi-case extension will need to control for verifier drift explicitly.

- The USE / DISCUSSION distinction is a semantic judgment. The extractor has to decide, per proposition, whether a commitment is being used as background or treated as the subject. This is exactly the kind of rubric that is prone to drift across corpora, across historical periods, and across verifier prompts. Across the five multi-case candidates the drift risk is high — an eighteenth-century chemistry text and a twentieth-century preprint are not written to the same conventions.

- The framework is compatible with the pattern being a special feature of physics, of pre-1900 corpora, or of scientific revolutions of a specific structural type (highly mathematised, small community, canonical publications). None of these narrower readings would rescue the general susceptibility framework. All of them would be legitimate outcomes of the multi-case test.

- P(t) alone is not proposed as a predictor of WHICH specific commitment will be deleted. The claim is only that P(t) may be higher for the eventually-deleted commitment than for others in the same corpus, and that its peak may precede the deletion. Even that claim, at N=1, is a candidate.

- The pre-revolutionary "discussion" that pulls P(t) down includes some of the most important pre-revolutionary work in the domain. Poincare, Larmor, and Lorentz are not noise; they are the pre-Einsteinian construction of the concepts Einstein deleted. Reading their contribution as "signal decay" is a specific interpretive choice. Other readings — that they are the first phase of the deletion itself, distributed across multiple authors — are also compatible with the data.

- The critical-phenomena analogy is heuristic. Anyone who imports it beyond vocabulary is over-fitting. Susceptibility in statistical mechanics has a definition; here we have a candidate observable and a suggestive time profile.

- The historical framing (Kuhn on paradigm shifts, Lakatos on progressive research programmes, Latour on translation and enrolment) is deliberately not engaged in this draft. A future version, or a companion paper, should place P(t) explicitly against those frameworks. The absence of that engagement is a limitation, not an oversight.

## 9. What comes next

- DCR4 (in flight). The pre-registered fresh test of the trajectory reading against Einstein 1905 as an oracle. DCR4 is the accessible check that the DCR3d / DCR3e finding survives non-post-hoc scoring on the same case. It is a necessary check but not sufficient — even a passing DCR4 leaves the multi-case question open.

- The multi-case retrospective test. Five candidate cases named in section 5. Building each pre-revolutionary corpus is the substantial engineering task; running the P(t) instrument once the corpora exist is comparatively cheap. Each case is a separate paper, or possibly a portfolio paper if the corpora share enough infrastructure.

- A companion paper placing P(t) against Kuhn, Lakatos, and Latour, and asking whether existing history-of-science frameworks predict the same trajectory shape or a different one.

- If the multi-case test passes: an instrument-building paper describing what a live scientometric monitor would look like and how it would be validated forward.

- If the multi-case test fails: a scoping paper describing what DID work about DCR3d — that in this ONE case a specific measurement produced a specific pre-deletion peak — and what did not generalise, treated as a domain-restricted finding.

None of these follow-ons is authorised by this paper. This paper's job is to name the framework and be explicit about what would raise it from candidate to supported.

---

## 10. What happened when the multi-case test began (post-publication update, 2026-07-28)

Two things happened in the ~24 hours after this paper was first
merged. Both change the reading in ways worth naming at the top of the
paper rather than in a comment thread.

### 10.1 DCR4 (Einstein 1905 as oracle)

DCR4 (`papers/date_cut_retrodiction_dcr4/paper.md`, PR #452 + correction
PR #454) fetched Einstein's 1905 *Elektrodynamik bewegter Körper*,
applied the same DCR3d rubric (extraction + use tag + discussion tag,
3-verifier consensus), and preregistered four gates against it:

- Q1: extraction sanity (≥ 15 propositions from Einstein 1905)
- Q2: T1 discussion count > T2 discussion count in Einstein 1905
- Q3: T1 discussion count in Einstein 1905 > 7 (the 1904 pre-cut count)
- Q4: T1 use/discussion ratio in Einstein 1905 < 1.25

The result was Q1 GO, Q4 GO, Q2 NO_GO, Q3 NO_GO. The four verifiers
unanimously agreed on 4 T1-discussion propositions and 4 T2-discussion
propositions in Einstein 1905. Zero of Einstein's ~12 predictions
required T1/T2/T3 as background — every prediction required only
OTHER (electromagnetic principles, kinematic definitions).

An immediate per-document reslice (PR #454) further clarified: the
aggregate 1904 T1 count of 7 was concentrated in one paper — Poincaré
1898 alone accounts for 4 of the 7, matching Einstein 1905 exactly.
Einstein does not have less T1 discussion than "the precursor era";
he ties the single most vocal precursor.

**Three findings from DCR4 that were not preregistered by this
framework paper:**

- **Discussion spike is a precursor phenomenon, not a
  revolutionary-paper phenomenon.** The "spike in the revolutionary
  paper" reading anticipated in §5 fails at 1905 on the Einstein case.
- **Prediction-independence.** Every one of Einstein's ~12 predictions
  is reconstructed so that no derivation depends on T1/T2/T3 as a
  premise. Every pre-1905 paper in the corpus has some
  prediction-dependence on either T1 or T2. Only Einstein has zero.
- **Symmetric equalisation.** Einstein 1905's T1:T2 discussion count
  is exactly 4:4. Under the per-doc reslice, no precursor paper has
  both T1 ≥ 4 AND T2 ≥ 4 in the same document (Poincaré 1898 is 4:0;
  FitzGerald 1889 and Larmor 1900 ch10 are 0:4; nobody balances both).

### 10.2 DCD1 pilot on Darwin (PR #460)

The Darwin case's pre-1859 biology corpus shipped as PR #459 (Malthus,
Herschel, Wallace, Erasmus Darwin, Darwin's 1845 Beagle journal, plus
15 chapters of *Origin* 1859 as oracle). The DCD1 pilot (PR #460) ran
the same DCR arc extraction and tagging pipeline on a subset — 5
pre-1859 + 3 Origin chapters, 191 consensus propositions, 3 use taggers,
3 discussion taggers, unanimous where reported. Categories D1 (species
fixity), D2 (separate creation), D3 (species essence) substituted for
T1/T2/T3.

Preregistered pilot gates and outcomes:

- P1 (extraction sanity, ≥ 5 props/doc average) — GO (23.9)
- P2 (D-categories discriminate: D1 ≥ 3, D2 ≥ 1, D3 ≥ 1) — GO (25, 31, 6)
- P3 (D1 in Origin > D1 in pre-Origin) — **NO_GO** (Origin 10 <
  pre-Origin 15)
- P4 (D1 use in Origin = 0, exploratory) — GO
- P5 (Origin D1:D2 within 2×, exploratory) — GO (10:12)

The core P3 gate — the analogue of the "spike in revolutionary paper"
hypothesis this paper anticipated — failed on Darwin as well. Erasmus
Darwin 1794 alone contributes D1 = 7, close to Origin's total D1 = 10
across three chapters. The precursor era owns the discussion again.

But P4 and P5 both fired. Darwin's Origin discusses D1 and D2 in
balanced measure (10:12) and reconstructs every one of its ~45
predictions across the three chapters so that no derivation depends on
D1/D2/D3. **Both DCR4 structural signatures replicated on Darwin.**

### 10.3 What the update changes about this paper

The original central hypothesis — a P(t)-shaped discussion spike whose
peak is close to the revolutionary paper — has now failed in two
independent cases (Einstein physics 1905, Darwin biology 1859). It is
possible the P(t) shape holds at a longer time-scale that we are
misresolving with only three or four pre-revolutionary cuts; but as
stated in §2 and §5, the framework's core prediction is refuted for
this operationalisation on two cases.

Two different structural signatures fired on both cases. Neither was
named in the original paper. They are stated here for the first time
in the framework paper's voice:

1. **Prediction-independence.** A revolutionary paper reconstructs
   every one of its predictions so that no derivation depends on the
   deleted commitment. Precursor papers, even the ones that discuss
   the deleted commitment intensely (Poincaré 1898, Erasmus Darwin
   1794), continue to USE it as background elsewhere in their
   arguments. The revolutionary paper achieves not "more discussion"
   but "zero use." This is a per-paper property that survives per-doc
   reslicing.

2. **Symmetric equalisation.** A revolutionary paper discusses the
   deleted commitment and its structurally paired partner (T2 for
   Einstein, D2 for Darwin) in balanced measure. Precursor papers are
   T-only or D-only: they engage one commitment and ignore the other,
   or engage them at very different intensities. The revolutionary
   paper treats them as one problem with two symmetric horns and
   dispatches both together.

These are candidate signatures now supported at N = 2. That is not the
same as "supported as a general law of scientific revolutions." Both
cases are natural sciences. Both involve a well-defined structural
partner for the deleted commitment (T2 for T1 in physics; D2 for D1
in biology). Whether Copernicus, Lavoisier, plate tectonics, or the
quantum revolution have similar structural pairings — or whether
prediction-independence + equalisation only makes sense when such
pairings exist — is what a third and fourth case would decide.

The Lavoisier corpus (PR #455) turned out too thin on Wikisource to
run the pilot on. The Darwin case did work, and shipped as DCD1 pilot.
A Copernicus corpus attempt is in flight as of this update; a Copernicus
result would give N = 3 across three centuries and three domains.

### 10.4 What the update leaves standing

- Everything in §§1-4 about deletability vs susceptibility. The
  moment-versus-state distinction survives the update; the P(t) shape
  we hypothesised for the susceptibility signal is what the data
  refuted, not the vocabulary of susceptibility itself.
- §7's diagnosis that this program has moved from AI-recovery
  ("can an LLM recover Einstein's deletion?") to scientometrics
  ("what dynamics do published corpora show around scientific
  revolutions?"). If anything the update makes that diagnosis
  stronger: what replicated in Darwin was not about LLMs and not about
  Einstein; it was about the structural properties of two revolutionary
  papers written 54 years apart.
- §8's caution. Verifier variance, dependence on the USE / DISCUSSION
  rubric, corpus availability, N = 1 (now N = 2) — every listed
  caution still applies.

### 10.5 What the update revises

- §5's decision table. "GO if P(t) for the target commitment peaks at
  least a decade before the revolution ... is higher at its peak than
  any other candidate commitment in the corpus" — the second half of
  that condition has now failed on both cases we've run. The multi-case
  test's decision criterion needs revising to test the two structural
  signatures found in DCR4 in addition to the P(t) shape originally
  proposed.
- §9's "what comes next" list. DCR4 is done, not in flight. DCD1
  pilot is done. Lavoisier failed at corpus stage; Darwin succeeded;
  Copernicus is being attempted; plate tectonics and quantum remain
  future work. The instrument-building paper and the Kuhn/Lakatos
  companion remain future work.

### 10.6 Specificity check (2026-07-29): the two signatures are Einstein-unique in DCR arc but NOT Origin-unique in Darwin

The §10.3 claim that the two signatures characterise the revolutionary
paper implicitly assumes they are UNIQUE to the revolutionary paper.
A per-document specificity check on already-committed verifier tags
(`experiments/darwin_species_fixity_corpus/run_specificity_check.py`,
verdict at `results/dcd1_pilot_specificity_check.json`) tested that
assumption on both cases.

**DCR arc (physics):** Einstein 1905 is the UNIQUE document with both
signatures firing meaningfully. Among 15 pre-Einstein documents, none
has both prediction_independence AND equalisation
(disc(T1) ≥ 3 AND disc(T2) ≥ 3 AND ratio ≥ 0.5). The signatures are
distinctive of Einstein against the physics corpus.

**Darwin (biology):** Origin is NOT unique. Three pre-1859 documents
also hit both signatures at the same substantive thresholds:

- Erasmus Darwin 1794 Zoonomia XXXIX: D1=7, D2=5, no D-use in
  predictions
- Wallace 1855 Sarawak law: D1=5, D2=8, no D-use in predictions
- Darwin 1845 Beagle ch17: D1=3, D2=6, no D-use in predictions

Origin chapters do hit (intro 3:3, ch14 4:7; ch4 hits pred_indep only
at 3:2 which fails the equalisation floor). But so do the three
pre-Origin documents listed. **On the Darwin corpus, the "unique to
revolutionary paper" claim fails.**

The signatures fire whenever a paper (a) has predictions but (b) does
not require the deleted commitment as background AND (c) discusses
both paired commitments at balanced counts. Zoonomia hits all three
because Erasmus Darwin discusses transmutation speculatively but his
concrete predictions are about mechanisms of generation and heredity,
which don't require D1 as premise. That reads as "prediction-
independence" even though the paper is deeply committed to a stance
on D1.

**What survives the specificity check:**
- The two signatures are real, stable observables. Not a scoring
  artifact.
- Einstein 1905 remains distinctive against the DCR arc's 15 physics
  documents. The N=1 physics uniqueness claim holds.
- The Erasmus/Wallace/Beagle triple hitting the same signatures as
  Origin is itself a finding: it identifies a class of speculative
  precursor papers that "look like" revolutionary papers on these
  two metrics.

**What the specificity check falsifies:**
- The N=2 uniqueness claim. On Darwin, the signatures do not
  distinguish Origin from Zoonomia, Sarawak, or Beagle ch17.
- The framing "the revolutionary paper is uniquely characterised by
  these two features." That framing survives on physics; it does
  not survive on biology.

**What the framework paper should therefore claim going forward:**
The two signatures may be a useful COMPONENT of a revolutionary-paper
identification pipeline, but they are not by themselves sufficient.
Distinguishing a revolutionary paper (Origin) from a speculative
precursor (Zoonomia) requires additional criteria — perhaps something
like "reconstructed derivations to eliminate a previously-required
premise" (which Einstein did but Erasmus Darwin did not) rather than
just "no derivations happen to use the premise" (which both do).

### 10.7 Attribution note

The DCR4 correction (§4.4 of that paper) and this update section were
written in response to the human director's request to check whether
the DCR4 aggregate claim was an averaging artifact. It was. The
per-doc reslice that revealed Poincaré 1898's contribution is a
cheap-but-load-bearing check that any future multi-case work should
run before publishing an aggregate claim.

---

## Appendix A: numbers reused

All numeric claims about the Einstein case in this paper come from two files in the current tree:

- `experiments/date_cut_retrodiction/results/dcr3d_verdict.json` (per-cut use / discussion counts and ratios, verifier consensus, gate decisions).
- `experiments/date_cut_retrodiction/results/dcr3e_verdict.json` (ratio drops across cuts, labelled post-hoc by its own runner).

No new computation is performed by this paper. Reproducibility of the underlying numbers is provided by the DCR3d and DCR3e runners already committed to the tree.

## Appendix B: how to read the softening

DCR3d's own paper closes with the sentence "Deletability is a build-up state, not a moment property." That formulation is too strong for what a single case supports. The corrected reading, adopted here throughout:

> This experiment shows that this specific operationalisation of one signal peaks well before the historical deletion in this one case. It is consistent with the idea that the measured signal behaves like a build-up state. It does not yet establish that all conceptual deletions have this temporal profile.

Every substantive claim in this paper is intended to be read with that hedge implicit. Where the paper says "candidate hypothesis," it means candidate hypothesis; where it says "in this case," it means in this case; where it says "consistent with," it does not mean "confirmed by." The multi-case test in section 5 is the path from consistent-with to supported-by, and it is not run here.
