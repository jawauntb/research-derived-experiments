import StructuralIntelligence.Basic

/-!
# Structural Intelligence — coupon-collector pigeonhole

The strictly combinatorial content of the coupon-collector step in
Theorem 5:  a sequence of `N` draws from an `M`-element universe cannot
cover the universe when `N < M`.

Formally we prove the equivalent function-theoretic statement: if
`f : Fin N → Fin M` covers `Fin M` (every `i : Fin M` is hit), then
`M ≤ N`.

The strategy is standard:
1.  Sum the characteristic functions of `f`'s preimages: for every
    `L : List (Fin M)`, `Σ_{i : Fin M} count i L = L.length`.
2.  If `f` covers `Fin M` then every summand is `≥ 1`, so the total
    is `≥ M`.

Everything is proven in pure Lean 4 core.
-/

namespace StructuralIntelligence

/-- Number of occurrences of `i : Fin M` in a `List (Fin M)`. -/
def countAt {M : Nat} (i : Fin M) (L : List (Fin M)) : Nat :=
  L.countP (fun x => decide (x = i))

@[simp] theorem countAt_nil {M : Nat} (i : Fin M) :
    countAt i ([] : List (Fin M)) = 0 := rfl

theorem countAt_cons {M : Nat} (i : Fin M) (x : Fin M) (rest : List (Fin M)) :
    countAt i (x :: rest) = countAt i rest + (if x = i then 1 else 0) := by
  simp [countAt, List.countP_cons]

theorem one_le_countAt_of_mem {M : Nat} {i : Fin M} :
    ∀ {L : List (Fin M)}, i ∈ L → 1 ≤ countAt i L
  | [], h => absurd h List.not_mem_nil
  | x :: rest, h => by
      rcases List.mem_cons.mp h with hx | hrest
      · rw [countAt_cons]
        have hind : (if x = i then (1 : Nat) else 0) = 1 := by simp [hx]
        rw [hind]
        exact Nat.le_add_left _ _
      · have ih := one_le_countAt_of_mem hrest
        rw [countAt_cons]
        exact Nat.le_add_right_of_le ih

/-- Sum over `Fin M` of the indicator "is this element `i`?" is exactly `1`. -/
theorem sumFin_indicator_eq_one {M : Nat} (x : Fin M) :
    sumFin M (fun i => if x = i then 1 else 0) = 1 := by
  induction M with
  | zero => exact x.elim0
  | succ M ih =>
    rw [sumFin_succ]
    match x with
    | ⟨0, hx⟩ =>
      have hzero : ((⟨0, hx⟩ : Fin (M + 1)) = 0) := by
        apply Fin.ext; rfl
      simp only [hzero, if_true]
      have hEq :
          (fun i : Fin M =>
              if (0 : Fin (M + 1)) = i.succ then (1 : Nat) else 0)
            = (fun _ : Fin M => 0) := by
        funext i
        have hne : (0 : Fin (M + 1)) ≠ i.succ := by
          intro heq
          have hv := congrArg Fin.val heq
          simp [Fin.succ] at hv
        simp [hne]
      rw [hEq, sumFin_zero_fn]
    | ⟨k + 1, hk⟩ =>
      have h0 : ((⟨k + 1, hk⟩ : Fin (M + 1)) = 0) = False := by
        apply propext
        constructor
        · intro heq
          have hv := congrArg Fin.val heq
          simp at hv
        · exact False.elim
      simp only [h0, if_false]
      have hshift :
          (fun i : Fin M =>
              if (⟨k + 1, hk⟩ : Fin (M + 1)) = i.succ then (1 : Nat) else 0)
            = (fun i : Fin M =>
                if (⟨k, Nat.lt_of_succ_lt_succ hk⟩ : Fin M) = i then 1 else 0) := by
        funext i
        by_cases heq : (⟨k, Nat.lt_of_succ_lt_succ hk⟩ : Fin M) = i
        · have hsucc : (⟨k + 1, hk⟩ : Fin (M + 1)) = i.succ := by
            apply Fin.ext
            have hv : k = i.val := by
              have := congrArg Fin.val heq
              simpa using this
            simp [Fin.succ, hv]
          simp [heq, hsucc]
        · have hne : (⟨k + 1, hk⟩ : Fin (M + 1)) ≠ i.succ := by
            intro hsucc
            apply heq
            apply Fin.ext
            have := congrArg Fin.val hsucc
            have hi : k + 1 = i.val + 1 := by simpa [Fin.succ] using this
            exact Nat.succ.inj hi
          simp [heq, hne]
      rw [hshift, ih]

/-- For any `L : List (Fin M)`, summing `countAt i L` over `i : Fin M`
    recovers `L.length`. -/
