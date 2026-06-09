# Discovery-Regime Audit Ledger

## Project Regime: Initial Publication

Question: how do we turn the paper synthesis into a public, reproducible research workspace without publishing local-only source archives or secrets?

Current regime:

- Artifact types: synthesis notes, source manifest, TODO ledger, experiment scripts, result JSON, audit cards, rejected alternatives.
- Operations: source archiving, text extraction, synthesis, synthetic simulation, env probing, publication guard, GitHub PR workflow.
- Gates/verifiers: no tracked files over 10 MB, no tracked local source archives, no obvious secret values, Python unit tests, syntax checks, publication guard, human review.
- Known limitations: paper PDFs and full extracted text are local-only; Authorea blocked direct download, but a local PDF with the same DOI is archived.

Action class:

- Retrieval/search/discovery: retrieval plus initial search.
- Why: publication adds already representable artifacts; the first synthetic experiment searches inside the weakness-vs-simplicity schema.

Gate:

- Acceptance rule: public repo can be pushed without large files, full extracted corpora, or secrets; first experiment produces deterministic output and unit tests pass.
- Withheld/rejected rule: full PDFs, extracted text, raw API outputs, and any secret-bearing artifacts stay untracked.

Results:

- Accepted artifacts: `experiments/weakness_vs_simplicity/results/pilot_2026_06_08.md`.
- Rejected or withheld artifacts: `references/papers/`, `references/text/`, `references/html/`.
- Key metrics: trap condition weakness mean Jaccard 0.9533; simplicity mean Jaccard 0.0938; random mean Jaccard 0.5061. No-memorizer control weakness mean Jaccard 0.9587; simplicity mean Jaccard 0.9493. Broad-negative-excluder stress weakness mean Jaccard 0.5246; simplicity mean Jaccard 0.9560. Validated-weakness stress validated weakness mean Jaccard 1.0000; pure weakness mean Jaccard 0.5246.
- Variance or ablation: no-memorizer control, unsafe broad-hypothesis stress test, and validation-gated stress run added.

Residual content:

- Explained by old regime: source collection and synthesis.
- New content outside old regime: none yet.
- Retractions or supersessions: none.

Environment note: `superoptimizers` has Doppler project `cofounder` / config `dev` configured. Presence-only probe found OpenAI, Anthropic, Gemini, Hugging Face, and Modal token variables available. No secret values are recorded here.

Next move: run seed/feature sweeps, then move to text/classification prompts or model-derived rule proposals.

## Concept Geometry Probe: OpenAI Embeddings

Question: can model embeddings make the cross-field geometry convergence hypothesis concrete enough to guide follow-up experiments?

Current regime:

- Artifact types: curated concept prompts, embedding vectors, cosine kernels, category labels, nearest-neighbor summaries, audit cards.
- Operations: OpenAI embedding call, cosine kernel construction, within/across category comparison, top-k neighbor inspection.
- Gates/verifiers: category separation threshold, same-category top-k threshold, qualitative bridge inspection, publication guard.
- Known limitations: hand-curated prompts and labels; language embeddings can encode discourse similarity without proving shared dynamics.

Action class:

- Retrieval/search/discovery: search.
- Why: this explores a model-backed concept geometry within the existing schema.

Gate:

- Acceptance rule: within-category mean cosine exceeds across-category mean cosine by at least `0.10`; top-3 same-category neighbor rate is at least `0.40`; bridge neighborhoods appear among core convergence terms.
- Withheld/rejected rule: raw embeddings and secret-bearing runtime context stay local-only.

Results:

- Accepted artifacts: `experiments/concept_geometry/results/openai_embedding_probe_2026_06_08.md`.
- Rejected or withheld artifacts: `artifacts/concept_geometry/openai_embedding_probe.json`.
- Key metrics: within-category mean cosine `0.4513`; across-category mean cosine `0.2781`; category separation `0.1732`; mean top-3 same-category rate `0.5417`.
- Variance or ablation: deterministic dry-run exists for tooling checks; paraphrase and second-model replications remain open.

Residual content:

- Explained by old regime: ordinary language similarity can explain much of the embedding-space structure.
- New content outside old regime: the model places several cross-field bridges in the neighborhoods we care about, including attractor/attractor-network, conceptual-space/representation-manifold, and valence/activation-vector.
- Retractions or supersessions: this should not be cited as evidence of shared active attractor dynamics.

Next move: run paraphrase perturbations and a second embedding model before moving to activation-space probes.

## Concept Geometry Probe: Paraphrase Stability

Question: does the concept-neighborhood signal survive wording perturbation and a second embedding model?

Current regime:

- Artifact types: concept prompts, paraphrase variants, embedding vectors, concept centroids, bridge-pair scores, cross-model kernel summaries.
- Operations: paraphrase expansion, OpenAI embedding calls, centroid construction, cosine-kernel comparison, bridge-pair scoring.
- Gates/verifiers: paraphrase cohesion, centroid category separation, top-k category rate, cross-model kernel correlation, cross-model neighbor overlap, publication guard.
- Known limitations: evidence remains inside language embedding models; paraphrases and bridge pairs are hand-authored.

Action class:

- Retrieval/search/discovery: search.
- Why: this stress-tests an existing concept-geometry claim without changing the artifact schema or adding an activation-space verifier.

Gate:

- Acceptance rule: mean paraphrase cohesion at least `0.70`; minimum concept mean cohesion at least `0.60`; centroid category separation at least `0.10`; mean top-3 same-category rate at least `0.40`; cross-model kernel Pearson at least `0.80`; cross-model neighbor overlap at least `0.50`.
- Withheld/rejected rule: raw embeddings and model payloads stay local-only under `artifacts/`.

Results:

- Accepted artifacts: `experiments/concept_geometry/results/paraphrase_stability_openai_2026_06_08.md`.
- Rejected or withheld artifacts: `artifacts/concept_geometry/paraphrase_stability_openai.json`.
- Key metrics: small-model paraphrase cohesion `0.7685`; large-model paraphrase cohesion `0.7835`; small-model category separation `0.1661`; large-model category separation `0.1559`; cross-model kernel Pearson `0.8884`; cross-model neighbor overlap `0.7292`.
- Variance or ablation: 72 paraphrase variants across two OpenAI embedding models.

Residual content:

- Explained by old regime: language-level semantic similarity can still explain most of the geometry.
- New content outside old regime: the bridge geometry is paraphrase-invariant and model-stable enough to justify moving into activation-space probes.
- Retractions or supersessions: single-prompt embedding claims should now be treated as weaker than paraphrase-centroid claims.

Next move: extract activation vectors from open models and test whether the same bridge directions appear outside embedding-only language space.

## Activation Geometry Probe: Modal Pythia-70M

Question: does the embedding-space bridge geometry appear in open-model hidden states?

Current regime:

- Artifact types: paraphrased concept prompts, pooled hidden-state vectors, raw and mean-centered concept centroids, bridge-pair scores, activation-space audit cards.
- Operations: Modal-backed open-model extraction, attention-mean pooling, global mean-centering, cosine-kernel summary, bridge-lift comparison.
- Gates/verifiers: deterministic dry-run control, anisotropy inspection, category separation threshold, bridge-lift threshold, bridge-pair rate threshold, publication guard.
- Known limitations: one small model, one layer, one pooling rule, hand-authored bridge pairs, no causal intervention yet.

Action class:

- Retrieval/search/discovery: discovery-leaning search.
- Why: this adds activation-space vectors as a new artifact class for the project, but the result still needs layer/model replication before we should call it a stable mechanism.

Gate:

- Acceptance rule: mean-centered category separation at least `0.05`, bridge lift at least `0.05`, and at least `0.75` of bridge pairs above the non-bridge cross-category mean.
- Withheld/rejected rule: raw activation arrays and full model payloads stay local-only under `artifacts/`.

Results:

- Accepted artifacts: `experiments/activation_geometry/results/modal_pythia_70m_layer_last_2026_06_08.md`.
- Rejected or withheld artifacts: `artifacts/activation_geometry/modal_pythia_70m_layer_last.json`.
- Key metrics: raw category separation `0.0002`; raw bridge lift `0.0002`; mean-centered category separation `0.1356`; mean-centered bridge lift `0.1957`; mean-centered bridge-pair above-baseline rate `0.9167`.
- Variance or ablation: raw-vs-centered comparison and deterministic dry-run only.

Residual content:

- Explained by old regime: language-level concept similarity may still drive the bridge geometry.
- New content outside old regime: bridge structure appears in open-model hidden states after removing the dominant common activation direction.
- Retractions or supersessions: raw activation cosine should not be used as evidence without centering or another anisotropy correction.

Next move: run layer sweeps and a second open model, then test whether selected bridge directions can steer generation or classification behavior.

## Source Assimilation: Muon Curvature Paper

Question: should `Why Muon Outperforms Adam: A Curvature Perspective` change the research program or merely join the source list?

Current regime:

- Artifact types: source manifest entries, local-only source PDFs, synthesis notes, experiment TODOs, audit cards.
- Operations: source triage, relevance assessment, public-safe manifest update, local archive update.
- Gates/verifiers: source should add an actionable metric/control or clarify an existing experiment risk; it should not blur optimizer curvature with representation geometry.
- Known limitations: this paper studies optimizer update directions and Hessian curvature, not concept or agency representations directly.

Action class:

- Retrieval/search/discovery: retrieval plus methods calibration.
- Why: the source is added to the bibliography and used to refine future activation-geometry controls, but it does not create a new experiment regime by itself.

Gate:

- Acceptance rule: use the paper only if it sharpens controls for activation geometry: anisotropy checks, centered-vs-raw comparisons, layerwise decomposition, and possible directional-curvature proxies.
- Withheld/rejected rule: do not pivot into optimizer benchmarking; do not claim NDS of optimizer updates is equivalent to concept geometry.

Results:

- Accepted artifacts: `references/SOURCES.md` entry; synthesis note under "Later Added Method Source"; TODO item for anisotropy and directional-curvature proxy checks.
- Rejected or withheld artifacts: local PDF `references/papers/arxiv_2606_04662_muon_curvature.pdf` remains ignored and untracked.
- Key insight: direction geometry needs curvature/anisotropy controls before it can support mechanistic claims.
- Variance or ablation: none; this is source triage, not an experiment.

Residual content:

- Explained by old regime: it extends the recurring "geometry as constraint" frame into optimizer update directions.
- New content outside old regime: it adds NDS as a candidate method-level control for future activation and training experiments.
- Retractions or supersessions: none.

Next move: keep the current activation layer sweep plan, but report anisotropy and consider cheap directional-curvature proxies before any strong mechanistic claim.

## Activation Geometry Probe: Pythia-70M Layer Sweep

Question: does activation-space bridge geometry survive a layer sweep?

Current regime:

- Artifact types: paraphrased concept prompts, pooled hidden-state vectors, layer-indexed raw and centered geometry summaries, bridge-lift reports, audit cards.
- Operations: Modal-backed open-model extraction, multi-layer hidden-state pooling, global mean-centering, cosine-kernel summary, bridge-lift comparison.
- Gates/verifiers: layerwise centered category separation, bridge lift, bridge-pair rate, raw anisotropy inspection, publication guard.
- Known limitations: one small model, one pooling rule, hand-authored bridge pairs, no causal intervention.

Action class:

- Retrieval/search/discovery: search.
- Why: the run extends the activation-space artifact across layers inside the current schema; it does not yet add a new verifier or causal operation.

Gate:

