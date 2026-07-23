# Concern-Gated Retrieval Wave 0 — Preregistration

**Package:** `experiments/concern_gated_retrieval_e2/wave0/`
**Wave:** 0 (premise, calibration, and freeze)
**Predecessor:** `experiments/concern_gated_retrieval/` (frozen L0 pilot; do not edit)
**Successor:** `experiments/concern_gated_retrieval_e2/wave1/` (COGR-E2a then E2b)
**Human director:** Jawaun Brown
**Draft date:** 2026-07-23
**Signature status:** unsigned. This document is only preregistered after the
calibration Modal run fills the TBD variance rows in §8 and the calibration
manifest hash is written into §11. The signed digest is stored in
`PROVENANCE.md`.

## 1. Abstract

Wave 0 is a **calibration-only** and **premise-scaffolding** step for the
concern-gated retrieval E2 program. Its scientific purpose is to make the E2a
concern-recovery screen and the E2b learned-geometry confirmation *rejectable*:
to build the procedural machinery, freeze effect thresholds against a variance
estimate, initialize concern with an adversarially wrong prior, and record the
promotion contract that later waves must clear or fail. Wave 0 evaluates
three procedurally distinct calibration families — **delayed commitments**,
**maintenance and fault response**, and **resource-constrained planning** —
each instantiating the same abstract retrieval problem through different
surface structure. Concern is deliberately misspecified: the prior
overweights a plausible alarm region and underweights at least one true
commitment region, so that no reasonable two-sided method starts at ceiling
on any family. All confirmatory templates remain inaccessible during
calibration.

Wave 0 does **not** test learned memory geometry, does **not** claim recovery
of concern from experience, does **not** demonstrate semantic meaning, and
does **not** support any interpretation of selfhood. Wave 0 is calibration
and family scaffolding plus wrong-prior initialization. That is the entire
promotable claim of this wave.

Wave 0 evaluation is synthetic-only. The **premise audit** — whether real,
governed long-horizon traces show off-context constraint failures at a rate
that would justify broad usefulness claims — is documented in this
preregistration as future work and receives a stub receipt in
[`PROVENANCE.md`](PROVENANCE.md). Non-synthetic history is barred until the
governance entry gates listed in
[`docs/concern_gated_retrieval_research_program.md`](../../../docs/concern_gated_retrieval_research_program.md)
§ "Safety and data-governance entry gates" pass.

## 2. Target object and decision

- **Target object.** The **calibration variance estimate**, headroom check,
  and frozen threshold row that Wave 1 confirmatory rows will be scored
  against.
- **Not the target object.** A retrieval winner, a mechanism claim, or a
  promotion decision. Wave 0 is a *freeze* step; no confirmatory row is
  generated or inspected in this wave.
- **Decision at end of Wave 0.**
  - *Freeze.* If every calibration integrity check in §9 passes and the
    calibration receipt shows non-ceiling headroom for each of the three
    families, sign the preregistration by writing the calibration manifest
    hash into §11 and into [`PROVENANCE.md`](PROVENANCE.md), and open Wave 1.
  - *Redesign.* If any family reaches ceiling on any method, or the wrong
    prior is not adversarial in the sense of §5, or the anti-leakage guard
    fires, Wave 0 is redesigned; the calibration receipt is retained as a
    negative record but no threshold is frozen.
- **No confirmatory rows.** Confirmatory templates (seed range 200000–201999,
  §10) are not touched during Wave 0. A confirmatory row in a calibration
  code path is a fatal integrity failure (§9).

## 3. Representation and data clock

- **Substrate.** A finite, undirected weighted graph over typed nodes,
  identical in numerical semantics to the pilot's
  `experiments.concern_gated_retrieval.graph.WeightedGraph`. Wave 0 imports
  that class and its `personalized_pagerank` primitive; the pilot module is
  not edited.
- **Episode.** One calibration episode is a tuple
  `(family, template_id, seed, history, active_context, concern_prior,
  sealed_env)` where:
  - `family ∈ {delayed_commitments, maintenance_fault, resource_constrained}`
    (§6);
  - `template_id` names the calibration template and is disjoint from any
    confirmatory template id (§10);
  - `history` is a list of observable events produced by the family generator
    **before** any retrieval or ranking call fires;
  - `active_context` is the small set of currently active items with which
    the retrieval decision must work;
  - `concern_prior` is the wrong prior specified in §5;
  - `sealed_env` is the sealed environment interface described in §4.
