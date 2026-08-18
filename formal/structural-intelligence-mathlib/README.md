# Structural Intelligence Lean 4 Proofs — Mathlib companion

Machine-checked artifact for the three **real-analytic** theorems from
the *Structural Intelligence* programme that the pure-core companion
project at `formal/structural-intelligence/` intentionally deferred to
"Mathlib territory".

The pure-core project uses no dependencies beyond Lean core and
compiles in seconds; the algebraic content of Theorems 4, 5-union-bound,
5-pigeonhole, 6-refinement, CT-1, CS-1/2, SA-1, AF-1/2, AG-2, TA-1,
RR-2, AA-2 lives there.  This project imports `mathlib`, which brings
in real numbers, `exp`, `log`, monotonicity, and finite-sum machinery
that the pure-core project cannot see.

## Pure-core vs. Mathlib split

| Project                                | Depends on          | Theorems                                                                                 |
| -------------------------------------- | ------------------- | ---------------------------------------------------------------------------------------- |
| `formal/structural-intelligence/`      | Lean 4 core only    | Algebraic cores: Theorems 4, 5-union-bound, 5-pigeonhole, 6-refinement, CT-1, CS-1/2, SA-1, AF-1/2, AG-2, TA-1, RR-2, AA-2 |
| `formal/structural-intelligence-mathlib/` (this)  | Lean 4 + mathlib    | Real-analytic: Theorem 5 quantitative rate, AG-1 survival bound, CT-2 monotone-reward core, Theorem 1 (Halmos–Savage minimal sufficient statistic), Theorem 2 (Shannon rate–distortion, uniform-Hamming closed form), Proposition 3 (Coarsen ⊣ Refine adjunction), Theorem CG-1 (Fisher information = covariance of sufficient statistic), Theorem CG-2 (concern holonomy = enclosed signed area), Theorem AA-1 (Bayes-mixture predictive log-likelihood lower bound), **SIC-A derived in the finite discrete positive-support case**, **SIC-C-c covering meta-theorem (conditional)**, **WI compatibility-indexed KL certificate (LSM cited, not proved)** |

Keeping the two projects separate lets the fast Lean CI job stay fast
(around three seconds) while this project takes on the multi-minute
mathlib build in an isolated CI lane.

## Toolchain

* Lean: `leanprover/lean4:v4.32.2`
* mathlib: `v4.32.2` (pinned via `lakefile.toml`)

## What is formalized

### Theorem 5 quantitative rate — `StructuralIntelligenceMathlib/Theorem5Rate.lean`

* `StructuralIntelligenceMathlib.theorem5_rate_bound` — **quantitative
  sample-complexity rate**.  Given natural `M ≥ 1`, real `c ≥ 1`,
  real `ε ∈ (0, 1)`, and real `N` with `N ≥ c · M · log (M / ε)`,

  ```
  (M : ℝ) * Real.exp (- N / (c * M)) ≤ ε.
  ```

  Proof: take `log` of both sides, use `le_div_iff₀'` to convert the
  hypothesis into `log (M/ε) ≤ N/(c·M)`, negate to
  `-N/(c·M) ≤ log (ε/M)`, exponentiate via `Real.exp_le_exp`, and
  multiply by `M > 0`.

* `StructuralIntelligenceMathlib.one_sub_le_exp_neg_pow` — the
  general elementary bridge `(1 - x)^N ≤ exp(-N·x)` for
  `x ∈ [0, 1]` and any `N : ℕ`.  Proof: apply `Real.add_one_le_exp`
  at `-x` to get `1 - x ≤ exp(-x)`, raise both nonneg sides to the
  `N`-th power via `pow_le_pow_left₀`, then fold with
  `Real.exp_nat_mul`.

* `StructuralIntelligenceMathlib.one_sub_inv_pow_le_exp_neg_div` — the
  Theorem-5 specialisation `(1 - 1/(c·M))^N ≤ exp(-N/(c·M))` at
  `x = 1/(c·M)` for `c ≥ 1`, `M ≥ 1`.  Combines directly with the
  union bound formalised in the pure-core companion project to close
  the quantitative half of Theorem 5.

### AG-1 survival bound — `StructuralIntelligenceMathlib/AG1Survival.lean`

* `StructuralIntelligenceMathlib.ag1_survival_lower_bound` —
  **Bernoulli's inequality** for `β ∈ [0, 1]`:

  ```
  1 - T · β ≤ (1 - β) ^ T.
  ```

  Obtained from mathlib's `one_add_mul_le_pow` (the `-2 ≤ a` version
  from `Mathlib.Algebra.Order.Ring.Pow`) applied at `a = -β`, which
  satisfies `-2 ≤ -β` because `β ≤ 1`.

