# Modal Smoke: Prompt JSON Hidden-Localization Sweep

Run date: 2026-07-03

Dry-run budget check: https://modal.com/apps/generalintelligencecompany/main/ap-NJycvksq9uBEx4r97www8O

Successful smoke run: https://modal.com/apps/generalintelligencecompany/main/ap-EgkE6nttSJ7GMq2GyObEZ5

Smoke artifact: `artifacts/long_horizon_bottleneck/prompt_json_hidden_localization_smoke.json`

Preregistration: `papers/long_horizon_bottleneck/prompt_json_hidden_localization_preregistration.md`

## Configuration

- Model: `Qwen/Qwen2.5-0.5B-Instruct`
- GPU: Modal `L4`
- Remote model jobs: 1
- Max containers: 3
- Logical behavior cells: 4
- Hidden sites per bottleneck cell: 1
- Conditions: `prompt_json_format_control`, `prompt_json_visible_control`, `prompt_json_short_horizon_control`, `prompt_json_bottleneck`
- Critical slots: `0`
- Seeds: `0`
- Episodes per cell: 2
- Hidden metric episodes per bottleneck cell: 1
- Hidden positions: `prompt_final`
- Hidden layers: `final`
- Base seed: `20260849`
- Conservative timeout-based budget cap: `$2.16`
- User budget supplied to runner: `$5.00`

## Outcome

The smoke run verifies the runner end to end on Modal: package mounting, model
loading, prompt generation, repair/no-op behavior scoring, hidden-state
extraction, summary gating, and artifact writing all completed.

This is not a confirmatory replication because it uses one model, one slot, one
seed, one hidden position, and one layer. Its terminal summary is still useful as
a wiring check:

- Controls pass: yes.
- Behavioral prompt-level moved bottleneck passes: yes.
- Hidden localization pass: no.
- Smoke outcome: `strong_negative`.

Hidden smoke site:

| Site | Memory specificity z | Memory rank percentile | Gate |
| --- | ---: | ---: | --- |
| `Qwen/Qwen2.5-0.5B-Instruct/prompt_final/final` | -0.066 | 0.500 | fail |

## Calibration Log

Two smoke attempts found and fixed runner issues before the successful smoke:

- https://modal.com/apps/generalintelligencecompany/main/ap-VKhBOsWM4Kk6wTPz82MMTu failed because Modal mounted only the runner file, so remote workers could not import the local `experiments` package. The fix adds `add_local_python_source("experiments")` to the Modal image.
- https://modal.com/apps/generalintelligencecompany/main/ap-BzUveI76hcoSUXkN6cFk32 failed after model load because the fallback layer-count expression evaluated `len(model.model)` even when `config.num_hidden_layers` existed. The fix resolves the layer count explicitly.

## Confirmatory Command

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
    experiments/long_horizon_bottleneck/modal_prompt_json_hidden_localization_sweep.py \
    --models Qwen/Qwen2.5-0.5B-Instruct,Qwen/Qwen2.5-1.5B-Instruct,HuggingFaceTB/SmolLM2-1.7B-Instruct \
    --seeds 4 \
    --episodes-per-cell 8 \
    --hidden-metric-episodes 2 \
    --critical-slots 0,1,2,3 \
    --hidden-positions prompt_final,generated_first,generated_final \
    --hidden-layers early,mid,late,final \
    --budget-usd 25 \
    --base-seed 20260850 \
    --out artifacts/long_horizon_bottleneck/prompt_json_hidden_localization_l4.json
```

The dry-run budget check for this default confirmatory command reports 3 Modal
`L4` model jobs, 192 behavior cells, 12 hidden sites per bottleneck cell, and a
conservative timeout-based cost of `$6.47`, below the `$25` run budget and far
below the project ceiling.
