# Research TODO

## Primer-derived execution contracts (2026-07-14)

- [x] Add one canonical program evidence registry with explicit gate/status states.
- [x] Add claim-to-evidence linkage and fail-closed validators for stable claim tiers.
- [x] Add a versioned experiment manifest schema, validator, and starter template.
- [x] Correct all six primer HTML titles and PDF metadata; rebuild PDFs from corrected HTML.
- [x] Correct the mathematics primer's Lagrangian/KKT signs, VOI sign, and discount arithmetic with regression tests.
- [ ] Migrate experiment families to structured manifests and replace prose-only provenance extraction.
  - [x] Partition all 54 research packages in `docs/experiment_contract_registry.json`: 5 structured manifests and 49 time-bounded legacy exceptions.
  - [x] Make provenance consume exact primary-run bindings for structured packages (commitment_surface primary is M5; E5/E6/E7 remain explicit partial history).
  - [ ] Replace the remaining legacy exceptions and partial run histories with exact structured run bindings.
- [ ] Add CI lanes for manifest coverage, public-artifact envelopes, and clean-clone reproduction.
  - [x] Enforce manifest-or-active-exception package coverage in the required root quality gate.
  - [ ] Enforce public-artifact envelopes and clean-clone reproduction.

## Now

- [x] Checkpoint the positive-family frontier pause state and exact next replication commands.
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
- [x] Start Phase / Arc 2A: Concerned Syntax benchmark and paper scaffold.
- [x] Start Phase / Arc 2B: Viable Computational Bodies benchmark and paper scaffold.
- [x] Complete and audit the E7 selective-subspace continual-learning grid
  (integrity INVALID: 6/32 matched groups exceed the frozen 2% timing gate;
  G1–G4 withheld, no scientific verdict).
- [x] Build and run frozen M5 Suite C reopen-trigger experiment (strict FAIL:
  F2 periodic latency tie and F3 normalized-trigger specificity tie reject the
  universal trigger-superiority claim; F0/F1/F4/F5 pass).

## Phase / Arc 2A: Concerned Syntax

- [x] Add a symbolic Concerned Shape Grammar benchmark.
- [x] Add constituency interventions: pair probe, high-constituent move, role ablation, distractor probe, null.
- [x] Compare null, flat-valence, compression, uncertainty-only, and concern-gated syntax selectors.
- [x] Run a local design pilot and commit the public result report.
- [x] Draft preregistration and paper.
- [x] Run a Modal multi-seed sweep.
- [x] Add learned agents that infer parse without direct access to hidden syntax.
- [x] Add vector observations where parse must be learned through an intervention.
- [ ] Add pixel observations where parse must be learned from generated shapes.

## Phase / Arc 2B: Viable Computational Bodies

- [x] Add a typed architecture/body motif grammar.
- [x] Add formal/static dependency and resource gates.
- [x] Compare accuracy-only, novelty-only, and viability-guided search.
- [x] Run a local design pilot and commit the public result report.
- [x] Draft preregistration and paper.
- [x] Run a Modal multi-seed sweep.
- [x] Add first executable body validation against the learned Arc 2A gate.
- [x] Add vector-observation executable module body validation.
- [x] Add Haskell typed ontology gate prototype for body admissibility.
- [ ] Replace symbolic motifs with executable neural modules.
- [ ] Add ASP/s(CASP), Z3, or equivalent external formal guard integration.

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

## Paper A Scale-Up: Translation Augmentation, Toroidal Codes, and Weakness Mediation

Prereg `papers/grid_cell_weakness/preregistration.md`; strategy `notes/weakness_topology_program_synthesis.md`.
Tests weakness, toroidal topology (Betti numbers), and OOD on a path-integration RNN - the
Fourier/weakness/torus triangle, with the Webb-Miolane/Gardner torus as the external anchor.
The final Modal result is a publishable negative mediation note: translation augmentation causes
toroidal codes and larger-arena OOD, but weakness does not govern topology or mediate OOD.