* `StructuralIntelligenceMathlib.ag1_joint_survival` — arithmetic
  product step.  If each per-step conditional survival probability
  `s t ∈ [1 - β, 1]`, then

  ```
  (1 - β)^T ≤ ∏ t : Fin T, s t.
  ```

  Proof: monotonicity of `Finset.prod_le_prod` for nonneg reals,
  after rewriting `(1 - β)^T` as `∏ _t : Fin T, (1 - β)` via
  `Fin.prod_const`.  This is exactly the product-of-conditionals
  form of the joint survival bound `Pr[q(X_t) ∈ V for all t < T] ≥ (1 - β)^T`
  under a Markov-chain reading; no measure-theoretic scaffold is
  needed because the input is stated at the level of the numeric
  factors.

* `StructuralIntelligenceMathlib.ag1_joint_survival_linear` —
  convenience corollary combining the two above:
  `1 - T · β ≤ ∏ t, s t`.

### CT-2 monotone-reward core — `StructuralIntelligenceMathlib/CT2MonotoneReward.lean`

* `StructuralIntelligenceMathlib.chebyshev_weighted_correlation` — the
  **weighted Chebyshev sum inequality** (a.k.a. weighted
  positive-correlation inequality): for nonneg weights `w` and any
  two comonotonic functions `f`, `g`,

  ```
  (∑ w_i · f_i) · (∑ w_i · g_i)  ≤  (∑ w_i) · (∑ w_i · f_i · g_i).
  ```

  Proved from first principles by expanding
  `∑_{i,j} w_i w_j (f_i - f_j)(g_i - g_j) ≥ 0` (each summand is
  nonneg by comonotonicity) and identifying the four resulting
  sums.  Mathlib's built-in `MonovaryOn.sum_mul_sum_le_card_mul_sum`
  gives the unweighted form; the weighted version is more useful
  here so it is stated directly.

* `StructuralIntelligenceMathlib.exp_beta_comonotone` — the
  comonotonicity input for CT-2: for `β ≥ 0`, the pair
  `(r_i, exp(β·r_i))` is comonotone
  (`(r_i - r_j)(exp(β·r_i) - exp(β·r_j)) ≥ 0`).  Uses
  `Real.exp_le_exp` for monotonicity of `exp`.

* `StructuralIntelligenceMathlib.ct2_covariance_nonneg` — the
  Chebyshev/positive-correlation inequality specialised to
  `f = r`, `g = exp(β·r)`:

  ```
  (∑ p_i · r_i) · (∑ p_i · exp(β·r_i))
    ≤ (∑ p_i) · (∑ p_i · r_i · exp(β·r_i)).
  ```

* `StructuralIntelligenceMathlib.ct2_boltzmann_raises_expected_reward`
  — the CT-2 monotone-reward wrapper.  For a finite probability
  distribution `p` (`∑ p_i = 1`), bounded reward `r`, inverse
  temperature `β ≥ 0`, and Boltzmann normaliser
  `Z := ∑ p_i · exp(β · r_i) > 0`, the Boltzmann-tilted
  distribution `p'(x) := p(x) · exp(β · r(x)) / Z` has expected
  reward at least `E_p[r]`:

  ```
  (∑ p_i · r_i) ≤ (∑ p_i · r_i · exp(β · r_i)) / Z.
  ```

### Theorem 1 (Halmos–Savage minimal sufficient statistic) — `StructuralIntelligenceMathlib/Theorem1MinimalSufficiency.lean`

* `StructuralIntelligenceMathlib.IsSufficient` — the pmf
  cross-multiplication form of Fisher–Neyman factorisation
  sufficiency: for every parameter pair `θ, θ'` and every sample pair
  `x, x'` with `T x = T x'`,

  ```
  P θ x · P θ' x'  =  P θ x' · P θ' x.
  ```

* `StructuralIntelligenceMathlib.IsMinimalSufficient` — the standard
  Halmos–Savage direction: `T` is minimal sufficient iff every other
  sufficient `T'` refines it, i.e., `T x = h (T' x)` for some `h`.

* `StructuralIntelligenceMathlib.IsSufficient_iff_likelihood_ratio_factors`
  — **the classical characterisation, proved in full**.  Under strict
  positivity of every `P θ`, `T` is sufficient iff for every
  parameter pair the likelihood ratio `P θ · / P θ' ·` factors
  through `T`.  Forward direction uses `Classical.choose` to select a
  representative per fibre; reverse direction is direct
  cross-multiplication under positivity.

