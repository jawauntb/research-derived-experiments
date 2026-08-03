import Mathlib.Analysis.SpecialFunctions.Log.Basic
import Mathlib.Analysis.Complex.Exponential
import Mathlib.Algebra.Order.GroupWithZero.Basic

/-!
# Structural Intelligence (Mathlib) — Theorem 5 quantitative rate

The load-bearing real-analytic inequality behind Theorem 5 of the
*Structural Intelligence* paper: given a discrete `M`-class hypothesis
family, a per-class failure probability upper-bounded by
`exp(- N / (c*M))`, and the union bound, the family-level failure
probability is at most `M · exp(- N / (c*M))`.  Requiring this bound to
be `≤ ε` and solving for `N` gives the sample-complexity rate

    N  ≥  c · M · log (M / ε).

This file proves the two real-analytic pieces the pure-core companion
project cannot see:

1.  `M · exp(- N / (c*M)) ≤ ε` whenever `N ≥ c · M · log (M / ε)`
    (`theorem5_rate_bound`).
2.  `(1 - 1/(c*M))^N ≤ exp(- N / (c*M))` — the elementary bridge from
    the counting-form binomial slack to the exponential form
    (`one_sub_inv_pow_le_exp_neg_div`).

Both facts use only `Real.exp`, `Real.log`, and elementary monotonicity
lemmas from Mathlib.
-/

namespace StructuralIntelligenceMathlib

open Real

/-- **Theorem 5 quantitative rate (real-analytic form).**

    Let `M ≥ 1` be a class count, `c ≥ 1` a constant, `ε ∈ (0, 1)`
    the target failure probability, and `N` a sample count satisfying
    `N ≥ c · M · log (M / ε)`.  Then

        M · exp(- N / (c · M))  ≤  ε.

    Proof sketch: because `c·M > 0`, the hypothesis on `N` is
    equivalent to `-N / (c·M) ≤ -log (M/ε) = log (ε/M)`; monotonicity
    of `exp` then gives `exp(-N/(c·M)) ≤ ε/M`, and multiplying by
    `M > 0` yields the claim.

    This is the sample-complexity rate that, combined with the union
    bound formalised in the pure-core companion project, closes the
    quantitative half of Theorem 5. -/
