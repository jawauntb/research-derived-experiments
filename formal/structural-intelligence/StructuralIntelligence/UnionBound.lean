import StructuralIntelligence.Basic

/-!
# Structural Intelligence — finite union bound

The counting form of the union bound: for any list `L` and any family of
predicates `P : Fin M → α → Bool`, the count of elements of `L` matching
*some* `P i` is at most the sum over `i : Fin M` of the count of elements
matching `P i`.

This is the combinatorial half of the union-bound step in Theorem 5 of
the *Structural Intelligence* paper.  The probabilistic corollary
`Pr[⋃ᵢ Aᵢ] ≤ Σᵢ Pr[Aᵢ]` is just this identity divided by `|L|`, and no
measure-theoretic machinery is needed.
-/

namespace StructuralIntelligence

/-- **Pointwise indicator union bound.**

    If some `P i x` holds then the sum of indicators over `Fin M` at `x`
    is at least `1`; if none holds it is `0`.  In particular

    `(if anyFin M (fun i => P i x) then 1 else 0)
        ≤ sumFin M (fun i => if P i x then 1 else 0)`. -/
theorem indicator_anyFin_le_sumFin_indicator
    {α : Type u} (M : Nat) (P : Fin M → α → Bool) (x : α) :
    (if anyFin M (fun i => P i x) = true then 1 else 0) ≤
      sumFin M (fun i => if P i x = true then 1 else 0) := by
  by_cases hAny : anyFin M (fun i => P i x) = true
  · rw [if_pos hAny]
    obtain ⟨i, hi⟩ := (anyFin_eq_true_iff M _).mp hAny
    have hOne : (if P i x = true then (1 : Nat) else 0) = 1 := by simp [hi]
    have hidx : 1 ≤ (fun i => if P i x = true then 1 else 0) i := by
      show 1 ≤ (if P i x = true then (1 : Nat) else 0)
      rw [hOne]
      exact Nat.le_refl 1
    exact one_le_sumFin_of_index _ i hidx
  · rw [if_neg hAny]
    exact Nat.zero_le _

/-- **Counting union bound.**

    For any list `L : List α` and any family `P : Fin M → α → Bool`, the
    number of elements of `L` satisfying at least one `P i` is at most the
    sum, over `i : Fin M`, of the number of elements satisfying `P i`.

    This is `Pr[⋃ᵢ Aᵢ] ≤ Σᵢ Pr[Aᵢ]` in counting form. -/
theorem countP_anyFin_le_sumFin_countP {α : Type u}
    (M : Nat) (P : Fin M → α → Bool) (L : List α) :
    L.countP (fun x => anyFin M (fun i => P i x)) ≤
      sumFin M (fun i => L.countP (P i)) := by
  induction L with
  | nil =>
    rw [List.countP_nil]
    -- sumFin over `fun i => List.countP (P i) []` = sumFin (fun _ => 0) = 0.
    have hEq :
        (fun i : Fin M => List.countP (P i) ([] : List α))
          = (fun _ : Fin M => 0) := by
      funext i; rw [List.countP_nil]
    rw [hEq, sumFin_zero_fn]
    exact Nat.le_refl 0
  | cons x rest ih =>
    -- Split both sides via `countP_cons`.
    rw [List.countP_cons]
    -- Rewrite the RHS termwise via `countP_cons` and `sumFin_add`.
    have hpoint :
        ∀ i : Fin M,
            (x :: rest).countP (P i)
              = rest.countP (P i) + (if P i x = true then 1 else 0) := by
      intro i; rw [List.countP_cons]
    have hRHS :
        sumFin M (fun i => (x :: rest).countP (P i))
          = sumFin M (fun i => rest.countP (P i))
              + sumFin M (fun i => if P i x = true then 1 else 0) := by
      calc sumFin M (fun i => (x :: rest).countP (P i))
          = sumFin M (fun i =>
              rest.countP (P i) + (if P i x = true then 1 else 0)) := by
                apply congrArg; funext i; exact hpoint i
        _ = sumFin M (fun i => rest.countP (P i))
              + sumFin M (fun i => if P i x = true then 1 else 0) :=
              sumFin_add M _ _
    rw [hRHS]
    -- Now combine `ih` with the pointwise indicator bound.
    exact Nat.add_le_add ih (indicator_anyFin_le_sumFin_indicator M P x)

end StructuralIntelligence
