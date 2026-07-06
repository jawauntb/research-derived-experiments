# Benchmark Card: Suite C Re-Engagement Under World Change

## Purpose

Test whether an agent that has learned to stop querying can reopen inquiry when
the world changes, then become quiet again only after the relevant
self/world attribution has recovered.

Suite C exists because final outcome recovery is too weak by itself. A model can
recover by over-probing, stay quiet because it has erased its own surprise
signal, or look stable while the causal attribution remains stale. The benchmark
therefore scores behavior together with inquiry, recovery, and no-false-calm
structure gates.

## Position In Causally Grounded Agents Benchmark

This benchmark is Suite C in the broader causally grounded finite agents
benchmark:

- Suite C: re-engagement under world change.
- Covered axes: behavior, inquiry, attribution, and anti-cheat controls.
- Partly covered axes: causal representation through self/world source heads.
- Not covered by this suite: long-horizon tool commitment, moved-slot hidden
  localization, broad structure-compatible OOD generalization, human/neural
  validation, and production reliability.

Use this card together with `docs/causally_grounded_agents_benchmark.md`,
`docs/causally_grounded_agents_release_schema.md`, and
`docs/publication_sharing_map.md`.

## Current Status

Suite C is packaged as a bounded positive result with a remaining recovery gap.

- Paper 22 established the failure: learned probe selection can self-silence
  after a regime shift. The agent stops asking exactly when its boundary has
  become stale.
- Paper 23A established the repair pressure: non-null prediction surprise
  re-engages probes after the shift, but the same mechanism over-fires and does
  not recover to the strict MAE threshold.
- Paper 23B established the best current mechanism: decision-layer cooling
  reduces post-shift anxiety, catches signal-layer false calm, and preserves
  second-shift re-openability.

Outcome: `bounded_positive_with_recovery_gap`.

The current public claim is not "Suite C is solved." The claim is that the
suite now has a reusable diagnostic shape and a strong partial positive:
decision-layer cooling is the right kind of repair, signal-layer surprise
suppression is a caught anti-cheat failure, and recovery/mediated-decomposition
remain the next empirical boundary.

## Primary Gates

| Gate | Requirement | Current result |
|---|---|---|
| C1. Silence replication | Learned current-replay probe has near-zero affected-bucket probes after a shift | Pass. Paper 23A reproduces the self-silencing baseline; the July 6 Modal report shows 0.0 affected post-shift nulls for `learned_scale_norm_current_replay`. |
| C2. Re-engagement | A candidate restores affected post-shift probe density and selects affected over unaffected buckets | Pass. Paper 23A headline reaches 137% of pre-shift affected density and 3.04x unaffected buckets; July 6 audit-floor and fast/slow probes restore nonzero affected post-shift nulls. |
| C3. Recovery | Re-engagement should pair with outcome recovery under the suite threshold or a preregistered oracle-relative threshold | Partial. Paper 23B improves recovery from 0/3 to 1-2/3 seeds for decision-layer variants, while `oracle_source` reaches 3/3. |
| C4. No false calm | A lower probe rate is valid only when attribution error falls too | Pass. `fixed_surprise_decrement` has low AUC but 0/3 recovery, so the gate correctly rejects direct surprise erasure. |
| C5. Cost-aware inquiry | The agent should avoid scheduled or always-probe solutions at comparable recovery | Partial. Decision-layer cooling reduces anxiety by 37-46% versus Paper 23A, but public JSONL rows and cost-normalized scorer are still a next implementation item. |
| C6. Re-openability | After a second shift, affected-bucket probes rise again above pre-second-shift density | Pass. Paper 23B reports 2.05x for `leaky_effort_integrator`, 1.81x for `decision_refractory`, and 2.18x for `burst_then_refractory`. |

## Anti-Cheat Controls

- `p22_learned_current_replay`: self-silencing lower baseline.
- `two_timescale_plus_prediction_error` / `p23a_surprise_no_cooling`: anxious
  re-engagement baseline.
- `fixed_surprise_decrement`: false-calm negative control.
- `scheduled_null_anchor`: high-cost positive control.
- `oracle_source`: semantic upper reference.
- `matched_random_time_budget`: random inquiry at matched probe count.

## Latest Accepted Result

- Suite C status report:
  `experiments/world_responds/results/suite_c_reengagement_2026_07_06.md`
- Machine-readable summary:
  `experiments/world_responds/results/suite_c_reengagement_2026_07_06.json`
- Paper 23A report:
  `experiments/world_responds/results/reengagement_23a_2026_07_06.md`
- Paper 23A PDF:
  `papers/probe_value_reengagement/paper.pdf`
- Paper 23B PDF:
  `papers/habituated_reengagement/paper.pdf`

## Failure Boundaries

Do not score Suite C as terminally passed unless a future run jointly satisfies:

1. re-engagement after learned quiet;
2. recovery under a justified threshold;
3. lower inquiry cost than scheduled or always-probe controls;
4. no false calm under signal-layer suppression controls;
5. second-shift re-openability.

The strongest remaining gap is a reusable Paper 23B runner that emits public
JSONL rows and a schema-valid summary directly from code rather than from the
paper-level result tables.

## Use

Use this suite when the question is whether an agent can keep its boundary
current over time: stop asking when saturated, ask again after the world
changes, and avoid mistaking silence for knowledge.

The existing Paper 23A Modal runner can reproduce the first re-engagement
search:

```bash
doppler --scope /Users/jawaun/superoptimizers run -- \
  uvx --python 3.12 --from modal modal run \
  experiments/world_responds/modal_world_responds_sweep.py \
  --mode paper23a \
  --seeds 20260610,1729,4242 \
  --n-episodes 500 \
  --eval-episodes 50 \
  --out artifacts/world_responds/reengagement_23a_v1.json \
  --report experiments/world_responds/results/reengagement_23a_2026_07_06.md
```

Paper 23B evidence is currently preserved in
`papers/habituated_reengagement/paper.md` and
`papers/habituated_reengagement/paper.pdf`; the next code hardening step is to
turn that sweep into a first-class `experiments/world_responds` runner with
JSONL rows.

## Non-Claims

This suite does not certify consciousness, general autonomous reliability,
human habituation, neural validity, or hidden-state localization. It is a
finite diagnostic for adaptive inquiry under nonstationary causal structure.
