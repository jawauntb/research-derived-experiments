# Paper 22 — Pre-Registration

**Title (working):** When the World Responds: Action-Correlated Shocks and the Limits of Null-Anchored Self/World Attribution

**Frozen:** 2026-06-12, before any Modal sweep runs.

## Question

Papers 16b through 21A built a chain of mechanisms — null anchor, current-replay, scale-normalized V_probe — that recover vector self/world attribution to near-oracle quality in environments where **world shocks are independent of the agent's actions**.

Paper 22 tests the first regime where this independence breaks: **the world's hazard responds to the agent's prior actions**. Once world shocks depend on action history, three causally distinct sources of viability change co-exist:

1. **Direct self effect.** Immediate effect of consuming food, poison, medicine, etc.
2. **Action-mediated world effect.** Agent's prior actions modulate the world's current hazard state.
3. **Action-independent exogenous world effect.** World shock that occurs regardless of action history.

The Paper 21A two-head decomposition `self_head(z, V, action)` + `world_head(z, V)` (action-blind world) is **formally misspecified** in this regime: an action-blind world head cannot represent the dependence of current hazard on agent history. The world head will absorb the mis-specification by drifting; the self head will compensate; the gauge can re-form even in the presence of null anchoring.

Three architectural responses are candidates:
- **Minimal**: history-conditioned world head — `world_head(z, V, action_history)`
- **Richer**: three-head decomposition — `direct_self_head` + `mediated_world_head(history)` + `exogenous_world_head` (role only)
- **None**: keep the action-blind world head and see what breaks

Paper 22 tests all three.

## Secondary conceptual upgrade: probe value ≠ current error

Paper 21A's `oracle_uncertainty_probe` measured current attribution error, not the expected reducibility of that error under one more null observation. These are different quantities. A bucket can have high current error but be hard to reduce; another can have moderate error but high reducibility.

For Paper 22, `oracle_probe_value` is redefined as:

```
oracle_probe_value(b) = E[ component_MAE_after_anchor - component_MAE_now ] given a null in bucket b
```

estimated by replay-buffer intervention (compute MAE before, do an extra null-anchor update, compute MAE after). This separates the current-uncertainty question from the value-of-information question.

## Measurement upgrade: training-time selectivity, not eval null rate

Paper 21A's experimental design produced eval-time null rate = 0% because the agent **correctly** stopped probing once its model converged. The G14/G15 gates became vacuous.

Paper 22 measures selectivity **during learning**:
- Learning-curve component MAE (checkpoint every 25 episodes)
- Per-bucket cumulative null density over training
- Per-bucket world_head error reduction trajectory
- Time-to-attribution-threshold (episodes to reach MAE ≤ 0.10)
- Cumulative null cost to reach attribution threshold
- Probe rate response to regime shift (G7)

These metrics let us distinguish selection-by-volume from selection-by-acquisition-value during training, regardless of where the system converges.

## Environment

Carry over Paper 21A two-variable env (E, D) and item types. Add hidden hazard state:

```
h(0) = 0
h(t+1) = γ · h(t) + κ · I[consume_trigger(t)]
```

where:
- γ = 0.7 (decay; half-life ≈ 2 steps)
- κ = 0.30 (boost per trigger consume)
- `trigger` depends on regime (see below)

Modified shock probability per dimension:
- `P(E_shock | role) = base_E(role) + amp · h(t)` (capped at 1.0)
- `P(D_shock | role) = base_D(role)` (D unaffected by action history in v1)
- amp = 0.5

Base distributions: same as P21A (P(shock|food)=0.8 for E, P(shock|poison)=0.6 for D).

**Regime shift at episode 250:**
- Regime A (episodes 0–249): trigger = "consume food" — eating food increases future E-shock
- Regime B (episodes 250–499): trigger = "consume medicine" — eating medicine increases future E-shock

This makes the hazard's coupling to action history shift mid-training. The pre-shift world model now over-predicts food-related E-shocks; the post-shift world model must re-learn for medicine-related hazards.

## Architectures

