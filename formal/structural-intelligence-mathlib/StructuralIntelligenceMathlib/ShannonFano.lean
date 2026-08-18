import Mathlib.Analysis.SpecialFunctions.BinaryEntropy
import Mathlib.Analysis.Convex.Jensen
import Mathlib.Analysis.Convex.SpecificFunctions.Basic
import StructuralIntelligenceMathlib.Theorem2RateDistortion

/-!
# Shannon 1959 converse via Fano (Wave 10)

Honesty.  The `0 < D` converse is **not** a KKT argument.  For a
uniform source and Hamming distortion it is Fano's inequality plus
Jensen on binary entropy plus monotonicity of Mathlib's
`qaryEntropy n` on `[0, 1 - 1/n]`.

`I(X; X̂) = H(X) − H(X | X̂) = log n − H(X | X̂)`, and
`H(X | X̂) ≤ h(P_e) + P_e log(n − 1) ≤ h(D) + D log(n − 1)`
whenever `P_e ≤ D ≤ 1 - 1/n`.
-/

namespace StructuralIntelligenceMathlib

open Finset BigOperators Real Set

set_option maxHeartbeats 4000000

private lemma n_cast_ne_zero {n : ℕ} (hn : 2 ≤ n) : (n : ℝ) ≠ 0 := by
  have : (2 : ℝ) ≤ n := by exact_mod_cast hn
  linarith

lemma binaryEntropy_eq_binEntropy (p : ℝ) :
    binaryEntropy p = Real.binEntropy p := by
  unfold binaryEntropy Real.binEntropy
  simp [Real.log_inv]
  ring

lemma log_nsub_int (n : ℕ) :
    Real.log ((n : ℝ) - 1) = Real.log ((n : ℤ) - 1) := by simp

lemma rdPhi_eq_qary (n : ℕ) (p : ℝ) :
    binaryEntropy p + p * Real.log ((n : ℝ) - 1) = Real.qaryEntropy n p := by
  unfold Real.qaryEntropy
  rw [binaryEntropy_eq_binEntropy]
  have hcast : (n : ℝ) - 1 = (((n : ℤ) - 1 : ℤ) : ℝ) := by
    rw [Int.cast_sub, Int.cast_natCast, Int.cast_one]
  rw [hcast]
  rw [add_comm]

lemma mul_log_mul_of_nonneg {a b : ℝ} (_ha : 0 ≤ a) (_hb : 0 ≤ b) :
    a * b * Real.log (a * b) = a * b * Real.log a + a * b * Real.log b := by
  by_cases ha0 : a = 0
  · simp [ha0, Real.log_zero]
  by_cases hb0 : b = 0
  · simp [hb0, Real.log_zero]
  rw [Real.log_mul ha0 hb0]
  ring

noncomputable def jointEntropy (n : ℕ) (μ : Fin n → ℝ) (K : Fin n → Fin n → ℝ) : ℝ :=
  - ∑ x, ∑ y, μ x * K x y * Real.log (μ x * K x y)

noncomputable def condEntropyRev (n : ℕ) (μ : Fin n → ℝ) (K : Fin n → Fin n → ℝ) : ℝ :=
  jointEntropy n μ K - entropy n (marginal n μ K)

lemma jointEntropy_chain
    {n : ℕ} (μ : Fin n → ℝ) (K : Fin n → Fin n → ℝ)
    (hμ : ∀ x, 0 ≤ μ x) (hK : ∀ x y, 0 ≤ K x y)
    (hK_stoch : ∀ x, ∑ y, K x y = 1) :
    jointEntropy n μ K = entropy n μ + condEntropy n μ K := by
  classical
  unfold jointEntropy entropy condEntropy
  have hterm : ∀ x y,
      μ x * K x y * Real.log (μ x * K x y)
        = μ x * K x y * Real.log (μ x) + μ x * K x y * Real.log (K x y) :=
    fun x y => mul_log_mul_of_nonneg (hμ x) (hK x y)
  simp_rw [hterm]
  rw [Finset.sum_congr rfl (fun x _ => Finset.sum_add_distrib)]
  rw [Finset.sum_add_distrib]
  have hsrc : ∑ x, ∑ y, μ x * K x y * Real.log (μ x) = ∑ x, μ x * Real.log (μ x) := by
    refine Finset.sum_congr rfl ?_
    intro x _
    calc
      ∑ y, μ x * K x y * Real.log (μ x)
          = (μ x * Real.log (μ x)) * ∑ y, K x y := by
            simp [mul_assoc, mul_left_comm, mul_comm, Finset.mul_sum, Finset.sum_mul]
      _ = μ x * Real.log (μ x) := by rw [hK_stoch x, mul_one]
  have hcond : ∑ x, ∑ y, μ x * K x y * Real.log (K x y)
      = ∑ x, μ x * ∑ y, K x y * Real.log (K x y) := by
    refine Finset.sum_congr rfl ?_
    intro x _
    simp [mul_assoc, Finset.mul_sum]
  rw [hsrc, hcond]
  simp only [entropy, mul_neg]
  rw [neg_add, Finset.sum_neg_distrib]

