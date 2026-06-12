# Held-Out Control Conditional Gate

Date: 2026-06-12

## Question

Does relation multi-class state gating fail because it trains on the same
source-sharing or target-sharing control classes that are later evaluated?

The previous stress test found that the relation multi-class gate preserved the
`attractor->attractor_network` positive under an objective-alias perturbation,
but leaked one target-sharing control:
`phase_space->attractor_network`. This run tests whether withholding structured
control classes during optimization removes that leak.

## Artifacts

Full held-out-control run:

`artifacts/activation_geometry/modal_pythia_70m_layer3_heldout_control_conditional_gate_alias1_seed20260610.json`

Duplicate target-holdout smoke:

`artifacts/activation_geometry/modal_pythia_70m_layer3_heldout_target_conditional_gate_alias1_seed20260610.json`

Modal runs:

- full held-out-control run:
  `https://modal.com/apps/generalintelligencecompany/main/ap-AHZ80yjJG5jXuZevVQMX9p`
- duplicate target-holdout smoke:
  `https://modal.com/apps/generalintelligencecompany/main/ap-iFykvjJA82ndEu7gbMnDgy`

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
- scale: `1.0`

New direction modes:

- `target_binary_relation_multiclass_holdout_source_opt_8`: trains the
  relation multi-class state gate with `source_sharing` relation controls
  withheld.
- `target_binary_relation_multiclass_holdout_target_opt_8`: trains with
  `target_sharing` relation controls withheld.
- `target_binary_relation_multiclass_holdout_overlap_opt_8`: trains with both
  `source_sharing` and `target_sharing` relation controls withheld.

## Gate

Acceptance rule:

- Preserve at least `1/2` strict positives.
- Reduce the objective-alias target-sharing leak from `1/12` controls to
  `0/12` controls.
- Keep `random_same_norm` at `0/2` positives and `0/12` controls.

Rejection rule:

- Reject held-out-control class filtering as the next mechanism if the same
  target-sharing control passes after its class is withheld from optimization.

## Results

| Mode | Strict positives | Strict controls | Control-class leaks |
| --- | ---: | ---: | --- |
| `target_binary_state_gate_opt_8` | `1/2` | `0/12` | none |
| `target_binary_relation_multiclass_state_gate_opt_8` | `1/2` | `1/12` | target-sharing `1/3` |
| `target_binary_relation_multiclass_holdout_source_opt_8` | `1/2` | `1/12` | target-sharing `1/3` |
| `target_binary_relation_multiclass_holdout_target_opt_8` | `1/2` | `1/12` | target-sharing `1/3` |
| `target_binary_relation_multiclass_holdout_overlap_opt_8` | `1/2` | `1/12` | target-sharing `1/3` |
| `random_same_norm` | `0/2` | `0/12` | none |

Robustly passing rows:

| Mode | Kind | Pair | Target delta | Target-margin delta | Target over max-control delta | Steered over max-control | Always-false margin |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `target_binary_relation_multiclass_state_gate_opt_8` | positive | `attractor->attractor_network` | `2.431` | `0.420` | `0.387` | `0.660` | `-0.226` |
| `target_binary_relation_multiclass_state_gate_opt_8` | target-sharing control | `phase_space->attractor_network` | `2.202` | `0.518` | `0.444` | `0.385` | `-0.314` |
| `target_binary_relation_multiclass_holdout_source_opt_8` | positive | `attractor->attractor_network` | `2.492` | `0.411` | `0.324` | `0.598` | `-0.155` |
| `target_binary_relation_multiclass_holdout_source_opt_8` | target-sharing control | `phase_space->attractor_network` | `2.431` | `0.792` | `0.701` | `0.580` | `-0.280` |
| `target_binary_relation_multiclass_holdout_target_opt_8` | positive | `attractor->attractor_network` | `2.406` | `0.377` | `0.362` | `0.665` | `-0.262` |
| `target_binary_relation_multiclass_holdout_target_opt_8` | target-sharing control | `phase_space->attractor_network` | `2.183` | `0.502` | `0.431` | `0.375` | `-0.323` |
| `target_binary_relation_multiclass_holdout_overlap_opt_8` | positive | `attractor->attractor_network` | `2.521` | `0.391` | `0.370` | `0.644` | `-0.163` |
| `target_binary_relation_multiclass_holdout_overlap_opt_8` | target-sharing control | `phase_space->attractor_network` | `2.424` | `0.787` | `0.700` | `0.588` | `-0.296` |
| `target_binary_state_gate_opt_8` | positive | `attractor->attractor_network` | `2.164` | `0.345` | `0.227` | `0.308` | `-0.080` |

The target-sharing leak survives all holdout schemes, including the scheme that
withholds target-sharing controls from relation-control prompt construction.

The `fixed_point->prototype` positive remains absent for every tested
relation multi-class variant. It moves in the target direction, but does not
beat the strongest control in the final strict gate.

## Interpretation

Held-out control-class filtering does not solve the leak. The failure is not
that the gate overfits to seeing target-sharing controls during training; it is
that the recovered `attractor` behavior and the
`phase_space->attractor_network` null occupy an overlapping target-family
channel under this binary relation interface.

This turns the target-sharing leak into a stronger diagnostic. A useful next
intervention must explicitly distinguish target identity from target-family
activation, or abandon this additive/gated binary relation interface.

## Decision

Reject the claim:

```text
Withholding source-sharing or target-sharing control classes during conditional
gate optimization is sufficient to recover semantic specificity.
```

Keep as evidence:

- the new holdout-control direction modes,
- the full held-out-control Modal payload,
- the duplicate target-holdout smoke payload,
- the negative result that target-family leakage survives class withholding.

## Next Research Move

Run an oracle or learned row-conditioned target-family disambiguation gate. The
question should be: can any simple conditional verifier distinguish
`attractor->attractor_network` from target-sharing nulls such as
`phase_space->attractor_network` when the target label family is shared?

If an oracle target-family gate fails, the right pivot is away from this binary
relation classifier. If it succeeds, the next paper-worthy object is no longer a
global or pair-specific vector; it is a conditional intervention that represents
target identity and target-family overlap as separate factors.
