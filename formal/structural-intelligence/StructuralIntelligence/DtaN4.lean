/-!
# Structural Intelligence — n=4 representability iff inclusion

On the registered `{0,1}⁴` harness of Paper A (`delete_the_absolute`),
`Y` is representable from screen `q` iff `G_q ⊆ G_Y`.

Finite biconditional only.  Do not claim general `n`.  No Mathlib.
No `sorry`.  No `native_decide`.  No `Complex.log`.  Not a new letter.
-/

namespace StructuralIntelligence
namespace DtaN4

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

/-- Source-index 4-tuple.  `(g·x)_i = x[perm i]`. -/
structure Perm where
  v0 : Nat
  v1 : Nat
  v2 : Nat
  v3 : Nat
deriving DecidableEq, Repr

def P (v0 v1 v2 v3 : Nat) : Perm := { v0, v1, v2, v3 }

def bit (w : World) : Nat → Bool
  | 0 => w.b0
  | 1 => w.b1
  | 2 => w.b2
  | 3 => w.b3
  | _ => false

def applyPerm (p : Perm) (w : World) : World :=
  W (bit w p.v0) (bit w p.v1) (bit w p.v2) (bit w p.v3)

def allPerms : List Perm :=
  [ P 0 1 2 3, P 1 0 2 3, P 2 1 0 3, P 1 2 0 3, P 2 0 1 3, P 0 2 1 3
  , P 3 2 1 0, P 2 3 1 0, P 2 1 3 0, P 3 1 2 0, P 1 3 2 0, P 1 2 3 0
  , P 3 0 1 2, P 0 3 1 2, P 0 1 3 2, P 3 1 0 2, P 1 3 0 2, P 1 0 3 2
  , P 3 0 2 1, P 0 3 2 1, P 0 2 3 1, P 3 2 0 1, P 2 3 0 1, P 2 0 3 1 ]

def idPerm : Perm := P 0 1 2 3

def rotPerms : List Perm :=
  [ P 0 1 2 3, P 1 2 3 0, P 2 3 0 1, P 3 0 1 2 ]

def stab0Perms : List Perm :=
  allPerms.filter (fun p => p.v0 == 0)

inductive ScreenId where
  | q_id | q_rot | q_perm | q_stab0
deriving DecidableEq, Repr

inductive TaskId where
  | bag | necklace | first_bit | identity
deriving DecidableEq, Repr

def groupOf : ScreenId → List Perm
  | .q_id => [idPerm]
  | .q_rot => rotPerms
  | .q_perm => allPerms
  | .q_stab0 => stab0Perms

def sort3 (a b c : Bool) : Bool × Bool × Bool :=
  let xs := [a, b, c]
  let lo := xs.min?.getD false
  let hi := xs.max?.getD false
  let mid :=
    if a ≠ lo && a ≠ hi then a
    else if b ≠ lo && b ≠ hi then b
    else if c ≠ lo && c ≠ hi then c
    else lo
  -- two equal bits: mid should be that value
  let mid' :=
    if a == b then a
    else if a == c then a
    else if b == c then b
    else mid
  (lo, mid', hi)

def qId (w : World) : World := w

def qRot (w : World) : World :=
  let r0 := w
  let r1 := applyPerm (P 1 2 3 0) w
  let r2 := applyPerm (P 2 3 0 1) w
  let r3 := applyPerm (P 3 0 1 2) w
  -- lex-least rotation; false < true, then b0..b3
  let lexLt (x y : World) : Bool :=
    if x.b0 != y.b0 then !x.b0 && y.b0
    else if x.b1 != y.b1 then !x.b1 && y.b1
    else if x.b2 != y.b2 then !x.b2 && y.b2
    else !x.b3 && y.b3
  let minW (x y : World) : World := if lexLt y x then y else x
  minW (minW r0 r1) (minW r2 r3)

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
  | .q_rot, w => qRot w
  | .q_perm, w => qPerm w
  | .q_stab0, w => qStab0 w

inductive YVal where
  | n : Nat → YVal
  | b : Bool → YVal
  | w : World → YVal
deriving DecidableEq, Repr

def popcount (w : World) : Nat :=
  (if w.b0 then 1 else 0) + (if w.b1 then 1 else 0) +
  (if w.b2 then 1 else 0) + (if w.b3 then 1 else 0)

def evalTask : TaskId → World → YVal
  | .bag, w => .n (popcount w)
  | .necklace, w => .w (qRot w)
  | .first_bit, w => .b w.b0
  | .identity, w => .w w

/-- `Y` is constant on `q`-fibres. -/
def represents (q : ScreenId) (y : TaskId) : Bool :=
  allWorlds.all fun x =>
    allWorlds.all fun x' =>
      !(decide (evalScreen q x = evalScreen q x')) ||
        decide (evalTask y x = evalTask y x')

/-- `g` preserves `Y`. -/
def preserves (y : TaskId) (p : Perm) : Bool :=
  allWorlds.all fun x => decide (evalTask y (applyPerm p x) = evalTask y x)

def gY (y : TaskId) : List Perm :=
  allPerms.filter (preserves y)

def memPerm (p : Perm) : List Perm → Bool
  | [] => false
  | q :: qs => decide (p = q) || memPerm p qs

/-- `G_q ⊆ G_Y`. -/
def included (q : ScreenId) (y : TaskId) : Bool :=
  (groupOf q).all fun p => memPerm p (gY y)

set_option maxRecDepth 100000
set_option maxHeartbeats 800000

theorem dta_n4_representable_iff :
    ∀ q : ScreenId, ∀ y : TaskId, represents q y = included q y := by
  intro q y
  cases q <;> cases y <;> decide

#print axioms dta_n4_representable_iff

end DtaN4
end StructuralIntelligence