- Acceptance rule: at least two transformer block-output layers must have centered category separation at least `0.05`, centered bridge lift at least `0.05`, and bridge-pair above-baseline rate at least `0.75`.
- Withheld/rejected rule: raw activation JSON stays untracked under `artifacts/`; layers that fail the gate remain in the public report.

Results:

- Accepted artifacts: `experiments/activation_geometry/results/modal_pythia_70m_layer_sweep_2026_06_08.md`; `experiments/activation_geometry/modal_layer_sweep.py`; layer-sweep payload helpers in `activation_geometry_probe.py`.
- Rejected or withheld artifacts: local-only `artifacts/activation_geometry/modal_pythia_70m_layer_sweep.json`.
- Key metrics: layer `2` centered bridge lift `0.2248`; layer `2` centered category separation `0.1857`; layer `2` centered bridge-pair rate `0.9167`. Layers `1`, `2`, `5`, and `6` clear the block-output gate.
- Variance or ablation: layer `3` and layer `4` fail the gate; layer `6` reproduces the previous final-layer result.

Residual content:

- Explained by old regime: language-level semantic similarity and embedding geometry may explain layer `0`.
- New content outside old regime: centered bridge geometry survives multiple transformer block outputs but weakens sharply in the middle layers.
- Retractions or supersessions: the final-layer result should be treated as one point in a layer-dependent profile, not as the canonical activation geometry of the model.

Next move: replicate the layer sweep on a second open model, then convert the strongest layer-2 bridge pairs into steering or classification interventions.

## Activation Geometry Probe: GPT-2 Layer Sweep

Question: does activation-space bridge geometry replicate in a second open model?

Current regime:

- Artifact types: paraphrased concept prompts, pooled hidden-state vectors, model-indexed and layer-indexed raw and centered geometry summaries, bridge-lift reports, audit cards.
- Operations: Modal-backed open-model extraction, multi-layer hidden-state pooling, global mean-centering, cosine-kernel summary, bridge-lift comparison.
- Gates/verifiers: model replication, layerwise centered category separation, bridge lift, bridge-pair rate, raw anisotropy inspection, publication guard.
- Known limitations: same prompt set, same mean-pooling rule, hand-authored bridge pairs, no causal intervention.

Action class:

- Retrieval/search/discovery: search.
- Why: the run tests transport across a second model inside the current activation-geometry artifact schema.

Gate:

- Acceptance rule: at least two transformer block-output layers must have centered category separation at least `0.05`, centered bridge lift at least `0.05`, and bridge-pair above-baseline rate at least `0.75`.
- Withheld/rejected rule: raw activation JSON stays untracked under `artifacts/`; layers that fail the gate remain in the public report.

Results:

- Accepted artifacts: `experiments/activation_geometry/results/modal_gpt2_layer_sweep_2026_06_08.md`.
- Rejected or withheld artifacts: local-only `artifacts/activation_geometry/modal_gpt2_layer_sweep.json`.
- Key metrics: layer `1` centered bridge lift `0.2348`; layer `1` centered category separation `0.1767`; layer `1` centered bridge-pair rate `1.0000`. Layers `1`, `2`, and `11` clear the block-output gate.
- Variance or ablation: middle layers `3..10` fail the bridge-rate criterion except layer `11`; final layer `12` fails the bridge-rate criterion.

Residual content:

- Explained by old regime: early layers may still reflect lexical and phrase-level semantic geometry rather than active attractor dynamics.
- New content outside old regime: centered bridge geometry replicates across a second open model, but the exact layer profile is not invariant.
- Retractions or supersessions: the Pythia final-layer pass should not be generalized to final layers across models.

Next move: run a pooling ablation, comparing mean pooling against final-token pooling for Pythia and GPT-2 before steering or causal claims.

## Activation Geometry Probe: Pooling Ablation

Question: does centered activation bridge geometry survive a pooling ablation?

Current regime:

- Artifact types: paraphrased concept prompts, pooled hidden-state vectors, model-indexed and layer-indexed raw and centered geometry summaries, pooling-indexed bridge-lift reports, audit cards.
- Operations: Modal-backed open-model extraction, mean pooling, final-token pooling, global mean-centering, cosine-kernel summary, bridge-lift comparison.
- Gates/verifiers: pooling perturbation, model replication, layerwise centered category separation, bridge lift, bridge-pair rate, raw anisotropy inspection, publication guard.
- Known limitations: same prompt set, hand-authored bridge pairs, no causal intervention, no bridge-pair-level stability analysis yet.

Action class:

- Retrieval/search/discovery: verifier upgrade.
- Why: the run adds pooling as an explicit verifier dimension and revises the accepted activation-geometry claim.

Gate:

- Acceptance rule: each model must have at least two transformer block-output layers with centered category separation at least `0.05`, centered bridge lift at least `0.05`, and bridge-pair above-baseline rate at least `0.75`.
- Withheld/rejected rule: raw activation JSON stays untracked under `artifacts/`; failed layers remain in the public report.

Results:

- Accepted artifacts: `experiments/activation_geometry/results/pooling_ablation_pythia_gpt2_2026_06_08.md`; pooling-aware manifest and runner updates.
- Rejected or withheld artifacts: local-only final-token raw activation payloads under `artifacts/activation_geometry/`.
- Key metrics: Pythia final-token layer `5` bridge lift `0.1811`; GPT-2 final-token layer `12` bridge lift `0.3619`.
- Variance or ablation: mean pooling emphasizes early block outputs; final-token pooling emphasizes later block outputs.

Residual content:

- Explained by old regime: centered bridge geometry persists across models and pooling rules.
- New content outside old regime: layer profiles are pooling-dependent; "best layer" is not an intrinsic model property.
- Retractions or supersessions: previous early-layer claims should be stated as mean-pooling claims, not as pooling-independent activation geometry.

Next move: choose candidate intervention layers separately for mean-pooling-style classifiers and final-token-style generation/steering probes.

## Activation Geometry Probe: Intervention Layer Candidates

Question: which layers are eligible for the first classifier and steering interventions?

Current regime:

- Artifact types: concept prompts, activation-layer metrics, pooling-indexed layer profiles, bridge-pair candidates, intervention preregistration notes.
- Operations: layer eligibility filtering, primary/backup/control selection, bridge-pair triage, gate definition.
- Gates/verifiers: centered activation gate, pooling-specific readout rule, held-out paraphrase gate, control-layer gate, control-pair gate.
- Known limitations: pair-level stability has not yet been recomputed for every selected layer; no causal patching has been run.

Action class:

- Retrieval/search/discovery: gate-setting search.
- Why: the run constrains the next causal/search step before outcomes are known.

Gate:

- Acceptance rule: candidate layers must come from accepted model/pooling sweeps and satisfy the role-specific selection rule.
- Withheld/rejected rule: embedding layer `0` and failed bridge-rate layers cannot be primary intervention targets.

Results:

- Accepted artifacts: `experiments/activation_geometry/results/intervention_layer_candidates_2026_06_08.md`.
- Rejected or withheld artifacts: no raw activations added; raw payloads remain local-only.
- Key metrics: mean-pooling primaries Pythia `2` and GPT-2 `1`; final-token primaries Pythia `5` and GPT-2 `12`.
- Variance or ablation: backup/control layers are preregistered for each model/readout.

Residual content:

- Explained by old regime: layer scores can select candidates.
- New content outside old regime: intervention targets are now readout-specific, not global layer claims.
- Retractions or supersessions: do not use a single "best layer" across classifier and generation settings.

Next move: implement the held-out paraphrase classifier/readout pilot before any generative steering claim.

## Activation Geometry Probe: Held-Out Readout Pilot

Question: do selected activation layers preserve bridge structure under held-out paraphrase readout?

Current regime:

- Artifact types: concept prompts, paraphrase-indexed activation payloads, train/holdout centroid readouts, bridge-pair pass tables, control-pair warnings.
- Operations: train-variant centering, nearest-centroid readout, held-out bridge cosine comparison, control-layer comparison.
- Gates/verifiers: held-out paraphrases, preselected primary/backup/control layers, positive bridge-pair gate, valence control gate, publication guard.
- Known limitations: only one holdout variant per concept, hand-authored control pairs, no matched random-pair distribution yet, no causal intervention.

Action class:

- Retrieval/search/discovery: verifier upgrade.
- Why: the run tests whether the earlier activation geometry survives an unseen paraphrase split and exposes control leakage before steering.

Gate:

- Acceptance rule: pass all preregistered held-out readout gates.
- Withheld/rejected rule: raw activation/readout payloads stay local-only under `artifacts/`; mixed gates are reported rather than promoted to causal claims.

Results:

- Accepted artifacts: `experiments/activation_geometry/results/heldout_readout_pilot_2026_06_08.md`; `experiments/activation_geometry/heldout_readout_pilot.py`.
- Rejected or withheld artifacts: local-only raw activation/readout payloads under `artifacts/activation_geometry/`.
- Key metrics: Pythia layer `2` concept accuracy `1.000`, bridge rate `0.833`, positive pairs `4/4`; GPT-2 layer `1` concept accuracy `1.000`, bridge rate `0.917`, positive pairs `4/4`.
- Variance or ablation: Pythia layer `6` has cleaner control pairs than layer `2`; GPT-2 layer `1` has strong positive pairs but leaky valence controls.

Residual content:

- Explained by old regime: concept identity readout can be strong even when some control pairs leak.
- New content outside old regime: held-out bridge structure survives for the four intended pairs, but specificity is not yet adequate for steering claims.
- Retractions or supersessions: do not proceed as if the valence controls failed; at least one valence control is now an adversarial positive control.

Next move: run the pair-level control-leakage diagnostic before the first final-token steering pilot.

## Activation Geometry Probe: Pair-Control Diagnostic

Question: which held-out bridge pairs survive pair-level matched and shuffled controls?

Current regime:

- Artifact types: concept prompts, selected activation payloads, held-out vectors, pair-control distributions, promotion tables.
- Operations: train-variant centering, held-out cosine scoring, exact category-pair matched controls, category-preserving label shuffles.
- Gates/verifiers: matched-control p95, shuffled-label p95, valence adversarial controls, primary/backup/control layers.
- Known limitations: same-category pools are small; this is readout-only and mean-pooling-only.

Action class:

- Retrieval/search/discovery: verifier upgrade.
- Why: the run adds a stronger accepted verifier that the earlier non-bridge baseline could not represent.

Gate:

- Acceptance rule: at least two positive pairs promote in both primary layers and no valence control promotes in either primary layer.
- Withheld/rejected rule: raw activation and diagnostic payloads stay local-only under `artifacts/`; model-specific or layer-control-positive pairs remain warnings rather than promoted causal claims.

Results:

- Accepted artifacts: `experiments/activation_geometry/results/pair_control_diagnostic_2026_06_08.md`; `experiments/activation_geometry/pair_control_diagnostic.py`.
- Rejected or withheld artifacts: local-only payloads under `artifacts/activation_geometry/`.
- Key metrics: Pythia primary layer `2` promotes `3/4` positive pairs and `0/2` valence controls; GPT-2 primary layer `1` promotes `4/4` positive pairs and `0/2` valence controls.
- Variance or ablation: Pythia backup layer `6` promotes `4/4` positive pairs with clean valence controls; control layers are not inert.

Residual content:

- Explained by old regime: weak cross-category baselines can make valence controls look bridge-like.
- New content outside old regime: three bridge pairs survive matched and shuffled controls in both primary layers.
- Retractions or supersessions: `conceptual_space` -> `representation_manifold` is no longer a cross-model primary candidate under strict controls.

Next move: run the first final-token steering pilot using the cross-model promoted pairs, with `conceptual_space` -> `representation_manifold` retained as a backup/model-specific probe.

