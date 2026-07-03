# Benchmark Card: Long-Horizon Moved Bottleneck

## Purpose

Test whether future control relevance moves both generated behavior and internal memory-state sensitivity toward the early variable that will later control action.

## Current Status

- Synthetic trained-agent ladder: positive through autoregressively decoded JSON-like action strings.
- Prompt-level open-model transfer: behavior positive; initial final-prompt hidden gate was a controlled strong negative.
- Hidden-localization replication: positive across the default multi-model, multi-layer,
  multi-token-position grid.
- Fixed-action localization counterfactual: positive after generated action tokens
  are held fixed under base and slot-flipped prompts.
- Latest models: `Qwen/Qwen2.5-0.5B-Instruct`, `Qwen/Qwen2.5-1.5B-Instruct`, `HuggingFaceTB/SmolLM2-1.7B-Instruct`.
- Latest confirmatory artifact: `artifacts/long_horizon_bottleneck/prompt_json_fixed_action_localization_l4.json`.
- Latest committed report: `experiments/long_horizon_bottleneck/results/zzzzzzzzzzzzzz_prompt_json_fixed_action_localization_l4_4seed_2026_07_03.md`.

## Prompt-Level Terminal Result

Controls and behavior pass:

- format/schema validity: 1.000;
- visible-control final/no-op/schema gates: 1.000;
- short-horizon final/schema/slot/value gates: 1.000;
- prompt bottleneck closed-loop final accuracy: 0.977;
- first parsed slot/value: 0.984 / 0.977;
- failed-repair parsed slot/value: 1.000 / 1.000;
- success-path no-op: 1.000.

The hidden-state gate fails:

- memory specificity z: +0.695;
- 95% bootstrap CI: [-0.376, 2.080];
- preregistered hidden gate requires the CI lower bound to be above zero.

Outcome: `strong_negative` for that single final-prompt hidden site.

## Hidden-Localization Terminal Result

The follow-up sweep tested whether the hidden negative was a bad measurement
site. It preserved the prompt-transfer behavior gates and probed
`prompt_final`, `generated_first`, and `generated_final` hidden states at
`early`, `mid`, `late`, and `final` layer aliases across the default cheap model
set: `Qwen/Qwen2.5-0.5B-Instruct`, `Qwen/Qwen2.5-1.5B-Instruct`, and
`HuggingFaceTB/SmolLM2-1.7B-Instruct`.

The confirmatory run is positive:

- controls pass for all three models;
- behavioral moved-bottleneck passes for all three models;
- 17 registered hidden sites pass specificity and rank gates;
- strongest sites are generated-final states, with positive CIs across all three model families.

Outcome: `positive`.

## Fixed-Action Localization Terminal Result

The fixed-action counterfactual tested whether the generated-action localization
positive was just answer-token identity. The runner teacher-forced the same
assistant JSON action under each base prompt and slot-flipped counterfactual,
then measured `prompt_final`, `fixed_noop_first/final`, and
`fixed_read_first/final` states across the same model and layer grid.

The confirmatory run is positive:

- controls pass for all three models;
- behavioral moved-bottleneck passes for all three models;
- 24 registered hidden sites pass specificity and rank gates;
- fixed noop final-layer sites pass in all three model families;
- strongest fixed noop site: `Qwen/Qwen2.5-1.5B-Instruct/fixed_noop_final/final`,
  specificity z 12.514, 95% CI [8.035, 18.310], rank 0.984.

Outcome: `positive`.

## Use

Use this benchmark when final task success is too weak and the real question is whether an agent's internal state tracks the variable that will later control an action or tool commitment.

## Non-Claims

This benchmark does not establish production tool reliability, autonomous API competence, human cognition, neural validation in humans, or consciousness.
