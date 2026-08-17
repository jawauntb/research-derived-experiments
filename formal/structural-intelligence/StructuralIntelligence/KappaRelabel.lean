/-!
# Structural Intelligence — κ relabel naturality (Paper F)

The bit-label swap `0 ↔ 3` is a coordinate change, not a change of
essence.  On the disclosed Paper F menu it sends
`first_bit` / `q_stab0` to `last_bit` / `q_stab_last` (and conversely).

This file copies the finite `κ_screen` algorithm (Kirchhoff mismatch
→ transport; else coarsest representing menu screen by fibre count,
then lexicographic screen id; then restore / quotient / noop).
Representing means `Y` is constant on fibres.  That is the
`CommonSuffScreen` criterion; we do not re-prove Theorem 4.

No `Mathlib`.  No `sorry`.  No `Complex.log`.  Not a new letter.

### Mathematical claim card

* Objects.  `World` = four `Bool`s.  `swap03` is the permutation
  `(3,1,2,0)` acting by `(g·x)_i = x[perm i]`.  Tasks
  `yFirstBit x = x.b0`, `yLastBit x = x.b3`.  Screens
  `q_id`, `q_rot`, `q_perm`, `q_stab0`, `q_stab_last` as in Paper F.
  Connection `KIRCHHOFF_FLAT` (no mismatch).
* Claim.  `∀ x, yFirstBit x = yLastBit (swap03 x)` and conversely;
  `κ_screen` on `(first_bit, q_perm)` chooses `q_stab0` / restore;
  on `(last_bit, q_perm)` chooses `q_stab_last` / restore; the
  `q_id` rows choose the same screens with quotient; the converse
  Paper F relabel row holds.
* Assumptions.  Finite enumeration of `{0,1}^4`.  Menu and total
  order are disclosed (fewest fibres, then lex id).
* Identification.  `κ_screen` is Theorem 4 plus a named total order,
  not a new master object.
* Edge / null.  Mismatch is the transport branch; `KIRCHHOFF_FLAT`
  never takes it.  Names are not essence.
-/

namespace StructuralIntelligence
namespace KappaRelabel

/-- A world is four bits.  Python `World = tuple[int, ...]` of length 4. -/
structure World where
  b0 : Bool
  b1 : Bool
  b2 : Bool
  b3 : Bool
  deriving DecidableEq, Repr, Inhabited

/-- `SWAP_03 = (3, 1, 2, 0)` with `(g·x)_i = x[perm i]`.
    So `(g·x).b0 = x.b3`, `b1 = x.b1`, `b2 = x.b2`, `b3 = x.b0`. -/
def swap03 (x : World) : World :=
  { b0 := x.b3, b1 := x.b1, b2 := x.b2, b3 := x.b0 }

def yFirstBit (x : World) : Bool := x.b0
def yLastBit (x : World) : Bool := x.b3

/-- Number of `true` bits among three. -/
def pop3 (a b c : Bool) : Nat :=
  (if a then 1 else 0) + (if b then 1 else 0) + (if c then 1 else 0)

/-- Number of `true` bits among four. -/
def pop4 (x : World) : Nat :=
  pop3 x.b0 x.b1 x.b2 + (if x.b3 then 1 else 0)

/-- Sorted triple, `false < true`.  Same fibres as `tuple(sorted(...))`. -/
def sort3 (a b c : Bool) : Bool × Bool × Bool :=
  match pop3 a b c with
  | 0 => (false, false, false)
  | 1 => (false, false, true)
  | 2 => (false, true, true)
  | _ => (true, true, true)

/-- Identity screen. -/
def qId (x : World) : World := x

/-- Sorted bits.  Same fibres as popcount / the bit histogram. -/
def qPerm (x : World) : World :=
  match pop4 x with
  | 0 => { b0 := false, b1 := false, b2 := false, b3 := false }
  | 1 => { b0 := false, b1 := false, b2 := false, b3 := true }
  | 2 => { b0 := false, b1 := false, b2 := true, b3 := true }
  | 3 => { b0 := false, b1 := true, b2 := true, b3 := true }
  | _ => { b0 := true, b1 := true, b2 := true, b3 := true }

/-- Keep `b0`; sort the rest.  Orbit-canonical map for `Stab(0)`. -/
def qStab0 (x : World) : World :=
  let s := sort3 x.b1 x.b2 x.b3
  { b0 := x.b0, b1 := s.1, b2 := s.2.1, b3 := s.2.2 }

/-- Sort the prefix; keep `b3`.  Dual of `qStab0`. -/
def qStabLast (x : World) : World :=
  let s := sort3 x.b0 x.b1 x.b2
  { b0 := s.1, b1 := s.2.1, b2 := s.2.2, b3 := x.b3 }

