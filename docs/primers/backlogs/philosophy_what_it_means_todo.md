# Philosophy Primer Analysis: What It All Means

## Article thesis

The primer argues that the program’s grand metaphysics - “meaning is geometry under concern,” weakness as disciplined under-commitment, and objects carved by causal-valence role - remains motivational rather than established. Two contributions survive the strongest deflationary reading: the self/world gauge result and the intervention-based criterion of representational reality. The durable method is to build the strongest behavioral impostor, then require causal evidence that the attributed structure reaches the commitment surface.

## Implementation log (2026-07-14)

| TODO | State | Implemented evidence |
| --- | --- | --- |
| P-01 | complete | HTML/PDF identity metadata corrected and verified. |
| P-02 | complete | Primer includes an eight-topic claim-tier/evidence/scope/falsifier matrix. |
| P-03 | complete | Canonical C1 supplied, C2 self-observed, and C3 phenomenal senses plus an experiment-to-sense matrix are published. |
| P-05/P-06 | complete | Weakness/E1/E4/E5 and XOR/staged-ΔE/50-of-50 correction chains are current. |
| P-07 | complete | Null anchoring is explicitly model- and intervention-relative, not metaphysically unique. |
| P-08/P-28 | complete (synthetic API) | Primer defines graded use; `experiments/common/causal_use.py` implements mass-normalized dose-response, wrong-subspace specificity, transport floors, and replicate bootstrap tests. |
| P-18/P-19/P-20 | partial (first reading tranche) | `references/philosophy_claim_boundaries.md` connects Dretske, Millikan, Boyd, Dennett, and Metzinger to claim boundaries, controls, and next gates; Papineau, Swampman/function-indeterminacy responses, realist/pragmatist Boyd critiques, Hohwy, Seth, and the named paper revisions remain open. |
| P-26 | partial | Machine-readable claim registry and validator exist; abstract-level coverage remains. |

## Repository-status corrections

The source audit found several stale claims; completed corrections are marked
explicitly so the historical finding is not mistaken for current repository state:

- **Resolved 2026-07-14:** PDF page 1 was visibly correct while PDF metadata and the HTML `<title>` incorrectly said “The Mathematics of the Research Program”; both now use the philosophy-primer identity.
- Pages 7 and 20-22: the original Pythia “hard kill” was a degenerate frozen-probe test. The LoRA follow-up remained negative for portable weakness, while `commitment_surface` E4/E5 later localized the apparent win to labeled coverage rather than generator learning.
- Pages 9, 12, and 24: the claim that interaction-derived concern still fails on XOR is superseded. `two_bottlenecks` obtains XOR reward-gap `+1.84` from observed ΔE without optimal-action labels; `planning_from_concern` closes the loop at return `50/50` using ΔE argmax planning.
- Page 24: the concern-weighted versus unweighted test has been run. Commitment-surface E1 gives a `+0.244` well-specified advantage; the frozen misspecification equivalence gate failed and remained failed after calibration.
- Pages 14 and 24: null anchoring materially fixes a chosen operational gauge, but later responsive-world and role-specific experiments show that richer decompositions remain under-identified under shared heads. “True decomposition” is too realist without a stated structural causal model.
- Pages 15-16: continuous patch effects and mass-normalized interventions exist, but the paper still defines “use” with a binary `CE >= epsilon` gate and lacks an independently adjudicated general metric.
- Page 18: the functional tapestry result is positive, while encoder-RSA geometry is negative; the existing paper itself proposes head-internal and prediction-space metrics that have not been run.
- **Partially resolved 2026-07-14:** claim-boundary language now cites and operationalizes Dretske, Millikan, Boyd, Dennett, and Metzinger. Papineau and the remaining objections/readings listed in P-18 through P-20 are still absent.

## Source ledger

