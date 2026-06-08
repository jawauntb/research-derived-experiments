# Causal Patching Diagnostic - 2026-06-08

## Question

If additive bridge directions fail at the final-token multiple-choice probe, does direct target-concept activation patching work?

The steering calibration and gradient-alignment diagnostics left a clear fork:

- Maybe centroid directions are too weak or too linear, but full target concept states are causally useful.
- Or the final-token multiple-choice interface is the wrong behavioral surface for this bridge geometry.

This run tests the first possibility by replacing the source prompt's final-token activation with target, distractor, random, or source-concept activations at selected final-token layers.

## Method

Inputs:

- Pythia causal-patching payload: `artifacts/activation_geometry/modal_pythia_70m_causal_patching.json`
- GPT-2 causal-patching payload: `artifacts/activation_geometry/modal_gpt2_causal_patching.json`

All raw payloads remain local-only under ignored `artifacts/`.

Commands:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_causal_patching.py --model-id EleutherAI/pythia-70m-deduped --primary-layer 5 --backup-layer 6 --control-layer 1 --batch-size 8 --max-length 128 --patch-alpha 1.0 --patch-modes target,distractor,random,source_noop --option-orders std,tds,dst --seed 20260608 --out artifacts/activation_geometry/modal_pythia_70m_causal_patching.json
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_causal_patching.py --model-id gpt2 --primary-layer 12 --backup-layer 11 --control-layer 4 --batch-size 8 --max-length 128 --patch-alpha 1.0 --patch-modes target,distractor,random,source_noop --option-orders std,tds,dst --seed 20260608 --out artifacts/activation_geometry/modal_gpt2_causal_patching.json
```

Patch modes:

- `target`: patch with the held-out paired target concept activation.
- `distractor`: patch with the distractor concept activation.
- `random`: patch with a deterministic random concept, preferring the target category when available.
- `source_noop`: patch with the source concept activation. This is a source-concept patch control, not an unhooked forward pass.

Probe:

```text
source concept text

