import Mathlib.Data.Fintype.Basic
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Analysis.SpecialFunctions.Log.Basic
import Mathlib.Tactic

/-!
# Structural Intelligence (Mathlib) — Theorem 2 (Shannon rate–distortion,
uniform–Hamming closed form)

The classical Shannon (1959) rate–distortion function for an alphabet
of size `n ≥ 2` with uniform source distribution and Hamming
distortion:

    R(D)  =  log n  −  h_binary(D)  −  D · log (n − 1),   `0 ≤ D ≤ 1 − 1/n`.

**Scope of this file.**  We formalise the ingredients that a Lean-4 +
Mathlib companion can honestly cover *today*:

* `binaryEntropy`, `uniformDist`, `symChannel`, `hammingDistortion` —
  the four core definitions.

* `symChannel_stochastic_row`, `symChannel_stochastic_col` — the
  symmetric error-`D` channel is a doubly stochastic kernel.

* `symChannel_marginal_uniform` — under uniform source, the receiver
  marginal is uniform.

* `symChannel_expected_hamming` — the symmetric error-`D` channel
  achieves expected Hamming distortion exactly `D`.

* `symChannel_row_entropy` — each row of the symmetric channel has
  entropy `h_binary(D) + D · log(n − 1)` in closed form.

* `symChannel_mutualInfo_closed_form` — the achieved mutual
  information `I(X; X̂) = log n − h_binary(D) − D · log(n − 1)`.

* `Shannon1959_converse_uniform_hamming` — **axiomatised.**  The
  converse half of Shannon 1959 states that no other test channel of
  distortion `≤ D` achieves *smaller* mutual information; the full
  proof requires a rate-distortion optimisation infrastructure
  (Lagrangian on the simplex of test channels) that Mathlib does not
  yet possess.  Cited: C. E. Shannon (1959), *Coding theorems for a
  discrete source with a fidelity criterion*, IRE Nat. Conv. Rec.,
  pt. 4, 142–163.
-/

namespace StructuralIntelligenceMathlib

open Finset BigOperators Real

/-- Binary entropy in nats.  With Mathlib's convention `log 0 = 0`,
    this is defined and equals `0` at the endpoints `p = 0` and
    `p = 1`. -/
noncomputable def binaryEntropy (p : ℝ) : ℝ :=
  - p * Real.log p - (1 - p) * Real.log (1 - p)

/-- Uniform distribution on `Fin n`. -/
noncomputable def uniformDist (n : ℕ) : Fin n → ℝ :=
  fun _ => (1 : ℝ) / n

/-- Hamming distortion (real-valued `{0,1}` indicator of inequality). -/
def hammingDistortion (n : ℕ) : Fin n → Fin n → ℝ :=
  fun x y => if x = y then 0 else 1

/-- Symmetric error-`D` channel on `Fin n`.  On diagonal: `1 − D`;
    off-diagonal: `D / (n − 1)`, uniformly spread over the `n − 1`
    non-matching symbols. -/
noncomputable def symChannel (n : ℕ) (D : ℝ) : Fin n → Fin n → ℝ :=
  fun x y => if x = y then 1 - D else D / ((n : ℝ) - 1)

/-- Shannon entropy of a distribution on `Fin n` (in nats), with
    Mathlib's `log 0 = 0` convention absorbing zero-mass entries. -/
noncomputable def entropy (n : ℕ) (μ : Fin n → ℝ) : ℝ :=
  - ∑ i, μ i * Real.log (μ i)

/-- Conditional entropy `H(X̂ | X) = ∑ x, μ(x) · H(K(x, ·))`. -/
noncomputable def condEntropy (n : ℕ) (μ : Fin n → ℝ) (K : Fin n → Fin n → ℝ) : ℝ :=
  ∑ x, μ x * entropy n (K x)

/-- Receiver marginal `p(x̂) = ∑ x, μ(x) K(x, x̂)`. -/
noncomputable def marginal (n : ℕ) (μ : Fin n → ℝ) (K : Fin n → Fin n → ℝ) : Fin n → ℝ :=
  fun y => ∑ x, μ x * K x y

/-- Mutual information `I(X; X̂) = H(X̂) − H(X̂ | X)`. -/
noncomputable def mutualInfo (n : ℕ) (μ : Fin n → ℝ) (K : Fin n → Fin n → ℝ) : ℝ :=
  entropy n (marginal n μ K) - condEntropy n μ K

