# Next Empirical Gap: Suite C Re-Engagement Under World Change

Generated: 2026-07-06

## Why Suite C Is Next

Suites D and E are the most hardened current results: the long-horizon moved
bottleneck and tool-commitment ladder now include synthetic, open-model,
causal-patch, prompt-family, and API behavior surfaces.

Suite C remains the most scientifically valuable active gap. Existing work has
shown all the interesting pieces separately:

- Paper 22: learned probing can self-silence after the world changes.
- Paper 23A: non-null surprise re-engages probing, but can over-fire.
- Paper 23B: decision-layer cooling reduces anxiety and preserves second-shift
  re-openability, while signal-layer cooling creates false calm.

The missing terminal result is a compact benchmark condition that jointly
requires re-engagement, recovery, cost discipline, and no false calm.

## Discovery-Regime Audit

- Old regime: self/world attribution and probe-value papers with per-paper
  gates, including Paper 22's post-shift silence, Paper 23A's anxiety, and
  Paper 23B's decision-layer cooling.
- Transition: a Suite C benchmark gate that treats re-engagement as a public
  benchmark condition rather than a paper-local result.
- Transported evidence: `papers/world_responds/paper.md`,
  `papers/probe_value_reengagement/paper.md`,
  `papers/habituated_reengagement/paper.md`, and
  `experiments/world_responds/results/reengagement_23a_2026_07_06.md`.
- Rejected alternatives: current-error probing as an oracle; ensemble variance
  as sufficient uncertainty; signal-layer surprise decrement as healthy
  habituation; final MAE alone as a pass.
- Residual finding: the benchmark must distinguish healthy quiet from false
  calm. A lower probe rate is only good if attribution actually recovered.
- Readiness: enough evidence exists to define the suite; the terminal gate is
  not yet complete.
- Allowed claim: diagnostic benchmark plan for finite re-engagement, not a
  completed human/neural result.

## Proposed Suite C Gate

The candidate terminal condition should include two world shifts. The first
shift tests re-engagement after learned quiet; the second shift tests whether
cooling decays enough to reopen inquiry.

Acceptance gates:

| Gate | Requirement | Rationale |
|---|---|---|
| C1. Silence replication | baseline learned current-replay probe has near-zero affected-bucket probes after shift | preserves the original failure |
| C2. Re-engagement | candidate has affected post-shift probe density at least 0.5x pre-shift and at least 2x unaffected buckets | proves the agent asks again where the world changed |
| C3. Recovery | candidate reaches final component MAE at or below the suite threshold in most seeds | prevents anxious probing without learning |
| C4. No false calm | probe drop must be paired with attribution-error drop; direct surprise suppression fails | distinguishes habituation from blindness |
| C5. Cost-aware inquiry | candidate uses fewer probes than scheduled-null or oracle-source controls at comparable recovery | prevents always-probe solutions |
| C6. Re-openability | after a second shift, affected-bucket probes rise again above pre-second-shift density | proves cooling is not permanent suppression |

## Candidate Conditions

Primary candidates:

- `decision_refractory`: raise the firing threshold as recent probe effort
  accumulates while preserving the surprise signal.
- `burst_then_refractory`: allow a limited burst after detected change, then
  enter a cooldown window.
- `learned_cooldown_head`: learn a decision-layer cooldown from recent probe
  effort and attribution improvement, without directly decrementing surprise.

Required controls:

- `p22_learned_current_replay`: self-silencing baseline.
- `two_timescale_plus_prediction_error`: anxious re-engagement baseline.
- `fixed_surprise_decrement`: false-calm negative control.
- `scheduled_null_anchor`: high-cost positive control.
- `oracle_source`: semantic upper reference.
- `matched_random_time_budget`: random inquiry at matched probe count.

## Release Artifacts

When run, Suite C should produce:

- `experiments/world_responds/BENCHMARK_CARD.md`;
- JSONL rows under `artifacts/world_responds/suite_c_reengagement_rows.jsonl`;
- summary JSON under `artifacts/world_responds/suite_c_reengagement_summary.json`;
- report under `experiments/world_responds/results/suite_c_reengagement_<date>.md`;
- paper update or short standalone report under `papers/habituated_reengagement/`.

## Stop Conditions

A useful strong negative is acceptable. The next run should stop and report a
bounded negative if:

- re-engagement passes but recovery fails again;
- recovery passes only by scheduled/prohibitively dense probing;
- cooling passes by false calm;
- second-shift re-openability fails.

The benchmark value comes from locating the bottleneck, not from forcing a
positive.

