# Prompt JSON Hidden-Localization Preregistration

## Claim Target

This experiment is a replication and localization follow-up to the prompt JSON
transfer result. The prior confirmatory run showed that a prompted open model
can solve the parser-scored long-horizon moved-bottleneck behavior, including
stochastic repair/no-op turns, but did not verify hidden critical-slot
specificity at the final prompt token.

The new question is narrower: if behavior transfers, is the moved critical slot
localized at any preregistered hidden site across token positions and layers?

## Frozen Model Set

The default confirmatory set is:

- `Qwen/Qwen2.5-0.5B-Instruct`
- `Qwen/Qwen2.5-1.5B-Instruct`
- `HuggingFaceTB/SmolLM2-1.7B-Instruct`

All default runs use Modal `L4` workers with a shared Hugging Face cache volume.
The runner maps one model per worker, capped at three concurrent containers, so
the default is faster than serial execution while remaining far under the
project's `$1000` ceiling.

## Frozen Conditions

Behavior rows preserve the prompt JSON transfer conditions:

- `prompt_json_format_control`: emit a schema-valid `{"tool": "noop"}` action.
- `prompt_json_visible_control`: answer is visible, so emit `noop` and avoid a
  strong hidden moved-slot signal.
- `prompt_json_short_horizon_control`: requested clue is local and explicit, so
  emit a schema-valid `read_slot` call with correct text slot and value.
- `prompt_json_bottleneck`: read long-horizon clue bindings, emit an initial
  `read_slot` action, then repair after failure or no-op after success.

Hidden-localization rows are emitted only for `prompt_json_bottleneck`.

## Frozen Hidden Sites

Token positions:

- `prompt_final`: final prompt token before generation.
- `generated_first`: first generated JSON action token.
- `generated_final`: final generated JSON action token.

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
- At least one preregistered `(model, token position, layer)` hidden site has:
  - bootstrap 95% confidence interval lower bound for `memory_specificity_z`
    greater than `0.0`;
  - mean `memory_rank_percentile` greater than `0.5`.

## Strong Negative Gate

The run is a controlled strong negative only when:

- all behavior controls pass;
- behavioral `prompt_json_bottleneck` passes;
- hidden-localization rows exist for the preregistered grid;
- no preregistered hidden site passes both hidden gates.

This is the useful negative: the model family demonstrates prompt-level behavior
but the registered hidden localization probe does not find a moved-slot site.

## Inconclusive Gate

The run is inconclusive if any behavior control fails, if behavioral
`prompt_json_bottleneck` fails, if no hidden-localization rows are produced, or
if model/runtime failure prevents the default grid from completing.

## Calibration and Confirmatory Split

Small smoke runs may validate Modal wiring, model loading, and row schema. Smoke
runs may reduce model count, seeds, slots, positions, layers, or episodes. They
may not change thresholds after confirmatory results are visible.

The confirmatory run should use held-out base seed `20260850` unless the smoke
run already consumed it accidentally; in that case, choose a new base seed and
record the change before dispatch.

## Allowed Claim

A positive result supports the claim that a prompt-level open model family has at
least one measured hidden site where moved future relevance is reflected in
critical-slot sensitivity. A controlled strong negative supports only the
narrower failure claim: under this prompt, parser, model set, and hidden-site
grid, behavior transfers without verified hidden moved-slot localization.

Neither outcome is evidence about human cognition, biological neural states,
production tool reliability, autonomous API competence, or consciousness.
