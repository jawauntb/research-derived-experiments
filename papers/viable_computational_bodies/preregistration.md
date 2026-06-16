# Paper 2B Pre-Registration

**Title (working):** Viability-Guided Evolution of Syntax-Bearing Computational Bodies

**Frozen:** 2026-06-16, before large Modal sweeps.

## Question

What computational bodies make concerned syntax learnable?

Arc 1 found that probe-policy improvements no longer closed a
role-specific mediated-identifiability gap under shared heads and null-only
intervention. Arc 2B tests the architecture side of that ceiling. The claim is
not that generic neural architecture search is enough. The claim is that
architecture search must be gated by viability, formal admissibility, and the
Arc 2A concerned-syntax tests.

## Search Space

Architectures are typed motif sets:

- `flat_encoder`
- `reward_head`
- `shortcut_reward_head`
- `tree_binder`
- `syntax_memory`
- `world_model`
- `intervention_planner`
- `role_specific_heads`
- `counterfactual_rollout`
- `formal_guard`
- `self_repair`

## Static Rules

| Rule | Rationale |
|---|---|
| `syntax_memory` requires `tree_binder` | memory of syntax needs bound constituents |
| `intervention_planner` requires `world_model` | plans need predicted consequences |
| `role_specific_heads` require `tree_binder` | role heads must attach to constituents |
| `counterfactual_rollout` requires `world_model` and `intervention_planner` | counterfactuals need a model and intervention policy |
| `self_repair` requires `formal_guard` | self-modification requires admissibility checks |
| `shortcut_reward_head` without `formal_guard` is rejected | reward shortcuts are an anti-cheat risk |
| resource cost must stay <= 12 | viability includes bounded body cost |

## Strategies

| Strategy | Expected failure or success |
|---|---|
| `accuracy_only` | should over-select shortcut reward heads |
| `novelty_only` | may find interesting bodies but should not reliably pass formal viability |
| `viability_guided` | should find syntax-bearing bodies that pass the full gate |

## Gates

A final architecture passes only if:

| Gate | Criterion |
|---|---|
| G1 formal validity | no static violations |
| G2 resource viability | cost <= 12 |
| G3 parse congruity | score >= 0.85 |
| G4 subtree facilitation | score >= 0.85 |
| G5 intervention invention | score >= 0.55 |
| G6 self/world split | score >= 0.75 |
| G7 anti-cheat | score >= 0.70 |
| G8 formal guard present | `formal_guard` is part of the body |

The strategy-level pilot gate requires viable final bodies in at least 75% of
seeds and mean concerned-syntax score >= 0.80.

## Interpretation Matrix

| Result | Interpretation |
|---|---|
| viability-guided passes and accuracy-only fails | architecture search needs formal/viability gates, not reward alone |
| novelty-only passes too | novelty descriptors are too aligned with viability, or search space is too easy |
| accuracy-only passes | shortcut controls are insufficient |
| all fail | target body grammar is underpowered or gates are too strict |

## What This Does Not Claim

This preregistration does not claim that the system discovers real neural
architectures yet. It defines a typed architecture-search acceptance surface
that will later be connected to Modal-backed learned agents and Arc 2A tasks.

