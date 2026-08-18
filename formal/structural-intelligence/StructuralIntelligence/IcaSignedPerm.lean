/-!
# Structural Intelligence — ICA identifiability class, Fin 2 (Wave 9)

Honesty.  Classical linear ICA (Comon / Hyvärinen: unmixing up to
permutation and sign for non-Gaussian independent sources) is
**not** proved here.  Instrument 8's Amari scores stay Python
(quarantined Monte Carlo).

This file banks only the **identifiability-class algebra** on
two coordinates: a 2×2 integer matrix is a signed permutation iff
it is diagonal-with-units or anti-diagonal-with-units.  Left
multiplication permutes and signs the registered source
`(1, -2)`.  That is the equivalence class Theorem 7 quotes.
The analytic recovery theorem stays needs-mathlib.

No Mathlib.  No `native_decide`.  Kernel `decide` only.

### Mathematical claim card

* Objects.  Explicit 2×2 integer matrices, signed-permutation
  predicate, action on a registered source vector.
* Claims.  The four signed permutations satisfy the predicate;
  a dense mixture does not; the action permutes-and-signs
  `(1, -2)`.
* Withheld.  Laplace sources, FastICA, Amari index, d_Z > 2,
  Theorem 7 itself.
-/

namespace StructuralIntelligence
namespace IcaSignedPerm

set_option maxRecDepth 400000
set_option maxHeartbeats 2000000

/-- Row-major 2×2 integer matrix `(a b ; c d)`. -/
structure Mat2 where
  a : Int
  b : Int
  c : Int
  d : Int
deriving DecidableEq, Repr

structure Vec2 where
  x : Int
  y : Int
deriving DecidableEq, Repr

def mulVec (M : Mat2) (v : Vec2) : Vec2 :=
  ⟨M.a * v.x + M.b * v.y, M.c * v.x + M.d * v.y⟩

/-- Signed-permutation matrices on two coordinates. -/
def isSignedPerm (M : Mat2) : Bool :=
  decide (
    ((M.a = 1 ∨ M.a = -1) ∧ M.b = 0 ∧ M.c = 0 ∧ (M.d = 1 ∨ M.d = -1)) ∨
    (M.a = 0 ∧ (M.b = 1 ∨ M.b = -1) ∧ (M.c = 1 ∨ M.c = -1) ∧ M.d = 0))

def idM : Mat2 := ⟨1, 0, 0, 1⟩
def swapM : Mat2 := ⟨0, 1, 1, 0⟩
def sign0M : Mat2 := ⟨-1, 0, 0, 1⟩
def swapSignM : Mat2 := ⟨0, -1, 1, 0⟩
def denseM : Mat2 := ⟨1, 1, 1, 1⟩

def src : Vec2 := ⟨1, -2⟩

theorem id_signed : isSignedPerm idM = true := by decide
theorem swap_signed : isSignedPerm swapM = true := by decide
theorem sign0_signed : isSignedPerm sign0M = true := by decide
theorem swapSign_signed : isSignedPerm swapSignM = true := by decide
theorem dense_not_signed : isSignedPerm denseM = false := by decide

theorem id_acts_as_id : mulVec idM src = src := by decide

theorem swap_swaps : mulVec swapM src = ⟨-2, 1⟩ := by decide

theorem sign0_flips_first : mulVec sign0M src = ⟨-1, -2⟩ := by decide

/-- **ICA class on two coordinates.**  The four registered signed
    permutations are legal unmixing leftovers; a dense mixture is
    not.  This is not Theorem 7. -/
theorem ica_class_fin2 :
    isSignedPerm idM = true ∧
    isSignedPerm swapM = true ∧
    isSignedPerm sign0M = true ∧
    isSignedPerm swapSignM = true ∧
    isSignedPerm denseM = false := by
  decide

#print axioms ica_class_fin2
#print axioms swap_swaps
#print axioms sign0_flips_first

end IcaSignedPerm
end StructuralIntelligence
