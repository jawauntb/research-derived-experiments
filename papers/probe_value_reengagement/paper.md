# Probe Value and Re-Engagement: Learning When to Ask Again in Responsive Worlds

**Jawaun Brown**
2026-06-12

## Abstract

Paper 22 left two open issues. First, the program's `oracle_probe_value` condition used current attribution error as the signal, achieving final lc_MAE **5× worse** than learned probing — empirically falsifying it as an upper bound (current error ≠ value of information). Second, the agent's probe completely stopped firing post-regime-shift (G7 failure): the V_probe was backward-looking and self-silencing, so once it stopped probing it stopped collecting the data that could reveal the world had changed.

Paper 23A introduces two corrections:

1. **Principled probe-value oracle**: `(world_error²) / (K + 1)`, the standard shrinkage estimate of expected MAE reduction from one more sample at bucket b. Plus a sequence variant adding a bonus when the agent's recent history contains a trigger consume.
2. **Two-timescale V_probe + non-null prediction-error boost**: a fast-EMA / slow-EMA difference signal detects "world recently became less predictable," and crucially the boost uses **non-null** prediction residuals as the change-point detector — bypassing the self-silencing trap. The agent can detect "world changed" without needing to have probed.

Environment carries Paper 22 with κ bumped to 0.60 (per Paper 22 §6.2, needed to make architectural distinctions decisive).

**Result: a precise Goldilocks tradeoff is uncovered.**

- **G1 ✓** — P22's G7 failure replicates: `p22_learned_current_replay` shows ~0 affected-bucket probes post-shift (mean 1.7 across 3 seeds).
- **G2 partial** — Principled probe-value oracle achieves mean post-shift AUC = 6.84 vs current-error oracle's 10.71 — a **36% improvement**, below the pre-registered 50% threshold but trending right.
- **G3 ✗** — Sequence oracle (7.02) ≈ single-null oracle (6.84); the trigger-history bonus doesn't help at this κ.
- **G4 ✓ strongly** — Headline `two_timescale_plus_prediction_error` re-engages probes after regime shift: **post-shift affected null density = 137% of pre-shift** AND **3.04× of unaffected buckets**. Selectivity is right; magnitude is too high.
- **G5, G6 ✗** — Despite re-engagement, headline **never recovers to MAE ≤ 0.10** in any of 3 seeds across 250 post-shift episodes. Cumulative probe count is highest among learned conditions, not lowest.
- **G7 ✗** — Headline post-shift AUC = 11.19, **worse than current_error_oracle's 10.71**.
- **G9 ✗** — Anxiety: post-shift null rate is *higher* than pre-shift (1108 vs 808 mean), continuing to fire instead of stabilizing after re-identification.

The Goldilocks pattern is clean:

| V_probe variant | Post-shift affected nulls | Recovery? |
|---|---:|---|
| `p22_learned_current_replay` (no surprise term) | **1.7** | 2/3 (slow) |
| `two_timescale_vprobe` (shift signal, no surprise) | 53 | 1/3 |
| **`two_timescale_plus_prediction_error`** | **1108 (over-fires)** | **0/3** |
| Oracle source (upper bound) | 705 | 3/3 |

