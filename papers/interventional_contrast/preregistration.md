# Paper 24 — Pre-Registration

**Title (working):** Interventional Contrast for Mediated Self/World Attribution: From Hand-Coded Buckets to Learned Probe Abstractions

**Frozen:** 2026-06-12, before any Modal sweep runs.

## Question

Paper 23B established the program's first stable maintained self/world boundary mechanism: detect (non-null surprise) → allocate (V_probe + shift signal) → saturate (decision-layer cooling) → re-engage (cooling decay + new surprise). The mechanism passed 8/10 gates including the decisive G6 "no false calm" anti-cheating gate and G10 re-openability after a second regime shift.

But Paper 23B's G8 (mediated/exogenous identifiability) flagged a remaining gap. Three-head world modeling captures total world prediction in action-correlated environments, but the **internal split between mediated and exogenous components is only partially identified**: HEADLINE under-predicted the mediated component by ~40% of its true value (MAE 0.09, at the threshold boundary). The summed prediction is right; the decomposition is gauge-arbitrary.

**Paper 24's primary question**: does an explicit interventional contrast loss — which trains the model to predict the *difference* between world contributions under high-hazard-history and low-hazard-history conditions — identify the mediated/exogenous split that summed-world-prediction alone cannot?

**Paper 24's secondary question**: can the agent learn its own probe abstractions (clusters over state) instead of using hand-coded (role × E_bin × D_bin × history) buckets, while preserving the maintained-boundary mechanism?

The primary question is the headline. The secondary question is staged carefully (oracle buckets first, then learned buckets) so a bucket-discovery failure cannot obscure a contrast-loss success.

## Frozen stack (from P23B)

DO NOT re-run the cooling factorial. P23B answered it. Carry forward:

- Three-head architecture (direct_self + mediated_world + exogenous_world)
- Two-timescale V_probe (fast α=0.25 / slow α=0.05 EMAs + shift signal)
- Non-null prediction-error EMA (α=0.10) as surprise detector
- **`decision_refractory` cooling** (P23B's empirical winner: threshold = τ · (1 + 1.5 · probe_effort)). NOT leaky_effort_integrator. The threshold-layer formulation preserved the calibrated probe-value signal in P23B and recovered in 2/3 seeds vs 1/3.
- Scale-normalized current_replay V_probe target
- κ=0.60 hazard coupling
- Online rollout + 50-episode warmup + ε-greedy + action-stratified SGD
- Two regime shifts (food→medicine at ep 250; medicine→food at ep 400)

## New: interventional contrast loss

Each cell maintains **paired high-h and low-h null buffers per bucket**:
```
high_h_buffer[b]   ← null observations recorded when h(t) > 0.3
low_h_buffer[b]    ← null observations recorded when h(t) < 0.1
```

At training time, when both buffers for bucket `b` have ≥ 4 observations, compute:
```
target_high_b = mean(observed_total_E_null in high_h_buffer[b])
target_low_b  = mean(observed_total_E_null in low_h_buffer[b])
contrast_target_b = target_high_b - target_low_b
```

These are **buffer means**, not single paired samples — the user specifically warned that single observations are too noisy because the shock process is stochastic.

Then:
```
mediated_contrast_pred_b = mediated_world_head(z_avg_b, ff, high_h_avg) − mediated_world_head(z_avg_b, ff, low_h_avg)

contrast_loss_b = MSE(mediated_contrast_pred_b, contrast_target_b)
exogenous_anchor_loss_b = MSE(exogenous_world_head(z_avg_b, ff), target_low_b)
```

Total auxiliary loss:
```
L_aux = λ_contrast · contrast_loss + λ_exo_anchor · exogenous_anchor_loss
```

with λ_contrast = 1.0, λ_exo_anchor = 1.0 frozen pre-sweep.

**`z_avg_b`** is the mean of encoded observations in the bucket's buffers (matched via current_replay buffer's z values).

