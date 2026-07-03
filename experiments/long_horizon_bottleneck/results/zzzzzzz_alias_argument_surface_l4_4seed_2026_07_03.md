# Modal Result: Alias Argument-Surface L4 Sweep

Run date: 2026-07-03

Modal run: https://modal.com/apps/generalintelligencecompany/main/ap-Dyuc8TrXW3aiQotS8TvejG

Budget dry run: https://modal.com/apps/generalintelligencecompany/main/ap-4ctppEBLMpp7uMinqw7ZGz

Artifact: `artifacts/long_horizon_bottleneck/alias_argument_surface_l4_4seed_2026_07_03.json`

## Configuration

- GPU: Modal `L4`
- Cells: 32 (`transformer` only, 2 conditions, 4 moved critical slots, 4 seeds)
- Conditions: `alias_stochastic_bottleneck`, `alias_visible_control`
- Registered clue slots: 4
- Aliases per canonical slot: 3
- Alias argument vocabulary size: 14
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
- Mean remote cell runtime: 15.07 seconds
- Max remote cell runtime: 16.56 seconds
- Base seed: 20260704

## Gate Summary

This run replaces the compact slot argument with an alias-rich argument
surface. Each canonical clue slot has three equivalent aliases. The training
loss accepts any alias in the correct slot's alias set, while the evaluator
parses predicted aliases back to canonical slots before applying the same
stochastic repair/no-op checks.

- alias_stochastic_bottleneck pass: final 1.000, parsed slot/value 1.000 / 1.000, failed repair 1.000, success no-op 1.000
- alias_visible_control pass: final 1.000, no-op fields 1.000, memory specificity +0.000

| Group | Closed-loop final accuracy | Teacher-forced final accuracy | First fields | First schema valid | First parsed slot | First parsed value | Failed repair fields | Failed repair schema | Failed repair slot | Failed repair value | Success repair no-op | Sampled failure rate | Memory specificity z | Tool-value specificity z | Gate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| alias_stochastic_bottleneck/transformer | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.506 | +2.309 | +2.309 | pass |
| alias_visible_control/transformer | 1.000 | 1.000 | 1.000 no-op | 1.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 0.506 | +0.000 | -0.000 | pass |

Pooled alias stochastic-failure gates pass:

- Closed-loop final behavior: pass, mean accuracy 1.000
- Teacher-forced final diagnostic: mean accuracy 1.000
- First alias-equivalent action fields: pass, mean accuracy 1.000
- First parsed slot/value: pass, mean accuracy 1.000 / 1.000
- Failed repair fields and schema: pass, mean accuracy 1.000 / 1.000
- Failed repair parsed slot/value: pass, mean accuracy 1.000 / 1.000
- Success-path repair no-op: pass, mean accuracy 1.000
- Sampled failure rate: 0.506, 95% CI [0.496, 0.515]
- Final memory-state specificity: pass, mean +2.309
- Repair-field tool specificity: pass, mean +2.309
- Visible-control null: pass, mean memory specificity remains near zero

## Regime Audit

- Old regime: stochastic tool failures were confirmed with compact slot-id arguments and then with an 8-slot larger argument namespace.
- Transition: the compact slot argument is replaced by three aliases per canonical slot, growing the argument vocabulary from 6 to 14 while preserving stochastic first-call failures.
- Transported evidence: moved critical slot, visible-control null, closed-loop scoring, L4 cost guard, final memory specificity, repair-field specificity, schema validity, parsed slot/value accuracy, sampled failure rate, and conditional repair/no-op behavior are preserved.
- Rejected alternative: this is not free-form JSON or true natural-language tool use; aliases are fixed classifier labels with synonym-like equivalence classes.
- Residual finding: the moved bottleneck survives stochastic API feedback and conditional repair behavior when the argument surface is alias-rich rather than a compact slot id.
- Readiness: alias-rich synthetic result is confirmed on Modal `L4`; true text-prompt tool use and multi-step planning variants remain optional follow-on regimes.
- Allowed claim: future control relevance can move finite memory and commitment sensitivity through a parsed tool schema under stochastic API feedback, even when the argument field contains synonym-like aliases.
- Next operation: package the result ladder into a field-facing writeup, or run a text/LLM prompt variant if the goal shifts from synthetic mechanism to agent realism.

## Interpretation Boundary

This is a neural-validated synthetic alias-surface result, not a production
agent, real API reliability benchmark, autonomous natural-language tool-use, or
consciousness claim.
