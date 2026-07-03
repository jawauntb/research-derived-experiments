# Prompt JSON Prompt-Family Causal Patch Preregistration

## Claim Target

This experiment tests whether the fixed-prefix causal-patch result is specific
to one prompt wording. The prior causal-patch run showed that patching a donor
hidden state into a critical-slot-flipped prompt can shift the next-token JSON
`value` readout toward the donor value. The new question is whether that result
survives multiple frozen prompt families.

## Frozen Model Set

The default confirmatory set is:

- `Qwen/Qwen2.5-0.5B-Instruct`
- `Qwen/Qwen2.5-1.5B-Instruct`
- `HuggingFaceTB/SmolLM2-1.7B-Instruct`

All default runs use Modal `L4` workers with a shared Hugging Face cache volume.
The runner maps one model per worker, capped at three concurrent containers.

## Frozen Prompt Families

- `standard`: the original long-horizon moved-bottleneck prompt.
- `compact`: a terser task/records/target wording that preserves the explicit
  requested-slot/read-slot contract.
- `ledger`: an audit-checklist wording that preserves the same memory records
  but changes the framing around distractors and the requested slot.

Each family preserves the same slot phrases, values, critical slot, and partial
assistant JSON value prefix.

## Frozen Task

For each model, prompt family, critical slot, seed, and episode:

1. Sample the long-horizon moved-bottleneck memory records.
2. Render a base prompt and a corrupted prompt where only the critical slot's
   value is flipped.
3. Append the partial assistant prefix
   `{"tool":"read_slot","slot":"<critical slot phrase>","value":`.
4. Patch one donor hidden state from the base prompt/prefix into the corrupted
   prompt/prefix.
5. Measure the donor-value minus corrupted-value next-token logit margin.

The primary row metric is:

`patch_effect = patched_margin - corrupted_margin`

## Frozen Patch Sites

Default token positions:

- `prompt_final`
- `value_prefix_final`

Default layer aliases:

- `late`
- `final`

The all-family robustness gate is evaluated over the default grid.

## Positive Gate

A patch group is positive under the existing causal-patch gate only when:

- clean prompts prefer the donor value on average: `clean_margin > 0`;
- corrupted prompts prefer the corrupted value on average:
  `corrupted_margin < 0`;
- the bootstrap 95% confidence interval lower bound for `patch_effect` is
  greater than `0`;
- mean `patch_direction_success` is greater than `0.5`.

The prompt-family run is positive only if every present `(prompt family, model)`
pair is causally ready and has at least one passing default patch group.

## Strong Negative Gate

The run is a controlled strong negative only if every present
`(prompt family, model)` pair is causally ready, but at least one pair lacks a
passing default patch group.

This is the useful negative: the value-token readout exists across prompt
families, but the causal-patch effect fails to robustly survive prompt wording.

## Inconclusive Gate

The run is inconclusive if any prompt-family/model pair is not causally ready,
if no patch rows are produced, or if model/runtime failure prevents the default
grid from completing.

## Calibration and Confirmatory Split

Small smoke runs may validate Modal wiring, prompt-family rendering, hook
compatibility, token-id extraction, and row schema. Smoke runs may reduce model
count, prompt-family count, seeds, slots, positions, layers, or episodes. They
may not change thresholds after confirmatory results are visible.

The confirmatory run should use held-out base seed `20261000` unless the smoke
run already consumed it accidentally; in that case, choose a new base seed and
record the change before dispatch.

## Allowed Claim

A positive result supports a prompt-robustness claim for this compact prompt
family set: the value-prefix causal-patch effect survives three frozen prompt
wordings across the default open-model set. It does not prove robustness to all
natural-language prompts, API models, multi-token tool-call mediation,
production reliability, human cognition, or consciousness.