lemma mutualInfo_eq_source_minus_rev
    {n : ℕ} (μ : Fin n → ℝ) (K : Fin n → Fin n → ℝ)
    (hμ : ∀ x, 0 ≤ μ x) (hK : ∀ x y, 0 ≤ K x y)
    (hK_stoch : ∀ x, ∑ y, K x y = 1) :
    mutualInfo n μ K = entropy n μ - condEntropyRev n μ K := by
  unfold mutualInfo condEntropyRev
  rw [jointEntropy_chain μ K hμ hK hK_stoch]
  ring

lemma entropy_le_log_card
    {n : ℕ} (μ : Fin n → ℝ) (S : Finset (Fin n))
    (hμ : ∀ i, 0 ≤ μ i) (hsum : ∑ i, μ i = 1)
    (hsupp : ∀ i, μ i ≠ 0 → i ∈ S) (hSpos : 0 < S.card) :
    entropy n μ ≤ Real.log (S.card : ℝ) := by
  classical
  let t : Finset (Fin n) := Finset.univ.filter (fun i => 0 < μ i)
  have htμ : ∀ i ∈ t, 0 < μ i := fun i hi => (Finset.mem_filter.mp hi).2
  have htsum : ∑ i ∈ t, μ i = 1 := by
    have hsplit := Finset.sum_filter_add_sum_filter_not (s := Finset.univ)
      (p := fun i : Fin n => 0 < μ i) μ
    have hzero : ∑ i ∈ Finset.univ.filter (fun i => ¬ 0 < μ i), μ i = 0 := by
      refine Finset.sum_eq_zero ?_
      intro i hi
      have : ¬ 0 < μ i := (Finset.mem_filter.mp hi).2
      exact le_antisymm (le_of_not_gt this) (hμ i)
    change ∑ x with 0 < μ x, μ x = 1
    linarith [hsplit, hsum, hzero]
  have htsub : t ⊆ S := by
    intro i hi
    exact hsupp i (ne_of_gt (htμ i hi))
  by_cases ht : t.Nonempty
  · have hmem : ∀ i ∈ t, (μ i)⁻¹ ∈ Ioi (0 : ℝ) := fun i hi => inv_pos.mpr (htμ i hi)
    have hjensen :=
      (strictConcaveOn_log_Ioi.concaveOn).le_map_sum
        (fun i hi => (htμ i hi).le) htsum hmem
    have hpts : ∑ i ∈ t, μ i • (μ i)⁻¹ = (t.card : ℝ) := by
      simp only [smul_eq_mul]
      have : ∀ i ∈ t, μ i * (μ i)⁻¹ = 1 :=
        fun i hi => mul_inv_cancel₀ (ne_of_gt (htμ i hi))
      rw [Finset.sum_congr rfl this, Finset.sum_const, nsmul_eq_mul, mul_one]
    have hlogs : ∑ i ∈ t, μ i • Real.log (μ i)⁻¹ = entropy n μ := by
      unfold entropy
      have hrest : ∑ i, μ i * Real.log (μ i) = ∑ i ∈ t, μ i * Real.log (μ i) := by
        apply Eq.symm
        apply Finset.sum_subset (Finset.filter_subset _ Finset.univ)
        intro i _ hi
        have : ¬ 0 < μ i := by simpa [t] using hi
        have hi0 : μ i = 0 := le_antisymm (le_of_not_gt this) (hμ i)
        simp [hi0, Real.log_zero]
      simp only [smul_eq_mul, Real.log_inv, neg_mul]
      have hneg : ∑ i ∈ t, μ i * -Real.log (μ i) = -∑ i ∈ t, μ i * Real.log (μ i) := by
        simp [Finset.sum_neg_distrib]
      rw [hneg, ← hrest]
    have hle : entropy n μ ≤ Real.log (t.card : ℝ) := by
      calc
        entropy n μ = ∑ i ∈ t, μ i • Real.log (μ i)⁻¹ := hlogs.symm
        _ ≤ Real.log (∑ i ∈ t, μ i • (μ i)⁻¹) := hjensen
        _ = Real.log (t.card : ℝ) := by rw [hpts]
    have htpos : (0 : ℝ) < t.card := by exact_mod_cast Finset.card_pos.mpr ht
    have hcard : (t.card : ℝ) ≤ S.card := by exact_mod_cast Finset.card_le_card htsub
    exact hle.trans (Real.log_le_log htpos hcard)
  · have hempty : t = ∅ := Finset.not_nonempty_iff_eq_empty.mp ht
    have : (0 : ℝ) = 1 := by simpa [hempty] using htsum
    exact (zero_ne_one this).elim

