# Paper 23A — Pre-Registration

**Title (working):** Probe Value and Re-Engagement: Learning When to Ask Again in Responsive Worlds

**Frozen:** 2026-06-12, before any Modal sweep runs.

## Question

Paper 22 made two findings that reshape the program:

1. **Current attribution error ≠ value of probing.** `oracle_probe_value` using current error as the signal achieved final lc_MAE 0.463 — **5× worse** than learned probing's 0.091. Every program oracle_X condition since Paper 17A has used current error and was therefore a confounded baseline.

2. **G7 failure: probe doesn't re-engage post-shift.** Learned probing dropped to **0 affected-bucket probes** after the regime-shift episode 250, despite the world's hazard structure having genuinely changed. The current V_probe is backward-looking and self-silencing: once it stops probing, it stops collecting the data that could tell it the world changed.

Paper 23A addresses both:

> Can an agent learn (i) a probe-value signal grounded in *marginal MAE reducibility*, not current error, AND (ii) a re-engagement mechanism that notices when its self/world boundary has become stale and re-opens identifying interventions, while preserving the "stop when not needed" behavior that made P19/P21A clean?

## Two conceptual upgrades

### Upgrade 1: Principled probe-value oracle

Replace the current-error oracle with an oracle that estimates **expected MAE reduction from one more intervention at bucket b**:

```
oracle_probe_value_single_null(b) ≈ |current_world_error_b|² · 1 / (K_b + 1)
```

where K_b is the current null count at bucket b. This is the standard shrinkage logic: adding one sample to a bucket of K reduces variance by approximately 1/(K+1), and the error² scales the magnitude. High error AND low K → high value of probing.

**Sequence-aware variant** for action-correlated worlds: probe value is boosted when current history matches a known trigger pattern (recent trigger consume → null-readout reveals mediated effect):
```
oracle_probe_value_sequence(b, history) ≈
    oracle_probe_value_single_null(b)
    + bonus · I[recent_trigger_consume_in_history]
```

Both oracles use simulator-derived ground truth (the true world component for the bucket). Learned probes only see observable residuals.

### Upgrade 2: Two-timescale V_probe + prediction-error boost

The current V_probe is the single-timescale current_replay target from P21A. Paper 23A extends:

- **Slow EMA** (α=0.05) of signed residuals per bucket — long-term world model error
- **Fast EMA** (α=0.25) of signed residuals per bucket — recent error
- **Shift signal**: `shift_b = max(0, |fast_b| − |slow_b| − margin)` with margin=0.02. Captures "the world recently became less predictable for this bucket."
- **Surprise from non-null actions**: EMA (α=0.10) of total_dE prediction residual when action ≠ null. **This is the critical addition** — it bypasses the self-silencing trap: the agent can detect "the world changed" from non-null observations alone, without needing to have probed recently.

Composite probe score per bucket per dim:
```
score_b,d = base_vprobe_b,d  + λ_shift · shift_b,d  + λ_surprise · non_null_surprise_b,d
```

Decision (per dim, in normalized units):
```
take_probe = (score_b,d / scale_d) > tau_d
```

with λ_shift = 2.0, λ_surprise = 1.0 (frozen pre-sweep).

## Conditions (9)

| Condition | V_probe / oracle signal | Re-engagement |
|---|---|---|
| `p22_learned_current_replay` | P21A scale-normalized current_replay (the P22 headline) | none — reproduces G7 failure |
| `current_error_oracle` | oracle access to `\|pred_world − true_world\|` | none |
| `true_probe_value_oracle_single_null` | oracle: `(error²) / (K + 1)` | implicit via K |
| `true_probe_value_oracle_sequence` | single_null + trigger-history bonus | implicit |
| `two_timescale_vprobe` | base + shift signal (no surprise term) | partial |
| **`two_timescale_plus_prediction_error`** | **HEADLINE.** base + shift + non-null surprise boost | full |
| `matched_random_time_budget` | uniform random null at headline rate per episode | n/a |
| `scheduled_null_anchor` | scheduled 33% null | n/a (positive control) |
| `oracle_source` | per-sample direct/mediated/exogenous labels | n/a (semantic upper bound) |

3 seeds × 9 conditions = 27 Modal cells. CPU only.

## Environment

Carry over Paper 22's action-correlated env. **Bump κ from 0.30 to 0.60** (per Paper 22's own §6.2: "stronger coupling is likely needed to make the architectural distinction decisive"). All other env params unchanged.

Regime shift at episode 250 (food trigger → medicine trigger). 500 total episodes per cell.

## Three-head architecture as default

All conditions use the three-head architecture from Paper 22:
- `direct_self_head(z, ffE, ffD, action) → 2`
- `mediated_world_head(z, ffE, ffD, hist_feats) → 2`
- `exogenous_world_head(z, ffE, ffD) → 2`

Total predicted ΔE/ΔD = direct + mediated + exogenous.

**New for P23A**: explicit identifiability tests on the mediated/exogenous split (see G8 below).

## Carried from P22 (unchanged)

- Online rollout + 50-episode warmup with uniform 33% null sampling
- ε-greedy 0.50 → 0.10 + action-stratified minibatch SGD
- Per-bucket current_replay buffer K=64
- Scale-normalized targets per dim
- Per-dim threshold calibration from warmup percentiles

## Headline metrics (frozen pre-sweep)

Drop "final lc_MAE" as headline. Use:

1. **post_shift_recovery_AUC**: sum of food_E + poison_D MAE checkpoints over episodes 250–500. Lower = faster recovery.
2. **time_to_recover**: episode at which post-shift MAE first drops below 0.10.
3. **cumulative_probe_cost_to_recover**: total nulls between episode 250 and time_to_recover.
4. **affected_vs_unaffected_probe_ratio**: post-shift null density in affected buckets (food, medicine) divided by post-shift density in unaffected (poison, neutral).

