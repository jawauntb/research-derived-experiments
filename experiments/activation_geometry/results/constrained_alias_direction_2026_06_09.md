# Constrained Alias Direction - 2026-06-09

## Question

The residualized alias-direction run showed that post-hoc projection attenuates leakage but does not isolate a concept-specific behavior channel. This run asks whether an explicitly adversarial direction-construction objective can do better:

```text
Can we subtract the known hard valence-control direction during behavior-direction
construction while preserving positive alias/canonical target movement?
```

## Method

Raw payloads remain local-only under ignored `artifacts/`.

Payloads:

```text
artifacts/activation_geometry/modal_pythia_70m_constrained_alias_direction_source_seed20260608.json
artifacts/activation_geometry/modal_pythia_70m_constrained_alias_direction_latent_seed20260608.json
```

Grid:

- Model: `EleutherAI/pythia-70m-deduped`
- Scoring surface: `full_label`
- Objective label scoring regime: `alias`
- Eval label scoring regimes: `alias`, `canonical`
- Prompt frames: `source_passage`, `latent_choice`
- Layers: primary `5`, backup `6`, control `1`
- Train variants: `0,1`
- Held-out variant: `2`
- Scales: `0.5,1.0,2.0`
- Label score normalization: mean logprob per label token
- Seed: `20260608`

Direction modes:

- `target_learned`: raw alias target-margin gradient.
- `target_resid_all`: previous projection residual against mean valence-control, source, and distractor directions.
- `target_penalty_hard_1_0`: target direction minus the norm-matched `valence->steering_vector` target direction.
- `target_penalty_hard_2_0`: target direction minus twice the norm-matched `valence->steering_vector` target direction.
- `target_penalty_control_mean_1_0`: target direction minus the norm-matched leave-one-out mean valence-control target direction.
- `random_same_norm`: same-norm random direction.

Important caveat: for the `valence->steering_vector` row itself, `target_penalty_hard_1_0` is a zero vector by construction. That row is a construction sanity check, not independent evidence that the hard control generalizes away. The independent control in this run is `valence->activation_vector`.

Commands:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_behavior_aligned_direction.py --model-id EleutherAI/pythia-70m-deduped --primary-layer 5 --backup-layer 6 --control-layer 1 --max-length 180 --train-variants 0,1 --holdout-variant 2 --scales 0.5,1.0,2.0 --direction-modes target_learned,target_resid_all,target_penalty_hard_1_0,target_penalty_hard_2_0,target_penalty_control_mean_1_0,random_same_norm --scoring-surface full_label --prompt-frame source_passage --objective-label-scoring-regimes alias --eval-label-scoring-regimes alias,canonical --label-score-normalization mean --aliases experiments/concept_geometry/concept_aliases.json --seed 20260608 --out artifacts/activation_geometry/modal_pythia_70m_constrained_alias_direction_source_seed20260608.json
```

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_behavior_aligned_direction.py --model-id EleutherAI/pythia-70m-deduped --primary-layer 5 --backup-layer 6 --control-layer 1 --max-length 180 --train-variants 0,1 --holdout-variant 2 --scales 0.5,1.0,2.0 --direction-modes target_learned,target_resid_all,target_penalty_hard_1_0,target_penalty_hard_2_0,target_penalty_control_mean_1_0,random_same_norm --scoring-surface full_label --prompt-frame latent_choice --objective-label-scoring-regimes alias --eval-label-scoring-regimes alias,canonical --label-score-normalization mean --aliases experiments/concept_geometry/concept_aliases.json --seed 20260608 --out artifacts/activation_geometry/modal_pythia_70m_constrained_alias_direction_latent_seed20260608.json
```

## Results

### Scale 1 Primary Layer

The hard-control penalty at weight `1.0` keeps all positives in both prompt frames and both eval label regimes. It reduces the mean valence-control delta much more than projection residualization, but one independent valence control remains alive.

