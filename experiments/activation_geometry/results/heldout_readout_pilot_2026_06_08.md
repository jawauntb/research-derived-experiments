# Held-Out Activation Readout Pilot - 2026-06-08

## Question

Do the selected mean-pooling activation layers preserve concept and bridge-pair structure when one paraphrase per concept is fully held out?

This pilot is a stricter verifier than the layer sweeps. The sweeps used all paraphrase variants to build concept centroids. Here, the readout trains each concept centroid on variants `0` and `1`, then evaluates only variant `2`.

## Method

Inputs:

- Pythia selected mean-pooling payload: `artifacts/activation_geometry/modal_pythia_70m_selected_mean_readout.json`
- GPT-2 selected mean-pooling payload: `artifacts/activation_geometry/modal_gpt2_selected_mean_readout.json`
- Combined held-out readout payload: `artifacts/activation_geometry/heldout_readout_selected_mean_combined.json`

All raw activation and readout payloads remain local-only under ignored `artifacts/`.

Commands:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_layer_sweep.py --model-id EleutherAI/pythia-70m-deduped --layers 2,6,4 --batch-size 8 --max-length 96 --pooling mean --out artifacts/activation_geometry/modal_pythia_70m_selected_mean_readout.json
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_layer_sweep.py --model-id gpt2 --layers 1,11,4 --batch-size 8 --max-length 96 --pooling mean --out artifacts/activation_geometry/modal_gpt2_selected_mean_readout.json
python3 experiments/activation_geometry/heldout_readout_pilot.py --concepts experiments/concept_geometry/concept_set.json --payload artifacts/activation_geometry/modal_pythia_70m_selected_mean_readout.json --payload artifacts/activation_geometry/modal_gpt2_selected_mean_readout.json --out artifacts/activation_geometry/heldout_readout_selected_mean_combined.json
```

Evaluation:

- Center activations by the mean of the training variants only.
- Normalize centered vectors.
- Build nearest-centroid readouts from variants `0` and `1`.
- Test concept/category readout on variant `2`.
- Compare held-out bridge-pair cosine against the same-run non-bridge cross-category mean.

## Layer Results

| Model | Role | Layer | Concept acc. | Category acc. | Bridge rate | Bridge lift | Positive pairs | Control pairs |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Pythia-70M | Primary | 2 | 1.000 | 1.000 | 0.833 | 0.148 | 4/4 | 1/2 |
| Pythia-70M | Backup | 6 | 1.000 | 1.000 | 0.750 | 0.155 | 4/4 | 0/2 |
| Pythia-70M | Control | 4 | 1.000 | 1.000 | 0.667 | 0.101 | 2/4 | 1/2 |
| GPT-2 | Primary | 1 | 1.000 | 1.000 | 0.917 | 0.124 | 4/4 | 2/2 |
| GPT-2 | Backup | 11 | 0.875 | 1.000 | 0.500 | 0.119 | 3/4 | 0/2 |
| GPT-2 | Control | 4 | 0.292 | 0.500 | 0.500 | 0.147 | 3/4 | 1/2 |

## Candidate Bridge Pairs

Primary-layer positives:

| Pair | Pythia layer 2 | GPT-2 layer 1 | Held-out result |
| --- | ---: | ---: | --- |
| `attractor` -> `attractor_network` | 0.348 | 0.278 | Passes both |
| `conceptual_space` -> `representation_manifold` | 0.112 | 0.240 | Passes both |
| `autopoiesis` -> `homeostasis` | 0.274 | 0.203 | Passes both |
| `validity_gate` -> `weak_constraint` | 0.300 | 0.177 | Passes both |

Control pairs:

| Pair | Pythia layer 2 | GPT-2 layer 1 | Held-out result |
| --- | ---: | ---: | --- |
| `valence` -> `activation_vector` | 0.009 | 0.054 | Passes both |
| `valence` -> `steering_vector` | -0.053 | 0.052 | Passes GPT-2 only |

## Gate

Pre-registered acceptance rule from the intervention-candidate report:

- Primary layers must outperform their control layers on bridge-pair above-baseline rate by at least `0.20`.
- At least three of four positive bridge-pair candidates must beat the non-bridge cross-category mean in both models.
- Valence control pairs should not pass both models.

Result: partially accepted.

- Positive candidate gate passes: all four positive bridge pairs pass in both primary layers.
- Classifier/readout gate passes as a concept identity check: both primary layers classify all 24 held-out concepts correctly.
- Control-layer margin is mixed: GPT-2 primary layer `1` beats control layer `4` by `0.417`, but Pythia primary layer `2` beats control layer `4` by only `0.167`, below the `0.20` margin.
- Valence control gate fails: `valence` -> `activation_vector` passes in both primary layers, and GPT-2 layer `1` passes both valence controls.

## Interpretation

The strongest result is not causal yet: selected mean-pooling layers can read out held-out concept identity and keep the four intended bridge pairs above the non-bridge cross-category baseline.

The main issue is specificity. GPT-2's primary layer makes the valence controls look bridge-like, and Pythia's primary/control bridge-rate margin misses the preregistered threshold by a small amount. This means the readout can support a next diagnostic, but it should not yet be used as evidence that the bridge directions are targeted enough for generation steering.

The surprising detail is that Pythia layer `6`, originally the backup, has cleaner controls than layer `2` while retaining 4/4 positive candidate pairs. For readout-only experiments, layer `2` still has the strongest prior score; for causal steering preparation, layer `6` may be the cleaner Pythia target.

## Next Move

Before final-token steering, run a pair-level control-leakage diagnostic:

- Recompute held-out readout with shuffled bridge labels and category-matched random cross-category pairs.
- Promote only pairs that beat both the non-bridge baseline and the matched random-pair distribution.
- Treat `valence` -> `activation_vector` as an active adversarial control, not a negative that can be assumed to fail.

## Discovery-Regime Audit

Question: do selected activation layers preserve bridge structure under held-out paraphrase readout?

Current regime:

- Artifact types: concept prompts, paraphrase-indexed activation payloads, train/holdout centroid readouts, bridge-pair pass tables, control-pair warnings.
- Operations: train-variant centering, nearest-centroid readout, held-out bridge cosine comparison, control-layer comparison.
- Gates/verifiers: held-out paraphrases, preselected primary/backup/control layers, positive bridge-pair gate, valence control gate, publication guard.
- Known limitations: only one holdout variant per concept, hand-authored control pairs, no matched random-pair distribution yet, no causal intervention.

Action class:

- Retrieval/search/discovery: verifier upgrade.
- Why: the run tests whether the earlier activation geometry survives an unseen paraphrase split and exposes control leakage before steering.

Gate:

- Acceptance rule: pass all preregistered held-out readout gates.
- Withheld/rejected rule: raw activation/readout payloads stay local-only under `artifacts/`; mixed gates are reported rather than promoted to causal claims.

Results:

- Accepted artifacts: this report; `experiments/activation_geometry/heldout_readout_pilot.py`.
- Rejected or withheld artifacts: local-only raw activation/readout payloads under `artifacts/activation_geometry/`.
- Key metrics: Pythia layer `2` concept accuracy `1.000`, bridge rate `0.833`, positive pairs `4/4`; GPT-2 layer `1` concept accuracy `1.000`, bridge rate `0.917`, positive pairs `4/4`.
- Variance or ablation: Pythia layer `6` has cleaner control pairs than layer `2`; GPT-2 layer `1` has strong positive pairs but leaky valence controls.

Residual content:

- Explained by old regime: concept identity readout can be strong even when some control pairs leak.
- New content outside old regime: held-out bridge structure survives for the four intended pairs, but specificity is not yet adequate for steering claims.
- Retractions or supersessions: do not proceed as if the valence controls failed; at least one valence control is now an adversarial positive control.

Next move: run the pair-level control-leakage diagnostic before the first final-token steering pilot.
