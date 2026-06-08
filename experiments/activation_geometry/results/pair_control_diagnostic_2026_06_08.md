# Pair-Control Activation Diagnostic - 2026-06-08

## Question

Which held-out bridge pairs survive stronger pair-level controls after the valence controls leaked in the held-out readout pilot?

The previous held-out readout showed that all four intended positive bridge pairs passed in both primary mean-pooling layers, but `valence` -> `activation_vector` also passed the simpler non-bridge baseline. This diagnostic asks whether the candidate pairs still stand out when compared against category-matched controls and category-preserving label shuffles.

## Method

Inputs:

- Pythia selected mean-pooling payload: `artifacts/activation_geometry/modal_pythia_70m_selected_mean_pair_controls.json`
- GPT-2 selected mean-pooling payload: `artifacts/activation_geometry/modal_gpt2_selected_mean_pair_controls.json`
- Pair-control diagnostic payload: `artifacts/activation_geometry/pair_control_diagnostic_selected_mean.json`

All raw activation and diagnostic payloads remain local-only under ignored `artifacts/`.

Commands:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_layer_sweep.py --model-id EleutherAI/pythia-70m-deduped --layers 2,6,4 --batch-size 8 --max-length 96 --pooling mean --out artifacts/activation_geometry/modal_pythia_70m_selected_mean_pair_controls.json
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_layer_sweep.py --model-id gpt2 --layers 1,11,4 --batch-size 8 --max-length 96 --pooling mean --out artifacts/activation_geometry/modal_gpt2_selected_mean_pair_controls.json
python3 experiments/activation_geometry/pair_control_diagnostic.py --concepts experiments/concept_geometry/concept_set.json --payload artifacts/activation_geometry/modal_pythia_70m_selected_mean_pair_controls.json --payload artifacts/activation_geometry/modal_gpt2_selected_mean_pair_controls.json --shuffle-count 512 --seed 20260608 --out artifacts/activation_geometry/pair_control_diagnostic_selected_mean.json
```

Promotion rule:

- The pair cosine must beat the held-out non-bridge cross-category mean.
- The pair cosine must beat the 95th percentile of exact category-pair matched non-bridge controls.
- The pair cosine must beat the 95th percentile of category-preserving shuffled-label controls.

For same-category pairs such as `autopoiesis` -> `homeostasis` and `validity_gate` -> `weak_constraint`, the matched controls are same-category non-bridge pairs. This is intentionally stricter than the old cross-category baseline.

## Layer Summary

| Model | Role | Layer | Positive promoted | Valence controls promoted |
| --- | --- | ---: | ---: | ---: |
| Pythia-70M | Primary | 2 | 3/4 | 0/2 |
| Pythia-70M | Backup | 6 | 4/4 | 0/2 |
| Pythia-70M | Control | 4 | 2/4 | 0/2 |
| GPT-2 | Primary | 1 | 4/4 | 0/2 |
| GPT-2 | Backup | 11 | 1/4 | 0/2 |
| GPT-2 | Control | 4 | 1/4 | 0/2 |

## Primary-Layer Pair Results

| Pair | Pythia layer 2 | GPT-2 layer 1 | Result |
| --- | --- | --- | --- |
| `attractor` -> `attractor_network` | 0.348 > matched p95 0.150, shuffled p95 0.247 | 0.278 > matched p95 0.128, shuffled p95 0.177 | Promoted both |
| `conceptual_space` -> `representation_manifold` | 0.112 < matched p95 0.226, shuffled p95 0.230 | 0.240 > matched p95 0.165, shuffled p95 0.220 | GPT-2 only |
| `autopoiesis` -> `homeostasis` | 0.274 > matched p95 0.136, shuffled p95 0.180 | 0.203 > matched p95 -0.039, shuffled p95 -0.037 | Promoted both |
| `validity_gate` -> `weak_constraint` | 0.300 > matched p95 0.151, shuffled p95 0.154 | 0.177 > matched p95 0.135, shuffled p95 0.136 | Promoted both |

Valence controls:

| Pair | Pythia layer 2 | GPT-2 layer 1 | Result |
| --- | --- | --- | --- |
| `valence` -> `activation_vector` | 0.009 < matched p95 0.066, shuffled p95 0.151 | 0.054 < matched p95 0.056, shuffled p95 0.083 | Not promoted |
| `valence` -> `steering_vector` | -0.053 < matched p95 0.066, shuffled p95 0.151 | 0.052 < matched p95 0.056, shuffled p95 0.083 | Not promoted |

## Gate

Acceptance rule:

- At least two positive bridge-pair candidates must promote in both primary layers.
- No valence control pair may promote in either primary layer.
- Control-layer positive promotions are allowed as warnings, but they prevent a layer-specific causal claim.

Result: accepted as a pair-level steering-candidate diagnostic, not as a causal layer-specific result.

- Three positive pairs promote in both primary layers: `attractor` -> `attractor_network`, `autopoiesis` -> `homeostasis`, and `validity_gate` -> `weak_constraint`.
- `conceptual_space` -> `representation_manifold` remains model-specific: it promotes in GPT-2 layer `1` but not Pythia layer `2`.
- Both valence controls fail promotion in both primary layers, resolving the prior valence leakage under stricter controls.
- Pythia layer `4` still promotes two positive pairs and GPT-2 layer `4` promotes `autopoiesis` -> `homeostasis`, so this diagnostic does not establish layer-specific causality.

## Interpretation

The stronger controls sharpen the candidate set. The original all-positive result was too broad; after matched and shuffled controls, the cross-model primary-layer survivors are:

- `attractor` -> `attractor_network`
- `autopoiesis` -> `homeostasis`
- `validity_gate` -> `weak_constraint`

These are now the best first targets for a final-token steering pilot. `conceptual_space` -> `representation_manifold` should stay in the report as a model-specific or backup candidate rather than a primary steering target.

The valence leakage from the previous run was likely a weak-baseline artifact. Both valence controls were above the old non-bridge mean in GPT-2 layer `1`, but neither beat the matched or shuffled 95th percentile.

## Caveats

- Same-category matched pools are small: `validity_gate` -> `weak_constraint` has only two exact same-category non-bridge controls, and `autopoiesis` -> `homeostasis` has four.
- This is still a readout diagnostic over mean-pooled vectors; it does not prove an activation intervention will move generation in the target direction.
- Control layers can still promote some positive pairs, so the next steering run must include layer controls and signed intervention controls.

## Discovery-Regime Audit

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

- Accepted artifacts: this report; `experiments/activation_geometry/pair_control_diagnostic.py`.
- Rejected or withheld artifacts: local-only payloads under `artifacts/activation_geometry/`.
- Key metrics: Pythia primary layer `2` promotes `3/4` positive pairs and `0/2` valence controls; GPT-2 primary layer `1` promotes `4/4` positive pairs and `0/2` valence controls.
- Variance or ablation: Pythia backup layer `6` promotes `4/4` positive pairs with clean valence controls; control layers are not inert.

Residual content:

- Explained by old regime: weak cross-category baselines can make valence controls look bridge-like.
- New content outside old regime: three bridge pairs survive matched and shuffled controls in both primary layers.
- Retractions or supersessions: `conceptual_space` -> `representation_manifold` is no longer a cross-model primary candidate under strict controls.

Next move: run the first final-token steering pilot using the cross-model promoted pairs, with `conceptual_space` -> `representation_manifold` retained as a backup/model-specific probe.