| Prompt frame | Eval labels | Direction | Positive passes | Positive mean | Valence-control passes | Valence-control mean |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| source_passage | alias | target_learned | 3/3 | 1.231 | 2/2 | 1.848 |
| source_passage | alias | target_resid_all | 3/3 | 0.974 | 2/2 | 1.008 |
| source_passage | alias | target_penalty_hard_1_0 | 3/3 | 1.263 | 1/2 | 0.572 |
| source_passage | alias | target_penalty_hard_2_0 | 3/3 | 1.286 | 1/2 | -0.876 |
| source_passage | alias | target_penalty_control_mean_1_0 | 3/3 | 1.236 | 2/2 | 1.035 |
| source_passage | canonical | target_learned | 3/3 | 0.604 | 2/2 | 0.775 |
| source_passage | canonical | target_resid_all | 3/3 | 0.548 | 1/2 | 0.392 |
| source_passage | canonical | target_penalty_hard_1_0 | 3/3 | 0.408 | 1/2 | 0.034 |
| source_passage | canonical | target_penalty_hard_2_0 | 2/3 | 0.188 | 0/2 | -0.771 |
| source_passage | canonical | target_penalty_control_mean_1_0 | 3/3 | 0.364 | 2/2 | 0.493 |
| latent_choice | alias | target_learned | 3/3 | 1.592 | 2/2 | 2.518 |
| latent_choice | alias | target_resid_all | 3/3 | 1.197 | 2/2 | 1.366 |
| latent_choice | alias | target_penalty_hard_1_0 | 3/3 | 1.586 | 1/2 | 0.598 |
| latent_choice | alias | target_penalty_hard_2_0 | 3/3 | 1.540 | 0/2 | -1.346 |
| latent_choice | alias | target_penalty_control_mean_1_0 | 3/3 | 1.532 | 2/2 | 1.225 |
| latent_choice | canonical | target_learned | 3/3 | 0.690 | 2/2 | 1.010 |
| latent_choice | canonical | target_resid_all | 3/3 | 0.522 | 2/2 | 0.777 |
| latent_choice | canonical | target_penalty_hard_1_0 | 3/3 | 0.392 | 1/2 | 0.193 |
| latent_choice | canonical | target_penalty_hard_2_0 | 1/3 | 0.062 | 0/2 | -0.547 |
| latent_choice | canonical | target_penalty_control_mean_1_0 | 2/3 | 0.281 | 2/2 | 0.749 |

### Specificity Tradeoff

`target_penalty_hard_1_0` is the best current candidate. It preserves all positives while reducing control means:

| Prompt frame | Eval labels | Raw control mean | Hard penalty 1.0 control mean | Reduction |
| --- | --- | ---: | ---: | ---: |
| source_passage | alias | 1.848 | 0.572 | 69.0% |
| source_passage | canonical | 0.775 | 0.034 | 95.6% |
| latent_choice | alias | 2.518 | 0.598 | 76.3% |
| latent_choice | canonical | 1.010 | 0.193 | 80.9% |

`target_penalty_hard_2_0` is too aggressive. It kills both controls in canonical scoring but drops positives, especially in the latent/canonical condition.

### Independent Control

At scale `1.0`, the hard-control penalty splits the controls as expected. The hard control row is zeroed by construction; the independent `valence->activation_vector` row still passes.

| Prompt frame | Eval labels | Direction | `valence->activation_vector` | `valence->steering_vector` |
| --- | --- | --- | ---: | ---: |
| source_passage | canonical | target_resid_all | -0.008, fail | 0.791, pass |
| source_passage | canonical | target_penalty_hard_1_0 | 0.068, pass | 0.000, fail |
| source_passage | canonical | target_penalty_hard_2_0 | -0.752, fail | -0.790, fail |
| latent_choice | canonical | target_resid_all | 0.438, pass | 1.116, pass |
| latent_choice | canonical | target_penalty_hard_1_0 | 0.386, pass | 0.000, fail |
| latent_choice | canonical | target_penalty_hard_2_0 | -0.290, fail | -0.804, fail |

