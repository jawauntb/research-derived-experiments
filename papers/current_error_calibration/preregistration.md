# Paper 19 — Pre-Registration

**Title (working):** Current-Error Calibration for Identifying Interventions: Recent Residuals Are Not Enough Unless Recomputed Against the Present Model

**Frozen:** 2026-06-12, before any Modal sweep runs.

## Question

Paper 18 ([Online Identifying Interventions](../online_identifying_interventions/paper.md)) cured Paper 17A's V_probe saturation failure via lagged signed-residual EMA debiasing (G11 ✓). But the debiased V_probe was **anti-calibrated** to oracle current attribution error: Spearman ρ = −0.55 between learned probe-rate by bucket and oracle uncertainty. Probe fired preferentially in *low*-uncertainty buckets (food) and skipped *high*-uncertainty buckets (poison). G3/G9 failed (learned 12.8% worse than matched-random at matched null budget).

The §5 diagnosis named one mechanism: V_probe's EMA target captures **historical residual scale**, not **current systematic attribution error**. But that diagnosis conflates multiple plausible causes:

**H1 — Historical lag.** EMA α=0.05 (effective window ≈ 20 samples) is too slow. Recent residuals would correctly reflect current model error.

**H2 — Stale-prediction problem.** Even recent residuals are stale: they were computed at *collection time* with the model as it was then, not the model as it is now. The world_head has since updated, so the stored residual is no longer the current error.

**H3 — Structural failure.** Same-class local residual signals are intrinsically non-epistemic, in the same family as Paper 14b's variance-uncorrelated-with-error finding. No amount of recency or recomputation closes the gap.

A "fix the EMA horizon" paper would only test H1. Paper 19 decomposes the failure mode and asks which of the three is operative.

## Hypotheses → conditions

| Hypothesis | Probe target | Distinguishing prediction |
|---|---|---|
| H1 (lag) | `recent_ema` (α=0.20) or `sliding_window_K` | Higher-recency target fixes anti-calibration; positive Spearman ρ; beats matched-random |
| H2 (staleness) | `current_replay` (recompute residuals with current world_head over per-bucket recent buffer) | Recomputed-against-present target succeeds where recency-only fails |
| H3 (structural) | All local-residual targets fail; oracle succeeds | All learned variants flat against matched-random; only oracle works |

## Conditions (10)

| Condition | Role |
|---|---|
| `factorized_no_null_online` | Gauge-symmetric failure baseline |
| `scheduled_null_anchor_online` | Positive anchor control |
| `matched_random_online` | Same null count as headline, random placement (Pass 2) |
| `learned_historical_ema_online` | Paper 18 baseline (α=0.05, lagged absolute) |
| `learned_recent_ema_online` | H1 test (α=0.20, lagged absolute) |
| `learned_sliding_window_online` | H1 nonparametric test (last K=50 null observations per bucket; absolute mean) |
| `learned_current_replay_online` | **H2 main** (per-bucket recent buffer; residuals recomputed at SGD time with current world_head) |
| **`learned_current_replay_audit_online`** | **HEADLINE** (current_replay + 5% audit floor) |
| `oracle_uncertainty_probe_online` | Upper bound on probe placement |
| `oracle_source_online` | Upper bound on semantic decomposition |

## Current-replay V_probe target

Per-bucket calibration buffer `C_b` of last `K=64` null observations as raw tuples `(obs, E, observed_total_under_null)`. At every SGD update (and at sample-construction time for V_probe loss), recompute:

```
e_b(t) = |  mean_{(obs,E,total) in C_b}[ world_head_current(z(obs), E) − total ]  |
```

where `world_head_current` is the head **as it currently exists**, not as it was when the observation was collected. V_probe targets samples in bucket `b` with `e_b(t)`.

This directly attacks the H2 staleness problem: it ensures every V_probe training step uses targets reflecting the **present** model error, not historical residuals.

For comparison, the other variants:

- `historical_ema_0p05`: EMA over signed residuals computed at collection time. (Paper 18 baseline.)
- `recent_ema_0p20`: same as P18 but α=0.20 (effective window ~5 samples). Still uses collection-time residuals.
- `sliding_window_K`: store last K=50 signed residuals per bucket; target is `|mean(last K residuals)|`. Nonparametric H1 test. Still uses collection-time residuals.
- `current_replay`: store last K=64 raw observations per bucket; recompute residuals via current world_head at SGD time. The H2 test.

## Audit floor

`epsilon_audit = 0.05`. Concretely: a baseline 5% probability of taking a null action regardless of V_probe's decision. Probe rule:

```
take_null = (rng < 0.05) or (V_probe(z, E) > cost)
```

Purpose: prevent missing-not-at-random failure. If the learned probe under-samples a bucket (because V_probe is wrong about it), the audit floor still injects some null observations into that bucket so V_probe has data to update from. Without this floor, anti-calibrated probes are self-confirming.

The headline condition uses the audit floor. A separate condition `learned_current_replay_online` runs without the floor to isolate its contribution. Pre-registered: if the audit version passes and no-audit fails, the claim is **"calibrated autonomy requires audit coverage,"** not "fully autonomous probing solved" (G19).

## Online training

Same online pipeline as Paper 18 (replay buffer + action-stratified minibatch SGD + ε-greedy on consume/skip decaying 0.30 → 0.05). The only change is the V_probe target.

## Bucket definition

`(item_role, E_bin)` with E_bin ∈ {E_low, E_high}. 8 buckets. Categorical (color, label) tags — same agent-side memory simplification as Paper 18, disclosed in §6.

## Cost sweep

Primary: `cost = 0.025`.
Sensitivity (run after main result stabilizes): `cost ∈ {0.01, 0.04}`.

## Sample budgets

Same as Paper 18: 200 episodes online; 1500 off-policy steps for off-policy cells; batch 48 stratified; eval 50 episodes per cell.

## Sanity checks (one seed, before full sweep)

Run `learned_current_replay_audit_online` at seed = 20260610, cost = 0.025. Require:
1. V_probe min < at least one tested cost (no saturation).
2. Null rate at headline cost ∈ [5%, 50%].
3. Calibration buffer `C_b` is populated for every bucket (no empty buckets after warmup).
4. Recomputed `e_b` differs from EMA-stored `μ_b` by at least 20% on at least 3 buckets — confirming the H2 mechanism actually changes the target.
5. Anchor losses still recover Paper 16b/17A/18 decomposition: scheduled_null_anchor_online food self ∈ [+0.85, +1.05].
6. No oracle source labels leak into learned conditions (code grep).

If any sanity check fails, fix and rerun. Do not launch full sweep until all six pass.

## Pre-registered gates

### Reused from 17A/18 (re-evaluated)

| Gate | Criterion |
|---|---|
| G1 | learned (headline) food self MAE ≤ 0.12 AND world MAE ≤ 0.10 |
| G2 | ≥ 70% reduction in food self overshoot vs `factorized_no_null_online` |
| G3 (≡ G9) | learned MAE ≥ 25% lower than `matched_random` at matched null budget |
| G5 | learned return ≥ 90% of scheduled AND ≥ 45/50 absolute |
| G11 | null rate ∈ [5%, 40%]; min V_probe < max cost |

### New for Paper 19

