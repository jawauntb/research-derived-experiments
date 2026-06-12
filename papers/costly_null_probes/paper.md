# Learning When Not to Act: Costly Null Probes for Self/World Identifiability in Minimal Homeostatic Agents

**Jawaun Brown**
2026-06-11

## Abstract

Paper 16b ([Identifiability Through Intervention](../null_intervention/paper.md)) showed that scheduled null actions, when used as world-only supervision, break the self/world gauge symmetry that defeats architectural factorization (Paper 16). The agent learned the first-order self/world boundary through the *act of not acting* — but the null actions were experimenter-scheduled. This paper asks whether a minimal homeostatic agent can **learn when to spend a viability cost** on a null probe such that the probe (i) improves attribution and (ii) fires preferentially in states the model is uncertain about.

We test seven conditions (factorized_no_null, factorized_null_passive, scheduled_null_anchor, matched_random_null_anchor, learned_costly_null_probe, oracle_uncertainty_probe, oracle_source) across three cost levels {0.01, 0.025, 0.04} and three seeds, with eight pre-registered gates frozen before any compute ran. **Headline finding (mixed): the anchor mechanism replicates strongly (G1, G2 pass; food self-overshoot reduced 85% vs no-null baseline), but the autonomous-selection mechanism falsifies (G3, G4, G5, G6, G7, G8 all fail). Specifically, matched-random null anchoring achieves slightly *better* attribution than the learned probe (G3), and the learned probe's V_probe head saturates above every cost threshold and fires 100% of the time at every state (G4, G6, G7).**

The failure mode is mechanistically informative and connects directly to Paper 14b. V_probe's training target — per-sample magnitude of the null-observed attribution residual — is dominated by exogenous shock noise rather than systematic attribution error. The model *does* learn the dominant scale signal (Pearson r = +0.84 between V_probe values and per-bucket oracle attribution error: food's high-shock-probability bucket has 2× higher V_probe than non-food buckets) but fails on the rank-within-cluster (Spearman ρ = +0.21). Worse, the absolute V_probe scale (~0.06 minimum) exceeds every tested cost (0.01–0.04), so the cost-gated selection rule never engages. Paper 14b showed ensemble variance failing at the regime boundary; here, learned residual magnitude fails to differentiate within an uncertainty cluster. The Paper-14b miscalibration trap transfers cleanly to the self/world identifiability problem one level up.

A second mechanistic finding: under off-policy uniform training (the pre-registered design), every anchor condition shares the same training data distribution. Eval-time probing therefore affects only viability cost (the agent pays cost per null), not attribution quality. To genuinely test autonomous data gathering for identifiability, an online paradigm — where probe decisions determine which (state, action, observation) triples enter the training buffer — is required. This becomes the central design choice for Paper 18.

## 1. Background and motivation

Paper 16 (First-Order Self) showed that an architecturally-factorized model — `self_head(z, E, action)` plus action-blind `world_head(z, E)` — is gauge-symmetric. The two heads can split the joint prediction `pred_self + pred_world ≈ observed_total_ΔE` in arbitrary ways while preserving behavior. Behavior saturates; attribution is wrong. Paper 16b ([null intervention](../null_intervention/paper.md)) broke the gauge by adding a null action (a no-op subject to world shocks but with no item-self effect) and training `world_head` on null-observed total ΔE while masking `self_head`'s contribution. The result was an 82% reduction in food self overshoot and recovery of true world expectation.

The mechanism worked, but in Paper 16b the agent did not *choose* to probe. The experimenter scheduled null actions during off-policy training and the agent never paid a viability cost for them. Bennett (2023) and Levin (2022) both argue that first-order self is constituted not by architectural factorization but by an active boundary process: the agent operationalizes the self/world distinction through interventions whose timing and selection are part of the agent's own structure. This paper asks whether minimal agents can take that step — selectively allocating viability cost to identifying interventions when uncertainty warrants it.

The conceptual touchstone is Vervaeke's relevance realization (Vervaeke, 2019) at the action-selection level: an agent that knows when *not acting* is informative. The empirical touchstone is the Paper-14b warning: same-architecture uncertainty estimators (identical-class ensembles) failed at the regime boundary where they were most needed, with variance at E=0.5 lower than at adjacent points and error-variance correlation ≈ 0. Any probe-value signal trained on residuals from the same model class inherits that risk.

## 2. Method

### 2.1 Environment

