# Pre-registration: Boundary Priors (Track 3)

Date committed: 2026-06-18 (before running the sweep)
Track: Experiment Track 3 — Boundary Priors (synthesis area #4; metric-stack §18)

## Breakthrough question

Is the self/world boundary in a minimal embodied agent an **evidentially fixed
fact** or a **prior that must be maintained and revised**? Operationally: when
the set of channels an agent can actually control changes, does adaptability
require a *plastic, removable* separation prior, or does a correct *fixed* prior
suffice?

This continues "There Is No Self-Evidence" (a finite agent cannot get evidence
for its self/world boundary as an independent fact) and Levin's TAME (selves are
plastic, multiscale, substrate-flexible), and it is the metric-stack paper's
named next direction (§18): make the **boundary location itself** the learned
object, not the mediated/exogenous split within a fixed boundary.

## Environment (minimal, hand-specified)

- `K` channels, each holding a bit `v_k in {0,1}`.
- Each channel has a hidden type `SELF` or `WORLD`. There are exactly
  `num_self` SELF channels.
- Per-channel target `t_k in {0,1}` (homeostatic setpoint).
- The agent has an **actuation budget** `C < num_self_plus_world`: it may
  actively set at most `C` channels per step. This embodiment constraint is
  what makes the boundary load-bearing — budget spent on an uncontrollable
  (WORLD) channel is wasted.
- Dynamics per step:
  - SELF channel, if actuated: `v_k <- a_k`. If not actuated: `v_k` persists.
  - WORLD channel: `v_k <- Bernoulli(p_world)` regardless of actuation
    (exogenous; action ignored).
- Reward per step: fraction of channels at target, `mean_k[v_k == t_k]`.
- **Boundary shift** at step `S`: the SELF/WORLD assignment is re-drawn
  (channels gain/lose controllability — tool attach/detach, limb loss). Targets
  unchanged. This is the metric-stack regime shift applied to the boundary.

## Agent and the prior

The agent maintains `b_k in [0,1]` = belief that channel `k` is SELF. Budget is
allocated to channels with high `b_k` that are currently off-target; a fraction
`epsilon` of steps probe uncertain channels. Control evidence on an actuated
channel: `signal = 1.0 if v_k(t+1) == a_k else 0.0` (SELF -> 1.0; WORLD -> ~0.5).

## Conditions

- `plastic` (POSITIVE): `b_k` updates from control evidence;
  `b_k <- b_k + lr*(signal - b_k)`. The prior is visible and removable.
- `fixed_self_correct` (CONTROL): `b_k` frozen at the TRUE initial assignment.
  Optimal pre-shift; the rigid prior is the thing under test.
- `fixed_all_self` (RED-TEAM SHORTCUT): `b_k = 1` for all channels — treat
  everything as controllable, never model a boundary. The strongest baseline
  that should almost work; if it ties `plastic`, knowing the boundary is useless.
- `fixed_all_world` (LOWER BOUND): `b_k = 0` — never confidently actuates.
- `random_prior` (CONTROL): `b_k` frozen at random values.
- `shuffled_evidence` (ANTI-CHEAT): `plastic` update rule, but the control
  signal is applied to a permuted channel index — attribution is broken.
  Tests whether recovery comes from genuine self/world attribution or from
  generic plasticity.

## Metrics (pre/post-shift windows)

- `mean_reward_pre`, `mean_reward_post`.
- `boundary_accuracy` = `mean_k[(b_k > 0.5) == (type_k == SELF)]`, pre and post.
- `criticality` proxy = variance of `b` across channels (poised vs. saturated).
- `belief_tracking_lag` = steps after shift until `boundary_accuracy >= 0.85`.

## Pre-registered gates (decided before running)

- **G1 (adaptability):** `plastic` post-shift reward exceeds `fixed_self_correct`
  post-shift reward by >= 0.05 in all 3 seeds.
- **G2 (re-tracking):** `plastic` `boundary_accuracy_post >= 0.85` in all 3 seeds.
- **G3 (attribution, not generic plasticity):** `shuffled_evidence` post-shift
  reward < `plastic` post-shift reward by >= 0.05, AND its
  `boundary_accuracy_post <= 0.65`, in all 3 seeds.
- **G4 (the boundary really moved):** `fixed_self_correct` has
  `boundary_accuracy_pre >= 0.9` but `boundary_accuracy_post <= 0.65` — its
  once-correct prior is wrong after the shift.

## Kill criteria (what would retract/weaken the claim)

- If `fixed_all_self` matches `plastic` post-shift (within 0.03), the
  "model the boundary" claim is **volume-dominated**: under this budget the
  boundary does not need to be represented.
- If `shuffled_evidence` recovers as well as `plastic`, recovery is from
  generic plasticity, not self/world attribution (G3 fails).
- If `fixed_self_correct` recovers post-shift on its own, the boundary did not
  meaningfully move (G4 fails) — environment misdesigned.

## Claim tier a pass earns

**Diagnostic** (the gate separates controls for distinct, named reasons). A
mechanism-tier claim would additionally require the plastic agent to *re-engage*
its boundary inference selectively (probe budget rises only after the shift),
mirroring the metric-stack's maintained-boundary signature; that is reported but
not gated in this pilot.
