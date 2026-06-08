# Full-Label Carrier Controls - 2026-06-08

## Question

The full-label behavior gate exposed target-specific behavior that the option-letter gate missed. But neutral label carriers were also active. This run asks whether the effect is semantic, label-copy pressure, arbitrary carrier/norm movement, or some combination.

## Method

Raw payloads remain local-only under ignored `artifacts/`.

Payloads:

```text
artifacts/activation_geometry/modal_pythia_70m_full_label_carrier_controls_latent_seed20260608.json
artifacts/activation_geometry/modal_pythia_70m_full_label_carrier_controls_source_seed20260608.json
```

Grid:

- Model: `EleutherAI/pythia-70m-deduped`
- Patch-vector surface: `hook_output`
- Injection layers: `5,6`
- Patch alpha: `1.0`
- Pair set: `combined`
- Baseline pairs: 8 sampled ordered concept pairs
- Total pairs: 15
- Patch modes: `target`, `distractor`, `random`, `source_noop`
- Prompt frames: `latent_choice`, `source_passage`
- Scoring surface: `full_label`
- Label score normalization: mean logprob per label token
- Eval variant: `2`
- Seed: `20260608`

Patch-text regimes:

- `definition`: the original concept definition text, usually including the label prefix.
- `definition_without_label`: the definition text with a leading `<label>:` prefix stripped when present.
- `neutral`: `Concept label: <label>.`
- `label_only`: just `<label>`.
- `blank_carrier`: `Concept label: [omitted].`
- `shuffled_label`: `Concept label: <different label>.`

Commands:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_label_free_behavior_gate.py --model-id EleutherAI/pythia-70m-deduped --injection-layers 5,6 --max-length 180 --eval-variant 2 --patch-alphas 1.0 --patch-modes target,distractor,random,source_noop --patch-text-regimes definition,definition_without_label,neutral,label_only,blank_carrier,shuffled_label --patch-vector-surface hook_output --prompt-frame latent_choice --scoring-surface full_label --label-score-normalization mean --pair-set combined --baseline-sample-count 8 --seed 20260608 --out artifacts/activation_geometry/modal_pythia_70m_full_label_carrier_controls_latent_seed20260608.json
```

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_label_free_behavior_gate.py --model-id EleutherAI/pythia-70m-deduped --injection-layers 5,6 --max-length 180 --eval-variant 2 --patch-alphas 1.0 --patch-modes target,distractor,random,source_noop --patch-text-regimes definition,definition_without_label,neutral,label_only,blank_carrier,shuffled_label --patch-vector-surface hook_output --prompt-frame source_passage --scoring-surface full_label --label-score-normalization mean --pair-set combined --baseline-sample-count 8 --seed 20260608 --out artifacts/activation_geometry/modal_pythia_70m_full_label_carrier_controls_source_seed20260608.json
```

## Results

### Latent Choice

| Regime | Layer | Specific passes | Mean target-margin delta | Mean target-over-control advantage |
| --- | ---: | ---: | ---: | ---: |
| definition | 5 | 9/15 | 0.982 | 0.622 |
| definition | 6 | 9/15 | 1.194 | 0.881 |
| definition_without_label | 5 | 5/15 | 0.450 | -0.248 |
| definition_without_label | 6 | 6/15 | 0.579 | -0.093 |
| neutral | 5 | 7/15 | 0.388 | 0.204 |
| neutral | 6 | 10/15 | 0.589 | 0.405 |
| label_only | 5 | 8/15 | 0.342 | 0.144 |
| label_only | 6 | 8/15 | 0.387 | 0.156 |
| blank_carrier | 5 | 0/15 | 0.044 | 0.000 |
| blank_carrier | 6 | 0/15 | 0.000 | 0.000 |
| shuffled_label | 5 | 0/15 | -0.010 | -0.429 |
| shuffled_label | 6 | 1/15 | -0.157 | -0.752 |

### Source Passage

| Regime | Layer | Specific passes | Mean target-margin delta | Mean target-over-control advantage |
| --- | ---: | ---: | ---: | ---: |
| definition | 5 | 12/15 | 2.983 | 0.646 |
| definition | 6 | 10/15 | 3.280 | 0.881 |
| definition_without_label | 5 | 7/15 | 2.453 | -0.251 |
| definition_without_label | 6 | 7/15 | 2.666 | -0.093 |
| neutral | 5 | 9/15 | 2.277 | 0.203 |
| neutral | 6 | 12/15 | 2.676 | 0.405 |
| label_only | 5 | 9/15 | 2.195 | 0.029 |
| label_only | 6 | 9/15 | 2.474 | 0.156 |
| blank_carrier | 5 | 0/15 | 1.933 | 0.000 |
| blank_carrier | 6 | 0/15 | 2.087 | 0.000 |
| shuffled_label | 5 | 0/15 | 1.887 | -0.420 |
| shuffled_label | 6 | 1/15 | 1.930 | -0.752 |

