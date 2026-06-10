# Readout-Span Binary Direction Probe

Date: 2026-06-10

## Question

Can a pair-conditioned optimizer avoid the structured leakage of free
pair-specific vectors by restricting the intervention to a local
target/source/distractor plus binary-control direction span?

The motivation was the failure of `target_binary_strict_opt_8` on the
stratified gate:

- model: `EleutherAI/pythia-70m-deduped`
- layer: `3`
- pair set: `layer3_strict_pocket_stratified_controls`
- objective labels: `alias_0`
- evaluation labels: `alias_2`
- result: `1/2` strict positives and `4/12` stratified controls.

## Intervention

This run adds `target_binary_readout_span_opt_8`.

It uses the same strict binary prompt objective as `target_binary_strict_opt_8`,
but optimizes coefficients over an orthonormal pair-local basis instead of a
free activation delta. The basis contains:

- `target`
- `source`
- `distractor`
- `binary_control_blank`
- `binary_control_generic`
- `binary_control_source`
- `binary_control_distractor`
- `binary_control_always_false`

The final vector is norm-matched to the reference target direction.

## Gate

Acceptance rule:

- preserve at least `1/2` strict positives;
- reduce stratified control leakage relative to free pair opt8;
- keep `random_same_norm` at `0/2` positives and `0/12` controls.

Rejection rule:

- `0/2` positives means the constrained span is too conservative;
- revived controls under scale stress mean scale is not a sufficient fix.

## Comparative Run

Command:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run --name pythia70-readout-span-opt8-strata experiments/activation_geometry/modal_behavior_aligned_direction.py --model-id EleutherAI/pythia-70m-deduped --primary-layer 3 --backup-layer -1 --control-layer -1 --max-length 128 --train-variants 0 --holdout-variant 2 --scales 1.0 --direction-modes target_binary_readout_span_opt_8,target_binary_strict_opt_8,random_same_norm --scoring-surface binary_relation --prompt-frame source_passage --objective-label-scoring-regimes alias_0 --eval-label-scoring-regimes alias_2 --label-score-normalization mean --aliases experiments/concept_geometry/concept_aliases.json --pair-set layer3_strict_pocket_stratified_controls --seed 20260610 --out artifacts/activation_geometry/modal_pythia_70m_layer3_readout_span_opt8_stratified_alias0_seed20260610.json
```

Artifact:

`artifacts/activation_geometry/modal_pythia_70m_layer3_readout_span_opt8_stratified_alias0_seed20260610.json`

Result:

| Mode | Strict positives | Strict controls | Implausible | Semantic near | Source-sharing | Target-sharing |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `target_binary_strict_opt_8` | `1/2` | `4/12` | `0/3` | `1/3` | `2/3` | `1/3` |
| `target_binary_readout_span_opt_8` | `0/2` | `1/12` | `0/3` | `1/3` | `0/3` | `0/3` |
| `random_same_norm` | `0/2` | `0/12` | `0/3` | `0/3` | `0/3` | `0/3` |

Strict pass rows for `target_binary_readout_span_opt_8`:

| Kind | Class | Pair | Target delta | Target margin delta | Target over max control | Steered over max control | Always-false margin |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| control | `semantic_near_null` | `steering_vector->semantic_distance` | `2.051` | `1.443` | `1.183` | `0.996` | `-0.968` |

Positive rows for `target_binary_readout_span_opt_8`:

| Pair | Strict pass | Target delta | Target margin delta | Target over max control | Steered over max control | Always-false margin |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `attractor->attractor_network` | no | `0.848` | `-0.084` | `-0.873` | `-0.468` | `-1.066` |
| `fixed_point->prototype` | no | `1.040` | `-0.121` | `-0.504` | `-0.645` | `-1.766` |

Optimization summary for `target_binary_readout_span_opt_8`:

- parameterization: `readout_span`
- basis count: `8`
- target prompts: `1`
- control prompts: `16`
- target margin mean/min during optimization: `-0.996` / `-0.996`
- control margin mean/max during optimization: `-0.995` / `-0.607`
- post-rescale norm: `2.496`

## Scale Stress

Command:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run --name pythia70-readout-span-opt8-strata-scale experiments/activation_geometry/modal_behavior_aligned_direction.py --model-id EleutherAI/pythia-70m-deduped --primary-layer 3 --backup-layer -1 --control-layer -1 --max-length 128 --train-variants 0 --holdout-variant 2 --scales 0.5,0.75,1.0,1.25,1.5 --direction-modes target_binary_readout_span_opt_8,random_same_norm --scoring-surface binary_relation --prompt-frame source_passage --objective-label-scoring-regimes alias_0 --eval-label-scoring-regimes alias_2 --label-score-normalization mean --aliases experiments/concept_geometry/concept_aliases.json --pair-set layer3_strict_pocket_stratified_controls --seed 20260610 --out artifacts/activation_geometry/modal_pythia_70m_layer3_readout_span_opt8_stratified_scale_seed20260610.json
```

Artifact:

`artifacts/activation_geometry/modal_pythia_70m_layer3_readout_span_opt8_stratified_scale_seed20260610.json`

Result:

| Scale | Strict positives | Strict controls | Implausible | Semantic near | Source-sharing | Target-sharing |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `0.50` | `0/2` | `0/12` | `0/3` | `0/3` | `0/3` | `0/3` |
| `0.75` | `0/2` | `1/12` | `0/3` | `1/3` | `0/3` | `0/3` |
| `1.00` | `0/2` | `1/12` | `0/3` | `1/3` | `0/3` | `0/3` |
| `1.25` | `0/2` | `2/12` | `0/3` | `1/3` | `0/3` | `1/3` |
| `1.50` | `0/2` | `2/12` | `0/3` | `0/3` | `1/3` | `1/3` |

Positive rows never pass. Increasing scale raises target deltas, but it does
not make either positive beat the strict yes-bias controls:

| Scale | Pair | Target delta | Target margin delta | Target over max control | Steered over max control | Always-false margin |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `0.50` | `attractor->attractor_network` | `0.608` | `0.148` | `-0.010` | `-0.163` | `-1.165` |
| `1.00` | `attractor->attractor_network` | `1.012` | `0.132` | `-0.179` | `0.227` | `-1.169` |
| `1.50` | `attractor->attractor_network` | `1.447` | `0.175` | `0.011` | `0.417` | `-1.129` |
| `0.50` | `fixed_point->prototype` | `0.604` | `0.003` | `-0.265` | `-0.642` | `-2.224` |
| `1.00` | `fixed_point->prototype` | `1.055` | `-0.116` | `-0.503` | `-0.644` | `-1.795` |
| `1.50` | `fixed_point->prototype` | `1.390` | `-0.153` | `-0.572` | `-0.631` | `-1.421` |

## Interpretation

This is a useful negative result.

The readout/control-span constraint reduces structured leakage relative to the
free pair optimizer at scale `1.0`: `1/12` control passes instead of `4/12`,
and it eliminates the source-sharing and target-sharing leaks seen in
`target_binary_strict_opt_8`.

But it also loses all positives. The scale sweep does not recover them; it only
brings back controls at higher scale. That means the obvious local linear span
is too conservative or aligned with the wrong semantic/control axis.

The next paper-relevant move should change the intervention class, not repeat a
bigger version of this sweep. The strongest next candidate is a genuinely
nonlinear or feature-selective pair-conditioned intervention under the same
stratified strict-binary verifier.
