# Label-Free Slot Semantics Transfer

Date: 2026-06-18

Question: can the `2A-v2-pixels-rich_programs` transfer contract replace supervised visible role-token calibration with label-free connected-component slot induction plus downstream rich-program feedback?

Manifest: 90 train trials per held-out slice, 40 test trials per held-out slice, 500 label-free induction trials, seed 20260618, 10 SGD epochs, role held-outs shield_poison, repair_core, food_trap, parse held-outs repeat_concat, hooked_repeat, alternating_bind, edge_core.

## Induced Semantics

| Clusters | Profiles | Kind | Family | Pair |
|---:|---:|---:|---:|---:|
| 9 | 4 | 1.000 | 1.000 | 1.000 |

## Gate Summary

| Agent | Sem kind | Sem family | Sem pair | Parse high | Action | Family high | Target high | Useful high | Rich high | Low prog | Regret | Slice gate | Transfer gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| learned_rich_program_composer | 0.000 | 0.000 | 0.000 | 0.728 | 0.829 | 0.493 | 0.715 | 0.493 | 0.718 | 0.533 | 0.061 | 0.000 | fail |
| unsupervised_semantic_family_only | 1.000 | 1.000 | 1.000 | 0.684 | 0.896 | 1.000 | 0.221 | 0.221 | 1.000 | 0.000 | 0.042 | 0.143 | fail |
| unsupervised_semantic_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.714 | 0.000 | 0.286 | fail |
| unsupervised_semantic_target_only | 1.000 | 1.000 | 1.000 | 0.644 | 0.882 | 0.143 | 1.000 | 0.143 | 0.143 | 0.714 | 0.051 | 0.000 | fail |
| unsupervised_slot_semantic_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.003 | 1.000 | PASS |

## Held-Out Slices

| Axis | Held-out | Agent | Sem kind | Sem pair | Family high | Target high | Useful high | Low prog | Gate |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| role_kind | shield_poison | learned_rich_program_composer | 0.000 | 0.000 | 0.000 | 0.225 | 0.000 | 0.000 | fail |
| role_kind | shield_poison | unsupervised_semantic_family_only | 1.000 | 1.000 | 1.000 | 0.050 | 0.050 | 0.000 | fail |
| role_kind | shield_poison | unsupervised_semantic_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| role_kind | shield_poison | unsupervised_semantic_target_only | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 0.000 | fail |
| role_kind | shield_poison | unsupervised_slot_semantic_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| role_kind | repair_core | learned_rich_program_composer | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 0.875 | fail |
| role_kind | repair_core | unsupervised_semantic_family_only | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| role_kind | repair_core | unsupervised_semantic_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | fail |
| role_kind | repair_core | unsupervised_semantic_target_only | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | fail |
| role_kind | repair_core | unsupervised_slot_semantic_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| role_kind | food_trap | learned_rich_program_composer | 0.000 | 0.000 | 0.000 | 0.150 | 0.000 | 0.000 | fail |
| role_kind | food_trap | unsupervised_semantic_family_only | 1.000 | 1.000 | 1.000 | 0.175 | 0.175 | 0.000 | fail |
| role_kind | food_trap | unsupervised_semantic_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| role_kind | food_trap | unsupervised_semantic_target_only | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 0.000 | fail |
| role_kind | food_trap | unsupervised_slot_semantic_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| true_parse | repeat_concat | learned_rich_program_composer | 0.000 | 0.000 | 0.833 | 0.944 | 0.833 | 0.500 | fail |
| true_parse | repeat_concat | unsupervised_semantic_family_only | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | fail |
| true_parse | repeat_concat | unsupervised_semantic_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | fail |
| true_parse | repeat_concat | unsupervised_semantic_target_only | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | fail |
| true_parse | repeat_concat | unsupervised_slot_semantic_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| true_parse | hooked_repeat | learned_rich_program_composer | 0.000 | 0.000 | 0.353 | 1.000 | 0.353 | 0.870 | fail |
| true_parse | hooked_repeat | unsupervised_semantic_family_only | 1.000 | 1.000 | 1.000 | 0.118 | 0.118 | 0.000 | fail |
| true_parse | hooked_repeat | unsupervised_semantic_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | fail |
| true_parse | hooked_repeat | unsupervised_semantic_target_only | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | fail |
| true_parse | hooked_repeat | unsupervised_slot_semantic_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| true_parse | alternating_bind | learned_rich_program_composer | 0.000 | 0.000 | 0.762 | 1.000 | 0.762 | 0.947 | fail |
| true_parse | alternating_bind | unsupervised_semantic_family_only | 1.000 | 1.000 | 1.000 | 0.143 | 0.143 | 0.000 | fail |
| true_parse | alternating_bind | unsupervised_semantic_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | fail |
| true_parse | alternating_bind | unsupervised_semantic_target_only | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | fail |
| true_parse | alternating_bind | unsupervised_slot_semantic_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| true_parse | edge_core | learned_rich_program_composer | 0.000 | 0.000 | 0.500 | 0.688 | 0.500 | 0.542 | fail |
| true_parse | edge_core | unsupervised_semantic_family_only | 1.000 | 1.000 | 1.000 | 0.062 | 0.062 | 0.000 | fail |
| true_parse | edge_core | unsupervised_semantic_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | fail |
| true_parse | edge_core | unsupervised_semantic_target_only | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | fail |
| true_parse | edge_core | unsupervised_slot_semantic_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |

## Interpretation

The accepted agent does not train on visible role-token labels. It clusters rendered connected components into appearance slots, identifies the neutral cluster by prevalence, and grounds each active cluster pair by rich-program feedback and action consistency. It then uses the same v2 program family, target, concern, parse-observation, and action contract as the transfer repair gate.

This is not natural-image object discovery, fully unsupervised world learning, fully unsupervised semantic-profile discovery, or open-ended program invention. The semantic profile table is provided and the feedback is synthetic and contract-shaped; the narrow claim is that role-slot semantics no longer require supervised role-token calibration.

Raw JSON remains local under `artifacts/concerned_syntax/`.
