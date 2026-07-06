# API Black-Box Multi-Provider Replication

Date: 2026-07-06

## Outcome

Prompt-family replication outcome: `positive` across 3 provider/model runs.
External-stress outcome: `mixed with controlled strong negative` across 3 provider/model runs.
Total scored rows: 528; total planned API requests: 792.

## Verification Signals

API prompt-family multi-provider gate pass: yes.
API external-stress all-provider gate pass: no.
API external-stress controlled strong negative found: yes.
API failed-cell controls preserved: yes.

## Provider Matrix

| Suite | Provider | Model | Rows | Requests | Cells | Failed cells | Outcome |
|---|---|---|---:|---:|---:|---:|---|
| external_stress | anthropic | `claude-haiku-4-5-20251001` | 80 | 120 | 20 | 0 | `positive` |
| external_stress | gemini | `gemini-3.1-flash-lite` | 80 | 120 | 20 | 0 | `positive` |
| external_stress | openai-responses | `gpt-4.1-nano` | 80 | 120 | 20 | 2 | `strong_negative` |
| prompt_family | anthropic | `claude-haiku-4-5-20251001` | 96 | 144 | 3 | 0 | `positive` |
| prompt_family | gemini | `gemini-3.1-flash-lite` | 96 | 144 | 3 | 0 | `positive` |
| prompt_family | openai-responses | `gpt-4.1-nano` | 96 | 144 | 3 | 0 | `positive` |

## Failure Surface

| Suite | Provider | Model | Stress | Family | Controls | Bottleneck | Failed condition gates |
|---|---|---|---|---|---|---|---|
| external_stress | openai-responses | `gpt-4.1-nano` | 4slot_gap8 | dispatch | yes | no | prompt_json_bottleneck |
| external_stress | openai-responses | `gpt-4.1-nano` | 8slot_gap16 | dispatch | yes | no | prompt_json_bottleneck |

## Regime Audit

- Old regime: one-provider black-box behavior after open-model hidden-state and causal-patch evidence.
- Transition: matched multi-provider API behavior with the same parser, controls, bottleneck gates, and repair gates.
- Transported evidence: prompt-family suite, external-stress axes, request guard, JSONL rows, and scored summaries.
- Rejected alternatives: smoke runs are not counted in the matched matrix, and black-box API behavior is not treated as hidden-state or production-tool evidence.
- Residual finding: provider-specific stress sensitivity is now visible; a run can be positive on the registered prompt-family suite and still fail a controlled dispatch stress cell.
- Readiness: prompt-family gates pass across all tested providers; external-stress readiness is mixed because failed cells remain under passing controls.
- Allowed claim: multi-provider black-box behavioral replication for the tested suites, with any failed stress cells treated as behavioral counterevidence rather than hidden-state evidence.
- Next operation: isolate the dispatch failure into wording, value-copying, and repair-memory variants.

## Local Artifacts

- `artifacts/long_horizon_bottleneck/api_blackbox_anthropic_haiku45_external_stress_summary.json`
- `artifacts/long_horizon_bottleneck/api_blackbox_anthropic_haiku45_prompt_family_summary.json`
- `artifacts/long_horizon_bottleneck/api_blackbox_gemini_flash_lite_external_stress_multi_summary.json`
- `artifacts/long_horizon_bottleneck/api_blackbox_gemini_flash_lite_prompt_family_multi_summary.json`
- `artifacts/long_horizon_bottleneck/api_blackbox_openai_gpt41_nano_external_stress_summary.json`
- `artifacts/long_horizon_bottleneck/api_blackbox_openai_gpt41_nano_prompt_family_summary.json`
