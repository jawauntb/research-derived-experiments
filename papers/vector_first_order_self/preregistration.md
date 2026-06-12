# Paper 20B — Pre-Registration

**Title (working):** Vector First-Order Self: Autonomous Identifying Interventions for Multi-Valence Homeostatic Agents

**Subtitle:** Per-dimension self/world attribution under autonomous current-replay null probing.

**Frozen:** 2026-06-12, before any Modal sweep runs.

## Question

The program's strongest scalar mechanisms now exist:

- **Paper 15** showed vector ΔV heads support zero-shot reweighting where scalar drive cannot, especially under shifted priorities for medicine.
- **Paper 16b** showed active null anchoring breaks the gauge symmetry that defeats architectural self/world factorization.
- **Paper 19** showed an autonomous probe-value head trained on residuals **recomputed against the current world_head** on a recent buffer produces calibrated autonomous null probing (Spearman ρ to oracle = +0.62, total MAE 61.5% below matched-random, no audit floor required).

**Does the Paper 19 current-replay probe mechanism still work when "what matters" is vector-valued — when the agent must identify self-caused vs world-caused changes separately across multiple internal variables (energy AND damage)?**

This is the composition stress test. Paper 20B is not a victory lap; it asks whether the strongest scalar mechanisms compose cleanly in the vector setting or whether new bottlenecks emerge when the probe must reason per-dimension.

## Design

### Environment

Two-variable internal state `V = (E, D)`:
- E (energy): decay 0.04/step; episode ends if E ≤ 0
- D (damage): passive accrual 0.03/step; episode ends if D ≥ 1.0
- Both initialize at E=0.5, D=0.0; T_max = 50

Four item roles with both E and D effects per consume:

| Role | dE_consume | dD_consume |
|---|---:|---:|
| food | +1.0 | 0.0 |
| poison | −1.0 | +0.5 |
| medicine | −0.3 | −0.4 |
| neutral | 0.0 | 0.0 |

World shocks per dimension:
- E shocks: P(E_shock=+0.30 | food) = 0.8, else 0.1
- D shocks: P(D_shock=+0.20 | poison) = 0.6, else 0.1

(Both dimensions have non-trivial world dynamics so the agent has real attribution work per dimension.)

### Priority weights

- balanced: (w_E, w_D) = (1.0, 1.0)
- hungry: (1.5, 0.5)
- injured: (0.5, 1.5)

Training uses balanced weights. Eval runs under all three.

Designed so **medicine action flips between hungry (skip) and balanced/injured (consume)**, making medicine the cleanest reweighting test (G7 centerpiece).

### Architecture

Encoder: `Linear(16, 64) → ReLU → Linear(64, 32)`.

Vector heads (output dim 2 = [E, D]):
- `self_head(z, ffE, ffD, action_onehot) → (ΔE_self, ΔD_self)`
- `world_head(z, ffE, ffD) → (ΔE_world, ΔD_world)`
- **`v_probe_head(z, ffE, ffD) → (q_E, q_D)`** (vector probe; Softplus per dim, both ≥ 0)

Where `ffE` is the 7-dim Fourier encoding of E (carryover) and `ffD` is the 7-dim Fourier encoding of D.

### Probe rules

- **`dimension_complete_probe`** (HEADLINE): `take_null = max(q_E, q_D) > cost`
- **`priority_weighted_probe`** (ablation): `take_null = w_E·q_E + w_D·q_D > cost`
- **`scalar_probe_vector_heads`** (control): vector heads, but scalar V_probe trained on `(err_E + err_D)/2`; `take_null = v_probe > cost`

The headline test is dimension_complete: it asks "is either dimension currently uncertain enough to warrant probing?" The priority-weighted version asks "is the *currently-prioritized* dimension uncertain?" — which is exactly the failure mode the user named: scalar concern wearing vector clothes.

### Current-replay V_probe target (per dimension)

Per-bucket calibration buffer `C_b` of last K=64 raw null observations as `(obs, E, D, observed_total_E, observed_total_D)`. At every SGD update, for each bucket:

