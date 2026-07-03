# Long-Horizon Moved Bottleneck

This experiment is the temporal analogue of the moved-location metric result:
instead of moving a spatial priority field, it moves which early sequence slot is
future-critical for a delayed decision.

Each episode contains four equally frequent early clue slots. A bit appears in
each slot, followed by a long delay and a final decision token. In the
`bottleneck` condition, the correct final action is the bit from one registered
critical slot; that critical slot is moved across runs. In the `visible_control`
condition, the final decision is visible at the query token, so the early slots
are matched distractors.

The primary metric is **final memory-state sensitivity**: perturb one slot's
early bit, keep everything else matched, and measure how much the final hidden
state moves. If future control relevance reallocates finite memory geometry, the
sensitivity peak should follow the moved critical slot.

## Cheap Modal Run

The runner defaults to Modal `L4`, which is much cheaper than H100 while still
fast for these small Torch sequence models. It includes a budget guard using
timeout-based worst-case GPU spend.

Fastest cheap confirmatory pass:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
    experiments/long_horizon_bottleneck/modal_moved_bottleneck_sweep.py \
    --seeds 8 --train-steps 700 --architectures transformer \
    --conditions bottleneck,visible_control \
    --critical-slots 0,1,2,3 \
    --budget-usd 25 \
    --out artifacts/long_horizon_bottleneck/transformer_l4_8seed.json
```

This is the recommended first pass because a single transformer cell solved the
bottleneck task at 700 steps, while a same-budget GRU calibration remained at
chance. The broader GRU sweep remains useful as a negative/architecture-control
diagnostic, but it is not the fastest route to a clean initial result.

Horizon stress pass:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
    experiments/long_horizon_bottleneck/modal_moved_bottleneck_sweep.py \
    --seeds 4 --train-steps 700 --architectures transformer \
    --conditions bottleneck,visible_control \
    --critical-slots 0,1,2,3 \
    --sequence-lengths 128,256,384 \
    --budget-usd 50 \
    --out artifacts/long_horizon_bottleneck/horizon_transformer_l4.json
```

The horizon pass reuses the same early clue positions and lengthens only the
post-clue delay. This tests whether the moved-bottleneck signal survives longer
credit-assignment spans rather than only the initial 128-token setting.

Tool-commitment pass:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
    experiments/long_horizon_bottleneck/modal_tool_commitment_sweep.py \
    --seeds 4 --train-steps 700 --architectures transformer \
    --conditions tool_bottleneck,visible_control \
    --critical-slots 0,1,2,3 \
    --budget-usd 25 \
    --out artifacts/long_horizon_bottleneck/closed_loop_tool_commitment_l4.json
```

The tool pass adds a commit token and a tool-return token. In the
`tool_bottleneck` condition, the agent must commit the moved critical slot and
its value before receiving the external return; in `visible_control`, it should
choose the null tool and solve from the terminal visible bit. The runner reports
both teacher-forced final accuracy and closed-loop final accuracy; the closed-loop
score is the gate metric because the model's emitted slot and value determine the
returned external state.

Tool-recovery pass:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
    experiments/long_horizon_bottleneck/modal_tool_recovery_sweep.py \
    --seeds 4 --train-steps 900 --architectures transformer \
    --conditions direct_bottleneck,repair_bottleneck,visible_control \
    --critical-slots 0,1,2,3 \
    --budget-usd 25 \
    --out artifacts/long_horizon_bottleneck/tool_recovery_l4.json
```

The recovery pass adds an API-style missing-return/error token after the first
tool attempt in `repair_bottleneck`. The agent must preserve the moved critical
bit through the error feedback and re-commit the correct slot/value at a later
repair token before the final query.

Structured tool-call pass:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
    experiments/long_horizon_bottleneck/modal_structured_tool_call_sweep.py \
    --seeds 4 --train-steps 900 --architectures transformer \
    --conditions structured_direct_bottleneck,structured_repair_bottleneck,structured_visible_control \
    --critical-slots 0,1,2,3 \
    --budget-usd 25 \
    --out artifacts/long_horizon_bottleneck/structured_tool_call_l4.json