* `StructuralIntelligenceMathlib.likelihoodRatioVector` — the
  LR-vector statistic `x ↦ (fun θ => P θ x / P θ₀ x)` for a fixed
  pivot `θ₀`.

* `StructuralIntelligenceMathlib.likelihoodRatioVector_sufficient` —
  **the LR vector is sufficient**, proved directly by algebraic
  cross-multiplication.

* `StructuralIntelligenceMathlib.exists_minimal_sufficient_finite_discrete`
  — **Halmos–Savage existence theorem**: in the finite discrete
  positive-support case, the LR-vector against any fixed pivot is a
  minimal sufficient statistic.  Sufficiency is proved from scratch;
  the *minimality* half — "extend the partial function defined on
  the image of an arbitrary sufficient `T'` to a total function on
  `Θ → ℝ`" — is the proved lemma
  `StructuralIntelligenceMathlib.HalmosSavage_minimality_h_extension`
  with an inline citation to Halmos & Savage (1949), *Ann. Math.
  Statist.* 20, 225–241, Theorem 2.  No project-local axiom.

### Theorem 2 (Shannon rate–distortion, uniform-Hamming) — `StructuralIntelligenceMathlib/Theorem2RateDistortion.lean`

* `StructuralIntelligenceMathlib.binaryEntropy`,
  `StructuralIntelligenceMathlib.uniformDist`,
  `StructuralIntelligenceMathlib.symChannel`,
  `StructuralIntelligenceMathlib.hammingDistortion`,
  `StructuralIntelligenceMathlib.entropy`,
  `StructuralIntelligenceMathlib.condEntropy`,
  `StructuralIntelligenceMathlib.marginal`,
  `StructuralIntelligenceMathlib.mutualInfo`,
  `StructuralIntelligenceMathlib.expectedDistortion` — the entropy /
  channel / MI toolkit, hand-rolled on `Fin n` with mathlib's
  `log 0 = 0` convention absorbing zero-mass entries.

* `StructuralIntelligenceMathlib.symChannel_stochastic_row`,
  `StructuralIntelligenceMathlib.symChannel_stochastic_col` — the
  symmetric error-`D` channel is a doubly stochastic kernel.  Proof
  uses the add-subtract split trick + `Finset.sum_ite_eq`.

* `StructuralIntelligenceMathlib.symChannel_marginal_uniform` —
  receiver marginal under uniform source is uniform.

* `StructuralIntelligenceMathlib.symChannel_expected_hamming` — the
  symmetric error-`D` channel achieves expected Hamming distortion
  exactly `D`.  Proved.

* `StructuralIntelligenceMathlib.symChannel_row_entropy` — closed
  form for each row's entropy:
  `H(K(x, ·)) = h_binary(D) + D · log(n − 1)`.  Proved (the algebra
  reduces via `field_simp` + `ring` after unfolding
  `log (D/(n-1)) = log D - log(n-1)`).

* `StructuralIntelligenceMathlib.symChannel_mutualInfo_closed_form`
  — **achievability**: the symmetric error-`D` channel attains

  ```
  I(X; X̂)  =  log n  −  h_binary(D)  −  D · log (n − 1).
  ```

  Fully proved.

* `StructuralIntelligenceMathlib.Shannon1959_converse_D_zero` —
  the converse at distortion `0`, proved: expected Hamming `≤ 0`
  forces a diagonal kernel, so `I = log n`.

* `StructuralIntelligenceMathlib.Shannon1959_converse_uniform_hamming`
  — the `0 < D` converse, **proved** in `ShannonFano.lean` by Fano
  plus Jensen on binary entropy plus monotonicity of Mathlib's
  `qaryEntropy n` on `[0, 1 - 1/n]`.  No KKT.  Cited: C. E. Shannon
  (1959), *Coding theorems for a discrete source with a fidelity
  criterion*, IRE Nat. Conv. Rec., pt. 4, 142–163, Theorem 3.

* `StructuralIntelligenceMathlib.R_D_uniform_hamming` — the full
  Shannon 1959 statement (both directions).  No project-local axiom.

### WI PAC-Bayes certificate — `StructuralIntelligenceMathlib/WeaknessPACBayes.lean`

Honesty.  Proves the algebraic KL certificate from
`papers/weakness_invariance_neurips/pac_bayes_weakness_sketch.md`.
The Langford–Seeger–Maurer PAC-Bayes-kl inequality is **cited, not
proved** (Langford & Seeger, CMU-CS-01-102, 2001; Seeger, *JMLR*
3:233–269, 2002; Maurer, arXiv:cs/0411099, 2004).

