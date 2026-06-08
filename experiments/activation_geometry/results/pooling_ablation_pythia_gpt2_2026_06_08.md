# Activation Pooling Ablation: Pythia-70M and GPT-2 - 2026-06-08

## Question

Does the activation-space bridge signal survive a pooling perturbation, or is the layer profile mostly an artifact of attention-mask mean pooling?

This ablation compares the already-published mean-pooling layer sweeps against new final-token pooling sweeps for `EleutherAI/pythia-70m-deduped` and `gpt2`. Final-token pooling uses the last non-padding token in each prompt.

## Manifest

- Models: `EleutherAI/pythia-70m-deduped`, `gpt2`
- Backend: Modal + Transformers
- Pythia layers: `0,1,2,3,4,5,6`
- GPT-2 layers: `0,1,2,3,4,5,6,7,8,9,10,11,12`
- Concept count: 24
- Prompt records: 72
- Mean-pooling baselines:
  - `experiments/activation_geometry/results/modal_pythia_70m_layer_sweep_2026_06_08.md`
  - `experiments/activation_geometry/results/modal_gpt2_layer_sweep_2026_06_08.md`
- Final-token raw outputs:
  - local-only `artifacts/activation_geometry/modal_pythia_70m_layer_sweep_final_token.json`
  - local-only `artifacts/activation_geometry/modal_gpt2_layer_sweep_final_token.json`
- Successful final-token Modal runs:
  - Pythia: `https://modal.com/apps/generalintelligencecompany/main/ap-QNhVI4nEDvpQuwhTuGkFfx`
  - GPT-2: `https://modal.com/apps/generalintelligencecompany/main/ap-zaCOPxjw9LALbpTi0PxGqq`

Commands:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_layer_sweep.py --model-id EleutherAI/pythia-70m-deduped --layers 0,1,2,3,4,5,6 --batch-size 8 --max-length 96 --pooling final-token --out artifacts/activation_geometry/modal_pythia_70m_layer_sweep_final_token.json
```

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_layer_sweep.py --model-id gpt2 --layers 0,1,2,3,4,5,6,7,8,9,10,11,12 --batch-size 8 --max-length 96 --pooling final-token --out artifacts/activation_geometry/modal_gpt2_layer_sweep_final_token.json
```

## Gate

The pooling ablation is accepted as evidence of pooling robustness if each model has at least two transformer block-output layers that clear the same centered activation gate under final-token pooling:

- Mean-centered category separation at least `0.05`.
- Mean-centered bridge lift at least `0.05`.
- At least `0.75` of bridge pairs above the non-bridge cross-category mean.

Layer `0` is reported but does not count toward the block-output gate.

## Summary

| Model | Pooling | Passing block layers | Strongest passing layer | Strongest centered bridge lift | Strongest centered category separation | Strongest centered bridge rate |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| Pythia-70M | Mean | `1,2,5,6` | 2 | 0.2248 | 0.1857 | 0.9167 |
| Pythia-70M | Final token | `2,3,4,5,6` | 5 | 0.1811 | 0.1643 | 0.8333 |
| GPT-2 | Mean | `1,2,11` | 1 | 0.2348 | 0.1767 | 1.0000 |
| GPT-2 | Final token | `9,10,11,12` | 12 | 0.3619 | 0.2700 | 0.8333 |

The bridge signal survives final-token pooling in both models, so mean pooling is not required for the effect. But pooling changes where the signal appears. Mean pooling emphasizes early block outputs, while final-token pooling emphasizes later block outputs.

## Final-Token Results

### Pythia-70M

| Layer | Centered category separation | Centered bridge lift | Centered bridge rate | Gate |
| --- | ---: | ---: | ---: | --- |
| 0 | 0.0751 | 0.0300 | 0.5833 | embedding / fail |
| 1 | 0.1022 | 0.0715 | 0.5000 | fail |
| 2 | 0.1356 | 0.0961 | 0.9167 | pass |
| 3 | 0.1384 | 0.0954 | 0.7500 | pass |
| 4 | 0.1544 | 0.1243 | 0.8333 | pass |
| 5 | 0.1643 | 0.1811 | 0.8333 | pass |
| 6 | 0.1565 | 0.1670 | 0.8333 | pass |

### GPT-2

