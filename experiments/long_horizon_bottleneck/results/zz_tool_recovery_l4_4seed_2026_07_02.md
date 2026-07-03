# Modal Result: Tool-Recovery L4 Sweep

Run date: 2026-07-02

Modal run: https://modal.com/apps/generalintelligencecompany/main/ap-N6VcMGi69pdu2G1C1cHxyI

Budget dry run: https://modal.com/apps/generalintelligencecompany/main/ap-7mD2yjz9gMACe2G7W48UDa

## Configuration

- GPU: Modal `L4`
- Cells: 48 (`transformer` only, 3 conditions, 4 moved critical slots, 4 seeds)
- Conditions: `direct_bottleneck`, `repair_bottleneck`, `visible_control`
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
- Max remote cell runtime: 12.89 seconds

## Gate Summary

The repair condition forces an API-style missing-return/error token after the
first tool attempt. Closed-loop final accuracy depends on the model's later
repair slot/value commitment, not on a teacher-forced return.

| Group | Closed-loop final accuracy | Teacher-forced final accuracy | First slot | First value | Repair slot | Repair value | Memory specificity z | Tool-value specificity z | Gate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| direct_bottleneck/transformer | 1.000 | 1.000 | 1.000 | 1.000 | n/a | n/a | +2.309 | +2.309 | pass |
| repair_bottleneck/transformer | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | +2.309 | +2.309 | pass |
| visible_control/transformer | 1.000 | 1.000 | 1.000 | n/a | 1.000 | n/a | +0.000 | +0.000 | pass |

Pooled repair-bottleneck gates pass:

- Closed-loop final behavior: pass, mean accuracy 1.000
- Teacher-forced final diagnostic: mean accuracy 1.000
- First tool slot/value commitment: pass, mean accuracy 1.000 / 1.000
- Repair tool slot/value commitment: pass, mean accuracy 1.000 / 1.000
- Final memory-state specificity: pass, 95% CI lower bound > 0
- Repair tool-value logit specificity: pass, 95% CI lower bound > 0
- Visible-control null: pass at the grouped level, mean memory specificity remains near zero

## Regime Audit

- Old regime: closed-loop tool commitment accepted a single generated slot/value and immediately returned the corresponding external state.
- Transition: the `repair_bottleneck` condition inserts a missing-return/API-error token after the first tool attempt, requiring a second repair commitment before the final query.
- Transported evidence: moved critical slot, visible-control null, closed-loop scoring, L4 cost guard, final memory specificity, and tool-value specificity are preserved.
- Rejected alternative: this is still not a natural-language API benchmark; the tool schema and error token are synthetic.
- Residual finding: the moved bottleneck survives an error-feedback and repair-commitment step. The agent retains the future-critical bit through the forced missing-return event and re-emits the correct slot/value at repair time.
- Readiness: synthetic API-recovery result is ready; natural-language schemas, malformed arguments, stochastic tool failures, and multi-step planning remain untested.
- Allowed claim: future control relevance can move finite memory and commitment sensitivity through a simple external-state repair loop in a transformer sequence agent.
- Next operation: replace supervised slot/value heads with structured tool-call strings or JSON actions so schema validity, parsing failures, and repair prompts become part of the model-visible interface.

## Interpretation Boundary

This is a neural-validated synthetic tool-recovery result, not a production
agent, human-behavior, autonomous natural-language tool-use, or consciousness
claim.