## Activation Geometry Probe: Final-Token Steering Pilot

Question: do promoted final-token bridge directions causally shift target next-token choice margins?

Current regime:

- Artifact types: selected final-token layers, held-out concept prompts, source-target activation directions, signed intervention payloads, next-token option-margin probes.
- Operations: final-token activation extraction, raw target-minus-source direction construction, transformer-block forward hooks, signed log-probability margin scoring.
- Gates/verifiers: primary/backup/control layers, valence controls, signed reverse intervention, scale ablation.
- Known limitations: fixed option order, raw uncentered directions only, next-token multiple-choice probe rather than free-form generation, no random direction controls yet.

Action class:

- Retrieval/search/discovery: discovery attempt that failed gate.
- Why: this is the first operation that moves from readout geometry to a direct activation intervention, but it does not produce an accepted steering artifact.

Gate:

- Acceptance rule: at scale `1.0`, at least two positive pairs pass in primary and backup layers, no primary valence controls pass, and control layers do not show the same pattern.
- Withheld/rejected rule: raw steering payloads stay local-only under `artifacts/`; failed steering effects are reported as rejected rather than promoted.

Results:

- Accepted artifacts: `experiments/activation_geometry/results/final_token_steering_pilot_2026_06_08.md`; `experiments/activation_geometry/modal_final_token_steering.py`; `experiments/activation_geometry/final_token_steering_pilot.py`.
- Rejected or withheld artifacts: local-only Modal steering payloads.
- Key metrics: Pythia primary layer `5` positive pass `0/3`, valence control pass `2/2`; GPT-2 primary layer `12` positive pass `1/3`, valence control pass `1/2`.
- Variance or ablation: effects are stable across scales `0.5` and `1.0`; Pythia promoted positive directions are consistently opposite-signed for the next-token probe.

Residual content:

- Explained by old regime: readout geometry can select plausible directions but does not guarantee causal control.
- New content outside old regime: raw bridge directions can be systematically wrong-signed or non-specific when hooked into final-token generation layers.
- Retractions or supersessions: do not claim the promoted readout pairs are steering directions without calibration.

Next move: implement a steering calibration diagnostic before any free-form generation run.

## Activation Geometry Probe: Steering Calibration Diagnostic

Question: can steering calibration turn promoted bridge readouts into reliable final-token interventions?

Current regime:

- Artifact types: selected final-token layers, held-out concept prompts, source-target activation directions, direction-mode calibration payloads, option-order randomized next-token margin probes.
- Operations: final-token activation extraction, direction sign/normalization variants, same-norm random direction controls, transformer-block forward hooks, option-order randomized log-probability margin scoring.
- Gates/verifiers: primary/backup/control layers, valence controls, random direction controls, option-order robust-pass rule, cross-model replication.
- Known limitations: one fixed intervention scale, centroid directions only, multiple-choice next-token probe rather than free-form generation, no learned direction objective.

Action class:

- Retrieval/search/discovery: verifier upgrade that rejects the current steering operation.
- Why: this run adds option-order and random-direction controls that the previous steering pilot could not represent, and it clarifies that the current intervention is underidentified.

Gate:

- Acceptance rule: a direction mode must pass at least two of three positive bridge pairs in primary and backup layers, pass no primary valence controls, avoid control-layer replication, and replicate across models.
- Withheld/rejected rule: raw Modal payloads remain local-only under `artifacts/`; partial primary-layer effects are recorded but not promoted.

Results:

- Accepted artifacts: `experiments/activation_geometry/results/steering_calibration_diagnostic_2026_06_08.md`; `experiments/activation_geometry/modal_steering_calibration.py`; `experiments/activation_geometry/steering_calibration_diagnostic.py`.
- Rejected or withheld artifacts: local-only Modal calibration payloads under `artifacts/activation_geometry/`.
- Key metrics: Pythia primary positive pass count never exceeds `1/3`; GPT-2 `raw_target_minus_source` reaches `2/3` primary positives with `0/2` valence controls but fails backup replication; GPT-2 `unit_target_minus_source` reaches `2/3` primary and backup positives but also `2/3` control-layer positives.
- Variance or ablation: direction sign, unit normalization, same-norm random directions, and three option orders tested.

Residual content:

- Explained by old regime: readout-selected bridge pairs can create plausible but non-specific next-token margin shifts.
- New content outside old regime: option-order and random-direction controls show that the current final-token additive intervention is too underidentified for causal claims.
- Retractions or supersessions: do not treat sign-flipped or unit-normalized centroid directions as accepted steering directions.

Next move: redesign the intervention verifier around learned/readout-conditioned directions or causal patching before any free-form generation run.

## Activation Geometry Probe: Steering Gradient-Alignment Diagnostic

Question: are bridge centroid directions aligned with the local output-margin gradient used by the final-token multiple-choice steering probe?

Current regime:

- Artifact types: selected final-token layers, held-out concept prompts, source-target centroid directions, prompt-local output-margin gradients, option-order randomized intervention payloads, centroid-gradient alignment summaries.
- Operations: final-token activation extraction, output-margin gradient capture via activation leaf hook, same-norm gradient and random controls, transformer-block forward hooks, option-order randomized log-probability margin scoring.
- Gates/verifiers: primary/backup/control layers, valence controls, random same-norm controls, option-order robust-pass rule, centroid-gradient cosine, cross-model replication.
- Known limitations: gradients are prompt-local and option-token-local; this is still a multiple-choice next-token probe, not free-form behavior.

Action class:

- Retrieval/search/discovery: verifier transition.
- Why: the run adds a new causal-alignment artifact, `centroid-gradient cosine`, and distinguishes representational readout axes from output-control axes.

Gate:

- Acceptance rule: a semantic steering direction would need primary and backup positive passes without primary valence-control passes or control-layer replication, plus materially positive centroid-gradient alignment.
- Withheld/rejected rule: raw Modal payloads remain local-only under `artifacts/`; gradient directions are treated as nonspecific controls unless they clear specificity gates.

Results:

- Accepted artifacts: `experiments/activation_geometry/results/steering_gradient_alignment_2026_06_08.md`; `experiments/activation_geometry/modal_steering_gradient_alignment.py`; `experiments/activation_geometry/steering_gradient_alignment.py`.
- Rejected or withheld artifacts: local-only Modal gradient-alignment payloads under `artifacts/activation_geometry/`.
- Key metrics: primary positive centroid-gradient cosine is `0.004070` for Pythia-70M and `0.000151` for GPT-2; gradient directions pass `3/3` primary positives but also `2/2` primary valence controls and `3/3` control-layer positives in both models.
- Variance or ablation: centroid, gradient same-norm, gradient unit, random same-norm, and three option orders tested across both models.

Residual content:

- Explained by old regime: readout-selected centroid directions can be stable representational axes without being local causal output-control axes.
- New content outside old regime: bridge centroids are near-orthogonal to prompt-local target-margin gradients across two models, suggesting a separation between representation geometry and the next-token option-control interface.
- Retractions or supersessions: do not use the current multiple-choice gradient as semantic steering evidence; do not expect larger centroid scale alone to solve the causal mismatch.

Next move: test causal patching from target concept activations before searching for larger or more complex additive steering vectors.

## Activation Geometry Probe: Causal Patching Diagnostic

Question: does direct target-concept activation patching rescue final-token bridge interventions?

Current regime:

- Artifact types: selected final-token layers, held-out concept prompts, target/distractor/random/source patch activations, option-order randomized target-margin payloads, specificity summaries.
- Operations: final-token activation extraction, activation replacement hooks, option-order randomized log-probability margin scoring, target-vs-control patch comparison.
- Gates/verifiers: primary/backup/control layers, valence controls, distractor/random/source patch controls, robust positive option-order rule, target-over-best-control specificity rule.
- Known limitations: patch activations are extracted from concept-definition prompts, while the behavioral probe uses an option-choice prompt.

Action class:

- Retrieval/search/discovery: verifier upgrade that rejects the current behavioral interface.
- Why: the run adds full-state causal patching as a stricter intervention operation than additive centroid steering.

Gate:

- Acceptance rule: positive bridge pairs must show primary-layer target-specific passes that beat distractor, random, and source-concept patch controls without valence-control leakage or control-layer replication.
- Withheld/rejected rule: raw Modal payloads remain local-only under `artifacts/`; backup-only and control-layer-only target-specific rows are warnings.

Results:

- Accepted artifacts: `experiments/activation_geometry/results/causal_patching_diagnostic_2026_06_08.md`; `experiments/activation_geometry/modal_causal_patching.py`; `experiments/activation_geometry/causal_patching_diagnostic.py`.
- Rejected or withheld artifacts: local-only Modal causal-patching payloads under `artifacts/activation_geometry/`.
- Key metrics: Pythia primary positive target-specific passes `0/3`; GPT-2 primary positive target-specific passes `0/3`.
- Variance or ablation: target, distractor, random, and source-concept patch controls tested across primary, backup, and control layers with three option orders.

Residual content:

- Explained by old regime: readout-selected bridge pairs need not become final-token answer-choice controls.
- New content outside old regime: full target activation patching fails the same primary-layer target-specific gate, suggesting the answer-choice surface or context mismatch is the likely failure source.
- Retractions or supersessions: do not treat direct concept activation patching as accepted causal bridge evidence for this probe.

Next move: run matched-context activation patching before abandoning the final-token multiple-choice interface.

## Activation Geometry Probe: Matched-Context Patching Diagnostic

Question: does matched-context activation patching rescue final-token bridge interventions?

Current regime:

- Artifact types: selected final-token layers, matched option-choice patch prompts, target/distractor/random/source hook-surface activations, option-order randomized target-margin payloads, specificity summaries.
- Operations: answer-choice prompt construction, hook-surface activation capture, activation replacement hooks, option-order randomized log-probability margin scoring, target-vs-control patch comparison.
- Gates/verifiers: exact `source_noop` sanity control, primary/backup/control layers, valence controls, distractor/random/source patch controls, robust option-order rule, target-over-best-control specificity rule.
- Known limitations: one context variant, one random-patch seed, two small causal LMs, and no free-form or downstream behavioral task.

Action class:

- Retrieval/search/discovery: regime refinement.
- Why: the run revises the intervention artifact from bare concept-state patching to matched answer-choice context-state patching, and the no-op sanity gate exposes the need to capture patch vectors at the hook surface.

Gate:

- Acceptance rule: promote only cross-model primary positive target-specific passes without primary valence-control leakage or control-layer replication.
- Withheld/rejected rule: model-specific pockets and leaky controls are reported but not promoted to semantic bridge-causality claims.

Results:

- Accepted artifacts: `experiments/activation_geometry/results/matched_context_patching_2026_06_08.md`; `experiments/activation_geometry/modal_matched_context_patching.py`; `experiments/activation_geometry/matched_context_patching.py`.
- Rejected or withheld artifacts: cross-model semantic bridge claim is rejected; Pythia-specific matched-context pocket is withheld pending replication.
- Key metrics: Pythia primary positive target-specific passes `2/3` with `1/2` valence-control leakage; GPT-2 primary positive target-specific passes `0/3`; max absolute `source_noop` aggregate delta `0.0` in both models.
- Variance or ablation: target, distractor, random, and exact source-context patch controls tested across primary, backup, and control layers with three option orders.

Residual content:

- Explained by old regime: readout-selected bridge pairs do not automatically imply cross-model causal steering.
- New content outside old regime: context matching can turn previously rejected direct patching into a Pythia-specific causal pocket.
- Retractions or supersessions: do not say final-token patching is simply dead; do not promote the Pythia pocket until it survives replication and leakage controls.