theorem theorem5_rate_bound
    (M : ℕ) (c ε N : ℝ)
    (hM : 1 ≤ M) (hc : 1 ≤ c) (hε_pos : 0 < ε) (_hε_lt : ε < 1)
    (hN : c * (M : ℝ) * Real.log ((M : ℝ) / ε) ≤ N) :
    (M : ℝ) * Real.exp (- N / (c * (M : ℝ))) ≤ ε := by
  -- Basic positivity facts.
  have hMpos : (0 : ℝ) < (M : ℝ) := by
    have : (1 : ℝ) ≤ (M : ℝ) := by exact_mod_cast hM
    linarith
  have hcpos : (0 : ℝ) < c := lt_of_lt_of_le zero_lt_one hc
  have hcM_pos : (0 : ℝ) < c * (M : ℝ) := mul_pos hcpos hMpos
  -- Step 1: `log(M/ε) ≤ N/(c*M)` follows from the hypothesis via
  -- `le_div_iff₀'`.
  have hN_div : Real.log ((M : ℝ) / ε) ≤ N / (c * (M : ℝ)) := by
    rw [le_div_iff₀' hcM_pos]
    exact hN
  -- Step 2: negate to get `-N/(c*M) ≤ -log(M/ε) = log(ε/M)`.
  have hε_over_M_pos : (0 : ℝ) < ε / (M : ℝ) := div_pos hε_pos hMpos
  have h_le_log : - N / (c * (M : ℝ)) ≤ Real.log (ε / (M : ℝ)) := by
    have h1 : - (N / (c * (M : ℝ))) ≤ - Real.log ((M : ℝ) / ε) :=
      neg_le_neg hN_div
    have h2 : - Real.log ((M : ℝ) / ε) = Real.log (ε / (M : ℝ)) := by
      rw [← Real.log_inv, inv_div]
    have h3 : - N / (c * (M : ℝ)) = - (N / (c * (M : ℝ))) := by
      rw [neg_div]
    linarith [h2 ▸ h1]
  -- Step 3: exponentiate.
  have h_exp_le : Real.exp (- N / (c * (M : ℝ))) ≤ ε / (M : ℝ) := by
    have h_mono := Real.exp_le_exp.mpr h_le_log
    rwa [Real.exp_log hε_over_M_pos] at h_mono
  -- Step 4: multiply by `M > 0` and simplify `M * (ε/M) = ε`.
  have h_mul :
      (M : ℝ) * Real.exp (- N / (c * (M : ℝ))) ≤ (M : ℝ) * (ε / (M : ℝ)) :=
    mul_le_mul_of_nonneg_left h_exp_le (le_of_lt hMpos)
  have hM_ne : (M : ℝ) ≠ 0 := ne_of_gt hMpos
  have h_simp : (M : ℝ) * (ε / (M : ℝ)) = ε := by
    field_simp
  linarith [h_simp ▸ h_mul]

/-- **Elementary bridge lemma.**

    For any real `x ∈ [0, 1]` and natural `N`, `(1 - x)^N ≤ exp (- N · x)`.
    Combined with `x = 1/(c·M)`, this is the classical step

        (1 - 1/(c·M))^N  ≤  exp(- N / (c·M))

    that lets one pass from the counting/binomial form of the failure
    probability to the exponential form used in `theorem5_rate_bound`.

    Proof strategy: apply `Real.add_one_le_exp` at `-x` to get
    `1 - x ≤ exp(-x)`; both sides are nonneg (since `x ≤ 1`), so
    `pow_le_pow_left₀` raises the inequality to the `N`-th power; then
    `Real.exp_nat_mul` folds `(exp(-x))^N = exp(-N·x)`. -/
theorem one_sub_le_exp_neg_pow
    (x : ℝ) (N : ℕ) (hx_le_one : x ≤ 1) (_hx_nonneg : 0 ≤ x) :
    (1 - x) ^ N ≤ Real.exp (- (N : ℝ) * x) := by
  -- `1 - x ≤ exp (-x)` from `Real.add_one_le_exp`.
  have h_pointwise : 1 - x ≤ Real.exp (- x) := by
    have := Real.add_one_le_exp (-x)
    linarith
  have h_nonneg_lhs : (0 : ℝ) ≤ 1 - x := by linarith
  have h_pow_le :
      (1 - x) ^ N ≤ (Real.exp (- x)) ^ N :=
    pow_le_pow_left₀ h_nonneg_lhs h_pointwise N
  -- Fold `(exp(-x))^N = exp(N * -x) = exp(-N*x)`.
  have h_fold : (Real.exp (- x)) ^ N = Real.exp (- (N : ℝ) * x) := by
    rw [← Real.exp_nat_mul]
    ring_nf
  rw [h_fold] at h_pow_le
  exact h_pow_le

/-- **The specific instance used by Theorem 5.**  With `x = 1/(c·M)`
    for `c ≥ 1` and `M ≥ 1`, we have `x ∈ [0, 1]`, so

        (1 - 1/(c·M))^N  ≤  exp(- N / (c·M)). -/
theorem one_sub_inv_pow_le_exp_neg_div
    (M : ℕ) (c : ℝ) (N : ℕ)
    (hM : 1 ≤ M) (hc : 1 ≤ c) :
    (1 - 1 / (c * (M : ℝ))) ^ N ≤ Real.exp (- (N : ℝ) / (c * (M : ℝ))) := by
  have hMpos : (0 : ℝ) < (M : ℝ) := by
    have : (1 : ℝ) ≤ (M : ℝ) := by exact_mod_cast hM
    linarith
  have hcpos : (0 : ℝ) < c := lt_of_lt_of_le zero_lt_one hc
  have hcM_pos : (0 : ℝ) < c * (M : ℝ) := mul_pos hcpos hMpos
  have hM_ge_one : (1 : ℝ) ≤ (M : ℝ) := by exact_mod_cast hM
  have hcM_ge_one : (1 : ℝ) ≤ c * (M : ℝ) := by
    have : (1 : ℝ) * 1 ≤ c * (M : ℝ) :=
      mul_le_mul hc hM_ge_one zero_le_one (le_trans zero_le_one hc)
    linarith
  -- `x := 1/(c·M)` lies in `[0, 1]`.
  have hx_nonneg : (0 : ℝ) ≤ 1 / (c * (M : ℝ)) := by positivity
  have hx_le_one : 1 / (c * (M : ℝ)) ≤ 1 := by
    rw [div_le_one hcM_pos]
    exact hcM_ge_one
  have h := one_sub_le_exp_neg_pow (1 / (c * (M : ℝ))) N hx_le_one hx_nonneg
  -- Rewrite `- N * (1/(c·M)) = - N / (c·M)`.
  have h_rw : - (N : ℝ) * (1 / (c * (M : ℝ))) = - (N : ℝ) / (c * (M : ℝ)) := by
    field_simp
  rw [h_rw] at h
  exact h

end StructuralIntelligenceMathlib
