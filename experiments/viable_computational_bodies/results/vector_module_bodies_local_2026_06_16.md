# Executable Module Bodies on Vector Concerned Syntax

Date: 2026-06-16

Question: do executable module bodies still separate from shortcuts when the Arc 2A surface is vector-generated rather than parse-given?

Manifest: 1200 train trials, 500 test trials, seed 20260616, 60 SGD epochs.

## Gate Summary

| Body | Parse high | Action | High probe | Low probe | Formal | Anti-cheat | Modules | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| modular_concerned_body | 1.000 | 1.000 | 1.000 | 0.190 | 1.000 | 0.950 | 0.950 | PASS |
| passive_vector_body | 0.532 | 0.866 | 0.000 | 0.000 | 1.000 | 0.550 | 0.450 | fail |
| restless_vector_body | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.550 | 0.800 | fail |
| surface_reward_body | 0.532 | 0.868 | 0.000 | 0.000 | 1.000 | 0.350 | 0.250 | fail |

## Interpretation

This is the first vector-observation module validation. The passing body combines a surface encoder, concern policy, causal binding head, role-conditioned action head, and calibration guard. Removing the probe policy, removing active binding, or removing the formal low-concern guard each produces a distinct failure mode.

Raw JSON remains local under `artifacts/concerned_syntax/vector_shapes_modal_sweep.json`.
