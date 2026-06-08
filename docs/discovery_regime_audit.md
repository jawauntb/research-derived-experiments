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
