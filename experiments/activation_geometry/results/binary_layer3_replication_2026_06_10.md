# Binary Layer-3 Replication - 2026-06-10

## Status

Completed a same-model layer replication of the binary PC residualization probe
on Pythia-70M layer `3`. Raw payloads remain local-only under ignored
`artifacts/`:

```text
artifacts/activation_geometry/modal_pythia_70m_layer3_binary_pc_residualization_seed20260610.json
```

The artifact contains `119` intervention rows using the same strict
binary-relation verifier, held-out alias split, random-null pair set, and
direction modes as the layer-5 PC run.

## Why This Run

Layer 5 showed that the dominant binary-control PC is almost the target
movement axis. This run asks whether that failure is specific to layer 5 or
whether the binary yes/no verifier remains dominated by the same entanglement
earlier in the residual stream.

## Completed Run Summary

| Direction | Kind | Loose/basic | Strict | Mean margin delta | Mean target delta | Mean delta over control | Mean steered over control | Mean false-carrier steered |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `target_learned` | positive | 6/7 | 0/7 | 0.193 | 4.190 | -0.301 | -0.631 | 2.292 |
| `target_learned` | control | 3/10 | 0/10 | -0.050 | 4.104 | -0.279 | -0.689 | 2.239 |
| `target_binary_controls_0_5` | positive | 4/7 | 0/7 | 0.205 | 2.637 | -0.113 | -0.603 | 0.711 |
| `target_binary_controls_0_5` | control | 3/10 | 0/10 | -0.011 | 2.469 | -0.156 | -0.723 | 0.656 |
| `target_binary_pc1_resid` | positive | 0/7 | 0/7 | 0.285 | 1.305 | 0.095 | -0.077 | -2.121 |
| `target_binary_pc1_resid` | control | 0/10 | 0/10 | 0.000 | 0.986 | -0.186 | -0.201 | -2.151 |
| `target_binary_pc3_resid` | positive | 0/7 | 0/7 | 0.261 | 1.212 | 0.015 | -0.275 | -1.479 |
| `target_binary_pc3_resid` | control | 0/10 | 0/10 | 0.013 | 0.933 | -0.139 | -0.372 | -1.487 |
| `target_binary_pc1_whiten` | positive | 3/7 | 2/7 | 0.299 | 2.414 | 0.110 | -0.106 | -0.695 |
| `target_binary_pc1_whiten` | control | 0/10 | 0/10 | -0.009 | 1.938 | -0.173 | -0.235 | -0.924 |
| `target_binary_pc3_whiten` | positive | 3/7 | 1/7 | 0.303 | 2.449 | 0.068 | -0.184 | -0.351 |
| `target_binary_pc3_whiten` | control | 1/10 | 0/10 | -0.001 | 1.993 | -0.165 | -0.314 | -0.580 |
| `random_same_norm` | positive | 0/7 | 0/7 | -0.045 | -0.047 | -0.293 | -0.929 | -1.718 |
| `random_same_norm` | control | 0/10 | 0/10 | -0.043 | 0.044 | -0.181 | -1.132 | -1.346 |

## Geometry

Layer 3 is still low-rank, but less collapsed than layer 5:

| Direction set | Count | Mean pairwise cosine | First PC energy | First 3 PCs energy | Top singular values |
| --- | ---: | ---: | ---: | ---: | --- |
| Target gradients | 17 | 0.805 | 0.819 | 0.878 | 3.730, 0.770, 0.651, 0.596, 0.536 |
| Yes-bias control gradients | 102 | 0.787 | 0.790 | 0.854 | 8.976, 1.978, 1.607, 1.386, 1.183 |
| Target + controls | 119 | 0.788 | 0.791 | 0.851 | 9.704, 2.045, 1.716, 1.503, 1.249 |
| Always-false gradients | 17 | 0.917 | 0.922 | 0.956 | 3.960, 0.584, 0.481, 0.412, 0.364 |

Target gradients are still strongly aligned with control PC1, but less
completely than layer 5:

| Slice | Mean cosine with control PC1 | PC2 | PC3 |
| --- | ---: | ---: | ---: |
| Positive pairs | 0.905 | -0.090 | 0.080 |
| Random-null controls | 0.881 | -0.120 | 0.026 |

## Strict Positive Pockets

`target_binary_pc1_whiten` produced strict positives for:

- `attractor->attractor_network`
- `fixed_point->prototype`

`target_binary_pc3_whiten` produced a strict positive for:

- `fixed_point->prototype`

The strict positives did not revive random-null controls (`0/10` strict
controls for both whitening modes), but the pocket is too small and unstable
to satisfy the Phase 1 paper gate.

## Interpretation

Layer 3 partially weakens the binary-axis entanglement but does not solve
semantic specificity. Compared with layer 5:

- raw target movement is broader (`6/7` loose positives vs `4/7`);
- control-PC whitening creates a small strict pocket (`2/7` positives for PC1);
- residualization still erases loose behavior (`0/7` loose positives);
- mean positive steered-over-control remains negative even for whitening.

Current best interpretation:

```text
The binary verifier is not merely a layer-5 artifact. Earlier layers have a
less collapsed control geometry and may contain small controlled pockets, but
Pythia-70M still does not provide a stable linear semantic steering result
under the strict held-out alias/random-null verifier.
```

## Reproduction Command

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_behavior_aligned_direction.py --model-id EleutherAI/pythia-70m-deduped --primary-layer 3 --backup-layer -1 --control-layer -1 --max-length 128 --train-variants 0,1 --holdout-variant 2 --scales 1.0 --direction-modes target_learned,target_binary_controls_0_5,target_binary_pc1_resid,target_binary_pc3_resid,target_binary_pc1_whiten,target_binary_pc3_whiten,random_same_norm --scoring-surface binary_relation --prompt-frame source_passage --objective-label-scoring-regimes alias_0+alias_1 --eval-label-scoring-regimes alias_2 --label-score-normalization mean --aliases experiments/concept_geometry/concept_aliases.json --pair-set expanded_random_nulls --seed 20260610 --out artifacts/activation_geometry/modal_pythia_70m_layer3_binary_pc_residualization_seed20260610.json
```

## Discovery-Regime Audit

Question: does the binary low-rank entanglement diagnosis replicate across
layers, or does an earlier layer expose a controlled semantic pocket?

Current regime:

- Artifact types: layer-specific binary-relation payloads, strict specificity
  aggregates, control-PC geometry summaries, strict-pocket pair lists.
- Operations: run the same PC residualization/whitening verifier at another
  transformer block output.
- Gates/verifiers: strict binary-specificity gate, loose behavior retention,
  random-null control suppression.
- Known limitations: same model and same seed; GPT-2 replication was attempted
  but produced no artifact before being stopped, so it is not evidence.

Action class:

- Retrieval/search/discovery: layer replication plus small residual pocket.
- Why: this tests whether the low-rank binary explanation is layer-specific and
  identifies a concrete pair-level pocket for follow-up.

Experiment:

- Manifest/report paths:
  `experiments/activation_geometry/results/binary_layer3_replication_2026_06_10.md`;
  local ignored artifact
  `artifacts/activation_geometry/modal_pythia_70m_layer3_binary_pc_residualization_seed20260610.json`.
- Positive targets: seven expanded random-null positives.
- Negative controls: ten random relation nulls plus row-level yes-bias controls.
- Stress tests: compare raw target, control-mean subtraction, PC residualization,
  PC whitening, and random directions at layer 3.

Gate:

- Acceptance rule: require enough strict positives to plausibly satisfy Phase 1
  after scale/layer replication, with `0/10` strict random-null controls.
- Withheld/rejected rule: do not claim success from isolated pair pockets or
  positive means when the strict gate remains sparse.

Results:

- Accepted artifacts: layer-3 replication report and strict-pocket pair list.
- Rejected or withheld artifacts: layer 3 as a completed paper-ready semantic
  steering result.
- Key metrics: `target_binary_pc1_whiten` gives `2/7` strict positives and
  `0/10` strict controls; `target_binary_pc3_whiten` gives `1/7` strict
  positives and `0/10` strict controls.
- Variance or ablation: whitening outperforms residualization; residualization
  still kills loose positives.

Residual content:

- Explained by old regime: binary yes/no gradients remain low-rank and aligned
  with answer-polarity controls.
- New content outside old regime: layer 3 has a small controlled whitening
  pocket absent at layer 5.
- Retractions or supersessions: supersede "binary surface is only verifier-only
  everywhere" with the narrower "layer 5 is verifier-only; layer 3 has a weak
  strict pocket that needs scale/layer stress before it can matter."

Next move: run a focused layer/scale sweep around layer 3 PC whitening, or
replicate this exact pocket on a second model. A paper claim still needs a
stable result across seeds, layers, or models.