Next move: replicate the Pythia matched-context pocket across variants, random seeds, and a nearby layer scan before trying free-form generation.

## Activation Geometry Probe: Pythia Matched-Context Replication

Question: does the Pythia matched-context patching pocket survive variants, random-control seeds, and nearby layers?

Current regime:

- Artifact types: matched-context patch payloads, hook-surface no-op controls, specificity rows, replication-grid summaries.
- Operations: context-variant sweep, random-control seed sweep, nearby-layer sweep, target-vs-control aggregation.
- Gates/verifiers: exact `source_noop` aggregate gate, target-over-best-control specificity gate, valence-control leakage check, variant/seed/layer stability check.
- Known limitations: Pythia-only, three layers, three context variants, three random-control seeds, no third-model replication yet.

Action class:

- Retrieval/search/discovery: search inside the matched-context patching regime.
- Why: the experiment perturbs variants, seeds, and layers without changing the artifact type or verifier.

Experiment:

- Manifest/report paths: `experiments/activation_geometry/results/pythia_matched_context_replication_2026_06_08.md`; local ignored payloads under `artifacts/activation_geometry/modal_pythia_70m_matched_context_repl_v*_s*_l456.json`.
- Positive targets: `attractor` -> `attractor_network`, `autopoiesis` -> `homeostasis`, `validity_gate` -> `weak_constraint`.
- Negative controls: `valence` -> `activation_vector`, `valence` -> `steering_vector`, distractor/random/source patch modes.
- Stress tests: context variants `0/1/2`, seeds `20260608/20260609/20260610`, layers `4/5/6`.

Gate:

- Acceptance rule: promote only effects that pass across variants and seeds at the target layer and do not look like valence-control leakage.
- Withheld/rejected rule: broad bridge mechanism is withheld if only one pair survives or controls show similar target-specific passes.

Results:

- Accepted artifacts: `experiments/activation_geometry/results/pythia_matched_context_replication_2026_06_08.md`; `experiments/activation_geometry/matched_context_replication.py`.
- Rejected or withheld artifacts: broad Pythia matched-context bridge mechanism remains withheld.
- Key metrics: layer-5 `attractor` -> `attractor_network` specific passes `9/9`; layer-5 `autopoiesis` -> `homeostasis` specific passes `3/9`; layer-5 `validity_gate` -> `weak_constraint` specific passes `0/9`; layer-5 valence controls specific passes `9/18`.
- Variance or ablation: `attractor` survives all variants and seeds; other candidate pairs are variant-dependent or fail.

Residual content:

- Explained by old regime: context matching can make some final-token patches causal in Pythia.
- New content outside old regime: the stable residual is not a broad bridge class; it is a narrow attractor-network pocket at layer `5`.
- Retractions or supersessions: supersede the previous "Pythia matched-context pocket" phrasing with the narrower "Pythia layer-5 attractor-network pocket".

Next move: run a focused attractor-pocket diagnostic with distractor sweeps, adversarial near-neighbor controls, and third-model or second-checkpoint replication.

## Activation Geometry Probe: Focused Attractor-Pocket Diagnostic

Question: does the focused attractor-network pocket survive distractor sweeps, adversarial near-neighbor controls, and second-checkpoint replication?

Current regime:

- Artifact types: matched-context patch payloads, specificity rows, focused gate summaries, near-neighbor leakage rows.
- Operations: distractor/frame sweep, target near-control, source near-control, second-checkpoint replication.
- Gates/verifiers: exact `source_noop` gate, positive distractor-sweep gate, near-control leakage gate, checkpoint-stability gate.
- Known limitations: only two Pythia-70M checkpoints, one context variant, answer-choice prompt surface only.

Action class:

- Retrieval/search/discovery: search inside the matched-context patching regime.
- Why: this run changes prompts, distractors, controls, and checkpoint while preserving the same causal-patching artifact type and verifier family.

Experiment:

- Manifest/report paths: `experiments/activation_geometry/results/attractor_pocket_diagnostic_2026_06_08.md`; local ignored payloads under `artifacts/activation_geometry/modal_pythia_70m*_attractor_pocket.json`.
- Positive targets: `attractor` -> `attractor_network` across two prompt frames and four distractors.
- Negative controls: `attractor` -> `prototype`, `attractor` -> `schema`, `prototype` -> `attractor_network`, `schema` -> `attractor_network`, plus distractor/random/source patch modes.
- Stress tests: prompt-frame sweep, distractor sweep, near-neighbor source/target swaps, second Pythia-family checkpoint.

Gate:

- Acceptance rule: promote the pocket only if all positive primary rows pass, near-neighbor controls clear, source no-op is exact, and the second checkpoint supports the effect.
- Withheld/rejected rule: reject a clean bridge claim if near-neighbor controls mimic the same target-specific pattern or if the effect weakens on the second checkpoint.

Results:

- Accepted artifacts: `experiments/activation_geometry/results/attractor_pocket_diagnostic_2026_06_08.md`; `experiments/activation_geometry/attractor_pocket_diagnostic.py`; `experiments/activation_geometry/modal_attractor_pocket_diagnostic.py`.
- Rejected or withheld artifacts: clean `attractor` -> `attractor_network` bridge claim is rejected.
- Key metrics: deduped primary positives `6/8`; deduped primary near-controls `4/8`; non-deduped primary positives `4/8`; non-deduped primary near-controls `1/8`; max source-noop delta `0.0`.
- Variance or ablation: deduped has a stronger but leakier basin; non-deduped has a weaker basin and no positive mean advantage.

Residual content:

- Explained by old regime: matched-context final-token patching can bias answer-choice margins.
- New content outside old claim: the surviving pattern is broader than one semantic bridge and looks like an attractor-family answer-choice basin.
- Retractions or supersessions: supersede "Pythia layer-5 attractor-network pocket" with "Pythia-70M-deduped layer-5 attractor-family answer-choice basin."

Next move: implement the answer-surface basin diagnostic to distinguish semantic source/target effects from label/option-surface effects.

## Activation Geometry Probe: Answer-Surface Basin Diagnostic

Question: does the attractor-family basin follow semantic source/target content, visible labels, or the option-choice surface?

Current regime:

- Artifact types: answer-surface patch payloads, label-regime rows, patch-text-regime rows, specificity summaries.
- Operations: canonical/alias/symbol relabeling, neutral-carrier patch prompts, source-family sweep, layer comparison.
- Gates/verifiers: exact definition-source no-op gate, neutral-carrier failure gate, symbol-label failure gate, alias-preservation gate.
- Known limitations: one model checkpoint, one context variant, still uses an answer-choice interface.

Action class:

- Retrieval/search/discovery: discovery-leaning verifier revision.
- Why: this adds new accepted artifact dimensions, label regimes and patch-text regimes, that the previous matched-context verifier could not represent.

Experiment:

- Manifest/report paths: `experiments/activation_geometry/results/answer_surface_basin_diagnostic_2026_06_08.md`; local ignored payload under `artifacts/activation_geometry/modal_pythia_70m_deduped_answer_surface_basin.json`.
- Positive targets: `attractor` -> `attractor_network`.
- Negative controls: neutral patch text, symbol labels, distractor/random/source patch modes.
- Stress tests: source-family sweep, canonical/alias/symbol labels, definition/neutral patch text, primary/control layer comparison.

Gate:

- Acceptance rule: call it semantically mediated only if aliases preserve the effect while neutral patch prompts and symbol labels break it.
- Withheld/rejected rule: reject label-free activation-space claims until a no-answer-choice readout test reproduces the basin.

Results:

- Accepted artifacts: `experiments/activation_geometry/results/answer_surface_basin_diagnostic_2026_06_08.md`; `experiments/activation_geometry/answer_surface_basin_diagnostic.py`; `experiments/activation_geometry/modal_answer_surface_basin.py`.
- Rejected or withheld artifacts: pure label-only artifact claim is rejected; label-free activation-space basin claim is withheld.
- Key metrics: primary canonical definitions `3/5`; primary alias definitions `3/5`; primary canonical neutral `0/5`; primary alias neutral `0/5`; primary symbol definitions `0/5`; exact definition-source no-op max delta `0.0`.
- Variance or ablation: control layer `6` has weak canonical-definition passes, so the basin is not uniquely localized to layer `5`.

Residual content:

- Explained by old regime: the multiple-choice final-token surface can carry target-margin effects.
- New content outside old claim: the effect requires semantic definitions and meaningful labels, but spreads across nearby source concepts.
- Retractions or supersessions: supersede "answer-choice label artifact" with "semantically mediated answer-surface basin."

Next move: run a label-free readout basin diagnostic to test whether the basin exists in activation space without visible answer choices.

## Activation Geometry Probe: Label-Free Readout Basin Diagnostic

Question: does the semantically mediated attractor-family basin exist in activation space without visible answer choices?

Current regime:

- Artifact types: label-free patch payloads, centroid-readout rows, definition/neutral patch-text controls, specificity summaries.
- Operations: held-out centroid readout training, layer-5 activation patching, layer-6 downstream readout scoring.
- Gates/verifiers: exact definition-source no-op gate, target-over-control readout specificity gate, neutral-carrier failure gate, generic-transfer control check.
- Known limitations: one model checkpoint, one injection/readout layer pair, centroid readout rather than a trained linear classifier.

Action class:

- Retrieval/search/discovery: search inside the upgraded label-free readout regime.
- Why: this run tests the new no-answer-choice verifier but does not yet establish a new attractor-specific artifact class.

Experiment:

- Manifest/report paths: `experiments/activation_geometry/results/label_free_readout_basin_2026_06_08.md`; local ignored payload under `artifacts/activation_geometry/modal_pythia_70m_deduped_label_free_readout_basin.json`.
- Positive targets: `attractor` -> `attractor_network`.
- Negative controls: neutral patch text, distractor/random/source patch modes.
- Stress tests: source-family sweep into `attractor_network`, generic valence/vector transfer controls.

Gate:

- Acceptance rule: accept label-free transfer if definition target patches pass specificity and neutral label-carrier patches fail.
- Withheld/rejected rule: withhold attractor-specific basin claims if generic transfer controls also pass.

Results:

- Accepted artifacts: `experiments/activation_geometry/results/label_free_readout_basin_2026_06_08.md`; `experiments/activation_geometry/label_free_readout_basin.py`; `experiments/activation_geometry/modal_label_free_readout_basin.py`.
- Rejected or withheld artifacts: attractor-specific activation-space basin claim is withheld.
- Key metrics: definition positive `1/1`; definition source-family `4/4`; definition generic controls `2/2`; neutral rows `0/7`; definition source-noop max delta `0.0`.
- Variance or ablation: definition patches transfer strongly; neutral label-carrier patches do not pass specificity.

Residual content:

- Explained by old regime: answer-choice target-margin effects can be semantically mediated.
- New content outside old claim: the target-state transfer survives without visible answer choices, but it appears generic rather than attractor-specific.
- Retractions or supersessions: supersede "semantically mediated answer-surface basin" with "generic label-free definition-derived target-state transfer; attractor-family rows are currently a special case only by topic, not by mechanism."

Next move: build a broad label-free target-state transfer baseline across many concept pairs and compare the attractor-family rows against that null distribution.

## Activation Geometry Probe: Label-Free Transfer Baseline

Question: are the attractor-family label-free transfer rows exceptional against a broad null distribution?

Current regime:

- Artifact types: label-free patch payloads, centroid-readout rows, sampled baseline-pair rows, transfer-baseline summaries.
- Operations: held-out centroid readout training, layer-5 activation patching, layer-6 downstream readout scoring, sampled same-category and cross-category baseline construction.
- Gates/verifiers: exact definition-source no-op gate, target-over-control readout specificity gate, neutral-carrier stress test, baseline percentile comparison.
- Known limitations: one checkpoint, one injection/readout layer pair, one alpha, limited concept inventory.

