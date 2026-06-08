# Answer-Surface Basin Diagnostic - 2026-06-08

## Question

Does the Pythia-70M-deduped layer-5 attractor-family basin follow semantic source/target content, visible answer labels, or the option-choice surface itself?

The focused attractor-pocket diagnostic rejected a clean `attractor` -> `attractor_network` bridge because near-neighbor controls leaked. This run asks whether that leakage is merely an answer-label artifact or whether the answer-choice basin still depends on semantic definitions and meaningful relabeling.

## Method

Raw payloads remain local-only under ignored `artifacts/`.

Payload:

```text
artifacts/activation_geometry/modal_pythia_70m_deduped_answer_surface_basin.json
```

Grid:

- Model: `EleutherAI/pythia-70m-deduped`
- Layers: primary `5`, control `6`
- Context variant: `0`
- Prompt frame: stable-state dynamics
- Source sweep into `attractor_network`: `attractor`, `prototype`, `schema`, `conceptual_space`, `basin_of_attraction`
- Label regimes:
  - `canonical`: original concept labels such as `attractor network`
  - `alias`: semantic aliases such as `recurrent stable-state network`
  - `symbol`: non-semantic labels such as `signal beta`
- Patch-text regimes:
  - `definition`: patch activations come from held-out concept definitions
  - `neutral`: patch activations come from minimal label carriers such as `Concept label: signal beta.`
- Patch modes: `target`, `distractor`, `random`, `source_noop`
- Option orders: `std`, `tds`, `dst`
- Patch alpha: `1.0`
- Seed: `20260608`

