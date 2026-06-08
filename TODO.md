# Research TODO

## Now

- [x] Preserve the initial paper set locally.
- [x] Draft the geometric convergence synthesis.
- [x] Define public-safe repo policy.
- [x] Start a discovery-regime audit ledger.
- [x] Scaffold the first synthetic experiment.
- [x] Run the first synthetic pilot.
- [x] Publish the repo to GitHub.
- [x] Push a feature branch, open PR #1, and merge it.

## Experiment Track 1: Weakness vs. Simplicity

- [x] Create a minimal synthetic benchmark.
- [x] Run the pilot and record accepted/rejected artifacts.
- [x] Add a negative control where memorizer hypotheses are removed.
- [x] Add a stress test where the vocabulary includes overly broad unsafe hypotheses.
- [x] Add a validity-gated weakness selector and compare it against pure weakness.
- [ ] Run seed/feature sweeps for the synthetic benchmark.
- [ ] Extend from Boolean-rule worlds to text/classification prompts.
- [ ] Compare against LLM-generated rules or embeddings.

## Experiment Track 2: Cross-Model Concept Geometry

- [x] Define concept set: concrete, abstract, values, emotions, agency/boundary terms.
- [x] Choose first embedding model: `text-embedding-3-small`.
- [x] Decide embedding/probing interface.
- [x] Run a no-secrets env probe under Doppler.
- [x] Confirm no-secrets env presence under `superoptimizers` Doppler scope.
- [x] Produce first concept-neighborhood report.
- [x] Run paraphrase perturbation stress test.
- [x] Compare with a second embedding model.
- [x] Extend from embedding-space neighborhoods to activation-space probes.
- [ ] Add an external semantic negative control for paraphrase geometry.
- [ ] Replicate concept geometry with a non-OpenAI embedding family.
- [x] Run activation layer sweep on Pythia-70M.
- [x] Replicate activation geometry with a second open model.
- [x] Compare mean pooling against final-token pooling for activation sweeps.
- [x] Summarize cross-model activation layer profiles across Pythia-70M and GPT-2.
- [x] Select pooling-aware candidate layers for classifier and steering interventions.
- [x] Run held-out paraphrase classifier/readout pilot on selected mean-pooling layers.
- [x] Run pair-level control-leakage diagnostics with shuffled and category-matched random bridge pairs.
- [ ] Run first final-token steering pilot on selected generation layers.
- [ ] Convert strongest bridge pairs into steering or classification interventions.
- [ ] Add anisotropy and directional-curvature proxy checks to activation sweeps where feasible.

## Experiment Track 3: Boundary Priors

- [ ] Specify toy embodied environment.
- [ ] Define self/environment boundary prior.
- [ ] Define perturbation and model-reduction intervention.
- [ ] Choose metrics: adaptability, cooperation, policy entropy, criticality proxy.

## Open Questions Ledger

- [ ] What counts as "same geometry" across substrates: linear map, kernel, topology, dynamics, or intervention?
- [ ] What distinguishes passive representation geometry from active attractor geometry?
- [ ] Can weakness maximization be measured in activation spaces?
- [ ] Can discovery be detected as a regime transition rather than search?
- [ ] What ethical threshold follows if self-maintaining geometry appears in artificial systems?
