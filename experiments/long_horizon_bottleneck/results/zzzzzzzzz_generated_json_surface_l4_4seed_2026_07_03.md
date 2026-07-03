# Modal Result: Generated JSON Surface L4 Sweep

Run date: 2026-07-03

Modal run: https://modal.com/apps/generalintelligencecompany/main/ap-Rl3RRB7Z1vDa9mGZdilrsg

Budget dry run: https://modal.com/apps/generalintelligencecompany/main/ap-F1mPrlinCEfkHbdW4gWUwy

Artifact: `artifacts/long_horizon_bottleneck/generated_json_surface_l4.json`

## Configuration

- GPU: Modal `L4`
- Cells: 32 (`transformer` only, 2 conditions, 4 moved critical slots, 4 seeds)
- Conditions: `generated_json_bottleneck`, `generated_json_visible_control`
- Registered clue slots: 4
- Text phrase variants per canonical slot: 3
- Generated JSON sequence length: 13 tokens
- Generated JSON vocabulary size: 27 tokens
- Example emitted call: `{ tool : read_slot , slot : second clue , value : 0 }`
- Example emitted no-op: `{ tool : noop }`
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
- Mean remote cell runtime: 12.32 seconds
- Max remote cell runtime: 12.83 seconds
- Base seed: 20260704

## Gate Summary

This run replaces classifier-rendered text fields with a fixed-length emitted
token sequence that renders to a JSON-like tool-call string. The evaluator
parses the emitted sequence into opcode, slot phrase, and value before applying
the same stochastic repair/no-op gates used by the text argument-surface pass.

- generated_json_bottleneck pass: final 1.000, parsed slot/value 1.000 / 1.000, failed repair 1.000, success no-op 1.000
- generated_json_visible_control pass: final 1.000, no-op sequence 1.000, memory specificity +0.000

| Group | Closed-loop final accuracy | Teacher-forced final accuracy | First sequence | First schema valid | First parsed slot | First parsed value | Failed repair sequence | Failed repair schema | Failed repair slot | Failed repair value | Success repair no-op | Sampled failure rate | Memory specificity z | Tool-sequence specificity z | Gate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| generated_json_bottleneck/transformer | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.506 | +2.307 | +2.309 | pass |
| generated_json_visible_control/transformer | 1.000 | 1.000 | 1.000 no-op | 1.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 0.506 | +0.000 | +0.000 | pass |

Pooled generated JSON stochastic-failure gates pass:

- Closed-loop final behavior: pass, mean accuracy 1.000
- Teacher-forced final diagnostic: mean accuracy 1.000
- First emitted JSON sequence: pass, mean exact accuracy 1.000
- First parsed slot/value: pass, mean accuracy 1.000 / 1.000
- Failed repair sequence and schema: pass, mean accuracy 1.000 / 1.000
- Failed repair parsed slot/value: pass, mean accuracy 1.000 / 1.000
- Success-path repair no-op sequence: pass, mean accuracy 1.000
- Sampled failure rate: 0.506, 95% CI [0.496, 0.515]
- Final memory-state specificity: pass, mean +2.307, 95% CI [2.304, 2.309]
- Repair JSON-sequence specificity: pass, mean +2.309, 95% CI [2.308, 2.309]
- Visible-control null: pass, mean memory specificity remains near zero

## Regime Audit

- Old regime: stochastic tool failures were confirmed with compact slot-id arguments, an 8-slot larger argument namespace, an alias-rich argument surface, and parser-facing text argument phrases.
- Transition: the model-visible action is now an emitted fixed-length JSON-like token sequence rather than three classifier fields, while preserving the stochastic first-call failure, conditional repair/no-op split, text phrase parser, and moved critical slot.
- Transported evidence: moved critical slot, visible-control null, closed-loop scoring, L4 cost guard, final memory specificity, repair-sequence specificity, schema validity, parsed slot/value accuracy, sampled failure rate, and conditional repair/no-op behavior are preserved.
- Rejected alternative: this is not a production LLM prompt benchmark; it isolates emitted parser strings before changing tokenizer, decoding, or pretraining priors.
- Residual finding: the moved bottleneck survives stochastic API feedback and conditional repair behavior when the parser consumes generated JSON-like token sequences rather than classifier-rendered phrase fields.
- Readiness: generated token-sequence JSON result is confirmed on Modal `L4`; autoregressive text or prompt-level LLM transfer remains the next realism step.
- Allowed claim: future control relevance can move finite memory and commitment sensitivity through a parsed, emitted JSON-like tool-call surface under stochastic API feedback in this synthetic neural-agent diagnostic.
- Next operation: run an autoregressive JSON text variant where decoding, malformed strings, and parser recovery are part of the measured bottleneck.

## Interpretation Boundary

This is a neural-validated synthetic generated-token result, not a production
agent, real API reliability benchmark, autonomous natural-language tool-use, or
consciousness claim.
