# Modal Result: Multifield Tool-Schema L4 Sweep

Run date: 2026-07-03

Modal run: https://modal.com/apps/generalintelligencecompany/main/ap-S6PgqvqeGAPggzdfNXm2Xx

Budget dry run: https://modal.com/apps/generalintelligencecompany/main/ap-vBQru8rqvWSpg7YvJE9HYK

Artifact: `artifacts/long_horizon_bottleneck/multifield_tool_schema_l4_4seed_2026_07_03.json`

## Configuration

- GPU: Modal `L4`
- Cells: 48 (`transformer` only, 3 conditions, 4 moved critical slots, 4 seeds)
- Conditions: `multifield_direct_bottleneck`, `multifield_repair_bottleneck`, `multifield_visible_control`
- Field vocabularies: opcode 3, slot argument 6, value argument 4
- Schema: executable call = `(call, valid_slot, 0|1)`; no-op = `(noop, missing_slot, missing_value)`; malformed examples include missing slot, bad slot, missing value, bad value, and bad opcode
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
- Conservative timeout-based budget cap: `$12.95`
- User budget supplied to runner: `$25.00`
- Mean remote cell runtime: 11.98 seconds
- Max remote cell runtime: 12.80 seconds
- Base seed: 20260704

## Gate Summary

This is the full Modal confirmation of the multifield tool-schema regime. The
model no longer emits a single fused action token; it emits separate opcode,
slot, and value fields, and closed-loop external state is returned only when the
parsed fields compose into an executable call for the moved bottleneck slot.

| Group | Closed-loop final accuracy | Teacher-forced final accuracy | First fields | First schema valid | First parsed slot | First parsed value | Repair fields | Repair schema valid | Repair parsed slot | Repair parsed value | Memory specificity z | Tool-value specificity z | Gate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| multifield_direct_bottleneck/transformer | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | n/a | n/a | n/a | n/a | +2.309 | +2.309 | pass |
| multifield_repair_bottleneck/transformer | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | +2.309 | +2.309 | pass |
| multifield_visible_control/transformer | 1.000 | 1.000 | 1.000 no-op | 1.000 | n/a | n/a | 1.000 no-op | 1.000 | n/a | n/a | +0.000 | -0.000 | pass |

Pooled multifield-repair gates pass:

- Closed-loop final behavior: pass, mean accuracy 1.000
- Teacher-forced final diagnostic: mean accuracy 1.000
- First multifield action fields: pass, mean accuracy 1.000
- Repair multifield action fields: pass, mean accuracy 1.000
- Repair composed schema validity: pass, mean 1.000
- Repair parsed slot/value: pass, mean accuracy 1.000 / 1.000
- Final memory-state specificity: pass, 95% CI lower bound > 0
- Tool-value specificity: pass, 95% CI lower bound > 0
- Visible-control no-op null: pass, mean memory specificity remains near zero

The visible-control action is a schema-valid no-op rather than an executable
call, so parsed slot/value accuracy is intentionally not defined for that
condition.

## Regime Audit

- Old regime: structured tool calls used one fused discrete token for each executable call, no-op, or malformed action.
- Transition: the action interface is factorized into opcode, slot argument, and value argument fields. The evaluator parses the tuple, composes schema validity across fields, and returns external state only for executable calls whose parsed slot matches the moved bottleneck.
- Transported evidence: moved critical slot, visible-control null, closed-loop scoring, L4 cost guard, final memory specificity, tool-value specificity, schema validity, parsed slot/value accuracy, and repair-loop commitment are preserved.
- Rejected alternative: this is not free-form JSON, natural-language tool use, or a production API benchmark; each field is still a fixed synthetic classifier.
- Residual finding: the moved bottleneck survives the shift from one-token structured actions to a compositional multifield schema, including the API-style error feedback and repair-commitment loop.
- Readiness: multifield synthetic tool-schema result is confirmed on Modal `L4`; stochastic failures, larger argument domains, and natural-language argument surfaces remain untested.
- Allowed claim: future control relevance can move finite memory and commitment sensitivity through a parsed, compositional tool schema in a transformer sequence agent.
- Next operation: add stochastic tool failures and natural-language argument surfaces while preserving the closed-loop schema parser and moved-critical-slot gates.

## Interpretation Boundary

This is a neural-validated synthetic multifield tool-schema result, not a
production agent, human-behavior, autonomous natural-language tool-use, or
consciousness claim.
