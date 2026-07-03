# Prompt JSON Fixed-Prefix Causal Patch Preregistration

## Claim Target

This experiment follows the prompt JSON fixed-action localization result. That
run showed that hidden critical-slot localization survives when generated action
tokens are held fixed. The remaining question is whether the measured hidden
state can causally move a behavior-adjacent readout.

The causal-patch question is narrow: if a hidden state from a base prompt is
patched into a critical-slot-flipped prompt immediately before the JSON `value`
token, do the next-token logits move back toward the base prompt's critical
slot value?

## Frozen Model Set

The default confirmatory set is:

- `Qwen/Qwen2.5-0.5B-Instruct`
- `Qwen/Qwen2.5-1.5B-Instruct`
- `HuggingFaceTB/SmolLM2-1.7B-Instruct`

All default runs use Modal `L4` workers with a shared Hugging Face cache volume.
The runner maps one model per worker, capped at three concurrent containers.

## Frozen Task

For each episode:

1. Sample the long-horizon moved-bottleneck memory records.
2. Render a base prompt and a corrupted prompt where only the critical slot's
   value is flipped.
3. Append a partial assistant action prefix ending immediately before the JSON
   value token:
   `{"tool":"read_slot","slot":"<critical slot phrase>","value":`
4. Measure the next-token logit margin between the base prompt's value token
   and the corrupted prompt's value token.
5. Patch one donor hidden state from the base prompt/prefix into the corrupted
   prompt/prefix and remeasure the margin.

The primary row metric is:

`patch_effect = patched_margin - corrupted_margin`

where each margin is `donor_value_logit - corrupted_value_logit`.

## Frozen Patch Sites

Default token positions:

- `prompt_final`: final prompt token before the fixed value prefix.
- `value_prefix_final`: final token of the fixed assistant prefix immediately
  before the JSON value token.

Default layer aliases:

- `late`: three quarters of transformer blocks.
- `final`: final transformer block output.

The runner accepts `early`, `mid`, and explicit integer layer indices for
diagnostics, but the default positive/negative interpretation is based on the
two-position by two-layer grid above.

## Positive Gate

A patch group is positive only when:

- clean prompts prefer the donor value on average: `clean_margin > 0`;
- corrupted prompts prefer the corrupted value on average:
  `corrupted_margin < 0`;
- the bootstrap 95% confidence interval lower bound for `patch_effect` is
  greater than `0`;
- the mean `patch_direction_success` is greater than `0.5`.

The run is positive when at least one preregistered `(model, position, layer)`
group passes all four gates.

## Strong Negative Gate

The run is a controlled strong negative only when:

- at least one group is causally ready, meaning clean and corrupted prompts
  prefer their own values in the expected directions;
- no preregistered patch group passes the positive gate.

This is the useful negative: the model exposes behavior-adjacent value logits
and fixed-action localization, but the registered patch sites do not causally
shift the value-token readout.

## Inconclusive Gate

The run is inconclusive if no group is causally ready, if no patch rows are
produced, or if model/runtime failure prevents the default grid from completing.

## Calibration and Confirmatory Split

Small smoke runs may validate Modal wiring, model loading, hook compatibility,
token-id extraction, and row schema. Smoke runs may reduce model count, seeds,
slots, positions, layers, or episodes. They may not change thresholds after
confirmatory results are visible.

The confirmatory run should use held-out base seed `20260950` unless the smoke
run already consumed it accidentally; in that case, choose a new base seed and
record the change before dispatch.

## Allowed Claim

A positive result supports the claim that at least one measured hidden site can
causally shift a behavior-adjacent JSON value-token readout toward the donor
critical slot value. It does not prove full task mediation, multi-token causal
control, natural-language robustness, production tool reliability, autonomous
API competence, human cognition, or consciousness.

A controlled strong negative says only that this registered patch grid failed
to shift the value-token readout under the specified prompt, model set, and
patch intervention.
