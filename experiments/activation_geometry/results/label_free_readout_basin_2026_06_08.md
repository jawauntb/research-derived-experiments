# Label-Free Readout Basin Diagnostic - 2026-06-08

## Question

Does the semantically mediated attractor-family answer basin survive without visible answer choices?

The previous answer-surface diagnostic showed that the basin was not a trivial label-only artifact: semantic aliases preserved part of the effect, while symbol labels and neutral label-carrier patch prompts broke it. This run removes answer choices entirely and asks whether definition-derived target states move downstream hidden states toward a label-free concept readout.

## Method

Raw payloads remain local-only under ignored `artifacts/`.

Payload:

```text
artifacts/activation_geometry/modal_pythia_70m_deduped_label_free_readout_basin.json
```

Grid:

- Model: `EleutherAI/pythia-70m-deduped`
- Injection layer: `5`
- Readout layer: `6`
- Readout: nearest-centroid cosine readout trained on definition variants `0` and `1`
- Evaluation prompts: held-out definition variant `2`
- No answer choices or visible option labels in source prompts
- Patch text regimes:
  - `definition`: patch activations from held-out concept definitions
  - `neutral`: patch activations from minimal label carriers such as `Concept label: attractor network.`
- Patch modes: `target`, `distractor`, `random`, `source_noop`
- Attractor-family rows: `attractor`, `prototype`, `schema`, `conceptual_space`, `basin_of_attraction` into `attractor_network`
- Generic controls: `valence` into `activation_vector` and `steering_vector`
- Patch alpha: `1.0`
- Seed: `20260608`

