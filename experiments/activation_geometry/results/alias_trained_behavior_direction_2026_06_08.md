# Alias-Trained Behavior Direction - 2026-06-08

## Question

The alias gate showed that raw canonical-definition patch vectors do not produce globally target-specific alias behavior. This run asks whether the failure is caused by the intervention, rather than by the model's behavior surface:

```text
Can we learn a behavior-aligned direction directly against alias labels, and
does that direction also transfer to canonical labels?
```

## Method

Raw payloads remain local-only under ignored `artifacts/`.

Payloads:

```text
artifacts/activation_geometry/modal_pythia_70m_alias_trained_direction_seed20260608.json
artifacts/activation_geometry/modal_pythia_70m_alias_trained_direction_source_seed20260608.json
```

Grid:

- Model: `EleutherAI/pythia-70m-deduped`
- Scoring surface: `full_label`
- Objective label scoring regime: `alias`
- Eval label scoring regimes: `alias`, `canonical`
- Prompt frames: `latent_choice`, `source_passage`
- Layers: primary `5`, backup `6`, control `1`
- Train variants: `0,1`
- Held-out variant: `2`
- Scales: `0.5,1.0,2.0`
- Directions: `target_learned`, `source_learned`, `distractor_learned`, `random_same_norm`
- Label score normalization: mean logprob per label token
- Seed: `20260608`

The learned direction is the mean gradient of a full-label continuation margin:

```text
target label score - 0.5 * (source label score + distractor label score)
```

For this run, the objective labels are aliases such as `stable-state network` rather than the canonical labels such as `attractor network`. The same learned direction is then evaluated against both alias and canonical label continuations.

Commands:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_behavior_aligned_direction.py --model-id EleutherAI/pythia-70m-deduped --primary-layer 5 --backup-layer 6 --control-layer 1 --max-length 180 --train-variants 0,1 --holdout-variant 2 --scales 0.5,1.0,2.0 --direction-modes target_learned,source_learned,distractor_learned,random_same_norm --scoring-surface full_label --prompt-frame latent_choice --objective-label-scoring-regimes alias --eval-label-scoring-regimes alias,canonical --label-score-normalization mean --aliases experiments/concept_geometry/concept_aliases.json --seed 20260608 --out artifacts/activation_geometry/modal_pythia_70m_alias_trained_direction_seed20260608.json
```

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_behavior_aligned_direction.py --model-id EleutherAI/pythia-70m-deduped --primary-layer 5 --backup-layer 6 --control-layer 1 --max-length 180 --train-variants 0,1 --holdout-variant 2 --scales 0.5,1.0,2.0 --direction-modes target_learned,source_learned,distractor_learned,random_same_norm --scoring-surface full_label --prompt-frame source_passage --objective-label-scoring-regimes alias --eval-label-scoring-regimes alias,canonical --label-score-normalization mean --aliases experiments/concept_geometry/concept_aliases.json --seed 20260608 --out artifacts/activation_geometry/modal_pythia_70m_alias_trained_direction_source_seed20260608.json
```

## Results

### Gate Summary

Target-learned alias directions pass every positive pair in both frames and both eval label regimes. They also pass every backup-layer positive, every control-layer positive, and both primary valence controls.

| Prompt frame | Eval labels | Scale | Target primary positives | Target backup positives | Target control-layer positives | Target valence controls |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| latent_choice | alias | 0.5 | 3/3 | 3/3 | 3/3 | 2/2 |
| latent_choice | alias | 1.0 | 3/3 | 3/3 | 3/3 | 2/2 |
| latent_choice | alias | 2.0 | 3/3 | 3/3 | 3/3 | 2/2 |
| latent_choice | canonical | 0.5 | 3/3 | 3/3 | 3/3 | 2/2 |
| latent_choice | canonical | 1.0 | 3/3 | 3/3 | 3/3 | 2/2 |
| latent_choice | canonical | 2.0 | 3/3 | 3/3 | 3/3 | 2/2 |
| source_passage | alias | 0.5 | 3/3 | 3/3 | 3/3 | 2/2 |
| source_passage | alias | 1.0 | 3/3 | 3/3 | 3/3 | 2/2 |
| source_passage | alias | 2.0 | 3/3 | 3/3 | 3/3 | 2/2 |
| source_passage | canonical | 0.5 | 3/3 | 3/3 | 3/3 | 2/2 |
| source_passage | canonical | 1.0 | 3/3 | 3/3 | 3/3 | 2/2 |
| source_passage | canonical | 2.0 | 3/3 | 3/3 | 3/3 | 2/2 |

### Mean Primary Positive Deltas

| Prompt frame | Eval labels | Scale | Target learned | Source learned | Distractor learned | Random same norm |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| latent_choice | alias | 0.5 | 0.793 | -0.292 | -0.468 | 0.020 |
| latent_choice | alias | 1.0 | 1.591 | -0.568 | -0.911 | -0.117 |
| latent_choice | alias | 2.0 | 3.116 | -1.059 | -1.711 | 0.116 |
| latent_choice | canonical | 0.5 | 0.345 | -0.194 | -0.142 | -0.013 |
| latent_choice | canonical | 1.0 | 0.690 | -0.382 | -0.272 | 0.017 |
| latent_choice | canonical | 2.0 | 1.319 | -0.731 | -0.491 | 0.054 |
| source_passage | alias | 0.5 | 0.633 | -0.249 | -0.391 | 0.009 |
| source_passage | alias | 1.0 | 1.231 | -0.508 | -0.760 | -0.089 |
| source_passage | alias | 2.0 | 2.294 | -1.064 | -1.459 | 0.060 |
| source_passage | canonical | 0.5 | 0.312 | -0.216 | -0.108 | 0.015 |
| source_passage | canonical | 1.0 | 0.605 | -0.438 | -0.222 | 0.039 |
| source_passage | canonical | 2.0 | 1.120 | -0.903 | -0.479 | -0.084 |

