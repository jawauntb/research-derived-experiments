# Paper 25 — Pre-Registration

**Title (working):** Role-Specific Mediated Effects, Two-Sided Gauge Anchoring, and Fully-Learned Probe Abstractions

**Frozen:** 2026-06-12, before any Modal sweep runs.

## Question

Paper 24 closed (most of) the mediated/exogenous identifiability gap from Paper 23B via interventional contrast supervision: G2 passed strongly (mediated MAE 56% reduction), and G6 (shuffled contrast) confirmed semantic alignment matters. But **G7 wrong-history contrast also improved** mediated MAE by ~52%, revealing that the Paper 24 environment had role-invariant mediated structure: `mediated_E = HAZARD_AMP · h · SHOCK_E_MAG` produced the same h-dependence signal regardless of which role caused h to rise. The contrast loss identified the *h-dependence* correctly but the environment couldn't disambiguate "role-specific mediated identification" from "generic h-detection."

Paper 24 also showed a **gauge co-shift**: mediated head was pulled up to the right magnitude, but exogenous head compensated downward to preserve the sum (exogenous MAE 0.003 → 0.040). The single-sided contrast anchor wasn't enough.

Paper 25 is the final identifiability stress test. **The probing machinery is frozen** — no changes to detection (non-null surprise), allocation (V_probe + scale-norm current_replay), saturation (decision_refractory cooling), or re-engagement. Only three structural changes:

1. **Role-specific mediated effects** — different roles have different mediated amplifiers; wrong-history pairs convey wrong magnitudes
2. **Two-sided gauge anchoring** — additional `mediated_low_zero_loss` and `exogenous_low_anchor_loss` with λ_exo sweep
3. **Fully-learned buckets** — K=16 k-means over (z, E, D, hist_features); no hand-coded structure

If all three pass, the autonomous-probing arc has earned a clean conclusion.

## Frozen stack (DO NOT MODIFY)

