# Steering Calibration Diagnostic - 2026-06-08

## Question

Can the failed final-token steering pilot be rescued by calibrating direction sign, direction norm, and option order?

The previous steering pilot rejected raw target-minus-source directions because the promoted bridge pairs did not cleanly move next-token target margins. This diagnostic tests whether that was merely a sign/order artifact or whether the final-token multiple-choice intervention is still underidentified.

## Method

Inputs:

- Pythia calibration payload: `artifacts/activation_geometry/modal_pythia_70m_steering_calibration.json`
- GPT-2 calibration payload: `artifacts/activation_geometry/modal_gpt2_steering_calibration.json`

All raw calibration payloads remain local-only under ignored `artifacts/`.

Commands:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_steering_calibration.py --model-id EleutherAI/pythia-70m-deduped --primary-layer 5 --backup-layer 6 --control-layer 1 --batch-size 8 --max-length 128 --scale 1.0 --direction-modes raw_target_minus_source,raw_source_minus_target,unit_target_minus_source,random_same_norm --option-orders std,tds,dst --seed 20260608 --out artifacts/activation_geometry/modal_pythia_70m_steering_calibration.json
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_steering_calibration.py --model-id gpt2 --primary-layer 12 --backup-layer 11 --control-layer 4 --batch-size 8 --max-length 128 --scale 1.0 --direction-modes raw_target_minus_source,raw_source_minus_target,unit_target_minus_source,random_same_norm --option-orders std,tds,dst --seed 20260608 --out artifacts/activation_geometry/modal_gpt2_steering_calibration.json
```

Calibration grid:

- Direction modes: raw target-minus-source, raw source-minus-target, unit target-minus-source, random same-norm.
- Option orders: source/target/distractor, target/distractor/source, distractor/source/target.
- Held-out prompt: source concept paraphrase variant `2`.
- Direction construction: train variants `0` and `1`.
- Metric: target-option log-probability margin against both source and distractor options.

Pair-level robust-pass rule:

- Mean target-margin delta across option orders must be positive.
- At least two of three option orders must have positive target-margin delta.

Model-level acceptance gate:

- At least two of three positive bridge pairs must robust-pass in the primary layer.
- At least two of three positive bridge pairs must robust-pass in the backup layer.
- No primary-layer valence controls may robust-pass.
- No control-layer positive set may show the same pattern.
- A direction mode should replicate across both models before being promoted.

## Gate Summary

| Model | Direction mode | Primary positives | Backup positives | Control-layer positives | Primary valence controls | Result |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Pythia-70M | `raw_target_minus_source` | 0/3 | 2/3 | 1/3 | 1/2 | Reject |
| Pythia-70M | `raw_source_minus_target` | 1/3 | 0/3 | 1/3 | 0/2 | Reject |
| Pythia-70M | `unit_target_minus_source` | 1/3 | 2/3 | 1/3 | 1/2 | Reject |
| Pythia-70M | `random_same_norm` | 0/3 | 1/3 | 2/3 | 0/2 | Reject |
| GPT-2 | `raw_target_minus_source` | 2/3 | 1/3 | 0/3 | 0/2 | Reject |
| GPT-2 | `raw_source_minus_target` | 0/3 | 0/3 | 0/3 | 2/2 | Reject |
| GPT-2 | `unit_target_minus_source` | 2/3 | 2/3 | 2/3 | 0/2 | Reject |
| GPT-2 | `random_same_norm` | 0/3 | 1/3 | 0/3 | 1/2 | Reject |

Result: no direction mode passes the preregistered calibration gate.

## Primary-Layer Pair Results

Mean target-margin delta is averaged over the three option orders.

| Model | Pair | Random | Raw source-target | Raw target-source | Unit target-source |
| --- | --- | ---: | ---: | ---: | ---: |
| Pythia-70M | `attractor` -> `attractor_network` | -0.259 | -0.048 | -0.027 | 0.012 |
| Pythia-70M | `autopoiesis` -> `homeostasis` | -0.612 | 0.070 | 0.021 | -0.010 |
| Pythia-70M | `validity_gate` -> `weak_constraint` | -0.665 | -0.014 | 0.008 | -0.001 |
| GPT-2 | `attractor` -> `attractor_network` | -0.083 | -0.000 | 0.000 | -0.000 |
| GPT-2 | `autopoiesis` -> `homeostasis` | -0.072 | -0.002 | 0.002 | 0.000 |
| GPT-2 | `validity_gate` -> `weak_constraint` | -0.057 | -0.000 | 0.000 | 0.000 |

## Interpretation

This diagnostic rejects the simple calibration rescue.

GPT-2 gives the most tempting partial result: `raw_target_minus_source` passes two of three primary positive bridge pairs and has no primary valence-control passes or control-layer positive passes. But it fails the backup-layer requirement, and Pythia does not replicate it at all. `unit_target_minus_source` looks better for GPT-2 primary and backup layers, but it also lights up two of three GPT-2 control-layer positives and one Pythia valence control, so it is not specific enough.

Pythia is a stronger rejection. None of the direction modes pass even two of three primary positive bridge pairs. The backup layer sometimes responds, but the control and valence behavior is active enough that the effect cannot be interpreted as clean bridge steering.

The random same-norm direction is also informative. It is not consistently useful for primary positives, but it produces robust passes in some control or exploratory settings. That says the multiple-choice margin probe is sensitive to intervention energy, layer, and option geometry, not only to semantic bridge direction.

The upshot: raw final-token bridge directions, sign flips, unit normalization, and fixed-scale random controls are insufficient. The readout geometry still looks useful as a candidate selector, but this intervention form does not yet identify a causal steering direction.

## Next Move

Do not run free-form generation yet. Redesign the steering verifier before expanding:

- Learn or select directions using a held-out readout objective rather than raw centroid differences.
- Add per-pair null prompts where source, target, and distractor are semantically unrelated but option-token geometry is preserved.
- Treat option-order robustness as mandatory, not a secondary diagnostic.
- Run a magnitude sweep only after a direction passes the specificity gate at a small scale.
- Consider causal patching or logit-lens/readout-conditioned probes before another additive final-token steering run.

## Discovery-Regime Audit

Question: can steering calibration turn promoted bridge readouts into reliable final-token interventions?

Current regime:

- Artifact types: selected final-token layers, held-out concept prompts, source-target activation directions, direction-mode calibration payloads, option-order randomized next-token margin probes.
- Operations: final-token activation extraction, direction sign/normalization variants, same-norm random direction controls, transformer-block forward hooks, option-order randomized log-probability margin scoring.
- Gates/verifiers: primary/backup/control layers, valence controls, random direction controls, option-order robust-pass rule, cross-model replication.
- Known limitations: one fixed intervention scale, centroid directions only, multiple-choice next-token probe rather than free-form generation, no learned direction objective.

Action class:

- Retrieval/search/discovery: verifier upgrade that rejects the current steering operation.
- Why: this run adds option-order and random-direction controls that the previous steering pilot could not represent, and it clarifies that the current intervention is underidentified.

Gate:

- Acceptance rule: a direction mode must pass at least two of three positive bridge pairs in primary and backup layers, pass no primary valence controls, avoid control-layer replication, and replicate across models.
- Withheld/rejected rule: raw Modal payloads remain local-only under `artifacts/`; partial primary-layer effects are recorded but not promoted.

Results:

- Accepted artifacts: this report; `experiments/activation_geometry/modal_steering_calibration.py`; `experiments/activation_geometry/steering_calibration_diagnostic.py`.
- Rejected or withheld artifacts: local-only Modal calibration payloads.
- Key metrics: Pythia primary positive pass count never exceeds `1/3`; GPT-2 `raw_target_minus_source` reaches `2/3` primary positives with `0/2` valence controls but fails backup replication; GPT-2 `unit_target_minus_source` reaches `2/3` primary and backup positives but also `2/3` control-layer positives.
- Variance or ablation: direction sign, unit normalization, same-norm random directions, and three option orders tested.

Residual content:

- Explained by old regime: readout-selected bridge pairs can create plausible but non-specific next-token margin shifts.
- New content outside old regime: option-order and random-direction controls show that the current final-token additive intervention is too underidentified for causal claims.
- Retractions or supersessions: do not treat sign-flipped or unit-normalized centroid directions as accepted steering directions.

Next move: redesign the intervention verifier around learned/readout-conditioned directions or causal patching before any free-form generation run.
