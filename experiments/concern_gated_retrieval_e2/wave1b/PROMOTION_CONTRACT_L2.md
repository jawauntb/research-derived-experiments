# Wave 1b — PROMOTION CONTRACT L2 (concern recovery + specificity)

**Claim id:** `COGR-E2-WAVE1B-L2-CONCERN-RECOVERY`
**Scope:** L2 rows only. Blocked-by L1 passing AND family redesign
passing the recency-decoupling pre-run assertion.
**Non-compensatory:** true.

## Pre-condition (blocking)

Wave 1a E2a KILLed under Wave 0's family design. L2 rows in Wave 1b run
iff both of:

1. Wave 1b PREREGISTRATION §4 pre-run assertion passes on every family
   (`oracle_recall_at_k(s) < 0.8` for every generic-signal baseline s,
   `recency_load_bearing_corr < 0.5`, `interaction_recovery(s) < 0.5`
   on planted complementary pairs).
2. Wave 1b PROMOTION_CONTRACT_L1 reports PASS on the L1 rows for the
   corresponding geometry × family cell.

If either fails, L2 is withheld and the paper reports so. L2 cannot
paper over an L1 KILL.

## Frozen constants

* `beta = 0.0` (Δ_task-only for the L2 gate)
* `gamma = 1.0`
* `k = 3` retrieval budget
* Per-family L2 thresholds — paired-seed variance from the crossed
  cells, calibrated at signature time from the confirmatory rows'
  frozen-wrong arm.

## Gates (must ALL pass on every family)

| Gate | Requirement |
|---|---|
| G0 integrity | (as L1) |
| G3 L2_recovery | Online-updated concern reduces oracle-distance vs the frozen-wrong prior with valid IPS/DR propensity accounting on every family |
| G4 L2_specificity | Online-learned concern beats every information-matched generic signal (value/priority/recency/salience) AND the wrong-agent profile on every family, on the paired-seed metric |
| G5 non_ceiling | (as L1) |
| G6 bundle_awareness | (as L1); additionally, the online-updated concern must recover ≥ 1 complementary pair per family that the frozen-wrong prior does not |
| G7 adversarial | Targeted single-source poisoning at the wave0-registered influence bound does not drive an undetected recovery reversal |
| G8 robustness | (as L1) |

## Promotion rule

L2 promoted iff L1 is promoted, the §4 pre-run assertion passes, every
gate above reports PASS on every family, and `WAVE1B_ANALYSIS_HASH` is
mirrored correctly.

## Demotion rule

(As L1.) An L2 row scored against a threshold produced under any
violated G0–G9 gate is retroactively demoted; downstream claims that
cite L2 (Wave 2 continuation on the concern-recovery path, Wave 3 L3
transfer on the recovery path) are marked non-evidence.
