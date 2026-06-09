# Multi-Control Alias Holdout - 2026-06-09

## Question

The constrained alias-direction run found a promising specificity frontier on the first alias surface: a hard `valence->steering_vector` penalty preserved positives while reducing valence-control movement. This run asks whether that result survives a stricter paper-readiness gate:

```text
Train the behavior direction on alias_0, then evaluate on held-out alias_1,
canonical labels, and the original alias_0 surface.
```

## Method

Raw payloads remain local-only under ignored `artifacts/`.

Payloads:

```text
artifacts/activation_geometry/modal_pythia_70m_multicontrol_alias_holdout_source_seed20260609.json
artifacts/activation_geometry/modal_pythia_70m_multicontrol_alias_holdout_latent_seed20260609.json
```

Grid:

- Model: `EleutherAI/pythia-70m-deduped`
- Objective labels: `alias_0`
- Eval labels: `alias_0`, held-out `alias_1`, `canonical`
- Prompt frames: `source_passage`, `latent_choice`
- Layers: primary `5`, backup `6`, control `1`
- Train variants: `0,1`
- Held-out text variant: `2`
- Scales: `0.5,1.0,2.0`
- Directions: raw target, previous all-residual, hard-control penalty, multi-control penalties, random same-norm
- Seed: `20260609`

This branch adds two verifier upgrades:

- `alias_0`/`alias_1` regimes, so alias transfer can be tested without changing the alias manifest.
- `target_penalty_controls_{0_5,1_0,2_0}` modes, where each leave-one-out control direction is norm-matched before the control set is averaged and subtracted.

Commands:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_behavior_aligned_direction.py --model-id EleutherAI/pythia-70m-deduped --primary-layer 5 --backup-layer 6 --control-layer 1 --max-length 180 --train-variants 0,1 --holdout-variant 2 --scales 0.5,1.0,2.0 --direction-modes target_learned,target_resid_all,target_penalty_hard_1_0,target_penalty_controls_0_5,target_penalty_controls_1_0,target_penalty_controls_2_0,random_same_norm --scoring-surface full_label --prompt-frame source_passage --objective-label-scoring-regimes alias_0 --eval-label-scoring-regimes alias_0,alias_1,canonical --label-score-normalization mean --aliases experiments/concept_geometry/concept_aliases.json --seed 20260609 --out artifacts/activation_geometry/modal_pythia_70m_multicontrol_alias_holdout_source_seed20260609.json
```

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_behavior_aligned_direction.py --model-id EleutherAI/pythia-70m-deduped --primary-layer 5 --backup-layer 6 --control-layer 1 --max-length 180 --train-variants 0,1 --holdout-variant 2 --scales 0.5,1.0,2.0 --direction-modes target_learned,target_resid_all,target_penalty_hard_1_0,target_penalty_controls_0_5,target_penalty_controls_1_0,target_penalty_controls_2_0,random_same_norm --scoring-surface full_label --prompt-frame latent_choice --objective-label-scoring-regimes alias_0 --eval-label-scoring-regimes alias_0,alias_1,canonical --label-score-normalization mean --aliases experiments/concept_geometry/concept_aliases.json --seed 20260609 --out artifacts/activation_geometry/modal_pythia_70m_multicontrol_alias_holdout_latent_seed20260609.json
```

## Results

### Scale 1 Primary Layer

Held-out `alias_1` is the breaking condition. The raw target direction still moves held-out aliases, but the constrained modes no longer keep all positives.

