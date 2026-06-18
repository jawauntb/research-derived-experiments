# Rich Program-Body Search Against 2A-v2

Date: 2026-06-18

Question: can Arc 2B search discover formal, resource-bounded bodies whose motifs express the `2A-v2-pixels-rich_programs` contract?

Manifest: 5 seeds, 18 generations, population 18, 3000 train / 1200 test 2A trials, 90 epochs. Contract: `2A-v2-pixels-rich_programs`.

## Body Gate Summary

| Strategy | Body gate | Empirical gate | Formal valid | Haskell | Family high | Target high | Useful high | Rich high | Low prog | Return | Cost | Best body | Agent | Formal source | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| reward_only | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 4.000 | `reward_head+shortcut_reward_head+vector_surface_encoder` | `surface_rich_shortcut` | `python_static` | fail |
| syntax_proxy | 0.000 | 0.400 | 0.200 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.670 | 0.948 | 15.800 | `calibration_guard+causal_binding_head+concern_policy+intervention_planner+program_family_head+reward_head+rich_program_composer+role_specific_heads+vector_surface_encoder+world_model` | `concerned_program_composer` | `python_static` | fail |
| viability_guided | 1.000 | 1.000 | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.168 | 0.910 | 16.000 | `calibration_guard+causal_binding_head+concern_policy+formal_guard+intervention_planner+program_family_head+reward_head+rich_program_composer+vector_surface_encoder+world_model` | `concerned_program_composer` | `python_static` | PASS |

## Interpretation

This lifts the coupled 2A/2B bridge from v1 target selection to the richer v2 program-language contract. A searched body now passes only if it can express concern gating, target binding, program-family selection, rich program composition, and formal body admissibility together.

`reward_only` remains a return shortcut. `syntax_proxy` can chase parse/family/target metrics without satisfying the full body contract. `viability_guided` is accepted only when search reconstructs the full morphology required by the v2 empirical gate.

Raw JSON remains local under `artifacts/viable_computational_bodies/`.
