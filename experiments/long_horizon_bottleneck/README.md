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
LLM agents, consciousness, or naturalistic tool use. Passing gates would justify
the next regime: moving from synthetic sequence agents to API/tool-use agents
where future-critical constraints, tools, or commitments move.