lemma entropy_split_error
    {n : ℕ} (hn : 2 ≤ n) (μ : Fin n → ℝ) (y : Fin n)
    (hμ : ∀ i, 0 ≤ μ i) (hsum : ∑ i, μ i = 1) :
    entropy n μ ≤
      binaryEntropy (1 - μ y) + (1 - μ y) * Real.log ((n : ℝ) - 1) := by
  classical
  let pe : ℝ := 1 - μ y
  have hy_le : μ y ≤ 1 := by
    have := Finset.single_le_sum (fun i _ => hμ i) (Finset.mem_univ y)
    simpa [hsum] using this
  have hpe : 0 ≤ pe := sub_nonneg.mpr hy_le
  have herr : ∑ x ∈ Finset.univ.erase y, μ x = pe := by
    have hsplit : ∑ x, μ x = μ y + ∑ x ∈ Finset.univ.erase y, μ x := by
      rw [← Finset.add_sum_erase (s := Finset.univ) μ (Finset.mem_univ y)]
    linarith
  by_cases hpe0 : pe = 0
  · have hy1 : μ y = 1 := by linarith
    have hoff : ∀ x, x ≠ y → μ x = 0 := by
      intro x hxy
      have hnn : ∀ z ∈ Finset.univ.erase y, 0 ≤ μ z := fun z _ => hμ z
      have hz : ∑ z ∈ Finset.univ.erase y, μ z = 0 := by simpa [hpe0] using herr
      exact (Finset.sum_eq_zero_iff_of_nonneg hnn).1 hz x
        (Finset.mem_erase.mpr ⟨hxy, Finset.mem_univ x⟩)
    have hdirac : (μ : Fin n → ℝ) = fun x => if x = y then (1 : ℝ) else 0 := by
      funext x
      by_cases hx : x = y <;> simp [hx, hy1, hoff]
    have hL : entropy n μ = 0 := by rw [hdirac, entropy_dirac]
    have hR : binaryEntropy (1 - μ y) + (1 - μ y) * Real.log ((n : ℝ) - 1) = 0 := by
      rw [show 1 - μ y = pe from rfl, hpe0, binaryEntropy_zero, zero_mul, add_zero]
    linarith
  · have hpepos : 0 < pe := lt_of_le_of_ne hpe (Ne.symm hpe0)
    let r : Fin n → ℝ := fun x => if x = y then 0 else μ x / pe
    have hr0 : r y = 0 := by simp [r]
    have hr_nonneg : ∀ x, 0 ≤ r x := by
      intro x
      by_cases hx : x = y
      · simp [r, hx]
      · simp [r, hx]; exact div_nonneg (hμ x) hpe
    have hr_erase : ∑ x ∈ Finset.univ.erase y, r x = 1 := by
      have hcongr : ∀ x ∈ Finset.univ.erase y, r x = μ x / pe := by
        intro x hx
        simp [r, (Finset.mem_erase.mp hx).1]
      rw [Finset.sum_congr rfl hcongr]
      simp [div_eq_mul_inv, ← Finset.sum_mul, herr, mul_inv_cancel₀ hpe0]
    have hr_univ : ∑ x, r x = 1 := by
      have hsplit : ∑ x, r x = r y + ∑ x ∈ Finset.univ.erase y, r x := by
        rw [← Finset.add_sum_erase (s := Finset.univ) r (Finset.mem_univ y)]
      simpa [hr0, hr_erase] using hsplit
    have hsupp : ∀ x, r x ≠ 0 → x ∈ Finset.univ.erase y := by
      intro x hx
      refine Finset.mem_erase.mpr ⟨?_, Finset.mem_univ x⟩
      intro hxy; simp [r, hxy] at hx
    have hcard : 0 < (Finset.univ.erase y).card := by
      have hceq : (Finset.univ.erase y).card = n - 1 := by
        simp [Finset.card_erase_of_mem (Finset.mem_univ y), Fintype.card_fin]
      have : 0 < n - 1 := Nat.sub_pos_of_lt hn
      simpa [hceq]
    have hHr : entropy n r ≤ Real.log ((n : ℝ) - 1) := by
      have := entropy_le_log_card r (Finset.univ.erase y) hr_nonneg hr_univ hsupp hcard
      have hcc : ((Finset.univ.erase y).card : ℝ) = (n : ℝ) - 1 := by
        have hcardn : (Finset.univ.erase y).card = n - 1 := by
          rw [Finset.card_erase_of_mem (Finset.mem_univ y), Finset.card_univ, Fintype.card_fin]
        rw [hcardn]
        simpa using Nat.cast_sub (R := ℝ) (Nat.one_le_of_lt hn)
      rwa [hcc] at this
    have hgroup : entropy n μ = binaryEntropy pe + pe * entropy n r := by
      unfold entropy binaryEntropy
      have hsplitμ :
          ∑ x, μ x * Real.log (μ x)
            = μ y * Real.log (μ y)
              + ∑ x ∈ Finset.univ.erase y, μ x * Real.log (μ x) := by
        rw [← Finset.add_sum_erase (s := Finset.univ)
          (fun x => μ x * Real.log (μ x)) (Finset.mem_univ y)]
      have hsplitr :
          ∑ x, r x * Real.log (r x)
            = ∑ x ∈ Finset.univ.erase y, r x * Real.log (r x) := by
        have :
            ∑ x, r x * Real.log (r x)
              = r y * Real.log (r y)
                + ∑ x ∈ Finset.univ.erase y, r x * Real.log (r x) := by
          rw [← Finset.add_sum_erase (s := Finset.univ)
            (fun x => r x * Real.log (r x)) (Finset.mem_univ y)]
        simpa [hr0, Real.log_zero] using this
      have hoff :
          ∑ x ∈ Finset.univ.erase y, μ x * Real.log (μ x)
            = pe * Real.log pe
              + pe * ∑ x ∈ Finset.univ.erase y, r x * Real.log (r x) := by
        have hcongr : ∀ x ∈ Finset.univ.erase y,
            μ x * Real.log (μ x) = pe * r x * Real.log (pe * r x) := by
          intro x hx
          have hxy : x ≠ y := (Finset.mem_erase.mp hx).1
          have hμr : μ x = pe * r x := by
            simp [r, hxy]; field_simp [hpe0]
          rw [hμr]
        rw [Finset.sum_congr rfl hcongr]
        have hlog : ∀ x ∈ Finset.univ.erase y,
            pe * r x * Real.log (pe * r x)
              = pe * r x * Real.log pe + pe * r x * Real.log (r x) :=
          fun x _ => mul_log_mul_of_nonneg hpe (hr_nonneg x)
        rw [Finset.sum_congr rfl hlog, Finset.sum_add_distrib]
        have h1 : ∑ x ∈ Finset.univ.erase y, pe * r x * Real.log pe
            = pe * Real.log pe := by
          calc
            ∑ x ∈ Finset.univ.erase y, pe * r x * Real.log pe
                = ∑ x ∈ Finset.univ.erase y, (pe * Real.log pe) * r x := by
                  refine Finset.sum_congr rfl ?_
                  intro x _; ring
            _ = (pe * Real.log pe) * ∑ x ∈ Finset.univ.erase y, r x := by
                  rw [← Finset.mul_sum]
            _ = pe * Real.log pe := by rw [hr_erase, mul_one]
        have h2 : ∑ x ∈ Finset.univ.erase y, pe * r x * Real.log (r x)
            = pe * ∑ x ∈ Finset.univ.erase y, r x * Real.log (r x) := by
          calc
            ∑ x ∈ Finset.univ.erase y, pe * r x * Real.log (r x)
                = ∑ x ∈ Finset.univ.erase y, pe * (r x * Real.log (r x)) := by
                  refine Finset.sum_congr rfl ?_
                  intro x _; ring
            _ = pe * ∑ x ∈ Finset.univ.erase y, r x * Real.log (r x) := by
                  rw [← Finset.mul_sum]
        rw [h1, h2]
      have ha : μ y = 1 - pe := by simp [pe]
      rw [hsplitμ, hoff, ha, hsplitr]
      ring
    rw [hgroup]
    have hlog : 0 ≤ Real.log ((n : ℝ) - 1) :=
      Real.log_nonneg (by
        have : (2 : ℝ) ≤ n := by exact_mod_cast hn
        linarith)
    nlinarith [hHr, hpe]

