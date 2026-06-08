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