| Prompt frame | Eval labels | Direction | Positive passes | Positive mean | Valence-control passes | Control mean |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| source_passage | alias_0 | target_learned | 3/3 | 1.231 | 2/2 | 1.848 |
| source_passage | alias_0 | target_penalty_hard_1_0 | 3/3 | 1.263 | 1/2 | 0.572 |
| source_passage | alias_0 | target_penalty_controls_2_0 | 3/3 | 1.244 | 2/2 | 0.178 |
| source_passage | alias_1 | target_learned | 3/3 | 0.408 | 2/2 | 0.265 |
| source_passage | alias_1 | target_resid_all | 3/3 | 0.455 | 1/2 | 0.132 |
| source_passage | alias_1 | target_penalty_hard_1_0 | 2/3 | 0.295 | 1/2 | 0.110 |
| source_passage | alias_1 | target_penalty_controls_1_0 | 2/3 | 0.369 | 2/2 | 0.120 |
| source_passage | alias_1 | target_penalty_controls_2_0 | 2/3 | 0.340 | 1/2 | -0.028 |
| source_passage | canonical | target_learned | 3/3 | 0.605 | 2/2 | 0.776 |
| source_passage | canonical | target_penalty_hard_1_0 | 3/3 | 0.408 | 1/2 | 0.034 |
| latent_choice | alias_0 | target_learned | 3/3 | 1.591 | 2/2 | 2.517 |
| latent_choice | alias_0 | target_penalty_hard_1_0 | 3/3 | 1.585 | 1/2 | 0.597 |
| latent_choice | alias_0 | target_penalty_controls_2_0 | 3/3 | 1.458 | 0/2 | -0.052 |
| latent_choice | alias_1 | target_learned | 3/3 | 0.410 | 2/2 | 0.383 |
| latent_choice | alias_1 | target_resid_all | 3/3 | 0.441 | 2/2 | 0.276 |
| latent_choice | alias_1 | target_penalty_hard_1_0 | 2/3 | 0.360 | 1/2 | 0.173 |
| latent_choice | alias_1 | target_penalty_controls_1_0 | 2/3 | 0.383 | 2/2 | 0.218 |
| latent_choice | alias_1 | target_penalty_controls_2_0 | 2/3 | 0.343 | 1/2 | 0.067 |
| latent_choice | canonical | target_learned | 3/3 | 0.690 | 2/2 | 1.011 |
| latent_choice | canonical | target_penalty_hard_1_0 | 3/3 | 0.392 | 1/2 | 0.193 |

### Held-Out Alias Failure Mode

The missing positive under held-out alias scoring is consistently the attractor pair. At scale `1.0`, every constrained mode fails `attractor->attractor_network` under `alias_1` in both prompt frames.

| Prompt frame | Direction | `attractor->attractor_network` | `autopoiesis->homeostasis` | `validity_gate->weak_constraint` |
| --- | --- | ---: | ---: | ---: |
| source_passage | target_penalty_hard_1_0 | -0.018 | 0.252 | 0.652 |
| source_passage | target_penalty_controls_1_0 | -0.042 | 0.289 | 0.860 |
| source_passage | target_penalty_controls_2_0 | -0.098 | 0.310 | 0.809 |
| latent_choice | target_penalty_hard_1_0 | -0.033 | 0.312 | 0.802 |
| latent_choice | target_penalty_controls_1_0 | -0.053 | 0.319 | 0.883 |
| latent_choice | target_penalty_controls_2_0 | -0.109 | 0.346 | 0.791 |

The held-out alias for `attractor_network` is `recurrent memory network`, which is lexically and mechanistically different from `stable-state network`. This suggests the previous frontier partly used the first alias surface, not only the underlying concept.

### Multi-Control Penalty

The multi-control penalty does not solve independent leakage. It can reduce control means, especially at higher weights, but it either leaves controls passing or weakens held-out positives.

| Prompt frame | Eval labels | Multi-control mode | Positive passes | Control passes | Control mean |
| --- | --- | --- | ---: | ---: | ---: |
| source_passage | alias_1 | controls_0_5 | 2/3 | 2/2 | 0.187 |
| source_passage | alias_1 | controls_1_0 | 2/3 | 2/2 | 0.120 |
| source_passage | alias_1 | controls_2_0 | 2/3 | 1/2 | -0.028 |
| latent_choice | alias_1 | controls_0_5 | 2/3 | 2/2 | 0.298 |
| latent_choice | alias_1 | controls_1_0 | 2/3 | 2/2 | 0.218 |
| latent_choice | alias_1 | controls_2_0 | 2/3 | 1/2 | 0.067 |

