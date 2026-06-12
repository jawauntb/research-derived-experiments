# Paper 21A — Pre-Registration

**Title (working):** Scale-Normalized Probe Calibration for Vector First-Order Self: A Target × Threshold Factorial

**Frozen:** 2026-06-12, before any Modal sweep runs.

## Question

Paper 20B established that:
- Anchor mechanism composes to vector setting (G1, G2 ✓ strong)
- Vector ΔV reweighting composes with self/world (G7, G8 ✓)
- BUT current_replay V_probe is scale-asymmetric: E dimension calibrates partially (Spearman +0.20), D dimension is anti-calibrated (Spearman −0.41); learned probing is 28% worse than matched-random at matched null count.

The diagnosis: the raw current_replay target `|mean signed residual|` is in raw ΔE/ΔD units. D's shocks (0.20) and self effects (0.5) are smaller than E's (0.30, 1.0). A single scalar cost threshold (0.025) discriminates E-scale but falls below D-scale noise floor → V_probe_D doesn't discriminate → D-buckets under-probed → D anti-calibrated.

**Paper 21A's question:** does the bottleneck close when V_probe targets are normalized to cross-dimensionally comparable units, OR when decision thresholds are scaled per dimension, OR is BOTH required, OR is the issue actually same-class self-confirmation (in which case 21A fails and 21B cross-fitting becomes necessary)?

This is a scale-calibration factorial. Not a one-line "divide by variance and see."

## Hypotheses

| Hypothesis | Mechanism | What confirms it |
|---|---|---|
| **H1 — Target scale failure** | The V_probe target itself was in wrong units; normalizing the *target* is the load-bearing fix | `norm_target_global_cost` passes G14, G15 |
| **H2 — Threshold scale failure** | V_probe target was fine; the *decision rule* compared cross-incommensurate values; per-dim threshold scaling is the fix | `raw_target_perdim_cost` passes G14, G15 |
| **H3 — Both** | Need to normalize both target and threshold | Only `norm_target_perdim_cost` (headline) passes |
| **H4 — Structural** | Same-class residual estimation is still self-confirming regardless of scale | All learned variants fail; oracle still works → escalate to 21B |

## 2×2 factorial + ladder (10 conditions)

| Condition | V_probe target | Threshold | Purpose |
|---|---|---|---|
| `raw_global_cost` | `|mean signed residual|` (raw) | single scalar `cost` (0.025) | **Reproduce 20B failure baseline** |
| `norm_target_global_cost` | `|mean signed residual| / sqrt(running_var_d + ε)` | single scalar τ in normalized units (set from warmup) | **H1 test** |
| `raw_target_perdim_cost` | raw | `(cost_E, cost_D)` with `cost_D = cost_E · scale_D / scale_E` | **H2 test** |
| **`norm_target_perdim_cost`** | normalized | per-dim `(τ_E, τ_D)` from per-dim warmup distributions | **HEADLINE** (combined) |
| `norm_target_dim_balanced_floor` | normalized | per-dim + 5% audit floor | Sensitivity: does audit coverage help? |
| `matched_random_total` | n/a | n/a | Same total null count as headline, uniform random placement |
| `matched_random_bucket_balanced` | n/a | n/a | Null distribution forced uniform across 16 buckets (stronger control) |
| `vector_scheduled_null_anchor` | n/a (scheduled 33% null) | n/a | Positive anchor control |
| `vector_oracle_uncertainty_probe` | oracle uncertainty | per-dim (max of `|pred_world − true_world|` per dim > cost) | Upper bound on probe placement |
| `vector_oracle_source` | n/a | n/a | Upper bound (semantic source labels) |

**3 seeds × 10 conditions = 30 Modal cells.** CPU only, ~15 min wall-clock.

## Target & threshold definitions (frozen)

**Running variance per dimension** (dimension-level, NOT bucket-level, to avoid reintroducing the 17A noise-floor trap):
```
mu_d(t)  = (1 − α) · mu_d(t − 1)  + α · r_d(t)
var_d(t) = (1 − α) · var_d(t − 1) + α · (r_d(t) − mu_d(t))²
```
where `r_d(t)` is the per-null-observation signed residual for dimension `d`, EMA α = 0.05.

**Raw target** (20B): `|mean over bucket of [pred_world_current − observed_total_null]|` per dim.

**Normalized target** (21A): `raw_target_d / sqrt(var_d + ε)` with ε=0.01.

