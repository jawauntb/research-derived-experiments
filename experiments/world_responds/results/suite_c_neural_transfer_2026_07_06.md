# Suite C Neural Probe Transfer

Date: 2026-07-06

## Discovery-Regime Audit

Question: can Suite C's decision-layer inquiry law survive when the probe decision is trained rather than hand-specified?

Current regime:
- Artifact types: learned probe-head payloads, held-out Suite C rows, tracked public summary JSON, figures, paper, critical review.
- Operations: teacher trace collection from `burst_then_refractory`, NumPy MLP training, threshold calibration, held-out evaluation.
- Gates/verifiers: C1-C6 Suite C gates plus stale-signal, wrong-signal, and signal-suppression controls.
- Known limitations: finite simulator transfer; not a human, biological, consciousness, or production-agent result.

Action class:
- Retrieval/search/discovery: bounded discovery-level transfer artifact.
- Why: the run adds a learned-policy artifact type and learned-signal controls not present in the terminal hand-policy gate.

Experiment:
- Train seeds: `[20271706, 20272703, 20273700, 20274697, 20275694, 20276691, 20277688, 20278685, 20279682, 20280679, 20281676, 20282673, 20283670, 20284667, 20285664, 20286661]`.
- Calibration seeds: `[20291706, 20292709, 20293712, 20294715, 20295718, 20296721]`.
- Held-out eval seeds: `[20311706, 20312709, 20313712, 20314715, 20315718, 20316721, 20317724, 20318727]`.
- Selected threshold: `0.320`.
- Training examples: `6912` with positive rate `0.054`.
- Controls: stale perceived signals, wrong-source perceived signals, suppressed stress signals, and matched random at the learned probe budget.

Gate:
- Acceptance rule: learned head passes C1-C6 on held-out seeds and all learned-policy controls fail in their intended way.
- Withheld/rejected rule: do not claim transfer if recovery comes from high-cost probing, if random budget matches selectivity, or if stale/wrong/suppressed signals pass.

## Gate Results

| Gate | Pass? | Evidence |
| --- | --- | --- |
| C1_silence_replication | PASS | baseline_post_shift_density=0.026 |
| C2_reengagement | PASS | first_reengagement_ratio=11.833, first_selectivity_ratio=16.667 |
| C3_recovery | PASS | final_component_mae=0.112, recovery_rate=1.000 |
| C4_no_false_calm | PASS | learned_no_false_calm_rate=1.000, suppressed_final_component_mae=0.554, suppressed_no_false_calm_rate=0.000 |
| C5_cost_aware_inquiry | PASS | learned_total_probes=23.125, matched_selectivity_ratio=0.969, oracle_total_probes=67.750, scheduled_total_probes=144.000 |
| C6_reopenability | PASS | second_reopen_ratio=17.448 |
| N1_learned_signal_controls | PASS | stale_control_failed=PASS, suppression_control_failed=PASS, wrong_signal_control_failed=PASS |

## Headline

The learned probe head reaches final affected MAE 0.112, first-shift selectivity 16.667, second-shift reopenability 17.448, and uses 23.1 probes.

Suite pass: **PASS**.

## Condition Summary

| Condition | N | Probes | Final MAE | Selectivity | Reopen | No false calm | Recovery |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `p22_learned_current_replay` | 8 | 9.1 | 1.281 | 1.302 | 0.521 | 0.875 | 0.000 |
| `scheduled_null_anchor` | 8 | 144.0 | 0.046 | 1.000 | 1.000 | 1.000 | 1.000 |
| `oracle_source` | 8 | 67.8 | 0.049 | 13.399 | 7.094 | 1.000 | 1.000 |
| `teacher_burst_then_refractory` | 8 | 22.9 | 0.110 | 17.448 | 16.927 | 1.000 | 1.000 |
| `learned_probe_head` | 8 | 23.1 | 0.112 | 16.667 | 17.448 | 1.000 | 1.000 |
| `stale_signal_head` | 8 | 25.8 | 0.237 | 8.594 | 8.495 | 0.875 | 0.500 |
| `wrong_signal_head` | 8 | 198.8 | 0.853 | 0.000 | 0.000 | 1.000 | 0.000 |
| `signal_suppression_head` | 8 | 14.8 | 0.554 | 16.667 | 0.000 | 0.000 | 0.000 |
| `matched_random_learned_budget` | 8 | 23.1 | 0.422 | 0.969 | 1.344 | 0.625 | 0.000 |

## Interpretation

The learned head is not rewarded for final error alone. It must re-open inquiry after two shifts, recover attribution, spend fewer probes than scheduled/oracle controls, and beat matched random inquiry at the same budget.

The three learned-policy controls keep the claim narrow. Stale signals test whether the head needs fresh world evidence; wrong signals test source attribution; signal suppression tests whether quiet can be produced by hiding stress from the policy.

## Artifact Ledger

- Local-only raw payload: `artifacts/world_responds/suite_c_neural_transfer_payload.json`
- Local-only raw rows: `artifacts/world_responds/suite_c_neural_transfer_rows.jsonl`
- Local-only raw summary: `artifacts/world_responds/suite_c_neural_transfer_summary.json`
- Public summary JSON: `experiments/world_responds/results/suite_c_neural_transfer_2026_07_06.json`
- Paper: `papers/habituated_reengagement/suite_c_neural_probe_transfer.md`
- PDF: `papers/habituated_reengagement/suite_c_neural_probe_transfer.pdf`
- Critical review: `docs/paper_reviews/suite_c_neural_probe_transfer_critical_review.md`
