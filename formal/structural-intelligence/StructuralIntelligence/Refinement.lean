import StructuralIntelligence.CommonSuffScreen

/-!
# Structural Intelligence — Refinement reduction (Theorem 6, algebraic core)

Theorem 6 (paper §2.5b) reduces continuous-case learnability to
Theorem 5 via an ε-covering: for `Z ⊂ ℝ^{d_Z}` the ε-covering number
is `N_ε = O((D_Z/ε)^{d_Z})`, giving `N ≥ c · N_ε · ln(N_ε / ε_rel)`
samples.  The **quantitative rate** requires real logs and is out of
scope for pure Lean core (see the package `README.md`).

The **algebraic core** of the reduction is a pure fact about
partitions and functional factorisation.  Following the pattern of
`CommonSuffScreen.lean`, we state it without any probability at all:

> If `q₁ : X → Z₁` is a common sufficient screen for a task family
> `Y` and `q₂ : X → Z₂` is a **refinement** of `q₁` (i.e., `q₁`
> factors through `q₂` via some `r : Z₂ → Z₁` with `q₁ = r ∘ q₂`),
> then `q₂` is also a common sufficient screen — the finer
> partition inherits the factorisation by composition
> (`Y α = h ∘ q₁ = h ∘ r ∘ q₂`).

Equivalently: whenever an ε-cover refines a coarse partition on
which every task is constant, every task is constant on the
refinement.  This is the mechanism by which the discrete
common-sufficient-screen conclusion (Theorem 5) lifts to the
ε-cover (Theorem 6), once the covering number is supplied.

The naming convention here follows the task-partition literature:
`Refines P₁ P₂` is the "P₂ ⊆ P₁ as a subset of `α × α`" relation,
i.e., `P₂` (the second argument) is at-least-as-fine as `P₁` (the
first, coarser argument).  Under this convention the statement above
reads: *coarse* screen `q₁` + `q₂` refines `q₁` ⇒ *fine* screen
`q₂` is also a screen.  This is the mathematically correct
direction of composition; the reverse would let a task be constant
on a coarser partition purely because it is constant on a finer one,
which is false in general.

Everything here is pure Lean 4 core (no `Mathlib`).
-/

namespace StructuralIntelligence

universe u v v' w y

section Refinement

/-- **Refinement of binary relations.**  `Refines P₁ P₂` says every
    `P₂`-equivalent pair is `P₁`-equivalent, i.e., `P₂ ⊆ P₁` as a
    subset of `α × α`.  Under the standard partition ordering this
    means `P₂` is at-least-as-fine as `P₁` (smaller equivalence
    classes). -/
def Refines {α : Type u} (P₁ P₂ : α → α → Prop) : Prop :=
  ∀ a b : α, P₂ a b → P₁ a b

/-- Refinement is reflexive. -/
theorem refinement_refl {α : Type u} (P : α → α → Prop) : Refines P P :=
  fun _ _ h => h

/-- **`refinement_transitive`.**  Refinement is transitive: if `P₂`
    refines `P₁` and `P₃` refines `P₂`, then `P₃` refines `P₁`.
    Elementary. -/
theorem refinement_transitive {α : Type u} {P₁ P₂ P₃ : α → α → Prop}
    (h₁₂ : Refines P₁ P₂) (h₂₃ : Refines P₂ P₃) :
    Refines P₁ P₃ :=
  fun a b h => h₁₂ a b (h₂₃ a b h)

/-- The equivalence relation induced by a quotient map `q : X → Z`
    identifies two inputs iff they have the same `q`-image. -/