* `StructuralIntelligenceMathlib.weakness_kl_certificate` —
  for a deterministic posterior `δ_h` and any `k ≤ W(h)` with
  `π_k > 0`, `−log P(h) ≤ log |H_{≥k}| − log π_k`.
* `StructuralIntelligenceMathlib.lsm_plug_certificate` — if the
  LSM numbers hold at `(klEmp, KL, m, extra)`, the certificate
  substitutes.  Not a proof of LSM.
* `StructuralIntelligenceMathlib.weakness_lsm_bound` — the
  certificate plugged into the LSM shape; `hLSM` is the citation
  and is not discharged.

`#print axioms` ⊆ `{propext, Classical.choice, Quot.sound}`.
No project-local axiom.  **Proved-not-verified.**

### Proposition 3 (Coarsen ⊣ Refine adjunction) — `StructuralIntelligenceMathlib/Proposition3Adjunction.lean`

* `StructuralIntelligenceMathlib.coarsen`,
  `StructuralIntelligenceMathlib.refine` — pushforward-along-`q` and
  fibrewise-integration-along-`K` on discrete distributions.

* `StructuralIntelligenceMathlib.FibreSupported`,
  `StructuralIntelligenceMathlib.FibreNormalised` — the two
  regularity conditions on the kernel `K` that make it a valid
  section of the quotient `q`.

* `StructuralIntelligenceMathlib.coarsen_refine_eq` — **the
  retraction identity `C ∘ R = id`**.  Proved by swapping the order
  of finite summation and using `Finset.sum_ite_eq'` to collapse the
  outer sum at the single `z' = z` term.

* `StructuralIntelligenceMathlib.R_C_unit` — **unit triangle
  identity**: `C (R (C μ)) = C μ`.  Direct consequence of the
  retraction identity applied to `ν := C q μ`.

* `StructuralIntelligenceMathlib.C_R_counit` — **counit triangle
  identity**: `R (C (R ν)) = R ν`.  Direct consequence of the
  retraction identity applied to `ν`, then reapplication of `R`.

* `StructuralIntelligenceMathlib.proposition3_adjunction` — both
  triangle identities packaged as a single conjunction — the object-
  level witness that `coarsen ⊣ refine` in the finite discrete
  distribution category.  **Zero axioms, zero `sorry`.**

### Theorem CG-1 (Fisher information = covariance of sufficient statistic) — `StructuralIntelligenceMathlib/CG1FisherMatrix.lean`

Theorem CG-1 from `papers/concern_as_fiber_geometry/paper.md`, §3.  For
a finite-support exponential family
`p_θ(x) = h(x) · exp(⟨θ, T(x)⟩ - A(θ))` on `Fintype α`, the Fisher
information matrix `I(θ)` equals the covariance of the sufficient
statistic under `p_θ`.

* `StructuralIntelligenceMathlib.expFamZ`,
  `StructuralIntelligenceMathlib.expFamA`,
  `StructuralIntelligenceMathlib.expFamP`,
  `StructuralIntelligenceMathlib.expFamMeanT`,
  `StructuralIntelligenceMathlib.expFamScore`,
  `StructuralIntelligenceMathlib.expFamFisher`,
  `StructuralIntelligenceMathlib.expFamVarT` — the 1D
  natural-parameter data: partition function, log-partition,
  density, mean, score, Fisher information, and variance of the
  sufficient statistic.  All `noncomputable`, all defined by
  `Finset.sum` over `Fintype α`.

* `StructuralIntelligenceMathlib.hasDerivAt_expFamZ` — the partition
  function is pointwise-differentiable with the natural under-the-sum
  derivative `∑ h(x) · T(x) · exp(θ · T(x))`.  Proof: apply
  `HasDerivAt.fun_sum` and chain `HasDerivAt.mul_const`,
  `HasDerivAt.exp`, `HasDerivAt.const_mul` term by term.

* `StructuralIntelligenceMathlib.cg1_logpartition_deriv_eq_meanT` —
  **the load-bearing analytic identity**.  Under `0 < Z(θ)`,
  `(∂/∂θ) log Z(θ) = E_{p_θ}[T]`.  Proof: apply `HasDerivAt.log` to
  the partition-function derivative, then reshape `Z'(θ) / Z(θ)` as
  `∑ p_θ(x) · T(x)` via `Finset.sum_div` and pointwise algebraic
  identity.

* `StructuralIntelligenceMathlib.cg1_score_identity_scalar` —
  **the score identity** in 1D natural-parameter form.  Under
  positive `h` and positive `Z` at every `θ'`,
  `(∂/∂θ') log p_{θ'}(x) |_{θ' = θ} = T(x) - E_{p_θ}[T]`.  Proof:
  decompose `log p_{θ'}(x) = log h(x) + θ' · T(x) - A(θ')` via
  `Real.log_div`, `Real.log_mul`, `Real.log_exp`, then differentiate
  each term using `hasDerivAt_const`, `HasDerivAt.mul_const`, and
  `cg1_logpartition_deriv_eq_meanT`.

