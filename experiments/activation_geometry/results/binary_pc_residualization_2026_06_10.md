# Binary PC Residualization - 2026-06-10

## Status

Completed a top-PC residualization/whitening probe against the low-rank
binary yes/no control surface. Raw payloads remain local-only under ignored
`artifacts/`:

```text
artifacts/activation_geometry/modal_pythia_70m_binary_pc_residualization_seed20260610.json
```

The artifact contains `119` intervention rows. It reuses the same Pythia-70M
binary-relation setup as the contrastive binary specificity run, but adds
global binary-control-PC directions built from the normalized control gradients.

## What Changed

- Added PC-adjusted binary direction modes:
  - `target_binary_pc1_resid`
  - `target_binary_pc3_resid`
  - `target_binary_pc1_whiten`
  - `target_binary_pc3_whiten`
- The PC basis is constructed once per layer/objective-label regime from all
  binary yes-bias control gradients, using the same uncentered normalized SVD
  reported in the previous geometry summary.
- Residualized modes remove the top `k` control PCs from the target binary
  gradient and rescale to the target norm.
- Whitened modes damp the top `k` control-PC coefficients by their singular
  values and rescale to the target norm.

## Gate

Rows still use the strict binary-specificity rule:

```text
target margin improves
target Yes-No margin increases
steered target Yes-No margin is positive
target delta beats the max yes-bias control delta
steered target margin beats the max steered yes-bias control margin
always-false carrier margin does not end positive
```

The table reports loose/basic behavior separately from strict behavior. Loose
behavior means the old direct binary criterion passed: target margin improves,
target Yes-No margin increases, and steered target margin is positive.

## Completed Run Summary

| Direction | Kind | Loose/basic | Strict | Mean margin delta | Mean target delta | Mean delta over control | Mean steered over control | Mean false-carrier steered |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `target_learned` | positive | 4/7 | 0/7 | 0.075 | 4.508 | -0.109 | -0.590 | 2.399 |
| `target_learned` | control | 3/10 | 0/10 | -0.043 | 4.357 | -0.149 | -0.534 | 2.330 |
| `target_binary_controls_0_5` | positive | 4/7 | 0/7 | 0.042 | 2.434 | -0.044 | -0.650 | 0.437 |
| `target_binary_controls_0_5` | control | 2/10 | 0/10 | 0.004 | 2.384 | -0.056 | -0.730 | 0.563 |
| `target_binary_pc1_resid` | positive | 0/7 | 0/7 | 0.024 | 1.012 | -0.078 | -0.463 | -2.028 |
| `target_binary_pc1_resid` | control | 0/10 | 0/10 | 0.058 | 0.887 | -0.018 | -0.232 | -1.689 |
| `target_binary_pc3_resid` | positive | 0/7 | 0/7 | -0.008 | 0.804 | -0.121 | -0.624 | -1.644 |
| `target_binary_pc3_resid` | control | 0/10 | 0/10 | 0.014 | 0.709 | -0.068 | -0.480 | -1.471 |
| `target_binary_pc1_whiten` | positive | 5/7 | 0/7 | 0.048 | 2.622 | -0.060 | -0.462 | -0.324 |
| `target_binary_pc1_whiten` | control | 2/10 | 0/10 | 0.026 | 2.239 | -0.057 | -0.243 | -0.311 |
| `target_binary_pc3_whiten` | positive | 5/7 | 0/7 | 0.048 | 2.681 | -0.064 | -0.491 | -0.163 |
| `target_binary_pc3_whiten` | control | 2/10 | 0/10 | 0.011 | 2.263 | -0.071 | -0.283 | -0.209 |
| `random_same_norm` | positive | 0/7 | 0/7 | -0.003 | -0.065 | -0.063 | -0.878 | -1.847 |
| `random_same_norm` | control | 0/10 | 0/10 | 0.023 | 0.091 | -0.056 | -1.030 | -1.412 |

## Geometry

The control-PC basis is stable with singular values:

```text
9.534, 1.480, 1.258
```

Target binary gradients are almost collinear with the first control PC:

| Slice | Mean cosine with control PC1 | PC2 | PC3 |
| --- | ---: | ---: | ---: |
| Positive pairs | 0.962 | 0.049 | -0.084 |
| Random-null controls | 0.954 | 0.034 | -0.059 |

This is the decisive mechanism check. The top binary-control PC is not merely
a nuisance direction adjacent to the target relation direction. It is where
most of the target binary movement lives.

