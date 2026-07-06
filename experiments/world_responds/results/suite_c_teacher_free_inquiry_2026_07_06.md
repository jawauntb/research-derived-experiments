# Suite C Teacher-Free Inquiry

Date: 2026-07-06

## Discovery-Regime Audit

Question: can Suite C re-engagement be learned without direct teacher labels, actions, or probabilities?

Current regime:
- Artifact types: finite Suite C rows, learned-policy summaries, public JSONL rows, public summary JSON, and gate report.
- Operations: CEM reward search over a linear probe policy, threshold calibration, held-out finite simulator evaluation.
- Gates/verifiers: C1-C6 Suite C gates, T1 teacher-free audit, N1 stale/wrong/suppressed signal controls, matched random budget.
- Known limitations: finite NumPy simulator; no open-agent, API-agent, biological, or consciousness claim.

Action class:
- Retrieval/search/discovery: bounded discovery-level transition.
- Why: the operation changes from teacher-trace imitation to downstream reward search while preserving the old Suite C gates.

Experiment:
- Train seeds: `[20331706, 20332703, 20333700, 20334697, 20335694]`.
- Calibration seeds: `[20341706, 20342703, 20343700, 20344697, 20345694, 20346691, 20347688, 20348685]`.
- Held-out eval seeds: `[20351706, 20352703, 20353700, 20354697, 20355694, 20356691, 20357688, 20358685]`.
- Selected threshold: `0.500`.
- Positive target: reward/CEM policy passes C1-C6 with lower probe cost than scheduled/oracle controls.
- Negative controls: stale signal, wrong signal, signal suppression, equal-budget random, recovery-only proxy, cost-only proxy.

Gate:
- Acceptance rule: C1-C6, T1, and N1 pass on held-out seeds with public-safe rows and summary.
- Withheld/rejected rule: stale/wrong/suppressed controls passing, random budget matching selectivity, or teacher supervision would make the result negative.

## Gate Results

| Gate | Pass? | Evidence |
| --- | --- | --- |
| C1_silence_replication | PASS | baseline_post_shift_density=0.005 |
| C2_reengagement | PASS | first_reengagement_ratio=3.000, first_selectivity_ratio=12.500 |
| C3_recovery | PASS | recovery_rate=1.000, final_component_mae=0.095 |
| C4_no_false_calm | PASS | learned_no_false_calm_rate=1.000, suppressed_no_false_calm_rate=0.000, suppressed_final_component_mae=0.464 |
| C5_cost_aware_inquiry | PASS | learned_total_probes=22.000, scheduled_total_probes=144.000, oracle_total_probes=68.875, matched_selectivity_ratio=0.833 |
| C6_reopenability | PASS | second_reopen_ratio=11.312 |
| T1_teacher_free_training | PASS | teacher_labels_used=false, teacher_actions_used=false, teacher_probabilities_used=false |
| N1_learned_signal_controls | PASS | stale_control_failed=PASS, wrong_signal_control_failed=PASS, suppression_control_failed=PASS |
| suite_pass | PASS |  |

## Headline

The teacher-free policy reaches final affected MAE 0.095, recovery rate 1.000, first-shift selectivity 12.500, second-shift reopenability 11.312, and 22.0 probes.

Matched random at the same budget reaches selectivity 0.833. Stale-signal recovery rate is 0.000; wrong-signal selectivity is 0.000; suppressed-signal final MAE is 0.464.

## Condition Summary

| Condition | N | Probes | Final MAE | Selectivity | Reopen | No false calm | Recovery |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `p22_learned_current_replay` | 8 | 7.5 | 1.351 | 0.260 | 0.323 | 1.000 | 0.000 |
| `scheduled_null_anchor` | 8 | 144.0 | 0.046 | 1.000 | 1.000 | 1.000 | 1.000 |
| `oracle_source` | 8 | 68.9 | 0.043 | 9.729 | 24.083 | 1.000 | 1.000 |
| `teacher_free_reward_policy` | 8 | 22.0 | 0.095 | 12.500 | 11.312 | 1.000 | 1.000 |
| `teacher_free_stale_signal` | 8 | 10.0 | 0.409 | 0.521 | 1.885 | 1.000 | 0.000 |
| `teacher_free_wrong_signal` | 8 | 198.0 | 0.810 | 0.000 | 0.000 | 1.000 | 0.000 |
| `teacher_free_signal_suppression` | 8 | 12.0 | 0.464 | 8.333 | 0.000 | 0.000 | 0.000 |
| `recovery_only_proxy_policy` | 8 | 14.9 | 0.167 | 12.500 | 12.500 | 0.000 | 0.000 |
| `cost_only_proxy_policy` | 8 | 0.0 | 0.891 | 0.000 | 0.000 | 1.000 | 0.000 |
| `matched_random_teacher_free_budget` | 8 | 22.0 | 0.459 | 0.833 | 1.490 | 0.500 | 0.000 |

## Interpretation

This is stronger than the teacher-trained probe head on the specific reviewer objection it targets: the training loss never consumes hand-policy actions, teacher labels, or teacher probabilities. It is still not an open-agent result; it is a finite diagnostic showing that Suite C can be learned from downstream world-response reward in this harness.

## Artifact Ledger

- Public rows JSONL: `experiments/world_responds/results/suite_c_teacher_free_inquiry_rows_2026_07_06.jsonl`
- Public summary JSON: `experiments/world_responds/results/suite_c_teacher_free_inquiry_2026_07_06.json`
- Report: `experiments/world_responds/results/suite_c_teacher_free_inquiry_2026_07_06.md`
