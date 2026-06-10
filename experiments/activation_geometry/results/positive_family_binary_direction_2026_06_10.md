# Positive-Family Binary Direction Pilot

Date: 2026-06-10

## Question

Can a single direction learned from positive bridge pairs versus stratified
controls separate semantic bridge behavior from source-sharing, target-sharing,
semantic-near, and implausible random-null controls?

## Intervention

This pilot adds `target_binary_positive_family_opt_8`.

Unlike `target_binary_strict_opt_8`, which optimizes a separate vector for every
pair, this mode optimizes one shared final-token vector per layer and objective
label regime:

- target prompts: source-to-target binary prompts for positive pairs only;
- control prompts: binary prompts for every stratified control pair, plus
  blank/generic/source/distractor/false-carrier controls on positive sources;
- norm constraint: match the mean positive target-gradient norm.

This is a stricter test of whether the layer-3 pocket contains a separable
positive-family feature rather than merely pair-specific target-label movement.

## Command

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run --name pythia70-positive-family-opt8-strata-alias0 experiments/activation_geometry/modal_behavior_aligned_direction.py --model-id EleutherAI/pythia-70m-deduped --primary-layer 3 --backup-layer -1 --control-layer -1 --max-length 128 --train-variants 0 --holdout-variant 2 --scales 1.0 --direction-modes target_binary_positive_family_opt_8,target_binary_strict_opt_8,random_same_norm --scoring-surface binary_relation --prompt-frame source_passage --objective-label-scoring-regimes alias_0 --eval-label-scoring-regimes alias_2 --label-score-normalization mean --aliases experiments/concept_geometry/concept_aliases.json --pair-set layer3_strict_pocket_stratified_controls --seed 20260610 --out artifacts/activation_geometry/modal_pythia_70m_layer3_positive_family_opt8_stratified_alias0_seed20260610.json
```

Artifact:

`artifacts/activation_geometry/modal_pythia_70m_layer3_positive_family_opt8_stratified_alias0_seed20260610.json`

## First Result

| Mode | Strict positives | Strict controls | Implausible | Semantic near | Source-sharing | Target-sharing |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `random_same_norm` | `0/2` | `0/12` | `0/3` | `0/3` | `0/3` | `0/3` |
| `target_binary_strict_opt_8` | `1/2` | `4/12` | `0/3` | `1/3` | `2/3` | `1/3` |
| `target_binary_positive_family_opt_8` | `1/2` | `0/12` | `0/3` | `0/3` | `0/3` | `0/3` |

Strict pass rows:

| Mode | Kind | Class | Pair | Target delta | Target over max control | Steered over max control | Always-false margin |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `target_binary_positive_family_opt_8` | positive | - | `attractor->attractor_network` | `2.543` | `0.249` | `0.644` | `-0.378` |
| `target_binary_strict_opt_8` | positive | - | `attractor->attractor_network` | `1.975` | `0.070` | `0.446` | `-0.674` |
| `target_binary_strict_opt_8` | control | `semantic_near_null` | `steering_vector->semantic_distance` | `2.926` | `2.063` | `1.745` | `-0.842` |
| `target_binary_strict_opt_8` | control | `source_sharing` | `attractor->semantic_distance` | `2.166` | `1.009` | `0.881` | `-0.602` |
| `target_binary_strict_opt_8` | control | `source_sharing` | `fixed_point->schema_revision` | `1.853` | `0.406` | `0.109` | `-0.869` |
| `target_binary_strict_opt_8` | control | `target_sharing` | `phase_space->attractor_network` | `2.639` | `0.721` | `0.681` | `-0.376` |

Optimization summary for `target_binary_positive_family_opt_8`:

- target prompts: `2`
- control prompts: `22`
- positive pairs: `2`
- control pairs: `12`
- target margin mean/min during optimization: `0.826` / `0.674`
- control margin mean/max during optimization: `-0.384` / `0.231`
- post-rescale norm: `2.317`

## Scale Stress Test

Command:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run --name pythia70-positive-family-opt8-strata-scale experiments/activation_geometry/modal_behavior_aligned_direction.py --model-id EleutherAI/pythia-70m-deduped --primary-layer 3 --backup-layer -1 --control-layer -1 --max-length 128 --train-variants 0 --holdout-variant 2 --scales 0.5,0.75,1.0,1.25,1.5 --direction-modes target_binary_positive_family_opt_8,random_same_norm --scoring-surface binary_relation --prompt-frame source_passage --objective-label-scoring-regimes alias_0 --eval-label-scoring-regimes alias_2 --label-score-normalization mean --aliases experiments/concept_geometry/concept_aliases.json --pair-set layer3_strict_pocket_stratified_controls --seed 20260610 --out artifacts/activation_geometry/modal_pythia_70m_layer3_positive_family_opt8_stratified_scale_seed20260610.json
```