lemma uniform_nonneg (n : ℕ) (x : Fin n) : 0 ≤ uniformDist n x := by
  unfold uniformDist
  exact div_nonneg (by norm_num) (Nat.cast_nonneg _)

lemma uniform_sum (n : ℕ) (hn : 2 ≤ n) : ∑ x : Fin n, uniformDist n x = 1 := by
  unfold uniformDist
  rw [Finset.sum_const, Finset.card_univ, Fintype.card_fin, nsmul_eq_mul]
  have : (n : ℝ) ≠ 0 := n_cast_ne_zero hn
  field_simp

lemma marginal_nonneg
    {n : ℕ} (μ : Fin n → ℝ) (K : Fin n → Fin n → ℝ)
    (hμ : ∀ x, 0 ≤ μ x) (hK : ∀ x y, 0 ≤ K x y) (y : Fin n) :
    0 ≤ marginal n μ K y :=
  Finset.sum_nonneg fun x _ => mul_nonneg (hμ x) (hK x y)

lemma marginal_sum
    {n : ℕ} (μ : Fin n → ℝ) (K : Fin n → Fin n → ℝ)
    (hK_stoch : ∀ x, ∑ y, K x y = 1) :
    ∑ y, marginal n μ K y = ∑ x, μ x := by
  unfold marginal
  rw [Finset.sum_comm]
  refine Finset.sum_congr rfl ?_
  intro x _
  rw [← Finset.mul_sum, hK_stoch x, mul_one]

noncomputable def posterior (n : ℕ) (μ : Fin n → ℝ) (K : Fin n → Fin n → ℝ)
    (y : Fin n) : Fin n → ℝ :=
  fun x =>
    if marginal n μ K y = 0 then (if x = y then (1 : ℝ) else 0)
    else (μ x * K x y) / marginal n μ K y

