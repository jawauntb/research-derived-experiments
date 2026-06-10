# Contrastive Binary Specificity - 2026-06-09

## Status

Completed the spectrum-enabled contrastive binary specificity run. Raw payloads
remain local-only under ignored `artifacts/`:

```text
artifacts/activation_geometry/modal_pythia_70m_binary_contrastive_specificity_seed20260609.json
```

The artifact contains `102` intervention rows plus `binary_gradient_geometry`
SVD summaries for target, control, combined target-plus-control, and
always-false gradients.

## What Changed

- Added contrastive binary direction modes:
  - `target_binary_controls_0_5`
  - `target_binary_controls_1_0`
  - `target_binary_controls_2_0`
  - `target_binary_controls_4_0`
- These modes construct the target binary Yes-No gradient and subtract a
  norm-matched mean of binary yes-bias control gradients.
- Promoted binary yes-bias controls into the robust-pass rule when control
  margins are available.
- Added payload support for binary gradient geometry summaries.

## Gate

A binary-relation row now passes semantic specificity only when all are true:

```text
target margin improves
target Yes-No margin increases
steered target Yes-No margin is positive
target delta beats the max yes-bias control delta
steered target margin beats the max steered yes-bias control margin
always-false carrier margin does not end positive
```

Older binary payloads without control margins retain the previous basic pass
rule for backward compatibility.

## Completed Run Summary

| Direction | Positive basic | Positive strict | Control basic | Control strict | Pos margin delta | Pos target delta | Pos delta over control | Pos steered over control | Pos false-carrier steered |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `target_learned` | 4/7 | 0/7 | 3/10 | 0/10 | 0.075 | 4.508 | -0.109 | -0.590 | 2.399 |
| `target_binary_controls_0_5` | 4/7 | 0/7 | 2/10 | 0/10 | 0.042 | 2.434 | -0.044 | -0.650 | 0.437 |
| `target_binary_controls_1_0` | 0/7 | 0/7 | 0/10 | 0/10 | 0.006 | 0.158 | -0.024 | -0.760 | -1.736 |
| `target_binary_controls_2_0` | 0/7 | 0/7 | 0/10 | 0/10 | 0.003 | -4.539 | -0.084 | -0.812 | -6.424 |
| `target_binary_controls_4_0` | 0/7 | 0/7 | 0/10 | 0/10 | -0.029 | -12.867 | -0.260 | -0.640 | -14.916 |
| `random_same_norm` | 0/7 | 0/7 | 0/10 | 0/10 | -0.013 | -0.055 | -0.085 | -0.880 | -1.773 |

## Gradient Geometry

The binary gradient field is extremely low-rank. Rows below use normalized
directions before SVD.

| Direction set | Count | Mean pairwise cosine | First PC energy | First 3 PCs energy | Top singular values |
| --- | ---: | ---: | ---: | ---: | --- |
| Target gradients | 17 | 0.921 | 0.926 | 0.952 | 3.968, 0.541, 0.386, 0.347, 0.333 |
| Yes-bias control gradients | 102 | 0.890 | 0.891 | 0.928 | 9.534, 1.480, 1.258, 0.999, 0.863 |
| Target + controls | 119 | 0.894 | 0.895 | 0.930 | 10.320, 1.528, 1.333, 1.054, 0.929 |
| Always-false gradients | 17 | 0.950 | 0.953 | 0.973 | 4.025, 0.437, 0.388, 0.312, 0.303 |

The mechanism is therefore not "pair-specific leakage" on this binary surface.
It is mostly a shared low-rank answer-polarity/candidate-affirmation axis.
However, the target gradients lie in that same axis, so subtracting the control
mean suppresses target behavior along with the confound.

## Interpretation

The strict binary-specificity gate rejects every direction.

The tradeoff is informative:

- `target_learned` reproduces the loose binary behavior signal, but still fails
  the yes-bias controls.
- `target_binary_controls_0_5` keeps much of the loose target movement, but
  controls still move with it and the false-carrier margin remains positive.
- `target_binary_controls_1_0` suppresses the false-carrier control, but it also
  collapses target movement.
