# Steering Gradient-Alignment Diagnostic - 2026-06-08

## Question

Are final-token bridge centroid directions aligned with the local causal direction that increases the target option's next-token margin?

The calibration diagnostic showed that sign flips, unit normalization, and option-order randomization do not rescue raw final-token bridge steering. This run adds a sharper verifier: compute the exact gradient of the target-option margin with respect to the final-token activation at the intervention layer, then compare that gradient to the source-target centroid direction.

## Method

Inputs:

- Pythia gradient-alignment payload: `artifacts/activation_geometry/modal_pythia_70m_steering_gradient_alignment.json`
- GPT-2 gradient-alignment payload: `artifacts/activation_geometry/modal_gpt2_steering_gradient_alignment.json`

All raw payloads remain local-only under ignored `artifacts/`.

Commands:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_steering_gradient_alignment.py --model-id EleutherAI/pythia-70m-deduped --primary-layer 5 --backup-layer 6 --control-layer 1 --batch-size 8 --max-length 128 --scale 1.0 --direction-modes centroid,gradient_same_norm,gradient_unit,random_same_norm --option-orders std,tds,dst --seed 20260608 --out artifacts/activation_geometry/modal_pythia_70m_steering_gradient_alignment.json
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_steering_gradient_alignment.py --model-id gpt2 --primary-layer 12 --backup-layer 11 --control-layer 4 --batch-size 8 --max-length 128 --scale 1.0 --direction-modes centroid,gradient_same_norm,gradient_unit,random_same_norm --option-orders std,tds,dst --seed 20260608 --out artifacts/activation_geometry/modal_gpt2_steering_gradient_alignment.json
```

Direction modes:

- `centroid`: train-variant target centroid minus source centroid, matching the prior steering direction.
- `gradient_same_norm`: target-margin gradient normalized to the centroid norm.
- `gradient_unit`: unit target-margin gradient.
- `random_same_norm`: random direction normalized to the centroid norm.

Gradient objective:

```text
log p(target option) - 0.5 * (log p(source option) + log p(distractor option))
```

The gradient is prompt-local and option-order-local. It is therefore a diagnostic control direction, not a semantic steering direction.

Pair-level robust-pass rule:

- Mean target-margin delta across option orders must be positive.
- At least two of three option orders must have positive target-margin delta.

Model-level interpretation gate:

- A semantic steering direction would need primary and backup positive passes without primary valence-control passes or control-layer replication.
- A gradient control is expected to move the target margin, but it is only semantically useful if it does not also light up valence controls and control layers.
- The centroid-gradient cosine should be materially positive if the representational bridge vector is locally aligned with the output-control direction.

## Gate Summary

| Model | Direction mode | Primary positives | Backup positives | Control-layer positives | Primary valence controls | Result |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Pythia-70M | `centroid` | 0/3 | 2/3 | 1/3 | 1/2 | Reject |
| Pythia-70M | `gradient_same_norm` | 3/3 | 3/3 | 3/3 | 2/2 | Nonspecific control |
| Pythia-70M | `gradient_unit` | 3/3 | 3/3 | 3/3 | 2/2 | Nonspecific control |
| Pythia-70M | `random_same_norm` | 0/3 | 1/3 | 2/3 | 0/2 | Reject |
| GPT-2 | `centroid` | 2/3 | 1/3 | 0/3 | 0/2 | Reject |
| GPT-2 | `gradient_same_norm` | 3/3 | 3/3 | 3/3 | 2/2 | Nonspecific control |
| GPT-2 | `gradient_unit` | 3/3 | 3/3 | 3/3 | 2/2 | Nonspecific control |
| GPT-2 | `random_same_norm` | 0/3 | 1/3 | 0/3 | 1/2 | Reject |

Result: no semantic steering direction is accepted. The gradient directions are powerful but nonspecific controls.

## Alignment Summary

Mean centroid-gradient cosine by model, role, and pair kind:

| Model | Role | Positive pairs | Valence controls | Exploratory |
| --- | --- | ---: | ---: | ---: |
| Pythia-70M | Primary | 0.004070 | 0.002178 | -0.010932 |
| Pythia-70M | Backup | -0.000987 | 0.000604 | 0.000714 |
| Pythia-70M | Control | 0.005462 | -0.013628 | -0.011030 |
| GPT-2 | Primary | 0.000151 | -0.000173 | -0.000238 |
| GPT-2 | Backup | 0.000675 | -0.000238 | 0.000005 |
| GPT-2 | Control | -0.005095 | -0.006206 | 0.011320 |

The primary positive centroid-gradient cosine is effectively zero in both models: `0.004070` for Pythia-70M and `0.000151` for GPT-2. This is the central finding.

## Primary-Layer Pair Results

Mean target-margin delta is averaged over the three option orders.

| Model | Pair | Centroid delta | Gradient same-norm delta | Gradient unit delta | Random same-norm delta | Mean cosine |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Pythia-70M | `attractor` -> `attractor_network` | -0.027 | 11.661 | 1.803 | -0.258 | 0.01049 |
| Pythia-70M | `autopoiesis` -> `homeostasis` | 0.022 | 7.457 | 1.718 | -0.612 | 0.00223 |
| Pythia-70M | `validity_gate` -> `weak_constraint` | 0.008 | 9.386 | 1.766 | -0.665 | -0.00051 |
| GPT-2 | `attractor` -> `attractor_network` | 0.000 | 5.185 | 0.142 | -0.083 | -0.00009 |
| GPT-2 | `autopoiesis` -> `homeostasis` | 0.002 | 5.018 | 0.140 | -0.072 | 0.00037 |
| GPT-2 | `validity_gate` -> `weak_constraint` | 0.000 | 1.898 | 0.143 | -0.057 | 0.00018 |

Primary valence controls also pass under both gradient modes:

| Model | Control pair | Gradient same-norm delta | Gradient unit delta | Mean cosine |
| --- | --- | ---: | ---: | ---: |
| Pythia-70M | `valence` -> `activation_vector` | 13.339 | 1.775 | -0.00312 |
| Pythia-70M | `valence` -> `steering_vector` | 11.815 | 1.742 | 0.00748 |
| GPT-2 | `valence` -> `activation_vector` | 3.752 | 0.150 | -0.00016 |
| GPT-2 | `valence` -> `steering_vector` | 2.836 | 0.148 | -0.00018 |

## Interpretation

This is a stronger finding than the previous failed calibration.

The next-token option-margin probe is locally controllable: the exact gradient direction robustly raises the target margin in both models, both primary layers, both backup layers, and control layers. But it is not specific. It also robustly raises target margins for valence controls and control-layer positives. So gradient steering is an output-token control, not evidence of semantic bridge steering.

The bridge centroid directions are almost orthogonal to those local output-control gradients. The cross-model primary positive mean cosines are near zero, and the pair-level cosines remain tiny even when centroid interventions occasionally pass the robust-pass rule. That explains the earlier failure: the readout-selected representational axis is not the same object as the local next-token causal axis.

This sharpens the research picture:

- Activation geometry can select stable representational bridge candidates.
- The multiple-choice next-token interface is controllable.
- But the representational bridge direction and the next-token control gradient are different axes.

So the next regime should not be "try larger centroid steering." It should test whether bridge information is causally usable through patching, readout-conditioned classifiers, or downstream tasks that do not collapse the claim into an answer-token gradient.

## Next Move

Run a causal patching diagnostic instead of another additive centroid steering run:

- Replace or interpolate the source prompt's final-token activation with the paired target prompt's final-token activation.
- Compare target patch, distractor patch, random same-category patch, and same-source no-op patch.
- Keep option-order randomization.
- Measure whether patching target concept activations shifts target margins more than distractor or random patches.

If direct target activation patching also fails, the multiple-choice prompt is likely the wrong behavioral interface for this geometry. If patching works but centroid vectors do not, we should search for a nonlinear or subspace intervention rather than a single additive direction.

## Discovery-Regime Audit

Question: are bridge centroid directions aligned with the local output-margin gradient used by the final-token multiple-choice steering probe?

Current regime:

- Artifact types: selected final-token layers, held-out concept prompts, source-target centroid directions, prompt-local output-margin gradients, option-order randomized intervention payloads, centroid-gradient alignment summaries.
- Operations: final-token activation extraction, output-margin gradient capture via activation leaf hook, same-norm gradient and random controls, transformer-block forward hooks, option-order randomized log-probability margin scoring.
- Gates/verifiers: primary/backup/control layers, valence controls, random same-norm controls, option-order robust-pass rule, centroid-gradient cosine, cross-model replication.
- Known limitations: gradients are prompt-local and option-token-local; this is still a multiple-choice next-token probe, not free-form behavior.

Action class:

- Retrieval/search/discovery: verifier transition.
- Why: the run adds a new causal-alignment artifact, `centroid-gradient cosine`, and distinguishes representational readout axes from output-control axes.

Gate:

- Acceptance rule: a semantic steering direction would need primary and backup positive passes without primary valence-control passes or control-layer replication, plus materially positive centroid-gradient alignment.
- Withheld/rejected rule: raw Modal payloads remain local-only under `artifacts/`; gradient directions are treated as nonspecific controls unless they clear specificity gates.

Results:

- Accepted artifacts: this report; `experiments/activation_geometry/modal_steering_gradient_alignment.py`; `experiments/activation_geometry/steering_gradient_alignment.py`.
- Rejected or withheld artifacts: local-only Modal gradient-alignment payloads under `artifacts/activation_geometry/`.
- Key metrics: primary positive centroid-gradient cosine is `0.004070` for Pythia-70M and `0.000151` for GPT-2; gradient directions pass `3/3` primary positives but also `2/2` primary valence controls and `3/3` control-layer positives in both models.
- Variance or ablation: centroid, gradient same-norm, gradient unit, random same-norm, and three option orders tested across both models.

Residual content:

- Explained by old regime: readout-selected centroid directions can be stable representational axes without being local causal output-control axes.
- New content outside old regime: bridge centroids are near-orthogonal to prompt-local target-margin gradients across two models, suggesting a separation between representation geometry and the next-token option-control interface.
- Retractions or supersessions: do not use the current multiple-choice gradient as semantic steering evidence; do not expect larger centroid scale alone to solve the causal mismatch.

Next move: test causal patching from target concept activations before searching for larger or more complex additive steering vectors.
