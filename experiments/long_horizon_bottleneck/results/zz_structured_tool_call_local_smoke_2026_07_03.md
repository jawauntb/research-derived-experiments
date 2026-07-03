# Result: Structured Tool-Call Bottleneck (Local CPU Pre-Registration Smoke)

Run date: 2026-07-03

Status: **local CPU smoke only.** This branch was developed in an environment
without Modal or Doppler credentials, so the confirmatory Modal `L4` sweep has
**not** been executed here. The evidence below is a small CPU smoke that
exercises the exact training/eval/parse/gate mechanism in
`modal_structured_tool_call_sweep.py`; it is not the preregistered L4 sweep and
carries no Modal run URL. The L4 command and budget to reproduce the committed
regime are given at the bottom.

## What This Regime Adds

The recovery sweep supervised separate slot and value heads. This regime
replaces them with a single **structured-action head** over a JSON-like
tool-call vocabulary of size `2*n_slots + 5`:

- `2*n_slots` executable calls, id `= slot*2 + value` → `{"tool": "read_slot", "slot": s, "value": v}`
- one schema-valid no-op → `{"tool": "noop"}`
- four malformed tokens → `{"error": "missing_slot" | "bad_slot" | "bad_value" | "malformed_order"}`

The evaluator parses the emitted token, checks schema validity, and returns
external state **only** when the parse is an executable call whose slot matches
the moved bottleneck. The closed-loop final answer therefore depends on the
model's own parsed structured action, not on a teacher-forced return.

Conditions:

- `structured_direct_bottleneck` — commit a valid call for the moved slot; the
  returned state is gated on the parsed slot matching.
- `structured_repair_bottleneck` — the first attempt is answered by an
  API-style error token that forces a second structured call at a later repair
  position before the final query.
- `structured_visible_control` — emit the no-op and solve from the terminal
  visible bit; early-slot memory specificity should not become strongly
  positive.

## Local CPU Smoke Configuration

- Device: CPU (`torch==2.7.1`, no CUDA)
- Architecture: `transformer`
- Cells: 6 (1 seed × 3 conditions × 2 moved critical slots)
- Sequence length: 48; slot gap 4; first commit position 24
- Train steps: 500; batch size 128; hidden size 48
- Eval batches: 3; metric batches: 2
- Wall clock: ~2m30s for all 6 cells on CPU

This is deliberately smaller and shorter than the preregistered L4 sweep
(`--seeds 4 --train-steps 900 --sequence-length 128 --hidden-size 64`,
4 moved slots). It confirms the mechanism trains and the gates evaluate; it is
not a statement about the full-power run.

## Local CPU Smoke Gate Summary

All three grouped gates passed in the smoke.

| Group | Closed-loop final | Teacher-forced | First token acc | First schema valid | Repair token acc | Repair schema valid | Memory spec z | Tool-value spec z | Gate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| structured_direct_bottleneck/transformer | 1.000 | 1.000 | 1.000 | 1.000 | n/a | n/a | +2.309 | +2.309 | pass |
| structured_repair_bottleneck/transformer | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | +2.309 | +2.309 | pass |
| structured_visible_control/transformer | 1.000 | 1.000 | 1.000 (no-op) | 0.000 | 1.000 (no-op) | 0.000 | < 0.5 (mean) | < 0.5 (mean) | pass |

Notes:

- For the bottleneck conditions, first/repair schema validity is `1.000` because
  the emitted tokens parse as executable calls; the parsed slot and value match
  the moved bottleneck at `1.000`.
- For the visible control the correct action is the no-op, so call-schema
  validity is `0.000` by construction (a no-op is schema-valid but not an
  executable call). The grouped memory specificity mean stays below the `0.5`
  null threshold; individual smoke cells are noisy at 1 seed × 2 slots, which is
  exactly why the L4 sweep uses 4 seeds × 4 slots.

## Regime Audit

- Old regime: recovery sweep supervised discrete slot and value heads and read
  them directly.
- Transition: a single structured-action head emits one token from a JSON-like
  tool-call vocabulary; a parse layer recovers opcode/slot/value and schema
  validity, and only executable calls with a matching slot return external state.
- Transported evidence: moved critical slot, closed-loop scoring, visible-control
  null, L4 cost guard, final memory specificity, and tool-value specificity are
  preserved. New gates add schema validity and parsed slot/value accuracy.
- Rejected alternative: this is still not a natural-language tool benchmark. The
  action set is a fixed discrete vocabulary and the tool semantics are toy.
- Residual finding (smoke-level): the moved bottleneck survives the switch from
  supervised heads to a parsed structured-action interface, including through the
  error/repair loop. Full-power confirmation awaits the L4 sweep.
- Readiness: mechanism is validated locally; the preregistered L4 statistics are
  the deliverable that promotes this from smoke to confirmed.
- Next operation: run the L4 sweep; then move toward multi-argument schemas,
  stochastic tool failures, and natural-language argument surfaces.

## Confirmatory Modal L4 Command (Not Yet Run Here)

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
    uvx --python 3.12 --from modal modal run \
    experiments/long_horizon_bottleneck/modal_structured_tool_call_sweep.py \
    --seeds 4 --train-steps 900 --architectures transformer \
    --conditions structured_direct_bottleneck,structured_repair_bottleneck,structured_visible_control \
    --critical-slots 0,1,2,3 --budget-usd 25 \
    --out artifacts/long_horizon_bottleneck/structured_tool_call_l4.json
```

- Cells: 48 (transformer only, 3 conditions, 4 moved slots, 4 seeds)
- GPU: Modal `L4`, 900s timeout guard, max 32 containers
- Conservative timeout-based budget cap: `$12.95` (well under the `$25` cap and
  far under `$1000`)
- Add `--dry-run-budget` first to print the manifest and budget without
  dispatching.

## Interpretation Boundary

This is a neural-validated synthetic structured tool-call result at smoke scale,
not a production agent, human-behavior, autonomous natural-language tool-use, or
consciousness claim. The structured interface is a fixed discrete vocabulary that
leans toward naturalistic tool schemas but remains synthetic.
