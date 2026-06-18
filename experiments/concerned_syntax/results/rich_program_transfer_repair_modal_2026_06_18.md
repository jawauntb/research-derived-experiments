# Rich Program Transfer Repair

Date: 2026-06-18

Question: can the `2A-v2-pixels-rich_programs` contract survive held-out role-kind and true-parse transfer once target and program-family selection are made role-equivariant?

Manifest: 5 seeds, 3000 train trials per held-out slice/seed, 1200 test trials per held-out slice/seed, 90 SGD epochs, role held-outs shield_poison, repair_core, food_trap, parse held-outs repeat_concat, hooked_repeat, alternating_bind, edge_core.

## Gate Summary

| Agent | Parse high | Action | Subtree | High prog | Low prog | Family high | Target high | Useful high | Rich high | Regret | Slice gate | Transfer gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| learned_rich_program_composer | 0.856 | 0.917 | 0.856 | 0.829 | 0.161 | 0.714 | 0.829 | 0.714 | 0.894 | 0.023 | 0.571 | fail |
| role_equivariant_family_only | 0.664 | 0.888 | 0.664 | 1.000 | 0.000 | 1.000 | 0.196 | 0.196 | 1.000 | 0.047 | 0.143 | fail |
| role_equivariant_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 0.714 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.286 | fail |
| role_equivariant_rich_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.004 | 1.000 | PASS |
| role_equivariant_target_only | 0.639 | 0.880 | 0.639 | 1.000 | 0.714 | 0.143 | 1.000 | 0.143 | 0.143 | 0.051 | 0.000 | fail |

## Held-Out Slices

| Axis | Held-out | Agent | Family high | Target high | Useful high | Low prog | Gate |
|---|---|---|---:|---:|---:|---:|---|
| role_kind | food_trap | learned_rich_program_composer | 0.000 | 0.602 | 0.000 | 0.000 | fail |
| role_kind | food_trap | role_equivariant_family_only | 1.000 | 0.057 | 0.057 | 0.000 | fail |
| role_kind | food_trap | role_equivariant_rich_without_concern | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| role_kind | food_trap | role_equivariant_rich_world_model | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| role_kind | food_trap | role_equivariant_target_only | 0.000 | 1.000 | 0.000 | 0.000 | fail |
| role_kind | repair_core | learned_rich_program_composer | 1.000 | 1.000 | 1.000 | 0.527 | fail |
| role_kind | repair_core | role_equivariant_family_only | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| role_kind | repair_core | role_equivariant_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | fail |
| role_kind | repair_core | role_equivariant_rich_world_model | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| role_kind | repair_core | role_equivariant_target_only | 1.000 | 1.000 | 1.000 | 1.000 | fail |
| role_kind | shield_poison | learned_rich_program_composer | 0.000 | 0.199 | 0.000 | 0.000 | fail |
| role_kind | shield_poison | role_equivariant_family_only | 1.000 | 0.061 | 0.061 | 0.000 | fail |
| role_kind | shield_poison | role_equivariant_rich_without_concern | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| role_kind | shield_poison | role_equivariant_rich_world_model | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| role_kind | shield_poison | role_equivariant_target_only | 0.000 | 1.000 | 0.000 | 0.000 | fail |
| true_parse | alternating_bind | learned_rich_program_composer | 1.000 | 1.000 | 1.000 | 0.167 | PASS |
| true_parse | alternating_bind | role_equivariant_family_only | 1.000 | 0.123 | 0.123 | 0.000 | fail |
| true_parse | alternating_bind | role_equivariant_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | fail |
| true_parse | alternating_bind | role_equivariant_rich_world_model | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| true_parse | alternating_bind | role_equivariant_target_only | 0.000 | 1.000 | 0.000 | 1.000 | fail |
| true_parse | edge_core | learned_rich_program_composer | 1.000 | 1.000 | 1.000 | 0.148 | PASS |
| true_parse | edge_core | role_equivariant_family_only | 1.000 | 0.046 | 0.046 | 0.000 | fail |
| true_parse | edge_core | role_equivariant_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | fail |
| true_parse | edge_core | role_equivariant_rich_world_model | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| true_parse | edge_core | role_equivariant_target_only | 0.000 | 1.000 | 0.000 | 1.000 | fail |
| true_parse | hooked_repeat | learned_rich_program_composer | 1.000 | 1.000 | 1.000 | 0.143 | PASS |
| true_parse | hooked_repeat | role_equivariant_family_only | 1.000 | 0.041 | 0.041 | 0.000 | fail |
| true_parse | hooked_repeat | role_equivariant_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | fail |
| true_parse | hooked_repeat | role_equivariant_rich_world_model | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| true_parse | hooked_repeat | role_equivariant_target_only | 0.000 | 1.000 | 0.000 | 1.000 | fail |
| true_parse | repeat_concat | learned_rich_program_composer | 1.000 | 1.000 | 1.000 | 0.144 | PASS |
| true_parse | repeat_concat | role_equivariant_family_only | 1.000 | 0.041 | 0.041 | 0.000 | fail |
| true_parse | repeat_concat | role_equivariant_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | fail |
| true_parse | repeat_concat | role_equivariant_rich_world_model | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| true_parse | repeat_concat | role_equivariant_target_only | 0.000 | 1.000 | 0.000 | 1.000 | fail |

## Interpretation

The learned rich composer remains the shortcut baseline: it can pass the i.i.d. v2 gate without proving role/parse transfer. The accepted repair decodes role slots, chooses the role-equivariant target, selects the required rich program family, and gates program use by decoded concern. Family-only, target-only, and rich-without-concern controls isolate the failure modes.

This is still an explicit role decoder/world model, not learned neural role semantics or open-ended program invention. It closes the Phase 2 transfer gate for the provided v2 grammar while leaving learned slot semantics as the next claim boundary.

Raw JSON remains local under `artifacts/concerned_syntax/`.