- **Data clock.** The generator produces the entire `history` and
  `active_context` before *any* ranking or retrieval function is called. No
  Wave 0 retrieval or update code may inspect events with a timestamp
  strictly greater than the retrieval decision's timestamp. This is a
  procedural invariant, not a soft guideline; it is enforced by the
  anti-leakage guard in §4.
- **Units.** Graph weights, restart mass, and concern weights are
  dimensionless. Sealed outcome is a scalar reward with a family-specific
  bounded domain declared in §6. Epiplexity, if used at all in Wave 0, is
  a diagnostic and expressed in bits.

## 4. Anti-leakage boundaries

Every Wave 0 dataclass, retrieval function, ranking function, and concern
update function is *policy-visible*. Every field listed below is
*evaluator-only* and must not be reachable from any policy-visible code path.

### 4.1 Evaluator-only fields (enumerated)

| Field | Where it lives | Why it is evaluator-only |
|---|---|---|
| `role_label` | template row | The load-bearing / distractor / alarm / trap identity of a node — the answer key. |
| `answer_key` | template row | The identifier(s) of the correct off-context retrieval target(s). |
| `future_utility` | sealed env | The bounded reward realized after a decision is submitted. |
| `oracle_concern` | template row | The oracle concern profile used only for the diagnostic ceiling arm. |
| `wrong_agent_id` | template row | Cross-agent concern labels for the wrong-agent baseline. |
| `template_family_split` | template row | `calibration` vs `confirmatory` — must not steer any calibration decision. |
| `paraphrase_family` | template row | Paraphrase-family holdout id (Wave 1 uses this; Wave 0 records it and refuses to condition on it). |
| `generator_seed_kind` | template row | Distinguishes calibration seed range 100000–100999 from confirmatory 200000–201999. |
| `epiplexity_future_target` | sealed env | Reachable-future target used by any sensitivity-only epiplexity diagnostic; scored only after the decision. |
| `sealed_outcome_receipt` | sealed env | The post-decision receipt produced by the environment; readable only by the evaluator. |

### 4.2 Sealed environment interface

The sealed environment exposes exactly one method to policy code:

```
SealedEnv.observe_outcome(decision) -> RealizedOutcome
```

`decision` is the retrieval/action decision submitted by the policy.
`RealizedOutcome` is a frozen dataclass containing only a scalar reward and a
policy-visible outcome id. All evaluator-only fields (§4.1) live on the
environment's private state and are not returned. `SealedEnv` is constructed
by the evaluator; the policy receives a wrapper that raises on any attribute
access outside the whitelisted method.

### 4.3 Runtime guard

A runtime guard in `wave0/` (to be implemented as
`wave0/anti_leakage.py` in the subsequent Wave 0 build task) enforces:

1. **Family-split isolation.** Every dataclass carrying a template records
   `template_family_split`. The guard's `assert_calibration_only(row)`
   raises `LeakageError` if a row with `template_family_split ==
   "confirmatory"` is passed to any calibration entry point.
2. **Evaluator-only field access.** The guard exposes a `PolicyView`
   wrapper. Attribute access to any name in §4.1 raises `LeakageError`.
3. **Time-monotone history.** Retrieval and update code receive an
   immutable `HistoryWindow` sliced at the decision timestamp; access to
   later events raises `LeakageError`.
4. **Statistical leakage audit.** Even permitted graph features must clear
   a label-permutation control before they are used as inputs; the audit
   receipt is stored with the calibration manifest.
5. **Byte-stable receipts.** The guard's error messages and the calibration
   summary do not include evaluator-only field values.

The guard's own tests are calibration-only fixtures. Wave 1 code paths reuse
the same guard with a confirmatory-mode flag; Wave 0 code paths cannot flip
that flag.

### 4.4 Poisoning guard (single-source influence bound)

The Wave 0 concern-update learner (`wave0/concern_update.py`) is exploratory
only — Wave 0 does **not** update the wrong prior at evaluation time — but
Wave 1 will exercise it under adversarial input, so its typed-provenance and
influence-bound contract is frozen here alongside the sealed-env and
family-split guards.

