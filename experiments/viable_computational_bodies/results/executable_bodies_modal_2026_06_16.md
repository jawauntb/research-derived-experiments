# Executable Body Validation on Concerned Syntax

Date: 2026-06-16

Question: do executable body variants validate the symbolic Phase 2B motif grammar on the Arc 2A learned-agent gate?

Manifest: 5 seeds, 3000 train trials per seed, 1200 test trials per seed, 90 SGD epochs.

## Gate Summary

| Body | Parse high | Action | High probe | Low probe | Formal | Anti-cheat | Gate |
|---|---:|---:|---:|---:|---:|---:|---|
| guarded_syntax_body | 1.000 | 1.000 | 1.000 | 0.202 | 1.000 | 0.950 | PASS |
| planner_without_tree_body | 0.492 | 0.875 | 1.000 | 0.000 | 0.000 | 0.700 | fail |
| restless_tree_body | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.550 | fail |
| shortcut_reward_body | 0.494 | 0.880 | 0.000 | 0.000 | 1.000 | 0.400 | fail |

## Interpretation

This is not a full NAS run. It is the first executable validation that the symbolic body grammar points at real mechanisms: a reward shortcut is not enough, a planner without tree features is not enough, and a tree parser without formal concern gating becomes restless. The guarded syntax body is the only one that combines tree binding, intervention planning, and capped calibration under the learned Arc 2A and body-side anti-cheat gates.

Raw JSON remains local under `artifacts/concerned_syntax/learned_agents_modal_sweep.json`.