## Probe-policy variants for contrast pairs

The contrast loss requires observations in *both* h-states per bucket. How are these collected?

- **Scheduled contrast pairs**: alongside the standard null probe, the agent additionally targets buckets where its `high_h_buffer` or `low_h_buffer` is short. Probe priority: bucket with `min(|high_h_buffer|, |low_h_buffer|)` lowest.
- **Learned contrast pairs**: V_probe is augmented with a "pair-completion bonus" — buckets needing the missing-h observations get a probe-score boost.
- **Matched-random contrast pairs**: same total number of contrast pairs as the learned variant, but pair targets are randomly assigned per episode.

## Bucket abstraction variants

- **Oracle buckets** (P23B default): `(role, E_bin, D_bin)` = 16 buckets. Headline.
- **Semi-learned buckets**: replace `role` with K=4 cluster IDs from online k-means on encoder output z. Keep E_bin × D_bin explicit. = 16 buckets.

Fully-learned cluster-over-(z, E, D, hist) buckets are out of scope for Paper 24 v1; if Paper 24 primary passes, that's Paper 25.

## Conditions (10)

| Condition | Buckets | Contrast pair acquisition | Contrast loss applied |
|---|---|---|---|
| `p23b_default_no_contrast_oracle_buckets` | oracle | n/a | no — replicates P23B |
| `contrast_loss_scheduled_pairs_oracle_buckets` | oracle | scheduled | yes |
| **`contrast_loss_learned_pairs_oracle_buckets`** | oracle | learned (V_probe + pair bonus) | yes — **HEADLINE** |
| `matched_random_contrast_pairs` | oracle | matched-random | yes |
| `shuffled_contrast_pairs` | oracle | scheduled, but pairs are SHUFFLED across buckets | yes — anti-cheat |
| `wrong_history_contrast` | oracle | scheduled, but contrast target uses different ROLE's pairs | yes — anti-regularization |
| `learned_buckets_no_contrast` | semi-learned | n/a | no |
| `learned_buckets_with_contrast` | semi-learned | learned | yes |
| `oracle_buckets_with_contrast` | oracle | learned | yes (= headline, but no shuffling controls) |
| `oracle_source` | oracle | n/a | n/a — semantic upper bound |

3 seeds × 10 conditions = 30 Modal cells.

## New metric: gap closure

P23B flagged that absolute MAE ≤ 0.10 thresholds are too strict at κ=0.60. Paper 24 uses **relative gap closure** as headline:

```
gap_closure(metric) = (baseline_metric − model_metric) / (baseline_metric − oracle_source_metric)
```

where `baseline` is the no-contrast oracle-buckets condition. Range: 0 (no improvement) to 1 (matches oracle_source).

## Pre-registered gates