| Layer | Centered category separation | Centered bridge lift | Centered bridge rate | Gate |
| --- | ---: | ---: | ---: | --- |
| 0 | 0.0708 | 0.0183 | 0.5833 | embedding / fail |
| 1 | 0.0841 | 0.0225 | 0.5000 | fail |
| 2 | 0.0926 | 0.0374 | 0.6667 | fail |
| 3 | 0.0989 | 0.0392 | 0.5833 | fail |
| 4 | 0.0989 | 0.0393 | 0.5000 | fail |
| 5 | 0.0988 | 0.0303 | 0.5833 | fail |
| 6 | 0.0963 | 0.0385 | 0.6667 | fail |
| 7 | 0.1041 | 0.0477 | 0.6667 | fail |
| 8 | 0.1134 | 0.0587 | 0.6667 | fail |
| 9 | 0.1278 | 0.0840 | 0.7500 | pass |
| 10 | 0.1459 | 0.1008 | 0.7500 | pass |
| 11 | 0.1612 | 0.1355 | 0.7500 | pass |
| 12 | 0.2700 | 0.3619 | 0.8333 | pass |

## Interpretation

The ablation clears the robustness gate. Both models have at least two block-output layers passing under final-token pooling: Pythia passes layers `2-6`, and GPT-2 passes layers `9-12`.

The earlier mean-pooling result should be revised rather than discarded. Mean pooling made the strongest cross-model pattern look early-layer-heavy: Pythia's best block layer was `2`, and GPT-2's was `1`. Final-token pooling makes the strongest evidence later: Pythia's best layer is `5`, and GPT-2's is `12`.

This makes sense mechanistically. Mean pooling averages token-level evidence across the whole prompt, so it can preserve lexical and phrase-level semantic geometry in earlier layers. Final-token pooling samples the position where the model has accumulated the whole prompt context, so bridge geometry shifts toward later contextual states.

The bridge signal is therefore not merely a mean-pooling artifact, but layer-location claims are pooling-dependent. Steering or classification experiments should choose intervention layers under a declared pooling/readout hypothesis instead of treating "best layer" as intrinsic to the model.

## Discovery-Regime Audit

Question: does centered activation bridge geometry survive a pooling ablation?

Current regime:

- Artifact types: paraphrased concept prompts, pooled hidden-state vectors, model-indexed and layer-indexed raw and centered geometry summaries, pooling-indexed bridge-lift reports, audit cards.
- Operations: Modal-backed open-model extraction, mean pooling, final-token pooling, global mean-centering, cosine-kernel summary, bridge-lift comparison.
- Gates/verifiers: pooling perturbation, model replication, layerwise centered category separation, bridge lift, bridge-pair rate, raw anisotropy inspection, publication guard.
- Known limitations: same prompt set, hand-authored bridge pairs, no causal intervention, no bridge-pair-level stability analysis yet.

Action class:

- Retrieval/search/discovery: verifier upgrade.
- Why: this adds pooling as an explicit verifier dimension and revises the accepted activation-geometry claim.

Experiment:

- Manifest/report paths: this report; local-only final-token payloads under `artifacts/activation_geometry/`.
- Positive targets: persistence of centered bridge geometry under final-token pooling in both models.
- Negative controls: explicit reporting of layers that fail the final-token gate.
- Stress tests: pooling perturbation across Pythia-70M and GPT-2.

Gate:

- Acceptance rule: each model must have at least two block-output layers with centered category separation at least `0.05`, centered bridge lift at least `0.05`, and bridge-pair above-baseline rate at least `0.75`.
- Withheld/rejected rule: raw activation JSON stays untracked under `artifacts/`; failed layers remain in the public report.

Results:

- Accepted artifacts: this report; pooling-aware manifest and runner updates.
- Rejected or withheld artifacts: local-only final-token raw activation payloads.
- Key metrics: Pythia final-token layer `5` bridge lift `0.1811`; GPT-2 final-token layer `12` bridge lift `0.3619`.
- Variance or ablation: mean pooling emphasizes early block outputs; final-token pooling emphasizes later block outputs.

Residual content:

- Explained by old regime: centered bridge geometry persists across models and pooling rules.
- New content outside old regime: layer profiles are pooling-dependent; "best layer" is not an intrinsic model property.
- Retractions or supersessions: previous early-layer claims should be stated as mean-pooling claims, not as pooling-independent activation geometry.

Next move: choose candidate intervention layers separately for mean-pooling-style classifiers and final-token-style generation/steering probes.
