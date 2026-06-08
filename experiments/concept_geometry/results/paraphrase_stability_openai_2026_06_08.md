# OpenAI Paraphrase Stability Probe - 2026-06-08

## Question

Does the concept-geometry signal survive wording perturbations and a second embedding model?

This stress test asks whether the previous bridge neighborhoods are only artifacts of one exact prompt wording, or whether concept centroids built from paraphrases preserve similar geometry across `text-embedding-3-small` and `text-embedding-3-large`.

## Manifest

- Concept source: `experiments/concept_geometry/concept_set.json`
- Paraphrase source: `experiments/concept_geometry/concept_paraphrases.json`
- Models: `text-embedding-3-small`, `text-embedding-3-large`
- Concept count: 24
- Paraphrase variants: 72
- Neighbor cutoff: top 3
- Raw output: local-only `artifacts/concept_geometry/paraphrase_stability_openai.json`
- Command:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- python3 experiments/concept_geometry/paraphrase_stability_probe.py --concepts experiments/concept_geometry/concept_set.json --paraphrases experiments/concept_geometry/concept_paraphrases.json --models text-embedding-3-small text-embedding-3-large --out artifacts/concept_geometry/paraphrase_stability_openai.json
```

## Gate

Pre-registered acceptance rule for treating the bridge signal as stable enough to justify activation-space follow-up:

- Mean paraphrase cohesion should be at least `0.70` for each model.
- Minimum concept-level paraphrase cohesion should be at least `0.60` for each model.
- Centroid category separation should be at least `0.10` for each model.
- Mean top-3 same-category rate should be at least `0.40` for each model.
- Cross-model pairwise-kernel Pearson correlation should be at least `0.80`.
- Cross-model mean top-3 neighbor overlap should be at least `0.50`.

## Results

| Metric | `text-embedding-3-small` | `text-embedding-3-large` |
| --- | ---: | ---: |
| Mean paraphrase cohesion | 0.7685 | 0.7835 |
| Minimum concept mean cohesion | 0.6789 | 0.6809 |
| Minimum variant-pair cohesion | 0.5803 | 0.5775 |
| Within-category centroid cosine | 0.4903 | 0.4614 |
| Across-category centroid cosine | 0.3241 | 0.3055 |
| Centroid category separation | 0.1661 | 0.1559 |
| Mean top-3 same-category rate | 0.5556 | 0.5556 |
| Mean bridge-pair cosine | 0.5131 | 0.4823 |

Cross-model agreement:

| Metric | Value |
| --- | ---: |
| Pairwise centroid-kernel Pearson | 0.8884 |
| Mean top-3 neighbor overlap | 0.7292 |

Selected bridge pairs:

| Bridge | Small | Large | Delta |
| --- | ---: | ---: | ---: |
| `attractor` - `attractor_network` | 0.7388 | 0.7475 | 0.0087 |
| `attractor_network` - `activation_vector` | 0.5345 | 0.5767 | 0.0422 |
| `conceptual_space` - `representation_manifold` | 0.5639 | 0.5481 | 0.0158 |
| `embedding` - `activation_vector` | 0.6240 | 0.4282 | 0.1958 |
| `embedding` - `steering_vector` | 0.5328 | 0.4413 | 0.0915 |
| `autopoiesis` - `self_boundary` | 0.5031 | 0.5523 | 0.0492 |
| `autopoiesis` - `homeostasis` | 0.5085 | 0.6171 | 0.1087 |
| `validity_gate` - `weak_constraint` | 0.5247 | 0.3965 | 0.1282 |
| `validity_gate` - `residual_content` | 0.3414 | 0.3459 | 0.0045 |
| `valence` - `activation_vector` | 0.4615 | 0.4101 | 0.0514 |
| `valence` - `steering_vector` | 0.3967 | 0.3643 | 0.0324 |
| `valence` - `attractor` | 0.4273 | 0.3601 | 0.0672 |

## Interpretation

The bridge signal survived the paraphrase and second-model stress test. The strongest result is not any single bridge, but the fact that paraphrase centroids preserve a similar pairwise geometry across two embedding models: kernel correlation `0.8884` and top-3 neighbor overlap `0.7292`.

This still remains language-space evidence. It says the vocabulary converges in embedding geometry robustly enough to prioritize follow-up, not that the underlying systems share the same causal dynamics.

The weakest retained bridge was `validity_gate` - `residual_content`, around `0.34` in both models. That is stable but not especially strong, so it should be treated as a tentative research-process analogy rather than a central mechanistic bridge.

## Discovery-Regime Audit

Question: Does the initial concept-neighborhood signal survive prompt perturbation and model substitution?

Current regime:

- Artifact types: concepts, paraphrase variants, embedding vectors, concept centroids, cosine kernels, bridge-pair scores, model-comparison summaries.
- Operations: paraphrase expansion, embedding, centroid construction, category summary, bridge scoring, cross-model kernel comparison.
- Gates/verifiers: paraphrase cohesion, centroid category separation, top-k category rate, cross-model kernel correlation, cross-model neighbor overlap, publication guard.
- Known limitations: all evidence remains inside language embedding models; paraphrases are hand-authored; bridge pairs are selected from the current hypothesis.

Action class:

- Retrieval/search/discovery: search.
- Why: this stress-tests an existing bridge hypothesis inside the concept-geometry schema. It does not yet add an activation-space verifier or a causal intervention.

Experiment:

- Manifest/report paths: this report; local-only `artifacts/concept_geometry/paraphrase_stability_openai.json`.
- Positive targets: bridge pairs involving attractors, activation vectors, conceptual spaces, representation manifolds, self-boundaries, homeostasis, valence, and validity gates.
- Negative controls: deterministic dry-run verifies the pipeline but does not serve as a semantic control.
- Stress tests: paraphrase perturbation and second embedding model.

Gate:

- Acceptance rule: all numeric thresholds listed above clear for both models and the cross-model comparison.
- Withheld/rejected rule: raw embeddings and full model output stay untracked under `artifacts/`.

Results:

- Accepted artifacts: this report, `concept_paraphrases.json`, `paraphrase_stability_probe.py`.
- Rejected or withheld artifacts: raw embedding payloads in `artifacts/`.
- Key metrics: small-model category separation `0.1661`; large-model category separation `0.1559`; cross-model kernel Pearson `0.8884`; neighbor overlap `0.7292`.
- Variance or ablation: two embedding models and 72 paraphrase variants; no external model family yet.

Residual content:

- Explained by old regime: language-level semantic relatedness still explains much of the result.
- New content outside old regime: paraphrase-invariant and model-stable bridge geometry is strong enough to motivate activation-space probes.
- Retractions or supersessions: the first single-prompt probe is superseded by centroid-based paraphrase summaries for embedding-space claims.

Next move: test whether these bridge directions appear in open-model activation spaces, ideally with Modal-backed extraction and steering/vector probes.
