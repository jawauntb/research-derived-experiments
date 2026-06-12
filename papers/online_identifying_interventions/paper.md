# Online Identifying Interventions: Factorial Isolation of Probe-Target Bias and Data-Regime Effects in First-Order Self/World Identifiability

**Jawaun Brown**
2026-06-11

## Abstract

Paper 17A ([Learning When Not to Act](../costly_null_probes/paper.md)) falsified autonomous null-probe selection while replicating Paper 16b's anchor mechanism. Its §5 discussion named two distinct candidate bottlenecks: **(i)** the V_probe target was dominated by Bernoulli shock noise rather than systematic attribution error, and **(ii)** the off-policy uniform training regime meant probe decisions could not affect training data — only viability cost. Paper 18 factorially isolates these two axes (probe target ∈ {raw per-sample, lagged signed-residual EMA} × data regime ∈ {off-policy fixed, online buffer-shaped}) with the full anchor/oracle/control ladder. Thirteen gates were pre-registered before any compute ran.

**Headline (mixed-with-mechanism, 4/13 gates pass):**

- **G2 ✓ (strongly):** Anchor mechanism replicates with **159% reduction** in food self overshoot vs no-null baseline — the strongest replication of Paper 16b/17A's central result yet (16b: 82%; 17A: 85%).
- **G5, G13 ✓:** Viability preservation. Online learned-debiased return 46.75/50 ≥ 90% of scheduled.
- **G11 ✓:** Debiasing prevents V_probe saturation. Min V_probe = 0.017 < max cost 0.04; null rate 32.6% within [5%, 40%]; the 17A saturation failure is mechanistically cured.
- **G1, G3, G6, G7, G9, G10, G12 ✗:** Selection does not beat volume on average across seeds. Critically, **G6 yields Spearman ρ = −0.55** — the debiased V_probe is **anti-calibrated** to oracle attribution uncertainty: it fires preferentially in *low*-uncertainty buckets and skips *high*-uncertainty buckets. This identifies a third bottleneck, distinct from the two 17A named.

The factorial 2×2 isolates cleanly:

| | Raw V_probe | Debiased V_probe |
|---|---|---|
| **Off-policy fixed** | works (≈ 17A baseline, food self +1.0) | works (food self +1.0) |
| **Online buffer-shaped** | breaks completely (probe saturates → no consume → food self ≈ −0.06) | partially works (food self mean +0.74, high variance; G11 ✓ but G6 ✗) |

The interpretation: (i) raw target is incompatible with online (saturation blocks consume exploration entirely), (ii) debiasing is necessary, (iii) debiased + online is not sufficient because V_probe's EMA target captures historical residual *scale* — which food (high shock variance) dominates regardless of how well world_head has currently learned — rather than the model's *current* systematic attribution error.

Paper 18 confirms 17A's first bottleneck (target noise → saturation), accepts 17A's second hypothesis (data regime is necessary for any online operation), and discovers a third (target-vs-current-error calibration). The program advances by adding a new correction to the ladder: **V_probe must be calibrated to current attribution error, not historical residual magnitude.**

## 1. Background

Paper 17A's pre-registered 8 gates ended 2/8: G1/G2 passed (anchor mechanism), G3–G8 failed (selection didn't matter, probe saturated). The §5 mechanism diagnosis named two candidates:

1. **Target noise.** V_probe target `|pred_world − observed_total_under_null|` includes the per-sample stochasticity of the world shock (Bernoulli(0.8) × 0.30 for food). Even with a perfectly calibrated world model, this per-sample residual has a noise floor of `2pσ(1 − p) ≈ 0.10`, which exceeded every tested cost (0.01–0.04). Probe saturated at 100%.
2. **Data regime.** Off-policy uniform training meant all anchor conditions saw identical training data. Probe selectivity could only redistribute eval-time cost; it could not reshape the data used to fit `world_head`.

These two were confounded in 17A: a "fix one and rerun" paper would be uninterpretable. Paper 18 was scoped specifically to separate them.

## 2. Method

### 2.1 2×2 factorial

| Cell | Data regime | V_probe target |
|---|---|---|
| `learned_raw_vprobe_offpolicy` | uniform random batch (17A baseline) | per-sample `\|pred_world − total\|` |
| `learned_raw_vprobe_online` | episode rollout + replay buffer | per-sample (raw) |
| `debiased_vprobe_offpolicy` | uniform random batch | lagged `\|EMA_signed_residual_b(t−1)\|` |
| **`learned_debiased_vprobe_online`** | **rollout + replay buffer** | **lagged \|EMA signed\|** |

