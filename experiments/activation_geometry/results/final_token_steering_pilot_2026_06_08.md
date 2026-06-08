# Final-Token Steering Pilot - 2026-06-08

## Question

Do the cross-model promoted bridge directions from the readout diagnostics produce targeted next-token shifts when injected at selected final-token generation layers?

This is the first activation intervention in this track. It is intentionally small: rather than generate free-form text, it scores a multiple-choice next-token probe so the signed intervention can be measured directly.

## Method

Inputs:

- Pythia steering payload: `artifacts/activation_geometry/modal_pythia_70m_final_token_steering.json`
- GPT-2 steering payload: `artifacts/activation_geometry/modal_gpt2_final_token_steering.json`

All raw steering payloads remain local-only under ignored `artifacts/`.

Commands:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_final_token_steering.py --model-id EleutherAI/pythia-70m-deduped --primary-layer 5 --backup-layer 6 --control-layer 1 --batch-size 8 --max-length 128 --scales 0.5,1.0 --out artifacts/activation_geometry/modal_pythia_70m_final_token_steering.json
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_final_token_steering.py --model-id gpt2 --primary-layer 12 --backup-layer 11 --control-layer 4 --batch-size 8 --max-length 128 --scales 0.5,1.0 --out artifacts/activation_geometry/modal_gpt2_final_token_steering.json
```

Steering procedure:

- Compute a raw final-token activation direction at the selected layer from train variants `0` and `1`: target centroid minus source centroid.
- Hold out source variant `2`.
- Build a next-token multiple-choice prompt with source as option `A`, target as option `B`, and a same-target-category distractor as option `C`.
- Inject `+scale * direction` or `-scale * direction` at the held-out prompt's final token and selected layer.
- Score the target option's log-probability margin against source and distractor options.

Signed-margin gate for each pair:

- `+direction` must increase the target margin relative to baseline.
- `-direction` must decrease the target margin relative to baseline.

Model-level acceptance gate:

- At scale `1.0`, at least two of three positive bridge pairs must pass in the primary layer.
- The backup layer must show the same qualitative sign for at least two of three positive bridge pairs.
- No primary-layer valence control may pass.
- Control layers must not show the same pattern.

## Gate Summary

| Model | Scale | Primary positives | Backup positives | Control-layer positives | Primary valence controls |
| --- | ---: | ---: | ---: | ---: | ---: |
| Pythia-70M | 0.5 | 0/3 | 0/3 | 1/3 | 2/2 |
| Pythia-70M | 1.0 | 0/3 | 0/3 | 1/3 | 2/2 |
| GPT-2 | 0.5 | 1/3 | 1/3 | 1/3 | 1/2 |
| GPT-2 | 1.0 | 1/3 | 1/3 | 1/3 | 1/2 |

Result: rejected as a clean steering result.

## Scale 1.0 Pair Results

`forward` is the target-margin change under `+direction`; `reverse` is the target-margin change under `-direction`.

| Model | Role | Pair | Forward | Reverse | Pass |
| --- | --- | --- | ---: | ---: | --- |
| Pythia-70M | Primary | `attractor` -> `attractor_network` | -1.100 | 0.863 | No |
| Pythia-70M | Primary | `autopoiesis` -> `homeostasis` | -0.208 | 0.515 | No |
| Pythia-70M | Primary | `validity_gate` -> `weak_constraint` | -0.124 | 0.143 | No |
| Pythia-70M | Primary control | `valence` -> `activation_vector` | 0.192 | -0.015 | Yes |
| Pythia-70M | Primary control | `valence` -> `steering_vector` | 0.544 | -0.369 | Yes |
| GPT-2 | Primary | `attractor` -> `attractor_network` | -0.050 | 0.057 | No |
| GPT-2 | Primary | `autopoiesis` -> `homeostasis` | -0.025 | 0.027 | No |
| GPT-2 | Primary | `validity_gate` -> `weak_constraint` | 0.039 | -0.039 | Yes |
| GPT-2 | Primary control | `valence` -> `activation_vector` | -0.014 | 0.018 | No |
| GPT-2 | Primary control | `valence` -> `steering_vector` | 0.051 | -0.050 | Yes |

Exploratory pair:

| Model | Role | Pair | Forward | Reverse | Pass |
| --- | --- | --- | ---: | ---: | --- |
| Pythia-70M | Backup | `conceptual_space` -> `representation_manifold` | 0.749 | -0.654 | Yes |
| GPT-2 | Primary | `conceptual_space` -> `representation_manifold` | 0.070 | -0.072 | Yes |
| GPT-2 | Backup | `conceptual_space` -> `representation_manifold` | 0.402 | -0.237 | Yes |

## Interpretation

The first final-token steering pilot fails the preregistered causal gate.

The important failure mode is directional: for Pythia, all three promoted positive directions move the target option the wrong way in both primary and backup layers. GPT-2 is less severe, but only `validity_gate` -> `weak_constraint` passes among the three promoted pairs, and the same pair also passes in the GPT-2 control layer. Meanwhile, at least one valence control passes in each model's primary layer.

So the readout result does not yet transport into a clean next-token intervention. The simplest explanation is that a raw target-minus-source representational direction is not automatically a causal direction for this multiple-choice logit probe. The result also warns that the probe itself may be sensitive to option/prompt geometry and valence-like directions.

The exploratory `conceptual_space` -> `representation_manifold` pair is interesting: it passes in GPT-2 primary and backup layers and Pythia backup, despite being demoted by the stricter readout controls. That makes it a useful calibration case, not a promoted causal result.

## Next Move

Do not scale up generation yet. Run a steering calibration diagnostic first:

- Compare raw, normalized, mean-centered, and sign-flipped directions.
- Randomize option order so target-option movement is not tied to fixed option `B`.
- Add random same-norm direction controls and source-target swapped directions.
- Evaluate whether a direction's sign can be predicted from held-out linear readout or must be calibrated against the output probe.

## Discovery-Regime Audit

Question: do promoted final-token bridge directions causally shift target next-token choice margins?

Current regime:

- Artifact types: selected final-token layers, held-out concept prompts, source-target activation directions, signed intervention payloads, next-token option-margin probes.
- Operations: final-token activation extraction, raw target-minus-source direction construction, transformer-block forward hooks, signed log-probability margin scoring.
- Gates/verifiers: primary/backup/control layers, valence controls, signed reverse intervention, scale ablation.
- Known limitations: fixed option order, raw uncentered directions only, next-token multiple-choice probe rather than free-form generation, no random direction controls yet.

Action class:

- Retrieval/search/discovery: discovery attempt that failed gate.
- Why: this is the first accepted operation that moves from readout geometry to a direct activation intervention, but it does not produce an accepted steering artifact.

Gate:

- Acceptance rule: at scale `1.0`, at least two positive pairs pass in primary and backup layers, no primary valence controls pass, and control layers do not show the same pattern.
- Withheld/rejected rule: raw steering payloads stay local-only under `artifacts/`; failed steering effects are reported as rejected rather than promoted.

Results:

- Accepted artifacts: this report; `experiments/activation_geometry/modal_final_token_steering.py`; `experiments/activation_geometry/final_token_steering_pilot.py`.
- Rejected or withheld artifacts: local-only Modal steering payloads.
- Key metrics: Pythia primary layer `5` positive pass `0/3`, valence control pass `2/2`; GPT-2 primary layer `12` positive pass `1/3`, valence control pass `1/2`.
- Variance or ablation: effects are stable across scales `0.5` and `1.0`; Pythia promoted positive directions are consistently opposite-signed for the next-token probe.

Residual content:

- Explained by old regime: readout geometry can select plausible directions but does not guarantee causal control.
- New content outside old regime: raw bridge directions can be systematically wrong-signed or non-specific when hooked into final-token generation layers.
- Retractions or supersessions: do not claim the promoted readout pairs are steering directions without calibration.

Next move: implement a steering calibration diagnostic before any free-form generation run.
