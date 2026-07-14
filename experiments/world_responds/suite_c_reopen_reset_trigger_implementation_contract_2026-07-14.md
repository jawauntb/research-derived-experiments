# M5 Reopen-Trigger Pre-Run Implementation Contract

**Frozen:** 2026-07-14T05:08:45Z, before execution of any M5 outcome or
false-calm cell.

This contract repairs operational gaps in the frozen M5 preregistration without
changing its question, arms, seeds, margins, or strict gates. The source
preregistration is
`suite_c_reopen_reset_trigger_preregistration_2026-07-13.md`, SHA-256
`91396da66d24889d2c9dc224b2c2ede13aaa115ce7339bdc5b66f39a46bb74ed`.
The immutable source revision is
`9e5e218a2efbcd726d0d9555d34c2292e886f72a`.

## Why a clarification is required

The preregistration names `T_util` and `T_norm` but does not specify their
statistics, update order, crossing direction, or numerical threshold
derivation. It also requires exact equality of actual probe counts while
allowing `T_none` never to reopen, which the existing adaptive probe policy
cannot guarantee without a common budget rule. Finally, an impulse-count
definition of false reopening would cap the periodic arm at `1/12`, making the
frozen `0.10` specificity margin mathematically impossible. No M5 outcome was
inspected when these gaps were identified or repaired.

## Frozen causal order

At each step `t`:

1. Apply the environment transition, if any.
2. Update trigger-observable state from the pre-action state.
3. Evaluate exactly one trigger edge.
4. If the commitment is closed and the trigger fires, open it for the current
   step plus the next seven steps.
5. Consume the step's frozen probe tokens and update the Suite C state.
6. Update post-action utility state for step `t + 1`.

An edge while the commitment is already open does not restart or extend the
eight-step window. All arms receive the ordinary first-shift opening at `t=24`;
the varied trigger governs subsequent reopening. `T_commit` receives the
detected external event only when a real shift is applied.

## Frozen trigger definitions

- **`T_commit`** fires on the existing detected commitment-surface change at
  the real second shift. It does not fire in the coupled no-change run.
- **`T_periodic`** fires when `t > 0` and `t mod 24 == 0`.
- **`T_none`** never fires after the common first-shift opening.
- **`T_util` (`utility_age_obsolescence`)** maintains per-bucket utility
  `u_b=0` and age `a_b=0`. After a probe, let
  `q_b=max(e_before-e_after,0)/max(e_before,1e-12)`; without a probe, `q_b=0`.
  Update `u_b <- 0.95*u_b + 0.05*q_b`, and set `a_b <- 0` when `q_b>0`, else
  `a_b <- a_b+1`. Before the next action,
  `s_util=max_b a_b*(1-u_b/u_scale)`, where `u_scale` is the maximum positive
  calibration utility. This explicitly operationalizes the preregistration's
  directionally ambiguous “utility × age” phrase as low-utility obsolescence
  times age, matching the stated continual-backprop motivation.
- **`T_norm`** uses the deterministic internal activation proxy already present
  in Suite C, `x_b=0.72*surprise_b+0.38*error_b`, excluding fresh score noise.
  With per-bucket calibration median `m_b` and robust scale
  `d_b=max(1e-6,1.4826*median(|x_b-m_b|))`, define
  `s_norm=max_b |x_b-m_b|/d_b`. All six buckets are included so the trigger
  cannot use the known affected-bucket labels.

`T_util` and `T_norm` fire only on a rising crossing: current score strictly
above its threshold and previous score at or below it. A score that remains
high cannot repeatedly retrigger.

## Outcome-blind calibration

Calibration replays only the existing full-on M4 reference dynamics for the
eight frozen paired seeds and observes only pre-first-shift steps `12..23`.
It is a shadow read: it cannot change probes or learning.

- `u_scale` is the maximum positive utility observed in that window.
- `m_b` and `d_b` are fit from that window.
- Each threshold is `nextafter(max calibration score, +infinity)`.

