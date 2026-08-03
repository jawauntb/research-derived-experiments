import StructuralIntelligenceMathlib.Theorem5Rate
import StructuralIntelligenceMathlib.AG1Survival
import StructuralIntelligenceMathlib.CT2MonotoneReward
import StructuralIntelligenceMathlib.Theorem1MinimalSufficiency
import StructuralIntelligenceMathlib.Theorem2RateDistortion
import StructuralIntelligenceMathlib.Proposition3Adjunction

/-!
# Structural Intelligence — Mathlib companion project

The Mathlib-backed counterpart to the pure-core Lean project at
`formal/structural-intelligence/`.  This project imports Mathlib and
formalises the three real-analytic theorems from the Structural
Intelligence programme that the pure-core project intentionally
deferred:

* `StructuralIntelligenceMathlib.theorem5_rate_bound` and
  `StructuralIntelligenceMathlib.one_sub_inv_pow_le_exp_neg_div` —
  the quantitative sample-complexity rate behind Theorem 5:
  `N ≥ c·M·log(M/ε)  ⇒  M·exp(-N/(c·M)) ≤ ε`, plus the elementary
  binomial-to-exponential bridge
  `(1 - 1/(c·M))^N ≤ exp(-N/(c·M))`.

* `StructuralIntelligenceMathlib.ag1_survival_lower_bound` and
  `StructuralIntelligenceMathlib.ag1_joint_survival` — the AG-1
  survival bound: Bernoulli's inequality `(1-β)^T ≥ 1 - T·β` for
  `β ∈ [0, 1]`, plus the arithmetic product-of-conditionals step
  giving `∏ s t ≥ (1-β)^T` when each conditional survival `s t` lies
  in `[1-β, 1]`.

* `StructuralIntelligenceMathlib.ct2_covariance_nonneg` and
  `StructuralIntelligenceMathlib.ct2_boltzmann_raises_expected_reward`
  — the CT-2 monotone-reward core: the positive-correlation
  (Chebyshev-sum) inequality
  `E[r · exp(β·r)] ≥ E[r] · E[exp(β·r)]` for `β ≥ 0`, wrapped as
  "the Boltzmann-tilted distribution raises expected reward".

* `StructuralIntelligenceMathlib.IsSufficient_iff_likelihood_ratio_factors`,
  `StructuralIntelligenceMathlib.likelihoodRatioVector_sufficient`,
  `StructuralIntelligenceMathlib.exists_minimal_sufficient_finite_discrete`
  — **Theorem 1 (Halmos–Savage minimal sufficient statistic)**: the
  finite-discrete, positive-support case.  Sufficiency-iff-LR-factors
  is proved in full; the LR vector is proved sufficient; and the
  final "extend a partial function on the LR image to a total map"
  packaging step (`HalmosSavage_minimality_h_extension`) is
  axiomatised with an explicit citation to Halmos & Savage 1949.

* `StructuralIntelligenceMathlib.symChannel_mutualInfo_closed_form`
  and `StructuralIntelligenceMathlib.R_D_uniform_hamming` —
  **Theorem 2 (Shannon rate–distortion, uniform-Hamming closed
  form)**: the achievability half (symmetric error-`D` channel
  attains `I(X; X̂) = log n - h_binary(D) - D · log(n − 1)`) is
  proved.  The converse
  (`Shannon1959_converse_uniform_hamming`) is axiomatised —
  Mathlib does not yet expose the Lagrangian / KKT infrastructure
  needed to close it internally.  Cited: Shannon 1959.

* `StructuralIntelligenceMathlib.R_C_unit`,
  `StructuralIntelligenceMathlib.C_R_counit`, and
  `StructuralIntelligenceMathlib.proposition3_adjunction`
  — **Proposition 3 (Coarsen ⊣ Refine)**: both triangle identities
  of the categorical adjunction between pushforward-along-quotient
  and pullback-along-kernel in the finite discrete category of
  distributions.  Fully proved, no axioms.

Why a separate project?  Mathlib introduces a heavy build (10–15 min
first fetch) that would slow the pure-core CI job which currently
compiles in seconds.  Keeping the two projects isolated lets the fast
lane stay fast while this project takes on the real-analysis work.
-/

-- Headline axiom footprints.
#print axioms StructuralIntelligenceMathlib.theorem5_rate_bound
#print axioms StructuralIntelligenceMathlib.one_sub_inv_pow_le_exp_neg_div
#print axioms StructuralIntelligenceMathlib.ag1_survival_lower_bound
#print axioms StructuralIntelligenceMathlib.ag1_joint_survival
#print axioms StructuralIntelligenceMathlib.ct2_covariance_nonneg
#print axioms StructuralIntelligenceMathlib.ct2_boltzmann_raises_expected_reward
#print axioms StructuralIntelligenceMathlib.IsSufficient_iff_likelihood_ratio_factors
#print axioms StructuralIntelligenceMathlib.likelihoodRatioVector_sufficient
#print axioms StructuralIntelligenceMathlib.exists_minimal_sufficient_finite_discrete
#print axioms StructuralIntelligenceMathlib.symChannel_mutualInfo_closed_form
#print axioms StructuralIntelligenceMathlib.symChannel_expected_hamming
#print axioms StructuralIntelligenceMathlib.R_D_uniform_hamming
#print axioms StructuralIntelligenceMathlib.R_C_unit
#print axioms StructuralIntelligenceMathlib.C_R_counit
#print axioms StructuralIntelligenceMathlib.proposition3_adjunction