theorem sumFin_countAt_eq_length {M : Nat} (L : List (Fin M)) :
    sumFin M (fun i => countAt i L) = L.length := by
  induction L with
  | nil =>
    -- Sum of zero function is zero, and `[].length = 0`.
    have hEq :
        (fun i : Fin M => countAt i ([] : List (Fin M)))
          = (fun _ : Fin M => 0) := by
      funext i; exact countAt_nil i
    rw [hEq, sumFin_zero_fn]
    rfl
  | cons x rest ih =>
    have hpt : ∀ i : Fin M,
        countAt i (x :: rest) = countAt i rest + (if x = i then 1 else 0) := by
      intro i; exact countAt_cons i x rest
    calc sumFin M (fun i => countAt i (x :: rest))
        = sumFin M (fun i => countAt i rest + (if x = i then 1 else 0)) := by
            apply congrArg; funext i; exact hpt i
      _ = sumFin M (fun i => countAt i rest)
            + sumFin M (fun i => if x = i then 1 else 0) := sumFin_add M _ _
      _ = rest.length + 1 := by
            rw [ih, sumFin_indicator_eq_one]
      _ = (x :: rest).length := by
            rw [List.length_cons]

/-- **Counting pigeonhole.** If every `i : Fin M` occurs in `L : List (Fin M)`,
    then `M ≤ L.length`. -/
theorem length_ge_of_covers {M : Nat} (L : List (Fin M))
    (h : ∀ i : Fin M, i ∈ L) : M ≤ L.length := by
  have hge : ∀ i : Fin M, 1 ≤ countAt i L := fun i => one_le_countAt_of_mem (h i)
  have hsum : sumFin M (fun _ => 1) ≤ sumFin M (fun i => countAt i L) :=
    sumFin_le_sumFin hge
  have h1 : sumFin M (fun _ : Fin M => 1) = M := sumFin_const_one M
  have hlen : sumFin M (fun i => countAt i L) = L.length :=
    sumFin_countAt_eq_length L
  calc M = sumFin M (fun _ : Fin M => 1) := h1.symm
    _ ≤ sumFin M (fun i => countAt i L) := hsum
    _ = L.length := hlen

/-- Length of `Fin.foldr n (fun j acc => f j :: acc) []` equals `n`. -/
theorem length_foldr_cons {M : Nat} :
    ∀ (n : Nat) (f : Fin n → Fin M),
      (Fin.foldr n (fun j acc => f j :: acc) ([] : List (Fin M))).length = n
  | 0, _ => rfl
  | n + 1, f => by
      rw [Fin.foldr_succ]
      show ((f 0) :: (Fin.foldr n (fun j acc => f j.succ :: acc) [])).length
        = n + 1
      rw [List.length_cons, length_foldr_cons n (fun j => f j.succ)]

/-- Every image value `f j` appears in the image list built from `f`. -/
theorem mem_foldr_cons {M : Nat} :
    ∀ (n : Nat) (f : Fin n → Fin M) (j : Fin n),
      f j ∈ (Fin.foldr n (fun j acc => f j :: acc) ([] : List (Fin M)))
  | 0, _, j => j.elim0
  | n + 1, f, j => by
      rw [Fin.foldr_succ]
      show f j ∈ (f 0 :: Fin.foldr n (fun j' acc => f j'.succ :: acc) [])
      match j with
      | ⟨0, _⟩ =>
        have h0 : f ⟨0, Nat.succ_pos _⟩ = f 0 := by
          apply congrArg; apply Fin.ext; rfl
        rw [h0]
        exact List.mem_cons_self
      | ⟨k + 1, hk⟩ =>
        have heq :
            f ⟨k + 1, hk⟩
              = (fun j' : Fin n => f j'.succ)
                  ⟨k, Nat.lt_of_succ_lt_succ hk⟩ := by
          apply congrArg; apply Fin.ext; rfl
        rw [heq]
        exact List.mem_cons_of_mem _
          (mem_foldr_cons n (fun j' => f j'.succ)
              ⟨k, Nat.lt_of_succ_lt_succ hk⟩)

/-- **Coupon-collector pigeonhole (function form).**  If a sequence
    `f : Fin N → Fin M` covers `Fin M` — every `i : Fin M` is hit —
    then `M ≤ N`.

    Equivalently: with `N < M` draws you can never hit all `M`
    coupons.  This is the deterministic core of the coupon-collector
    step in Theorem 5. -/
theorem coupon_collector_pigeonhole
    {N M : Nat} (f : Fin N → Fin M)
    (cover : ∀ i : Fin M, ∃ j : Fin N, f j = i) :
    M ≤ N := by
  let L : List (Fin M) :=
    Fin.foldr N (fun j acc => f j :: acc) []
  have hlen : L.length = N := length_foldr_cons N f
  have hmem : ∀ i : Fin M, i ∈ L := by
    intro i
    obtain ⟨j, hj⟩ := cover i
    have h := mem_foldr_cons N f j
    rw [hj] at h
    exact h
  have := length_ge_of_covers L hmem
  rw [hlen] at this
  exact this

end StructuralIntelligence
