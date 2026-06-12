# Paper 17A — Pre-Registration

**Title (working):** Learning When Not to Act: Costly Null Probes for Self/World Identifiability in Minimal Homeostatic Agents

**Frozen:** 2026-06-11, before any Modal sweep runs.

## Question

Paper 16b showed null-anchor intervention breaks the self/world gauge symmetry that defeats architectural factorization (Paper 16). Null observations, when used as world-only supervision, recover the true self/world decomposition (food self error +0.51 → +0.09, 82% false-credit reduction).

But in Paper 16b the null actions are **experimenter-scheduled**. The agent receives null-anchor data on a fixed timetable. The biggest crutch in the program now is that identifying interventions are designed by the experimenter, not discovered by the agent.

**Question:** Can a minimal homeostatic agent **learn when to spend viability on a null probe** so that the probe both (i) improves self/world identifiability and (ii) fires preferentially in states where the model's attribution is actually uncertain?

The "and" is critical. Improved identifiability without calibrated probe placement is the self/world analogue of Paper 14b's ensemble failure — variance at the regime boundary was lower than at adjacent points (error-variance correlation ≈ 0), so a same-architecture uncertainty signal can be confidently wrong. Paper 17A is designed to distinguish *autonomous epistemic selection* from *higher-volume anchored data*.

## Conditions (7)

| Condition | Purpose |
|---|---|
| `factorized_no_null` | Paper 16 failure baseline (no null action at all) |
| `factorized_null_passive` | Null data without anchor loss — should not solve gauge |
| `scheduled_null_anchor` | Experimenter-scheduled positive control (Paper 16b mechanism) |
| `matched_random_null_anchor` | Same null budget as learned, but **random placement** |
| `learned_costly_null_probe` | **Main condition.** Agent learns when to probe |
| `oracle_uncertainty_probe` | Upper bound on **probe placement** (NOT source labels) |
| `oracle_source` | Upper bound on **semantic source supervision** (Paper 16b) |

`oracle_uncertainty_probe` deserves emphasis: it gets oracle access only to *where* to probe (per-state attribution error of the current factorized model). Its component losses are the same null-anchor losses as `learned_costly_null_probe`. It cannot collapse into `oracle_source` because it does not receive per-sample self/world labels.

## Cost sweep

`cost ∈ {0.01, 0.025, 0.04}` energy units, applied per null action during eval rollout.

**Headline result: cost = 0.025.**
0.01 = low-cost sensitivity. 0.04 = high-cost sensitivity. At cost = 0, probing would be free and trivially solved; at cost ≫ 0.04, failure is uninformative.

## Seeds

`{20260610, 1729, 4242}` — three independent seeds per (condition, cost).

## Cell budget

