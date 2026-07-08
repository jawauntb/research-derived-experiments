# Gauge-Fixed Concern Transport Local Full Rerun

- Overall: **PASS**
- Claim level: `local full rerun of the synthetic gate suite; verifies deterministic experiment logic, not a fresh Modal L4 dispatch`
- Execution: `local Python 3.12 CPU rerun`
- Date: `2026-07-08`
- Preset: `full`
- Tracks: `concern_weighted_ood, causal_gauge_fixing, mechanistic_commitment, reafference_null, moved_bottleneck`
- Seeds: `64`
- Rows: `320`

## Gates

| Track | Status | Primary metrics |
| --- | --- | --- |
| Causal gauge fixing | PASS | `alignment_lift`=0.494; `commitment_effect_lift`=0.164 |
| Concern-weighted OOD | PASS | `weighted_error_gain`=0.458; `concern_selector_is_shape`=1.000 |
| Mechanistic commitment | PASS | `patch_effect_ratio`=35.964; `distractor_probe_auc`=0.999; `distractor_patch_effect`=0.010 |
| Moved bottleneck | PASS | `active_vs_early_gain`=0.488; `active_inactive_ratio`=69.420; `localized_active_bottleneck`=0.930 |
| Reafference/null | PASS | `attribution_lift`=0.331; `correction_error_reduction`=0.669; `null_intervention_auc`=0.964 |

## Discovery-Regime Audit

- **Old regime:** proof-focused theorem paper with proposed demos.
- **Transition:** Modal L4 synthetic cells with raw rows, gates, controls, and figures.
- **Preserved gates:** concern weighting, gauge separation, commitment effect, null controls, and moved-bottleneck localization.
- **Allowed claim:** this rerun verifies the deterministic full-suite experiment logic locally; the separate committed `gfc_l4_suite_2026_07_07.*` artifacts remain the Modal L4 evidence.
- **Residual bottleneck:** human, neural, biological, and foundation-model validation remain future work.

## Raw Payload

`experiments/gauge_fixed_concern_transport/results/gfc_local_full_rerun_2026_07_08.json`

## Verification Commands

```bash
/Users/jawaun/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 \
  -m experiments.gauge_fixed_concern_transport.core \
  --preset full \
  --out experiments/gauge_fixed_concern_transport/results/gfc_local_full_rerun_2026_07_08.json

/Users/jawaun/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 \
  -m experiments.gauge_fixed_concern_transport.summarize \
  --in experiments/gauge_fixed_concern_transport/results/gfc_local_full_rerun_2026_07_08.json \
  --out experiments/gauge_fixed_concern_transport/results/gfc_local_full_rerun_2026_07_08.md

doppler --scope /Users/jawaun/superoptimizers run -- \
  uvx --python 3.12 --from modal modal run \
  experiments/gauge_fixed_concern_transport/modal_l4_suite.py \
  --preset full \
  --seeds 64 \
  --budget-usd 250 \
  --dry-run-budget
```

Modal dry-run app: `ap-bdNzGJCVhgT0MFih66ar0H`; budget guard reported
`320` L4 cells and a conservative timeout estimate of `$63.936 / $250.00`.
