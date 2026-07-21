# D2 Pilot Decision Freeze — 2026-07-20

**Status:** revise — Constraint Transport may resume under the harness-enforced
contract after name-free re-ablation; keep Grounded Statecharts narrowed;
CHS/HU still pending.

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

1. ~~Redesign live prompts so condition identity is harness-enforced, not
   instruction-named.~~ Implemented in `condition_policy.py` with name-free
   default prompts; re-run weak-prompt ablation under harness v2 before any
   CT/GS escalation.
2. Finish the 3-repeat labeled matrix only as a variance characterization, not
   as confirmatory evidence.
3. Independently seal CHS candidates from live failure harvest before CHS1.

## Harness-enforced contract (v2)

As of the harness-enforced redesign:

- Default live prompts omit condition names (`build_live_prompt` == weak prompt).
- `GROUNDED_HARNESS_LABELED_PROMPT=1` is diagnostic-only.
- Scoring uses post-policy evidence: G3 repair can clear false completion;
  external envelope enforcement can clear capability widenings.
- Escalation still requires name-free joint_success δ ≥ 0.15 (CT) or a
  preregistered false-completion improvement (GS) under this contract.

## Harness-v2 name-free re-ablation (2026-07-20)

Path: `artifacts/grounded_statecharts/weak_prompt_ablation_harness_v2/`  
(16/16 rows; 0 failures; `gpt-4.1-mini`)

| Contrast | Point estimate | Gate |
|---|---|---|
| constraint joint_success: external − envelope_only | **+1.000** | ≥ 0.15 with ≥4 tasks → **pass** |
| artifact false_completion: G3 − G0 | **0.0** | no GS improvement |

Mechanism read (bounded):

- CT: under the same name-free prompt, `envelope_only` stays at joint_success 0
  while `envelope_external_guards` reaches 1 after harness capability narrowing.
  This is harness enforcement of constraints, not prompt-label compliance and
  not a claim that the model internalized the envelope.
- GS: both G0 and G3 show false_completion 0 in this slice (model rarely takes
  the false-complete path), so G3 repair has nothing to fix → null.

### Revised decisions after harness-v2 ablation

1. **Constraint Transport:** reopen D3 planning under the harness-enforced,
   name-free contract. Keep the claim boundary: external guards recover joint
   success after attempted widenings; do not claim model-side constraint
   learning from this slice alone.
2. **Grounded Statecharts:** remain narrowed. No false-completion delta under
   name-free + harness repair in this ablation.
3. **CHS / Unlearning:** still do not escalate.

## 3-repeat labeled variance slice

Path: `artifacts/grounded_statecharts/d2_pilot_r3/` (432/432 publishable; 0 provider failures).

| Contrast | Point estimate (3 repeats nested) | Notes |
|---|---|---|
| artifact false_completion: G3 − G0 | −0.167 | Matches 1-repeat planning slice |
| artifact task_success: G3 − G0 | +0.167 | Still no raw-success loss |
| constraint joint_success: external − envelope_only | +1.000 | Still labeled-prompt only; weak-prompt kill stands |

This 3-repeat matrix is variance characterization under the labeled prompt contract.
It does **not** reverse the weak-prompt kill of CT escalation.

