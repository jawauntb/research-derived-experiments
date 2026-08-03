import Mathlib.Analysis.SpecialFunctions.Log.Deriv
import Mathlib.Analysis.SpecialFunctions.ExpDeriv
import Mathlib.Analysis.Calculus.Deriv.Add
import Mathlib.Analysis.Calculus.Deriv.Mul
import Mathlib.Analysis.Calculus.Deriv.Basic
import Mathlib.Analysis.SpecialFunctions.Log.Basic
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Algebra.BigOperators.Field
import Mathlib.Algebra.BigOperators.Ring.Finset
import Mathlib.Data.Fintype.BigOperators
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Ring
import Mathlib.Tactic.FieldSimp

/-!
# Structural Intelligence (Mathlib) — CG-1 Fisher information = covariance

Theorem CG-1 from `papers/concern_as_fiber_geometry/paper.md`, §3.  For
a finite-support exponential family

    p_θ(x)  =  h(x) · exp(⟨θ, T(x)⟩ - A(θ)),
    Z(θ)    :=  ∑_x h(x) · exp(⟨θ, T(x)⟩),      A(θ) := log Z(θ),

with `T : α → Fin k → ℝ` the sufficient statistic and `θ : Fin k → ℝ`
the natural parameter, the Fisher information matrix `I(θ)` equals the
covariance of the sufficient statistic under `p_θ`:

    I_{ij}(θ)  =  Cov_{p_θ}[T_i, T_j].

**Scope of this file.**

* The load-bearing analytic step is the **log-partition derivative
  identity** `A'(θ) = E_{p_θ}[T]` (`cg1_logpartition_deriv_eq_meanT`
  in the 1D natural-parameter case).  From it, the **score identity**
  `∂ log p_θ(x) / ∂ θ = T(x) - E_{p_θ}[T]`
  (`cg1_score_identity_scalar`) follows directly via
  `HasDerivAt.log` and `HasDerivAt.exp`.

* The **matrix identity** `Fisher = Covariance` is stated in the
  `Fin k` multi-parameter form (`cg1_fisher_matrix_eq_covariance`).
  Once the score is defined as the centered sufficient statistic
  `s_i(θ, x) := T(x)_i - E_{p_θ}[T_i]`, the entry-wise identity
  `E_{p_θ}[s_i · s_j]  =  Cov_{p_θ}[T_i, T_j]` is definitional — the
  substantive content is the score identity that motivates this
  definition of score, which is proved in the 1D natural-parameter
  file via `HasDerivAt`.

Neither theorem introduces a project-local axiom.  The only Mathlib
inputs are the standard `HasDerivAt` chain rules for `Real.log` and
`Real.exp` (which are already used by `Theorem5Rate.lean` and
`CT2MonotoneReward.lean` in this project) and elementary `Finset.sum`
manipulations.
-/

namespace StructuralIntelligenceMathlib

open Finset

variable {α : Type*} [Fintype α]

/-! ### 1D natural-parameter exponential family -/

/-- Partition function `Z(θ) := ∑_x h(x) · exp(θ · T(x))`. -/
noncomputable def expFamZ (h T : α → ℝ) (θ : ℝ) : ℝ :=
  ∑ x, h x * Real.exp (θ * T x)

/-- Formal derivative of `Z` (differentiated under the finite sum). -/
noncomputable def expFamZ' (h T : α → ℝ) (θ : ℝ) : ℝ :=
  ∑ x, h x * T x * Real.exp (θ * T x)

/-- Log-partition function `A(θ) := log Z(θ)`. -/
noncomputable def expFamA (h T : α → ℝ) (θ : ℝ) : ℝ :=
  Real.log (expFamZ h T θ)

/-- Exponential-family density
    `p_θ(x) := h(x) · exp(θ · T(x)) / Z(θ)`. -/
noncomputable def expFamP (h T : α → ℝ) (θ : ℝ) (x : α) : ℝ :=
  h x * Real.exp (θ * T x) / expFamZ h T θ

/-- Expected sufficient statistic `E_{p_θ}[T]`. -/
noncomputable def expFamMeanT (h T : α → ℝ) (θ : ℝ) : ℝ :=
  ∑ x, expFamP h T θ x * T x

/-- Score at sample `x`: the centered sufficient statistic. -/
noncomputable def expFamScore (h T : α → ℝ) (θ : ℝ) (x : α) : ℝ :=
  T x - expFamMeanT h T θ

