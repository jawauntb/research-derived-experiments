# Concerned Intervention Transfer Gate

Date: 2026-06-16

Question: does the frozen `2A-v1-pixels-observe_pair` contract survive held-out role-kind and hidden true-parse transfer, or is the accepted i.i.d. result still too tied to the training surface?

Manifest: 5 seeds, 3000 train trials per seed, 1200 test trials per seed, 90 SGD epochs, 16 probe programs, 48x48 RGB images.

Transfer axes:

- Held-out role kinds: `shield_poison`, `repair_core`, `food_trap`
- Held-out true parses: `repeat_concat`, `hooked_repeat`, `alternating_bind`, `edge_core`

## I.I.D. Gate Summary

| Agent | Parse high | Action | Subtree | Low probe | Target high | Useful high | Gate |
|---|---:|---:|---:|---:|---:|---:|---|
| concern_without_target | 0.534 | 0.883 | 0.522 | 0.156 | 0.088 | 0.088 | fail |
| concerned_program_inventor | 1.000 | 1.000 | 0.796 | 0.156 | 1.000 | 1.000 | PASS |
| random_program_probe | 0.519 | 0.879 | 0.530 | 1.000 | 0.060 | 0.060 | fail |
| surface_program_shortcut | 0.486 | 0.876 | 0.494 | 0.000 | 0.000 | 0.000 | fail |
| target_without_concern | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | fail |

## `concerned_program_inventor` Transfer Slices

| Axis | Held out | Parse high | Action | Subtree | High probe | Low probe | Target high | Useful high | Gate rate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| role_kind | `food_trap` | 0.829 | 0.492 | 0.829 | 0.657 | 0.000 | 0.657 | 0.657 | 0.000 |
| role_kind | `repair_core` | 0.000 | 0.969 | 0.737 | 0.000 | 0.479 | 0.000 | 0.000 | 0.000 |
| role_kind | `shield_poison` | 0.593 | 0.987 | 0.593 | 0.180 | 0.000 | 0.180 | 0.180 | 0.000 |
| true_parse | `alternating_bind` | 1.000 | 0.932 | 0.726 | 1.000 | 0.167 | 1.000 | 1.000 | 0.400 |
| true_parse | `edge_core` | 1.000 | 1.000 | 0.692 | 1.000 | 0.149 | 1.000 | 1.000 | 0.200 |
| true_parse | `hooked_repeat` | 1.000 | 1.000 | 0.713 | 1.000 | 0.148 | 1.000 | 1.000 | 0.400 |
| true_parse | `repeat_concat` | 1.000 | 1.000 | 0.719 | 1.000 | 0.153 | 1.000 | 1.000 | 0.200 |

## Transfer Verdict

| Agent | I.I.D. gate | Mean slice gate | All slices pass | Weakest slice | Transfer gate |
|---|---:|---:|---|---|---|
| concerned_program_inventor | 1.000 | 0.171 | no | role_kind:`repair_core` | fail |

## Interpretation

This suite keeps the existing i.i.d. intervention-invention gate intact, then asks whether the same learned target and concern policies transfer when a role family or hidden parse family is withheld from training. A failed transfer slice is not treated as a bookkeeping failure; it is the current claim boundary.

Allowed claim: `2A-v1-pixels-observe_pair` remains a frozen minimal i.i.d. intervention-invention contract. Held-out role/parse transfer is now a required next gate, not evidence already carried by the i.i.d. result.

Raw JSON remains local under `artifacts/concerned_syntax/`.