* `StructuralIntelligenceMathlib.cg1_fisher_eq_variance` — 1D scalar
  form: `I(θ) = Var_{p_θ}[T]`.  Definitional once
  `expFamScore h T θ x = T(x) - E_{p_θ}[T]` is fixed; the
  substantive content is the score identity.

* `StructuralIntelligenceMathlib.expFamZk`,
  `StructuralIntelligenceMathlib.expFamPk`,
  `StructuralIntelligenceMathlib.expFamMeanTk`,
  `StructuralIntelligenceMathlib.expFamScorek`,
  `StructuralIntelligenceMathlib.expFamFisherMatrix`,
  `StructuralIntelligenceMathlib.expFamCovMatrix` — the multi-parameter
  `Fin k` versions of the same objects, with `⟨θ, T x⟩` implemented
  as `∑ i : Fin k, θ i · T x i`.

* `StructuralIntelligenceMathlib.cg1_fisher_matrix_eq_covariance` —
  **the matrix form the paper cites**: `I_{ij}(θ) = Cov_{p_θ}[T_i, T_j]`
  entry-wise, on `Fintype α` and `Fin k`.  Definitional after the
  score identity has fixed the definition of score; proved by
  `Finset.sum_congr` + `ring`.

* `StructuralIntelligenceMathlib.expFamScore_mean_zero` — auxiliary
  lemma: the score has mean zero under `p_θ`, from `∑ p_θ = 1` +
  linearity.  Not required by the main identity but useful for the
  Cov = raw-second-moment reformulation.

### Theorem CG-2 (concern holonomy = enclosed signed area) — `StructuralIntelligenceMathlib/CG2Holonomy.lean`

Theorem CG-2 from `papers/concern_as_fiber_geometry/paper.md`, §4.
For the paper's §4-corrected concern 1-form `α = -ε · c_2 · dc_1`
(the earlier `ε(z_2 dc_1 - z_1 dc_2)` form was exact and had zero
holonomy — a mistake caught by the instrument on first run), the
counterclockwise line integral around the rectangle
`[a, a+w] × [b, b+h]` equals `ε · w · h`, i.e., `ε` times the enclosed
signed area.

* `StructuralIntelligenceMathlib.holonomyRectangle` — the sum of the
  four edge line-integrals of `α = -ε · c_2 · dc_1`.  Horizontal
  edges give `∓ε · c_2 · w` (with `c_2` fixed and equal to `b` or
  `b + h`); vertical edges contribute zero since `α` has no `dc_2`
  component.

* `StructuralIntelligenceMathlib.cg2_holonomy_equals_signed_area` —
  the analytic identity `holonomyRectangle ε a b w h = ε · w · h`.
  Proof: `ring`.  The base-point `(a, b)` and the horizontal offset
  `b` all cancel — only the enclosed area matters.

* `StructuralIntelligenceMathlib.cg2_discrete_greens_grid` — the
  Riemann-sum "total curl" form.  On an `N × M` grid partition, the
  per-cell curl `ε · (w/N) · (h/M)` summed over all `N · M` cells
  equals `ε · w · h`.  Proof: collapse each inner sum via
  `Finset.sum_const` + `Finset.card_range` + `nsmul_eq_mul`, then
  cancel `N/N` and `M/M` using `div_self`.

* `StructuralIntelligenceMathlib.cg2_discrete_greens_symmetric` —
  square-grid corollary exhibiting `Finset.sum_comm` explicitly:
  swapping the two grid axes leaves the total curl invariant.

* `StructuralIntelligenceMathlib.cg2_bottom_edge_riemann`,
  `StructuralIntelligenceMathlib.cg2_top_edge_riemann`,
  `StructuralIntelligenceMathlib.cg2_boundary_riemann_equals_area`
  — the Riemann-sum boundary form: on an `N`-subdivided rectangle,
  bottom-edge Riemann sum evaluates to `-ε · b · w`, top-edge
  (reversed) to `ε · (b+h) · w`, and vertical edges to zero; total
  is `ε · w · h`, matching `cg2_discrete_greens_grid`.  This is the
  discrete Green's theorem for the paper's specific `α`.

### Theorem AA-1 (Bayes-mixture predictive log-likelihood lower bound) — `StructuralIntelligenceMathlib/AA1MonotoneCompetence.lean`

