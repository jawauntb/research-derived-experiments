# State-Gated Binary Direction Probe

Date: 2026-06-10

## Question

Can a genuinely conditional final-token intervention recover strict binary target
behavior after additive free vectors, linear readout/control spans, and sparse
feature masks all failed semantic specificity?

The immediate rejected frontier was:

- `target_binary_strict_opt_8`: `1/2` strict positives and `4/12` stratified
  controls.
- `target_binary_readout_span_opt_8`: `0/2` strict positives and `1/12`
  stratified controls.
- `target_binary_feature_mask_opt_8`: `0/2` strict positives and `2/12`
  stratified controls.

This probe tests whether a hidden-state-conditioned gate can attenuate the
intervention on control-like states while preserving target movement.

## Intervention

This run adds `target_binary_state_gate_opt_8`.

For each source/target pair, it:

1. Optimizes the same strict binary relation objective as pair opt8.
2. Builds a gate direction by residualizing the target direction against source,
   distractor, and binary-control directions.
3. Captures unsteered final-token hidden states for target and control training
   prompts.
4. Sets the gate threshold halfway between the target-score mean and the maximum
   control score.
5. Applies the learned delta through a sigmoid gate at evaluation time:
   `sigmoid((cos(hidden, gate_direction) - threshold) / gate_temperature)`.

The gate temperature is `0.05`. The control directions are source, distractor,
blank carrier, generic carrier, source carrier, distractor carrier, shuffled
target, and always-false carrier.

## Gate

Acceptance rule:

- recover at least `1/2` strict positives;
- keep `0/12` stratified controls at the clean scale;
- keep `random_same_norm` at `0/2` positives and `0/12` controls.

Stress rule:

- reject a broad claim if the clean point is scale-fragile;
- reject a true state-discrimination claim if target hidden-state gate scores
  fail to separate from control scores.

## Focused Run

Command:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run --name pythia70-state-gate-opt8-strata experiments/activation_geometry/modal_behavior_aligned_direction.py --model-id EleutherAI/pythia-70m-deduped --primary-layer 3 --backup-layer -1 --control-layer -1 --max-length 128 --train-variants 0 --holdout-variant 2 --scales 1.0 --direction-modes target_binary_state_gate_opt_8,random_same_norm --scoring-surface binary_relation --prompt-frame source_passage --objective-label-scoring-regimes alias_0 --eval-label-scoring-regimes alias_2 --label-score-normalization mean --aliases experiments/concept_geometry/concept_aliases.json --pair-set layer3_strict_pocket_stratified_controls --seed 20260610 --out artifacts/activation_geometry/modal_pythia_70m_layer3_state_gate_opt8_stratified_seed20260610.json
```

Artifact:

`artifacts/activation_geometry/modal_pythia_70m_layer3_state_gate_opt8_stratified_seed20260610.json`

Result:

| Mode | Strict positives | Strict controls | Implausible | Semantic near | Source-sharing | Target-sharing |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `target_binary_state_gate_opt_8` | `1/2` | `0/12` | `0/3` | `0/3` | `0/3` | `0/3` |
| `random_same_norm` | `0/2` | `0/12` | `0/3` | `0/3` | `0/3` | `0/3` |

Strict positive row:

| Pair | Target delta | Target margin delta | Target over max control | Steered over max control | Always-false margin |
| --- | ---: | ---: | ---: | ---: | ---: |
| `attractor->attractor_network` | `2.255` | `0.526` | `0.499` | `0.381` | `-0.063` |

Positive rows:

| Pair | Strict pass | Target delta | Target margin delta | Target over max control | Steered over max control | Always-false margin |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `attractor->attractor_network` | yes | `2.255` | `0.526` | `0.499` | `0.381` | `-0.063` |
| `fixed_point->prototype` | no | `0.997` | `-0.089` | `-0.168` | `-0.858` | `-1.951` |

Representative optimization summaries:

| Pair | Post-rescale norm | Target margin mean | Control margin mean | Control margin max | Gate target mean | Gate control max | Gate target over control max | Gate threshold |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `attractor->attractor_network` | `2.496` | `0.198` | `-0.515` | `0.198` | `0.0515` | `0.0561` | `-0.0046` | `0.0538` |
| `fixed_point->prototype` | `2.303` | `0.446` | `-0.464` | `0.446` | `0.0188` | `0.0301` | `-0.0114` | `0.0245` |

## Scale Stress

Command:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run --name pythia70-state-gate-opt8-scale experiments/activation_geometry/modal_behavior_aligned_direction.py --model-id EleutherAI/pythia-70m-deduped --primary-layer 3 --backup-layer -1 --control-layer -1 --max-length 128 --train-variants 0 --holdout-variant 2 --scales 0.5,0.75,1.0,1.25,1.5 --direction-modes target_binary_state_gate_opt_8,random_same_norm --scoring-surface binary_relation --prompt-frame source_passage --objective-label-scoring-regimes alias_0 --eval-label-scoring-regimes alias_2 --label-score-normalization mean --aliases experiments/concept_geometry/concept_aliases.json --pair-set layer3_strict_pocket_stratified_controls --seed 20260610 --out artifacts/activation_geometry/modal_pythia_70m_layer3_state_gate_opt8_stratified_scale_seed20260610.json
```

