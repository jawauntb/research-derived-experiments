# E1 Follow-up — Misspecification Variance Quantification

Preregistration: `papers/commitment_surface/e1_misspecification_variance_preregistration_2026-07-09.md`

## Result

- Verdict: **CONSISTENT_WITH_RANDOM_ASSIGNMENT_VARIANCE**
- Original observed gap: `-0.054159416947479`
- Reconstructed original gap: `-0.054159416947479`
- Null replicates: 2048 over 96 frozen cells
- Null mean gap: -0.058864
- Null variance: 0.000259200
- Null SD: 0.016100
- 95% CI for null mean: [-0.059561, -0.058167]
- `P(null gap <= observed)`: 0.620117 (1270/2048); Wilson 95% CI [0.598890, 0.640895]

The original frozen ±0.05 sub-gate remains a strict failure. The follow-up gate only decides whether that failed realization is surprising under independent marginal-preserving reassignment.

## Null quantiles

| Quantile | Gap |
|---:|---:|
| 0.5% | -0.100315 |
| 2.5% | -0.091310 |
| 5.0% | -0.086249 |
| 50.0% | -0.058614 |
| 95.0% | -0.033478 |
| 97.5% | -0.029364 |
| 99.5% | -0.019041 |

## Per-modulus null distribution

| Modulus | Observed | Mean | SD | 2.5% | Median | 97.5% | Lower-tail P |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 7 | -0.074337 | -0.073724 | 0.030726 | -0.132576 | -0.073390 | -0.015234 | 0.493164 |
| 11 | -0.066644 | -0.076804 | 0.027577 | -0.130352 | -0.076485 | -0.023632 | 0.644531 |
| 13 | -0.021497 | -0.026065 | 0.026539 | -0.077601 | -0.026112 | 0.025149 | 0.570801 |

## Independence and exchangeability audit

- `observed_gap_reconstruction_matches`: **PASS**
- `structure_invariant`: **PASS**
- `assignment_cardinality_preserved`: **PASS**
- `derived_assignment_seeds_unique`: **PASS**
- `independent_of_candidate_coverage_by_construction`: **PASS**
- `exchangeable_fixed_cardinality_by_construction`: **PASS**
- `max_abs_position_inclusion_z_le_5`: **PASS**
- `abs_hypergeometric_overlap_z_le_4`: **PASS**
- `abs_lag1_gap_autocorrelation_le_0p10`: **PASS**

- Maximum absolute position-inclusion z: 3.768
- True-focus overlap: observed 692746.0, expected 692538.5, z=0.330
- Lag-1 aggregate-gap autocorrelation: -0.0016
- Inclusion-rate correlation with candidate coverage: -0.0013
- Inclusion-rate correlation with true-focus membership: 0.0096

Weights are exchangeable, not iid, within an assignment; equal coordinate marginals are the corollary requirement.

Candidate pools and C_star are frozen before namespaced RNG seeds draw misspecified focus positions.

## Claim boundary

This conditional randomization test diagnoses the frozen E1 candidate pools and deployments. It does not establish equivalence in other candidate families, and it does not turn the original gate into a pass. The score-level in-expectation identity does not imply equality after nonlinear argmax selection.
