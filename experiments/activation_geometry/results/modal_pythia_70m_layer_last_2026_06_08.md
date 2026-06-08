# Modal Pythia Activation Geometry Probe - 2026-06-08

## Question

Do the concept-geometry bridges that survived embedding-space stress tests also appear in hidden-state geometry for an open language model?

This is the first activation-space probe. It uses an open 70M-parameter Pythia model, pools last-layer hidden states over the same 72 paraphrased concept prompts, and checks concept-centroid geometry before and after global mean-centering.

## Manifest

- Model: `EleutherAI/pythia-70m-deduped`
- Backend: Modal + Transformers
- Layer: `-1` / final hidden state
- Concept count: 24
- Prompt records: 72
- Activation dimension: 512
- Pooling: attention-mask mean over token hidden states
- Raw output: local-only `artifacts/activation_geometry/modal_pythia_70m_layer_last.json`
- Modal run: `https://modal.com/apps/generalintelligencecompany/main/ap-PhueNCGevlNRVWk7B762sw`
- Command:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_activation_probe.py --model-id EleutherAI/pythia-70m-deduped --layer -1 --batch-size 8 --max-length 96 --out artifacts/activation_geometry/modal_pythia_70m_layer_last.json
```

Python 3.12 is intentional for the local Modal CLI. Python 3.13 attempted to build `cbor2==6.1.2` from source and failed in this environment.

## Gate

Pre-registered acceptance rule for treating this as a useful first activation-space bridge result:

- Dry-run should behave like a noise/control path, with no strong bridge lift.
- Raw activations should be inspected for anisotropy rather than trusted directly.
- Mean-centered activations should show category separation of at least `0.05`.
- Mean-centered bridge-pair cosine should exceed the non-bridge cross-category mean by at least `0.05`.
- At least `0.75` of bridge pairs should exceed the non-bridge cross-category mean.

## Results

| Metric | Raw activations | Mean-centered activations |
| --- | ---: | ---: |
| Mean paraphrase cohesion | 0.9995 | 0.6995 |
| Minimum concept mean cohesion | 0.9993 | 0.5409 |
| Within-category centroid cosine | 0.9988 | 0.0780 |
| Across-category centroid cosine | 0.9987 | -0.0576 |
| Category separation | 0.0002 | 0.1356 |
| Mean top-3 same-category rate | 0.2639 | 0.3194 |
| Mean bridge cosine | 0.9988 | 0.1331 |
| Mean non-bridge cross-category cosine | 0.9987 | -0.0625 |
| Bridge lift | 0.0002 | 0.1957 |
| Bridge pairs above non-bridge mean | 0.5000 | 0.9167 |

Selected mean-centered bridge pairs:

| Bridge | Cosine |
| --- | ---: |
| `attractor` - `attractor_network` | 0.5360 |
| `validity_gate` - `weak_constraint` | 0.4263 |
| `autopoiesis` - `homeostasis` | 0.3433 |
| `conceptual_space` - `representation_manifold` | 0.2660 |
| `validity_gate` - `residual_content` | 0.1530 |
| `attractor_network` - `activation_vector` | 0.1008 |
| `embedding` - `steering_vector` | 0.0953 |
| `autopoiesis` - `self_boundary` | -0.0470 |
| `valence` - `activation_vector` | -0.0498 |
| `valence` - `steering_vector` | -0.2577 |

## Interpretation

The raw last-layer activation space is dominated by a common direction: nearly every concept centroid has cosine around `0.999` with every other centroid. Raw cosine geometry is therefore not trustworthy here.

After global mean-centering, the bridge-pair signal becomes visible. Mean-centered bridge lift is `0.1957`, and `11/12` bridge pairs beat the non-bridge cross-category mean. The result clears the first activation-space gate and is a real step beyond embedding-only evidence.

This is not yet a causal or steering result. It says that a small open LM's final hidden states contain a mean-centered geometry where many hypothesized bridge pairs are closer than unrelated cross-category pairs. The valence-to-activation/steering bridges are weak or negative in this run, which should be treated as a useful partial failure rather than hidden under the average.

## Discovery-Regime Audit

Question: does the embedding-space bridge geometry appear in open-model hidden states?

Current regime:

- Artifact types: paraphrased concept prompts, pooled hidden-state vectors, raw and mean-centered concept centroids, bridge-pair scores, activation-space audit cards.
- Operations: Modal-backed open-model extraction, attention-mean pooling, global mean-centering, cosine-kernel summary, bridge-lift comparison.
- Gates/verifiers: deterministic dry-run control, anisotropy inspection, category separation threshold, bridge-lift threshold, bridge-pair rate threshold, publication guard.
- Known limitations: one small model, one layer, one pooling rule, hand-authored bridge pairs, no causal intervention yet.

Action class:

- Retrieval/search/discovery: discovery-leaning search.
- Why: the run adds activation-space vectors as a new artifact class for this project, but the result is still a first probe rather than a stable mechanism.

Experiment:

- Manifest/report paths: this report; local-only `artifacts/activation_geometry/modal_pythia_70m_layer_last.json`.
- Positive targets: attractor/attractor-network, conceptual-space/representation-manifold, autopoiesis/homeostasis, validity-gate/weak-constraint, embedding/steering-vector.
- Negative controls: deterministic dry-run and raw anisotropy inspection.
- Stress tests: mean-centering against raw activation collapse; no layer or model sweep yet.

Gate:

- Acceptance rule: mean-centered category separation at least `0.05`, bridge lift at least `0.05`, and at least `0.75` of bridge pairs above the non-bridge cross-category mean.
- Withheld/rejected rule: raw activation JSON stays untracked under `artifacts/`.

Results:

- Accepted artifacts: this report, `activation_geometry_probe.py`, `modal_activation_probe.py`.
- Rejected or withheld artifacts: raw activation payload under `artifacts/activation_geometry/`.
- Key metrics: mean-centered category separation `0.1356`; bridge lift `0.1957`; bridge-pair above-baseline rate `0.9167`.
- Variance or ablation: raw-vs-centered comparison and deterministic dry-run only.

Residual content:

- Explained by old regime: language-level concept similarity may still drive the bridge geometry.
- New content outside old regime: bridge structure appears in open-model hidden states after removing the dominant common activation direction.
- Retractions or supersessions: raw activation cosine should not be used as evidence without centering or another anisotropy correction.

Next move: run a layer sweep and a second open model, then test whether selected bridge directions can steer generation or classification behavior.
