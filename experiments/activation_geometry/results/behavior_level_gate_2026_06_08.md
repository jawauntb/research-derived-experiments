# Behavior-Level Gate - 2026-06-08

## Question

Does the trained-readout-confirmed hook-output transfer ridge change model behavior, or does it remain a readout-space phenomenon?

The trained readout gate showed that late Pythia-70M hook-output patches move both centroid and ridge concept readouts toward the target. This run asks for the next stronger claim: does the same label-free target-state patch make the model more likely to choose the target concept in a next-token multiple-choice answer surface?

## Method

Raw payloads remain local-only under ignored `artifacts/`.

Payloads:

```text
artifacts/activation_geometry/modal_pythia_70m_behavior_gate_seed20260608.json
artifacts/activation_geometry/modal_pythia_70m_behavior_gate_latent_seed20260608.json
```

Grid:

- Model: `EleutherAI/pythia-70m-deduped`
- Patch-vector surface: `hook_output`
- Injection layers: `4,5,6`
- Patch alphas: `0.75,1.0`
- Pair set: `combined`
- Baseline pairs: 8 sampled ordered concept pairs
- Total pairs: 15
- Patch text regimes: `definition`, `neutral`
- Patch modes: `target`, `distractor`, `random`, `source_noop`
- Prompt frames: `source_passage`, `latent_choice`
- Option orders: 3 cyclic orders
- Eval variant: `2`
- Seed: `20260608`

The `source_passage` frame asks the model to choose which concept a visible source passage points to. This is a hard override test because the text itself indicates the source answer. The `latent_choice` frame removes the passage and asks the model to choose the concept indicated by the current internal state, so the activation patch is the only concept-bearing signal besides option labels.

Commands:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_label_free_behavior_gate.py --model-id EleutherAI/pythia-70m-deduped --injection-layers 4,5,6 --max-length 160 --eval-variant 2 --patch-alphas 0.75,1.0 --patch-modes target,distractor,random,source_noop --patch-text-regimes definition,neutral --patch-vector-surface hook_output --pair-set combined --baseline-sample-count 8 --seed 20260608 --out artifacts/activation_geometry/modal_pythia_70m_behavior_gate_seed20260608.json
```

```bash
doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/activation_geometry/modal_label_free_behavior_gate.py --model-id EleutherAI/pythia-70m-deduped --injection-layers 4,5,6 --max-length 160 --eval-variant 2 --patch-alphas 0.75,1.0 --patch-modes target,distractor,random,source_noop --patch-text-regimes definition,neutral --patch-vector-surface hook_output --prompt-frame latent_choice --pair-set combined --baseline-sample-count 8 --seed 20260608 --out artifacts/activation_geometry/modal_pythia_70m_behavior_gate_latent_seed20260608.json
```

Analysis helper:

```bash
python3 scripts/summarize_label_free_behavior_gate.py artifacts/activation_geometry/modal_pythia_70m_behavior_gate_seed20260608.json artifacts/activation_geometry/modal_pythia_70m_behavior_gate_latent_seed20260608.json
```

## Manifest Sanity

| Artifact | Model | Seed | Surface | Prompt frame | Injection layers | Alphas | Regimes | Option orders | Baseline N | Pairs |
| --- | --- | ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| source passage | EleutherAI/pythia-70m-deduped | 20260608 | hook_output | source_passage | 4,5,6 | 0.75,1.0 | definition,neutral | 3 | 8 | 15 |
| latent choice | EleutherAI/pythia-70m-deduped | 20260608 | hook_output | latent_choice | 4,5,6 | 0.75,1.0 | definition,neutral | 3 | 8 | 15 |

## Definition Behavior Specificity

| Prompt frame | Layer | Alpha | Specific passes | Pass rate | Mean target-margin delta | Median target-margin delta | Mean target-over-control advantage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| source_passage | 4 | 0.75 | 2/15 | 13.3% | 0.060 | 0.053 | -0.077 |
| source_passage | 4 | 1.00 | 2/15 | 13.3% | 0.068 | 0.068 | -0.077 |
| source_passage | 5 | 0.75 | 1/15 | 6.7% | 0.035 | 0.026 | -0.076 |
| source_passage | 5 | 1.00 | 0/15 | 0.0% | 0.045 | 0.028 | -0.089 |
| source_passage | 6 | 0.75 | 3/15 | 20.0% | 0.029 | 0.037 | -0.001 |
| source_passage | 6 | 1.00 | 0/15 | 0.0% | 0.040 | 0.048 | 0.000 |
| latent_choice | 4 | 0.75 | 2/15 | 13.3% | 0.029 | 0.026 | -0.057 |
| latent_choice | 4 | 1.00 | 1/15 | 6.7% | 0.046 | 0.045 | -0.063 |
| latent_choice | 5 | 0.75 | 1/15 | 6.7% | 0.012 | -0.016 | -0.060 |
| latent_choice | 5 | 1.00 | 2/15 | 13.3% | 0.046 | 0.058 | -0.054 |
| latent_choice | 6 | 0.75 | 1/15 | 6.7% | 0.009 | -0.012 | -0.002 |
| latent_choice | 6 | 1.00 | 0/15 | 0.0% | 0.013 | -0.021 | 0.000 |

The behavior gate does not pass. Definition target patches often produce positive target-margin deltas, but distractor, random, or source-noop patches match or exceed them. The strongest apparent source-passage cell is only `3/15` specific passes at layer `6`, alpha `0.75`, with mean advantage `-0.001`. The latent-choice frame does not rescue the effect.

## Neutral Carrier Comparison

| Prompt frame | Layer | Alpha | Specific passes | Pass rate | Mean target-margin delta | Mean target-over-control advantage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| source_passage | 4 | 0.75 | 0/15 | 0.0% | -0.029 | -0.009 |
| source_passage | 4 | 1.00 | 0/15 | 0.0% | -0.022 | -0.009 |
| source_passage | 5 | 0.75 | 0/15 | 0.0% | -0.005 | -0.006 |
| source_passage | 5 | 1.00 | 1/15 | 6.7% | 0.013 | -0.007 |
| source_passage | 6 | 0.75 | 1/15 | 6.7% | 0.026 | -0.001 |
| source_passage | 6 | 1.00 | 0/15 | 0.0% | 0.040 | 0.000 |
| latent_choice | 4 | 0.75 | 0/15 | 0.0% | -0.007 | -0.011 |
| latent_choice | 4 | 1.00 | 1/15 | 6.7% | -0.008 | -0.013 |
| latent_choice | 5 | 0.75 | 0/15 | 0.0% | -0.008 | -0.004 |
| latent_choice | 5 | 1.00 | 1/15 | 6.7% | -0.000 | -0.007 |
| latent_choice | 6 | 0.75 | 0/15 | 0.0% | 0.008 | -0.000 |
| latent_choice | 6 | 1.00 | 0/15 | 0.0% | 0.013 | 0.000 |

Neutral carriers also fail the behavior gate, as expected. The important point is that definition carriers do not show target-specific behavior above controls either.

## Diagnosis

This result separates the current evidence into two tiers:

```text
Accepted: hook-output definition states are transported through late Pythia-70M
representations and remain visible to centroid and trained linear readouts.

