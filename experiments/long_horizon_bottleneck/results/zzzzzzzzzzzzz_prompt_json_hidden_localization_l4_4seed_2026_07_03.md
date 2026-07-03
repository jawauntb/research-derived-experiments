# Modal Result: Prompt JSON Hidden-Localization L4 Sweep

Run date: 2026-07-03

Confirmatory Modal run: https://modal.com/apps/generalintelligencecompany/main/ap-R9jK0vbrfRQfuq6vgjHymj

Dry-run budget check: https://modal.com/apps/generalintelligencecompany/main/ap-NJycvksq9uBEx4r97www8O

Smoke run: https://modal.com/apps/generalintelligencecompany/main/ap-EgkE6nttSJ7GMq2GyObEZ5

Artifact: `artifacts/long_horizon_bottleneck/prompt_json_hidden_localization_l4.json`

Preregistration: `papers/long_horizon_bottleneck/prompt_json_hidden_localization_preregistration.md`

## Configuration

- Models: `Qwen/Qwen2.5-0.5B-Instruct`, `Qwen/Qwen2.5-1.5B-Instruct`, `HuggingFaceTB/SmolLM2-1.7B-Instruct`
- GPU: Modal `L4`
- Remote model jobs: 3
- Max containers: 3
- Logical behavior cells: 192
- Hidden localization rows: 576
- Total rows: 768
- Hidden sites per bottleneck cell: 12
- Conditions: `prompt_json_format_control`, `prompt_json_visible_control`, `prompt_json_short_horizon_control`, `prompt_json_bottleneck`
- Episodes per cell: 8
- Hidden metric episodes per bottleneck cell: 2
- Critical slots: `0,1,2,3`
- Hidden positions: `prompt_final`, `generated_first`, `generated_final`
- Hidden layers: `early`, `mid`, `late`, `final`
- Base seed: `20260850`
- Timeout guard: 7200 seconds per model job
- Conservative timeout-based budget cap: `$6.47`
- User budget supplied to runner: `$25.00`

## Gate Summary

The confirmatory run is positive under the preregistered hidden-localization
gate. All behavior controls pass for all three models, behavioral
`prompt_json_bottleneck` passes for all three models, and at least one
registered hidden site passes the specificity and rank gates.

Terminal decision:

- Controls pass: yes.
- Behavioral prompt-level moved bottleneck passes: yes.
- Hidden localization pass: yes.
- Preregistered outcome: `positive`.

## Behavior Gates

| Group | Closed-loop final accuracy | Schema validity | First parsed slot | First parsed value | Gate |
| --- | ---: | ---: | ---: | ---: | --- |
| prompt_json_bottleneck/HuggingFaceTB/SmolLM2-1.7B-Instruct | 1.000 | 1.000 | 1.000 | 1.000 | pass |
| prompt_json_bottleneck/Qwen/Qwen2.5-0.5B-Instruct | 0.961 | 0.984 | 0.984 | 0.961 | pass |
| prompt_json_bottleneck/Qwen/Qwen2.5-1.5B-Instruct | 0.938 | 1.000 | 1.000 | 0.938 | pass |
| prompt_json_format_control/HuggingFaceTB/SmolLM2-1.7B-Instruct | n/a | 1.000 | n/a | n/a | pass |
| prompt_json_format_control/Qwen/Qwen2.5-0.5B-Instruct | n/a | 1.000 | n/a | n/a | pass |
| prompt_json_format_control/Qwen/Qwen2.5-1.5B-Instruct | n/a | 1.000 | n/a | n/a | pass |
| prompt_json_short_horizon_control/HuggingFaceTB/SmolLM2-1.7B-Instruct | 1.000 | 1.000 | 1.000 | 1.000 | pass |
| prompt_json_short_horizon_control/Qwen/Qwen2.5-0.5B-Instruct | 1.000 | 1.000 | 1.000 | 1.000 | pass |
| prompt_json_short_horizon_control/Qwen/Qwen2.5-1.5B-Instruct | 1.000 | 1.000 | 1.000 | 1.000 | pass |
| prompt_json_visible_control/HuggingFaceTB/SmolLM2-1.7B-Instruct | 1.000 | 1.000 | n/a | n/a | pass |
| prompt_json_visible_control/Qwen/Qwen2.5-0.5B-Instruct | 1.000 | 1.000 | n/a | n/a | pass |
| prompt_json_visible_control/Qwen/Qwen2.5-1.5B-Instruct | 1.000 | 1.000 | n/a | n/a | pass |

