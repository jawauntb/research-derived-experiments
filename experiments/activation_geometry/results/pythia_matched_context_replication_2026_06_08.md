# Pythia Matched-Context Replication - 2026-06-08

## Question

Does the Pythia-70M matched-context patching pocket survive context variants, random-control seeds, and nearby layer perturbations?

The previous matched-context run found a Pythia-specific pocket at layer `5`, but it was not accepted as semantic bridge causality because GPT-2 rejected the effect and Pythia had valence-control leakage. This run stress-tests that residual before expanding to generation or larger models.

## Method

Raw payloads remain local-only under ignored `artifacts/`.

Payload glob:

```text
artifacts/activation_geometry/modal_pythia_70m_matched_context_repl_v*_s*_l456.json
```

Grid:

- Model: `EleutherAI/pythia-70m-deduped`
- Layers: `4`, `5`, `6`
- Context variants: `0`, `1`, `2`
- Random-control seeds: `20260608`, `20260609`, `20260610`
- Patch modes: `target`, `distractor`, `random`, `source_noop`
- Option orders: `std`, `tds`, `dst`
- Patch alpha: `1.0`

Command template:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_matched_context_patching.py --model-id EleutherAI/pythia-70m-deduped --primary-layer 4 --backup-layer 5 --control-layer 6 --max-length 128 --context-variant <0|1|2> --patch-alpha 1.0 --patch-modes target,distractor,random,source_noop --option-orders std,tds,dst --seed <20260608|20260609|20260610> --out artifacts/activation_geometry/modal_pythia_70m_matched_context_repl_v<V>_s<S>_l456.json
```

Aggregation:

```bash
python3 experiments/activation_geometry/matched_context_replication.py --variant-layer 5 artifacts/activation_geometry/modal_pythia_70m_matched_context_repl_v*_s*_l456.json > artifacts/activation_geometry/pythia_matched_context_replication_summary.json
```

Sanity gate:

- Max absolute `source_noop` aggregate delta: `0.0`
- This confirms the exact no-op hook-surface control remains intact across all nine runs.

Pair-level gate:

- Target patch must have positive mean target-margin delta across option orders.
- At least two of three option orders must be positive.
- Target patch must beat the best of `distractor`, `random`, and `source_noop`.

Promotion gate:

- The Pythia pocket is promoted only if the positive bridge pattern survives variants/seeds/layers and valence controls do not show the same target-specific pattern.

## Layer-Pair Summary

Each cell summarizes nine runs: three context variants times three random-control seeds.

| Layer | Kind | Pair | Specific passes | Robust passes | Mean target delta | Mean advantage |
| ---: | --- | --- | ---: | ---: | ---: | ---: |
| 4 | Positive | `attractor` -> `attractor_network` | 6/9 | 6/9 | 0.059 | 0.021 |
| 4 | Positive | `autopoiesis` -> `homeostasis` | 6/9 | 6/9 | 0.041 | 0.006 |
| 4 | Positive | `validity_gate` -> `weak_constraint` | 0/9 | 0/9 | -0.050 | -0.116 |
| 4 | Exploratory | `conceptual_space` -> `representation_manifold` | 6/9 | 6/9 | 0.081 | -0.003 |
| 4 | Control | `valence` -> `activation_vector` | 0/9 | 0/9 | 0.008 | -0.029 |
| 4 | Control | `valence` -> `steering_vector` | 1/9 | 9/9 | 0.031 | -0.013 |
| 5 | Positive | `attractor` -> `attractor_network` | 9/9 | 9/9 | 0.156 | 0.087 |
| 5 | Positive | `autopoiesis` -> `homeostasis` | 3/9 | 6/9 | 0.007 | -0.046 |
| 5 | Positive | `validity_gate` -> `weak_constraint` | 0/9 | 0/9 | -0.080 | -0.182 |
| 5 | Exploratory | `conceptual_space` -> `representation_manifold` | 3/9 | 9/9 | 0.076 | -0.014 |
| 5 | Control | `valence` -> `activation_vector` | 3/9 | 3/9 | 0.036 | -0.057 |
| 5 | Control | `valence` -> `steering_vector` | 6/9 | 9/9 | 0.053 | 0.008 |
| 6 | Positive | `attractor` -> `attractor_network` | 3/9 | 9/9 | 0.094 | -0.027 |
| 6 | Positive | `autopoiesis` -> `homeostasis` | 3/9 | 6/9 | 0.001 | -0.021 |
| 6 | Positive | `validity_gate` -> `weak_constraint` | 0/9 | 0/9 | -0.065 | -0.157 |
| 6 | Exploratory | `conceptual_space` -> `representation_manifold` | 6/9 | 9/9 | 0.144 | 0.029 |
| 6 | Control | `valence` -> `activation_vector` | 3/9 | 3/9 | -0.015 | -0.067 |
| 6 | Control | `valence` -> `steering_vector` | 3/9 | 3/9 | 0.012 | -0.007 |

## Layer-5 Variant Summary

Layer `5` was the original Pythia primary layer. Each row summarizes three random-control seeds.

| Variant | Kind | Pair | Specific passes | Mean target delta | Mean advantage |
| ---: | --- | --- | ---: | ---: | ---: |
| 0 | Positive | `attractor` -> `attractor_network` | 3/3 | 0.205 | 0.160 |
| 1 | Positive | `attractor` -> `attractor_network` | 3/3 | 0.072 | 0.029 |
| 2 | Positive | `attractor` -> `attractor_network` | 3/3 | 0.191 | 0.072 |
| 0 | Positive | `autopoiesis` -> `homeostasis` | 0/3 | 0.081 | -0.045 |
| 1 | Positive | `autopoiesis` -> `homeostasis` | 0/3 | -0.097 | -0.097 |
| 2 | Positive | `autopoiesis` -> `homeostasis` | 3/3 | 0.038 | 0.005 |
| 0 | Positive | `validity_gate` -> `weak_constraint` | 0/3 | -0.066 | -0.157 |
| 1 | Positive | `validity_gate` -> `weak_constraint` | 0/3 | -0.144 | -0.270 |
| 2 | Positive | `validity_gate` -> `weak_constraint` | 0/3 | -0.030 | -0.118 |
| 0 | Control | `valence` -> `activation_vector` | 0/3 | -0.031 | -0.131 |
| 1 | Control | `valence` -> `activation_vector` | 0/3 | 0.031 | -0.046 |
| 2 | Control | `valence` -> `activation_vector` | 3/3 | 0.107 | 0.005 |
| 0 | Control | `valence` -> `steering_vector` | 3/3 | 0.083 | 0.023 |
| 1 | Control | `valence` -> `steering_vector` | 3/3 | 0.071 | 0.071 |
| 2 | Control | `valence` -> `steering_vector` | 0/3 | 0.005 | -0.069 |
| 0 | Exploratory | `conceptual_space` -> `representation_manifold` | 0/3 | 0.035 | -0.105 |
| 1 | Exploratory | `conceptual_space` -> `representation_manifold` | 0/3 | 0.093 | -0.021 |
| 2 | Exploratory | `conceptual_space` -> `representation_manifold` | 3/3 | 0.100 | 0.084 |

## Interpretation

There is one stable Pythia finding:

```text
Layer-5 matched-context target patches for `attractor` -> `attractor_network`
pass the specificity gate in all 9 variant/seed runs.
```

This is not just a random-control artifact. The best control is `distractor` in every run for the stable layer-5 attractor pair, and the target patch still beats it in every variant and seed. The effect is strongest in variant `0`, weaker but still positive in variant `1`, and close to the prior matched-context result in variant `2`.

The broader bridge claim does not replicate:

- `autopoiesis` -> `homeostasis` only passes layer `5` on variant `2`.
- `validity_gate` -> `weak_constraint` fails everywhere.
- The exploratory `conceptual_space` -> `representation_manifold` effect is variant- and layer-dependent.
- Valence controls leak: layer-5 `valence` -> `steering_vector` passes `6/9`, and `valence` -> `activation_vector` passes `3/9`.

So the accepted update is narrow:

```text
Matched-context patching exposes a stable Pythia layer-5 attractor-network pocket,
but not a general semantic bridge-patching mechanism.
```

The right next move is a focused attractor-pocket diagnostic, not a broad generation demo. We should vary distractors and prompt frames around `attractor` -> `attractor_network`, add adversarial near-neighbor controls such as `prototype`, `schema`, and `category`, and test a third small causal LM or a second Pythia-family checkpoint.

## Discovery-Regime Audit

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

- Manifest/report paths: this report; local ignored payloads under `artifacts/activation_geometry/modal_pythia_70m_matched_context_repl_v*_s*_l456.json`.
- Positive targets: `attractor` -> `attractor_network`, `autopoiesis` -> `homeostasis`, `validity_gate` -> `weak_constraint`.
- Negative controls: `valence` -> `activation_vector`, `valence` -> `steering_vector`, distractor/random/source patch modes.
- Stress tests: context variants `0/1/2`, seeds `20260608/20260609/20260610`, layers `4/5/6`.

Gate:

- Acceptance rule: promote only effects that pass across variants and seeds at the target layer and do not look like valence-control leakage.
- Withheld/rejected rule: broad bridge mechanism is withheld if only one pair survives or controls show similar target-specific passes.

Results:

- Accepted artifacts: this report; `experiments/activation_geometry/matched_context_replication.py`.
- Rejected or withheld artifacts: broad Pythia matched-context bridge mechanism remains withheld.
- Key metrics: layer-5 `attractor` -> `attractor_network` specific passes `9/9`; layer-5 `autopoiesis` -> `homeostasis` specific passes `3/9`; layer-5 `validity_gate` -> `weak_constraint` specific passes `0/9`; layer-5 valence controls specific passes `9/18`.
- Variance or ablation: `attractor` survives all variants and seeds; other candidate pairs are variant-dependent or fail.

Residual content:

- Explained by old regime: context matching can make some final-token patches causal in Pythia.
- New content outside old regime: the stable residual is not a broad bridge class; it is a narrow attractor-network pocket at layer `5`.
- Retractions or supersessions: supersede the previous "Pythia matched-context pocket" phrasing with the narrower "Pythia layer-5 attractor-network pocket".

Next move: run a focused attractor-pocket diagnostic with distractor sweeps, adversarial near-neighbor controls, and third-model or second-checkpoint replication.
