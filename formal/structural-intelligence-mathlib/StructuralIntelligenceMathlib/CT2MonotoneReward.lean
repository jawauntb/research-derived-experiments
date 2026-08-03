import Mathlib.Data.Real.Basic
import Mathlib.Analysis.Complex.Exponential
import Mathlib.Algebra.Order.BigOperators.Ring.Finset
import Mathlib.Algebra.BigOperators.Ring.Finset
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Ring

/-!
# Structural Intelligence (Mathlib) — CT-2 monotone-reward core

The load-bearing correlation inequality behind Theorem CT-2
(Compiler-Tomography monotone-reward core): the reward `r` and its
Boltzmann weight `exp(β · r)` (for `β ≥ 0`) are, under any nonneg
weight vector, positively correlated.  In finite-support notation,

    (∑ᵢ pᵢ)·(∑ᵢ pᵢ · rᵢ · exp(β·rᵢ))
      ≥ (∑ᵢ pᵢ · rᵢ) · (∑ᵢ pᵢ · exp(β·rᵢ)).

When `p` is a probability distribution (`∑ pᵢ = 1`), this is exactly
the Chebyshev sum inequality
`E[r · exp(β·r)] ≥ E[r] · E[exp(β·r)]`.

The wrapper `ct2_boltzmann_raises_expected_reward` uses this to show
that the Boltzmann-tilted distribution
`p'(x) ∝ p(x) · exp(β · r(x))` has expected reward `E_{p'}[r]` at
least `E_p[r]`.

We prove the weighted Chebyshev-sum / positive-correlation inequality
directly by expanding the nonneg quantity
`∑ᵢ∑ⱼ wᵢwⱼ(fᵢ - fⱼ)(gᵢ - gⱼ) ≥ 0` and identifying the four resulting
sums.  The reused Mathlib input is only the strict monotonicity of
`Real.exp` (via `Real.exp_le_exp`) used to establish comonotonicity of
`r` and `exp(β·r)`.
-/

namespace StructuralIntelligenceMathlib

open Finset Real

variable {α : Type*}

/-- **Positive correlation lemma (weighted Chebyshev sum inequality).**

    Let `s : Finset α`, `w : α → ℝ` nonneg weights, and
    `f g : α → ℝ` two functions that comonotonically depend on the
    same underlying values on `s`: for any `i j ∈ s`,
    `(f i - f j) · (g i - g j) ≥ 0`.  Then

        (∑ i ∈ s, w i · f i) · (∑ i ∈ s, w i · g i)
          ≤ (∑ i ∈ s, w i) · (∑ i ∈ s, w i · f i · g i).

    Proof: expand
    `∑ᵢ∑ⱼ wᵢ wⱼ (fᵢ - fⱼ)(gᵢ - gⱼ) ≥ 0` and rearrange; each
    summand is nonneg because `wᵢ, wⱼ ≥ 0` and
    `(fᵢ - fⱼ)(gᵢ - gⱼ) ≥ 0` by the comonotonicity hypothesis. -/