Artifact:

`artifacts/activation_geometry/modal_pythia_70m_layer3_state_gate_opt8_stratified_scale_seed20260610.json`

Scale table:

| Scale | State-gate positives | State-gate controls | Control leak classes | Random positives | Random controls |
| ---: | ---: | ---: | --- | ---: | ---: |
| `0.5` | `0/2` | `0/12` | none | `0/2` | `0/12` |
| `0.75` | `0/2` | `0/12` | none | `0/2` | `0/12` |
| `1.0` | `1/2` | `0/12` | none | `0/2` | `0/12` |
| `1.25` | `0/2` | `3/12` | semantic-near `1/3`, source-sharing `1/3`, target-sharing `1/3` | `0/2` | `0/12` |
| `1.5` | `0/2` | `1/12` | source-sharing `1/3` | `0/2` | `0/12` |

Strict pass rows in the scale stress:

| Scale | Kind | Class | Pair | Target delta | Target margin delta | Target over max control | Steered over max control | Always-false margin |
| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `1.0` | positive | positive | `attractor->attractor_network` | `2.256` | `0.526` | `0.498` | `0.384` | `-0.064` |
| `1.25` | control | `semantic_near_null` | `steering_vector->semantic_distance` | `2.589` | `1.119` | `0.696` | `0.604` | `-0.039` |
| `1.25` | control | `source_sharing` | `fixed_point->schema_revision` | `1.760` | `0.358` | `0.262` | `0.008` | `-0.569` |
| `1.25` | control | `target_sharing` | `phase_space->attractor_network` | `2.362` | `0.469` | `0.370` | `0.252` | `-0.022` |
| `1.5` | control | `source_sharing` | `fixed_point->schema_revision` | `2.083` | `0.391` | `0.238` | `0.045` | `-0.221` |

Positive rows across scale:

| Scale | Pair | Strict pass | Target delta | Target margin delta | Target over max control | Steered over max control | Always-false margin |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `0.5` | `attractor->attractor_network` | no | `1.056` | `0.272` | `0.236` | `-0.262` | `-0.617` |
| `0.75` | `attractor->attractor_network` | no | `1.633` | `0.391` | `0.357` | `0.057` | `-0.360` |
| `1.0` | `attractor->attractor_network` | yes | `2.256` | `0.526` | `0.498` | `0.384` | `-0.064` |
| `1.25` | `attractor->attractor_network` | no | `2.910` | `0.677` | `0.641` | `0.683` | `0.291` |
| `1.5` | `attractor->attractor_network` | no | `3.571` | `0.831` | `0.784` | `0.954` | `0.681` |
| `0.5` | `fixed_point->prototype` | no | `0.520` | `-0.000` | `-0.037` | `-0.788` | `-2.274` |
| `0.75` | `fixed_point->prototype` | no | `0.764` | `-0.033` | `-0.067` | `-0.816` | `-2.115` |
| `1.0` | `fixed_point->prototype` | no | `1.004` | `-0.086` | `-0.164` | `-0.857` | `-1.953` |
| `1.25` | `fixed_point->prototype` | no | `1.240` | `-0.139` | `-0.254` | `-0.907` | `-1.792` |
| `1.5` | `fixed_point->prototype` | no | `1.472` | `-0.203` | `-0.372` | `-0.966` | `-1.637` |

## Interpretation

This is the first conditional intervention that reopens the clean focused
frontier: `1/2` strict positives and `0/12` stratified controls at scale `1.0`,
with random same-norm still clean.

It is not a Phase 1 pass. The result is narrow and scale-fragile:

- scales `0.5` and `0.75` lose all positives;
- scales `1.25` and `1.5` revive structured controls or the always-false
  carrier;
- `fixed_point->prototype` never recovers;
- the gate calibration is not a clean target/control classifier.

The last point matters. For both positive pairs, the target hidden-state gate
score is below the max control score (`-0.0046` and `-0.0114` target-over-control
max). So the state gate should not be described as discovering a clean hidden
state separator. The better interpretation is softer: conditional attenuation
can restore the narrow `attractor` pocket that additive variants could not keep
clean, but the current gate is not robust enough to ground a paper claim.

Conclusion: keep `target_binary_state_gate_opt_8` as a promising conditional
frontier and checkpoint it before stopping. The next stress test should perturb
objective alias and train variant for this conditional operation, and the next
mechanistic improvement should target gate calibration rather than another broad
scale sweep.
