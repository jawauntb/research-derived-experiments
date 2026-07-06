# Suite C Teacher-Free Wide-Seed Bootstrap

Date: 2026-07-06

## Setup

- Held-out eval seeds: 64
- Bootstrap reps over eval seeds: 1000
- Training regime: teacher-free reward/CEM linear probe policy.
- Units: eval seed clusters; each bootstrap sample resamples full per-seed condition rows.

## Gate Status

| Gate | Pass? |
| --- | --- |
| C1_silence_replication | PASS |
| C2_reengagement | PASS |
| C3_recovery | PASS |
| C4_no_false_calm | PASS |
| C5_cost_aware_inquiry | PASS |
| C6_reopenability | PASS |
| T1_teacher_free_training | PASS |
| N1_learned_signal_controls | PASS |
| suite_pass | PASS |

## Bootstrap Metrics

| Metric | Point | 95% CI |
| --- | ---: | ---: |
| `learned_final_component_mae` | 0.095 | [0.095, 0.096] |
| `learned_recovery_rate` | 1.000 | [1.000, 1.000] |
| `learned_first_selectivity_ratio` | 12.500 | [12.500, 12.500] |
| `learned_second_reopen_ratio` | 11.164 | [10.273, 11.906] |
| `learned_total_probes` | 21.984 | [21.953, 22.000] |
| `matched_random_selectivity_ratio` | 1.208 | [0.904, 1.524] |
| `selectivity_lift_vs_matched_random` | 11.292 | [10.976, 11.596] |
| `final_mae_gain_vs_matched_random` | 0.353 | [0.323, 0.382] |
| `stale_signal_recovery_rate` | 0.000 | [0.000, 0.000] |
| `wrong_signal_selectivity_ratio` | 0.000 | [0.000, 0.000] |
| `suppressed_signal_final_component_mae` | 0.469 | [0.461, 0.476] |
| `suite_pass_rate` | 1.000 | [1.000, 1.000] |

## Interpretation

Across a wider held-out finite Suite C seed panel, the teacher-free reward/CEM policy preserves the original C1-C6 and T1/N1 pass while matched-random, stale, wrong, and suppressed-signal controls remain separated.

The interval is still finite-harness evidence, not an open-agent claim. The next paper-grade step is an ablation that replaces the privileged source-is-affected feature with a learned or noisy source estimate.
