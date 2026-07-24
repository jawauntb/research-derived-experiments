# Wave 1b — PROMOTION CONTRACT L1 (representation contribution)

**Claim id:** `COGR-E2-WAVE1B-L1-DUAL-SOURCE-RETRIEVAL`
**Scope:** L1 rows only. Independent of L2. Concern-recovery failure in
E2a does not block this contract.
**Non-compensatory:** true.

## Frozen constants

* `beta = 0.0` (Δ_task-only for the L1 gate)
* `gamma = 1.0`
* `k = 3` retrieval budget
* Per-family L1 thresholds — see [`PREREGISTRATION.md §11`](PREREGISTRATION.md#11-frozen-thresholds).

## Gates (must ALL pass on every family)

| Gate | Requirement |
|---|---|
| G0 integrity | IntegrityAudit clean; sealed evaluator accessed exactly once per (episode, policy-choice); template-split guard clean |
| G1 L1_behavior | Candidate mechanism paired-seed lower bound `Δ_task − 2σ ≥ delta_thresh_L1` on every family AND strictly dominates every matched-budget baseline on `oracle_recall_at_k` AND on `simple_regret_set` |
| G2 L1_representation | On the learned-geometry cells, ablating the top-scoring learned edge changes downstream `Δ_task` in the predicted direction on ≥ 70% of episodes |
| G5 non_ceiling | Every family's best matched baseline sits `≥ 0.05` below the oracle ceiling |
| G6 bundle_awareness | ≥ 1 complementary pair recovered per family per 300 seeds AND ≥ 90% dangerous-conjunction avoidance per family |
| G8 robustness | No family-level reversal hidden by aggregate |
| G9 leakage_audit | Label-permutation and randomized-generator controls both within tolerance |

## Promotion rule

L1 promoted iff every gate above reports PASS on every family AND
`WAVE1B_ANALYSIS_HASH` matches between `PREREGISTRATION.md §13` and
`PROVENANCE.md §6`.

## Demotion rule

If any post-signature audit discovers a Wave 1b L1 row scored against a
threshold populated from a calibration or replay row that violated any
G0–G9 gate, the L1 verdict is retroactively demoted to `REDESIGN`. All
downstream claims (Wave 2 continuation, Wave 3 L3 transfer) that cite
L1 are marked non-evidence. No post-hoc threshold swap is permitted.