1. **Typed provenance.** Every `ProbeReceipt` carries a `source_id`. The
   default `"trusted"` id names calibration probes; Wave 1 will require
   callers to declare a distinct, non-empty id per untrusted source
   (roadmap §"Required anti-shortcut design" item 8).
2. **Aggregate magnitude bound.** For each unique `source_id`, the
   concern-update learner clamps `Σ_a |v_hat_a from that source|` to
   `max_source_influence` (Wave 0 default `1.0`) before the
   mirror-descent step. The bound is applied per update, not per receipt,
   so a source with many receipts cannot circumvent it by spreading
   contribution across probes.
3. **Bounded post-guard weight movement.** After the guard runs, every
   anchor's weight changes by at most a factor of
   `exp(eta * max_source_influence)` per source per update — a
   worst-case that Wave 1 targeted-poisoning stress will exercise. Wave 0
   registers this tolerance shape only.
4. **No poisoning-induced anchor synthesis.** Anchors probed by a receipt
   but absent from the caller-supplied prior are dropped, not synthesized
   into the anchor set. Wave 1 may relax this once trusted vs. untrusted
   source semantics are frozen.

## 5. Wrong-prior specification

Wave 0's concern prior is **adversarially misspecified**. Concretely, the
Wave 0 prior:

1. **Inflates a plausible alarm region.** For each family, the generator
   emits a "loud" region — a chronic alarm-like anchor whose surface
   features (recency, frequency, semantic similarity to context) make it
   look like a reasonable priority. The Wave 0 prior places a weight of
   `w_alarm_init = 1.0` on that region.
2. **Suppresses at least one true commitment region.** For each family, at
   least one true commitment region — the region a correctly aligned prior
   would upweight — is initialized to `w_commit_init = 0.05` (below the
   uniform baseline).
3. **Leaves at least one other true commitment region at uniform.** So the
   wrong prior is not a total inversion; a well-designed method has some
   surface to grip on while still being adversarially penalized on the
   suppressed region.

The specific per-family alarm and suppressed-commitment identifiers are
listed in §6 and are held only by the evaluator; the policy sees the numeric
prior, not the labels.

- **Delayed commitments.** Alarm region = "current-day trending news".
  Suppressed commitment = "date-anchored personal obligation".
- **Maintenance and fault response.** Alarm region = "high-severity
  boilerplate warning". Suppressed commitment = "old observation whose
  relevance is only exposed by a later symptom".
- **Resource-constrained planning.** Alarm region = "recent large-magnitude
  transaction". Suppressed commitment = "prior obligation that constrains
  which otherwise-valid action is best".

Wave 0 does not update this prior. Concern-update rules are a Wave 1 object.
This is critical: Wave 0 cannot claim, or be described as claiming, concern
recovery.

## 6. Three procedural families

Each family instantiates the same abstract retrieval problem — "identify the
off-context fact whose loading would improve the sealed outcome" — with a
different surface structure. Templates are held out at the *family* and
*paraphrase-family* levels, not merely at the row level. Every family
generates its `history` and `active_context` **before** any ranking call.

### 6.1 `delayed_commitments`

- **Abstract retrieval problem.** A load-bearing fact was mentioned early
  in `history` and has been off-context for many events; the decision is
  which off-context candidate to retrieve at the moment it becomes
  outcome-relevant.
- **Surface features.** Date arithmetic, promise wording, calendar
  distractors, and a chronic news-style alarm.
- **Holdout scheme.** Wave 0 uses calibration templates
  `DC-C-01 … DC-C-16`. Confirmatory templates `DC-X-01 … DC-X-32` are
  reserved for Wave 1 and inaccessible now. Paraphrase-family split: at
  least one paraphrase family per template is held out from calibration.

### 6.2 `maintenance_fault`

- **Abstract retrieval problem.** An early observation only becomes
  load-bearing when a later symptom appears; the decision is whether to
  retrieve that old observation instead of a louder recent warning.
- **Surface features.** Log-style event streams, boilerplate warnings, and
  a chronic "critical alert" alarm.
- **Holdout scheme.** Calibration templates `MF-C-01 … MF-C-16`;
  confirmatory `MF-X-01 … MF-X-32` reserved. Paraphrase-family split as
  above.

### 6.3 `resource_constrained`

- **Abstract retrieval problem.** A hidden prior obligation changes which
  otherwise-valid action is best; the decision is whether to retrieve the
  constraint fact.