/-- Fisher information (scalar 1D) `E_{p_θ}[score(x)²]`. -/
noncomputable def expFamFisher (h T : α → ℝ) (θ : ℝ) : ℝ :=
  ∑ x, expFamP h T θ x * (expFamScore h T θ x) ^ 2

/-- Variance of sufficient statistic `Var_{p_θ}[T]`. -/
noncomputable def expFamVarT (h T : α → ℝ) (θ : ℝ) : ℝ :=
  ∑ x, expFamP h T θ x * (T x - expFamMeanT h T θ) ^ 2

/-- **`Z` is differentiable pointwise with the natural derivative under
    the finite sum.** -/
theorem hasDerivAt_expFamZ (h T : α → ℝ) (θ : ℝ) :
    HasDerivAt (expFamZ h T) (expFamZ' h T θ) θ := by
  show HasDerivAt (fun θ' => ∑ x, h x * Real.exp (θ' * T x))
    (∑ x, h x * T x * Real.exp (θ * T x)) θ
  refine HasDerivAt.fun_sum (u := Finset.univ) ?_
  intro x _
  -- d/dθ (h x * exp(θ * T x)) = h x * T x * exp(θ * T x).
  have h1 : HasDerivAt (fun θ' => θ' * T x) (T x) θ := by
    simpa using (hasDerivAt_id θ).mul_const (T x)
  have h2 :
      HasDerivAt (fun θ' => Real.exp (θ' * T x))
        (Real.exp (θ * T x) * T x) θ := h1.exp
  have h3 :
      HasDerivAt (fun θ' => h x * Real.exp (θ' * T x))
        (h x * (Real.exp (θ * T x) * T x)) θ := h2.const_mul (h x)
  exact h3.congr_deriv (by ring)

/-- **Log-partition derivative equals expected sufficient statistic**
    (the load-bearing exponential-family identity behind CG-1).

    Assuming the partition function is strictly positive at `θ`,

        (∂/∂θ) log Z(θ)  =  E_{p_θ}[T].

    Proof: differentiate `log ∘ Z` via `HasDerivAt.log`, then reshape
    the resulting `Z'(θ) / Z(θ)` as a sum of per-`x` terms and
    identify each with `p_θ(x) · T(x)`. -/
