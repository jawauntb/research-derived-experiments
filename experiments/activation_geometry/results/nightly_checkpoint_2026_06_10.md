# Activation Geometry Nightly Checkpoint: Second-Model Pocket Replication

Date: 2026-06-10

## Why this checkpoint exists

The current publication path is not blocked by code. It is blocked by evidence:
the strict binary-relation verifier has found only a tiny Pythia-70M layer-3
pocket, and we need to know whether that pocket survives a second model or a
different intervention class.

This note preserves the state before pausing so the next session can resume
without reconstructing the experimental thread.

## Accepted evidence so far

- Pythia-70M layer 5: top-PC residualization/whitening fails as a semantic
  steering route. The target binary gradients are almost collinear with the
  dominant control PC.
- Pythia-70M layer 3: PC1 whitening at scale `1.0` gives the cleanest strict
  pocket: `2/7` strict positives and `0/10` random-null controls.
- The stable strict positives around scale `1.0` are:
  - `attractor->attractor_network`
  - `fixed_point->prototype`
- Scale calibration is exhausted as the next big move: scale `1.25` adds one
  strict positive but revives one strict random-null control.

## Failed or withheld evidence

The first Pythia-160M full-pair replication attempt did not produce an artifact
and must not be treated as evidence.

Attempted command:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_behavior_aligned_direction.py --model-id EleutherAI/pythia-160m-deduped --primary-layer 3 --backup-layer -1 --control-layer -1 --max-length 128 --train-variants 0,1 --holdout-variant 2 --scales 1.0 --direction-modes target_binary_pc1_whiten,random_same_norm --scoring-surface binary_relation --prompt-frame source_passage --objective-label-scoring-regimes alias_0+alias_1 --eval-label-scoring-regimes alias_2 --label-score-normalization mean --aliases experiments/concept_geometry/concept_aliases.json --pair-set expanded_random_nulls --seed 20260610 --out artifacts/activation_geometry/modal_pythia_160m_layer3_pc1_whiten_replication_seed20260610.json
```

Failure mode:

- Modal app URL:
  `https://modal.com/apps/generalintelligencecompany/main/ap-wAKzF1PvlJe76EOMTEQPaq`
- Local client failed with:
  `modal.exception.ConnectionError: [Errno 8] nodename nor servname provided, or not known`
- Modal stopped the app after the client disconnected.
- No local artifact exists at
  `artifacts/activation_geometry/modal_pythia_160m_layer3_pc1_whiten_replication_seed20260610.json`.

## Code checkpoint

Added a focused pair set:

- `layer3_strict_pocket_random_nulls`
- Positives:
  - `attractor->attractor_network`
  - `fixed_point->prototype`
- Controls:
  - all ten `RANDOM_RELATION_NULL_PAIRS`, including the hard adversarial
    `valence->steering_vector` row.

This does not change the claim. It only makes the next second-model replication
cheaper and less ambiguous.

## Next command

Run the focused Pythia-160M replication:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_behavior_aligned_direction.py --model-id EleutherAI/pythia-160m-deduped --primary-layer 3 --backup-layer -1 --control-layer -1 --max-length 128 --train-variants 0,1 --holdout-variant 2 --scales 1.0 --direction-modes target_binary_pc1_whiten,random_same_norm --scoring-surface binary_relation --prompt-frame source_passage --objective-label-scoring-regimes alias_0+alias_1 --eval-label-scoring-regimes alias_2 --label-score-normalization mean --aliases experiments/concept_geometry/concept_aliases.json --pair-set layer3_strict_pocket_random_nulls --seed 20260610 --out artifacts/activation_geometry/modal_pythia_160m_layer3_pocket_replication_seed20260610.json
```

Acceptance rule:

- `target_binary_pc1_whiten` should preserve both strict positives or at least
  clearly outperform `random_same_norm`.
- Strict random-null controls must remain `0/10`.

Rejection rule:

- If the two strict positives disappear on Pythia-160M, treat the Pythia-70M
  layer-3 pocket as model-specific and pivot toward a nonlinear or feature-guided
  intervention under the same strict binary verifier.
- If controls revive, keep the result as a specificity-boundary failure rather
  than a semantic steering success.

## Discovery-regime status

This is still search, not discovery. The current regime can represent these
artifacts: pair sets, strict binary aggregates, random-null controls, and scale
frontiers. A discovery-level transition would require a stable accepted pocket
across model/layer/seed, or a new operation such as a feature-guided nonlinear
intervention that passes the same strict gate.