lemma posterior_nonneg
    {n : ℕ} (μ : Fin n → ℝ) (K : Fin n → Fin n → ℝ) (y : Fin n)
    (hμ : ∀ x, 0 ≤ μ x) (hK : ∀ x y, 0 ≤ K x y) :
    ∀ x, 0 ≤ posterior n μ K y x := by
  intro x
  unfold posterior
  split_ifs
  · norm_num
  · norm_num
  · exact div_nonneg (mul_nonneg (hμ x) (hK x y)) (marginal_nonneg μ K hμ hK y)

lemma posterior_sum
    {n : ℕ} (μ : Fin n → ℝ) (K : Fin n → Fin n → ℝ) (y : Fin n)
    (_hμ : ∀ x, 0 ≤ μ x) (_hK : ∀ x y, 0 ≤ K x y) :
    ∑ x, posterior n μ K y x = 1 := by
  unfold posterior
  by_cases hm : marginal n μ K y = 0
  · simp [hm]
  · simp [hm]
    rw [← Finset.sum_div]
    exact div_self hm

lemma expected_hamming_row
    {n : ℕ} (K : Fin n → Fin n → ℝ) (x : Fin n)
    (hK_stoch : ∑ y, K x y = 1) :
    ∑ y, K x y * hammingDistortion n x y = 1 - K x x := by
  classical
  unfold hammingDistortion
  have hterm : ∀ y, K x y * (if x = y then (0 : ℝ) else 1) =
      (if x = y then (0 : ℝ) else K x y) := by
    intro y; split_ifs <;> ring
  simp_rw [hterm]
  have hsplit : ∑ y, K x y = K x x + ∑ y ∈ Finset.univ.erase x, K x y := by
    rw [← Finset.add_sum_erase (s := Finset.univ) (K x) (Finset.mem_univ x)]
  have hite : ∑ y, (if x = y then (0 : ℝ) else K x y)
      = ∑ y ∈ Finset.univ.erase x, K x y := by
    have :
        ∑ y, (if x = y then (0 : ℝ) else K x y)
          = (if x = x then (0 : ℝ) else K x x)
            + ∑ y ∈ Finset.univ.erase x, (if x = y then (0 : ℝ) else K x y) := by
      rw [← Finset.add_sum_erase (s := Finset.univ)
        (fun y => if x = y then (0 : ℝ) else K x y) (Finset.mem_univ x)]
    have hoff : ∀ y ∈ Finset.univ.erase x,
        (if x = y then (0 : ℝ) else K x y) = K x y := by
      intro y hy
      exact if_neg (Finset.ne_of_mem_erase hy).symm
    rw [this, if_pos rfl, Finset.sum_congr rfl hoff, zero_add]
  linarith

lemma expected_hamming_eq
    {n : ℕ} (μ : Fin n → ℝ) (K : Fin n → Fin n → ℝ)
    (hK_stoch : ∀ x, ∑ y, K x y = 1) :
    expectedDistortion n μ K (hammingDistortion n) = ∑ x, μ x * (1 - K x x) := by
  unfold expectedDistortion
  refine Finset.sum_congr rfl ?_
  intro x _
  rw [expected_hamming_row K x (hK_stoch x)]

lemma posterior_diag
    {n : ℕ} (μ : Fin n → ℝ) (K : Fin n → Fin n → ℝ) (y : Fin n)
    (hμ : ∀ x, 0 ≤ μ x) (hK : ∀ x y, 0 ≤ K x y) :
    marginal n μ K y * (1 - posterior n μ K y y) =
      marginal n μ K y - μ y * K y y := by
  unfold posterior
  by_cases hm : marginal n μ K y = 0
  · have hy0 : μ y * K y y = 0 := by
      have hnn : ∀ x, 0 ≤ μ x * K x y := fun x => mul_nonneg (hμ x) (hK x y)
      have hsum0 : ∑ x, μ x * K x y = 0 := by simpa [marginal] using hm
      have := (Finset.sum_eq_zero_iff_of_nonneg
        (fun x _ => hnn x)).1 (by simpa using hsum0) y (Finset.mem_univ y)
      exact this
    simp [hm, hy0]
  ·
    -- `posterior` was already unfolded; reduce the `m ≠ 0` branch.
    simp only [hm, ↓reduceIte]
    field_simp [hm]

