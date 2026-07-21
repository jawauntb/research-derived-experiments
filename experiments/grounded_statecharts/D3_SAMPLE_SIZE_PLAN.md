# D3 Sample-Size Plan — Grounded Harness

**Date:** 2026-07-20 (revised)  
**Basis:** harness-v2 name-free re-ablation (`weak_prompt_ablation_harness_v2`,
`gpt-4.1-mini`, 4 tasks/family) plus held-out harness-v2 D2 matrix  
**Status:** CT confirmatory slice completed under the harness-enforced name-free
contract (120/120 publishable; δ=+1.0; CI [1.0,1.0]). Grounded Statecharts remains
secondary / narrowed (false_completion δ ≈ −0.083 on held-out D2).

## Targets

1. **Constraint Transport confirmatory (primary):** joint_success for
   `envelope_external_guards` vs `envelope_only` (and optionally vs
   prose/direct baseline as a secondary cell).
2. **Grounded Statecharts supportive only:** false_completion for
   `statechart_g3` vs `statechart_g0`, with a frozen ≤10pp raw-success loss
   kill gate. Do not escalate GS on the current null.

## Observed planning inputs

- Harness-v2 name-free ablation CT joint_success effect = **+1.0** (4 tasks).
- Labeled-prompt D2 effects are variance-only / diagnostic and must not gate
  escalation.
- GS false_completion effect under harness-v2 name-free ablation = **0.0**.
- Planning effects for confirmatory power:
  - constraint: plan for δ = 0.25 absolute joint-success (conservative vs +1.0)
  - statechart: do not power for confirmatory; report intervals only

## Design

- Keep 12 held-out tasks/family (frozen bank).
- Use **5 nested repeats** for confirmatory CT (up from 1 planning repeat).
- Bootstrap unit remains **task**, repeats nested under tasks.
- **Prompt contract frozen:** name-free default; labeled prompts
  (`GROUNDED_HARNESS_LABELED_PROMPT=1`) banned for gates.
- **Mechanism contract frozen:** `condition_policy.py` harness enforcement
  (external capability narrowing; G3 repair).
- Add two OOD probes (not in primary multiplicity):
  1. held-out paraphrase wording (same semantics)
  2. deeper delegation depth (+1) for constraint family

## Approximate power

For paired task-level means with 12 tasks:

- Detecting δ = 0.25 at α = 0.05 (two-sided) with SD ≈ 0.30 needs roughly
  12–16 tasks; current N=12 is borderline → keep 12 tasks and rely on 5 repeats
  to stabilize task means, or add 4 more held-out tasks before D3 freeze.

## Budget ceiling

- Max live spend for confirmatory slice: $75 USD.
- Same `DEFAULT_PILOT_BUDGET` per episode.
- Planned episodes upper bound with frozen 12 tasks × 6 conditions × 5 repeats
  × 2 families = 720 (full matrix). CT-primary slice may drop non-informative
  GS cells if preregistered before spend.

## Escalation rule

Execute D3 CT only after:

1. name-free / harness-v2 joint_success δ ≥ 0.15 with task_count ≥ 4
   (**already met** in `weak_prompt_ablation_harness_v2`), and
2. held-out harness-v2 D2 matrix integrity passes (all publishable; 0 provider
   failures), and
3. no-op / stochastic replay characterization is logged for the declared model.

## Claim boundary

- Allowed: external guards recover joint success after capability widenings
  under a name-free prompt (harness enforcement).
- Not allowed from this plan alone: model-side constraint learning, GS product
  readiness, CHS1, HU1–HU7.

## Kill criteria

- Confirmatory name-free CT δ collapses below the practical threshold.
- Effect vanishes when external enforcement is removed in the 2×2 (typed
  envelope alone without external guards).
- Integrity / replay / budget gates fail.
- Spend exceeds $75 without a pre-registered gate pass.
- Any gate uses labeled prompts.
