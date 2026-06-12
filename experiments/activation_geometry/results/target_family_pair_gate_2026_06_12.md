# Target-Family Pair Gate

Date: 2026-06-12

## Question

Can an oracle-style relation-pair prototype gate separate exact target identity
from target-family overlap?

The previous held-out-control run showed that withholding `target_sharing`
controls during optimization did not remove the target-sharing leak
`phase_space->attractor_network`. This run asks whether the leak survives even
when the multi-class gate represents each relation-control pair as its own
prototype class instead of averaging controls into broad classes such as
`target_sharing`.

## Artifacts

Focused pair-gate comparison:

`artifacts/activation_geometry/modal_pythia_70m_layer3_target_family_pair_gate_alias1_seed20260610.json`

Pair-gate scale sweep:

`artifacts/activation_geometry/modal_pythia_70m_layer3_target_family_pair_gate_scale_alias1_seed20260610.json`

Modal runs:

- focused comparison:
  `https://modal.com/apps/generalintelligencecompany/main/ap-GAzuhUP1cJC3Dnc16CH9iP`
- scale sweep:
  `https://modal.com/apps/generalintelligencecompany/main/ap-g7vaOaZCBZ7Wpt6sXLCnNg`

## Configuration

- model: `EleutherAI/pythia-70m-deduped`
- primary layer: `3`
- train variant: `0`
- held-out variant: `2`
- objective labels: `alias_1`
- eval labels: `alias_2`
- scoring surface: `binary_relation`
- prompt frame: `source_passage`
- pair set: `layer3_strict_pocket_stratified_controls`

New direction mode:

- `target_binary_relation_pair_multiclass_state_gate_opt_8`

This mode uses the same optimized relation multi-class state-gate intervention
as `target_binary_relation_multiclass_state_gate_opt_8`, but changes the gate's
control prototypes:

- previous gate: `relation_control:target_sharing`
- new pair gate:
  `relation_control:target_sharing:phase_space->attractor_network`,
  `relation_control:target_sharing:schema_revision->prototype`, etc.

For the `attractor->attractor_network` row, the pair gate used `19` control
prototype groups, including a separate prototype for the known leaking row
`phase_space->attractor_network`.

## Gate

Acceptance rule:

- Preserve at least `1/2` strict positives.
- Reduce the objective-alias target-sharing leak to `0/12` controls.
- Keep `random_same_norm` at `0/2` positives and `0/12` controls.
- Prefer a nontrivial scale neighborhood rather than a single fragile point.

Rejection rule:

- Reject pair-prototype target-family disambiguation if the same target-sharing
  control passes after it has its own prototype class.

## Focused Comparison

Scale `1.0`:

| Mode | Strict positives | Strict controls | Control-class leaks | Relation grouping | Groups |
| --- | ---: | ---: | --- | --- | ---: |
| `target_binary_state_gate_opt_8` | `1/2` | `0/12` | none | n/a | n/a |
| `target_binary_relation_multiclass_state_gate_opt_8` | `1/2` | `1/12` | target-sharing `1/3` | `class` | `11` |
| `target_binary_relation_pair_multiclass_state_gate_opt_8` | `1/2` | `1/12` | target-sharing `1/3` | `pair` | `19` |
| `random_same_norm` | `0/2` | `0/12` | none | n/a | n/a |

Robustly passing rows:

| Mode | Kind | Pair | Target delta | Target-margin delta | Target over max-control delta | Steered over max-control | Always-false margin |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `target_binary_relation_multiclass_state_gate_opt_8` | positive | `attractor->attractor_network` | `2.431` | `0.420` | `0.387` | `0.660` | `-0.226` |
| `target_binary_relation_multiclass_state_gate_opt_8` | target-sharing control | `phase_space->attractor_network` | `2.202` | `0.518` | `0.444` | `0.385` | `-0.314` |
| `target_binary_relation_pair_multiclass_state_gate_opt_8` | positive | `attractor->attractor_network` | `2.445` | `0.312` | `0.311` | `0.586` | `-0.166` |
| `target_binary_relation_pair_multiclass_state_gate_opt_8` | target-sharing control | `phase_space->attractor_network` | `2.415` | `0.738` | `0.651` | `0.579` | `-0.295` |
| `target_binary_state_gate_opt_8` | positive | `attractor->attractor_network` | `2.164` | `0.345` | `0.227` | `0.308` | `-0.080` |

