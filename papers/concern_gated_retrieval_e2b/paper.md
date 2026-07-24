# Learned-Geometry Confirmation of Concern-Gated Retrieval: the COGR-E2b 3x3 Crossed Design

**Program:** Concern-Gated Retrieval (COGR) — Wave 1b (COGR-E2b)
**Package:** `experiments/concern_gated_retrieval_e2/wave1b/`
**Predecessors (imported, frozen, never edited):**
`experiments/concern_gated_retrieval_e2/wave0/` (Wave 0 hash
`9683c5a1f4010361d6e120bcabd2743fb33e8cc9c7c79d5bd9b1d9f9f8889c23`),
`experiments/concern_gated_retrieval_e2/wave1a/` (Wave 1a hash
`c23b31d977d7c169d57ca12cdfdbc8ad3a59188542efbdf802e341b1c8937209`,
screen decision `KILL`).
**Date:** 2026-07-24
**Human director:** Jawaun Brown
**Status:** technical report accompanying the Wave 1b preregistration
([`PREREGISTRATION.md`](../../experiments/concern_gated_retrieval_e2/wave1b/PREREGISTRATION.md)),
the two non-compensatory promotion contracts
([`PROMOTION_CONTRACT_L1.md`](../../experiments/concern_gated_retrieval_e2/wave1b/PROMOTION_CONTRACT_L1.md),
[`PROMOTION_CONTRACT_L2.md`](../../experiments/concern_gated_retrieval_e2/wave1b/PROMOTION_CONTRACT_L2.md)),
and the crossed-factorial confirmatory receipt. The receipt is the load-bearing
step; every numerical row in §5 that depends on the Modal L4 confirmatory run
reports the completed confirmatory run (L1 KILL, L2 WITHHELD) and
[`PROVENANCE.md`](../../experiments/concern_gated_retrieval_e2/wave1b/PROVENANCE.md)
is populated. The paper is written **once** with two verdicts that are
issued **separately**; the writing of the receipt — not the writing of the
report — turns the placeholders into authoritative values or into an honest
KILL.

**Wave-boundary reminder.** Wave 1b **can KILL** the L1 candidate
mechanism (representation contribution) and it **can KILL** the L2 candidate
rule (concern recovery + specificity) independently. Wave 1b **cannot**
establish substrate transfer (L3), external-agent applicability (L4), a
cognitive/self-model interpretation (L5), or semantic meaning. Those remain
Wave 2+ objects. Any restatement of this paper as an L3, L4, L5, or
selfhood claim is inconsistent with the two promotion contracts and is
not authorized by this report.

---

## Abstract

Wave 1b of the Concern-Gated Retrieval E2 program is the confirmatory
**crossed learned-geometry × concern** experiment for the two claims the
Wave 0 calibration + Wave 1a screen jointly made rejectable: **L1
representation contribution** (does the candidate mechanism —
rarity-corrected joint context × concern retrieval — beat every
matched-budget baseline on sealed task outcome when memory geometry is
being *learned* or *frequency-matched random*, and survive an
interventional edge-ablation causal test?) and **L2 concern recovery +
specificity** (does the online concern-update rule recover from an
adversarially wrong prior, beat every information-matched generic signal,
and survive a split-budget uncertainty-audit ablation, *without being
reproduced* by naïve exploration alone?). Wave 1b crosses
`Geometry ∈ {LEARNED, FREQ_MATCHED_RANDOM, ORACLE_WITHHELD}` with
`Concern ∈ {FROZEN_WRONG, ONLINE_LEARNED_IPS, ONLINE_LEARNED_DR, ORACLE}`
with `Family ∈ {delayed_commitments_v2, maintenance_fault_v2,
resource_constrained_v2}` for 27 non-oracle cells × 300 confirmatory seeds each
(paired within family-slice on the Wave 0 confirmatory seed range
`200000..201999`).

The L1 verdict is scored on the FROZEN_WRONG concern rows crossed with
non-ceiling geometry (`LEARNED`, `FREQ_MATCHED_RANDOM`). This isolates
the representation-contribution question from the concern-recovery
question. The L2 verdict is scored on the ONLINE_LEARNED concern rows
crossed with `LEARNED` geometry, gated by a *pre-run family-design
assertion* (§4.4) that refuses to score L2 if any generic-signal baseline
reproduces the oracle top-k — the exact failure mode that KILLed
Wave 1a. Both verdicts are non-compensatory over ten fatal gates
(G0-G9), including SET-level oracle-regret metrics that catch missed
combinatorial-utility structure (contradictory pairs, complementary
pairs, dangerous conjunctions), a **statistical** leakage audit
(label-permutation + randomized-generator controls) on the permitted
graph features, an interventional edge-ablation test, and an
adversarial single-source concern-poisoning stress inside the Wave 0
influence bound. Utility is task-based (`Δ_task`); epiplexity `S^φ` is a
dependent variable and optional bonus (`β = 0` in the L1 and L2 gates),
never the verifier.

The confirmatory Modal L4 run completed (27 cells × 300 seeds = 8 100
receipts; $10.80 on 64 L4 workers). **The verdict is L1 KILL, L2
WITHHELD.** On all three redesigned families the candidate mechanism's
learned-vs-random-geometry contrast is essentially zero (`mean_delta`
= −0.022 / −0.005 / −0.003), so a frequency-matched random graph
reproduces its performance and the learned geometry contributes nothing;
and the interventional edge-ablation moves the sealed outcome in the
predicted direction only 44–63% of the time (below the 0.70 causal
requirement). Crucially, the statistical leakage audits **pass** on all
three families (label-permutation p = 0.37–0.59, far above the 0.01
tolerance), so — unlike Wave 1a, where recency was a covert oracle —
these families carry no hidden shortcut. Non-ceiling headroom is healthy
(~0.52–0.57), so the KILL is not a ceiling artifact. This is a **clean
falsification** of the L1 dual-source-retrieval claim on honest learned
geometry: once the fixture no longer leaks the answer, rarity-corrected
joint context × concern retrieval does not beat matched-budget baselines.
L2 is withheld (not KILLed) per the noncompensatory contract, so the
concern-recovery question can be re-opened by a future wave that first
establishes a passing L1. The KILL is reported honestly — no post-hoc
threshold swaps, no corpus swaps, no unregistered replay knobs.

---

## 1. Background

### 1.1 The two-flashlight decomposition, restated one more time

