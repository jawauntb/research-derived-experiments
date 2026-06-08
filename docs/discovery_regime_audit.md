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
