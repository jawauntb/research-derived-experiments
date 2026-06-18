# Searched Program Policy Gate

Date: 2026-06-17

Question: can a search process discover a concern-gated program policy over the frozen pixel `observe_pair(a,b)` menu, rather than receiving the positive policy as a named agent?

Manifest: 5 seeds, 3000 train trials per seed, 1200 test trials per seed, 90 SGD epochs, 600 recipe-search trials per seed, 108 searched recipes, 16 probe programs.

## Gate Summary

| Strategy | Parse high | Action | Subtree | Objects | High probe | Low probe | Target high | Useful high | Regret | Recipe | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| concerned_program_search | 1.000 | 1.000 | 0.789 | 1.000 | 1.000 | 0.156 | 1.000 | 1.000 | 0.005 | `concern_or_calibration+slot_scores+bind_if_useful_probe+bound_action` | PASS |
| reward_only_program_search | 0.515 | 0.876 | 0.508 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.058 | `never+random_pair+prior_only+bound_action` | fail |
| syntax_proxy_program_search | 1.000 | 0.867 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | `always+slot_scores+bind_if_useful_probe+shortcut_action` | fail |

## Interpretation

The old 2A-v1 gate named the positive policy directly as `concerned_program_inventor`. This gate searches over a small program-policy recipe grammar: probe rule, target selector, binding update, and action rule. The positive strategy only passes when search combines concern gating, target selection, useful binding, and bound-conditioned action.

`reward_only_program_search` is optimized for action under probe cost and can prefer a cheap shortcut. `syntax_proxy_program_search` can recover target/binding metrics while ignoring low-concern discipline. The accepted `concerned_program_search` must keep the no-restless cap while still asking the useful question on high-concern trials.

Allowed claim: searched policy composition over the frozen `observe_pair` menu now recovers the 2A-v1 concern/target/binding contract. This is not yet open-ended motor-program discovery or a rich movement/ablation language.

Raw JSON remains local under `artifacts/concerned_syntax/`.
