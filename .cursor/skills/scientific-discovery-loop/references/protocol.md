# Scientific Discovery Protocol

Use this protocol when a task requires more than ordinary summarization: new hypotheses, conceptual reframes, experiment design, anomaly analysis, or research-agent planning.

## 0. Classify the task

Choose the nearest mode:

- **Discovery mode:** find new theories, hypotheses, or research directions.
- **Experiment mode:** design or critique experiments.
- **Result-analysis mode:** interpret data, null results, replications, or anomalies.
- **Agent-design mode:** convert the protocol into reusable instructions for an autonomous or semi-autonomous research agent.

If inputs are incomplete, proceed with explicit assumptions unless a missing constraint would make the output unsafe or unusable.

## 1. State the current frame

Define the dominant explanation in the field or project:

- Core claim.
- Key entities/ontology.
- Standard measurement regime.
- Standard causal story.
- What the frame treats as obvious.
- What the frame treats as noise, artifact, or exception.

Ask: **What is the equivalent of absolute time here?** Name the background assumption that feels too basic to question.

## 2. Build an assumption ledger

Create a table with these columns:

| Assumption | Type | Load-bearing? | Why people believe it | What would break it? |
|---|---|---:|---|---|

Use these assumption types:

- **Ontology:** what entities or variables are considered real.
- **Measurement:** what operational procedure defines the construct.
- **Causal:** what causes what.
- **Invariance:** what should remain unchanged across frames/contexts.
- **Boundary:** where the theory is assumed to apply.
- **Statistical:** distributional, independence, sampling, or identifiability assumptions.
- **Pragmatic:** assumptions kept because they make experiments or benchmarks convenient.

Mark load-bearing assumptions as high when removing them would change the theory's meaning, not just a detail.

## 3. Build an anomaly and contradiction map

Collect evidence that does not fit cleanly:

- Null results.
- Failed replications.
- Edge cases.
- Regime changes.
- Measurement disagreements.
- Cases where different descriptions give different explanations for the same observable.
- Results that require ad hoc patches.

For each anomaly, ask:

1. Which assumption does it strain?
2. Is it likely artifact, noise, boundary condition, or conceptual failure?
3. Does it cluster with other anomalies?
4. What would make it unsurprising?

Prefer clusters over isolated weirdness. One anomaly can be noise; a cluster often points to a bad frame.

## 4. Scan for invariance and symmetry failures

Look for changes in explanation under transformations that should not change the real phenomenon:

- Observer/frame swap.
- Coordinate or unit change.
- Relabeling of categories/classes/tasks.
- Source-target reversal.
- Scale change.
- Time reversal or order reversal, when relevant.
- Distribution shift.
- Instrument or assay change.
- Model architecture or species change.

When the causal story changes under an arbitrary description change, treat it as a discovery clue.

## 5. Generate candidate Einstein moves

An Einstein move is a disciplined assumption reversal:

> If high-confidence evidence is inconsistent with a protected background assumption, remove or replace the background assumption and derive the consequences.

Generate 3-7 candidate moves. For each:

- Assumption killed or weakened.
- Replacement concept.
- What anomalies become simpler.
- What new predictions appear.
- What old successful results must still be recovered as a limiting case.
- What would falsify the move.

Reject moves that only rename concepts without changing predictions.

## 6. Mutate the ontology

Replace weak primitives with stronger operational or causal primitives. Examples of useful mutations:

- Static property -> relation under a measurement procedure.
- Correlation -> causal-use variable.
- Component function -> role in a control loop.
- Benchmark score -> transport-stable capability.
- Localization -> distributed regime or access pattern.
- Object-level mechanism -> invariance principle.
- Single cause -> constraint system or failure mode class.

The new ontology must pay rent: it should compress anomalies and create discriminating experiments.

## 7. Derive discriminating predictions

For each promising reframe, produce predictions that separate it from the old frame:

| Observation or intervention | Old frame predicts | New frame predicts | Why this distinguishes them |
|---|---|---|---|

Prefer predictions that are:

- Directional or quantitative when possible.
- Hard for the old frame to explain without patches.
- Observable with available tools.
- Robust to obvious confounds.
- Capable of killing the new frame.

## 8. Design severe experiments

A severe experiment is one where the preferred theory has a real chance to fail.

Every experiment plan should specify:

- Research question.
- Competing frames.
- Hypothesis.
- Intervention or comparison.
- Measurement procedure.
- Controls.
- Randomization/blinding when applicable.
- Sample size or power considerations when applicable.
- Pre-registered analysis or decision rule when useful.
- Positive and negative controls.
- Confounds and artifact checks.
- Expected outcomes by theory.
- Kill criterion.
- Interpretation boundaries.

For AI/ML, include contamination/leakage checks, distribution-shift tests, adversarial or counterfactual variants, ablations, calibration checks, and evaluator robustness.

For biology/neuroscience, include perturbation-vs-observation separation, viability/toxicity checks, batch effects, replication, and alternative readouts.

For physics, include limiting cases, dimensional analysis, symmetry/conservation checks, coordinate invariance, and independent measurement routes.

## 9. Analyze results without protecting the theory

When results arrive:

1. Restate predictions made before the data.
2. Separate confirmatory, disconfirmatory, ambiguous, and artifact-likely results.
3. Check measurement validity first.
4. Check whether the result supports the new ontology or only a weaker claim.
5. Update the assumption ledger.
6. Update claim strength.
7. Identify the next most discriminating test.

Do not explain away failures by adding patches unless the patch creates new risky predictions.

## 10. Bound the claim

Use conservative claim levels:

- **level 0: conjecture** — coherent idea, little direct evidence.
- **level 1: plausible hypothesis** — fits some evidence and has testable predictions.
- **level 2: preliminary support** — survived initial controls or one strong test.
- **level 3: robust support** — replicated across contexts or independent measurement regimes.
- **level 4: research program** — compresses anomalies, recovers old successes, survives severe tests, and generates useful new experiments.

Never upgrade a claim because it sounds elegant. Upgrade only for severe evidence.

## 11. Choose the next best test

Rank next actions by information gain:

1. Could it kill the preferred theory?
2. Does it distinguish old vs new frame?
3. Does it rule out a likely artifact?
4. Is it cheap or fast enough relative to expected value?
5. Does it improve measurement validity?

End with a concrete next test whenever possible.