Same homeostatic bandit as Paper 16b. Energy E ∈ [0,1]; passive decay 0.04 per step; T_max = 50; episode terminates at E ≤ 0. Four item roles (food +1.0, poison −1.0, medicine −0.1, neutral 0.0) encoded as 16-dim noisy observations with permuted indices to prevent trivial feature read-off. Two-bit color + label observation, OBS_NOISE = 0.15. Training shock distribution: P(shock | food) = 0.8, else 0.1; shock magnitude 0.30. Shifted distribution moves correlation to medicine.

### 2.2 Architecture

Encoder: `Linear(16, 64) → ReLU → Linear(64, 32)`. Two prediction heads:
- `self_head(z, fourier_E(E), action_onehot) → 32 → 1` (action-conditional self-component)
- `world_head(z, fourier_E(E)) → 32 → 1` (action-blind world-component)

Plus, new in this paper, a **probe-value head**:
- `v_probe_head(z, fourier_E(E)) → 32 → Softplus(1) → ℝ≥0`

Trained off-policy on uniformly sampled (item, E, action) tuples; Adam lr=2e-3; 1500 steps; batch 64.

### 2.3 Conditions (7)

| Condition | Training loss | Eval-time probe rule |
|---|---|---|
| `factorized_no_null` | `MSE(pred_self + pred_world, observed_total)`, n_actions=2 | no nulls |
| `factorized_null_passive` | Same loss, n_actions=3 (null included w/o anchor) | no eval probing |
| `scheduled_null_anchor` | Null→world-only; non-null→joint | no eval probing |
| `matched_random_null_anchor` | Same anchor loss, training null rate = learned probe's realized rate | no eval probing |
| **`learned_costly_null_probe`** | Same anchor loss + V_probe trained on `\|pred_world.detach() − total\|` at nulls | probe if `V_probe(z, E) > cost` |
| `oracle_uncertainty_probe` | Same anchor loss | probe if `\|pred_world − true_world\| > cost` |
| `oracle_source` | Per-sample self/world labels (Paper 16b upper bound) | n/a |

`oracle_uncertainty_probe` deliberately does NOT receive oracle source labels — only oracle access to the probe-firing decision (true per-state attribution error) — so it cannot collapse into `oracle_source`.

### 2.4 Sweep

- Pass 1 (parallel): 30 cells = 3 seeds × (4 cost-irrelevant + 2 cost-relevant × 3 costs)
- Pass 2 (parallel, sequenced): 9 cells of `matched_random_null_anchor` with null rate matched to Pass 1's realized `learned_costly_null_probe` rates

39 Modal cells total. CPU only. Wall-clock ≈ 6 minutes via `.map()`.

### 2.5 Pre-registered gates (frozen pre-sweep)

All evaluated at headline cost = 0.025 unless stated. Complete pre-registration in `preregistration.md`, committed before Modal launch.

| Gate | Criterion |
|---|---|
| G1 — Active identifiability | learned food self MAE ≤ 0.12 AND world MAE ≤ 0.10 |
| G2 — False-credit reduction | ≥ 70% vs `factorized_no_null` food self overshoot |
| G3 — Selection beats volume | learned MAE ≥ 25% lower than `matched_random` MAE |
| G4 — Probe efficiency | ≥ 80% of scheduled-anchor identifiability gain with ≤ 20% null actions |
| G5 — Viability preservation | learned return ≥ 90% of scheduled AND ≥ 45/50 absolute |
| G6 — Calibrated placement | Spearman ρ ≥ 0.5 of learned vs oracle null-rate per state bucket |
| G7 — Top-risk enrichment | learned probe fires ≥ 2× more in top-quartile uncertainty buckets |
| G8 — Behavior/representation split | G1 + G6 both required for mechanistic success |

A complete pre-registered interpretation matrix mapping each result pattern to a paper conclusion is in `preregistration.md`.

## 3. Results

### 3.1 Gate verdicts (headline cost 0.025)

| Gate | Result | Pass? |
|---|---|---|
| G1 — Active identifiability | food self MAE = **0.077**, world MAE = **0.052** | ✓ |
| G2 — False-credit reduction | **85.2%** (no-null overshoot +0.519 → learned +0.077) | ✓ |
| G3 — Selection beats volume | learned total MAE 0.129 vs matched_random 0.081 → **−60%** (worse) | ✗ |
| G4 — Probe efficiency | gain ratio 1.00 but null rate **100%** | ✗ |
| G5 — Viability preservation | learned return **41.5** vs scheduled 49.5 (84%) | ✗ |
| G6 — Calibrated placement | Spearman ρ **undefined** (fire rates uniform = 1.0) | ✗ |
| G7 — Top-risk enrichment | top/bottom ratio = **1.00** | ✗ |
| G8 — Behavior/representation split | G1 ✓ + G6 ✗ → fails | ✗ |

