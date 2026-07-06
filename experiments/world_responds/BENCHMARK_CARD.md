# Benchmark Card: Suite C Re-Engagement Under World Change

Generated: 2026-07-06

## Claim

Suite C tests adaptive inquiry under nonstationary world dynamics. A condition passes only if it re-engages probes after a world shift, recovers attribution, avoids false calm, uses fewer probes than high-cost controls, and re-opens inquiry after a second shift.

## Status

- Suite pass: **PASS**
- Headline condition: `burst_then_refractory`
- Learned-transfer pass: **PASS** for `learned_probe_head`
- Teacher-free inquiry pass: **PASS** for `teacher_free_reward_policy`
- Claim level: `diagnostic`; finite controlled benchmark gates with hand-policy,
  teacher-trained probe-head, and teacher-free reward/CEM layers, not a
  consciousness, biological, or production reliability claim.

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
- `teacher_free_stale_signal`: teacher-free policy control where fresh stress is withheld.
- `teacher_free_wrong_signal`: teacher-free policy control where stress is attributed to the wrong source.
- `teacher_free_signal_suppression`: teacher-free policy control where stress is hidden while attribution error remains high.
- `matched_random_teacher_free_budget`: equal-budget random inquiry control for the teacher-free policy.

## Learned-Policy Transfer

The transfer runner trains a small NumPy MLP probe head from Suite C teacher
traces, calibrates a threshold on separate seeds, and evaluates held-out seeds.
The learned head reaches final affected MAE 0.112, first-shift selectivity
16.667, second-shift reopenability 17.448, and 23.1 probes. Matched random at
the same budget reaches selectivity 0.969.

## Teacher-Free Inquiry

The teacher-free runner selects a linear probe policy by cross-entropy-method
search on downstream recovery, selectivity, reopenability, probe cost, and
anti-cheat controls. The training loss does not consume hand-policy labels,
teacher actions, or teacher probabilities. On held-out seeds,
`teacher_free_reward_policy` passes C1-C6 plus T1/N1: final affected MAE 0.095,
recovery rate 1.000, first-shift selectivity 12.500, second-shift reopenability
11.312, and 22.0 probes. Stale-signal recovery is 0.000, wrong-signal
selectivity is 0.000, suppressed-signal final MAE is 0.464, and matched random
at the same budget reaches selectivity 0.833.

The wider 64-seed/1000-bootstrap check preserves the result: final affected MAE
0.095 with 95% CI [0.095, 0.096], recovery rate 1.000 [1.000, 1.000],
selectivity lift over matched random 11.292 [10.976, 11.596], stale-signal
recovery 0.000 [0.000, 0.000], and suite pass rate 1.000 [1.000, 1.000].

## Source-Estimate and Tool-Transfer Follow-Up

The less-privileged source-estimate ablation replaces the privileged
`source_is_affected` feature with an observable error/surprise-jump estimate.
It passes the finite Suite C gate. The local JSON-like tool-transfer adapter
also passes, while a malformed-tool control fails: malformed recovery rate
0.000 and final affected MAE 0.158 versus 0.102 for valid tool transfer.
This is still a finite local adapter, not an external API-agent result.

## Artifacts

- Local-only raw rows: `artifacts/world_responds/suite_c_reengagement_rows.jsonl`
- Local-only raw summary: `artifacts/world_responds/suite_c_reengagement_summary.json`
- Public release summary: `experiments/world_responds/results/suite_c_reengagement_2026_07_06.json`
- Result report: `experiments/world_responds/results/suite_c_reengagement_2026_07_06.md`
- Learned-transfer summary: `experiments/world_responds/results/suite_c_neural_transfer_2026_07_06.json`
- Learned-transfer report: `experiments/world_responds/results/suite_c_neural_transfer_2026_07_06.md`
- Teacher-free rows: `experiments/world_responds/results/suite_c_teacher_free_inquiry_rows_2026_07_06.jsonl`
- Teacher-free summary: `experiments/world_responds/results/suite_c_teacher_free_inquiry_2026_07_06.json`
- Teacher-free report: `experiments/world_responds/results/suite_c_teacher_free_inquiry_2026_07_06.md`
- Teacher-free wide stats: `experiments/world_responds/results/suite_c_teacher_free_wide_stats_2026_07_06.md`
- Source-estimate/tool-transfer summary: `experiments/world_responds/results/suite_c_source_ablation_transfer_2026_07_06.json`
- Source-estimate/tool-transfer rows: `experiments/world_responds/results/suite_c_source_ablation_transfer_rows_2026_07_06.jsonl`
- Source-estimate/tool-transfer report: `experiments/world_responds/results/suite_c_source_ablation_transfer_2026_07_06.md`
- Paper: `papers/habituated_reengagement/suite_c_reengagement_under_world_change.md`
- Learned-transfer paper: `papers/habituated_reengagement/suite_c_neural_probe_transfer.md`
- Critical review: `docs/paper_reviews/suite_c_reengagement_under_world_change_critical_review.md`
- Learned-transfer critical review: `docs/paper_reviews/suite_c_neural_probe_transfer_critical_review.md`

## Non-Claims

This benchmark does not certify consciousness, broad autonomy, biological
validity, or open-world reliability. The teacher-free and source-estimate
tool-transfer layers are finite NumPy/local-adapter results; external open-agent
transfer remains a separate claim.