lemma weighted_error_eq_expected
    {n : ℕ} (μ : Fin n → ℝ) (K : Fin n → Fin n → ℝ)
    (hμ : ∀ x, 0 ≤ μ x) (hK : ∀ x y, 0 ≤ K x y)
    (hK_stoch : ∀ x, ∑ y, K x y = 1) (hμsum : ∑ x, μ x = 1) :
    ∑ y, marginal n μ K y * (1 - posterior n μ K y y)
      = expectedDistortion n μ K (hammingDistortion n) := by
  have hleft : ∑ y, marginal n μ K y * (1 - posterior n μ K y y)
      = ∑ y, (marginal n μ K y - μ y * K y y) := by
    refine Finset.sum_congr rfl ?_
    intro y _
    exact posterior_diag μ K y hμ hK
  rw [hleft, Finset.sum_sub_distrib, marginal_sum μ K hK_stoch, hμsum]
  rw [expected_hamming_eq μ K hK_stoch]
  have hright : ∑ x, μ x * (1 - K x x) = 1 - ∑ x, μ x * K x x := by
    have hterm : ∀ x, μ x * (1 - K x x) = μ x - μ x * K x x := fun x => by ring
    rw [Finset.sum_congr rfl (fun x _ => hterm x), Finset.sum_sub_distrib, hμsum]
  linarith

lemma condEntropyRev_eq_avg
    {n : ℕ} (μ : Fin n → ℝ) (K : Fin n → Fin n → ℝ)
    (hμ : ∀ x, 0 ≤ μ x) (hK : ∀ x y, 0 ≤ K x y) :
    condEntropyRev n μ K
      = ∑ y, marginal n μ K y * entropy n (posterior n μ K y) := by
  classical
  unfold condEntropyRev jointEntropy entropy
  -- joint = -∑_{x,y} μK log(μK)
  -- H(m) = -∑_y m log m
  -- goal: joint - H(m) = ∑_y m * (-∑_x p log p) = -∑_{x,y} m p log p
  have hinner : ∀ y,
      ∑ x, μ x * K x y * Real.log (μ x * K x y)
        = marginal n μ K y * Real.log (marginal n μ K y)
          + marginal n μ K y * ∑ x, posterior n μ K y x
              * Real.log (posterior n μ K y x) := by
    intro y
    by_cases hm : marginal n μ K y = 0
    · have hterm0 : ∀ x, μ x * K x y = 0 := by
        intro x
        have hnn : ∀ z, 0 ≤ μ z * K z y := fun z => mul_nonneg (hμ z) (hK z y)
        have hsum0 : ∑ z, μ z * K z y = 0 := by simpa [marginal] using hm
        exact (Finset.sum_eq_zero_iff_of_nonneg
          (fun z _ => hnn z)).1 (by simpa using hsum0) x (Finset.mem_univ x)
      have hL : ∑ x, μ x * K x y * Real.log (μ x * K x y) = 0 := by
        refine Finset.sum_eq_zero ?_
        intro x _
        simp [hterm0 x, Real.log_zero]
      have hR1 : marginal n μ K y * Real.log (marginal n μ K y) = 0 := by
        simp [hm, Real.log_zero]
      have hR2 : posterior n μ K y = fun x => if x = y then (1 : ℝ) else 0 := by
        funext x; simp [posterior, hm]
      have hR3 : ∑ x, posterior n μ K y x * Real.log (posterior n μ K y x) = 0 := by
        refine Finset.sum_eq_zero ?_
        intro x _
        by_cases hx : x = y
        · simp [posterior, hm, hx]
        · simp [posterior, hm, hx]
      simp [hL, hR1, hm, hR3]
    · have hmpos : 0 < marginal n μ K y :=
        lt_of_le_of_ne (marginal_nonneg μ K hμ hK y) (Ne.symm hm)
      have hp : ∀ x, posterior n μ K y x = (μ x * K x y) / marginal n μ K y := by
        intro x; simp [posterior, hm]
      have hμK : ∀ x, μ x * K x y = marginal n μ K y * posterior n μ K y x := by
        intro x
        rw [hp x]
        field_simp [hm]
      have hcongr : ∀ x,
          μ x * K x y * Real.log (μ x * K x y)
            = marginal n μ K y * posterior n μ K y x
                * Real.log (marginal n μ K y * posterior n μ K y x) := by
        intro x
        rw [hμK x]
      simp_rw [hcongr]
      have hlog : ∀ x,
          marginal n μ K y * posterior n μ K y x
              * Real.log (marginal n μ K y * posterior n μ K y x)
            = marginal n μ K y * posterior n μ K y x * Real.log (marginal n μ K y)
              + marginal n μ K y * posterior n μ K y x
                  * Real.log (posterior n μ K y x) :=
        fun x => mul_log_mul_of_nonneg (marginal_nonneg μ K hμ hK y)
          (posterior_nonneg μ K y hμ hK x)
      simp_rw [hlog, Finset.sum_add_distrib]
      have h1 : ∑ x, marginal n μ K y * posterior n μ K y x * Real.log (marginal n μ K y)
          = marginal n μ K y * Real.log (marginal n μ K y) := by
        calc
          ∑ x, marginal n μ K y * posterior n μ K y x * Real.log (marginal n μ K y)
              = ∑ x, (marginal n μ K y * Real.log (marginal n μ K y))
                  * posterior n μ K y x := by
                refine Finset.sum_congr rfl ?_
                intro x _; ring
          _ = (marginal n μ K y * Real.log (marginal n μ K y))
                * ∑ x, posterior n μ K y x := by
                rw [← Finset.mul_sum]
          _ = marginal n μ K y * Real.log (marginal n μ K y) := by
                rw [posterior_sum μ K y hμ hK, mul_one]
      have h2 : ∑ x, marginal n μ K y * posterior n μ K y x
            * Real.log (posterior n μ K y x)
          = marginal n μ K y * ∑ x, posterior n μ K y x
              * Real.log (posterior n μ K y x) := by
        simp [mul_assoc, Finset.mul_sum]
      rw [h1, h2]
  have hsum_xy :
      ∑ x, ∑ y, μ x * K x y * Real.log (μ x * K x y)
        = ∑ y, ∑ x, μ x * K x y * Real.log (μ x * K x y) :=
    Finset.sum_comm
  rw [hsum_xy, Finset.sum_congr rfl (fun y _ => hinner y), Finset.sum_add_distrib]
  simp only [entropy, Finset.sum_neg_distrib, mul_neg]
  ring

