# Wave 1b — COGR-E2b Preregistration

**Package:** `experiments/concern_gated_retrieval_e2/wave1b/`
**Predecessors (imported, never edited):** `wave0/` (Wave 0 hash `9683c5a1…`), `wave1a/` (Wave 1a hash `c23b31d9…`, screen decision KILL)
**Human director:** Jawaun Brown
**Draft date:** 2026-07-24
**Signature status:** unsigned. Signed only after the Modal confirmatory run completes and every G0–G9 gate reports a receipt in `PROVENANCE.md`.

## 1. Abstract

Wave 1b is the confirmatory crossed learned-geometry × concern
experiment for the concern-gated retrieval program. Its object is to
adjudicate two claims separately: **L1 — representation contribution**
(does the candidate mechanism beat matched-budget baselines on sealed
task outcome when geometry is learned or frequency-matched random) and
**L2 — concern recovery + specificity** (does online-learned concern
recover from a wrong prior and beat information-matched generic signals
on L1-supporting geometry). L1 and L2 are non-compensatory and issued
separately; the roadmap forbids one from rescuing the other.

Wave 1b corrects three failure modes that surfaced in Wave 1a's KILL
and in the Spencer echo-chamber critique:

* families are redesigned so no generic signal (recency, embedding
  similarity, care-only, freq-only) reaches oracle top-k — the Wave 1a
  KILL scope;
* utility is measured over **candidate sets**, not just singletons, so
  useful bundles and dangerous conjunctions are visible;
* primary utility is task-based, not epiplexity-based; epiplexity is a
  dependent variable and optional bonus, not the verifier.

## 2. Target objects

* **L1 target.** The candidate mechanism `multiplicative_ppr` composed
  with a **learned graph** (§4) or a **frequency-matched random graph**,
  scored against the full matched-budget baseline slate (§8) on
  `Δ_task` (§6) with SET-level oracle regret (§7) as the decisive
  metric.

* **L2 target.** The online concern-update rule (`LoggedProbePolicy` +
  `update_concern(estimator ∈ {ips, dr})` + poisoning guard) composed
  with a **learned graph** under a **wrong prior**, scored against
  information-matched generic signals and against the frozen-wrong
  concern baseline.

Wave 1a's E2a screen KILLed the concern-update rule under Wave 0's
fixed withheld geometry and Wave 0's family design. L2 in Wave 1b is
therefore conditional: it runs iff the Wave 1b family redesign passes
the §4 pre-run recency-decoupling assertion. L1 rows run
unconditionally because the L1 gate does not depend on the
concern-update rule.

## 3. Terminology (per Spencer)

Named explicitly so the promotion contract does not conflate three
different objects:

* **Regret** — how much utility the policy missed. `simple_regret =
  max_S Δ(S) − Δ(selected_set)`. Report SET-level (§7).
* **Propensity** — the probability `q_t(v)` that memory v was selected.
  Enables IPS / DR debiasing **on the supported set**. It cannot
  recover information about v with `q_t(v) = 0`.
* **Exploration** — the mechanism that gives neglected v nonzero
  `q_t(v)`. Distinct from propensity logging.

Each appears as a separate receipt in `PROVENANCE.md`.

## 4. Family redesigns (recency ≠ oracle, bundle-planting)

Three families, each v2 of the corresponding Wave 0 family:

* `delayed_commitments_v2` — dates, promises, dependencies, and
  interruptions.
* `maintenance_fault_v2` — earlier observations become load-bearing
  only when a later symptom appears.
* `resource_constrained_v2` — a hidden prior obligation determines
  which otherwise-valid action is best.

**Anti-recency constraints (mandatory).** Each family must satisfy:

1. Load-bearing memory at a random non-recent position (not in the last
   three positions of the event stream) on **≥ 50%** of episodes.
2. 3–5 recent distractors whose recency dominates the load-bearing
   memory.
3. At least one semantic-decoy that maximises embedding similarity to
   the context but is not load-bearing.

**Pre-run assertion (blocks L2 rows if violated).** On a random 100-seed
calibration sample from each family, for every generic-signal baseline
`s ∈ {recency, embedding_sim, care_only, freq_only, salience, value,
priority}`:

```
oracle_recall_at_k(s)         < 0.8
interaction_recovery(s)       < 0.5   # on planted complementary pairs
recency_load_bearing_corr     < 0.5
```

If any assertion fails on any family, Wave 1b L2 rows are withheld and
the family is redesigned. L1 rows still run on the families that pass.

