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
| `formal/structural-intelligence-mathlib/` (this)  | Lean 4 + mathlib    | Real-analytic: Theorem 5 quantitative rate, AG-1 survival bound, CT-2 monotone-reward core, Theorem 1 (Halmos–Savage minimal sufficient statistic), Theorem 2 (Shannon rate–distortion, uniform-Hamming closed form), Proposition 3 (Coarsen ⊣ Refine adjunction) |

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
  `Θ → ℝ`" — is packaged into the single axiom
  `StructuralIntelligenceMathlib.HalmosSavage_minimality_h_extension`
  with an inline citation to Halmos & Savage (1949), *Ann. Math.
  Statist.* 20, 225–241, Theorem 2.

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

* `StructuralIntelligenceMathlib.R_D_uniform_hamming` — the full
  Shannon 1959 statement (both directions).  The **converse** — no
  channel of distortion `≤ D` achieves strictly smaller mutual
  information — is packaged into the axiom
  `StructuralIntelligenceMathlib.Shannon1959_converse_uniform_hamming`.
  Its full proof requires a Lagrangian / KKT argument on the simplex
  of transition matrices, infrastructure that Mathlib does not
  currently expose.  Cited: C. E. Shannon (1959), *Coding theorems
  for a discrete source with a fidelity criterion*, IRE Nat. Conv.
  Rec., pt. 4, 142–163, Theorem 3.

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

## What is not formalized

Every theorem in this project compiles with **zero `sorry`s**.  Most
depend only on the standard Lean 4 axioms `propext`,
`Classical.choice`, and `Quot.sound` (i.e. no extra axioms beyond
what mathlib itself uses).

Two theorems make honest use of an additional **project-local
`axiom`** each, with an inline citation:

* `StructuralIntelligenceMathlib.HalmosSavage_minimality_h_extension`
  — packaging step needed by
  `exists_minimal_sufficient_finite_discrete`.  All of the
  mathematical content (LR vector is sufficient; LR vector determines
  every sufficient statistic up to a function; iff-characterisation
  of sufficiency by LR-factoring) is proved in the file.  The axiom
  captures only the classical-choice extension of the partial
  function on the image of `T'` to a total function on `Θ → ℝ`.
  Reference: Halmos & Savage (1949), *Ann. Math. Statist.* 20,
  225–241, Theorem 2.

* `StructuralIntelligenceMathlib.Shannon1959_converse_uniform_hamming`
  — the converse half of Shannon's rate-distortion theorem for
  uniform source with Hamming distortion.  Achievability — the
  symmetric error-`D` channel realises `log n − h_binary(D) − D · log(n−1)`
  — is proved in full.  The converse (no other channel achieves
  smaller mutual information) requires a Lagrangian / KKT argument on
  the simplex of transition matrices; Mathlib does not yet expose the
  optimisation-on-a-simplex infrastructure this would need.
  Reference: C. E. Shannon (1959), *Coding theorems for a discrete
  source with a fidelity criterion*, IRE Nat. Conv. Rec., pt. 4,
  142–163, Theorem 3.

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