```
err_E(b, t) = | mean_{(obs,E,D,Te,Td) ∈ C_b}[ world_head_current_E(z(obs),E,D) − Te ] |
err_D(b, t) = | mean_{(obs,E,D,Te,Td) ∈ C_b}[ world_head_current_D(z(obs),E,D) − Td ] |
```

V_probe targets for a null sample at bucket `b`:
- `q_E_target = err_E(b, t)`
- `q_D_target = err_D(b, t)`

Vector probe loss: `MSE(v_probe_E, q_E_target) + MSE(v_probe_D, q_D_target)`.

The scalar-probe control trains on `(err_E + err_D)/2` to a single scalar output.

### Buckets

`(item_role, E_bin, D_bin)` with E_bin ∈ {E_low (<0.5), E_high (≥0.5)} and D_bin ∈ {D_low (<0.5), D_high (≥0.5)} → 16 buckets total.

(Note: V_probe outputs are per-dimension, but the bucket key is the joint (role, E_bin, D_bin). Each bucket carries both `err_E` and `err_D` targets.)

### Online training

Same as Paper 19: episode rollout + replay buffer + action-stratified minibatch SGD + ε-greedy on consume/skip decaying 0.30 → 0.05.

Greedy action selection: `score(action) = w_E_train · ΔE_self_pred(action) − w_D_train · ΔD_self_pred(action)` with `w_E_train = w_D_train = 1.0`.

### Conditions (12)

| Condition | Role |
|---|---|
| `vector_total_dV` | Competent vector baseline without self/world decomposition |
| `vector_factorized_no_null` | Gauge-symmetry failure baseline |
| `vector_passive_null` | Tests whether null inclusion alone fails again |
| `vector_scheduled_null_anchor` | Positive anchor control |
| `vector_matched_random_anchor` | Same null count, random placement (Pass 2) |
| **`vector_learned_current_replay_probe`** | **HEADLINE** (vector V_probe + dimension_complete_probe) |
| `vector_learned_current_replay_probe_audit` | Sensitivity check; expect no-audit ≥ audit |
| `vector_oracle_uncertainty_probe` | Upper bound on probe placement |
| `vector_oracle_source` | Upper bound on semantic attribution |
| `scalar_drive_selfworld` | Scalar collapse failure (P15 control) |
| `scalar_probe_vector_heads` | Vector heads, scalar V_probe (probe-dim collapse control) |
| `priority_weighted_probe` | Vector V_probe, relevance-weighted probe rule (neglect control) |

### Cell budget

- Pass 1 (parallel): 11 conditions × 3 seeds = 33 cells at headline cost
- Pass 2 (parallel, sequenced): `vector_matched_random_anchor` × 3 seeds = 3 cells with null rate locked to headline's realized rate
- **Total: 36 Modal cells.** CPU only, ~10–12 min wall-clock.

### Cost

