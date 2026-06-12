# Paper 18 — Pre-Registration

**Title (working):** Online Identifying Interventions: Factorial Isolation of Probe-Target Bias and Data-Regime Effects in First-Order Self/World Identifiability

**Frozen:** 2026-06-11, before any Modal sweep runs.

## Question

Paper 17A falsified autonomous null-probe selection on six of eight pre-registered gates, while replicating Paper 16b's anchor mechanism at 85% false-credit reduction. The §5 discussion named **two distinct candidate bottlenecks**:

1. **Bad probe target.** V_probe trained on per-sample `|pred_world − observed_total_under_null|` is dominated by Bernoulli shock noise. Its minimum value (~0.06) exceeds every tested cost (0.01–0.04), so the cost-gated rule never engages. Within homoscedastic clusters, V_probe cannot rank states (Spearman ρ = +0.21).

2. **Wrong data regime.** Off-policy uniform training means all anchor conditions see identical data. Probe selectivity cannot affect attribution quality, only viability cost. To test whether autonomous probing genuinely shapes identifiability, the agent's probe decisions must determine training-buffer composition.

A "previous paper + both fixes at once" design would confound the two. **Paper 18 must factorially isolate them** before the program can claim either lever is load-bearing.

## Core design: 2×2 factorial

| | **Probe target: raw residual** | **Probe target: lagged signed-residual EMA** |
|---|---|---|
| **Data regime: off-policy fixed** | `learned_raw_vprobe_offpolicy` (replicates 17A) | `debiased_vprobe_offpolicy` (diagnostic) |
| **Data regime: online buffer-shaped** | `learned_raw_vprobe_online` | **`learned_debiased_vprobe_online` (HEADLINE)** |

Predicted outcomes per cell:
- **(raw, off-policy)**: 17A failure pattern — saturates above cost.
- **(debiased, off-policy)**: G6/G7 calibration should improve; attribution should NOT improve (fixed data). If attribution improves, oracle source labels are leaking.
- **(raw, online)**: Data-shaping might rescue attribution even with noisy probe target if online updates absorb the placement signal anyway.
- **(debiased, online)**: Both fixes together. The decisive test of G9.

## Full condition ladder (10)

| Condition | Role |
|---|---|
| `factorized_no_null_online` | Paper 16 gauge-symmetric failure baseline |
| `factorized_null_passive_online` | Null inclusion without anchor |
| `scheduled_null_anchor_online` | Experimenter-scheduled anchor (P16b positive control) under online training |
| `matched_random_global_online` | Same total null count as headline, random placement (Pass 2) |
| `learned_raw_vprobe_offpolicy` | 17A replication / 2×2 cell |
| `learned_raw_vprobe_online` | 2×2 cell: online data, raw target |
| `debiased_vprobe_offpolicy` | 2×2 cell: off-policy data, debiased target (diagnostic) |
| **`learned_debiased_vprobe_online`** | **MAIN.** 2×2 cell: online + debiased |
| `oracle_uncertainty_probe_online` | Upper bound on probe placement (no source label leakage) |
| `oracle_source_online` | Per-sample self/world labels (P16b upper bound) |

## Debiased V_probe target

**Target form (frozen):**
```
r_t = world_head_old(z_t, E_t) − observed_total_under_null_t       (signed residual)
μ_b(t) = EMA over null observations within bucket b, momentum α=0.05
v_target_t = |μ_b(t − 1)|                                          (LAGGED absolute)
```

Critical design choices:

- **Sign matters.** Averaging signed residuals cancels zero-mean Bernoulli shock noise (`E[σB(p) − pσ] = 0` for a calibrated world model). Averaging absolute residuals preserves the noise floor (which is what 17A's V_probe ate).
- **Lag matters.** Sample t's training target uses EMA up to t−1. The current observation cannot contribute to its own target. This is recorded at observation time as `lagged_ema_target_t` and stored alongside the sample in the replay buffer.
- **Keep target in ΔE units.** No variance normalization in v1; the target is then directly comparable to per-null action cost.

The raw V_probe target (17A) is the per-sample `|pred_world − observed_total|`. Other than the target, V_probe architecture is identical across all variants (`Linear(EMBED+7, 32) → Tanh → Linear(32, 1) → Softplus`).

## Online training implementation

Episode rollout + replay buffer + action-stratified minibatch SGD.

```
repeat for N_EPISODES:
    initialize E = ENERGY_INIT, steps = 0
    while E > 0 and steps < T_MAX:
        observe item (c, l), encode → z
        decide action ∈ {skip, consume, null} using current model + V_probe + cost
        step env → (self_step, world_step, total = self_step + world_step)
        if action == NULL: apply cost
        if action == NULL: record lagged μ_b(t−1) as v_target before updating EMA
        append (obs_raw, E, action, total, c, l, E_bin, lagged_v_target) to buffer
        if action == NULL: update EMA bucket μ_b
        every K rollout steps: sample stratified minibatch from buffer, SGD update
        E += total
        steps += 1
```

**Stratification: by ACTION only.** Each minibatch contains roughly 1/3 null, 1/3 skip, 1/3 consume samples. Within each stratum, samples are uniform random from the buffer's entries of that action. **This preserves the probe's data-shaping effect** (probe decisions determine which roles appear in the null stratum) while preventing minibatch starvation of any action type.

Off-policy conditions skip the rollout entirely and sample (item, E, action) uniformly each step, as in 17A. This isolates the data-regime axis cleanly.

## Bucket definition (G6, G7, G10, G12)

Buckets: `(c, l, E_bin)` where E_bin ∈ {E_low (E<0.5), E_high (E≥0.5)}. Total = 4 items × 2 E_bins = 8 buckets.

The bucket key uses the discrete categorical item identity (c, l), not the noisy observation features. **This is an agent-side categorical-memory simplification** — the agent gets oracle access to a discrete item identifier without sensory noise, used only for EMA bookkeeping. This is disclosed in §6 of the paper. The autonomous-perception-discovery extension is out of scope for Paper 18.

## Cost sweep

`cost ∈ {0.01, 0.025, 0.04}`. Headline = 0.025. Same regime as 17A.

## Sample budgets

- Online conditions: 100 episodes × ~30 average steps = ~3000 buffer entries. SGD: every 30 rollout steps, K=4 SGD steps with batch_size=48 (stratified into 16/16/16 by action), total ~400 SGD updates.
- Off-policy conditions: 1500 SGD updates × 64 batch as in 17A.
- Both regimes see comparable total gradient steps. NOT identical sample counts — online sees fewer total samples by design, mirroring real homeostatic constraints.

## Sanity checks (single seed, before full sweep)

Run `learned_debiased_vprobe_online` at seed=20260610, cost=0.025 only. Require all of:
1. Debiased V_probe minimum value < at least one tested cost (i.e., < 0.04). If V_probe still saturates at 100% null rate, EMA is misconfigured.
2. Learned null rate ∈ [3%, 95%]. Neither uniform 0 nor uniform 1.
3. Buffer composition shows probe-shaping: per-bucket null density correlates with V_probe (Spearman ρ ≥ 0.3).
4. Anchor losses still recover Paper 16b decomposition: scheduled_null_anchor_online food self overshoot ≤ +0.20.
5. No oracle source label appears in any non-oracle condition's loss (code grep).
6. Bucket EMA uses categorical (c, l) tag, not simulator-private state.

If any sanity check fails, fix and rerun. **Do not launch full sweep until all six pass.**

## Pre-registered gates

### From 17A (re-evaluated under online setting)

| Gate | Criterion |
|---|---|
| G1 | learned (online debiased) food self MAE ≤ 0.12 AND world MAE ≤ 0.10 |
| G2 | ≥ 70% reduction in food self overshoot vs `factorized_no_null_online` |
| G3 | learned MAE ≥ 25% lower than matched_random_global_online at same null budget |
| G4 | learned reaches ≥ 80% of scheduled-anchor gain with null rate ≤ 20% (online setting) |
| G5 | learned return ≥ 90% of scheduled AND ≥ 45/50 absolute |
| G6 | Spearman ρ ≥ 0.5 of learned vs oracle null rates per bucket |
| G7 | top-quartile/bottom-quartile probe rate ratio ≥ 2× |
| G8 | G1 ∧ G6 must pass for mechanistic success |

### New (Paper 18 specific)

| Gate | Criterion | Tests |
|---|---|---|
| **G9 — Online selection beats volume** | `learned_debiased_vprobe_online` total component MAE ≥ 25% lower than `matched_random_global_online` at matched total null count | Decisive new test. 17A could not perform this; online data-shaping makes it possible. |
| **G10 — Probe shapes data** | (a) Per-bucket null density in top-quartile-oracle-error buckets ≥ 2× of matched-random in those buckets. (b) Per-bucket world-head error reduction over training is correlated with per-bucket null density (Pearson r ≥ 0.5) | Confirms probe-shaping translates to attribution gain |
| **G11 — Debiasing prevents saturation** | (a) Learned null rate at cost 0.025 ∈ [5%, 40%]. (b) Min V_probe value < max tested cost (0.04) | The 17A failure-of-debiasing should be specifically fixed |
| **G12 — Calibration survives online** | (a) Spearman ρ ≥ 0.5 between learned null rate by bucket and oracle uncertainty by bucket. (b) Top/bottom enrichment ≥ 2× | Subsumes G6+G7 specifically for online setting |
| **G13 — Viability preservation** | Online return ≥ 90% of `scheduled_null_anchor_online` AND ≥ 45/50 absolute, UNLESS explicitly reporting negative viability tradeoff | Prevents accidental self-harm |

## Pre-registered interpretation matrix

| Result pattern | Interpretation |
|---|---|
| Headline passes G1–G13 | **Strong positive.** Autonomous probing with debiased V_probe under online data-shaping recovers first-order self/world identifiability beyond matched-volume placement. |
| Debiased off-policy improves G6/G12 calibration but not G1 attribution | Correct prediction: debiasing fixes the calibration axis; fixed data prevents attribution gain. Confirms 2×2 logic. |
| Debiased online improves G1 attribution but G9 fails (matched-random matches it) | Agent learns where uncertainty is, but its placement still does not matter — confirms 17A's "volume dominates placement" verdict survives online training |
| Oracle online passes G10 but learned online fails G9 | Identifying probes are sufficient; learned uncertainty signal is still the bottleneck (debiasing didn't go far enough) |
| Raw online passes G9 | 17A's noise-target diagnosis was wrong; data-shaping alone was the load-bearing fix. Major program revision. |
| Debiased online STILL saturates (G11 fails) | EMA target is still estimating noise/scale, not systematic error. Move to richer uncertainty signal (cross-validation residuals, perturbation-based, etc.) |
| High return but G1 fails | Paper 16 failure pattern repeats — behavior without intended attribution. Paper 18 has not advanced the program. |
| Oracle online fails G1 | Null-probe identifiability is brittle under online viability constraints; the 16b/17A result depended on off-policy stability. |
| All learned conditions fail | The autonomous-identifiability claim is brittle in the minimal setting; need richer environment or richer uncertainty signal. |

## Cell budget

- Pass 1 (parallel):
  - Cost-irrelevant (4 conds × 1 cost × 3 seeds) = 12
  - Cost-relevant non-matched (5 conds × 3 costs × 3 seeds) = 45
  - Pass 1 total: 57
- Pass 2 (parallel, sequenced): matched_random_global_online with rate from headline = 3 costs × 3 seeds = 9
- **Total: 66 Modal cells, CPU only.**

## What success and failure look like

**Strong positive** (G1–G13 all pass at cost 0.025 for `learned_debiased_vprobe_online`): the program advances from "intervention data, scheduled" → "intervention data, learned via autonomous data-shaping with debiased uncertainty". Removes both crutches the 16b/17A trajectory identified.

**Mixed positive** (G1–G2 pass at strong magnitude, G9 fails but G10/G11/G12 pass): debiasing fixes calibration, online data-shaping engages, but placement gain is small. Honest result. Program advances by clarifying that *which* probe target / how much data-shaping helps is task-specific.

**Strong negative** (G9 fails, G10 fails): "selection doesn't matter, even with debiased target and online data shaping." The program's autonomous-identifiability arc terminates here, and the next direction is multi-valence (17B) or a richer uncertainty signal.

Any outcome is publishable. All outcomes narrow the program.
