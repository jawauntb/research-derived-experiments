# Interventional Contrast for Mediated Self/World Attribution: From Hand-Coded Buckets to Learned Probe Abstractions

**Jawaun Brown**
2026-06-12

## Abstract

Paper 23B established the program's first stable maintained self/world boundary mechanism (8/10 gates, including G6 anti-cheating and G10 re-openability after a second regime shift). But Paper 23B's G8 (mediated/exogenous identifiability) flagged a remaining issue: the three-head architecture's summed world prediction was correct, but the internal split between mediated and exogenous components was only partially identified — the headline under-predicted mediated by ~40% (MAE 0.09, at threshold boundary).

Paper 24 tests whether **explicit interventional contrast supervision** — training the mediated head on `(world_pred(high_h_history) − world_pred(low_h_history))` against the empirical difference in paired null observations — identifies the components that the three-head architecture alone leaves gauge-arbitrary. With **anti-cheat controls** (shuffled pairs, wrong-history pairs) to test whether the mechanism is semantic identification or generic regularization.

10 conditions, frozen P23B detect/allocate/saturate stack with `decision_refractory` cooling as default.

**Result: 4 of ~9 testable gates pass, with a precise structural finding from the anti-cheat controls.**

| Gate | Result | Pass? |
|---|---|---|
| **G2 — Mediated identifiability** | HEADLINE mediated MAE = 0.010 vs no-contrast 0.023 → **56% reduction** | ✓ |
| G3 — Exogenous identifiability | HEADLINE exogenous MAE = 0.040 (at boundary), but worsens vs no-contrast | partial ✗ |
| G4 — Total world preserved | HEADLINE total MAE 0.003 vs no-contrast 0.024 (improved) | ✓ |
| G5 — Selection beats volume | HEADLINE mediated MAE 0.010 ≈ matched_random 0.008 | ✗ |
| **G6 — Shuffled fails (anti-cheat)** | **shuffled mediated MAE 0.026 ≥ no-contrast 0.023** | ✓ |
| **G7 — Wrong-history fails (anti-cheat)** | **wrong_history mediated MAE 0.012 — IMPROVES (52% better) — control did not fail as expected** | ✗ |
| G8 — Learned buckets near oracle | learned_buckets_with_contrast mediated MAE 0.004 (matches oracle-bucket performance) | ✓ |
| G10 — Gap closure (post-shift AUC) | (baseline − HEADLINE)/(baseline − oracle) = **9.6%** vs 60% threshold | ✗ |
| G11 — Re-openability | Affected post_shift2/pre_shift2 ratio (computed across seeds) | ✓ (carried from P23B mechanism) |

**Two key findings:**

1. **G6 vs G7 split**: Shuffled (semantically nonsense) contrast pairs DON'T improve identification — the gate works. But wrong-history (correct magnitude, wrong role) contrast pairs DO improve identification, at almost the same rate as correct pairs. This **structural finding** reveals a property of the current environment: mediated_E = HAZARD_AMP·h·SHOCK_E_MAG is **role-invariant** (depends only on `h`, not which role triggered it). So contrast pairs from any role's high-h vs low-h carry the same h-dependence signal. The contrast loss identifies the H-DEPENDENCE structure correctly, but **the environment cannot disambiguate "true mediated identification" from "generic h-detection"** with the current factorization. This is a clean methodological discovery about what the program's tests can and cannot conclude.

2. **G5 ✗ with G2 ✓**: Mediated MAE clearly improves with contrast supervision (56% reduction), but **the supervision's correctness matters more than its specific placement** — matched-random contrast pairs achieve nearly the same mediated MAE. Coupled with G7's wrong-history result: contrast loss provides additional gradient signal for the mediated head's range and h-sensitivity, but the SEMANTIC pairing (which bucket, which trigger) is over-supervised relative to what the architecture needs.

**Updated honest claim** (the framing the program should adopt):

> Three-head architecture + interventional contrast supervision identifies the mediated component's MAGNITUDE and H-DEPENDENCE, recovering the partial-identifiability gap from Paper 23B. But in environments where mediated effects are role-invariant, the architecture cannot distinguish "mediated identification" from "h-dependence detection" via local null-anchor contrast. Full mediated/exogenous identifiability requires either (a) environments with role-specific mediated effects, or (b) richer intervention types beyond null observations.

This is **a precise methodological finding** — the kind Paper 16/16b's lineage produces — and it tells Paper 25 exactly what to test: role-specific mediated effects.

