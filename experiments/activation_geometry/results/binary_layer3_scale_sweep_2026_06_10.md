# Binary Layer-3 Scale Sweep - 2026-06-10

## Status

Completed a focused scale sweep around the Pythia-70M layer-3 PC1-whitening
pocket. Raw payloads remain local-only under ignored `artifacts/`:

```text
artifacts/activation_geometry/modal_pythia_70m_layer3_pc1_whiten_scale_sweep_seed20260610.json
```

The artifact contains `170` intervention rows. An earlier broader
three-layer/three-scale sweep was stopped before producing an artifact because
it was oversized for this iteration; it is non-evidence.

## Why This Run

The layer-3 replication found a small strict pocket under
`target_binary_pc1_whiten`: `2/7` strict positives and `0/10` strict controls at
scale `1.0`. This run asks whether scale calibration can expand that pocket
without reviving random-null controls.

## Completed Run Summary

| Direction | Scale | Kind | Loose/basic | Strict | Mean margin delta | Mean target delta | Mean delta over control | Mean steered over control | Mean false-carrier steered |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `target_binary_pc1_whiten` | 0.5 | positive | 0/7 | 0/7 | 0.224 | 1.438 | 0.039 | -0.280 | -1.172 |
| `target_binary_pc1_whiten` | 0.5 | control | 0/10 | 0/10 | 0.019 | 1.210 | -0.097 | -0.353 | -1.168 |
| `target_binary_pc1_whiten` | 0.75 | positive | 3/7 | 1/7 | 0.252 | 1.948 | 0.052 | -0.203 | -0.930 |
| `target_binary_pc1_whiten` | 0.75 | control | 0/10 | 0/10 | 0.012 | 1.628 | -0.135 | -0.287 | -1.035 |
| `target_binary_pc1_whiten` | 1.0 | positive | 3/7 | 2/7 | 0.297 | 2.415 | 0.108 | -0.107 | -0.694 |
| `target_binary_pc1_whiten` | 1.0 | control | 0/10 | 0/10 | -0.008 | 1.936 | -0.173 | -0.233 | -0.924 |
| `target_binary_pc1_whiten` | 1.25 | positive | 4/7 | 3/7 | 0.309 | 2.801 | 0.116 | -0.055 | -0.484 |
| `target_binary_pc1_whiten` | 1.25 | control | 2/10 | 1/10 | -0.006 | 2.205 | -0.200 | -0.208 | -0.817 |
| `target_binary_pc1_whiten` | 1.5 | positive | 6/7 | 2/7 | 0.314 | 3.153 | 0.103 | -0.046 | -0.300 |
| `target_binary_pc1_whiten` | 1.5 | control | 3/10 | 1/10 | -0.009 | 2.423 | -0.223 | -0.182 | -0.700 |
| `random_same_norm` | 0.5 | positive | 0/7 | 0/7 | -0.036 | -0.086 | -0.110 | -0.933 | -1.752 |
| `random_same_norm` | 0.5 | control | 0/10 | 0/10 | -0.000 | -0.041 | -0.075 | -1.057 | -1.510 |
| `random_same_norm` | 0.75 | positive | 0/7 | 0/7 | -0.038 | -0.069 | -0.163 | -0.934 | -1.750 |
| `random_same_norm` | 0.75 | control | 0/10 | 0/10 | 0.040 | -0.004 | -0.105 | -1.056 | -1.479 |
| `random_same_norm` | 1.0 | positive | 0/7 | 0/7 | -0.013 | -0.114 | -0.191 | -0.794 | -1.972 |
| `random_same_norm` | 1.0 | control | 0/10 | 0/10 | 0.011 | 0.034 | -0.159 | -1.137 | -1.374 |
| `random_same_norm` | 1.25 | positive | 0/7 | 0/7 | -0.035 | -0.035 | -0.157 | -0.833 | -1.851 |
| `random_same_norm` | 1.25 | control | 0/10 | 0/10 | 0.026 | 0.073 | -0.201 | -0.905 | -1.516 |
| `random_same_norm` | 1.5 | positive | 0/7 | 0/7 | 0.096 | 0.162 | -0.182 | -0.809 | -1.631 |
| `random_same_norm` | 1.5 | control | 0/10 | 0/10 | 0.022 | 0.043 | -0.165 | -0.947 | -1.538 |

## Strict Pair Curve

| Scale | Strict positive pairs | Strict control pairs |
| ---: | --- | --- |
| 0.5 | none | none |
| 0.75 | `attractor->attractor_network` | none |
| 1.0 | `attractor->attractor_network`, `fixed_point->prototype` | none |
| 1.25 | `attractor->attractor_network`, `basin_of_attraction->schema`, `fixed_point->prototype` | `steering_vector->semantic_distance` |
| 1.5 | `basin_of_attraction->schema`, `fixed_point->prototype` | `steering_vector->semantic_distance` |

