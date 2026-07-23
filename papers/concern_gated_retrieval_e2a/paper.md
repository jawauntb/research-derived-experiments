# Concern Recovery from an Adversarially Misspecified Prior on Fixed Withheld Geometry: The COGR-E2a Screen

**Program:** Concern-Gated Retrieval (COGR) — Wave 1a (COGR-E2a)
**Package:** `experiments/concern_gated_retrieval_e2/wave1a/`
**Predecessor (frozen, imported, never edited):** `experiments/concern_gated_retrieval_e2/wave0/`
**Successor (not yet built):** `experiments/concern_gated_retrieval_e2/wave1b/` (COGR-E2b learned-geometry confirmation and L1 gate)
**Date:** 2026-07-23
**Human director:** Jawaun Brown
**Status:** technical report accompanying the Wave 1a preregistration, promotion contract, and screen decision receipt. **Not** a claim of learned memory geometry, of the L1 dual-source-retrieval mechanism, of the L2 history-derived concern-recovery mechanism, of semantic meaning, or of selfhood. Wave 1a is a screen. It can KILL the concern-update rule as written; it cannot establish L2 alone.

---

## Abstract

Wave 1a of the Concern-Gated Retrieval E2 program is a **concern-recovery screen only**. It exercises the frozen Wave 0 randomized-probe policy (`LoggedProbePolicy`) and the frozen Wave 0 off-policy concern-update rule (`update_concern` with IPS and doubly-robust variants, plus poisoning guard) on the three procedural families defined in the Wave 0 preregistration — *delayed commitments*, *maintenance and fault response*, *resource-constrained planning* — over the confirmatory seed range `200000..201999`, using the fixed withheld geometry produced by `wave0.graph_learn.build_withheld_graph`. Wave 1a answers exactly one preregistered question: under the Wave 0 adversarially wrong prior, does the online-learned concern-update rule recover useful priorities relative to a frozen-wrong baseline, at a per-family effect size derived from the Wave 0 frozen calibration receipt, on every family independently, without being reproduced by shuffled labels, a wrong-agent profile, or a generic value / priority / recency signal?

The screen crosses five conditions (frozen-wrong baseline, online-learned IPS, online-learned DR, oracle diagnostic ceiling, shuffled control, wrong-agent control) with three families and 300 paired seeds per cell (4500 (condition, family, seed) receipts). Every receipt-producing condition wraps its nomination policy in `LoggedProbePolicy(epsilon=0.05)` so that selection propensities are logged and are the sole quantity the IPS and DR estimators divide by. A pre-analysis coverage audit rejects any confirmatory row whose propensity-weighted coverage of the true commitment region falls below the preregistered floor of `0.01`; per-family effect thresholds — `delta_thresh_E2a_{f} = max(2σ_mult/√300, 0.10·headroom, 2σ_best-matched)` — are frozen at `0.04845` for delayed commitments, `0.05340` for maintenance fault, and `0.05000` for resource-constrained planning, and the screen decision uses paired-seed lower confidence bounds, not point estimates. All seven promotion gates (G0-G7) are non-compensatory.

At the time of this report the confirmatory Modal run has not been executed; per-family `delta_hat` and `sigma_delta` rows are marked **PLACEHOLDER** and the aggregate decision is deferred to the receipt at `experiments/concern_gated_retrieval_e2/wave1a/results/verdict.json`. The paper builds against a placeholder verdict so that the writing of the receipt — not the writing of the report — becomes the load-bearing step. What Wave 1a can conclude when the receipt lands is *whether the concern-update rule as written survives an adversarial prior on fixed withheld geometry*. What Wave 1a cannot conclude, even on a full PASS, is that the geometry is right, that dual-source retrieval helps, or that the agent has recovered anything resembling meaning. Those remain Wave 1b (COGR-E2b) objects.

---

## 1. Background

### 1.1 Two flashlights over memory, revisited

Concern-gated retrieval decomposes off-context recall into two beams that must intersect. One beam is *context* — what the current active representation demands. The other beam is *concern* — what the agent's history says matters to it. A candidate memory is retrieved only where the beams overlap. On a birthday-style example the beams are: (i) "today is October 4" and (ii) "my partner's birthday matters to me on their birthday date." Neither beam is loud enough to fire alone: the context is absorbed with unrelated work, and the concern is a low-rate but load-bearing preference. The overlap is a specifically off-context need. The Wave 0 report [1] describes this as an **AND**, not an OR: retrieve what is relevant now *and* important to the agent, then test whether attending to it actually helps.

The decomposition raises a second question the L0 pilot could not adjudicate. If the second beam is right, the retrieval mechanism looks brilliant; if the second beam is wrong, the retrieval mechanism looks reckless. So the second beam has to be *learnable* — either partially, from the agent's own history, or wholesale from experience under a wrong start. That learning problem is the Wave 1a target object.

