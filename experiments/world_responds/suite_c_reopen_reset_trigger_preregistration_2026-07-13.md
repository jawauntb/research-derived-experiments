# Suite C Reopen-as-Plasticity-Reset-Trigger — Pre-registration (M5)

**Frozen: 2026-07-13 (UTC)**, before implementation or execution of any M5 arm.
The existing Suite C implementation is
`experiments/world_responds/suite_c_reengagement.py`, extended by the M4
factorial harness `experiments/world_responds/suite_c_factorial_ablation.py`;
this addendum reuses those harnesses and does not replace them.

## Current frame and question

M4 (`experiments/commitment_surface/results/m4_suite_c_factorial_ablation_2026_07_09.md`)
ran the 2^3 `allocate × cool × reopen` factorial over the anti-Goodhart loop
`detect → allocate → saturate → cool → reopen` and found that **only `reopen`**
(re-engaging probing/learning after a detected world change) is necessary for
the terminal criterion: reopen main effect `+1.000` (CI `[+1.000, +1.000]`),
`allocate` and `cool` behaviorally null. Reopen is therefore the load-bearing
primitive.

The continual-learning literature fights loss of plasticity with reset /
regeneration mechanisms: continual backprop / utility-based unit resets
(Dohare et al., *Nature* 2024; arXiv:2404.00781), self-normalized resets
(arXiv:2410.20098), and regenerative regularization (arXiv:2308.11958). All
key the reset to **internal statistics** (unit utility, age, activation norm)
or to a **fixed schedule**. Suite C's `reopen`, by contrast, keys re-engagement
to a detected **commitment-surface change** in the external world.

Question: is Suite C's commitment-triggered `reopen` a *better plasticity-reset
criterion* than utility-based / self-normalized / periodic resets — i.e., does
re-opening keyed to a detected commitment-surface change beat resets keyed to
internal statistics on latency and specificity, holding everything else
identical?

## Competing explanations

- **H_internal-statistic-reset-suffices:** re-engagement is driven by internal
  drift signals; a utility/age reset (T_util), a self-normalized reset (T_norm),
  or a periodic reset (T_periodic) re-engages as fast and as specifically as the
  commitment-change trigger, so the external commitment signal adds nothing.
- **H_commitment-change-trigger-is-better:** re-engagement quality depends on
  keying the reset to a *detected external commitment-surface change*; the
  commitment trigger (T_commit) re-engages at least as fast, and is strictly
  more specific (lower false-reopen on no-change), than every internal-statistic
  trigger.

## Assumption ledger

- **Load-bearing assumption:** among reset triggers with matched budget, the
  *trigger criterion* (what decides WHEN to reopen) is the only degree of
  freedom that matters; magnitude, allocation, and cooling are held fixed.
- **Measurement assumption:** the existing row-level terminal criterion is the
  outcome, `reengagement_pass ∧ recovery_pass ∧ no_false_calm ∧ reopen_pass`;
  no new success metric replaces it. Specificity is measured by a false-reopen
  rate on the no-change / false-calm control.
- **Inherited assumption:** `burst_then_refractory` is a finite diagnostic
  harness, not a neural, biological, consciousness, or production model.
- **Independence assumption:** seeds are paired blocks; contrasts and bootstrap
  intervals resample seeds.
- **Anti-cheat assumption:** matched per-seed probe budgets and the transported
  C1–C6 + false-calm controls remain in the run, so budget alone cannot buy a
  win.

## Frozen design

### Harness and seeds

Reuse the deterministic Suite C `burst_then_refractory` workflow unchanged:
`SuiteCConfig` at 72 steps, shifts at 24 and 48, same affected/unaffected
buckets, same C1–C6 thresholds. Freeze **detect ON** and **saturate ON** exactly
as M4. Freeze **allocate=0** and **cool=0** (M4 showed both null; fixing them
removes confounds and isolates the trigger). Eight paired seeds, matching M4:

`[20260709, 20261712, 20262715, 20263718, 20264721, 20265724, 20266727, 20267730]`.

SHA-256 namespacing: any per-arm sub-stream is derived as
`int.from_bytes(sha256(f"{seed}:{arm}:{stream}".encode()).digest()[:8], "big")`
so arms are decorrelated but reproducible from the frozen seed list.

### Trigger arms (the ONLY thing that varies)

Everything except the reopen/reset trigger is byte-identical across arms.
The trigger decides WHEN the closed probe-action commitment is re-armed.

- **T_commit:** reopen on the Suite C detected commitment-surface change (the
  M4 `reopen` signal on the intervention-pinned second world shift).
- **T_util:** continual-backprop-style utility/age reset — re-arm when a running
  unit-utility × age statistic crosses a frozen threshold (internal statistic).
- **T_norm:** self-normalized reset — re-arm when the self-normalized activation
  drift statistic crosses a frozen threshold (internal statistic).
- **T_periodic:** fixed-schedule reset — re-arm every `P` steps regardless of the
  world (naive baseline). `P` frozen to the mean inter-shift interval (24).
- **T_none:** never reopen (floor; expected 0/8 by M4).

All trigger thresholds are frozen from the M4 dynamics **before** any M5 cell is
run; post-hoc retuning is forbidden (see rejected alternatives).