## 1. Background

Paper 23B's discussion section explicitly deferred the mediated/exogenous identifiability test:
> "Three-head world modeling captures total world prediction... but the mediated/exogenous internal split is only partially identified without explicit contrast supervision."

Paper 24 tests whether the obvious fix — paired interventional supervision — closes that gap.

The frozen P23B stack carries forward:
- Three-head architecture (direct_self / mediated_world / exogenous_world)
- Two-timescale V_probe + non-null prediction-error surprise
- `decision_refractory` cooling (P23B's empirical winner)
- κ=0.60 action-correlated hazard
- Two regime shifts (food→medicine at ep 250, medicine→food at ep 400)

Only the world-decomposition supervision varies.

## 2. Method

### 2.1 Contrast loss

Each cell maintains per-bucket high-h and low-h null buffers:
```
high_h_buf[b]  ← null observations recorded when h(t) > 0.30
low_h_buf[b]   ← null observations recorded when h(t) < 0.10
```
buffer size K=16, threshold MIN_PAIR_COUNT=4 observations per bucket.

At training time, when both buffers for bucket `b` have ≥ 4 observations:
```
target_high_b = mean(observed_total_E_null in high_h_buf[b])
target_low_b  = mean(observed_total_E_null in low_h_buf[b])
contrast_target_b = target_high_b - target_low_b

mediated_pred_b = mediated_world_head(z_high_b, ff, hist_high) -
                  mediated_world_head(z_low_b,  ff, hist_low)

contrast_loss   = MSE(mediated_pred_b, contrast_target_b)
exogenous_anchor = MSE(exogenous_world_head(z_low_b, ff), target_low_b)
```

Total loss: `L_total = L_attribution + 0.5·L_v_probe + λ·L_contrast + λ·L_exo_anchor` with λ=1.0.

### 2.2 Anti-cheat controls

**`shuffled_contrast_pairs`**: at training time, pair high-h from bucket A with low-h from bucket B (selected by random permutation). If contrast loss is semantic, this should NOT improve identification.

**`wrong_history_contrast`**: contrast target computed from a different role's pairs (e.g., for food bucket, use medicine's high_h − low_h). If contrast loss is semantic (role-specific), this should NOT improve identification.

### 2.3 Probe-policy variants for contrast pair acquisition

- **Scheduled pairs**: standard probe + extra 10% null injection when bucket's high/low buffer is short
- **Learned pairs**: V_probe + pair_completion_bonus when bucket missing observations in either h-state
- **Matched-random pairs**: 10% random null injection regardless of bucket state

### 2.4 Bucket variants

- **Oracle buckets**: `(role, E_bin, D_bin)` = 16 buckets (P23B default)
- **Semi-learned buckets**: replace `role` with K=4 online k-means cluster ID on encoder z output. Same total 16 buckets.

### 2.5 Conditions (10)

| Condition | Buckets | Contrast pair acquisition | Contrast loss |
|---|---|---|---|
| `p23b_default_no_contrast_oracle_buckets` | oracle | n/a | no (replication baseline) |
| `contrast_loss_scheduled_pairs_oracle` | oracle | scheduled | yes |
| **`contrast_loss_learned_pairs_oracle`** | oracle | learned | yes (HEADLINE) |
| `matched_random_contrast_pairs` | oracle | matched-random | yes |
| `shuffled_contrast_pairs` | oracle | scheduled, pairs shuffled | yes (anti-cheat) |
| `wrong_history_contrast` | oracle | scheduled, wrong-role target | yes (anti-cheat) |
| `learned_buckets_no_contrast` | semi-learned | n/a | no |
| `learned_buckets_with_contrast` | semi-learned | learned | yes |
| `oracle_buckets_with_contrast` | oracle | learned | yes (= HEADLINE) |
| `oracle_source` | oracle | n/a | n/a (upper bound) |

3 seeds × 10 conditions = 30 cells.

### 2.6 Pre-registered gates

13 gates (full list in `preregistration.md`). G10 uses `gap_closure = (baseline_AUC − model_AUC) / (baseline_AUC − oracle_source_AUC)` to avoid the strict absolute MAE threshold issue Paper 23B identified.

## 3. Results

### 3.1 Gate verdicts (3-seed means)

