# Modal GPT-2 Activation Layer Sweep - 2026-06-08

## Question

Does the Pythia-70M activation bridge profile transport to a second open language model?

This run repeats the same activation-geometry layer sweep on `gpt2` with the same 72 paraphrased concept prompts and the same attention-mask mean pooling. Layer `0` is the embedding hidden state; layers `1` through `12` are transformer block outputs.

## Manifest

- Model: `gpt2`
- Backend: Modal + Transformers
- Layers: `0,1,2,3,4,5,6,7,8,9,10,11,12`
- Concept count: 24
- Prompt records: 72
- Activation dimension: 768 for every layer
- Pooling: attention-mask mean over token hidden states
- Raw output: local-only `artifacts/activation_geometry/modal_gpt2_layer_sweep.json`
- Modal run: `https://modal.com/apps/generalintelligencecompany/main/ap-f4NhDsSzXvFQr4R3HKfPm0`
- Command:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_layer_sweep.py --model-id gpt2 --layers 0,1,2,3,4,5,6,7,8,9,10,11,12 --batch-size 8 --max-length 96 --out artifacts/activation_geometry/modal_gpt2_layer_sweep.json
```

## Gate

The second-model replication is accepted if at least two block-output layers clear the same centered activation gate used for Pythia:

- Mean-centered category separation at least `0.05`.
- Mean-centered bridge lift at least `0.05`.
- At least `0.75` of bridge pairs above the non-bridge cross-category mean.

Raw activations are reported for anisotropy inspection, not used as the main acceptance criterion.

## Results

| Layer | Raw category separation | Raw bridge lift | Raw bridge rate | Centered category separation | Centered bridge lift | Centered bridge rate | Centered top-3 category rate | Centered paraphrase cohesion |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 0.0030 | 0.0030 | 0.9167 | 0.1660 | 0.1780 | 0.9167 | 0.4306 | 0.4492 |
| 1 | 0.0034 | 0.0041 | 1.0000 | 0.1767 | 0.2348 | 1.0000 | 0.4306 | 0.4894 |
| 2 | 0.0022 | 0.0028 | 0.8333 | 0.1273 | 0.1850 | 0.7500 | 0.3194 | 0.4439 |
| 3 | 0.0004 | 0.0003 | 0.8333 | 0.0427 | 0.0901 | 0.5000 | 0.2083 | 0.3210 |
| 4 | 0.0005 | 0.0004 | 0.8333 | 0.0528 | 0.0974 | 0.5000 | 0.2222 | 0.3228 |
| 5 | 0.0005 | 0.0004 | 0.8333 | 0.0624 | 0.0937 | 0.5000 | 0.2222 | 0.3339 |
| 6 | 0.0006 | 0.0005 | 0.7500 | 0.0710 | 0.0968 | 0.5000 | 0.2500 | 0.3359 |
| 7 | 0.0008 | 0.0006 | 0.7500 | 0.0873 | 0.1004 | 0.5000 | 0.2361 | 0.3477 |
| 8 | 0.0010 | 0.0009 | 0.7500 | 0.1107 | 0.1140 | 0.5000 | 0.2639 | 0.3649 |
| 9 | 0.0013 | 0.0013 | 0.7500 | 0.1315 | 0.1313 | 0.5000 | 0.2917 | 0.3863 |
| 10 | 0.0020 | 0.0019 | 0.7500 | 0.1623 | 0.1392 | 0.6667 | 0.3056 | 0.4203 |
| 11 | 0.0023 | 0.0016 | 0.7500 | 0.1894 | 0.1422 | 0.7500 | 0.3472 | 0.4543 |
| 12 | 0.0003 | 0.0002 | 0.5833 | 0.1502 | 0.1713 | 0.6667 | 0.2222 | 0.5252 |

Top layers by mean-centered bridge lift:

| Rank | Layer | Centered bridge lift | Centered category separation | Centered bridge rate |
| --- | ---: | ---: | ---: | ---: |
| 1 | 1 | 0.2348 | 0.1767 | 1.0000 |
| 2 | 2 | 0.1850 | 0.1273 | 0.7500 |
| 3 | 0 | 0.1780 | 0.1660 | 0.9167 |

## Interpretation

The second-model replication clears the gate. Three GPT-2 block outputs pass: layers `1`, `2`, and `11`. The embedding hidden state at layer `0` also passes, but it should remain analytically separate from block-output evidence.

The strongest GPT-2 signal appears in layer `1`, with centered bridge lift `0.2348`, centered category separation `0.1767`, and all bridge pairs above the non-bridge cross-category mean. This partially transports the Pythia result: both models show strong early block-output bridge geometry and weak middle-layer bridge-pair rates.

The exact Pythia profile does not fully transport. Pythia's final block output passed strongly, while GPT-2's final layer `12` has high centered bridge lift but fails the bridge-rate gate at `0.6667`. GPT-2 layer `11` passes instead. This suggests the robust claim should be narrower: centered bridge geometry is portable across two open causal LMs, but the layer profile is model-dependent.

Raw GPT-2 cosine geometry is not useful as primary evidence. Across all layers, raw category separation and raw bridge lift are tiny, while raw paraphrase cohesion is near `1.0`. Mean-centering remains necessary before interpreting activation-space neighborhoods.

## Cross-Model Takeaway

Common across Pythia-70M and GPT-2:

- Early block outputs pass the centered bridge gate.
- Middle layers have positive centered bridge lift but weak bridge-pair rates.
- Raw cosine geometry is dominated by common activation directions.

Different across models:

- Pythia's strongest block-output layer is `2`; GPT-2's is `1`.
- Pythia's final block output passes; GPT-2's final output fails the bridge-rate gate, while its penultimate output passes.
- GPT-2 raw layer `0` is far more anisotropic than Pythia raw layer `0`.

## Discovery-Regime Audit

Question: does activation-space bridge geometry replicate in a second open model?

Current regime:

- Artifact types: paraphrased concept prompts, pooled hidden-state vectors, model-indexed and layer-indexed raw and centered geometry summaries, bridge-lift reports, audit cards.
- Operations: Modal-backed open-model extraction, multi-layer hidden-state pooling, global mean-centering, cosine-kernel summary, bridge-lift comparison.
- Gates/verifiers: model replication, layerwise centered category separation, bridge lift, bridge-pair rate, raw anisotropy inspection, publication guard.
- Known limitations: same prompt set, same mean-pooling rule, hand-authored bridge pairs, no causal intervention.

Action class:

- Retrieval/search/discovery: search.
- Why: this tests transport across a second model inside the current activation-geometry artifact schema.

Experiment:

- Manifest/report paths: this report; local-only `artifacts/activation_geometry/modal_gpt2_layer_sweep.json`.
- Positive targets: model-level replication of centered bridge geometry and early-layer persistence.
- Negative controls: raw activation inspection and explicit reporting of failed layers.
- Stress tests: 13 GPT-2 hidden-state layers, rather than a single final layer.

Gate:

- Acceptance rule: at least two block-output layers must have centered category separation at least `0.05`, centered bridge lift at least `0.05`, and bridge-pair above-baseline rate at least `0.75`.
- Withheld/rejected rule: raw activation JSON stays untracked under `artifacts/`; layers that fail the gate remain in the public report.

Results:

- Accepted artifacts: this report.
- Rejected or withheld artifacts: local-only `artifacts/activation_geometry/modal_gpt2_layer_sweep.json`.
- Key metrics: layer `1` centered bridge lift `0.2348`; layer `1` centered category separation `0.1767`; layer `1` centered bridge-pair rate `1.0000`. Layers `1`, `2`, and `11` clear the block-output gate.
- Variance or ablation: middle layers `3..10` fail the bridge-rate criterion except layer `11`; final layer `12` fails the bridge-rate criterion.

Residual content:

- Explained by old regime: early layers may still reflect lexical and phrase-level semantic geometry rather than active attractor dynamics.
- New content outside old regime: centered bridge geometry replicates across a second open model, but the exact layer profile is not invariant.
- Retractions or supersessions: the Pythia final-layer pass should not be generalized to final layers across models.

Next move: run a pooling ablation, comparing mean pooling against final-token pooling for Pythia and GPT-2 before steering or causal claims.
