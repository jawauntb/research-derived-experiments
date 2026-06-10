# State-Gate Robustness Probe

Date: 2026-06-10

## Question

Does the state-gated strict-binary frontier survive the smallest robustness
perturbations that rejected the previous positive-family vector: objective alias
and train prompt variant?

The prior state-gate checkpoint found a narrow clean point:

- objective `alias_0`, train variant `0`, eval `alias_2`, scale `1.0`;
- `target_binary_state_gate_opt_8`: `1/2` strict positives and `0/12`
  stratified controls;
- `random_same_norm`: `0/2` positives and `0/12` controls.

This probe keeps the same model, layer, pair set, verifier, and scale, then
changes only one perturbation at a time.

## Gate

Acceptance rule:

- preserve at least `1/2` strict positives;
- keep `0/12` stratified controls;
- keep `random_same_norm` at `0/2` positives and `0/12` controls.

Rejection rule:

- any structured control leak means the conditional frontier is not robust
  enough to become the paper nucleus;
- `fixed_point->prototype` staying negative means the result is still a
  one-pocket `attractor` phenomenon.

## Objective Alias Perturbation

Command:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run --name pythia70-state-gate-opt8-alias1 experiments/activation_geometry/modal_behavior_aligned_direction.py --model-id EleutherAI/pythia-70m-deduped --primary-layer 3 --backup-layer -1 --control-layer -1 --max-length 128 --train-variants 0 --holdout-variant 2 --scales 1.0 --direction-modes target_binary_state_gate_opt_8,random_same_norm --scoring-surface binary_relation --prompt-frame source_passage --objective-label-scoring-regimes alias_1 --eval-label-scoring-regimes alias_2 --label-score-normalization mean --aliases experiments/concept_geometry/concept_aliases.json --pair-set layer3_strict_pocket_stratified_controls --seed 20260610 --out artifacts/activation_geometry/modal_pythia_70m_layer3_state_gate_opt8_stratified_alias1_seed20260610.json
```

Modal app:

`https://modal.com/apps/generalintelligencecompany/main/ap-9idq8dWMfLUWLQMfqMxU5z`

Artifact:

`artifacts/activation_geometry/modal_pythia_70m_layer3_state_gate_opt8_stratified_alias1_seed20260610.json`

Result:

| Mode | Strict positives | Strict controls | Implausible | Semantic near | Source-sharing | Target-sharing |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `target_binary_state_gate_opt_8` | `1/2` | `0/12` | `0/3` | `0/3` | `0/3` | `0/3` |
| `random_same_norm` | `0/2` | `0/12` | `0/3` | `0/3` | `0/3` | `0/3` |

Strict pass row:

| Kind | Class | Pair | Target delta | Target margin delta | Target over max control | Steered over max control | Always-false margin |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| positive | positive | `attractor->attractor_network` | `2.210` | `0.385` | `0.305` | `0.329` | `-0.056` |

Positive rows:

| Pair | Strict pass | Target delta | Target margin delta | Target over max control | Steered over max control | Always-false margin |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `attractor->attractor_network` | yes | `2.210` | `0.385` | `0.305` | `0.329` | `-0.056` |
| `fixed_point->prototype` | no | `1.309` | `0.166` | `-0.147` | `-0.516` | `-1.123` |

Representative optimization summaries:

| Pair | Post-rescale norm | Train target margin | Train control mean | Train control max | Gate target mean | Gate control max | Gate target over control max | Gate threshold |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `attractor->attractor_network` | `2.860` | `0.077` | `-0.352` | `0.077` | `0.0764` | `0.0820` | `-0.0057` | `0.0792` |
| `fixed_point->prototype` | `2.669` | `0.018` | `-0.431` | `0.018` | `0.0196` | `0.0380` | `-0.0183` | `0.0288` |

## Train-Variant Perturbation

Command:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run --name pythia70-state-gate-opt8-trainv1 experiments/activation_geometry/modal_behavior_aligned_direction.py --model-id EleutherAI/pythia-70m-deduped --primary-layer 3 --backup-layer -1 --control-layer -1 --max-length 128 --train-variants 1 --holdout-variant 2 --scales 1.0 --direction-modes target_binary_state_gate_opt_8,random_same_norm --scoring-surface binary_relation --prompt-frame source_passage --objective-label-scoring-regimes alias_0 --eval-label-scoring-regimes alias_2 --label-score-normalization mean --aliases experiments/concept_geometry/concept_aliases.json --pair-set layer3_strict_pocket_stratified_controls --seed 20260610 --out artifacts/activation_geometry/modal_pythia_70m_layer3_state_gate_opt8_stratified_trainv1_seed20260610.json
```

Modal app:

`https://modal.com/apps/generalintelligencecompany/main/ap-8cApd2F1cjZ9yYSaJzIhAx`

Artifact:

`artifacts/activation_geometry/modal_pythia_70m_layer3_state_gate_opt8_stratified_trainv1_seed20260610.json`

Result:

| Mode | Strict positives | Strict controls | Implausible | Semantic near | Source-sharing | Target-sharing |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `target_binary_state_gate_opt_8` | `1/2` | `1/12` | `0/3` | `1/3` | `0/3` | `0/3` |
| `random_same_norm` | `0/2` | `0/12` | `0/3` | `0/3` | `0/3` | `0/3` |

Strict pass rows:

| Kind | Class | Pair | Target delta | Target margin delta | Target over max control | Steered over max control | Always-false margin |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| positive | positive | `attractor->attractor_network` | `2.203` | `0.447` | `0.366` | `0.344` | `-0.078` |
| control | `semantic_near_null` | `steering_vector->semantic_distance` | `2.240` | `0.817` | `0.136` | `0.151` | `-0.191` |

Positive rows:

| Pair | Strict pass | Target delta | Target margin delta | Target over max control | Steered over max control | Always-false margin |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `attractor->attractor_network` | yes | `2.203` | `0.447` | `0.366` | `0.344` | `-0.078` |
| `fixed_point->prototype` | no | `0.689` | `-0.072` | `-0.174` | `-0.926` | `-2.134` |

Representative optimization summaries:

| Pair | Post-rescale norm | Train target margin | Train control mean | Train control max | Gate target mean | Gate control max | Gate target over control max | Gate threshold |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `attractor->attractor_network` | `2.214` | `-0.336` | `-0.704` | `-0.161` | `0.0772` | `0.0772` | `0.0000` | `0.0772` |
| `fixed_point->prototype` | `2.556` | `0.604` | `-0.568` | `0.604` | `0.0496` | `0.0609` | `-0.0113` | `0.0553` |

## Interpretation

The result is split:

- The state-gated `attractor` pocket survives objective alias perturbation.
- The same operation fails train-variant robustness by reviving a semantic-near
  control leak: `steering_vector->semantic_distance`.
- `fixed_point->prototype` remains negative under both perturbations.
- The gate calibration caveat persists. In the alias run, target gate scores
  remain below max control scores for both positive pairs. In the train-variant
  run, the `attractor` gate is exactly tied at the target/control boundary, not
  cleanly separated.

This is more encouraging than the positive-family vector, because the alias
perturbation no longer kills the clean `attractor` pocket. But it is still not
paper-ready: the state-gated intervention does not pass the smallest
train-prompt perturbation, and the repeated semantic-near leak shows the gate is
not yet a reliable semantic-specific mechanism.

Conclusion: do not expand this state gate to larger models or more concepts yet.
The next paper-relevant move is to improve the conditional mechanism itself:
learn or calibrate a control-aware gate that explicitly suppresses
semantic-near control states, then rerun the same alias/train robustness gate.