| Gate | Criterion |
|---|---|
| **G1 — P23B replication** | `p23b_default_no_contrast` reproduces maintained-boundary: re-engages post-shift, cools, re-opens post-second-shift |
| **G2 — Mediated identifiability** | HEADLINE mediated_world MAE ≥ 40% lower than no-contrast baseline AND mediated MAE ≤ 0.06 |
| **G3 — Exogenous identifiability** | HEADLINE exogenous_world MAE ≤ 0.04 AND no worse than no-contrast |
| **G4 — Total world preserved** | HEADLINE combined world MAE not worse than 110% of no-contrast |
| **G5 — Contrast selection beats volume** | HEADLINE mediated MAE ≥ 25% lower than `matched_random_contrast_pairs` |
| **G6 — Shuffled contrast fails** | `shuffled_contrast_pairs` mediated MAE ≥ 90% of no-contrast (contrast must require correct pairing, not be generic regularization) |
| **G7 — Wrong-history contrast fails** | `wrong_history_contrast` mediated MAE ≥ 90% of no-contrast (anti-regularization control) |
| **G8 — Learned buckets near oracle** | `learned_buckets_with_contrast` mediated MAE within 30% of `oracle_buckets_with_contrast` |
| **G9 — No false calm (from P23B)** | Probe rate may only fall if raw surprise AND component MAE also fall |
| **G10 — Gap closure (relative-to-oracle)** | HEADLINE post-shift AUC gap_closure ≥ 0.60 (replaces P23B's strict MAE ≤ 0.10 threshold) |
| **G11 — Re-openability** | After second shift, affected-bucket probe density ≥ 1.5× pre-second-shift AND ≥ 2× unaffected |
| **G12 — Vector reweighting preserved** | Medicine accuracy within 0.05 of oracle across balanced/hungry/injured |
| **G13 — Behavior alone does not count** | High return or good total-world prediction without G2 + G3 = mechanistic failure |

## Pre-registered interpretation matrix

| Result pattern | Interpretation |
|---|---|
| HEADLINE passes G2 + G3 + G6 + G7 + G10 + G11 | **Strong positive.** Mediated/exogenous identifiable via interventional contrast; maintained-boundary preserved. |
| G2 passes, G6/G7 also "pass" (improve) | Contrast was just regularization, not semantic identification. Honest framing: results are weaker than claimed. |
| G2 passes, G5 fails | Contrast helps but selection of contrast pairs doesn't beat volume; the supervision matters but not its placement. |
| G8 fails | Learned buckets don't preserve the contrast benefit. Three-head identifiability is bucket-supervision-dependent. |
| G2 fails | The mediated component is intrinsically hard to identify from null observations alone; need richer interventions. |
| All learned variants fail; oracle_source works | Cross-fit / heterogeneous architecture next (P19 escalation). |
| G9 fails | Cooling mechanism cheats; mechanism revision needed. |
| G11 fails | Cooling overshoots; mechanism is brittle to repeated shifts. |
| Behavior succeeds, G2 + G3 fail | Paper 16 pattern: behavior without intended attribution. Mechanistic failure. |

## Pre-committed continuation

If HEADLINE passes G2 + G6 + G7 + G10 + G11:
- **Paper 25**: fully learned probe abstractions (cluster over (z, E, D, hist)) + symmetric action-correlation on D-axis + harder regime structure.

If G2 fails:
- **Paper 25-alt**: richer intervention types beyond null (e.g., counterfactual rollouts, action-counterfactuals).

If G8 fails:
- **Paper 25-buckets**: learned bucket discovery as standalone, with frozen contrast machinery.

## External literature framing

- **Causal mediation analysis** (Pearl): explicit identification of mediated vs direct effects through interventional comparisons.
- **Contrastive predictive coding** (Oord et al.): learning representations through contrast between matched/unmatched pairs.
- **Brehmer et al. weakly-supervised causal representation learning**: interventional pairs unlock identifiability.
- **Habituation literature** (carried from P23B): decision-layer cooling preserves detection while regulating action.
- **Online clustering / vector quantization** (for learned buckets): how to discover discrete abstractions over continuous state.

Honest framing:

> Paper 24 tests whether the three-head architecture's mediated/exogenous decomposition — partially identified in Paper 23B — becomes fully identifiable through explicit interventional contrast. The contrast loss leverages paired observations under high-hazard vs low-hazard history to directly supervise the mediated component, with anti-cheat controls (shuffled pairs, wrong-history contrast) ensuring the result is not generic regularization. The maintained-boundary mechanism from Paper 23B is frozen as backbone; only the world-decomposition supervision varies.

## What success looks like

The strongest positive: contrast loss reduces mediated MAE by 50%+ while preserving G6 (no false calm) and G11 (re-openability). Learned buckets reach within 30% of oracle-bucket performance. The agent has not only a maintained boundary but a mechanistically identified self/mediated-world/exogenous-world decomposition.

This would close the major architectural gap from Paper 22 and put the program in a position to stress-test the full stack against richer environment classes in Paper 25+.