Theorem AA-1 from `papers/autocatalytic_artwork/paper.md`.  For a
finite prior `π : Fin n → ℝ` (nonneg, `∑ π = 1`) and a positive
family of component predictives `p : Fin n → ℝ`, the log of the
Bayes mixture `q = ∑ π_i · p_i` dominates the prior-weighted
per-component log-mean:

    log (∑ i, π i · p i)   ≥   ∑ i, π i · log (p i).

Under the sample-likelihood reading where `p_i(x_{1:T})` is the
per-hypothesis sample likelihood, the RHS is the prior-averaged
per-hypothesis log-likelihood and the LHS is the mixture predictive
log-likelihood; expectation under any generative distribution gives
the Barron-1998 audience-competence bound.

* `StructuralIntelligenceMathlib.aa1_log_mixture_ge_weighted_log` —
  the core inequality.  Proof: apply `ConcaveOn.le_map_sum`
  (`Mathlib.Analysis.Convex.Jensen`) to `Real.log` on `Set.Ioi 0`,
  using `strictConcaveOn_log_Ioi.concaveOn`; convert `π i • p i`
  to `π i * p i` via `smul_eq_mul`.

* `StructuralIntelligenceMathlib.aa1_log_mixture_ge_weighted_log_sample`
  — the sample-form specialisation, obtained by pointwise
  application of the core inequality at each fixed observation `x`.

* `StructuralIntelligenceMathlib.aa1_refinement_raises_lower_bound`
  — the monotonicity-under-refinement corollary.  If `π' i · log(p i)
  ≥ π i · log(p i)` for every hypothesis index (the operational
  "refinement puts more mass on higher-log-likelihood components"
  condition), then `∑ π i · log(p i) ≤ log(∑ π' i · p i)`.  Proof:
  `Finset.sum_le_sum` for the RHS-boost, then the core Jensen
  inequality closes to the mixture log-likelihood.

### SIC-A derived in the finite discrete positive-support case — `StructuralIntelligenceMathlib/SICA_FiniteExistence.lean`

Companion paper: `papers/structural_intelligence_foundations/paper.md`.
The Structural Intelligence Conjecture opens with SIC-A: the existence
of a master fibration `(q : X → Z, K : Z ⇝ X)` with
`supp K(·|z) ⊆ q⁻¹(z)`.  In the parent paper the fibration is
*posited*; this file **derives** SIC-A in the finite discrete
positive-support case by composing already-verified components.

* `StructuralIntelligenceMathlib.sic_a_finite_discrete` — **the derived
  SIC-A statement**.  Given a finite non-empty sample space `α`, a
  finite parameter set `Θ`, a strictly-positive pmf family
  `P : Θ → α → ℝ`, and any pivot `θ₀ ∈ Θ`, exhibits a finite target
  type `Z` (with `Fintype` and `DecidableEq` instances), a partition
  map `q : α → Z`, and a kernel `K : Z → α → ℝ` such that (a) `q` is
  sufficient for `P` (from Theorem 1's
  `likelihoodRatioVector_sufficient`), (b) `K` is fibre-supported
  (`K z x = 0` whenever `q x ≠ z`, from Proposition 3's side
  condition, made concrete for our uniform-on-fibre `K`), and (c) `K`
  is fibre-normalised on the image of `q` (`∑ x, K z x = 1` for every
  `z ∈ image(q)`, second-disjunct branch retained for signature
  honesty for `z ∉ image(q)`).  Construction: `q :=
  likelihoodRatioVector P θ₀`, `Z := image(q)` as a Finset-subtype of
  `(Θ → ℝ)`, `K(z, x) := |q⁻¹(z)|⁻¹` if `q x = z` else `0`.  Axiom
  footprint: `[propext, Classical.choice, Quot.sound]` — **zero new
  project-local axioms**.

* `StructuralIntelligenceMathlib.sic_a_finite_discrete_coarsest` — the
  minimality corollary.  The LR-vector-induced quotient is coarsest
  among common sufficient statistics — every other sufficient `T'`
  refines it.  Direct call to
  `exists_minimal_sufficient_finite_discrete`, so it *inherits*
  `HalmosSavage_minimality_h_extension` (now a theorem).  No
  project-local axiom introduced here.

### SIC-C-c covering meta-theorem (conditional) — `StructuralIntelligenceMathlib/SICC_CoveringMeta.lean`

Companion paper:
`papers/structural_intelligence_covering_learnability/paper.md`.
The parent paper posits SIC-C-c (uniform polynomial-in-`d_Z`
learnability of the minimally sufficient fibration `q`) as an
unconditional conjecture, then splits it *per inductive-bias class*
via Instruments 8–11.  This file **closes SIC-C-c conditionally** by
composing Theorem 5-rate (`theorem5_rate_bound`) with the pure-core
Theorem 6 ε-covering reduction
(`StructuralIntelligence.refinement_preserves_screen`):