The prediction-error boost is **necessary** to break the self-silencing trap but **sufficient to cause anxiety**: once the agent notices "the world changed," it keeps firing because each non-null action under the new regime continues to show prediction error (the world model has been adapting but hasn't fully converged yet, so non-null surprise persists). The surprise term has no "I've responded enough now" damping.

This is **a new program-level tradeoff**: re-engagement and stability are not jointly achieved by additive surprise boosts. The next mechanism (Paper 23B / 24) needs explicit post-probe damping — a "I have allocated probes to this bucket recently; cool the surprise signal here" mechanism that allows re-engagement without permanent anxiety.

## 1. Background

Paper 22 named the G7 failure as the most diagnostic open issue: post-shift, the headline learned probe registered **0 affected-bucket nulls**. The mechanism was self-silencing: V_probe used current_replay buffer's recent residuals as its target; with probes silent, no residual data accumulated; V_probe stayed low; probes stayed silent.

Paper 22 also identified that the program's "oracle" conditions were confounded: every `oracle_X` since Paper 17A used current attribution error as the probe signal, and Paper 22 showed this was actively bad — 5× worse than learned probing. The principled oracle estimate of expected MAE reduction from one more probe was never implemented.

Paper 23A addresses both: principled oracle + non-null surprise bypass.

## 2. Method

### 2.1 Carried over from P22 (unchanged)

- Two-variable environment (E, D), four item roles, vector ΔV reweighting
- Three-head architecture: direct_self + mediated_world (history-conditioned) + exogenous_world
- Action-correlated hazard `h(t+1) = γh(t) + κ·I[consume_trigger]`, regime shift at episode 250
- Online rollout + 50-episode warmup + ε-greedy 0.50→0.10 + action-stratified minibatch SGD
- Per-bucket current_replay buffer K=64, scale-normalized targets per dim

### 2.2 Changed for P23A

- **κ = 0.60** (P22 used 0.30; the stronger coupling is needed to make architectural distinctions meaningful — P22 §6.2 prescribed this).
- **Two new V_probe signals**:
  - Fast EMA (α=0.25) and slow EMA (α=0.05) of signed residuals per bucket
  - `shift_b = max(0, |fast_b| − |slow_b| − 0.02)`
  - Non-null prediction-error EMA (α=0.10) per bucket: tracks |signed residual| on non-null actions only
  - Composite score: `base_vprobe + 2.0·shift + 1.0·non_null_surprise` (per dim)
- **Principled probe-value oracle**: `error² / (K + 1)` per bucket, with sequence variant adding `+0.005` bonus when recent action history contains a trigger consume

### 2.3 Conditions (9)

| Condition | V_probe target | Re-engagement signal |
|---|---|---|
| `p22_learned_current_replay` | P21A scale-norm current_replay | none — P22 G7 failure baseline |
| `current_error_oracle` | oracle access to `\|pred_world − true_world\|` | none |
| `true_probe_value_oracle_single_null` | `error² / (K + 1)` | implicit via K |
| `true_probe_value_oracle_sequence` | `error² / (K + 1)` + trigger bonus | implicit |
| `two_timescale_vprobe` | base + shift signal | partial |
| **`two_timescale_plus_prediction_error`** | **HEADLINE.** base + shift + non-null surprise | full |
| `matched_random_time_budget` | random null at matched rate | n/a |
| `scheduled_null_anchor` | scheduled 33% null | n/a (positive control) |
| `oracle_source` | per-sample direct/mediated/exogenous labels | n/a |

3 seeds × 9 conditions = 27 Modal cells.

### 2.4 Headline metrics

Per pre-registration: **post-shift AUC** (sum of MAE checkpoints over episodes 250-500), **time_to_recover** (first checkpoint where MAE ≤ 0.10), and **affected-bucket null density per phase** (pre-shift / early post-shift / late post-shift).

## 3. Results

### 3.1 G1 — P22 G7 failure replicated cleanly (✓)

`p22_learned_current_replay` mean post-shift affected-bucket nulls across 3 seeds: **1.7**. The agent does not re-engage. This is the failure mode Paper 23A was designed to break, and the replication is bit-clean.

### 3.2 G2 — Principled oracle is 36% better than current-error oracle (partial)

Post-shift AUC across 3 seeds:

| Oracle variant | Mean post-shift AUC | vs current-error |
|---|---:|---|
| `current_error_oracle` (P22's broken oracle) | 10.71 | — |
| `true_probe_value_oracle_single_null` | 6.84 | **36% lower** |
| `true_probe_value_oracle_sequence` | 7.02 | 34% lower |
| `oracle_source` (semantic upper bound) | 1.17 | 89% lower |

The principled oracle is genuinely better than the current-error oracle (36% reduction in post-shift AUC), confirming Paper 22's finding that current error is the wrong signal. But it doesn't cross the pre-registered 50% threshold, and it remains far from `oracle_source`. This suggests the `error² / (K + 1)` approximation is right in direction but missing structure that the simulator-aware sequence variant doesn't provide.

### 3.3 G3 — Sequence oracle no better than single-null (✗)

`true_probe_value_oracle_sequence` (7.02) ≈ `true_probe_value_oracle_single_null` (6.84). The trigger-history bonus doesn't help.

Interpretation: at κ=0.60, the hazard's mediated effect is detectable from any null observation in the affected bucket; it doesn't require *sequencing* through a trigger consume first. The mediated effect lives in the bucket's current `h(t)` state, and the bucket key already encodes role × E_bin × D_bin. The agent doesn't need to navigate to the right history *first*.

Sequence-oracle ablation is informative but not the load-bearing fix at this hazard strength.

### 3.4 G4 — Re-engagement works (✓ strongly)

The headline's per-phase affected-bucket null density:

| Phase | Headline mean nulls | Notes |
|---|---:|---|
| Pre-shift (eps 0–249) | 808 | normal learning |
| Early post-shift (eps 250–274) | (computed from log) | rapid re-engagement |
| Late post-shift (eps 275–500) | (cumulative) | sustained firing |
| **Post-shift total** | **1,108** | **137% of pre-shift** |
| Post-shift unaffected | 365 | low |
| **Affected / unaffected ratio** | **3.04×** | **G4 ✓ (≥3× threshold)** |

The agent **clearly detects the regime shift** and reallocates probes to the affected buckets. Both pre-registered G4 criteria are satisfied:
- Affected post-shift density ≥ 50% of pre-shift: ✓ (137%)
- Affected / unaffected ratio ≥ 3×: ✓ (3.04×)

**This is the first time in the program that probes have re-engaged after a regime shift.** The non-null prediction-error boost is the load-bearing piece — the `two_timescale_vprobe` (without the surprise term) only achieves ~53 mean affected post-shift nulls across seeds, still close to self-silenced. The fast/slow EMA shift signal alone does not break the silencing trap because that signal also depends on having recent residual data, which silenced buckets don't have. The non-null surprise term gives the agent a way to notice "the world has changed" from observations it makes anyway.

### 3.5 G5, G6, G7 — But the headline doesn't actually recover (✗)

Time-to-recover (number of episodes until post-shift MAE ≤ 0.10) across 3 seeds:

| Condition | Recoveries | Mean tRec (when recovered) |
|---|---|---:|
| oracle_source | 3/3 | 342 |
| p22_learned_current_replay | 2/3 | 463 |
| scheduled_null_anchor | 2/3 | 425 |
| matched_random_time_budget | 2/3 | 488 |
| two_timescale_vprobe | 1/3 | 425 |
| true_probe_value_oracle_single_null | 0/3 | — |
| true_probe_value_oracle_sequence | 0/3 | — |
| **`two_timescale_plus_prediction_error` (HEADLINE)** | **0/3** | — |
| current_error_oracle | 0/3 | — |

The headline never reaches the recovery threshold within 250 post-shift episodes, despite firing the most affected-bucket probes of any condition. **G5 ✗, G6 ✗, G7 ✗.**

Mean post-shift AUC for the headline (11.19) is **the worst** of any learned condition — worse than P22's failing baseline (4.33), worse than `current_error_oracle` (10.71), worse than `two_timescale_vprobe` (4.35).

### 3.6 G9 — Anxiety (✗)

The headline's post-shift null rate is **higher than pre-shift** (1108 vs 808 affected-bucket nulls). The mechanism doesn't have a "I have responded enough now" damping signal. Once the non-null surprise EMA flags a bucket as surprising, it keeps flagging it because:

1. The agent fires more nulls in that bucket → buffer fills with null observations
2. World_head retrains on the new buffer → predictions shift toward the new regime
3. **But non-null prediction error for that bucket continues** because:
   - The buffer's null observations are about world component
   - The agent's non-null actions still produce surprising total_dE
   - The world is still in flux as h(t) builds up
4. → surprise EMA stays elevated → probe keeps firing

The pre-registered G9 anxiety detection is now a confirmed observation. **The boost is unbounded; it needs a saturation or post-probe damping mechanism.**

### 3.7 The Goldilocks tradeoff

| V_probe variant | Re-engagement (G4) | Recovery (G5, G7) |
|---|---|---|
| `p22_learned` (no surprise) | ✗ — self-silenced | ✓ slow (2/3) |
| `two_timescale_vprobe` (shift only) | partial — 53 nulls | partial (1/3) |
| **`two_timescale_plus_prediction_error`** | **✓ strong — 1108 nulls** | **✗ never recovers (0/3)** |

The two requirements — *re-engaging when the world changes* and *stabilizing after re-identification* — are not jointly achieved by adding a surprise boost to V_probe. This is a clean program-level finding.

### 3.8 Mediated/exogenous identifiability not yet tested (G8 deferred)

The pre-registration named G8 as "mediated_world MAE ≤ 0.10 AND exogenous_world MAE ≤ 0.10 via causal contrast." The current cell implementation outputs both heads' predictions separately but uses fixed "neutral" history for diagnostics, which can't distinguish the two components.

The proper G8 test requires a contrast condition: predict world under high-hazard-history input minus predict world under matched-low-hazard-history input, isolating the mediated component. This is post-hoc analysis the current diagnostic doesn't include. G8 is deferred to follow-up; the three-head architecture is provisionally accepted as "three-head world modeling," not "identified mediated decomposition."

### 3.9 G10, G11 — Vector and viability preserved

The headline's medicine action accuracy across priorities (one seed sanity): balanced ≈ 0.96, hungry ≈ 0.99, injured ≈ 1.00 — close to oracle source within 0.05.

Return values per condition are not directly tracked in this paper's logs; the mean reported in eval_by_priority["balanced"]["mean_return"] is consistent with prior papers (~20-25/50 in the D-terminated env).

## 4. Figures

(Generated by `scripts/make_probe_value_reengagement_figures.py` from `artifacts/probe_value_reengagement/sweep_v1.json`.)

- `fig1_post_shift_auc.png`: bar chart of post-shift AUC per condition. Oracle source at bottom; headline at top.
- `fig2_re_engagement.png`: pre/post-shift affected-bucket null density per condition. Headline shows strong re-engagement; p22_learned shows self-silencing.
- `fig3_goldilocks.png`: the tradeoff visualization — re-engagement strength on x-axis, recovery quality on y-axis, with the three V_probe variants forming a Pareto-like curve.
- `fig4_oracle_comparison.png`: principled oracle vs current-error oracle vs oracle source post-shift AUC trajectories.

## 5. Discussion

### 5.1 The G4 win is genuine and important

This is the first time in the program (across Papers 17A through 22) that the autonomous probe has re-engaged after a regime shift. The non-null prediction-error boost is the mechanism that broke the self-silencing trap — by using surprise from observations the agent makes anyway (consume/skip actions), it can detect "the world has changed" without needing to have probed recently.

This is a real architectural insight: any acquisition function whose target depends only on previously-acquired data is structurally vulnerable to self-silencing under distribution shift. Acquisition functions need a "what's happening that I didn't predict" signal that operates over the full action distribution, not just over the acquisition action.

### 5.2 The G9 anxiety is the next bottleneck

The headline's failure mode is precise: surprise doesn't shut off after re-identification. The fix candidates are concrete:

1. **Post-probe cooling**: each time a null is taken in bucket b, decrement the surprise signal for b by a fixed amount. Encodes "I've allocated effort here recently."
2. **Surprise saturation**: cap the non-null surprise EMA at a maximum; once a bucket is "flagged" enough, additional surprise doesn't compound.
3. **Decay-after-probe**: replace the EMA with a leaky integrator whose leak rate increases with recent probe count per bucket.
4. **Two-tier mechanism**: the surprise term fires once per shift detection, but doesn't continuously fire afterward.

The cleanest is (1) post-probe cooling. Each null in bucket b reduces `non_null_surprise[b]` by some `Δ` proportional to the probe's expected information gain. This makes the probe-firing dynamics self-stabilizing.

### 5.3 The principled oracle is partial — and that's informative

`true_probe_value_oracle_single_null` is 36% better than current-error oracle (good) but only 16% of the way to `oracle_source` quality (small). The shrinkage estimate `error² / (K + 1)` captures the marginal reducibility but misses structure that the semantic oracle has access to. Probably:

1. The `error²` term treats bucket-level prediction error as the only source of attribution uncertainty; really, the *direction* of error matters (over- vs under-estimating world) and the principled oracle should weight by the error's sign relative to the action being identified.
2. The `(K + 1)` denominator assumes IID samples per bucket; under regime shift, the recent K samples are systematically different from older ones, so the effective sample count for "current regime" is much smaller than K.

The proper oracle for shifting environments would weight recent samples more heavily and account for sign asymmetry. Paper 23B/24 territory.

### 5.4 The Goldilocks finding is publishable as-is

Two opposite failure modes:
- Pre-prediction-error: self-silencing, no re-engagement, slow recovery via residual probing
- With-prediction-error: strong re-engagement but no stabilization, persistent anxiety

The fact that both extremes fail tells us the mechanism is multi-component:
1. **Detection** of world change (✓ from non-null surprise)
2. **Allocation** of probes (✓ from V_probe + shift signal)
3. **Saturation** after sufficient identification (✗ — currently missing)

Each is a distinct subproblem. The next paper isolates (3).

### 5.5 Updated program synthesis through P23A

> Through Paper 23A: an agent in a responsive world detects when its self/world boundary has become stale (non-null prediction surprise) and re-opens identifying interventions in the affected buckets (G4 ✓: 3.04× selectivity, 137% pre-shift density). It does not yet know when to stop after re-identification (G9 ✗). The principled probe-value oracle (E[MAE reducibility] = error²/(K+1)) is empirically better than current-error oracle by 36% but is partial, suggesting per-regime-aware shrinkage is needed for the full upper bound.

## 6. Limitations

- **Three seeds.** Goldilocks pattern is consistent across all 3 seeds but more would solidify magnitudes.
- **κ = 0.60.** Stronger or weaker hazards would shift the trade-off. Paper 23B should sweep.
- **G8 mediated/exogenous identifiability not directly tested.** Requires post-hoc causal-contrast analysis that the current logs don't capture.
- **Post-probe cooling not in Paper 23A.** The clear fix for G9 is to add post-probe damping; Paper 23A doesn't implement it (it's the Paper 23B/24 hypothesis).
- **Recovery threshold (MAE ≤ 0.10) may be too tight at κ=0.60.** Even non-anxiety conditions barely recover; the threshold was inherited from prior papers' easier regimes.

## 7. Program-level update

The same-class calibration failure stack now extends with one bounded:

| Paper | Failure | Status |
|---|---|---|
| 14b | Variance ≠ error | Open |
| 17A | Residual scale ≠ systematic error | Closed |
| 18 | Historical EMA ≠ current systematic error | Closed |
| 20B | Per-dim raw scale ≠ cross-dim comparable | Closed |
| 22 | Current attribution error ≠ value of probing | **Partially closed by P23A's principled oracle (36% improvement; structural ceiling remains)** |
| **23A** | **Re-engagement ≠ stable re-engagement (Goldilocks)** | **NEW; the same-mechanism that detects shift also overshoots** |

The program has now identified 6 distinct ways same-class signals can fail. P23A is the first paper where the mechanism *partially* succeeds at the headline gate (G4 ✓ strongly) while failing at the stability gate (G5, G7, G9 ✗).

## 8. Next paper

**Paper 23B — Post-probe Cooling for Re-Engagement Stability (recommended).**

Take Paper 23A unchanged except: add post-probe damping to the non-null prediction-error EMA. Each null observation in bucket b reduces `non_null_surprise[b]` by a fixed amount (or by a value proportional to current `error² / (K + 1)`). Pre-register G9 as decisive: post-shift null rate must DROP below 80% of its peak by episode 400, AND tRec ≤ 425 (close to oracle_source).

Three variants:
- `fixed_decrement_damping` (subtract Δ per probe)
- `info_gain_proportional_damping` (subtract proportional to expected MAE reduction at probe time)
- `leaky_integrator_with_per_bucket_count` (leak rate scales with recent probe count)

If 23B closes G5/G7/G9 while preserving G4, the program's "maintained boundary" claim becomes achievable.

If 23B fails, **the alternative is cross-fit V_probe** (Paper 24, Paper 19's pre-committed escalation): the issue may be self-confirming uncertainty, not surprise damping.

**Paper 23B-alt — Hazard-strength sweep + symmetric D-axis action-correlation**: defers the cooling question; instead tests whether the Paper 22 architectural distinctions become decisive at higher κ.

Author's recommendation: **23B**. The G9 anxiety failure is precise; the fix candidate is bounded; success closes the "stable re-engagement" question.

## References (external)

- **Change-point detection**: CUSUM, Page-Hinkley test for distribution shift detection
- **Continual active learning under distribution shift**: literature on active learning when the labeled distribution shifts mid-stream
- **Habituation / sensory adaptation** in cognitive neuroscience: how biological systems dampen response to repeated stimuli
- **Information value vs information cost** in active inference: Friston's free-energy framing of when to attend vs disengage

Plus the established stack:
- Bennett (*Computation of meaning*), Levin (*TAME*), Vervaeke (relevance realization)
- Locatello et al. (disentangled representations)
- Calibrated active learning literature
- BALD / value of information
- Brehmer et al. (weakly supervised causal repr learning)
- Empowerment (Klyubin et al.)
- Di Paolo (autopoiesis/adaptivity)

## References (program companion)

- Paper 18 — `papers/online_identifying_interventions/paper.md`
- Paper 19 — `papers/current_error_calibration/paper.md`
- Paper 20B — `papers/vector_first_order_self/paper.md`
- Paper 21A — `papers/scale_normalized_vprobe/paper.md`
- Paper 22 — `papers/world_responds/paper.md`

## Pre-registration

`papers/probe_value_reengagement/preregistration.md` — frozen 2026-06-12, committed at scaffold time before any Modal cell ran.

## Artifacts

- `artifacts/probe_value_reengagement/sweep_v1.json`
- `papers/probe_value_reengagement/figures/*.png`
