# Binary Pair-Optimized Intervention Pilot

Date: 2026-06-10

## Question

After the Pythia-70M layer-3 PC-whitened two-pair pocket failed to replicate in
Pythia-160M, does a pair-optimized activation vector recover semantic-specific
binary behavior under the same strict verifier?

## Intervention

This run adds a new direction family:

- `target_binary_strict_opt_8`
- `target_binary_strict_opt_16`

For each pair, the direction is a learned final-token activation vector at the
selected layer. It is optimized directly against batched binary Yes/No prompts:

- positive objective: increase the source-to-target binary relation margin;
- control penalty: suppress blank, generic, source, distractor, shuffled-target,
  always-false, and random-null target-label prompts;
- norm constraint: match the existing target binary-gradient norm.

This keeps the verifier unchanged while changing the intervention class from a
single gradient/PC projection to an explicitly behavior-optimized vector.

## Smoke Gate

Command:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run --name pythia70-strict-opt8-smoke-cw2 experiments/activation_geometry/modal_behavior_aligned_direction.py --model-id EleutherAI/pythia-70m-deduped --primary-layer 3 --backup-layer -1 --control-layer -1 --max-length 128 --train-variants 0 --holdout-variant 2 --scales 1.0 --direction-modes target_binary_strict_opt_8,target_binary_pc1_whiten,random_same_norm --scoring-surface binary_relation --prompt-frame source_passage --objective-label-scoring-regimes alias_0 --eval-label-scoring-regimes alias_2 --label-score-normalization mean --aliases experiments/concept_geometry/concept_aliases.json --pair-set layer3_strict_pocket_smoke --seed 20260610 --out artifacts/activation_geometry/modal_pythia_70m_layer3_strict_opt8_cw2_smoke_seed20260610.json
```

| Mode | Positives | Controls | Notes |
| --- | ---: | ---: | --- |
| `target_binary_strict_opt_8` | `1/1` | `0/1` | Passes `attractor->attractor_network`; rejects hard `valence->steering_vector`. |
| `target_binary_pc1_whiten` | `0/1` | `0/1` | Does not recover the positive in this alias0 smoke run. |
| `random_same_norm` | `0/1` | `0/1` | Negative control behaves as expected. |

The first optimizer attempt with weaker control weight failed this smoke gate by
making the always-false carrier positive. The accepted implementation uses
control weight `2.0`.

## Full Random-Null Pilot

Commands:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run --name pythia70-strict-opt8-full-null-alias0 experiments/activation_geometry/modal_behavior_aligned_direction.py --model-id EleutherAI/pythia-70m-deduped --primary-layer 3 --backup-layer -1 --control-layer -1 --max-length 128 --train-variants 0 --holdout-variant 2 --scales 1.0 --direction-modes target_binary_strict_opt_8,target_binary_pc1_whiten,random_same_norm --scoring-surface binary_relation --prompt-frame source_passage --objective-label-scoring-regimes alias_0 --eval-label-scoring-regimes alias_2 --label-score-normalization mean --aliases experiments/concept_geometry/concept_aliases.json --pair-set layer3_strict_pocket_random_nulls --seed 20260610 --out artifacts/activation_geometry/modal_pythia_70m_layer3_strict_opt8_fullnull_alias0_seed20260610.json
```

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run --name pythia70-strict-opt16-full-null-alias0 experiments/activation_geometry/modal_behavior_aligned_direction.py --model-id EleutherAI/pythia-70m-deduped --primary-layer 3 --backup-layer -1 --control-layer -1 --max-length 128 --train-variants 0 --holdout-variant 2 --scales 1.0 --direction-modes target_binary_strict_opt_16,target_binary_strict_opt_8,target_binary_pc1_whiten,random_same_norm --scoring-surface binary_relation --prompt-frame source_passage --objective-label-scoring-regimes alias_0 --eval-label-scoring-regimes alias_2 --label-score-normalization mean --aliases experiments/concept_geometry/concept_aliases.json --pair-set layer3_strict_pocket_random_nulls --seed 20260610 --out artifacts/activation_geometry/modal_pythia_70m_layer3_strict_opt16_fullnull_alias0_seed20260610.json
```

| Mode | Strict positives | Strict random-null controls | Frontier status |
| --- | ---: | ---: | --- |
| `random_same_norm` | `0/2` | `0/10` | Clean negative baseline. |
| `target_binary_pc1_whiten` | `0/2` | `1/10` | Worse than the earlier two-alias result under this alias0 pilot. |
| `target_binary_strict_opt_8` | `1/2` | `1/10` | Recovers one positive but leaks one random-null control. |
| `target_binary_strict_opt_16` | `1/2` | `1/10` | More optimization does not improve the aggregate gate. |

Strict survivor/leak rows:

| Mode | Row | Kind | Strict pass | Target margin delta | Target over max control | Always-false margin |
| --- | --- | --- | --- | ---: | ---: | ---: |
| `target_binary_strict_opt_8` | `attractor->attractor_network` | positive | yes | `0.297` | `0.414` | `-0.723` |
| `target_binary_strict_opt_8` | `fixed_point->prototype` | positive | no | `0.019` | `-0.619` | `-1.632` |
| `target_binary_strict_opt_8` | `regime_transition->family_resemblance` | control | yes | `0.440` | `0.297` | `-0.194` |
| `target_binary_strict_opt_16` | `attractor->attractor_network` | positive | yes | `0.728` | `0.828` | `-0.764` |
| `target_binary_strict_opt_16` | `fixed_point->prototype` | positive | no | `-0.078` | `-1.018` | `-2.549` |
| `target_binary_strict_opt_16` | `steering_vector->semantic_distance` | control | yes | `4.378` | `2.643` | `-0.118` |

## Interpretation

This is not paper-ready semantic steering.

The pair-optimized direction is a real intervention improvement over random and
PC1-whitening in the narrow smoke gate, and it consistently recovers
`attractor->attractor_network`. But the full random-null gate still fails:
optimizing the vector also finds at least one random-null row that can satisfy
the strict binary verifier.

The failure is informative. The bottleneck is no longer only the low-rank
Yes/No carrier direction. The current random-null set contains relation pairs
that the model can make semantically plausible under direct optimization,
especially:

- `regime_transition->family_resemblance`
- `steering_vector->semantic_distance`

The next verifier improvement should stratify controls by target/source overlap
and semantic plausibility, rather than treating every random relation null as an
equally valid hard negative.

## Discovery-Regime Status

Action class: search with a new operation.

Accepted artifact:

- pair-optimized strict-binary direction mode;
- smoke-gate pass on one positive plus hard control.

Rejected artifact:

- pair-optimized single-vector intervention as a completed semantic-specific
  mechanism.

Residual content:

- direct behavior optimization can recover target behavior that PC1-whitening
  misses;
- single-vector optimization still leaks into plausible random-null controls;
- broad sweeps will need batching/caching improvements because the current
  optimized direction is much slower than gradient/PC modes.

Next move:

- stratify controls into implausible random nulls, semantically near nulls,
  target-sharing controls, and source-sharing controls;
- rerun the optimized direction against those strata;
- only then test the robust two-variant, two-alias objective.