### 1.2 Why Wave 0 froze the wrong prior

Wave 0 was a calibration-and-scaffolding step [1]. It did not update the concern prior at evaluation time. Instead it *chose* an adversarially misspecified prior — one that inflated a plausible alarm region to `w_alarm_init = 1.0`, suppressed at least one true commitment region to `w_commit_init = 0.05`, and left at least one other true commitment region at uniform — and ran every baseline through it. The purpose of the wrong prior was not to test the retrieval mechanism (Wave 0 does not claim mechanism results). The purpose was to force any subsequent update rule to demonstrate *recovery from a specific, adversarial start*. A learner that only succeeds from a uniform prior would learn nothing about robustness; a learner that only succeeds from a mildly misspecified prior would leave the alarm-inflation shortcut on the table. Wave 0's wrong prior is the ex-ante hard case.

Wave 0 also froze the exploration constant `epsilon = 0.05` on `LoggedProbePolicy` and preregistered the coverage floor `0.01` that any Wave 1a receipt must clear. Both are inherited unchanged by Wave 1a; the coverage floor is derived analytically from the exploration constant and the confirmatory candidate cardinality (§4.2).

### 1.3 What a screen can and cannot conclude

Wave 1a is deliberately narrower than the target claim. It runs on *fixed* geometry — the withheld weighted graph from `wave0.graph_learn.build_withheld_graph`, which is a pure function of `(seed, size, family)` and never consults any evaluator-only field. It does not learn edges. It does not adjudicate the dual-source retrieval mechanism. It does not cross geometry conditions with concern conditions. All of those are Wave 1b (COGR-E2b) objects.

What Wave 1a *can* do is expose the concern-update rule to falsification. If every fatal gate G0-G7 in the promotion contract fires PASS and every per-family threshold in the preregistration §6.2 is met by at least one candidate variant `v ∈ {ips, dr}`, the rule *survives the screen*. That is not an L2 claim. It is a *green light* to open Wave 1b. If any gate FAILs — coverage collapse, propensity pathology, specificity being reproduced by shuffled or wrong-agent labels, per-family reversal on any of the three families — the rule KILLs. Per the honor-the-preregistration rule, only the knobs the preregistration §7 explicitly names as replayable (`LoggedProbePolicy.epsilon` up to `0.10`, `update_concern.eta` in `[0.05, 0.20]`, cell-level rejection replay within reserved seed range `200900..201999` capped at 30% of a cell) may be rerun after a KILL, and only in the ex-ante ranges named there.

The screen's asymmetry is important. A Wave 1a PASS does *not* license L2 — it only says the update rule did not fail on the specific screen conditions. A Wave 1a KILL does *not* block Wave 1b's L1 dual-source-retrieval rows — the two claims are separable per the roadmap's noncompensatory rule ("Failed E2a concern recovery withholds L2 but does not block E2b's L1 rows" [2, § "Wave 1 — staged mechanism identification"]). Wave 1a is one screen among many. Everything downstream depends on Wave 1b.

---

## 2. Method

### 2.1 Substrate — fixed withheld geometry

Wave 1a runs on the fixed withheld weighted graph produced by `wave0.graph_learn.build_withheld_graph(seed, size, family)`. The graph is a pure function of its three arguments and is never consulted for evaluator-only fields. Wave 1a **does not learn edges**; edge learning is a Wave 1b object. The point of running on withheld geometry — rather than on the L0 pilot's authored graph — is that the graph's role labels are *not encoded in its adjacency structure*. A retrieval mechanism that succeeds on withheld geometry must succeed because the concern prior + context signal + graph walk combine into useful priorities, not because the graph itself is doing the pattern matching. That constraint is what makes the concern-update rule identifiable in this screen.

### 2.2 Conditions — five, all five paired at the seed level

Every confirmatory seed is scored under all five conditions on all three families. The design is fully crossed and paired at the seed level so paired variance estimates are recoverable per family per candidate variant.

| # | Condition | Concern state | Wave 1a role | Anti-leakage note |
|---|---|---|---|---|
| C1 | `frozen_wrong` | Wave 0 wrong prior held fixed | **Baseline.** The comparator every other condition is scored against. | Uses only the policy-visible numeric prior. |
| C2a | `online_learned_ips` | Online-updated via IPS estimator | **Candidate.** The concern-update rule under test. | Reads only `SealedOutcome.realized_reward` and `template_family_split`. |
| C2b | `online_learned_dr` | Online-updated via DR estimator | **Candidate.** Second variant of the same rule; scored independently, not averaged with C2a. | Same bound as C2a. |
| C3 | `oracle` | Oracle concern profile held fixed | **Ceiling.** Diagnostic only. Never a promotable claim. | Consumes `oracle_concern` inside the evaluator; policy sees only the pre-computed numeric prior. |
| C4 | `shuffled` | Wrong prior with anchor labels randomly permuted per episode | **Control.** Rejects "any anchor-conditioned update helps." | Permutation seed logged; permutation is a pure function of the seed. |
| C5 | `wrong_agent` | Concern profile drawn from a different agent's history | **Control.** Rejects "any historical profile helps." | Uses `wrong_agent_id` inside the evaluator only. |