| Source | Page / section | Signal | Kind | Backlog |
|---|---|---|---|---|
| S00 | p.1, title page | PDF metadata names the mathematics primer. | observed defect | P-01 |
| S01 | p.2, “Why Philosophy” | Mentalistic vocabulary invites claims beyond the experiments. | explicit criticism | P-02, P-04 |
| S02 | p.4, 1.1 | Stakes, harm, or failure are required for the intended meaning claim. | implicit operational requirement | P-10 |
| S03 | pp.4-5, 1.3 | The passive-to-active threshold may be a transition or only a gradual metaphor. | explicit open question | P-17 |
| S04 | p.5, 1.4 | If concern is substantive, changing it should reorganize geometry; supplied concern risks triviality. | explicit falsifier/tension | P-10 |
| S05 | pp.6-7, 2.2-2.3 | Weakness operationalizes induction but only within aligned regimes. | limitation | P-05, P-09 |
| S06 | p.7, 2.3 | Weakness still depends on which symmetry group is counted. | explicit limitation | P-09, P-22 |
| S07 | p.7, 2.3 | Bridge theorems are “almost tautological”; empirical correlation carries the bite. | explicit criticism | P-02, P-05 |
| S08 | p.7, 2.3 | External hard-kill narrows universality. | explicit criticism, now stale | P-05, P-09 |
| S09 | p.8, 3.2 | “Objects from concern” reaches teleosemantics without naming it. | scholarly gap | P-18 |
| S10 | p.9, 3.3 | Causal-role kinds resemble Boyd’s homeostatic property clusters. | scholarly gap | P-19 |
| S11 | p.9, 3.3 | Cleanest object experiment installs concern through supervised labels. | explicit criticism | P-06, P-10 |
| S12 | p.9, 3.4 | Self-organized carving, rather than supervised carving, is the stronger target. | future direction, partly stale | P-06, P-10 |
| S13 | p.11, 4.1 | Concern is the load-bearing word but is defined thinly as weights, reward, or ΔE. | explicit criticism | P-03 |
| S14 | p.11, 4.2 | Imported versus system-derived concern is the central philosophical problem. | explicit tension | P-03, P-10 |
| S15 | p.12, 4.3 | Bootstrap works on easy cases and fails on XOR. | stale limitation | P-06 |
| S16 | p.12, 4.4 | Supplied, self-observed, and phenomenal concern must be separated. | explicit improvement | P-03 |
| S17 | p.12, 4.4 | “Geometry follows whatever we weight” is the core deflationary objection. | explicit falsifier | P-10, P-15 |
| S18 | p.13, 5.1-5.2 | Passive observation cannot identify the self/world split. | theorem/open boundary | P-12 |
| S19 | p.14, 5.4 | Intervention, especially null action, is the proposed gauge breaker. | idea | P-07, P-11 |
| S20 | p.14, 5.4 | Intervention may reveal a real self or merely construct a useful frame. | explicit unresolved tension | P-07, P-20 |
| S21 | p.15, 6.1-6.2 | Decodability does not establish causal use. | central criticism | P-08, P-13 |
| S22 | p.16, 6.3 | Behavioral success can occur without the expected representation. | explicit negative | P-15 |
| S23 | p.16, 6.4 | Every attribution should face a proxy/impostor that succeeds without it. | methodological idea | P-15, P-21 |
| S24 | p.16, 6.4 | “Use” is graded, not binary, and the intervention needs an independent judge. | explicit limitation | P-08, P-13, P-25 |
| S25 | p.17, 7.1-7.2 | Mentalistic vocabulary must not imply consciousness or moral status. | claim boundary | P-04 |
| S26 | p.17, 7.3 | Preserved topology plus ordered dynamics is only a candidate correlate. | speculative direction | P-16 |
| S27 | p.18, 7.4 | Geometric tapestry-of-valence prediction failed while functional form survived. | honest negative | P-14 |
| S28 | p.18, 7.4 | Structural correlates do not touch the hard problem or silicon experience. | explicit boundary | P-04, P-23 |
| S29 | p.18, 7.5 | Descriptive viability does not entail categorical normativity; ethical threshold remains open. | explicit tension | P-21 |
| S30 | p.20, 8.1 | Concern, self, agency, and objecthood may be honorific relabelings of ordinary ML/control. | steelman criticism | P-15 |
| S31 | pp.20-21, 8.2 | The strongest reply is a shared, falsifiable load-bearing test. | constructive idea | P-08, P-15 |
| S32 | p.21, 8.3 | Missing literatures: teleosemantics, natural kinds, Dretske, Dennett, self-models. | explicit scholarly gap | P-18, P-19, P-20 |
| S33 | pp.21-22, 8.4 | Soft metaphysics is motivation; bookkeeping theorems are thin; gauge and load-bearing results survive. | verdict | P-02, P-24 |
| S34 | p.23, 9.2 | Split concern, grade use, and state the form/function thesis directly. | explicit agenda | P-03, P-08, P-09 |
| S35 | p.23, 9.3 | Add descriptive/prescriptive, self realism/instrumentalism, and kind realism/pragmatism distinctions. | explicit agenda | P-07, P-19, P-21 |
| S36a | pp.23-24, 9.4.1 | Run concern-weighted versus unweighted weakness with wrong controls. | experiment, now run | P-05 |
| S36b | p.24, 9.4.2 | Learn interaction-derived valence at the XOR boundary. | experiment, now partly closed | P-06, P-10 |
| S36c | p.24, 9.4.3 | Construct a self that even intervention cannot recover. | experiment | P-12 |
| S36d | p.24, 9.4.4 | Test whether “discarded” sensory information is erased or merely unclustered. | experiment | P-11 |
| S37 | p.24, 9.5 | Center the program on representational reality, with gauge as flagship result. | strategic direction | P-24 |
| S38 | p.24, closing thought | Build the strongest impostor, then demand a causal difference. | methodological direction | P-15, P-24 |