/-- Lexicographic `false < true` on the four bits. -/
def worldLt (x y : World) : Bool :=
  if x.b0 != y.b0 then !x.b0 && y.b0
  else if x.b1 != y.b1 then !x.b1 && y.b1
  else if x.b2 != y.b2 then !x.b2 && y.b2
  else !x.b3 && y.b3

def worldMin (x y : World) : World :=
  if worldLt y x then y else x

/-- One rotate-left: `(b0,b1,b2,b3) ↦ (b1,b2,b3,b0)`. -/
def rotate1 (x : World) : World :=
  { b0 := x.b1, b1 := x.b2, b2 := x.b3, b3 := x.b0 }

/-- Lex-least rotation.  Python `q_rot`. -/
def qRot (x : World) : World :=
  let r1 := rotate1 x
  let r2 := rotate1 r1
  let r3 := rotate1 r2
  worldMin x (worldMin r1 (worldMin r2 r3))

/-- Disclosed menu ids, matching the Python strings. -/
inductive ScreenId where
  | q_id
  | q_rot
  | q_perm
  | q_stab0
  | q_stab_last
  deriving DecidableEq, Repr, Inhabited

/-- Lexicographic rank of the Python screen id.
    `"q_id" < "q_perm" < "q_rot" < "q_stab0" < "q_stab_last"`. -/
def ScreenId.lexRank : ScreenId → Nat
  | .q_id => 0
  | .q_perm => 1
  | .q_rot => 2
  | .q_stab0 => 3
  | .q_stab_last => 4

def screenFn : ScreenId → World → World
  | .q_id => qId
  | .q_rot => qRot
  | .q_perm => qPerm
  | .q_stab0 => qStab0
  | .q_stab_last => qStabLast

def menu : List ScreenId :=
  [.q_id, .q_rot, .q_perm, .q_stab0, .q_stab_last]

inductive Action where
  | transport
  | restore
  | quotient
  | noop
  | broken
  deriving DecidableEq, Repr, Inhabited

/-- `KIRCHHOFF_FLAT` has no mismatch.  The other constructor is the
    transport branch of `κ_screen`; unused on the relabel rows. -/
inductive Connection where
  | kirchhoffFlat
  | mismatch
  deriving DecidableEq, Repr

def Connection.mismatches : Connection → Bool
  | .kirchhoffFlat => false
  | .mismatch => true

structure KappaChoice where
  action : Action
  screenId : Option ScreenId
  deriving DecidableEq, Repr

/-- All 16 worlds, lexicographic, matching `product((0,1), repeat=4)`. -/
def allWorlds : List World :=
  [ { b0 := false, b1 := false, b2 := false, b3 := false }
  , { b0 := false, b1 := false, b2 := false, b3 := true }
  , { b0 := false, b1 := false, b2 := true,  b3 := false }
  , { b0 := false, b1 := false, b2 := true,  b3 := true }
  , { b0 := false, b1 := true,  b2 := false, b3 := false }
  , { b0 := false, b1 := true,  b2 := false, b3 := true }
  , { b0 := false, b1 := true,  b2 := true,  b3 := false }
  , { b0 := false, b1 := true,  b2 := true,  b3 := true }
  , { b0 := true,  b1 := false, b2 := false, b3 := false }
  , { b0 := true,  b1 := false, b2 := false, b3 := true }
  , { b0 := true,  b1 := false, b2 := true,  b3 := false }
  , { b0 := true,  b1 := false, b2 := true,  b3 := true }
  , { b0 := true,  b1 := true,  b2 := false, b3 := false }
  , { b0 := true,  b1 := true,  b2 := false, b3 := true }
  , { b0 := true,  b1 := true,  b2 := true,  b3 := false }
  , { b0 := true,  b1 := true,  b2 := true,  b3 := true }
  ]

def consFresh {α} [BEq α] (x : α) (xs : List α) : List α :=
  if xs.any (· == x) then xs else x :: xs

def uniqueCount {α} [BEq α] (xs : List α) : Nat :=
  (xs.foldr consFresh []).length

/-- Fibre count of a screen on the 16-world harness. -/
def fiberCount (q : World → World) : Nat :=
  uniqueCount (allWorlds.map q)

/-- `Y` is constant on every `q`-fibre.  Representing, not a CSS proof. -/
def represents (y : World → Bool) (q : World → World) : Bool :=
  allWorlds.all fun x =>
    allWorlds.all fun x' =>
      (q x != q x') || (y x == y x')