## Geometry

The layer-3 geometry matches the previous layer-3 replication:

| Direction set | Count | Mean pairwise cosine | First PC energy | First 3 PCs energy | Top singular values |
| --- | ---: | ---: | ---: | ---: | --- |
| Target gradients | 17 | 0.805 | 0.818 | 0.878 | 3.730, 0.771, 0.651, 0.597, 0.536 |
| Yes-bias control gradients | 102 | 0.787 | 0.790 | 0.854 | 8.976, 1.978, 1.607, 1.386, 1.183 |
| Target + controls | 119 | 0.788 | 0.791 | 0.851 | 9.704, 2.045, 1.716, 1.503, 1.249 |
| Always-false gradients | 17 | 0.917 | 0.922 | 0.956 | 3.960, 0.585, 0.481, 0.413, 0.364 |

## Interpretation

The layer-3 PC1-whitening pocket has a scale tradeoff:

- lower scales suppress controls but have too few strict positives;
- scale `1.0` is the cleanest point (`2/7` positives, `0/10` controls);
- scale `1.25` reaches `3/7` positives but starts admitting a strict random-null
  control;
- scale `1.5` increases loose positives but keeps the control leak.

Current best interpretation:

```text
Layer 3 contains a small controlled binary-relation pocket, but scale tuning
does not turn it into a stable semantic-specific steering result. The pocket is
pair-specific and sits near the random-null leakage boundary.
```

## Reproduction Command

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_behavior_aligned_direction.py --model-id EleutherAI/pythia-70m-deduped --primary-layer 3 --backup-layer -1 --control-layer -1 --max-length 128 --train-variants 0,1 --holdout-variant 2 --scales 0.5,0.75,1.0,1.25,1.5 --direction-modes target_binary_pc1_whiten,random_same_norm --scoring-surface binary_relation --prompt-frame source_passage --objective-label-scoring-regimes alias_0+alias_1 --eval-label-scoring-regimes alias_2 --label-score-normalization mean --aliases experiments/concept_geometry/concept_aliases.json --pair-set expanded_random_nulls --seed 20260610 --out artifacts/activation_geometry/modal_pythia_70m_layer3_pc1_whiten_scale_sweep_seed20260610.json
```

## Discovery-Regime Audit

Question: can scale calibration expand the layer-3 PC1-whitening pocket without
reviving random-null controls?

Current regime:

- Artifact types: scale-specific binary-relation payloads, strict pair curves,
  geometry summaries, rejected scale frontier.
- Operations: sweep intervention scale for the best layer-3 PC-whitened mode.
- Gates/verifiers: strict binary-specificity pass counts for positives and
  random-null controls.
- Known limitations: same model, same seed, same layer; no second-model
  evidence yet.

Action class:

- Retrieval/search/discovery: scale-frontier search inside an already discovered
  weak pocket.
- Why: this tests whether the layer-3 pocket can be made broad enough for the
  Phase 1 paper gate by calibration alone.

Experiment:

- Manifest/report paths:
  `experiments/activation_geometry/results/binary_layer3_scale_sweep_2026_06_10.md`;
  local ignored artifact
  `artifacts/activation_geometry/modal_pythia_70m_layer3_pc1_whiten_scale_sweep_seed20260610.json`.
- Positive targets: seven expanded random-null positives.
- Negative controls: ten random relation nulls plus row-level yes-bias controls.
- Stress tests: scales `0.5`, `0.75`, `1.0`, `1.25`, and `1.5`.

Gate:

- Acceptance rule: broaden strict positive passes while preserving `0/10`
  strict random-null controls.
- Withheld/rejected rule: reject scale settings that gain positives only by
  admitting random-null controls.

Results:

- Accepted artifacts: scale frontier and strict pair curve.
- Rejected or withheld artifacts: scale tuning alone as a completed semantic
  specificity solution.
- Key metrics: best clean scale is `1.0` with `2/7` strict positives and `0/10`
  controls. Scale `1.25` reaches `3/7` positives but admits `1/10` controls.
- Variance or ablation: random same-norm remains `0/7` positives and `0/10`
  controls at every scale.

Residual content:

- Explained by old regime: the layer-3 pocket is weak and pair-specific.
- New content outside old regime: `attractor->attractor_network` and
  `fixed_point->prototype` are stable controlled positives around scale `1.0`;
  `basin_of_attraction->schema` appears only when controls begin to leak.
- Retractions or supersessions: supersede "scale sweep may make layer 3
  paper-ready" with "scale sweep maps a real but too-small specificity
  frontier."

Next move: either replicate the two stable layer-3 strict positives across a
second seed/model, or pivot to a pair-focused/nonlinear intervention. A broad
paper claim still needs more than a two-pair pocket.
