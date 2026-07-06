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
- Fixed-prefix causal patch: positive value-token logit shifts at
  `value_prefix_final` late/final sites in all three model families.
- Prompt-family causal patch robustness: positive across standard, compact, and
  audit-checklist prompt framings.
- API black-box behavioral benchmark: Gemini 3.1 Flash-Lite, Anthropic Haiku
  4.5, and OpenAI GPT-4.1 Nano all pass the matched prompt-family suite.
  Gemini and Anthropic pass the external-stress suite; OpenAI produces a
  controlled strong negative on two `dispatch` stress cells.
- API dispatch robustness characterization: a 720-request Modal CPU follow-up
  finds the OpenAI GPT-4.1 Nano dispatch failure is sparse, not broad. Across
  16 `(stress, critical slot)` cells, 15 pass; only 8-slot/gap-16 at critical
  slot 0 reproduces as a failed-repair value miss, and neutral wording,
  copy assistance, and repair hinting all pass.
- Latest models: `Qwen/Qwen2.5-0.5B-Instruct`, `Qwen/Qwen2.5-1.5B-Instruct`, `HuggingFaceTB/SmolLM2-1.7B-Instruct`.
- Latest prompt-level causal artifact: `artifacts/long_horizon_bottleneck/prompt_json_prompt_family_causal_patch_l4.json`.
- Latest API artifact: `artifacts/long_horizon_bottleneck/api_dispatch_robustness_openai_gpt41_nano_summary.json`.
- Latest committed report: `experiments/long_horizon_bottleneck/results/zzzzzzzzzzzzzzzzzzzz_api_dispatch_robustness_openai_gpt41_nano_2026_07_06.md`.

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

## Fixed-Prefix Causal Patch Terminal Result

The causal-patch pass tested whether the localized state can shift the
behavior-adjacent next-token logits before the JSON `value` field. It patched a
donor hidden state from the base prompt/prefix into a critical-slot-flipped
prompt/prefix, then measured the donor-value minus corrupted-value logit margin.

The confirmatory run is positive:

- clean prompts prefer the donor value and corrupted prompts prefer the flipped
  value;
- `value_prefix_final` late/final patch sites pass in all three model families;
- prompt-final patch sites do not pass, localizing the causal leverage to the
  action/value prefix state;
- strongest effect: `SmolLM2/value_prefix_final/final`, patch effect 7.053,
  95% CI [6.738, 7.344], recovery 0.899.

Outcome: `positive`.

## Prompt-Family Causal Patch Terminal Result

The prompt-family robustness pass reran the causal-patch grid across three
frozen prompt framings: `standard`, `compact`, and `ledger`/audit-checklist.

The confirmatory run is positive:

- all 9 `(prompt family, model)` pairs are causally ready;
- all 9 pairs have at least one passing default patch group;
- `value_prefix_final` late/final sites pass throughout;
- prompt-final sites remain negative controls;
- strongest final-layer value-prefix effect: compact Qwen2.5-1.5B, patch effect
  7.754, 95% CI [7.282, 8.234], recovery 0.937.

Outcome: `positive`.

## API Black-Box Behavioral Terminal Result

The API benchmark exposes the moved-bottleneck task as a one-command black-box
evaluator. It emits JSONL rows and scored summaries for provider/model runs.

The matched multi-provider prompt-family behavior suite is positive:

- 288 scored rows;
- 432 API requests;
- providers/models: `gemini-3.1-flash-lite`,
  `claude-haiku-4-5-20251001`, and `gpt-4.1-nano`;
- all `standard`, `compact`, and `ledger` cells complete;
- controls pass and bottleneck/repair gates pass in all nine provider/family
  cells.

The matched external-validity stress suite is mixed:

- 240 scored rows;
- 360 API requests;
- Gemini and Anthropic pass all 20 stress/family cells;
- OpenAI GPT-4.1 Nano passes controls but fails two `dispatch` bottleneck cells;
- axes include 8-slot width, longer filler gaps, `retrieval`, and `dispatch`
  prompt framings.

Outcome: prompt-family `positive`; external stress `mixed with controlled strong
negative`.

## API Dispatch Robustness Terminal Result

The dispatch robustness runner keeps the same provider adapter, JSON parser,
controls, failed-repair phase, and diagnostic variants, then expands the
OpenAI GPT-4.1 Nano characterization across four stress cells and critical
slots 0-3 on Modal CPU workers.

The robustness follow-up is sparse reproduced and localized:

- 336 scored rows;
- 720 API requests;
- controls pass;
- 16 `(stress, critical slot)` cells complete;
- 15 cells do not reproduce the original dispatch failure;
- only 8-slot/gap-16 at critical slot 0 reproduces, as a failed-repair value
  miss: first action 1.000, repair-after-error 0.000, success no-op 1.000;
- neutral wording, copy-assisted dispatch, and repair-hinted dispatch all pass
  for the reproduced cell.

Outcome: `sparse_reproduced_localized`. The allowed claim is narrower than the
initial stress negative: for this tested OpenAI model, the dispatch failure is a
real but sparse black-box repair-surface pressure point, not a broadly stable
dispatch failure across slots or stress settings.

## Use

Use this benchmark when final task success is too weak and the real question is whether an agent's internal state tracks the variable that will later control an action or tool commitment.

## Non-Claims

This benchmark does not establish production tool reliability, autonomous API competence, human cognition, neural validation in humans, or consciousness. API black-box runs are behavioral only; they do not establish hidden-state localization or causal patching.
