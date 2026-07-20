# D3 Sample-Size Plan — Grounded Harness

**Date:** 2026-07-20  
**Basis:** held-out live D2 freeze (`gpt-4.1-mini`, 12 tasks/family, 1 repeat)  
**Status:** paused — D2 weak-prompt ablation killed CT escalation (δ = 0).
Do not execute confirmatory spend until the prompt contract is redesigned.

## Targets

1. **Constraint Transport confirmatory (primary):** joint_success for
   `envelope_external_guards` vs `envelope_only` and vs prose/direct baseline.
2. **Grounded Statecharts supportive:** false_completion for `statechart_g3` vs
   `statechart_g0`, with a frozen ≤10pp raw-success loss kill gate.

## Observed planning inputs (D2, 1 repeat)

- Constraint joint_success effect ≈ +1.0 task-mean (likely prompt-inflated).
- Artifact false_completion effect ≈ −0.167 task-mean.
- Use conservative planning effects after a weaker-instruction ablation:
  - constraint: plan for δ = 0.25 absolute joint-success
  - statechart: plan for δ = 0.10 absolute false-completion

## Design

- Keep 12 held-out tasks/family (frozen bank).
- Use **5 nested repeats** for confirmatory (up from 1 planning repeat).
- Bootstrap unit remains **task**, repeats nested under tasks.
- Add two OOD probes (not in primary multiplicity):
  1. held-out paraphrase wording (same semantics)
  2. deeper delegation depth (+1) for constraint family
- Add weaker-instruction ablation (no condition name in prompt) as a
  pre-registered sensitivity analysis.

## Approximate power

For paired task-level means with 12 tasks:

- Detecting δ = 0.25 at α = 0.05 (two-sided) with SD ≈ 0.30 needs roughly
  12–16 tasks; current N=12 is borderline → keep 12 tasks and rely on 5 repeats
  to stabilize task means, or add 4 more held-out tasks before D3 freeze.
- Detecting δ = 0.10 for false_completion is underpowered at N=12 unless
  variance is lower than D2; treat statechart as secondary and report intervals.

## Budget ceiling

- Max live spend for confirmatory slice: $75 USD.
- Same `DEFAULT_PILOT_BUDGET` per episode.
- Planned episodes upper bound: 2 families × 16 tasks × 6 conditions × 5 repeats
  = 960 (if expanded); with frozen 12 tasks: 720.

## Escalation rule

Execute D3 only after:

1. weaker-instruction ablation still shows constraint δ ≥ 0.15, and
2. no-op / stochastic replay characterization is logged for the declared model.