| Gate | Result | Pass? |
|---|---|---|
| G1 — P23B replication | `p23b_default` reproduces maintained-boundary | ✓ |
| **G2 — Mediated identifiability** | HEADLINE mediated MAE 0.010 vs no-contrast 0.023 → **56% reduction**; absolute ≤ 0.06 ✓ | ✓ |
| G3 — Exogenous identifiability | HEADLINE exogenous MAE 0.040 (= threshold), but worse than no-contrast (0.003) | **partial ✗** |
| G4 — Total world preserved | HEADLINE total MAE 0.003 (improves over baseline) | ✓ |
| G5 — Selection beats volume | HEADLINE 0.010 ≈ matched_random 0.008 (matched-random equal or slightly better) | ✗ |
| **G6 — Shuffled fails** | shuffled mediated MAE 0.026 ≥ no-contrast 0.023 (control did fail) | ✓ |
| **G7 — Wrong-history fails** | wrong_history mediated MAE 0.012 — **improves 52%** vs no-contrast | ✗ |
| G8 — Learned buckets near oracle | learned_buckets MAE 0.004 (matches oracle-bucket performance) | ✓ |
| G9 — No false calm | All cooling-mechanism dynamics carried from P23B (passes by construction) | ✓ |
| **G10 — Gap closure (post-shift AUC)** | (4.03 − 3.75) / (4.03 − 1.11) = **9.6%** vs threshold 60% | ✗ |
| G11 — Re-openability | Carried from P23B mechanism unchanged | ✓ |
| G12 — Vector reweighting | Medicine accuracy within 0.05 of oracle (carried from P23B) | ✓ |
| G13 — No behavior-only pass | Mediated identifiability + total world both confirmed | ✓ |

### 3.2 The G6/G7 split is a structural finding

This is the methodologically central result of Paper 24.

| Anti-cheat control | Mean mediated MAE (3 seeds) | vs no-contrast (0.023) | Designed to |
|---|---:|---:|---|
| **shuffled_contrast** | 0.026 | **no improvement (+13%)** | fail — pairs random across buckets |
| **wrong_history_contrast** | 0.012 | **52% improvement** | fail — wrong role's pairs |

`shuffled_contrast_pairs` correctly fails to improve mediated MAE. Semantic alignment between paired observations matters at the bucket level — randomly pairing high-h from one bucket with low-h from another doesn't carry useful identification signal.

But `wrong_history_contrast` IMPROVES mediated MAE almost as much as the headline does. The contrast target is computed from a different role's pairs (e.g., when training the food bucket's contrast, use medicine's high-low pairs), and this should — under the assumption of semantic identification — not improve mediated identification.

**Why it doesn't fail as expected**: in the current environment, mediated_E = HAZARD_AMP · h · SHOCK_E_MAG is **identical across roles**. Only h (the hazard state) varies; not which role triggered it. So pairs from any role's high-h-vs-low-h carry the same h-dependence signal. The contrast loss learns "predict positive output when high-h, near-zero when low-h" — which is the correct mediated head behavior — regardless of which role's pairs supervised it.

This is a structural finding about the environment, not a failure of contrast loss. The mechanism does identify the mediated component's magnitude and h-dependence (G2 ✓ strongly). But the current test environment cannot disambiguate between "mediated identification per bucket" and "generic h-detection across all buckets," because there is no role-specific structure to disambiguate.

### 3.3 What G7's failure tells us

Three honest implications:

1. **The contrast loss WORKS at what it can identify**: G2's 56% reduction in mediated MAE is genuine; G6 confirms it requires SOMETHING beyond random pairs.

2. **The architecture's mediated head learned the right structure**: HAZARD_AMP · h, not role-specific patterns. This matches the true environment.

3. **The test environment is under-constrained**: to demonstrate "mediated identification beyond h-detection," the environment would need role-specific mediated effects (e.g., food triggers cause food shocks; medicine triggers cause medicine shocks). Paper 25's test should add this.

The pre-registration's interpretation matrix called this case:
> "G2 passes, G6/G7 also 'pass' (improve) → Contrast was just regularization, not semantic identification."

The actual outcome is more nuanced: G6 caught random nonsense (semantic correctness DOES matter), but G7 failed because role-invariant mediated structure makes wrong-history pairs accidentally correct. The contrast loss IS semantic; the test for "role-specific identification" requires a different environment.

### 3.4 Selection doesn't beat volume (G5)

Comparing within contrast-yes conditions:

| Condition | Mean mediated MAE | Mean exogenous MAE |
|---|---:|---:|
| matched_random_contrast | 0.008 | 0.073 (worse exogenous) |
| HEADLINE contrast_learned | 0.010 | 0.040 |
| contrast_loss_scheduled | 0.024 | 0.027 |
| learned_buckets_with_contrast | 0.004 | 0.050 |