| Architecture | self head | world head | additional input |
|---|---|---|---|
| `action_blind` (P21A baseline) | `(z, ffE, ffD, action) → 2` | `(z, ffE, ffD) → 2` | — |
| `history_world` | `(z, ffE, ffD, action) → 2` | `(z, ffE, ffD, hist_feats) → 2` | hist_feats = EMA(consume×role) over last 5 steps, 5-dim |
| `three_head` | direct_self `(z, ffE, ffD, action) → 2` | mediated_world `(z, ffE, ffD, hist) → 2` + exogenous_world `(z, ffE, ffD) → 2` | total = direct + mediated + exogenous |

History features: running EMA (α=0.30) of per-role consume indicators over last 5 steps; 4-dim (one per role) + 1 for null rate = 5-dim.

## Conditions (10)

| Condition | Architecture | Probe rule | Purpose |
|---|---|---|---|
| `p21a_independent_baseline` | action_blind | learned scale-norm probe | Replicate P21A under independent shocks (no hazard coupling) |
| `two_head_actionblind_world` | action_blind | scheduled 33% null | Expected failure under action-correlated shocks |
| `two_head_history_world` | history_world | scheduled 33% null | Test whether history-conditioning fixes the world head |
| `three_head_direct_mediated_exogenous` | three_head | scheduled 33% null | Headline semantic decomposition |
| `scheduled_null_anchor` | history_world | scheduled 33% null | Positive anchor control (= two_head_history but counted as control) |
| **`learned_scale_norm_current_replay`** | history_world | P21A normalized V_probe | **HEADLINE** autonomous probe under action-correlated env |
| `matched_random_time_budget` | history_world | Time-matched random null (matches headline's per-episode rate, applied at every training time) | Time-matched control |
| `matched_random_bucket_dim` | history_world | Bucket-balanced random null (forces uniform across 16 buckets × 2 dims) | Strongest random control |
| `oracle_probe_value` | history_world | Oracle access to per-bucket expected MAE reduction | Upper bound on probe placement |
| `oracle_source` | three_head | per-sample direct/mediated/exogenous labels | Upper bound on semantic decomposition |

3 seeds × 10 conditions = 30 Modal cells.

## V_probe specifics (carried from P21A)

- Per-bucket current_replay calibration buffer (K=64)
- Per-dim signed-residual current-model recomputation at every SGD update
- Variance-normalized target: `|mean signed residual| / sqrt(running_var_d + ε)`
- Per-dim threshold (τ_E, τ_D) at 85th percentile of warmup V_probe distributions

For `history_world` architecture: V_probe input also includes history features (same input as world_head).

## Online training

Same as P21A: replay buffer + ε-greedy 0.50 → 0.10 + 50-episode warmup + action-stratified minibatch SGD. n_episodes = 500.

## Sanity checks (one seed, before full sweep)

Run `learned_scale_norm_current_replay` at seed 20260610. Require all:

1. Hazard state `h(t)` varies during episode (range ≥ 0.1 within an episode).
2. Regime shift visible: average h(t) during regime A ≠ average during regime B.
3. World predictions adapt to regime shift: world_head's expected food-E prediction changes between episodes 240–250 and 290–300.
4. Probe rate at headline cost ∈ [0.1%, 40%] during BOTH regimes.
5. Anchor still recovers per-dim attribution: per-dim MAE ≤ 0.15 at end of training.
6. No oracle leakage.

If any fail, fix and rerun.

## Pre-registered gates

| Gate | Criterion |
|---|---|
| **G1 — P21A replication** | `p21a_independent_baseline` per-dim MAE ≤ 0.10 (P21A's result under no hazard coupling) |
| **G2 — Action-blind failure** | `two_head_actionblind_world` world_E MAE ≥ 2× of `two_head_history_world` under action-correlated shocks |
| **G3 — Mediated decomposition** | `three_head_direct_mediated_exogenous` recovers direct vs mediated vs exogenous components with per-component MAE ≤ 0.10 |
| **G4 — Selection beats time-matched volume** | Headline learning-curve AUC component MAE ≥ 25% lower than `matched_random_time_budget` |
| **G5 — Probe efficiency** | Headline reaches per-dim MAE ≤ 0.10 with ≤ 75% of the cumulative null count of time-matched random |
| **G6 — Dynamic calibration** | During non-converged periods, rolling Spearman(probe rate per bucket, oracle_probe_value per bucket) ≥ 0.5 |
| **G7 — Re-probing after regime shift** | Headline null rate rises ≥ 1.5× in shift-affected buckets within 30 episodes post-shift, then falls back ≥ 50% by episode 450 |
| **G8 — Behavior alone insufficient** | High return without G1, G3, G6 passing is mechanistic failure (preserves program's central methodological lesson) |
| **G9 — Vector reweighting preserved** | Medicine action accuracy within 0.05 of oracle across balanced/hungry/injured priorities |
| **G10 — Relative viability** | Return ≥ 90% of `scheduled_null_anchor` return under same hazard regime |

## Pre-registered interpretation matrix

| Result | Interpretation |
|---|---|
| Headline passes G1–G10 | **Strong positive.** Vector autonomous probing maintains self/world attribution when the world responds to the agent. |
| G2 passes (action-blind fails), G3 passes (three-head works), but G4 fails | World-responding env makes proper architecture necessary, but autonomous selection still doesn't beat time-matched random. Decomposition is necessary; selectivity isn't sufficient. |
| G7 fails (no re-probing after shift) | Probe doesn't track regime shifts; the agent doesn't maintain its boundary across time. |
| All learned variants fail; oracle works | Calibration is still the bottleneck despite the harder env. Move to cross-fitted V_probe (Paper 23). |
| Oracle probe value fails | Null anchoring is insufficient under action-correlated shocks regardless of probe; need different intervention type. |
| `history_world` fails but `three_head` succeeds | Two-component world is too coarse; explicit mediated/exogenous separation required. |
| G9 fails (reweighting breaks under action correlation) | Vector concern doesn't compose with mediated world. |
| Action-blind world succeeds despite mis-specification | The mediated component is small enough to absorb; the regime isn't yet hard enough; need stronger coupling. |

## Pre-committed continuation

If headline passes:
- **Paper 23**: same-step action-correlated shocks (shock_t depends on action_t, not action_{t-1}). Strict identifiability limit.
- **Paper 24**: learned bucket discovery (replace hand-defined role × E_bin × D_bin with encoder-derived clustering).

If headline fails:
- **Paper 23 (alt)**: cross-fitted V_probe (model A's residuals train V_probe for model B). Pre-committed escalation from Paper 19.

## External framing (intro / related work)

Same six-cluster citation stack as P21A. Add for Paper 22 specifically:

- **Action-conditioned predictive models**: Ha & Schmidhuber world models / Dreamer family — explicit treatment of action-conditioned hidden state evolution
- **Causal mediator identification**: literature on identifying mediated effects in causal inference (Pearl's mediation analysis)
- **Sense of agency under delayed/mediated consequences**: cognitive neuroscience work on agency attribution when sensory feedback is delayed or mediated by environmental dynamics

The honest framing line:

> Paper 22 is the first test in the program of a world that responds to the agent's prior actions. Action-mediated hazards force the self/world decomposition to factor through three causally distinct sources of viability change; the null-anchor mechanism that worked under action-independent shocks must now contend with a mediated-world component that an action-blind world head cannot represent.

## What success and failure look like

**Strong positive** (G1–G10): the program's autonomous-probing mechanism handles a world that responds. The minimal agent maintains vector first-order self attribution through hidden hazard dynamics and regime shifts. Major step toward the "maintained boundary" framing.

**Honest negative** (G2 ✓ but G4 ✗): action-blind fails, history-conditioned helps, but learned probing doesn't add over time-matched random. Program continues by replacing current-error V_probe with reducible-error / value-of-information V_probe.

**Localizing negative** (G3 ✗): three-head decomposition fails; world is not cleanly mediated/exogenous separable from the agent's data; need stronger intervention type beyond null.

All outcomes narrow the program.
