# Stratified Binary Control Gate

Date: 2026-06-10

## Question

After pair-optimized strict-binary directions leaked random relation controls,
are those failures concentrated in semantically near-null controls, or do they
also appear in controls that only share the source, only share the target, or
should be implausible random nulls?

## Verifier Change

This checkpoint adds two pair sets:

- `layer3_strict_pocket_stratified_controls`
- `expanded_stratified_controls`

The layer-3 strict-pocket set keeps the two previously stable positives:

- `attractor->attractor_network`
- `fixed_point->prototype`

It then splits controls into four classes:

| Class | Purpose |
| --- | --- |
| `source_sharing` | Same source concept as a positive, wrong target. Tests source-conditioned leakage. |
| `target_sharing` | Same target concept as a positive, wrong source. Tests target-label leakage. |
| `implausible_random_null` | Cross-domain controls expected to be weak negatives. |
| `semantic_near_null` | Plausible or previously leaked controls that should be treated as hard negatives, not interchangeable random nulls. |

Gate summaries now report `primary_control_pass_count_by_class` and
`primary_control_total_by_class`, so future runs can separate "bad negative"
failures from broad leakage.

## First Run

Command:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run --name pythia70-strict-opt8-strata-alias0 experiments/activation_geometry/modal_behavior_aligned_direction.py --model-id EleutherAI/pythia-70m-deduped --primary-layer 3 --backup-layer -1 --control-layer -1 --max-length 128 --train-variants 0 --holdout-variant 2 --scales 1.0 --direction-modes target_binary_strict_opt_8,target_binary_pc1_whiten,random_same_norm --scoring-surface binary_relation --prompt-frame source_passage --objective-label-scoring-regimes alias_0 --eval-label-scoring-regimes alias_2 --label-score-normalization mean --aliases experiments/concept_geometry/concept_aliases.json --pair-set layer3_strict_pocket_stratified_controls --seed 20260610 --out artifacts/activation_geometry/modal_pythia_70m_layer3_strict_opt8_stratified_alias0_seed20260610.json
```

Artifact:

`artifacts/activation_geometry/modal_pythia_70m_layer3_strict_opt8_stratified_alias0_seed20260610.json`

## Results

| Mode | Strict positives | Strict controls | Implausible | Semantic near | Source-sharing | Target-sharing |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `random_same_norm` | `0/2` | `0/12` | `0/3` | `0/3` | `0/3` | `0/3` |
| `target_binary_pc1_whiten` | `0/2` | `4/12` | `0/3` | `2/3` | `1/3` | `1/3` |
| `target_binary_strict_opt_8` | `1/2` | `4/12` | `0/3` | `1/3` | `2/3` | `1/3` |

Strict pass rows:

| Mode | Kind | Class | Pair | Target delta | Target over max control | Steered over max control | Always-false margin |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `target_binary_strict_opt_8` | positive | - | `attractor->attractor_network` | `1.975` | `0.070` | `0.446` | `-0.674` |
| `target_binary_strict_opt_8` | control | `semantic_near_null` | `steering_vector->semantic_distance` | `2.926` | `2.063` | `1.745` | `-0.842` |
| `target_binary_strict_opt_8` | control | `source_sharing` | `attractor->semantic_distance` | `2.166` | `1.009` | `0.881` | `-0.602` |
| `target_binary_strict_opt_8` | control | `source_sharing` | `fixed_point->schema_revision` | `1.853` | `0.406` | `0.109` | `-0.869` |
| `target_binary_strict_opt_8` | control | `target_sharing` | `phase_space->attractor_network` | `2.639` | `0.721` | `0.681` | `-0.376` |
| `target_binary_pc1_whiten` | control | `semantic_near_null` | `steering_vector->semantic_distance` | `2.124` | `0.210` | `0.225` | `-0.563` |
| `target_binary_pc1_whiten` | control | `semantic_near_null` | `valence->steering_vector` | `2.343` | `0.054` | `0.099` | `-0.435` |
| `target_binary_pc1_whiten` | control | `source_sharing` | `attractor->semantic_distance` | `2.227` | `0.210` | `0.687` | `-0.347` |
| `target_binary_pc1_whiten` | control | `target_sharing` | `phase_space->attractor_network` | `2.569` | `0.329` | `0.294` | `-0.539` |

## Interpretation

The stratification turns the previous pooled failure into a sharper mechanism
diagnosis.

The good news: implausible random-null controls stay clean for every tested
direction. The strict verifier is not simply accepting arbitrary unrelated
relations.

The bad news: leakage is not confined to semantically near-null controls.
`target_binary_strict_opt_8` leaks two source-sharing controls and one
target-sharing control, in addition to one semantic-near-null control. This
means pair-optimized single vectors are still exploiting structured source and
target overlap channels, not only relation plausibility.

The strongest accepted positive remains `attractor->attractor_network`, but its
strict margin over the strongest control is thin (`0.070`) compared with several
control leaks. This makes it a fragile pocket rather than a publishable semantic
specificity result.

## Acceptance Rule

The best current pair-optimized direction would become more interpretable if:

- positives remain nonzero under strict binary scoring;
- implausible random-null controls stay at `0` strict passes;
- source-sharing and target-sharing controls reveal whether leakage is source-
  or target-driven;
- semantic-near-null controls absorb most leakage.

If leakage appears across all strata, the next step should stop adding linear or
single-vector objectives and move to a nonlinear or feature-guided intervention.

Result: leakage does not appear across all strata, but it does appear across
multiple structured strata. The next intervention should therefore condition on
the source-target pair jointly, or use feature/readout-guided control rather
than a single global final-token vector.
