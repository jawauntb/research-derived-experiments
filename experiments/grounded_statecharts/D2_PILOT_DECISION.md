# D2 Pilot Decision Freeze — 2026-07-20

**Status:** revise — Constraint Transport escalates to D3 planning under the
harness-enforced name-free contract; Grounded Statecharts remains narrowed;
CHS has a paired-contrast seal bridge (orchestration/output only); HU pending.

**Model:** `openai` / `gpt-4.1-mini`  
**Adapter:** live  
**Held-out tasks:** 12 per family  
**Contracts:** name-free prompts default; `condition_policy.py` enforces
conditions in code; labeled prompts diagnostic-only  
**Artifact paths:** `artifacts/grounded_statecharts/` (not committed)

## Integrity

| Slice | Publishable | Provider failures |
|---|---|---|
| Labeled D2 (1 repeat, diagnostic) | yes | 0 |
| Labeled D2 (3 repeats, variance only) | 432/432 | 0 |
| Weak-prompt pre-harness ablation | 16/16 | 0 |
| Harness-v2 name-free ablation | 16/16 | 0 |
| Harness-v2 held-out D2 (1 repeat, 144 eps) | 144/144 | 0 |

## Directional results (task-clustered)

| Contrast | Labeled prompt | Weak (pre-harness) | Harness-v2 ablation | Harness-v2 held-out D2 |
|---|---|---|---|---|
| artifact false_completion: G3 − G0 | −0.167 | 0.0 | 0.0 | **−0.083** (CI −0.25..0.0) |
| constraint joint_success: external − envelope_only | +1.000 | 0.0 | +1.000 | **+1.000** (CI 1.0..1.0) |

Surprising held-out read: under name-free prompts, `envelope_only` joint_success
is **0/12 tasks** and `envelope_external_guards` is **12/12** after harness
enforcement — a perfect task-level separation with nested bootstrap CI pinned
at +1.0. Artifact false-completion shows only a small G3 edge (−0.083) with
no raw task-success loss (G3−G0 = 0.0).

## Decisions (authoritative)

1. **Constraint Transport:** escalate to D3 planning. The labeled-only effect was
   a prompt artifact under the old contract; under harness-enforced name-free
   prompts the joint-success δ returns to +1.0. Claim boundary: external guards
   recover joint success after widenings — **not** model-side constraint learning.
2. **Grounded Statecharts:** remain narrowed. No false-completion delta under
   name-free + harness repair in the ablation (model rarely false-completes).
3. **CHS:** paired-contrast seals from public rows are allowed under
   `artifacts/.../chs_sealed_live/` for orchestration/output only. Heuristic
   harvest stays unsealed triage. Full six-surface CHS1 remains open.
4. **HU:** still do not escalate beyond stronger fixture banks / live pilots.
5. **Smoke rows:** remain discarded.

## Kill criteria

- Pre-harness weak-prompt CT δ = 0.0 killed the **old labeled-prompt** escalation path.
- Harness-v2 name-free CT δ = +1.0 with ≥4 tasks **passes** the redesigned gate.
- GS still fails its improvement gate (δ = 0.0).

## Public dataset and CHS seal status

- Public sanitized dataset: `results/d2_pilot_public/` (144 rows, checksums,
  claim boundary).
- Paired-contrast seals: `artifacts/.../chs_sealed_live/` (12 orchestration
  seals from CT contrasts; no six-surface CHS1 claim).

## Next best tests

1. ~~Complete held-out harness-v2 D2 matrix and publish sanitized public dataset.~~
2. ~~Seal paired-contrast CHS labels from that matrix.~~
3. Freeze and execute D3 CT confirmatory spend per `D3_SAMPLE_SIZE_PLAN.md`
   (5 nested repeats; labeled prompts banned).
4. Expand CHS seals beyond orchestration/output with injected surface coverage.
5. Replace HU replicated fixture replays with independently generated corpora
   before any live HU claim.

## 3-repeat labeled variance slice

Path: `artifacts/grounded_statecharts/d2_pilot_r3/` (432/432 publishable).

Variance characterization under the **old labeled** prompt contract only.
Escalation authority is the harness-v2 name-free ablation, not this slice.

## D3 CT confirmatory (harness-v2 name-free)

Path: `artifacts/grounded_statecharts/d3_ct_confirmatory/` (120/120 publishable;
5 nested repeats; CT cells only).  
Public copy: `results/d3_ct_confirmatory_public/`.

| Contrast | Point estimate | Bootstrap CI |
|---|---|---|
| joint_success: external − envelope_only | **+1.000** | **[1.0, 1.0]** |

Confirmatory result matches the held-out D2 planning slice under the same
harness-enforced name-free contract. Claim remains: external guards recover
joint success after widenings — not model-side constraint learning.