**Bundle planting.** Each episode plants across templates:

* `(i)   useful singletons`         `Δ({v}) > 0`
* `(ii)  contradictory pairs`       `Δ({a}) > 0, Δ({b}) > 0, Δ({a,b}) < min(Δ({a}), Δ({b})) / 2`
* `(iii) complementary pairs`       `Δ({a}) ≈ 0, Δ({b}) ≈ 0, Δ({a,b}) > 0`
* `(iv)  dangerous conjunctions`    `Δ({a}), Δ({b}), Δ({c})` individually safe; `Δ({a,b,c})` delivers a sealed-evaluator constraint-violation penalty
* `(v)   isolation-distractors`     `Δ({v}) > 0` alone but `Δ({v} ∪ context)` harms trajectory

The evaluator-side `BundleManifest` records which bundle types were
planted per episode. It is refused by any policy path via the wave0
`IntegrityAudit`.

## 5. Sample plan

* **Confirmatory seed range.** `200000..201999` (inherited from Wave 0
  §7). Disjoint from Wave 0 calibration `100000..100999`. The
  wave0 template-split guard raises `LeakageError` on any mix.
* **Cells.** Geometry ∈ {LEARNED, FREQ_MATCHED_RANDOM, ORACLE_WITHHELD}
  × Concern ∈ {FROZEN_WRONG, ONLINE_LEARNED_IPS, ONLINE_LEARNED_DR,
  ORACLE} × Family ∈ {DC_v2, MF_v2, RC_v2} = **36 cells**.
* **Seeds per cell.** N = 300 (paired across concern conditions on the
  same seeds within each geometry × family strip).
* **Replay reserve.** `200900..201999` accessible only under
  §11-registered replayable knobs.

## 6. Utility function

Primary utility per episode:

```
Δ_task(v) = J_g(trajectory | v) − J_g(trajectory | ∅)
```

where `J_g` is the sealed-evaluator **task-outcome measure** — goal
attainment, commitments honored, constraint violations avoided — and is
computed independently of concern.

Composite utility for optional bonus / dependent-variable analysis:

```
U(v) = Δ_task(v) + β · S^φ(v) − γ · constraint_violations(v)
```

`β` and `γ` are frozen in `PROMOTION_CONTRACT_L1.md`. The **L1 gate uses
β = 0**. Cells with `β > 0` are reported as dependent-variable
diagnostics, never as promotion evidence. Epiplexity S^φ is therefore
never the verifier.

## 7. Oracle-regret metrics (SET-level, first-class)

On the synthetic families the candidate set satisfies |V \ R_t| ≤ 20.
The evaluator can enumerate:

* all singletons (≤ 20 per episode)
* all pairs (≤ 190 per episode)
* feasibility-gated triples (bounded to ≤ 1140 per episode; skipped
  when episode-time budget is exhausted)

Report per episode:

```
oracle_recall_at_k(policy)   = |selected_top_k ∩ union(oracle_top_k_sets)| / k
simple_regret_set(policy)    = max_S Δ(S) − Δ(selected_set)
cumulative_regret            = Σ over episodes
interaction_recovery(policy) = frac. of episodes where policy retrieves both
                                members of a planted complementary pair AND
                                avoids all three members of a planted
                                dangerous conjunction
```

Hit@1 remains reported as a diagnostic; it is not a decisive metric.

## 8. Baseline slate

Reuse the full `wave0.baselines` slate: `no_retrieval`, `random_rank`,
`freq_only`, `context_only_ppr`, `care_only_ppr`, `additive_ppr`,
`multiplicative_ppr` (candidate), `embedding_similarity`,
`learned_one_stage`, `info_matched_value`, `info_matched_priority`,
`info_matched_recency`, `wrong_agent_concern`, `oracle_ceiling`
(ceiling, refused).

Add for Wave 1b:

* `learned_one_stage_with_concern` — the matched-budget learned ranker
  fed the same concern feature the candidate consumes.
* `k_split_care_uncertain_audit` — labelled ablation at three splits
  (70/20/10, 50/30/20, 80/10/10). Not the promotion path.
* `oracle_pair_ranker` — ceiling-only pair-aware oracle for bundle
  recovery; refused by the promotion harness.

## 9. Fatal gates (G0–G9)

Non-compensatory. A single FAIL blocks the affected verdict regardless
of every other gate.

* **G0 integrity** — evaluator-only fields unreachable from any policy
  path; IntegrityAudit clean at import.
