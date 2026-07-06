# Benchmark Card: Suite C Re-Engagement Under World Change

Generated: 2026-07-06

## Claim

Suite C tests adaptive inquiry under nonstationary world dynamics. A condition passes only if it re-engages probes after a world shift, recovers attribution, avoids false calm, uses fewer probes than high-cost controls, and re-opens inquiry after a second shift.

## Status

- Suite pass: **PASS**
- Headline condition: `burst_then_refractory`
- Learned-transfer pass: **PASS** for `learned_probe_head`
- Claim level: `diagnostic`; finite controlled benchmark gate and teacher-trained probe-head transfer, not a consciousness, biological, or production reliability claim.

## Execution Record

- Full Modal run: https://modal.com/apps/generalintelligencecompany/main/ap-Fgpr3fPDhd0mCNsStCfJ72.
- Dry-run budget check: https://modal.com/apps/generalintelligencecompany/main/ap-hsB4QplExuXn36Q8foGpAL.
- Conservative budget estimate: $14.3856 against budget $75.0.
- Rows emitted: 72.

## Minimum Pass Rule

A model or policy cannot pass Suite C from final recovery alone. It must pass behavior, inquiry, attribution, cost, false-calm, and second-shift gates together.

## Gates

| Gate | Requirement | Result |
| --- | --- | --- |
| C1_silence_replication | P22 baseline remains nearly silent after shift. | PASS |
| C2_reengagement | Candidate probes affected buckets after shift and beats unaffected buckets by at least 2x. | PASS |
| C3_recovery | Candidate reaches the affected-component MAE threshold in most seeds. | PASS |
| C4_no_false_calm | Probe quieting is paired with attribution-error reduction; signal suppression fails. | PASS |
| C5_cost_aware_inquiry | Candidate uses fewer probes than scheduled/oracle controls at comparable recovery. | PASS |
| C6_reopenability | Candidate re-opens inquiry after a second shift. | PASS |

## Anti-Cheat Controls

- `p22_learned_current_replay`: learned quiet baseline.
- `two_timescale_plus_prediction_error`: anxious re-engagement baseline.
- `fixed_surprise_decrement`: signal-layer false-calm negative control.
- `scheduled_null_anchor`: high-cost positive control.
- `oracle_source`: semantic high-cost reference.
- `matched_random_time_budget`: equal-budget random inquiry control.
- `stale_signal_head`: learned-policy control where affected buckets do not receive fresh post-shift stress.
- `wrong_signal_head`: learned-policy control where stress is attributed to the wrong source.
- `signal_suppression_head`: learned-policy control where perceived stress is hidden while actual attribution error remains high.

## Learned-Policy Transfer

The transfer runner trains a small NumPy MLP probe head from Suite C teacher
traces, calibrates a threshold on separate seeds, and evaluates held-out seeds.
The learned head reaches final affected MAE 0.112, first-shift selectivity
16.667, second-shift reopenability 17.448, and 23.1 probes. Matched random at
the same budget reaches selectivity 0.969.

## Artifacts

- Local-only raw rows: `artifacts/world_responds/suite_c_reengagement_rows.jsonl`
- Local-only raw summary: `artifacts/world_responds/suite_c_reengagement_summary.json`
- Public release summary: `experiments/world_responds/results/suite_c_reengagement_2026_07_06.json`
- Result report: `experiments/world_responds/results/suite_c_reengagement_2026_07_06.md`
- Learned-transfer summary: `experiments/world_responds/results/suite_c_neural_transfer_2026_07_06.json`
- Learned-transfer report: `experiments/world_responds/results/suite_c_neural_transfer_2026_07_06.md`
- Paper: `papers/habituated_reengagement/suite_c_reengagement_under_world_change.md`
- Learned-transfer paper: `papers/habituated_reengagement/suite_c_neural_probe_transfer.md`
- Critical review: `docs/paper_reviews/suite_c_reengagement_under_world_change_critical_review.md`
- Learned-transfer critical review: `docs/paper_reviews/suite_c_neural_probe_transfer_critical_review.md`

## Non-Claims

This benchmark does not certify consciousness, broad autonomy, biological validity, or open-world reliability. The learned-transfer layer is teacher-trained inside the same finite harness; reward-trained and open-agent transfer remain separate claims.