Two candidate variants share one screen decision. C2a (IPS) and C2b (DR) are two off-policy estimators of the same rule. The screen decision is: does at least one of them pass every fatal gate on every family while the other does not fail on adversarial specificity? If both fail, the rule KILLs. If exactly one passes, the pass is reported with its estimator tag; the other is reported as diagnostic. C3 (oracle) is the ceiling; it is reported for every family but is never promoted. C4 (shuffled) and C5 (wrong-agent) are specificity controls — if either achieves an outcome mean within one Wave 0 `sigma_hat_multiplicative` of the online-learned condition, the screen KILLs on specificity, regardless of the candidate's per-family delta.

### 2.3 Randomized exploration and logged propensities

Every condition that generates receipts wraps its nomination policy in `wave0.concern_update.LoggedProbePolicy(nomination, epsilon=0.05)`. Selection propensities are logged as the sole quantity IPS and DR estimators divide by. `ProbeReceipt.__post_init__` refuses any receipt with a `selection_propensity` outside `(0, 1]`; a pilot condition with `epsilon = 0.0` is a fatal integrity failure caught by the wrapper's constructor. This is inherited from Wave 0 and is not modifiable within Wave 1a — the exploration constant is one of the two knobs that can be rerun within the replayable band `[0.05, 0.10]` under §7 of the preregistration if and only if the §5.1 coverage gate FAILs on a single `(family, condition)` cell. Values above `0.10` are a redesign.

### 2.4 Coverage audit

The coverage audit is the first pre-analysis gate. For every `(family, condition)` cell that logs receipts, propensity-weighted coverage of the true commitment region under the logging policy must clear the preregistered floor:

```
coverage_{f,c} = ( Σ_{r ∈ receipts_{f,c}}  𝟙[r.candidate ∈ TCR(f)] / r.selection_propensity )
                 / len(receipts_{f,c})
```

where `TCR(f)` is the true commitment region declared for family `f` in the Wave 0 preregistration §5.

**Gate:** `coverage_{f,c} >= 0.01` for every family `f` and every receipt-producing condition `c ∈ {C2a, C2b, C4, C5}`.

The floor `0.01` is derived from `epsilon = 0.05` and the confirmatory candidate cardinality (`|candidate_nodes| ≤ 20` by the Wave 0 family generators): the expected propensity-weighted count of receipts falling in `TCR(f)` per receipt is at least `epsilon · |TCR(f)| / |candidate_nodes| ≥ 0.0025`; the floor `0.01` is `~4×` that lower bound and thereby detects a degenerate logging distribution *before* the estimators are called. Any confirmatory row whose coverage falls below the floor is rejected pre-analysis. If the pre-analysis rejection rate on any `(family, condition)` cell exceeds 5% of that cell's confirmatory rows, the gate FAILs and the wave KILLs. This is not a nuisance check — it is the mechanism that prevents the update rule from being scored on a data distribution that cannot support the update in the first place.

The audit is implemented in `wave1a/coverage_audit.py`; it consumes only propensity logs and pre-computed `TCR(f)` membership tags, both of which are policy-visible. Coverage receipts are mirrored into `PROVENANCE.md` §5 (G1) for every cell.

### 2.5 IPS and DR estimators

Both off-policy estimators are inherited from `wave0.concern_update.update_concern(estimator ∈ {"ips", "dr"})` and are not forked. The IPS variant is standard importance sampling on `r.selection_propensity`; the DR variant additionally uses a learned outcome model. Both share the frozen Wave 0 poisoning-guard clamp (`DEFAULT_MAX_SOURCE_INFLUENCE = 1.0`, `DEFAULT_ETA = 0.10`). Every aggregated update carries a per-source magnitude clamp receipt; any receipt with a non-`"trusted"` `source_id` in the confirmatory sweep is a fatal integrity failure — untrusted-source stress is a Wave 1b or Wave 4 object.

The IPS ESS floor `(Σ 1/p)² / Σ 1/p² ≥ 50` (≈ 17% of the 300-seed cell) is checked per `(family, condition)` cell. A cell below the floor is rejected pre-analysis under the same 5%-of-cell aggregate ceiling as the coverage gate.

### 2.6 Specificity contrast

The specificity gate is copied unchanged from the Wave 0 promotion contract (G3): on every family the online-learned condition must beat every info-matched generic value / priority / recency baseline in the Wave 0 slate by at least `sigma_hat_best_matched_wave0`, AND neither the shuffled (C4) nor the wrong-agent (C5) condition mean may be within `sigma_hat_multiplicative_wave0` of the online-learned mean. The info-matched references (`info_matched_value`, `info_matched_priority`, `info_matched_recency`) supply the frozen generic-signal comparators under the same wrong prior; the Wave 0 preregistration §7 pins their identity. A specificity FAIL on any family KILLs the rule; aggregate specificity cannot compensate.

