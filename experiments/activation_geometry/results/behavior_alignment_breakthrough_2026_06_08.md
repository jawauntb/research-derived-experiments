# Behavior Alignment Breakthrough Path - 2026-06-08

## Question

After the option-token behavior gate failed, is the failure caused by the behavior surface, by the raw patch intervention, or by both?

This run follows the two most promising next shots:

- Score full concept labels as continuations instead of option letters.
- Learn behavior-aligned directions from train variants and test them on held-out variants.

## Method

Raw payloads remain local-only under ignored `artifacts/`.

Payloads:

```text
artifacts/activation_geometry/modal_pythia_70m_full_label_behavior_seed20260608.json
artifacts/activation_geometry/modal_pythia_70m_full_label_behavior_source_seed20260608.json
artifacts/activation_geometry/modal_pythia_70m_behavior_aligned_direction_seed20260608.json
```

Full-label grid:

- Model: `EleutherAI/pythia-70m-deduped`
- Patch-vector surface: `hook_output`
- Injection layers: `4,5,6`
- Patch alphas: `0.75,1.0`
- Pair set: `combined`
- Baseline pairs: 8 sampled ordered concept pairs
- Total pairs: 15
- Patch text regimes: `definition`, `neutral`
- Patch modes: `target`, `distractor`, `random`, `source_noop`
- Prompt frames: `latent_choice`, `source_passage`
- Scoring surface: `full_label`
- Label score normalization: mean logprob per label token
- Eval variant: `2`
- Seed: `20260608`

Learned-direction grid:

- Model: `EleutherAI/pythia-70m-deduped`
- Layers: primary `5`, backup `6`, control `1`
- Train variants: `0,1`
- Held-out variant: `2`
- Scales: `0.5,1.0,2.0`
- Directions: `target_learned`, `source_learned`, `distractor_learned`, `random_same_norm`
- Option orders: `std,tds,dst`
- Seed: `20260608`

