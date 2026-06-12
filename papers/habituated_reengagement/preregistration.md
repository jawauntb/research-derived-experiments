# Paper 23B — Pre-Registration

**Title (working):** Habituated Re-Engagement: Post-Probe Cooling Stabilizes Autonomous Identifying Interventions

**Frozen:** 2026-06-12, before any Modal sweep runs.

## Question

Paper 23A introduced a non-null prediction-error boost that broke the self-silencing trap from Paper 22 (G4 ✓ strongly: post-shift affected null density 137% of pre-shift, 3.04× of unaffected buckets). But the same mechanism produced **anxiety**: the headline `two_timescale_plus_prediction_error` never recovered MAE ≤ 0.10 in any seed (0/3), and post-shift null rate was *higher* than pre-shift.

The diagnosis: the mechanism has three subproblems, the first two solved and the third missing.

| Subproblem | Status |
|---|---|
| 1. Detect world change | ✓ (from non-null surprise) |
| 2. Allocate probes | ✓ (V_probe + shift signal) |
| **3. Saturate after sufficient identification** | **✗ — missing** |

Paper 23B isolates (3). **The critical conceptual constraint**: cooling should NOT erase the surprise signal. Surprise is the agent's correct read of "the world is unpredictable here." If we suppress it, the agent loses its detection capacity. Instead, cooling should reduce the *action tendency* — the surprise stays informational, but recent probe effort temporarily reduces the agent's propensity to probe further.

This is habituation, not denial.

## Core mechanism

Two separate per-bucket per-dim state variables:

```
raw_surprise[b, d]      — EMA of |signed residual| on non-null actions (P23A's surprise term)
probe_effort[b, d]      — leaky integrator of recent null counts
```

Probe score (decision layer):

```
probe_score[b, d] =
    base_vprobe[b, d]
  + λ_shift   · shift_signal[b, d]
  + λ_surprise · raw_surprise[b, d]
  − β · probe_effort[b, d]
```

Equivalent threshold-layer formulation (for refractory variants):

```
effective_threshold[b, d] = τ[d] · (1 + λ_cool · probe_effort[b, d])
take_null = probe_score[b, d] > effective_threshold[b, d]
```

## Five cooling variants (the factorial)

| Variant | Mechanism | Risk |
|---|---|---|
| `fixed_surprise_decrement` | `raw_surprise[b, d] -= Δ` when null taken in (b,d). Signal-layer cooling. | May hide real surprise |
| `info_gain_surprise_decrement` | `raw_surprise[b, d] -= η · probe_value_estimate`. Signal layer, info-proportional. | Better, still edits signal |
| `decision_refractory` | Surprise unchanged; raise threshold after recent probes. Decision-layer. | Conceptually safest |
| **`leaky_effort_integrator`** | **HEADLINE.** Surprise unchanged; subtract β·effort in score. ρ=0.93 decay per step. | Main candidate |
| `burst_then_refractory` | Allow N=20 probes per bucket post-shift, then cooldown window of 25 episodes | Cleanest Goldilocks |

ρ for leaky integrator: 0.93. β: 1.0. Δ for fixed decrement: 0.5. η for info-gain: 0.5. Cooldown window for burst_then_refractory: 25 episodes after N=20 affected-bucket probes.

## Second regime shift

Carry P23A env (κ=0.60) but add a **second regime shift** at episode 400:

- Episodes 0–249: trigger = "food"
- Episodes 250–399: trigger = "medicine"  (first shift, as P23A)
- Episodes 400–500: trigger = "food" again (second shift, tests re-openability)

This lets G10 test the *maintained-boundary* pattern:
> quiet → alarm → probe burst → cool → quiet → alarm again → probe → cool

Without the second shift, a heavy cooldown could pass by creating permanent suppression.

## Carried from P23A (unchanged)

