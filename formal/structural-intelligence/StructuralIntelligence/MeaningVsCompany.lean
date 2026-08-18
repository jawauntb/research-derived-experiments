import StructuralIntelligence.CausalSemantics

/-!
# Structural Intelligence — meaning vs company (Wave 6)

The §7 sting of "Intention Is All You Need", banked in the kernel: on
the registered six-message, four-context world of the causal-semantics
companion (`experiments/causal_semantics_pair/`, paper §4), the
**meaning quotient** (Ψ-equivalence classes) and the **co-occurrence
quotient** (distributional-company classes) are *incomparable*
partitions — neither refines the other.  What a symbol does and what a
symbol hangs around with are different partitions of the message
space, and no tuning of a distributional method changes which lattice
element it computes.

This file instantiates the general Wave-3 core
(`StructuralIntelligence.CausalSemantics.PsiEquiv`, CS-1/CS-2) on the
registered concrete world.  Distributions are exact percent-integer
vectors (every registered probability is a multiple of 0.05, so
percents are exact).  Kernel `decide` only.  No Mathlib.  No
`native_decide`.

Categorical reading, at the grade it earns: the meaning quotient is a
congruence (CS-1, already proved in the core) whose quotient is the
coarsest structure-preserving one (CS-2, already proved) — a universal
property.  Incomparability here is the statement that two quotient
maps out of the same object have no factoring in either direction: two
incomparable elements of the congruence lattice.  That part is earned
by enumeration below; nothing stronger is claimed.
-/

namespace StructuralIntelligence
namespace MeaningVsCompany

/-- The six registered messages. -/
inductive M6 where
  | m0
  | m1
  | m2
  | m3
  | m4
  | m5
deriving DecidableEq, Repr

/-- The four registered contexts. -/
inductive C4 where
  | c0
  | c1
  | c2
  | c3
deriving DecidableEq, Repr

def allMessages : List M6 := [.m0, .m1, .m2, .m3, .m4, .m5]

def allContexts : List C4 := [.c0, .c1, .c2, .c3]

theorem allContexts_complete : ∀ c : C4, c ∈ allContexts := by
  intro c
  cases c <;> simp [allContexts]

/-- A downstream distribution over the four future states, in exact
    percent units (the registered probabilities are all multiples of
    0.05, so this encoding is lossless). -/
abbrev Dist := Nat × Nat × Nat × Nat

def dA : C4 → Dist
  | .c0 => (50, 50, 0, 0)
  | .c1 => (25, 25, 25, 25)
  | .c2 => (30, 30, 20, 20)
  | .c3 => (40, 10, 40, 10)

def dB : C4 → Dist
  | .c0 => (0, 0, 50, 50)
  | .c1 => (70, 10, 10, 10)
  | .c2 => (20, 20, 30, 30)
  | .c3 => (10, 40, 10, 40)

def dC : C4 → Dist
  | .c0 => (100, 0, 0, 0)
  | .c1 => (10, 70, 10, 10)
  | .c2 => (50, 50, 0, 0)
  | .c3 => (25, 25, 25, 25)

def dD : C4 → Dist
  | .c0 => (0, 0, 0, 100)
  | .c1 => (10, 10, 70, 10)
  | .c2 => (0, 0, 50, 50)
  | .c3 => (10, 40, 40, 10)

/-- The registered update operator Ψ (paper §4): m0,m1 ↦ class A;
    m2,m3 ↦ class B; m4 ↦ C; m5 ↦ D. -/
def psi : M6 → C4 → Dist
  | .m0, c => dA c
  | .m1, c => dA c
  | .m2, c => dB c
  | .m3, c => dB c
  | .m4, c => dC c
  | .m5, c => dD c

/-- The registered co-occurrence signature κ: even-indexed messages
    share (4,4,1,1); odd-indexed share (1,1,4,4). -/
