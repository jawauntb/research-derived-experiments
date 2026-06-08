# OpenAI Concept Geometry Probe - 2026-06-08

## Question

Does a general-purpose text embedding model place cross-field geometric vocabulary into meaningful neighborhoods, especially around attractors, conceptual spaces, activation geometry, constraints, and self-boundary terms?

This is a weak bridge probe. It can show whether language-trained geometry already links the vocabularies, but it cannot by itself show that the underlying systems share dynamics, mechanisms, or intervention structure.

## Manifest

- Concept source: `experiments/concept_geometry/concept_set.json`
- Model: `text-embedding-3-small`
- Concept count: 24
- Category count: 7
- Neighbor cutoff: top 3
- Raw output: local-only `artifacts/concept_geometry/openai_embedding_probe.json`
- Command:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- python3 experiments/concept_geometry/openai_embedding_probe.py --concepts experiments/concept_geometry/concept_set.json --out artifacts/concept_geometry/openai_embedding_probe.json
```

## Gate

Pre-registered acceptance rule for treating this as a useful first bridge probe:

- Within-category mean cosine should exceed across-category mean cosine by at least `0.10`.
- Mean top-3 same-category neighbor rate should be at least `0.40`.
- Qualitative bridge neighborhoods should appear among the core convergence terms rather than only inside one category.

## Results

| Metric | Value |
| --- | ---: |
| Within-category mean cosine | 0.4513 |
| Across-category mean cosine | 0.2781 |
| Category separation | 0.1732 |
| Mean top-3 same-category rate | 0.5417 |

The run cleared the numeric gate. The qualitative neighborhoods also show useful bridges:

| Anchor | Nearest neighbors |
| --- | --- |
| `attractor` | `basin_of_attraction` 0.6970; `attractor_network` 0.6588; `fixed_point` 0.5737 |
| `attractor_network` | `attractor` 0.6588; `basin_of_attraction` 0.5570; `activation_vector` 0.4645 |
| `conceptual_space` | `semantic_distance` 0.6435; `representation_manifold` 0.5234; `schema` 0.4476 |
| `embedding` | `activation_vector` 0.5528; `representation_manifold` 0.5457; `steering_vector` 0.5017 |
| `autopoiesis` | `self_boundary` 0.4957; `homeostasis` 0.4231; `fixed_point` 0.3532 |
| `validity_gate` | `weak_constraint` 0.4528; `simplicity_bias` 0.3490; `residual_content` 0.3078 |
| `valence` | `activation_vector` 0.4428; `steering_vector` 0.4174; `attractor` 0.3899 |

## Discovery-Regime Audit

Question: Can embedding-space neighborhoods make the proposed cross-field convergence concrete enough to guide the next experiments?

Current regime:

- Artifact types: curated concept prompts, embedding vectors, cosine kernels, category labels, nearest-neighbor summaries, audit cards.
- Operations: OpenAI embedding call, cosine kernel construction, within/across category comparison, top-k neighbor inspection.
- Gates/verifiers: numeric separation threshold, same-category neighbor threshold, qualitative cross-category bridge inspection, public-safe publication guard.
- Known limitations: the category set is hand-curated, the prompts define the terms for the model, and the model was trained on language that already contains these analogies.

Action class:

- Retrieval/search/discovery: search.
- Why: the run explores a new model-backed artifact inside the existing concept-geometry schema, but does not add a new verifier or mechanism yet.

Experiment:

- Manifest/report paths: this report; local-only `artifacts/concept_geometry/openai_embedding_probe.json`.
- Positive targets: attractor/attractor-network, conceptual-space/representation-manifold, activation/steering-vector, self-boundary/autopoiesis/homeostasis.
- Negative controls: deterministic dry-run path exists for tooling checks, but not a semantic negative control.
- Stress tests: none in this run.

Gate:

- Acceptance rule: category separation at least `0.10`, top-3 same-category rate at least `0.40`, and visible cross-category bridge neighborhoods.
- Withheld/rejected rule: raw embedding JSON and any secret-bearing runtime context stay untracked.

Results:

- Accepted artifacts: this public result report and the experiment script.
- Rejected or withheld artifacts: raw embeddings under `artifacts/`.
- Key metrics: category separation `0.1732`; mean top-3 same-category rate `0.5417`.
- Variance or ablation: none yet.

Residual content:

- Explained by old regime: language-level semantic relatedness can explain part of the clustering.
- New content outside old regime: a few bridge neighborhoods are strong enough to prioritize as mechanistic follow-ups, especially attractor/attractor-network/activation-vector and conceptual-space/representation-manifold.
- Retractions or supersessions: do not treat this as evidence of shared dynamical structure.

Next move: replicate with paraphrase perturbations and a second embedding model, then compare language-space bridges against activation-space probes in open models.
