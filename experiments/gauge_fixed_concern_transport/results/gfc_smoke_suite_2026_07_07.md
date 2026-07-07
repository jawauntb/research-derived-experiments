# Gauge-Fixed Concern Transport L4 Suite

- Overall: **PASS**
- Claim level: `local smoke for synthetic gate logic`
- Preset: `smoke`
- Tracks: `concern_weighted_ood, causal_gauge_fixing, mechanistic_commitment, reafference_null, moved_bottleneck`
- Seeds: `4`
- Rows: `20`

## Gates

| Track | Status | Primary metrics |
| --- | --- | --- |
| Causal gauge fixing | PASS | `alignment_lift`=0.366; `commitment_effect_lift`=0.119 |
| Concern-weighted OOD | PASS | `weighted_error_gain`=0.630; `concern_selector_is_shape`=1.000 |
| Mechanistic commitment | PASS | `patch_effect_ratio`=36.609; `distractor_probe_auc`=0.999; `distractor_patch_effect`=0.010 |
| Moved bottleneck | PASS | `active_vs_early_gain`=0.491; `active_inactive_ratio`=109.464; `localized_active_bottleneck`=0.925 |
| Reafference/null | PASS | `attribution_lift`=0.345; `correction_error_reduction`=0.684; `null_intervention_auc`=0.962 |

## Discovery-Regime Audit

- **Old regime:** proof-focused theorem paper with proposed demos.
- **Transition:** Modal L4 synthetic cells with raw rows, gates, controls, and figures.
- **Preserved gates:** concern weighting, gauge separation, commitment effect, null controls, and moved-bottleneck localization.
- **Allowed claim:** synthetic L4 empirical validation only.
- **Residual bottleneck:** human, neural, biological, and foundation-model validation remain future work.

## Raw Payload

`artifacts/gauge_fixed_concern_transport/smoke_suite.json`