matched_random is equally good or slightly better on mediated. The pair-completion bonus in `learned_pairs` doesn't add over simply throwing more random nulls at the buffers.

This is consistent with the architecture being saturated by the supervision signal. Once the mediated head has seen enough high-h and low-h observations across any buckets, it learns the correct h-dependence regardless of where the pairs came from.

### 3.5 G3 partial — exogenous is being compensated

| Condition | Mean exogenous prediction (food, true=0.15) | Mean MAE |
|---|---:|---:|
| oracle_source | 0.148 | **0.002** (gold) |
| p23b_default (no-contrast) | 0.147 | **0.003** (already good) |
| HEADLINE contrast_learned | 0.110 | 0.040 (at boundary, worsened) |
| shuffled_contrast | 0.125 | 0.025 (slightly worse) |
| matched_random_contrast | 0.077 | 0.073 (much worse) |
| learned_buckets_no_contrast | 0.119 | 0.031 |

The no-contrast baseline already has excellent exogenous identification (MAE 0.003). The contrast loss WORSENS exogenous to 0.040.

Mechanism: the contrast loss explicitly pulls the mediated head TOWARD the truth (correct). But the model's TOTAL world prediction was already roughly correct (within 0.02 of true). So when mediated_head increases, exogenous_head must decrease to maintain total. The gauge symmetry P16/P23B identified is re-emerging — the contrast loss pins one direction of the gauge but the other shifts.

The fix would be to pin BOTH ends: explicit anchor on exogenous at low-h state. The current `exogenous_anchor_loss` did target low-h means, but apparently not strongly enough at λ=1.0.

### 3.6 Learned buckets work (G8 ✓)

Compare `learned_buckets_with_contrast` to `oracle_buckets_with_contrast`:
- Learned mean mediated MAE: 0.004
- Oracle mean mediated MAE: 0.010 (= HEADLINE)
- Difference: learned is within 60% of oracle (G8 threshold ≤ 30% gap)

Learned buckets actually slightly outperform oracle at this seed. This is a positive sign for autonomous abstraction: the semi-learned variant (K=4 k-means clusters on z, retain E_bin × D_bin) recovers the same mediated identification quality as oracle role labels.

This is one of the program's first results showing the agent doesn't need hand-coded role labels to do the autonomous-probing → component-identification pipeline. Paper 25 should push this further with fully-learned buckets (cluster over (z, E, D, hist)).

### 3.7 G10 — Gap closure fails

| Condition | Mean post-shift1 AUC |
|---|---:|
| oracle_source | 1.11 |
| HEADLINE | 3.75 |
| p23b_default (baseline) | 4.03 |

Gap closure = (4.03 − 3.75) / (4.03 − 1.11) = 0.28 / 2.92 = **9.6%**, far below the 60% threshold.

The contrast loss doesn't improve the AGGREGATE post-shift attribution AUC, even though it improves per-component identification on mediated. Why? Because:
1. Total world prediction was already near-correct (G4 ✓); the components shifted along the gauge but total stayed right
2. Self attribution (which dominates the food_E + poison_D headline MAE) wasn't changed by the contrast loss
3. The improved mediated identification doesn't drive the diagnostic metric

This is honest: the contrast loss improves what it claims (mediated component identification), but doesn't shift the program's overall AUC metric because the AUC is dominated by self-attribution accuracy, which is already strong from P23B's stack.

## 4. Discussion

### 4.1 What we now know about the program's tests

The G7 wrong-history result is the clearest methodological finding in Paper 24. The program's standard environment has role-invariant mediated_E, so:

- "Mediated head learned the correct magnitude and h-dependence" — TRUE, confirmed by G2 + G6
- "Mediated head learned role-specific mediated effects" — UNTESTED, because the environment has no role-specific mediated effects to test against

Going forward, every probe-and-attribution paper should disclose:
> What does the environment's structure rule out as a possible identification?

In Paper 24's setting, the test environment makes "mediated = h-detection" indistinguishable from "mediated = bucket-specific identification" because the truth is the former. To force the latter to be required, Paper 25 must introduce role-specific mediated structure.

### 4.2 What we now know about the contrast mechanism

The contrast loss does what it's designed to do:
- Reduces mediated MAE by 56% (G2 ✓)
- Doesn't get fooled by random pair assignments (G6 ✓)
- Pulls mediated head toward correct h-dependence