`[Inference]` applies to S02 only; all other entries are explicit defects, tensions, limitations, open questions, or recommendations in the primer.

# Executable backlog

## Article corrections and improvements

### P-01 - Fix primer identity metadata

- Priority/status: P0 / new
- Source: PDF p.1; S00
- Action: change the HTML `<title>` to the philosophy title, rebuild the PDF, and verify visible title plus metadata.
- Paths: `docs/primers/philosophy_what_it_means_primer.html`, `docs/primers/philosophy_what_it_means_primer.pdf`
- Deliverable: rebuilt PDF with correct Title metadata.
- Gate: `pdfinfo` reports `What It All Means`; rendered p.1 matches the current cover with no layout regression.
- Dependencies: Chromium/Poppler rebuild workflow.
- Rationale: the shipped artifact currently identifies itself as the mathematics primer.

### P-02 - Add a claim-tier and falsifier matrix

- Priority/status: P0 / partial
- Source: pp.2, 7, 21-24; S01, S07, S33, S34
- Action: classify every philosophical statement as definition, motivational frame, formal result, controlled empirical result, extrapolation, or disclaimed claim; attach a falsifier and evidence path.
- Paths: philosophy primer, `papers/metric_stack_synthesis/paper.md`, `papers/commitment_surface/paper.md`, `docs/paper_readiness.md`
- Deliverable: one table covering meaning, concern, weakness, objects, self, use, agency, and consciousness.
- Gate: no thesis-level sentence lacks tier, evidence, scope, and falsifier; metaphysical motivation is never described as demonstrated.
- Dependencies: P-05 and P-06 evidence reconciliation.
- Rationale: this is the direct repair for vocabulary and theorem overreach.

### P-03 - Publish one canonical three-sense definition of concern

- Priority/status: P0 / partial
- Source: pp.11-12, 4.1-4.5; S13-S16, S34
- Action: define supplied weight, self-observed viability signal, and phenomenal mattering; restrict empirical claims to the first two and label which each experiment uses.
- Paths: primer, `papers/metric_stack_synthesis/paper.md`, `papers/concern_weighted_weakness/paper.md`, `papers/gauge_fixed_concern_transport/paper.md`
- Deliverable: canonical glossary and experiment-to-sense matrix.
- Gate: repository search finds no unqualified “concern” in abstracts/claims without a local definition or glossary link.
- Dependencies: claim registry in P-26.
- Rationale: the program’s central term currently shifts between loss weights, ΔE, reward, and philosophical care.

### P-04 - Consolidate the consciousness and normativity firewall