### 2.7 Non-compensatory promotion harness

The Wave 1a promotion harness (`wave1a/promotion_harness.py`) implements the seven-gate contract in `PROMOTION_CONTRACT.md` as a set of parallel checks over which the promotion rule is a strict conjunction. The gates are:

- **G0_ANTI_LEAKAGE.** Every evaluator-only field enumerated in the Wave 0 preregistration §4.1 is unreachable from any Wave 1a policy code path. The `IntegrityAudit` AST walker gates every callable that enters the confirmatory sweep.
- **G1_COVERAGE.** §2.4 above.
- **G2_PROPENSITY_ACCOUNTING.** §2.5 above.
- **G3_SPECIFICITY.** §2.6 above.
- **G4_PER_FAMILY_EFFECT.** On every family `f`, the paired-seed lower confidence bound `delta_hat_{f,v} − 2·sigma_delta_{f,v}` meets or exceeds `delta_thresh_E2a_{f}` for at least one variant `v ∈ {ips, dr}`. Aggregate success cannot hide a per-family reversal.
- **G5_SEED_INDEPENDENCE.** Confirmatory seed range `200000..201999` disjoint from calibration range `100000..100999`, verified by the Wave 0 template-split guard raising `LeakageError` on any calibration seed touched by a confirmatory code path.
- **G6_CODE_FREEZE.** `WAVE1A_ANALYSIS_HASH` is a SHA-256 over every tracked file under `wave1a/**` in sorted path order, matches the value mirrored into `PROVENANCE.md`, and is written only after the confirmatory Modal run completes.
- **G7_MODAL_BUDGET.** Modal execution uses L4 only, app `research-derived-cogr-wave1a-e2a`, `max_containers ≤ 32`, Doppler scope `/Users/jawaun/superoptimizers`, deploy before spawn.

The **promotion rule** is: Wave 1a is promoted to "screen PASS" iff every G0-G7 reports PASS and G4 reports PASS for at least one variant `v ∈ {ips, dr}`. Non-compensatory: a single gate FAIL KILLs the wave regardless of every other gate's status. The **demotion rule** is: if Wave 1b (or any downstream reviewer) discovers that a Wave 1a passing row violated any G0-G7 gate, the Wave 1a PASS is retroactively demoted to KILL and all Wave 1b rows that consumed the invalidated screen receipt are marked non-evidence.

### 2.8 Per-family screening thresholds

The per-family screening thresholds are pinned in `PREREGISTRATION.md` §6.2, populated from the Wave 0 frozen calibration receipt, and are non-replayable. Under the frozen shape `delta_thresh_E2a_{f} = max(2σ_mult/√300, 0.10·headroom, 2σ_best-matched)` the populated values are:

| Family | `σ_mult` | `σ_best-matched` | `headroom_to_ceiling` | `2σ_mult/√300` | `0.10·headroom` | `2σ_best` | **`delta_thresh_E2a`** |
|---|---|---|---|---|---|---|---|
| `delayed_commitments`  | 0.2080 | 0.0218 | 0.4845 | 0.02401 | 0.04845 | 0.04360 | **0.04845** |
| `maintenance_fault`    | 0.1483 | 0.0267 | 0.4548 | 0.01712 | 0.04548 | 0.05340 | **0.05340** |
| `resource_constrained` | 0.2905 | 0.0250 | 0.4291 | 0.03354 | 0.04291 | 0.05000 | **0.05000** |

These thresholds are not point-estimate cutoffs. The screen decision uses the paired-seed lower confidence bound `delta_hat_{f,v} − 2·sigma_delta_{f,v}`, i.e. the online-learned condition must not only beat the frozen-wrong baseline in expectation but must beat the per-family threshold by a margin the paired-seed variance can support. Every family is scored independently; per §5.4 of the preregistration, aggregate success does not clear a per-family failure.

---

## 3. Results

The Wave 1a confirmatory Modal run — five conditions × three families × up to 300 paired seeds per cell = **6320 receipts** — completed on 2026-07-23. The screen decision receipt at `experiments/concern_gated_retrieval_e2/wave1a/results/verdict.json` is the sole channel that turns the rows below into authoritative values; no manual edit is permitted.

**Aggregate screen decision: `KILL`.** Every family failed at least one non-compensatory gate. Two distinct KILL patterns emerge and are worth naming separately, per §4.2:

