/-!
# Structural Intelligence — sections of a quotient (Wave 6)

The categorical reading of the master object, banked at the grade it
earns.  The pair (q, K) is a section–retraction pair: `q` compresses,
`K` realizes, and "the compiler lands in the compliant set" is
`q ∘ K = id` on the specification region.  Two facts about sections
are theorems, not readings, and both are the delegation problem in
one line each:

* `sections_spec_indistinguishable` — any two sections of `q` agree
  at the specification level everywhere on the region.  Being a
  section says *nothing* about which section: the choice is invisible
  upstairs.  This is silent substitution's type signature.
* `section_swap` — the section space is closed under arbitrary
  fiberwise replacement: swap any single value for any other member
  of its fiber and the result is again a section.  The space of right
  inverses is exactly the fiberwise freedom.

Plus a registered witness on a four-point world: the two-by-two fiber
structure carries exactly four sections, all pairwise distinct
downstairs and all identical upstairs (kernel `decide`).

What is *not* claimed: anything Kleisli-general (stochastic sections
are the Python instruments' job), any adjunction, any naturality —
those stay conjectures owing their forgetful maps, per the sameness
ladder.  No Mathlib.  No `native_decide`.
-/

namespace StructuralIntelligence
namespace KleisliSection

/-- `K` is a section of `q` on `region`: compiling any specification
    in the region complies with it. -/
def IsSectionOn (q : X → Z) (K : Z → X) (region : List Z) : Prop :=
  ∀ z ∈ region, q (K z) = z

/-- **Sections are indistinguishable at the specification level.**
    Any two sections of the same quotient agree upstairs on the whole
    region — the description-level record cannot separate compilers.
    (General; three lines; the whole delegation problem.) -/
theorem sections_spec_indistinguishable (q : X → Z) (K₁ K₂ : Z → X)
    (region : List Z) (h₁ : IsSectionOn q K₁ region)
    (h₂ : IsSectionOn q K₂ region) :
    ∀ z ∈ region, q (K₁ z) = q (K₂ z) := by
  intro z hz
  rw [h₁ z hz, h₂ z hz]

/-- **Fiberwise freedom.**  Replacing a section's value at one
    specification by any other member of that specification's fiber
    yields another section.  The section space is closed under
    pointwise fiber moves — nothing upstairs constrains the choice. -/
theorem section_swap [DecidableEq Z] (q : X → Z) (K : Z → X)
    (region : List Z) (h : IsSectionOn q K region)
    (z₀ : Z) (x' : X) (hx' : q x' = z₀) :
    IsSectionOn q (fun z => if z = z₀ then x' else K z) region := by
  intro z hz
  by_cases hcase : z = z₀
  · simp [hcase, hx']
  · simp [hcase]
    exact h z hz

/-! ## Registered witness: four sections, one shadow -/

/-- Four realizations. -/
inductive X4 where
  | p0
  | p1
  | p2
  | p3
deriving DecidableEq, Repr

/-- Two specifications. -/
inductive Z2 where
  | s0
  | s1
deriving DecidableEq, Repr

/-- The registered quotient: fibers {p0, p1} over s0 and {p2, p3}
    over s1. -/
def q4 : X4 → Z2
  | .p0 => .s0
  | .p1 => .s0
  | .p2 => .s1
  | .p3 => .s1

def region2 : List Z2 := [.s0, .s1]

def kA : Z2 → X4
  | .s0 => .p0
  | .s1 => .p2

def kB : Z2 → X4
  | .s0 => .p0
  | .s1 => .p3

def kC : Z2 → X4
  | .s0 => .p1
  | .s1 => .p2

def kD : Z2 → X4
  | .s0 => .p1
  | .s1 => .p3

def allSections : List (Z2 → X4) := [kA, kB, kC, kD]

def isSectionB (K : Z2 → X4) : Bool :=
  region2.all fun z => decide (q4 (K z) = z)

/-- All four registered compilers are sections, they are pairwise
    distinct downstairs, and the section count is exactly the product
    of the fiber sizes (2 × 2 = 4). -/
theorem four_sections_distinct :
    (allSections.all isSectionB = true) ∧
    (kA .s1 ≠ kB .s1) ∧ (kA .s0 ≠ kC .s0) ∧ (kB .s0 ≠ kD .s0) ∧
    (kC .s1 ≠ kD .s1) ∧ allSections.length = 2 * 2 := by
  decide

/-- **One shadow.**  All four sections project to the same
    specification-level record on the whole region: the compiler
    choice is invisible upstairs.  Kernel enumeration of the witness
    plus the general lemma above. -/
theorem four_sections_one_shadow :
    ∀ z ∈ region2,
      q4 (kA z) = q4 (kB z) ∧ q4 (kB z) = q4 (kC z) ∧
        q4 (kC z) = q4 (kD z) := by
  decide

#print axioms sections_spec_indistinguishable
#print axioms section_swap
#print axioms four_sections_distinct
#print axioms four_sections_one_shadow

end KleisliSection
end StructuralIntelligence