- Three-head architecture (direct_self + mediated_world + exogenous_world)
- Two-timescale V_probe (fast EMA α=0.25 + slow EMA α=0.05 + shift signal margin 0.02)
- Non-null prediction-error EMA (α=0.10) — kept as P23A
- λ_shift=2.0, λ_surprise=1.0 (unchanged)
- Online rollout + warmup + ε-greedy + action-stratified SGD + scale-norm current_replay V_probe
- κ=0.60

## New: mediated/exogenous causal contrast (G8 from P23A, now tested)

At end of training, for each (item, role) compute:

- `world_pred_HIGH_HAZARD` = world_head(z, ff, hist with full trigger consumption signature)
- `world_pred_LOW_HAZARD` = world_head(z, ff, hist with zero trigger consumption)
- **mediated_world = world_pred_HIGH − world_pred_LOW**
- **exogenous_world = world_pred_LOW**

Compare to true mediated (HAZARD_AMP · h_max · SHOCK_E_MAG) and true exogenous (BASE_SHOCK_E · SHOCK_E_MAG). Report per-component MAE.

## Improved oracle (diagnostic, not headline)

`recent_keff_probe_value_oracle`:
```
K_eff(b) = sum_{recent null obs in b} exp(−age / τ_decay)   where τ_decay = 80 steps
probe_value(b) = current_error²(b) / (K_eff(b) + 1)
```

This makes the oracle regime-aware: samples from before the regime shift count less, properly reflecting that they're from the wrong distribution.

## Conditions (10)

| Condition | Purpose |
|---|---|
| `p22_learned_current_replay` | Self-silencing baseline |
| `p23a_surprise_no_cooling` | Anxiety baseline (P23A headline) |
| `fixed_surprise_decrement` | Simple signal-layer cooling |
| `info_gain_surprise_decrement` | Info-proportional signal cooling |
| `decision_refractory` | Threshold-layer cooling |
| **`leaky_effort_integrator`** | **HEADLINE** — decision-layer leaky integrator |
| `burst_then_refractory` | Strong Goldilocks controller |
| `scheduled_null_anchor` | Positive control |
| `oracle_source` | Semantic upper bound |
| `recent_keff_probe_value_oracle` | Improved oracle (diagnostic) |

3 seeds × 10 = 30 Modal cells.

## Sanity checks (one seed, before full sweep)

Run `leaky_effort_integrator` at seed 20260610. Require all:

1. Two-timescale + surprise mechanism is intact (raw_surprise EMA is non-trivial after some non-null surprise)
2. probe_effort is non-zero after the first probe burst, decays after probe stop
3. Post-first-shift probe burst is visible (affected-bucket null rate rises within 25 episodes)
4. Post-first-shift probe rate falls BELOW its peak by episode 400 (cooling works)
5. Post-second-shift (ep 400+) probe rate rises again (re-openability)
6. Anchor losses still recover scheduled attribution (sanity check on training pipeline)

If any fail, fix and rerun.

## Pre-registered gates (frozen)

| Gate | Criterion |
|---|---|
| **G1 — P23A anxiety replication** | `p23a_surprise_no_cooling` shows high post-shift nulls AND fails to recover in 0–1/3 seeds |
| **G2 — Re-engagement preserved** | Headline reaches affected/unaffected probe ratio ≥ 3× in early post-first-shift window (ep 250–275) |
| **G3 — Anxiety suppressed** | Headline post-first-shift affected-bucket null rate drops below 80% of its peak by episode 400 |
| **G4 — Recovery improves** | Headline post-shift AUC ≥ 30% better than P23A headline's 11.19 (target ≤ 7.85) |
| **G5 — Time-to-recover** | ≥ 2/3 seeds reach MAE ≤ 0.10 by episode 425, OR headline reaches ≥ 80% of oracle_source AUC |
| **G6 — No false calm** | Probe rate drop is matched by raw surprise drop AND component MAE drop. Specifically: if post-shift probe rate falls from peak by X%, raw surprise must fall by ≥ X/2%, AND component MAE must fall by ≥ X/3%. Cooling alone cannot count as success. |
| **G7 — Probe efficiency** | Headline uses fewer total nulls than P23A headline AND no more than 1.2× of oracle_source's ~705 affected post-shift nulls |
| **G8 — Mediated/exogenous identifiability** | Causal contrast: mediated_world MAE ≤ 0.10 AND exogenous_world MAE ≤ 0.10 |
| **G9 — Viability preserved** | Return ≥ 90% of scheduled or oracle |
| **G10 — Re-openability** | Post-second-shift (ep 400+) headline affected-bucket null rate is ≥ 50% of the early post-first-shift peak. Cooldown must not be permanent. |

