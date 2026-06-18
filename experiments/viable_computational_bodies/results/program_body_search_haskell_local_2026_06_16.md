# Program-Body Search Against 2A-v1

Date: 2026-06-16

Question: can Arc 2B search discover formal, resource-bounded bodies whose motifs express the current Arc 2A intervention-invention contract?

Manifest: 5 seeds, 18 generations, population 18, 1200 train / 500 test 2A trials, 60 epochs. Contract: `2A-v1-pixels-observe_pair`.

## Body Gate Summary

| Strategy | Body gate | Empirical gate | Formal valid | Haskell | Target high | Useful high | Low probe | Return | Cost | Best body | Agent | Formal source | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| reward_only | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 | 3.000 | `reward_head+shortcut_reward_head+vector_surface_encoder` | `surface_program_shortcut` | `haskell` | fail |
| syntax_proxy | 0.000 | 0.400 | 0.000 | 1.000 | 1.000 | 1.000 | 0.655 | 0.930 | 8.400 | `calibration_guard+causal_binding_head+concern_policy+counterfactual_rollout+formal_guard+intervention_planner+reward_head+vector_surface_encoder` | `concerned_program_inventor` | `haskell` | fail |
| viability_guided | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.144 | 0.908 | 10.000 | `calibration_guard+causal_binding_head+concern_policy+flat_encoder+formal_guard+intervention_planner+reward_head+syntax_memory+vector_surface_encoder+world_model` | `concerned_program_inventor` | `haskell` | PASS |

## 2A Role-Transfer Stress

Held-out role kind: `food_trap`. This is a stress test, not yet a required body gate.

| Agent | Parse high | Action | Low probe | Target high | Useful high | Gate |
|---|---:|---:|---:|---:|---:|---|
| concern_without_target | 0.524 | 0.472 | 0.000 | 0.114 | 0.114 | fail |
| concerned_program_inventor | 0.816 | 0.472 | 0.000 | 0.670 | 0.670 | fail |
| random_program_probe | 0.498 | 0.472 | 0.000 | 0.058 | 0.058 | fail |
| surface_program_shortcut | 0.472 | 0.472 | 0.000 | 0.000 | 0.000 | fail |
| target_without_concern | 1.000 | 0.472 | 0.000 | 1.000 | 1.000 | fail |

## Interpretation

This is the first coupled Arc 2A/2B contract. The empirical 2A-v1 gate is frozen as pixels plus an `observe_pair(a,b)` program menu. A searched body passes only if its motif set can express the empirical concerned-program-inventor control and also satisfies formal body constraints. When Cabal is available, candidate motif sets are checked by the Haskell ontology through `ontology-check --motifs`; otherwise the report records the explicit `python_static` fallback.

`reward_only` is a body-side shortcut control. `syntax_proxy` can chase parse/target metrics without the full viability contract. `viability_guided` is accepted only if search reconstructs concern policy, calibration, target selection, program planning, binding, and formal guard motifs together.

Raw JSON remains local under `artifacts/viable_computational_bodies/`.