lemma fano_avg
    {n : ℕ} (hn : 2 ≤ n) (μ : Fin n → ℝ) (K : Fin n → Fin n → ℝ)
    (hμ : ∀ x, 0 ≤ μ x) (hK : ∀ x y, 0 ≤ K x y)
    (hK_stoch : ∀ x, ∑ y, K x y = 1) (hμsum : ∑ x, μ x = 1) :
    condEntropyRev n μ K
      ≤ binaryEntropy (expectedDistortion n μ K (hammingDistortion n))
        + expectedDistortion n μ K (hammingDistortion n)
          * Real.log ((n : ℝ) - 1) := by
  classical
  let m : Fin n → ℝ := marginal n μ K
  let pe : Fin n → ℝ := fun y => 1 - posterior n μ K y y
  have hm_nonneg : ∀ y, 0 ≤ m y := fun y => marginal_nonneg μ K hμ hK y
  have hmsum : ∑ y, m y = 1 := by
    simpa [m] using marginal_sum μ K hK_stoch ▸ hμsum
  have hpost_sum : ∀ y, ∑ x, posterior n μ K y x = 1 :=
    fun y => posterior_sum μ K y hμ hK
  have hpost_nn : ∀ y x, 0 ≤ posterior n μ K y x :=
    fun y x => posterior_nonneg μ K y hμ hK x
  have hpost_le : ∀ y, posterior n μ K y y ≤ 1 := by
    intro y
    have := Finset.single_le_sum (fun x _ => hpost_nn y x) (Finset.mem_univ y)
    simpa [hpost_sum y] using this
  have hpe_nn : ∀ y, 0 ≤ pe y := fun y => sub_nonneg.mpr (hpost_le y)
  have hpe_le : ∀ y, pe y ≤ 1 := by
    intro y
    have : 0 ≤ posterior n μ K y y := hpost_nn y y
    simp [pe]; linarith
  have hsplit : ∀ y,
      entropy n (posterior n μ K y)
        ≤ binaryEntropy (pe y) + pe y * Real.log ((n : ℝ) - 1) :=
    fun y => entropy_split_error hn (posterior n μ K y) y (hpost_nn y) (hpost_sum y)
  rw [condEntropyRev_eq_avg μ K hμ hK]
  have havg :
      ∑ y, m y * entropy n (posterior n μ K y)
        ≤ ∑ y, m y * (binaryEntropy (pe y) + pe y * Real.log ((n : ℝ) - 1)) := by
    refine Finset.sum_le_sum ?_
    intro y _
    exact mul_le_mul_of_nonneg_left (hsplit y) (hm_nonneg y)
  refine le_trans havg ?_
  have hsplit2 :
      ∑ y, m y * (binaryEntropy (pe y) + pe y * Real.log ((n : ℝ) - 1))
        = ∑ y, m y * binaryEntropy (pe y)
          + (∑ y, m y * pe y) * Real.log ((n : ℝ) - 1) := by
    have hterm : ∀ y,
        m y * (binaryEntropy (pe y) + pe y * Real.log ((n : ℝ) - 1))
          = m y * binaryEntropy (pe y)
            + m y * pe y * Real.log ((n : ℝ) - 1) := fun y => by ring
    rw [Finset.sum_congr rfl (fun y _ => hterm y), Finset.sum_add_distrib]
    have hassoc : ∀ y, m y * pe y * Real.log ((n : ℝ) - 1)
        = (m y * pe y) * Real.log ((n : ℝ) - 1) := fun y => by ring
    rw [Finset.sum_congr rfl (fun y _ => hassoc y), Finset.sum_mul]
  rw [hsplit2]
  have hPe : ∑ y, m y * pe y = expectedDistortion n μ K (hammingDistortion n) := by
    simpa [m, pe] using weighted_error_eq_expected μ K hμ hK hK_stoch hμsum
  have hPe_nn : 0 ≤ expectedDistortion n μ K (hammingDistortion n) := by
    rw [← hPe]
    exact Finset.sum_nonneg fun y _ => mul_nonneg (hm_nonneg y) (hpe_nn y)
  have hlog : 0 ≤ Real.log ((n : ℝ) - 1) :=
    Real.log_nonneg (by
      have : (2 : ℝ) ≤ n := by exact_mod_cast hn
      linarith)
  -- Jensen: ∑ m · h(pe) ≤ h(∑ m · pe)
  have hmem : ∀ y ∈ Finset.univ, pe y ∈ Icc (0 : ℝ) 1 :=
    fun y _ => ⟨hpe_nn y, hpe_le y⟩
  have hjensen :=
    (strictConcave_binEntropy.concaveOn).le_map_sum
      (t := Finset.univ) (w := m) (p := pe)
      (fun i _ => hm_nonneg i) hmsum hmem
  have hj : ∑ y, m y * Real.binEntropy (pe y)
      ≤ Real.binEntropy (∑ y, m y * pe y) := by
    simpa [smul_eq_mul] using hjensen
  have hbin : ∑ y, m y * binaryEntropy (pe y)
      ≤ binaryEntropy (∑ y, m y * pe y) := by
    simpa [binaryEntropy_eq_binEntropy] using hj
  rw [hPe] at hbin
  nlinarith [hbin, hPe_nn, hlog]