- Larger control penalties push target movement negative.

Current best interpretation:

```text
The direct binary behavior surface is real and steerable, but in Pythia-70M
layer 5 the target relation gradient is entangled with a broad answer-polarity
or candidate-affirmation channel. Simple linear control subtraction does not
recover a semantic-specific direction.
```

## Reproduction Command

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_behavior_aligned_direction.py --model-id EleutherAI/pythia-70m-deduped --primary-layer 5 --backup-layer -1 --control-layer -1 --max-length 128 --train-variants 0,1 --holdout-variant 2 --scales 1.0 --direction-modes target_learned,target_binary_controls_0_5,target_binary_controls_1_0,target_binary_controls_2_0,target_binary_controls_4_0,random_same_norm --scoring-surface binary_relation --prompt-frame source_passage --objective-label-scoring-regimes alias_0+alias_1 --eval-label-scoring-regimes alias_2 --label-score-normalization mean --aliases experiments/concept_geometry/concept_aliases.json --pair-set expanded_random_nulls --seed 20260609 --out artifacts/activation_geometry/modal_pythia_70m_binary_contrastive_specificity_seed20260609.json
```

## Discovery-Regime Audit

Question: can a contrastive binary objective subtract yes-bias while preserving
relation-specific target movement?

Current regime:

- Artifact types: binary-relation payloads, yes-bias control margins,
  contrastive binary direction modes, strict binary-specificity aggregates,
  binary gradient geometry summaries.
- Operations: target Yes-No gradient construction, binary control-gradient
  construction, norm-matched multi-control subtraction, held-out alias binary
  scoring.
- Gates/verifiers: target movement must beat blank/generic/source/distractor/
  shuffled-target/always-false controls and must not make the always-false
  carrier positive.
- Known limitations: one model, one seed, one layer; low-rank diagnosis is
  binary-surface-specific and does not contradict earlier full-label alias
  leakage diagnostics.

Action class:

- Retrieval/search/discovery: verifier hardening plus rejected intervention
  family.
- Why: this upgrades yes-bias controls from post-hoc diagnosis to an acceptance
  rule and tests whether simple linear contrastive subtraction can recover a
  semantic direction.

Experiment:

- Manifest/report paths: this checkpoint; local ignored artifact
  `artifacts/activation_geometry/modal_pythia_70m_binary_contrastive_specificity_seed20260609.json`.
- Positive targets: expanded random-null pair set positives.
- Negative controls: ten random relation nulls plus per-row yes-bias controls.
- Stress tests: control-subtraction weights `0.5`, `1.0`, `2.0`, `4.0`.

Gate:

- Acceptance rule: promote only rows that clear the strict binary-specificity
  rule above.
- Withheld/rejected rule: reject directions that keep loose target movement but
  fail yes-bias controls, or suppress controls only by also suppressing target.

Results:

- Accepted artifacts: strict binary-specificity gate and contrastive direction
  modes.
- Rejected or withheld artifacts: `target_learned` and all tested
  `target_binary_controls_*` directions as semantic-specific steering.
- Key metrics: strict passes are `0/7` positives and `0/10` controls for every
  tested direction. Target + control gradients have first-PC energy `0.895`,
  with first three PCs explaining `0.930` of normalized-gradient energy.
- Variance or ablation: weight `0.5` keeps loose target behavior but leaves
  controls active; weight `1.0+` suppresses controls by collapsing or reversing
  target movement.

Residual content:

- Explained by old regime: the loose binary surface is answer-polarity
  steerable.
- New content outside old regime: yes-bias-aware acceptance rejects the apparent
  binary pocket; the binary gradient field is low-rank, but simple contrastive
  subtraction cannot separate target relation movement from control movement.
- Retractions or supersessions: supersede "build contrastive binary directions
  next" with "contrastive binary subtraction tested; next need spectrum/low-rank
  diagnosis or a different nonlinear/feature-guided intervention."

Next move: test top-PC residualization/whitening as a deliberately lossy probe.
If removing the dominant binary axis kills target movement, the binary surface
should be treated as a verifier-only diagnostic rather than a route to semantic
steering in Pythia-70M.
