# Label-Free Transfer Baseline - 2026-06-08

## Question

Are the attractor-family label-free transfer rows exceptional, or are they ordinary instances of a broader definition-derived target-state transfer effect?

The previous label-free readout diagnostic accepted target-state transfer without visible answer choices, but it also showed that generic controls passed. This run adds a broad null distribution of sampled concept pairs and compares the attractor-family rows against that distribution.

## Method

Raw payloads remain local-only under ignored `artifacts/`.

Payload:

```text
artifacts/activation_geometry/modal_pythia_70m_deduped_label_free_transfer_baseline.json
```

Grid:

- Model: `EleutherAI/pythia-70m-deduped`
- Injection layer: `5`
- Readout layer: `6`
- Readout: nearest-centroid cosine readout trained on definition variants `0` and `1`
- Evaluation prompts: held-out definition variant `2`
- Pair set: `combined`
- Focus pairs: 7 previously tested rows
- Baseline pairs: 56 sampled ordered concept pairs, excluding the focus left-right pairs
- Baseline split: 14 same-category rows and 42 cross-category rows
- Patch text regimes: `definition`, `neutral`
- Patch modes: `target`, `distractor`, `random`, `source_noop`
- Patch alpha: `1.0`
- Seed: `20260608`

Command:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_label_free_readout_basin.py --model-id EleutherAI/pythia-70m-deduped --injection-layers 5 --readout-layers 6 --max-length 128 --train-variants 0,1 --eval-variant 2 --patch-alpha 1.0 --patch-modes target,distractor,random,source_noop --patch-text-regimes definition,neutral --pair-set combined --baseline-sample-count 56 --seed 20260608 --out artifacts/activation_geometry/modal_pythia_70m_deduped_label_free_transfer_baseline.json
```

Sanity gate:

- Max absolute `definition` source-noop aggregate delta: `0.0`.
- This confirms that replacing a source definition activation with the same source definition activation is an exact no-op under the definition regime.
- The `neutral` source-noop rows are not expected to be exact no-ops because their carrier prompt differs from the source definition prompt.

Specificity gate:

- Target patch must increase target readout margin.
- Target class must be top-3 under the patched readout.
- Target patch must beat the best of distractor, random, and source-noop patch modes.

## Baseline Distribution

| Patch text | Group | Specific passes | Pass rate | Mean target delta | Median target delta | Mean advantage | Median advantage |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| definition | baseline distribution | 43/56 | 76.8% | 0.366 | 0.357 | 0.170 | 0.186 |
| neutral | baseline distribution | 7/56 | 12.5% | 0.145 | 0.120 | 0.010 | 0.009 |

The broad null is not sparse. Most sampled definition-patch baseline rows pass the same specificity gate that the attractor rows pass.

## Focus Rows Against Baseline

| Patch text | Kind | Specific passes | Pass rate | Mean target delta | Mean advantage | Mean advantage percentile | Max advantage percentile |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| definition | positive | 1/1 | 100.0% | 0.259 | 0.259 | 71.4% | 71.4% |
| definition | source_family | 4/4 | 100.0% | 0.516 | 0.264 | 71.4% | 85.7% |
| definition | generic_control | 2/2 | 100.0% | 0.489 | 0.246 | 71.4% | 71.4% |
| neutral | positive | 0/1 | 0.0% | -0.184 | -0.029 | 5.4% | 5.4% |
| neutral | source_family | 0/4 | 0.0% | 0.095 | -0.032 | 5.4% | 7.1% |
| neutral | generic_control | 0/2 | 0.0% | 0.219 | 0.026 | 73.2% | 94.6% |

The attractor-family rows pass, but they are not anomalous against the definition baseline. The mean advantage for the positive/source-family rows is around the 71st percentile, and the strongest source-family row reaches only the 86th percentile.

## Same-Category vs Cross-Category Baselines

| Patch text | Baseline kind | Specific passes | Mean target delta | Mean advantage |
| --- | --- | ---: | ---: | ---: |
| definition | same category | 9/14 | 0.220 | 0.069 |
| definition | cross category | 34/42 | 0.415 | 0.204 |
| neutral | same category | 5/14 | 0.083 | 0.016 |
| neutral | cross category | 2/42 | 0.165 | 0.008 |

Cross-category definition transfer is stronger than same-category transfer in this sampled null. This may reflect an easier target-margin move when source and target concepts are more separated, so it should be treated as a property to probe rather than a final explanation.

## Strongest Baseline Rows

| Rank | Kind | Pair | Target delta | Best control | Advantage | Pass |
| ---: | --- | --- | ---: | --- | ---: | --- |
| 1 | cross category | `autopoiesis` -> `basin_of_attraction` | 0.991 | distractor | 0.698 | yes |
| 2 | cross category | `prototype` -> `simplicity_bias` | 0.572 | random | 0.568 | yes |
| 3 | same category | `self_boundary` -> `valence` | 0.695 | distractor | 0.566 | yes |
| 4 | cross category | `validity_gate` -> `self_boundary` | 0.661 | random | 0.560 | yes |
| 5 | cross category | `activation_vector` -> `valence` | 0.628 | random | 0.554 | yes |
| 6 | same category | `phase_space` -> `basin_of_attraction` | 0.600 | random | 0.526 | yes |
| 7 | same category | `homeostasis` -> `valence` | 0.523 | source_noop | 0.523 | yes |
| 8 | cross category | `self_boundary` -> `attractor_network` | 0.882 | random | 0.507 | yes |

Several baseline rows are substantially stronger than the attractor focus rows. That is the most important negative evidence against an attractor-specific mechanism.

## Interpretation

The general label-free target-state transfer effect survives and looks real under this verifier.

Definition-derived target patches at layer `5` frequently move downstream layer-`6` hidden states toward the target concept under a label-free centroid readout. The effect depends on semantic definition content: the neutral-carrier baseline pass rate is much lower, and the focus/source-family neutral rows fail specificity.

The attractor-specific claim should be downgraded. The attractor rows are successful, but they are not exceptional against the broad null. The accepted finding is:

```text
Pythia-70M-deduped supports broad label-free definition-derived target-state
transfer from layer 5 to layer 6.
```

The rejected or withheld finding is:

```text
The attractor-family rows are not currently evidence for a special
attractor-specific activation basin.
```

This is useful progress because it turns the question from "is there an attractor-family basin?" into a more mechanistic question:

```text
When and why can a definition-derived concept state overwrite, redirect, or
reclassify a downstream hidden state under a label-free readout?
```

## Limitations

- One small causal LM checkpoint.
- One injection/readout layer pair.
- One patch alpha.
- Nearest-centroid readout rather than a trained classifier.
- Baseline distractors are chosen preferentially from the target category, which may affect the same-category and cross-category comparison.
- The sampled null is broad but still limited by the current concept set.

## Next Move

Run a layer and alpha dose-response for the generic transfer effect:

- Sweep earlier injection layers, downstream readout layers, and patch alpha.
- Ask whether transfer only appears when we overwrite a late hidden state, or whether it propagates from earlier layers.
- Compare definition, neutral, distractor, random, and source-noop controls at every layer/alpha setting.
- Preserve attractor-family rows as one slice, but optimize the experiment around the broader target-state transfer mechanism.

## Discovery-Regime Audit

Question: are the attractor-family label-free transfer rows exceptional against a broad null distribution?

Current regime:

- Artifact types: label-free patch payloads, centroid-readout rows, sampled baseline-pair rows, transfer-baseline summaries.
- Operations: held-out centroid readout training, layer-5 activation patching, layer-6 downstream readout scoring, sampled same-category and cross-category baseline construction.
- Gates/verifiers: exact definition-source no-op gate, target-over-control readout specificity gate, neutral-carrier stress test, baseline percentile comparison.
- Known limitations: one checkpoint, one injection/readout layer pair, one alpha, limited concept inventory.

Action class:

- Retrieval/search/discovery: search inside the label-free readout regime.
- Why: the run extends the null distribution without changing the intervention artifact type.

Experiment:

- Manifest/report paths: this report; local ignored payload under `artifacts/activation_geometry/modal_pythia_70m_deduped_label_free_transfer_baseline.json`.
- Positive targets: `attractor` -> `attractor_network`.
- Negative controls: neutral patch text, distractor/random/source patch modes.
- Stress tests: 56 sampled baseline pairs split across same-category and cross-category rows.

Gate:

- Acceptance rule: promote attractor exceptionality only if focus/source-family rows sit high in the baseline advantage distribution.
- Withheld/rejected rule: withhold attractor-specific claims if baseline rows pass at comparable or higher rates.

Results:

- Accepted artifacts: this report; `experiments/activation_geometry/label_free_readout_basin.py`; `experiments/activation_geometry/modal_label_free_readout_basin.py`.
- Rejected or withheld artifacts: attractor-specific activation basin claim is withheld.
- Key metrics: definition baseline passes `43/56`; definition positive `1/1`; definition source-family `4/4`; source-family mean advantage percentile `71.4%`; source-family max advantage percentile `85.7%`; neutral baseline passes `7/56`.
- Variance or ablation: definition content dominates neutral label-carrier transfer; cross-category definition baseline rows are stronger than same-category rows in this sample.

Residual content:

- Explained by old regime: the label-free attractor rows are examples of generic definition-derived target-state transfer.
- New content outside old regime: the broader mechanism itself is now the residual worth explaining.
- Retractions or supersessions: supersede "generic label-free target-state transfer, attractor-family special case uncertain" with "broad label-free target-state transfer; attractor-specific exceptionality rejected for now."

Next move: run a layer/alpha dose-response to determine whether generic transfer is a late-state overwrite artifact or a propagating intervention.
