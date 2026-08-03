/-!
# Structural Intelligence — basic combinatorial utilities

Helpers for summing `Nat`-valued functions and taking `Bool`-valued disjunctions
over `Fin M`.  Everything here is pure Lean 4 core (no `Mathlib`).
-/

namespace StructuralIntelligence

/-- Sum a `Nat`-valued function over `Fin M`. -/
def sumFin (M : Nat) (f : Fin M → Nat) : Nat :=
  Fin.foldr M (fun i acc => f i + acc) 0

/-- Disjunction of a `Bool`-valued predicate over `Fin M`. -/
def anyFin (M : Nat) (p : Fin M → Bool) : Bool :=
  Fin.foldr M (fun i acc => p i || acc) false

@[simp] theorem sumFin_zero (f : Fin 0 → Nat) : sumFin 0 f = 0 := rfl

theorem sumFin_succ (M : Nat) (f : Fin (M + 1) → Nat) :
    sumFin (M + 1) f = f 0 + sumFin M (fun i => f i.succ) := by
  simp [sumFin, Fin.foldr_succ]

@[simp] theorem anyFin_zero (p : Fin 0 → Bool) : anyFin 0 p = false := rfl

theorem anyFin_succ (M : Nat) (p : Fin (M + 1) → Bool) :
    anyFin (M + 1) p = (p 0 || anyFin M (fun i => p i.succ)) := by
  simp [anyFin, Fin.foldr_succ]

/-- The sum of the zero function is zero. -/
theorem sumFin_zero_fn (M : Nat) :
    sumFin M (fun _ : Fin M => (0 : Nat)) = 0 := by
  induction M with
  | zero => rfl
  | succ M ih =>
    rw [sumFin_succ]
    show (0 : Nat) + sumFin M (fun i : Fin M => (0 : Nat)) = 0
    rw [ih]

/-- Sum of the constant 1. -/
theorem sumFin_const_one (M : Nat) : sumFin M (fun _ => 1) = M := by
  induction M with
  | zero => rfl
  | succ M ih =>
    rw [sumFin_succ]
    simp [ih, Nat.add_comm]

/-- `1 ≤ f i` for some `i` gives `1 ≤ sumFin M f`. -/
theorem one_le_sumFin_of_index {M : Nat} (f : Fin M → Nat)
    (i : Fin M) (h : 1 ≤ f i) : 1 ≤ sumFin M f := by
  induction M with
  | zero => exact i.elim0
  | succ M ih =>
    rw [sumFin_succ]
    match i, h with
    | ⟨0, _⟩, h =>
      have hf0 : 1 ≤ f 0 := by
        have h0 : ((⟨0, Nat.succ_pos _⟩ : Fin (M + 1)) : Fin (M + 1)) = 0 := by
          apply Fin.ext; rfl
        rw [h0] at h; exact h
      exact Nat.le_trans hf0 (Nat.le_add_right _ _)
    | ⟨k + 1, hk⟩, h =>
      have ih' : 1 ≤ sumFin M (fun i => f i.succ) := by
        have hf : 1 ≤ (fun i : Fin M => f i.succ) ⟨k, Nat.lt_of_succ_lt_succ hk⟩ := by
          show 1 ≤ f (⟨k, Nat.lt_of_succ_lt_succ hk⟩ : Fin M).succ
          have : ((⟨k, Nat.lt_of_succ_lt_succ hk⟩ : Fin M).succ)
              = (⟨k + 1, hk⟩ : Fin (M + 1)) := by
            apply Fin.ext; rfl
          rw [this]; exact h
        exact ih (fun i => f i.succ) ⟨k, Nat.lt_of_succ_lt_succ hk⟩ hf
      exact Nat.le_trans ih' (Nat.le_add_left _ _)

/-- `sumFin` distributes over pointwise addition. -/
theorem sumFin_add (M : Nat) (f g : Fin M → Nat) :
    sumFin M (fun i => f i + g i) = sumFin M f + sumFin M g := by
  induction M with
  | zero => rfl
  | succ M ih =>
    simp only [sumFin_succ, ih]
    ac_rfl

/-- Pointwise monotonicity of `sumFin`. -/
theorem sumFin_le_sumFin {M : Nat} {f g : Fin M → Nat}
    (h : ∀ i, f i ≤ g i) : sumFin M f ≤ sumFin M g := by
  induction M with
  | zero => exact Nat.le_refl _
  | succ M ih =>
    rw [sumFin_succ, sumFin_succ]
    exact Nat.add_le_add (h 0) (ih fun i => h i.succ)

/-- `anyFin M p = true` iff some index witnesses `p`. -/
theorem anyFin_eq_true_iff (M : Nat) (p : Fin M → Bool) :
    anyFin M p = true ↔ ∃ i : Fin M, p i = true := by
  induction M with
  | zero =>
    constructor
    · intro h
      simp [anyFin_zero] at h
    · rintro ⟨i, _⟩
      exact i.elim0
  | succ M ih =>
    rw [anyFin_succ]
    constructor
    · intro h
      rcases Bool.or_eq_true .. |>.mp h with h0 | hrest
      · exact ⟨0, h0⟩
      · obtain ⟨i, hi⟩ := (ih _).mp hrest
        exact ⟨i.succ, hi⟩
    · rintro ⟨i, hi⟩
      match i, hi with
      | ⟨0, _⟩, hi =>
        exact Bool.or_eq_true .. |>.mpr (Or.inl hi)
      | ⟨k + 1, hk⟩, hi =>
        refine Bool.or_eq_true .. |>.mpr (Or.inr ?_)
        exact (ih _).mpr ⟨⟨k, Nat.lt_of_succ_lt_succ hk⟩, hi⟩

end StructuralIntelligence
