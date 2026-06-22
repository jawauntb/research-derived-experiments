# Searched Executable Modules Against Label-Free 2A-v2 Transfer

Date: 2026-06-22

Question: can Arc 2B search executable module bodies that consume the label-free `2A-v2-pixels-rich_programs` transfer contract, rather than accepting a compact hand-instantiated body?

Manifest: 1 seeds, 6 generations, population 8, 120 train / 50 test trials per held-out slice/seed, 80 label-free induction trials/seed, 12 epochs. Contract: `2A-v2-pixels-rich_programs-label_free_transfer`.

Required modules: `component_slot_encoder`, `concern_gate`, `formal_guard`, `label_free_slot_inducer`, `program_family_router`, `rich_program_composer`, `semantic_profile_grounder`, `target_binder`, `world_model`.

## Body Search Summary

| Strategy | Body gate | Transfer | Formal | Sem kind | Sem pair | Modules | Family | Target | Useful | Rich | Low prog | Cost | Best body | Agent | Formal source | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| family_proxy | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 0.444 | 1.000 | 0.198 | 0.198 | 1.000 | 0.000 | 10.000 | `component_slot_encoder+label_free_slot_inducer+program_family_router+reward_head+semantic_profile_grounder` | `unsupervised_semantic_family_only` | `python_static` | fail |
| reward_only | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.111 | 0.594 | 0.742 | 0.594 | 0.875 | 0.411 | 6.000 | `component_slot_encoder+learned_composer_head+reward_head+surface_shortcut_head` | `learned_rich_program_composer` | `python_static` | fail |
| target_proxy | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 0.556 | 0.143 | 1.000 | 0.143 | 0.143 | 0.714 | 12.000 | `component_slot_encoder+label_free_slot_inducer+reward_head+semantic_profile_grounder+target_binder+world_model` | `unsupervised_semantic_target_only` | `python_static` | fail |
| ungated_rich_proxy | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 0.778 | 1.000 | 1.000 | 1.000 | 1.000 | 0.714 | 18.000 | `action_head+component_slot_encoder+label_free_slot_inducer+profile_memory+program_family_router+reward_head+rich_program_composer+semantic_profile_grounder+target_binder+world_model` | `unsupervised_semantic_rich_without_concern` | `python_static` | fail |
| viability_guided | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 19.000 | `component_slot_encoder+concern_gate+formal_guard+label_free_slot_inducer+profile_memory+program_family_router+reward_head+rich_program_composer+semantic_profile_grounder+target_binder+world_model` | `unsupervised_slot_semantic_world_model` | `python_static` | PASS |

## Interpretation

`viability_guided` is accepted only when search reconstructs the complete label-free executable body: component slots, slot induction, semantic profile grounding, concern gating, target binding, family routing, rich composition, world-model support, and a formal guard.

`reward_only`, `family_proxy`, `target_proxy`, and `ungated_rich_proxy` fail for different reasons. They can prefer return shortcuts, family routing, target binding, or rich composition, but they do not simultaneously inherit the held-out label-free transfer gate, module coverage, and low-concern no-program discipline.

This is searched executable-module discovery over a bounded contract grammar. It is not full neural architecture search, natural-image object discovery, or fully unsupervised semantic profile discovery.

Raw JSON remains local under `artifacts/viable_computational_bodies/`.
