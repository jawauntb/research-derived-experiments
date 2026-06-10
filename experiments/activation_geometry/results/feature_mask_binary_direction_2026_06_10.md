# Feature-Mask Binary Direction Probe

Date: 2026-06-10

## Question

Can sparse feature selection recover strict binary target behavior after the
linear readout/control-span constraint reduced leakage but killed all positives?

The previous rejected frontier was:

- `target_binary_strict_opt_8`: `1/2` strict positives and `4/12` stratified
  controls.
- `target_binary_readout_span_opt_8`: `0/2` strict positives and `1/12`
  stratified controls.

This probe tests whether selecting target-dominant coordinates before
optimization can retain target movement while cutting the shared control/Yes
axis.

## Intervention

This run adds `target_binary_feature_mask_opt_8`.

For each source/target pair, it:

1. Computes a coordinate score:
   `abs(target_direction) - max(abs(source/distractor/control_directions))`.
2. Keeps the top `15%` coordinates by that score.
3. Optimizes the strict binary relation objective only inside that sparse mask.
4. Norm-matches the final masked vector to the target direction.

The mask controls are `source`, `distractor`, and the binary carrier-control
directions: blank, generic, source, distractor, shuffled target, and
always-false.

## Gate

Acceptance rule:

- recover at least `1/2` strict positives;
- keep fewer stratified control leaks than free pair opt8;
- keep `random_same_norm` at `0/2` positives and `0/12` controls.

Rejection rule:

- `0/2` positives means sparse feature selection does not recover the pocket;
- structured control leaks mean the selected coordinates still carry the
  source/target/control axis.

## Run

Command:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run --name pythia70-feature-mask-opt8-smoke experiments/activation_geometry/modal_behavior_aligned_direction.py --model-id EleutherAI/pythia-70m-deduped --primary-layer 3 --backup-layer -1 --control-layer -1 --max-length 128 --train-variants 0 --holdout-variant 2 --scales 1.0 --direction-modes target_binary_feature_mask_opt_8,random_same_norm --scoring-surface binary_relation --prompt-frame source_passage --objective-label-scoring-regimes alias_0 --eval-label-scoring-regimes alias_2 --label-score-normalization mean --aliases experiments/concept_geometry/concept_aliases.json --pair-set layer3_strict_pocket_stratified_controls --seed 20260610 --out artifacts/activation_geometry/modal_pythia_70m_layer3_feature_mask_opt8_stratified_smoke_seed20260610.json
```

Artifact:

`artifacts/activation_geometry/modal_pythia_70m_layer3_feature_mask_opt8_stratified_smoke_seed20260610.json`

Result:

| Mode | Strict positives | Strict controls | Implausible | Semantic near | Source-sharing | Target-sharing |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `target_binary_feature_mask_opt_8` | `0/2` | `2/12` | `0/3` | `1/3` | `1/3` | `0/3` |
| `random_same_norm` | `0/2` | `0/12` | `0/3` | `0/3` | `0/3` | `0/3` |

Strict pass rows for `target_binary_feature_mask_opt_8`:

| Kind | Class | Pair | Target delta | Target margin delta | Target over max control | Steered over max control | Always-false margin |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| control | `semantic_near_null` | `steering_vector->semantic_distance` | `2.292` | `1.124` | `0.649` | `0.451` | `-0.182` |
| control | `source_sharing` | `attractor->semantic_distance` | `1.951` | `0.818` | `0.491` | `0.129` | `-0.064` |

Positive rows:

| Pair | Strict pass | Target delta | Target margin delta | Target over max control | Steered over max control | Always-false margin |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `attractor->attractor_network` | no | `1.864` | `-0.121` | `-0.279` | `-0.116` | `0.045` |
| `fixed_point->prototype` | no | `1.018` | `-0.093` | `-0.194` | `-0.790` | `-1.824` |

Representative mask summary:

| Field | Value |
| --- | ---: |
| mask count | `77` |
| mask density | `0.1504` |
| positive score coordinates | `75` |
| selected score mean | `0.0207` |
| selected score min | `-0.0012` |
| all-coordinate score mean | `-0.0474` |
| all-coordinate score max | `0.0723` |

## Interpretation

This is another useful negative result.

Sparse coordinate selection does not recover the target pocket. It produces
strong target-logprob deltas, but those deltas do not beat the strict binary
controls on either positive row. It also revives the same structured leakage
classes the verifier was designed to catch: one semantic-near leak and one
source-sharing leak.

The mask diagnostic is informative: only `75` of `512` coordinates have a
positive target-minus-control score, and the selected-score minimum is already
slightly negative at a `15%` mask. That suggests the target/control separation is
not cleanly coordinate-sparse in this representation.

Conclusion: additive vector variants are now increasingly well-pruned. Free
vectors leak, linear readout/control spans suppress positives, and sparse
feature masks leak without recovering positives. The next intervention should
be genuinely conditional or non-additive, for example a prompt-conditioned gate,
a learned nonlinear readout intervention, or causal patching of an identified
feature circuit rather than another single final-token additive vector.
