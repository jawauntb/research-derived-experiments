# Research TODO

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
- [x] Start Track 3: Boundary Priors embodied agent (pilot passes all 4 pre-registered gates, diagnostic tier).
- [x] Pre-register External Contact predictions about systems the lab did not build (`docs/external_contact_preregistration.md`).
- [x] Compile a brief on Michael Levin's three most recent papers for Track 3 bearings (`references/levin_recent_papers_2026_06.md`).

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

- [x] Specify toy embodied environment (`experiments/boundary_priors`: K channels, each SELF/WORLD, scarce actuation budget, disjoint boundary shift).
- [x] Define self/environment boundary prior (per-channel self-belief `b_k`; plastic vs. fixed vs. shuffled-attribution conditions).
- [x] Define perturbation and model-reduction intervention (boundary shift at step 300; removable prior via belief decay toward 0.5).
- [x] Choose metrics: adaptability (post-shift reward), boundary accuracy, re-track lag, criticality proxy, probe rate.
- [x] Run a pilot and pre-register gates; commit the public result report (`results/pilot_2026_06_18.md`, all 4 gates pass at diagnostic tier).
- [x] Make probing costly and test selective re-engagement after the shift (`reengagement.py`): re-engagement signature M1+M2+M4 pass 3/3 seeds (quiet→spike→satiate, no false calm); M3 net-reward dominance partial at 2/3. Mechanism tier reached on the signature.
- [ ] Replace uniform-random probing with a coverage-aware probe target; test whether M3 reaches 3/3 without raising probe cost.
- [ ] Let `num_self` change at the shift (lose effectors), a harder TAME-like boundary move.
- [ ] Represent the boundary as a navigable embedding coordinate (Levin 2026 remapping/navigation).

## External Contact (predictions about systems the lab did not build)

Pre-registration: `docs/external_contact_preregistration.md`. Network egress is
currently blocked (HF/PyPI 403; verified 2026-06-18), so each prediction ships a
Tier A (offline stdlib) and Tier B (fetch-when-unblocked) test.

- [x] P3 GloVe (concept geometry, single external family): build and run the Tier A stdlib harness with public GloVe vectors (`experiments/external_contact/results/p3_glove_2026_06_22.md`). All three frozen gates pass after centering (P3a margin 0.106, NMI 0.531; P3b gap 0.252; P3c-2way RSA 0.747), with `autopoiesis` missing from GloVe so the run covers 23/24 concepts.
- [x] P3c-3way amendment (cross-family fastText): pre-registered min-pairwise-RSA >= 0.6 across three families (GloVe-300d, GloVe-100d, fastText-300d). Result at `experiments/external_contact/results/p3_three_family_2026_06_22.md`. **PARTIAL FALSIFICATION**: GloVe-300 vs GloVe-100 RSA = 0.747 (within-family), GloVe-300 vs fastText = 0.543, GloVe-100 vs fastText = 0.346 — min 0.346 fails the 0.6 threshold. fastText alone: P3a margin 0.073 (FAIL), NMI 0.539 (PASS), P3b gap 0.260 (PASS). Allowed claim narrows from "mechanism → regime transition" to "regime transition / partial external load-bearing, substrate-sensitive."
- [x] P2 Tier A (uncertainty≠error / no-false-calm on published deep-ensemble + BALD curves): frozen transcription from Ovadia 2019 Table G.1 + Kirsch 2019 Table 1/§4 in `experiments/external_contact/p2_uncertainty_public.csv`; check at `experiments/external_contact/p2_uncertainty_check.py`; result report at `experiments/external_contact/results/p2_uncertainty_2026_06_22.md`. P2b (BatchBALD strictly beats naive BALD on label budget) PASSES 5/5 comparisons. P2a aggregate proxy (ensemble ECE q75/q25 = 3.55× on CIFAR-10-C) PASSES, but P2a literal (per-sample Pearson r) is NOT checkable against published tables — undecided until Tier B. Allowed claim: regime transition / methodology external load-bearing (partial), NOT the field claim the prereg conditionally allowed.
- [ ] P2 Tier B (Modal, in flight): deep ensembles on CIFAR-10-C, per-sample Pearson r per corruption severity to evaluate the literal P2a threshold. Modal entrypoint at `experiments/external_contact/modal_p2_ensembles_cifar10c.py`.
- [ ] P1 (Modal, in flight): Pythia weakness→OOD on partial-orbit modular addition mod {13,17,23} across pythia-70m/-160m/-410m. Modal entrypoint at `experiments/external_contact/modal_p1_pythia_weakness.py`. P1 smoke (1 size, 1 n, 1 seed) completed; full sweep pending P2 smoke validation.

## Open Questions Ledger

- [ ] What counts as "same geometry" across substrates: linear map, kernel, topology, dynamics, or intervention?
- [ ] What distinguishes passive representation geometry from active attractor geometry?
- [ ] Can weakness maximization be measured in activation spaces?
- [ ] Can discovery be detected as a regime transition rather than search?
- [ ] What ethical threshold follows if self-maintaining geometry appears in artificial systems?
