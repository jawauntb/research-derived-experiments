import StructuralIntelligenceMathlib.Theorem5Rate
import StructuralIntelligenceMathlib.AG1Survival
import StructuralIntelligenceMathlib.CT2MonotoneReward
import StructuralIntelligenceMathlib.Theorem1MinimalSufficiency
import StructuralIntelligenceMathlib.Theorem2RateDistortion
import StructuralIntelligenceMathlib.ShannonFano
import StructuralIntelligenceMathlib.Proposition3Adjunction
import StructuralIntelligenceMathlib.CG1FisherMatrix
import StructuralIntelligenceMathlib.CG2Holonomy
import StructuralIntelligenceMathlib.AA1MonotoneCompetence
import StructuralIntelligenceMathlib.SICA_FiniteExistence
import StructuralIntelligenceMathlib.SICC_CoveringMeta
import StructuralIntelligenceMathlib.WeaknessPACBayes

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
  **proved** (same `Classical.choose` packaging as the forward
  direction of the characterisation; no project-local axiom).
  Cited: Halmos & Savage 1949.

* `StructuralIntelligenceMathlib.symChannel_mutualInfo_closed_form`
  and `StructuralIntelligenceMathlib.R_D_uniform_hamming` —
  **Theorem 2 (Shannon rate–distortion, uniform-Hamming closed
  form)**: the achievability half (symmetric error-`D` channel
  attains `I(X; X̂) = log n - h_binary(D) - D · log(n − 1)`) is
  proved.  The `D = 0` converse
  (`Shannon1959_converse_D_zero`) is proved (zero Hamming forces
  a diagonal kernel).  The `0 < D` converse
  (`Shannon1959_converse_uniform_hamming`) is proved by Fano plus
  Jensen on binary entropy plus monotonicity of Mathlib's
  `qaryEntropy n` on `[0, 1 - 1/n]` — not KKT.  Cited: Shannon 1959.

* `StructuralIntelligenceMathlib.R_C_unit`,
  `StructuralIntelligenceMathlib.C_R_counit`, and
  `StructuralIntelligenceMathlib.proposition3_adjunction`
  — **Proposition 3 (Coarsen ⊣ Refine)**: both triangle identities
  of the categorical adjunction between pushforward-along-quotient
  and pullback-along-kernel in the finite discrete category of
  distributions.  Fully proved, no axioms.

* `StructuralIntelligenceMathlib.cg1_logpartition_deriv_eq_meanT`,
  `StructuralIntelligenceMathlib.cg1_score_identity_scalar`,
  `StructuralIntelligenceMathlib.cg1_fisher_matrix_eq_covariance` —
  **Theorem CG-1 (Fisher information = covariance of sufficient
  statistic)**: for the finite-support exponential family
  `p_θ(x) = h(x) · exp(⟨θ, T(x)⟩ - A(θ))`, the log-partition
  derivative equals the mean sufficient statistic (`A'(θ) = E[T]`);
  the derivative of `log p_θ(x)` at each sample equals the centered
  sufficient statistic `T(x) - E[T]` (score identity); and the
  Fisher information matrix `I(θ)_{ij}` equals the covariance
  matrix `Cov[T_i, T_j]`.  No axioms.

* `StructuralIntelligenceMathlib.cg2_holonomy_equals_signed_area`,
  `StructuralIntelligenceMathlib.cg2_discrete_greens_grid`,
  `StructuralIntelligenceMathlib.cg2_boundary_riemann_equals_area` —
  **Theorem CG-2 (concern holonomy = enclosed signed area)**: the
  paper §4 non-exact concern 1-form `α = -ε · c_2 · dc_1` has
  holonomy exactly `ε · w · h` around any counterclockwise
  rectangular loop with side-lengths `w, h`, and the finite
  Riemann-sum discretisation on an `N × M` grid reproduces this
  value exactly (`Finset.sum_comm` + telescoping).  No axioms.

* `StructuralIntelligenceMathlib.aa1_log_mixture_ge_weighted_log`,
  `StructuralIntelligenceMathlib.aa1_log_mixture_ge_weighted_log_sample`,
  `StructuralIntelligenceMathlib.aa1_refinement_raises_lower_bound`
  — **Theorem AA-1 (Bayes-mixture predictive log-likelihood
  dominates the prior-weighted per-hypothesis log-mean)**: finite
  concave-log Jensen inequality
  `∑ π_i · log p_i ≤ log(∑ π_i · p_i)` for any positive
  hypothesis-likelihood family and any finite prior — the arithmetic
  core of the Barron 1998 audience-competence bound.  No axioms.

