# Concern-Gated Retrieval Wave 1a — Preregistration (COGR-E2a)

**Package:** `experiments/concern_gated_retrieval_e2/wave1a/`
**Wave:** 1a — COGR-E2a concern-recovery screen
**Predecessor (imported, never edited):**
`experiments/concern_gated_retrieval_e2/wave0/`
**Successor (not yet created):**
`experiments/concern_gated_retrieval_e2/wave1b/` (COGR-E2b, learned-geometry
confirmation and L1 gate)
**Human director:** Jawaun Brown
**Draft date:** 2026-07-23
**Signature status:** unsigned. This document is only preregistered after
the Wave 1a analysis-code hash is written into §8, mirrored into
[`PROVENANCE.md`](PROVENANCE.md), and the frozen Wave 0 hash referenced
in §6 is verified byte-for-byte against
[`../wave0/PROVENANCE.md`](../wave0/PROVENANCE.md) §6.

## 1. Abstract

Wave 1a is a **concern-recovery screen only**. It exercises the frozen
Wave 0 randomized-probe policy and the frozen Wave 0 off-policy
concern-update rule (IPS and DR variants) on the three procedural
families defined in [`../wave0/PREREGISTRATION.md`](../wave0/PREREGISTRATION.md)
§6, over the confirmatory seed range `200000..201999`, using the fixed
withheld geometry produced by
`experiments.concern_gated_retrieval_e2.wave0.graph_learn.build_withheld_graph`.
The wave answers exactly one question: under the Wave 0 adversarially
wrong prior, does the online-learned concern-update rule recover useful
priorities relative to a frozen-wrong baseline, at a preregistered
effect size, across every family, without being reproduced by shuffled
labels, a wrong-agent profile, or a generic value / priority / recency
signal?

Wave 1a **cannot** establish learned memory geometry, a dual-source
retrieval L1 gate, an L2 history-derived-concern-recovery claim, semantic
meaning, or selfhood. These are Wave 1b (COGR-E2b) objects. A pass on
Wave 1a is a green light to open Wave 1b; a fail is a KILL of the
concern-update rule as written and forbids Wave 1b from re-using the
same rule without a redesigned preregistration. Per the honor-the-
preregistration rule, only the knobs explicitly named as replayable in
§7 may be rerun after a KILL.

Wave 1a evaluation is synthetic-only. It does not touch non-synthetic
history, external memory, or real-agent traces; the premise audit
remains future work with the stub receipt in
[`../wave0/PROVENANCE.md`](../wave0/PROVENANCE.md) §7.

## 2. Target object and decision

- **Target object.** The **concern-update rule** — specifically the
  composition ``LoggedProbePolicy`` + ``update_concern(estimator ∈
  {"ips", "dr"})`` + poisoning guard — evaluated as an off-policy
  learner on fixed withheld geometry against the Wave 0
  adversarially wrong prior.
- **Not the target object.** Learned memory geometry, the dual-source
  retrieval mechanism, the L1 mechanism claim, the L2 concern-recovery
  claim, the utilization filter, or any live-agent behavior.
- **Decision at end of Wave 1a.**
  - *Screen pass.* If every fatal gate in §5 reports PASS and every
    frozen effect threshold in §6 is met on every family, publish the
    screen-pass receipt, sign the preregistration by writing the
    analysis-code hash into §8, mirror it into
    [`PROVENANCE.md`](PROVENANCE.md), and open Wave 1b.
  - *Screen kill.* If any fatal gate FAILs or any per-family effect
    threshold is missed, publish the KILL receipt honestly. No post-hoc
    threshold swap, corpus swap, seed-range swap, or family swap is
    permitted. Only the replayable knobs enumerated in §7 may be rerun,
    and only under the ex-ante replay rule in §7.
- **Wave 1a does not adjudicate L1.** Even a fully passing Wave 1a is
  not evidence for the L1 dual-source-retrieval claim. L1 promotion is
  gated on Wave 1b's crossed-geometry design; a Wave 1a KILL does not
  block Wave 1b's L1 rows.

## 3. Representation, geometry, and data clock

- **Substrate.** The fixed withheld weighted graph produced by
  `experiments.concern_gated_retrieval_e2.wave0.graph_learn.build_withheld_graph(
  seed, size, family)`. The graph is a pure function of
  `(seed, size, family)` and never consults any evaluator-only field.
  Wave 1a **does not learn edges**; edge learning is a Wave 1b object.