theorem cg1_logpartition_deriv_eq_meanT
    (h T : α → ℝ) (θ : ℝ)
    (hZ_pos : 0 < expFamZ h T θ) :
    HasDerivAt (expFamA h T) (expFamMeanT h T θ) θ := by
  unfold expFamA
  have h1 := hasDerivAt_expFamZ h T θ
  have h2 :
      HasDerivAt (fun θ' => Real.log (expFamZ h T θ'))
        (expFamZ' h T θ / expFamZ h T θ) θ :=
    h1.log (ne_of_gt hZ_pos)
  -- Rewrite `Z' / Z` as `∑ p_θ(x) · T(x)`.
  have h_ratio : expFamZ' h T θ / expFamZ h T θ = expFamMeanT h T θ := by
    unfold expFamZ' expFamMeanT expFamP
    rw [Finset.sum_div]
    apply Finset.sum_congr rfl
    intro x _
    ring
  rw [h_ratio] at h2
  exact h2

/-- Positivity of the density at any `x`, given positive `h` and positive `Z`. -/
theorem expFamP_pos
    (h T : α → ℝ) (θ : ℝ) (x : α)
    (hh_pos : 0 < h x)
    (hZ_pos : 0 < expFamZ h T θ) :
    0 < expFamP h T θ x := by
  unfold expFamP
  have hexp_pos : 0 < Real.exp (θ * T x) := Real.exp_pos _
  have hnum : 0 < h x * Real.exp (θ * T x) := mul_pos hh_pos hexp_pos
  exact div_pos hnum hZ_pos

/-- **CG-1 score identity (1D natural-parameter form).**

    For an exponential family with positive base `h` and positive
    partition function at every `θ'`,

        (∂/∂θ') log p_{θ'}(x)  |_{θ' = θ}   =   T(x) - E_{p_θ}[T].

    In particular, the score at each `x` is the centered sufficient
    statistic `expFamScore h T θ x`.

    Proof: decompose `log p_{θ'}(x) = log h(x) + θ' · T(x) - A(θ')`
    using `Real.log_div`, `Real.log_mul`, `Real.log_exp`, then use
    linearity of derivative in `θ'` and
    `cg1_logpartition_deriv_eq_meanT` for the `A(θ')` term. -/
theorem cg1_score_identity_scalar
    (h T : α → ℝ) (θ : ℝ) (x : α)
    (hh_pos : ∀ y, 0 < h y)
    (hZ_pos_all : ∀ θ', 0 < expFamZ h T θ') :
    HasDerivAt (fun θ' => Real.log (expFamP h T θ' x))
      (expFamScore h T θ x) θ := by
  unfold expFamScore
  -- Decompose log p_{θ'}(x) as log h(x) + θ' * T x - A(θ').
  have h_expand :
      (fun θ' => Real.log (expFamP h T θ' x))
        = (fun θ' => Real.log (h x) + θ' * T x - expFamA h T θ') := by
    ext θ'
    unfold expFamP expFamA
    have hhx_ne : h x ≠ 0 := ne_of_gt (hh_pos x)
    have hexp_ne : Real.exp (θ' * T x) ≠ 0 := ne_of_gt (Real.exp_pos _)
    have hnum_ne : h x * Real.exp (θ' * T x) ≠ 0 := mul_ne_zero hhx_ne hexp_ne
    have hZ_ne : expFamZ h T θ' ≠ 0 := ne_of_gt (hZ_pos_all θ')
    rw [Real.log_div hnum_ne hZ_ne, Real.log_mul hhx_ne hexp_ne, Real.log_exp]
  rw [h_expand]
  -- Now differentiate log(h x) + θ' * T x - A(θ').
  have h_const : HasDerivAt (fun _θ' : ℝ => Real.log (h x)) 0 θ :=
    hasDerivAt_const θ _
  have h_lin : HasDerivAt (fun θ' : ℝ => θ' * T x) (T x) θ := by
    simpa using (hasDerivAt_id θ).mul_const (T x)
  have h_A :
      HasDerivAt (expFamA h T) (expFamMeanT h T θ) θ :=
    cg1_logpartition_deriv_eq_meanT h T θ (hZ_pos_all θ)
  have h_sum :
      HasDerivAt (fun θ' => Real.log (h x) + θ' * T x)
        (0 + T x) θ := h_const.add h_lin
  have h_diff :
      HasDerivAt (fun θ' => Real.log (h x) + θ' * T x - expFamA h T θ')
        (0 + T x - expFamMeanT h T θ) θ := h_sum.sub h_A
  convert h_diff using 1
  ring

/-- **CG-1 Fisher-equals-variance (1D natural-parameter form).**

    The Fisher information at `θ` equals the variance of the
    sufficient statistic under `p_θ`.  This is *definitional* once
    the score is defined as the centered sufficient statistic
    (`expFamScore h T θ x = T x - expFamMeanT h T θ`); the
    substantive content is the score-identity theorem above, which
    proves this definition of score really is the derivative of the
    log density. -/
theorem cg1_fisher_eq_variance
    (h T : α → ℝ) (θ : ℝ) :
    expFamFisher h T θ = expFamVarT h T θ := by
  unfold expFamFisher expFamVarT expFamScore
  rfl

/-- **Score has mean zero under the model** (auxiliary lemma, also
    used to derive the covariance form from the raw second moment).

    Assumes total probability sums to 1 (which holds automatically
    when `Z(θ) > 0` since `∑_x h(x) · exp(θ · T(x)) = Z(θ)` and
    dividing gives `∑_x p_θ(x) = 1`). -/
theorem expFamScore_mean_zero
    (h T : α → ℝ) (θ : ℝ)
    (hZ_pos : 0 < expFamZ h T θ) :
    (∑ x, expFamP h T θ x * expFamScore h T θ x) = 0 := by
  unfold expFamScore expFamMeanT
  -- Total mass equals 1.
  have h_sum_p : (∑ x, expFamP h T θ x) = 1 := by
    unfold expFamP expFamZ
    rw [← Finset.sum_div]
    exact div_self (ne_of_gt hZ_pos)
  -- Expand `p · (T - EX) = p · T - (EX) · p` and split the sum.
  set c : ℝ := ∑ y, expFamP h T θ y * T y with hc
  have h_split :
      (∑ x, expFamP h T θ x * (T x - c))
        = (∑ x, expFamP h T θ x * T x) - c * (∑ x, expFamP h T θ x) := by
    have h_ring :
        ∀ x, expFamP h T θ x * (T x - c)
              = expFamP h T θ x * T x - c * expFamP h T θ x := by
      intro x; ring
    calc (∑ x, expFamP h T θ x * (T x - c))
        = ∑ x, (expFamP h T θ x * T x - c * expFamP h T θ x) := by
          exact Finset.sum_congr rfl (fun x _ => h_ring x)
      _ = (∑ x, expFamP h T θ x * T x)
            - (∑ x, c * expFamP h T θ x) := by
          exact (Finset.sum_sub_distrib
                (f := fun x => expFamP h T θ x * T x)
                (g := fun x => c * expFamP h T θ x))
      _ = (∑ x, expFamP h T θ x * T x) - c * (∑ x, expFamP h T θ x) := by
          rw [← Finset.mul_sum]
  -- Substitute total-mass = 1 and c = mean.
  rw [h_split, h_sum_p, mul_one, hc, sub_self]

/-! ### Multi-parameter form: Fisher matrix = covariance matrix -/

/-- Inner product `⟨θ, T x⟩` for `θ, T x : Fin k → ℝ`. -/
noncomputable def dotFin {k : ℕ} (θ Tx : Fin k → ℝ) : ℝ :=
  ∑ i : Fin k, θ i * Tx i

/-- Multi-parameter partition function. -/
noncomputable def expFamZk {k : ℕ}
    (h : α → ℝ) (T : α → Fin k → ℝ) (θ : Fin k → ℝ) : ℝ :=
  ∑ x, h x * Real.exp (dotFin θ (T x))

/-- Multi-parameter density. -/
noncomputable def expFamPk {k : ℕ}
    (h : α → ℝ) (T : α → Fin k → ℝ) (θ : Fin k → ℝ) (x : α) : ℝ :=
  h x * Real.exp (dotFin θ (T x)) / expFamZk h T θ

/-- Mean sufficient statistic, coordinate `i`. -/
noncomputable def expFamMeanTk {k : ℕ}
    (h : α → ℝ) (T : α → Fin k → ℝ) (θ : Fin k → ℝ) (i : Fin k) : ℝ :=
  ∑ x, expFamPk h T θ x * T x i

/-- Score at sample `x`, coordinate `i`: the centered sufficient statistic. -/
noncomputable def expFamScorek {k : ℕ}
    (h : α → ℝ) (T : α → Fin k → ℝ) (θ : Fin k → ℝ) (x : α) (i : Fin k) : ℝ :=
  T x i - expFamMeanTk h T θ i

/-- Fisher information matrix, `(i, j)`-entry. -/
noncomputable def expFamFisherMatrix {k : ℕ}
    (h : α → ℝ) (T : α → Fin k → ℝ) (θ : Fin k → ℝ) (i j : Fin k) : ℝ :=
  ∑ x, expFamPk h T θ x
        * expFamScorek h T θ x i * expFamScorek h T θ x j

/-- Covariance matrix of the sufficient statistic. -/
noncomputable def expFamCovMatrix {k : ℕ}
    (h : α → ℝ) (T : α → Fin k → ℝ) (θ : Fin k → ℝ) (i j : Fin k) : ℝ :=
  ∑ x, expFamPk h T θ x
        * (T x i - expFamMeanTk h T θ i)
        * (T x j - expFamMeanTk h T θ j)

/-- **CG-1 (matrix form): the Fisher information matrix equals the
    covariance matrix of the sufficient statistic.**

    Once the score at coordinate `i` is defined as the centered
    sufficient statistic `T_i(x) - E_{p_θ}[T_i]`, the identity

        I_{ij}(θ)  =  Cov_{p_θ}[T_i, T_j]

    holds entry-wise by definition.  The substantive analytic content
    — that this definition of score really *is* the coordinate-wise
    derivative of `log p_θ(x)` — is captured by
    `cg1_score_identity_scalar` (1D per-direction version).  The
    corresponding directional-derivative statement in multi-parameter
    form follows from `cg1_score_identity_scalar` applied to the
    one-parameter subfamily `t ↦ p_{θ + t · e_i}(x)`; we do not
    unfold that reduction here since the matrix statement of CG-1 is
    already the theorem the paper cites. -/
theorem cg1_fisher_matrix_eq_covariance
    {k : ℕ} (h : α → ℝ) (T : α → Fin k → ℝ) (θ : Fin k → ℝ) (i j : Fin k) :
    expFamFisherMatrix h T θ i j = expFamCovMatrix h T θ i j := by
  unfold expFamFisherMatrix expFamCovMatrix expFamScorek
  apply Finset.sum_congr rfl
  intro x _
  ring

end StructuralIntelligenceMathlib