theorem chebyshev_weighted_correlation
    (s : Finset α) (w f g : α → ℝ)
    (hw : ∀ i ∈ s, 0 ≤ w i)
    (hcomono : ∀ i ∈ s, ∀ j ∈ s, 0 ≤ (f i - f j) * (g i - g j)) :
    (∑ i ∈ s, w i * f i) * (∑ i ∈ s, w i * g i)
      ≤ (∑ i ∈ s, w i) * (∑ i ∈ s, w i * f i * g i) := by
  -- Double sum: rewrite each of the four pieces of
  -- `(fᵢ-fⱼ)(gᵢ-gⱼ)` as a product of two single sums.  Each step
  -- factors the inner sum by pulling out the `i`-dependent factor,
  -- then factors the outer sum.
  have s1 :
      (∑ i ∈ s, ∑ j ∈ s, w i * w j * (f i * g i))
        = (∑ i ∈ s, w i * f i * g i) * (∑ j ∈ s, w j) := by
    have inner :
        ∀ i, (∑ j ∈ s, w i * w j * (f i * g i))
              = (w i * f i * g i) * (∑ j ∈ s, w j) := by
      intro i
      have : (∑ j ∈ s, w i * w j * (f i * g i))
          = (∑ j ∈ s, (w i * f i * g i) * w j) := by
        apply Finset.sum_congr rfl; intro j _; ring
      rw [this, ← Finset.mul_sum]
    have outer :
        (∑ i ∈ s, ∑ j ∈ s, w i * w j * (f i * g i))
          = ∑ i ∈ s, (w i * f i * g i) * (∑ j ∈ s, w j) := by
      apply Finset.sum_congr rfl; intro i _; exact inner i
    rw [outer, ← Finset.sum_mul]
  have s2 :
      (∑ i ∈ s, ∑ j ∈ s, w i * w j * (f i * g j))
        = (∑ i ∈ s, w i * f i) * (∑ j ∈ s, w j * g j) := by
    have inner :
        ∀ i, (∑ j ∈ s, w i * w j * (f i * g j))
              = (w i * f i) * (∑ j ∈ s, w j * g j) := by
      intro i
      have : (∑ j ∈ s, w i * w j * (f i * g j))
          = (∑ j ∈ s, (w i * f i) * (w j * g j)) := by
        apply Finset.sum_congr rfl; intro j _; ring
      rw [this, ← Finset.mul_sum]
    have outer :
        (∑ i ∈ s, ∑ j ∈ s, w i * w j * (f i * g j))
          = ∑ i ∈ s, (w i * f i) * (∑ j ∈ s, w j * g j) := by
      apply Finset.sum_congr rfl; intro i _; exact inner i
    rw [outer, ← Finset.sum_mul]
  have s3 :
      (∑ i ∈ s, ∑ j ∈ s, w i * w j * (f j * g i))
        = (∑ i ∈ s, w i * g i) * (∑ j ∈ s, w j * f j) := by
    have inner :
        ∀ i, (∑ j ∈ s, w i * w j * (f j * g i))
              = (w i * g i) * (∑ j ∈ s, w j * f j) := by
      intro i
      have : (∑ j ∈ s, w i * w j * (f j * g i))
          = (∑ j ∈ s, (w i * g i) * (w j * f j)) := by
        apply Finset.sum_congr rfl; intro j _; ring
      rw [this, ← Finset.mul_sum]
    have outer :
        (∑ i ∈ s, ∑ j ∈ s, w i * w j * (f j * g i))
          = ∑ i ∈ s, (w i * g i) * (∑ j ∈ s, w j * f j) := by
      apply Finset.sum_congr rfl; intro i _; exact inner i
    rw [outer, ← Finset.sum_mul]
  have s4 :
      (∑ i ∈ s, ∑ j ∈ s, w i * w j * (f j * g j))
        = (∑ i ∈ s, w i) * (∑ j ∈ s, w j * f j * g j) := by
    have inner :
        ∀ i, (∑ j ∈ s, w i * w j * (f j * g j))
              = w i * (∑ j ∈ s, w j * f j * g j) := by
      intro i
      have : (∑ j ∈ s, w i * w j * (f j * g j))
          = (∑ j ∈ s, w i * (w j * f j * g j)) := by
        apply Finset.sum_congr rfl; intro j _; ring
      rw [this, ← Finset.mul_sum]
    have outer :
        (∑ i ∈ s, ∑ j ∈ s, w i * w j * (f j * g j))
          = ∑ i ∈ s, w i * (∑ j ∈ s, w j * f j * g j) := by
      apply Finset.sum_congr rfl; intro i _; exact inner i
    rw [outer, ← Finset.sum_mul]
  -- Expand the target double sum.
  have key :
      (∑ i ∈ s, ∑ j ∈ s, w i * w j * ((f i - f j) * (g i - g j)))
        = 2 * ((∑ i ∈ s, w i) * (∑ i ∈ s, w i * f i * g i)
              - (∑ i ∈ s, w i * f i) * (∑ i ∈ s, w i * g i)) := by
    have expand :
        (∑ i ∈ s, ∑ j ∈ s, w i * w j * ((f i - f j) * (g i - g j)))
          =
        (∑ i ∈ s, ∑ j ∈ s,
            (w i * w j * (f i * g i) - w i * w j * (f i * g j)
             - w i * w j * (f j * g i) + w i * w j * (f j * g j))) := by
      apply Finset.sum_congr rfl
      intro i _
      apply Finset.sum_congr rfl
      intro j _
      ring
    rw [expand]
    simp only [Finset.sum_add_distrib, Finset.sum_sub_distrib]
    rw [s1, s2, s3, s4]
    ring
  -- The double sum on the LHS is nonneg (each summand is).
  have h_nonneg :
      0 ≤ (∑ i ∈ s, ∑ j ∈ s, w i * w j * ((f i - f j) * (g i - g j))) := by
    apply Finset.sum_nonneg
    intro i hi
    apply Finset.sum_nonneg
    intro j hj
    have hwi : 0 ≤ w i := hw i hi
    have hwj : 0 ≤ w j := hw j hj
    have hwij : 0 ≤ w i * w j := mul_nonneg hwi hwj
    exact mul_nonneg hwij (hcomono i hi j hj)
  -- Combine: `0 ≤ 2 · (RHS - LHS)`  ⇒  `LHS ≤ RHS`.
  have := key ▸ h_nonneg
  linarith

/-- **Comonotonicity of `r` and `exp(β · r)` for `β ≥ 0`.**

    On any set, the pairs `(r i - r j)` and `(exp(β·r i) - exp(β·r j))`
    always have the same sign, so their product is nonneg. -/
