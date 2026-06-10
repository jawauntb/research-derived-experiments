# Binary Relation Steering: Pythia-160M Pocket Replication

Date: 2026-06-10

## Question

Does the tiny Pythia-70M layer-3 strict pocket replicate in a second, larger
open model, or was it a model-specific accident?

The pocket from the Pythia-70M layer-3 scale sweep contained two stable strict
positives under `target_binary_pc1_whiten` at scale `1.0`:

- `attractor->attractor_network`
- `fixed_point->prototype`

This run tests only those two positives against the same ten random relation
null controls.

## Setup

- Model: `EleutherAI/pythia-160m-deduped`
- Layer: `3`
- Pair set: `layer3_strict_pocket_random_nulls`
- Positive pairs: `2`
- Random-null controls: `10`
- Direction modes: `target_binary_pc1_whiten`, `random_same_norm`
- Scoring surface: `binary_relation`
- Prompt frame: `source_passage`
- Objective label scoring: `alias_0+alias_1`
- Eval label scoring: held-out `alias_2`
- Train variants: `0,1`
- Holdout variant: `2`
- Seed: `20260610`

Local Modal attached runs failed twice with heartbeat/DNS errors before producing
artifacts. To make the run robust, the Modal runner now supports
`--modal-volume-out`, which spawns the remote function and writes the raw payload
inside the Modal Volume `rde-activation-results`.

Local ignored artifacts:

- `artifacts/activation_geometry/modal_pythia_160m_layer3_pocket_replication_seed20260610.json`
- `artifacts/activation_geometry/modal_pythia_160m_layer3_pocket_scale_sweep_seed20260610.json`

Modal raw payloads:

- `rde-activation-results:activation_geometry/pythia160_layer3_pocket_seed20260610_raw.json`
- `rde-activation-results:activation_geometry/pythia160_layer3_pocket_scale_sweep_seed20260610_raw.json`

## Result

The Pythia-70M strict pocket does **not** replicate in Pythia-160M at layer 3.

### Scale-1 Replication

At scale `1.0`, `target_binary_pc1_whiten` produces positive target Yes-margin
movement, but both focused positives fail the strict gate because the movement
does not beat the strongest yes-bias control channels.

| Direction | Strict positives | Strict random-null controls | Positive mean target delta | Positive mean steered-over-control |
| --- | ---: | ---: | ---: | ---: |
| `target_binary_pc1_whiten` | `0/2` | `0/10` | `0.550` | `-0.372` |
| `random_same_norm` | `0/2` | `0/10` | `-0.072` | `-0.979` |

Pair-level details for `target_binary_pc1_whiten` at scale `1.0`:

| Pair | Strict gate | Target delta | Steered over max control | Delta over max control | Always-false steered margin |
| --- | --- | ---: | ---: | ---: | ---: |
| `attractor->attractor_network` | fail | `0.859` | `0.039` | `-0.366` | `1.181` |
| `fixed_point->prototype` | fail | `0.241` | `-0.783` | `-0.289` | `1.315` |

### Focused Scale Sweep

Scaling does not recover the pocket. Across scales `0.5`, `0.75`, `1.0`,
`1.25`, and `1.5`, both `target_binary_pc1_whiten` and `random_same_norm` have
`0/2` strict positives and `0/10` strict random-null controls.

| Scale | Direction | Strict positives | Strict controls | Positive target delta | Control target delta | Positive steered-over-control |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `0.5` | `target_binary_pc1_whiten` | `0/2` | `0/10` | `0.406` | `0.513` | `-0.445` |
| `0.75` | `target_binary_pc1_whiten` | `0/2` | `0/10` | `0.504` | `0.677` | `-0.366` |
| `1.0` | `target_binary_pc1_whiten` | `0/2` | `0/10` | `0.551` | `0.778` | `-0.370` |
| `1.25` | `target_binary_pc1_whiten` | `0/2` | `0/10` | `0.570` | `0.834` | `-0.360` |
| `1.5` | `target_binary_pc1_whiten` | `0/2` | `0/10` | `0.569` | `0.872` | `-0.349` |
| `0.5` | `random_same_norm` | `0/2` | `0/10` | `-0.032` | `-0.003` | `-0.943` |
| `0.75` | `random_same_norm` | `0/2` | `0/10` | `-0.021` | `0.003` | `-0.842` |
| `1.0` | `random_same_norm` | `0/2` | `0/10` | `0.043` | `0.025` | `-0.923` |
| `1.25` | `random_same_norm` | `0/2` | `0/10` | `-0.101` | `-0.030` | `-0.986` |
| `1.5` | `random_same_norm` | `0/2` | `0/10` | `0.057` | `-0.055` | `-0.856` |

## Mechanistic Diagnostic

The binary gradient geometry remains strongly low-rank in Pythia-160M:

