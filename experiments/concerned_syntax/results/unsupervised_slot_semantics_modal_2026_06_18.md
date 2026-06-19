# Label-Free Slot Semantics Transfer

Date: 2026-06-18

Question: can the `2A-v2-pixels-rich_programs` transfer contract replace supervised visible role-token calibration with label-free connected-component slot induction plus downstream rich-program feedback?

Manifest: 5 seeds, 3000 train trials per held-out slice/seed, 1200 test trials per held-out slice/seed, 1200 label-free induction trials/seed, 90 SGD epochs, role held-outs shield_poison, repair_core, food_trap, parse held-outs repeat_concat, hooked_repeat, alternating_bind, edge_core.

## Induced Semantics

| Clusters | Profiles | Kind | Family | Pair |
|---:|---:|---:|---:|---:|
| 9 | 4 | 1.000 | 1.000 | 1.000 |

## Gate Summary

| Agent | Sem kind | Sem family | Sem pair | Parse high | Action | Family high | Target high | Useful high | Rich high | Low prog | Regret | Slice gate | Transfer gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| learned_rich_program_composer | 0.000 | 0.000 | 0.000 | 0.856 | 0.917 | 0.714 | 0.829 | 0.714 | 0.894 | 0.161 | 0.023 | 0.571 | fail |
| unsupervised_semantic_family_only | 1.000 | 1.000 | 1.000 | 0.674 | 0.892 | 1.000 | 0.214 | 0.214 | 1.000 | 0.000 | 0.047 | 0.143 | fail |
| unsupervised_semantic_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.714 | 0.000 | 0.286 | fail |
| unsupervised_semantic_target_only | 1.000 | 1.000 | 1.000 | 0.639 | 0.880 | 0.143 | 1.000 | 0.143 | 0.143 | 0.714 | 0.051 | 0.000 | fail |
| unsupervised_slot_semantic_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.004 | 1.000 | PASS |

## Held-Out Slices

| Axis | Held-out | Agent | Sem kind | Sem pair | Family high | Target high | Useful high | Low prog | Gate |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| role_kind | food_trap | learned_rich_program_composer | 0.000 | 0.000 | 0.000 | 0.602 | 0.000 | 0.000 | fail |
| role_kind | food_trap | unsupervised_semantic_family_only | 1.000 | 1.000 | 1.000 | 0.085 | 0.085 | 0.000 | fail |
| role_kind | food_trap | unsupervised_semantic_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| role_kind | food_trap | unsupervised_semantic_target_only | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 0.000 | fail |
| role_kind | food_trap | unsupervised_slot_semantic_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| role_kind | repair_core | learned_rich_program_composer | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 0.527 | fail |
| role_kind | repair_core | unsupervised_semantic_family_only | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| role_kind | repair_core | unsupervised_semantic_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | fail |
| role_kind | repair_core | unsupervised_semantic_target_only | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | fail |
| role_kind | repair_core | unsupervised_slot_semantic_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| role_kind | shield_poison | learned_rich_program_composer | 0.000 | 0.000 | 0.000 | 0.199 | 0.000 | 0.000 | fail |
| role_kind | shield_poison | unsupervised_semantic_family_only | 1.000 | 1.000 | 1.000 | 0.088 | 0.088 | 0.000 | fail |
| role_kind | shield_poison | unsupervised_semantic_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| role_kind | shield_poison | unsupervised_semantic_target_only | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 0.000 | fail |
| role_kind | shield_poison | unsupervised_slot_semantic_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| true_parse | alternating_bind | learned_rich_program_composer | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 0.167 | PASS |
| true_parse | alternating_bind | unsupervised_semantic_family_only | 1.000 | 1.000 | 1.000 | 0.085 | 0.085 | 0.000 | fail |
| true_parse | alternating_bind | unsupervised_semantic_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | fail |
| true_parse | alternating_bind | unsupervised_semantic_target_only | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | fail |
| true_parse | alternating_bind | unsupervised_slot_semantic_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| true_parse | edge_core | learned_rich_program_composer | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 0.148 | PASS |
| true_parse | edge_core | unsupervised_semantic_family_only | 1.000 | 1.000 | 1.000 | 0.077 | 0.077 | 0.000 | fail |
| true_parse | edge_core | unsupervised_semantic_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | fail |
| true_parse | edge_core | unsupervised_semantic_target_only | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | fail |
| true_parse | edge_core | unsupervised_slot_semantic_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| true_parse | hooked_repeat | learned_rich_program_composer | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 0.143 | PASS |
| true_parse | hooked_repeat | unsupervised_semantic_family_only | 1.000 | 1.000 | 1.000 | 0.084 | 0.084 | 0.000 | fail |
| true_parse | hooked_repeat | unsupervised_semantic_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | fail |
| true_parse | hooked_repeat | unsupervised_semantic_target_only | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | fail |
| true_parse | hooked_repeat | unsupervised_slot_semantic_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| true_parse | repeat_concat | learned_rich_program_composer | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 0.144 | PASS |
| true_parse | repeat_concat | unsupervised_semantic_family_only | 1.000 | 1.000 | 1.000 | 0.082 | 0.082 | 0.000 | fail |
| true_parse | repeat_concat | unsupervised_semantic_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | fail |
| true_parse | repeat_concat | unsupervised_semantic_target_only | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | fail |
| true_parse | repeat_concat | unsupervised_slot_semantic_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |

## Interpretation

The accepted agent does not train on visible role-token labels. It clusters rendered connected components into appearance slots, identifies the neutral cluster by prevalence, and grounds each active cluster pair by rich-program feedback and action consistency. It then uses the same v2 program family, target, concern, parse-observation, and action contract as the transfer repair gate.

This is not natural-image object discovery, fully unsupervised world learning, fully unsupervised semantic-profile discovery, or open-ended program invention. The semantic profile table is provided and the feedback is synthetic and contract-shaped; the narrow claim is that role-slot semantics no longer require supervised role-token calibration.

Raw JSON remains local under `artifacts/concerned_syntax/`.