- **Surface features.** Ledger-style transactions, unit conversions, and
  a chronic "large recent transaction" alarm.
- **Holdout scheme.** Calibration templates `RC-C-01 … RC-C-16`;
  confirmatory `RC-X-01 … RC-X-32` reserved. Paraphrase-family split as
  above.

**Bounded reward domain.** Sealed outcomes are scalar rewards in
`[-1.0, +1.0]` for every family. The generator ensures the load-bearing
target's expected reward differential over the best distractor is at most
`0.6`, so that no reasonable two-sided method starts at ceiling.

## 7. Baseline slate

Every Wave 0 calibration row scores every baseline in the following slate.
Baselines are matched at the retrieval budget and the compute budget as
defined by the calibration manifest.

| # | Baseline | Purpose |
|---|---|---|
| 1 | `no_retrieval` | Floor. |
| 2 | `random` | Chance floor at matched budget. |
| 3 | `freq_only` | Retrieval by unconditional node frequency. |
| 4 | `context_only` | Personalized PageRank from `active_context` only. |
| 5 | `care_only` | Personalized PageRank from `concern_prior` only (wrong). |
| 6 | `additive` | `r_ctx + r_care` fusion at matched budget. |
| 7 | `multiplicative` | Rarity-corrected Hadamard product (the pilot rule). |
| 8 | `embedding_similarity` | Modern embedding-similarity retrieval. |
| 9 | `learned_one_stage_ranker` | A single learned ranker at matched capacity and compute. |
| 10 | `info_matched_value` | Information-matched generic value / advantage second signal. |
| 11 | `info_matched_priority` | Information-matched task-priority second signal. |
| 12 | `info_matched_recency` | Information-matched recency second signal. |
| 13 | `wrong_agent` | Concern profile drawn from a *different* agent's history — must not help. |
| 14 | `oracle_ceiling` | Oracle concern + oracle geometry; diagnostic ceiling only, never a promotable claim. |

