# Learned Object Slots Discovered Profiles Transfer

Date: 2026-06-22

Question: can learned foreground object slots replace algorithmic connected components while preserving discovered semantic profiles and the held-out `2A-v2-pixels-rich_programs` transfer gate?

Manifest: 5 seeds, 3000 train trials per held-out slice/seed, 1200 test trials per held-out slice/seed, 1200 profile-induction trials/seed, 1200 extractor calibration images/seed, 90 SGD epochs, 45 extractor epochs, role held-outs shield_poison, repair_core, food_trap, parse held-outs repeat_concat, hooked_repeat, alternating_bind, edge_core.

## Learned Object Slots

| Count | Slot recovery | Scene recovery | Center error |
|---:|---:|---:|---:|
| 1.000 | 1.000 | 1.000 | 0.019 |

## Induced Semantics

| Clusters | Profiles | Cluster purity | Family | Pair | Action template |
|---:|---:|---:|---:|---:|---:|
| 9 | 4 | 1.000 | 1.000 | 1.000 | 1.000 |

## Gate Summary

| Agent | Transfer | Purity | Sem family | Sem pair | Action template | Family high | Target high | Useful high | Rich high | Low prog | Regret |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| learned_object_slot_discovered_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.004 |
| learned_object_slot_family_only | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.214 | 0.214 | 1.000 | 0.000 | 0.047 |
| learned_object_slot_rich_without_concern | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.714 | 0.000 |
| learned_object_slot_target_only | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.143 | 1.000 | 0.143 | 0.143 | 0.714 | 0.052 |
| learned_rich_program_composer | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.714 | 0.762 | 0.714 | 0.844 | 0.188 | 0.016 |

## Held-Out Slices

| Axis | Held-out | Agent | Slot recovery | Purity | Sem pair | Target high | Useful high | Low prog | Gate |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| role_kind | food_trap | learned_object_slot_discovered_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| role_kind | food_trap | learned_object_slot_family_only | 1.000 | 1.000 | 1.000 | 0.085 | 0.085 | 0.000 | fail |
| role_kind | food_trap | learned_object_slot_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| role_kind | food_trap | learned_object_slot_target_only | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | fail |
| role_kind | food_trap | learned_rich_program_composer | 1.000 | 0.000 | 0.000 | 0.180 | 0.000 | 0.000 | fail |
| role_kind | repair_core | learned_object_slot_discovered_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| role_kind | repair_core | learned_object_slot_family_only | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| role_kind | repair_core | learned_object_slot_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | fail |
| role_kind | repair_core | learned_object_slot_target_only | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | fail |
| role_kind | repair_core | learned_rich_program_composer | 1.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.720 | fail |
| role_kind | shield_poison | learned_object_slot_discovered_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| role_kind | shield_poison | learned_object_slot_family_only | 1.000 | 1.000 | 1.000 | 0.087 | 0.087 | 0.000 | fail |
| role_kind | shield_poison | learned_object_slot_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| role_kind | shield_poison | learned_object_slot_target_only | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | fail |
| role_kind | shield_poison | learned_rich_program_composer | 1.000 | 0.000 | 0.000 | 0.156 | 0.000 | 0.000 | fail |
| true_parse | alternating_bind | learned_object_slot_discovered_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| true_parse | alternating_bind | learned_object_slot_family_only | 1.000 | 1.000 | 1.000 | 0.091 | 0.091 | 0.000 | fail |
| true_parse | alternating_bind | learned_object_slot_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | fail |
| true_parse | alternating_bind | learned_object_slot_target_only | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 1.000 | fail |
| true_parse | alternating_bind | learned_rich_program_composer | 1.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.160 | PASS |
| true_parse | edge_core | learned_object_slot_discovered_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| true_parse | edge_core | learned_object_slot_family_only | 1.000 | 1.000 | 1.000 | 0.077 | 0.077 | 0.000 | fail |
| true_parse | edge_core | learned_object_slot_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | fail |
| true_parse | edge_core | learned_object_slot_target_only | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 1.000 | fail |
| true_parse | edge_core | learned_rich_program_composer | 1.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.149 | PASS |
| true_parse | hooked_repeat | learned_object_slot_discovered_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| true_parse | hooked_repeat | learned_object_slot_family_only | 1.000 | 1.000 | 1.000 | 0.081 | 0.081 | 0.000 | fail |
| true_parse | hooked_repeat | learned_object_slot_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | fail |
| true_parse | hooked_repeat | learned_object_slot_target_only | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 1.000 | fail |
| true_parse | hooked_repeat | learned_rich_program_composer | 1.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.146 | PASS |
| true_parse | repeat_concat | learned_object_slot_discovered_world_model | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| true_parse | repeat_concat | learned_object_slot_family_only | 1.000 | 1.000 | 1.000 | 0.081 | 0.081 | 0.000 | fail |
| true_parse | repeat_concat | learned_object_slot_rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | fail |
| true_parse | repeat_concat | learned_object_slot_target_only | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 1.000 | fail |
| true_parse | repeat_concat | learned_rich_program_composer | 1.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.142 | PASS |

## Interpretation

The accepted path does not run the connected-component extractor. It trains a foreground pixel model, uses fixed slot-local center search to produce six object slots, induces semantic profiles from those learned slots, and then runs the same held-out transfer verifier as the discovered-profile result.

This is not natural-image object discovery or a full slot-attention model. The renderer, six-slot layout, and contract-shaped intervention feedback remain scaffolds. The bounded claim is that discovered semantic profiles no longer depend on algorithmic connected-component features in this synthetic 2A-v2 world.

Raw JSON remains local under `artifacts/concerned_syntax/`.