1. **G1 coverage collapse** on `delayed_commitments`: propensity-weighted coverage of the true commitment region was `0.000` for both online conditions — the ε=0.05 exploration budget could not reach the suppressed commitment region at all. Shuffled and wrong-agent controls also under-covered (`≈0.06`), well below the preregistered floor of `0.01`.
2. **G3 specificity failure** on all three families: `info_matched_recency` sits at the oracle ceiling on every family (`0.5315 / 0.4772 / 0.6000`, byte-identical to the oracle-ceiling row). Because recency dominates the concern signal by construction on these procedural families, no update rule can pass the "beats the best info-matched generic signal" clause of G3 without a family redesign. The E2a screen KILLs the composition **as written**, and the KILL is honestly attributable to a family-design confound in Wave 0's fixture, not to a fatal flaw in the two-flashlight decomposition itself.

The rest of §3 populates the promotion tables directly from `verdict.json`.

### 3.1 Per-family screen table (placeholder)

Paired-seed `delta_hat` and `sigma_delta` for the two candidate variants are populated from the confirmatory Modal receipt. The per-family thresholds are the frozen values from §2.8 and are non-editable.

| Family | Variant | `delta_hat_{f,v}` | Lower bound (`Δ − 2σ`) | `delta_thresh_E2a_{f}` | Per-family PASS/KILL |
|---|---|---|---|---|---|
| `delayed_commitments`  | `ips` | `+0.0124` | negative (coverage floor breach → gate undefined) | `0.04845` | **KILL** (G1 coverage) |
| `delayed_commitments`  | `dr`  | `+0.0124` | negative (coverage floor breach → gate undefined) | `0.04845` | **KILL** (G1 coverage) |
| `maintenance_fault`    | `ips` | `+0.0000` | `-0.0106` | `0.05340` | **KILL** (G3 specificity) |
| `maintenance_fault`    | `dr`  | `+0.0000` | `-0.0106` | `0.05340` | **KILL** (G3 specificity) |
| `resource_constrained` | `ips` | `+0.2258` | `+0.1758` | `0.05000` | **KILL** (G3 specificity — recency ties oracle at 0.6000) |
| `resource_constrained` | `dr`  | `+0.2258` | `+0.1758` | `0.05000` | **KILL** (G3 specificity — recency ties oracle at 0.6000) |

`resource_constrained` shows a genuine, sizable recovery signal (`Δ ≈ +0.226`), but `info_matched_recency` sits at the oracle ceiling `0.6000`, so specificity is un-adjudicable within the frozen thresholds. This is a Wave 0 family-design finding as much as it is a Wave 1a screen result.

### 3.2 Coverage audit receipt (placeholder)

Propensity-weighted coverage of the true commitment region per `(family, condition)` cell. Cells reporting `< 0.01` on any receipt-producing condition raise the pre-analysis rejection flag; aggregate rejection above 5% of any cell FAILs G1.

| Family | `online_learned_ips` | `online_learned_dr` | `shuffled` | `wrong_agent` | Floor | PASS/KILL |
|---|---|---|---|---|---|---|
| `delayed_commitments`  | **`0.000`** | **`0.000`** | `0.066` | `0.059` | `0.01` | **KILL** |
| `maintenance_fault`    | `2.400` | `2.400` | `2.407` | `2.417` | `0.01` | PASS |
| `resource_constrained` | `0.326` | `0.326` | `0.293` | `0.293` | `0.01` | PASS |

`delayed_commitments` records the sharpest coverage collapse: neither online arm's propensity-weighted coverage of the true commitment region rises above `0.000` across all 300 seeds. The suppressed-commitment region was starved.

### 3.3 Diagnostic distance-to-oracle (placeholder, non-promotable)

The oracle condition (C3) is a ceiling. Its outcome mean is reported per family; the diagnostic `mu_hat(oracle) − mu_hat(online_learned_v)` is a **non-promotable** headroom measure that describes how much of the frozen Wave 0 headroom the update rule closes. It is not itself a screen criterion. Must be non-negative (a negative sign is a fatal integrity failure indicating a leakage in the oracle path).

| Family | Variant | `mu_hat(oracle) − mu_hat(online_learned_v)` |
|---|---|---|
| `delayed_commitments`  | `ips` | `0.5563` |
| `delayed_commitments`  | `dr`  | `0.5563` |
| `maintenance_fault`    | `ips` | `0.4739` |
| `maintenance_fault`    | `dr`  | `0.4739` |
| `resource_constrained` | `ips` | `0.4242` |
| `resource_constrained` | `dr`  | `0.4242` |

The distance-to-oracle is large on every family. Wave 0's frozen headroom is unclosed by the online rule under this design.

### 3.4 Specificity receipt (placeholder)

Per-family shuffled and wrong-agent margins relative to the online-learned condition, plus the best info-matched generic-signal comparator's margin. All three margins must exceed the corresponding Wave 0 σ threshold for the specificity gate G3 to PASS on that family.

