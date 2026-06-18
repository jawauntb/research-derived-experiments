# Searched Rich Program Policy Gate

Date: 2026-06-18

Question: can a bounded search process discover the useful v2 rich-program policy recipe, instead of receiving the positive `concerned_program_composer` as a named agent?

Manifest: 1200 train trials, 500 test trials, seed 20260618, 60 SGD epochs, 600 recipe-search trials, 540 searched recipes, 67 programs across 4 families.

## Gate Summary

| Strategy | Parse high | Action | Subtree | Objects | High prog | Low prog | Family high | Target high | Useful high | Rich high | Regret | Recipe | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| concerned_rich_program_search | 1.000 | 1.000 | 0.752 | 1.000 | 1.000 | 0.115 | 1.000 | 1.000 | 1.000 | 1.000 | 0.003 | `concern_or_calibration+learned_family+slot_scores+bind_if_useful_program+bound_action` | PASS |
| family_proxy_rich_program_search | 0.541 | 0.884 | 0.494 | 1.000 | 1.000 | 1.000 | 1.000 | 0.101 | 0.101 | 1.000 | 0.039 | `always+learned_family+random_pair+prior_only+shortcut_action` | fail |
| reward_only_rich_program_search | 0.541 | 0.884 | 0.494 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.039 | `never+observe_pair+random_pair+prior_only+shortcut_action` | fail |
| syntax_proxy_rich_program_search | 1.000 | 0.884 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | `always+learned_family+slot_scores+bind_if_useful_program+shortcut_action` | fail |

## Interpretation

The prior v2 result supplied the positive composer as a named agent. This gate searches a recipe grammar over primitive choices: probe rule, program-family selector, object-target selector, binding update, and action rule. The accepted strategy must find the conjunction of concern gating, learned family routing, causal target selection, useful binding, and bound-conditioned action.

`reward_only_rich_program_search` optimizes cheap action and can ignore the hidden binding. `family_proxy_rich_program_search` can recover family routing without the target/binding contract. `syntax_proxy_rich_program_search` can recover syntax while violating the low-concern no-restless-program cap. Only the concerned search objective is allowed to pass.

This remains a finite DSL search over a provided program language, not open-ended motor or tool discovery.

Raw JSON remains local under `artifacts/concerned_syntax/`.