* **G1 L1_behavior** — candidate mechanism strictly dominates every
  matched-budget baseline on `Δ_task`, `oracle_recall_at_k`, and
  `simple_regret_set` on non-ceiling geometry.
* **G2 L1_representation** — intervening on the learned edge with
  highest score changes downstream `Δ_task` in the predicted direction.
* **G3 L2_recovery** — the online-updated concern reduces oracle-distance
  vs the frozen-wrong prior with valid propensity accounting.
* **G4 L2_specificity** — online-learned concern beats all
  information-matched generic signals AND the wrong-agent profile on
  every family.
* **G5 non_ceiling** — no promotable baseline saturates within 0.05 of
  the oracle ceiling on any family.
* **G6 bundle_awareness** — the candidate mechanism finds ≥ 1
  complementary pair per family across the 300 confirmatory seeds AND
  avoids ≥ 90% of planted dangerous conjunctions.
* **G7 adversarial** — resistance to targeted concern poisoning within
  the wave0 single-source-influence bound.
* **G8 robustness** — no family-level reversal is hidden by aggregate;
  every family reports its own PASS/KILL.
* **G9 leakage_audit** — label-permutation and randomized-generator
  controls on permitted graph features are within their preregistered
  tolerance.

## 10. Leakage audit

Two controls, both required to pass:

* **Label permutation.** Under a random permutation of role labels, the
  learned geometry must not place the load-bearing node in the top-k of
  PPR from any context restart above chance (`p < 0.01` bootstrap).
* **Randomized generator.** Regenerate family episodes with a randomised
  generator seed but identical surface schema. Learned edges must not
  carry cross-generator predictive power for the target.

Either fires ⇒ `G9 leakage_audit` FAILs.

## 11. Frozen thresholds

L1 per-family effect thresholds derive from the Wave 0 PROVENANCE §4
variance rows:

```
delayed_commitments    mu_best = 0.5314   sigma_best = 0.0218   headroom = 0.4845   delta_thresh_L1 = 0.0484
maintenance_fault      mu_best = 0.5029   sigma_best = 0.0267   headroom = 0.4548   delta_thresh_L1 = 0.0534
resource_constrained   mu_best = 0.5750   sigma_best = 0.0250   headroom = 0.4291   delta_thresh_L1 = 0.0500
```

L1 promotion requires the candidate mechanism's paired-seed lower
bound `Δ − 2σ ≥ delta_thresh_L1` on **every family**.

L2 thresholds inherit the same shape with paired-seed variance
estimated from Wave 1b's crossed cells directly.

Bundle-awareness thresholds (G6): ≥ 1 complementary-pair recovery per
family per 300 seeds; ≥ 90% dangerous-conjunction avoidance per family
per 300 seeds.

**Replayable knobs** (only within their preregistered ranges): `epsilon
∈ [0.05, 0.10]`, `eta ∈ [0.05, 0.20]`, cell-level rejection replay
capped at 30% per cell drawing from `200900..201999`.

## 12. Epiplexity implementation

Read the operator's memory entry `reference-zhang-levin-epiplexity`
before implementing.

* When candidates share `X̃`: use `SharedQREpiplexity` with augmented QR
  + multiple-RHS solve + determinant identity in output-space
  (`det(I_m + η W W^T) = det(I_D + η W^T W)`).
* When `X̃` differs per candidate: `IndependentSolveEpiplexity` (batched
  independent QR on GPU). This is not a shared-factorization speedup.
* The crossed-runner records which regime it used in `PROVENANCE §7`.

No `Rademacher`, `Nyström`, `MMD`, or `LZ` "approximation" is used as
an epiplexity estimator in Wave 1b. Those are separate observers; if
Wave 4 wants them, it defines them as alternatives with an empirical
validation study.

Speedups are **measured and reported**, not projected. No unqualified
"20–30×" claim in any Wave 1b receipt.

## 13. Analysis-code freeze plan

* `WAVE1B_ANALYSIS_HASH` = SHA-256 over every tracked file under
  `experiments/concern_gated_retrieval_e2/wave1b/**` in sorted path
  order, excluding `results/`.
* Mirrored between `PREREGISTRATION.md §13` (this section) and
  `PROVENANCE.md §6` at signature time.
* Wave 0 hash `9683c5a1f4010361d6e120bcabd2743fb33e8cc9c7c79d5bd9b1d9f9f8889c23`
  and Wave 1a hash
  `c23b31d977d7c169d57ca12cdfdbc8ad3a59188542efbdf802e341b1c8937209`
  are reference-verified byte-for-byte at signature time.
