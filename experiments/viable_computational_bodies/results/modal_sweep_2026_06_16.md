# Viable Computational Bodies Modal Sweep

Date: 2026-06-16

Manifest: 6 seeds per strategy, 32 generations, population 32.

Remote command:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
  uvx --python 3.12 --from modal modal run \
  experiments/viable_computational_bodies/modal_body_evolution_sweep.py \
  --generations 32 --population 32
```

## Gate Summary

| Strategy | Viable rate | Syntax score | Train return | Formal valid | Anti-cheat | Cost | Best architecture | Gate |
|---|---:|---:|---:|---:|---:|---:|---|---|
| accuracy_only | 0.000 | 0.417 | 1.000 | 0.333 | 0.400 | 8.000 | `flat_encoder+formal_guard+reward_head+shortcut_reward_head+tree_binder+world_model` | fail |
| novelty_only | 0.167 | 0.835 | 0.483 | 1.000 | 0.725 | 11.833 | `flat_encoder+formal_guard+intervention_planner+role_specific_heads+syntax_memory+tree_binder+world_model` | fail |
| viability_guided | 1.000 | 0.830 | 0.495 | 1.000 | 0.950 | 11.000 | `flat_encoder+formal_guard+intervention_planner+role_specific_heads+syntax_memory+tree_binder+world_model` | PASS |

## Interpretation

`viability_guided` is accepted when it repeatedly discovers formal, resource-bounded, syntax-bearing bodies. Reward-only search remains a shortcut control; novelty-only search is informative but does not reliably satisfy the full viability gate.

Accepted strategies: `viability_guided`

Raw JSON remains local under `artifacts/viable_computational_bodies/`.
