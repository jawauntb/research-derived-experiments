# Prompt JSON Prompt-Family Causal Patch L4 Confirmatory Run

Date: 2026-07-03

Outcome: `positive`

Artifact: `artifacts/long_horizon_bottleneck/prompt_json_prompt_family_causal_patch_l4.json`

Preregistration: `papers/long_horizon_bottleneck/prompt_json_prompt_family_causal_patch_preregistration.md`

Modal full run: `https://modal.com/apps/generalintelligencecompany/main/ap-2OSfTykyaMmYQQGt05MbGb`

Modal successful smoke run: `https://modal.com/apps/generalintelligencecompany/main/ap-zumcfkie6jhxpuQJmEyWMp`

Modal dry run: `https://modal.com/apps/generalintelligencecompany/main/ap-2Llgn1XbinUGUDmZvWms7p`

## Question

The fixed-prefix causal-patch run showed that patching a donor hidden state into
a critical-slot-flipped prompt can shift the next-token JSON `value` readout
toward the donor value. This run asks whether that causal effect survives three
frozen prompt families rather than only one wording.

## Design

- Models: `Qwen/Qwen2.5-0.5B-Instruct`,
  `Qwen/Qwen2.5-1.5B-Instruct`,
  `HuggingFaceTB/SmolLM2-1.7B-Instruct`.
- Prompt families: `standard`, `compact`, `ledger`.
- Modal hardware: `L4`, one model per worker, three-worker cap.
- Conservative timeout budget estimate: `$6.47` against a `$25.00` cap.
- Rows: 4,608 causal-patch rows.
- Seeds: 4.
- Critical slots: 0, 1, 2, 3.
- Episodes per cell: 8.
- Patch positions: `prompt_final`, `value_prefix_final`.
- Patch layers: `late`, `final`.

Calibration smokes were used before the confirmatory run to ensure alternate
prompt families were causally ready. No confirmatory thresholds were changed
after the held-out `20261000` full run.

## Verification Signals

All family/model causal-ready gate pass: yes.

All family/model patch gate pass: yes.

Value-prefix final patch groups pass: yes.

Prompt-final patch groups pass: no.

## Gate Decision

The run is positive:

- all 9 `(prompt family, model)` pairs are causally ready;
- all 9 pairs have at least one passing default patch group;
- `value_prefix_final` late/final groups pass throughout;
- `prompt_final` groups remain negative controls;
- controlled strong negative is false.

## Family/Model Gates

| Prompt family / model | Causal ready | Patch pass |
|---|---:|---:|
| compact / SmolLM2-1.7B | yes | yes |
| compact / Qwen2.5-0.5B | yes | yes |
| compact / Qwen2.5-1.5B | yes | yes |
| ledger / SmolLM2-1.7B | yes | yes |
| ledger / Qwen2.5-0.5B | yes | yes |
| ledger / Qwen2.5-1.5B | yes | yes |
| standard / SmolLM2-1.7B | yes | yes |
| standard / Qwen2.5-0.5B | yes | yes |
| standard / Qwen2.5-1.5B | yes | yes |

## Final-Layer Value-Prefix Effects

| Site | Patch effect | 95% CI | Recovery | Direction |
|---|---:|---:|---:|---:|
| compact / SmolLM2 / `value_prefix_final` / final | 6.439 | [6.129, 6.733] | 0.906 | 1.000 |
| compact / Qwen2.5-0.5B / `value_prefix_final` / final | 6.204 | [5.936, 6.462] | 0.854 | 1.000 |
| compact / Qwen2.5-1.5B / `value_prefix_final` / final | 7.754 | [7.282, 8.234] | 0.937 | 1.000 |
| ledger / SmolLM2 / `value_prefix_final` / final | 5.626 | [5.299, 5.959] | 0.901 | 1.000 |
| ledger / Qwen2.5-0.5B / `value_prefix_final` / final | 4.949 | [4.639, 5.236] | 0.851 | 1.000 |
| ledger / Qwen2.5-1.5B / `value_prefix_final` / final | 6.648 | [6.159, 7.132] | 0.951 | 1.000 |
| standard / SmolLM2 / `value_prefix_final` / final | 7.049 | [6.751, 7.346] | 0.900 | 1.000 |
| standard / Qwen2.5-0.5B / `value_prefix_final` / final | 5.455 | [5.236, 5.648] | 0.836 | 1.000 |
| standard / Qwen2.5-1.5B / `value_prefix_final` / final | 6.830 | [6.280, 7.411] | 0.879 | 0.969 |

## Interpretation

This adds prompt-family robustness to the causal-patch story. The effect is no
longer only a single-prompt phenomenon: every model passes under standard,
compact, and audit-checklist framings. The same useful negative control remains:
prompt-final patch sites do not pass, while value-prefix late/final sites pass.

The robustness claim is still bounded. These are three frozen prompt families,
not arbitrary natural-language prompts or API models. The result supports the
compact claim that the value-prefix causal leverage survives several controlled
wording changes across the default open-model set.

## Reproduction

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
    experiments/long_horizon_bottleneck/modal_prompt_json_causal_patch_sweep.py \
    --models Qwen/Qwen2.5-0.5B-Instruct,Qwen/Qwen2.5-1.5B-Instruct,HuggingFaceTB/SmolLM2-1.7B-Instruct \
    --prompt-families standard,compact,ledger \
    --seeds 4 \
    --episodes-per-cell 8 \
    --critical-slots 0,1,2,3 \
    --patch-positions prompt_final,value_prefix_final \
    --patch-layers late,final \
    --budget-usd 25 \
    --base-seed 20261000 \
    --out artifacts/long_horizon_bottleneck/prompt_json_prompt_family_causal_patch_l4.json
```