### Matched budget and preserved controls

Each arm receives the same per-seed probe budget as T_commit (the M4 matched
per-seed budget); budgets are exact-matched per seed and asserted in F0. Rerun
the unmodified reference suite on the same seeds with all existing conditions
(`p22_learned_current_replay`, `two_timescale_plus_prediction_error`,
`fixed_surprise_decrement`, `scheduled_null_anchor`, `oracle_source`, the three
decision-layer candidates, `matched_random_time_budget`) and the false-calm
control, exactly as in M4. Existing 2026-07-09 artifacts are immutable; M5
outputs use new 2026-07-13 paths.

## Frozen metrics (per arm, over paired seeds)

- **terminal pass rate** — fraction of 8 seeds passing the row-level criterion.
- **re-engagement latency** — steps from the second world change to first
  affected-bucket probe (lower is better).
- **selectivity** — affected vs unaffected post-shift probe density ratio.
- **reopen ratio** — second-shift affected probe rise (C6 quantity).
- **final MAE** — final affected-component attribution error.
- **probe cost** — total probes (must equal the matched budget).
- **false-reopen rate** — fraction of the no-change / false-calm control window
  in which the trigger fires when the world did NOT change (lower is better).

Report per-arm point estimates and 95% paired percentile bootstrap intervals
from 10,000 seed resamples, RNG seed 20260713. Intervals are uncertainty
summaries, not p-values.

## Frozen analysis and strict gates (kill criteria)

- **F0 — integrity + matched budgets + transported controls:** all arms present
  for all 8 seeds; reruns byte-stable; every arm's per-seed probe cost exactly
  equals the T_commit matched budget; reference C1–C6 suite PASS;
  `fixed_surprise_decrement` remains rejected by no-false-calm; matched-random
  remains less selective than the headline at its per-seed budget. (As M4 F0/F6.)
- **F1 — T_commit terminal pass 8/8:** T_commit terminal pass rate is `1.000`
  (8/8). Anything less is a strict failure.
- **F2 — latency dominance:** T_commit median re-engagement latency is `≤` that
  of each internal-statistic trigger (T_util, T_norm, T_periodic) by a frozen
  margin of at least 1 step, per paired-seed contrast.
- **F3 — specificity:** T_commit false-reopen rate on the false-calm / no-change
  control is strictly below that of every internal-statistic trigger by a frozen
  margin of at least 0.10. A good trigger fires on real commitment change, not
  internal drift.
- **F4 — joint non-domination:** no internal-statistic trigger dominates
  T_commit on the joint `(latency, false-reopen)` point — i.e., no arm is
  simultaneously `≤` T_commit on latency AND `≤` T_commit on false-reopen. Any
  such Pareto-dominating arm is a strict failure.
- **F5 — floor sanity:** T_none terminal pass rate is `0.000` (0/8), confirming
  the harness still requires reopening.

**Strict verdict:** PASS only if F0–F5 all pass. Otherwise FAIL. The strict
verdict is determined ONLY by the frozen gates; no directional or post-hoc
near-pass upgrades it. Failures stay failures even if T_commit wins on some
unlisted metric. This is finite-harness diagnostic evidence, not neural or
external continual-learning validation. No post-hoc threshold retuning.

## Discriminating predictions

- H_commitment-change-trigger-is-better predicts F1–F5 all pass: T_commit passes
  8/8, is no slower than every internal-statistic trigger, is strictly more
  specific on the no-change control, and is Pareto-undominated.
- H_internal-statistic-reset-suffices predicts at least one internal-statistic
  trigger matches T_commit on latency AND matches-or-beats its false-reopen rate
  (fails F3/F4), or that T_periodic re-engages while over-firing on no-change
  (high false-reopen, isolating specificity as the real axis).

## Claim boundary

A PASS supports only a **diagnostic finite-harness claim** that, in the Suite C
world, a reopen trigger keyed to a detected commitment-surface change is a
better plasticity-reset criterion (faster and more specific) than utility-based,
self-normalized, or periodic resets keyed to internal statistics. It does **not**
establish superiority in neural continual learning, does not certify the
commitment trigger against learned reset heuristics in deep nets, and does not
transport outside Suite C. A FAIL downgrades the "commitment-trigger-is-better"
wording to a hypothesis and names the surviving internal-statistic trigger as
the next mechanistic target.

## Rejected alternatives (pre-run)

- A new toy state machine was rejected because it would not test the existing
  Suite C world-change dynamics that M4 established `reopen` on.
- The neural-transfer Suite C workflow was rejected here because it changes both
  policy learning and reset semantics; a clean trigger-only intervention comes
  first. Neural transport is a later test, not a substitute for this one.
- Unpaired / aggregate-only reporting was rejected; paired per-seed rows are
  required so latency and false-reopen contrasts are within-seed.
- Post-hoc tuning of trigger thresholds (T_util utility/age cutoff, T_norm
  normalization threshold, T_periodic period) after observing cells is forbidden;
  all thresholds are frozen from M4 dynamics before any M5 cell runs.
- Dropping the false-calm / no-change control was rejected: without it there is
  no specificity axis, and a trigger that always fires would look latency-optimal
  while being useless. F3/F4 depend on it.