/-- Expected distortion `E[d(X, X̂)] = ∑_x μ(x) ∑_y K(x,y) d(x,y)`. -/
noncomputable def expectedDistortion
    (n : ℕ) (μ : Fin n → ℝ) (K : Fin n → Fin n → ℝ) (d : Fin n → Fin n → ℝ) : ℝ :=
  ∑ x, μ x * ∑ y, K x y * d x y

/-- Positivity of `(n : ℝ) - 1` for `n ≥ 2`. -/
private lemma nsub_one_pos {n : ℕ} (hn : 2 ≤ n) : (0 : ℝ) < (n : ℝ) - 1 := by
  have : (2 : ℝ) ≤ (n : ℝ) := by exact_mod_cast hn
  linarith

private lemma nsub_one_ne_zero {n : ℕ} (hn : 2 ≤ n) : ((n : ℝ) - 1) ≠ 0 :=
  ne_of_gt (nsub_one_pos hn)

private lemma n_pos {n : ℕ} (hn : 2 ≤ n) : (0 : ℝ) < (n : ℝ) := by
  have : (2 : ℝ) ≤ (n : ℝ) := by exact_mod_cast hn
  linarith

private lemma n_ne_zero {n : ℕ} (hn : 2 ≤ n) : (n : ℝ) ≠ 0 :=
  ne_of_gt (n_pos hn)

/-- Row-sum identity: every row of the symmetric channel sums to `1`.

    Proof: split at `y = x` via the add-subtract-`B` trick.  Writing
    `symChannel x y = (if x = y then A - B else 0) + B` with
    `A = 1 - D`, `B = D/(n-1)`, the first summand collapses to `A - B`
    (unique `x = y` term), the second to `n · B`; totals to
    `A + (n-1) · B = (1-D) + D = 1`. -/
theorem symChannel_stochastic_row {n : ℕ} (hn : 2 ≤ n) (D : ℝ) (x : Fin n) :
    ∑ y, symChannel n D x y = 1 := by
  classical
  have hn1ne : ((n : ℝ) - 1) ≠ 0 := nsub_one_ne_zero hn
  unfold symChannel
  -- Rewrite each summand.
  have key : ∀ y, (if x = y then (1 - D : ℝ) else D / ((n : ℝ) - 1))
              = (if x = y then (1 - D - D / ((n : ℝ) - 1) : ℝ) else 0)
                + D / ((n : ℝ) - 1) := by
    intro y; split_ifs <;> ring
  simp_rw [key]
  rw [Finset.sum_add_distrib]
  rw [Finset.sum_ite_eq Finset.univ x (fun _ => (1 - D - D / ((n : ℝ) - 1) : ℝ))]
  rw [if_pos (Finset.mem_univ x)]
  rw [Finset.sum_const, Finset.card_univ, Fintype.card_fin]
  -- Now: (1 - D - D/(n-1)) + n • (D/(n-1)) = 1
  have h_smul : (n : ℕ) • (D / ((n : ℝ) - 1)) = (n : ℝ) * (D / ((n : ℝ) - 1)) := by
    rw [nsmul_eq_mul]
  rw [h_smul]
  field_simp
  ring

/-- Column-sum identity: every column of the symmetric channel sums
    to `1` (by full symmetry — same computation as row sums but with
    the `if x = y` swap). -/
