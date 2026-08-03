import StructuralIntelligence.Refinement

/-!
# Structural Intelligence — Causal Semantics CS-1 and CS-2 (algebraic core)

The algebraic backbones of Theorems CS-1 (Ψ-equivalence is a congruence) and
CS-2 (the meaning quotient is the coarsest common sufficient statistic on
messages) from the *Causal Semantics* companion paper.

For a semantics `psi : M → C → D` sending a message `m` and a context `c`
to a discrete distribution slot, **Ψ-equivalence** is agreement in every
context:

> `PsiEquiv psi m₁ m₂ ↔ ∀ c, psi m₁ c = psi m₂ c`.

CS-1 says Ψ-equivalence is an equivalence relation (reflexive, symmetric,
transitive) and is preserved under any context-list operation.  CS-2 says
the resulting **message quotient** is the coarsest common sufficient
screen on `M`: every other screen `q : M → Q` that determines Ψ-behaviour
refines the Ψ-equivalence relation.

Everything here is pure Lean 4 core (no `Mathlib`).
-/

namespace StructuralIntelligence

universe u v w v'

section CausalSemantics

variable {M : Type u} {C : Type v} {D : Type w}

/-- **Ψ-equivalence.**  Two messages are Ψ-equivalent under a semantics
    `psi : M → C → D` if they induce the same distribution slot in
    every context. -/
def PsiEquiv (psi : M → C → D) (m₁ m₂ : M) : Prop :=
  ∀ c : C, psi m₁ c = psi m₂ c

/-- Ψ-equivalence is reflexive. -/
theorem psiEquiv_refl (psi : M → C → D) (m : M) : PsiEquiv psi m m :=
  fun _ => rfl

/-- Ψ-equivalence is symmetric. -/
theorem psiEquiv_symm {psi : M → C → D} {m₁ m₂ : M}
    (h : PsiEquiv psi m₁ m₂) : PsiEquiv psi m₂ m₁ :=
  fun c => (h c).symm

/-- Ψ-equivalence is transitive. -/
theorem psiEquiv_trans {psi : M → C → D} {m₁ m₂ m₃ : M}
    (h₁₂ : PsiEquiv psi m₁ m₂) (h₂₃ : PsiEquiv psi m₂ m₃) :
    PsiEquiv psi m₁ m₃ :=
  fun c => (h₁₂ c).trans (h₂₃ c)

/-- **CS-1 congruence extension.**  Ψ-equivalent messages induce the
    same list of context-slot values under any list of contexts.  This
    is the constructive form of "Ψ is a congruence under context-list
    combinators": once two messages agree in every single context, they
    agree in every finite context sequence one might chain together. -/
theorem psi_equiv_preserves_under_context
    {psi : M → C → D} {m₁ m₂ : M} (h : PsiEquiv psi m₁ m₂) :
    ∀ (cs : List C), cs.map (psi m₁) = cs.map (psi m₂) := by
  intro cs
  induction cs with
  | nil => rfl
  | cons c rest ih =>
    show psi m₁ c :: rest.map (psi m₁)
        = psi m₂ c :: rest.map (psi m₂)
    rw [h c, ih]

/-- The **message quotient** relation: two messages identified iff
    Ψ-equivalent.  Definitionally the same as `PsiEquiv`; the alternate
    name marks the intended interpretation as a quotient. -/
def MessageQuotient (psi : M → C → D) (m₁ m₂ : M) : Prop :=
  PsiEquiv psi m₁ m₂

/-- The canonical message-quotient map `M → (C → D)`, sending
    `m ↦ (fun c => psi m c)`.  This is the "map to the equivalence
    class" for `PsiEquiv`. -/
def messageQuotientMap (psi : M → C → D) : M → (C → D) :=
  fun m c => psi m c

/-- **CS-2 (sufficient direction).**  The message-quotient map factors
    every context slot of `psi`: for every context `c`,
    `psi (·, c) = (fun f => f c) ∘ messageQuotientMap psi`.  In particular
    `messageQuotientMap psi` is a common sufficient screen for the
    context-indexed family `{psi (·, c) : c : C}`.  Definitional. -/
theorem messageQuotient_is_common_sufficient
    (psi : M → C → D) (m : M) (c : C) :
    psi m c = (messageQuotientMap psi m) c := rfl

/-- The message-quotient map has `PsiEquiv` as its induced equivalence
    relation: two messages have equal image iff Ψ-equivalent.  This is
    the "the quotient by PsiEquiv is exactly `messageQuotientMap`'s
    fibre partition" statement. -/
theorem messageQuotientMap_eq_iff (psi : M → C → D) (m₁ m₂ : M) :
    messageQuotientMap psi m₁ = messageQuotientMap psi m₂
      ↔ PsiEquiv psi m₁ m₂ := by
  constructor
  · intro heq c
    exact congrFun heq c
  · intro h
    funext c
    exact h c

/-- **CS-2 (coarsest common-sufficient-statistic).**

    Suppose `q : M → Q` is any other common sufficient screen — that is,
    whenever `q m₁ = q m₂`, the messages are Ψ-equivalent (agreement
    under `q` forces agreement in every context, the "sufficient
    direction").  Then `q` refines the Ψ-equivalence relation:
    every `q`-equivalence class lies inside a Ψ-equivalence class.
    Equivalently, using the package's `Refines` convention
    (`Refines P₁ P₂` says `P₂ ⊆ P₁`), `PsiEquiv psi` is refined by
    `qRel q`.

    This is the coarsest-CSS statement of CS-2 at the algebraic level:
    the message quotient is the *largest* quotient of `M` that still
    determines `psi` in every context, and any competing screen is at
    least as fine. -/
theorem messageQuotient_is_coarsest
    {psi : M → C → D} {Q : Type v'} (q : M → Q)
    (hSuff : ∀ m₁ m₂ : M, q m₁ = q m₂ → PsiEquiv psi m₁ m₂) :
    Refines (PsiEquiv psi) (qRel q) := by
  intro m₁ m₂ hq
  exact hSuff m₁ m₂ hq

end CausalSemantics

end StructuralIntelligence
