# Learned Executable Modules Against 2A-v2 Transfer

Date: 2026-06-18

Question: can executable module bodies consume the held-out `2A-v2-pixels-rich_programs` transfer contract rather than only mapping symbolic motifs to in-distribution controls?

Manifest: 5 seeds, 3000 train trials per held-out slice/seed, 1200 test trials per held-out slice/seed, 90 epochs.

## Body Gate Summary

| Body | Agent | Transfer | Modules | Family | Target | Useful | Rich | Low prog | Cost | Missing | Gate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| family_router_body | `role_equivariant_family_only` | 0.000 | 0.571 | 1.000 | 0.196 | 0.196 | 1.000 | 0.000 | 9 | rich_program_composer, target_binder, world_model | fail |
| learned_composer_body | `learned_rich_program_composer` | 0.000 | 0.143 | 0.714 | 0.829 | 0.714 | 0.894 | 0.161 | 13 | concern_gate, formal_guard, program_family_router, rich_program_composer, target_binder, world_model | fail |
| target_binder_body | `role_equivariant_target_only` | 0.000 | 0.429 | 0.143 | 1.000 | 0.143 | 0.143 | 0.714 | 8 | concern_gate, formal_guard, program_family_router, rich_program_composer | fail |
| transfer_repaired_executable_body | `role_equivariant_rich_world_model` | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 16 | none | PASS |
| ungated_rich_body | `role_equivariant_rich_without_concern` | 0.000 | 0.714 | 1.000 | 1.000 | 1.000 | 1.000 | 0.714 | 13 | concern_gate, formal_guard | fail |

## Interpretation

The accepted body is not allowed to pass by target selection, family routing, or rich composition alone. It must expose all required executable modules and inherit the transfer gate from the repaired 2A-v2 world-model agent.

This is still a compact executable-module validation, not full neural architecture search. The role-slot decoder is explicit; replacing it with learned neural role semantics remains the next Phase 3-facing boundary.

Raw JSON remains local under `artifacts/viable_computational_bodies/`.
