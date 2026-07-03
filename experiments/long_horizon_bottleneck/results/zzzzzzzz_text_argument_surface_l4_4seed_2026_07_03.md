# Modal Result: Text Argument-Surface L4 Sweep

Run date: 2026-07-03

Modal run: https://modal.com/apps/generalintelligencecompany/main/ap-IzaMxGOJyYo0Y3uNaJlcMI

Budget dry run: https://modal.com/apps/generalintelligencecompany/main/ap-EfkXRQLTBairmkcgYZURH0

Artifact: `artifacts/long_horizon_bottleneck/text_argument_surface_l4.json`

## Configuration

- GPU: Modal `L4`
- Cells: 32 (`transformer` only, 2 conditions, 4 moved critical slots, 4 seeds)
- Conditions: `text_stochastic_bottleneck`, `text_visible_control`
- Registered clue slots: 4
- Text variants per canonical slot: 3
- Text argument vocabulary size: 14
- Phrase variants: `clue_i`, ordinal phrases such as `second clue`, and descriptive phrases such as `memory slot i`
- Failure probability: 0.5 per episode
- Sequence length: 128
- First commit position: 64
- Error or first-return position: 65
- Repair commit position: 66
- Repair return position: 67
- Train steps: 900
- Batch size: 256
- Hidden size: 64
- Max containers: 32
- Timeout guard: 900 seconds per cell
- Conservative timeout-based budget cap: `$8.63`
- User budget supplied to runner: `$25.00`
- Mean remote cell runtime: 14.85 seconds
- Max remote cell runtime: 16.59 seconds
- Base seed: 20260704

## Gate Summary

This run replaces the alias-id slot argument with parser-facing text phrases.
The model still emits a classifier token, but each token renders to a text
argument such as `clue_1`, `second clue`, or `memory slot 1`. The evaluator
parses the rendered phrase back to a canonical slot before applying the same
stochastic repair/no-op gates used by the alias argument-surface pass.

- text_stochastic_bottleneck pass: final 1.000, parsed slot/value 1.000 / 1.000, failed repair 1.000, success no-op 1.000
- text_visible_control pass: final 1.000, no-op fields 1.000, memory specificity +0.000

| Group | Closed-loop final accuracy | Teacher-forced final accuracy | First fields | First schema valid | First parsed slot | First parsed value | Failed repair fields | Failed repair schema | Failed repair slot | Failed repair value | Success repair no-op | Sampled failure rate | Memory specificity z | Tool-value specificity z | Gate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| text_stochastic_bottleneck/transformer | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.506 | +2.309 | +2.309 | pass |
| text_visible_control/transformer | 1.000 | 1.000 | 1.000 no-op | 1.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 0.506 | +0.000 | -0.000 | pass |

Pooled text stochastic-failure gates pass:

- Closed-loop final behavior: pass, mean accuracy 1.000
- Teacher-forced final diagnostic: mean accuracy 1.000
- First text-argument action fields: pass, mean accuracy 1.000
- First parsed slot/value: pass, mean accuracy 1.000 / 1.000
- Failed repair fields and schema: pass, mean accuracy 1.000 / 1.000
- Failed repair parsed slot/value: pass, mean accuracy 1.000 / 1.000
- Success-path repair no-op: pass, mean accuracy 1.000
- Sampled failure rate: 0.506, 95% CI [0.496, 0.515]
- Final memory-state specificity: pass, mean +2.309, 95% CI [2.309, 2.309]
- Repair-field tool specificity: pass, mean +2.309, 95% CI [2.309, 2.309]
- Visible-control null: pass, mean memory specificity remains near zero

## Regime Audit

- Old regime: stochastic tool failures were confirmed with compact slot-id arguments, an 8-slot larger argument namespace, and an alias-rich argument surface.
- Transition: the slot argument now renders to text phrases before being parsed back to canonical slots, while preserving the stochastic first-call failure, conditional repair/no-op split, and moved critical slot.
- Transported evidence: moved critical slot, visible-control null, closed-loop scoring, L4 cost guard, final memory specificity, repair-field specificity, schema validity, parsed slot/value accuracy, sampled failure rate, and conditional repair/no-op behavior are preserved.
- Rejected alternative: this is not free-form language-model generation; it isolates parser-facing text arguments before changing model class or decoding.
- Residual finding: the moved bottleneck survives stochastic API feedback and conditional repair behavior when the argument namespace is text-labeled rather than only compact or alias-token labeled.
- Readiness: text-labeled synthetic result is confirmed on Modal `L4`; prompt-level LLM transfer remains the next realism step.
- Allowed claim: future control relevance can move finite memory and commitment sensitivity through a parsed, text-labeled tool schema under stochastic API feedback in this synthetic neural-agent diagnostic.
- Next operation: run a prompt-level JSON tool-call variant where generated strings, rather than classifier-rendered phrases, are parsed and scored.

## Interpretation Boundary

This is a neural-validated synthetic text-argument result, not a production
agent, real API reliability benchmark, autonomous natural-language tool-use, or
consciousness claim.
