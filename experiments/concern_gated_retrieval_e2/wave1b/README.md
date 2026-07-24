# Concern-Gated Retrieval Wave 1b — COGR-E2b Crossed-Factorial Confirmation

**Package:** `experiments/concern_gated_retrieval_e2/wave1b/`
**Wave:** 1b (COGR-E2b learned-geometry confirmation and L1 / L2 gate)
**Predecessors (imported, never edited):**
`experiments/concern_gated_retrieval_e2/wave0/`,
`experiments/concern_gated_retrieval_e2/wave1a/`
**Successor:** none yet; a Wave 1c is only opened if Wave 1b passes at
least one of L1 or L2 and downstream reviewers ratify the receipt.
**Human director:** Jawaun Brown
**Status:** preregistered; unsigned until the analysis-code freeze hash is
written into [`PREREGISTRATION.md`](PREREGISTRATION.md) §14 and mirrored
into [`PROVENANCE.md`](PROVENANCE.md).

## Scientific claim boundary

Wave 1b is a **crossed 3 x 3 x 3 confirmatory** step that issues two
verdicts **separately**:

- **L1 (representation contribution):** does joint context/concern
  retrieval with LEARNED geometry beat every matched-budget baseline on
  sealed task outcome, dominate them on SET-level Recall@k against the
  exhaustive oracle top-k, dominate them on simple SET-level regret, and
  survive an edge-intervention causal test, on every family, under the
  FROZEN-WRONG concern axis (Wave 0 wrong prior held fixed)?
- **L2 (concern recovery + specificity):** does the online-learned
  concern update, crossed with LEARNED geometry, recover useful concern
  from the wrong prior with adequate coverage, beat every generic
  value/priority/recency/wrong-agent signal at matched information, and
  survive the split-budget ablation `k_split_care_uncertain_audit` on
  every family?

Wave 1b **can reject** either claim. Wave 1b **cannot** establish semantic
meaning, selfhood, transferable retrieval principle (L3), external agent
validity (L4), or a cognitive/self-model interpretation (L5). Those are
Wave 3+ objects.

Per the roadmap and Wave 1a promotion contract, a Wave 1a KILL does not
block Wave 1b's L1 rows. Wave 1a's E2a KILL withholds L2 but does not
invalidate an independently supported L1 result.

## What Wave 1a's KILL fixed and what Wave 1b inherits

Wave 1a KILLed on two orthogonal problems:

1. **G1 coverage floor breach** on `delayed_commitments`
   (`coverage = 0.000 < 0.01`).
2. **G3 specificity family-design confound** on all three families:
   `info_matched_recency` reproduced the oracle ceiling byte-for-byte
   (0.5315 / 0.4772 / 0.6000).

Wave 1b closes (2) with the **family redesigns** in
[`PREREGISTRATION.md`](PREREGISTRATION.md) §4: load-bearing memories are
placed at a random non-recent position on at least 50% of episodes; a
pre-run assertion refuses to run confirmatory rows if
`oracle_recall_at_k(s) >= 0.8` for any generic-signal baseline `s` on any
family. Wave 1b closes (1) with the split-budget ablation in
[`PREREGISTRATION.md`](PREREGISTRATION.md) §8 and by keeping
`LoggedProbePolicy.epsilon` inside the Wave 1a replayable range
`[0.05, 0.10]` for L2 rows only. L1 rows are frozen-wrong on the concern
axis and are not affected by (1).

## Reuse boundary

Every numerical primitive, sealed-environment interface, template-split
guard, off-policy estimator, and baseline callable is imported from
Wave 0 or Wave 1a. Wave 1b introduces:

1. **`arms.py`** — the 3 x 3 x 3 crossed-arm runner (geometry axis in
   `{LEARNED, FREQ_MATCHED_RANDOM, ORACLE_WITHHELD}` x concern axis in
   `{FROZEN_WRONG, ONLINE_LEARNED, ORACLE}` x family axis in
   `{delayed_commitments, maintenance_fault, resource_constrained}`).
2. **`families/`** — redesigned generators with bundle planting
   (singletons, contradictory pairs, complementary pairs, dangerous
   conjunctions, isolation-distractors) and load-bearing-role
   cross-tabulation.
3. **`bundle_oracle.py`** — exhaustive-oracle enumeration of top-k SETS
   (all singletons, all pairs, feasibility-gated triples) that produces
   `oracle_top_k`, `oracle_regret_set`, `interaction_recovery`.
4. **`utility.py`** — the primary task utility
   `U(v) = Delta_task(v) + beta * S^phi(v) - gamma * constraint_violations(v)`
   with `beta`, `gamma` preregistered in
   [`PREREGISTRATION.md`](PREREGISTRATION.md) §6.
5. **`epiplexity.py`** — Zhang-Levin `S^phi = (1/2) log_2 det(I_m + eta W W^T)`,
   implemented via `SharedQREpiplexity` (shared augmented QR + batched
   right-hand-side solve + `det(I + eta W W^T) = det(I + eta W^T W)`
   identity, only valid when candidates share `X_tilde`) and
   `IndependentSolveEpiplexity` (per-candidate QR, GPU-batched, when
   `X_tilde` differs per candidate). The crossed-runner records which
   regime applies in [`PROVENANCE.md`](PROVENANCE.md).