* `StructuralIntelligenceMathlib.sicc_covering_meta` — for a
  hypothesis class with ε-covering number `K` (`K ≥ 1`), any sample
  count `N ≥ c · K · log(K / δ)` yields the family-level failure
  probability bound `K · exp(- N / (c·K)) ≤ δ`.  Direct call to
  `theorem5_rate_bound` with `M := K, ε := δ`.

* `StructuralIntelligenceMathlib.sicc_covering_poly` — packaging
  under the polynomial-covering hypothesis `N(ε, H) ≤ f(1/ε)`.  For
  `K ≤ f(1/ε)`, `N ≥ c · f(1/ε) · log(f(1/ε) / δ)` gives the same
  failure-probability bound.  Uses log-monotonicity
  (`Real.log_le_log`) and `div_le_div_of_nonneg_right` to chain
  `c · K · log(K/δ) ≤ c · f(1/ε) · log(f(1/ε)/δ) ≤ N`, then invokes
  `sicc_covering_meta`.

Axiom footprint: `[propext, Classical.choice, Quot.sound]` for both —
**zero new project-local axioms**.  The precondition
(polynomial ε-covering number) is sharp: it holds for linear ICA,
sparse-linear ICA, iVAE, interventional CRL (each having
`N(ε, H) ≤ (1/ε)^{poly(d_Z)}`), and provably fails for Locatello
2019's fully-unsupervised nonlinear ICA (dense diffeomorphism cover,
`N(ε, H) = exp(Ω(d_Z))`).

## Mathlib lemmas reused

| Lemma                                     | Where                                                   | Used for                                    |
| ----------------------------------------- | ------------------------------------------------------- | ------------------------------------------- |
| `Real.exp_log`                            | `Mathlib.Analysis.SpecialFunctions.Log.Basic`           | Invert `log` after exponentiating in T5 rate |
| `Real.log_inv`                            | `Mathlib.Analysis.SpecialFunctions.Log.Basic`           | `-log (M/ε) = log (ε/M)`                     |
| `Real.exp_le_exp`                         | `Mathlib.Analysis.Complex.Exponential`                  | Monotonicity of `exp` (both directions)     |
| `Real.add_one_le_exp`                     | `Mathlib.Analysis.Complex.Exponential`                  | `1 - x ≤ exp(-x)` bridge for T5             |
| `Real.exp_nat_mul`                        | `Mathlib.Analysis.Complex.Exponential`                  | `(exp x)^n = exp (n · x)`                    |
| `le_div_iff₀'`                            | `Mathlib.Algebra.Order.GroupWithZero.Basic`             | Move `c·M` from left-mul to right-div        |
| `le_div_iff₀`                             | `Mathlib.Algebra.Order.GroupWithZero.Basic`             | CT-2 Boltzmann wrapper divides by `Z`       |
| `pow_le_pow_left₀`                        | `Mathlib.Algebra.Order.GroupWithZero.Basic`             | Raise `1 - x ≤ exp(-x)` to the `n`-th power |
| `one_add_mul_le_pow`                      | `Mathlib.Algebra.Order.Ring.Pow`                        | Bernoulli's inequality for `-2 ≤ a`         |
| `Finset.prod_le_prod`                     | `Mathlib.Algebra.Order.BigOperators.GroupWithZero.Finset` | Monotonicity of finite products (nonneg reals) |
| `Fin.prod_const`                          | `Mathlib.Algebra.BigOperators.Fin`                      | `∏ _ : Fin n, c = c ^ n`                     |
| `HasDerivAt.fun_sum`                      | `Mathlib.Analysis.Calculus.Deriv.Add`                   | Differentiate `Z(θ) = ∑ x, h(x) · exp(θ · T(x))` under the finite sum for CG-1 |
| `HasDerivAt.exp`, `HasDerivAt.const_mul`  | `Mathlib.Analysis.SpecialFunctions.ExpDeriv`            | Chain rule for `θ ↦ h(x) · exp(θ · T(x))` for CG-1 |
| `HasDerivAt.log`                          | `Mathlib.Analysis.SpecialFunctions.Log.Deriv`           | `A'(θ) = Z'(θ) / Z(θ)` for CG-1              |
| `HasDerivAt.congr_deriv`                  | `Mathlib.Analysis.Calculus.Deriv.Basic`                 | Rewrite derivative-value up to `ring`-equality in CG-1 |
| `Finset.sum_div`                          | `Mathlib.Algebra.BigOperators.Field`                    | Distribute `1 / Z(θ)` under the sum for CG-1 mean identity |
| `Real.log_div`, `Real.log_mul`, `Real.log_exp` | `Mathlib.Analysis.SpecialFunctions.Log.Basic`      | Decompose `log p_θ(x)` for CG-1 score identity |
| `Finset.sum_const`, `Finset.card_range`, `nsmul_eq_mul` | `Mathlib.Algebra.BigOperators.Group.Finset.Basic` | Collapse the CG-2 constant-cell-curl grid sum   |
| `Finset.sum_comm`                         | `Mathlib.Algebra.BigOperators.Group.Finset.Basic`       | Swap grid-axis sums in CG-2 symmetric-grid form |
| `div_self`                                | `Mathlib.Algebra.Group.Basic` (via mathlib re-exports)  | Cancel `N/N`, `M/M` in CG-2 discrete-grid identity |
| `strictConcaveOn_log_Ioi`, `ConcaveOn.le_map_sum` | `Mathlib.Analysis.Convex.SpecificFunctions.Basic`, `Mathlib.Analysis.Convex.Jensen` | Concave-log Jensen for AA-1 mixture inequality |
| `Finset.sum_le_sum`                       | `Mathlib.Algebra.BigOperators.Order`                    | Pointwise monotonicity for AA-1 refinement corollary |