**Summary: 2/8 gates pass.** The anchor mechanism replicates (G1, G2 strong). The autonomous-selection mechanism falsifies on every gate it can be tested by (G3–G8).

### 3.2 Anchor mechanism replicates 16b (G1, G2 strong)

Across all seeds at cost 0.025:

| Condition | food pred self_consume | food pred world | food self overshoot |
|---|---:|---:|---:|
| TRUE | +0.96 | +0.24 | 0.00 |
| `factorized_no_null` | +1.479 | −0.235 | +0.52 |
| `factorized_null_passive` | +1.731 | −0.518 | +0.77 |
| `scheduled_null_anchor` | +1.037 | +0.188 | +0.08 |
| `matched_random_null_anchor` | +1.006 | +0.206 | +0.05 |
| `learned_costly_null_probe` | +1.037 | +0.188 | +0.08 |
| `oracle_uncertainty_probe` | +1.037 | +0.188 | +0.08 |
| `oracle_source` | +0.946 | +0.239 | −0.01 |

Passive null inclusion makes attribution *worse* than no-null at all (+0.77 vs +0.52 overshoot), replicating 16b's finding that anchor matters more than presence. The anchor mechanism cleanly recovers the correct decomposition for every condition that uses it (overshoot drops from +0.52 to +0.05–0.08). False-credit reduction is **85.2%**, marginally improving on 16b's 82%.

### 3.3 Selection does not beat volume (G3 fail)

