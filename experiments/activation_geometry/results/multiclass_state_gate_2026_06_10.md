# Multi-Class State-Gate Checkpoint

Date: 2026-06-10

## Question

Can a hidden-state gate that compares target evidence against multiple control
prototypes preserve the narrow `attractor->attractor_network` effect while
suppressing the train-variant semantic-near leak that broke the scalar state
gate?

The previous relation-control scalar gate removed controls but killed positives.
This run changes the gate type: instead of a single residualized scalar
threshold, `target_binary_*_multiclass_state_gate_opt_8` builds normalized
target and control hidden-state prototypes, then gates the delta by the target
prototype margin over the strongest control prototype.

## Implementation

New modes:

- `target_binary_multiclass_state_gate_opt_8`
- `target_binary_relation_multiclass_state_gate_opt_8`

Both keep the existing pair-specific optimized delta. The new intervention dict
uses `kind="multiclass_state_gate"` and stores:

- the optimized delta;
- one target hidden-state centroid;
- grouped control centroids;
- a target-vs-control gate threshold and temperature.

The relation variant adds relation-level control prompts from the stratified
control pairs, grouped by control class.

## Completed Run

Command:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run --name pythia70-multiclass-state-gate-trainv1 experiments/activation_geometry/modal_behavior_aligned_direction.py --model-id EleutherAI/pythia-70m-deduped --primary-layer 3 --backup-layer -1 --control-layer -1 --max-length 128 --train-variants 1 --holdout-variant 2 --scales 1.0 --direction-modes target_binary_multiclass_state_gate_opt_8,target_binary_relation_multiclass_state_gate_opt_8,target_binary_state_gate_opt_8,random_same_norm --scoring-surface binary_relation --prompt-frame source_passage --objective-label-scoring-regimes alias_0 --eval-label-scoring-regimes alias_2 --label-score-normalization mean --aliases experiments/concept_geometry/concept_aliases.json --pair-set layer3_strict_pocket_stratified_controls --seed 20260610 --out artifacts/activation_geometry/modal_pythia_70m_layer3_multiclass_state_gate_trainv1_seed20260610.json
```

Modal app:

`https://modal.com/apps/generalintelligencecompany/main/ap-AV3dpxAxB9IZX72qzyP9Cg`

Artifact:

`artifacts/activation_geometry/modal_pythia_70m_layer3_multiclass_state_gate_trainv1_seed20260610.json`

## Result

| Mode | Strict positives | Strict controls | Control-class leaks |
| --- | ---: | ---: | --- |
| `target_binary_state_gate_opt_8` | `1/2` | `1/12` | semantic-near `1/3` |
| `target_binary_multiclass_state_gate_opt_8` | `1/2` | `1/12` | semantic-near `1/3` |
| `target_binary_relation_multiclass_state_gate_opt_8` | `1/2` | `0/12` | none |
| `random_same_norm` | `0/2` | `0/12` | none |

Positive rows for the relation multi-class gate:

| Pair | Strict pass | Target delta | Target margin delta | Target over max control delta | Steered over max control | Always-false margin |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `attractor->attractor_network` | yes | `1.938` | `0.306` | `0.244` | `0.353` | `-0.352` |
| `fixed_point->prototype` | no | `0.820` | `-0.148` | `-0.235` | `-0.987` | `-2.164` |

The relation multi-class gate is the first control-aware gate that uses
relation-level controls without killing the `attractor` positive. That is a
real improvement over the scalar relation-control gate, which gave `0/2`
positives and `0/12` controls at all tested scales.

## Caveats

This is not paper-ready yet.

- It still recovers only `1/2` positives.
- The hidden-state prototype margins are tiny at training time; the mechanism
  may still be mostly soft attenuation rather than a clean semantic classifier.
- Alias and scale stress were started but intentionally stopped before artifacts
  landed so the branch could be checkpointed cleanly.

Interrupted follow-up app ids:

- scale sweep: `https://modal.com/apps/generalintelligencecompany/main/ap-zkf6l4VL8WSe9F3hujzrEx`
- alias stress: `https://modal.com/apps/generalintelligencecompany/main/ap-WQYJM9o3WEXfzgB5RU8MxB`

## Resume Commands

Scale stress:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run --name pythia70-relation-multiclass-scale experiments/activation_geometry/modal_behavior_aligned_direction.py --model-id EleutherAI/pythia-70m-deduped --primary-layer 3 --backup-layer -1 --control-layer -1 --max-length 128 --train-variants 1 --holdout-variant 2 --scales 0.75,1.0,1.25,1.5 --direction-modes target_binary_relation_multiclass_state_gate_opt_8,random_same_norm --scoring-surface binary_relation --prompt-frame source_passage --objective-label-scoring-regimes alias_0 --eval-label-scoring-regimes alias_2 --label-score-normalization mean --aliases experiments/concept_geometry/concept_aliases.json --pair-set layer3_strict_pocket_stratified_controls --seed 20260610 --out artifacts/activation_geometry/modal_pythia_70m_layer3_relation_multiclass_state_gate_scale_seed20260610.json
```

Objective-alias stress:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run --name pythia70-relation-multiclass-alias1 experiments/activation_geometry/modal_behavior_aligned_direction.py --model-id EleutherAI/pythia-70m-deduped --primary-layer 3 --backup-layer -1 --control-layer -1 --max-length 128 --train-variants 0 --holdout-variant 2 --scales 1.0 --direction-modes target_binary_relation_multiclass_state_gate_opt_8,target_binary_state_gate_opt_8,random_same_norm --scoring-surface binary_relation --prompt-frame source_passage --objective-label-scoring-regimes alias_1 --eval-label-scoring-regimes alias_2 --label-score-normalization mean --aliases experiments/concept_geometry/concept_aliases.json --pair-set layer3_strict_pocket_stratified_controls --seed 20260610 --out artifacts/activation_geometry/modal_pythia_70m_layer3_relation_multiclass_state_gate_alias1_seed20260610.json
```

## Interpretation

This upgrades the current frontier from "relation controls kill positives" to
"relation controls can be used if the gate is multi-class/prototype based." The
current paper nucleus is still narrow, but the mechanism class is no longer
obviously exhausted. The next session should finish alias and scale stress before
expanding to more models, concepts, or generation tests.
