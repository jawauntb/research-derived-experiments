# Modal Result: Structured Tool-Call L4 Sweep

Run date: 2026-07-03

Modal run: https://modal.com/apps/generalintelligencecompany/main/ap-d9mdnHoIy8NXvdg6mokT9Q

Budget dry run: https://modal.com/apps/generalintelligencecompany/main/ap-eSpppzgfQiSzCQ0BghKoSF

## Configuration

- GPU: Modal `L4`
- Cells: 48 (`transformer` only, 3 conditions, 4 moved critical slots, 4 seeds)
- Conditions: `structured_direct_bottleneck`, `structured_repair_bottleneck`, `structured_visible_control`
- Action vocabulary size: 13 (`2*n_slots` executable calls, one no-op, four malformed tokens)
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
- Mean remote cell runtime: 11.77 seconds
- Max remote cell runtime: 13.32 seconds

## Gate Summary

This is the full Modal confirmation of the structured tool-call regime that was
previously only smoke-tested on CPU. Closed-loop final accuracy depends on the
model's parsed structured action, not on a teacher-forced return.

| Group | Closed-loop final accuracy | Teacher-forced final accuracy | First token | First executable-call validity | First parsed slot | First parsed value | Repair token | Repair executable-call validity | Repair parsed slot | Repair parsed value | Memory specificity z | Tool-value specificity z | Gate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| structured_direct_bottleneck/transformer | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | n/a | n/a | n/a | n/a | +2.309 | +2.309 | pass |
| structured_repair_bottleneck/transformer | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | +2.309 | +2.309 | pass |
| structured_visible_control/transformer | 1.000 | 1.000 | 1.000 no-op | n/a | n/a | n/a | 1.000 no-op | n/a | n/a | n/a | -0.000 | +0.000 | pass |

Pooled structured-repair gates pass:

- Closed-loop final behavior: pass, mean accuracy 1.000
- Teacher-forced final diagnostic: mean accuracy 1.000
- First structured action token: pass, mean accuracy 1.000
- Repair structured action token: pass, mean accuracy 1.000
- Repair executable-call validity: pass, mean 1.000
- Repair parsed slot/value: pass, mean accuracy 1.000 / 1.000
- Final memory-state specificity: pass, 95% CI lower bound > 0
- Structured-action logit specificity: pass, 95% CI lower bound > 0
- Visible-control null: pass at the grouped level, mean memory specificity remains near zero

Visible-control no-op tokens are correct non-executable actions, so executable
call-validity is not a meaningful control metric for that condition.

## Regime Audit

- Old regime: tool recovery used separate supervised slot and value heads.
- Transition: a single structured-action head emits a JSON-like token representing an executable call, no-op, or malformed action. The evaluator parses that token and only returns external state for executable calls whose parsed slot matches the moved bottleneck.
- Transported evidence: moved critical slot, visible-control null, closed-loop scoring, L4 cost guard, final memory specificity, and tool/action specificity are preserved.
- Rejected alternative: this is not a natural-language tool-use benchmark; the action set is still a fixed discrete synthetic vocabulary.
- Residual finding: the moved bottleneck survives the shift from supervised slot/value heads to parsed structured actions, including the error-feedback and repair-commitment loop.
- Readiness: structured synthetic tool-call result is now confirmed on Modal `L4`; multi-argument schemas, stochastic tool failures, and natural-language argument surfaces remain untested.
- Allowed claim: future control relevance can move finite memory and commitment sensitivity through a parsed structured-action interface in a transformer sequence agent.
- Next operation: move from one-token structured actions to multi-token/multi-argument schemas with malformed arguments, stochastic tool failures, and natural-language repair prompts.

## Interpretation Boundary

This is a neural-validated synthetic structured tool-call result, not a
production agent, human-behavior, autonomous natural-language tool-use, or
consciousness claim.