lemma qary_mono
    {n : ℕ} (hn : 2 ≤ n) {p q : ℝ}
    (hp0 : 0 ≤ p) (hq : p ≤ q) (hq1 : q ≤ 1 - 1 / (n : ℝ)) :
    binaryEntropy p + p * Real.log ((n : ℝ) - 1)
      ≤ binaryEntropy q + q * Real.log ((n : ℝ) - 1) := by
  have hp1 : p ≤ 1 - 1 / (n : ℝ) := hq.trans hq1
  have hmono : MonotoneOn (qaryEntropy n) (Icc (0 : ℝ) (1 - 1 / (n : ℝ))) :=
    (qaryEntropy_strictMonoOn (q := n) hn).monotoneOn
  have hpI : p ∈ Icc (0 : ℝ) (1 - 1 / (n : ℝ)) := ⟨hp0, hp1⟩
  have hqI : q ∈ Icc (0 : ℝ) (1 - 1 / (n : ℝ)) := ⟨hp0.trans hq, hq1⟩
  have := hmono hpI hqI hq
  simpa [rdPhi_eq_qary] using this

/-- **Shannon 1959 converse (uniform Hamming).**  Fano + Jensen +
    `qaryEntropy` monotonicity.  No KKT. -/
theorem Shannon1959_converse_uniform_hamming
    (n : ℕ) (hn : 2 ≤ n) (D : ℝ)
    (_hD0 : 0 ≤ D) (hD1 : D ≤ 1 - 1 / (n : ℝ))
    (K : Fin n → Fin n → ℝ)
    (hK_nonneg : ∀ x y, 0 ≤ K x y)
    (hK_stoch : ∀ x, ∑ y, K x y = 1)
    (hK_dist : expectedDistortion n (uniformDist n) K (hammingDistortion n) ≤ D) :
    Real.log (n : ℝ) - binaryEntropy D - D * Real.log ((n : ℝ) - 1)
      ≤ mutualInfo n (uniformDist n) K := by
  have hμ : ∀ x, 0 ≤ uniformDist n x := uniform_nonneg n
  have hμsum := uniform_sum n hn
  have hI := mutualInfo_eq_source_minus_rev (uniformDist n) K hμ hK_nonneg hK_stoch
  rw [hI, entropy_uniform n hn]
  have hFano := fano_avg hn (uniformDist n) K hμ hK_nonneg hK_stoch hμsum
  set Pe := expectedDistortion n (uniformDist n) K (hammingDistortion n)
  have hPe0 : 0 ≤ Pe := by
    unfold Pe expectedDistortion
    exact Finset.sum_nonneg fun x _ =>
      mul_nonneg (hμ x) (Finset.sum_nonneg fun y _ =>
        mul_nonneg (hK_nonneg x y) (by
          unfold hammingDistortion; split_ifs <;> norm_num))
  have hPeD : Pe ≤ D := hK_dist
  have hmono := qary_mono hn hPe0 hPeD hD1
  linarith

/-- **Theorem 2 (Rate–distortion, uniform Hamming, closed form).**

    Achievability (symmetric error-`D` channel) plus the Fano converse. -/
theorem R_D_uniform_hamming
    (n : ℕ) (hn : 2 ≤ n) (D : ℝ) (hD0 : 0 < D) (hD1 : D < 1)
    (hD_le : D ≤ 1 - 1 / (n : ℝ)) :
    mutualInfo n (uniformDist n) (symChannel n D)
      = Real.log (n : ℝ) - binaryEntropy D - D * Real.log ((n : ℝ) - 1)
    ∧
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
