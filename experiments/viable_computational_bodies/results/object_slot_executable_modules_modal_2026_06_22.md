# Object-Slot Executable Modules Against Discovered 2A-v2 Transfer

Date: 2026-06-22

Question: can Arc 2B search executable module bodies that consume the learned-object-slot plus discovered-profile 2A transfer contract, rather than the older label-free supplied-profile contract?

Manifest: 5 seeds, 18 generations, population 18, 3000 train / 1200 test trials per held-out slice/seed, 1200 profile-induction trials/seed, 1200 extractor calibration images/seed, 90 policy epochs, 45 extractor epochs. Contract: `2A-v2-learned_object_slots-discovered_profiles`.

Required modules: `concern_gate`, `discovered_profile_inducer`, `formal_guard`, `learned_foreground_extractor`, `object_slot_centerer`, `profile_action_template`, `program_family_router`, `rich_program_composer`, `target_binder`, `world_model`.

## Body Search Summary

| Strategy | Body gate | Transfer | Formal | Slot | Scene | Purity | Sem pair | Action template | Modules | Family | Target | Useful | Rich | Low prog | Cost | Best body | Agent | Formal source | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| family_proxy | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.400 | 1.000 | 0.214 | 0.214 | 1.000 | 0.000 | 11.000 | `discovered_profile_inducer+learned_foreground_extractor+object_slot_centerer+program_family_router+reward_head` | `learned_object_slot_family_only` | `python_static` | fail |
| reward_only | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.714 | 0.762 | 0.714 | 0.844 | 0.188 | 6.000 | `component_slot_encoder+learned_composer_head+reward_head+surface_shortcut_head` | `learned_rich_program_composer` | `python_static` | fail |
| target_proxy | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.500 | 0.143 | 1.000 | 0.143 | 0.143 | 0.714 | 13.000 | `discovered_profile_inducer+learned_foreground_extractor+object_slot_centerer+reward_head+target_binder+world_model` | `learned_object_slot_target_only` | `python_static` | fail |
| ungated_rich_proxy | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.800 | 1.000 | 1.000 | 1.000 | 1.000 | 0.714 | 18.000 | `discovered_profile_inducer+learned_foreground_extractor+object_slot_centerer+profile_action_template+program_family_router+reward_head+rich_program_composer+target_binder+world_model` | `learned_object_slot_rich_without_concern` | `python_static` | fail |
| viability_guided | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 21.000 | `concern_gate+discovered_profile_inducer+formal_guard+learned_foreground_extractor+object_slot_centerer+profile_action_template+profile_memory+program_family_router+reward_head+rich_program_composer+target_binder+world_model` | `learned_object_slot_discovered_world_model` | `python_static` | PASS |

## Interpretation

`viability_guided` is accepted only when search reconstructs the complete learned object-slot executable body: learned foreground extraction, slot-local center search, discovered profile induction, action-template grounding, concern gating, target binding, family routing, rich composition, world-model support, and a formal guard.

`reward_only`, `family_proxy`, `target_proxy`, and `ungated_rich_proxy` remain rejected. They can prefer return shortcuts, family routing, target binding, or rich composition, but they do not simultaneously inherit learned object-slot recovery, discovered-profile transfer, full module coverage, formal validity, and low-concern discipline.

This result upgrades which 2A contract 2B consumes. It is not natural-image object discovery, full slot attention, or trainable neural architecture search. The fixed synthetic renderer, six-slot layout, slot-local center search, bounded module grammar, and contract-shaped feedback remain explicit scaffolds.

Raw JSON remains local under `artifacts/viable_computational_bodies/`.