Commands:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_label_free_behavior_gate.py --model-id EleutherAI/pythia-70m-deduped --injection-layers 4,5,6 --max-length 180 --eval-variant 2 --patch-alphas 0.75,1.0 --patch-modes target,distractor,random,source_noop --patch-text-regimes definition,neutral --patch-vector-surface hook_output --prompt-frame latent_choice --scoring-surface full_label --label-score-normalization mean --pair-set combined --baseline-sample-count 8 --seed 20260608 --out artifacts/activation_geometry/modal_pythia_70m_full_label_behavior_seed20260608.json
```

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_label_free_behavior_gate.py --model-id EleutherAI/pythia-70m-deduped --injection-layers 4,5,6 --max-length 180 --eval-variant 2 --patch-alphas 0.75,1.0 --patch-modes target,distractor,random,source_noop --patch-text-regimes definition,neutral --patch-vector-surface hook_output --prompt-frame source_passage --scoring-surface full_label --label-score-normalization mean --pair-set combined --baseline-sample-count 8 --seed 20260608 --out artifacts/activation_geometry/modal_pythia_70m_full_label_behavior_source_seed20260608.json
```

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_behavior_aligned_direction.py --model-id EleutherAI/pythia-70m-deduped --primary-layer 5 --backup-layer 6 --control-layer 1 --max-length 128 --train-variants 0,1 --holdout-variant 2 --scales 0.5,1.0,2.0 --direction-modes target_learned,source_learned,distractor_learned,random_same_norm --option-orders std,tds,dst --seed 20260608 --out artifacts/activation_geometry/modal_pythia_70m_behavior_aligned_direction_seed20260608.json
```

## Full-Label Behavior Gate

The option-token behavior gate failed, but the full-label behavior gate does not. Definition target patches beat distractor/random/source-noop controls across both prompt frames.

| Prompt frame | Layer | Alpha | Definition passes | Definition mean delta | Definition mean advantage | Neutral passes | Neutral mean advantage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| latent_choice | 4 | 0.75 | 9/15 | 0.613 | 0.249 | 7/15 | 0.120 |
| latent_choice | 4 | 1.00 | 11/15 | 0.820 | 0.378 | 8/15 | 0.051 |
| latent_choice | 5 | 0.75 | 9/15 | 0.762 | 0.521 | 7/15 | 0.172 |
| latent_choice | 5 | 1.00 | 9/15 | 0.982 | 0.622 | 7/15 | 0.204 |
| latent_choice | 6 | 0.75 | 9/15 | 0.787 | 0.668 | 7/15 | 0.268 |
| latent_choice | 6 | 1.00 | 9/15 | 1.194 | 0.881 | 10/15 | 0.405 |
| source_passage | 4 | 0.75 | 9/15 | 2.098 | 0.189 | 9/15 | 0.119 |
| source_passage | 4 | 1.00 | 10/15 | 2.691 | 0.341 | 9/15 | 0.050 |
| source_passage | 5 | 0.75 | 12/15 | 2.113 | 0.532 | 11/15 | 0.175 |
| source_passage | 5 | 1.00 | 12/15 | 2.983 | 0.646 | 9/15 | 0.203 |
| source_passage | 6 | 0.75 | 12/15 | 2.191 | 0.649 | 12/15 | 0.252 |
| source_passage | 6 | 1.00 | 10/15 | 3.280 | 0.881 | 12/15 | 0.405 |

Definition carriers beat neutral carriers on average in every cell. The mean definition-minus-neutral advantage ranges from `0.071` to `0.476`, and the mean definition-minus-neutral target-margin delta ranges from `0.295` to `0.706`.

The strongest clean-looking cells are:

- `latent_choice`, layer `6`, alpha `1.0`: definition `9/15`, mean advantage `0.881`, neutral mean advantage `0.405`.
- `source_passage`, layer `5`, alpha `1.0`: definition `12/15`, mean advantage `0.646`, neutral mean advantage `0.203`.
- `source_passage`, layer `6`, alpha `0.75`: definition `12/15`, mean advantage `0.649`, neutral mean advantage `0.252`.

Interpretation: the old behavior failure was at least partly an option-token answer-surface failure. When the model is scored on full concept labels, raw hook-output definition patches do produce target-specific behavior-level movement above distractor/random/source-noop controls.

## Neutral Carrier Caveat

The neutral carrier is not inert. It often improves target full-label margins too, especially in the source-passage frame. This prevents a clean semantic-causality claim.

The current accepted claim should be narrow:

```text
Full-label continuation scoring reveals behavior-level target movement that
the option-token gate missed.
```

The stronger claim remains withheld:

```text
The movement is purely semantic rather than partly label-carrier or activation
norm/format driven.
```

## Learned Behavior-Aligned Direction

The learned-direction pilot averages gradients for target/source/distractor objectives on train variants `0,1`, then evaluates on held-out variant `2`.

Target-learned directions pass all three positive pairs at the primary layer for every tested scale:

| Scale | Primary positive target-learned passes | Mean primary positive target delta | Primary valence-control passes | Control-layer positive passes |
| ---: | ---: | ---: | ---: | ---: |
| 0.5 | 3/3 | 0.036 | 2/2 | 3/3 |
| 1.0 | 3/3 | 0.047 | 2/2 | 2/3 |
| 2.0 | 3/3 | 0.054 | 1/2 | 1/3 |

Pair-level primary target-learned deltas:

| Pair | Scale 0.5 | Scale 1.0 | Scale 2.0 |
| --- | ---: | ---: | ---: |
| attractor->attractor_network | 0.014 | 0.016 | 0.009 |
| autopoiesis->homeostasis | 0.083 | 0.104 | 0.104 |
| validity_gate->weak_constraint | 0.011 | 0.021 | 0.050 |

This is a weak but real behavior-aligned intervention signal. It is not yet a clean concept-specific mechanism because valence controls and control-layer positives can also pass. The effect size is also far smaller than the full-label raw-state intervention.

Accepted artifact: a reusable learned-direction pilot.

Withheld claim: learned directions solve the behavior-alignment problem.

## Diagnosis

This run creates a sharper three-part diagnosis:

1. Option-token scoring was too brittle. Full-label continuation scoring recovers behavior-level target movement.
2. Raw definition-state patching can cross into behavior under the right scoring surface.
3. Behavior-learned gradients are promising but not cleanly specific yet.

The most paper-relevant new result is the answer-surface split:

```text
Representational transport looked behaviorally inert under option-letter scoring,
but becomes behaviorally visible under full concept-label scoring.
```

That suggests a stronger research question:

```text
When does transported activation geometry become behaviorally addressable, and
which behavioral surfaces expose or hide it?
```

## Next Move

The next experiment should tighten the neutral-carrier problem before we claim a semantic behavior mechanism:

- Replicate the full-label gate with a second seed and second open model.
- Add label-only, shuffled-label, and length-matched carrier controls.
- Score aliases/paraphrased labels so success is not tied to one exact label string.
- Learn behavior directions against the full-label objective rather than the option-token objective.
- Compare pair-level readout deltas against full-label behavior deltas to predict which transported states are behavior-addressable.

## Discovery-Regime Audit

Question: after the option-token behavior gate failed, can full-label scoring or learned behavior-aligned directions expose behavior-level transfer?

Current regime:

- Artifact types: hook-output patch payloads, option-token behavior rows, full-label continuation rows, learned-gradient direction rows, target-vs-control specificity summaries.
- Operations: label-free definition/neutral state capture, final-token hook-output replacement, full-label continuation logprob scoring, train-variant gradient averaging, held-out option-token intervention.
- Gates/verifiers: target must beat distractor/random/source-noop controls; definition should exceed neutral carrier; learned target direction should exceed source/distractor/random directions and avoid valence/control-layer leakage.
- Known limitations: one seed, one small causal LM, exact-label scoring, neutral carriers are active, learned directions are still option-token based.

Action class:

- Retrieval/search/discovery: verifier transition plus intervention search.
- Why: full-label scoring creates a new behavior verifier that accepts effects the previous option-token verifier rejected; learned directions add a new behavior-aligned intervention class.

Experiment:

- Manifest/report paths: this report; local ignored payloads under `artifacts/activation_geometry/modal_pythia_70m_full_label_behavior*.json` and `artifacts/activation_geometry/modal_pythia_70m_behavior_aligned_direction_seed20260608.json`.
- Positive targets: focus rows plus 8 sampled baseline pairs for full-label; promoted steering pairs for learned directions.
- Negative controls: neutral patch text, distractor/random/source-noop patch modes, source/distractor learned directions, random same-norm direction, valence controls, control layer.
- Stress tests: prompt frames `latent_choice` and `source_passage`; injection layers `4,5,6`; alphas `0.75,1.0`; learned scales `0.5,1.0,2.0`.

Gate:

- Acceptance rule: accept behavior-surface improvement if definition target patches beat controls and definition carriers exceed neutral carriers on average.
- Withheld/rejected rule: withhold clean semantic-causality or learned-direction claims if neutral carriers, valence controls, or control-layer directions match too much of the effect.

Results:

- Accepted artifacts: full-label behavior scoring surface; learned behavior-aligned direction pilot; Modal packaging fix for learned-direction runner.
- Rejected or withheld artifacts: clean semantic-causality claim and learned-direction mechanism claim remain withheld.
- Key metrics: full-label definition target patches pass up to `12/15`, with mean target-over-control advantage up to `0.881`; definition exceeds neutral mean advantage in every full-label cell; learned target direction passes `3/3` primary positives at all scales but also shows control leakage.
- Variance or ablation: source-passage and latent-choice frames both show full-label movement; neutral carrier and learned-direction controls expose remaining confounds.

Residual content:

- Explained by old regime: broad definition-derived transfer remains generic and label carriers can move behavior surfaces.
- New content outside old regime: the behavior-level negative result is surface-dependent; full-label continuation scoring exposes a behavior-visible effect.
- Retractions or supersessions: supersede "raw state replacement fails behavior-level gates" with "raw state replacement fails option-token gates but passes full-label behavior gates with neutral-carrier caveats."

Next move: replicate full-label behavior gates with stronger carrier/label controls and learn directions against the full-label objective.