Target-learned directions dominate source-learned, distractor-learned, and random directions. The sign and scale response are clean: larger target-direction scales create larger positive target-margin deltas, while source/distractor directions suppress target margins.

### Leakage Diagnosis

The same target-learned directions are not concept-specific enough.

Mean primary valence-control deltas are larger than the intended positive-pair deltas:

| Prompt frame | Eval labels | Scale | Positive target mean | Valence-control target mean |
| --- | --- | ---: | ---: | ---: |
| latent_choice | alias | 0.5 | 0.793 | 1.274 |
| latent_choice | alias | 1.0 | 1.591 | 2.517 |
| latent_choice | alias | 2.0 | 3.116 | 4.828 |
| latent_choice | canonical | 0.5 | 0.345 | 0.497 |
| latent_choice | canonical | 1.0 | 0.690 | 1.010 |
| latent_choice | canonical | 2.0 | 1.319 | 2.043 |
| source_passage | alias | 0.5 | 0.633 | 0.940 |
| source_passage | alias | 1.0 | 1.231 | 1.848 |
| source_passage | alias | 2.0 | 2.294 | 3.541 |
| source_passage | canonical | 0.5 | 0.312 | 0.381 |
| source_passage | canonical | 1.0 | 0.605 | 0.776 |
| source_passage | canonical | 2.0 | 1.120 | 1.607 |

Control layer `1` also passes every positive pair for `target_learned` in both frames and eval regimes. This means the intervention is not localized to the previously identified hook-output transfer ridge.

## Diagnosis

Accepted:

```text
Alias full-label behavior objectives are highly addressable by learned activation
directions.
```

Accepted:

```text
Directions learned against alias labels transfer to canonical-label scoring.
```

Accepted:

```text
Target-learned alias directions are directionally meaningful: source-learned and
distractor-learned controls tend to move the target margin in the opposite direction,
and random same-norm controls are much weaker.
```

Withheld:

```text
Alias-trained behavior directions are evidence of concept-specific semantic
transport.
```

Best current interpretation:

```text
Alias-trained behavior directions expose an output-control interface for concept
labels. They solve the alias addressability problem, but they do not yet solve the
semantic-specificity problem.
```

This is still a useful result. The earlier alias gate showed raw transported states cannot reliably move aliases. This run shows the model can be steered toward alias labels when we optimize the behavior surface directly. The missing ingredient is not "aliases are impossible"; it is "we need a direction that is both behavior-addressable and semantically constrained."

## Next Move

The next breakthrough path is a contrastive or residualized direction, not another direct target gradient:

- Learn alias target directions and subtract source/distractor/control-label components.
- Penalize valence-control movement during direction construction.
- Test whether a residual direction preserves positive-pair alias movement while reducing valence and control-layer leakage.
- Compare residualized behavior directions against raw transported definition-state vectors.

## Discovery-Regime Audit

Question: can alias-label behavior be made addressable by learning behavior-aligned directions directly against alias objectives?

Current regime:

- Artifact types: alias-label manifests, full-label gradient directions, canonical/alias eval rows, direction-control rows, leakage tables.
- Operations: train-variant full-label gradient averaging, held-out full-label continuation scoring, cross-label evaluation, source/distractor/random direction controls.
- Gates/verifiers: target-learned direction should beat source/distractor/random controls; alias-trained direction should improve alias labels and transfer to canonical labels; semantic claims require avoiding valence and control-layer leakage.
- Known limitations: one seed, one model, per-pair learned directions, no residualization, no second alias per concept yet.

Action class:

- Retrieval/search/discovery: intervention search with rejected mechanism claim.
- Why: this adds alias full-label gradients as an intervention class, but the resulting direction fails semantic-specificity controls.

Experiment:

- Manifest/report paths: this report; local ignored payloads under `artifacts/activation_geometry/modal_pythia_70m_alias_trained_direction*.json`.
- Positive targets: promoted steering pairs.
- Negative controls: source-learned, distractor-learned, random-same-norm directions; valence-control pairs; control layer.
- Stress tests: prompt frames `latent_choice` and `source_passage`; eval labels `alias` and `canonical`; scales `0.5,1.0,2.0`.

Gate:

- Acceptance rule: accept alias addressability if target-learned directions reliably improve alias target margins and beat source/distractor/random directions.
- Withheld/rejected rule: withhold semantic transport if valence controls or control-layer positives pass at comparable strength.

Results:

- Accepted artifacts: full-label alias objective support in the learned-direction runner; this report.
- Rejected or withheld artifacts: semantic transport claim remains withheld.
- Key metrics: target-learned directions pass `3/3` primary positives for both prompt frames, all scales, and both eval label regimes; source/distractor directions are negative on mean; target-learned valence controls pass `2/2` and control-layer positives pass `3/3`.
- Variance or ablation: source-passage and latent-choice frames agree; alias-trained directions also transfer to canonical scoring.

Residual content:

- Explained by old regime: direct behavior gradients can control label logits.
- New content outside old regime: alias-label behavior is addressable and cross-label transferable, but only through a leaky output-control direction.
- Retractions or supersessions: supersede "alias labels may be unreachable behaviorally" with "alias labels are behaviorally reachable, but raw transported states and direct gradients occupy different regimes."

Next move: build residualized alias directions that subtract source/distractor/control components, then rerun the alias gate against leakage controls.