## Diagnosis

Accepted:

```text
Explicit held-out alias scoring is necessary; alias_0 success does not imply
alias_1 success.
```

Accepted:

```text
The first constrained-direction frontier is alias-surface dependent.
```

Rejected:

```text
The current hard-control or multi-control penalties are sufficient for paper-level
semantic specificity.
```

Withheld:

```text
Alias-trained constrained directions are label-invariant semantic steering
directions.
```

Best current interpretation:

```text
Direct behavior gradients can move held-out aliases, but the constrained cleanup
that improves the training-alias surface removes or weakens at least one real
held-out semantic target. The frontier is real but not yet concept-invariant.
```

This is a productive failure. It prevents us from writing an overclaimed paper and tells us the next route: train/evaluate over multiple aliases jointly, then test on held-out aliases and independent controls.

## Next Move

- Train behavior directions on multiple aliases per role, not a single alias phrase.
- Keep `alias_1` or a third paraphrased label as the held-out lexical surface.
- Expand the positive/control concept set before spending compute on larger models.
- Add a CAA/CAV-style baseline under the same held-out alias verifier.

## Discovery-Regime Audit

Question: does the constrained alias-direction frontier survive held-out alias and leave-one-out multi-control stress tests?

Current regime:

- Artifact types: alias-indexed label manifests, full-label gradient directions, constrained direction modes, held-out alias eval rows, leave-one-out control rows.
- Operations: alias-indexed label scoring, norm-matched multi-control subtraction, held-out full-label continuation scoring.
- Gates/verifiers: held-out alias positives must remain robust; independent controls must weaken relative to raw target directions; construction-zeroed controls do not count as independent evidence.
- Known limitations: Pythia-70M only, three positives, two valence controls, one held-out alias per concept.

Action class:

- Retrieval/search/discovery: verifier hardening with a rejected candidate.
- Why: this adds a held-out alias verifier and falsifies the current constrained frontier as a paper-level mechanism.

Experiment:

- Manifest/report paths: this report; local ignored payloads under `artifacts/activation_geometry/modal_pythia_70m_multicontrol_alias_holdout_*.json`.
- Positive targets: promoted steering pairs.
- Negative controls: valence controls with leave-one-out control bases; random same-norm controls.
- Stress tests: `source_passage` and `latent_choice`; eval labels `alias_0`, `alias_1`, and `canonical`; penalty weights `0.5`, `1.0`, `2.0`.

Gate:

- Acceptance rule: promote the constrained frontier only if held-out `alias_1` positives remain `3/3` while independent controls weaken.
- Withheld/rejected rule: withhold if any positive systematically fails under held-out alias or if controls still pass.

Results:

- Accepted artifacts: `alias_0`/`alias_1` regimes; multi-control penalty modes; this report.
- Rejected or withheld artifacts: current constrained alias direction remains non-paper-ready.
- Key metrics: raw target directions pass `3/3` held-out `alias_1` positives but controls pass `2/2`; constrained modes reduce controls but drop held-out positives to `2/3`, consistently failing `attractor->attractor_network`.
- Variance or ablation: both prompt frames agree on the held-out alias failure; canonical and `alias_0` remain easier than `alias_1`.

Residual content:

- Explained by old regime: exact-label and first-alias behavior surfaces are easier to control than label-invariant concept behavior.
- New content outside old regime: held-out alias scoring exposes an alias-specific weakness in the constrained frontier.
- Retractions or supersessions: supersede "hard-control penalty is close to paper-ready" with "hard-control penalty is a useful frontier but not alias-invariant."

Next move: jointly train over multiple aliases and broaden the concept/control set before scaling models.
