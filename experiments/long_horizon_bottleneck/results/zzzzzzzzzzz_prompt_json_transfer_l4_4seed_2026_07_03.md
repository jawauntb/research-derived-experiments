# Modal Result: Prompt JSON Transfer L4 Sweep

Run date: 2026-07-03

Confirmatory Modal run: https://modal.com/apps/generalintelligencecompany/main/ap-YGiBjPASNZrq2bEWl84nPD

Budget dry run: https://modal.com/apps/generalintelligencecompany/main/ap-b7wEr3XNgOX9C7NG0bQxkj

Calibration runs: https://modal.com/apps/generalintelligencecompany/main/ap-qv3Zepun0hDJUMXRDPgGtE, https://modal.com/apps/generalintelligencecompany/main/ap-mKecq6Eh7k3Hl2IvTWmSkn, https://modal.com/apps/generalintelligencecompany/main/ap-aekLQN0iNcUk1ySdUrQ5I2

Artifact: `artifacts/long_horizon_bottleneck/prompt_json_transfer_l4.json`

Preregistration: `papers/long_horizon_bottleneck/prompt_json_transfer_preregistration.md`

## Configuration

- Model: `Qwen/Qwen2.5-0.5B-Instruct`
- GPU: Modal `L4`
- Remote containers: 1
- Logical cells: 64 (4 conditions, 4 moved critical slots, 4 seeds)
- Conditions: `prompt_json_format_control`, `prompt_json_visible_control`, `prompt_json_short_horizon_control`, `prompt_json_bottleneck`
- Episodes per cell: 8
- Hidden metric episodes per bottleneck cell: 2
- Registered clue slots: 4
- Text phrase variants per canonical slot: 3
- Failure probability: 0.5 per episode
- Base seed: 20260800
- Timeout guard: 3600 seconds
- Conservative timeout-based budget cap: `$1.08`
- User budget supplied to runner: `$25.00`
- Remote runtime: 212.0 seconds

## Gate Summary

The confirmatory run is a controlled strong negative for the full prompt-level gate. Format, visible-control, short-horizon, and behavioral moved-bottleneck gates pass. The full bottleneck gate fails only because hidden critical-slot specificity is not confirmed: the mean specificity is positive, but the 95% bootstrap lower bound crosses zero.

| Group | Closed-loop final accuracy | Schema validity | First parsed slot | First parsed value | Failed repair slot | Failed repair value | Success repair no-op | Memory specificity z | Memory rank percentile | Gate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| prompt_json_bottleneck/Qwen/Qwen2.5-0.5B-Instruct | 0.977 | 0.984 | 0.984 | 0.977 | 1.000 | 1.000 | 1.000 | +0.695, CI [-0.376, 2.080] | 0.594 | fail |
| prompt_json_format_control/Qwen/Qwen2.5-0.5B-Instruct | n/a | 1.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | pass |
| prompt_json_short_horizon_control/Qwen/Qwen2.5-0.5B-Instruct | 1.000 | 1.000 | 1.000 | 1.000 | n/a | n/a | n/a | n/a | n/a | pass |
| prompt_json_visible_control/Qwen/Qwen2.5-0.5B-Instruct | 1.000 | 1.000 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | pass |

Terminal decision:

- Controls pass: yes.
- Behavioral prompt-level moved bottleneck passes: yes.
- Hidden critical-slot specificity gate passes: no.
- Preregistered outcome: `strong_negative`.

## Calibration Log

Calibration was capped at three attempts before the held-out confirmatory run.

- Calibration 1 found that JSON no-op controls passed, but the short-control prompt let the model use the task title as a slot name and sometimes spell `second clue` as `second_clue`.
- Calibration 2 froze a clearer allowed-slot prompt and parser normalization for underscores/hyphens. Format, visible, short, and behavioral bottleneck gates passed without hidden metrics.
- Calibration 3 exercised hidden-state scoring. It suggested that the hidden critical-slot metric would likely be the limiting gate. No further prompt, parser, or threshold changes were made.

The confirmatory run used held-out base seed `20260800`.

## Regime Audit

- Old regime: synthetic trained agents passed generated and autoregressively decoded JSON-like action surfaces with moved-slot hidden specificity and visible-control nulls.
- Transition: the action surface is now a prompted pretrained open model emitting parser-scored JSON text, with real tokenizer decoding and malformed-output recovery.
- Transported evidence: moved critical slot, visible-control null, short-horizon control, JSON format control, stochastic first-call failure, repair/no-op behavior, Modal L4 budget guard, and hidden critical-slot sensitivity are preserved.
- Rejected alternatives: a failed format or short-control result would have been inconclusive rather than a strong negative; calibration removed those interface failures before confirmatory testing.
- Residual finding: prompt-level JSON behavior transfers strongly, but the hidden-state sensitivity metric does not become reliably critical-slot specific under this prompt/model setup.
- Readiness: the prompt-level transfer gate reached a controlled strong negative under the preregistered decision rule.
- Allowed claim: Qwen2.5-0.5B-Instruct can solve the parser-scored prompt-level moved-bottleneck behavior under stochastic repair, but this run does not support the stronger claim that its hidden-state geometry reliably tracks the future-critical slot.
- Next operation: replicate the prompt-level gate with a stronger open model and compare hidden metrics at multiple token positions/layers before treating the hidden-state negative as model-general.

## Interpretation Boundary

This is a prompt-level generated-behavior result with an open pretrained model. It is not a production-agent reliability result, autonomous API-use result, human behavioral claim, neural validation claim for humans, or consciousness claim.