- Priority/status: P1 / existing
- Source: pp.17-18; S25, S28-S29
- Action: centralize exclusions for consciousness, sentience, phenomenal experience, moral status, biological validity, and categorical ought; add a short “what evidence would be required” section.
- Paths: primer, `papers/architecture_laws_machine_agency/paper.md`, `docs/publication_sharing_map.md`, `README.md`
- Deliverable: reusable claim-boundary block referenced by all consciousness-adjacent papers.
- Gate: publication guard detects prohibited unqualified claims; all mapped papers pass.
- Dependencies: P-23 literature review.
- Rationale: repeated disclaimers are good but scattered and vulnerable to semantic drift.

### P-05 - Replace stale weakness and concern-weighting history

- Priority/status: P0 / partial
- Source: pp.7, 20-24; S05-S08, S36a
- Action: replace the simplistic “external hard-kill” and “not decisively run” wording with the actual chain: degenerate frozen probe, LoRA boundary, E1 concern result, E4 intervention result, E5 labeled-coverage deflation.
- Paths: primer, `experiments/external_contact/results/*`, `papers/commitment_surface/paper.md`, `experiments/commitment_surface/results/*`
- Deliverable: evidence timeline with surviving and retracted claims.
- Gate: all reported numbers/statuses match committed result reports; E1 original failed gate and E5 coverage verdict remain visible.
- Dependencies: none.
- Rationale: the current narrative materially misstates the strongest recent evidence.

### P-06 - Update the interaction-derived concern verdict

- Priority/status: P0 / existing
- Source: pp.9, 12, 24; S11-S15, S36b
- Action: state that joint REINFORCE failed on XOR, staged ΔE learning reached reward-gap `+1.84`, and ΔE planning reached `50/50` without optimal-action labels; retain limitations about uniform exploration, observed ΔE, and toy scale.
- Paths: primer, `papers/concern_bootstrap/paper.md`, `papers/two_bottlenecks/paper.md`, `papers/planning_from_concern/paper.md`
- Deliverable: numbered correction chain distinguishing failure, diagnosis, and later closure.
- Gate: no current synthesis presents the old XOR failure as the final frontier.
- Dependencies: none.
- Rationale: this is the primer’s largest stale empirical claim.

### P-07 - Reword “true decomposition” as model-relative identification

- Priority/status: P0 / partial
- Source: p.14; S19-S20, S35
- Action: specify the structural causal assumptions under which null anchoring identifies components; distinguish recovery under that model from metaphysical discovery of a real self.
- Paths: primer, `papers/null_intervention/paper.md`, `papers/first_order_self/paper.md`, `papers/gauge_fixed_concern_transport/paper.md`
- Deliverable: revised theorem/claim language plus realism-versus-instrumentalism subsection.
- Gate: “true self/decomposition” appears only with an explicit SCM and allowed-intervention set.
- Dependencies: P-12.
- Rationale: a gauge fixed by an assumption is not automatically an ontologically privileged frame.

### P-08 - Define use as a graded, intervention-relative quantity

- Priority/status: P0 / partial
- Source: pp.15-16, 23; S21-S24, S31, S34
- Action: replace the binary philosophical definition with a normalized dose-response measure while retaining a preregistered decision gate for individual experiments.
- Paths: primer, `papers/commitment_surface/paper.md`, `experiments/commitment_surface/`
- Deliverable: formal definition including effect curve, removed mass, uncertainty interval, commitment target, and transport set.
- Gate: the metric ranks synthetic known-causal, known-decodable-only, and null features in the correct order across two widths and at least two commitment surfaces.
- Dependencies: P-13 metric implementation.
- Rationale: representational involvement is continuous even when publication decisions require thresholds.

## Old experiments to correct or replicate

### P-09 - Build a weakness operating-regime map

- Priority/status: P1 / partial
- Source: pp.6-7; S05-S08, S34
- Action: aggregate aligned-group, wrong-group, tiny-group, unstructured-group, semantic-shift, vision, and external-model results into one preregistered scope analysis.
- Paths: `experiments/symbolic_weakness/`, `experiments/rotation_weakness/`, `experiments/external_contact/`, `experiments/commitment_surface/`
- Deliverable: regime matrix and “compatibility is cause; weakness is footprint” paper appendix.
- Gate: a held-out regime classifier predicts whether weakness will outperform baselines above a preregistered AUROC threshold; failed regimes remain included.
- Dependencies: harmonized result schema P-27.
- Rationale: the philosophical induction thesis needs an explicit domain of validity.