## Pre-registered interpretation matrix

| Result pattern | Interpretation |
|---|---|
| Headline passes G3 + G4 + G6 + G10 | **Strong positive.** Stable re-engagement + re-openability achieved. First maintained self/world boundary in the program. |
| G3 passes but G6 fails | False calm: cooling silenced agent without resolving attribution. Mechanism cheats. |
| G3 passes G6 passes but G10 fails | Cooldown became permanent suppression; agent learned helplessness. |
| `decision_refractory` works but `fixed_surprise_decrement` fails | Surprise magnitude itself wasn't the problem; action regulation needed habituation. |
| `fixed_surprise_decrement` works but `decision_refractory` fails | Surprise signal was over-firing; signal-layer suppression sufficed. |
| `burst_then_refractory` wins | Explicit Goldilocks controller beats continuous damping. |
| `leaky_effort_integrator` wins | Continuous habituation beats discrete burst-and-cool. |
| All cooling variants fail G6 | Cooling mechanisms generally cheat by silencing without resolving. Move to different architecture (Paper 24 cross-fit). |
| G8 fails (mediated/exogenous not identifiable) | Three-head architecture has internal gauge symmetry; need explicit contrast training. |

## What success looks like

The pattern we want to see in one cell trace:

```
ep 1-249 (regime A):     low non-null surprise → low probes → MAE drops
ep 250 (shift 1):        non-null surprise rises in food/medicine buckets
ep 250-275:              probes burst in affected buckets (re-engagement)
ep 275-350:              probe_effort builds up → threshold rises → probes slow
ep 350-400:              MAE recovers; raw surprise also drops as world model adapts; probes drop accordingly (no false calm)
ep 400 (shift 2):        non-null surprise rises again
ep 400-425:              probes re-engage despite recent cooldown (re-openable)
ep 425-500:              probes again cool down after re-identification
```

That is the "**maintained self/world boundary**" pattern. It is the first version of:

> An agent that knows when to ask, when to stop asking, and how to ask again — without forgetting how to ask.

## Pre-committed continuation

If headline passes G3 + G4 + G6 + G10:
- **Paper 24**: learned bucket discovery (replace hand-defined role × E_bin × D_bin with encoder-derived clustering) OR same-step action correlation.

If G6 fails (false calm):
- **Paper 24-alt**: cross-fit V_probe (P19 escalation). The mechanism may be self-confirming.

If G8 fails (mediated/exogenous not identifiable):
- **Paper 24-mediated**: explicit interventional contrast training. Add a "compare null at high-h vs low-h history" loss to disambiguate.

## External literature framing

Add for Paper 23B:
- **Habituation** in cognitive neuroscience: how biological systems dampen response to repeated stimuli without losing the underlying detection
- **Refractory periods** in neural firing: temporary suppression after activation
- **Adaptive thresholds** in change-point detection: CUSUM with reset
- **Active inference / Friston**: precision tuning vs information dampening

Honest framing line:

> Paper 23B treats the probe mechanism as a habituation system: the agent should detect surprise normally but reduce its action tendency to keep probing after recent identifying interventions. Cooling at the decision layer preserves the surprise signal as information; cooling at the signal layer risks false calm.

That distinguishes us from "just decay the surprise" approaches.
