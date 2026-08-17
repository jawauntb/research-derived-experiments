/-!
# Structural Intelligence — EML zero identity

Algebraic rewrite of the registered US-4′ zero witness

`eml(a, eml(eml(a,1),1)) = 0`

for a carrier element `a` (the Python instrument specialises to
`a ∈ {1, x}`).  Definition:

`eml(a, b) := exp(a) - ln(b)`.

No `Mathlib`, no `Real`, no `Float`, no `Complex.log`.  Paper 0 /
`log 0` is off this path: after `ln 1 = 0` the inner argument of the
outer `ln` is definitionally in the image of `exp`.

The `exp`/`ln` cancellation laws and the two subtraction facts are
**class fields** (explicit hypotheses), not environment `axiom`s.
`#print axioms eml_zero_identity` is therefore empty: the rewrite
uses only those fields.

Honesty.  This does not construct `ℝ`, does not prove that the
usual real `exp`/`ln` satisfy the fields, and does not identify
functions from a numerical grid.  It kernel-checks the rewrite
`exp(a) - ln(exp(exp(a))) = 0` from cancellation plus `x-0=x`
and `x-x=0`.

### Mathematical claim card

* Objects.  Carrier `α`; `exp, ln : α → α`; `sub : α → α → α`;
  `zero, one : α`; `Pos : α → Prop` (intended `x > 0`).
* Claim.  `∀ a : α, eml a (eml (eml a one) one) = zero`.
* Assumptions.  `ln (exp x) = x`; `Pos x → exp (ln x) = x`;
  `exp zero = one`; `Pos (exp x)`; `sub x zero = x`;
  `sub x x = zero`.
* Identification.  `eml` is the definition above, not a new primitive.
* Edge / null.  `ln 0` is never applied.  The middle argument equals
  `exp (exp a)` and is `Pos` by `exp_pos`.
-/

namespace StructuralIntelligence
namespace EmlZeroIdentity

/-- Minimal exp/ln/subtraction fragment used by the zero rewrite.
    Not a ring.  The intended model is `ℝ` with the usual `exp`/`ln`,
    but that model is not constructed here. -/
class ExpLn (α : Type) where
  exp : α → α
  ln : α → α
  sub : α → α → α
  zero : α
  one : α
  /-- Intended meaning: `x > 0`.  Used only to state `exp_ln`. -/
  Pos : α → Prop
  /-- `ln (exp x) = x`. -/
  ln_exp : ∀ x, ln (exp x) = x
  /-- `exp (ln x) = x` on positives. -/
  exp_ln : ∀ x, Pos x → exp (ln x) = x
  /-- `exp 0 = 1`, so `ln 1 = 0` follows from `ln_exp`. -/
  exp_zero : exp zero = one
  /-- Image of `exp` is positive. -/
  exp_pos : ∀ x, Pos (exp x)
  /-- `x - 0 = x`. -/
  sub_zero : ∀ x, sub x zero = x
  /-- `x - x = 0`. -/
  sub_self : ∀ x, sub x x = zero

namespace ExpLn

variable {α : Type} [ExpLn α]

/-- Odrzywołek operator: `eml(a,b) = exp(a) - ln(b)`. -/
def eml (a b : α) : α :=
  sub (exp a) (ln b)

/-- `ln 1 = ln (exp 0) = 0`. -/
theorem ln_one : ln (one : α) = zero := by
  calc ln one
      = ln (exp zero) := by rw [exp_zero]
    _ = zero          := ln_exp zero

/-- `eml(a,1) = exp(a) - ln(1) = exp(a)`. -/
theorem eml_right_one (a : α) : eml a one = exp a := by
  calc eml a one
      = sub (exp a) (ln one) := rfl
    _ = sub (exp a) zero     := by rw [ln_one]
    _ = exp a                := sub_zero (exp a)

/-- `eml(eml(a,1),1) = exp(exp(a))`. -/
theorem eml_eml_right_one (a : α) :
    eml (eml a one) one = exp (exp a) := by
  calc eml (eml a one) one
      = exp (eml a one) := eml_right_one (eml a one)
    _ = exp (exp a)     := by rw [eml_right_one a]

/-- The middle argument is in the image of `exp`, hence `Pos`.
    This is the positivity side-condition that keeps `ln 0` off
    the path. -/
theorem middle_pos (a : α) : Pos (eml (eml a one) one) := by
  rw [eml_eml_right_one]
  exact exp_pos (exp a)

/-- `exp ∘ ln` cancels on the middle argument. -/
theorem exp_ln_middle (a : α) :
    exp (ln (eml (eml a one) one)) = eml (eml a one) one :=
  exp_ln _ (middle_pos a)

/-- **Headline.**  `eml(a, eml(eml(a,1),1)) = 0`. -/
theorem eml_zero_identity (a : α) :
    eml a (eml (eml a one) one) = zero := by
  calc eml a (eml (eml a one) one)
      = sub (exp a) (ln (eml (eml a one) one)) := rfl
    _ = sub (exp a) (ln (exp (exp a)))         := by rw [eml_eml_right_one]
    _ = sub (exp a) (exp a)                    := by rw [ln_exp]
    _ = zero                                   := sub_self (exp a)

/-- Constant-leaf specialisation: `eml(1, eml(eml(1,1),1)) = 0`. -/
theorem eml_zero_identity_one :
    eml (one : α) (eml (eml one one) one) = zero :=
  eml_zero_identity one

/-- Variable-leaf specialisation: `eml(x, eml(eml(x,1),1)) = 0`. -/
theorem eml_zero_identity_x (x : α) :
    eml x (eml (eml x one) one) = zero :=
  eml_zero_identity x

end ExpLn

end EmlZeroIdentity
end StructuralIntelligence