**Global threshold τ**: scalar in normalized units. Set after warmup so that ~10–20% of normalized V_probe values during late warmup exceed τ.

**Per-dim threshold (τ_E, τ_D)**: each set so that ~10–20% of per-dim normalized values exceed during late warmup.

**Per-dim raw cost (cost_E, cost_D)**: `cost_E = 0.025` (P20B default); `cost_D = cost_E · sqrt(var_D) / sqrt(var_E)`.

## Carried over from 20B (unchanged)

- Environment: two-variable (E, D), item types, world shocks, priority weights — identical.
- Architecture: encoder + vector self/world heads + vector V_probe head — identical.
- Online training: ε-greedy 0.50 → 0.10 + 50-episode warmup + action-stratified minibatch — identical.
- Current-replay buffer K=64 per bucket — identical.
- Probe rule shape: max(q_E, q_D) > threshold (or per-dim OR with respective thresholds).

The ONLY causal changes between 20B and 21A:
1. V_probe target may be normalized (per condition)
2. Threshold may be per-dim (per condition)

This keeps the factorial's causal interpretation clean.

## Sanity checks (one seed, before full sweep)

Run `norm_target_perdim_cost` at seed 20260610. Require all:

1. **Running variances stabilize.** By end of training, `var_E` and `var_D` should each have ≥ 200 EMA updates. Final values should differ by ≥ 2× (var_E > var_D as expected from shock magnitude asymmetry).
2. **Normalized V_probe values cross-dim comparable.** Mean(q_E_norm) and Mean(q_D_norm) within 2× of each other (vs 20B's wildly different absolute scales).
3. **Null rate at headline cost in [3%, 40%].**
4. **Per-dim threshold calibration produces both dims firing.** Per-dim probe rates per bucket: at least one D-bucket has fire rate ≥ 0.3.
5. **Anchor still recovers decomposition.** scheduled_null_anchor food self_E ∈ [+0.85, +1.10] AND poison self_D ∈ [+0.40, +0.60].
6. **No oracle source leakage** in non-oracle conditions (code grep).

If any fail, fix and rerun.

## Pre-registered gates

**Decisive new gates (21A-specific):**

| Gate | Criterion |
|---|---|
| **G14 — D calibration restored** | Headline D-dim Spearman ρ ≥ 0.5 between probe rate (per bucket) and oracle current attribution error |
| **G15 — Selection beats volume** | Headline total component MAE ≥ 25% below `matched_random_total` |
| **G16 — D selection beats volume** | D-specific component MAE ≥ 25% below matched_random |
| **G17 — No E regression** | E-dim Spearman ρ ≥ 0.2 AND E component MAE ≤ 110% of 20B headline (0.057) |
| **G18 — Cross-dim balance** | Worse-dim MAE ≤ 2× better-dim MAE (or both ≤ 0.07) |
| **G19 — Probe allocation balance** | Top/bottom enrichment ≥ 2× separately for E and D |
| **G20 — No saturation / no collapse** | Training null rate ∈ [0.1%, 40%]; no priority-weighted-style over-firing |

**Carried from 20B (re-evaluated):**

| Gate | Criterion |
|---|---|
| G1 | per-dim self/world MAE ≤ 0.10 for both E and D |
| G2 | ≥ 70% false-credit reduction vs `factorized_no_null` baseline (use 20B's no_null reference if needed) |
| G21 (≡ G7) | Medicine accuracy within 0.05 of oracle across balanced/hungry/injured |
| G22 — Relative viability | Return ≥ 90% of scheduled OR oracle (NOT the old 45/50 absolute — D-terminated env makes that unreachable) |
| G23 — Mechanism gate | If attribution improves but G14/G15 fail, paper cannot claim "autonomous vector probing solved"; honest "partial" framing required |

## New calibration diagnostics (from active-learning literature)

These are reported as supplementary but NOT gated (no pre-registered threshold). They make 21A legible to the active-learning audience.

- **Reliability curve**: V_probe output bins (10 quantile bins) plotted against mean oracle attribution error per bin. Should be monotonically increasing.
- **Expected Calibration Error (ECE)**: weighted absolute deviation of reliability curve from y=x line, per dimension.
- **Acquisition gain curve**: MAE reduction as a function of top-k probed buckets (k ∈ {1, 2, 4, 8, 16}). For each k, oracle assigns null only to the top-k buckets; we report MAE improvement.

## Pre-registered interpretation matrix

| Result pattern | Interpretation |
|---|---|
| All 4 factorial cells pass G14, G15 | Both fixes work independently; either is sufficient. Robust positive. |
| Only `norm_target_global_cost` passes (cell 2) | H1: target normalization alone fixes it. The decision rule was fine. |
| Only `raw_target_perdim_cost` passes (cell 3) | H2: threshold scaling alone fixes it. V_probe targets were OK but cost was wrong. |
| Only `norm_target_perdim_cost` passes (cell 4 = headline) | H3: both fixes are necessary. The simpler conditions miss complementary effects. |
| Headline passes G15 but G14 fails on D | Behavior improved (selection beats volume) but D calibration didn't truly recover — partial fix, honest framing required (G23). |
| All factorial cells fail; oracle works | H4: same-class self-confirmation. Move to 21B cross-fitted V_probe. |
| Headline passes G14/G15 but G17 fails (E regresses) | Fix overcompensates; not a true vector solution; another round needed. |
| `norm_target_dim_balanced_floor` passes alone, headline fails | Audit coverage is load-bearing; autonomy is partial. |
| Headline fails G22 (return < 90% scheduled) | Probe selectivity hurts viability — too many nulls fire in wrong places. |
| High return but G14/G15 fail | Paper 16 pattern again: behavior without intended attribution. |

## Pre-committed escalation (Paper 21B)

If all four factorial learned cells fail G14 or G15:

> "Paper 21B will cross-fit V_probe to test same-class self-confirmation. Two world_head copies trained on different minibatch splits; V_probe targets computed using world_head_A's residuals to train V_probe for world_head_B (and vice versa). If 21B succeeds, the bottleneck was self-confirmation, not scale. If 21B also fails, the program's autonomous-probe arc has localized to heterogeneous-architecture or meta-learned approaches."

This is pre-committed so the program doesn't open-endedly drift.

## External literature framing (intro/related work)

Cite tight, ~12–16 papers across:

- **Calibrated active learning failures** (closest external framing): *Calibrated Uncertainty Sampling for Active Learning*; *When Active Learning Fails, Uncalibrated OOD Uncertainty*.
- **Epistemic uncertainty calibration**: *Epistemic Neural Networks*; *Quantifying Epistemic Uncertainty in Deep Learning*.
- **BALD / information gain / active inference**: *Bayesian Active Learning by Disagreements*; *Active Inference and Epistemic Value in Graphical Models*.
- **Causal representation identifiability**: Brehmer et al. *Weakly Supervised Causal Representation Learning*; *General Identifiability and Achievability for CRL*; *Identifiability of Causal Abstractions*.
- **Sense of agency**: Comparator model literature; *Predictive Processing Model for Self-Other Distinction*.
- **Homeostatic active inference + Di Paolo + empowerment**: *Simulating homeostatic/allostatic active inference*; Di Paolo on autopoiesis-adaptivity; *Empowerment*.

Framing line (verbatim-usable):

> We treat null actions as identifying interventions: costly epistemic actions whose value lies not in immediate reward but in reducing uncertainty about which future viability changes are self-caused versus world-caused. Prior work in active learning predicts uncertainty-driven acquisition works when uncertainty is calibrated, and fails when it is not. We show this failure mode inside a minimal self/world attribution problem and test a scale-normalized current-error correction.

Claim discipline if 21A succeeds:

> In a minimal two-variable homeostatic bandit, autonomous identifying interventions become vector-sensitive when probe uncertainty is calibrated in dimension-normalized units; without scale normalization, the agent's decision about when to identify is biased toward the larger-magnitude dimension.

NOT: "we solved uncertainty" / "consciousness" / "agency solved."

## What success and failure look like

**Strong positive (H3 or all-of-the-above):** Headline passes G14, G15, G17 (no E regression), G18 (cross-dim balance), G19 (top/bottom enrichment per dim), G21 (reweighting preserved). The vector autonomy gap from 20B closes; the program advances from "scalar autonomy works" to "vector autonomy works under proper scale calibration."

**Mixed positive (H1 or H2 alone):** Only one factorial cell passes. The program learns which axis (target vs threshold) was load-bearing; future probe designs use that knowledge.

**Negative (H4):** All learned variants fail; 21B cross-fit is the pre-committed next step.

All outcomes narrow the program.
