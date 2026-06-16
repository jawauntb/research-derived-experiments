# Program-Body Search Against 2A-v1

Date: 2026-06-16

Question: can Arc 2B search discover formal, resource-bounded bodies whose motifs express the current Arc 2A intervention-invention contract?

Manifest: 5 seeds, 24 generations, population 24, 3000 train / 1200 test 2A trials, 90 epochs. Contract: `2A-v1-pixels-observe_pair`.

## Body Gate Summary

| Strategy | Body gate | Empirical gate | Formal valid | Target high | Useful high | Low probe | Return | Cost | Best body | Agent | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| reward_only | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 4.000 | `reward_head+shortcut_reward_head+vector_surface_encoder` | `surface_program_shortcut` | fail |
| syntax_proxy | 0.000 | 0.200 | 0.400 | 1.000 | 1.000 | 0.830 | 0.944 | 11.600 | `calibration_guard+causal_binding_head+concern_policy+counterfactual_rollout+intervention_planner+reward_head+vector_surface_encoder+world_model` | `concerned_program_inventor` | fail |
| viability_guided | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.156 | 0.930 | 12.000 | `calibration_guard+causal_binding_head+concern_policy+formal_guard+intervention_planner+reward_head+vector_surface_encoder+world_model` | `concerned_program_inventor` | PASS |

## Interpretation

This is the first coupled Arc 2A/2B contract. The empirical 2A-v1 gate is frozen as pixels plus an `observe_pair(a,b)` program menu. A searched body passes only if its motif set can express the empirical concerned-program-inventor control and also satisfies static body constraints.

`reward_only` is a body-side shortcut control. `syntax_proxy` can chase parse/target metrics without the full viability contract. `viability_guided` is accepted only if search reconstructs concern policy, calibration, target selection, program planning, binding, and formal guard motifs together.

Raw JSON remains local under `artifacts/viable_computational_bodies/`.
