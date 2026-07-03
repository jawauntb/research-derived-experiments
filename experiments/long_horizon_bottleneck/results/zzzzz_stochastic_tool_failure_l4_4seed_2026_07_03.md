# Modal Result: Stochastic Tool-Failure L4 Sweep

Run date: 2026-07-03

Modal run: https://modal.com/apps/generalintelligencecompany/main/ap-i3jxqw4yTwDRmK6cj5lCen

Budget dry run: https://modal.com/apps/generalintelligencecompany/main/ap-jUNdiGajZHyj93QUYC46En

Artifact: `artifacts/long_horizon_bottleneck/stochastic_tool_failure_l4_4seed_2026_07_03.json`

## Configuration

- GPU: Modal `L4`
- Cells: 32 (`transformer` only, 2 conditions, 4 moved critical slots, 4 seeds)
- Conditions: `stochastic_failure_bottleneck`, `stochastic_visible_control`
- Failure probability: 0.5 per episode
- Field vocabularies: opcode 3, slot argument 6, value argument 4
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
- Mean remote cell runtime: 12.54 seconds
- Max remote cell runtime: 13.48 seconds
- Base seed: 20260704

## Gate Summary

This is the full Modal confirmation of the stochastic tool-failure regime. The
first tool call fails per episode with probability 0.5. If it succeeds, the
repair action should be a schema-valid no-op; if it fails, the repair action
must be a complete executable call for the moved bottleneck slot.

| Group | Closed-loop final accuracy | Teacher-forced final accuracy | First fields | First schema valid | First parsed slot | First parsed value | Failed repair fields | Failed repair schema | Failed repair slot | Failed repair value | Success repair no-op | Sampled failure rate | Memory specificity z | Tool-value specificity z | Gate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| stochastic_failure_bottleneck/transformer | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.506 | +2.309 | +2.309 | pass |
| stochastic_visible_control/transformer | 1.000 | 1.000 | 1.000 no-op | 1.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 0.506 | +0.000 | -0.000 | pass |

Pooled stochastic-failure gates pass:

- Closed-loop final behavior: pass, mean accuracy 1.000
- Teacher-forced final diagnostic: mean accuracy 1.000
- First multifield action fields: pass, mean accuracy 1.000
- First parsed slot/value: pass, mean accuracy 1.000 / 1.000
- Failed repair fields and schema: pass, mean accuracy 1.000 / 1.000
- Failed repair parsed slot/value: pass, mean accuracy 1.000 / 1.000
- Success-path repair no-op: pass, mean accuracy 1.000
- Sampled failure rate: 0.506, 95% CI [0.496, 0.515]
- Final memory-state specificity: pass, 95% CI lower bound > 0
- Repair-field tool specificity: pass, 95% CI lower bound > 0
- Visible-control null: pass, mean memory specificity remains near zero

## Regime Audit

- Old regime: deterministic multifield schemas always gave either a direct return or a forced repair error.
- Transition: first-call success or failure is sampled per episode. The repair target is conditional: call again after failure, no-op after success.
- Transported evidence: moved critical slot, visible-control null, closed-loop scoring, L4 cost guard, final memory specificity, repair-field specificity, schema validity, parsed slot/value accuracy, and repair-loop commitment are preserved.
- Rejected alternative: this is not a production API benchmark; failures are synthetic Bernoulli samples, and arguments remain fixed discrete fields.
- Residual finding: the moved bottleneck survives stochastic API feedback and conditional repair/no-op behavior.
- Readiness: stochastic synthetic tool-failure result is confirmed on Modal `L4`; larger schemas and natural-language argument surfaces remain untested.
- Allowed claim: future control relevance can move finite memory and commitment sensitivity through a parsed tool schema even when API success or failure is uncertain at the first call.
- Next operation: replace fixed discrete arguments with natural-language or larger-schema argument surfaces while preserving stochastic feedback and closed-loop gates.

## Interpretation Boundary

This is a neural-validated synthetic stochastic tool-failure result, not a
production agent, real API reliability benchmark, autonomous natural-language
tool-use, or consciousness claim.
