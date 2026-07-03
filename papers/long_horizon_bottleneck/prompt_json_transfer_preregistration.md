# Prompt JSON Transfer Preregistration

## Claim Target

The next regime transition is from trained synthetic heads to a prompted, open-model action surface. The experiment is complete only if it produces one of two terminal outcomes:

- **Positive transfer:** a prompted model emits executable JSON actions that preserve moved-bottleneck control under stochastic tool failure and repair.
- **Controlled strong negative:** parser, format, visible-control, and short-horizon controls pass, but the moved-bottleneck/repair condition fails in a localized way.

A run that fails the format or simple control tasks is not a strong negative. It is an inconclusive prompt-interface failure.

## Frozen Conditions

- `prompt_json_format_control`: the model must emit exactly a schema-valid `{"tool": "noop"}` action.
- `prompt_json_visible_control`: the answer is visible in the prompt, so the model should emit `noop` and not create hidden action specificity.
- `prompt_json_short_horizon_control`: the requested clue is local and explicit, so the model must emit a schema-valid `read_slot` call with the correct text slot and value.
- `prompt_json_bottleneck`: the model sees long-horizon clue bindings, emits an initial `read_slot` action, then receives either a failure repair prompt or a success no-op prompt.

## Positive Gate

The confirmatory run is positive only when all required gates pass:

- JSON/schema validity is at least 0.95 for format and control rows.
- Closed-loop final accuracy in `prompt_json_bottleneck` is at least 0.85.
- First-call parsed slot accuracy is at least 0.85.
- First-call parsed value accuracy is at least 0.85.
- Failed-repair parsed slot accuracy is at least 0.85.
- Failed-repair parsed value accuracy is at least 0.85.
- Success-repair no-op accuracy is at least 0.85.
- Visible-control final/no-op/schema gates pass, with no strong positive memory specificity.
- If hidden states are available, critical-slot sensitivity is positive and critical-slot rank is above chance.

## Strong Negative Gate

The confirmatory run is a controlled strong negative only when all required controls pass and the bottleneck gate fails. The failure mode must be reported using parser-local categories:

- invalid JSON or schema drift;
- wrong text slot;
- wrong value;
- failure to repair after stochastic tool failure;
- failure to emit `noop` after tool success;
- no hidden-state critical-slot sensitivity when hidden states are available.

## Calibration and Confirmatory Split

Prompt wording, parser policy, thresholds, generation settings, and model identity must be frozen before the confirmatory run. A small calibration run may adjust only prompt clarity and decoding settings. The calibration cap is three attempts. The confirmatory run must use held-out seeds and may not change thresholds after results are visible.

## Allowed Claim

A positive result justifies a generated-behavior diagnostic claim for a prompt-level open model. It is not human behavioral evidence, not a proof of consciousness, and not a neural validation claim. A controlled strong negative is useful if it localizes where the synthetic moved-bottleneck regime fails to transfer.
