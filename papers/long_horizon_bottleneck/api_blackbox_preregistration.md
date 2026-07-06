# API Black-Box Behavioral Benchmark Preregistration

## Claim Target

This experiment turns the prompt-level moved-bottleneck diagnostic into a
black-box API benchmark. The prior prompt-level hidden-state and causal-patch
results tested internal state in open models. The new question is narrower:
can an API model emit the correct parser-scored JSON action across prompt
families, repair after a failed tool call, and no-op after a successful tool
call?

## Frozen Behavioral Surface

Each row asks for exactly one JSON object:

```json
{"tool":"read_slot","slot":"<exact slot phrase>","value":0}
```

or:

```json
{"tool":"noop"}
```

The scorer uses the same `parse_prompt_json_action` parser as the open-model
prompt-level sweeps. A response may contain prose only if the parser can still
extract one valid JSON object.

## Frozen Conditions

- `prompt_json_format_control`: emit `{"tool":"noop"}`.
- `prompt_json_visible_control`: answer is already visible; emit noop.
- `prompt_json_short_horizon_control`: one nearby record; emit the correct
  read-slot action.
- `prompt_json_bottleneck`: long-horizon records with matched distractors;
  emit the read-slot action for the requested phrase, then respond to both
  failed-tool and successful-tool repair turns.

## Frozen Prompt Families

Registered prompt-family suite:

- `standard`
- `compact`
- `ledger`

External-validity stress suite may additionally include:

- `retrieval`
- `dispatch`

These extra families preserve the same slot phrases, values, and JSON action
schema while changing task framing toward record retrieval and API dispatch.

## Positive Gate

For each `(provider, model, prompt family, stress case)` cell, all registered
conditions must be present and pass:

- schema validity at least 0.95 where applicable;
- action/no-op/slot/value accuracy at least 0.85;
- failed-tool repair emits the same correct read-slot action;
- successful-tool repair emits noop.

The suite is positive only if every complete cell passes both controls and the
long-horizon bottleneck condition.

## Controlled Strong Negative Gate

The suite is a useful strong negative if all controls pass but at least one
long-horizon bottleneck cell fails. That means the API model can follow the
format, visible-answer, and short-horizon contracts, but the delayed moved
bottleneck or repair behavior does not survive.

## Inconclusive Gate

The suite is inconclusive if controls fail, required cells are missing, provider
errors prevent completion, or the parser cannot extract valid JSON often enough
to pass the schema gates.

## Cost and Runtime Guard

Runs must print a request-count dry run or enforce `--max-requests`. Default
temperature is zero. Local deterministic fixture runs are allowed for package
validation, but provider claims require a real API provider run.

## Allowed Claim

A positive result supports a black-box behavioral claim for the tested provider,
model, prompt families, and stress cases. It does not show hidden-state
localization, causal patching, production reliability, autonomous tool use,
human cognition, or consciousness.