Artifact:

`artifacts/activation_geometry/modal_pythia_70m_layer3_positive_family_opt8_stratified_scale_seed20260610.json`

| Scale | Strict positives | Strict controls | Control class leaks |
| ---: | ---: | ---: | --- |
| `0.5` | `0/2` | `0/12` | none |
| `0.75` | `0/2` | `0/12` | none |
| `1.0` | `1/2` | `0/12` | none |
| `1.25` | `1/2` | `1/12` | `target_sharing: 1/3` |
| `1.5` | `0/2` | `0/12` | none; positive fails always-false carrier |

Positive rows by scale:

| Scale | Pair | Strict pass | Target delta | Target over max control | Steered over max control | Always-false margin |
| ---: | --- | --- | ---: | ---: | ---: | ---: |
| `0.5` | `attractor->attractor_network` | no | `1.148` | `0.102` | `-0.003` | `-0.786` |
| `0.75` | `attractor->attractor_network` | no | `1.877` | `0.240` | `0.526` | `-0.586` |
| `1.0` | `attractor->attractor_network` | yes | `2.543` | `0.249` | `0.644` | `-0.378` |
| `1.25` | `attractor->attractor_network` | yes | `3.056` | `0.294` | `0.585` | `-0.148` |
| `1.5` | `attractor->attractor_network` | no | `3.465` | `0.308` | `0.582` | `0.077` |
| `0.5` | `fixed_point->prototype` | no | `0.774` | `-0.241` | `-0.849` | `-2.542` |
| `0.75` | `fixed_point->prototype` | no | `1.118` | `-0.433` | `-0.975` | `-2.462` |
| `1.0` | `fixed_point->prototype` | no | `1.395` | `-0.689` | `-1.231` | `-2.302` |
| `1.25` | `fixed_point->prototype` | no | `1.444` | `-1.068` | `-1.611` | `-2.072` |
| `1.5` | `fixed_point->prototype` | no | `1.508` | `-1.255` | `-1.797` | `-1.848` |

## Gate

This mode is interesting only if it improves the specificity frontier over the
pair-specific optimized vector:

- keep at least one strict positive;
- reduce structured control passes below `target_binary_strict_opt_8`;
- keep implausible random-null controls at zero.

If it loses positives and does not reduce structured controls, the evidence
pushes against single-vector interventions and toward nonlinear/readout-guided
or feature-selective mechanisms.

## Interpretation

This is the best specificity frontier so far under the strict binary verifier:
`1/2` positives and `0/12` stratified controls at scale `1.0`.

The improvement is mechanistically useful. Pair-specific opt8 was able to move
the same positive but leaked four structured controls. A positive-family vector
keeps the `attractor->attractor_network` movement while suppressing all
source-sharing, target-sharing, semantic-near-null, and implausible controls at
the clean scale.

This is still not paper-ready. It does not recover `fixed_point->prototype`, and
the scale sweep shows a narrow operating band: at `1.25`, a target-sharing
control revives; at `1.5`, the positive fails the always-false carrier check.

Next move: replicate this positive-family frontier across objective aliases,
train variants, and a second model/layer before expanding concepts. If it
survives, it becomes the first plausible paper nucleus: semantic specificity as
a family-level activation feature rather than a pair-specific steering vector.
