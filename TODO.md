# Research TODO

## Now

- [x] Checkpoint the activation-geometry pause state and exact next replication command.
- [x] Checkpoint the post-Pythia-160M pause state and pair-optimized intervention pivot.
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
- [x] Add a symbolic symmetry benchmark where several train-perfect rules fit, but only the weak invariant rule generalizes OOD.
- [x] Run the first symbolic prefix-shift pilot and record the selector gap.
- [ ] Run seed/feature sweeps for the synthetic benchmark.
- [x] Run seed/modulus/train-window sweeps for the symbolic symmetry benchmark.
- [x] Add non-cyclic symbolic tasks: parity cosets, color-permutation invariants, and dihedral reflection.
- [x] Replace oracle symmetry labels with learned or induced candidate transformations (`weakness_data_inferred` 100% on cyclic and dihedral).
- [ ] Extend from Boolean-rule worlds to text/classification prompts.
- [ ] Compare against LLM-generated rules or embeddings.
- [x] Train small neural models on symbolic tasks and compare OOD prediction by loss, flatness, compression, and weakness.
- [x] Define a model-level weakness metric as compatible transformation volume on the learned function table.

## Flagship Paper Track: Weakness Predicts OOD

- [x] Draft the paper target: weakness predicts OOD generalization better than loss, simplicity, flatness, or compression.
- [x] Create the first symbolic benchmark and pilot result.
- [x] Run broad symbolic sweeps with Wilson 95% confidence intervals and multiple task families (500 trials per family, four families).
- [x] Add neural baselines trained on the same symbolic tasks (256-model sweep with diverse architecture/init/optimizer/augmentation).
- [x] Compare weakness against train loss, validation loss, MDL/compression, description length, flatness/sharpness, and random selection (all classical baselines are well below weakness).
- [x] Add ablations where the supplied transformation group is wrong, incomplete, or noisy (wrong-group correctly fails; noisy-group robust; data-inferred-group works).
- [x] Add a Modal entrypoint and run a parallelized 1024-model sweep (`modal_neural_sweep.py`).
- [x] Write the first full paper draft with limitations and reviewer-risk mitigations (`papers/weakness_invariance_neurips/paper.md`).
- [ ] Add learned-rule or LLM-rule baselines where the model proposes hypotheses from training examples (future work).

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
- [x] Run first final-token steering pilot on selected generation layers.
- [x] Run steering calibration diagnostic with normalized/sign-flipped/random directions and option-order randomization.
- [x] Redesign the steering verifier with learned/readout-conditioned directions or causal patching before free-form generation.
- [x] Run causal patching diagnostic with target, distractor, random, and no-op activation patches.
- [x] Run matched-context activation patching using activations from the same option-choice prompt template.
- [x] Replicate the Pythia matched-context patching pocket across variants, random seeds, and nearby layers.
- [x] Run a focused attractor-pocket diagnostic with distractor sweeps and adversarial near-neighbor controls.
- [x] Run an answer-surface basin diagnostic to separate semantic source/target effects from label or option-surface effects.
- [x] Run a label-free readout basin diagnostic to test whether the attractor-family basin exists without visible answer choices.
- [x] Run a broad label-free target-state transfer baseline and compare attractor-family rows against the null distribution.
- [x] Run a layer/alpha dose-response for broad label-free target-state transfer.
- [x] Replicate the layer-4/5 downstream transfer ridge with a broader baseline and second seed/checkpoint.
- [x] Add a hook/readout-surface diagnostic for same-layer label-free patching.
- [x] Rerun the label-free dose-response ridge with hook-output patch vectors and a broader baseline.
- [x] Add a trained hook-output readout gate for the label-free transfer ridge.
- [x] Add a behavior-level gate for the trained-readout-confirmed transfer ridge.
- [x] Design a behavior-aligned intervention after the raw state-replacement behavior gate failed.
- [x] Add label-only, shuffled-label, blank-carrier, and stripped-definition carrier controls for full-label behavior scoring.
- [x] Add alias-label scoring controls for full-label behavior scoring.
- [ ] Replicate the full-label behavior gate with a second seed and second open model.
- [ ] Add paraphrased-label and length-matched carrier controls for full-label behavior scoring.
- [ ] Diagnose alias survivor pockets with multiple aliases and alias-shuffled controls.
- [ ] Learn behavior-aligned directions against the full-label objective.
- [x] Learn behavior-aligned directions against alias-label objectives.
- [x] Build residualized alias directions that subtract source/distractor/control-label components.
- [x] Build constrained alias behavior directions with explicit valence-control penalties.
- [x] Treat `valence->steering_vector` as the adversarial leakage control in behavior-direction experiments.
- [x] Build a multi-control constrained alias objective and evaluate held-out aliases/controls.
- [x] Train behavior directions jointly over multiple aliases and evaluate on held-out alias phrases.
- [x] Expand positive/control concept sets before larger-model replication.
- [x] Track a specificity frontier: positive mean retained vs independent control mean suppressed.
- [x] Diagnose whether behavior-direction leakage channels are low-rank or pair-specific.
- [x] Add a target-disjoint control family to test whether leakage is only same-target overlap.
- [x] Add random relation nulls to the behavior-direction specificity gate.
- [x] Add CAA/CAV-style activation-difference baselines under the held-out alias verifier.
- [x] Add a non-logprob generation or learned behavior-readout gate for semantic specificity.
- [x] Add a learned behavior-readout gate after strict generation-match produced zero target hits.
- [x] Redesign the behavior interface with a constrained short-answer gate after generation-match and generation-readout both produced zero target hits.
- [x] Build a direct behavior-classification/intervention gate after all generation and short-answer behavior gates produced zero target hits.
- [x] Add binary yes-bias controls after the direct relation classifier produced nonzero but confounded target passes.
- [x] Build contrastive binary directions that penalize blank/generic/source/distractor/shuffled/false-carrier Yes margins.
- [x] Rerun contrastive binary specificity after checkpoint to populate `binary_gradient_geometry` SVD summaries.
- [x] Decide whether binary leakage is low-rank enough for projection/whitening or too entangled for linear steering.
- [x] Test top-PC residualized or whitened binary directions to see whether any target movement survives removal of the answer-polarity axis.
- [x] Replicate the binary low-rank entanglement diagnosis on a second model/layer or pivot to a nonlinear/feature-guided intervention under the same strict binary verifier.
- [x] Run a focused layer/scale sweep around Pythia-70M layer 3 PC whitening after it produced a small strict pocket (`2/7` positives, `0/10` controls).
- [x] Add a focused pair set for the two stable layer-3 strict positives plus random-null controls.
- [x] Run the focused Pythia-160M layer-3 pocket replication using `layer3_strict_pocket_random_nulls`.
- [x] Run a focused Pythia-160M scale stress test to rule out simple scale mismatch.
- [ ] Test a pair-focused nonlinear or feature-guided intervention after the Pythia-70M two-pair pocket failed to replicate in Pythia-160M.
- [ ] Stratify behavior controls into target-sharing, source-sharing, and fully target-disjoint classes.
- [ ] Replicate the hook-output transfer ridge on a second checkpoint or open model.
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
