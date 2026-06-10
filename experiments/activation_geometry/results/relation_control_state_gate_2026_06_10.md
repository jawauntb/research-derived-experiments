# Relation-Control State-Gate Probe

Date: 2026-06-10

## Question

Can a state-gated binary intervention suppress the train-variant semantic-near
leak by training the gate and delta against actual relation-level control
prompts, not only binary carrier controls?

The previous robustness probe showed:

- objective `alias_1` survived: `1/2` positives and `0/12` controls;
- train variant `1` failed: `1/2` positives and `1/12` controls;
- the failing control was `steering_vector->semantic_distance`, a
  `semantic_near_null`.

This probe adds `target_binary_relation_state_gate_opt_8`, which keeps the same
state-gated intervention but adds relation-level control prompts from other
stratified control source passages into optimization and gate calibration.

## Intervention

`target_binary_relation_state_gate_opt_8` is identical to
`target_binary_state_gate_opt_8` except for one added control source:

- for each target pair, keep the existing binary carrier controls;
- add target-label prompts from other stratified control pairs using those
  controls' own source passages;
- exclude the current pair from this extra relation-control set.

This avoids changing the baseline mode and tests whether the semantic-near leak
is due to missing relation-level controls during gate calibration.

## Gate

Acceptance rule:

- recover at least `1/2` strict positives under train variant `1`;
- keep `0/12` stratified controls;
- keep `random_same_norm` at `0/2` positives and `0/12` controls.

Rejection rule:

- `0/2` positives means relation-level controls overconstrain the intervention;
- higher scales fail if they recover positives only by reviving the always-false
  carrier or structured controls.

## Focused Train-Variant Run

Command:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run --name pythia70-relation-state-gate-trainv1 experiments/activation_geometry/modal_behavior_aligned_direction.py --model-id EleutherAI/pythia-70m-deduped --primary-layer 3 --backup-layer -1 --control-layer -1 --max-length 128 --train-variants 1 --holdout-variant 2 --scales 1.0 --direction-modes target_binary_relation_state_gate_opt_8,target_binary_state_gate_opt_8,random_same_norm --scoring-surface binary_relation --prompt-frame source_passage --objective-label-scoring-regimes alias_0 --eval-label-scoring-regimes alias_2 --label-score-normalization mean --aliases experiments/concept_geometry/concept_aliases.json --pair-set layer3_strict_pocket_stratified_controls --seed 20260610 --out artifacts/activation_geometry/modal_pythia_70m_layer3_relation_state_gate_opt8_stratified_trainv1_seed20260610.json
```

Modal app:

`https://modal.com/apps/generalintelligencecompany/main/ap-T7u8Sp3xi9LX3dFQI1cIEb`

Artifact:

`artifacts/activation_geometry/modal_pythia_70m_layer3_relation_state_gate_opt8_stratified_trainv1_seed20260610.json`

Result:

| Mode | Strict positives | Strict controls | Implausible | Semantic near | Source-sharing | Target-sharing |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `target_binary_relation_state_gate_opt_8` | `0/2` | `0/12` | `0/3` | `0/3` | `0/3` | `0/3` |
| `target_binary_state_gate_opt_8` | `1/2` | `1/12` | `0/3` | `1/3` | `0/3` | `0/3` |
| `random_same_norm` | `0/2` | `0/12` | `0/3` | `0/3` | `0/3` | `0/3` |

The original state gate again leaks:

| Kind | Class | Pair | Target delta | Target margin delta | Target over max control | Steered over max control | Always-false margin |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| positive | positive | `attractor->attractor_network` | `2.194` | `0.436` | `0.353` | `0.336` | `-0.078` |
| control | `semantic_near_null` | `steering_vector->semantic_distance` | `2.242` | `0.823` | `0.140` | `0.155` | `-0.193` |

Relation-control positive rows:

| Pair | Strict pass | Target delta | Target margin delta | Target over max control | Steered over max control | Always-false margin |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `attractor->attractor_network` | no | `1.852` | `0.210` | `0.188` | `-0.047` | `-0.037` |
| `fixed_point->prototype` | no | `0.788` | `-0.075` | `-0.149` | `-0.900` | `-2.038` |

