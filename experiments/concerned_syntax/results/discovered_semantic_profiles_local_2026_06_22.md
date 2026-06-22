# Discovered Semantic Profiles Transfer

Date: 2026-06-22

Question: can the `2A-v2-pixels-rich_programs` transfer contract replace the supplied semantic profile table with profiles induced from intervention/outcome and action-consistency traces?

Manifest: 90 train trials per held-out slice, 40 test trials per held-out slice, 500 profile-induction trials, seed 20260622, 10 SGD epochs, role held-outs shield_poison, repair_core, food_trap, parse held-outs repeat_concat, hooked_repeat, alternating_bind, edge_core.

## Induced Semantics

| Clusters | Profiles | Cluster purity | Family | Pair | Action template |
|---:|---:|---:|---:|---:|---:|
| 9 | 4 | 1.000 | 1.000 | 1.000 | 1.000 |

## Gate Summary

| Agent | Purity | Sem family | Sem pair | Action template | Parse high | Action | Family high | Target high | Useful high | Rich high | Low prog | Regret | Slice gate | Transfer gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| discovered_semantic_family_only | 1.000 | 1.000 | 1.000 | 1.000 | 0.665 | 0.893 | 1.000 | 0.204 | 0.204 | 1.000 | 0.000 | 0.059 | 0.143 | fail |
| discovered_semantic_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.714 | 0.000 | 0.286 | fail |
| discovered_semantic_target_only | 1.000 | 1.000 | 1.000 | 1.000 | 0.625 | 0.879 | 0.143 | 1.000 | 0.143 | 0.143 | 0.714 | 0.064 | 0.000 | fail |
| discovered_semantic_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.005 | 1.000 | PASS |
| learned_rich_program_composer | 0.000 | 0.000 | 0.000 | 0.000 | 0.676 | 0.825 | 0.510 | 0.696 | 0.510 | 0.874 | 0.428 | 0.060 | 0.000 | fail |

## Held-Out Slices

| Axis | Held-out | Agent | Purity | Sem pair | Family high | Target high | Useful high | Low prog | Gate |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| role_kind | shield_poison | discovered_semantic_family_only | 1.000 | 1.000 | 1.000 | 0.075 | 0.075 | 0.000 | fail |
| role_kind | shield_poison | discovered_semantic_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| role_kind | shield_poison | discovered_semantic_target_only | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 0.000 | fail |
| role_kind | shield_poison | discovered_semantic_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| role_kind | shield_poison | learned_rich_program_composer | 0.000 | 0.000 | 0.000 | 0.075 | 0.000 | 0.000 | fail |
| role_kind | repair_core | discovered_semantic_family_only | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| role_kind | repair_core | discovered_semantic_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | fail |
| role_kind | repair_core | discovered_semantic_target_only | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | fail |
| role_kind | repair_core | discovered_semantic_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| role_kind | repair_core | learned_rich_program_composer | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 0.775 | fail |
| role_kind | food_trap | discovered_semantic_family_only | 1.000 | 1.000 | 1.000 | 0.100 | 0.100 | 0.000 | fail |
| role_kind | food_trap | discovered_semantic_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| role_kind | food_trap | discovered_semantic_target_only | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 0.000 | fail |
| role_kind | food_trap | discovered_semantic_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| role_kind | food_trap | learned_rich_program_composer | 0.000 | 0.000 | 0.000 | 0.150 | 0.000 | 0.000 | fail |
| true_parse | repeat_concat | discovered_semantic_family_only | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | fail |
| true_parse | repeat_concat | discovered_semantic_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | fail |
| true_parse | repeat_concat | discovered_semantic_target_only | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | fail |
| true_parse | repeat_concat | discovered_semantic_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| true_parse | repeat_concat | learned_rich_program_composer | 0.000 | 0.000 | 0.458 | 0.750 | 0.458 | 0.250 | fail |
| true_parse | hooked_repeat | discovered_semantic_family_only | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | fail |
| true_parse | hooked_repeat | discovered_semantic_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | fail |
| true_parse | hooked_repeat | discovered_semantic_target_only | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | fail |
| true_parse | hooked_repeat | discovered_semantic_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| true_parse | hooked_repeat | learned_rich_program_composer | 0.000 | 0.000 | 0.682 | 1.000 | 0.682 | 0.667 | fail |
| true_parse | alternating_bind | discovered_semantic_family_only | 1.000 | 1.000 | 1.000 | 0.105 | 0.105 | 0.000 | fail |
| true_parse | alternating_bind | discovered_semantic_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | fail |
| true_parse | alternating_bind | discovered_semantic_target_only | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | fail |
| true_parse | alternating_bind | discovered_semantic_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| true_parse | alternating_bind | learned_rich_program_composer | 0.000 | 0.000 | 0.632 | 1.000 | 0.632 | 0.952 | fail |
| true_parse | edge_core | discovered_semantic_family_only | 1.000 | 1.000 | 1.000 | 0.150 | 0.150 | 0.000 | fail |
| true_parse | edge_core | discovered_semantic_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | fail |
| true_parse | edge_core | discovered_semantic_target_only | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | fail |
| true_parse | edge_core | discovered_semantic_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| true_parse | edge_core | learned_rich_program_composer | 0.000 | 0.000 | 0.800 | 0.900 | 0.800 | 0.350 | fail |

## Interpretation

The accepted agent clusters rendered connected components, identifies active cluster pairs, and fits an anonymous profile for each pair from candidate-family success feedback, bound/unbound utility gaps, and action templates. It does not receive the old semantic kind profile table, kind-to-family mapping, role-pair table, or concern-weight table.

This is semantic-profile induction inside the synthetic connected-component 2A-v2 world. It is not natural-image object discovery, fully open-ended semantics, human or neural validation, or open-ended motor/apparatus invention. The feedback remains synthetic and contract-shaped.

Raw JSON remains local under `artifacts/concerned_syntax/`.