## What is not formalized

Every theorem in this project compiles with **zero `sorry`s**.  Most
depend only on the standard Lean 4 axioms `propext`,
`Classical.choice`, and `Quot.sound` (i.e. no extra axioms beyond
what mathlib itself uses).

Ten of the twelve theorem-family headlines depend only on Mathlib's
axiom base (`propext`, `Classical.choice`, `Quot.sound`).  The three
new headlines added in the second wave —
`cg1_fisher_matrix_eq_covariance` and its scalar/derivative
companions, `cg2_holonomy_equals_signed_area` and its Riemann-sum
companions, and `aa1_log_mixture_ge_weighted_log` with its
sample-form and refinement-monotonicity corollaries — introduce
**zero** additional project-local axioms.  The third-wave headline
`sic_a_finite_discrete` (SIC-A derived in the finite discrete
positive-support case, `SICA_FiniteExistence.lean`) also introduces
**zero** additional project-local axioms; its coarsestness
corollary `sic_a_finite_discrete_coarsest` uses
`HalmosSavage_minimality_h_extension` as a theorem.
The fourth-wave headlines `sicc_covering_meta` and
`sicc_covering_poly` (SIC-C-c covering meta-theorem,
`SICC_CoveringMeta.lean`) close the SIC-C-c conjecture *conditionally*
by composing Theorem 5-rate (this project) with Theorem 6's
ε-covering reduction (pure-core `refinement_preserves_screen`); both
introduce **zero** additional project-local axioms.

No first-wave headline uses a project-local `axiom`.  Wave 9
discharged Halmos–Savage packaging; Wave 10 discharged the Shannon
`0 < D` converse (`ShannonFano.lean`, Fano + Jensen + `qaryEntropy`
monotonicity; not KKT).  Wave 12 adds the WI KL certificate
(`WeaknessPACBayes.lean`); LSM stays a hypothesis.  All remain
**proved-not-verified** (SafeVerify is the mathlib-free 4.29 lane).
`#print axioms` on `R_D_uniform_hamming` and
`weakness_kl_certificate` is `{propext, Classical.choice, Quot.sound}`.

The CT-2 wrapper is stated with `Z > 0` as a hypothesis rather than
deducing it from the shape of `p` and `r`.  A cleaner version would
show `Z > 0` follows from `∃ i, p i > 0` and any real reward
(because `exp(β · r) > 0` pointwise); this is a purely notational
extension and does not change the mathematical content of CT-2.

The Markov-chain lift of `ag1_joint_survival` from
`∏ t, s t ≥ (1-β)^T` to a genuine kernel-conditional probability
statement `P[q(X_t) ∈ V ∀ t < T] ≥ (1-β)^T` is left in prose:
the arithmetic step is exactly the one this file provides, and the
kernel-conditional lift is the standard Markov chain-rule identity
`P[A_0 ∩ ... ∩ A_T] = ∏ P[A_{t+1} | A_t] · P[A_0]` from measure
theory.

## Building

```
cd formal/structural-intelligence-mathlib
lake update mathlib            # first time only
lake exe cache get             # fetches mathlib .olean cache
lake build
```

First cold build with `cache get` is around 5–10 minutes (dominated
by the cache download).  Incremental builds of this project's own
three modules take under 30 seconds.