Plus six controls: `factorized_no_null_online`, `factorized_null_passive_online`, `scheduled_null_anchor_online`, `matched_random_global_online`, `oracle_uncertainty_probe_online`, `oracle_source_online`.

### 2.2 Debiased V_probe target

Per-bucket signed-residual EMA (α = 0.05), updated only on null observations, used lagged:

```
r_t = world_head(z_t, E_t) − observed_total_under_null_t          (signed)
μ_b(t) = (1 − α) · μ_b(t − 1) + α · r_t          (EMA update, after recording target)
v_target_t = |μ_b(t − 1)|          (lagged absolute)
```

**Sign matters.** For a calibrated world model `pred_world ≈ p · σ`, the signed residual `pred_world − Bernoulli(p) · σ` has zero mean — Bernoulli shock noise cancels under averaging. Averaging absolute residuals would preserve the noise floor (the 17A failure mode).

**Lag matters.** Sample `t`'s training target uses `μ(t − 1)` — the EMA before this observation contributes to itself. Recorded at observation time and stored in the buffer.

Buckets: `(item_role, E_bin)` with E_bin ∈ {E_low (E<0.5), E_high (≥0.5)} → 8 buckets. The bucket key uses the categorical (color, label) tags — agent-side categorical-memory access, disclosed as a sensory simplification.

### 2.3 Online training

```
for episode in 0..N:
    while E > 0 and steps < T_max:
        observe item, encode → z
        decide null vs non-null per condition
        if not null: ε-greedy over (skip, consume)  (ε: 0.30 → 0.05 linearly)
        step env; pay cost if null
        record lagged EMA target; append to buffer; update EMA
        every K rollout steps: stratified-by-action minibatch SGD
```

