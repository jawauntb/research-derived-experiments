# Modal Result: Tool-Commitment L4 Sweep

Run date: 2026-07-02

Modal run: https://modal.com/apps/generalintelligencecompany/main/ap-CKKyTPJ4CpZFMIFSBGkpSy

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
- Mean remote cell runtime: 9.26 seconds
- Max remote cell runtime: 9.81 seconds

## Gate Summary

| Group | Final accuracy | Tool slot accuracy | Tool value accuracy | Memory specificity z | Tool-value specificity z | Gate |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| tool_bottleneck/transformer | 1.000 | 1.000 | 1.000 | +2.309 | +2.309 | pass |
| visible_control/transformer | 1.000 | 1.000 | n/a | +0.000 | -0.000 | pass |

Pooled tool-bottleneck gates pass:

- Final behavior: pass, mean accuracy 1.000
- Tool slot commitment: pass, mean accuracy 1.000
- Tool value commitment: pass, mean accuracy 1.000
- Final memory-state specificity: pass, 95% CI lower bound > 0
- Tool-value logit specificity: pass, 95% CI lower bound > 0
- Visible-control null: pass, mean memory specificity remains near zero

## Regime Audit

- Old regime: synthetic sequence memory with hidden-state gates and no explicit action/API commitment.
- Transition: the agent now has a commit token, a tool-slot head, a tool-value head, and a later tool-return token representing external state.
- Transported evidence: the moved-slot intervention, visible-control null, L4 cost guard, and final memory specificity gates are preserved.
- Rejected alternative: this is still not a production tool-use benchmark; it is a synthetic external-state bridge.
- Residual finding: the moved bottleneck transfers from hidden sequence memory into a supervised tool commitment interface. The critical slot controls both final hidden-state sensitivity and the tool-value commitment logits.
- Readiness: synthetic tool-commitment result is ready; natural language tool use, API errors, and model-generated tool calls remain untested.
- Allowed claim: future control relevance can move finite memory and commitment sensitivity in a transformer sequence agent with an explicit external-state interface.
- Next operation: introduce closed-loop generated tool calls, where the model's chosen tool action determines the returned state rather than using teacher-forced tool returns.

## Interpretation Boundary

This is a neural-validated synthetic tool-interface result, not a production
agent, human-behavior, autonomous tool-use, or consciousness claim.
