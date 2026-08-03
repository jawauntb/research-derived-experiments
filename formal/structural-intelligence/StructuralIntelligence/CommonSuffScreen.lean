/-!
# Structural Intelligence — Common-Sufficient Screen (Theorem 4, algebraic core)

The algebraic core of Theorem 4 (Cross-task stability, conditional) in the
*Structural Intelligence* paper (`papers/structural_intelligence/paper.md`,
§ 2.4).  The probability-space formulation of Theorem 4 requires measure
theory (mathlib), but the *mechanism* of the theorem is purely functional
and can be stated with no probability at all:

> If every task `Y_α : X → 𝒴_α` factors through a common map `q : X → Z`,
> then any two inputs `x, x'` with `q x = q x'` agree on every task:
> `Y_α x = Y_α x'` for all `α`.

Equivalently: the equivalence relation `~_q` induced on `X` by `q`
refines the equivalence relation `~_Y` induced by the joint task family
`{Y_α}`.  This is Theorem 4's mechanism-of-action in its purely
set-theoretic form; the measure-theoretic conditional-independence
statement `Y_α ⟂ Y_β ∣ q(X)` reduces to it once one observes that
fibre-constant functions of `q(X)` are exactly the `σ(q)`-measurable
functions.

Everything here is pure Lean 4 core (no `Mathlib`).
-/

namespace StructuralIntelligence

universe u v v' w y

section CommonSuffScreen

variable {X : Type u} {Z : Type v} {A : Type w} {Yfam : A → Type y}

/-- A **common sufficient screen** for a task family `Y : ∀ α, X → Yfam α`
    is a map `q : X → Z` through which every task factors: for every task
    index `α`, there exists `h_α : Z → Yfam α` with `Y α = h_α ∘ q`.

    In statistical terms `q` is a *sufficient statistic* common to every
    task in the family — everything the tasks care about is already
    determined by `q`. -/
def IsCommonSuffScreen
    (Y : ∀ α : A, X → Yfam α) (q : X → Z) : Prop :=
  ∀ α : A, ∃ h : Z → Yfam α, ∀ x : X, Y α x = h (q x)

/-- **Theorem 4-core (Functional Common-Sufficient Screen).**

    If `q : X → Z` is a common sufficient screen for the task family
    `Y : ∀ α, X → Yfam α`, then `q x = q x'` implies `Y α x = Y α x'`
    for every task index `α`.

    Equivalently: the equivalence relation `~_q` induced on `X` by `q`
    refines the equivalence relation `~_Y` induced by the joint task
    family (`x ~_Y x'` iff `Y α x = Y α x'` for every `α`).

    This is the algebraic core of Theorem 4 in the *Structural
    Intelligence* paper (§ 2.4).  The full probability-space conclusion
    `Y_α ⟂ Y_β | q(X)` for all `α ≠ β` requires measure theory, but this
    functional fibre-refinement is the mechanism doing all the work:
    once every task is a function of `q`, the joint task vector is a
    function of `q`, and so conditioning on `q` fixes every task
    outcome (pointwise, and hence a fortiori in distribution). -/
theorem commonSuffScreen_refines
    {Y : ∀ α : A, X → Yfam α} {q : X → Z}
    (hFactor : IsCommonSuffScreen Y q)
    {x x' : X} (hq : q x = q x') :
    ∀ α : A, Y α x = Y α x' := by
  intro α
  obtain ⟨h, hh⟩ := hFactor α
  calc Y α x
      = h (q x)  := hh x
    _ = h (q x') := by rw [hq]
    _ = Y α x'   := (hh x').symm

/-- The **joint task quotient** `q_Y : X → (∀ α, Yfam α)` defined pointwise
    by `q_Y x = (α ↦ Y α x)`.  This is the *canonical* common-sufficient
    screen: every task factors through it via the α-th projection, and
    its fibres are exactly the sets on which every task is constant. -/
def jointTaskQuotient (Y : ∀ α : A, X → Yfam α) :
    X → (∀ α : A, Yfam α) :=
  fun x α => Y α x

/-- The joint task quotient factors every task: `Y α = π_α ∘ q_Y`
    with `π_α f = f α`.  In particular `jointTaskQuotient Y` is a
    common sufficient screen. -/
theorem jointTaskQuotient_isCommonSuffScreen
    (Y : ∀ α : A, X → Yfam α) :
    IsCommonSuffScreen Y (jointTaskQuotient Y) := by
  intro α
  refine ⟨fun f => f α, ?_⟩
  intro x
  rfl

/-- Two inputs are equivalent under the joint task quotient iff they
    agree on every task.  This is the exact statement that
    `jointTaskQuotient Y` implements the joint task equivalence
    relation `~_Y`. -/
theorem jointTaskQuotient_eq_iff
    (Y : ∀ α : A, X → Yfam α) (x x' : X) :
    jointTaskQuotient Y x = jointTaskQuotient Y x'
      ↔ ∀ α : A, Y α x = Y α x' := by
  constructor
  · intro heq α
    exact congrFun heq α
  · intro h
    funext α
    exact h α

/-- **Corollary (Coarsest common-sufficient statistic).**

    Suppose `q : X → Z` is a common sufficient screen for
    `Y : ∀ α, X → Yfam α` and, additionally, `q` satisfies the converse
    of Theorem 4-core:

    `(∀ α, Y α x = Y α x') → q x = q x'`.

    Then `q` is *coarsest* in the following precise sense: for any other
    common sufficient screen `q' : X → Z'`, agreement under `q'` implies
    agreement under `q`.  Equivalently, `q`'s equivalence relation
    coincides with the joint task equivalence `~_Y`, so its fibres are
    the largest possible.

    The proof is pure algebra — no `sorry`. -/
theorem commonSuffScreen_coarsest
    {Y : ∀ α : A, X → Yfam α}
    {q : X → Z} (_hq : IsCommonSuffScreen Y q)
    (hConv : ∀ x x' : X, (∀ α : A, Y α x = Y α x') → q x = q x')
    {Z' : Type v'} {q' : X → Z'} (hq' : IsCommonSuffScreen Y q')
    {x x' : X} (hEq' : q' x = q' x') :
    q x = q x' := by
  apply hConv
  intro α
  exact commonSuffScreen_refines hq' hEq' α

/-- **Two-form of the corollary.**  A common sufficient screen `q`
    that additionally satisfies the converse implication has the same
    equivalence relation as the joint task quotient.  This is the
    "unique up to bijection of quotients" statement: any two coarsest
    common sufficient screens quotient `X` in exactly the same way. -/
theorem commonSuffScreen_eq_jointTaskQuotient_iff
    {Y : ∀ α : A, X → Yfam α}
    {q : X → Z} (hq : IsCommonSuffScreen Y q)
    (hConv : ∀ x x' : X, (∀ α : A, Y α x = Y α x') → q x = q x')
    (x x' : X) :
    q x = q x' ↔ jointTaskQuotient Y x = jointTaskQuotient Y x' := by
  constructor
  · intro hEq
    exact (jointTaskQuotient_eq_iff Y x x').mpr
      (commonSuffScreen_refines hq hEq)
  · intro hEq
    exact hConv x x' ((jointTaskQuotient_eq_iff Y x x').mp hEq)

end CommonSuffScreen

end StructuralIntelligence
