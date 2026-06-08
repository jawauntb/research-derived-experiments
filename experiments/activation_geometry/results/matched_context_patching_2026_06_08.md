# Matched-Context Patching Diagnostic - 2026-06-08

## Question

Did the previous causal-patching run fail because patch activations came from bare concept-definition prompts while the behavior probe used an answer-choice prompt?

This run keeps the final-token multiple-choice probe, but extracts patch activations from prompts with the same option-choice template as the patched source prompt. The `source_noop` control now patches the exact source answer-choice activation back into the same prompt.

## Method

Inputs:

- Pythia matched-context payload: `artifacts/activation_geometry/modal_pythia_70m_matched_context_patching.json`
- GPT-2 matched-context payload: `artifacts/activation_geometry/modal_gpt2_matched_context_patching.json`

All raw payloads remain local-only under ignored `artifacts/`.

Commands:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_matched_context_patching.py --model-id EleutherAI/pythia-70m-deduped --primary-layer 5 --backup-layer 6 --control-layer 1 --max-length 128 --patch-alpha 1.0 --patch-modes target,distractor,random,source_noop --option-orders std,tds,dst --seed 20260608 --out artifacts/activation_geometry/modal_pythia_70m_matched_context_patching.json
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_matched_context_patching.py --model-id gpt2 --primary-layer 12 --backup-layer 11 --control-layer 4 --max-length 128 --patch-alpha 1.0 --patch-modes target,distractor,random,source_noop --option-orders std,tds,dst --seed 20260608 --out artifacts/activation_geometry/modal_gpt2_matched_context_patching.json
```

Patch modes:

- `target`: patch with the paired target concept activation from the matched option-choice prompt.
- `distractor`: patch with the distractor concept activation from the same option-choice frame.
- `random`: patch with a deterministic random concept, preferring the target category when possible.
- `source_noop`: patch with the source concept activation from the exact same option-choice prompt.

Implementation sanity check:

- Patch activations are captured at the same transformer-block hook surface used for replacement.
- This matters because final hidden states can differ from block hook outputs at final layers due to final layernorm.
- Max absolute `source_noop` mean delta is `0.0` for both models, so the no-op control is now exact at the aggregate level.

Gate:

- A pair passes if target-patch mean target-margin delta is positive across option orders, at least two of three option orders are positive, and the target patch beats the best of `distractor`, `random`, and `source_noop`.
- A model-level bridge claim would require primary positive passes without primary valence-control leakage and with backup/cross-model support.

## Gate Summary

| Model | Role | Positive target-specific passes | Valence-control target-specific passes | Exploratory target-specific passes | Result |
| --- | --- | ---: | ---: | ---: | --- |
| Pythia-70M | Primary layer `5` | 2/3 | 1/2 | 1/1 | Model-specific pocket, leaky |
| Pythia-70M | Backup layer `6` | 1/3 | 1/2 | 1/1 | Partial backup, leaky |
| Pythia-70M | Control layer `1` | 1/3 | 0/2 | 1/1 | Control-layer warning |
| GPT-2 | Primary layer `12` | 0/3 | 0/2 | 0/1 | Reject |
| GPT-2 | Backup layer `11` | 0/3 | 0/2 | 0/1 | Reject |
| GPT-2 | Control layer `4` | 0/3 | 0/2 | 0/1 | Reject |

Result: matched context rescues a Pythia-specific causal patching pocket, but no cross-model bridge claim is accepted.

## Primary-Layer Specificity Results

Mean target-margin delta is averaged over the three option orders. `Advantage` is target patch mean minus the best control patch mean.

| Model | Pair kind | Pair | Target mean delta | Best control | Best control mean delta | Advantage | Target robust? | Specific pass? |
| --- | --- | --- | ---: | --- | ---: | ---: | --- | --- |
| Pythia-70M | Positive | `attractor` -> `attractor_network` | 0.192 | `distractor` | 0.121 | 0.071 | Yes | Yes |
| Pythia-70M | Positive | `autopoiesis` -> `homeostasis` | 0.038 | `distractor` | 0.033 | 0.005 | Yes | Yes |
| Pythia-70M | Positive | `validity_gate` -> `weak_constraint` | -0.030 | `distractor` | 0.030 | -0.061 | No | No |
| Pythia-70M | Exploratory | `conceptual_space` -> `representation_manifold` | 0.099 | `distractor` | 0.015 | 0.084 | Yes | Yes |
| Pythia-70M | Control | `valence` -> `activation_vector` | 0.107 | `distractor` | 0.101 | 0.005 | Yes | Yes |
| Pythia-70M | Control | `valence` -> `steering_vector` | 0.005 | `random` | 0.045 | -0.040 | Yes | No |
| GPT-2 | Positive | `attractor` -> `attractor_network` | -0.048 | `random` | 0.021 | -0.069 | No | No |
| GPT-2 | Positive | `autopoiesis` -> `homeostasis` | -0.041 | `source_noop` | 0.000 | -0.041 | No | No |
| GPT-2 | Positive | `validity_gate` -> `weak_constraint` | -0.016 | `source_noop` | 0.000 | -0.016 | No | No |
| GPT-2 | Exploratory | `conceptual_space` -> `representation_manifold` | -0.054 | `random` | 0.028 | -0.083 | No | No |
| GPT-2 | Control | `valence` -> `activation_vector` | -0.029 | `distractor` | 0.060 | -0.089 | No | No |
| GPT-2 | Control | `valence` -> `steering_vector` | -0.032 | `distractor` | 0.028 | -0.060 | No | No |

## Interpretation

This result changes the story.

The previous concept-definition patching run rejected direct target activation patching in both models. Matched-context patching shows that this rejection was too broad: in Pythia-70M, two positive bridge pairs and the exploratory conceptual-space pair become target-specific at the primary layer once the patch activation is taken from the same answer-choice context.

But this is not yet an accepted bridge-causality result:

- GPT-2 has `0/3` positive target-specific passes across primary, backup, and control layers.
- Pythia has primary valence-control leakage on `valence` -> `activation_vector`.
- Pythia's `autopoiesis` -> `homeostasis` primary advantage is small: `0.005`.
- Pythia also has a control-layer positive pass for `autopoiesis` -> `homeostasis`.

So the residual content is narrower and more interesting than the old failure:

```text
Context-matched target states can causally move some Pythia final-token option margins,
but this is not yet cross-model semantic bridge causality.
```

The best current hypothesis is that the answer-choice surface can use matched-context concept states in some models/layers, while concept-definition states are out-of-distribution for this intervention. The next test should not be a broad generation demo. It should replicate the Pythia pocket under stricter controls:

- alternate held-out variant or paraphrase split,
- repeated random-patch seeds,
- a nearby Pythia layer scan,
- and a third small causal LM before promotion.

## Discovery-Regime Audit

Question: does matched-context activation patching rescue final-token bridge interventions?

Current regime:

- Artifact types: selected final-token layers, matched option-choice patch prompts, target/distractor/random/source hook-surface activations, option-order randomized target-margin payloads, specificity summaries.
- Operations: answer-choice prompt construction, hook-surface activation capture, activation replacement hooks, option-order randomized log-probability margin scoring, target-vs-control patch comparison.
- Gates/verifiers: exact `source_noop` sanity control, primary/backup/control layers, valence controls, distractor/random/source patch controls, robust option-order rule, target-over-best-control specificity rule.
- Known limitations: one context variant, one random-patch seed, two small causal LMs, and no free-form or downstream behavioral task.

Action class:

- Retrieval/search/discovery: regime refinement.
- Why: the run revises the intervention artifact from bare concept-state patching to matched answer-choice context-state patching, and the no-op sanity gate exposes the need to capture patch vectors at the hook surface.

Gate:

- Acceptance rule: promote only cross-model primary positive target-specific passes without primary valence-control leakage or control-layer replication.
- Withheld/rejected rule: model-specific pockets and leaky controls are reported but not promoted to semantic bridge-causality claims.

Results:

- Accepted artifacts: this report; `experiments/activation_geometry/modal_matched_context_patching.py`; `experiments/activation_geometry/matched_context_patching.py`.
- Rejected or withheld artifacts: cross-model semantic bridge claim is rejected; Pythia-specific matched-context pocket is withheld pending replication.
- Key metrics: Pythia primary positive target-specific passes `2/3` with `1/2` valence-control leakage; GPT-2 primary positive target-specific passes `0/3`; max absolute `source_noop` aggregate delta `0.0` in both models.
- Variance or ablation: target, distractor, random, and exact source-context patch controls tested across primary, backup, and control layers with three option orders.

Residual content:

- Explained by old regime: readout-selected bridge pairs do not automatically imply cross-model causal steering.
- New content outside old regime: context matching can turn previously rejected direct patching into a Pythia-specific causal pocket.
- Retractions or supersessions: do not say final-token patching is simply dead; do not promote the Pythia pocket until it survives replication and leakage controls.

Next move: replicate the Pythia matched-context pocket across variants, random seeds, and a nearby layer scan before trying free-form generation.
