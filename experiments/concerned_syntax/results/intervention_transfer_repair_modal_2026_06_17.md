# Intervention Transfer Repair

Date: 2026-06-17

Question: can a role-equivariant perceptual/world-model operation repair the held-out role-kind transfer failure in the frozen `2A-v1-pixels-observe_pair` contract?

Manifest: 5 seeds, 3000 train trials per held-out kind/seed, 1200 test trials per held-out kind/seed, 90 SGD epochs, held-out kinds shield_poison, repair_core, food_trap.

## Gate Summary

| Agent | Parse high | Action | Subtree | High probe | Low probe | Target high | Useful high | Regret | Slice gate | Transfer gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| learned_program_inventor | 0.789 | 0.802 | 0.709 | 0.580 | 0.176 | 0.580 | 0.580 | 0.027 | 0.000 | fail |
| role_equivariant_target_only | 1.000 | 1.000 | 1.000 | 1.000 | 0.333 | 1.000 | 1.000 | 0.000 | 0.667 | fail |
| role_equivariant_world_model | 1.000 | 1.000 | 0.860 | 1.000 | 0.000 | 1.000 | 1.000 | 0.004 | 1.000 | PASS |
| world_concern_random_target | 0.754 | 0.879 | 0.614 | 1.000 | 0.000 | 0.390 | 0.390 | 0.052 | 0.333 | fail |

## Interpretation

The learned baseline preserves the original shortcut failure under held-out high-concern role kinds. The repair is not another i.i.d. target learner: it decodes visible role slots, selects the two non-neutral objects as the intervention target, computes whether the candidate parses change viability, and only then uses `observe_pair(a,b)`. Target-only and random-target controls show that both the equivariant target operation and the concern gate are required.

Raw JSON remains local under `artifacts/concerned_syntax/`.