Withheld: those transported states have not yet been shown to drive specific
next-token behavior on simple multiple-choice answer surfaces.
```

The failure mode is informative. In the source-passage frame, definition patches increase target margins in aggregate, but the control patches do too. In the latent-choice frame, removing source-passage interference makes the effect smaller rather than more specific. That suggests the readout-space ridge is not immediately equivalent to a behavior-steering vector.

## Interpretation

Rejected or withheld claim:

```text
The current evidence does not support a behavior-level transfer claim.
```

Best current framing:

```text
The project has a robust representational transport result, plus an initial
negative behavior gate. That is paper-useful because it marks the boundary
between activation-readout geometry and behaviorally effective steering.
```

This is not the breakthrough-positive result we hoped for, but it is exactly the kind of negative gate a serious paper needs. It prevents overclaiming and points to the next mechanistic question: what additional alignment is required for a transported concept state to cross the behavior interface?

## Limitations

- One seed.
- One model checkpoint.
- Multiple-choice option-token behavior may be too brittle or too option-bias-sensitive.
- The patch is inserted at the final token of an answer prompt, while the readout ridge was measured on definition-only carriers.
- `latent_choice` is intentionally diagnostic but somewhat unnatural as a language prompt.

## Next Move

The next paper-relevant experiment should not simply scale this failed gate. It should test a better behavior interface:

- Use label-logprob scoring over full concept labels rather than option letters.
- Try generation continuation prompts where the target concept label or definition should appear naturally.
- Learn a behavior-aligned steering direction from successful readout movements, rather than injecting raw definition states.
- Compare behavior-gate failure against readout deltas pair-by-pair to predict which transported states are closest to behavior alignment.

## Discovery-Regime Audit

Question: does the trained-readout-confirmed hook-output transfer ridge change next-token behavior?

Current regime:

- Artifact types: hook-output patch payloads, centroid/ridge readout summaries, behavior prompt frames, option-order logprob rows, target-vs-control specificity summaries.
- Operations: label-free definition/neutral patch-vector capture, final-token activation patching, option-token logprob scoring, prompt-frame ablation.
- Gates/verifiers: target patch must robustly improve target margin across option orders and beat distractor/random/source-noop controls; neutral carriers should not match definition specificity.
- Known limitations: one checkpoint, option-token answer surface, no learned behavior-aligned direction.

Action class:

- Retrieval/search/discovery: verifier transition with rejected claim.
- Why: this run adds behavior-level logprob scoring as a new verifier type and tests whether the representational ridge crosses into model choices.

Experiment:

- Manifest/report paths: this report; local ignored payloads under `artifacts/activation_geometry/modal_pythia_70m_behavior_gate*.json`.
- Positive targets: focus rows plus 8 sampled baseline pairs.
- Negative controls: neutral patch text, distractor/random/source-noop patch modes, option-order controls.
- Stress tests: prompt frames `source_passage` and `latent_choice`; injection layers `4,5,6`; alphas `0.75,1.0`.

Gate:

- Acceptance rule: accept behavior transfer only if definition target patches have positive robust target-margin movement and positive target-over-control advantage.
- Withheld/rejected rule: withhold behavior-level claims if controls match or exceed target patches.

Results:

- Accepted artifacts: behavior-gate runner and summary script.
- Rejected or withheld artifacts: behavior-level transfer claim is withheld.
- Key metrics: definition source-passage max pass rate `3/15`; definition latent-choice max pass rate `2/15`; mean target-over-control advantage is non-positive in every definition cell.
- Variance or ablation: removing source-passage text does not rescue target specificity.

Residual content:

- Explained by old regime: readout-space movement remains real but does not imply behavioral steering.
- New content outside old regime: the project now has a behavior verifier that can reject overclaims.
- Retractions or supersessions: supersede "next step may confirm behavior transfer" with "simple behavior transfer fails under option-token gates; behavior alignment needs a stronger intervention or different interface."

Next move: design a behavior-aligned intervention rather than raw state replacement.
