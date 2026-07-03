# Prompt JSON Fixed-Action Localization Preregistration

## Claim Target

This experiment is a counterfactual follow-up to the prompt JSON
hidden-localization run. The prior run found strong hidden localization at
generated action-token sites, especially `generated_final`, but those sites can
be partly explained by the generated answer tokens themselves.

The new question is narrower: if behavior transfers, does hidden
critical-slot localization survive when the assistant action tokens are fixed
under the base prompt and every slot-flipped counterfactual prompt?

## Frozen Model Set

The default confirmatory set is:

- `Qwen/Qwen2.5-0.5B-Instruct`
- `Qwen/Qwen2.5-1.5B-Instruct`
- `HuggingFaceTB/SmolLM2-1.7B-Instruct`

All default runs use Modal `L4` workers with a shared Hugging Face cache volume.
The runner maps one model per worker, capped at three concurrent containers.
The conservative timeout-based guard for the default grid is far below the
project's `$1000` ceiling.

## Frozen Conditions

Behavior rows preserve the prompt JSON transfer conditions:

- `prompt_json_format_control`: emit a schema-valid `{"tool": "noop"}` action.
- `prompt_json_visible_control`: answer is visible, so emit `noop`.
- `prompt_json_short_horizon_control`: requested clue is local and explicit, so
  emit a schema-valid `read_slot` call with correct text slot and value.
- `prompt_json_bottleneck`: read long-horizon clue bindings, emit an initial
  `read_slot` action, then repair after failure or no-op after success.

Hidden-localization rows are emitted only for `prompt_json_bottleneck`.

## Fixed-Action Counterfactuals

For each base episode and each slot flip, the runner teacher-forces the same
assistant action text. No generated action token is allowed to differ between
the base prompt and its counterfactual prompts.

Frozen action templates:

- `fixed_noop`: `{"tool":"noop"}`
- `fixed_read`: `{"tool":"read_slot","slot":"<critical slot phrase>","value":0}`

The `fixed_read` slot phrase is determined by the registered critical slot for
that row. Its value is fixed at `0` and does not depend on the episode's true
slot value.

## Frozen Hidden Sites

Default token positions:

- `prompt_final`: final prompt token before generation.
- `fixed_noop_first`: first token of the teacher-forced noop action.
- `fixed_noop_final`: final token of the teacher-forced noop action.
- `fixed_read_first`: first token of the teacher-forced read action.
- `fixed_read_final`: final token of the teacher-forced read action.

Layer aliases:

- `early`: one quarter of transformer blocks.
- `mid`: one half of transformer blocks.
- `late`: three quarters of transformer blocks.
- `final`: final transformer block output.

The runner also accepts explicit integer layer indices for diagnostics, but the
default positive/negative interpretation is based on the alias grid above.

## Positive Gate

The run is positive only when all of the following hold:

- Format, visible-control, and short-horizon controls pass under the existing
  prompt JSON thresholds.
- Behavioral `prompt_json_bottleneck` gates pass: closed-loop final accuracy,
  first parsed slot/value accuracy, failed-repair parsed slot/value accuracy,
  failed-repair schema validity, success no-op accuracy, and success schema
  validity meet the preregistered thresholds.
- At least one preregistered `(model, fixed-action token position, layer)`
  hidden site has:
  - bootstrap 95% confidence interval lower bound for `memory_specificity_z`
    greater than `0.0`;
  - mean `memory_rank_percentile` greater than `0.5`.

## Strong Negative Gate

The run is a controlled strong negative only when:

- all behavior controls pass;
- behavioral `prompt_json_bottleneck` passes;
- hidden-localization rows exist for the fixed-action grid;
- no preregistered fixed-action hidden site passes both hidden gates.

This is the useful negative: the model family demonstrates prompt-level behavior
but the fixed-action probe does not find moved-slot localization after removing
generated-answer-token variation.

## Inconclusive Gate

The run is inconclusive if any behavior control fails, if behavioral
`prompt_json_bottleneck` fails, if no fixed-action hidden rows are produced, or
if model/runtime failure prevents the default grid from completing.

## Calibration and Confirmatory Split

Small smoke runs may validate Modal wiring, model loading, action-span
extraction, and row schema. Smoke runs may reduce model count, seeds, slots,
positions, layers, or episodes. They may not change thresholds after
confirmatory results are visible.

The confirmatory run should use held-out base seed `20260900` unless the smoke
run already consumed it accidentally; in that case, choose a new base seed and
record the change before dispatch.

## Allowed Claim

A positive result supports the claim that at least one measured hidden site
tracks moved critical-slot sensitivity even when generated action tokens are
held fixed across base and counterfactual prompts. This is stronger evidence
than the generated-action localization result, but it is still a prompt/model/
parser-specific mechanistic benchmark.

A controlled strong negative supports the narrower failure claim: under this
prompt, parser, model set, fixed-action templates, and hidden-site grid,
behavior transfers without verified fixed-action hidden localization.

Neither outcome is evidence about human cognition, biological neural states,
production tool reliability, autonomous API competence, or consciousness.