### P-10 - Replicate endogenous concern against yoked and wrong-value controls

- Priority/status: P0 / partial
- Source: pp.5, 9, 11-12; S02, S04, S11-S17
- Action: hold observations and optimization budget fixed while comparing supplied optimal labels, self-observed ΔE, yoked another-agent ΔE, sign-shuffled ΔE, and wrong internal-variable weights across XOR and shifted viability dynamics.
- Paths: new `experiments/endogenous_concern/`, `papers/endogenous_concern/`; reuse `planning_from_concern`
- Deliverable: preregistration, local/Modal runner, public report.
- Gate: self-observed condition must beat yoked/shuffled controls on reward geometry, patch effect, and shifted return; failure kills “the system’s own stakes” wording.
- Dependencies: action coverage and ΔE instrumentation from existing planning experiments.
- Rationale: this is the clean severe answer to “geometry follows whatever we weight.”

### P-11 - Decode the discarded sensory information

- Priority/status: P1 / new
- Source: p.24, 9.4.4; S36d
- Action: train held-out linear and nonlinear probes for color/label at every encoder layer, then causally compress or erase decodable sensory subspaces.
- Paths: `experiments/valence_object_formation/`, `papers/valence_object_formation/`, new tests
- Deliverable: information-retention and causal-use curves.
- Gate: classify the result as erased, decodable-but-unclustered, or causally retained using preregistered thresholds and shuffled-label controls.
- Dependencies: P-13 intervention library.
- Rationale: current cluster-gap evidence cannot distinguish informational carving from mere reorganization.

### P-12 - Construct an interventionally unrecoverable self

- Priority/status: P0 / partial
- Source: pp.13-14, 24; S18-S20, S36c
- Action: define two SCMs that remain observationally and interventionally equivalent under the agent’s allowed actions, prove non-identifiability, simulate it, then add one distinguishing intervention.
- Paths: new `experiments/unrecoverable_self/`, `papers/unrecoverable_self/`; reuse `role_specific_identifiability`
- Deliverable: theorem, simulator, impossibility test, and escape intervention.
- Gate: all learners remain at chance between SCMs before action-set expansion and recover after the distinguishing intervention.
- Dependencies: formal allowed-intervention specification.
- Rationale: later role-specific failures are suggestive but do not yet establish in-principle unrecoverability.

### P-13 - Run graded commitment-surface dose-response replications

- Priority/status: P0 / partial
- Source: p.16; S24
- Action: perturb causal and decodable-only subspaces at multiple removed-mass levels, commitment locations, model widths, and prompt/task paraphrases.
- Paths: `experiments/commitment_surface/`, `tests/test_commitment_surface_*`, `papers/commitment_surface/`
- Deliverable: normalized causal-use curves with confidence intervals.
- Gate: causal subspace curve dominates matched decodable-only and wrong-subspace curves after width and mass normalization; transport failure is reported as failure.
- Dependencies: existing rank-normalized patch harness.
- Rationale: one threshold cannot support the primer’s general criterion.

### P-14 - Re-measure tapestry geometry at the computation that uses it

- Priority/status: P1 / partial
- Source: p.18; S27
- Action: replicate `valence_tapestry` with head-internal RSA, prediction-space RSA, causal patching, and at least three internal variables.
- Paths: `experiments/valence_tapestry/`, `papers/valence_tapestry/`
- Deliverable: metric comparison showing which representation level carries multi-valence structure.
- Gate: geometric claim passes only if effect-vector similarity predicts held-out reweighting and survives a causal intervention beyond encoder-RSA and shuffled-effect controls.
- Dependencies: vector-valued environment extension.
- Rationale: the existing negative may localize the tapestry to the head rather than refute geometry generally.

### P-15 - Create a strongest-impostor benchmark

