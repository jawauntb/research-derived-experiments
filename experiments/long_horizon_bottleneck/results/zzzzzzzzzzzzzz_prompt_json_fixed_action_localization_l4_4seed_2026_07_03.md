# Prompt JSON Fixed-Action Localization L4 Confirmatory Run

Date: 2026-07-03

Outcome: `positive`

Artifact: `artifacts/long_horizon_bottleneck/prompt_json_fixed_action_localization_l4.json`

Preregistration: `papers/long_horizon_bottleneck/prompt_json_fixed_action_localization_preregistration.md`

Modal full run: `https://modal.com/apps/generalintelligencecompany/main/ap-caOYmq8AQ6YBLfQQnq9D7f`

Modal smoke run: `https://modal.com/apps/generalintelligencecompany/main/ap-0dvmw8RHmhcw99p7DuRw6I`

## Question

The prior hidden-localization run found strong positive sites at generated JSON
action tokens. This run asks whether that survives a stricter counterfactual:
under the base prompt and every slot-flipped prompt, the assistant action tokens
are teacher-forced to be fixed rather than generated from the prompt.

## Design

- Models: `Qwen/Qwen2.5-0.5B-Instruct`,
  `Qwen/Qwen2.5-1.5B-Instruct`,
  `HuggingFaceTB/SmolLM2-1.7B-Instruct`.
- Modal hardware: `L4`, one model per worker, three-worker cap.
- Conservative timeout budget estimate: `$6.47` against a `$25.00` cap.
- Rows: 1,152 total; 192 behavior rows and 960 hidden-localization rows.
- Seeds: 4.
- Critical slots: 0, 1, 2, 3.
- Hidden positions: `prompt_final`, `fixed_noop_first`,
  `fixed_noop_final`, `fixed_read_first`, `fixed_read_final`.
- Hidden layers: `early`, `mid`, `late`, `final`.
- Fixed action templates:
  - `fixed_noop`: `{"tool":"noop"}`
  - `fixed_read`: `{"tool":"read_slot","slot":"<critical slot phrase>","value":0}`

## Verification Signals

Behavior controls pass: yes.

Behavioral bottleneck gate pass: yes.

Fixed-action localization gate pass: yes.

Strongest fixed noop specificity: z 12.514, CI [8.035, 18.310].

## Gate Decision

The run is positive:

- behavior controls pass;
- behavioral moved-bottleneck passes;
- hidden localization passes;
- controlled strong negative is false.

## Behavior Gates

| Condition / model | Final | Schema | First slot | First value | Pass |
|---|---:|---:|---:|---:|---|
| bottleneck / SmolLM2-1.7B | 1.000 | 1.000 | 1.000 | 1.000 | yes |
| bottleneck / Qwen2.5-0.5B | 0.969 | 0.992 | 0.992 | 0.969 | yes |
| bottleneck / Qwen2.5-1.5B | 0.938 | 1.000 | 1.000 | 0.938 | yes |
| format control / all models | n/a | 1.000 | n/a | n/a | yes |
| short-horizon control / all models | 1.000 | 1.000 | 1.000 | 1.000 | yes |
| visible control / all models | 1.000 | 1.000 | n/a | n/a | yes |

## Passing Hidden Sites

Twenty-four registered hidden sites pass. Strongest representative fixed-action
sites:

| Site | Specificity z | 95% CI | Rank |
|---|---:|---:|---:|
| Qwen2.5-1.5B / `fixed_noop_final` / final | 12.514 | [8.035, 18.310] | 0.984 |
| Qwen2.5-1.5B / `fixed_noop_first` / final | 9.895 | [4.281, 18.286] | 0.953 |
| Qwen2.5-1.5B / `fixed_read_final` / final | 7.520 | [3.957, 11.388] | 0.906 |
| Qwen2.5-0.5B / `fixed_read_final` / final | 6.928 | [4.545, 9.553] | 0.977 |
| SmolLM2-1.7B / `fixed_read_final` / final | 5.493 | [3.084, 8.311] | 0.836 |
| SmolLM2-1.7B / `fixed_noop_final` / final | 3.160 | [1.759, 4.844] | 0.812 |

## Interpretation

This closes the main confound on the previous generated-token localization
positive. The hidden signal is not only a readout of whichever answer tokens the
model generated, because the action tokens are held fixed between the base
prompt and every counterfactual slot flip. The strongest result is especially
useful: `fixed_noop_final` passes in all three model families at final-layer
sites, including a very large effect in `Qwen/Qwen2.5-1.5B-Instruct`.

The result still does not prove a full causal mechanism. It establishes a
stronger measurement claim: in prompt-level open models that pass the
long-horizon moved-bottleneck behavior, moved critical-slot sensitivity is
detectable at fixed-action hidden states after generated answer-token variation
has been removed.

## Reproduction

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
    experiments/long_horizon_bottleneck/modal_prompt_json_hidden_localization_sweep.py \
    --models Qwen/Qwen2.5-0.5B-Instruct,Qwen/Qwen2.5-1.5B-Instruct,HuggingFaceTB/SmolLM2-1.7B-Instruct \
    --seeds 4 \
    --episodes-per-cell 8 \
    --hidden-metric-episodes 2 \
    --critical-slots 0,1,2,3 \
    --hidden-positions prompt_final,fixed_noop_first,fixed_noop_final,fixed_read_first,fixed_read_final \
    --hidden-layers early,mid,late,final \
    --budget-usd 25 \
    --base-seed 20260900 \
    --out artifacts/long_horizon_bottleneck/prompt_json_fixed_action_localization_l4.json
```
