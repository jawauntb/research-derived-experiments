# OpenAI Dispatch Robustness Characterization

Date: 2026-07-06

## Outcome

Outcome: `partially_reproduced_localized`.
Rows: 336; planned requests: 720.
Controls pass: yes.
Original dispatch failure reproduced: yes.
Localized cells: 1; unresolved cells: 0.
Original dispatch failure not reproduced cells: 15.
Robustness outcome: `sparse_reproduced_localized`.
Original-failure cells: 1/16 (rate 0.062).
Gate: reproduced original-failure cells: 8slot_gap16 slot 0.

## Diagnostic Matrix

| Stress | Critical slot | Original | Neutral wording | Copy-assisted | Repair-hinted | Diagnosis |
|---|---:|---|---|---|---|---|
| 4slot_gap16 | 0 | pass | pass | pass | pass | none |
| 4slot_gap16 | 1 | pass | pass | pass | pass | none |
| 4slot_gap16 | 2 | pass | pass | pass | pass | none |
| 4slot_gap16 | 3 | pass | pass | pass | pass | none |
| 4slot_gap8 | 0 | pass | pass | pass | pass | none |
| 4slot_gap8 | 1 | pass | pass | pass | pass | none |
| 4slot_gap8 | 2 | pass | pass | pass | pass | none |
| 4slot_gap8 | 3 | pass | pass | pass | pass | none |
| 8slot_gap16 | 0 | fail | pass | pass | pass | dispatch wording/surface, value-copy pressure, repair-memory pressure |
| 8slot_gap16 | 1 | pass | pass | pass | pass | none |
| 8slot_gap16 | 2 | pass | pass | pass | pass | none |
| 8slot_gap16 | 3 | pass | pass | pass | pass | none |
| 8slot_gap8 | 0 | pass | pass | pass | pass | none |
| 8slot_gap8 | 1 | pass | pass | pass | pass | none |
| 8slot_gap8 | 2 | pass | pass | pass | pass | none |
| 8slot_gap8 | 3 | pass | pass | pass | pass | none |

## Phase Metrics