- Pass 1 (cost-irrelevant + cost-relevant non-matched): 3 seeds × (4 cost-irrelevant + 2 cost-relevant × 3 costs) = 30 cells
- Pass 2 (matched_random uses Pass 1's learned-probe rates): 3 seeds × 3 costs = 9 cells
- **Total: 39 Modal cells**

## Probe-policy mechanism (learned, no oracle)

Each `learned_costly_null_probe` agent carries an auxiliary probe-value head:
```
V_probe(z, E) ∈ ℝ ≥ 0
```
trained alongside `self_head` and `world_head`. Its target on **null observations only** is:
```
target = |world_head(z, E).detach() − observed_total_ΔE_under_null|
```
i.e., the magnitude of the model's current world-attribution error at that state. The detach prevents the probe head from leaking gradients back through the world head.

**Eval-time probe rule:**
```
if V_probe(z, E) > cost:
    take null action (and pay `cost` from E)
else:
    take greedy argmax over (skip, consume) using self_head(z, E, a)
```

This is **not ensemble variance**. It is a learned single-head regressor on observable null residuals. Paper 14b explicitly warned that same-architecture ensemble variance fails at regime boundaries — V_probe avoids that failure mode by training directly on attribution residuals rather than predictive variance.

## Oracle-uncertainty probe

Same eval-time rule, but `V_probe` replaced with:
```
true_attrib_err(z, E, item) = |world_head(z, E) − P(shock|role) × shock_magnitude|
```
computed using simulator-known true world expectation per state bucket. The agent still uses the same null-anchor losses for training; only the *probe-firing decision* is oracle-informed.

## Matched-random null anchor

Trained off-policy with anchor loss, but action mix forced so null rate equals the **realized** null rate of `learned_costly_null_probe` at the same (cost, seed). Implemented in Pass 2 after Pass 1 reports per-cell null rates.

## Pre-registered gates (frozen)

All gates evaluated at **cost = 0.025** unless stated.

| Gate | Criterion | Tests |
|---|---|---|
| **G1 — Active identifiability** | `learned_costly_null_probe` food self_consume MAE ≤ 0.12 AND food world MAE ≤ 0.10 | Probe actually recovers decomposition |
| **G2 — False-credit reduction** | ≥ 70% reduction in food self overshoot vs `factorized_no_null` | Direct continuation of 16b's 82% result |
| **G3 — Selection beats volume** | `learned` component-MAE ≥ 25% lower than `matched_random` at same null rate | Rules out "just more null data" explanation |
| **G4 — Probe efficiency** | `learned` reaches ≥ 80% of `scheduled_null_anchor`'s identifiability gain with ≤ 20% null actions | Autonomous probing is not brute-force null spam |
| **G5 — Viability preservation** | `learned` mean return ≥ 90% of `scheduled_null_anchor` return AND ≥ 45/50 absolute at cost 0.025 | Prevents epistemic self-harm |
| **G6 — Calibrated probe placement** | Spearman ρ ≥ 0.5 between learned null-rate-by-state-bucket and oracle null-rate-by-state-bucket | Rules out Paper-14b-style fake epistemics |
| **G7 — Top-risk enrichment** | Learned probe fires ≥ 2× more in top-quartile oracle-uncertainty buckets than bottom-quartile buckets | More robust than correlation alone |
| **G8 — Behavior/representation split** | High return WITHOUT G1+G6 passing = mechanistic failure | Preserves program's central methodological lesson |

**State buckets** for G6/G7: `item_role × E_bin` (4 roles × 2 E bins = 8 buckets). Aggregated over seeds.

## Pre-registered interpretation matrix

| Result pattern | Interpretation |
|---|---|
| Learned passes G1–G8 | **Strong positive.** Autonomous null probing supports first-order self/world identifiability. |
| Oracle probe succeeds, learned fails | Null probing is sufficient; learned epistemic selection failed (probe-value head learned wrong signal) |
| Learned improves vs no-null but does NOT beat matched_random | Gain is from anchored volume, not intelligent placement — Paper 17A's central question fails |
| Learned passes G5 (return) but fails G1 (MAE) | Behavior without intended attribution; Paper 16-pattern repeats one level up |
| Learned probe fires often but G6 fails | Epistemic-looking action without epistemic structure — Paper 14b-style failure transferred to self/world |
| Scheduled passes, learned + oracle both fail | Costed selective probing is too sparse OR uncertainty target is misdefined |
| Passive null still fails | Confirms 16b: intervention data alone is insufficient without anchoring |
| All null-anchor variants fail | 16b mechanism is brittle under cost/autonomy → major negative result |

## Out of scope

- Vector ΔV (multi-dimensional self/world) — that's Paper 17B if 17A passes
- Action-correlated shocks — that's Paper 17C
- World-model shift robustness — also 17C territory
- Encoder RSA tapestry geometry — orthogonal program direction

## What success and failure look like

**Strong positive** would advance the program from "intervention data, scheduled" to "intervention data, autonomously selected by the agent based on internal uncertainty estimates." This removes the largest remaining experimenter crutch and is the closest the program has come to operationalizing Vervaeke's relevance realization at the action-selection level: the agent is choosing when an inaction is informative.

**Strong negative** (in particular: learned ≈ matched_random) would localize the bottleneck and motivate either (a) a better probe-value signal that's robust to the Paper-14b miscalibration trap, or (b) a richer environment where attribution uncertainty has stronger state-conditional structure for V_probe to latch onto.

Either outcome is publishable. Both narrow the program.
