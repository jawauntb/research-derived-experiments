import StructuralIntelligence.CommonSuffScreen

/-!
# Structural Intelligence — Theorem 4, finite counting CI (Wave 9)

Honesty.  The algebraic core of Theorem 4 is already
`commonSuffScreen_refines` (**do not re-prove**).  This file adds
only the finite counting-measure reading:

> On any finite list of worlds, a common sufficient screen makes
> every task **fiber-constant**.  Empirical conditionals
> `count(Y=y | q=z)` are therefore 0 or 1, which is discrete
> conditional independence of `Y` from the rest of `X` given `q`.

The measure-theoretic statement `Y_α ⟂ Y_β | q` on a general
probability space stays open (needs Mathlib measure theory).
No Mathlib here.  No `native_decide`.

### Mathematical claim card

* Objects.  `IsCommonSuffScreen`, fiber-constancy on a list,
  registered `{0,1}²` witness.
* Claims.  CSS ⇒ fiber-constant on every list; registered q =
  first bit determines both registered tasks.
* Withheld.  General probability-space CI.
-/

namespace StructuralIntelligence
namespace T4FiniteCI

set_option maxRecDepth 400000
set_option maxHeartbeats 4000000

/-- `Y` is constant on `q`-fibers inside the listed worlds. -/
def fiberConstantOn {X Z Y : Type}
    (xs : List X) (q : X → Z) (Yf : X → Y) : Prop :=
  ∀ x ∈ xs, ∀ x' ∈ xs, q x = q x' → Yf x = Yf x'

/-- **Finite CI reading of Theorem 4.**  A common sufficient screen
    makes every task fiber-constant on every finite list.  Cite
    `commonSuffScreen_refines`; do not re-prove it. -/
theorem css_implies_fiber_constant
    {X Z A : Type} {Yfam : A → Type}
    {Y : ∀ α : A, X → Yfam α} {q : X → Z}
    (h : IsCommonSuffScreen Y q)
    (xs : List X) (α : A) :
    fiberConstantOn xs q (Y α) := by
  intro x _hx x' _hx' hq
  exact commonSuffScreen_refines h hq α

/-! ## Registered `{0,1}²` witness -/

inductive Bit2 where
  | b00
  | b01
  | b10
  | b11
deriving DecidableEq, Repr

def allBit2 : List Bit2 := [.b00, .b01, .b10, .b11]

def firstBit : Bit2 → Bool
  | .b00 => false
  | .b01 => false
  | .b10 => true
  | .b11 => true

def secondBit : Bit2 → Bool
  | .b00 => false
  | .b01 => true
  | .b10 => false
  | .b11 => true

inductive Task where
  | first
  | firstCopy
deriving DecidableEq, Repr

def Y : Task → Bit2 → Bool
  | .first, w => firstBit w
  | .firstCopy, w => firstBit w

theorem firstBit_is_css : IsCommonSuffScreen Y firstBit := by
  intro α
  refine ⟨fun b => b, ?_⟩
  intro w
  cases α <;> rfl

theorem registered_fiber_constant :
    fiberConstantOn allBit2 firstBit (Y .first) ∧
    fiberConstantOn allBit2 firstBit (Y .firstCopy) := by
  constructor
  · exact css_implies_fiber_constant firstBit_is_css allBit2 .first
  · exact css_implies_fiber_constant firstBit_is_css allBit2 .firstCopy

/-- Second bit is *not* constant on first-bit fibers: q is not a
    screen for an off-fiber task.  Negative control. -/
theorem secondBit_not_fiber_constant :
    ¬ fiberConstantOn allBit2 firstBit secondBit := by
  intro h
  have := h .b00 (by decide) .b01 (by decide) rfl
  exact Bool.false_ne_true this

#print axioms css_implies_fiber_constant
#print axioms registered_fiber_constant
#print axioms secondBit_not_fiber_constant

end T4FiniteCI
end StructuralIntelligence