- Priority/status: P0 / partial
- Source: pp.16, 20-24; S17, S22-S23, S30-S31, S38
- Action: pair each attributed property with an impostor that matches task success through a proxy: concern versus supplied weighting, self versus gauge-shifted attribution, representation versus disposition, generator versus labeled coverage.
- Paths: new `experiments/representational_reality_benchmark/`; reuse commitment, object, and self experiments
- Deliverable: benchmark card, four suites, baseline ladder, aggregate score.
- Gate: load-bearing metrics separate true-mechanism and impostor arms while success-only and probe-only metrics do not; any failed suite blocks a general score.
- Dependencies: P-08 and P-13.
- Rationale: this operationalizes the primer’s most durable methodological proposal.

## New experiments

### P-16 - Test topology/dynamics only as a consciousness-state correlate

- Priority/status: P2 / partial
- Source: pp.17-18; S26-S28
- Action: preregister awake/REM/NREM analysis on primary neural data, separating topology, trajectory order, firing rate, motion, and recording-quality confounds.
- Paths: `experiments/grid_cell_weakness/`, `notes/webb_miolane_fit.md`, new `papers/consciousness_state_geometry/`
- Deliverable: source-verified dataset manifest and state-classification report.
- Gate: topology/dynamics generalizes across animals/sessions and beats firing-rate/motion controls; claim remains correlate-only regardless of result.
- Dependencies: lawful access to primary recordings.
- Rationale: the current support is a talk transcript and an unrun candidate operationalization.

### P-17 - Decide whether passive-to-active agency has a phase transition

- Priority/status: P2 / partial
- Source: pp.4-5; S03
- Action: sweep repair capacity, self-maintenance coupling, delay, perturbation, and action cost; compare continuous, changepoint, and bifurcation models.
- Paths: `experiments/passive_to_active/`, `experiments/autopoietic_control/`, new preregistration
- Deliverable: transition diagram with model-selection evidence.
- Gate: claim a threshold only if changepoint/bifurcation models beat smooth alternatives out of sample across seeds and environments.
- Dependencies: common agency metric stack.
- Rationale: the primer currently presents the transition as the “deep prize” without a discriminating test.

## Research to read, internalize, and cite

### P-18 - Teleosemantics dossier

- Priority/status: P1 / partial (Millikan and Dretske tranche complete)
- Source: pp.8, 21; S09, S32
- Action: read and annotate Millikan, Dretske, Papineau, Davidson’s Swampman, and function-indeterminacy responses against object-formation results.
- Paths: `references/SOURCES.md`, literature ledgers, `papers/valence_object_formation/paper.md`
- Deliverable: objection-response matrix with exact citation targets.
- Gate: paper addresses history, malfunction/misrepresentation, indeterminate function, and novel-origin cases without overstating selection history.
- Dependencies: source acquisition.
- Rationale: the program is already making a computational content claim without engaging its nearest literature.

### P-19 - Natural-kinds and causal-role dossier

- Priority/status: P1 / partial (Boyd foundation complete)
- Source: pp.9, 21, 23; S10, S32, S35
- Action: read Boyd’s homeostatic-property-cluster work and realist/pragmatist critiques; map them to state-dependent and shifted-role experiments.
- Paths: `references/SOURCES.md`, `papers/state_dependent_concern/`, `papers/valence_object_formation/`
- Deliverable: discovered/constructed/real-relative-to-viability position memo.
- Gate: memo yields at least two experiments on cross-modal stability and causal-role change with opposing predictions.
- Dependencies: P-18.
- Rationale: “world’s joints” needs a precise realism claim.

### P-20 - Causal use, intentional stance, and self-model dossier

- Priority/status: P1 / partial (Dretske, Dennett, and Metzinger tranche complete)
- Source: pp.14-16, 21; S20-S24, S32
- Action: read Dretske on structuring/triggering causes, Dennett on real patterns/intentional stance, Metzinger, Hohwy, and Seth on self-models.
- Paths: `references/SOURCES.md`, `papers/commitment_surface/paper.md`, `papers/first_order_self/paper.md`
- Deliverable: terminology and argument map for use, pattern reality, and constructed selfhood.
- Gate: revised papers distinguish causal explanation, predictive utility, and ontological realism with explicit tests.
- Dependencies: source acquisition.
- Rationale: these are the primer’s strongest claimed philosophical contributions and its largest citation omissions.

