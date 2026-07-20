# D2 Pilot Decision Freeze — 2026-07-20

**Status:** revise — stop product/scientific escalation for Constraint Transport
until weaker-instruction effects return; narrow Grounded Statecharts; keep
CHS/HU pending.

**Model:** `openai` / `gpt-4.1-mini`  
**Adapter:** live  
**Held-out tasks:** 12 per family  
**Repeats in labeled-prompt freeze slice:** 1  
**Weak-prompt ablation:** 4 tasks/family, 1 repeat (`artifacts/.../weak_prompt_ablation/`)  
**Artifact paths:** `artifacts/grounded_statecharts/` (not committed)

## Integrity

Labeled D2 (1 repeat):

- all_publishable: true
- budget_ok: true
- held_out_only: true
- provider_failures: 0

Weak-prompt ablation:

- n_rows: 16
- failures: 0 after parser coercion for path/CSV schema drift

## Directional results (task-clustered)

| Contrast | Labeled prompt | Weak prompt (no condition labels) |
|---|---|---|
| artifact false_completion: G3 − G0 | −0.167 | 0.0 |
| constraint joint_success: external − envelope_only | +1.000 | 0.0 |
| artifact task_success: G3 − G0 | +0.250 | (not primary) |
| wrong_edge joint_success mean | 0.25 | (not re-estimated) |

## Decisions (revised after ablation)

1. **Constraint Transport:** stop escalation. The +1.0 joint-success effect
   collapses to 0 under weaker instructions without condition labels. Treat the
   labeled-prompt D2 effect as a prompt/scaffold artifact, not mechanism
   evidence. Rebuild the prompt contract and re-run before any D3 CT claim.
2. **Grounded Statecharts:** keep narrowed. Labeled G3 helped modestly; weak
   prompt wiped the false-completion delta. Do not ship a product claim.
3. **CHS / Unlearning:** still do not escalate. Heuristic harvest from live rows
   exists under `artifacts/.../chs_from_live/` but labels remain unsealed.
4. **Smoke rows:** remain discarded.

## Kill criteria fired

- Pre-registered D3 gate: escalate CT only if weak-prompt joint_success
  δ ≥ 0.15 with ≥4 tasks. Observed δ = 0.0 → **kill CT escalation**.

## Next best tests

1. Redesign live prompts so condition identity is harness-enforced, not
   instruction-named.
2. Finish the 3-repeat labeled matrix only as a variance characterization, not
   as confirmatory evidence.
3. Independently seal CHS candidates from live failure harvest before CHS1.