Command:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_answer_surface_basin.py --model-id EleutherAI/pythia-70m-deduped --primary-layer 5 --control-layer 6 --max-length 128 --context-variant 0 --patch-alpha 1.0 --patch-modes target,distractor,random,source_noop --option-orders std,tds,dst --label-regimes canonical,alias,symbol --patch-text-regimes definition,neutral --seed 20260608 --out artifacts/activation_geometry/modal_pythia_70m_deduped_answer_surface_basin.json
```

Sanity gate:

- Max absolute `source_noop` aggregate delta for `definition` patch prompts: `0.0`.
- Neutral-carrier `source_noop` is not expected to be exact, because it deliberately replaces the source definition with a minimal label-bearing patch prompt.

Decision gate:

- If `neutral` patch prompts preserve the effect, the basin is likely label-carrier driven.
- If `symbol` labels preserve the effect, the basin is likely option-surface or slot driven.
- If `alias` labels preserve the effect while `symbol` and `neutral` regimes fail, the basin depends on semantic definitions plus meaningful labels.

## Regime Summary

| Role | Label regime | Patch text | Specific passes | Mean target delta | Mean advantage |
| --- | --- | --- | ---: | ---: | ---: |
| primary | canonical | definition | 3/5 | 0.177 | 0.030 |
| primary | canonical | neutral | 0/5 | -0.025 | -0.040 |
| primary | alias | definition | 3/5 | 0.038 | 0.018 |
| primary | alias | neutral | 0/5 | -0.017 | -0.023 |
| primary | symbol | definition | 0/5 | -0.017 | -0.069 |
| primary | symbol | neutral | 1/5 | -0.013 | -0.035 |
| control | canonical | definition | 3/5 | 0.121 | 0.007 |
| control | canonical | neutral | 1/5 | -0.031 | -0.053 |
| control | alias | definition | 2/5 | -0.002 | -0.007 |
| control | alias | neutral | 1/5 | -0.043 | -0.064 |
| control | symbol | definition | 1/5 | 0.043 | 0.001 |
| control | symbol | neutral | 1/5 | 0.008 | -0.050 |

## Primary Rows

| Label | Patch text | Kind | Pair | Target delta | Best control | Advantage | Pass |
| --- | --- | --- | --- | ---: | --- | ---: | --- |
| canonical | definition | positive | `attractor` -> `attractor_network` | 0.158 | distractor | 0.090 | yes |
| canonical | definition | source family | `basin_of_attraction` -> `attractor_network` | 0.094 | distractor | -0.145 | no |
| canonical | definition | source family | `conceptual_space` -> `attractor_network` | 0.272 | random | 0.258 | yes |
| canonical | definition | source family | `prototype` -> `attractor_network` | 0.181 | distractor | 0.119 | yes |
| canonical | definition | source family | `schema` -> `attractor_network` | 0.177 | distractor | -0.172 | no |
| alias | definition | positive | `attractor` -> `attractor_network` | 0.087 | distractor | 0.048 | yes |
| alias | definition | source family | `basin_of_attraction` -> `attractor_network` | -0.007 | distractor | -0.027 | no |
| alias | definition | source family | `conceptual_space` -> `attractor_network` | 0.029 | source_noop | 0.029 | yes |
| alias | definition | source family | `prototype` -> `attractor_network` | 0.031 | random | -0.009 | no |
| alias | definition | source family | `schema` -> `attractor_network` | 0.051 | source_noop | 0.051 | yes |
| symbol | definition | positive | `attractor` -> `attractor_network` | -0.012 | distractor | -0.106 | no |
| canonical | neutral | positive | `attractor` -> `attractor_network` | -0.026 | distractor | 0.003 | no |
| alias | neutral | positive | `attractor` -> `attractor_network` | -0.138 | distractor | -0.175 | no |
| symbol | neutral | positive | `attractor` -> `attractor_network` | -0.012 | distractor | -0.004 | no |

## Interpretation

The answer-surface basin is not a trivial label-only artifact.

Two controls break the positive effect:

- Neutral label-carrier patch prompts fail. Canonical labels with neutral patch text go from `3/5` specific passes to `0/5`; aliases with neutral patch text also go to `0/5`.
- Non-semantic symbol labels fail. Definition patch prompts with symbol labels go to `0/5` primary specific passes, with negative mean advantage.

But semantic alias labels preserve part of the effect:

- Canonical definitions: `3/5` primary specific passes, mean advantage `0.030`.
- Alias definitions: `3/5` primary specific passes, mean advantage `0.018`.

So the basin seems to require both semantic definitions and meaningful answer labels. It does not survive when the patch prompt is just a label carrier, and it does not survive when the visible choices are meaningless symbols.

This still does not rescue the original clean bridge claim. The effect remains source-family broad: under canonical definitions, `prototype` and `conceptual_space` also pass into `attractor_network`; under aliases, `schema` and `conceptual_space` pass. It is also not sharply localized to layer `5`: the control layer `6` has `3/5` canonical-definition passes, though with much smaller mean advantage (`0.007`).

The best current name is:

```text
Pythia-70M-deduped has a semantically mediated attractor-family answer basin
on the multiple-choice final-token interface.
```

This is a better residual than the previous “maybe it is just labels” worry. The answer-choice surface is still involved, but it appears to be carrying semantic structure, not only option labels or slot identity.

## Next Move

Move one step away from visible answer labels:

- Train or reuse a label-free readout over final-token states for the attractor-family concepts.
- Patch definition-derived target activations into source-definition prompts without answer choices.
- Measure whether the hidden state moves toward the `attractor_network` readout class under canonical and alias-held-out definitions.
- Include layer localization, because layer `6` still shows weak basin behavior in the answer-choice interface.

If the label-free readout reproduces the source-family basin, the residual becomes a genuine activation-space basin candidate. If it disappears, the multiple-choice answer surface remains the necessary carrier.

## Discovery-Regime Audit

Question: does the attractor-family basin follow semantic source/target content, visible labels, or the option-choice surface?

Current regime:

- Artifact types: answer-surface patch payloads, label-regime rows, patch-text-regime rows, specificity summaries.
- Operations: canonical/alias/symbol relabeling, neutral-carrier patch prompts, source-family sweep, layer comparison.
- Gates/verifiers: exact definition-source no-op gate, neutral-carrier failure gate, symbol-label failure gate, alias-preservation gate.
- Known limitations: one model checkpoint, one context variant, still uses an answer-choice interface.

Action class:

- Retrieval/search/discovery: discovery-leaning verifier revision.
- Why: this adds new accepted artifact dimensions, label regimes and patch-text regimes, that the previous matched-context verifier could not represent.

Experiment:

- Manifest/report paths: this report; local ignored payload under `artifacts/activation_geometry/modal_pythia_70m_deduped_answer_surface_basin.json`.
- Positive targets: `attractor` -> `attractor_network`.
- Negative controls: neutral patch text, symbol labels, distractor/random/source patch modes.
- Stress tests: source-family sweep, canonical/alias/symbol labels, definition/neutral patch text, primary/control layer comparison.

Gate:

- Acceptance rule: call it semantically mediated only if aliases preserve the effect while neutral patch prompts and symbol labels break it.
- Withheld/rejected rule: reject label-free activation-space claims until a no-answer-choice readout test reproduces the basin.

Results:

- Accepted artifacts: this report; `experiments/activation_geometry/answer_surface_basin_diagnostic.py`; `experiments/activation_geometry/modal_answer_surface_basin.py`.
- Rejected or withheld artifacts: pure label-only artifact claim is rejected; label-free activation-space basin claim is withheld.
- Key metrics: primary canonical definitions `3/5`; primary alias definitions `3/5`; primary canonical neutral `0/5`; primary alias neutral `0/5`; primary symbol definitions `0/5`; exact definition-source no-op max delta `0.0`.
- Variance or ablation: control layer `6` has weak canonical-definition passes, so the basin is not uniquely localized to layer `5`.

Residual content:

- Explained by old regime: the multiple-choice final-token surface can carry target-margin effects.
- New content outside old claim: the effect requires semantic definitions and meaningful labels, but spreads across nearby source concepts.
- Retractions or supersessions: supersede "answer-choice label artifact" with "semantically mediated answer-surface basin."

Next move: run a label-free readout basin diagnostic to test whether the basin exists in activation space without visible answer choices.
