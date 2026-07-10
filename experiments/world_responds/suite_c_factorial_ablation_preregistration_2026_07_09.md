# Suite C Allocate × Cool × Reopen Factorial — Follow-up Pre-registration

**Frozen:** 2026-07-09T21:38:40-04:00, before implementation or execution of the
factorial cells.  The existing Suite C implementation is
`experiments/world_responds/suite_c_reengagement.py`; this addendum extends that
harness and does not replace it.

## Current frame and question

The commitment-surface paper compresses the correction chain as
`detect → allocate → saturate → cool → reopen` and conjectures that
`{allocate, cool, reopen}` is the load-bearing subset in Suite C. Existing
Suite C evidence establishes re-engagement for complete decision-layer
policies, but does not isolate these three stages factorially.

Question: in the existing two-world-shift Suite C workflow, does removing each
of allocate, cool, or reopen break the existing row-level world-change
re-engagement criterion, and are the corresponding factorial main effects and
interactions consistent with complementary rather than substitutable stages?

## Assumption ledger

- **Load-bearing assumption:** each of allocate, cool, and reopen is necessary
  in the context of the other two.
- **Measurement assumption:** the existing row-level terminal criterion is the
  relevant outcome: `reengagement_pass AND recovery_pass AND no_false_calm AND
  reopen_pass`. No new success metric will replace it.
- **Inherited assumption:** the hand-specified `burst_then_refractory` policy is
  a valid finite diagnostic harness, not a neural, biological, consciousness,
  or production-agent model.
- **Independence assumption:** seeds are paired blocks, not independent cells;
  contrasts and bootstrap intervals resample seeds.
- **Anti-cheat assumption:** changing probe volume alone is insufficient, so
  the existing matched-random, scheduled, oracle, anxious, silence, and
  false-calm controls remain in the run.

## Anomaly map and candidate reframe

The anomaly is that M4 currently infers component necessity from comparisons
across different historical policies. A complete policy can pass while one of
its named conceptual stages is redundant inside the actual Suite C dynamics.
The severe reframe is therefore component-level: retain one real policy and
intervene only on its three named action gates.

## Frozen design

### Harness and seeds

Run the existing deterministic Suite C simulator for eight paired seeds:

`[20260709, 20261712, 20262715, 20263718, 20264721, 20265724, 20266727, 20267730]`.

Use `SuiteCConfig` unchanged: 72 steps, shifts at 24 and 48, the same affected
and unaffected buckets, and the same C1–C6 thresholds. Eight seeds exceed the
requested minimum of five.

### 2^3 cells

The base policy is the existing `burst_then_refractory` candidate. Cross three
binary interventions, producing all eight cells per seed:

- **allocate=1:** shift-triggered burst budget is assigned only to the existing
  concern-relevant affected buckets. **allocate=0:** the same burst quota is
  assigned uniformly to all buckets; detection and quota size are unchanged.
- **cool=1:** retain the existing post-burst three-step decision refractory
  period. **cool=0:** remove only that refractory gate.
- **reopen=1:** the second intervention-pinned world shift re-arms the burst.
  **reopen=0:** the second shift remains detected in error/surprise state, but
  cannot reopen the closed probe-action commitment.

Two stages are frozen on in every cell:

- **detect:** the existing error/surprise residual, score noise, and world-shift
  state updates are unchanged.
- **saturate:** the existing eight-probe burst quota and its consumption rule
  are unchanged.

The all-on cell must reproduce the unmodified `burst_then_refractory` row
exactly on all pre-existing fields for every seed.

### Preserved controls

Run the unmodified reference suite on the same seeds with all existing
conditions: `p22_learned_current_replay`,
`two_timescale_plus_prediction_error`, `fixed_surprise_decrement`,
`scheduled_null_anchor`, `oracle_source`, all three decision-layer candidates,
and `matched_random_time_budget`. The matched-random budget remains paired to
the reference suite's selected headline condition, exactly as in the existing
workflow. Existing result artifacts dated 2026-07-06 are immutable; follow-up
outputs use new 2026-07-09 paths.