| Stress | Critical slot | Variant | First action | Repair-after-error | Success no-op | Failed gates |
|---|---:|---|---:|---:|---:|---|
| 4slot_gap16 | 0 | copy_assisted | 1.000 | 1.000 | 1.000 | none |
| 4slot_gap16 | 1 | copy_assisted | 1.000 | 1.000 | 1.000 | none |
| 4slot_gap16 | 2 | copy_assisted | 1.000 | 1.000 | 1.000 | none |
| 4slot_gap16 | 3 | copy_assisted | 1.000 | 1.000 | 1.000 | none |
| 4slot_gap16 | 0 | dispatch_original | 1.000 | 1.000 | 1.000 | none |
| 4slot_gap16 | 1 | dispatch_original | 1.000 | 1.000 | 1.000 | none |
| 4slot_gap16 | 2 | dispatch_original | 1.000 | 1.000 | 1.000 | none |
| 4slot_gap16 | 3 | dispatch_original | 1.000 | 1.000 | 1.000 | none |
| 4slot_gap16 | 0 | repair_hinted | 1.000 | 1.000 | 1.000 | none |
| 4slot_gap16 | 1 | repair_hinted | 1.000 | 1.000 | 1.000 | none |
| 4slot_gap16 | 2 | repair_hinted | 1.000 | 1.000 | 1.000 | none |
| 4slot_gap16 | 3 | repair_hinted | 1.000 | 1.000 | 1.000 | none |
| 4slot_gap16 | 0 | wording_neutral | 1.000 | 1.000 | 1.000 | none |
| 4slot_gap16 | 1 | wording_neutral | 1.000 | 1.000 | 1.000 | none |
| 4slot_gap16 | 2 | wording_neutral | 1.000 | 1.000 | 1.000 | none |
| 4slot_gap16 | 3 | wording_neutral | 1.000 | 1.000 | 1.000 | none |
| 4slot_gap8 | 0 | copy_assisted | 1.000 | 1.000 | 1.000 | none |
| 4slot_gap8 | 1 | copy_assisted | 1.000 | 1.000 | 1.000 | none |
| 4slot_gap8 | 2 | copy_assisted | 1.000 | 1.000 | 1.000 | none |
| 4slot_gap8 | 3 | copy_assisted | 1.000 | 1.000 | 1.000 | none |
| 4slot_gap8 | 0 | dispatch_original | 1.000 | 1.000 | 1.000 | none |
| 4slot_gap8 | 1 | dispatch_original | 1.000 | 1.000 | 1.000 | none |
| 4slot_gap8 | 2 | dispatch_original | 1.000 | 1.000 | 1.000 | none |
| 4slot_gap8 | 3 | dispatch_original | 1.000 | 1.000 | 1.000 | none |
| 4slot_gap8 | 0 | repair_hinted | 1.000 | 1.000 | 1.000 | none |
| 4slot_gap8 | 1 | repair_hinted | 1.000 | 1.000 | 1.000 | none |
| 4slot_gap8 | 2 | repair_hinted | 1.000 | 1.000 | 1.000 | none |
| 4slot_gap8 | 3 | repair_hinted | 1.000 | 1.000 | 1.000 | none |
| 4slot_gap8 | 0 | wording_neutral | 1.000 | 1.000 | 1.000 | none |
| 4slot_gap8 | 1 | wording_neutral | 1.000 | 1.000 | 1.000 | none |
| 4slot_gap8 | 2 | wording_neutral | 1.000 | 1.000 | 1.000 | none |
| 4slot_gap8 | 3 | wording_neutral | 1.000 | 1.000 | 1.000 | none |
| 8slot_gap16 | 0 | copy_assisted | 1.000 | 1.000 | 1.000 | none |
| 8slot_gap16 | 1 | copy_assisted | 1.000 | 1.000 | 1.000 | none |
| 8slot_gap16 | 2 | copy_assisted | 1.000 | 1.000 | 1.000 | none |
| 8slot_gap16 | 3 | copy_assisted | 1.000 | 1.000 | 1.000 | none |
| 8slot_gap16 | 0 | dispatch_original | 1.000 | 0.000 | 1.000 | repair_failed_action_acc_ge_0_85 |
| 8slot_gap16 | 1 | dispatch_original | 1.000 | 1.000 | 1.000 | none |
| 8slot_gap16 | 2 | dispatch_original | 1.000 | 1.000 | 1.000 | none |
| 8slot_gap16 | 3 | dispatch_original | 1.000 | 1.000 | 1.000 | none |
| 8slot_gap16 | 0 | repair_hinted | 1.000 | 1.000 | 1.000 | none |
| 8slot_gap16 | 1 | repair_hinted | 1.000 | 1.000 | 1.000 | none |
| 8slot_gap16 | 2 | repair_hinted | 1.000 | 1.000 | 1.000 | none |
| 8slot_gap16 | 3 | repair_hinted | 1.000 | 1.000 | 1.000 | none |
| 8slot_gap16 | 0 | wording_neutral | 1.000 | 1.000 | 1.000 | none |
| 8slot_gap16 | 1 | wording_neutral | 1.000 | 1.000 | 1.000 | none |
| 8slot_gap16 | 2 | wording_neutral | 1.000 | 1.000 | 1.000 | none |
| 8slot_gap16 | 3 | wording_neutral | 1.000 | 1.000 | 1.000 | none |
| 8slot_gap8 | 0 | copy_assisted | 1.000 | 1.000 | 1.000 | none |
| 8slot_gap8 | 1 | copy_assisted | 1.000 | 1.000 | 1.000 | none |
| 8slot_gap8 | 2 | copy_assisted | 1.000 | 1.000 | 1.000 | none |
| 8slot_gap8 | 3 | copy_assisted | 1.000 | 1.000 | 1.000 | none |
| 8slot_gap8 | 0 | dispatch_original | 1.000 | 1.000 | 1.000 | none |
| 8slot_gap8 | 1 | dispatch_original | 1.000 | 1.000 | 1.000 | none |
| 8slot_gap8 | 2 | dispatch_original | 1.000 | 1.000 | 1.000 | none |
| 8slot_gap8 | 3 | dispatch_original | 1.000 | 1.000 | 1.000 | none |
| 8slot_gap8 | 0 | repair_hinted | 1.000 | 1.000 | 1.000 | none |
| 8slot_gap8 | 1 | repair_hinted | 1.000 | 1.000 | 1.000 | none |
| 8slot_gap8 | 2 | repair_hinted | 1.000 | 1.000 | 1.000 | none |
| 8slot_gap8 | 3 | repair_hinted | 1.000 | 1.000 | 1.000 | none |
| 8slot_gap8 | 0 | wording_neutral | 1.000 | 1.000 | 1.000 | none |
| 8slot_gap8 | 1 | wording_neutral | 1.000 | 1.000 | 1.000 | none |
| 8slot_gap8 | 2 | wording_neutral | 1.000 | 1.000 | 1.000 | none |
| 8slot_gap8 | 3 | wording_neutral | 1.000 | 1.000 | 1.000 | none |

## Regime Audit

- Old regime: the API external-stress benchmark exposed two OpenAI `dispatch` cells with passing controls and failed bottleneck gates.
- Transition: this run keeps the same parser, provider adapter, seeds, stress cells, and repair protocol, but splits the failed dispatch surface into original, neutral-wording, value-copy-assisted, and repair-hinted variants.
- Transported evidence: exact JSON action parser, no-op controls, short-copy controls, failed-repair and success-no-op phases, and the previously failed stress settings.
- Rejected alternatives: the diagnostic does not treat black-box behavior as hidden-state localization and does not add broader provider claims.
- Residual finding: the diagnosis column identifies whether the reproduced failure is relieved by wording, value visibility, or repair hints.
- Allowed claim: black-box behavioral robustness/localization for the tested OpenAI model, slots, and stress cells only.

## Local Artifacts

- Rows: `artifacts/long_horizon_bottleneck/api_dispatch_robustness_openai_gpt41_nano_rows.jsonl`