Representative optimization summaries:

| Pair | Control prompt count | Post-rescale norm | Train target margin | Train control mean | Train control max | Gate target mean | Gate control max | Gate target over control max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `attractor->attractor_network` | `28` | `2.216` | `-0.415` | `-0.758` | `-0.042` | `0.0762` | `0.0802` | `-0.0040` |
| `fixed_point->prototype` | `28` | `2.556` | `0.725` | `-0.786` | `0.725` | `0.0499` | `0.0614` | `-0.0115` |

## Scale Sweep

Command:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run --name pythia70-relation-state-gate-trainv1-scale experiments/activation_geometry/modal_behavior_aligned_direction.py --model-id EleutherAI/pythia-70m-deduped --primary-layer 3 --backup-layer -1 --control-layer -1 --max-length 128 --train-variants 1 --holdout-variant 2 --scales 1.0,1.25,1.5 --direction-modes target_binary_relation_state_gate_opt_8,random_same_norm --scoring-surface binary_relation --prompt-frame source_passage --objective-label-scoring-regimes alias_0 --eval-label-scoring-regimes alias_2 --label-score-normalization mean --aliases experiments/concept_geometry/concept_aliases.json --pair-set layer3_strict_pocket_stratified_controls --seed 20260610 --out artifacts/activation_geometry/modal_pythia_70m_layer3_relation_state_gate_opt8_stratified_trainv1_scale_seed20260610.json
```

Modal app:

`https://modal.com/apps/generalintelligencecompany/main/ap-sLoKKWKhbnyYlr6j02dYKh`

Artifact:

`artifacts/activation_geometry/modal_pythia_70m_layer3_relation_state_gate_opt8_stratified_trainv1_scale_seed20260610.json`

Scale table:

| Scale | Relation-control positives | Relation-control controls | Random positives | Random controls |
| ---: | ---: | ---: | ---: | ---: |
| `1.0` | `0/2` | `0/12` | `0/2` | `0/12` |
| `1.25` | `0/2` | `0/12` | `0/2` | `0/12` |
| `1.5` | `0/2` | `0/12` | `0/2` | `0/12` |

Positive rows across scale:

| Scale | Pair | Strict pass | Target delta | Target margin delta | Target over max control | Steered over max control | Always-false margin |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `1.0` | `attractor->attractor_network` | no | `1.852` | `0.210` | `0.188` | `-0.047` | `-0.037` |
| `1.25` | `attractor->attractor_network` | no | `2.320` | `0.248` | `0.212` | `0.152` | `0.232` |
| `1.5` | `attractor->attractor_network` | no | `2.836` | `0.338` | `0.284` | `0.395` | `0.505` |
| `1.0` | `fixed_point->prototype` | no | `0.788` | `-0.075` | `-0.149` | `-0.900` | `-2.038` |
| `1.25` | `fixed_point->prototype` | no | `0.959` | `-0.140` | `-0.208` | `-0.958` | `-1.916` |
| `1.5` | `fixed_point->prototype` | no | `1.112` | `-0.230` | `-0.266` | `-1.016` | `-1.815` |

## Interpretation

Relation-level control prompts remove the train-variant semantic-near leak, but
they also remove all strict positives. Scaling does not rescue the result.

The `attractor` row is diagnostic:

- at scale `1.0`, the target moves and the always-false carrier remains
  negative, but the steered target is still below the strongest control;
- at scales `1.25` and `1.5`, the steered target beats controls, but the
  always-false carrier becomes positive.

So the method exposes a three-way tradeoff rather than a clean frontier:
relation-level controls suppress semantic-near leakage, target movement, and
carrier safety cannot all be satisfied by this gated additive delta.

Conclusion: `target_binary_relation_state_gate_opt_8` is a useful rejected
alternative. The next mechanism should not merely add more relation controls to
the same pair-specific additive/gated optimizer. A more promising next move is a
learned gate or verifier-coupled intervention whose gate is trained to separate
target, semantic-near, and carrier-control states as distinct classes, or a
pivot away from pair-specific binary optimization toward a shared conditional
operation.