Command:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_label_free_readout_basin.py --model-id EleutherAI/pythia-70m-deduped --injection-layers 5 --readout-layers 6 --max-length 128 --train-variants 0,1 --eval-variant 2 --patch-alpha 1.0 --patch-modes target,distractor,random,source_noop --patch-text-regimes definition,neutral --seed 20260608 --out artifacts/activation_geometry/modal_pythia_70m_deduped_label_free_readout_basin.json
```

Sanity gate:

- Max absolute `definition` source-noop aggregate delta: `0.0`.
- This confirms that replacing a source definition activation with the same source definition activation is an exact no-op under the label-free readout.

Specificity gate:

- Target patch must increase target readout margin.
- Target class must be top-3 under the patched readout.
- Target patch must beat the best of distractor, random, and source-noop patch modes.

## Gate Summary

| Patch text | Kind | Specific passes | Mean target delta | Mean advantage |
| --- | --- | ---: | ---: | ---: |
| definition | positive | 1/1 | 0.259 | 0.259 |
| definition | source_family | 4/4 | 0.516 | 0.264 |
| definition | generic_control | 2/2 | 0.489 | 0.246 |
| neutral | positive | 0/1 | -0.184 | -0.029 |
| neutral | source_family | 0/4 | 0.095 | -0.032 |
| neutral | generic_control | 0/2 | 0.219 | 0.026 |

## Row Summary

| Patch text | Kind | Pair | Target delta | Best control | Advantage | Target top-3 | Pass |
| --- | --- | --- | ---: | --- | ---: | ---: | --- |
| definition | positive | `attractor` -> `attractor_network` | 0.259 | source_noop | 0.259 | 1 | yes |
| definition | source family | `basin_of_attraction` -> `attractor_network` | 0.639 | distractor | 0.175 | 1 | yes |
| definition | source family | `conceptual_space` -> `attractor_network` | 0.468 | source_noop | 0.468 | 1 | yes |
| definition | source family | `prototype` -> `attractor_network` | 0.437 | distractor | 0.243 | 1 | yes |
| definition | source family | `schema` -> `attractor_network` | 0.518 | distractor | 0.169 | 1 | yes |
| definition | generic control | `valence` -> `activation_vector` | 0.729 | random | 0.243 | 1 | yes |
| definition | generic control | `valence` -> `steering_vector` | 0.249 | source_noop | 0.249 | 1 | yes |
| neutral | positive | `attractor` -> `attractor_network` | -0.184 | random | -0.029 | 1 | no |
| neutral | source family | `basin_of_attraction` -> `attractor_network` | 0.271 | random | -0.038 | 0 | no |
| neutral | source family | `conceptual_space` -> `attractor_network` | -0.024 | random | -0.035 | 0 | no |
| neutral | source family | `prototype` -> `attractor_network` | -0.014 | random | -0.043 | 0 | no |
| neutral | source family | `schema` -> `attractor_network` | 0.147 | random | -0.014 | 0 | no |
| neutral | generic control | `valence` -> `activation_vector` | 0.373 | random | 0.005 | 0 | no |
| neutral | generic control | `valence` -> `steering_vector` | 0.064 | distractor | 0.046 | 0 | no |

## Interpretation

The answer-choice interface is not necessary for target-state transfer.

Definition-derived target patches at layer `5` move downstream layer-`6` hidden states toward the target concept under a label-free centroid readout. The original `attractor` -> `attractor_network` row passes, and all four source-family rows into `attractor_network` pass. The neutral label-carrier controls fail all specificity gates, which means the effect is not produced by minimal label text alone.

But this is not yet evidence for an attractor-specific activation-space basin. The generic controls pass too:

```text
valence -> activation_vector: pass
valence -> steering_vector: pass
```

So the accepted result is broader and more conservative:

```text
Pythia-70M-deduped supports label-free definition-derived target-state transfer
from layer 5 to layer 6, and the attractor-family basin is one instance of this
generic transfer behavior.
```

This is real progress because it separates three possibilities:

- Pure answer-label artifact: rejected by answer-surface and label-free controls.
- Label-free target-state transfer: accepted.
- Attractor-specific basin: still withheld because generic controls also transfer.

## Next Move

Run a broad label-free target-state transfer baseline:

- Sample many concept pairs across categories.
- Patch target definition states at layer `5` and read out at layer `6`.
- Compare target-transfer success and margin against semantic distance, category membership, and random controls.
- Ask whether attractor-family rows are anomalously strong, unusually robust, or simply ordinary instances of generic target-state transfer.

If attractor-family rows are exceptional against that null distribution, we can resurrect a narrow basin claim. If not, the general mechanism becomes the finding: definition-derived concept states can causally overwrite downstream concept readouts.

## Discovery-Regime Audit

Question: does the semantically mediated attractor-family basin exist in activation space without visible answer choices?

Current regime:

- Artifact types: label-free patch payloads, centroid-readout rows, definition/neutral patch-text controls, specificity summaries.
- Operations: held-out centroid readout training, layer-5 activation patching, layer-6 downstream readout scoring.
- Gates/verifiers: exact definition-source no-op gate, target-over-control readout specificity gate, neutral-carrier failure gate, generic-transfer control check.
- Known limitations: one model checkpoint, one injection/readout layer pair, centroid readout rather than a trained linear classifier.

Action class:

- Retrieval/search/discovery: search inside the upgraded label-free readout regime.
- Why: this run tests the new no-answer-choice verifier but does not yet establish a new attractor-specific artifact class.

Experiment:

- Manifest/report paths: this report; local ignored payload under `artifacts/activation_geometry/modal_pythia_70m_deduped_label_free_readout_basin.json`.
- Positive targets: `attractor` -> `attractor_network`.
- Negative controls: neutral patch text, distractor/random/source patch modes.
- Stress tests: source-family sweep into `attractor_network`, generic valence/vector transfer controls.

Gate:

- Acceptance rule: accept label-free transfer if definition target patches pass specificity and neutral label-carrier patches fail.
- Withheld/rejected rule: withhold attractor-specific basin claims if generic transfer controls also pass.

Results:

- Accepted artifacts: this report; `experiments/activation_geometry/label_free_readout_basin.py`; `experiments/activation_geometry/modal_label_free_readout_basin.py`.
- Rejected or withheld artifacts: attractor-specific activation-space basin claim is withheld.
- Key metrics: definition positive `1/1`; definition source-family `4/4`; definition generic controls `2/2`; neutral rows `0/7`; definition source-noop max delta `0.0`.
- Variance or ablation: definition patches transfer strongly; neutral label-carrier patches do not pass specificity.

Residual content:

- Explained by old regime: answer-choice target-margin effects can be semantically mediated.
- New content outside old claim: the target-state transfer survives without visible answer choices, but it appears generic rather than attractor-specific.
- Retractions or supersessions: supersede "semantically mediated answer-surface basin" with "generic label-free definition-derived target-state transfer; attractor-family rows are currently a special case only by topic, not by mechanism."

Next move: build a broad label-free target-state transfer baseline across many concept pairs and compare the attractor-family rows against that null distribution.