Choose the closest related concept.
A/B/C. source, target, distractor labels in randomized order
Answer:
```

Score:

```text
target margin = log p(target option) - 0.5 * (log p(source option) + log p(distractor option))
target-margin delta = patched target margin - baseline target margin
```

Pair-level target patch gate:

- Mean target-margin delta across the three option orders must be positive.
- At least two of three option orders must have positive target-margin delta.
- The target patch must beat the best control patch among `distractor`, `random`, and `source_noop`.

Model-level interpretation gate:

- Accept only if primary positive pairs show target-specific passes without valence-control passes, and the effect is not reproduced by control layers.
- Treat backup-only or control-layer-only passes as warnings, not as accepted causal bridge evidence.

## Gate Summary

| Model | Role | Positive target-specific passes | Valence-control target-specific passes | Exploratory target-specific passes | Result |
| --- | --- | ---: | ---: | ---: | --- |
| Pythia-70M | Primary layer `5` | 0/3 | 0/2 | 0/1 | Reject |
| Pythia-70M | Backup layer `6` | 0/3 | 0/2 | 0/1 | Reject |
| Pythia-70M | Control layer `1` | 0/3 | 0/2 | 1/1 | Warning |
| GPT-2 | Primary layer `12` | 0/3 | 0/2 | 0/1 | Reject |
| GPT-2 | Backup layer `11` | 1/3 | 0/2 | 0/1 | Backup-only warning |
| GPT-2 | Control layer `4` | 1/3 | 0/2 | 0/1 | Control-layer warning |

Result: no primary-layer target-specific causal patching effect is accepted in either model.

## Primary-Layer Specificity Results

Mean target-margin delta is averaged over the three option orders. `Advantage` is target patch mean minus the best control patch mean.

| Model | Pair kind | Pair | Target mean delta | Best control | Best control mean delta | Advantage | Target robust? | Specific pass? |
| --- | --- | --- | ---: | --- | ---: | ---: | --- | --- |
| Pythia-70M | Positive | `attractor` -> `attractor_network` | 0.242 | `random` | 0.263 | -0.021 | Yes | No |
| Pythia-70M | Positive | `autopoiesis` -> `homeostasis` | -0.108 | `random` | 0.034 | -0.142 | No | No |
| Pythia-70M | Positive | `validity_gate` -> `weak_constraint` | -0.132 | `random` | 0.019 | -0.151 | No | No |
| Pythia-70M | Exploratory | `conceptual_space` -> `representation_manifold` | 0.062 | `random` | 0.116 | -0.054 | Yes | No |
| Pythia-70M | Control | `valence` -> `activation_vector` | -0.106 | `distractor` | -0.089 | -0.017 | No | No |
| Pythia-70M | Control | `valence` -> `steering_vector` | 0.045 | `source_noop` | 0.230 | -0.185 | Yes | No |
| GPT-2 | Positive | `attractor` -> `attractor_network` | -0.014 | `distractor` | -0.014 | 0.000 | No | No |
| GPT-2 | Positive | `autopoiesis` -> `homeostasis` | -0.058 | `distractor` | -0.058 | 0.000 | No | No |
| GPT-2 | Positive | `validity_gate` -> `weak_constraint` | -0.015 | `distractor` | -0.015 | 0.000 | No | No |
| GPT-2 | Exploratory | `conceptual_space` -> `representation_manifold` | -0.050 | `distractor` | -0.050 | 0.000 | No | No |
| GPT-2 | Control | `valence` -> `activation_vector` | -0.005 | `distractor` | -0.005 | 0.000 | No | No |
| GPT-2 | Control | `valence` -> `steering_vector` | -0.079 | `distractor` | -0.079 | 0.000 | No | No |

The primary-layer failure is not subtle. Pythia sometimes shows positive target-patch movement, but the best control patch beats it. GPT-2 primary-layer target patches do not show a positive robust effect, and their mean effects are tied with distractor controls.

## Specific-Pass Warnings

Only three rows pass the target-specific rule anywhere:

| Model | Role | Kind | Pair | Target mean delta | Best control | Advantage |
| --- | --- | --- | --- | ---: | --- | ---: |
| Pythia-70M | Control | Exploratory | `conceptual_space` -> `representation_manifold` | 0.167 | `source_noop` | 0.027 |
| GPT-2 | Backup | Positive | `attractor` -> `attractor_network` | 0.013 | `distractor` | 0.0003 |
| GPT-2 | Control | Positive | `attractor` -> `attractor_network` | 0.075 | `distractor` | 0.007 |

These are not promoted. The GPT-2 backup-layer `attractor` pass is tiny and is accompanied by a stronger control-layer pass for the same pair. The Pythia pass occurs only for the exploratory pair on the control layer.

## Interpretation

This rejects the hypothesis that the previous additive-steering failure was merely due to using a weak linear centroid vector. Full target-concept activation patching also fails the primary-layer target-specific gate.

The emerging pattern across the intervention sequence is now sharper:

- Held-out readout geometry finds stable bridge candidates.
- Additive final-token centroid steering is unstable or non-specific.
- Prompt-local target-margin gradients are strongly causal but non-semantic.
- Full concept-state patching does not produce clean primary-layer target-specific effects.

Together, these results point away from "just search harder for a bigger final-token vector." The likely bottleneck is the final-token multiple-choice interface or the context mismatch between concept-definition activations and answer-choice prompts.

The strongest next experiment is therefore not free-form generation yet. It is a matched-context patching test:

- Build source, target, distractor, and random activations from prompts that share the same option-choice template.
- Patch those matched-context activations into the same answer-choice surface.
- Keep the same specificity gate.

If matched-context patching works, the failure was context mismatch. If it also fails, we should retire this final-token multiple-choice interface for bridge causality and pivot to readout-conditioned classifiers or downstream behavioral tasks.

## Discovery-Regime Audit

Question: does direct target-concept activation patching rescue final-token bridge interventions?

Current regime:

- Artifact types: selected final-token layers, held-out concept prompts, target/distractor/random/source patch activations, option-order randomized target-margin payloads, specificity summaries.
- Operations: final-token activation extraction, activation replacement hooks, option-order randomized log-probability margin scoring, target-vs-control patch comparison.
- Gates/verifiers: primary/backup/control layers, valence controls, distractor/random/source patch controls, robust positive option-order rule, target-over-best-control specificity rule.
- Known limitations: patch activations are extracted from concept-definition prompts, while the behavioral probe uses an option-choice prompt.

Action class:

- Retrieval/search/discovery: verifier upgrade that rejects the current behavioral interface.
- Why: the run adds full-state causal patching as a stricter intervention operation than additive centroid steering.

Gate:

- Acceptance rule: positive bridge pairs must show primary-layer target-specific passes that beat distractor, random, and source-concept patch controls without valence-control leakage or control-layer replication.
- Withheld/rejected rule: raw Modal payloads remain local-only under `artifacts/`; backup-only and control-layer-only target-specific rows are warnings.

Results:

- Accepted artifacts: this report; `experiments/activation_geometry/modal_causal_patching.py`; `experiments/activation_geometry/causal_patching_diagnostic.py`.
- Rejected or withheld artifacts: local-only Modal causal-patching payloads under `artifacts/activation_geometry/`.
- Key metrics: Pythia primary positive target-specific passes `0/3`; GPT-2 primary positive target-specific passes `0/3`.
- Variance or ablation: target, distractor, random, and source-concept patch controls tested across primary, backup, and control layers with three option orders.

Residual content:

- Explained by old regime: readout-selected bridge pairs need not become final-token answer-choice controls.
- New content outside old regime: full target activation patching fails the same primary-layer target-specific gate, suggesting the answer-choice surface or context mismatch is the likely failure source.
- Retractions or supersessions: do not treat direct concept activation patching as accepted causal bridge evidence for this probe.

Next move: run matched-context activation patching before abandoning the final-token multiple-choice interface.