| Direction family | Count | First-PC energy | First-3-PC energy | Mean pairwise cosine |
| --- | ---: | ---: | ---: | ---: |
| target directions | `12` | `0.877` | `0.928` | `0.865` |
| binary control directions | `72` | `0.692` | `0.871` | `0.642` |
| target plus controls | `84` | `0.715` | `0.873` | `0.666` |
| always-false controls | `12` | `0.913` | `0.959` | `0.905` |

This supports the same broad diagnosis as the Pythia-70M runs: the binary
surface is dominated by answer-polarity or carrier-confirmation geometry. PC1
whitening can create apparent target movement, but the target movement is not
specific enough to beat the strict yes-bias controls.

## Interpretation

This is a negative second-model replication. The Pythia-70M layer-3 two-pair
pocket should now be treated as weak and model-specific, not as a paper-ready
semantic steering result.

The useful contribution is a sharper failure boundary:

- Layer-5 Pythia-70M: binary PC cleanup fails completely.
- Layer-3 Pythia-70M: a tiny strict pocket appears.
- Layer-3 Pythia-160M: the same pocket disappears across a focused scale sweep.

The next meaningful move is no longer "bigger repeats of the same linear
direction." The strict binary verifier should be reused, but the intervention
should change class: pair-focused nonlinear optimization, feature-guided
intervention, or another mechanism that is not just a linear direction in the
low-rank binary carrier subspace.

## Commands

Initial focused replication:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run --detach --name pythia160-pocket-volume-spawn experiments/activation_geometry/modal_behavior_aligned_direction.py --model-id EleutherAI/pythia-160m-deduped --primary-layer 3 --backup-layer -1 --control-layer -1 --max-length 128 --train-variants 0,1 --holdout-variant 2 --scales 1.0 --direction-modes target_binary_pc1_whiten,random_same_norm --scoring-surface binary_relation --prompt-frame source_passage --objective-label-scoring-regimes alias_0+alias_1 --eval-label-scoring-regimes alias_2 --label-score-normalization mean --aliases experiments/concept_geometry/concept_aliases.json --pair-set layer3_strict_pocket_random_nulls --seed 20260610 --out none --modal-volume-out activation_geometry/pythia160_layer3_pocket_seed20260610_raw.json
```

Focused scale sweep:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run --detach --name pythia160-pocket-scale-volume-spawn experiments/activation_geometry/modal_behavior_aligned_direction.py --model-id EleutherAI/pythia-160m-deduped --primary-layer 3 --backup-layer -1 --control-layer -1 --max-length 128 --train-variants 0,1 --holdout-variant 2 --scales 0.5,0.75,1.0,1.25,1.5 --direction-modes target_binary_pc1_whiten,random_same_norm --scoring-surface binary_relation --prompt-frame source_passage --objective-label-scoring-regimes alias_0+alias_1 --eval-label-scoring-regimes alias_2 --label-score-normalization mean --aliases experiments/concept_geometry/concept_aliases.json --pair-set layer3_strict_pocket_random_nulls --seed 20260610 --out none --modal-volume-out activation_geometry/pythia160_layer3_pocket_scale_sweep_seed20260610_raw.json
```

## Discovery-Regime Audit

Question: does the two-pair Pythia-70M layer-3 strict pocket survive a second
model and scale stress?

Current regime:

- Artifact types: strict binary-relation aggregates, pair-set narrowed pocket
  reports, random-null control tables, binary gradient geometry summaries.
- Operations: PC1-whitened linear steering, random same-norm baseline, scale
  sweep, durable Modal Volume raw-payload capture.
- Gates/verifiers: strict positive pass counts, `0/10` random-null control
  passes, target movement over strongest yes-bias control, low-rank geometry
  diagnostic.
- Known limitations: one layer in the second model; no nonlinear or
  feature-guided intervention yet.

Action class:

- Retrieval/search/discovery: search plus falsification.
- Why: this tests whether an existing pocket transports to another model. It
  does not create a new accepted semantic steering artifact.

Results:

- Accepted artifacts: durable Modal Volume runner support; Pythia-160M negative
  replication report.
- Rejected or withheld artifacts: Pythia-70M layer-3 pocket as a robust
  cross-model result.
- Key metrics: `target_binary_pc1_whiten` is `0/2` strict positives and `0/10`
  controls at every scale from `0.5` to `1.5`; `random_same_norm` is also `0/2`
  positives and `0/10` controls.
- Variance or ablation: scale sweep over five values rules out simple scale
  mismatch.

Residual content:

- Explained by old regime: the binary relation surface is low-rank and
  answer-polarity dominated.
- New content outside old regime: the tiny layer-3 Pythia-70M pocket is not
  robust across model scale.
- Retractions or supersessions: supersede "replicate the two stable layer-3
  strict positives across a second model" with "second-model replication fails;
  pivot to a different intervention class under the same verifier."

Next move: evaluate a pair-focused nonlinear or feature-guided intervention
against the strict binary verifier instead of continuing linear PC-whitening
scale/layer sweeps.