- **Episode.** One confirmatory episode is a tuple
  `(family, template_id, seed, history, active_context, condition,
  sealed_env)` where:
  - `family ∈ {delayed_commitments, maintenance_fault, resource_constrained}`;
  - `template_id` is a confirmatory template id `{DC,MF,RC}-X-NN` drawn
    from the confirmatory pool declared in
    [`../wave0/PREREGISTRATION.md`](../wave0/PREREGISTRATION.md) §6;
  - `seed ∈ 200000..201999`;
  - `history` and `active_context` are produced by the family generator
    before any retrieval or ranking call fires;
  - `condition` is one of the five conditions in §4;
  - `sealed_env` exposes the whitelisted `observe_outcome(decision)`
    method only.
- **Data clock.** As in Wave 0: the generator emits `history` and
  `active_context` before any ranking call. Retrieval, ranking, and
  concern-update code receive an immutable `HistoryWindow` sliced at
  the decision timestamp and cannot inspect later events.
- **Randomization.** Every condition that generates receipts wraps its
  nomination policy in
  `wave0.concern_update.LoggedProbePolicy(nomination, epsilon=0.05)`.
  Selection propensities are logged and are the sole quantity IPS and
  DR estimators divide by. A pilot condition with `epsilon = 0.0` is a
  fatal integrity failure; the wrapper's constructor enforces it.

## 4. Conditions

Every confirmatory seed is scored under all five conditions on all
three families; the design is fully crossed and paired at the seed
level so paired variance estimates are recoverable.

| # | Condition | Concern state | Wave 1a role | Anti-leakage note |
|---|---|---|---|---|
| C1 | `frozen_wrong` | Wave 0 wrong prior held fixed | **Baseline.** The comparator every other condition is scored against. | Uses only the policy-visible numeric prior. |
| C2a | `online_learned_ips` | Online-updated via IPS estimator from `update_concern(estimator="ips")` | **Candidate.** The concern-update rule under test. | Reads only `SealedOutcome.realized_reward` and `template_family_split`. |
| C2b | `online_learned_dr` | Online-updated via DR estimator from `update_concern(estimator="dr")` | **Candidate.** Second variant of the rule under test; scored independently, not averaged with C2a. | Same anti-leakage bound as C2a. |
| C3 | `oracle` | Oracle concern profile held fixed | **Ceiling.** Diagnostic only. Never a promotable claim. | Consumes `oracle_concern` inside the evaluator; policy sees only the pre-computed numeric prior. |
| C4 | `shuffled` | Wave 0 wrong prior with anchor labels randomly permuted per episode | **Control.** Rejects "any anchor-conditioned update helps." | Permutation seed logged; permutation is a pure function of the seed. |
| C5 | `wrong_agent` | Concern profile drawn from a different agent's history | **Control.** Rejects "any historical profile helps." | Uses `wrong_agent_id` inside the evaluator only. |

Notes:

- **Two candidate variants, one screen decision.** C2a and C2b are two
  variants of the same update rule. The screen decision is: does at
  least one of them pass every fatal gate in §5 while the other does
  not fail on adversarial specificity (§5.3)? If both variants fail,
  the rule KILLs. If exactly one passes, the pass is reported with its
  estimator tag; the other is reported as diagnostic.
- **Oracle is diagnostic.** C3 defines the ceiling headroom; it is
  reported for every family but never promoted.
- **Shuffled and wrong-agent are specificity controls.** If either C4
  or C5 achieves an outcome mean within
  `sigma_hat_multiplicative_wave0` (per family, from
  [`../wave0/PROVENANCE.md`](../wave0/PROVENANCE.md) §4) of the
  online-learned condition, the screen KILLs on specificity.

## 5. Fatal gates by claim