def representing (y : World → Bool) : List ScreenId :=
  menu.filter fun s => represents y (screenFn s)

/-- Coarser = fewer fibres; ties broken by lex screen id (`min` on ids). -/
def better (a b : ScreenId) : ScreenId :=
  let na := fiberCount (screenFn a)
  let nb := fiberCount (screenFn b)
  if Nat.blt na nb then a
  else if Nat.blt nb na then b
  else if Nat.blt a.lexRank b.lexRank then a
  else b

def coarsestRepresenting (y : World → Bool) : Option ScreenId :=
  match representing y with
  | [] => none
  | s :: ss => some (ss.foldl better s)

/-- Finite `κ_screen`.  Mismatch → transport; else coarsest representing
    screen, then restore / quotient / noop against the current `q`. -/
def kappaScreen (y : World → Bool) (q : ScreenId) (c : Connection) : KappaChoice :=
  if c.mismatches then
    { action := .transport, screenId := none }
  else
    match coarsestRepresenting y with
    | none => { action := .broken, screenId := none }
    | some chosen =>
      let qFn := screenFn q
      let representsQ := represents y qFn
      let chosenN := fiberCount (screenFn chosen)
      let currentN := fiberCount qFn
      let action :=
        if !representsQ then Action.restore
        else if Nat.blt chosenN currentN then Action.quotient
        else Action.noop
      { action, screenId := some chosen }

/-! ## Facts 1–2: the swap is a coordinate change -/

theorem yFirstBit_swap03 (x : World) :
    yFirstBit x = yLastBit (swap03 x) :=
  rfl

theorem yLastBit_swap03 (x : World) :
    yLastBit x = yFirstBit (swap03 x) :=
  rfl

/-! ## Facts 3–7: `κ_screen` on the Paper F relabel rows -/

set_option maxRecDepth 10000

theorem kappa_firstBit_qPerm :
    kappaScreen yFirstBit .q_perm .kirchhoffFlat =
      { action := .restore, screenId := some .q_stab0 } := rfl

theorem kappa_lastBit_qPerm :
    kappaScreen yLastBit .q_perm .kirchhoffFlat =
      { action := .restore, screenId := some .q_stab_last } := rfl

theorem kappa_firstBit_qId :
    kappaScreen yFirstBit .q_id .kirchhoffFlat =
      { action := .quotient, screenId := some .q_stab0 } := rfl

theorem kappa_lastBit_qId :
    kappaScreen yLastBit .q_id .kirchhoffFlat =
      { action := .quotient, screenId := some .q_stab_last } := rfl

/-- Paper F converse row: `last_bit,q_perm` maps to `first_bit,q_perm`
    with choices `q_stab_last → q_stab0`. -/
theorem kappa_relabel_converse :
    kappaScreen yLastBit .q_perm .kirchhoffFlat =
      { action := .restore, screenId := some .q_stab_last } ∧
    kappaScreen yFirstBit .q_perm .kirchhoffFlat =
      { action := .restore, screenId := some .q_stab0 } :=
  ⟨kappa_lastBit_qPerm, kappa_firstBit_qPerm⟩

/-- Headline: bit-label swap `0 ↔ 3` is natural.  Names are not essence. -/
theorem kappa_relabel_natural :
    (∀ x, yFirstBit x = yLastBit (swap03 x)) ∧
    (∀ x, yLastBit x = yFirstBit (swap03 x)) ∧
    kappaScreen yFirstBit .q_perm .kirchhoffFlat =
      { action := .restore, screenId := some .q_stab0 } ∧
    kappaScreen yLastBit .q_perm .kirchhoffFlat =
      { action := .restore, screenId := some .q_stab_last } ∧
    kappaScreen yFirstBit .q_id .kirchhoffFlat =
      { action := .quotient, screenId := some .q_stab0 } ∧
    kappaScreen yLastBit .q_id .kirchhoffFlat =
      { action := .quotient, screenId := some .q_stab_last } ∧
    kappaScreen yLastBit .q_perm .kirchhoffFlat =
      { action := .restore, screenId := some .q_stab_last } ∧
    kappaScreen yFirstBit .q_perm .kirchhoffFlat =
      { action := .restore, screenId := some .q_stab0 } :=
  ⟨yFirstBit_swap03, yLastBit_swap03, kappa_firstBit_qPerm, kappa_lastBit_qPerm,
    kappa_firstBit_qId, kappa_lastBit_qId, kappa_lastBit_qPerm, kappa_firstBit_qPerm⟩

#print axioms kappa_relabel_natural

end KappaRelabel
end StructuralIntelligence
