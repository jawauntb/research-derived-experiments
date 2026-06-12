# Multi-Class State-Gate Stress Test

Date: 2026-06-12

## Question

Does the relation-level multi-class prototype gate remain a clean strict-binary
semantic-specific intervention under scale and objective-alias stress?

The previous checkpoint found the first narrow case where relation-level controls
could be incorporated without killing the `attractor->attractor_network`
positive:

- train variant `1`
- objective alias `alias_0`
- held-out evaluation alias `alias_2`
- scale `1.0`
- Pythia-70M layer `3`

This stress test asks whether that result is stable enough to promote, or
whether it should remain a diagnostic boundary.

## Artifacts

Scale stress:

`artifacts/activation_geometry/modal_pythia_70m_layer3_relation_multiclass_state_gate_scale_seed20260610.json`

Objective-alias stress:

`artifacts/activation_geometry/modal_pythia_70m_layer3_relation_multiclass_state_gate_alias1_seed20260610.json`

Modal runs:

- scale stress: `https://modal.com/apps/generalintelligencecompany/main/ap-quTs38YT3Wr6gP1Qoohpj3`
- objective-alias stress: `https://modal.com/apps/generalintelligencecompany/main/ap-sOo3Yf8xet7aJXRazgodnb`

## Scale Stress

Configuration:

- model: `EleutherAI/pythia-70m-deduped`
- primary layer: `3`
- train variant: `1`
- held-out variant: `2`
- objective labels: `alias_0`
- eval labels: `alias_2`
- scoring surface: `binary_relation`
- prompt frame: `source_passage`
- pair set: `layer3_strict_pocket_stratified_controls`
- scales: `0.75`, `1.0`, `1.25`, `1.5`

| Scale | Mode | Strict positives | Strict controls | Control-class leaks |
| ---: | --- | ---: | ---: | --- |
| `0.75` | `target_binary_relation_multiclass_state_gate_opt_8` | `0/2` | `0/12` | none |
| `1.0` | `target_binary_relation_multiclass_state_gate_opt_8` | `1/2` | `0/12` | none |
| `1.25` | `target_binary_relation_multiclass_state_gate_opt_8` | `1/2` | `4/12` | semantic-near `2/3`, source-sharing `1/3`, target-sharing `1/3` |
| `1.5` | `target_binary_relation_multiclass_state_gate_opt_8` | `0/2` | `2/12` | semantic-near `1/3`, source-sharing `1/3` |
| `0.75` | `random_same_norm` | `0/2` | `0/12` | none |
| `1.0` | `random_same_norm` | `0/2` | `0/12` | none |
| `1.25` | `random_same_norm` | `0/2` | `0/12` | none |
| `1.5` | `random_same_norm` | `0/2` | `0/12` | none |

Positive rows for the relation multi-class gate:

| Scale | Pair | Strict pass | Target delta | Target margin delta | Target over max control delta | Steered over max control | Always-false margin |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `0.75` | `attractor->attractor_network` | no | `1.437` | `0.247` | `0.190` | `0.049` | `-0.547` |
| `0.75` | `fixed_point->prototype` | no | `0.626` | `-0.054` | `-0.146` | `-0.898` | `-2.273` |
| `1.0` | `attractor->attractor_network` | yes | `1.937` | `0.305` | `0.243` | `0.355` | `-0.353` |
| `1.0` | `fixed_point->prototype` | no | `0.819` | `-0.150` | `-0.243` | `-0.994` | `-2.164` |
| `1.25` | `attractor->attractor_network` | yes | `2.446` | `0.361` | `0.295` | `0.666` | `-0.156` |
| `1.25` | `fixed_point->prototype` | no | `1.011` | `-0.252` | `-0.392` | `-1.087` | `-2.054` |
| `1.5` | `attractor->attractor_network` | no | `2.952` | `0.406` | `0.329` | `0.757` | `0.043` |
| `1.5` | `fixed_point->prototype` | no | `1.194` | `-0.348` | `-0.530` | `-1.180` | `-1.944` |

Interpretation:

- Scale `0.75` is underpowered: it keeps controls clean but loses positives.
- Scale `1.0` is the only clean positive operating point.
- Scale `1.25` preserves the `attractor` positive but revives broad structured
  leakage across semantic-near, source-sharing, and target-sharing controls.
- Scale `1.5` is not a simple stronger version of scale `1.0`: it revives
  controls and flips the always-false carrier positive on the `attractor`
  positive row.

## Objective-Alias Stress

Configuration:

- model: `EleutherAI/pythia-70m-deduped`
- primary layer: `3`
- train variant: `0`
- held-out variant: `2`
- objective labels: `alias_1`
- eval labels: `alias_2`
- scoring surface: `binary_relation`
- prompt frame: `source_passage`
- pair set: `layer3_strict_pocket_stratified_controls`
- scale: `1.0`

| Mode | Strict positives | Strict controls | Control-class leaks |
| --- | ---: | ---: | --- |
| `target_binary_state_gate_opt_8` | `1/2` | `0/12` | none |
| `target_binary_relation_multiclass_state_gate_opt_8` | `1/2` | `1/12` | target-sharing `1/3` |
| `random_same_norm` | `0/2` | `0/12` | none |

Positive and leaked rows:

| Mode | Kind | Pair | Strict pass | Target delta | Target margin delta | Target over max control delta | Steered over max control | Always-false margin |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `target_binary_state_gate_opt_8` | positive | `attractor->attractor_network` | yes | `2.164` | `0.345` | `0.227` | `0.308` | `-0.080` |
| `target_binary_state_gate_opt_8` | positive | `fixed_point->prototype` | no | `1.310` | `0.167` | `-0.150` | `-0.516` | `-1.119` |
| `target_binary_relation_multiclass_state_gate_opt_8` | positive | `attractor->attractor_network` | yes | `2.431` | `0.420` | `0.387` | `0.660` | `-0.226` |
| `target_binary_relation_multiclass_state_gate_opt_8` | positive | `fixed_point->prototype` | no | `1.788` | `0.396` | `0.209` | `-0.218` | `-1.384` |
| `target_binary_relation_multiclass_state_gate_opt_8` | control | `phase_space->attractor_network` | yes | `2.202` | `0.518` | `0.444` | `0.385` | `-0.314` |

Interpretation:

- The relation multi-class gate preserves the `attractor` positive under an
  objective-alias perturbation.
- It does not preserve semantic specificity: a target-sharing null
  (`phase_space->attractor_network`) passes the same strict gate.
- The simpler scalar state gate is cleaner in this alias slice (`1/2`,
  `0/12`), so the relation multi-class gate is not a monotonic improvement.

## Decision

Withhold the relation multi-class prototype gate as a paper claim.

Accepted evidence:

- Relation-level controls are not inherently lethal; they can be represented as
  prototype classes without killing the `attractor` positive.
- The strict verifier is doing useful work: random same-norm remains clean,
  while structured source/target/semantic-near controls revive when the gate is
  over-scaled or alias-shifted.

Rejected or withheld claim:

- The current relation multi-class gate is not a stable semantic-specific
  intervention. It has a narrow scale window, only recovers `1/2` positives,
  fails objective-alias specificity through target-sharing leakage, and never
  recovers `fixed_point->prototype`.

Next research move:

Do not expand this exact gate to more models yet. The next useful mechanism
step is a stronger held-out-control objective: train the conditional gate with
disjoint target-sharing/source-sharing controls and evaluate on held-out
control classes, or pivot to a learned classifier/gate that explicitly separates
target identity from target-family and source-family overlap.
