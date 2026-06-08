# Modal Pythia Activation Layer Sweep - 2026-06-08

## Question

Does the activation-space bridge signal from the final-layer Pythia probe survive across layers, or was it a single-layer artifact?

This sweep extracts pooled hidden states from `EleutherAI/pythia-70m-deduped` for the same 72 paraphrased concept prompts. Layer `0` is the embedding hidden state; layers `1` through `6` are transformer block outputs.

## Manifest

- Model: `EleutherAI/pythia-70m-deduped`
- Backend: Modal + Transformers
- Layers: `0,1,2,3,4,5,6`
- Concept count: 24
- Prompt records: 72
- Activation dimension: 512 for every layer
- Pooling: attention-mask mean over token hidden states
- Raw output: local-only `artifacts/activation_geometry/modal_pythia_70m_layer_sweep.json`
- Modal run: `https://modal.com/apps/generalintelligencecompany/main/ap-oMTDzR6vr9oiYhUUcda1xd`
- Command:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_layer_sweep.py --model-id EleutherAI/pythia-70m-deduped --layers 0,1,2,3,4,5,6 --batch-size 8 --max-length 96 --out artifacts/activation_geometry/modal_pythia_70m_layer_sweep.json
```

## Gate

The sweep is accepted as useful layerwise evidence if at least two block-output layers clear the final-layer activation gate:

- Mean-centered category separation at least `0.05`.
- Mean-centered bridge lift at least `0.05`.
- At least `0.75` of bridge pairs above the non-bridge cross-category mean.

Raw activations are reported for anisotropy inspection, not used as the main acceptance criterion.

## Results

| Layer | Raw category separation | Raw bridge lift | Raw bridge rate | Centered category separation | Centered bridge lift | Centered bridge rate | Centered top-3 category rate | Centered paraphrase cohesion |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 0.0652 | 0.0905 | 1.0000 | 0.1636 | 0.2098 | 1.0000 | 0.4583 | 0.4001 |
| 1 | 0.0146 | 0.0227 | 0.9167 | 0.1522 | 0.2051 | 0.9167 | 0.3611 | 0.5681 |
| 2 | 0.0165 | 0.0178 | 0.7500 | 0.1857 | 0.2248 | 0.9167 | 0.4861 | 0.5653 |
| 3 | 0.0081 | -0.0006 | 0.5000 | 0.0427 | 0.0790 | 0.5833 | 0.1806 | 0.7182 |
| 4 | 0.0039 | 0.0025 | 0.5000 | 0.0007 | 0.0985 | 0.5833 | 0.1667 | 0.7419 |
| 5 | 0.0102 | 0.0075 | 0.5833 | 0.1009 | 0.1494 | 0.7500 | 0.2361 | 0.7255 |
| 6 | 0.0002 | 0.0002 | 0.5000 | 0.1356 | 0.1957 | 0.9167 | 0.3194 | 0.6995 |

Top layers by mean-centered bridge lift:

| Rank | Layer | Centered bridge lift | Centered category separation | Centered bridge rate |
| --- | ---: | ---: | ---: | ---: |
| 1 | 2 | 0.2248 | 0.1857 | 0.9167 |
| 2 | 0 | 0.2098 | 0.1636 | 1.0000 |
| 3 | 1 | 0.2051 | 0.1522 | 0.9167 |

## Interpretation

The layer sweep clears the gate. Four transformer block outputs pass the centered activation criterion: layers `1`, `2`, `5`, and `6`. Layer `0` also passes, but it is the embedding hidden state rather than a block output.

The strongest block-output signal appears at layer `2`, not the final layer. This suggests the bridge geometry is not merely a last-layer decoding artifact. It also is not uniformly present: layers `3` and `4` fail because their centered bridge-pair rates drop to `0.5833`, and layer `4` has almost no centered category separation despite positive bridge lift.

Raw activation geometry continues to show anisotropy risk. Later raw layers have tiny category separation and bridge lift, while the centered metrics recover signal. Layer `0` is the exception: raw embedding-state geometry already has meaningful category separation and bridge lift, which is plausible because it is closer to token/lexical geometry than to deep residual stream geometry.

This result upgrades the activation-space claim from "one final layer contains centered bridge geometry" to "the signal is layer-dependent and survives several block outputs, with the strongest evidence in early block outputs." The failure in layers `3-4` is useful residual content for the next experiment: we need to test whether this is a Pythia-70M-specific representational phase, an artifact of mean pooling, or a prompt-set effect.

## Discovery-Regime Audit

Question: does activation-space bridge geometry survive a layer sweep?

Current regime:

- Artifact types: paraphrased concept prompts, pooled hidden-state vectors, layer-indexed raw and centered geometry summaries, bridge-lift reports, audit cards.
- Operations: Modal-backed open-model extraction, multi-layer hidden-state pooling, global mean-centering, cosine-kernel summary, bridge-lift comparison.
- Gates/verifiers: layerwise centered category separation, bridge lift, bridge-pair rate, raw anisotropy inspection, publication guard.
- Known limitations: one small model, one pooling rule, hand-authored bridge pairs, no causal intervention.

Action class:

- Retrieval/search/discovery: search.
- Why: this extends the activation-space artifact across layers inside the current schema; it does not yet add a new verifier or causal operation.

Experiment:

- Manifest/report paths: this report; local-only `artifacts/activation_geometry/modal_pythia_70m_layer_sweep.json`.
- Positive targets: layerwise persistence of centered bridge lift and category separation.
- Negative controls: raw activation inspection and explicit reporting of failed layers.
- Stress tests: all hidden-state layers available for Pythia-70M, rather than only the final layer.

Gate:

- Acceptance rule: at least two block-output layers must have centered category separation at least `0.05`, centered bridge lift at least `0.05`, and bridge-pair above-baseline rate at least `0.75`.
- Withheld/rejected rule: raw activation JSON stays untracked under `artifacts/`; layers that fail the gate remain in the public report.

Results:

- Accepted artifacts: this report; `modal_layer_sweep.py`; layer-sweep payload helpers in `activation_geometry_probe.py`.
- Rejected or withheld artifacts: raw activation payload under `artifacts/activation_geometry/`.
- Key metrics: layer `2` centered bridge lift `0.2248`; layer `2` centered category separation `0.1857`; layer `2` centered bridge-pair rate `0.9167`.
- Variance or ablation: layer `3` and layer `4` fail the gate; layer `6` reproduces the previous final-layer result.

Residual content:

- Explained by old regime: language-level semantic similarity and embedding geometry may explain layer `0`.
- New content outside old regime: centered bridge geometry survives multiple transformer block outputs but weakens sharply in the middle layers.
- Retractions or supersessions: the final-layer result should be treated as one point in a layer-dependent profile, not as the canonical activation geometry of the model.

Next move: replicate the layer sweep on a second open model, then convert the strongest layer-2 bridge pairs into steering or classification interventions.
