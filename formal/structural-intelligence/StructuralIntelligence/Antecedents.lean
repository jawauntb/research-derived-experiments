import StructuralIntelligence.Refinement

/-!
# Structural Intelligence — Antecedent Taxonomy SA-1 (algebraic core)

The algebraic core of Theorem SA-1 (Antecedent taxonomy, partition-
intersection Markov screen) from the *Structural Antecedents* companion
paper.

For a family of quotients `q_u : X → Z_u` indexed by `u : U`, the
**intersection screen** identifies two inputs iff every `q_u` identifies
them:

> `IntersectionScreen q x₁ x₂ ↔ ∀ u, q u x₁ = q u x₂`.

This is the coarsest quotient that refines every `q_u`, i.e., the
"partition intersection" in the partition lattice.  SA-1 says: if every
task in a family is locally sufficient at *some* member of the family
`{q_u}`, then the intersection screen is a common sufficient screen for
the whole task family, and it is the coarsest one with that property
(any competing screen refines the intersection).

Everything here is pure Lean 4 core (no `Mathlib`).
-/

namespace StructuralIntelligence

universe u v w v' a y

section Antecedents

variable {X : Type u} {U : Type v} {Z : U → Type w}

/-- The **intersection screen** for a family of quotients
    `q : ∀ u : U, X → Z u` identifies `x₁` and `x₂` iff every family
    member `q u` identifies them.  Equivalently, its fibres are the
    intersection of the fibres of every `q u`. -/
def IntersectionScreen (q : ∀ u : U, X → Z u) (x₁ x₂ : X) : Prop :=
  ∀ u : U, q u x₁ = q u x₂

/-- The intersection screen refines every family member: it is at
    least as fine as each `q u`.  Definitional. -/
theorem intersection_refines_each
    {q : ∀ u : U, X → Z u} {x₁ x₂ : X}
    (h : IntersectionScreen q x₁ x₂) (u : U) :
    q u x₁ = q u x₂ := h u

/-- **Local sufficiency.**  A task family `Y : ∀ α, X → Yfam α` is
    *locally sufficient* for the family `{q u}` if every task is
    determined by *some* family member: for each `α`, there is a `u`
    such that `q u x₁ = q u x₂` implies `Y α x₁ = Y α x₂`. -/
def LocallySufficient
    {A : Type a} {Yfam : A → Type y}
    (q : ∀ u : U, X → Z u) (Y : ∀ α : A, X → Yfam α) : Prop :=
  ∀ α : A, ∃ u : U, ∀ x₁ x₂ : X,
    q u x₁ = q u x₂ → Y α x₁ = Y α x₂

/-- **SA-1 (Antecedent taxonomy, algebraic core).**

    If the task family `Y` is locally sufficient for the family
    `{q u}`, then the intersection screen is a common sufficient
    screen for the whole task family: `IntersectionScreen q x₁ x₂`
    implies `Y α x₁ = Y α x₂` for every task index `α`.

    Proof: for each `α`, pick the local witness `u`; the intersection
    hypothesis at `u` supplies the needed `q u x₁ = q u x₂`. -/
theorem intersection_is_common_sufficient
    {A : Type a} {Yfam : A → Type y}
    {q : ∀ u : U, X → Z u} {Y : ∀ α : A, X → Yfam α}
    (hLocal : LocallySufficient q Y)
    {x₁ x₂ : X} (hInt : IntersectionScreen q x₁ x₂) :
    ∀ α : A, Y α x₁ = Y α x₂ := by
  intro α
  obtain ⟨u, hu⟩ := hLocal α
  exact hu x₁ x₂ (hInt u)

/-- **SA-1 (Coarsest over family).**  Any competing screen `q'` that
    is at least as fine as every family member `q u` — i.e., `q' x₁ =
    q' x₂` implies `q u x₁ = q u x₂` for every `u` — is a refinement
    of the intersection screen.

    Under the package's `Refines` convention (`Refines P₁ P₂` says
    `P₂ ⊆ P₁`), this is exactly `Refines (IntersectionScreen q)
    (qRel q')`.  The intersection screen is the *coarsest* quotient
    that captures every `q u`: it lies at the meet of the family in
    the partition lattice. -/
theorem intersection_is_coarsest_over_family
    (q : ∀ u : U, X → Z u)
    {Z' : Type v'} (q' : X → Z')
    (hCapture : ∀ u : U, ∀ x₁ x₂ : X,
      q' x₁ = q' x₂ → q u x₁ = q u x₂) :
    Refines (IntersectionScreen q) (qRel q') := by
  intro x₁ x₂ hq' u
  exact hCapture u x₁ x₂ hq'

end Antecedents

end StructuralIntelligence