The learned one-stage ranker (#9) and the info-matched second-signal
baselines (#10–12) are the specific matched-budget alternatives Wave 1 must
beat for a valid L1 claim; Wave 0 uses them to size effects.

## 8. Frozen effect thresholds

Thresholds are reported as **calibration variance estimates**. Placeholders
are `TBD` in this draft and are frozen only after the Modal calibration run
populates them in [`PROVENANCE.md`](PROVENANCE.md) and this section is
updated to match.

### 8.1 Threshold shape (frozen at signature time)

For each of the three families:

- `mu_hat_multiplicative` — calibration mean of the multiplicative
  baseline's sealed outcome on wrong-prior rows.
- `sigma_hat_multiplicative` — calibration standard deviation of the
  same, across calibration seeds 100000–100999.
- `mu_hat_best_matched` — calibration mean of the best matched-budget
  baseline in {`additive`, `learned_one_stage_ranker`, `info_matched_value`,
  `info_matched_priority`, `info_matched_recency`, `embedding_similarity`}.
- `sigma_hat_best_matched` — corresponding calibration standard deviation.
- `headroom_to_ceiling` — `mu_hat_oracle_ceiling − mu_hat_multiplicative`.
  Must be strictly positive on every family for Wave 0 to freeze.
- `delta_thresh_L1` — the Wave 1 L1 gate threshold: `multiplicative` sealed
  outcome minus `best matched-budget` sealed outcome. Frozen at
  `max(2 * sigma_hat_best_matched, 0.10 * headroom_to_ceiling)`.

### 8.2 Placeholders (populated by the Modal calibration step)

| Family | `mu_hat_multiplicative` | `sigma_hat_multiplicative` | `mu_hat_best_matched` | `sigma_hat_best_matched` | `headroom_to_ceiling` | `delta_thresh_L1` |
|---|---|---|---|---|---|---|
| `delayed_commitments` | TBD | TBD | TBD | TBD | TBD | TBD |
| `maintenance_fault` | TBD | TBD | TBD | TBD | TBD | TBD |
| `resource_constrained` | TBD | TBD | TBD | TBD | TBD | TBD |

The Modal step's provenance receipt (§11 hash) is the sole channel through
which `TBD` becomes a numeric value in this section. No manual edit is
permitted.

## 9. Fatal gates (copied from the roadmap)

Copied from `docs/concern_gated_retrieval_research_program.md` § "Fatal gates
by claim" and § "Required anti-shortcut design". These are noncompensatory;
failure of any one is a fatal Wave 0 integrity failure and forbids freezing
thresholds.

### 9.1 Integrity

- No evaluator-only field (§4.1) is reachable from graph learning,
  retrieval, ranking, concern update, or verification code — including
  through statistically leaky permitted features.
- The runtime guard (§4.3) raises on every attempted violation; regression
  tests exercise each violation class.
- A confirmatory-template row in a calibration code path is a fatal
  integrity failure.

### 9.2 Non-ceiling

- Every family shows strictly positive `headroom_to_ceiling` in §8.
- No baseline in §7 achieves sealed-outcome mean within
  `0.05 * bounded_reward_range` of the oracle ceiling on any family. If any
  method saturates, the family generator's difficulty is increased and the
  calibration is re-run before any threshold is frozen.

### 9.3 Robustness

- The primary Wave 1 effect must survive **every** preregistered family
  (§6) independently. Aggregate success cannot hide a family-level
  reversal; Wave 0 records the per-family variance so the aggregate rule
  is enforceable.
- Calibration includes graph noise, paraphrase, reordered histories,
  unseen concern combinations, and larger memory sizes at the levels the
  Wave 1 confirmatory rows will use.

### 9.4 Adversarial

- The wrong prior (§5) is verified to inflate the alarm and suppress the
  designated commitment on every calibration row.
- Targeted history or feedback poisoning cannot produce an undetected,
  irreversible attention-hijacking state above the tolerance recorded in
  the calibration receipt. Wave 0 registers the tolerance shape; Wave 1
  executes the injection stress.

## 10. Sample size and seed plan

- **Calibration seeds.** `100000, 100001, …, 100999` (1000 seeds).
  Distributed across the three families as approximately 333 seeds per
  family, with the exact per-family split recorded in the calibration
  manifest (§11).
- **Confirmatory seeds (reserved).** `200000, 200001, …, 201999`
  (2000 seeds). Inaccessible during Wave 0. The confirmatory seed range is
  declared here so Wave 0 can register that it does not touch it, not so
  Wave 0 can execute against it.
- **Independence.** Calibration and confirmatory seed ranges are disjoint
  by construction. The generator refuses to accept a seed outside its
  declared range for its declared mode.
- **Per-cell sample size.** Each `(family, method)` calibration cell
  contains at least 300 seeded episodes drawn from the calibration seed
  range. Variance estimates in §8 are computed against this sample size and
  are reported alongside their bootstrap intervals in the calibration
  receipt.
- **Modal execution.** Wave 0 Modal fan-out targets L4 GPUs only, per the
  wave-wide operating rule that Modal spend stays at or below 35% of an
  equivalent H100 rate. Deploy occurs before spawn; the deployed image
  hash is recorded in [`PROVENANCE.md`](PROVENANCE.md).

## 11. Analysis-code freeze plan

Wave 0 is not signed until the analysis and generator code that produced
the calibration receipt is content-hashed and pinned.

- **Scope of the hash.** SHA-256 over the concatenated bytes of every
  tracked file under `experiments/concern_gated_retrieval_e2/wave0/**`,
  computed in sorted path order after the calibration Modal run completes
  and the placeholders in §8 are filled.
- **Where the hash lives.** In this section, replacing
  `WAVE0_ANALYSIS_HASH = TBD`, and mirrored into
  [`PROVENANCE.md`](PROVENANCE.md) alongside the Modal deploy hash and
  the calibration seed range receipt.
- **What the hash freezes.** The three family generators, the sealed
  environment interface, the anti-leakage guard (§4.3), the calibration
  scorer, the variance estimator, the threshold-freezing rule (§8.1), and
  this preregistration. Wave 1 confirmatory rows are scored against the
  frozen threshold row of §8 using code identified by this hash. Any
  post-freeze change to Wave 0 code invalidates the freeze and requires a
  redesign, not a silent update.

```
WAVE0_ANALYSIS_HASH = TBD
```

- **Honor-the-freeze rule.** No post-hoc corpus swap, threshold swap,
  seed-range swap, or family swap is permitted once the hash is written.
  Only knobs this preregistration explicitly names as `TBD → populated`
  may be filled in by the Modal receipt.
