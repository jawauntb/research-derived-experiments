# Learned Slot Semantics Transfer

Date: 2026-06-18

Question: can the `2A-v2-pixels-rich_programs` transfer contract replace its explicit RGB role decoder with a learned supervised slot-semantic decoder while preserving held-out role-kind and true-parse transfer?

Manifest: 5 seeds, 3000 train trials per held-out slice/seed, 1200 test trials per held-out slice/seed, 1200 semantic calibration trials/seed, 90 SGD epochs, role held-outs shield_poison, repair_core, food_trap, parse held-outs repeat_concat, hooked_repeat, alternating_bind, edge_core.

## Semantic Decoder

| Slot roles | Scene roles | Kind | Pair |
|---:|---:|---:|---:|
| 1.000 | 1.000 | 1.000 | 1.000 |

## Gate Summary

| Agent | Sem roles | Sem kind | Sem pair | Parse high | Action | Family high | Target high | Useful high | Rich high | Low prog | Regret | Slice gate | Transfer gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| learned_rich_program_composer | 0.000 | 0.000 | 0.000 | 0.856 | 0.917 | 0.714 | 0.829 | 0.714 | 0.894 | 0.161 | 0.023 | 0.571 | fail |
| learned_semantic_family_only | 1.000 | 1.000 | 1.000 | 0.665 | 0.889 | 1.000 | 0.214 | 0.214 | 1.000 | 0.000 | 0.048 | 0.143 | fail |
| learned_semantic_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.714 | 0.000 | 0.286 | fail |
| learned_semantic_target_only | 1.000 | 1.000 | 1.000 | 0.639 | 0.880 | 0.143 | 1.000 | 0.143 | 0.143 | 0.714 | 0.051 | 0.000 | fail |
| learned_slot_semantic_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.004 | 1.000 | PASS |

## Held-Out Slices

| Axis | Held-out | Agent | Sem kind | Sem pair | Family high | Target high | Useful high | Low prog | Gate |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| role_kind | food_trap | learned_rich_program_composer | 0.000 | 0.000 | 0.000 | 0.602 | 0.000 | 0.000 | fail |
| role_kind | food_trap | learned_semantic_family_only | 1.000 | 1.000 | 1.000 | 0.086 | 0.086 | 0.000 | fail |
| role_kind | food_trap | learned_semantic_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| role_kind | food_trap | learned_semantic_target_only | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 0.000 | fail |
| role_kind | food_trap | learned_slot_semantic_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| role_kind | repair_core | learned_rich_program_composer | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 0.527 | fail |
| role_kind | repair_core | learned_semantic_family_only | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| role_kind | repair_core | learned_semantic_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | fail |
| role_kind | repair_core | learned_semantic_target_only | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | fail |
| role_kind | repair_core | learned_slot_semantic_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| role_kind | shield_poison | learned_rich_program_composer | 0.000 | 0.000 | 0.000 | 0.199 | 0.000 | 0.000 | fail |
| role_kind | shield_poison | learned_semantic_family_only | 1.000 | 1.000 | 1.000 | 0.079 | 0.079 | 0.000 | fail |
| role_kind | shield_poison | learned_semantic_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| role_kind | shield_poison | learned_semantic_target_only | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 0.000 | fail |
| role_kind | shield_poison | learned_slot_semantic_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| true_parse | alternating_bind | learned_rich_program_composer | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 0.167 | PASS |
| true_parse | alternating_bind | learned_semantic_family_only | 1.000 | 1.000 | 1.000 | 0.087 | 0.087 | 0.000 | fail |
| true_parse | alternating_bind | learned_semantic_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | fail |
| true_parse | alternating_bind | learned_semantic_target_only | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | fail |
| true_parse | alternating_bind | learned_slot_semantic_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| true_parse | edge_core | learned_rich_program_composer | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 0.148 | PASS |
| true_parse | edge_core | learned_semantic_family_only | 1.000 | 1.000 | 1.000 | 0.077 | 0.077 | 0.000 | fail |
| true_parse | edge_core | learned_semantic_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | fail |
| true_parse | edge_core | learned_semantic_target_only | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | fail |
| true_parse | edge_core | learned_slot_semantic_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| true_parse | hooked_repeat | learned_rich_program_composer | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 0.143 | PASS |
| true_parse | hooked_repeat | learned_semantic_family_only | 1.000 | 1.000 | 1.000 | 0.082 | 0.082 | 0.000 | fail |
| true_parse | hooked_repeat | learned_semantic_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | fail |
| true_parse | hooked_repeat | learned_semantic_target_only | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | fail |
| true_parse | hooked_repeat | learned_slot_semantic_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| true_parse | repeat_concat | learned_rich_program_composer | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 0.144 | PASS |
| true_parse | repeat_concat | learned_semantic_family_only | 1.000 | 1.000 | 1.000 | 0.088 | 0.088 | 0.000 | fail |
| true_parse | repeat_concat | learned_semantic_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | fail |
| true_parse | repeat_concat | learned_semantic_target_only | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | fail |
| true_parse | repeat_concat | learned_slot_semantic_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |

## Interpretation

The accepted agent consumes learned slot semantics rather than nearest-color role decoding: a supervised prototype decoder maps each rendered component into a visible role token, then the world model binds target pair, program family, concern gate, parse observation, and action. Family-only, target-only, and ungated-rich controls keep the old shortcut failures visible under the same transfer slices.

This is not unsupervised object discovery, natural-image vision, or open-ended program invention. The semantic decoder uses supervised visible role-token calibration, and the program grammar remains the provided v2 grammar.

Raw JSON remains local under `artifacts/concerned_syntax/`.