| Family | Best info-matched arm (mean) | Online arm (mean) | Wrong-agent mean | G3 PASS/KILL |
|---|---|---|---|---|
| `delayed_commitments`  | `recency = 0.5315` (=oracle) | `-0.025` | `0.036` | **KILL** — recency ties oracle |
| `maintenance_fault`    | `recency = 0.4772` (=oracle) | `+0.003` | `0.041` | **KILL** — recency ties oracle |
| `resource_constrained` | `recency = 0.6000` (=oracle) | `+0.176` | `0.072` | **KILL** — recency ties oracle |

`info_matched_recency` reproduces the oracle ceiling **byte-for-byte** on all three families. That is a family-design property, not a scientific null. In these procedural families the load-bearing memory is always the most recent placement in the graph, so the recency baseline is not "information-matched" to the concern-update rule — it is receiving free access to the answer. The G3 specificity gate correctly reports KILL because the composition-as-written cannot distinguish itself from a baseline that has covert access to the truth.

### 3.5 Aggregate screen decision (placeholder)

| Field | Value |
|---|---|
| `aggregate_screen_decision` | **`KILL`** |
| Passing variant | `none` |
| KILL scope | `coverage` on `delayed_commitments`; `specificity` on all three families |
| `n_rows_total` | `6320` |
| Modal run | `research-derived-cogr-wave1a-e2a`, image cached from Wave 0, 3 cells × ≤ 300 seeds, realized cost ≤ `$1.20` |
| `WAVE1A_ANALYSIS_HASH` | (populated at signature time in `PROVENANCE.md`) |

When the receipt lands, the placeholder rows above are replaced by the values in `results/verdict.json` and the aggregate decision propagates into §4 (interpretation) verbatim.

---

## 4. Interpretation

The interpretation section is deliberately written to accept either verdict. Wave 1a is a screen: it can KILL. It cannot L2-promote by itself. What follows separates the two branches honestly.

### 4.1 If the screen SURVIVES

If every G0-G7 gate PASSes and at least one candidate variant PASSes G4 on every family, Wave 1a has *screened* the concern-update rule. The correct summary is:

> Under an adversarially misspecified prior on fixed withheld geometry, the online concern-update rule recovered priorities well enough to clear a preregistered, per-family, paired-seed lower-bound threshold on all three procedural families, without being reproduced by shuffled labels, a wrong-agent profile, or the best info-matched generic signal. The concern-update rule survives the E2a screen and is a green light to open E2b.

That is *not* an L2 claim. It is a screen result. Specifically:

- **What it establishes.** That the composition `LoggedProbePolicy(epsilon=0.05)` + `update_concern(estimator=v)` + poisoning guard is not fatally undermined by the ex-ante hard case Wave 0 was constructed to pose. That the update rule's edge over the frozen-wrong baseline is not explained by shuffled anchors, a different agent's profile, or a generic value / priority / recency signal at matched information budget. That the paired-seed variance can support the observed effect at 2σ.
- **What it does not establish.** That the geometry is right — Wave 1a uses withheld geometry, not learned geometry, so any claim about dual-source retrieval is *forbidden* at this stage. That the update rule works when geometry itself is being learned — Wave 1b is the crossed geometry × concern design. That the rule generalizes off the three procedural families. That there is a real-agent bottleneck for this mechanism to solve — the premise audit remains future work.

A screen PASS is, precisely, permission to run Wave 1b. Every downstream claim ladder step is gated on Wave 1b's rows against Wave 1b's own preregistration. Wave 1a's receipt is inherited by Wave 1b for the concern-update slot in the crossed matrix and for nothing else.

### 4.2 If the screen KILLS

If any G0-G7 gate FAILs — coverage collapse on any `(family, condition)` cell, propensity pathology (ESS floor, non-trusted source), specificity being reproduced by shuffled or wrong-agent labels, per-family reversal on any of the three families, integrity leak on any policy-visible field — Wave 1a KILLs the concern-update rule *as written*. The correct summary is:

> Under an adversarially misspecified prior on fixed withheld geometry, the online concern-update rule as composed in Wave 0 failed the preregistered E2a screen on `[family_or_gate]`. Per the honor-the-preregistration rule, only the knobs the preregistration §7 explicitly names as replayable may be rerun after a KILL, and only within their ex-ante ranges. Wave 1b's L1 dual-source-retrieval rows remain open — L1 and L2 are separable per the roadmap's noncompensatory rule — but any Wave 1b row that uses the KILLed rule as its concern condition must not be described as evidence for L2.

The KILL is not a bug report. It is the paper. Two failure modes are especially important to write down honestly rather than to work around:

- **Coverage collapse.** If the propensity-weighted coverage of a true commitment region falls below `0.01` on more than 5% of a cell's rows, the update rule is being scored on receipts that cannot mechanically support the update. This is not evidence that the rule is wrong; it is evidence that the exploration constant is insufficient. The preregistration permits rerunning within `epsilon ∈ [0.05, 0.10]` on the reserved seed range `200900..201999` capped at 30% of the affected cell. Beyond that band is a redesign, not a replay.
- **Specificity failure.** If either the shuffled (C4) or wrong-agent (C5) condition mean is within `sigma_hat_multiplicative_wave0` of the online-learned mean on any family, the observed edge cannot be attributed to *this specific* update rule. That is a KILL. It is *not* a threshold-swap opportunity. The gate is non-compensatory, and per the honor-the-preregistration rule, only the two named knobs are replayable — and only if the specificity failure is downstream of a §5.1 coverage failure that they can remediate.

A KILL that is not remediable within the replayable band is an honest KILL. The paper is written. Wave 1b's L1 rows still run.

### 4.3 Split verdicts across variants

A subtle but authorized outcome is a split verdict where exactly one of the two candidate variants passes and the other does not. The preregistration §4 notes this case explicitly: the screen decision is PASS if the passing variant clears all gates *and* the failing variant does not fail on adversarial specificity in a way that contaminates the passing variant's receipt. If both variants fail on any family, the rule KILLs. If exactly one variant passes, the pass is reported with its estimator tag and the other is reported as diagnostic. This asymmetry preserves the honest interpretation that IPS and DR are two off-policy views of the *same* update rule, not two independent rules; a rule that survives under one honest estimator is a rule that survives.

### 4.4 What Wave 1a does not claim under either verdict

