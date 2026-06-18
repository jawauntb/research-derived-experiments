# Concerned Rich Program Language

Date: 2026-06-17

Question: can a pixel-level concerned-syntax agent choose among `observe_pair`, `move_anchor`, `ablate_pair`, and composed two-step programs while preserving low-concern discipline?

Manifest: 1200 train trials, 500 test trials, seed 20260617, 60 SGD epochs, 67 programs across 4 families, 48x48 RGB images.

## Gate Summary

| Agent | Parse high | Action | Subtree | Objects | High prog | Low prog | Family high | Target high | Useful high | Rich high | Regret | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| concerned_program_composer | 1.000 | 1.000 | 0.790 | 1.000 | 1.000 | 0.140 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | PASS |
| family_without_target | 0.484 | 0.854 | 0.514 | 1.000 | 1.000 | 0.140 | 1.000 | 0.070 | 0.070 | 1.000 | 0.051 | fail |
| random_rich_program | 0.453 | 0.848 | 0.488 | 1.000 | 1.000 | 1.000 | 0.248 | 0.132 | 0.008 | 0.767 | 0.053 | fail |
| rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | fail |
| surface_rich_shortcut | 0.453 | 0.884 | 0.488 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.053 | fail |
| target_without_family | 0.453 | 0.848 | 0.608 | 1.000 | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 0.000 | 0.053 | fail |

## Interpretation

The v2 gate makes program-family choice part of intervention invention. High-concern role families require different useful program families: composed move+observe for shield/poison, move-anchor for repair/core, and ablation for food/trap. The accepted agent must learn when to act, what target matters, and which program family exposes the hidden binding.

This is still a provided program grammar, not open-ended motor apparatus discovery. It is stronger than v1 because `observe_pair` alone is no longer the universal useful intervention.

Raw JSON remains local under `artifacts/concerned_syntax/`.