* `StructuralIntelligenceMathlib.sic_a_finite_discrete` and
  `StructuralIntelligenceMathlib.sic_a_finite_discrete_coarsest` —
  **SIC-A derived in the finite discrete positive-support case**
  (companion paper: `papers/structural_intelligence_foundations/`).
  Composes Theorem 1 (LR-vector as `q`) with Proposition 3's
  fibre-supported / fibre-normalised kernel construction (uniform-on-
  fibre `K`) to *derive* the master fibration `(q, K)` — reducing SIC-A
  from a posit to a theorem in the finite discrete positive-support
  case.  Coarsestness is inherited from T1's minimality
  (`HalmosSavage_minimality_h_extension` is now a theorem; no
  project-local axiom remains on this path).

* `StructuralIntelligenceMathlib.sicc_covering_meta` and
  `StructuralIntelligenceMathlib.sicc_covering_poly` —
  **SIC-C-c covering meta-theorem (conditional)**: for any inductive-
  bias hypothesis class `H` with ε-covering number `K` (resp.
  `N(ε, H) ≤ f(1/ε)`), the sample complexity to recover the minimally
  sufficient fibration on the finite ε-cover at accuracy ε with
  confidence `1 − δ` is `N ≥ c · K · log(K/δ)` (resp.
  `N ≥ c · f(1/ε) · log(f(1/ε)/δ)`).  Composition of
  `theorem5_rate_bound` (quantitative rate on the finite cover) with
  the pure-core ε-covering reduction
  `StructuralIntelligence.refinement_preserves_screen`.  The
  precondition — polynomial covering number `N(ε, H)` — separates
  "H for which SIC-C-c holds" (poly-covered classes: linear ICA,
  sparse-linear ICA, iVAE, interventional CRL) from
  "H for which SIC-C-c provably fails" (Locatello 2019: fully-
  unsupervised nonlinear ICA is exponentially-covered).  No new axioms
  beyond those already used by `theorem5_rate_bound`.

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
#print axioms StructuralIntelligenceMathlib.HalmosSavage_minimality_h_extension
#print axioms StructuralIntelligenceMathlib.symChannel_mutualInfo_closed_form
#print axioms StructuralIntelligenceMathlib.symChannel_expected_hamming
#print axioms StructuralIntelligenceMathlib.Shannon1959_converse_D_zero
#print axioms StructuralIntelligenceMathlib.Shannon1959_converse_uniform_hamming
#print axioms StructuralIntelligenceMathlib.R_D_uniform_hamming
#print axioms StructuralIntelligenceMathlib.R_C_unit
#print axioms StructuralIntelligenceMathlib.C_R_counit
#print axioms StructuralIntelligenceMathlib.proposition3_adjunction
#print axioms StructuralIntelligenceMathlib.cg1_logpartition_deriv_eq_meanT
#print axioms StructuralIntelligenceMathlib.cg1_score_identity_scalar
#print axioms StructuralIntelligenceMathlib.cg1_fisher_matrix_eq_covariance
#print axioms StructuralIntelligenceMathlib.cg1_fisher_eq_variance
#print axioms StructuralIntelligenceMathlib.cg2_holonomy_equals_signed_area
#print axioms StructuralIntelligenceMathlib.cg2_discrete_greens_grid
#print axioms StructuralIntelligenceMathlib.cg2_boundary_riemann_equals_area
#print axioms StructuralIntelligenceMathlib.aa1_log_mixture_ge_weighted_log
#print axioms StructuralIntelligenceMathlib.aa1_log_mixture_ge_weighted_log_sample
#print axioms StructuralIntelligenceMathlib.aa1_refinement_raises_lower_bound
#print axioms StructuralIntelligenceMathlib.sic_a_finite_discrete
#print axioms StructuralIntelligenceMathlib.sic_a_finite_discrete_coarsest
#print axioms StructuralIntelligenceMathlib.sicc_covering_meta
#print axioms StructuralIntelligenceMathlib.sicc_covering_poly
#print axioms StructuralIntelligenceMathlib.weakness_kl_certificate
#print axioms StructuralIntelligenceMathlib.lsm_plug_certificate
#print axioms StructuralIntelligenceMathlib.weakness_lsm_bound