Primary: `cost = 0.025`. Sensitivity sweep deferred (consistent with P19's deferral).

## Sanity checks (one seed before full sweep)

Run `vector_learned_current_replay_probe` at seed=20260610, cost=0.025. Require all of:

1. Vector V_probe outputs (q_E, q_D) **differ across buckets** — not collapsing to a scalar (per-bucket std of q_E − q_D > 0.01).
2. Per-bucket calibration buffers populated for every (role × E_bin × D_bin) bucket after warmup.
3. world_head_E recovers food's true E world expectation (close to +0.24) AND world_head_D recovers poison's true D world expectation (close to +0.12) under `vector_scheduled_null_anchor`.
4. Null rate at cost 0.025 ∈ [3%, 50%].
5. Min (q_E, q_D) across buckets < max cost (0.04).
6. No oracle source label leakage into non-oracle conditions (code grep).

If any fail, fix and rerun. Do not launch full sweep until all six pass.

## Pre-registered gates

| Gate | Criterion |
|---|---|
| **G1 — Vector active identifiability** | Headline per-dimension self MAE ≤ 0.10 AND world MAE ≤ 0.10 for both E and D |
| **G2 — False-credit reduction** | ≥ 70% reduction in food-self-E overshoot AND poison-self-D overshoot vs `vector_factorized_no_null` |
| **G3 — Dimension-wise probe calibration** | Spearman ρ ≥ 0.5 between learned probe rate per bucket and oracle current attribution error, SEPARATELY for E and D |
| **G4 — Top/bottom enrichment** | Top-quartile oracle-error buckets receive ≥ 2× null density of bottom-quartile, separately for E and D |
| **G5 — Selection beats volume** | Learned headline total component MAE ≥ 25% below `vector_matched_random_anchor` at matched null count |
| **G6 — Vector probe beats scalar probe** | Headline beats `scalar_probe_vector_heads` by ≥ 15% component MAE OR ≥ 0.25 Spearman ρ on the worse dimension |
| **G7 — Zero-shot reweighting** | Medicine-action accuracy under balanced, hungry, injured priorities within 0.05 of oracle (for headline vector self/world) |
| **G8 — Scalar-drive failure reproduced** | `scalar_drive_selfworld` fails ≥ 1 shifted-priority context by ≥ 0.15 medicine action accuracy |
| **G9 — No dimension neglect** | Worse-dimension attribution MAE ≤ 2× better-dimension MAE, unless both are already ≤ 0.07 |
| **G10 — Viability preservation** | Return ≥ 45/50 AND ≥ 90% of scheduled-anchor return |
| **G11 — Probe efficiency / no saturation** | Eval null rate ∈ [0.1%, 40%]; early-high → late-low dynamics confirmed via per-episode bucketed null rate log |
| **G12 — Behavior alone does not count** | Return ≥ 45/50 without G1 AND G3 AND G5 passing = mechanistic failure |

## Pre-registered interpretation matrix

| Result pattern | Interpretation |
|---|---|
| Headline passes G1–G12 | **Strong positive.** Autonomous identifying interventions scale to multi-valence first-order self. |
| Return succeeds, G1 fails | Paper 16 pattern returns: behavior without intended self/world structure |
| G1 succeeds, G7 fails | Self/world decomposition works, but vector concern is not being used flexibly |
| G7 succeeds, G1 fails | P15 mechanism composes with action, but not with first-order self |
| `scalar_probe_vector_heads` matches return but fails G6 on D | Scalar priority collapsed vector identifiability — confirms need for vector probe |
| `priority_weighted_probe` ignores D under hungry priority | Relevance-realization is local to current need, not complete self/world identification |
| No-audit fails, audit succeeds | Vector setting needs a calibration floor; autonomy becomes partial |
| `matched_random` beats learned | Paper 18 failure recurs at vector scale: placement is not epistemic in vector setting |
| Headline current_replay fails in vector despite scalar P19 success | Issue is bucket/sample complexity OR cross-dimensional interference, not current-error calibration itself |
| `scalar_drive_selfworld` passes G7 | Surprising; scalar drive turned out flexible enough — refutes the P15 lesson |

## Pre-committed claim limits

**If headline passes:**

> In a minimal two-variable homeostatic bandit, an agent can autonomously choose null interventions that identify which dimensions of viability change are self-caused versus world-caused, while preserving vector-valued concern for zero-shot priority reweighting.

NOT:
- "Full self"
- "Consciousness"
- "Agency solved"

Field-facing version:

> First-order self/world attribution can be made vector-valued and autonomously maintained through current-error-calibrated identifying interventions.

## Out of scope

- Action-correlated world shocks (Paper 20C territory)
- Higher-dimensional state (V = (E, D, hydration, ...) generalization)
- Multi-step planning
- Real-world environments / continuous state

## Failure escalation

If headline fails G1 or G5 but `vector_oracle_uncertainty_probe` passes:
- The mechanism failed in vector setting due to bucket complexity (16 buckets × 2 dims) — the next paper either reduces dimension or moves to learned-bucket discovery via encoder clustering.

If `vector_oracle_uncertainty_probe` also fails:
- Vector first-order self may be intrinsically harder than scalar. Next direction: cross-fitted error prediction or heterogeneous-architecture probe (the failure-mode escalation pre-committed in Paper 19's §8).

If `scalar_probe_vector_heads` passes G5 but headline doesn't:
- Vector probe is unnecessary; scalar collapse over dimensions is fine. Next paper reformulates the program's per-dimension probe design.

Any outcome is publishable. All narrow the program.