def qRel {X : Type u} {Z : Type v} (q : X → Z) (x x' : X) : Prop :=
  q x = q x'

/-- The `qRel` of any function is an equivalence relation
    (reflexive component). -/
theorem qRel_refl {X : Type u} {Z : Type v} (q : X → Z) (x : X) :
    qRel q x x := rfl

/-- Symmetry of `qRel`. -/
theorem qRel_symm {X : Type u} {Z : Type v} (q : X → Z) {x x' : X}
    (h : qRel q x x') : qRel q x' x := h.symm

/-- Transitivity of `qRel`. -/
theorem qRel_trans {X : Type u} {Z : Type v} (q : X → Z) {x x' x'' : X}
    (h₁ : qRel q x x') (h₂ : qRel q x' x'') : qRel q x x'' := h₁.trans h₂

/-- If `q₁ = r ∘ q₂` for some `r : Z₂ → Z₁`, then `qRel q₂` refines
    `qRel q₁` — the finer quotient inherits every equivalence of the
    coarser one. -/
theorem qRel_refines_of_factor {X : Type u} {Z₁ : Type v} {Z₂ : Type v'}
    (q₁ : X → Z₁) (q₂ : X → Z₂) (r : Z₂ → Z₁)
    (hFact : ∀ x, q₁ x = r (q₂ x)) :
    Refines (qRel q₁) (qRel q₂) := by
  intro a b hab
  show q₁ a = q₁ b
  rw [hFact a, hFact b]
  exact congrArg r hab

/-- **Theorem 6-core (Refinement reduction).**

    If `q₁ : X → Z₁` is a common sufficient screen for a task family
    `Y : ∀ α, X → Yfam α`, and `q₂ : X → Z₂` **refines** `q₁` in the
    functional sense that `q₁` factors through `q₂` via some
    `r : Z₂ → Z₁` with `q₁ = r ∘ q₂`, then `q₂` is also a common
    sufficient screen for `Y`.

    Proof: for every task index `α`, obtain the factorisation
    `Y α = h ∘ q₁` (`IsCommonSuffScreen`), then
    `Y α = h ∘ r ∘ q₂` by the hypothesis.  Composition.

    Interpretation.  This is the algebraic content of Theorem 6
    (§2.5b of the *Structural Intelligence* paper) once the
    ε-covering number `N_ε` is fixed: an ε-cover of `Z` induces a
    finite partition of `X` that refines the true fibre structure of
    every task, and this lemma promotes the discrete
    common-sufficient-screen conclusion (Theorem 5) to the ε-cover.
    The quantitative rate `N ≥ c · N_ε · ln(N_ε / ε_rel)` needs real
    logs and is out of scope for the pure-Lean-core artifact. -/
theorem refinement_preserves_screen
    {X : Type u} {Z₁ : Type v} {Z₂ : Type v'}
    {A : Type w} {Yfam : A → Type y}
    {Y : ∀ α : A, X → Yfam α}
    {q₁ : X → Z₁} {q₂ : X → Z₂} {r : Z₂ → Z₁}
    (hScreen : IsCommonSuffScreen Y q₁)
    (hFact : ∀ x, q₁ x = r (q₂ x)) :
    IsCommonSuffScreen Y q₂ := by
  intro α
  obtain ⟨h, hh⟩ := hScreen α
  refine ⟨h ∘ r, ?_⟩
  intro x
  show Y α x = h (r (q₂ x))
  rw [hh x, hFact x]

/-- Corollary at the relational level: under the same factorisation
    hypothesis `q₁ = r ∘ q₂`, the fibre equivalence of `q₂` refines
    that of `q₁`.  This is the "quotient of `q₂` refines quotient of
    `q₁`" statement in the relational form used throughout the
    partition literature. -/
theorem refinement_preserves_screen_qRel
    {X : Type u} {Z₁ : Type v} {Z₂ : Type v'}
    (q₁ : X → Z₁) (q₂ : X → Z₂) (r : Z₂ → Z₁)
    (hFact : ∀ x, q₁ x = r (q₂ x)) :
    Refines (qRel q₁) (qRel q₂) :=
  qRel_refines_of_factor q₁ q₂ r hFact

end Refinement

end StructuralIntelligence