## Diagnosis

The full-label behavior effect survives the stronger carrier controls, but it is not pure semantics.

What the controls show:

- `blank_carrier` fails everywhere. The effect is not arbitrary carrier format or activation norm movement.
- `shuffled_label` fails almost everywhere and has strongly negative target-over-control advantage. The correct label matters.
- `label_only` and `neutral` remain active but are consistently weaker than full definitions. Label-string pressure is part of the behavior surface.
- `definition_without_label` keeps positive raw target-margin deltas but loses target-over-control specificity. The leading label prefix is doing major work.
- Full `definition` is strongest across both prompt frames and both layers.

The best current interpretation is:

```text
Full-label behavior transfer is label-anchored and definition-context boosted.
```

This is narrower than a pure semantic-transfer claim, but stronger than the previous caveat. The effect is not explained by blank carrier movement, wrong-label movement, or label-only movement alone.

## Claim Status

Accepted:

```text
The full-label scoring surface exposes behavior-level target movement that is
specific to the correct label and is amplified by the full definition carrier.
```

Withheld:

```text
The transported state is purely semantic independent of the lexical label.
```

Superseded:

```text
Neutral-carrier activity means the full-label result is too confounded to interpret.
```

Better replacement:

```text
Neutral and label-only carriers reveal a real label-anchoring component, while
blank and shuffled-label controls rule out arbitrary carrier movement. The
full definition adds an extra target-specific boost beyond label-only carriers.
```

## Next Move

The next strongest experiment is not another same-model carrier grid. It should test whether the label-anchored/full-definition split generalizes:

- Replicate with a second seed and second open model.
- Add aliases and paraphrased labels so the target is not one exact string.
- Learn behavior-aligned directions against the full-label objective, then test whether they preserve target movement under alias labels.
- Compare pair-level readout movement against the full-definition-minus-label-only behavior boost.

## Discovery-Regime Audit

Question: does the full-label behavior effect survive stronger carrier controls?

Current regime:

- Artifact types: full-label behavior payloads, patch-text carrier regimes, target-vs-control specificity rows, definition-minus-control contrast summaries.
- Operations: hook-output state capture from different carrier texts, full-label continuation scoring, source/noop/distractor/random patch controls.
- Gates/verifiers: full definition should exceed label-only, neutral, blank-carrier, and shuffled-label controls; blank and shuffled controls should fail if the effect is concept/label-specific.
- Known limitations: one seed, one model, exact-label scoring, no alias target labels yet.

Action class:

- Retrieval/search/discovery: verifier refinement.
- Why: this run adds new carrier-control artifact classes that distinguish arbitrary carrier movement, wrong-label movement, label-only movement, and definition-context boost.

Experiment:

- Manifest/report paths: this report; local ignored payloads under `artifacts/activation_geometry/modal_pythia_70m_full_label_carrier_controls_*.json`.
- Positive targets: focus rows plus 8 sampled baseline pairs.
- Negative controls: `blank_carrier`, `shuffled_label`, distractor/random/source-noop patch modes.
- Stress tests: prompt frames `latent_choice` and `source_passage`; layers `5,6`; stripped-definition, neutral, and label-only carrier ablations.

Gate:

- Acceptance rule: accept strengthened full-label behavior claim if full definitions beat controls and shuffled/blank carriers fail.
- Withheld/rejected rule: withhold pure semantic transfer if stripped definitions or label-free carriers match the full definition effect.

Results:

- Accepted artifacts: carrier-control regimes in the full-label behavior gate; this report.
- Rejected or withheld artifacts: pure semantic-transfer claim remains withheld.
- Key metrics: full definitions pass `9/15` to `12/15`; label-only/neutral are active but weaker; blank carriers pass `0/15`; shuffled-label carriers pass at most `1/15` with negative mean advantage.
- Variance or ablation: source-passage and latent-choice frames agree on the ordering: `definition` > `neutral/label_only` > `blank_carrier/shuffled_label`.

Residual content:

- Explained by old regime: exact label strings can steer full-label behavior.
- New content outside old regime: full definitions add a target-specific boost beyond label-only carriers, while wrong labels actively suppress target-specificity.
- Retractions or supersessions: supersede "neutral carrier activity makes the full-label result uninterpretable" with "the effect is label-anchored and definition-context boosted."

Next move: replicate across seed/model and test alias labels to separate exact-string anchoring from conceptual behavior transfer.