This shows the shape of the tradeoff: hard-control subtraction can protect positives from the known adversarial direction, but a separate valence-channel remains unless the penalty is strong enough to damage positives.

## Diagnosis

Accepted:

```text
A hard-control penalty can preserve positive alias/canonical target movement while
substantially reducing valence-control movement.
```

Accepted:

```text
The `valence->steering_vector` channel is more useful as an explicit adversarial
basis than as one member of a mean control basis.
```

Rejected:

```text
Mean-control subtraction is sufficient for semantic specificity.
```

Withheld:

```text
The constrained direction is fully concept-specific.
```

Best current interpretation:

```text
Behavior-addressable alias directions contain separable adversarial control
subchannels. Penalizing a named hard-control channel improves specificity without
destroying positives, but the remaining valence->activation_vector leakage shows
that one adversarial direction is not enough.
```

This is more promising than post-hoc residualization. We now have a direction-construction lever that creates a measurable specificity/strength frontier. The publishable version needs held-out adversarial controls and a multi-control constrained objective, not just one manually chosen hard-control basis.

## Next Move

- Add a multi-control constrained objective with a small penalty sweep, including both valence controls as independent adversarial bases.
- Add second aliases or held-out alias phrases so adversarial penalties are not evaluated on the same lexical surface used to build them.
- Promote a specificity frontier metric: positive mean retained versus independent control mean suppressed.
- Replicate the best frontier point on a second seed/checkpoint before treating it as a mechanism.

## Discovery-Regime Audit

Question: can a named adversarial-control penalty make alias-trained behavior directions more specific without destroying positive concept movement?

Current regime:

- Artifact types: alias-label manifests, full-label gradient directions, constrained direction modes, canonical/alias eval rows, adversarial-control tables.
- Operations: train-variant full-label gradient averaging, norm-matched hard-control subtraction, held-out full-label continuation scoring, prompt-frame replication.
- Gates/verifiers: positives must remain robust; independent valence controls should be suppressed; construction-zeroed controls are sanity checks, not independent successes.
- Known limitations: one seed, one model, one manually chosen hard-control channel, one alias per concept.

Action class:

- Retrieval/search/discovery: search with a promising new operation.
- Why: this adds an adversarial-control direction-construction operation and produces a specificity frontier that post-hoc residualization did not expose.

Experiment:

- Manifest/report paths: this report; local ignored payloads under `artifacts/activation_geometry/modal_pythia_70m_constrained_alias_direction_*.json`.
- Positive targets: promoted steering pairs.
- Negative controls: `valence->activation_vector`, `valence->steering_vector`, mean-control penalty, random same-norm controls, control layer.
- Stress tests: prompt frames `source_passage` and `latent_choice`; eval labels `alias` and `canonical`; scales `0.5,1.0,2.0`.

Gate:

- Acceptance rule: accept a constrained-direction improvement if positives remain `3/3` while independent valence-control means fall substantially below raw target-learned means.
- Withheld/rejected rule: withhold full semantic specificity if any independent valence control still passes or if suppression depends on construction-zeroing.

Results:

- Accepted artifacts: hard-control penalty direction modes; this report.
- Rejected or withheld artifacts: full semantic specificity remains withheld; mean-control subtraction is rejected as insufficient.
- Key metrics: at scale `1.0`, `target_penalty_hard_1_0` keeps `3/3` positives in both prompt frames and both eval regimes; it reduces mean valence-control deltas by `69.0%` to `95.6%`; `valence->activation_vector` still passes.
- Variance or ablation: hard penalty `2.0` suppresses controls more strongly but damages canonical positives; mean-control penalty preserves positives but leaves controls passing.

Residual content:

- Explained by old regime: behavior gradients can move labels and simple projections attenuate leakage.
- New content outside old regime: a named adversarial-control penalty exposes a tunable specificity/strength frontier.
- Retractions or supersessions: supersede "post-hoc residualization is the best available cleanup" with "constrained direction construction is the more promising path."

Next move: build a multi-control constrained objective and evaluate it against held-out aliases/controls.