## Interpretation

Top-PC residualization removes the false-carrier confound but also removes the
loose target behavior. PC1 residualization produces `0/7` loose positives and
`0/7` strict positives. PC3 residualization is weaker still.

Whitening is less destructive, preserving `5/7` loose positives, but it does
not recover semantic specificity. It still fails the strict gate because target
movement does not beat the strongest yes-bias control movement.

Current best interpretation:

```text
For Pythia-70M layer 5, the direct binary-relation surface is a useful
diagnostic verifier but not a route to linear semantic steering. The target
relation direction and the answer-polarity/candidate-affirmation control
direction share the same dominant low-rank axis.
```

## Reproduction Command

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_behavior_aligned_direction.py --model-id EleutherAI/pythia-70m-deduped --primary-layer 5 --backup-layer -1 --control-layer -1 --max-length 128 --train-variants 0,1 --holdout-variant 2 --scales 1.0 --direction-modes target_learned,target_binary_controls_0_5,target_binary_pc1_resid,target_binary_pc3_resid,target_binary_pc1_whiten,target_binary_pc3_whiten,random_same_norm --scoring-surface binary_relation --prompt-frame source_passage --objective-label-scoring-regimes alias_0+alias_1 --eval-label-scoring-regimes alias_2 --label-score-normalization mean --aliases experiments/concept_geometry/concept_aliases.json --pair-set expanded_random_nulls --seed 20260610 --out artifacts/activation_geometry/modal_pythia_70m_binary_pc_residualization_seed20260610.json
```

## Discovery-Regime Audit

Question: is the binary yes/no leakage low-rank enough that removing or
whitening the dominant control PCs reveals relation-specific target movement?

Current regime:

- Artifact types: binary-relation payloads, strict specificity aggregates,
  binary control-PC bases, PC-residualized and PC-whitened direction modes.
- Operations: uncentered SVD over normalized binary control gradients,
  top-PC removal, top-PC damping, target-norm restoration, held-out alias
  scoring.
- Gates/verifiers: strict binary-specificity gate plus loose/basic behavior
  retention.
- Known limitations: one model, one seed, one layer; this probes linear
  directions, not nonlinear feature interventions.

Action class:

- Retrieval/search/discovery: mechanistic falsification of the low-rank rescue
  hypothesis.
- Why: this directly tests the previous residual content: whether the dominant
  low-rank binary axis is separable nuisance structure or the same axis that
  carries target movement.

Experiment:

- Manifest/report paths:
  `experiments/activation_geometry/results/binary_pc_residualization_2026_06_10.md`;
  local ignored artifact
  `artifacts/activation_geometry/modal_pythia_70m_binary_pc_residualization_seed20260610.json`.
- Positive targets: seven expanded random-null positives.
- Negative controls: ten random relation nulls plus row-level yes-bias controls.
- Stress tests: remove or whiten top `1` and top `3` binary-control PCs.

Gate:

- Acceptance rule: a PC-adjusted direction must retain loose positive behavior
  and pass the strict yes-bias-aware gate on positives without reviving random
  null controls.
- Withheld/rejected rule: reject directions that suppress controls by
  suppressing target behavior, or keep loose behavior while failing strict
  control dominance.

Results:

- Accepted artifacts: PC-adjusted direction modes and control-PC diagnostics.
- Rejected or withheld artifacts: PC residualization/whitening as a semantic
  steering route for this model/layer.
- Key metrics: all PC modes have `0/7` strict positives. PC1 residualization
  has `0/7` loose positives; PC1/PC3 whitening keep `5/7` loose positives but
  still have negative mean target-over-control margins.
- Variance or ablation: removing PC1 is enough to erase loose target behavior;
  adding PCs does not restore specificity.

Residual content:

- Explained by old regime: binary yes/no movement is low-rank and steerable.
- New content outside old regime: the dominant low-rank control axis is also
  the dominant target movement axis, so linear PC cleanup does not expose a
  hidden semantic relation direction.
- Retractions or supersessions: supersede "try projection/whitening before
  giving up on binary steering" with "binary surface is verifier-only for
  Pythia-70M layer 5 unless a nonlinear or feature-guided intervention changes
  the mechanism."

Next move: stop optimizing this binary surface on Pythia-70M layer 5 as a
linear steering route. For paper-worthiness, either replicate the negative
mechanism on another model/layer or pivot to a nonlinear/feature-guided
intervention that is explicitly evaluated by the same strict binary verifier.