The pair-level gate does not attenuate the target-sharing leak. It makes the
known leaking target-sharing row stronger on several strict-margin measures.

Training-time prototype margins also show the gate is not learning a strong
separator: for the `attractor->attractor_network` row, the pair gate's
`target_over_control_max` is approximately `2.98e-7`.

## Scale Sweep

| Scale | Mode | Strict positives | Strict controls | Control-class leaks |
| ---: | --- | ---: | ---: | --- |
| `0.75` | `target_binary_relation_pair_multiclass_state_gate_opt_8` | `0/2` | `0/12` | none |
| `0.75` | `random_same_norm` | `0/2` | `0/12` | none |
| `1.0` | `target_binary_relation_pair_multiclass_state_gate_opt_8` | `1/2` | `1/12` | target-sharing `1/3` |
| `1.0` | `random_same_norm` | `0/2` | `0/12` | none |
| `1.25` | `target_binary_relation_pair_multiclass_state_gate_opt_8` | `0/2` | `2/12` | source-sharing `1/3`, target-sharing `1/3` |
| `1.25` | `random_same_norm` | `0/2` | `0/12` | none |
| `1.5` | `target_binary_relation_pair_multiclass_state_gate_opt_8` | `1/2` | `2/12` | semantic-near-null `1/3`, source-sharing `1/3` |
| `1.5` | `random_same_norm` | `0/2` | `0/12` | none |

Robustly passing pair-gate rows:

| Scale | Kind | Pair | Target delta | Target-margin delta | Target over max-control delta | Steered over max-control | Always-false margin |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `1.0` | positive | `attractor->attractor_network` | `2.429` | `0.329` | `0.325` | `0.607` | `-0.219` |
| `1.0` | target-sharing control | `phase_space->attractor_network` | `2.421` | `0.746` | `0.660` | `0.585` | `-0.295` |
| `1.25` | source-sharing control | `attractor->activation_vector` | `3.646` | `1.209` | `0.978` | `0.355` | `-0.608` |
| `1.25` | target-sharing control | `phase_space->attractor_network` | `3.183` | `1.000` | `0.895` | `0.860` | `-0.081` |
| `1.5` | positive | `fixed_point->prototype` | `2.704` | `0.545` | `0.269` | `0.011` | `-0.757` |
| `1.5` | semantic-near control | `valence->steering_vector` | `2.467` | `0.185` | `0.169` | `0.094` | `-0.199` |
| `1.5` | source-sharing control | `attractor->activation_vector` | `4.368` | `1.375` | `1.077` | `0.454` | `-0.384` |

## Interpretation

This is a stronger negative than the held-out-control result. The leak is not
removed by:

- training with target-sharing controls present,
- withholding target-sharing controls,
- or giving the target-sharing control its own prototype class.

The current hidden-state prototype gate cannot cleanly separate exact target
identity from target-family overlap under the binary-relation behavior surface.
The result is consistent with an under-identified interface: the accepted
`attractor->attractor_network` positive and the target-sharing null
`phase_space->attractor_network` share too much of the behavior-relevant
channel for this gate family.

## Decision

Reject the claim:

```text
Exact relation-pair control prototypes are sufficient to recover semantic
specificity from the relation multi-class gate.
```

Keep as evidence:

- the `target_binary_relation_pair_multiclass_state_gate_opt_8` direction mode,
- the focused pair-gate artifact,
- the scale-sweep artifact,
- the negative result that exact target-family prototypes do not create a clean
  gate.

## Next Research Move

Stop optimizing this prototype-gated binary-relation interface.

The next useful test is representational rather than interventional: train or
fit an explicit supervised readout that classifies exact relation identity
within a target family before steering. If a readout cannot distinguish
`attractor->attractor_network` from `phase_space->attractor_network` on held-out
aliases/source variants, the binary relation task is under-identified at this
layer/interface. If it can, then the failure is specifically in the additive
intervention/gate implementation rather than in the available representation.
