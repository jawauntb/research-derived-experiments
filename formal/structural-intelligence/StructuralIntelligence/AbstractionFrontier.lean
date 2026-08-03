/-!
# Structural Intelligence — Abstraction Frontier AF-1 and AF-2 (algebraic core)

The algebraic cores of Theorems AF-1 (Pareto set is an antichain) and
AF-2 (Pareto contains the common sufficient screens in the static case)
from the *Abstraction Frontier* companion paper.

The abstraction-frontier framework ranks candidate quotients `q : Q`
against a fixed number `n` of axes (task-insufficiency, coding cost,
etc.); lower is better on every axis.  **Domination** is componentwise
`≤` with strict `<` on at least one axis; the **Pareto set** consists of
the non-dominated quotients.

AF-1 is the classical antichain fact: two Pareto-optimal quotients
cannot dominate each other.  AF-2 says that, in the two-axis static
case (only task-sufficiency and coding cost vary), any *common
sufficient screen* (zero task-insufficiency) that minimises coding
cost among common sufficient screens is Pareto — the CSS lattice sits
on the Pareto frontier.

Everything here is pure Lean 4 core (no `Mathlib`).  Axes are modelled
as `Fin n → Nat` (integer proxies for real-valued axes; the extension
to `ℝ`-valued axes is orthogonal and lives in Mathlib territory).
-/

namespace StructuralIntelligence

universe u

section AbstractionFrontier

variable {Q : Type u}

/-- **Dominates**.  `q₁` dominates `q₂` if `q₁` is componentwise
    `≤ q₂` on every axis and *strictly better* on at least one.
    Lower is better on every axis. -/
def Dominates {n : Nat} (axes : Q → Fin n → Nat) (q₁ q₂ : Q) : Prop :=
  (∀ i : Fin n, axes q₁ i ≤ axes q₂ i) ∧
  (∃ i : Fin n, axes q₁ i < axes q₂ i)

/-- **IsPareto**.  A quotient is Pareto-optimal if nothing dominates
    it. -/
def IsPareto {n : Nat} (axes : Q → Fin n → Nat) (q : Q) : Prop :=
  ¬ ∃ q' : Q, Dominates axes q' q

/-- **AF-1 (Pareto set is an antichain).**  Two Pareto-optimal
    quotients cannot dominate each other.  Direct from the definition
    of `IsPareto`: if either dominates the other, the dominated one
    fails `IsPareto`. -/
theorem pareto_set_is_antichain
    {n : Nat} {axes : Q → Fin n → Nat}
    {q₁ q₂ : Q}
    (h₁ : IsPareto axes q₁) (h₂ : IsPareto axes q₂) :
    ¬ Dominates axes q₁ q₂ ∧ ¬ Dominates axes q₂ q₁ := by
  refine ⟨?_, ?_⟩
  · intro hDom
    exact h₂ ⟨q₁, hDom⟩
  · intro hDom
    exact h₁ ⟨q₂, hDom⟩

/-- **AF-2 (Pareto contains CSS in the two-axis static case).**

    Under the simplifying assumption that only two axes vary
    (task-sufficiency at index `0` and coding cost at index `1`;
    the other axes are constant across `Q` and can be dropped from the
    domination check), any candidate `q*` that is a **common sufficient
    screen** (`axes q* 0 = 0`) and minimises coding cost among common
    sufficient screens is Pareto-optimal.

    Proof: suppose `q'` dominates `q*`.  The strict-improvement axis
    is either `0` or `1`.  If it is `0`, then `axes q' 0 < axes q* 0
    = 0`, impossible in `Nat`.  If it is `1`, componentwise
    `≤` at axis `0` gives `axes q' 0 ≤ 0`, so `axes q' 0 = 0`; but
    then `q'` is also a common sufficient screen, and cost-minimality
    of `q*` gives `axes q* 1 ≤ axes q' 1`, contradicting
    `axes q' 1 < axes q* 1`. -/
theorem pareto_contains_css_when_zero_sufficiency
    {axes : Q → Fin 2 → Nat} {qStar : Q}
    (hSuff : axes qStar 0 = 0)
    (hMin : ∀ q' : Q, axes q' 0 = 0 → axes qStar 1 ≤ axes q' 1) :
    IsPareto axes qStar := by
  rintro ⟨q', hLe, i, hLt⟩
  -- Case on which axis is strictly improved.
  rcases i with ⟨k, hk⟩
  match k, hk with
  | 0, hk =>
    -- axes q' ⟨0, _⟩ < axes qStar ⟨0, _⟩, but axes qStar 0 = 0.
    have hEq : (⟨0, hk⟩ : Fin 2) = (0 : Fin 2) := rfl
    rw [hEq, hSuff] at hLt
    exact Nat.not_lt_zero _ hLt
  | 1, hk =>
    have hEq : (⟨1, hk⟩ : Fin 2) = (1 : Fin 2) := rfl
    rw [hEq] at hLt
    -- axes q' 1 < axes qStar 1
    have hLe0 : axes q' 0 ≤ axes qStar 0 := hLe 0
    rw [hSuff] at hLe0
    have hZero : axes q' 0 = 0 := Nat.le_zero.mp hLe0
    have hMinLe := hMin q' hZero
    exact Nat.lt_irrefl _ (Nat.lt_of_lt_of_le hLt hMinLe)
  | (n + 2), hn =>
    -- Fin 2 has no such index.
    exact absurd hn (by omega)

end AbstractionFrontier

end StructuralIntelligence