## Outcomes and factorial estimands

Primary binary outcome `Y` is the existing row-level terminal criterion:
`reengagement_pass ∧ recovery_pass ∧ no_false_calm ∧ reopen_pass`.
Secondary outcomes are the unchanged first re-engagement ratio, first
selectivity ratio, second reopen ratio, final affected-component MAE, total
probes, and no-false-calm indicator.

For factor levels coded `x ∈ {-1,+1}`, estimate each effect as
`2 * mean(product(x_j) * Y)` over the balanced eight cells and paired seeds.
This yields three main effects, three two-way interactions, and one three-way
interaction. Report the same contrasts for all secondary outcomes. Report
95% paired percentile bootstrap intervals from 10,000 seed resamples with RNG
seed 20260709. These intervals are uncertainty summaries, not p-values.

## Pre-registered gates and kill criteria

- **F0 — integrity:** 64 factorial rows are present; every seed has all eight
  cells; rerunning is byte-stable; the all-on cell exactly matches the existing
  base-policy rows on pre-existing fields.
- **F1 — full-loop replication:** all-on terminal pass rate is at least 0.75
  (at least 6/8 seeds).
- **F2 — single-removal necessity:** for each factor, its single knockout with
  the other two on has terminal pass rate at most 0.25 (at most 2/8), and the
  paired all-on-minus-knockout pass-rate difference is at least 0.50.
- **F3 — main effects:** each terminal-pass main effect is at least +0.20 and
  its paired-bootstrap 95% lower bound is strictly above zero.
- **F4 — interactions:** all three pairwise and the three-way terminal-pass
  contrasts must be estimable and reported. The complementarity prediction is
  that none is negative at the point estimate; any negative interaction is a
  strict failure of this gate. Intervals may include zero because eight paired
  seeds are not powered for interaction significance.
- **F5 — no interaction rescue:** every cell missing at least one of the three
  factors has terminal pass rate at most 0.25. A high-performing reduced cell
  falsifies the claimed load-bearing subset even if marginal main effects are
  positive.
- **F6 — transported controls:** the unmodified reference suite still passes
  C1–C6; `fixed_surprise_decrement` remains rejected by no-false-calm; the
  matched-random control remains less selective than the selected headline at
  its per-seed matched probe budget.

**Strict verdict:** PASS only if F0–F6 all pass. Otherwise FAIL; no directional
or post-hoc near-pass can upgrade it.

## Discriminating predictions

- M4 predicts F1–F6 pass: each named stage has a positive main effect, each
  single removal kills terminal re-engagement, and no reduced interaction cell
  rescues the criterion.
- The redundancy alternative predicts at least one single knockout retains the
  terminal criterion and therefore fails F2/F5, even if the complete loop and
  historical controls still pass.
- The proxy-volume alternative predicts matched-random or allocate-off probing
  can match selective re-engagement, violating F6 or F5.

## Rejected alternatives (pre-run)

- A new toy state machine was rejected because it would not test the existing
  Suite C/world-change dynamics.
- The neural-transfer Suite C workflow was rejected for this first ablation
  because it changes both policy learning and component semantics; it is a
  later transport test, not a clean component intervention.
- Three one-factor ablations without the other five cells were rejected because
  they cannot estimate interactions or expose rescue.
- Aggregate-only runs were rejected; paired per-seed rows are required.
- Retuning thresholds after observing cells is forbidden.

## Claim boundary and next test

A PASS supports only a **diagnostic finite-harness causal-ablation claim** that
allocate, cool, and reopen are jointly necessary in this implementation. It
does not establish the decomposition in learned neural policies or outside
Suite C. A FAIL downgrades M4's strong load-bearing-subset wording to a
compression hypothesis and identifies the surviving knockout as the next
mechanistic target. The next transport test is to apply the same frozen
component interventions to the existing neural/teacher-free Suite C workflow
without changing these gates.