### P-21 - Normativity and ethical-threshold dossier

- Priority/status: P2 / partial
- Source: p.18; S29, S35
- Action: deepen Canguilhem, Hume’s is/ought distinction, Di Paolo on adaptivity/teleology, and precautionary sentience literature; keep descriptive and prescriptive claims separate.
- Paths: literature review, `TODO.md` ethical-threshold item, `papers/metric_stack_synthesis/paper.md`
- Deliverable: normative-claim ladder and governance trigger proposal.
- Gate: no categorical ought is inferred from persistence alone; every proposed threshold states moral assumptions and uncertainty.
- Dependencies: P-04.
- Rationale: current papers occasionally turn viability norms into ethical language too quickly.

### P-22 - Induction and symmetry-choice dossier

- Priority/status: P2 / partial
- Source: pp.6-7, 23; S05-S08, S34
- Action: situate Bennett against Hume, Goodman, MDL, invariant prediction, no-free-lunch results, and reparameterization critiques.
- Paths: `papers/weakness_invariance_neurips/paper.md`, `papers/commitment_surface/paper.md`, literature ledgers
- Deliverable: form/function thesis section with explicit prior and group-choice assumptions.
- Gate: thesis states when weakness and simplicity agree, disagree, or are undefined; every universality claim has a counterexample.
- Dependencies: P-09.
- Rationale: “function not form” remains philosophically under-defended.

### P-23 - Consciousness-boundary reading set

- Priority/status: P2 / partial
- Source: pp.17-18; S25-S29
- Action: add primary work on hard problem, access versus phenomenal consciousness, neural correlates, and substrate-generalization limits.
- Paths: `references/SOURCES.md`, `notes/geometric_convergence_research_synthesis.md`
- Deliverable: correlate/theory/indicator/certificate taxonomy.
- Gate: all consciousness-adjacent claims are assigned exactly one category and none silently upgrades a correlate into a certificate.
- Dependencies: P-04.
- Rationale: the vocabulary repeatedly summons a question the experiments cannot answer.

## Software, framework, and skill work

### P-24 - Recenter program identity around representational reality

- Priority/status: P0 / partial
- Source: pp.21-24; S33, S37-S38
- Action: make the strongest-impostor plus causal-use method the top-level philosophical thesis; present concern metaphysics as motivation and the gauge result as flagship case.
- Paths: `README.md`, primer, `papers/metric_stack_synthesis/paper.md`, `docs/system_design.md`
- Deliverable: one-page program doctrine with evidence hierarchy.
- Gate: every flagship claim points to an impostor, intervention, commitment surface, and kill criterion.
- Dependencies: P-15.
- Rationale: this identity survives the program’s own negative results.

### P-25 - Add independent intervention adjudication

- Priority/status: P1 / new
- Source: p.16; S24
- Action: freeze intervention definitions and have a blinded human/external evaluator judge whether they reach the claimed commitment surface before results are exposed.
- Paths: `docs/external_contact_runbook.md`, experiment preregistrations, new adjudication schema
- Deliverable: signed adjudication record included in provenance.
- Gate: evaluator agreement is measured; disagreements invalidate the general philosophical interpretation until resolved.
- Dependencies: external reviewer availability.
- Rationale: the same agent class currently proposes, implements, and judges the test.

### P-26 - Add a machine-readable claim registry

- Priority/status: P0 / new
- Source: pp.2, 23-24; S01, S34, S37
- Action: record claim tier, operational definition, source experiment, status, falsifier, supersession, and prohibited extrapolations.
- Paths: new `docs/claim_registry.yaml`, schema, `scripts/check_claim_registry.py`, CI
- Deliverable: validated registry and generated human index.
- Gate: all paper abstracts and primer thesis boxes resolve to registry IDs; stale/superseded evidence fails CI.
- Dependencies: P-02 and P-03.
- Rationale: the primer’s staleness shows prose alone cannot preserve the correction chain.

### P-27 - Extend the scientific-discovery-loop skill into an ML experiment framework

