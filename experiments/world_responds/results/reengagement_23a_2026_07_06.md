# Paper 23A: Probe Re-Engagement and True Probe-Value Oracle

Date: 2026-07-06

## Discovery-Regime Audit

Question: can the Paper 22 re-engagement failure be fixed by adding a persistent audit floor or a fast/slow surprise detector, and does a reducible-error oracle behave differently from the current-error proxy?

Current regime:
- Artifact types: Modal sweep JSON, committed result report, paper-ready figures.
- Operations: world-responds hazard environment, null-anchor self/world attribution, learned V_probe, oracle probe rules.
- Gates/verifiers: post-shift affected-bucket probe ratio, final learning-curve MAE, Modal lint/type/publication checks.
- Known limitations: the true probe-value oracle is exact for a bucket-mean null estimator, not a full neural retraining rollout.

Action class:
- Retrieval/search/discovery: search inside the Paper 22 artifact schema, with one verifier upgrade.
- Why: the run adds re-engagement conditions and replaces current-error oracle logic with a reducible-error oracle proxy.

Gate:
- Acceptance rule: a re-engagement condition should restore nonzero post-shift affected-bucket probes while keeping final LC MAE in the same broad range as the baseline learned probe.
- Withheld/rejected rule: if post-shift probes remain zero, the condition does not close G7.

## Summary Metrics

| Condition | Final LC MAE | Cum nulls | Affected pre-shift nulls | Affected post-shift nulls | Post/pre |
|---|---:|---:|---:|---:|---:|
| `learned_scale_norm_current_replay` | 0.091 | 212.7 | 117.3 | 0.0 | 0.000 |
| `learned_scale_norm_audit_floor` | 0.105 | 645.0 | 224.7 | 109.7 | 0.544 |
| `learned_scale_norm_fast_slow` | 0.112 | 1042.0 | 369.3 | 191.0 | 0.511 |
| `oracle_probe_value` | 0.463 | 6080.7 | 1545.3 | 1464.7 | 0.948 |
| `oracle_probe_value_true` | 0.156 | 50.7 | 24.0 | 4.3 | 0.180 |
| `matched_random_time_budget` | 0.124 | 132.3 | 23.3 | 44.3 | 1.956 |

## Verdict

Accepted as a re-engagement search result: at least one re-engagement condition increases post-shift affected-bucket probing over the learned baseline.

## Interpretation

- Baseline post-shift affected probing: 0.0.
- Audit-floor post-shift affected probing: 109.7.
- Fast/slow post-shift affected probing: 191.0.
- True reducible-error oracle post-shift affected probing: 4.3.

The core test is whether the agent has a path back into inquiry after the world changes. Final MAE matters, but G7 is specifically about avoiding self-confirming silence.

## Next Move

Use this result to decide whether Paper 23A should become a full paper or whether the verifier needs a stronger neural-retraining oracle before publication.

## Artifact Ledger

- Raw ignored payload: `artifacts/world_responds/reengagement_23a_v1.json`
- Committed report: `experiments/world_responds/results/reengagement_23a_2026_07_06.md`
