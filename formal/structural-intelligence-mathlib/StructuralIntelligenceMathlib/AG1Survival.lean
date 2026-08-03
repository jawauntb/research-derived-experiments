import Mathlib.Data.Real.Basic
import Mathlib.Algebra.Order.Ring.Pow
import Mathlib.Algebra.Order.BigOperators.GroupWithZero.Finset
import Mathlib.Algebra.BigOperators.Fin
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Ring

/-!
# Structural Intelligence (Mathlib) — AG-1 survival bound

The quantitative half of Theorem AG-1 from the *Alignment Governance*
companion paper: if the one-step probability of leaving a viability
set `V` is at most `β ∈ [0, 1]`, then a length-`T` trajectory survives
in `V` with probability at least `(1 - β)^T`, which in turn is at
least the linear lower bound `1 - T · β`.

Two ingredients are formalised here:

1.  `ag1_survival_lower_bound` — **Bernoulli's inequality**
    `(1 - β)^T ≥ 1 - T · β` for `β ∈ [0, 1]`, obtained from Mathlib's
    `one_add_mul_le_pow` applied at `x = -β` (which has `-2 ≤ x`
    trivially, since `β ≤ 1`).

2.  `ag1_joint_survival` — a purely arithmetic **product-of-conditionals
    step**: if each conditional survival probability
    `s t : ℝ` lies in `[1 - β, 1]`, then the product `∏_{t < T} s t`
    is bounded below by `(1 - β)^T`.  This is what one would multiply
    into a Markov-chain formulation of AG-1 to get the joint bound; it
    is stated at the level of the numeric factors so that no measure
    theory is needed.

Mathlib lemmas reused:
* `one_add_mul_le_pow` — Bernoulli's inequality for `n : ℕ`, `-2 ≤ a`.
* `Finset.prod_le_prod` — monotonicity of finite products over nonneg
  reals.
-/

namespace StructuralIntelligenceMathlib

open Finset

/-- **AG-1 survival lower bound (Bernoulli's inequality).**

    For `β ∈ [0, 1]` and any natural `T`,

        (1 - β)^T  ≥  1 - T · β.

    Obtained from `one_add_mul_le_pow` at `x = -β`: because `β ≤ 1`,
    we have `-β ≥ -1 ≥ -2`, hence the hypothesis `-2 ≤ -β` is met.

    In the AG-1 context, `1 - β` is the per-step probability that the
    state stays in the viability set, and the LHS is the joint
    survival lower bound over a length-`T` trajectory.  The RHS gives
    the coarser but linear-in-`T` bound used for quick
    back-of-envelope reasoning. -/
theorem ag1_survival_lower_bound
    (β : ℝ) (T : ℕ) (_hβ_nonneg : 0 ≤ β) (hβ_le_one : β ≤ 1) :
    1 - (T : ℝ) * β ≤ (1 - β) ^ T := by
  -- Apply `one_add_mul_le_pow` at `a = -β`; needs `-2 ≤ -β`.
  have hx_ge : (-2 : ℝ) ≤ -β := by linarith
  have h : (1 : ℝ) + (T : ℝ) * (-β) ≤ (1 + -β) ^ T :=
    one_add_mul_le_pow hx_ge T
  -- Rewrite `1 + T * (-β) = 1 - T · β` and `1 + -β = 1 - β`.
  have h_lhs : (1 : ℝ) + (T : ℝ) * (-β) = 1 - (T : ℝ) * β := by ring
  have h_rhs : ((1 : ℝ) + -β) ^ T = (1 - β) ^ T := by
    have : (1 : ℝ) + -β = 1 - β := by ring
    rw [this]
  linarith [h_lhs ▸ h_rhs ▸ h]

/-- **Joint-survival product step (arithmetic core of AG-1).**

    Let `s : Fin T → ℝ` be a sequence of one-step conditional
    survival probabilities, each in `[1 - β, 1]` for some
    `β ∈ [0, 1]`.  Then the joint survival probability
    `∏_{t : Fin T} s t` is bounded below by `(1 - β)^T`.

    Under a Markov-chain reading, `s t` is the conditional probability
    `P[q(X_{t+1}) ∈ V | q(X_t) ∈ V]`, so the LHS is the product form
    of `P[q(X_t) ∈ V for all t < T]` by the chain rule, and this
    lemma gives the promised `(1 - β)^T` lower bound. -/
theorem ag1_joint_survival
    (β : ℝ) (T : ℕ) (_hβ_nonneg : 0 ≤ β) (hβ_le_one : β ≤ 1)
    (s : Fin T → ℝ)
    (h_lower : ∀ t, 1 - β ≤ s t)
    (_h_upper : ∀ t, s t ≤ 1) :
    (1 - β) ^ T ≤ ∏ t, s t := by
  have h1mβ_nonneg : (0 : ℝ) ≤ 1 - β := by linarith
  have h_pow_eq_prod : (1 - β) ^ T = ∏ _t : Fin T, (1 - β) :=
    (Fin.prod_const T (1 - β)).symm
  rw [h_pow_eq_prod]
  apply Finset.prod_le_prod
  · intro _ _; exact h1mβ_nonneg
  · intro t _; exact h_lower t

/-- Convenience corollary combining the two: under the same
    hypotheses on `s` and `β`, the joint survival is at least the
    linear `1 - T · β` bound. -/
theorem ag1_joint_survival_linear
    (β : ℝ) (T : ℕ) (hβ_nonneg : 0 ≤ β) (hβ_le_one : β ≤ 1)
    (s : Fin T → ℝ)
    (h_lower : ∀ t, 1 - β ≤ s t)
    (h_upper : ∀ t, s t ≤ 1) :
    1 - (T : ℝ) * β ≤ ∏ t, s t :=
  le_trans
    (ag1_survival_lower_bound β T hβ_nonneg hβ_le_one)
    (ag1_joint_survival β T hβ_nonneg hβ_le_one s h_lower h_upper)

end StructuralIntelligenceMathlib
