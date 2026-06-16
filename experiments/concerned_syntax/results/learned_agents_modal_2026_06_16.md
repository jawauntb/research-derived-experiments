# Learned Concerned-Syntax Agents

Date: 2026-06-16

Question: can learned agents infer causal constituency from intervention observations without direct hidden-parse access?

Manifest: 5 seeds, 3000 train trials per seed, 1200 test trials per seed, 90 SGD epochs.

## Gate Summary

| Agent | Parse high | Action | Subtree | High probe | Low probe | Probe cost | Regret | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| learned_concerned_syntax | 1.000 | 1.000 | 0.797 | 1.000 | 0.202 | 0.024 | 0.003 | PASS |
| planner_no_tree | 0.492 | 0.875 | 0.494 | 1.000 | 0.000 | 0.020 | 0.051 | fail |
| restless_tree | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.040 | 0.000 | fail |
| shortcut_reward | 0.494 | 0.880 | 0.495 | 0.000 | 0.000 | 0.000 | 0.054 | fail |

## Interpretation

The accepted agent must learn both sides of the Phase 2A fork: a tree-bearing parse interpreter and a concern-gated intervention policy. The guarded learner also uses a capped low-concern calibration channel, kept below the anti-restless threshold, so syntax maintenance does not collapse exactly at the subtree gate. Shortcut reward can learn action tendencies without parse. Restless tree inquiry can recover parse while failing no-restless-inquiry. Planner-without-tree can probe at the right times but cannot reliably bind the observation to a candidate constituent.

Raw JSON remains local under `artifacts/concerned_syntax/`.
