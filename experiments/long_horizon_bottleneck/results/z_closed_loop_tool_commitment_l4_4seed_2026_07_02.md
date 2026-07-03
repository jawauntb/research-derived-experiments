# Modal Result: Closed-Loop Tool-Commitment L4 Sweep

Run date: 2026-07-02

Modal run: https://modal.com/apps/generalintelligencecompany/main/ap-3DzDhKpLh8XgmygQOhmVie

Budget dry run: https://modal.com/apps/generalintelligencecompany/main/ap-8Ot5fec7bUHkjDsNInf0iG

## Configuration

- GPU: Modal `L4`
- Cells: 32 (`transformer` only, 2 conditions, 4 moved critical slots, 4 seeds)
- Sequence length: 128
- Commit position: 64
- Train steps: 700
- Batch size: 256
- Hidden size: 64
- Max containers: 32
- Timeout guard: 900 seconds per cell
- Conservative timeout-based budget cap: `$8.63`
- User budget supplied to runner: `$25.00`
- Mean remote cell runtime: 9.31 seconds
- Max remote cell runtime: 10.18 seconds

## Gate Summary

The gate uses closed-loop final accuracy; teacher-forced final accuracy remains diagnostic.

| Group | Closed-loop final accuracy | Teacher-forced final accuracy | Tool slot accuracy | Tool value accuracy | Memory specificity z | Tool-value specificity z | Gate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| tool_bottleneck/transformer | 1.000 | 1.000 | 1.000 | 1.000 | +2.309 | +2.309 | pass |
| visible_control/transformer | 1.000 | 1.000 | 1.000 | n/a | +0.000 | -0.000 | pass |

Pooled tool-bottleneck gates pass:

- Closed-loop final behavior: pass, mean accuracy 1.000
- Teacher-forced final diagnostic: mean accuracy 1.000
- Tool slot commitment: pass, mean accuracy 1.000
- Tool value commitment: pass, mean accuracy 1.000
- Final memory-state specificity: pass, 95% CI lower bound > 0
- Tool-value logit specificity: pass, 95% CI lower bound > 0
- Visible-control null: pass at the grouped level, mean memory specificity remains near zero

## Regime Audit

- Old regime: tool-return evaluation was teacher-forced, so the final state could be correct even if generated tool actions were not actually responsible for the returned external state.
- Transition: at evaluation time the model first emits a tool slot and value at the commit token, then that predicted action is written into the later tool-return token before the final query.
- Transported evidence: moved critical slot, visible-control null, L4 cost guard, final memory specificity, tool-slot accuracy, and tool-value specificity are preserved.
- Rejected alternative: this is not yet natural-language tool use or a production API benchmark; tool calls remain synthetic supervised heads.
- Residual finding: the moved bottleneck survives a closed-loop external-state handoff. The model's own committed slot and value are sufficient to recover the future-critical bit, and sensitivity remains concentrated on the moved critical slot.
- Readiness: closed-loop synthetic tool-commitment result is ready; natural language tool schemas, API failures, and real model tool-calling remain untested.
- Allowed claim: future control relevance can move finite memory and commitment sensitivity in a transformer sequence agent even when the final decision depends on the agent's own earlier external-state commitment.
- Next operation: move from synthetic slot/value heads to a small language/tool-call environment with schema errors, missing returns, and recovery attempts.

## Interpretation Boundary

This is a neural-validated synthetic tool-interface result, not a production
agent, human-behavior, autonomous natural-language tool-use, or consciousness
claim.