- Three-head architecture
- Two-timescale V_probe (fast α=0.25, slow α=0.05, shift margin 0.02)
- Non-null prediction-error surprise (α=0.10)
- Scale-normalized current_replay V_probe target
- **`decision_refractory` cooling** (P23B's winner: τ · (1 + 1.5·effort))
- Online rollout + 50-ep warmup + ε-greedy 0.50→0.10 + action-stratified SGD
- Per-bucket high_h_buf, low_h_buf for contrast pairs (P24 mechanism)
- Two regime shifts (food→medicine at ep 250, medicine→food at ep 400)

## Change 1: Role-specific mediated environment

Replace P22-P24's single `HAZARD_AMP = 0.5` with per-role per-dimension amplifiers:

```
ROLE_HAZARD_AMP_E = {"food": 0.50, "medicine": 0.20, "poison": 0.00, "neutral": 0.00}
ROLE_HAZARD_AMP_D = {"food": 0.00, "medicine": 0.00, "poison": 0.33, "neutral": 0.00}

P(E_shock | role, h) = BASE_E[role] + ROLE_HAZARD_AMP_E[role] · h
P(D_shock | role, h) = BASE_D[role] + ROLE_HAZARD_AMP_D[role] · h
```

True per-bucket contrast targets (at h ≈ 1):
- food's mediated E contrast = 0.50 · 0.30 = **0.15** (strong, on E dim)
- medicine's mediated E contrast = 0.20 · 0.30 = **0.06** (weaker, on E dim)
- poison's mediated D contrast = 0.33 · 0.20 = **0.066** (D dim, not E)
- neutral's mediated contrast = 0 (no hazard sensitivity)

Now wrong-history contrast — using medicine's pairs to supervise food's mediated head — supervises food to magnitude 0.06 instead of true 0.15. **The G6 (wrong-history fails) gate should actually fail in this environment, validating the test.**

## Change 2: Two-sided gauge anchoring

P24's contrast machinery had:
- `contrast_loss`: pin mediated(high) − mediated(low) to observed contrast
- `exogenous_anchor_loss`: pin exogenous to mean(low_h null observations)

But the model still co-shifted because mediated(low_h) was free to drift. Paper 25 adds:

```
mediated_low_zero_loss = MSE(mediated_world_head(z, ff, low_h_avg_hist), 0)
```

This anchors mediated at low-h to zero (the true value when hazard is absent). Together with contrast_loss and exogenous_anchor_loss, both ends of the gauge are pinned.

**λ_exo sweep**: {1, 3, 5} for the combined `(mediated_low_zero + exogenous_anchor)` weight. Headline = λ_exo = 3.

## Change 3: Fully-learned buckets

Replace P24's semi-learned (K=4 k-means on z + E_bin × D_bin = 16) with fully-learned:

- Cluster feature: concatenated `[z (32-dim), E (1), D (1), hist (5)] = 39-dim`
- K=16 clusters
- Online k-means with α=0.05
- Initialize cluster centers from warmup-period observations

Bucket key = cluster_id (0..15).

## Conditions (9)

| Condition | Environment | Contrast supervision | Buckets |
|---|---|---|---|
| `p24_default_role_invariant_no_contrast` | P22-P24 (role-invariant) | no | oracle (role × E_bin × D_bin) |
| `role_specific_no_contrast` | NEW role-specific | no | oracle |
| `role_specific_contrast_one_sided` | role-specific | P24's one-sided (no mediated_low_zero) | oracle |
| `role_specific_contrast_twosided_lambda1` | role-specific | two-sided λ_exo=1 | oracle |
| **`role_specific_contrast_twosided_lambda3`** | **role-specific** | **two-sided λ_exo=3 (HEADLINE)** | **oracle** |
| `wrong_history_contrast_role_specific` | role-specific | two-sided λ_exo=3, WRONG-ROLE pairs | oracle |
| `shuffled_contrast_role_specific` | role-specific | two-sided λ_exo=3, SHUFFLED pairs | oracle |
| `fully_learned_buckets_with_contrast` | role-specific | two-sided λ_exo=3 | learned (K=16 over 39-dim) |
| `oracle_source_role_specific` | role-specific | n/a | oracle (semantic upper bound) |

3 seeds × 9 conditions = 27 Modal cells.

## Pre-registered gates

| Gate | Criterion |
|---|---|
| **G1 — Role-specific challenge works** | `wrong_history_contrast_role_specific` mediated MAE ≥ 2× of HEADLINE mediated MAE (env actually disambiguates) |
| **G2 — Mediated identifiability** | HEADLINE mediated MAE ≤ 0.06 AND ≥ 50% reduction vs `role_specific_no_contrast` |
| **G3 — Exogenous identifiability** | HEADLINE exogenous MAE ≤ 0.04 AND no worse than no-contrast by more than 0.01 |
| **G4 — No gauge co-shift** | HEADLINE mediated improves AND exogenous improves OR stays within ±0.01 of no-contrast |
| G5 — Shuffled fails | `shuffled_contrast_role_specific` does not improve mediated MAE (≥ 90% of no-contrast) |
| **G6 — Wrong-history fails** | `wrong_history_contrast_role_specific` does not improve mediated MAE (≥ 90% of no-contrast) — **environment makes this gate work properly** |
| **G7 — Fully learned buckets near oracle** | `fully_learned_buckets_with_contrast` mediated MAE within 30% of HEADLINE |
| G8 — Bucket non-collapse | Learned buckets: max bucket density / total nulls ≤ 0.4 (no single cluster dominates) |
| G9 — Maintained-boundary preserved | HEADLINE preserves P23B's re-engagement and no-false-calm dynamics |
| G10 — Vector concern preserved | Medicine accuracy within 0.05 of oracle across balanced/hungry/injured |
| G11 — No behavior-only pass | Good return or total-world prediction without G2/G3 = mechanistic failure |

## Pre-registered interpretation matrix

| Result pattern | Interpretation |
|---|---|
| HEADLINE passes G1+G2+G3+G4+G6+G7 | **Strong positive.** Autonomous-probing arc complete: role-specific mediated identifiability + gauge pinned + learned abstractions. |
| G6 still fails (wrong-history still helps) | Environment still under-constrained OR architecture has structural invariance that survives role-specific amps. Need richer disambiguation. |
| G4 fails (gauge co-shift persists) | Two-sided anchoring insufficient; need stronger penalty on mediated(low_h) deviation from zero or per-bucket exogenous anchor. |
| G2 passes, G7 fails (learned buckets worse) | Identifiability works in oracle bucket space, but fully-learned abstraction collapses role specificity. |
| G8 fails (bucket collapse) | k-means online dynamics unstable; need warmup or alternative clustering (vector quantization, codebook). |
| All pass except G7 | Learned bucket discovery is the last open problem; Paper 26 focuses on it. |
| HEADLINE fails G2 | Role-specific environment may need stronger contrast signal; or null-anchor insufficient. |

## Pre-committed continuation

If HEADLINE passes G1+G2+G3+G4+G6+G7:
- **Paper 26 (final arc paper)**: synthesis paper consolidating the program through P25. NOT another mechanism paper.

If only G7 fails:
- **Paper 26-buckets**: dedicate to learned abstraction methods (vector quantization, contrastive clustering).

If G6 still fails:
- **Paper 26-env**: richer environment design (non-stationary mediated effects, action-counterfactuals beyond null).

If G4 fails:
- **Paper 26-gauge**: tighter gauge pinning via per-bucket exogenous anchors or factorization-by-construction.

## What success looks like

> An agent with frozen autonomous-probing machinery and no hand-coded role labels identifies role-specific mediated and exogenous world components in a regime-shifting environment, while preserving the maintained-boundary mechanism from Paper 23B.

That would be a natural stopping point for the autonomous-probing arc. The program would have:
1. Self-organized concern (Papers 6–10)
2. Vector valence and zero-shot reweighting (Paper 15)
3. Self/world gauge breaking via null intervention (Paper 16b)
4. Calibrated autonomous probing under viability constraint (Papers 17A–19)
5. Vector first-order self with stable identification (Papers 20B–21A)
6. Responsive-world adaptation with three-head architecture (Paper 22)
7. Detect-allocate-saturate-re-engage cycle (Papers 23A–23B)
8. Interventional contrast for mediated identifiability (Paper 24)
9. **Role-specific component identification + learned abstractions (Paper 25)**

That's the complete arc.
