# OpenAI Dispatch Failure Characterization

Date: 2026-07-06

## Outcome

Outcome: `partially_reproduced_localized`.
Rows: 28; planned requests: 60.
Controls pass: yes.
Original dispatch failure reproduced: yes.
Localized cells: 1; unresolved cells: 0.
Original dispatch failure not reproduced cells: 1.

## Diagnostic Matrix

| Stress | Original | Neutral wording | Copy-assisted | Repair-hinted | Diagnosis |
|---|---|---|---|---|---|
| 4slot_gap8 | pass | pass | pass | pass | none |
| 8slot_gap16 | fail | pass | pass | fail | dispatch wording/surface, value-copy pressure |

## Phase Metrics

| Stress | Variant | First action | Repair-after-error | Success no-op | Failed gates |
|---|---|---:|---:|---:|---|
| 4slot_gap8 | copy_assisted | 1.000 | 1.000 | 1.000 | none |
| 4slot_gap8 | dispatch_original | 1.000 | 1.000 | 1.000 | none |
| 4slot_gap8 | repair_hinted | 1.000 | 1.000 | 1.000 | none |
| 4slot_gap8 | wording_neutral | 1.000 | 1.000 | 1.000 | none |
| 8slot_gap16 | copy_assisted | 1.000 | 1.000 | 1.000 | none |
| 8slot_gap16 | dispatch_original | 1.000 | 0.500 | 1.000 | repair_failed_action_acc_ge_0_85 |
| 8slot_gap16 | repair_hinted | 0.500 | 0.500 | 1.000 | first_action_acc_ge_0_85, repair_failed_action_acc_ge_0_85 |
| 8slot_gap16 | wording_neutral | 1.000 | 1.000 | 1.000 | none |

## Regime Audit

- Old regime: the API external-stress benchmark exposed two OpenAI `dispatch` cells with passing controls and failed bottleneck gates.
- Transition: this run keeps the same parser, provider adapter, seeds, stress cells, and repair protocol, but splits the failed dispatch surface into original, neutral-wording, value-copy-assisted, and repair-hinted variants.
- Transported evidence: exact JSON action parser, no-op controls, short-copy controls, failed-repair and success-no-op phases, and the previously failed stress settings.
- Rejected alternatives: the diagnostic does not treat black-box behavior as hidden-state localization and does not add broader provider claims.
- Residual finding: the diagnosis column identifies whether the reproduced failure is relieved by wording, value visibility, or repair hints.
- Allowed claim: black-box behavioral failure localization for the tested OpenAI model and stress cells only.

## Local Artifacts

- Rows: `artifacts/long_horizon_bottleneck/api_dispatch_characterization_openai_gpt41_nano_rows.jsonl`