Wave 1a does not license any claim about learned memory geometry, dual-source retrieval, L2 concern recovery from experience, semantic meaning, selfhood, or real-world usefulness. The concern-update rule may be a good learner of priorities on fixed withheld geometry and still be useless on learned geometry (that is Wave 1b's question). The rule may KILL on the screen and its underlying decomposition may still be right; Wave 1b's L1 rows would still adjudicate the dual-source claim independently. Wave 1a's interpretive scope is exactly the sentence at the top of §4.1 or §4.2, whichever the receipt supports. Nothing further.

---

## 5. Limitations

Wave 1a is a screen. Its honest limitations are the boundary conditions the promotion contract was built to protect.

**Geometry is fixed.** The withheld weighted graph is a pure function of `(seed, size, family)`. It is not learned. Wave 1a's screen result therefore says nothing about how the update rule composes with a geometry that is itself being learned or with a geometry that is randomly frequency-matched. Both compositions are Wave 1b (COGR-E2b) objects. The roadmap [2, § "Wave 1 — staged mechanism identification"] pins the crossed design as: geometry ∈ {learned, frequency-matched, oracle} × concern ∈ {frozen-wrong, online-learned, oracle}. Wave 1a occupies exactly one cell of that matrix.

**L1 is gated by Wave 1b, not Wave 1a.** The L1 dual-source-retrieval claim asks whether joint context × concern retrieval outperforms context-only and concern-only retrieval at matched information budget on non-ceiling geometry. Wave 1a does not run that contrast. Even a full Wave 1a PASS is not evidence for L1. Even a full Wave 1a KILL does not block Wave 1b's L1 rows.

**L2 requires the crossed design.** The L2 history-derived concern-recovery claim asks whether the online-learned concern condition beats the frozen-wrong condition under the L1-supporting geometry. Wave 1a passes on that claim under exactly one geometry (fixed withheld); the L2 claim requires that pass to hold under Wave 1b's L1-supporting geometry as well. Wave 1a is a necessary screen, not a sufficient one.

**Synthetic only.** The three families are procedural generators built for this program. No family is a governed real-world trace. The premise audit — whether real, governed long-horizon agent traces show off-context constraint failures at a rate that would justify broad usefulness claims — is documented as future work in `PROVENANCE.md` §9 and receives an explicitly non-evidential stub receipt. No governed data is ingested by Wave 1a code. Every safety and data-governance entry gate listed in the roadmap [2, § "Safety and data-governance entry gates"] remains outstanding.

**Confirmatory templates, one seed range.** The confirmatory seed range `200000..201999` is disjoint from the calibration range `100000..100999`; the Wave 0 template-split guard raises `LeakageError` on any calibration seed touched by a confirmatory code path. Wave 1a does not sample from other seed ranges; the reserved replay band `200900..201999` is only accessible under the two replayable knobs enumerated in preregistration §7.

**Rule is a composition, not a single algorithm.** The screen target is the composition `LoggedProbePolicy(epsilon=0.05)` + `update_concern(estimator ∈ {ips, dr})` + poisoning guard. A KILL falsifies the composition as it stands; it does not adjudicate whether an alternative composition (a different exploration policy, a different off-policy estimator, a different poisoning-guard shape) would survive. Any such alternative is a new preregistration.

**Poisoning stress not executed.** Wave 1a registers the Wave 0 single-source influence bound (`DEFAULT_MAX_SOURCE_INFLUENCE = 1.0`, `DEFAULT_ETA = 0.10`) but does not run untrusted-source stress; that is Wave 1b or Wave 4. Any receipt with a non-`"trusted"` `source_id` in the confirmatory sweep is a fatal integrity failure.

**No deployment claim.** As with Wave 0, Wave 1a does not license any deployment claim. Clinical, legal, financial, and other high-stakes deployment requires domain-specific validation and human governance the program has not begun.

---

## 6. Next: COGR-E2b

Two claim-specific contrasts open once Wave 1a signs, regardless of whether the screen PASSes or KILLs.

**COGR-E2b — learned-geometry confirmation.** The crossed design is:

| Geometry | Concern state | Identified contrast |
|---|---|---|
| Frequency-matched random, learned, oracle | Frozen non-ceiling concern | L1 dual-source retrieval |
| Fixed/withheld, learned, oracle | Frozen-wrong, online-learned, oracle | Concern recovery and geometry × concern interaction (L2) |

Two gates ride on this design. **L1** uses the frozen non-ceiling concern rows against Wave 0's `delta_thresh_L1` per family; it is *independent* of Wave 1a's outcome. If Wave 1a PASSes, L2 rows can be scored against the Wave 1a concern-update receipt. If Wave 1a KILLs, L2 rows are withheld — the rule is not honest evidence — but L1 rows still run, because the roadmap's noncompensatory rule separates them explicitly [2, § "Wave 1 — staged mechanism identification"].

Wave 1b is a separate preregistration. It will freeze its own thresholds against Wave 0's calibration receipt and its own additional Wave 1a inheritance clauses; its own crossed-geometry conditions require their own coverage audits, specificity contrasts, and per-family thresholds. The interfaces Wave 1a exposes to Wave 1b are enumerated in the `README.md` of `wave1a/` (public interfaces manifest); Wave 1b consumes them read-only.

Beyond Wave 1b, the roadmap [2] specifies a narrow live-agent beachhead as a continuation gate (not L4 promotion), substrate transfer (Wave 3), and a final round of safety, scaling, and independent replication (Wave 4). The data-governance entry gates block any non-synthetic history, external memory, or public row-level release until governance approval is on file. Wave 1a does not touch any of those; its only real-world contact is the stub receipt in `PROVENANCE.md` §9 that records the premise audit as outstanding.

---

## 7. References

[1] Jawaun Brown. *Concern-Gated Retrieval Wave 0: Preregistered Calibration and Wrong-Prior Scaffolding for Learned-Geometry Confirmation.* Wave 0 technical report. `papers/concern_gated_retrieval_wave0/paper.md` in this repository (`105a6b0`, 2026-07-23).

[2] Jawaun Brown. *Concern-Gated Retrieval: Theory, Evidence, and Research Program.* Canonical roadmap. `docs/concern_gated_retrieval_research_program.md` in this repository (2026-07-23). Referenced sections: "Executive thesis", "The intuition: two flashlights over memory", "Claim ladder and promotion semantics", "Immediate experiment program: COGR-E2", "Required anti-shortcut design", "Fatal gates by claim", "Wave 1 — staged mechanism identification", "Safety and data-governance entry gates", "Applicability contract".

[3] Zhang, S. and Levin, M. *Intelligence from Learnable Novelty.* arXiv preprint arXiv:2607.18433v1, 2026. Source of the frozen-reservoir stable-ridge epiplexity estimator that the L0 pilot composed with concern-gated retrieval as a reproducible utilization filter. In this program epiplexity is a secondary diagnostic; Wave 1a does not use it as a screen criterion.

**Companion artifacts.**

- Wave 1a preregistration: `experiments/concern_gated_retrieval_e2/wave1a/PREREGISTRATION.md`
- Wave 1a promotion contract: `experiments/concern_gated_retrieval_e2/wave1a/PROMOTION_CONTRACT.md`
- Wave 1a provenance skeleton: `experiments/concern_gated_retrieval_e2/wave1a/PROVENANCE.md`
- Wave 1a screen decision receipt (placeholder at time of writing): `experiments/concern_gated_retrieval_e2/wave1a/results/verdict.json`
- Wave 0 technical report (predecessor, frozen, imported): `papers/concern_gated_retrieval_wave0/paper.md`
- Wave 0 promotion contract: `experiments/concern_gated_retrieval_e2/wave0/PROMOTION_CONTRACT.md`
- L0 pilot (frozen; imported, never edited): `experiments/concern_gated_retrieval/`

---

*This report is a technical artifact of the Concern-Gated Retrieval E2 Wave 1a build. It preserves the wave-boundary language of the roadmap and the promotion contract. Wave 1a is a **screen**: it can KILL the concern-update rule as written; it cannot establish learned memory geometry, the L1 dual-source-retrieval mechanism claim, the L2 history-derived-concern-recovery claim, semantic meaning, or selfhood. Any restatement of this paper that describes Wave 1a as an L2 claim is inconsistent with the promotion contract and is not authorized by this report.*