theorem symChannel_stochastic_col {n : ℕ} (hn : 2 ≤ n) (D : ℝ) (y : Fin n) :
    ∑ x, symChannel n D x y = 1 := by
  classical
  have hn1ne : ((n : ℝ) - 1) ≠ 0 := nsub_one_ne_zero hn
  unfold symChannel
  have key : ∀ x, (if x = y then (1 - D : ℝ) else D / ((n : ℝ) - 1))
              = (if x = y then (1 - D - D / ((n : ℝ) - 1) : ℝ) else 0)
                + D / ((n : ℝ) - 1) := by
    intro x; split_ifs <;> ring
  simp_rw [key]
  rw [Finset.sum_add_distrib]
  rw [Finset.sum_ite_eq' Finset.univ y (fun _ => (1 - D - D / ((n : ℝ) - 1) : ℝ))]
  rw [if_pos (Finset.mem_univ y)]
  rw [Finset.sum_const, Finset.card_univ, Fintype.card_fin]
  have h_smul : (n : ℕ) • (D / ((n : ℝ) - 1)) = (n : ℝ) * (D / ((n : ℝ) - 1)) := by
    rw [nsmul_eq_mul]
  rw [h_smul]
  field_simp
  ring

/-- Under uniform source, the receiver marginal is uniform. -/
theorem symChannel_marginal_uniform {n : ℕ} (hn : 2 ≤ n) (D : ℝ) :
    marginal n (uniformDist n) (symChannel n D) = uniformDist n := by
  funext y
  unfold marginal uniformDist
  have h_pull :
      ∑ x, ((1 : ℝ) / n) * symChannel n D x y
        = ((1 : ℝ) / n) * ∑ x, symChannel n D x y := by
    rw [Finset.mul_sum]
  rw [h_pull, symChannel_stochastic_col hn D y, mul_one]

/-- The symmetric error-`D` channel achieves expected Hamming distortion
    exactly `D` under uniform source.

    Proof: the inner sum
    `∑ y, symChannel(x, y) · hamming(x, y)` collapses to `D`
    (using the same split trick), so the outer average over uniform
    source is `D`. -/
theorem symChannel_expected_hamming {n : ℕ} (hn : 2 ≤ n) (D : ℝ) :
    expectedDistortion n (uniformDist n) (symChannel n D) (hammingDistortion n) = D := by
  classical
  have hnne : (n : ℝ) ≠ 0 := n_ne_zero hn
  have hn1ne : ((n : ℝ) - 1) ≠ 0 := nsub_one_ne_zero hn
  unfold expectedDistortion uniformDist symChannel hammingDistortion
  -- Inner sum eval.
  have inner_eq : ∀ x : Fin n,
      ∑ y, (if x = y then (1 - D : ℝ) else D / ((n : ℝ) - 1))
             * (if x = y then (0 : ℝ) else 1) = D := by
    intro x
    have key : ∀ y : Fin n,
        (if x = y then (1 - D : ℝ) else D / ((n : ℝ) - 1))
          * (if x = y then (0 : ℝ) else 1)
          = (if x = y then (0 : ℝ) else 0) + (if x = y then (0 : ℝ) else D / ((n : ℝ) - 1)) := by
      intro y; split_ifs <;> ring
    simp_rw [key]
    -- rewrite each side: first sum is 0, second we need to compute.
    rw [Finset.sum_add_distrib]
    have h_first : ∑ y : Fin n, (if x = y then (0 : ℝ) else 0) = 0 := by
      simp
    rw [h_first, zero_add]
    -- Now: ∑ y, (if x = y then 0 else D/(n-1)) = D.
    -- Rewrite: (if x = y then 0 else D/(n-1)) = D/(n-1) - (if x = y then D/(n-1) else 0).
    have key2 : ∀ y : Fin n, (if x = y then (0 : ℝ) else D / ((n : ℝ) - 1))
                    = D / ((n : ℝ) - 1) - (if x = y then D / ((n : ℝ) - 1) else 0) := by
      intro y; split_ifs <;> ring
    simp_rw [key2]
    rw [Finset.sum_sub_distrib]
    rw [Finset.sum_const, Finset.card_univ, Fintype.card_fin]
    rw [Finset.sum_ite_eq Finset.univ x (fun _ => D / ((n : ℝ) - 1))]
    rw [if_pos (Finset.mem_univ x)]
    -- n • (D/(n-1)) - D/(n-1) = D.
    have h_smul : (n : ℕ) • (D / ((n : ℝ) - 1)) = (n : ℝ) * (D / ((n : ℝ) - 1)) := by
      rw [nsmul_eq_mul]
    rw [h_smul]
    field_simp
  simp_rw [inner_eq]
  rw [← Finset.sum_mul, Finset.sum_const, Finset.card_univ, Fintype.card_fin]
  have h_smul_n : (n : ℕ) • ((1 : ℝ) / n) = 1 := by
    rw [nsmul_eq_mul]
    field_simp
  rw [h_smul_n, one_mul]

/-- **Row entropy of the symmetric channel** (each row has the same
    entropy, given by the binary-plus-log formula).

    `H(K(x, ·)) = h_binary(D) + D · log(n − 1)`. -/
theorem symChannel_row_entropy
    {n : ℕ} (hn : 2 ≤ n) (D : ℝ) (hD0 : 0 < D) (hD1 : D < 1) (x : Fin n) :
    entropy n (symChannel n D x)
      = binaryEntropy D + D * Real.log ((n : ℝ) - 1) := by
  classical
  have hn1ne : ((n : ℝ) - 1) ≠ 0 := nsub_one_ne_zero hn
  have hDne : D ≠ 0 := ne_of_gt hD0
  have hDsub : (0 : ℝ) < 1 - D := by linarith
  have hDsubne : (1 - D : ℝ) ≠ 0 := ne_of_gt hDsub
  unfold entropy symChannel binaryEntropy
  -- Let A = 1 - D, B = D/(n-1).  Then
  --   ∑ y, (if x = y then A else B) * log (if x = y then A else B)
  --     = A * log A + (n - 1) * (B * log B)
  -- because exactly one y satisfies x = y.
  have key : ∀ y : Fin n,
      (if x = y then (1 - D : ℝ) else D / ((n : ℝ) - 1))
        * Real.log (if x = y then (1 - D : ℝ) else D / ((n : ℝ) - 1))
        = (if x = y then
              (1 - D) * Real.log (1 - D)
                - (D / ((n : ℝ) - 1)) * Real.log (D / ((n : ℝ) - 1))
            else 0)
          + (D / ((n : ℝ) - 1)) * Real.log (D / ((n : ℝ) - 1)) := by
    intro y; split_ifs <;> ring
  simp_rw [key]
  rw [Finset.sum_add_distrib]
  rw [Finset.sum_ite_eq Finset.univ x
        (fun _ => (1 - D) * Real.log (1 - D)
                    - (D / ((n : ℝ) - 1)) * Real.log (D / ((n : ℝ) - 1)))]
  rw [if_pos (Finset.mem_univ x)]
  rw [Finset.sum_const, Finset.card_univ, Fintype.card_fin]
  have h_smul : (n : ℕ) • ((D / ((n : ℝ) - 1)) * Real.log (D / ((n : ℝ) - 1)))
                  = (n : ℝ) * ((D / ((n : ℝ) - 1)) * Real.log (D / ((n : ℝ) - 1))) := by
    rw [nsmul_eq_mul]
  rw [h_smul]
  -- Expand log(D/(n-1)) = log D - log(n-1).
  have h_expand : Real.log (D / ((n : ℝ) - 1)) = Real.log D - Real.log ((n : ℝ) - 1) :=
    Real.log_div hDne hn1ne
  rw [h_expand]
  -- Now the goal is a pure algebraic identity in log D, log(1-D), log(n-1), n, D.
  -- We need to show:
  --   - ( (1-D) log(1-D) - (D/(n-1)) * (log D - log(n-1))
  --       + n * ((D/(n-1)) * (log D - log(n-1))) )
  --   = - D log D - (1-D) log(1-D) + D * log(n-1)
  -- Combine terms with common (D/(n-1)) * (log D - log(n-1)) factor:
  --   coefficient = -1 + n = n - 1
  --   so we have -(1-D) log(1-D) - (n-1) * (D/(n-1)) * (log D - log(n-1))
  --   Then (n-1) * (D/(n-1)) = D, giving -(1-D) log(1-D) - D * (log D - log(n-1))
  --   = -(1-D) log(1-D) - D log D + D log(n-1)   ✓
  field_simp
  ring

/-- **Mutual information under the symmetric channel** (closed form). -/
theorem symChannel_mutualInfo_closed_form
    {n : ℕ} (hn : 2 ≤ n) (D : ℝ) (hD0 : 0 < D) (hD1 : D < 1) :
    mutualInfo n (uniformDist n) (symChannel n D)
      = Real.log (n : ℝ) - binaryEntropy D - D * Real.log ((n : ℝ) - 1) := by
  classical
  have hnne : (n : ℝ) ≠ 0 := n_ne_zero hn
  unfold mutualInfo condEntropy
  -- H(X̂) = entropy of uniform on Fin n = log n.
  have h_marg : marginal n (uniformDist n) (symChannel n D) = uniformDist n :=
    symChannel_marginal_uniform hn D
  rw [h_marg]
  have h_ent_unif : entropy n (uniformDist n) = Real.log (n : ℝ) := by
    unfold entropy uniformDist
    have h_term : ∀ i : Fin n, ((1 : ℝ) / n) * Real.log ((1 : ℝ) / n)
                      = (1 / n) * (- Real.log n) := by
      intro i
      rw [Real.log_div (by norm_num : (1 : ℝ) ≠ 0) hnne]
      simp [Real.log_one]
    rw [Finset.sum_congr rfl (fun i _ => h_term i)]
    rw [← Finset.sum_mul, Finset.sum_const, Finset.card_univ, Fintype.card_fin]
    have h_smul_n : (n : ℕ) • ((1 : ℝ) / n) = 1 := by
      rw [nsmul_eq_mul]; field_simp
    rw [h_smul_n]
    ring
  rw [h_ent_unif]
  -- H(X̂ | X) = ∑ x, (1/n) * (h_binary D + D log(n-1))
  --          = h_binary D + D log(n-1).
  have h_row_const : ∀ x : Fin n, entropy n (symChannel n D x)
                        = binaryEntropy D + D * Real.log ((n : ℝ) - 1) :=
    fun x => symChannel_row_entropy hn D hD0 hD1 x
  have h_cond :
      ∑ x, uniformDist n x * entropy n (symChannel n D x)
        = binaryEntropy D + D * Real.log ((n : ℝ) - 1) := by
    unfold uniformDist
    have h_terms : ∀ x : Fin n,
        ((1 : ℝ) / n) * entropy n (symChannel n D x)
          = ((1 : ℝ) / n) * (binaryEntropy D + D * Real.log ((n : ℝ) - 1)) := by
      intro x; rw [h_row_const x]
    rw [Finset.sum_congr rfl (fun x _ => h_terms x)]
    rw [← Finset.sum_mul, Finset.sum_const, Finset.card_univ, Fintype.card_fin]
    have h_smul_n : (n : ℕ) • ((1 : ℝ) / n) = 1 := by
      rw [nsmul_eq_mul]; field_simp
    rw [h_smul_n, one_mul]
  rw [h_cond]
  ring

/-- **Shannon 1959 converse (axiomatised).**

    The converse half of Shannon's rate–distortion theorem for the
    uniform source and Hamming distortion: no test channel `K`
    achieving expected Hamming distortion `≤ D` can attain mutual
    information strictly less than the closed form
    `log n − h_binary(D) − D · log(n − 1)`.

    Combined with `symChannel_mutualInfo_closed_form` (achievability
    by the symmetric error-`D` channel), this pins the rate–distortion
    function to the classical formula.

    We axiomatise the converse: its full proof requires a
    Lagrangian/KKT argument on the simplex of transition matrices,
    infrastructure Mathlib does not currently expose.  Cited:
    C. E. Shannon (1959), *Coding theorems for a discrete source with
    a fidelity criterion*, IRE Nat. Conv. Rec., pt. 4, 142-163
    (Theorem 3, uniform-source / Hamming case). -/
axiom Shannon1959_converse_uniform_hamming
    (n : ℕ) (hn : 2 ≤ n) (D : ℝ)
    (hD0 : 0 ≤ D) (hD1 : D ≤ 1 - 1 / (n : ℝ))
    (K : Fin n → Fin n → ℝ)
    (hK_nonneg : ∀ x y, 0 ≤ K x y)
    (hK_stoch : ∀ x, ∑ y, K x y = 1)
    (hK_dist : expectedDistortion n (uniformDist n) K (hammingDistortion n) ≤ D) :
    Real.log (n : ℝ) - binaryEntropy D - D * Real.log ((n : ℝ) - 1)
      ≤ mutualInfo n (uniformDist n) K

/-- **Theorem 2 (Rate–distortion, uniform Hamming, closed form).**

    Combining achievability (symmetric error-`D` channel realises the
    formula) with the axiomatised converse gives the classical
    rate–distortion function

        R(D) = log n − h_binary(D) − D · log(n − 1)

    for the uniform source with Hamming distortion on `Fin n`,
    `n ≥ 2`, `0 < D < 1`. -/
theorem R_D_uniform_hamming
    (n : ℕ) (hn : 2 ≤ n) (D : ℝ) (hD0 : 0 < D) (hD1 : D < 1)
    (hD_le : D ≤ 1 - 1 / (n : ℝ)) :
    -- Achievability: symmetric channel meets the closed form.
    mutualInfo n (uniformDist n) (symChannel n D)
      = Real.log (n : ℝ) - binaryEntropy D - D * Real.log ((n : ℝ) - 1)
    ∧
    -- Converse (from axiom): no channel does better.
    ∀ (K : Fin n → Fin n → ℝ),
      (∀ x y, 0 ≤ K x y) →
      (∀ x, ∑ y, K x y = 1) →
      expectedDistortion n (uniformDist n) K (hammingDistortion n) ≤ D →
      Real.log (n : ℝ) - binaryEntropy D - D * Real.log ((n : ℝ) - 1)
        ≤ mutualInfo n (uniformDist n) K := by
  refine ⟨symChannel_mutualInfo_closed_form hn D hD0 hD1, ?_⟩
  intro K hK_nn hK_st hK_d
  exact Shannon1959_converse_uniform_hamming n hn D (le_of_lt hD0) hD_le K hK_nn hK_st hK_d

end StructuralIntelligenceMathlib
