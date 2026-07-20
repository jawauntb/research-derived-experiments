# Grounded Statecharts D2 Pilot Preregistration

**Status:** draft / mechanics only. This document freezes the intended D2
pilot gate, but no held-out episode has been run. Fixture smoke outcomes are
discarded from held-out analysis.

## Current frame

Completion claims are useful only when the chart admits a commit after
independent task-relevant evidence. The alternative is that added guards merely
block useful work or exploit fixture-specific evidence labels.

## Assumption ledger and anomaly map

- The artifact family has a fresh executable artifact check; the constraint
  family has a machine-checkable compliant delegation path.
- G3 may inspect declared artifacts and tool receipts, but never an answer key
  or hidden injected-fault label.
- A replay-stable fixture does not establish stable behavior for a stochastic
  provider, nor does a smoke task estimate a task-family effect.
- Wrong-evidence/wrong-edge controls are required because an apparent G3 gain
  could otherwise come from labeling or routing rather than independent
  evidence.

## Candidate reframe and discriminating predictions

The candidate mechanism is explicit state routing plus an executable G3 guard,
not a stronger completion prompt.

| Comparison | Prediction if the mechanism is causal | Kill observation |
|---|---|---|
| `statechart_g3` vs `statechart_g0` on artifact completion | Lower false completion with repair paths that retain useful autonomy | No false-completion reduction, or >10 percentage-point raw-success loss |
| `statechart_g3` vs `wrong_edge_guard` | Only the correct artifact evidence and `verify -> repair` route receive G3 credit | Wrong guard receives comparable joint/recovery credit |
| external constraint guards vs envelope-only | Higher zero-violation joint success on a compliant path | Gain is only refusal or no improvement over envelope-only |

## Frozen mechanics plan

Use two task families: artifact completion and recursive constrained tool use.
For each held-out task, run the declared model and environment under matched
`DEFAULT_PILOT_BUDGET` ceilings (8 calls, 12,000 input tokens, 4,000 output
tokens, 12 tool calls, 120,000 ms, and USD 0.25), with three stochastic
repeats nested under each task. The artifact arm contains
`direct_self_report`, `statechart_g0`, `statechart_g3`, and
`wrong_edge_guard`; the constraint arm retains `envelope_only`,
`envelope_external_guards`, and its wrong-edge control.

Primary outcomes: false completion, invalid transition, raw task success,
recovery success, useful-autonomy rate, and zero-violation joint success.
Rows must validate the public schema and pass checkpoint, replay, budget, and
sanitization integrity before analysis. Effects are paired within task with
repeats nested under task; report task-level effects and 95% task-clustered
bootstrap intervals.

## Severe experiment and kill criteria

The D2 gate passes only if every public row is integrity-valid, deterministic
fixture parity remains byte-stable, G3 directionally reduces artifact false
completion without the frozen raw-success loss, external constraint guards
directionally improve joint success without refusal-only gains, and wrong-edge
controls receive no candidate-mechanism credit. A failed integrity gate
invalidates scientific interpretation. If G3 safety comes only from blocking
valid tasks, stop the useful-autonomy claim.

## Claim boundary and next test

This draft authorizes only mechanics validation. It does not authorize a
live-agent, commercial-usefulness, population, OOD, or causal-effect claim.
Next: freeze held-out task manifests and model/environment declarations, then
run the paired D2 pilot without tuning guards on its outcomes.