| Gate | Criterion | What it tests |
|---|---|---|
| **G14 — Recent/current calibration** | Learned probe-rate by bucket has Spearman ρ ≥ 0.5 with oracle current attribution uncertainty | The Paper 18 anti-calibration is fixed |
| **G15 — Error-reduction tracks probe density** | Per-bucket world_head error reduction (start vs end of training) correlates Pearson r ≥ 0.5 with per-bucket cumulative null density | Probe-shaping translates to attribution gain |
| **G16 — Beats matched random** | Headline total component MAE ≥ 25% lower than `matched_random_online` at matched null count | Decisive test (≡ G9 from P18) |
| **G17 — No saturation / no collapse** | Null rate at cost 0.025 ∈ [5%, 40%] AND min V_probe < max cost AND food self pred ≥ +0.7 (no collapse to passive-null pattern) | All P18 G11-style conditions hold |
| **G18 — Current replay beats stale recency** | `learned_current_replay_audit` beats `learned_recent_ema` AND `learned_sliding_window` by ≥ 15% component MAE OR ≥ +0.25 Spearman ρ | Decisive H1 vs H2 distinguisher |
| **G19 — Audit honesty** | If `learned_current_replay_audit` passes G16/G18 AND `learned_current_replay` (no audit) fails G16/G18, the paper's headline claim is "calibrated autonomy requires audit coverage," not "fully autonomous selection solved" | Anti-overclaim guardrail |
| **G20 — Behavior alone does not count** | Return ≥ 45/50 without G14 AND G16 passing is mechanistic failure | Preserves program's central methodological lesson |

## Pre-registered interpretation matrix

| Result pattern | Interpretation |
|---|---|
| `recent_ema` AND `sliding_window` pass G14, G16 | H1 confirmed: Paper 18's bottleneck was historical lag. Simple recency fixes it. |
| `recent_ema`, `sliding_window` fail; `current_replay` passes G14, G16, G18 | H2 confirmed: stale residuals were the issue. V_probe needs current-model error recomputation. |
| `current_replay` (audit) passes; `current_replay` (no audit) fails | H2 + missing-not-at-random: calibrated autonomy needs audit coverage. Honest partial win. |
| All learned variants fail; oracle passes | H3 confirmed: local same-class residuals are structurally non-epistemic. Next paper must move to cross-validation or meta-learning. |
| All variants ≈ matched_random | Selection still doesn't matter; the data-shaping pathway isn't enough; new direction needed. |
| Headline passes G16 but fails G14 | Behavior helps without calibrated placement — repeats P16 pattern at a level up |
| High return, G1 fails | Behavior without attribution; mechanistic failure (G20) |

## Pre-registered failure-mode escalation

If all four learned variants fail G16 (i.e., none beats matched-random) AND oracle passes:

> "Local same-class residual signals are intrinsically insufficient for autonomous identifying intervention selection in this minimal setting. The program should pivot to one of: (a) cross-fitted error prediction (model A's residuals train V_probe for model B); (b) deliberately heterogeneous-architecture probe model; (c) meta-learned probe value (predict future MAE reduction directly via reinforcement)."

This is pre-committed so that a negative Paper 19 result has a clean continuation, not an open-ended "try something else."

## Cell budget

- Pass 1 (parallel): 3 seeds × (3 cost-irrelevant + 6 cost-relevant non-matched at headline cost 0.025 only) = 27 cells
- Pass 2 (parallel, sequenced): 3 seeds × `matched_random` at headline cost = 3 cells
- **Headline total: 30 cells.** Cost sensitivity {0.01, 0.04} runs after, adding ~18 more cells if needed.

Initial sweep is CPU only. Approx 8 min via `.map()`.

## What success and failure look like

**H1 confirmed** (recency alone is enough): the Paper 18 bottleneck was lag. Simple recent EMA or sliding window restores positive Spearman. Mechanism done; program moves to vector self/world (17B) or richer environments.

**H2 confirmed** (current_replay required): stale residuals were the deeper problem. Current-replay closes the calibration gap. Program advances by acknowledging that local same-class signals need to be computed against the *present* model, not against the model that observed them.

**H3 confirmed** (all local signals fail): the §6 escalation to cross-validation / meta-learning kicks in. Program acknowledges that V_probe-style residual signals are structurally limited, and the next paper moves to one of the three pre-committed alternatives.

**Audit dependence**: if the headline only works with audit, the paper's claim is partial: "calibrated autonomy emerges with a small forced-exploration floor, not from V_probe selection alone." This is still progress — it tells us that the missing-not-at-random trap is real and quantifies how much coverage is needed to escape it.

Any of these outcomes is publishable. All narrow the program.