theorem exp_beta_comonotone
    (r : α → ℝ) (β : ℝ) (hβ : 0 ≤ β) (i j : α) :
    0 ≤ (r i - r j) * (Real.exp (β * r i) - Real.exp (β * r j)) := by
  rcases le_total (r j) (r i) with h | h
  · -- `r i ≥ r j`: both factors are `≥ 0`.
    have h1 : 0 ≤ r i - r j := by linarith
    have h2 : β * r j ≤ β * r i := mul_le_mul_of_nonneg_left h hβ
    have h3 : Real.exp (β * r j) ≤ Real.exp (β * r i) :=
      Real.exp_le_exp.mpr h2
    have h4 : 0 ≤ Real.exp (β * r i) - Real.exp (β * r j) := by linarith
    exact mul_nonneg h1 h4
  · -- `r i ≤ r j`: both factors are `≤ 0`; product still `≥ 0`.
    have h1 : r i - r j ≤ 0 := by linarith
    have h2 : β * r i ≤ β * r j := mul_le_mul_of_nonneg_left h hβ
    have h3 : Real.exp (β * r i) ≤ Real.exp (β * r j) :=
      Real.exp_le_exp.mpr h2
    have h4 : Real.exp (β * r i) - Real.exp (β * r j) ≤ 0 := by linarith
    -- Rewrite as `(-(r i - r j)) * (-(exp ... - exp ...))` and apply
    -- `mul_nonneg` to the two nonneg negations.
    have h_eq : (r i - r j) * (Real.exp (β * r i) - Real.exp (β * r j))
        = (-(r i - r j)) * (-(Real.exp (β * r i) - Real.exp (β * r j))) := by
      ring
    rw [h_eq]
    exact mul_nonneg (by linarith) (by linarith)

/-- **CT-2 covariance-nonneg core (Chebyshev / positive-correlation
    form).**

    Let `p : α → ℝ` be a nonneg weight function on a finite index set
    `s`, `r : α → ℝ` a bounded reward, and `β ≥ 0` an inverse
    temperature.  Then

        (∑ i ∈ s, p i · r i) · (∑ i ∈ s, p i · exp(β · r i))
          ≤ (∑ i ∈ s, p i) · (∑ i ∈ s, p i · r i · exp(β · r i)).

    In particular, if `∑ i ∈ s, p i = 1` (probability distribution),
    then `E[r · exp(β·r)] ≥ E[r] · E[exp(β·r)]`. -/
theorem ct2_covariance_nonneg
    (s : Finset α) (p : α → ℝ) (r : α → ℝ) (β : ℝ)
    (hp : ∀ i ∈ s, 0 ≤ p i) (hβ : 0 ≤ β) :
    (∑ i ∈ s, p i * r i) * (∑ i ∈ s, p i * Real.exp (β * r i))
      ≤ (∑ i ∈ s, p i)
          * (∑ i ∈ s, p i * r i * Real.exp (β * r i)) :=
  chebyshev_weighted_correlation s p r (fun i => Real.exp (β * r i))
    hp (fun i _ j _ => exp_beta_comonotone r β hβ i j)

/-- **CT-2 monotone-reward wrapper (Boltzmann update raises expected
    reward).**

    Let `p : α → ℝ` be a probability distribution on a finite set `s`
    (nonneg with total mass `1`), `r : α → ℝ` a bounded reward,
    and `β ≥ 0` an inverse temperature.  Assume the Boltzmann
    normaliser `Z := ∑ i ∈ s, p i · exp(β · r i)` is strictly
    positive (i.e., the support of `p` is not empty).  Then the
    Boltzmann-tilted distribution `p'(x) := p(x) · exp(β · r(x)) / Z`
    has expected reward at least `E_p[r]`:

        (∑ i ∈ s, p i · r i)
          ≤ (∑ i ∈ s, p i · r i · exp(β · r i)) / Z.

    Reason: multiply by `Z > 0`, use `∑ p = 1`, and apply
    `ct2_covariance_nonneg`. -/
theorem ct2_boltzmann_raises_expected_reward
    (s : Finset α) (p : α → ℝ) (r : α → ℝ) (β : ℝ)
    (hp : ∀ i ∈ s, 0 ≤ p i) (hsum : ∑ i ∈ s, p i = 1)
    (hβ : 0 ≤ β)
    (hZ_pos : 0 < ∑ i ∈ s, p i * Real.exp (β * r i)) :
    (∑ i ∈ s, p i * r i)
      ≤ (∑ i ∈ s, p i * r i * Real.exp (β * r i))
          / (∑ i ∈ s, p i * Real.exp (β * r i)) := by
  have h_core := ct2_covariance_nonneg s p r β hp hβ
  -- Multiply the RHS of `h_core` uses `∑ p = 1`, then divide by `Z`.
  rw [hsum, one_mul] at h_core
  rw [le_div_iff₀ hZ_pos]
  exact h_core

end StructuralIntelligenceMathlib