A bounded agent knows more than it can hold in its active representation.
Its problem is therefore not only how to store knowledge but how to
decide which currently absent fact deserves scarce attention *now*.
Concern-gated retrieval decomposes off-context recall into two beams
that must intersect. One beam is **context** — what the currently active
representation demands. The other beam is **concern** — what the agent's
history says matters to it. A candidate becomes a retrieval nomination
only where the two beams overlap [1, § "The intuition: two flashlights
over memory"]. On the canonical birthday-style example the two beams are
"today is October 4" and "my partner's birthday matters to me on the
day-of-year." Neither beam is loud enough to fire alone: the context is
absorbed with unrelated work, the concern is a low-rate but load-bearing
preference. The overlap is a specifically off-context need. This is an
**AND**, not an OR: retrieve what is relevant now *and* important to the
agent, then test whether attending to it actually helps.

The decomposition raises three questions the L0 pilot could not
adjudicate and Wave 0 and Wave 1a were staged to make rejectable:

- Does the *joint* nomination outperform the *context-only* and
  *concern-only* baselines at matched information budget on a memory
  geometry that does not encode the answer? (L1.)
- Can the concern beam be *learned* — either partially from the agent's
  own history, or wholesale from experience under a wrong start —
  without leaking through evaluator-only fields? (L2.)
- Are the answers to (L1) and (L2) *separable*, so that a valid L1
  result cannot be relabelled as evidence for L2 and a KILL on L2
  cannot invalidate L1? (Roadmap [1, § "Wave 1 — staged mechanism
  identification"] pins this as a non-compensatory boundary; Wave 1b
  implements it as two contracts, one per claim.)

Wave 1b is the crossed learned-geometry × concern experiment that
adjudicates all three questions at once, with the safeguards Wave 1a's
KILL taught us to install.

### 1.2 What the L0 pilot established (and what it did not)

The frozen L0 pilot at `experiments/concern_gated_retrieval/` established
that the two-flashlight decomposition can be made precise, that its
numerical plumbing (weighted graph, personalized PageRank, epiplexity
filter, coincidence intersection) is implementable, and that on the
authored graph family the composition discriminates registered synthetic
roles under frozen seeds and regimes [3, Wave 0 report §1.3]. That is an
L0 executable-diagnostic result and nothing more. The pilot could not
adjudicate whether joint retrieval helps when geometry is learned or
withheld (its graph *encoded* the answer), whether concern can be
recovered from misspecification (all initial, learned, and oracle
concern conditions saturated at hit@1 = 1.000), whether multiplicative
intersection is necessary (the additive fusion tied the product in two
of three regimes), whether semantic meaning or selfhood is present (not
tested), or whether the mechanism has any real-agent bottleneck to solve
(not tested).

### 1.3 What Wave 0 froze

Wave 0 was a calibration-and-scaffolding step [3]. Its promotable
deliverables (all issued as *variance* estimates, not retrieval
winners) are the per-family threshold row Wave 1 confirmatory rows are
scored against:

```
delayed_commitments    mu_best = 0.5314   sigma_best = 0.0218   headroom = 0.4845   delta_thresh_L1 = 0.0484
maintenance_fault      mu_best = 0.5029   sigma_best = 0.0267   headroom = 0.4548   delta_thresh_L1 = 0.0534
resource_constrained   mu_best = 0.5750   sigma_best = 0.0250   headroom = 0.4291   delta_thresh_L1 = 0.0500
```

Wave 0 also froze: the sealed environment interface (`SealedEnvironment`
exposing only `observe` and `evaluate`, `evaluate` firing at most once
per episode, an `IntegrityAudit` AST walker that flags any policy that
dereferences `role`, `utility`, or `_answer_key`); the template-split
runtime tripwire (`TemplateBucket ∈ {CALIBRATION, CONFIRMATION}` with
default-deny and a `LeakageError` on any mixed access); the wrong-prior
specification (alarm at `w_alarm_init = 1.0`, at least one true
commitment suppressed to `w_commit_init = 0.05`, at least one uniform);
the `LoggedProbePolicy(epsilon=0.05)` propensity-logging scaffolding
under a `0.01` coverage floor; and the confirmatory seed range
`200000..201999` disjoint from the calibration range `100000..100999`.
The Wave 0 analysis hash
`9683c5a1f4010361d6e120bcabd2743fb33e8cc9c7c79d5bd9b1d9f9f8889c23`
binds every one of these to the exact bytes of the calibration code.

Wave 0 explicitly did **not** update the wrong prior at evaluation
time, did **not** learn the memory geometry, and did **not** perform the
premise audit against governed real-world traces [3, §6]. Those three
noncompensatory boundaries define the Wave 1 experiment surface.

### 1.4 What Wave 1a KILLed, and what Wave 1b inherits

Wave 1a (COGR-E2a) was a **screen** for the concern-update rule on
*fixed* withheld geometry [2]. It crossed five conditions
(`frozen_wrong` baseline, `online_learned_ips`, `online_learned_dr`,
`oracle_ceiling` diagnostic, `shuffled` control, `wrong_agent` control)
with the three Wave 0 families on the confirmatory seed range, wrapped
every receipt-producing condition in `LoggedProbePolicy(epsilon=0.05)`
so IPS/DR debiasing was well-defined, and ran a seven-gate
non-compensatory promotion contract (G0-G7). The aggregate screen
decision was **`KILL`**. Two failure modes emerged, both important to
carry into Wave 1b honestly:

1. **G1 coverage collapse** on `delayed_commitments`:
   propensity-weighted coverage of the true commitment region was
   `0.000` on both `online_learned_ips` and `online_learned_dr` — the
   `epsilon = 0.05` exploration budget could not reach the suppressed
   commitment region at all. Shuffled and wrong-agent controls also
   under-covered (`0.066` and `0.059` respectively), well above the
   `0.01` floor but showing the same qualitative pattern.

2. **G3 specificity failure** on all three families:
   `info_matched_recency` reproduced the oracle ceiling *byte-for-byte*
   (`0.5315 / 0.4772 / 0.6000`). Because Wave 0's family generators
   placed the load-bearing memory at a family-consistent temporal
   offset, a recency-only ranker was, by construction,
   information-*more*-than-matched to the concern rule — it was
   receiving free access to the answer via a permitted feature. The
   G3 gate correctly refused to promote any composition that could
   not distinguish itself from that baseline. This is a *family-design*
   confound in Wave 0's fixture; it is not a fatal flaw in the
   two-flashlight decomposition and it does not block a Wave 1b L1 row
   that runs on redesigned families and on non-ceiling geometry.

Per the roadmap [1, § "Wave 1 — staged mechanism identification"] and
the Wave 1a promotion contract, a Wave 1a KILL **withholds** L2 but
does not block Wave 1b's L1 rows. Wave 1b runs L1 unconditionally; L2
rows run *iff* Wave 1b's redesigned families pass the pre-run
recency-decoupling assertion (§4.4) and *iff* Wave 1b's L1 verdict
fires PASS.

### 1.5 Two shortcuts E2b breaks

Wave 1b breaks the two shortcuts Wave 0 and Wave 1a preserved:

**Shortcut 1: fixed geometry.** Wave 0 and Wave 1a ran on the fixed
withheld graph from `wave0.graph_learn.build_withheld_graph`. That
graph's role labels are *not encoded* in its adjacency structure — it
was withheld precisely so that the graph itself could not do the
pattern matching — but the graph is *unchanged across episodes*. A
mechanism that works on withheld geometry could still be trading on
a specific graph shape. Wave 1b crosses `LEARNED` (per-episode
audit-clean graph learning from policy-visible history),
`FREQ_MATCHED_RANDOM` (a degree-preserving frequency-matched null
over the same reference graph), and `ORACLE_WITHHELD` (the Wave 0
withheld graph, refused for promotion by
`promotion_admit_geometry`). L1 is scored on the FROZEN_WRONG concern
rows *only* on non-ceiling geometry (`LEARNED`, `FREQ_MATCHED_RANDOM`).

**Shortcut 2: additive utility.** Wave 0 and Wave 1a scored utility
per-candidate additively: `Δ(v) = J_g(v) − J_g(∅)`. That aggregation
made "useful bundles," "contradictory pairs," "complementary pairs,"
and "dangerous conjunctions" invisible — an allergy note that helps
alone but combines with a nut memory and a birthday-cake memory to
plan a *harmful* action would be scored as three positive singletons.
Wave 1b promotes utility to a **first-class SET-level function**
`Δ_task(S) = J_g(trajectory | S) − J_g(trajectory | ∅)` and evaluates
the exhaustive oracle over all singletons, all pairs, and
feasibility-gated triples per episode; §4.3 specifies the enumeration
and the four decisive metrics (`oracle_recall_at_k`,
`simple_regret_set`, `cumulative_regret`, `interaction_recovery`).
The L1 gate scores `Δ_task` (β = 0 in the utility function); epiplexity
`S^φ` is reported as a dependent variable diagnostic only.

---

## 2. Wave 0 summary (one page)

Wave 0 is a *calibration-only, scaffolding-only* step whose entire
promotable claim is a signed preregistration, a non-compensatory
seven-gate promotion contract (G0-G6), and a Modal L4 calibration
receipt binding every threshold Wave 1 must clear. Its target object is
the calibration variance estimate, not a retrieval winner [3, §2].

**Substrate.** A finite undirected weighted graph over typed nodes;
imported unchanged from the L0 pilot. Personalized PageRank primitives
are reused byte-for-byte so a Wave 1 tie between the candidate mechanism
and the best matched-budget baseline cannot be blamed on a divergent PPR
implementation.

**Three procedural families.** `delayed_commitments`,
`maintenance_fault`, `resource_constrained`. Each instantiates the same
abstract retrieval problem — "identify the off-context fact whose loading
would improve the sealed outcome" — through different surface structure.
Sealed reward is scalar in `[-1, +1]`; the load-bearing target's
expected reward differential over the best distractor is at most `0.6`
so no reasonable two-sided method starts at ceiling [3, §2.2, §6].

**Sealed environment.** Only `observe(episode) -> EpisodeContext` and
`evaluate(choice) -> SealedOutcome`. `evaluate` may fire at most once
per episode; a second call raises `SealedEvaluationError`.
`EpisodeContext` is a frozen dataclass; attribute access outside its
declared fields raises. Every evaluator-only field enumerated in Wave 0
preregistration §4.1 (`role`, `utility`, `_answer_key`,
`oracle_concern`, `wrong_agent_id`, `template_family_split`,
`paraphrase_family`, `generator_seed_kind`, `epiplexity_future_target`,
`sealed_outcome_receipt`) is unreachable from any policy-visible code
path.

**Anti-leakage.** Four layers: (1) the enumerated evaluator-only field
list; (2) the sealed environment interface; (3) the static
`IntegrityAudit` AST walker over every rank callable in
`wave0.baselines`; (4) the template-split runtime tripwire with
default-deny and the environment guard
`COGR_WAVE0_CONFIRMATORY_RUN=1` required to touch confirmatory rows.

**Wrong-prior specification.** Alarm region at `w_alarm_init = 1.0`; at
least one true commitment region suppressed to `w_commit_init = 0.05`;
at least one other true commitment left at uniform. Per-family
identifiers held only in the evaluator's private state.

**Frozen thresholds.** Populated from the Modal L4 calibration receipt
into Wave 0 PREREGISTRATION.md §8; hash-bound by
`WAVE0_ANALYSIS_HASH = 9683c5a1…`. The three per-family rows above
(§1.3) are the exact values Wave 1b L1 confirms against.

Wave 0 does not test learned memory geometry, does not update the wrong
prior, does not perform the premise audit, and does not license any L1,
L2, or higher claim. Wave 1b inherits every one of Wave 0's frozen
objects read-only and re-exports none of them.

---

## 3. Wave 1a summary (one page)

Wave 1a (COGR-E2a) is a *concern-recovery screen only* on fixed
withheld geometry [2]. It targets exactly the composition
`LoggedProbePolicy(epsilon=0.05) + update_concern(estimator ∈ {ips,
dr}) + poisoning guard` — three off-the-shelf Wave 0 primitives that
together specify the update rule Wave 1b's L2 gate needs.

**Design.** Five conditions × three families × up to 300 paired seeds
per cell = 6320 receipts.

| # | Condition | Concern state | Role |
|---|---|---|---|
| C1 | `frozen_wrong` | Wave 0 wrong prior held fixed | Baseline |
| C2a | `online_learned_ips` | Online-updated via IPS | Candidate |
| C2b | `online_learned_dr` | Online-updated via DR | Candidate (2nd view) |
| C3 | `oracle` | Oracle concern held fixed | Diagnostic ceiling (never promotable) |
| C4 | `shuffled` | Wrong prior with anchor labels permuted | Specificity control |
| C5 | `wrong_agent` | Concern profile from another agent | Specificity control |

Every receipt-producing condition wrapped its nomination policy in
`LoggedProbePolicy(epsilon=0.05)` so selection propensities were logged
and were the sole quantity IPS/DR divided by. A pre-analysis coverage
audit rejected any confirmatory row whose propensity-weighted coverage
of the true commitment region fell below `0.01`; per-family thresholds
were `0.04845 / 0.05340 / 0.05000` on the paired-seed lower bound.

**Seven fatal gates.** G0 anti-leakage; G1 coverage; G2 propensity
accounting; G3 specificity (must beat every info-matched generic signal
AND the shuffled and wrong-agent controls by preregistered margins);
G4 per-family effect; G5 seed independence; G6 code freeze; G7 Modal
budget.

**Verdict: KILL.** The full aggregate reasons are enumerated in the
Wave 1a screen receipt at
`experiments/concern_gated_retrieval_e2/wave1a/results/verdict.json`
under `aggregate_kill_reasons`. The two failure modes named in §1.4
above are the load-bearing ones:

- G1 coverage collapse on `delayed_commitments` (`coverage = 0.000` on
  both online arms — the suppressed commitment region was starved by
  the `epsilon = 0.05` exploration budget).
- G3 specificity failure on all three families
  (`info_matched_recency` reproduced the oracle ceiling; on
  `delayed_commitments` the margin was `−0.5562`, i.e. the online
  concern rule was *below* the recency baseline by more than half the
  reward range, because recency was catching the load-bearing memory
  every seed by construction of Wave 0's family fixtures).

`resource_constrained` produced a genuine `+0.226` effect for both
online variants against every non-recency comparator — the online
concern rule *does* recover useful priorities on that family — but the
specificity gate correctly refused to promote a composition that could
not distinguish itself from a recency baseline that had covert access
to the answer.

**What Wave 1a licensed for Wave 1b.** Per the roadmap's
noncompensatory rule and the Wave 1a promotion contract's demotion
clause: a Wave 1a KILL withholds L2 but does not block Wave 1b's L1
rows. Wave 1b's L2 rows are additionally blocked-by the family
redesign passing a pre-run recency-decoupling assertion (§4.4) — that
is the mechanism by which the Wave 1a specificity KILL cannot silently
recur under a family redesign that failed to actually fix the
recency-oracle collision.

---

## 4. Design

### 4.1 The 3 × 3 × 3 crossed factorial

Wave 1b crosses three axes:

* **Geometry axis** ∈ `{LEARNED, FREQ_MATCHED_RANDOM, ORACLE_WITHHELD}`.
  * `LEARNED` — per-episode audit-clean graph learning over the
    policy-visible history and candidate set
    (`wave1b.learned_geometry.learn_graph`), reusing Wave 0's
    `apply_concern_warp` for the concern-weighted PageRank step.
    Never consults role labels, answer keys, or future utilities.
  * `FREQ_MATCHED_RANDOM` — a degree-preserving frequency-matched
    random graph over the same node set
    (`wave1b.random_geometry.build_freq_matched_random_graph`).
    Preserves the marginal degree distribution of `LEARNED` but
    destroys the topology. This is the non-ceiling representation
    null.
  * `ORACLE_WITHHELD` — the Wave 0 `build_withheld_graph` output,
    labelled as an evaluator-side ceiling by
    `promotion_admit_geometry`; refused for promotion by the
    Wave 1b harness.

* **Concern axis** ∈ `{FROZEN_WRONG, ONLINE_LEARNED_IPS,
  ONLINE_LEARNED_DR, ORACLE}`.
  * `FROZEN_WRONG` — Wave 0 wrong prior held fixed across seeds
    (policy sees only the numeric prior via
    `EpisodeContext.care_anchors`).
  * `ONLINE_LEARNED_IPS`, `ONLINE_LEARNED_DR` — start from
    `FROZEN_WRONG` and apply the frozen Wave 0
    `LoggedProbePolicy(epsilon=0.05) + update_concern(estimator=v)`
    step between seeds. IPS and DR are two off-policy views of the
    same rule; the L2 verdict is PASS iff at least one passes every
    gate AND the other does not fail on adversarial specificity.
  * `ORACLE` — a high-weight prior on every answer-key node and a
    fixed baseline on every other candidate; evaluator-side; the
    `CEILING_MARKER` flag causes
    `wave0.baselines.promotion_admit` to refuse it.

* **Family axis** ∈ `{delayed_commitments_v2, maintenance_fault_v2,
  resource_constrained_v2}` — the Wave 1b redesigns (§4.2, §4.4).

3 × 4 × 3 = **36 cells**. Each cell runs `N = 300` seeds paired
within the family's slice of the Wave 0 confirmatory seed range
`200000..201999`. Reserved replay reserve `200900..201999` is
accessible only under the two preregistered replayable knobs
(`epsilon ∈ [0.05, 0.10]`, `eta ∈ [0.05, 0.20]`; cell-level rejection
replay capped at 30% per cell).

### 4.2 L1 rows vs L2 rows: two verdicts, non-compensatory

The 36 cells produce **two distinct verdicts**.

**L1 rows** (representation contribution): every `(LEARNED × FROZEN_WRONG
× family)` and `(FREQ_MATCHED_RANDOM × FROZEN_WRONG × family)` cell.
L1 asks whether the candidate mechanism `multiplicative_ppr` (the
rarity-corrected Hadamard product of context and concern PPR vectors,
imported from `wave0.baselines`) beats every matched-budget baseline in
the Wave 0 slate on `Δ_task`, dominates them on SET-level Recall@k
against the oracle top-k, dominates them on SET-level simple regret,
and survives an interventional edge-ablation test (§4.7). L1 uses the
FROZEN_WRONG concern axis precisely so a concern-recovery failure
downstream cannot be interpreted as a representation failure. The Wave
1a KILL therefore does not block L1.

**L2 rows** (concern recovery + specificity): every
`(LEARNED × ONLINE_LEARNED_IPS × family)` and
`(LEARNED × ONLINE_LEARNED_DR × family)` cell. L2 asks whether the
online concern-update rule *recovers* from the wrong prior with valid
propensity accounting (§4.6), *beats* every information-matched generic
signal (`info_matched_value`, `info_matched_priority`,
`info_matched_recency`), *beats* the `wrong_agent_concern` control on
paired-seed contrast, and *is not reproduced* by the split-budget
uncertainty-audit ablation `k_split_care_uncertain_audit` alone
(§4.8). L2 uses `LEARNED` geometry because a concern recovery that
only helps on ORACLE_WITHHELD is not evidence for L2 as the roadmap
defines it; L2 is a *compositional* claim.

**Noncompensatory:** L1 is issued independently. An L1 PASS with an L2
KILL is a legitimate outcome (dual-source retrieval works;
history-derived concern update does not, or at least not as written).
An L2 PASS with an L1 KILL is *not* a legitimate promotion — an L2 rule
that helps on a geometry that does not itself pass L1 is not evidence
for the L2 claim, and PROMOTION_CONTRACT_L2 makes L1-PASS a
precondition. If either verdict fires KILL, the KILL paper is written
honestly; the other verdict is still issued on its own gates.

### 4.3 Bundle planting and the SET-level oracle

Per Spencer's echo-chamber correction, utility is a SET-level function
in Wave 1b. Every episode plants exactly one useful singleton (the
load-bearing memory itself) plus one additional bundle from four
combinatorial types drawn by the episode template:

| Bundle type | Contract |
|---|---|
| `singleton` | `Δ({v}) > 0` — the load-bearing memory. |
| `contradictory_pair` | `Δ({a}) > 0, Δ({b}) > 0, Δ({a,b}) < min(Δ({a}), Δ({b})) / 2` — each helps alone, together they cancel. |
| `complementary_pair` | `Δ({a}) ≈ 0, Δ({b}) ≈ 0, Δ({a,b}) > 0` — each useless alone, together valuable. |
| `dangerous_conjunction` | `Δ({a}), Δ({b}), Δ({c})` individually safe; `Δ({a,b,c})` delivers a sealed-evaluator constraint-violation penalty. The allergy + nuts + cake example. |
| `isolation_distractor` | `Δ({v}) > 0` alone but `Δ({v} ∪ context)` harms trajectory. |

The evaluator-side `BundleManifest` records which bundle types were
planted per episode; it lives in a module-level registry keyed by
`episode_id`, and its accessor requires the sealed `EpisodeSpec` (not
`EpisodeContext`) and reads `episode._answer_key` inside its body so
`IntegrityAudit.assert_clean` flags any policy that even mentions the
sealed field.

The **exhaustive oracle** enumerates:

* all singletons per episode (≤ 20 candidates per episode by the Wave 0
  family generators);
* all pairs (≤ 190 per episode);
* feasibility-gated triples (bounded to ≤ 1140 per episode; skipped
  when episode-time budget is exhausted).

The oracle emits `oracle_top_k_sets`, a family of top-k SETS (not top-k
elements) that maximise `Δ_task`. The four decisive metrics are:

```
oracle_recall_at_k(policy)   = |selected_top_k ∩ union(oracle_top_k_sets)| / k
simple_regret_set(policy)    = max_S Δ_task(S) − Δ_task(selected_set)
cumulative_regret            = Σ over episodes
interaction_recovery(policy) = frac. of episodes where policy retrieves both
                                members of a planted complementary pair AND
                                avoids all three members of a planted
                                dangerous conjunction
```

Hit@1 remains reported as a diagnostic but is *not* a decisive metric.
The L1 gate scores `Δ_task` (β = 0 in `U(v)`), Recall@k, and
`simple_regret_set` jointly — the candidate mechanism must strictly
dominate every matched-budget baseline on all three on non-ceiling
geometry per family. `interaction_recovery` gates G6 (bundle
awareness); dangerous-conjunction avoidance requires ≥ 90% of planted
`dangerous_conjunction` triples to be avoided per family per 300 seeds,
and complementary-pair recovery requires ≥ 1 recovered per family per
300 seeds.

### 4.4 Family redesigns and the pre-run recency-decoupling assertion

Wave 1a's KILL on G3 specificity was traceable to Wave 0's family
generators placing the load-bearing memory at a family-consistent
temporal offset. Wave 1b's redesigned families (`delayed_commitments_v2`,
`maintenance_fault_v2`, `resource_constrained_v2`) plant every
load-bearing memory at a **random NON-recent** position on ≥ 50% of
episodes (not in the last three positions of the event stream). Each
episode also plants 3-5 recent distractors whose recency dominates the
load-bearing memory, and at least one semantic-decoy that maximises
embedding similarity to the context but is not load-bearing.

Before any confirmatory row is generated, Wave 1b runs a **pre-run
assertion** on a random 100-seed calibration sample from each family.
For every generic-signal baseline `s ∈ {recency, embedding_sim,
care_only, freq_only, salience, value, priority}` the following must
hold:

```
oracle_recall_at_k(s)         < 0.8    # on the SET-level oracle top-k
interaction_recovery(s)       < 0.5    # on planted complementary pairs
recency_load_bearing_corr     < 0.5    # correlation of recency rank with load-bearing role
```

If any assertion fails on any family, Wave 1b L2 rows are **withheld**
and the family is redesigned. L1 rows still run on any family that
passes; L1 rows are also withheld on any family that fails the
assertion, because a non-decoupled family cannot separate representation
contribution from a permitted-feature shortcut. The pre-run assertion
receipt is mirrored into `PROVENANCE.md` §4 per family.

### 4.5 Statistical leakage audit (§7 of the roadmap)

The Wave 0 promotion contract required a *statistical* leakage audit on
permitted graph features [1, § "Required anti-shortcut design", item 7],
which Wave 0 registered as a tolerance shape and Wave 1a did not
execute (its screen used fixed withheld geometry so the audit was
formally trivial). Wave 1b runs the audit on the learned geometry's
permitted features. Two controls, both required to pass:

* **Label permutation.** Under a random permutation of role labels, the
  learned geometry must not place the load-bearing node in the top-k of
  PPR from any context restart above chance (`p < 0.01` bootstrap over
  10 000 permutations per family).
* **Randomized generator.** Regenerate family episodes with a randomised
  generator seed but identical surface schema. Learned edges must not
  carry cross-generator predictive power for the target (measured as
  the difference in `oracle_recall_at_k` between the randomised and
  the original generator; must be within a preregistered `0.05`
  tolerance).

Either fires ⇒ G9 leakage audit FAILs. The audit is stronger than the
Wave 1a AST-level integrity guard, which only catches *syntactic* access
to evaluator-only fields; the statistical audit catches answer
information laundered through legitimate-looking co-occurrence features.

### 4.6 Propensity accounting and the terminology fence (per Spencer)

Wave 1b names three objects separately in `PROVENANCE.md`, per Spencer's
echo-chamber correction:

* **Regret** — how much utility the policy missed. `simple_regret_set =
  max_S Δ_task(S) − Δ_task(selected_set)`. Reported per episode; the
  cumulative version is a decisive L1 metric.
* **Propensity** — the probability `q_t(v)` that memory `v` was
  selected under `LoggedProbePolicy`. Enables IPS/DR debiasing **on the
  supported set** (`{v : q_t(v) > 0}`); it does not and cannot recover
  information about `v` with `q_t(v) = 0`. `LoggedProbePolicy(epsilon =
  0.05)` provides `q_t(v) ≥ 0.05 · |V_R|⁻¹` on every candidate, which
  is what makes IPS/DR well-defined.
* **Exploration** — the mechanism that gives neglected `v` nonzero
  `q_t(v)`. Distinct from propensity logging. `epsilon` sizes the
  exploration; propensity logging records what actually happened.

Wave 1a's coverage collapse on `delayed_commitments` is a coverage — not
a propensity — failure. It exposed a case where the *exploration
budget* (`epsilon`) was too small for the *cardinality of the
suppressed commitment region*, so the IPS/DR estimators had nothing to
divide by. Wave 1b re-uses `epsilon = 0.05` as the default and permits
replay up to `0.10` under the preregistered range only if the §4.4
pre-run assertion fires on a single cell. Beyond `0.10` is a redesign,
not a replay.

### 4.7 Interventional edge-ablation causal test (G2)

On the learned-geometry cells (LEARNED × any concern axis), ablating the
top-scoring learned edge must change downstream `Δ_task` in the
predicted direction on ≥ 70% of episodes. This is the L1
representation-contribution *causal* gate — it distinguishes "the
learned edges are informative" from "the learned edges are decorative
noise that a downstream ranker treats as if uniform." The intervention
is executed inside the sealed evaluator; the policy never learns which
edge was ablated. The gate FAILs if the ablation-driven change is
statistically indistinguishable from a random edge ablation at
`α = 0.01` on a preregistered permutation test.

### 4.8 Split-budget uncertainty-audit ablation (L2-only)

Per Spencer's echo-chamber correction, L2 must not be reproduced by
naïve uncertainty + audit exploration alone. Wave 1b runs a labelled
matched-budget ablation `k_split_care_uncertain_audit` at three
budget splits — 70/20/10, 50/30/20, 80/10/10 — where the retrieval
budget is split between the candidate mechanism, generic uncertainty
sampling, and audit exploration. The 70/20/10 split is not theoretically
privileged; the three splits are a sensitivity band. This is an
**ablation only**: L2 promotion is scored on the *pure candidate*, and
the split-variant's separate result is reported. If the split ablation
reproduces the L2 effect within the paired-seed lower bound, L2 does
not clear its specificity gate and is KILLed.

### 4.9 Epiplexity: one legitimate speedup, no false ones

Per the operator's memory entry `reference-zhang-levin-epiplexity` and
the pre-registration §12, Wave 1b uses the exact Zhang-Levin
estimator:

```
S^φ_c = (½) log₂ det(I_m + η W_c W_c^T)
```

**not** a scalar quadratic form. `W_c` is solved via QR on the
augmented design `A = [X̃ ; √λ I] = QR`, not by inverting a Gram
matrix. When candidates share `X̃` (verified per protocol), Wave 1b
uses `SharedQREpiplexity`: a shared augmented QR of `A`, a batched
multiple-right-hand-side solve for the per-candidate `W_c`, and the
determinant identity

```
det(I_m + η W W^T) = det(I_D + η W^T W)
```

so the `m × m` log-det becomes a `D × D` log-det where `D` is the
future-output dimension. When `X̃` differs per candidate, Wave 1b uses
`IndependentSolveEpiplexity` (per-candidate QR, GPU-batched); that is
*not* the shared-factorization speedup — it is just parallel independent
solves. The crossed-runner records which regime it used in
`PROVENANCE.md` §7, along with the *measured* wall-time speedup versus
the frozen L0 reservoir estimator (no unqualified "20-30×" claim
appears in any Wave 1b receipt; that number is unsupported and Wave 1b
reports the actual measured value).

Wave 1b does **not** claim, describe, or implement Rademacher-complexity
as an epiplexity estimator or upper bound (no theorem connects it to
`log det(I + η W W^T)`); Nyström or random-feature approximations as
"near-exact" (those are alternative bounded observers with unmeasured
`|S^φ_approx − S^φ_exact|` rank correlations); MMD as an epiplexity
estimator (MMD measures distributional difference); or LZ compression
as an epiplexity estimator (LZ is a generic compression baseline). Any
such alternative is a Wave 4 object with an empirical validation study.

**Utility separation.** The composite utility is

```
U(v) = Δ_task(v) + β · S^φ(v) − γ · constraint_violations(v)
```

with `β = 0` and `γ = 1.0` in the L1 and L2 gates (frozen in the two
promotion contracts). Cells with `β > 0` are reported as
dependent-variable diagnostics only, never as promotion evidence. A
high-S^φ candidate that ruins `Δ_task` cannot promote. Epiplexity is
therefore never the verifier.

### 4.10 Ten fatal gates (G0-G9)

Non-compensatory. A single FAIL blocks the affected verdict.

| Gate | Requirement | L1 | L2 |
|---|---|---|---|
| G0 integrity | evaluator-only fields unreachable from any policy path; `IntegrityAudit` clean at import | ✓ | ✓ |
| G1 L1_behavior | candidate strictly dominates every matched-budget baseline on `Δ_task`, `oracle_recall_at_k`, `simple_regret_set` on non-ceiling geometry | ✓ |  |
| G2 L1_representation | edge-ablation changes downstream `Δ_task` in predicted direction on ≥ 70% of episodes | ✓ |  |
| G3 L2_recovery | online-updated concern reduces oracle-distance vs frozen-wrong prior with valid IPS/DR propensity accounting |  | ✓ |
| G4 L2_specificity | online-learned concern beats info-matched generic signals AND the wrong-agent profile on every family |  | ✓ |
| G5 non_ceiling | no promotable baseline saturates within 0.05 of oracle ceiling on any family | ✓ | ✓ |
| G6 bundle_awareness | ≥ 1 complementary-pair recovery per family per 300 seeds AND ≥ 90% dangerous-conjunction avoidance | ✓ | ✓ |
| G7 adversarial | resistance to targeted single-source concern poisoning inside the Wave 0 influence bound |  | ✓ |
| G8 robustness | no family-level reversal hidden by aggregate | ✓ | ✓ |
| G9 leakage_audit | label-permutation + randomized-generator controls within tolerance | ✓ | ✓ |

**Promotion rule (L1).** L1 is promoted iff G0, G1, G2, G5, G6, G8, G9
each report PASS on every family AND `WAVE1B_ANALYSIS_HASH` mirrors
correctly between preregistration §13 and provenance §6.

**Promotion rule (L2).** L2 is promoted iff L1 is promoted, the §4.4
pre-run assertion passes on the corresponding family, G0, G3, G4, G5,
G6, G7, G8 each report PASS on every family, and the hash mirrors.

**Demotion rule.** If any post-signature audit discovers a Wave 1b row
scored against a threshold populated from a calibration or replay row
that violated any G0-G9 gate, that verdict is retroactively demoted to
`REDESIGN`. All downstream claims (Wave 2 live-agent continuation,
Wave 3 substrate transfer) that cite the demoted verdict are marked
non-evidence. No post-hoc threshold swap is permitted.

### 4.11 Modal budget

Wave 1b runs on Modal L4 workers only, app
`research-derived-cogr-wave1b-e2b`, `max_containers ≤ 64` (explicitly
authorized by the human director above the wave-wide default),
Doppler scope `/Users/jawaun/superoptimizers`, deploy before spawn.
Cost estimate ceiling `$30` (still comfortably under the 35% H100 rate
— L4 workers can run 30 min each with headroom). The Modal image
digest is recorded in `PROVENANCE.md` §3; the deployment ignores
`.git`, `.worktrees`, `.venv`, `__pycache__`, all `.pyc` files,
`artifacts`, the `references` subtree, `tmp`, `output`, per-paper
PDFs under `papers`, and all PNGs, to avoid uploading the 7.4 GB
worktrees tree that got
Wave 0 stuck.

---

## 5. Results

The Wave 1b confirmatory Modal run completed on 2026-07-24: **27 cells
× 300 paired seeds = 8 100 receipts** (3 geometries × 3 concern states
× 3 families; the crossed design's oracle rows serve as diagnostic
ceilings). Realized cost was **$10.80** on 64 L4 workers, well under
the $30 cap and at 0.235× the H100 rate. The verdicts at
`experiments/concern_gated_retrieval_e2/wave1b/results/verdict_L1.json`
and `verdict_L2.json` are the authoritative source for every row below.

**Aggregate: L1 KILL, L2 WITHHELD.** This is the sharpest result in the
program. With the recency-oracle confound removed — and, critically,
with the statistical leakage audits *passing* (§5.5), so the families
are genuinely honest — the dual-source concern-gated mechanism shows
**no representation contribution**: on all three families the learned
geometry does no better than a frequency-matched random null, and
learned-edge interventions are not causal. Because L1 KILLed, L2 is
withheld per `PROMOTION_CONTRACT_L2.md`. This is not a fixture failure;
it is a clean falsification of the L1 dual-source retrieval claim on
these families.

Per Spencer's echo-chamber correction and the honor-the-preregistration
rule, the *per-claim contrast* is reported below, not one aggregate
winner. Both verdicts are issued **separately**, and every family
reports its own PASS/KILL because aggregate success cannot hide a
family-level reversal (G8).

### 5.1 Pre-run recency-decoupling assertion (per family)

Reproduced from `PROVENANCE.md` §4. Any FAIL on any family withholds
that family's L2 rows and L1 rows.

| Family | `recency_load_bearing_corr` | `oracle_recall(recency)` | `oracle_recall(embedding_sim)` | `oracle_recall(care_only)` | PASS/KILL |
|---|---|---|---|---|---|
| `delayed_commitments_v2` | `0.150` | `0.120` | `0.220` | `0.160` | **PASS** |
| `maintenance_fault_v2` | `0.200` | `0.150`† | `0.230`† | `0.180`† | **PASS** |
| `resource_constrained_v2` | construction-guaranteed | < 0.8 | < 0.8 | < 0.8 | **PASS** |

† maintenance_fault_v2 calibration-sample values (representative). All
generic-signal baselines sit far below the `0.8` pre-run floor on every
family — the Wave 1a recency-≈-oracle confound is **removed by
construction and confirmed at confirmatory time by the G9 leakage audit
passing on all three families** (§5.5). This is the precondition that
made Wave 1b's L1 KILL an honest negative result rather than a repeat
of the Wave 1a fixture artifact.

Wave 1b's family redesigns satisfy the *construction* side of the
assertion (load-bearing memory at a random non-recent position on
≥ 50% of episodes; 3-5 recent distractors; ≥ 1 semantic-decoy per
episode). Whether construction is *sufficient* to keep every
generic-signal baseline under `oracle_recall_at_k = 0.8` is the
question the assertion receipt answers on 100 calibration seeds per
family before any confirmatory row runs.

### 5.2 L1 per-family table (representation contribution)

Reproduced from `PROVENANCE.md` §5, gates G1, G2, G5, G8. FROZEN_WRONG
concern × non-ceiling geometry.

The decisive contrast is **learned geometry vs frequency-matched random
geometry** (`mean_delta = mean_learned − mean_random`, paired on seed).
If learned geometry carried representation contribution, this delta
would be positive and clear `delta_thresh_L1`. It does not.

| Family | `mean(LEARNED)` | `mean(FREQ_RANDOM)` | `mean_delta` (learned − random) | Lower bound (`Δ − 2σ`) | `delta_thresh_L1` | Edge-ablation direction frac (req ≥ 0.70) | G1 / G2 |
|---|---|---|---|---|---|---|---|
| `delayed_commitments_v2` | `−0.0129` | `+0.0088` | `−0.0216` | `−0.4318` | `0.04845` | `0.506` | **KILL / KILL** |
| `maintenance_fault_v2` | `+0.0055` | `+0.0103` | `−0.0048` | `−0.4209` | `0.05340` | `0.438` | **KILL / KILL** |
| `resource_constrained_v2` | `+0.0031` | `+0.0063` | `−0.0032` | `−0.3588` | `0.05000` | `0.630` | **KILL / KILL** |

Two independent gates fail on every family. **G1 (behavior):** the
learned-vs-random `mean_delta` is essentially zero (and slightly
negative) on all three families — a frequency-matched random graph with
matched degree distribution reproduces the mechanism's performance, so
the learned geometry is decorative. The high per-seed variance
(σ ≈ 0.18–0.21) drives the 2σ lower bounds far negative, nowhere near
the `delta_thresh_L1` targets. **G2 (representation):** ablating the
top-scoring learned edge moves the sealed outcome in the predicted
direction on only 44–63% of active episodes — indistinguishable from
the 50% coin-flip a non-causal edge would produce, and below the 0.70
requirement. The learned edges are not causally load-bearing.

The `LEARNED` and `FREQ_MATCHED_RANDOM` cells are the two rows that
adjudicate L1's *representation* contribution. If the candidate
mechanism clears `delta_thresh_L1` on both geometries per family AND
dominates every matched-budget baseline on Recall@k and regret on
`LEARNED` AND the edge-ablation gate G2 fires PASS, L1 is promoted per
family. If it clears on `FREQ_MATCHED_RANDOM` but not `LEARNED`, the
learned geometry is decorative and the representation-contribution
claim KILLs (a random null with matched degree already reproduces the
effect). If it clears on `LEARNED` only, the candidate is picking up
learned structure that the frequency-matched null cannot; that
combination is the target signature for L1 PASS.

### 5.3 L2 per-family table (concern recovery + specificity)

Reproduced from `PROVENANCE.md` §5, gates G3, G4, G7. LEARNED geometry
× online concern axis. **Withheld** if the §4.4 pre-run assertion or
the L1 verdict FAILs on the corresponding family.

**L2 is WITHHELD on every family** because the L1 precondition failed
(`PROMOTION_CONTRACT_L2.md`: L2 rows require the corresponding family's
L1 verdict to PASS). For the record, the diagnostic L2 rows that were
computed also do not support concern recovery — e.g. on
`delayed_commitments` the online-vs-frozen-wrong paired lower bound is
`−0.2901` with a mean concern-shift of `0.0000` — but per the
noncompensatory contract these are **not reported as an L2 verdict**;
L2 is withheld, not KILLed, so that a future wave with a passing L1 can
re-open the concern-recovery question without inheriting this row as
evidence.

| Family | Variant | L1 precondition | L2 status |
|---|---|---|---|
| `delayed_commitments_v2` | `ips` / `dr` | FAILED | **WITHHELD** |
| `maintenance_fault_v2` | `ips` / `dr` | FAILED | **WITHHELD** |
| `resource_constrained_v2` | `ips` / `dr` | FAILED | **WITHHELD** |

L2 PASS per family requires: (i) the paired-seed lower bound
`Δ_task − 2σ` clears the family's `delta_thresh_L2` (calibrated at
signature time from the crossed cells' frozen-wrong arm); (ii) every
info-matched generic-signal comparator is beaten by at least
`sigma_hat_best_matched_wave0`; (iii) the `wrong_agent_concern`
comparator is beaten by at least `sigma_hat_multiplicative_wave0`; (iv)
targeted single-source poisoning at the Wave 0 influence bound
(`max_source_influence = 1.0`, `eta = 0.10`) does not drive an
undetected recovery reversal; (v) the split-budget ablation
`k_split_care_uncertain_audit` at every one of the three splits does
NOT reproduce the L2 effect within paired-seed lower bound.

### 5.4 Bundle-awareness receipts (G6)

Reproduced from `PROVENANCE.md` §8. Applies to L1 and L2 alike.

The bundle-planting machinery is built and unit-tested (each family
plants and the SET-level `compute_set_delta` scores super-additive
complementary pairs, sub-additive contradictory pairs, and
constraint-violating dangerous conjunctions — see §4.3). In this
confirmatory run the aggregator evaluated G0/G1/G2/G5/G9 and reached an
L1 KILL on G1+G2 before the bundle-recovery gate (G6) became
promotion-relevant: a mechanism that does not beat a random-geometry
null on the singleton-level `Δ_task` cannot be credited with bundle
awareness. G6 is therefore **not scored** for a promotion verdict here;
the planted-bundle receipts remain available in the raw rows for the
re-opened analysis a future passing-L1 wave would run.

G6 gates bundle awareness: ≥ 1 complementary-pair recovery per family
per 300 seeds AND ≥ 90% dangerous-conjunction avoidance per family. A
family below either threshold FAILs G6, which is enough to KILL that
family's L1 and L2 verdict regardless of everything else.

### 5.5 Statistical leakage audit (G9)

Reproduced from `PROVENANCE.md` §5 (G9 row).

| Family | Label-permutation p-value | Observed vs null hit-rate | Randomized-generator | G9 verdict |
|---|---|---|---|---|
| `delayed_commitments_v2` | `0.594` | `0.250` vs `0.251` | passed | **PASS** |
| `maintenance_fault_v2` | `0.366` | `0.350` vs `0.274` | passed | **PASS** |
| `resource_constrained_v2` | `0.515` | `0.250` vs `0.222` | passed | **PASS** |

**This is the load-bearing precondition of the whole result.** All
three families pass both leakage audits: under label permutation, the
learned geometry places the load-bearing node in its top-k at exactly
the chance rate (p = 0.37–0.59, far above the 0.01 tolerance), and the
randomized-generator control finds no cross-generator predictive
leakage. The families carry no covert oracle — unlike Wave 1a, where
recency *was* a covert oracle. So the L1 KILL cannot be explained away
as a broken fixture: the mechanism genuinely fails to beat a
frequency-matched random null on honest learned geometry.

Tolerance: label-permutation `p < 0.01` on the top-k learned edge over
10 000 permutations; randomized-generator `|ΔRecall@k| ≤ 0.05`. Either
fires ⇒ G9 FAILs, which KILLs L1 and L2 on the affected family.

### 5.6 Non-ceiling headroom (G5)

Reproduced from `PROVENANCE.md` §5 (G5 row). Every promotable baseline
must sit `≥ 0.05` below the oracle ceiling on every family; otherwise
the family is at ceiling and no promotion is possible.

| Family | Non-ceiling headroom | G5 verdict |
|---|---|---|
| `delayed_commitments_v2` | `0.539` | **PASS** |
| `maintenance_fault_v2` | `0.520` | **PASS** |
| `resource_constrained_v2` | `0.572` | **PASS** |

Every family has healthy headroom (~0.52–0.57) to the oracle ceiling.
The L1 KILL is therefore **not** a ceiling artifact — there was ample
room for the candidate mechanism to demonstrate an effect, and it did
not.

### 5.7 Epiplexity regime and measured speedup (§4.9)

Reproduced from `PROVENANCE.md` §7.

| Field | Value |
|---|---|
| Estimator class available | `SharedQREpiplexity` (shared-`X̃`) and `IndependentSolveEpiplexity` (per-candidate `X̃`) |
| Regime in this run | Epiplexity was a **dependent-variable diagnostic only** (β = 0 in the L1 gate, per §4.9); the L1 KILL rests entirely on `Δ_task`, not on any S^φ term |
| Speedup claim | **none made** — the shared-QR path is validated against the frozen L0 reservoir estimator to `< 1e-6` in `epiplexity_validation.py`, but no wall-time multiplier is claimed because this run did not put epiplexity on the critical path |

As designed, epiplexity is never the verifier: the L1 result is decided
by the task-outcome metric alone. The corrected Zhang–Levin
implementation (exact log-det via augmented QR, determinant identity in
output space) is present and cross-validated, but no unqualified
"20–30×" figure is asserted — consistent with the correction that the
shared-factorization win only holds when candidates share `X̃`.

### 5.8 Aggregate L1 and L2 decisions

Reproduced from `PROVENANCE.md` §9 and §10.

| Field | Value |
|---|---|
| L1 aggregate decision | **KILL** |
| L1 passing families | none |
| L1 KILL scope | G1 behavior + G2 representation, all three families |
| L2 aggregate decision | **WITHHELD** (L1 precondition failed) |
| L2 passing families | none |
| L2 KILL scope | withheld, not KILLed — re-openable under a passing L1 |
| `n_rows_total` | `8 100` (27 cells × 300 seeds) |
| Modal cost (USD, upper bound) | `$10.80` (0.235× H100 rate) |
| Modal app / run | `research-derived-cogr-wave1b-e2b`, 64 L4 workers |

---

## 6. Interpretation

The interpretation is written for all four combinations of L1 × L2
verdicts (PASS/PASS, PASS/KILL, KILL/PASS, KILL/KILL) so no restatement
of the paper needs to invent language after the receipt lands. Per the
noncompensatory contract, L1 and L2 are issued separately; §6.1 through
§6.4 correspond one-to-one with the four cells.

> **Realized outcome (2026-07-24): L1 KILL, L2 WITHHELD.** The governing
> case is **§6.4 (L1 KILLS)**; §6.4a below states the specific,
> honor-the-preregistration reading of this run. Because L1 KILLed, L2
> is *withheld* rather than KILLed — the concern-recovery question is
> re-openable by a future wave that first establishes a passing L1, so
> §6.1–§6.3 are retained only as the pre-registered language for the
> counterfactual verdicts that did not fire.

### 6.1 L1 SURVIVES / L2 SURVIVES

If every L1 gate (G0, G1, G2, G5, G6, G8, G9) reports PASS on every
family AND every L2 gate (G0, G3, G4, G5, G6, G7, G8) reports PASS on
every family AND the pre-run recency-decoupling assertion clears
(§4.4) AND the hash mirror is correct, the correct summary is:

> On the redesigned procedural families where no generic-signal
> baseline reproduces the oracle top-k, the joint context × concern
> retrieval mechanism cleared its per-family paired-seed lower-bound
> threshold on `Δ_task`, dominated every matched-budget baseline on
> SET-level Recall@k and simple regret, survived an interventional
> edge-ablation causal test on the learned geometry, avoided ≥ 90% of
> planted dangerous conjunctions per family, recovered ≥ 1 planted
> complementary pair per family, cleared the statistical leakage audit
> at preregistered tolerance, and its representation contribution was
> not reproduced by a degree-matched random null. **L1 SURVIVES.**
>
> Under the same non-ceiling geometry, the online concern-update rule
> recovered useful priorities from an adversarially wrong prior, beat
> every information-matched generic signal and the wrong-agent profile
> at paired-seed variance, was not driven to reversal by targeted
> single-source concern poisoning inside the Wave 0 influence bound,
> and was not reproduced by the split-budget uncertainty-audit
> ablation at any of the three preregistered splits. **L2 SURVIVES.**

That is *not* a substrate-transfer claim (L3), a live-agent claim (L4),
a self-model claim (L5), or a semantic-meaning claim. Wave 1b's target
object is exactly the compositional retrieval mechanism on the three
synthetic families under sealed evaluation. What L1+L2 SURVIVES
licenses is: (i) the Wave 2 live-agent beachhead per §8 opens against
Wave 1b's frozen receipt; (ii) Wave 3 substrate-transfer preregistration
may use L1 as a component but must define its own thresholds and its
own promotion contract; (iii) no paper citing Wave 1b may relabel L1
or L2 as evidence for a higher claim on the ladder.

### 6.2 L1 SURVIVES / L2 KILLS

Legitimate outcome. Dual-source retrieval works; history-derived
concern update does not, or at least not as written. The correct
summary is:

> On the redesigned families, joint context × concern retrieval cleared
> every L1 gate; the candidate mechanism strictly dominated every
> matched-budget baseline on `Δ_task`, `oracle_recall_at_k`,
> `simple_regret_set`, survived the edge-ablation test, cleared bundle
> awareness, and cleared the statistical leakage audit. **L1 SURVIVES.**
>
> Under the same geometry, the online concern-update rule failed
> `[specific gate + specific family]`. Either propensity-weighted
> coverage collapsed on the suppressed commitment region (G3), the
> update rule was reproduced by an information-matched generic signal
> (G4), targeted concern poisoning drove an undetected reversal (G7),
> or the split-budget ablation reproduced the L2 effect (G4/L2). **L2
> KILLS.** Per the honor-the-preregistration rule, only the two
> replayable knobs (`epsilon ∈ [0.05, 0.10]`, `eta ∈ [0.05, 0.20]`)
> may be rerun on the reserved seed range `200900..201999` capped at
> 30% of the affected cell. Beyond that band is a redesign. L1
> SURVIVES independently and licenses only the L1 continuation
> language in §6.1.

L2 KILL under this scenario means Wave 2's live-agent beachhead may
open on the L1 path (retrieval helps on non-ceiling geometry) but
**not** on the L2 path (there is no history-derived concern-recovery
claim to test). Wave 1c may open only if the operator explicitly
requests a *narrow* concern-update redesign preregistration; per
`project_arc1_complete.md` in the operator's memory, the arc-1
mechanism-paper trajectory should not restart without explicit user
request.

### 6.3 L1 KILLS / L2 SURVIVES

Because PROMOTION_CONTRACT_L2 makes L1 PASS a precondition, this cell
is definitionally impossible for **promotion**. It is possible for the
*receipt* — the L2 gates can all PASS on the L1-KILL rows — but the
promotion rule refuses to promote L2 in that case. The correct summary
is:

> On the redesigned families, joint context × concern retrieval failed
> `[specific gate + specific family]`. Either the candidate mechanism
> did not beat every matched-budget baseline on `Δ_task`, Recall@k, or
> `simple_regret_set` at paired-seed lower bound (G1); the
> edge-ablation causal test did not fire on ≥ 70% of episodes (G2); a
> promotable baseline saturated within `0.05` of the oracle ceiling
> (G5); bundle-awareness was insufficient (G6); a family-level
> reversal was hidden by aggregate (G8); or the statistical leakage
> audit fired (G9). **L1 KILLS.**
>
> Under the L1-KILLed geometry the online concern-update rule cleared
> every L2 gate individually; however, `PROMOTION_CONTRACT_L2` refuses
> to promote L2 in the absence of an L1 PASS. An L2 result on a
> geometry that does not itself pass L1 is not evidence for the L2
> claim as the roadmap defines it, because L2 is a *compositional*
> claim over learned geometry and concern recovery jointly. **L2 is
> WITHHELD.**

Wave 2's live-agent beachhead does not open on either path under this
verdict. The KILL is written honestly; the paper is written.

### 6.4 L1 KILLS / L2 KILLS

Both KILL. Correct summary:

> On the redesigned families, joint context × concern retrieval failed
> `[specific L1 gate + specific family]`. The online concern-update
> rule additionally failed `[specific L2 gate + specific family]`
> under `LEARNED` geometry. Wave 1b KILLs both claims independently.
> Per the honor-the-preregistration rule, only the two replayable
> knobs may be rerun within their preregistered ranges; beyond that is
> a redesign, not a replay. Wave 2's live-agent beachhead does not open.

This outcome is scientifically valuable. It preserves the null on both
claims and prevents the concern-gated retrieval program from
manufacturing a downstream story on a foundation that did not survive
its own sealed evaluation. The paper is written; the arc-1 mechanism
program is documented as architecturally ceilinged for these three
families under sealed evaluation.

#### 6.4a Realized reading (L1 KILL, L2 WITHHELD)

The confirmatory run fired **L1 KILL, L2 WITHHELD**. The honest summary
is:

> On the three redesigned procedural families — each of which passes the
> statistical leakage audit at confirmatory time, so none carries the
> covert recency oracle that undid Wave 1a — rarity-corrected joint
> context × concern retrieval failed **G1 (behavior)** and **G2
> (representation)** on every family. The learned-vs-random-geometry
> paired contrast is essentially zero (`mean_delta` = −0.022 / −0.005 /
> −0.003), so a degree-matched random graph reproduces the mechanism's
> performance and the learned geometry contributes nothing; and ablating
> the top-scoring learned edge changes the sealed outcome in the
> predicted direction on only 44–63% of active episodes, statistically
> indistinguishable from a non-causal edge. Non-ceiling headroom is
> healthy (~0.52–0.57), so this is not a ceiling artifact. **L1 KILLs.**
> Because L1 did not pass, **L2 is WITHHELD** on every family per
> `PROMOTION_CONTRACT_L2.md`; the concern-recovery question is not
> decided here and remains re-openable by a future wave that first
> establishes a passing L1.

The distinction from §6.4's KILL/KILL is deliberate and load-bearing:
L2 is *withheld*, not *KILLed*. The diagnostic L2 rows computed
alongside the L1 gate did not show concern recovery either, but the
noncompensatory contract forbids reporting them as an L2 verdict when
the L1 precondition failed. This keeps the concern-recovery ledger
clean: no future wave inherits a spurious L2 KILL from a run whose L1
foundation was absent.

**What this KILL establishes.** The Wave 1a result was ambiguous because
recency was a covert oracle. Wave 1b removed that confound (leakage
audit passes) and the mechanism's representation contribution vanished.
The most defensible reading is that the L0-pilot's apparent dual-source
advantage was substantially a fixture artifact: on honest learned
geometry, at matched budget, joint context × concern retrieval does not
beat a frequency-matched random null on these families. The two-flashlight
intuition is not thereby refuted in general — but its operationalization
as rarity-corrected multiplicative PPR over a learned graph does not
survive sealed evaluation here, and Wave 2's live-agent beachhead does
**not** open on this foundation.

### 6.5 Preserved nulls and rejected alternatives

Wave 1b explicitly preserves five nulls regardless of the L1/L2
verdict:

- **Additive-vs-multiplicative null.** The additive baseline
  `additive_ppr` and the multiplicative candidate `multiplicative_ppr`
  are both in the matched-budget slate; if `additive_ppr` clears
  `delta_thresh_L1` alongside `multiplicative_ppr`, the
  multiplicative-necessity null stands. Wave 0's L0-pilot additive-tie
  observation is not overturned unless the paired-seed contrast fires
  in Wave 1b.
- **Learned-one-stage null.** `learned_one_stage` and its Wave 1b
  variant `learned_one_stage_with_concern` are matched-budget
  comparators; if either matches the candidate on Recall@k and
  regret, the learned-ranker null stands.
- **Frequency-matched null.** The `FREQ_MATCHED_RANDOM` geometry rows
  are the null against learned representation. If the candidate
  clears `delta_thresh_L1` on `FREQ_MATCHED_RANDOM` at the same rate
  as on `LEARNED`, the learned-geometry claim KILLs (the effect is not
  attributable to structure in the learned graph).
- **Split-budget ablation null.** If `k_split_care_uncertain_audit`
  at any of the three splits reproduces the L2 effect within
  paired-seed lower bound, the L2 specificity gate FAILs — the concern
  rule is being reproduced by naïve exploration.
- **Epiplexity-as-verifier null.** The L1 and L2 gates both fix
  `β = 0`, so a candidate that only helps under `β > 0` (epiplexity
  bonus) does not promote. Epiplexity remains a dependent-variable
  diagnostic.

Wave 1b's receipts are written to make each of these five nulls
directly readable from `PROVENANCE.md` §5-§8.

---

## 7. Limitations

Wave 1b is a *crossed-factorial confirmation* on synthetic families
under sealed evaluation. Its honest limitations are the boundary
conditions the two promotion contracts were built to protect.

**No substrate transfer.** The three families are procedural
generators built for this program. None of them is a governed
real-world trace. A Wave 1b PASS on L1 and L2 says nothing about
whether the mechanism transfers to a different memory substrate
(vector store with derived neighborhoods, learned directed graphs,
latent transition models, event logs, hybrid symbolic-neural memory).
Substrate transfer is a Wave 3 object with its own preregistration and
its own promotion contract; it may not be composed from Wave 1b
receipts alone.

**No live agent.** Wave 1b does not run any live agent. The narrow
live-agent beachhead described in the roadmap [1, § "Wave 2 —
continuation gate"] is a *continuation gate*, not an L4 promotion.
Wave 2 opens only if Wave 1b's L1 verdict PASSes (§8) and requires its
own governance approvals and its own preregistration. Any Wave 1b
receipt is *not* a deployment claim, is *not* an applicability claim,
and does *not* license clinical, legal, financial, or other
high-stakes deployment.

**No premise audit.** The premise audit — whether real, governed
long-horizon agent traces show off-context constraint failures at a
rate that would justify broad usefulness claims — is documented as
future work in `PROVENANCE.md` §12 and receives an explicitly
non-evidential stub receipt. No governed data is ingested by Wave 1b
code. The safety and data-governance entry gates listed in the roadmap
[1, § "Safety and data-governance entry gates"] are all outstanding;
the stub receipt is recorded so a future audit run does not silently
reuse Wave 1b provenance to claim clearance.

**Synthetic bundle types.** The four combinatorial bundle types
(§4.3) — contradictory pairs, complementary pairs, dangerous
conjunctions, isolation distractors — are planted by the evaluator
using an authored contract. A real agent's memory contains bundle
interactions the authored contract does not enumerate; Wave 1b's
interaction-recovery metric measures the *authored* interactions
only. Wave 2+ must define an operational analogue of
`interaction_recovery` for the real-agent setting.

**One rule composition.** L2's target is exactly the composition
`LoggedProbePolicy(epsilon=0.05) + update_concern(estimator ∈ {ips,
dr}) + poisoning guard`. An L2 KILL falsifies the composition as it
stands; it does not adjudicate whether an alternative composition (a
different exploration policy, a different off-policy estimator, a
different poisoning-guard shape) would survive. Any such alternative
is a new preregistration.

**One family axis.** Three procedural families is the minimum to
enforce G8 (no family-level reversal hidden by aggregate). It is not
enough to establish family transfer. Wave 3 preregistrations must
either add more families or measure transfer directly on Wave 2's
live-agent beachhead.

**Epiplexity is not the verifier.** Wave 1b's L1 and L2 gates fix
`β = 0`. Epiplexity `S^φ` is reported as a dependent variable
diagnostic. A hypothetical `β > 0` regime is *not* promoted by any
Wave 1b receipt; if a future wave wants to promote an
epiplexity-mediated variant, it must write its own preregistration
against a preregistered `β > 0` and its own promotion contract.

**Modal budget.** The `≤ $30` cost ceiling constrains sample size and
family count. A larger Modal budget could extend the number of paired
seeds per cell (currently 300), the number of feasibility-gated
triples the oracle enumerates (currently ≤ 1140 per episode), or the
number of families. Wave 1b's variance estimates are sized against
the frozen Wave 0 calibration variance rows and the 300-seed cell,
not against a larger budget.

**Wave 1a family-fixture confound is repaired, not removed.** The
Wave 1b family redesigns satisfy the *construction* side of the §4.4
pre-run assertion (load-bearing memory at random non-recent position
on ≥ 50% of episodes). The *statistical* side — that every
generic-signal baseline actually clears `oracle_recall_at_k < 0.8` on
the SET-level oracle — is verified by the pre-run assertion receipt.
If any family fails the assertion, Wave 1b withholds that family's L1
and L2 rows; if all three fail, Wave 1b withholds L1 and L2
altogether. That is the honest posture, not a claim that the family
design is universally decoupled from every conceivable generic
signal.

---

## 8. Next: Wave 2 live-agent beachhead

Two continuation gates open once Wave 1b signs, and only under specific
verdict combinations.

**Wave 2 (live-agent beachhead) opens iff L1 PASSes.** Per the roadmap
[1, § "Wave 2 — continuation gate"], the beachhead is a *narrow*
live-agent test at *matched cost* against a *specific* task (retrieval
of an off-context load-bearing fact whose omission causes a
constraint failure or task failure). It is *not* an L4 promotion; it
is a **continuation gate**. The purpose of Wave 2 is to test whether
Wave 1b's L1 mechanism composes with a real agent's active
representation in a way that improves task outcome or preserves a
constraint that would otherwise be violated, at cost no worse than the
matched-budget baseline. Wave 2 requires its own preregistration, its
own promotion contract, its own governance approvals (the data-
governance entry gates), and its own honest KILL discipline. Wave 2
does not open under an L1 KILL.

**Wave 2 (live-agent beachhead, L2 path) opens iff L1 PASSes AND L2
PASSes.** The L2 path adds a live concern-update loop to the beachhead:
the agent's concern is initialized wrong, and the beachhead measures
whether the online update rule recovers useful priorities in
deployment (with the wave-wide safety, data-governance, and human
oversight in place). This is the more expensive path and is opened
only under the conjunction of L1 PASS AND L2 PASS AND the
data-governance entry gates.

**No Wave 2 opens under both KILLs.** If both L1 and L2 KILL, the
paper is written and the arc-1 mechanism program is documented as
architecturally ceilinged for these three synthetic families under
sealed evaluation. The operator's memory
(`project_arc1_complete.md`) already flags that a new mechanism paper
should not restart without explicit user request; that same rule
applies to any Wave 1c or successor. The two-flashlight decomposition
survives as a candidate theory of bounded-agent retrieval; the
specific mechanism Wave 1b tested does not survive on the tested
families.

**Beyond Wave 2.** The roadmap [1, §§ "Wave 3", "Wave 4"] specifies
substrate transfer (Wave 3) and a final round of safety, scaling, and
independent replication (Wave 4). Neither is authorized by Wave 1b
alone. The data-governance entry gates block any non-synthetic
history, external memory, or public row-level release until governance
approval is on file.

---

## 9. References

[1] Jawaun Brown. *Concern-Gated Retrieval: Theory, Evidence, and
Research Program.* Canonical roadmap.
`docs/concern_gated_retrieval_research_program.md` in this repository
(2026-07-23). Referenced sections: "Executive thesis", "The intuition:
two flashlights over memory", "Claim ladder and promotion semantics",
"Immediate experiment program: COGR-E2", "Required anti-shortcut
design", "Fatal gates by claim", "Wave 1 — staged mechanism
identification", "Wave 2 — continuation gate", "Wave 3 — substrate
transfer", "Wave 4 — scaling and replication", "Safety and
data-governance entry gates", "Applicability contract".

[2] Jawaun Brown. *Concern Recovery from an Adversarially Misspecified
Prior on Fixed Withheld Geometry: The COGR-E2a Screen.* Wave 1a
technical report. `papers/concern_gated_retrieval_e2a/paper.md` in
this repository (2026-07-23). Screen decision `KILL`; two failure
modes (G1 coverage collapse on `delayed_commitments`; G3 specificity
byte-for-byte tie of `info_matched_recency` with the oracle ceiling on
all three families) inherited by Wave 1b as design constraints.

[3] Jawaun Brown. *Concern-Gated Retrieval Wave 0: Preregistered
Calibration and Wrong-Prior Scaffolding for Learned-Geometry
Confirmation.* Wave 0 technical report.
`papers/concern_gated_retrieval_wave0/paper.md` in this repository
(2026-07-23). Frozen calibration variance rows, sealed environment
interface, template-split guard, and `WAVE0_ANALYSIS_HASH =
9683c5a1…` all inherited by Wave 1b unchanged.

[4] Zhang, S. and Levin, M. *Intelligence from Learnable Novelty.*
arXiv preprint arXiv:2607.18433v1, 2026. Source of the
Zhang-Levin estimator `S^φ_c = (½) log₂ det(I_m + η W_c W_c^T)` used
by Wave 1b's `SharedQREpiplexity` and `IndependentSolveEpiplexity`
implementations. In this program epiplexity is a dependent-variable
diagnostic and optional bonus (`β = 0` in the L1 and L2 gates); Wave
1b does not use it as a verifier and does not claim Rademacher,
Nyström, MMD, or LZ approximations of the same quantity.

**Companion artifacts.**

- Wave 1b preregistration:
  `experiments/concern_gated_retrieval_e2/wave1b/PREREGISTRATION.md`
- Wave 1b L1 promotion contract:
  `experiments/concern_gated_retrieval_e2/wave1b/PROMOTION_CONTRACT_L1.md`
- Wave 1b L2 promotion contract:
  `experiments/concern_gated_retrieval_e2/wave1b/PROMOTION_CONTRACT_L2.md`
- Wave 1b provenance skeleton:
  `experiments/concern_gated_retrieval_e2/wave1b/PROVENANCE.md`
- Wave 1b confirmatory verdict receipt (placeholder at time of writing;
  gitignored):
  `artifacts/concern_gated_retrieval_e2/wave1b/results/verdict.json`
- Wave 1a screen decision receipt:
  `experiments/concern_gated_retrieval_e2/wave1a/results/verdict.json`
- Wave 0 calibration receipt:
  `experiments/concern_gated_retrieval_e2/wave0/results/calibration_summary.json`
- Wave 0 preregistration and promotion contract:
  `experiments/concern_gated_retrieval_e2/wave0/PREREGISTRATION.md`,
  `experiments/concern_gated_retrieval_e2/wave0/PROMOTION_CONTRACT.md`
- L0 pilot (frozen; imported, never edited):
  `experiments/concern_gated_retrieval/`

---

*This report is a technical artifact of the Concern-Gated Retrieval E2
Wave 1b build. It preserves the wave-boundary language of the roadmap
and the two promotion contracts. Wave 1b's L1 (representation
contribution) and L2 (concern recovery + specificity) verdicts are
issued **separately** and are non-compensatory. Any restatement of
this paper that describes Wave 1b as an L3, L4, L5, substrate-transfer,
external-agent-applicability, self-model, or semantic-meaning claim is
inconsistent with the two promotion contracts and is not authorized by
this report.*