- [x] Build the self-contained harness: path-integration RNN + the four metrics (weakness under wrapped translations, gudhi persistent homology, Fourier participation ratio, OOD) — `experiments/grid_cell_weakness/core.py`.
- [x] Validate the metric harness discriminates torus vs plane vs sphere (torus β₁=2 + void, score 0.823 vs 0.001/0.0; weakness 0.998 vs 0.300/0.700) and run the end-to-end CPU pilot (`results/pilot_2026_06_28.md`).
- [x] Add the self-contained Modal sweep entrypoint with G1–G6 gate evaluation (`modal_grid_cell_weakness_sweep.py`).
- [x] Run a reduced local CPU sweep (3 conditions × 2 seeds) — spectral leg (G5 ρ=+0.89) and topology causal contrast (G6 0.27 vs 0.00) confirmed; OOD legs (G3/G4) need real arena geometry (`results/local_cpu_sweep_2026_06_29.md`).
- [x] Dispatch the full Modal sweep (5 conditions × 2 archs × 32 seeds, steps=4000, --decode-arenas) from a Modal-authed machine to test G2-G4 with larger-arena OOD (`results/modal_grid_cell_weakness_sweep_2026_07_02.md`).
- [x] Add the wrong-group/random-shift null-control reporting and the topology-mediation (G4) figure (gate-margin heatmap).
- [x] Derive the conditional weakness↔PAC-Bayes bound sketch: a pre-sample
  symmetry-indexed mixture prior gives
  \(\mathrm{KL}(\delta_h\|P)\le\ln|H_{\ge W_G(h)}|-\ln\pi_{W_G(h)}\), while
  explicitly withholding neural/OOD conclusions pending the registered finite
  enumeration (`papers/weakness_invariance_neurips/pac_bayes_weakness_sketch.md`).
- [ ] Reward-deformation follow-up (Paper B seed): reward locally lowers weakness to raise resolution — the `valence_tapestry` gap on the navigation torus.
- [ ] Brain-data prediction (deferred; data hosts proxy-blocked here): weakness tracks H₁ persistence in the Gardner et al. grid-cell recordings.

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
- [x] Test a pair-focused optimized single-vector intervention after the Pythia-70M two-pair pocket failed to replicate in Pythia-160M.
- [x] Stratify behavior controls into source-sharing, target-sharing, implausible random-null, and semantically near-null classes.
- [x] Run the first stratified strict-binary control gate on the Pythia-70M layer-3 pocket.
- [x] Build a positive-family binary direction that trains positives against stratified controls.
- [x] Run the positive-family strict-binary scale sweep on the Pythia-70M layer-3 pocket.
- [ ] Test a genuinely nonlinear or feature-guided intervention after pair-optimized single vectors still leaked controls.
- [x] Stress-test the positive-family strict frontier across objective aliases and train variants.
- [x] Run the positive-family `alias_1` objective / `alias_2` evaluation replication on Pythia-70M layer 3.
- [x] Run the positive-family train-variant `1` replication on Pythia-70M layer 3.
- [x] Halt positive-family second-model/layer replication after the alias/train gate failed.
- [x] Build and test a pair-conditioned readout/control-span binary intervention after the positive-family frontier failed alias/train replication.
- [x] Build and test a sparse feature-mask pair-conditioned intervention after the linear readout/control-span constraint killed positives.
- [x] Build and test a genuinely conditional state-gated binary intervention after additive free, span-constrained, and sparse-mask vectors all failed strict specificity.
- [x] Stress-test the state-gated strict frontier across objective alias and train variant.
- [x] Test relation-level control prompts for state-gate calibration.
- [ ] Improve state-gate calibration to suppress semantic-near controls before expanding models or concepts.
- [x] Try a learned multi-class gate or shared conditional operation after relation-control state gating killed positives.
- [x] Finish scale and alias stress for `target_binary_relation_multiclass_state_gate_opt_8`.
- [x] Build a held-out-control conditional gate that trains on disjoint source/target/control families and evaluates on held-out control classes.
- [x] Run an oracle or learned row-conditioned target-family disambiguation gate after held-out-control class filtering failed to remove target-sharing leakage.
- [ ] Test supervised exact-relation readout identifiability within a target family before further binary-relation steering.
- [ ] Replicate the hook-output transfer ridge on a second checkpoint or open model.
- [ ] Convert strongest bridge pairs into steering or classification interventions.
- [ ] Add anisotropy and directional-curvature proxy checks to activation sweeps where feasible.

## Experiment Track 3: Boundary Priors

- [ ] Specify toy embodied environment.
- [ ] Define self/environment boundary prior.
- [ ] Define perturbation and model-reduction intervention.
- [ ] Choose metrics: adaptability, cooperation, policy entropy, criticality proxy.

## Open Questions Ledger

- [ ] What counts as "same geometry" across substrates: linear map, kernel, topology, dynamics, or intervention? (Webb–Miolane torus is an existence proof for *topological invariant / homology* as an answer-type — same 2-torus across init, architecture, and species; see [notes/webb_miolane_fit.md](notes/webb_miolane_fit.md).)
- [ ] What distinguishes passive representation geometry from active attractor geometry?
- [ ] Can weakness maximization be measured in activation spaces?
- [ ] Can discovery be detected as a regime transition rather than search?
- [ ] What ethical threshold follows if self-maintaining geometry appears in artificial systems?

## Primer-derived research backlog

The six primer reviews are now tracked as page-anchored, gated TODOs rather than
free-floating suggestions. Start at [the backlog index](docs/primers/backlogs/README.md),
then work each article list in its own source order. The index records the
recommended cross-article sequence and the status (`new`, `partial`, or
`existing`) of every item.