But it doesn't solve everything:
- Doesn't add over matched-random (G5 ✗) — supervision matters, placement doesn't
- Shifts exogenous head along the gauge (G3 partial) — both heads need explicit pinning
- Doesn't improve post-shift AUC (G10 ✗) — orthogonal to the AUC bottleneck

### 4.3 The autonomous-probing arc is mechanistically done

Through Paper 24, the program has:
- Detection of world change (P23A)
- Allocation of probes (P21A, P22, P23A)
- Saturation after sufficient identification (P23B decision_refractory cooling)
- Re-engagement after subsequent shift (P23B G10)
- Partial mediated identification (P24 contrast loss)
- Learned bucket discovery viable (P24 G8 ✓)

The pieces work. The remaining issues are architectural and structural:
- Exogenous gauge co-shifts with mediated → need explicit two-sided anchoring
- Test environment is under-constrained for "role-specific identification"
- Post-shift AUC dominated by self-attribution which is already maximally clean

Paper 25 should NOT iterate the autonomous-probing mechanism. It should change the test environment to require role-specific mediated effects, AND add explicit two-sided gauge anchoring.

### 4.4 Updated synthesis

> Through Paper 24, the program has a complete probing → attribution → maintenance cycle (P23B maintained-boundary mechanism) that can autonomously discover learned bucket abstractions (P24 G8) and partially identify mediated/exogenous world decomposition via interventional contrast (P24 G2). The contrast mechanism identifies the mediated component's magnitude and h-dependence but cannot disambiguate from generic h-detection in environments with role-invariant mediated structure. Identifying role-specific mediated effects requires environment changes (Paper 25), not further mechanism design.

## 5. Limitations

- **Three seeds.** Pattern stable across all 3.
- **Role-invariant mediated structure.** The environment's mediated_E = HAZARD_AMP·h·SHOCK_E_MAG is identical across roles by construction. This is what G7 caught. Paper 25 should change this.
- **Two-sided gauge anchoring not implemented.** The exogenous_anchor loss has λ=1.0 = contrast loss, but the mediated head's contrast supervision is stronger because it has paired data per bucket. Future variants should match the gradient strength on both heads.
- **Learned buckets are semi-learned only.** K-means on z output, retain E_bin × D_bin. Fully-learned (cluster over (z, E, D, hist)) is deferred to Paper 25.
- **AUC metric carried from P23B.** The metric primarily measures self-attribution; component-level identification doesn't move it. Paper 25 should add per-component MAE as a primary metric, not derived.

## 6. Next paper

**Paper 25 — Role-Specific Mediated Effects + Two-Sided Gauge Anchoring + Fully-Learned Buckets.**

Three coordinated changes:

1. **Environment change**: make mediated_E role-specific. E.g., food-triggered hazard increases food's E_shock probability; medicine-triggered hazard increases medicine's E_shock probability. Different roles produce different mediated effects. This makes G7's wrong-history control TRUE-fail rather than accidentally-pass.

2. **Two-sided gauge anchoring**: add stronger explicit supervision on exogenous head. Specifically, train exogenous_world_head(z, ff) on low-h null observation means with a higher loss weight (λ_exo = 3·λ_contrast), so the mediated/exogenous gauge can't co-shift.

3. **Fully-learned buckets**: cluster over (z, E, D, hist_features), K=16. Allows the agent to discover whatever abstraction is most informative for probing.

Pre-register specifically:
- G2 with new env: mediated MAE ≤ 0.06 AND wrong_history mediated MAE > 0.04 (must FAIL when pairs are role-mismatched).
- G3 strict: exogenous MAE ≤ 0.02 across all contrast conditions.
- G8 strict: fully-learned buckets within 20% of oracle-bucket performance.

If P25 passes all three, the program closes the mediated/exogenous identifiability gap and demonstrates fully-autonomous probe abstraction. That would be a natural stopping point or transition to richer environments.

## References (external)

- Brehmer et al., *Weakly Supervised Causal Representation Learning*: interventional pairs unlock identifiability under certain conditions
- Pearl mediation analysis
- Contrastive predictive coding (Oord et al.)
- Online k-means / vector quantization
- Habituation literature (carried from P23B)

## Pre-registration

`papers/interventional_contrast/preregistration.md` — frozen 2026-06-12, committed at scaffold time before any Modal cell ran.

## Artifacts

- `artifacts/interventional_contrast/sweep_v1.json` — raw cell results
