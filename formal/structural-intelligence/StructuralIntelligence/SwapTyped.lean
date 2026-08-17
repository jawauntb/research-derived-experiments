/-!
# Structural Intelligence — Paper B swap cell

Typed restore / quotient succeed; the crossed over-repair fails.
Opposite repairs are not interchangeable.  Do not reopen enumeration.

Finite `{0,1}⁴` only.  No Mathlib.  No `sorry`.  No `native_decide`.
-/

namespace StructuralIntelligence
namespace SwapTyped

structure World where
  b0 : Bool
  b1 : Bool
  b2 : Bool
  b3 : Bool
deriving DecidableEq, Repr

def W (b0 b1 b2 b3 : Bool) : World := { b0, b1, b2, b3 }

def allWorlds : List World :=
  [ W false false false false, W false false false true
  , W false false true  false, W false false true  true
  , W false true  false false, W false true  false true
  , W false true  true  false, W false true  true  true
  , W true  false false false, W true  false false true
  , W true  false true  false, W true  false true  true
  , W true  true  false false, W true  true  false true
  , W true  true  true  false, W true  true  true  true ]

inductive ScreenId where
  | q_id | q_perm | q_stab0
deriving DecidableEq, Repr

inductive TaskId where
  | first_bit | bag
deriving DecidableEq, Repr

def sort3 (a b c : Bool) : Bool × Bool × Bool :=
  let lo := [a, b, c].min?.getD false
  let hi := [a, b, c].max?.getD false
  let mid' :=
    if a == b then a
    else if a == c then a
    else if b == c then b
    else if a ≠ lo && a ≠ hi then a
    else if b ≠ lo && b ≠ hi then b
    else c
  (lo, mid', hi)

def qId (w : World) : World := w

def qPerm (w : World) : World :=
  let n :=
    (if w.b0 then 1 else 0) + (if w.b1 then 1 else 0) +
    (if w.b2 then 1 else 0) + (if w.b3 then 1 else 0)
  match n with
  | 0 => W false false false false
  | 1 => W false false false true
  | 2 => W false false true  true
  | 3 => W false true  true  true
  | _ => W true  true  true  true

def qStab0 (w : World) : World :=
  let (a, b, c) := sort3 w.b1 w.b2 w.b3
  W w.b0 a b c

def evalScreen : ScreenId → World → World
  | .q_id, w => qId w
  | .q_perm, w => qPerm w
  | .q_stab0, w => qStab0 w

inductive YVal where
  | b : Bool → YVal
  | n : Nat → YVal
deriving DecidableEq, Repr

def popcount (w : World) : Nat :=
  (if w.b0 then 1 else 0) + (if w.b1 then 1 else 0) +
  (if w.b2 then 1 else 0) + (if w.b3 then 1 else 0)

def evalTask : TaskId → World → YVal
  | .first_bit, w => .b w.b0
  | .bag, w => .n (popcount w)

def represents (q : ScreenId) (y : TaskId) : Bool :=
  allWorlds.all fun x =>
    allWorlds.all fun x' =>
      !(decide (evalScreen q x = evalScreen q x')) ||
        decide (evalTask y x = evalTask y x')

def uniqueCount {α : Type} [DecidableEq α] : List α → Nat
  | [] => 0
  | x :: xs => uniqueCount xs + if decide (x ∈ xs) then 0 else 1

def fiberCount (s : ScreenId) : Nat :=
  uniqueCount (allWorlds.map (evalScreen s))

set_option maxRecDepth 100000
set_option maxHeartbeats 400000

theorem over_typed_stab0 : represents .q_stab0 .first_bit = true := by decide
theorem over_typed_id : represents .q_id .first_bit = true := by decide
theorem over_crossed_perm : represents .q_perm .first_bit = false := by decide
theorem under_typed_perm : represents .q_perm .bag = true := by decide
theorem under_privilege_id : represents .q_id .bag = true := by decide
theorem fiber_perm_lt_id : fiberCount .q_perm < fiberCount .q_id := by decide

/-- Typed restore/quotient succeed; crossed over-repair (`q_perm` on
    `first_bit`) fails.  Opposite repairs are not interchangeable. -/
theorem swap_typed_wins :
    represents .q_stab0 .first_bit = true ∧
    represents .q_id .first_bit = true ∧
    represents .q_perm .first_bit = false ∧
    represents .q_perm .bag = true ∧
    represents .q_id .bag = true ∧
    fiberCount .q_perm < fiberCount .q_id :=
  ⟨over_typed_stab0, over_typed_id, over_crossed_perm,
    under_typed_perm, under_privilege_id, fiber_perm_lt_id⟩

#print axioms swap_typed_wins

end SwapTyped
end StructuralIntelligence
