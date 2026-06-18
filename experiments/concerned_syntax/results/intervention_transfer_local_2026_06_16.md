# Concerned Intervention Transfer Gate

Date: 2026-06-16

Question: does the frozen `2A-v1-pixels-observe_pair` contract survive held-out role-kind and hidden true-parse transfer, or is the accepted i.i.d. result still too tied to the training surface?

Manifest: 650 train trials, 260 test trials, seed 20260616, 45 SGD epochs, 16 probe programs, 48x48 RGB images.

Transfer axes:

- Held-out role kinds: `shield_poison`, `repair_core`, `food_trap`
- Held-out true parses: `repeat_concat`, `hooked_repeat`, `alternating_bind`, `edge_core`

## I.I.D. Gate Summary

| Agent | Parse high | Action | Subtree | Low probe | Target high | Useful high | Gate |
|---|---:|---:|---:|---:|---:|---:|---|
| concern_without_target | 0.538 | 0.862 | 0.519 | 0.141 | 0.114 | 0.114 | fail |
| concerned_program_inventor | 1.000 | 0.981 | 0.785 | 0.141 | 1.000 | 1.000 | PASS |
| random_program_probe | 0.500 | 0.854 | 0.523 | 1.000 | 0.030 | 0.030 | fail |
| surface_program_shortcut | 0.470 | 0.877 | 0.485 | 0.000 | 0.000 | 0.000 | fail |
| target_without_concern | 1.000 | 0.981 | 1.000 | 1.000 | 1.000 | 1.000 | fail |

## `concerned_program_inventor` Transfer Slices

| Axis | Held out | Parse high | Action | Subtree | High probe | Low probe | Target high | Useful high | Gate rate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| role_kind | `food_trap` | 0.896 | 0.465 | 0.896 | 0.754 | 0.000 | 0.754 | 0.754 | 0.000 |
| role_kind | `repair_core` | 0.000 | 0.888 | 0.823 | 0.000 | 0.573 | 0.000 | 0.000 | 0.000 |
| role_kind | `shield_poison` | 0.585 | 0.950 | 0.585 | 0.231 | 0.000 | 0.231 | 0.231 | 0.000 |
| true_parse | `alternating_bind` | 1.000 | 0.938 | 0.804 | 1.000 | 0.185 | 1.000 | 1.000 | 1.000 |
| true_parse | `edge_core` | 1.000 | 1.000 | 0.812 | 1.000 | 0.167 | 1.000 | 1.000 | 1.000 |
| true_parse | `hooked_repeat` | 1.000 | 1.000 | 0.712 | 1.000 | 0.205 | 1.000 | 1.000 | 0.000 |
| true_parse | `repeat_concat` | 1.000 | 1.000 | 0.708 | 1.000 | 0.132 | 1.000 | 1.000 | 0.000 |

## Transfer Verdict

| Agent | I.I.D. gate | Mean slice gate | All slices pass | Weakest slice | Transfer gate |
|---|---:|---:|---|---|---|
| concerned_program_inventor | 1.000 | 0.286 | no | role_kind:`repair_core` | fail |

## Interpretation

This suite keeps the existing i.i.d. intervention-invention gate intact, then asks whether the same learned target and concern policies transfer when a role family or hidden parse family is withheld from training. A failed transfer slice is not treated as a bookkeeping failure; it is the current claim boundary.

Allowed claim: `2A-v1-pixels-observe_pair` remains a frozen minimal i.i.d. intervention-invention contract. Held-out role/parse transfer is now a required next gate, not evidence already carried by the i.i.d. result.

Raw JSON remains local under `artifacts/concerned_syntax/`.
