# Modal Result: 8-Slot Stochastic Tool-Failure L4 Sweep

Run date: 2026-07-03

Modal run: https://modal.com/apps/generalintelligencecompany/main/ap-fGP2GWej3do2LkP1EFF1Eg

Budget dry run: https://modal.com/apps/generalintelligencecompany/main/ap-aDvNpG61VsLnHEW9KjNfJj

Artifact: `artifacts/long_horizon_bottleneck/stochastic_tool_failure_8slot_l4_4seed_2026_07_03.json`

## Configuration

- GPU: Modal `L4`
- Cells: 64 (`transformer` only, 2 conditions, 8 moved critical slots, 4 seeds)
- Conditions: `stochastic_failure_bottleneck`, `stochastic_visible_control`
- Registered clue slots: 8
- Slot argument vocabulary size: 10
- Failure probability: 0.5 per episode
- Sequence length: 160
- First commit position: 80
- Error or first-return position: 81
- Repair commit position: 82
- Repair return position: 83
- Train steps: 900
- Batch size: 256
- Hidden size: 64
- Max containers: 32
- Timeout guard: 900 seconds per cell
- Conservative timeout-based budget cap: `$17.26`
- User budget supplied to runner: `$25.00`
- Mean remote cell runtime: 18.08 seconds
- Max remote cell runtime: 19.21 seconds
- Base seed: 20260704

## Gate Summary

This reruns the stochastic tool-failure regime with twice as many registered
clue slots. The slot argument vocabulary grows from 6 to 10, and the sequence is
lengthened so the first commit still occurs after all clue tokens.

| Group | Closed-loop final accuracy | Teacher-forced final accuracy | First fields | First schema valid | First parsed slot | First parsed value | Failed repair fields | Failed repair schema | Failed repair slot | Failed repair value | Success repair no-op | Sampled failure rate | Memory specificity z | Tool-value specificity z | Gate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| stochastic_failure_bottleneck/transformer | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.506 | +3.023 | +3.023 | pass |
| stochastic_visible_control/transformer | 1.000 | 1.000 | 1.000 no-op | 1.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 0.506 | -0.000 | +0.000 | pass |

Pooled 8-slot stochastic-failure gates pass:

- Closed-loop final behavior: pass, mean accuracy 1.000
- Teacher-forced final diagnostic: mean accuracy 1.000
- First multifield action fields: pass, mean accuracy 1.000
- First parsed slot/value: pass, mean accuracy 1.000 / 1.000
- Failed repair fields and schema: pass, mean accuracy 1.000 / 1.000
- Failed repair parsed slot/value: pass, mean accuracy 1.000 / 1.000
- Success-path repair no-op: pass, mean accuracy 1.000
- Sampled failure rate: 0.506, 95% CI [0.499, 0.512]
- Final memory-state specificity: pass, mean +3.023
- Repair-field tool specificity: pass, mean +3.023
- Visible-control null: pass, mean memory specificity remains near zero

## Regime Audit

- Old regime: stochastic tool failures were confirmed with four registered clue slots and a slot argument vocabulary of 6.
- Transition: the same stochastic repair/no-op gate is run with eight registered clue slots, a slot argument vocabulary of 10, and a longer sequence.
- Transported evidence: moved critical slot, visible-control null, closed-loop scoring, L4 cost guard, final memory specificity, repair-field specificity, schema validity, parsed slot/value accuracy, sampled failure rate, and conditional repair/no-op behavior are preserved.
- Rejected alternative: this is not natural-language argument use; the argument namespace is larger but still a fixed discrete classifier.
- Residual finding: the moved bottleneck survives stochastic API feedback and conditional repair behavior in a larger argument namespace.
- Readiness: 8-slot stochastic synthetic result is confirmed on Modal `L4`; natural-language argument surfaces remain untested.
- Allowed claim: future control relevance can move finite memory and commitment sensitivity through a larger parsed tool schema under stochastic API feedback.
- Next operation: replace fixed discrete argument IDs with natural-language or alias-rich argument surfaces while preserving the stochastic feedback gate.

## Interpretation Boundary

This is a neural-validated synthetic larger-schema result, not a production
agent, real API reliability benchmark, autonomous natural-language tool-use, or
consciousness claim.
