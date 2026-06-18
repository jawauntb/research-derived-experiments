# Concerned Rich Program Language

Date: 2026-06-17

Question: can a pixel-level concerned-syntax agent choose among `observe_pair`, `move_anchor`, `ablate_pair`, and composed two-step programs while preserving low-concern discipline?

Manifest: 5 seeds, 3000 train trials per seed, 1200 test trials per seed, 90 SGD epochs, 67 programs across 4 families, 48x48 RGB images.

## Gate Summary

| Agent | Parse high | Action | Subtree | Objects | High prog | Low prog | Family high | Target high | Useful high | Rich high | Regret | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| concerned_program_composer | 1.000 | 1.000 | 0.794 | 1.000 | 1.000 | 0.162 | 1.000 | 1.000 | 1.000 | 1.000 | 0.004 | PASS |
| family_without_target | 0.541 | 0.890 | 0.534 | 1.000 | 1.000 | 0.162 | 1.000 | 0.080 | 0.080 | 1.000 | 0.057 | fail |
| random_rich_program | 0.503 | 0.881 | 0.507 | 1.000 | 1.000 | 1.000 | 0.249 | 0.139 | 0.021 | 0.749 | 0.061 | fail |
| rich_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | fail |
| surface_rich_shortcut | 0.503 | 0.879 | 0.507 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.061 | fail |
| target_without_family | 0.503 | 0.881 | 0.633 | 1.000 | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 0.000 | 0.061 | fail |

## Interpretation

The v2 gate makes program-family choice part of intervention invention. High-concern role families require different useful program families: composed move+observe for shield/poison, move-anchor for repair/core, and ablation for food/trap. The accepted agent must learn when to act, what target matters, and which program family exposes the hidden binding.

This is still a provided program grammar, not open-ended motor apparatus discovery. It is stronger than v1 because `observe_pair` alone is no longer the universal useful intervention.

Raw JSON remains local under `artifacts/concerned_syntax/`.