Thus neither trigger fires in calibration, and neither threshold is selected
from a response to either known shift. The calibration receipt must record the
numeric values, inputs, source revision, and SHA-256 before any M5 outcome or
no-change cell is run. No threshold search or replacement is permitted after
that receipt exists.

## Exact matched-probe rule

For each seed, the budget `B_seed` is the actual probe count of the immutable
M4 cell `allocate=0, cool=0, reopen=1`. A common probe plan is constructed
before arm execution from that reference cell's ordered `(t,bucket)` probe
slots. Every M5 arm consumes exactly those `B_seed` tokens.

At a token whose reference bucket is affected:

- if the commitment is open, probe that affected bucket;
- if closed, probe a deterministic unaffected fallback bucket chosen by
  SHA-256 namespace `seed:m5:closed-fallback:t:reference_bucket`.

Reference tokens on unaffected buckets remain unchanged. Therefore actual
probe counts—not merely allocated quotas—are exactly equal across arms, while
a closed arm cannot obtain affected-bucket learning through filler probes.
The plan ID, reference budget, routed bucket, and open/closed state are retained
in the ignored raw artifact. Arm execution order cannot alter the plan.

This common routing controller is the pre-run operational meaning of “holding
everything except the trigger identical.” It is applied to all five arms and
is not chosen from M5 results.

## Frozen metrics and counterfactual

- The latency window is `t=48..59`. Per-seed latency is the first actual
  affected-bucket probe minus 48; no probe is right-censored to 12.
- F2 uses the paired per-seed contrast
  `latency_internal-latency_commit`; its point gate passes when the median is at
  least one step for each internal trigger. Bootstrap intervals are summaries.
- The false-calm run is coupled to the outcome run. At `t=48`, draw and discard
  the same shift random variates but do not apply the error/surprise jump; keep
  downstream RNG alignment. `T_commit` receives no change event.
- False-reopen rate is the fraction of the 12-step window `48..59` for which
  the commitment is open. This measures the active cost of a false reset; an
  eight-step periodic reset therefore occupies `8/12`, rather than being
  misrepresented as a single `1/12` impulse.
- F4 uses each arm's median latency and mean false-reopen occupancy.
- One shared `10,000 × 8` paired bootstrap index matrix, RNG seed `20260713`,
  is used for every arm and metric.

The transported reference C1–C6 suite and its existing fixed-surprise and
matched-random controls remain byte-unchanged and separate from this new
second-shift no-change counterfactual.

## Fail-closed rules

- Any mismatch in plan IDs, actual per-seed probe counts, seeds, arm coverage,
  reference controls, calibration receipt, or byte-identical rerun fails F0.
- Thresholds, formulas, routing, censoring, and occupancy cannot be changed
  after calibration or outcome execution.
- The original preregistration and this repair remain side by side. Reporting
  must call out the repair; it may not describe the missing details as if they
  had been present on 2026-07-13.
- PASS still requires the original F0–F5 gates without directional upgrades.

## Calibration receipt

Frozen at **2026-07-14T05:13:04Z**, before any M5 outcome or false-calm cell.
The committed calibration artifact is
`suite_c_reopen_reset_trigger_calibration_2026_07_14.json`, file SHA-256
`7e62142b8a8efdd57176c6d5255ee6439941d951b4d9a5a20825d9198c3d58b9` and
canonical receipt SHA-256
`741efa930978a0de622b4fbea4deed82e250535b0b0b37ecaf3f9043136d992b`.

- `u_scale = 0.0320439394807567`
- `max(s_util) = 17.354255196499498`
- `theta_util = 17.3542551964995`
- `max(s_norm) = 3.690618751503418`
- `theta_norm = 3.6906187515034183`
- robust activation medians:
  `[0.16827199894389155, 0.14641468947966987, 0.16628676011780996,
  0.13337825154254845, 0.1348125508633118, 0.13641534038341346]`
- robust activation scales:
  `[0.01736078331866432, 0.012419370363202372, 0.014501740597921729,
  0.010872194095393136, 0.011134091126949228, 0.013972995237701919]`

No further calibration, threshold change, or alternative statistic is allowed.
