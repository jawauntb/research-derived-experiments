# Learned Slot Semantics Transfer

Date: 2026-06-18

Question: can the `2A-v2-pixels-rich_programs` transfer contract replace its explicit RGB role decoder with a learned supervised slot-semantic decoder while preserving held-out role-kind and true-parse transfer?

Manifest: 5 seeds, 600 train trials per held-out slice/seed, 240 test trials per held-out slice/seed, 600 semantic calibration trials/seed, 30 SGD epochs, role held-outs shield_poison, repair_core, food_trap, parse held-outs repeat_concat, hooked_repeat, alternating_bind, edge_core.

## Semantic Decoder

| Slot roles | Scene roles | Kind | Pair |
|---:|---:|---:|---:|
| 1.000 | 1.000 | 1.000 | 1.000 |

## Gate Summary

| Agent | Sem roles | Sem kind | Sem pair | Parse high | Action | Family high | Target high | Useful high | Rich high | Low prog | Regret | Slice gate | Transfer gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| learned_rich_program_composer | 0.000 | 0.000 | 0.000 | 0.849 | 0.888 | 0.705 | 0.811 | 0.705 | 0.895 | 0.182 | 0.033 | 0.543 | fail |
| learned_semantic_family_only | 1.000 | 1.000 | 1.000 | 0.665 | 0.891 | 1.000 | 0.214 | 0.214 | 1.000 | 0.000 | 0.046 | 0.143 | fail |
| learned_semantic_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.714 | 0.000 | 0.286 | fail |
| learned_semantic_target_only | 1.000 | 1.000 | 1.000 | 0.639 | 0.881 | 0.143 | 1.000 | 0.143 | 0.143 | 0.714 | 0.049 | 0.000 | fail |
| learned_slot_semantic_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.004 | 1.000 | PASS |

## Held-Out Slices

| Axis | Held-out | Agent | Sem kind | Sem pair | Family high | Target high | Useful high | Low prog | Gate |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| role_kind | food_trap | learned_rich_program_composer | 0.000 | 0.000 | 0.000 | 0.482 | 0.000 | 0.000 | fail |
| role_kind | food_trap | learned_semantic_family_only | 1.000 | 1.000 | 1.000 | 0.091 | 0.091 | 0.000 | fail |
| role_kind | food_trap | learned_semantic_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| role_kind | food_trap | learned_semantic_target_only | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 0.000 | fail |
| role_kind | food_trap | learned_slot_semantic_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| role_kind | repair_core | learned_rich_program_composer | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 0.603 | fail |
| role_kind | repair_core | learned_semantic_family_only | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| role_kind | repair_core | learned_semantic_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | fail |
| role_kind | repair_core | learned_semantic_target_only | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | fail |
| role_kind | repair_core | learned_slot_semantic_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| role_kind | shield_poison | learned_rich_program_composer | 0.000 | 0.000 | 0.000 | 0.212 | 0.000 | 0.000 | fail |
| role_kind | shield_poison | learned_semantic_family_only | 1.000 | 1.000 | 1.000 | 0.069 | 0.069 | 0.000 | fail |
| role_kind | shield_poison | learned_semantic_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| role_kind | shield_poison | learned_semantic_target_only | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 0.000 | fail |
| role_kind | shield_poison | learned_slot_semantic_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| true_parse | alternating_bind | learned_rich_program_composer | 0.000 | 0.000 | 0.953 | 0.990 | 0.953 | 0.204 | fail |
| true_parse | alternating_bind | learned_semantic_family_only | 1.000 | 1.000 | 1.000 | 0.084 | 0.084 | 0.000 | fail |
| true_parse | alternating_bind | learned_semantic_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | fail |
| true_parse | alternating_bind | learned_semantic_target_only | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | fail |
| true_parse | alternating_bind | learned_slot_semantic_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| true_parse | edge_core | learned_rich_program_composer | 0.000 | 0.000 | 0.984 | 0.995 | 0.984 | 0.159 | PASS |
| true_parse | edge_core | learned_semantic_family_only | 1.000 | 1.000 | 1.000 | 0.081 | 0.081 | 0.000 | fail |
| true_parse | edge_core | learned_semantic_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | fail |
| true_parse | edge_core | learned_semantic_target_only | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | fail |
| true_parse | edge_core | learned_slot_semantic_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| true_parse | hooked_repeat | learned_rich_program_composer | 0.000 | 0.000 | 0.997 | 0.998 | 0.997 | 0.150 | PASS |
| true_parse | hooked_repeat | learned_semantic_family_only | 1.000 | 1.000 | 1.000 | 0.093 | 0.093 | 0.000 | fail |
| true_parse | hooked_repeat | learned_semantic_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | fail |
| true_parse | hooked_repeat | learned_semantic_target_only | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | fail |
| true_parse | hooked_repeat | learned_slot_semantic_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| true_parse | repeat_concat | learned_rich_program_composer | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 0.156 | PASS |
| true_parse | repeat_concat | learned_semantic_family_only | 1.000 | 1.000 | 1.000 | 0.083 | 0.083 | 0.000 | fail |
| true_parse | repeat_concat | learned_semantic_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | fail |
| true_parse | repeat_concat | learned_semantic_target_only | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | fail |
| true_parse | repeat_concat | learned_slot_semantic_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |

## Interpretation

The accepted agent consumes learned slot semantics rather than nearest-color role decoding: a supervised prototype decoder maps each rendered component into a visible role token, then the world model binds target pair, program family, concern gate, parse observation, and action. Family-only, target-only, and ungated-rich controls keep the old shortcut failures visible under the same transfer slices.

This is not unsupervised object discovery, natural-image vision, or open-ended program invention. The semantic decoder uses supervised visible role-token calibration, and the program grammar remains the provided v2 grammar.

Raw JSON remains local under `artifacts/concerned_syntax/`.
