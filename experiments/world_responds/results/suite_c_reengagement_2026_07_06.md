# Suite C Re-Engagement Benchmark Status

Generated: 2026-07-06

## Discovery-Regime Audit

- Old regime: separate Paper 22, Paper 23A, and Paper 23B results with
  paper-local gates.
- Transition: Suite C packaging for re-engagement under world change, using the
  shared causally grounded agents benchmark vocabulary.
- Transported evidence: `papers/world_responds/paper.md`,
  `papers/probe_value_reengagement/paper.md`,
  `papers/habituated_reengagement/paper.md`, and
  `experiments/world_responds/results/reengagement_23a_2026_07_06.md`.
- Rejected alternatives: final MAE alone, current-error probing as an oracle,
  signal-layer surprise erasure, and always-probe schedules.
- Residual finding: Suite C is not a terminal pass yet. It is a bounded
  positive with a recovery and public-runner gap.
- Allowed claim: proxy-resistant benchmark card plus partial positive evidence
  for decision-layer cooling and no-false-calm gating.

## Suite Question

Can an agent that has learned to stop probing reopen identifying interventions
after a world shift, then stop again only because the relevant attribution has
recovered?

## Evidence Map

| Evidence | What it contributes | Result |
|---|---|---|
| Paper 22, `papers/world_responds/paper.md` | Baseline self-silencing failure after world change | Learned probes go quiet after shift; re-engagement floor is needed. |
| Paper 23A, `papers/probe_value_reengagement/paper.md` | Non-null surprise breaks self-silencing | Headline re-engages to 137% of pre-shift density and 3.04x unaffected buckets, but causes anxiety and 0/3 strict recoveries. |
| July 6 Paper 23A Modal report | Fresh committed re-engagement search result | Audit-floor and fast/slow variants restore nonzero affected post-shift nulls; baseline remains 0.0. |
| Paper 23B, `papers/habituated_reengagement/paper.md` | Decision-layer cooling and no-false-calm gate | Decision variants reduce anxiety by 37-46%, preserve second-shift reopenability, and catch signal-layer false calm. |

## Gate Status

| Gate | Status | Evidence |
|---|---|---|
| C1. Silence replication | Pass | July 6 report: `learned_scale_norm_current_replay` has 0.0 affected post-shift nulls. Paper 23A reports the P22 replay baseline at about 1.7 mean affected post-shift probes. |
| C2. Re-engagement | Pass | Paper 23A: 137% pre-shift affected density and 3.04x unaffected buckets. July 6 report: audit-floor and fast/slow variants restore 109.7 and 191.0 affected post-shift nulls. |
| C3. Recovery | Partial | Paper 23B: `decision_refractory` and `burst_then_refractory` recover 2/3 seeds, `leaky_effort_integrator` recovers 1/3, `oracle_source` recovers 3/3. |
| C4. No false calm | Pass | `fixed_surprise_decrement` has the lowest learned post-shift AUC but 0/3 recovery, so silence without outcome improvement is rejected. |
| C5. Cost-aware inquiry | Partial | Decision-layer variants cut post-shift AUC by 37-46% versus P23A anxiety, but a public JSONL cost-normalized scorer has not been emitted yet. |
| C6. Re-openability | Pass | Paper 23B second-shift ratios: 2.05x for `leaky_effort_integrator`, 1.81x for `decision_refractory`, 2.18x for `burst_then_refractory`. |

## Verdict

Outcome: `bounded_positive_with_recovery_gap`.

Suite C is packaged enough to share as a benchmark frontier and methodological
pattern. It should not be described as fully solved. The correct claim is:

> Decision-layer cooling is a stronger re-engagement repair than signal-layer
> surprise suppression because it dampens action without erasing the change
> signal. The no-false-calm gate is load-bearing: lower inquiry rate is only a
> pass when attribution/outcome improves too.

## Minimum Pass Rule

The minimum pass rule is not terminally satisfied for the full suite because
the behavior/recovery gate is still partial. The structure-specific and
anti-cheat gates are meaningful and positive:

- behavior/recovery: partial;
- inquiry/re-engagement structure gate: pass;
- anti-cheat/no-false-calm gate: pass;
- public release artifact completeness: partial, pending Paper 23B JSONL runner.

## Next Implementation Step

The next code-hardening step is a Paper 23B runner under
`experiments/world_responds` that emits:

- `artifacts/world_responds/suite_c_reengagement_rows.jsonl`;
- `artifacts/world_responds/suite_c_reengagement_summary.json`;
- a regenerated `experiments/world_responds/results/suite_c_reengagement_<date>.md`.

Stop with a useful strong negative if the public runner reproduces
re-engagement but not recovery, or if recovery only comes from scheduled dense
probing.
