# API Black-Box Gemini Flash-Lite Behavioral Benchmark

Date: 2026-07-06

Outcome: `positive`

Preregistration: `papers/long_horizon_bottleneck/api_blackbox_preregistration.md`

Local artifacts:

- `artifacts/long_horizon_bottleneck/api_blackbox_fixture_prompt_family_summary.json`
- `artifacts/long_horizon_bottleneck/api_blackbox_fixture_prompt_family_rows.jsonl`
- `artifacts/long_horizon_bottleneck/api_blackbox_fixture_external_stress_summary.json`
- `artifacts/long_horizon_bottleneck/api_blackbox_fixture_external_stress_rows.jsonl`
- `artifacts/long_horizon_bottleneck/api_blackbox_gemini_flash_lite_smoke_summary.json`
- `artifacts/long_horizon_bottleneck/api_blackbox_gemini_flash_lite_smoke_rows.jsonl`
- `artifacts/long_horizon_bottleneck/api_blackbox_gemini_flash_lite_prompt_family_summary.json`
- `artifacts/long_horizon_bottleneck/api_blackbox_gemini_flash_lite_prompt_family_rows.jsonl`
- `artifacts/long_horizon_bottleneck/api_blackbox_gemini_flash_lite_external_stress_summary.json`
- `artifacts/long_horizon_bottleneck/api_blackbox_gemini_flash_lite_external_stress_rows.jsonl`

## Question

The previous prompt-family causal-patch result showed that open-model
value-prefix hidden states can causally shift the JSON value-token readout
across three frozen prompt framings. This run asks the black-box behavioral
question: can a production API model pass the same parser-scored JSON action
contract without hidden-state access?

## Design

- Provider: Gemini API.
- Model: `gemini-3.1-flash-lite`.
- Endpoint family: `generateContent`.
- Temperature: 0.
- Max output tokens: 64.
- Parser: shared `parse_prompt_json_action`.
- Prompt-family suite: `standard`, `compact`, `ledger`.
- External-stress suite: `standard`, `compact`, `ledger`, `retrieval`,
  `dispatch`.
- Conditions: format control, visible control, short-horizon control, and
  long-horizon bottleneck with failed-tool and successful-tool repair turns.

Provider adapter details were checked against current official API references:
OpenAI Chat Completions/Responses, Anthropic Messages, and Gemini
`generateContent`. The committed evaluator is dependency-free and also supports
OpenAI-compatible chat endpoints plus deterministic fixture providers.

## Verification Signals

API prompt-family controls gate pass: yes.

API prompt-family bottleneck gate pass: yes.

API external-stress controls gate pass: yes.

API external-stress bottleneck gate pass: yes.

## Package Validation

The deterministic fixture provider validates the benchmark package and scoring
surface without spending API tokens.

| Run | Rows | Cells | Outcome |
|---|---:|---:|---|
| fixture prompt-family suite | 96 | 3 | positive |
| fixture external-stress suite | 320 | 20 | positive |

## Gemini Prompt-Family Run

Command:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
  env PYTHONPATH=. python3 -m experiments.long_horizon_bottleneck.eval \
  --provider gemini \
  --models gemini-3.1-flash-lite \
  --suite prompt_family \
  --prompt-families standard,compact,ledger \
  --seeds 1 \
  --episodes-per-cell 2 \
  --critical-slots 0,1,2,3 \
  --max-requests 150 \
  --max-output-tokens 64 \
  --sleep-seconds 0.05 \
  --out artifacts/long_horizon_bottleneck/api_blackbox_gemini_flash_lite_prompt_family_summary.json \
  --jsonl artifacts/long_horizon_bottleneck/api_blackbox_gemini_flash_lite_prompt_family_rows.jsonl
```

Result:

| Prompt family | Bottleneck final | First slot | First value | Failed repair slot/value | Success no-op |
|---|---:|---:|---:|---:|---:|
| `standard` | 1.000 | 1.000 | 1.000 | 1.000 / 1.000 | 1.000 |
| `compact` | 1.000 | 1.000 | 1.000 | 1.000 / 1.000 | 1.000 |
| `ledger` | 1.000 | 1.000 | 1.000 | 1.000 / 1.000 | 1.000 |

The run produced 96 scored rows and 144 API requests. All three
`(prompt family, model)` cells were complete, controls-pass, and
bottleneck-pass.

## Gemini External-Stress Run

Command:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
  env PYTHONPATH=. python3 -m experiments.long_horizon_bottleneck.eval \
  --provider gemini \
  --models gemini-3.1-flash-lite \
  --suite external_stress \
  --prompt-families standard,compact,ledger,retrieval,dispatch \
  --seeds 1 \
  --episodes-per-cell 1 \
  --critical-slots 0 \
  --n-slots 4,8 \
  --slot-gap 8,16 \
  --max-requests 150 \
  --max-output-tokens 64 \
  --sleep-seconds 0.05 \
  --out artifacts/long_horizon_bottleneck/api_blackbox_gemini_flash_lite_external_stress_summary.json \
  --jsonl artifacts/long_horizon_bottleneck/api_blackbox_gemini_flash_lite_external_stress_rows.jsonl
```

Result:

- 80 scored rows;
- 120 API requests;
- 20 stress/family cells;
- all 20 cells complete, controls-pass, and bottleneck-pass.

The stress axes covered longer filler gaps, 8-slot width, and the two extra
black-box prompt framings (`retrieval` and `dispatch`).

## Regime Audit

- Old regime: open-model hidden-state localization and causal patching over
  prompt-level JSON actions.
- Transition: black-box API behavior with no hidden-state access, dependency-free
  provider adapters, JSONL outputs, and a public CLI.
- Transported evidence: same moved-bottleneck prompt contract, same JSON parser,
  same control/repair gates, and same prompt-family vocabulary for the primary
  suite.
- Rejected alternatives: no hidden-state or causal-patch claim is made for API
  providers; raw ignored `artifacts/` are not treated as committed evidence.
- Residual finding: Gemini 3.1 Flash-Lite passes both the registered
  prompt-family behavior suite and a small external-validity stress suite.
- Allowed claim: black-box behavioral diagnostic result for the tested Gemini
  model and stress cases, not an interpretability or production-reliability
  claim.

## Interpretation

This completes the public-benchmark bridge. The benchmark can now be run as a
one-command black-box evaluator, emits JSONL rows and scored summaries, and has
a real cheap API-model positive result. The result does not add hidden-state
evidence, but it shows the behavior surface is not limited to local open-model
weights or one prompt wording.