```

The structured pass replaces the supervised slot and value heads with a single
structured-action head over a small JSON-like tool-call vocabulary: `2*n_slots`
executable calls (`{"tool": "read_slot", "slot": s, "value": v}`), one schema-valid
no-op (`{"tool": "noop"}`), and four malformed tokens (`missing_slot`, `bad_slot`,
`bad_value`, `malformed_order`). The evaluator parses the emitted token, checks
schema validity, and returns external state only when the parse is an executable
call whose slot matches the moved bottleneck. In `structured_direct_bottleneck`
the agent commits a valid call for the moved slot; in
`structured_repair_bottleneck` the first attempt is answered by an API-style
error token that forces a second structured call at the repair position; in
`structured_visible_control` the agent should emit the no-op and solve from the
terminal visible bit. Gates add schema-validity and parsed slot/value checks on
top of the closed-loop final accuracy, memory specificity, tool-value
specificity, and visible-control null.

Multifield tool-schema pass:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
    experiments/long_horizon_bottleneck/modal_multifield_tool_schema_sweep.py \
    --seeds 4 --train-steps 900 --architectures transformer \
    --conditions multifield_direct_bottleneck,multifield_repair_bottleneck,multifield_visible_control \
    --critical-slots 0,1,2,3 \
    --budget-usd 25 \
    --out artifacts/long_horizon_bottleneck/multifield_tool_schema_l4.json
```

The multifield pass replaces the fused structured-action token with three
separate fields: opcode, slot argument, and value argument. The parser composes
schema validity across fields, distinguishing executable calls, a schema-valid
no-op, missing or bad slot/value arguments, and bad opcodes. Gates require
closed-loop final accuracy, per-field action accuracy, composed schema validity,
parsed slot/value accuracy for executable calls, memory specificity, tool-value
specificity, and the visible-control no-op null.

Stochastic tool-failure pass:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
    experiments/long_horizon_bottleneck/modal_stochastic_tool_failure_sweep.py \
    --seeds 4 --train-steps 900 --architectures transformer \
    --conditions stochastic_failure_bottleneck,stochastic_visible_control \
    --critical-slots 0,1,2,3 \
    --failure-probability 0.5 \
    --budget-usd 25 \
    --out artifacts/long_horizon_bottleneck/stochastic_tool_failure_l4.json
```

The stochastic pass keeps the multifield schema but samples first-call failures
per episode. On success, the agent should emit a schema-valid repair no-op; on
failure, it must repair by re-emitting the executable call for the moved critical
slot. Gates split those cases so a model cannot pass by always repairing or
always no-oping.

Larger-schema stochastic pass:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
    experiments/long_horizon_bottleneck/modal_stochastic_tool_failure_sweep.py \
    --seeds 4 --train-steps 900 --architectures transformer \
    --conditions stochastic_failure_bottleneck,stochastic_visible_control \
    --n-slots 8 --sequence-length 160 \
    --critical-slots 0,1,2,3,4,5,6,7 \
    --failure-probability 0.5 \
    --budget-usd 25 \
    --out artifacts/long_horizon_bottleneck/stochastic_tool_failure_8slot_l4.json
```

The larger-schema pass doubles the registered clue slots, grows the slot
argument vocabulary to 10, and lengthens the sequence so the first commit still
comes after all clues. It checks whether the stochastic repair/no-op gate
survives a larger argument namespace rather than only the four-slot toy schema.

Alias argument-surface pass:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
    experiments/long_horizon_bottleneck/modal_stochastic_tool_failure_sweep.py \
    --seeds 4 --train-steps 900 --architectures transformer \
    --conditions alias_stochastic_bottleneck,alias_visible_control \
    --critical-slots 0,1,2,3 \
    --aliases-per-slot 3 \
    --failure-probability 0.5 \
    --budget-usd 25 \
    --out artifacts/long_horizon_bottleneck/alias_argument_surface_l4.json