def kappa : M6 → Dist
  | .m0 => (4, 4, 1, 1)
  | .m1 => (1, 1, 4, 4)
  | .m2 => (4, 4, 1, 1)
  | .m3 => (1, 1, 4, 4)
  | .m4 => (4, 4, 1, 1)
  | .m5 => (1, 1, 4, 4)

/-- List-bounded Ψ-equivalence (decidable form). -/
def psiEqOn (m₁ m₂ : M6) : Bool :=
  allContexts.all fun c => decide (psi m₁ c = psi m₂ c)

/-- The decidable form agrees with the Wave-3 core's `PsiEquiv` on
    this world, because `allContexts` enumerates `C4`. -/
theorem psiEqOn_iff_PsiEquiv (m₁ m₂ : M6) :
    psiEqOn m₁ m₂ = true ↔ PsiEquiv psi m₁ m₂ := by
  constructor
  · intro h c
    have hall := List.all_eq_true.mp h
    have hc := hall c (allContexts_complete c)
    exact of_decide_eq_true hc
  · intro h
    apply List.all_eq_true.mpr
    intro c _
    exact decide_eq_true (h c)

/-- Registered meaning classes: A = {m0,m1}, B = {m2,m3}, C = {m4},
    D = {m5}. -/
def meaningClass : M6 → Nat
  | .m0 => 0
  | .m1 => 0
  | .m2 => 1
  | .m3 => 1
  | .m4 => 2
  | .m5 => 3

/-- **The meaning quotient is exactly the registered four-class
    partition**: Ψ-equivalence holds iff the registered class labels
    agree, over all 36 message pairs. -/
theorem meaning_quotient_is_registered :
    ∀ x ∈ allMessages, ∀ y ∈ allMessages,
      (psiEqOn x y = true ↔ meaningClass x = meaningClass y) := by
  decide

/-- **The company quotient is exactly the parity partition**:
    κ-signatures agree iff message parity agrees. -/
def parity : M6 → Nat
  | .m0 => 0
  | .m1 => 1
  | .m2 => 0
  | .m3 => 1
  | .m4 => 0
  | .m5 => 1

theorem company_quotient_is_parity :
    ∀ x ∈ allMessages, ∀ y ∈ allMessages,
      (kappa x = kappa y ↔ parity x = parity y) := by
  decide

/-- **Incomparability, both directions, by explicit witness.**
    Company does not refine meaning: m0 and m2 share a κ-signature
    and are not Ψ-equivalent.  Meaning does not refine company:
    m0 and m1 are Ψ-equivalent and have different κ-signatures. -/
theorem neither_partition_refines_the_other :
    (kappa .m0 = kappa .m2 ∧ psiEqOn .m0 .m2 = false) ∧
    (psiEqOn .m0 .m1 = true ∧ kappa .m0 ≠ kappa .m1) := by
  decide

/-- The refinement failure transported to the core's `PsiEquiv`
    (CS-1's congruence): the witness pair m0, m2 shares company and
    differs in meaning in the exact Wave-3 sense. -/
theorem company_does_not_refine_meaning :
    kappa .m0 = kappa .m2 ∧ ¬ PsiEquiv psi .m0 .m2 := by
  constructor
  · decide
  · intro h
    have := (psiEqOn_iff_PsiEquiv .m0 .m2).mpr h
    have hfalse : psiEqOn .m0 .m2 = false := by decide
    rw [this] at hfalse
    exact Bool.noConfusion hfalse

/-- Meaning does not refine company, in the exact Wave-3 sense. -/
theorem meaning_does_not_refine_company :
    PsiEquiv psi .m0 .m1 ∧ kappa .m0 ≠ kappa .m1 := by
  constructor
  · exact (psiEqOn_iff_PsiEquiv .m0 .m1).mp (by decide)
  · decide

#print axioms meaning_quotient_is_registered
#print axioms company_quotient_is_parity
#print axioms neither_partition_refines_the_other
#print axioms company_does_not_refine_meaning
#print axioms meaning_does_not_refine_company

end MeaningVsCompany
end StructuralIntelligence
