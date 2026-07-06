# Benchmark Card: Suite C Re-Engagement Under World Change

Generated: 2026-07-06

## Claim

Suite C tests adaptive inquiry under nonstationary world dynamics. A condition passes only if it re-engages probes after a world shift, recovers attribution, avoids false calm, uses fewer probes than high-cost controls, and re-opens inquiry after a second shift.

## Status

- Suite pass: **PASS**
- Headline condition: `burst_then_refractory`
- Claim level: `diagnostic`; finite controlled benchmark gate, not a consciousness, biological, or production reliability claim.

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

## Artifacts

- Local-only raw rows: `artifacts/world_responds/suite_c_reengagement_rows.jsonl`
- Local-only raw summary: `artifacts/world_responds/suite_c_reengagement_summary.json`
- Public release summary: `experiments/world_responds/results/suite_c_reengagement_2026_07_06.json`
- Result report: `experiments/world_responds/results/suite_c_reengagement_2026_07_06.md`
- Paper: `papers/habituated_reengagement/suite_c_reengagement_under_world_change.md`
- Critical review: `docs/paper_reviews/suite_c_reengagement_under_world_change_critical_review.md`

## Non-Claims

This benchmark does not certify consciousness, broad autonomy, biological validity, or open-world reliability. It is a controlled finite test of adaptive inquiry mechanics.