## Sanity checks (one seed, before full sweep)

Run `two_timescale_plus_prediction_error` at seed 20260610. Require:

1. Hazard state varies (range ≥ 0.2 within an episode at κ=0.60)
2. Regime shift visible: pre-shift vs post-shift average h(t) differ
3. Two-timescale signals produce non-trivial values: max bucket fast-EMA ≠ slow-EMA after warmup
4. Non-null prediction-error EMA tracks actual surprise (positive correlation with true_world - pred_world residuals)
5. Post-shift, headline null rate rises in affected buckets within 30 episodes (preview of G4)
6. Anchor still recovers attribution: scheduled food self_E MAE ≤ 0.10

## Pre-registered gates (frozen)

| Gate | Criterion |
|---|---|
| **G1 — P22 replication** | `p22_learned_current_replay` reproduces P22: efficient early probing, ~0 affected-bucket probes post-shift |
| **G2 — Corrected oracle sanity** | `true_probe_value_oracle_single_null` post-shift recovery AUC ≥ 50% lower than `current_error_oracle` |
| **G3 — Sequence oracle value** | `true_probe_value_oracle_sequence` recovers ≥ 15% better post-shift AUC than `single_null` IF mediated identification requires triggers (otherwise: equivalent within noise) |
| **G4 — Re-engagement** | Headline learned fires in affected buckets within 25 episodes post-shift AND reaches ≥ 50% of early-training affected-bucket probe density (or ≥ 3× unaffected-bucket density) |
| **G5 — Recovery speed** | Headline reaches post-shift MAE ≤ 0.10 at least 30% faster (in episodes) than `matched_random_time_budget` |
| **G6 — Probe efficiency** | Headline uses ≤ 25% of `matched_random_time_budget`'s null count to reach comparable post-shift MAE |
| **G7 — Learned near-oracle** | Headline post-shift AUC within 20% of `true_probe_value_oracle_single_null` (i.e., learned ≥ 80% of oracle's improvement over matched-random) |
| **G8 — Mediated/exogenous identifiability** | Three-head decomposition: mediated_world MAE ≤ 0.10 AND exogenous_world MAE ≤ 0.10 (computed via causal contrast: null under high-hazard history vs null under matched low-hazard history) |
| **G9 — No false re-probing** | At no-shift control (using P21A-independent baseline), two-timescale mechanism's post-convergence null rate remains ≤ 5%. **The agent doesn't have anxiety.** |
| **G10 — Vector concern preserved** | Medicine accuracy within 0.05 of oracle across balanced/hungry/injured priorities, OR failures explained by narrow margins (≤ 0.10) |
| **G11 — Viability preserved** | Return ≥ 90% of `scheduled_null_anchor` return |

## Pre-registered interpretation matrix

| Result | Interpretation |
|---|---|
| Headline passes G2, G4, G5, G6, G7 | **Strong positive.** Agent learns to ask again under regime shift; probe-value signal beats current-error oracle and approaches true probe-value oracle. |
| G2 fails (corrected oracle no better than current-error) | The principled oracle is hitting a structural ceiling; mediated reducibility may itself be small. |
| G3 large positive (sequence oracle >> single-null) | Mediated identification genuinely requires action sequences; null-alone is insufficient. |
| G4 passes, G5/G6 fail | Re-engagement works but probes are misallocated. |
| G7 fails (learned far from oracle) | Two-timescale + surprise signals aren't enough; need richer epistemic representation. |
| G8 fails (mediated/exogenous not separately identified) | Three-head decomposition has a new internal gauge symmetry; honest framing should call this "three-head world modeling," not "identified mediated decomposition." |
| G9 fails | Mechanism re-engages too often; agent has "anxiety" instead of relevance-realization. |
| All learned variants fail; oracle works | Cross-fit V_probe (P19 escalation) becomes the next move. |

## Pre-committed continuation

If headline passes G4 + G7 + G8:
- **Paper 23B**: hazard-strength sweep + symmetric action-correlation on D-axis.

If G8 fails (mediated/exogenous not identifiable):
- **Paper 23B-alt**: design interventions that explicitly target mediation — e.g., null after high vs low hazard history with otherwise-matched states.

If G4 fails:
- **Paper 24**: cross-fit V_probe with heterogeneous architecture.

## What success looks like

> In a responsive world with mid-training regime shift, an agent detects via non-null prediction surprise that its self/world boundary has become stale, re-opens identifying interventions in the affected buckets, uses ≤ 25% of the probes a time-matched random strategy would, approaches a true value-of-information oracle to within 20%, and stops probing again once re-identification is complete — without re-firing on routine noise.

That is "**learning when to ask again**," not just "learning when to ask."

## External literature framing

Carry over P22's stack plus:
- **Novelty detection / change-point detection**: CUSUM, page-Hinkley, surprise-driven exploration
- **Active learning under distribution shift**: continual active learning literature
- **Sense of agency under environmental drift**: literature on agency maintenance through changing sensorimotor contingencies
- **Value of information in active inference**: explicit treatment of intervention value vs information value

Honest framing line:

> Paper 23A redefines the program's probe-value signal as marginal MAE reducibility — the expected benefit of one more identifying intervention — and introduces a re-engagement mechanism that detects boundary staleness via non-null prediction surprise. Both upgrades address concrete bottlenecks Paper 22 named: oracle confounding (current error ≠ value) and self-silencing (probe stops → no data → probe stays stopped).