## Passing Hidden Sites

Seventeen registered `(model, token position, layer)` hidden sites passed.
Generated-final sites are the strongest and most consistent signal. Values
below are means with bootstrap 95% confidence intervals for
`memory_specificity_z`; all listed rows also have mean rank above chance.

| Site | Memory specificity z | 95% CI | Rank percentile |
| --- | ---: | ---: | ---: |
| HuggingFaceTB/SmolLM2-1.7B-Instruct/generated_final/mid | 228.301 | [129.438, 386.540] | 1.000 |
| Qwen/Qwen2.5-1.5B-Instruct/generated_final/early | 216.902 | [119.175, 332.137] | 0.922 |
| Qwen/Qwen2.5-0.5B-Instruct/generated_final/early | 183.444 | [99.032, 279.601] | 0.922 |
| HuggingFaceTB/SmolLM2-1.7B-Instruct/generated_final/early | 132.152 | [78.225, 194.584] | 1.000 |
| Qwen/Qwen2.5-0.5B-Instruct/generated_final/mid | 92.172 | [46.351, 143.808] | 0.922 |
| HuggingFaceTB/SmolLM2-1.7B-Instruct/generated_final/final | 74.022 | [50.923, 100.980] | 1.000 |
| HuggingFaceTB/SmolLM2-1.7B-Instruct/generated_final/late | 72.963 | [57.349, 89.785] | 1.000 |
| Qwen/Qwen2.5-1.5B-Instruct/generated_final/mid | 55.841 | [32.868, 84.134] | 0.945 |
| Qwen/Qwen2.5-0.5B-Instruct/generated_final/late | 16.361 | [7.522, 27.075] | 0.938 |
| Qwen/Qwen2.5-0.5B-Instruct/generated_final/final | 15.094 | [8.659, 22.562] | 0.945 |
| Qwen/Qwen2.5-1.5B-Instruct/generated_first/final | 8.270 | [3.027, 16.818] | 0.898 |
| Qwen/Qwen2.5-1.5B-Instruct/generated_final/late | 8.160 | [5.451, 11.604] | 0.945 |
| Qwen/Qwen2.5-1.5B-Instruct/prompt_final/late | 6.982 | [4.551, 9.603] | 0.961 |
| Qwen/Qwen2.5-1.5B-Instruct/prompt_final/final | 6.691 | [4.454, 9.145] | 0.969 |
| Qwen/Qwen2.5-1.5B-Instruct/generated_final/final | 6.508 | [4.300, 8.967] | 0.938 |
| Qwen/Qwen2.5-1.5B-Instruct/generated_first/late | 4.958 | [3.084, 7.328] | 0.953 |
| HuggingFaceTB/SmolLM2-1.7B-Instruct/generated_first/mid | 0.938 | [0.175, 1.805] | 0.703 |

## Interpretation

This result resolves the immediate ambiguity left by the first prompt-level
transfer run. The original final-prompt-token metric on Qwen 0.5B was too narrow:
behavior transferred, but that hidden site did not verify. The localization
replication shows that the moved-slot hidden signal is present in the generated
action trajectory, especially at final generated JSON tokens, and also appears
at late/final prompt-token sites for Qwen 1.5B.

The strongest allowed claim is still narrow: under this prompt, parser, model
set, and hidden-site grid, prompt-level behavior transfers and at least one
registered hidden site localizes the future-critical slot. This does not by
itself prove robust natural-language agent competence, production tool
reliability, or consciousness.

## Regime Audit

- Old regime: prompted Qwen 0.5B solved the parser-scored behavior, but final
  prompt-token hidden specificity was a controlled strong negative.
- Transition: hidden specificity is now localized over multiple models, layers,
  and token positions.
- Transported evidence: format control, visible control, short-horizon control,
  stochastic repair/no-op behavior, moved critical slots, and Modal L4 budget
  guard are preserved.
- New evidence: hidden localization passes at generated-final sites across all
  default models and at prompt-final sites for Qwen 1.5B.
- Residual risk: generated-token hidden states partly include the generated
  action token identity, so the next probe should separate prompt-state memory
  from action-surface commitment with activation patching or fixed-action
  counterfactuals.
- Readiness: the prompt-level hidden-localization replication reached a
  preregistered positive terminal outcome.
