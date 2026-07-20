# D2 Pilot Decision Freeze — 2026-07-20

**Status:** escalate to D3 planning for Constraint Transport joint-success;
narrow Grounded Statecharts false-completion claim; keep CHS/HU pending.

**Model:** `openai` / `gpt-4.1-mini`  
**Adapter:** live  
**Held-out tasks:** 12 per family  
**Repeats in this freeze slice:** 1 (variance estimation; full 3-repeat confirmatory still required for D3)  
**Artifact path:** `artifacts/grounded_statecharts/d2_pilot/` (not committed)

## Integrity

- all_publishable: true
- budget_ok: true
- held_out_only: true
- provider_failures: 0

## Directional results (task-clustered)

| Contrast | Point estimate | Notes |
|---|---|---|
| artifact false_completion: G3 − G0 | −0.167 | Directional improvement; G0 false-completion was already low (0.167) |
| artifact task_success: G3 − G0 | +0.250 | No raw-success loss; G3 higher |
| constraint joint_success: external − envelope_only | +1.000 | Strong directional separation on this prompt/scoring contract |
| wrong_edge joint_success mean | 0.25 | Control still receives some success; do not over-claim uniqueness |

## Decisions

1. **Constraint Transport:** escalate. Typed+external guards dominate envelope-only
   on held-out recursive tasks under this scoring contract. Freeze a D3 sample-size
   plan and add OOD wording/depth probes before confirmatory claims.
2. **Grounded Statecharts:** narrow. G3 reduces false completion without success
   loss, but base false-completion rate is modest on this model/prompt pair.
   Keep G3 as a candidate; enlarge repeats and harden temptation before product
   claims.
3. **CHS / Unlearning:** do not escalate from this slice. Continue sealed-label
   plumbing and wait for authentic failure rows with withheld labels.
4. **Smoke rows:** remain discarded. This freeze uses held-out tasks only.

## Kill / caution flags

- Prompt-scaffolded action JSON may inflate condition compliance; D3 must include
  a weaker-instruction ablation.
- One repeat is insufficient for confirmatory intervals; treat bootstrap CIs here
  as planning inputs only.
- Wrong-edge still shows non-zero joint success; attribution uniqueness is not
  established.