```

The alias pass replaces the compact slot argument with three equivalent aliases
per canonical slot, growing the argument vocabulary to 14. The training loss
accepts any alias in the correct slot's alias set, while the evaluator parses
aliases back to canonical slots before applying the same stochastic repair/no-op
gates. It is a bridge toward natural-language arguments, not free-form language.

Text argument-surface pass:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
    experiments/long_horizon_bottleneck/modal_stochastic_tool_failure_sweep.py \
    --seeds 4 --train-steps 900 --architectures transformer \
    --conditions text_stochastic_bottleneck,text_visible_control \
    --critical-slots 0,1,2,3 \
    --aliases-per-slot 3 \
    --failure-probability 0.5 \
    --budget-usd 25 \
    --out artifacts/long_horizon_bottleneck/text_argument_surface_l4.json
```

The text pass keeps the stochastic repair/no-op environment but renders slot
arguments as parser-facing phrases such as `clue_1`, `second clue`, and
`memory slot 1`. The evaluator parses those phrases back to canonical slots
before applying the same gates. This is still a synthetic classifier surface,
but it attacks the next bottleneck after compact alias IDs: whether the moved
critical variable survives a text-labeled JSON argument namespace.

Generated JSON surface pass:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
    experiments/long_horizon_bottleneck/modal_stochastic_tool_failure_sweep.py \
    --seeds 4 --train-steps 900 --architectures transformer \
    --conditions generated_json_bottleneck,generated_json_visible_control \
    --critical-slots 0,1,2,3 \
    --aliases-per-slot 3 \
    --failure-probability 0.5 \
    --budget-usd 25 \
    --out artifacts/long_horizon_bottleneck/generated_json_surface_l4.json
```

The generated JSON pass replaces the three classifier fields with a
fixed-length emitted token sequence that renders to a JSON-like tool-call
string, such as `{ tool : read_slot , slot : second clue , value : 0 }` or
`{ tool : noop }`. The evaluator parses the emitted sequence back into opcode,
slot phrase, and value before applying the same stochastic repair/no-op gates.
This is still constrained synthetic generation, not an autoregressive LLM
prompt benchmark, but it attacks the next bottleneck after classifier-rendered
text phrases: whether the moved critical variable survives parser-scored
generated action strings.

Smoke:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
    experiments/long_horizon_bottleneck/modal_moved_bottleneck_sweep.py \
    --seeds 1 --train-steps 120 --architectures gru \
    --conditions bottleneck,visible_control \
    --budget-usd 10 \
    --out artifacts/long_horizon_bottleneck/smoke.json
```

Default modest sweep:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
    experiments/long_horizon_bottleneck/modal_moved_bottleneck_sweep.py \
    --seeds 8 --train-steps 700 --budget-usd 100 \
    --out artifacts/long_horizon_bottleneck/moved_bottleneck_sweep.json
```

## Gates

- **G1 behavior:** bottleneck agents solve the delayed decision above 0.90 accuracy.
- **G2 metric transport:** final memory-state sensitivity is specifically higher
  for the moved critical slot.
- **G3 rank:** the critical slot ranks above chance among registered slots.
- **G4 visible-control null:** when the answer is visible at the terminal query,
  early-slot specificity should not become strongly positive.

## Scope Boundary

This is a synthetic long-horizon memory diagnostic, not a claim about production
LLM agents, consciousness, or naturalistic tool use. The structured and
multifield tool-schema passes move the model-visible interface toward
naturalistic tool schemas (parsed calls, schema validity, malformed actions,
argument fields, and repair prompts) but remain fully synthetic: fields are
fixed discrete classifiers, not free-form JSON or natural-language tool use, and
the tool semantics are toy. The stochastic failure pass adds per-episode API
success/failure variation, but the failure process is still synthetic and
environment-sampled. The larger-schema pass raises the argument namespace but
still uses compact discrete fields. The alias pass adds synonym-like argument
equivalence classes, but those aliases are still fixed classifier labels.
Passing gates justify either packaging the synthetic mechanism ladder or moving
to a true text/LLM prompt regime. The generated JSON pass adds emitted
fixed-length parser strings, but those strings are still vocabulary-constrained
and supervised; they are not open-ended decoding from a pretrained model.