Action class:

- Retrieval/search/discovery: search inside the label-free readout regime.
- Why: the run extends the null distribution without changing the intervention artifact type.

Experiment:

- Manifest/report paths: `experiments/activation_geometry/results/label_free_transfer_baseline_2026_06_08.md`; local ignored payload under `artifacts/activation_geometry/modal_pythia_70m_deduped_label_free_transfer_baseline.json`.
- Positive targets: `attractor` -> `attractor_network`.
- Negative controls: neutral patch text, distractor/random/source patch modes.
- Stress tests: 56 sampled baseline pairs split across same-category and cross-category rows.

Gate:

- Acceptance rule: promote attractor exceptionality only if focus/source-family rows sit high in the baseline advantage distribution.
- Withheld/rejected rule: withhold attractor-specific claims if baseline rows pass at comparable or higher rates.

Results:

- Accepted artifacts: `experiments/activation_geometry/results/label_free_transfer_baseline_2026_06_08.md`; `experiments/activation_geometry/label_free_readout_basin.py`; `experiments/activation_geometry/modal_label_free_readout_basin.py`.
- Rejected or withheld artifacts: attractor-specific activation basin claim is withheld.
- Key metrics: definition baseline passes `43/56`; definition positive `1/1`; definition source-family `4/4`; source-family mean advantage percentile `71.4%`; source-family max advantage percentile `85.7%`; neutral baseline passes `7/56`.
- Variance or ablation: definition content dominates neutral label-carrier transfer; cross-category definition baseline rows are stronger than same-category rows in this sample.

Residual content:

- Explained by old regime: the label-free attractor rows are examples of generic definition-derived target-state transfer.
- New content outside old regime: the broader mechanism itself is now the residual worth explaining.
- Retractions or supersessions: supersede "generic label-free target-state transfer, attractor-family special case uncertain" with "broad label-free target-state transfer; attractor-specific exceptionality rejected for now."

Next move: run a layer/alpha dose-response to determine whether generic transfer is a late-state overwrite artifact or a propagating intervention.

## Activation Geometry Probe: Label-Free Transfer Dose Response

Question: is broad label-free target-state transfer a late overwrite, or does it have a downstream layer/alpha regime?

Current regime:

- Artifact types: label-free patch payloads, centroid-readout rows, sampled baseline-pair rows, patch-alpha grid summaries.
- Operations: held-out centroid readout training, activation patching at selected injection layers, downstream layer-6 readout scoring, target-vs-control specificity aggregation.
- Gates/verifiers: strict downstream source-noop gate, target-over-control specificity gate, neutral-carrier stress test, alpha dose-response.
- Known limitations: one checkpoint, one readout layer, small baseline sample, unresolved same-layer hook/readout mismatch.

Action class:

- Retrieval/search/discovery: discovery-leaning verifier refinement.
- Why: the run adds alpha as a first-class grid dimension and exposes a missing artifact type for same-layer hook/readout-surface validity.

Experiment:

- Manifest/report paths: `experiments/activation_geometry/results/label_free_transfer_dose_response_2026_06_08.md`; local ignored payload under `artifacts/activation_geometry/modal_pythia_70m_deduped_label_free_dose_response.json`.
- Positive targets: focus rows plus 8 sampled baseline pairs.
- Negative controls: neutral patch text, distractor/random/source patch modes.
- Stress tests: injection layers `2,3,4,5,6`; patch alphas `0.25,0.5,0.75,1.0`; strict downstream no-op filtering.

Gate:

- Acceptance rule: accept a downstream transfer ridge only if strict downstream source-noop is exact and definition patches show a layer/alpha increase that neutral carriers do not match.
- Withheld/rejected rule: withhold same-layer cells if source-noop is nonzero; reject a pure late-overwrite interpretation if earlier strict downstream layers show specific dose-responsive transfer.

Results:

- Accepted artifacts: `experiments/activation_geometry/results/label_free_transfer_dose_response_2026_06_08.md`; `experiments/activation_geometry/label_free_readout_basin.py`; `experiments/activation_geometry/modal_label_free_readout_basin.py`.
- Rejected or withheld artifacts: same-layer `6 -> 6` interpretation is withheld.
- Key metrics: strict downstream definition source-noop max delta `0.0`; layer `4 -> 6` definition pass rate reaches `10/15`; layer `5 -> 6` definition pass rate reaches `11/15`; neutral carrier pass rates remain at or below `2/15` in all strict downstream cells.
- Variance or ablation: baseline-only rows show the same layer/alpha ridge with lower pass rates; source-family rows are stronger but no longer the sole phenomenon.

Residual content:

- Explained by old regime: broad target-state transfer is a generic definition-derived phenomenon, not attractor-specific.
- New content outside old regime: the transfer has a mid/late downstream ridge and an alpha dose-response.
- Retractions or supersessions: supersede "maybe a late overwrite" with "strict downstream transfer is strongest from layers 4-5 into layer 6; same-layer cells are invalid under current hook/readout instrumentation."

Next move: replicate the downstream ridge with more baseline rows and a second seed/checkpoint, while separately diagnosing same-layer hook/readout validity.

## Activation Geometry Probe: Same-Layer Hook-Surface Diagnostic

Question: did same-layer label-free patching fail because the intervention is non-identity, or because patch vectors were captured at the wrong surface?

Current regime:

- Artifact types: label-free patch payloads, patch-vector-surface summaries, source-noop sanity tables.
- Operations: hidden-state vector capture, hook-output vector capture, transformer-block final-token patching, downstream readout scoring.
- Gates/verifiers: source-noop max absolute delta by patch-vector surface and injection/readout pair.
- Known limitations: one model checkpoint, one patch alpha, focus pairs only.

Action class:

- Retrieval/search/discovery: verifier refinement.
- Why: the run adds patch-vector surface as a first-class verifier dimension and fixes an invalid same-layer measurement.

Experiment:

- Manifest/report paths: `experiments/activation_geometry/results/same_layer_hook_surface_diagnostic_2026_06_08.md`; local ignored payloads under `artifacts/activation_geometry/modal_pythia_70m_same_layer_*_surface.json`.
- Positive targets: focus rows from the label-free readout diagnostic.
- Negative controls: distractor/random/source-noop patch modes.
- Stress tests: compare `hidden_state` against `hook_output` for `5 -> 6` and `6 -> 6`.

Gate:

- Acceptance rule: same-layer cells become interpretable only if `source_noop` is exactly zero at the hook surface.
- Withheld/rejected rule: withhold any same-layer surface that fails source-noop identity.

Results:

- Accepted artifacts: `experiments/activation_geometry/results/same_layer_hook_surface_diagnostic_2026_06_08.md`; `experiments/activation_geometry/modal_label_free_readout_basin.py`; `experiments/activation_geometry/label_free_readout_basin.py`.
- Rejected or withheld artifacts: hidden-state same-layer `6 -> 6` remains rejected as an invalid surface.
- Key metrics: hidden_state `6 -> 6` max source-noop delta `0.247`; hook_output `6 -> 6` max source-noop delta `0.0`; hook_output preserves `5 -> 6` source-noop max delta `0.0`.
- Variance or ablation: `5 -> 6` is identical across surfaces; final-layer same-layer behavior changes only when surface alignment matters.

Residual content:

- Explained by old regime: PR #24's strict downstream ridge remains valid.
- New content outside old regime: patch-vector surface must be explicit for same-layer/final-layer patching.
- Retractions or supersessions: supersede "same-layer cells invalid/unknown" with "same-layer cells are valid under hook-output patch vectors and invalid under post-final-LN hidden-state patch vectors."

Next move: rerun the broader dose-response with `hook_output` and a larger baseline sample.

## Activation Geometry Probe: Hook-Output Dose-Response Replication

Question: does the label-free transfer ridge survive hook-output surface correction, a broader baseline, and a second seed?

Current regime:

- Artifact types: label-free patch payloads, hook-output patch-vector manifests, sampled baseline-pair rows, source-noop identity tables, dose-response summaries.
- Operations: hook-output activation capture, held-out centroid readout training, final-token activation patching at transformer-block outputs, target-vs-control specificity aggregation.
- Gates/verifiers: exact source-noop identity, definition-vs-neutral stress, alpha dose-response, baseline percentile comparison, two-seed replication.
- Known limitations: one checkpoint, one readout layer, nearest-centroid readout, no behavior-level task yet.

Action class:

- Retrieval/search/discovery: consolidation search with verifier refinement.
- Why: the run keeps the existing label-free patch schema but tests the ridge under a corrected surface, larger null, and second seed; the accepted same-layer cell revises a previously withheld artifact class.

Experiment:

- Manifest/report paths: `experiments/activation_geometry/results/hook_output_dose_response_replication_2026_06_08.md`; local ignored payloads under `artifacts/activation_geometry/modal_pythia_70m_hook_output_dose_response_seed*.json`.
- Positive targets: focus rows plus 24 sampled baseline pairs per seed.
- Negative controls: neutral patch text, distractor/random/source-noop patch modes, broad baseline rows.
- Stress tests: injection layers `3,4,5,6`; alphas `0.5,0.75,1.0`; two seeds; same-layer hook-output identity.

Gate:

- Acceptance rule: accept the replicated ridge only if source-noop is exact, definition patches show a stable layer/alpha specificity ridge across seeds, and neutral carriers do not match it.
- Withheld/rejected rule: reject attractor-specific revival unless focus/source-family rows are clearly exceptional against baseline and generic controls.

Results:

- Accepted artifacts: `experiments/activation_geometry/results/hook_output_dose_response_replication_2026_06_08.md`; `scripts/summarize_label_free_dose_response.py`.
- Rejected or withheld artifacts: no hook-output same-layer cells are withheld; attractor-specific revival is rejected.
- Key metrics: source-noop max delta `0.0` across 744 aggregates; combined definition pass rates reach `38/62` at `4 -> 6`, `46/62` at `5 -> 6`, and `54/62` at `6 -> 6`; neutral at `6 -> 6`, alpha `1.0` reaches only `13/62`.
- Variance or ablation: two seeds agree on the layer/alpha ridge; baseline-only rows show the same ridge, with `40/48` passes at `6 -> 6`, alpha `1.0`.

Residual content:

- Explained by old regime: broad definition-derived transfer remains generic rather than attractor-specific.
- New content outside old regime: same-layer `6 -> 6` is now a valid hook-output artifact and is the strongest point on the ridge.
- Retractions or supersessions: supersede "same-layer cells are invalid/unknown" with "same-layer cells are valid under hook-output patch vectors, but not attractor-specific."

Next move: use trained readouts and behavior-level gates to distinguish representational transport from readout-only movement.

## Activation Geometry Probe: Trained Readout Gate

Question: does the hook-output label-free transfer ridge survive a trained readout?

Current regime:

- Artifact types: label-free patch payloads, hook-output patch-vector manifests, centroid/ridge readout summaries, source-noop identity tables, baseline percentile summaries.
- Operations: hook-output activation capture, held-out centroid readout scoring, one-vs-all multiclass ridge fitting, final-token activation patching at transformer-block outputs.
- Gates/verifiers: exact definition/source-noop identity, definition-vs-neutral stress, centroid-vs-ridge readout agreement, two-seed replication, baseline percentile comparison.
- Known limitations: one checkpoint, one readout layer, no behavior-level task yet.

Action class:

- Retrieval/search/discovery: verifier refinement.
- Why: the run adds trained readout mode as a first-class verifier dimension and tests whether the existing ridge survives a different scoring surface.

Experiment:

- Manifest/report paths: `experiments/activation_geometry/results/trained_readout_gate_2026_06_08.md`; local ignored payloads under `artifacts/activation_geometry/modal_pythia_70m_trained_readout_gate_seed*.json`.
- Positive targets: focus rows plus 24 sampled baseline pairs per seed.
- Negative controls: neutral patch text, distractor/random/source-noop patch modes, broad baseline rows.
- Stress tests: readout modes `centroid,ridge`; injection layers `4,5,6`; alphas `0.75,1.0`; two seeds.

Gate:

- Acceptance rule: accept readout-mode robustness only if ridge readout preserves the definition transfer ridge, definition/source-noop is exact, and neutral carriers do not match definition specificity.
- Withheld/rejected rule: reject attractor-specific revival unless focus/source-family rows are clearly exceptional against baseline and generic controls.

Results:

- Accepted artifacts: `experiments/activation_geometry/results/trained_readout_gate_2026_06_08.md`; `experiments/activation_geometry/modal_label_free_readout_basin.py`; `experiments/activation_geometry/label_free_readout_basin.py`; `scripts/summarize_label_free_dose_response.py`.
- Rejected or withheld artifacts: attractor-specific revival remains rejected.
- Key metrics: definition/source-noop max delta `0.0`; ridge definition pass rates reach `42/62` at `4 -> 6`, `53/62` at `5 -> 6`, and `57/62` at `6 -> 6`; ridge neutral at `6 -> 6`, alpha `1.0` reaches `17/62`.
- Variance or ablation: both seeds show the same layer ordering; ridge margins shrink relative to centroid while pass rates stay strong or improve.

Residual content:

- Explained by old regime: broad definition-derived transfer remains generic rather than attractor-specific.
- New content outside old regime: the transfer ridge survives a trained linear readout and is not merely nearest-centroid geometry.
- Retractions or supersessions: supersede "centroid readout may be producing the ridge" with "centroid is not necessary for the ridge, though readout-space movement still needs behavior-level validation."

Next move: add a behavior-level gate that tests whether readout-space transport predicts answer/logprob changes.

## Activation Geometry Probe: Behavior-Level Gate

Question: does the trained-readout-confirmed hook-output transfer ridge change next-token behavior?

Current regime:

- Artifact types: hook-output patch payloads, centroid/ridge readout summaries, behavior prompt frames, option-order logprob rows, target-vs-control specificity summaries.
- Operations: label-free definition/neutral patch-vector capture, final-token activation patching, option-token logprob scoring, prompt-frame ablation.
- Gates/verifiers: target patch must robustly improve target margin across option orders and beat distractor/random/source-noop controls; neutral carriers should not match definition specificity.
- Known limitations: one checkpoint, option-token answer surface, no learned behavior-aligned direction.

Action class:

- Retrieval/search/discovery: verifier transition with rejected claim.
- Why: this run adds behavior-level logprob scoring as a new verifier type and tests whether the representational ridge crosses into model choices.

Experiment:

- Manifest/report paths: `experiments/activation_geometry/results/behavior_level_gate_2026_06_08.md`; local ignored payloads under `artifacts/activation_geometry/modal_pythia_70m_behavior_gate*.json`.
- Positive targets: focus rows plus 8 sampled baseline pairs.
- Negative controls: neutral patch text, distractor/random/source-noop patch modes, option-order controls.
- Stress tests: prompt frames `source_passage` and `latent_choice`; injection layers `4,5,6`; alphas `0.75,1.0`.

Gate:

- Acceptance rule: accept behavior transfer only if definition target patches have positive robust target-margin movement and positive target-over-control advantage.
- Withheld/rejected rule: withhold behavior-level claims if controls match or exceed target patches.

Results:

- Accepted artifacts: `experiments/activation_geometry/modal_label_free_behavior_gate.py`; `experiments/activation_geometry/label_free_behavior_gate.py`; `scripts/summarize_label_free_behavior_gate.py`; `experiments/activation_geometry/results/behavior_level_gate_2026_06_08.md`.
- Rejected or withheld artifacts: behavior-level transfer claim is withheld.
- Key metrics: definition source-passage max pass rate `3/15`; definition latent-choice max pass rate `2/15`; mean target-over-control advantage is non-positive in every definition cell.
- Variance or ablation: removing source-passage text does not rescue target specificity.

Residual content:

- Explained by old regime: readout-space movement remains real but does not imply behavioral steering.
- New content outside old regime: the project now has a behavior verifier that can reject overclaims.
- Retractions or supersessions: supersede "next step may confirm behavior transfer" with "simple behavior transfer fails under option-token gates; behavior alignment needs a stronger intervention or different interface."

Next move: design a behavior-aligned intervention rather than raw state replacement.

## Activation Geometry Probe: Behavior Alignment Breakthrough Path

Question: after the option-token behavior gate failed, can full-label scoring or learned behavior-aligned directions expose behavior-level transfer?

Current regime:

- Artifact types: hook-output patch payloads, option-token behavior rows, full-label continuation rows, learned-gradient direction rows, target-vs-control specificity summaries.
- Operations: label-free definition/neutral state capture, final-token hook-output replacement, full-label continuation logprob scoring, train-variant gradient averaging, held-out option-token intervention.
- Gates/verifiers: target must beat distractor/random/source-noop controls; definition should exceed neutral carrier; learned target direction should exceed source/distractor/random directions and avoid valence/control-layer leakage.
- Known limitations: one seed, one small causal LM, exact-label scoring, neutral carriers are active, learned directions are still option-token based.

Action class:

- Retrieval/search/discovery: verifier transition plus intervention search.
- Why: full-label scoring creates a new behavior verifier that accepts effects the previous option-token verifier rejected; learned directions add a new behavior-aligned intervention class.

Experiment:

- Manifest/report paths: `experiments/activation_geometry/results/behavior_alignment_breakthrough_2026_06_08.md`; local ignored payloads under `artifacts/activation_geometry/modal_pythia_70m_full_label_behavior*.json` and `artifacts/activation_geometry/modal_pythia_70m_behavior_aligned_direction_seed20260608.json`.
- Positive targets: focus rows plus 8 sampled baseline pairs for full-label; promoted steering pairs for learned directions.
- Negative controls: neutral patch text, distractor/random/source-noop patch modes, source/distractor learned directions, random same-norm direction, valence controls, control layer.
- Stress tests: prompt frames `latent_choice` and `source_passage`; injection layers `4,5,6`; alphas `0.75,1.0`; learned scales `0.5,1.0,2.0`.

Gate:

- Acceptance rule: accept behavior-surface improvement if definition target patches beat controls and definition carriers exceed neutral carriers on average.
- Withheld/rejected rule: withhold clean semantic-causality or learned-direction claims if neutral carriers, valence controls, or control-layer directions match too much of the effect.

Results:

- Accepted artifacts: full-label behavior scoring surface; learned behavior-aligned direction pilot; Modal packaging fix for learned-direction runner.
- Rejected or withheld artifacts: clean semantic-causality claim and learned-direction mechanism claim remain withheld.
- Key metrics: full-label definition target patches pass up to `12/15`, with mean target-over-control advantage up to `0.881`; definition exceeds neutral mean advantage in every full-label cell; learned target direction passes `3/3` primary positives at all scales but also shows control leakage.
- Variance or ablation: source-passage and latent-choice frames both show full-label movement; neutral carrier and learned-direction controls expose remaining confounds.

Residual content:

- Explained by old regime: broad definition-derived transfer remains generic and label carriers can move behavior surfaces.
- New content outside old regime: the behavior-level negative result is surface-dependent; full-label continuation scoring exposes a behavior-visible effect.
- Retractions or supersessions: supersede "raw state replacement fails behavior-level gates" with "raw state replacement fails option-token gates but passes full-label behavior gates with neutral-carrier caveats."

Next move: replicate full-label behavior gates with stronger carrier/label controls and learn directions against the full-label objective.

## Activation Geometry Probe: Full-Label Carrier Controls

Question: does the full-label behavior effect survive stronger carrier controls?

Current regime:

- Artifact types: full-label behavior payloads, patch-text carrier regimes, target-vs-control specificity rows, definition-minus-control contrast summaries.
- Operations: hook-output state capture from different carrier texts, full-label continuation scoring, source/noop/distractor/random patch controls.
- Gates/verifiers: full definition should exceed label-only, neutral, blank-carrier, and shuffled-label controls; blank and shuffled controls should fail if the effect is concept/label-specific.
- Known limitations: one seed, one model, exact-label scoring, no alias target labels yet.

Action class:

- Retrieval/search/discovery: verifier refinement.
- Why: this run adds new carrier-control artifact classes that distinguish arbitrary carrier movement, wrong-label movement, label-only movement, and definition-context boost.

Experiment:

- Manifest/report paths: `experiments/activation_geometry/results/full_label_carrier_controls_2026_06_08.md`; local ignored payloads under `artifacts/activation_geometry/modal_pythia_70m_full_label_carrier_controls_*.json`.
- Positive targets: focus rows plus 8 sampled baseline pairs.
- Negative controls: `blank_carrier`, `shuffled_label`, distractor/random/source-noop patch modes.
- Stress tests: prompt frames `latent_choice` and `source_passage`; layers `5,6`; stripped-definition, neutral, and label-only carrier ablations.

Gate:

- Acceptance rule: accept strengthened full-label behavior claim if full definitions beat controls and shuffled/blank carriers fail.
- Withheld/rejected rule: withhold pure semantic transfer if stripped definitions or label-free carriers match the full definition effect.

Results:

- Accepted artifacts: carrier-control regimes in the full-label behavior gate; `experiments/activation_geometry/results/full_label_carrier_controls_2026_06_08.md`.
- Rejected or withheld artifacts: pure semantic-transfer claim remains withheld.
- Key metrics: full definitions pass `9/15` to `12/15`; label-only/neutral are active but weaker; blank carriers pass `0/15`; shuffled-label carriers pass at most `1/15` with negative mean advantage.
- Variance or ablation: source-passage and latent-choice frames agree on the ordering: `definition` > `neutral/label_only` > `blank_carrier/shuffled_label`.

Residual content:

- Explained by old regime: exact label strings can steer full-label behavior.
- New content outside old regime: full definitions add a target-specific boost beyond label-only carriers, while wrong labels actively suppress target-specificity.
- Retractions or supersessions: supersede "neutral carrier activity makes the full-label result uninterpretable" with "the effect is label-anchored and definition-context boosted."

Next move: replicate across seed/model and test alias labels to separate exact-string anchoring from conceptual behavior transfer.

## Activation Geometry Probe: Full-Label Alias Gate

Question: does canonical full-label behavior transfer survive non-identical alias scoring?

Current regime:

- Artifact types: alias-label manifests, full-label behavior payloads, canonical-vs-alias specificity rows, alias survivor pocket tables.
- Operations: hook-output state capture from canonical carriers, full-label continuation scoring over canonical and alias labels, target-vs-control specificity aggregation.
- Gates/verifiers: canonical definition patches should reproduce the carrier-control result; alias patches must beat distractor/random/source-noop controls to count as label-invariant concept transfer.
- Known limitations: one seed, one model, one alias per concept, aliases are hand-authored, no alias-trained behavior direction yet.

Action class:

- Retrieval/search/discovery: verifier refinement with a boundary result.
- Why: this run changes the scored lexical surface and tests whether behavior transfer is label-invariant.

Experiment:

- Manifest/report paths: `experiments/activation_geometry/results/full_label_alias_gate_2026_06_08.md`; local ignored payloads under `artifacts/activation_geometry/modal_pythia_70m_full_label_alias_*.json`.
- Positive targets: focus rows plus 8 sampled baseline pairs.
- Negative controls: alias scoring against distractor/random/source-noop patch modes, `blank_carrier`, `shuffled_label`, `neutral`, `label_only`.
- Stress tests: prompt frames `latent_choice` and `source_passage`; layers `5,6`; canonical vs alias scoring.

Gate:

- Acceptance rule: accept label-invariant behavior transfer only if alias-scored definition target patches pass robustly and have positive target-over-control advantage.
- Withheld/rejected rule: withhold concept-level behavior transfer if alias target movement is matched or exceeded by controls.

Results:

- Accepted artifacts: alias label manifest, alias scoring support in the behavior gate, `experiments/activation_geometry/results/full_label_alias_gate_2026_06_08.md`.
- Rejected or withheld artifacts: broad label-invariant behavior transfer claim remains withheld.
- Key metrics: canonical definitions pass `9/15` to `12/15` with mean advantage `0.622` to `0.881`; alias definitions pass only `4/15` to `6/15` and have negative mean advantage from `-0.094` to `-0.196`.
- Variance or ablation: both prompt frames agree: canonical effect replicates; alias specificity collapses globally; a few pair-specific alias pockets remain.

Residual content:

- Explained by old regime: exact canonical labels dominate the behavior-visible effect.
- New content outside old regime: alias scoring reveals weak, pair-specific synonym pockets that may mark either true concept transfer or alias-surface confounds.
- Retractions or supersessions: supersede "full-label behavior transfer may be concept-level" with "full-label behavior transfer is currently canonical-label anchored, with only local alias pockets."

Next move: run multiple-alias and alias-shuffle diagnostics, then try alias-trained behavior-aligned directions.

## Activation Geometry Probe: Alias-Trained Behavior Direction

Question: can alias-label behavior be made addressable by learning behavior-aligned directions directly against alias objectives?

Current regime:

- Artifact types: alias-label manifests, full-label gradient directions, canonical/alias eval rows, direction-control rows, leakage tables.
- Operations: train-variant full-label gradient averaging, held-out full-label continuation scoring, cross-label evaluation, source/distractor/random direction controls.
- Gates/verifiers: target-learned direction should beat source/distractor/random controls; alias-trained direction should improve alias labels and transfer to canonical labels; semantic claims require avoiding valence and control-layer leakage.
- Known limitations: one seed, one model, per-pair learned directions, no residualization, no second alias per concept yet.

Action class:

- Retrieval/search/discovery: intervention search with rejected mechanism claim.
- Why: this adds alias full-label gradients as an intervention class, but the resulting direction fails semantic-specificity controls.

Experiment:

- Manifest/report paths: `experiments/activation_geometry/results/alias_trained_behavior_direction_2026_06_08.md`; local ignored payloads under `artifacts/activation_geometry/modal_pythia_70m_alias_trained_direction*.json`.
- Positive targets: promoted steering pairs.
- Negative controls: source-learned, distractor-learned, random-same-norm directions; valence-control pairs; control layer.
- Stress tests: prompt frames `latent_choice` and `source_passage`; eval labels `alias` and `canonical`; scales `0.5,1.0,2.0`.

Gate:

- Acceptance rule: accept alias addressability if target-learned directions reliably improve alias target margins and beat source/distractor/random directions.
- Withheld/rejected rule: withhold semantic transport if valence controls or control-layer positives pass at comparable strength.

Results:

- Accepted artifacts: full-label alias objective support in the learned-direction runner; `experiments/activation_geometry/results/alias_trained_behavior_direction_2026_06_08.md`.
- Rejected or withheld artifacts: semantic transport claim remains withheld.
- Key metrics: target-learned directions pass `3/3` primary positives for both prompt frames, all scales, and both eval label regimes; source/distractor directions are negative on mean; target-learned valence controls pass `2/2` and control-layer positives pass `3/3`.
- Variance or ablation: source-passage and latent-choice frames agree; alias-trained directions also transfer to canonical scoring.

Residual content:

- Explained by old regime: direct behavior gradients can control label logits.
- New content outside old regime: alias-label behavior is addressable and cross-label transferable, but only through a leaky output-control direction.
- Retractions or supersessions: supersede "alias labels may be unreachable behaviorally" with "alias labels are behaviorally reachable, but raw transported states and direct gradients occupy different regimes."

Next move: build residualized alias directions that subtract source/distractor/control components, then rerun the alias gate against leakage controls.

## Activation Geometry Probe: Residualized Alias Direction

Question: can simple residualization make alias-trained behavior directions less leaky without losing positive concept movement?

Current regime:

- Artifact types: alias-label manifests, full-label gradient directions, residualized direction modes, canonical/alias eval rows, leakage tables.
- Operations: train-variant full-label gradient averaging, projection residualization, leave-one-out control-basis construction, held-out full-label continuation scoring.
- Gates/verifiers: positive pairs must pass in primary/backup layers; valence controls and control-layer positives must not pass at comparable strength; residual modes should improve target-over-control specificity.
- Known limitations: one seed, one model, one alias per concept, post-hoc linear residuals only.

Action class:

- Retrieval/search/discovery: search with a rejected simplification.
- Why: this adds residualized direction modes inside the existing behavior-direction schema and tests whether leakage is linearly removable.

Experiment:

- Manifest/report paths: `experiments/activation_geometry/results/residualized_alias_direction_2026_06_08.md`; local ignored payloads under `artifacts/activation_geometry/modal_pythia_70m_residualized_alias_direction_*.json`.
- Positive targets: promoted steering pairs.
- Negative controls: same-norm random directions; valence-control pairs; control layer.
- Stress tests: prompt frames `latent_choice` and `source_passage`; eval labels `alias` and `canonical`; scales `0.5,1.0,2.0`.

Gate:

- Acceptance rule: promote residualized semantic transport only if positive pairs remain robust while primary valence controls and control-layer positives fail or become much weaker than positives.
- Withheld/rejected rule: withhold semantic claims if controls still pass, even when their mean deltas are attenuated.

Results:

- Accepted artifacts: residualized direction modes in the learned-direction runner; `experiments/activation_geometry/results/residualized_alias_direction_2026_06_08.md`.
- Rejected or withheld artifacts: the simple linear-removal explanation is rejected; semantic transport remains withheld.
- Key metrics: `target_resid_all` keeps `3/3` primary positives in every frame/eval setting at scale `1.0`; it reduces valence-control means by `23.1%` to `49.4%`; controls still pass `2/2` except source-passage canonical, where they drop to `1/2`.
- Variance or ablation: source/distractor-only and control-only residuals are weaker than the combined residual; source-passage canonical is cleaner than alias scoring.

Residual content:

- Explained by old regime: behavior gradients can move target labels and random directions are much weaker.
- New content outside old regime: leakage has at least two distinguishable channels; `valence->activation_vector` can be suppressed in one setting, but `valence->steering_vector` remains adversarial.
- Retractions or supersessions: supersede "subtract a generic control component" with "post-hoc projection is only an attenuation method, not a specificity method."

Next move: replace post-hoc residualization with a constrained behavior objective that penalizes `valence->steering_vector` during direction construction.

## Activation Geometry Probe: Constrained Alias Direction

Question: can a named adversarial-control penalty make alias-trained behavior directions more specific without destroying positive concept movement?

Current regime:

- Artifact types: alias-label manifests, full-label gradient directions, constrained direction modes, canonical/alias eval rows, adversarial-control tables.
- Operations: train-variant full-label gradient averaging, norm-matched hard-control subtraction, held-out full-label continuation scoring, prompt-frame replication.
- Gates/verifiers: positives must remain robust; independent valence controls should be suppressed; construction-zeroed controls are sanity checks, not independent successes.
- Known limitations: one seed, one model, one manually chosen hard-control channel, one alias per concept.

Action class:

- Retrieval/search/discovery: search with a promising new operation.
- Why: this adds an adversarial-control direction-construction operation and produces a specificity frontier that post-hoc residualization did not expose.

Experiment:

- Manifest/report paths: `experiments/activation_geometry/results/constrained_alias_direction_2026_06_09.md`; local ignored payloads under `artifacts/activation_geometry/modal_pythia_70m_constrained_alias_direction_*.json`.
- Positive targets: promoted steering pairs.
- Negative controls: `valence->activation_vector`, `valence->steering_vector`, mean-control penalty, random same-norm controls, control layer.
- Stress tests: prompt frames `source_passage` and `latent_choice`; eval labels `alias` and `canonical`; scales `0.5,1.0,2.0`.

Gate:

- Acceptance rule: accept a constrained-direction improvement if positives remain `3/3` while independent valence-control means fall substantially below raw target-learned means.
- Withheld/rejected rule: withhold full semantic specificity if any independent valence control still passes or if suppression depends on construction-zeroing.

Results:

- Accepted artifacts: hard-control penalty direction modes; `experiments/activation_geometry/results/constrained_alias_direction_2026_06_09.md`.
- Rejected or withheld artifacts: full semantic specificity remains withheld; mean-control subtraction is rejected as insufficient.
- Key metrics: at scale `1.0`, `target_penalty_hard_1_0` keeps `3/3` positives in both prompt frames and both eval regimes; it reduces mean valence-control deltas by `69.0%` to `95.6%`; `valence->activation_vector` still passes.
- Variance or ablation: hard penalty `2.0` suppresses controls more strongly but damages canonical positives; mean-control penalty preserves positives but leaves controls passing.

Residual content:

- Explained by old regime: behavior gradients can move labels and simple projections attenuate leakage.
- New content outside old regime: a named adversarial-control penalty exposes a tunable specificity/strength frontier.
- Retractions or supersessions: supersede "post-hoc residualization is the best available cleanup" with "constrained direction construction is the more promising path."

Next move: build a multi-control constrained objective and evaluate it against held-out aliases/controls.

## Symbolic Weakness Benchmark: Prefix-Shift Pilot

Question: can weakness or invariance identify the OOD-generalizing rule when several train-perfect symbolic rules fit the data?

Current regime:

- Artifact types: symbolic tasks, candidate rules, selector metrics, OOD splits, markdown result reports, audit cards.
- Operations: cyclic task generation, candidate enumeration, translation-equivariance scoring, selector comparison, deterministic pilot runs.
- Gates/verifiers: unit tests, train-perfect selector check, OOD accuracy, invariant-selection rate, local-patch negative controls, publication guard.
- Known limitations: the admissible transformation group is supplied by the evaluator; neural learners and learned transformation discovery are not included yet.

Action class:

- Retrieval/search/discovery: search.
- Why: this creates a sharper benchmark inside the existing weakness-vs-simplicity program. It does not yet add a learned weakness verifier.

Experiment:

- Manifest/report paths: `experiments/symbolic_weakness/results/prefix_shift_pilot_2026_06_09.md`.
- Positive targets: weakness selector should choose the global cyclic shift and generalize OOD.
- Negative controls: train loss, simplicity, compression, flatness proxy, and random train-consistent selection.
- Stress tests: pending seed/modulus/train-window sweeps and wrong/noisy transformation-group controls.

Gate:

- Acceptance rule: all reported selectors train-perfect; weakness invariant rate and mean OOD accuracy at least `0.95`; train loss, simplicity, compression, and flatness proxy local-patch rate at least `0.95` and mean OOD accuracy at most `0.15`.
- Withheld/rejected rule: do not claim neural, learned-rule, learned-symmetry, or strong flatness-baseline evidence from this symbolic oracle pilot.

Results:

- Accepted artifacts: `experiments/symbolic_weakness/experiment.py`, `tests/test_symbolic_weakness.py`, and `experiments/symbolic_weakness/results/prefix_shift_pilot_2026_06_09.md`.
- Rejected or withheld artifacts: raw JSON under `artifacts/symbolic_weakness/`.
- Key metrics: weakness mean OOD accuracy `1.000`, invariant rate `1.000`; train loss, simplicity, compression, and flatness proxy mean OOD accuracy `0.000`, local-patch rate `1.000`; all selectors mean train accuracy `1.000`.
- Variance or ablation: 300 trials over moduli `{7, 11, 13}` with seed `11`; broader sweeps pending.

Residual content:

- Explained by old regime: weak compatible constraints can beat short local descriptions in synthetic settings.
- New content outside old regime: the paper target now has a concrete symbolic symmetry benchmark where weakness cleanly predicts OOD while loss, simplicity, compression, and a flatness proxy fail.
- Retractions or supersessions: the older Boolean-only weakness benchmark should be treated as preliminary; the flagship track should use symmetry and transformation compatibility as the central operationalization.

Next move: run symbolic sweeps, add non-cyclic task families, add wrong/noisy group controls, then train small neural models and measure latent equivariance as model-level weakness.

## Activation Geometry Probe: Multi-Control Alias Holdout

Question: does the constrained alias-direction frontier survive held-out alias and leave-one-out multi-control stress tests?

Current regime:

- Artifact types: alias-indexed label manifests, full-label gradient directions, constrained direction modes, held-out alias eval rows, leave-one-out control rows.
- Operations: alias-indexed label scoring, norm-matched multi-control subtraction, held-out full-label continuation scoring.
- Gates/verifiers: held-out alias positives must remain robust; independent controls must weaken relative to raw target directions; construction-zeroed controls do not count as independent evidence.
- Known limitations: Pythia-70M only, three positives, two valence controls, one held-out alias per concept.

Action class:

- Retrieval/search/discovery: verifier hardening with a rejected candidate.
- Why: this adds a held-out alias verifier and falsifies the current constrained frontier as a paper-level mechanism.

Experiment:

- Manifest/report paths: `experiments/activation_geometry/results/multicontrol_alias_holdout_2026_06_09.md`; local ignored payloads under `artifacts/activation_geometry/modal_pythia_70m_multicontrol_alias_holdout_*.json`.
- Positive targets: promoted steering pairs.
- Negative controls: valence controls with leave-one-out control bases; random same-norm controls.
- Stress tests: `source_passage` and `latent_choice`; eval labels `alias_0`, `alias_1`, and `canonical`; penalty weights `0.5`, `1.0`, `2.0`.

Gate:

- Acceptance rule: promote the constrained frontier only if held-out `alias_1` positives remain `3/3` while independent controls weaken.
- Withheld/rejected rule: withhold if any positive systematically fails under held-out alias or if controls still pass.

Results:

- Accepted artifacts: `alias_0`/`alias_1` regimes; multi-control penalty modes; `experiments/activation_geometry/results/multicontrol_alias_holdout_2026_06_09.md`.
- Rejected or withheld artifacts: current constrained alias direction remains non-paper-ready.
- Key metrics: raw target directions pass `3/3` held-out `alias_1` positives but controls pass `2/2`; constrained modes reduce controls but drop held-out positives to `2/3`, consistently failing `attractor->attractor_network`.
- Variance or ablation: both prompt frames agree on the held-out alias failure; canonical and `alias_0` remain easier than `alias_1`.

Residual content:

- Explained by old regime: exact-label and first-alias behavior surfaces are easier to control than label-invariant concept behavior.
- New content outside old regime: held-out alias scoring exposes an alias-specific weakness in the constrained frontier.
- Retractions or supersessions: supersede "hard-control penalty is close to paper-ready" with "hard-control penalty is a useful frontier but not alias-invariant."

Next move: jointly train over multiple aliases and broaden the concept/control set before scaling models.

## Weakness Predicts OOD: Multi-Family Symbolic + Neural

Question: does symmetry-compatible-hypothesis weakness predict OOD generalization (a) across symbolic task families that admit local shortcuts, and (b) across trained neural networks with diverse architecture and data-augmentation regimes?

Current regime:

- Artifact types: family registry, selector registry, multi-family benchmark JSON with Wilson 95% CIs, neural sweep JSON with per-model artefacts, correlation summaries, Modal entrypoints.
- Operations: synthetic candidate generation, with-action equivariance counting, leave-one-out validation, MDL-style compression scoring, Hutchinson sharpness probe, group inference from data, group corruption (wrong/noisy), unit tests.
- Gates/verifiers: pre-registered acceptance thresholds in `experiments/symbolic_weakness/results/*.md`; Wilson 95% CIs; `compileall`; `unittest`; publication guard.
- Known limitations: domains are finite and small (n ≤ 13); the parity family is a known negative case (|G|=2 too small to disambiguate); the S_n family is a known partial case (centralizer sizes coincide for many wrong involutions).

Action class:

- Retrieval/search/discovery: discovery + search. The benchmark *discovers* the operating regime in which weakness is and is not load-bearing.

Gate:

- Acceptance: `weakness_oracle` selects the invariant family in ≥95% of cyclic and dihedral trials (Wilson 95% CI lower bound ≥0.95); `weakness_wrong_group` selects the invariant in ≤5% of those trials; on the neural side, `weakness_oracle_norm` Pearson correlation with OOD accuracy exceeds 0.4 across ≥256 models with diverse augmentation/architecture/init/optimizer.
- Withheld: claims of universal weakness superiority, claims about non-symbolic domains (language/perception), claims about parity/S_n where the benchmark explicitly fails.

Results:

- Accepted artifacts: `experiments/symbolic_weakness/results/multi_family_500_2026_06_09.md`, `experiments/symbolic_weakness/results/neural_sweep_v3_2026_06_09.md`, `experiments/symbolic_weakness/results/modal_neural_sweep_v1_2026_06_09.md`, `papers/weakness_invariance_neurips/paper.md`.
- Key metrics: cyclic and dihedral weakness invariant-rate 1.000 with CI lower bound ≥0.992; classical baselines invariant-rate 0.000 with CI upper bound ≤0.008; neural weakness_oracle_norm Pearson with OOD = +0.817 (local 256-MLP sweep) / +0.813 (Modal 1024-MLP sweep), wrong-group control Pearson ≤ −0.116 across both runs.
- Variance or ablation: wrong-group, noisy-group, data-inferred-group, partial-cyclic-group, and random-label controls all show the expected directional behavior (wrong/random → null, noisy/inferred → mostly recover).

Residual content:

- Explained by current regime: simplicity, MDL, training loss, parameter norm, sharpness, and held-out validation are insufficient to disambiguate train-perfect shortcuts from globally invariant rules on the symbolic families where the candidate group is rich enough to separate them.
- New content outside current regime: parity and S_n require either a richer candidate transformation set or a fundamentally different selector — they delineate the operating boundary of weakness-as-symmetry-volume.
- Retractions: none.

Next move: add compositional task families (Z_n × Z_m); add a small-transformer variant; investigate whether learned-group inference can extend weakness to S_n where the oracle group is too coarse.

## Activation Geometry Probe: Multi-Alias Expanded Specificity

Question: does multi-alias objective training plus a larger pair set produce semantic-specific behavior directions?

Current regime:

- Artifact types: alias-indexed label manifests, grouped objective regimes, full-label gradient directions, expanded pair manifests, specificity reports.
- Operations: multi-alias gradient averaging, held-out alias scoring, norm-matched multi-control penalties, specificity-score comparison.
- Gates/verifiers: held-out alias positives must transfer and independent controls must remain lower than positives under the same score surface.
- Known limitations: one model, one seed, no generation scoring yet, expanded controls are hand-picked rather than random-relation nulls.

Action class:

- Retrieval/search/discovery: verifier hardening with a rejected candidate.
- Why: this creates a stronger gate and falsifies the current multi-alias behavior objective as a paper-ready specificity mechanism.

Experiment:

- Manifest/report paths: `experiments/activation_geometry/results/multialias_expanded_specificity_2026_06_09.md`; local ignored payloads under `artifacts/activation_geometry/modal_pythia_70m_multialias_expanded_*.json`.
- Positive targets: expanded steering pairs.
- Negative controls: expanded control pairs with leave-one-out control bases.
- Stress tests: `source_passage` and `latent_choice`; held-out `alias_2`; canonical labels; three scales.

Gate:

- Acceptance rule: pass if held-out `alias_2` positives remain high while controls are suppressed enough to make specificity clearly positive.
- Withheld/rejected rule: withhold if controls pass broadly or specificity is near zero/negative.

Results:

- Accepted artifacts: grouped objective regimes; third aliases; expanded pair set; result report.
- Rejected or withheld artifacts: multi-alias constrained behavior directions remain non-paper-ready.
- Key metrics: held-out `alias_2` target-learned reaches `6/7` positives in both prompt frames but controls pass `5/5`; specificity is `0.034` in `source_passage` and `0.002` in `latent_choice`.
- Variance or ablation: both prompt frames agree; constrained and residual modes do not improve specificity.

Residual content:

- Explained by old regime: behavior gradients can move many held-out target labels.
- New content outside old regime: the main obstacle is now identifiable as broad control leakage, not just single-alias fragility.
- Retractions or supersessions: supersede "multi-alias training may be enough" with "multi-alias training improves transfer but not specificity."

Next move: diagnose whether leakage is low-rank or pair-specific.

## Activation Geometry Probe: Direction Subspace Diagnostic

Question: is behavior-direction leakage low-rank or pair-specific?

Current regime:

- Artifact types: behavior target-gradient directions, pairwise cosine summaries, singular spectra, control-subspace capture tables.
- Operations: multi-alias target-gradient extraction, normalized direction SVD, control-subspace projection, pairwise cosine ranking.
- Gates/verifiers: low-rank leakage would show high control energy in one or two components and high positive capture by that control subspace; pair-specific leakage would show low average capture but high individual pair overlaps.
- Known limitations: one model, one layer, one seed; no random relation nulls yet.

Action class:

- Retrieval/search/discovery: mechanistic diagnostic.
- Why: this adds a direction-subspace artifact class that was missing from the previous score-only specificity gates.

Experiment:

- Manifest/report paths: `experiments/activation_geometry/results/direction_subspace_diagnostic_2026_06_09.md`; local ignored payloads under `artifacts/activation_geometry/modal_pythia_70m_direction_subspace_*.json`.
- Positive targets: expanded steering pairs.
- Negative controls: expanded control pairs.
- Stress tests: `source_passage` and `latent_choice`.

Gate:

- Acceptance rule: classify leakage as low-rank only if low-rank control components capture most positive direction energy on average.
- Withheld/rejected rule: withhold low-rank explanation if average positive capture stays low and high overlaps are pair-specific.

Results:

- Accepted artifacts: Modal subspace diagnostic and result report.
- Rejected or withheld artifacts: one-vector or simple low-rank shared leakage explanation.
- Key metrics: control effective rank `4.179`/`4.201`; rank-5 control subspace captures only `0.159`/`0.194` positive energy on average, but max pair capture reaches `0.581`/`0.676`.
- Variance or ablation: source and latent prompt frames agree.

Residual content:

- Explained by old regime: broad full-label gradients move many labels.
- New content outside old regime: leakage is localized in relation pockets, not captured by one shared control vector.
- Retractions or supersessions: supersede "subtract the control subspace" with "stratify controls and add target-disjoint random relation nulls."

Next move: add random relation nulls and target-disjoint controls.
