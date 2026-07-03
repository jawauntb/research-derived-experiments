# Modal Result: Autoregressive JSON Surface L4 Sweep

Run date: 2026-07-03

Modal run: https://modal.com/apps/generalintelligencecompany/main/ap-Euh8MDI0zcNHo5thWHWtX2

Budget dry run: https://modal.com/apps/generalintelligencecompany/main/ap-RXUon2Eyammm4zCZRKlsZp

Artifact: `artifacts/long_horizon_bottleneck/autoregressive_json_surface_l4.json`

## Configuration

- GPU: Modal `L4`
- Cells: 32 (`transformer` only, 2 conditions, 4 moved critical slots, 4 seeds)
- Conditions: `autoregressive_json_bottleneck`, `autoregressive_json_visible_control`
- Registered clue slots: 4
- Text phrase variants per canonical slot: 3
- JSON generation mode: autoregressive
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
- Mean remote cell runtime: 15.08 seconds
- Max remote cell runtime: 16.62 seconds
- Base seed: 20260704

## Gate Summary

This run keeps the generated JSON parser and token vocabulary, but decodes each
action autoregressively from the commit state: the previous emitted token is fed
back before predicting the next token. The evaluator parses the greedy decoded
sequence into opcode, slot phrase, and value before applying the same stochastic
repair/no-op gates used by the generated JSON pass.

- autoregressive_json_bottleneck pass: final 1.000, parsed slot/value 1.000 / 1.000, failed repair 1.000, success no-op 1.000
- autoregressive_json_visible_control pass: final 1.000, no-op sequence 1.000, memory specificity -0.000

| Group | Closed-loop final accuracy | Teacher-forced final accuracy | First decoded sequence | First schema valid | First parsed slot | First parsed value | Failed repair sequence | Failed repair schema | Failed repair slot | Failed repair value | Success repair no-op | Sampled failure rate | Memory specificity z | Action-channel specificity z | Gate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| autoregressive_json_bottleneck/transformer | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.506 | +2.309 | +2.309 | pass |
| autoregressive_json_visible_control/transformer | 1.000 | 1.000 | 1.000 no-op | 1.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 0.506 | -0.000 | +0.000 | pass |

Pooled autoregressive JSON stochastic-failure gates pass:

- Closed-loop final behavior: pass, mean accuracy 1.000
- Teacher-forced final diagnostic: mean accuracy 1.000
- First greedy decoded JSON sequence: pass, mean exact accuracy 1.000
- First parsed slot/value: pass, mean accuracy 1.000 / 1.000
- Failed repair sequence and schema: pass, mean accuracy 1.000 / 1.000
- Failed repair parsed slot/value: pass, mean accuracy 1.000 / 1.000
- Success-path repair no-op sequence: pass, mean accuracy 1.000
- Sampled failure rate: 0.506, 95% CI [0.496, 0.515]
- Final memory-state specificity: pass, mean +2.309, 95% CI [2.308, 2.309]
- Repair action-channel specificity: pass, mean +2.309, 95% CI [2.309, 2.309]
- Visible-control null: pass, mean memory specificity remains near zero

## Regime Audit

- Old regime: stochastic tool failures were confirmed through compact, alias, text, parallel generated JSON, and visible-control null surfaces.
- Transition: the model-visible action is now decoded token-by-token from the commit state, rather than predicted as a parallel fixed sequence head, while preserving the parser, stochastic feedback, and moved critical slot.
- Transported evidence: moved critical slot, visible-control null, closed-loop scoring, L4 cost guard, final memory specificity, action-channel specificity, schema validity, parsed slot/value accuracy, sampled failure rate, and conditional repair/no-op behavior are preserved.
- Rejected alternative: this is not yet a pretrained LLM prompt benchmark; it isolates autoregressive decoding before changing tokenizer, prompt priors, or natural-language model class.
- Residual finding: the moved bottleneck survives stochastic API feedback and conditional repair behavior when the parser consumes greedy autoregressively decoded JSON-like action strings.
- Readiness: autoregressive token-sequence JSON result is confirmed on Modal `L4`; prompt-level LLM transfer remains the next realism step.
- Allowed claim: future control relevance can move finite memory and commitment sensitivity through a parsed, autoregressively decoded JSON-like tool-call surface under stochastic API feedback in this synthetic neural-agent diagnostic.
- Next operation: run a small pretrained or prompt-level JSON action transfer where tokenizer-level decoding and malformed-string recovery are part of the measured bottleneck.

## Interpretation Boundary

This is a neural-validated synthetic autoregressive-token result, not a
production agent, real API reliability benchmark, autonomous natural-language
tool-use, or consciousness claim.
