# Residualized Alias Direction - 2026-06-08

## Question

The alias-trained behavior direction run showed that alias labels are behavior-addressable and transfer to canonical scoring, but direct target gradients leak through valence controls and control-layer positives. This run asks:

```text
Can simple residualization preserve alias-trained positive movement while removing
generic valence/control-label leakage?
```

## Method

Raw payloads remain local-only under ignored `artifacts/`.

Payloads:

```text
artifacts/activation_geometry/modal_pythia_70m_residualized_alias_direction_latent_seed20260608.json
artifacts/activation_geometry/modal_pythia_70m_residualized_alias_direction_source_seed20260608.json
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
- Label score normalization: mean logprob per label token
- Seed: `20260608`

Direction modes:

- `target_learned`: raw alias target-margin gradient.
- `target_resid_sd`: target direction with projections onto source and distractor learned directions removed.
- `target_resid_control`: target direction with projection onto a leave-one-out mean valence-control target direction removed.
- `target_resid_all`: control residualization followed by source/distractor projection removal.
- `random_same_norm`: same-norm random direction.

All residual directions are rescaled to the original target-direction norm, so scale comparisons remain meaningful.

Commands:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_behavior_aligned_direction.py --model-id EleutherAI/pythia-70m-deduped --primary-layer 5 --backup-layer 6 --control-layer 1 --max-length 180 --train-variants 0,1 --holdout-variant 2 --scales 0.5,1.0,2.0 --direction-modes target_learned,target_resid_sd,target_resid_control,target_resid_all,random_same_norm --scoring-surface full_label --prompt-frame latent_choice --objective-label-scoring-regimes alias --eval-label-scoring-regimes alias,canonical --label-score-normalization mean --aliases experiments/concept_geometry/concept_aliases.json --seed 20260608 --out artifacts/activation_geometry/modal_pythia_70m_residualized_alias_direction_latent_seed20260608.json
```

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_behavior_aligned_direction.py --model-id EleutherAI/pythia-70m-deduped --primary-layer 5 --backup-layer 6 --control-layer 1 --max-length 180 --train-variants 0,1 --holdout-variant 2 --scales 0.5,1.0,2.0 --direction-modes target_learned,target_resid_sd,target_resid_control,target_resid_all,random_same_norm --scoring-surface full_label --prompt-frame source_passage --objective-label-scoring-regimes alias --eval-label-scoring-regimes alias,canonical --label-score-normalization mean --aliases experiments/concept_geometry/concept_aliases.json --seed 20260608 --out artifacts/activation_geometry/modal_pythia_70m_residualized_alias_direction_source_seed20260608.json
```

The first source-passage attempt hit a Modal client heartbeat/DNS timeout; the rerun completed with the same manifest.

## Results

### Scale 1 Primary Layer

`target_resid_all` is the strongest residual mode. It preserves positive-pair passes, but it does not clear the leakage gate.

| Prompt frame | Eval labels | Direction | Positive passes | Positive mean | Valence-control passes | Valence-control mean |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| latent_choice | alias | target_learned | 3/3 | 1.591 | 2/2 | 2.517 |
| latent_choice | alias | target_resid_sd | 3/3 | 1.248 | 2/2 | 2.311 |
| latent_choice | alias | target_resid_control | 3/3 | 1.583 | 2/2 | 2.156 |
| latent_choice | alias | target_resid_all | 3/3 | 1.197 | 2/2 | 1.365 |
| latent_choice | alias | random_same_norm | 2/3 | -0.029 | 1/2 | -0.029 |
| latent_choice | canonical | target_learned | 3/3 | 0.690 | 2/2 | 1.010 |
| latent_choice | canonical | target_resid_sd | 3/3 | 0.597 | 2/2 | 0.905 |
| latent_choice | canonical | target_resid_control | 3/3 | 0.666 | 2/2 | 1.014 |
| latent_choice | canonical | target_resid_all | 3/3 | 0.522 | 2/2 | 0.777 |
| latent_choice | canonical | random_same_norm | 2/3 | -0.052 | 1/2 | 0.013 |
| source_passage | alias | target_learned | 3/3 | 1.231 | 2/2 | 1.848 |
| source_passage | alias | target_resid_sd | 3/3 | 0.987 | 2/2 | 1.586 |
| source_passage | alias | target_resid_control | 3/3 | 1.229 | 2/2 | 1.662 |
| source_passage | alias | target_resid_all | 3/3 | 0.974 | 2/2 | 1.008 |
| source_passage | alias | random_same_norm | 2/3 | 0.006 | 1/2 | 0.023 |
| source_passage | canonical | target_learned | 3/3 | 0.604 | 2/2 | 0.775 |
| source_passage | canonical | target_resid_sd | 3/3 | 0.600 | 2/2 | 0.508 |
| source_passage | canonical | target_resid_control | 3/3 | 0.588 | 2/2 | 0.735 |
| source_passage | canonical | target_resid_all | 3/3 | 0.548 | 1/2 | 0.392 |
| source_passage | canonical | random_same_norm | 2/3 | 0.011 | 2/2 | 0.056 |

### What Improved

The combined residual mode consistently attenuates control movement:

| Prompt frame | Eval labels | Raw control mean | All-residual control mean | Reduction |
| --- | --- | ---: | ---: | ---: |
| latent_choice | alias | 2.517 | 1.365 | 45.8% |
| latent_choice | canonical | 1.010 | 0.777 | 23.1% |
| source_passage | alias | 1.848 | 1.008 | 45.5% |
| source_passage | canonical | 0.775 | 0.392 | 49.4% |

The source-passage canonical setting is the closest partial success: `target_resid_all` keeps `3/3` positives and drops valence controls from `2/2` to `1/2`. But this does not survive alias scoring, and it does not survive higher scale as a clean pass-rate gate.

### Hard Control Channel

At scale `1.0`, source-passage canonical scoring under `target_resid_all` splits the valence controls:

| Pair | Kind | Pass | Mean target-margin delta |
| --- | --- | --- | ---: |
| valence->activation_vector | control | false | -0.008 |
| valence->steering_vector | control | true | 0.791 |
| attractor->attractor_network | positive | true | 0.028 |
| autopoiesis->homeostasis | positive | true | 0.801 |
| validity_gate->weak_constraint | positive | true | 0.816 |

This is the most useful diagnostic in the run. Simple residualization can suppress one valence-control pathway, but `valence->steering_vector` remains as strong as the best positives. Also, the `attractor->attractor_network` positive becomes nearly zero while still technically passing, so the residual is not isolating a uniformly semantic mechanism.

## Diagnosis

Accepted:

```text
Projection residualization attenuates alias-trained control leakage while preserving
positive-pair pass counts.
```

Accepted:

```text
The strongest residual mode is the combined control/source/distractor residual,
not either residual family alone.
```

Rejected:

```text
Valence/control leakage is just a single removable linear component.
```

Withheld:

```text
Residualized alias directions are concept-specific semantic transport directions.
```

Best current interpretation:

```text
The behavior-aligned alias direction lives in an output-control geometry where
positive concept movement and valence/control movement are partially entangled.
Post-hoc linear projection reduces the broad leak but does not separate the
semantic channel.
```

This is a useful boundary. The next likely breakthrough is not another projection variant. It is a direction-construction objective with leakage penalties built in, or a learned low-dimensional behavior subspace where control channels are estimated and rejected before intervention.

## Next Move

- Build a constrained behavior direction that optimizes positive-pair alias/canonical target movement while explicitly penalizing valence-control target movement during gradient construction.
- Treat `valence->steering_vector` as the adversarial control, not a generic side check.
- Add second-alias and alias-shuffle controls so the learned direction cannot win by overfitting the first alias phrase.
- Compare constrained behavior directions against transported hook-output states on the same source/canonical partial-success setting.

## Discovery-Regime Audit

Question: can simple residualization make alias-trained behavior directions less leaky without losing positive concept movement?

Current regime:

- Artifact types: alias-label manifests, full-label gradient directions, residualized direction modes, canonical/alias eval rows, leakage tables.
- Operations: train-variant full-label gradient averaging, projection residualization, leave-one-out control-basis construction, held-out full-label continuation scoring.
- Gates/verifiers: positive pairs must pass in primary/backup layers; valence controls and control-layer positives must not pass at comparable strength; residual modes should improve target-over-control specificity.
- Known limitations: one seed, one model, one alias per concept, post-hoc linear residuals only.

Action class:

- Retrieval/search/discovery: search with a rejected simplification.
- Why: this adds residualized direction modes inside the existing behavior-direction schema and tests whether leakage is linearly removable.

Experiment:

- Manifest/report paths: this report; local ignored payloads under `artifacts/activation_geometry/modal_pythia_70m_residualized_alias_direction_*.json`.
- Positive targets: promoted steering pairs.
- Negative controls: same-norm random directions; valence-control pairs; control layer.
- Stress tests: prompt frames `latent_choice` and `source_passage`; eval labels `alias` and `canonical`; scales `0.5,1.0,2.0`.

Gate:

- Acceptance rule: promote residualized semantic transport only if positive pairs remain robust while primary valence controls and control-layer positives fail or become much weaker than positives.
- Withheld/rejected rule: withhold semantic claims if controls still pass, even when their mean deltas are attenuated.

Results:

- Accepted artifacts: residualized direction modes in the learned-direction runner; this report.
- Rejected or withheld artifacts: the simple linear-removal explanation is rejected; semantic transport remains withheld.
- Key metrics: `target_resid_all` keeps `3/3` primary positives in every frame/eval setting at scale `1.0`; it reduces valence-control means by `23.1%` to `49.4%`; controls still pass `2/2` except source-passage canonical, where they drop to `1/2`.
- Variance or ablation: source/distractor-only and control-only residuals are weaker than the combined residual; source-passage canonical is cleaner than alias scoring.

Residual content:

- Explained by old regime: behavior gradients can move target labels and random directions are much weaker.
- New content outside old regime: leakage has at least two distinguishable channels; `valence->activation_vector` can be suppressed in one setting, but `valence->steering_vector` remains adversarial.
- Retractions or supersessions: supersede "subtract a generic control component" with "post-hoc projection is only an attenuation method, not a specificity method."

Next move: replace post-hoc residualization with a constrained behavior objective that penalizes `valence->steering_vector` during direction construction.
