# Prompt JSON Fixed-Prefix Causal Patch L4 Confirmatory Run

Date: 2026-07-03

Outcome: `positive`

Artifact: `artifacts/long_horizon_bottleneck/prompt_json_causal_patch_l4.json`

Preregistration: `papers/long_horizon_bottleneck/prompt_json_causal_patch_preregistration.md`

Modal full run: `https://modal.com/apps/generalintelligencecompany/main/ap-aeuCBfA3ZuG5pYEXaoUOMd`

Modal smoke run: `https://modal.com/apps/generalintelligencecompany/main/ap-bJ2xNKq6EJAu27YvHxqPrO`

## Question

The fixed-action localization run showed that hidden critical-slot localization
survives when generated action tokens are held fixed. This run asks whether the
localized state can causally shift a behavior-adjacent readout: the next-token
logit margin for the JSON `value` field.

## Design

- Models: `Qwen/Qwen2.5-0.5B-Instruct`,
  `Qwen/Qwen2.5-1.5B-Instruct`,
  `HuggingFaceTB/SmolLM2-1.7B-Instruct`.
- Modal hardware: `L4`, one model per worker, three-worker cap.
- Conservative timeout budget estimate: `$6.47` against a `$25.00` cap.
- Rows: 1,536 causal-patch rows.
- Seeds: 4.
- Critical slots: 0, 1, 2, 3.
- Episodes per cell: 8.
- Patch positions: `prompt_final`, `value_prefix_final`.
- Patch layers: `late`, `final`.
- Readout: next-token logit margin at the partial JSON prefix
  `{"tool":"read_slot","slot":"<critical slot phrase>","value":`.

Margins are donor-value logit minus corrupted-value logit. The primary effect
is `patched_margin - corrupted_margin`.

## Verification Signals

Causal readiness gate pass: yes.

Patch effect gate pass: yes.

Value-prefix final patch groups pass: yes.

Prompt-final patch groups pass: no.

## Gate Decision

The run is positive:

- clean prompts prefer the donor value;
- corrupted prompts prefer the flipped/corrupted value;
- at least one patch group has a positive patch-effect CI lower bound;
- at least one patch group has direction success above chance;
- controlled strong negative is false.

## Group Results

| Site | Clean margin | Corrupt margin | Patch effect | 95% CI | Recovery | Direction | Pass |
|---|---:|---:|---:|---:|---:|---:|---|
| SmolLM2 / `value_prefix_final` / final | 3.987 | -3.846 | 7.053 | [6.738, 7.344] | 0.899 | 1.000 | yes |
| SmolLM2 / `value_prefix_final` / late | 3.987 | -3.846 | 2.371 | [2.202, 2.529] | 0.293 | 1.000 | yes |
| Qwen2.5-0.5B / `value_prefix_final` / final | 3.508 | -3.071 | 5.503 | [5.299, 5.697] | 0.837 | 1.000 | yes |
| Qwen2.5-0.5B / `value_prefix_final` / late | 3.508 | -3.071 | 4.976 | [4.734, 5.204] | 0.750 | 1.000 | yes |
| Qwen2.5-1.5B / `value_prefix_final` / final | 3.916 | -3.659 | 6.916 | [6.375, 7.453] | 0.904 | 0.969 | yes |
| Qwen2.5-1.5B / `value_prefix_final` / late | 3.916 | -3.659 | 4.175 | [3.926, 4.421] | 0.566 | 1.000 | yes |
| SmolLM2 / `prompt_final` / final | 3.987 | -3.846 | 0.000 | [0.000, 0.000] | 0.000 | 0.000 | no |
| Qwen2.5-0.5B / `prompt_final` / final | 3.508 | -3.071 | 0.000 | [0.000, 0.000] | 0.000 | 0.000 | no |
| Qwen2.5-1.5B / `prompt_final` / final | 3.916 | -3.659 | 0.000 | [0.000, 0.000] | 0.000 | 0.000 | no |

## Interpretation

This is the strongest prompt-level mechanism result so far. The prior
fixed-action localization result established that moved-slot sensitivity is
measurable without generated-answer-token variation. This causal-patch result
adds that patching the donor activation into the corrupted prompt can restore
most of the donor value-token logit margin at `value_prefix_final`.

The negative prompt-final patch is also useful. It suggests that, for this
readout, the actionable causal state is not simply the final prompt token. The
causal leverage appears after the fixed assistant value prefix has focused the
model on the exact JSON field being predicted.

This still does not prove full multi-token task mediation or robustness across
prompt families. It does support a narrower mechanistic claim: under the frozen
prompt/model/parser setup, a localized hidden state can causally shift the
behavior-adjacent value-token readout toward the moved critical slot.

## Reproduction

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
    experiments/long_horizon_bottleneck/modal_prompt_json_causal_patch_sweep.py \
    --models Qwen/Qwen2.5-0.5B-Instruct,Qwen/Qwen2.5-1.5B-Instruct,HuggingFaceTB/SmolLM2-1.7B-Instruct \
    --seeds 4 \
    --episodes-per-cell 8 \
    --critical-slots 0,1,2,3 \
    --patch-positions prompt_final,value_prefix_final \
    --patch-layers late,final \
    --budget-usd 25 \
    --base-seed 20260950 \
    --out artifacts/long_horizon_bottleneck/prompt_json_causal_patch_l4.json
```