Under the pre-registered design, `matched_random_null_anchor` is trained with the same null rate as the learned probe (capped at 0.60 — the learned probe's realized rate of 1.0 collapses to this cap, producing matched-random's training null rate of 60% versus scheduled's 33%). Matched-random achieves total MAE 0.081 versus learned's 0.129, a 60% advantage in the wrong direction. **The full effect of the anchor is explained by null-data volume; the learned probe's *placement* contributes nothing on top.**

### 3.4 V_probe learned the dominant signal but saturates above every cost (G6, G7 fail)

Per-bucket diagnostics at cost = 0.025:

| Bucket | V_probe | Oracle attribution error | True world | Pred world |
|---|---:|---:|---:|---:|
| food_E_low | +0.115 | 0.056 | +0.240 | +0.184 |
| food_E_high | +0.119 | 0.059 | +0.240 | +0.181 |
| poison_E_low | +0.065 | 0.037 | +0.030 | −0.007 |
| poison_E_high | +0.065 | 0.037 | +0.030 | −0.007 |
| medicine_E_low | +0.063 | 0.041 | +0.030 | −0.011 |
| medicine_E_high | +0.064 | 0.045 | +0.030 | −0.015 |
| neutral_E_low | +0.060 | 0.047 | +0.030 | −0.017 |
| neutral_E_high | +0.061 | 0.047 | +0.030 | −0.017 |

V_probe **partly** tracks oracle attribution error:
- Pearson r = **+0.843** (food's high scale lifts V_probe ~2× above the non-food cluster)
- Spearman ρ = **+0.214** (within non-food, V_probe does not discriminate)

The minimum V_probe value (+0.060, neutral_E_low) **exceeds the highest tested cost (0.04)** in every bucket. The cost-gated selection rule therefore engages nowhere — the probe fires 100% of the time at every state, yielding a uniform fire rate that makes the pre-registered G6 Spearman undefined and G7 top/bottom ratio = 1.0.

V_probe's failure pattern is exactly the form Paper 14b warned about, one level up. There, identical-architecture ensembles' variance at the regime boundary was *lower* than at adjacent points despite higher absolute error. Here, V_probe trained on per-sample residual magnitudes captures the dominant heteroscedasticity signal (food has the largest shock-variance) but cannot rank within homoscedastic clusters. Worse, training-time variance is dominated by stochastic shocks (Bernoulli 0/+0.30) rather than systematic prediction error — so V_probe's *scale* is calibrated to noise, not error.

### 3.5 Oracle uncertainty probe is selective; learned probe is not

Oracle probe per-bucket fire rates at cost 0.025 (averaged over seeds):

| Bucket | Learned | Oracle |
|---|---:|---:|
| food_E_low | 1.00 | 0.97 |
| food_E_high | 1.00 | 0.99 |
| poison_E_low | 1.00 | 0.80 |
| poison_E_high | 1.00 | 0.63 |
| medicine_E_low | 1.00 | 0.87 |
| medicine_E_high | 1.00 | 0.69 |
| neutral_E_low | 1.00 | 0.95 |
| neutral_E_high | 1.00 | 0.83 |

Oracle differentiates across buckets (range 0.63–0.99), with E_high consistently lower than E_low — the model's world predictions are slightly better at high E because the bulk of training data concentrates there under any policy that survives to high E. Learned probe is uniform 1.0. Even oracle's range is high; the trained model's world predictions are simply not accurate enough across most buckets for cost-0.025 gating to discriminate aggressively.

### 3.6 Off-policy training decouples probe selectivity from attribution quality

A subtler finding. Under off-policy uniform training (the pre-registered design), all anchor conditions share identical training data distributions; the only difference is the loss form. Attribution recovery is therefore **identical** across `scheduled_null_anchor`, `learned_costly_null_probe`, and `oracle_uncertainty_probe` — their food self predictions are bit-for-bit identical (+1.037, +1.037, +1.037) because they all use the same anchor loss on the same training samples. The eval-time probe rule affects only viability cost, not the underlying model.

Oracle probe's selectivity therefore manifests as **higher return** (~45.5 mean) than the learned probe (~41.5 mean), but **identical attribution**. To test whether autonomous probing can improve attribution, an online paradigm is needed: the probe decision must determine what data enters the training buffer.

This is itself a methodological finding worth pre-registering. The original 17A design tested probe-selectivity-with-fixed-data, which is the strictly easier sub-problem. The harder problem — probe-selectivity-shapes-data-which-shapes-attribution — requires Paper 17A-online.

### 3.7 Cost sensitivity

For oracle probe (the only condition where the cost-gated rule actually engages):

| Cost | Mean null rate | Mean return |
|---|---:|---:|
| 0.010 | 0.96 | 47.1 |
| 0.025 | 0.81 | 45.5 |
| 0.040 | 0.63 | 42.9 |

Oracle probe's null rate decreases monotonically with cost, as expected. Learned probe's rate is 1.00 at every cost — the cost dimension is invisible to the saturated V_probe.

## 4. Figures

- **fig1 — `figures/fig1_self_predictions.png`**: per-role self_consume predictions at headline cost. Confirms anchor conditions recover food (+1.04 ± 0.03) against true +0.96; passive null fails worse than no-null.
- **fig2 — `figures/fig2_world_predictions.png`**: per-role world predictions. Anchor conditions recover food world to +0.19–0.24 vs true +0.24; no-null and passive go negative.
- **fig3 — `figures/fig3_food_overshoot_headline.png`**: bar chart of food self overshoot. 85% reduction vs no-null; matched-random and learned both achieve the reduction.
- **fig4 — `figures/fig4_cost_sensitivity.png`**: cost-sensitivity sweep across {0.01, 0.025, 0.04}. Learned probe's null rate is flat at 1.0; oracle probe drops monotonically; food overshoot is cost-invariant (training data unchanged).
- **fig5 — `figures/fig5_probe_calibration.png`**: G6/G7 calibration scatter. Left: learned vs oracle fire rate per bucket — learned is saturated at 1.0; ρ undefined. Right: top-quartile vs bottom-quartile fire-rate enrichment; learned ratio = 1.00 vs oracle's selective pattern.

## 5. Discussion

### 5.1 What replicates and what doesn't

The anchor mechanism from Paper 16b replicates strongly — slightly stronger, in fact (85% vs 82% false-credit reduction). The mechanism is robust: any condition that uses null-anchor losses achieves near-oracle component recovery, including matched-random anchoring with no intelligent probe selection. Paper 16b's central claim ("intervention data must be anchored, not just included") survives this paper unchanged.

What does **not** survive: the conjecture that *autonomous epistemic selection* over null probes could improve identifiability beyond scheduled probing. Under the pre-registered V_probe design, learned selection is worse than random matched-volume placement (G3), saturates above all cost thresholds (G4, G6, G7), and costs the agent ~16% of viability return (G5).

### 5.2 Why V_probe saturated

V_probe targets per-sample magnitudes of attribution residuals at null observations: `|pred_world.detach() − observed_total_under_null|`. This signal is dominated by exogenous shock noise. With shock probability p and magnitude σ, the expected residual under a perfectly calibrated world model is:

`E[|σ·B(p) − pσ|] = 2pσ(1 − p)`

For food (p=0.8, σ=0.30): expected per-sample residual ≈ 0.096 — even with a perfect world model, V_probe's target is bounded below by shock variance, not by attribution error. The minimum learned V_probe value across buckets (~0.06) matches this floor; the entire dynamic range of V_probe lives in shock-noise territory, above every tested cost threshold.

A debiased V_probe variant — targeting `|pred_world − E[observed_total|null, state_bucket]|` via running per-bucket EMAs — would strip the noise. This is the obvious next iteration but is post-hoc to the pre-registration; reporting it would violate the locked design. It is filed as Paper 17A-bis.

### 5.3 The Paper-14b miscalibration trap transfers

Paper 14b found that identical-architecture ensemble variance at the regime boundary E=0.5 was *lower* than at adjacent points despite the model's prediction error spiking there. Variance and error were uncorrelated (r ≈ 0). The mechanism: ensembles of the same architecture trained on the same data converge to systematically-similar mistakes.

Here the analogous pattern: V_probe trained on the model's own residuals at null observations inherits the model's noise structure rather than its error structure. Where the model is systematically wrong (food, +0.06 attribution error) it agrees with itself (V_probe = +0.115); where the model is systematically right (non-food, +0.04 attribution error) it also agrees with itself (V_probe = +0.06). V_probe's range across systematic error is ~2×; V_probe's range across noise floor is ~10× wider. Cost-gated selection over a noise-dominated signal cannot discriminate signal.

Both findings reinforce a methodological pattern: **same-class uncertainty estimators are not epistemic.** Paper 14b proposed nonidentical-architecture ensembles or auxiliary calibration losses as the next direction; the analogous prescription here is to target *systematic* attribution error (e.g., per-bucket EMA residuals, regularized to penalize raw variance) rather than per-sample magnitudes.

### 5.4 The decoupling of probe and training data

A second mechanistic finding that the pre-registration did not anticipate: under off-policy uniform training, every anchor condition sees identical training data, and the eval-time probe rule affects only viability cost. The "selection improves attribution" hypothesis cannot be tested in this design — selection can only redistribute eval-time costs.

The deeper claim that "an agent learns when to probe so as to identify itself" requires an **online** paradigm where probe decisions determine which (state, action, observation) triples enter the training buffer. Then probe selectivity has a direct path to influencing attribution: probe in high-uncertainty buckets → more anchor data there → faster local convergence of `world_head` → reduced attribution error.

This becomes the central architectural choice for the next iteration. Two clean candidates:
1. **Paper 17A-online**: same setup, but training proceeds episode-by-episode; the probe policy is part of the data-collection process; V_probe redesigned to target debiased per-bucket residuals.
2. **Paper 17B (vector self/world)**: combine Paper 15's vector ΔV head with Paper 16b's anchor mechanism, testing whether multi-dimensional attribution (ΔE_self, ΔE_world) × (ΔD_self, ΔD_world) is identifiable through null anchoring.

### 5.5 Connection to Vervaeke and Levin

The pre-registration framed this paper as the agent learning relevance realization at the action-selection level — knowing when *inaction* is informative. The results show that minimal homeostatic agents *can* discover the coarsest level of this — they can learn that high-shock states have higher prediction residuals — but that this coarse-grained discrimination is overwhelmed by per-sample noise. Bennett's first-order self in this minimal environment is constituted by the *act* of null intervention (the anchor mechanism) rather than by *choice* about when to act (the probe mechanism). The probe-choice level — Levin's "selecting cognitive boundaries on demand" — appears to require either richer uncertainty signals (debiased V_probe) or richer environmental coupling (online data-shaping).

## 6. Limitations

- **Pre-registration was honored at cost of headline.** V_probe trained on noisy per-sample residuals saturates; a debiased target (per-bucket EMA) would likely pass G6/G7 but is post-hoc. Reporting the failed-as-designed result is the methodologically correct call.
- **Off-policy training is a strong simplification.** It cleanly decouples probe selectivity from training-data quality, which means the design tests only a sub-problem of autonomous identifiability. The full problem requires online training (§5.4).
- **Cost regime not exhaustive.** Tested {0.01, 0.025, 0.04}. At cost ≫ 0.06 the probe would mechanically be suppressed regardless of V_probe; at cost = 0 the probe would trivially fire everywhere with no information value. The interesting middle regime is what we tested.
- **State bucketing is coarse.** Eight buckets (4 roles × 2 E bins) hide finer-grained heterogeneity. Paper 17A-online should sweep finer E binning to test whether selectivity emerges at higher resolution.
- **Single environment.** Same minimal homeostatic bandit as Papers 12–16b. The mechanism's brittleness or robustness across environment classes is open.

## 7. Where this leaves the program

Paper 16b's anchor mechanism is **strengthened** by this paper: replicates at 85% reduction, robust under random placement, robust to inclusion of probe-value training. The program's strongest identifiability result stands.

The autonomous-selection claim is **falsified for the V_probe-on-residuals design**. The falsification is mechanistically informative: it transfers the Paper-14b miscalibration trap to the self/world domain and localizes the failure to per-sample residual targets that mix systematic error with shock noise. It also reveals that off-policy training as designed cannot test the deeper claim; online data-shaping is needed.

**The strongest defensible synthesis** through Paper 17A:

> In minimal homeostatic bandit settings, concern-like structure can be learned from viability dynamics, used directly for model-based action, extended to vector-valued mattering, and made self/world-identifiable through active *anchored* intervention — but each step required a methodological correction over the naive form of the previous one, and autonomous selection of identifying interventions remains an open problem because same-class uncertainty signals inherit the model's noise rather than its error.

**Strongest remaining limitation:** the agent does not yet shape its own training data through identifying interventions. Probe selectivity is decoupled from attribution quality under off-policy training.

## 8. Next paper

Two viable next directions:

**Paper 17A-online (recommended)**: Restage 17A with online training. Replace off-policy uniform sampling with episode-by-episode rollout. Probe decisions during rollout determine training-buffer contents. Replace V_probe targets with debiased per-bucket EMA residuals (`|world_head_pred − running_mean(observed_total_under_null, bucket)|`). Pre-register the same G1–G8, plus G9: learned probe must outperform matched-random under online training (the test that 17A could not perform). Expected outcome: stronger differentiation, with the V_probe debiasing fixing the saturation failure; the question of whether online data shaping recovers selective-attribution-gain becomes empirically tractable.

**Paper 17B (vector self/world)**: combine [Paper 15's vector ΔV head](../valence_tapestry/paper.md) with Paper 16b's anchor mechanism. Two internal variables (E, D); per-dimension self and world heads; null anchors per-dimension. Gates: per-dimension component MAE ≤ 0.10, zero-shot reweighting under shifted priorities, and a parallel of 17A's "selection beats volume" test for the vector case. This composes existing wins rather than attacking the open frontier, so it is methodologically safer but advances the program less.

The author's recommendation is **17A-online** because it directly attacks the bottleneck this paper identified. The autonomous identifiability question is the program's current frontier; partially answering it here only sharpens the next test.

## References (external)

- Bennett, M. T. (2023). *On the computation of meaning, language models, and incomprehensible horrors.* Synthese 201, 75.
- Locatello, F., Bauer, S., Lucic, M., Rätsch, G., Gelly, S., Schölkopf, B., & Bachem, O. (2019). *Challenging common assumptions in the unsupervised learning of disentangled representations.* ICML.
- Levin, M. (2022). *Technological Approach to Mind Everywhere: An experimentally-grounded framework for understanding diverse bodies and minds.* Frontiers in Systems Neuroscience.
- Vervaeke, J. (2019). *Awakening from the Meaning Crisis.* Lecture series.

## References (program companion)

- Paper 14b — Calibrated Ensemble Uncertainty in Allostatic Planning — `papers/ensemble_uncertainty/paper.md`
- Paper 15 — Tapestry of Valence — `papers/valence_tapestry/paper.md`
- Paper 16 — First-Order Self / Reafference — `papers/first_order_self/paper.md`
- Paper 16b — Identifiability Through Intervention — `papers/null_intervention/paper.md`

## Pre-registration

`papers/costly_null_probes/preregistration.md` — frozen 2026-06-11, committed at scaffold time (commit `a4439cd`) before any Modal cell ran.

## Artifacts

- `artifacts/costly_null_probes/sweep_v1.json` — raw cell results
- `artifacts/costly_null_probes/verdicts_v1.json` — gate-by-gate pass/fail
- `papers/costly_null_probes/figures/*.png` — fig1–fig5