Fatal gates are copied from the roadmap
(`docs/concern_gated_retrieval_research_program.md` § "Fatal gates by
claim" and § "Required anti-shortcut design"). Each gate is
noncompensatory. Failure of any one is a Wave 1a KILL and forbids
signing §8. The rejection copy is honest and preserved in
[`PROVENANCE.md`](PROVENANCE.md) §5 regardless of outcome.

### 5.1 Coverage (adequate exploration of the true commitment region)

For every `(family, condition)` cell that logs receipts,
propensity-weighted coverage of the true commitment region under the
logging policy must clear the preregistered floor. The floor is
inherited from Wave 0's frozen `DEFAULT_EPSILON = 0.05` exploration
constant on the `LoggedProbePolicy` wrapper.

Formally, let `receipts_{f,c}` be the receipts produced in family `f`
under condition `c`, and let `TCR(f)` be the true commitment region
declared in [`../wave0/PREREGISTRATION.md`](../wave0/PREREGISTRATION.md)
§5 for family `f` (`date-anchored personal obligation`, `old
observation exposed by a later symptom`, `prior obligation constraining
otherwise-valid action`). Then:

```
coverage_{f,c} = ( Σ_{r ∈ receipts_{f,c}}  𝟙[r.candidate ∈ TCR(f)] / r.selection_propensity )
                 / len(receipts_{f,c})
```

**Gate:** `coverage_{f,c} >= 0.01` for every family `f` and every
receipt-producing condition `c ∈ {C2a, C2b, C4, C5}`.

The floor `0.01` is derived from Wave 0's default exploration constant
`epsilon = 0.05` and the confirmatory candidate cardinality
(`|candidate_nodes| ≤ 20` by the Wave 0 family generators). Under the
logging policy the expected propensity-weighted count of receipts
falling in `TCR(f)` per receipt is at least
`epsilon * |TCR(f)| / |candidate_nodes| ≥ 0.05 * 1 / 20 = 0.0025`;
the floor `0.01` is `~4×` that lower bound and thereby detects a
degenerate logging distribution before the estimators are called. Any
confirmatory row whose coverage falls below the floor is rejected
pre-analysis; if the pre-analysis rejection rate on any `(family,
condition)` cell exceeds 5% of that cell's confirmatory rows, the gate
FAILs and the wave KILLs.

### 5.2 Propensity accounting

Every IPS and DR estimate must clear the following runtime checks
before it enters an aggregated statistic. Each is enforced by the
existing Wave 0 guards; Wave 1a's contribution is the receipt.

1. **Strict positivity.** Every logged `selection_propensity` is
   strictly in `(0, 1]` (enforced by
   `ProbeReceipt.__post_init__`).
2. **Homogeneous family split.** Every receipt in a single
   `update_concern` call carries `template_family_split =
   "calibration"` for Wave 1a's calibration replays, or
   `"confirmatory"` for the confirmatory sweep. Mixing splits raises
   `LeakageError` (`wave0.concern_update.update_concern`).
3. **Poisoning-guard receipt.** Every aggregated update carries a
   per-source magnitude clamp receipt with `max_source_influence =
   DEFAULT_MAX_SOURCE_INFLUENCE` (Wave 0 §4.4). Untrusted-source
   sweeps are out of Wave 1a scope; any receipt with a non-`"trusted"`
   `source_id` in the confirmatory sweep is a fatal integrity failure.
4. **ESS floor.** The IPS effective sample size
   `(Σ 1/p)² / Σ 1/p²` for every `(family, condition)` cell must be
   at least `50` (≈ 17% of the 300-seed cell). A cell below this floor
   is rejected pre-analysis; the same 5%-of-cell aggregate rejection
   ceiling as in §5.1 applies.

### 5.3 Specificity vs generic value / priority / recency signals

The screen must not be reproduced by a generic signal. Wave 0's
info-matched baselines (`info_matched_value`, `info_matched_priority`,
`info_matched_recency`, from
[`../wave0/PREREGISTRATION.md`](../wave0/PREREGISTRATION.md) §7 lines
10–12) supply the frozen generic-signal reference under the same wrong
prior. The specificity gate FAILs if any of the following holds for
any family:

- The best info-matched generic-signal condition's confirmatory sealed
  outcome mean meets or exceeds the online-learned condition's mean
  minus `sigma_hat_best_matched_wave0` (per-family, from
  [`../wave0/PROVENANCE.md`](../wave0/PROVENANCE.md) §4).
- The `shuffled` condition (C4) mean is within
  `sigma_hat_multiplicative_wave0` of the online-learned condition on
  that family.
- The `wrong_agent` condition (C5) mean is within
  `sigma_hat_multiplicative_wave0` of the online-learned condition on
  that family.

A specificity FAIL on any family KILLs the rule; aggregate specificity
cannot compensate.

### 5.4 No aggregate hiding a family reversal

The primary Wave 1a effect (§6) must survive every preregistered
family independently. Every threshold in §6 is a **per-family**
threshold. Aggregate success across families does not clear a
per-family failure; a per-family reversal (online-learned worse than
frozen-wrong at any threshold-sized margin) KILLs regardless of the
other two families.

### 5.5 Anti-leakage integrity

Inherited from Wave 0. No evaluator-only field is reachable from any
Wave 1a policy code path. The `IntegrityAudit` AST walker
(`wave0.sealed_env`) gates every callable that enters the confirmatory
sweep. A single audited violation is a fatal integrity failure that
retroactively demotes any dependent statistic.

### 5.6 Adversarial (poisoning) tolerance registration

Wave 1a registers the same single-source influence bound as Wave 0
(`DEFAULT_MAX_SOURCE_INFLUENCE = 1.0`, `DEFAULT_ETA = 0.10`). Wave 1a
does **not** execute untrusted-source poisoning stress; that is a Wave
1b or Wave 4 object. Wave 1a is out of specification if any receipt
carries a non-`"trusted"` `source_id`.

## 6. Frozen effect thresholds

The Wave 1a effect thresholds are frozen against the Wave 0
calibration receipt in
[`../wave0/PROVENANCE.md`](../wave0/PROVENANCE.md) §4. That receipt is
identified by the Wave 0 analysis-code hash
`WAVE0_ANALYSIS_HASH = 9683c5a1f4010361d6e120bcabd2743fb33e8cc9c7c79d5bd9b1d9f9f8889c23`
and is verified byte-for-byte at Wave 1a signature time; a mismatch is
a fatal integrity failure that prevents §8 from being signed.

### 6.1 Threshold shape (frozen at signature time)

For each family `f ∈ {delayed_commitments, maintenance_fault,
resource_constrained}` and each online-learned variant `v ∈ {ips, dr}`:

- `delta_hat_{f,v}` — confirmatory paired-seed mean of
  `mu_hat(online_learned_v, f) − mu_hat(frozen_wrong, f)`.
- `sigma_delta_{f,v}` — paired-seed standard error of `delta_hat_{f,v}`.
- `distance_to_oracle_{f,v}` — diagnostic:
  `mu_hat(oracle, f) − mu_hat(online_learned_v, f)`. Must be
  non-negative; not a promotable claim.
- `delta_thresh_E2a_{f}` — the per-family screening threshold, frozen as

```
  delta_thresh_E2a_{f} =
      max( 2 * sigma_hat_multiplicative_wave0_{f} / sqrt(N_per_condition_per_family),
           0.10 * headroom_to_ceiling_wave0_{f},
           2 * sigma_hat_best_matched_wave0_{f} )
```

  where the Wave 0 quantities are the frozen values in
  [`../wave0/PROVENANCE.md`](../wave0/PROVENANCE.md) §4 and
  `N_per_condition_per_family = 300` (§7).

### 6.2 Populated per-family thresholds

Computed from the Wave 0 frozen calibration receipt and pinned here at
draft time. These values become authoritative once §8 is signed; any
subsequent change is a redesign, not an update.

| Family | `sigma_hat_multiplicative_wave0` | `sigma_hat_best_matched_wave0` | `headroom_to_ceiling_wave0` | `2σ_mult / √300` | `0.10 · headroom` | `2 σ_best` | `delta_thresh_E2a` |
|---|---|---|---|---|---|---|---|
| `delayed_commitments` | 0.2080 | 0.0218 | 0.4845 | 0.02401 | 0.04845 | 0.04360 | **0.04845** |
| `maintenance_fault`   | 0.1483 | 0.0267 | 0.4548 | 0.01712 | 0.04548 | 0.05340 | **0.05340** |
| `resource_constrained`| 0.2905 | 0.0250 | 0.4291 | 0.03354 | 0.04291 | 0.05000 | **0.05000** |

### 6.3 Screen decision rule

The screen decision for a candidate variant `v ∈ {ips, dr}` is:

- **PASS on family `f`** iff
  `delta_hat_{f,v} − 2 * sigma_delta_{f,v} >= delta_thresh_E2a_{f}`
  (a lower-bound decision, not a point estimate).
- **Variant screen PASS** iff `v` PASSes every family independently
  and every §5 gate holds for `v` on every family.
- **Wave 1a PASS** iff at least one variant screen PASSes and the
  other variant does not fail on §5.3 specificity in a way that
  contaminates the passing variant's receipt.
- **Wave 1a KILL** in every other case.

## 7. Sample size and seed plan

- **Confirmatory seed pool.** `200000..201999` (2000 seeds).
  Calibration seeds `100000..100999` are inaccessible; the Wave 0
  template-split guard raises `LeakageError` on misuse. Wave 1a runs
  with `COGR_WAVE0_CONFIRMATORY_RUN=1` set at Modal spawn time; this
  is the first stage in the program licensed to read the confirmatory
  pool.
- **Per-cell sample size.** Each `(family, condition)` cell contains
  at least **300 seeded episodes**. With three families this is
  **N_total_per_condition = 900** for each of the five conditions,
  for a total of **4500 (condition × family × seed) receipts**.
- **Paired design.** The 900 seeds per condition are the same 900
  seeds across all five conditions (paired at the seed level). This
  supports paired-seed variance estimation of `delta_hat_{f,v}` and
  reduces the per-family standard error against the frozen Wave 0
  reference.
- **Seed allocation.**
  - `delayed_commitments`: `200000..200299`
  - `maintenance_fault`: `200300..200599`
  - `resource_constrained`: `200600..200899`
  - Reserved (pre-analysis rejection replays, §5.1 / §5.2 gates only,
    replayable knob-limited): `200900..201999`.
- **Replayable knobs.** Only the following knobs may be rerun after a
  fatal gate rejection, and only within the reserved replay range
  `200900..201999`; every other knob is frozen at signature time. This
  enumeration is exhaustive; no other knob may be replayed under any
  circumstance.
  1. `LoggedProbePolicy.epsilon` — replayable up to `epsilon = 0.10`
     if §5.1 coverage fails on a single `(family, condition)` cell.
     Values above `0.10` are a redesign.
  2. `update_concern.eta` — replayable within `[0.05, 0.20]` if §5.2
     ESS fails without §5.1 also failing.
  3. Cell-level rejection replay — a rejected row from
     `200000..200899` is replaced by the next available seed from the
     replay reserve `200900..201999`, capped at 30% of that cell's
     receipts. Above 30% is a redesign.
- **Non-replayable knobs.** Family definitions, condition definitions,
  Wave 0 prior weights (`W_ALARM_INIT = 1.0`, `W_COMMIT_INIT = 0.05`),
  poisoning-guard bounds, template split, seed range, per-family
  threshold values (§6.2), and the `IntegrityAudit` guard list. Any
  change to these is a redesign and requires a new preregistration
  hash.
- **Modal execution.**
  - App name: `research-derived-cogr-wave1a-e2a`.
  - GPU type: L4 only (H100 forbidden by the wave-wide operating
    rule).
  - `max_containers`: up to 32 (explicitly authorized by the human
    director for this wave; every other constraint from Wave 0 still
    holds).
  - Doppler scope: `/Users/jawaun/superoptimizers`.
  - Deploy before spawn (per the deployed-image rule); the deployed
    image hash is recorded in [`PROVENANCE.md`](PROVENANCE.md).

## 8. Analysis-code freeze plan

Wave 1a is not signed until the analysis and sweep code that produced
the confirmatory receipt is content-hashed and pinned.

- **Scope of the hash.** SHA-256 over the concatenated bytes of every
  tracked file under
  `experiments/concern_gated_retrieval_e2/wave1a/**`, computed in
  sorted path order after the confirmatory Modal run completes and
  every per-family threshold in §6.2 has been tested against the
  paired confirmatory rows.
- **Where the hash lives.** In this section, replacing
  `WAVE1A_ANALYSIS_HASH = TBD`, and mirrored into
  [`PROVENANCE.md`](PROVENANCE.md) alongside the Modal deploy hash,
  the confirmatory seed-range receipt, and the coverage-audit receipt.
- **What the hash freezes.** The Wave 1a condition runner, the
  coverage audit, the specificity check, the paired-seed variance
  estimator, the screen decision rule (§6.3), and this
  preregistration. Wave 1b is scored against Wave 1a's frozen receipt
  only for its Wave 1a inheritance clauses; Wave 1b's L1 rows are
  frozen against its own future preregistration.

```
WAVE1A_ANALYSIS_HASH = TBD
```

- **Byte-for-byte Wave 0 verification.** At signature time the Wave 0
  hash referenced in §6 is verified byte-for-byte against
  [`../wave0/PROVENANCE.md`](../wave0/PROVENANCE.md) §6. A mismatch
  prevents §8 from being signed.
- **Honor-the-freeze rule.** No post-hoc corpus swap, threshold swap,
  seed-range swap, family swap, or condition swap is permitted after
  the hash is written. Only the replayable knobs in §7 may be rerun,
  and only within the ex-ante ranges named there. The
  honor-the-preregistration rule (human director's memory,
  `feedback-honor-pre-registration`) is authoritative and binds this
  document.