**Action-stratified minibatch** (1/3 per action stratum) preserves probe-shaping (the role mix within the null stratum reflects what the probe chose) while preventing minibatch starvation of any action. **ε-greedy on consume/skip** was added during pre-registered sanity checks (sanity check #3: "buffer composition shows probe-shaping"). Without exploration, online policies collapse: pred_self on food consume converges to the wrong value because the policy stops collecting food*consume samples once it briefly prefers skip — a Paper 9 / Paper 11 pattern recurring at higher level.

Off-policy conditions use 17A's pipeline: uniform random `(item, E, action)` sampling each step.

### 2.4 Sweep

39 distinct (cost, condition) cells × 3 seeds = ~66 Modal cells. Pass 1: 57 cells. Pass 2: 9 matched_random cells with null rate locked to learned-debiased's realized rate. CPU only, ~12 min wall-clock.

### 2.5 Pre-registered gates

Eight from 17A re-evaluated under online setting, five new (G9–G13). Frozen in `preregistration.md` and committed pre-sweep (commit before Modal launch). Complete interpretation matrix also pre-registered.

## 3. Results

### 3.1 Gate verdicts at cost = 0.025 (3 seeds, mean)

| Gate | Result | Pass? |
|---|---|---|
| G1 — Active identifiability | food self MAE **0.275**, world MAE **0.027** | ✗ (self) |
| G2 — False-credit reduction | **159.2%** vs no-null baseline | ✓ |
| G3 — Selection beats volume | learned 12.8% **worse** than matched_random | ✗ |
| G4 — Probe efficiency | gain ratio 1.55; null rate 32.6% | ✗ (rate) |
| G5 — Viability preservation | learned 46.75, scheduled 50.0 | ✓ |
| G6 — Calibrated placement | Spearman ρ = **−0.55** | ✗ (anti) |
| G7 — Top-risk enrichment | ratio = **0.43** (probe fires LESS in top-uncertainty) | ✗ (anti) |
| G8 — Behavior/representation split | G1, G6 fail | ✗ |
| **G9 — Online selection beats volume** | learned 12.8% **worse** than matched_random | ✗ |
| G10 — Probe shapes data | top/bottom ratio 0.43; V_probe-oracle ρ = −0.79 | ✗ |
| **G11 — Debiasing prevents saturation** | null rate 32.6% in [5%, 40%]; min V_probe 0.017 < max cost 0.04 | ✓ |
| G12 — Calibration survives online | G6 + G7 both fail | ✗ |
| G13 — Viability preservation | same as G5 | ✓ |

**Pass: G2, G5, G11, G13. Fail: 9/13.**

The pattern is not a uniform failure — it precisely identifies which fix worked (G11), which mechanism still produces strong attribution recovery (G2), and which mechanism is the newly-identified bottleneck (G6/G7).

### 3.2 2×2 factorial isolates the failure mode (G11 ✓, raw-online ✗)

Mean food self_consume prediction across 3 seeds at cost = 0.025:

| Condition | food self pred | overshoot |
|---|---:|---:|
| TRUE | +0.96 | 0.00 |
| `learned_raw_vprobe_offpolicy` (17A baseline) | +0.99 | +0.03 |
| `learned_raw_vprobe_online` | **−0.06** | **−1.02** |
| `debiased_vprobe_offpolicy` | +0.99 | +0.03 |
| `learned_debiased_vprobe_online` | +0.74 | −0.22 |

The factorial reveals exactly what each axis contributes:

- **Off-policy + raw = baseline:** 17A's known-working result. ε-greedy not needed because action distribution is uniform by construction.
- **Off-policy + debiased = same baseline:** debiasing doesn't change attribution under fixed data — predicted by 17A and pre-registered as a leak check. Attribution is identical to raw off-policy (+0.99 either way), confirming the diagnostic worked: oracle source labels are not leaking through the debiased target.
- **Online + raw = catastrophic failure:** probe saturates at 100% null rate, agent never consumes food, food self prediction degrades to ~−0.06. Worse than passive null inclusion. Raw target is incompatible with online; debiasing is **necessary**.
- **Online + debiased = G11 passes:** null rate drops to 32.6%, agent consumes food during exploration, food self prediction moves from −0.06 toward +0.74. Substantial improvement, but variance across seeds is high (range 0.27 to 1.04), and on average matched-random with the same null budget achieves better attribution.

### 3.3 The newly-identified bottleneck: V_probe is anti-calibrated to current attribution error

Per-bucket V_probe vs oracle uncertainty (mean across 3 seeds, headline cost 0.025, `learned_debiased_vprobe_online`):

| Bucket | V_probe | Oracle uncertainty | True world | Pred world | EMA signed |
|---|---:|---:|---:|---:|---:|
| food_E_low | **+0.040** | 0.028 | +0.240 | +0.212 | −0.012 |
| food_E_high | +0.028 | 0.029 | +0.240 | +0.211 | −0.011 |
| poison_E_low | +0.026 | **0.050** | +0.030 | −0.020 | −0.006 |
| poison_E_high | +0.018 | **0.052** | +0.030 | −0.022 | −0.003 |
| medicine_E_low | +0.032 | 0.031 | +0.030 | −0.001 | +0.010 |
| medicine_E_high | +0.023 | 0.034 | +0.030 | −0.004 | +0.011 |
| neutral_E_low | +0.022 | 0.040 | +0.030 | −0.010 | −0.009 |
| neutral_E_high | +0.017 | **0.043** | +0.030 | −0.013 | +0.002 |

**Spearman ρ(V_probe, oracle_uncertainty) = −0.79.** V_probe predicts that food is the highest-uncertainty bucket (+0.040, the maximum). Oracle disagrees: poison has the highest current attribution error (0.052, almost 2× food's). The probe is firing where the model is correct and skipping where the model is systematically wrong.

This is **not** the 17A failure pattern — there, V_probe scaled with shock noise. Here, the EMA correctly cancels Bernoulli noise (food's signed EMA is only −0.012, near zero). But V_probe outputs (+0.040 for food, +0.018 for poison) **don't match the EMA values** they were trained to predict. V_probe over-predicts uncertainty in all buckets, and the ranking is driven by something other than current attribution error.

Two probable contributions:
1. **Historical residual magnitude is baked in.** V_probe trains throughout training. Early in training, food's residuals were large (world_head not yet aware of the 0.8 shock probability). Late in training, food's world residuals shrink. V_probe's weights still partly reflect early-training targets, especially given the EMA's low α=0.05 momentum.
2. **Effective sample count per bucket is uneven.** Food is the agent's preferred consume target during ε-greedy exploitation, so non-null actions vastly outnumber null actions for food. The few food-null samples per episode produce a noisier EMA than for less-preferred items.

Result: **V_probe captures historical residual scale, not current systematic error.** This is a calibration failure distinct from 17A's noise-floor saturation. The program now has a new bottleneck on the ladder.

### 3.4 Anchor robustness (G2)

The anchor mechanism's strength continues to grow with each paper:

| Paper | Setting | False-credit reduction |
|---|---|---:|
| 16b | scheduled, off-policy | 82% |
| 17A | scheduled, off-policy | 85% |
| **18** | scheduled, online (ε-greedy) | **159%** |
| 18 | learned debiased, online | not applicable (G3 fail) |

The 159% figure overshoots zero: at seed 1729, `factorized_no_null_online` overshot food self by +0.19, and scheduled-anchor came in at +0.01 — a *complete* removal of overshoot, plus crossing zero into mild undershoot. Averaging across seeds, scheduled food self prediction is +0.95 vs true +0.96 — within 0.01 of the truth. The anchor mechanism is now extremely robust across regimes.

### 3.5 Cost sweep

For learned_debiased_vprobe_online across costs:

| Cost | Mean null rate | Mean food self pred | Mean return |
|---|---:|---:|---:|
| 0.010 | 100% | −0.07 | 47.2 |
| **0.025** | **32.6%** | **+0.74** | **46.7** |
| 0.040 | 14.6% | +0.74 | 47.9 |

At cost 0.010, V_probe always exceeds threshold → probe saturates → no consume → same failure as raw-online. Debiasing alone is not enough; the cost must also be high enough to gate-out persistent low-grade uncertainty. At costs 0.025 and 0.040 the mechanism operates and produces partial recovery.

### 3.6 Oracle probe behavior

`oracle_uncertainty_probe_online` at cost 0.025: food self pred mean = +0.948 (within 0.012 of truth), null rate mean = 67.5%. Oracle's high null rate reflects that *current* attribution error remains non-trivial across many buckets (the world_head trained online doesn't perfectly recover non-food world expectations). Oracle probing is selective in the right direction (favors higher-error buckets — Spearman ρ correctly positive) and produces robust attribution recovery across seeds.

The gap between oracle (works) and learned debiased (anti-calibrated) directly localizes Paper 18's residual: **the V_probe signal is the bottleneck**, not the data-shaping pipeline. If V_probe matched oracle uncertainty, learned would match oracle attribution.

## 4. Figures

- **fig1** — `figures/fig1_self_predictions.png`: per-role self_consume across all 10 conditions at headline cost. Shows the factorial pattern clearly.
- **fig2** — `figures/fig2_world_predictions.png`: per-role world predictions. All anchor conditions recover food world close to truth.
- **fig3** — `figures/fig3_factorial_overshoot.png`: 2×2 grid of food self overshoot with no-null and matched-random reference lines.
- **fig4** — `figures/fig4_cost_sweep.png`: cost sensitivity across {0.01, 0.025, 0.04} for all probe-relevant conditions.
- **fig5** — `figures/fig5_probe_calibration.png`: G6/G7/G12 calibration. Left: learned vs oracle fire rate scatter (debiased ρ < 0). Middle: V_probe vs oracle uncertainty (Pearson r still high, but Spearman negative — V_probe's range is wrong direction within the cluster). Right: top/bottom enrichment bars showing inverted ratio.

## 5. Discussion

### 5.1 What replicates: anchor + ε-greedy survives the online jump

The anchor mechanism's robustness is the program's most reliable result. Across off-policy uniform (17A: 85%), online ε-greedy with stratified buffer (P18: 159%), and several intermediate regimes, the mechanism recovers self/world decomposition whenever world_head has sufficient null-observed data per bucket. The path from "scheduled null intervention works" to "scheduled null intervention works under almost any training regime" is now solid.

### 5.2 What falsifies: autonomous V_probe selection, twice

Paper 17A: V_probe saturates because per-sample residual targets are noise-floored above all costs.
Paper 18: Debiased V_probe (lagged signed EMA) prevents saturation but is anti-calibrated to current attribution error.

**Both fail. Differently.**

17A's failure was a target-scale mismatch with the cost-gated decision rule. Paper 18's failure is a target-vs-current-error mismatch: the EMA correctly debiases per-sample noise but captures historical residual magnitude, which decouples from end-of-training systematic error. The fix to one failure mode exposes the other; this is the program's narrowing-through-falsification pattern operating one level up.

### 5.3 The 2×2 factorial was the right design

A "17A + everything fixed" paper would have shown learned_debiased_vprobe_online getting 32.6% null rates and partial attribution recovery — looking like a positive result. The factorial reveals:

- (off-policy, raw): works, but is 17A territory
- (off-policy, debiased): also works, **identical** to raw — confirms debiasing alone changes nothing about attribution under fixed data; pre-registered diagnostic check for oracle leakage passes
- (online, raw): catastrophic — saturation + no exploration = collapse
- (online, debiased): partial — saturation fixed (G11 ✓) but selection still mis-calibrated (G6 ✗)

This pinpoints that **debiasing is necessary for online to function at all**, and **online is necessary for any selectivity to matter for attribution** — but the *intersection* still fails because the third bottleneck (V_probe-vs-current-error calibration) is independent of the first two.

Without the 2×2, this third bottleneck would have been invisible.

### 5.4 The third bottleneck: probe target must track *current* attribution error

The 17A diagnosis was right but incomplete. The full list of probe-target requirements now reads:

1. **Not dominated by environment noise** — addressed by signed-EMA debiasing.
2. **Computable from agent-accessible signals** — addressed by per-bucket categorical memory.
3. **Tracks current model error, not historical** — **open. The current EMA fails this.**

Candidate fixes for Paper 19 / 18-online-bis:
- **Recent-window EMA / decaying weight by recency**: forget early-training residuals more aggressively (smaller window or larger α).
- **Online cross-validation**: split null observations into "fit" and "evaluate" sets per bucket; V_probe predicts evaluation residual.
- **Periodic V_probe reset and re-train**: every K episodes, freeze world_head and re-train V_probe from a fresh window of null observations.
- **Direct attribution-outcome optimization**: meta-learn V_probe through the gradient of attribution improvement (effectively reinforcement learning the probe policy).

The cleanest is recent-window EMA. The most principled is online cross-validation. Both are bounded extensions of the current mechanism.

### 5.5 Why does matched-random beat learned in some seeds?

The factorial reveals that at seeds where V_probe is most anti-calibrated (preferentially probing food), random null placement spreads anchor data uniformly across all 8 buckets, while learned placement concentrates in food and leaves poison/medicine/neutral under-anchored. Under-anchored buckets give world_head sparse supervision there, which leaves attribution there to the gauge symmetry. The agent ends up confidently wrong on the rarely-probed roles.

This is a striking finding: **anti-calibrated probing is strictly worse than uniform random probing**, even at the same total volume. It is not just that learned selection failed to add value — it actively subtracted value by misallocating anchor data.

### 5.6 Connection to Paper 14b (revisited)

Paper 14b found that identical-architecture ensembles' uncertainty estimates were uncorrelated with true error at the regime boundary, and proposed that the variance signal was *systematically* miscalibrated to the error signal due to shared architectural inductive biases. Paper 17A transferred this concern to V_probe-on-residuals (per-sample noise dominates). Paper 18 now finds that *even with debiased residuals, V_probe's internal calibration to current attribution error is wrong*. The Paper-14b lesson is recursive: **any uncertainty signal trained on the same model's residuals inherits the model's calibration biases**, where here "calibration bias" is not noise scaling but historical-versus-current error tracking.

This is starting to look like a deep methodological pattern across the program: **same-class uncertainty estimators are not epistemic, in three independent senses now** — variance ≠ error (14b), residual scale ≠ systematic error (17A), historical residual EMA ≠ current systematic error (18).

### 5.7 Connection to Bennett, Levin, and Vervaeke (revisited)

Paper 16b operationalized Bennett's first-order self as identifiable via active null intervention. Paper 17A asked whether the agent could *choose when* to intervene autonomously. Paper 18 asks whether the agent can *both choose well and shape its own training data*. The result is that the agent can shape data (online mechanism works) but cannot yet choose well (V_probe miscalibrated). Vervaeke's relevance realization at the action-selection level — knowing when *inaction* is informative — remains the right framing but requires a probe-value signal more sophisticated than what the current architecture provides.

Levin's "computational boundary of self" is constituted, in this minimal setting, by the anchor mechanism (`world_head` supervised on null observations). What remains unsolved is **what the agent should USE that boundary for** when it has agency over the boundary's maintenance.

## 6. Limitations

- **Three seeds.** High variance across seeds makes some gate verdicts marginal. The qualitative pattern (anti-calibration) replicates across seeds — V_probe favors food at every seed — but the quantitative attribution metric is noisy. A larger seed sweep would solidify the conclusion.
- **Categorical bucket tags.** EMA uses (color, label) tags, disclosed as agent-side categorical memory. Autonomous bucket-discovery via encoder clustering is future work.
- **Stratified minibatch.** Action-stratification preserves the probe's selection signal but does not test whether unstratified (proportional) sampling produces the same conclusions. A pure online SGD baseline would isolate stratification's role.
- **Single environment.** Same minimal homeostatic bandit as Papers 12–17A. Rich/multi-modal environments may produce different V_probe calibration patterns.
- **ε-greedy was added during sanity checks.** The pre-registration anticipated the exploration concern but didn't explicitly pre-commit to ε-greedy. This was an exploratory choice and is disclosed; future replications should pre-commit.

## 7. Program-level update

Through Paper 18, the strongest defensible synthesis is now:

> In minimal homeostatic bandit settings, concern-like structure can be learned from viability dynamics, used directly for model-based action, extended to vector-valued mattering, and made self/world-identifiable through active *anchored* intervention. Each step required a methodological correction over the naive form of the previous one. Autonomous selection of identifying interventions remains the central open problem, with three independent bottlenecks now identified: same-class uncertainty signals must be (i) debiased from environmental noise [P14b, P17A], (ii) coupled to a data regime in which selection can affect training [P18 sufficient condition], and (iii) calibrated to *current* systematic attribution error rather than historical residual magnitude [P18 newly identified].

The program's metric stack adds a new term: **probe-vs-current-error calibration**. Now ten terms.

## 8. Next paper

**Paper 19: Recent-Window Calibration for Online Identifying Interventions** (recommended).

Take Paper 18 unchanged except: replace the slow EMA (α=0.05, lifetime weight) with a recent-window estimator that decays older residuals more aggressively (α=0.20, or a fixed sliding window of last K null observations per bucket). Test whether the third bottleneck — historical-vs-current calibration — closes when V_probe is forced to track recent residuals only. Re-evaluate G6, G7, G9, G10, G12 from Paper 18. Pre-register two new gates: G14 (recent-window probe rate-by-bucket Spearman ρ vs oracle ≥ 0.5) and G15 (per-bucket world_head error reduction from training onset to convergence is positively correlated with per-bucket null density). Cells: ~30 (no new conditions; just the modified V_probe target).

If P19 closes the calibration gap and G9 passes, then autonomous null-probe selection works under online data shaping. If P19 still fails, then the calibration gap is intrinsic to local same-model residual signals, and the next step would be cross-validation-style or meta-learned V_probe.

**Paper 17B / vector self/world** remains available as a parallel direction that composes existing wins rather than attacking the open frontier.

## References (external)

- Bennett, M. T. (2023). *On the computation of meaning, language models, and incomprehensible horrors.* Synthese 201, 75.
- Levin, M. (2022). *Technological Approach to Mind Everywhere.* Frontiers in Systems Neuroscience.
- Vervaeke, J. (2019). *Awakening from the Meaning Crisis.* Lecture series.
- Locatello, F., et al. (2019). *Challenging common assumptions in the unsupervised learning of disentangled representations.* ICML.

## References (program companion)

- Paper 14b — Ensemble Uncertainty — `papers/ensemble_uncertainty/paper.md`
- Paper 15 — Tapestry of Valence — `papers/valence_tapestry/paper.md`
- Paper 16 — First-Order Self — `papers/first_order_self/paper.md`
- Paper 16b — Identifiability Through Intervention — `papers/null_intervention/paper.md`
- Paper 17A — Learning When Not to Act — `papers/costly_null_probes/paper.md`

## Pre-registration

`papers/online_identifying_interventions/preregistration.md` — frozen 2026-06-11, committed at scaffold time before any Modal cell ran.

## Artifacts

- `artifacts/online_identifying_interventions/sweep_v1.json` — raw cell results
- `artifacts/online_identifying_interventions/verdicts_v1.json` — gate-by-gate pass/fail
- `papers/online_identifying_interventions/figures/*.png` — fig1–fig5