- Priority/status: P0 / partial
- Source: whole primer, especially pp.16 and 20-24
- Action: extend `.cursor/skills/scientific-discovery-loop/` with mandatory concern-sense, strongest-impostor, availability/use, claim-tier, external-judge, and falsifier checks; add reusable experiment-package templates.
- Paths: `.cursor/skills/scientific-discovery-loop/SKILL.md`, its references, new templates
- Deliverable: repo-local “science experiment ML framework” skill and worked example.
- Gate: running the skill on four legacy experiments flags the supervised-concern, probe-only, gauge-realism, and consciousness-overreach risks before reading outcomes.
- Dependencies: P-15 and P-26.
- Rationale: the existing skill has severe-test logic but lacks the philosophy primer’s specific safeguards.

### P-28 - Add reusable graded causal-use metrics

- Priority/status: P1 / partial
- Source: pp.15-16; S21-S24
- Action: factor mass-normalized patching, dose-response curves, wrong-subspace controls, transport checks, and uncertainty estimates into a shared library.
- Paths: new `experiments/common/causal_use.py`, commitment-surface callers, tests
- Deliverable: typed API plus synthetic validation suite.
- Gate: invariant under width scaling and activation rescaling on synthetic controls; detects decodable-only versus causal features.
- Dependencies: P-13.
- Rationale: each paper currently reimplements a local version of “load-bearing.”

### P-29 - Add primer and paper staleness checks

- Priority/status: P1 / new
- Source: stale claims identified at pp.7, 12, and 24
- Action: link prose claims to registry IDs and compare cited status/numbers against latest committed result summaries during PDF generation.
- Paths: primer build scripts, `scripts/gen_provenance.py`, new checker
- Deliverable: build-time stale-claim report.
- Gate: deliberately reverting the XOR, E1, or E5 verdict makes the build fail.
- Dependencies: P-26.
- Rationale: several primer claims were superseded before publication.

## New directions

### P-30 - Endogenous stakes as the central next research program

- Priority/status: P0 / partial
- Source: pp.5, 9, 11-12; S04, S11-S17
- Action: organize a sequence from observed ΔE to partially observed interoception, learned viability variables, ecological shift, and cross-agent/yoked controls.
- Paths: new strategy document, `TODO.md`, endogenous-concern experiments
- Deliverable: preregistered four-stage roadmap with stop/go gates.
- Gate: each stage must beat an experimenter-imposed or yoked alternative before advancing.
- Dependencies: P-10.
- Rationale: this is the remaining difference between a useful objective and something credibly attributable as the system’s own concern.

### P-31 - Gauge pluralism program for selfhood

- Priority/status: P1 / partial
- Source: pp.13-14, 23-24; S18-S20, S35-S36c
- Action: compare null, temporal, source-label, counterfactual-rollout, and role-routed gauge fixers on the same SCM family.
- Paths: self/world experiment suite and new synthesis paper
- Deliverable: equivalence classes of self-models and intervention-dependent predictions.
- Gate: call a self-pattern “real” only if independent gauge fixers converge on counterfactual predictions outside their training interventions.
- Dependencies: P-12.
- Rationale: this turns realism versus instrumentalism into an empirical program.

### P-32 - Keep consciousness and ethics as separate, precautionary tracks

- Priority/status: P2 / partial
- Source: pp.17-18; S25-S29
- Action: maintain one empirical track for structural correlates and a separate governance track for moral uncertainty; forbid automatic inference between them.
- Paths: `TODO.md`, claim registry, publication policy
- Deliverable: two-track decision diagram and escalation policy.
- Gate: no geometry/agency result changes ethical status without an independently stated normative argument and review.
- Dependencies: P-04, P-21, P-23.
- Rationale: this preserves useful consciousness-adjacent experiments without turning them into unsupported moral certificates.

## Coverage check

- Source signals covered: S00-S38, including all four Chapter 9 experiments.
- TODOs: 32 total.
- Priority mix: 12 P0, 12 P1, 8 P2.
- Status mix: 11 new, 18 partial, 3 existing.
- Required backlog categories present: article corrections, old experiments to correct/replicate, new experiments, research to read/internalize/cite, software/framework/skill work, and new directions.