6. **`ablations.py`** — the `k_split_care_uncertain_audit` labelled
   ablation with three splits (70/20/10, 50/30/20, 80/10/10). NOT the
   promotion path.
7. **`leakage_audit.py`** — the §7-required label-permutation and
   randomized-generator statistical leakage audit for the permitted
   graph features. Wave 1a implemented only the AST-level integrity
   guard; Wave 1b implements the statistical audit.
8. **`e2b_runner.py`** — the confirmatory-sweep entry point.
9. **`modal_l4_sweep.py`** — Modal L4 fan-out at
   `research-derived-cogr-wave1b-e2b`, up to 64 containers.

Wave 0 and Wave 1a objects Wave 1b imports and does not fork:

| Object | Source |
|---|---|
| `build_withheld_graph`, `apply_concern_warp`, `rarity_scores` | `wave0.graph_learn` |
| `LoggedProbePolicy`, `update_concern`, `ProbeReceipt` | `wave0.concern_update` |
| `SealedEnvironment`, `EpisodeSpec`, `EpisodeContext`, `SealedOutcome`, `IntegrityAudit`, `TemplateFamilySplit`, `ProceduralFamily`, `RetrievalChoice` | `wave0.sealed_env` |
| `TemplateRegistry`, `TemplateBucket`, `stable_template_id`, `assert_calibration_only`, `LeakageError` | `wave0.template_split` |
| `BASELINES`, `match_budget`, `promotion_admit`, `CANDIDATE_MECHANISM_PARAM_COUNT`, `learned_one_stage_parameter_count`, every rank callable in the slate | `wave0.baselines` |
| Family generators (`generate_delayed_commitments`, `generate_maintenance_fault`, `generate_resource_constrained`) — used as SHAPE PRIOR only; Wave 1b's `families/` module wraps them with bundle planting and non-recent load-bearing placement | `wave0.families.*` |
| Wave 1a five-condition sweep infrastructure | `wave1a.conditions`, `wave1a.coverage_audit`, `wave1a.specificity` — inherited as receipts, not re-executed |

## Layout

```
wave1b/
├── README.md                    # this file
├── PREREGISTRATION.md           # crossed-factorial design; unsigned until analysis-code hash lands
├── PROMOTION_CONTRACT_L1.md     # L1-gate promotion contract (representation contribution)
├── PROMOTION_CONTRACT_L2.md     # L2-gate promotion contract (concern recovery + specificity)
├── PROVENANCE.md                # skeleton; Modal run receipts fill it in
└── __init__.py                  # scope-boundary docstring
```

Implementation modules (`arms.py`, `families/`, `bundle_oracle.py`,
`utility.py`, `epiplexity.py`, `ablations.py`, `leakage_audit.py`,
`e2b_runner.py`, `modal_l4_sweep.py`, `results/`) are added by follow-up
Wave 1b build tasks and are governed by this preregistration.

## Anti-leakage contract inheritance and extension

Wave 1b inherits the Wave 0 anti-leakage contract in
[`../wave0/PREREGISTRATION.md`](../wave0/PREREGISTRATION.md) §4 and the
Wave 1a inheritance clauses in
[`../wave1a/PREREGISTRATION.md`](../wave1a/PREREGISTRATION.md) §5.5, and
adds:

- **Statistical leakage audit (roadmap §7 requirement).** Every
  permitted graph feature used by learned geometry is subjected to a
  label-permutation control and a randomized-generator control. If the
  audit fires, KILL. This is stronger than the Wave 1a AST-level
  guard.
- **Bundle-aware anti-leakage.** Bundle labels (`singleton`,
  `contradictory_pair`, `complementary_pair`, `dangerous_conjunction`,
  `isolation_distractor`) are evaluator-only and reachable only through
  the exhaustive-oracle enumeration path in the evaluator; they are
  never returned to policy code.
- **Interaction-recovery receipt.** Recovered by the evaluator from
  sealed outcomes, not by the policy.

Wave 1b runs with `COGR_WAVE0_CONFIRMATORY_RUN=1` set at Modal spawn
time. Calibration seeds (`100000..100999`) remain unreachable.

## Ownership and change control

This subtree is authoritative for the L1 representation-contribution
verdict and the L2 concern-recovery-and-specificity verdict of the
COGR-E2 program. Any change to `PREREGISTRATION.md`,
`PROMOTION_CONTRACT_L1.md`, `PROMOTION_CONTRACT_L2.md`, or the
analysis-code hash mirror in `PROVENANCE.md` must accompany a redesign
justification recorded in the change log. No post-hoc corpus swap,
threshold swap, seed-range swap, family swap, or condition swap is
permitted after the analysis-code hash is written. See the honor-the-
preregistration rule in the human director's memory (feedback-honor-pre-
registration).

If Wave 1b's confirmatory receipt is a KILL on either L1 or L2, the
KILL paper is written honestly. No post-hoc threshold swaps to escape a
bad verdict.
