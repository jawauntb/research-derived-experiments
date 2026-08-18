import StructuralIntelligence.KappaScreen

/-!
# Structural Intelligence — Door 3: concern picks the screen (Wave 5)

Honesty.  This file banks the door-3 headlines of
`experiments/delete_repair_concern/` and
`experiments/delete_repair_concern_transport/`.  Concern is a
registered weight vector and nothing else — not valence, not agency,
not learned.  The choice rule is expected serving cost over `bag`'s
representing screens with Paper F's tie-break (fewest fibres, then
lexicographic name).  We do not re-prove Theorem 4 or any Wave 2
headline.  No Mathlib.  No `native_decide`.  Kernel `decide` only.

Arithmetic is exact by integer scaling, disclosed here once:

* A half–half concern over tasks `{t₁, t₂}` has expected cost
  `(c t₁ + c t₂) / 2`; we compare the **sums** `c t₁ + c t₂`.
  The Python gap `21/2` appears as the sum-gap `21`.
* The dial `w_ε = (1−ε)·bag + ε·pair_eq` with `ε = k/54` has expected
  cost `((54−k)·c bag + k·c pair_eq) / 54`; we compare the scaled
  costs `(54−k)·c bag + k·c pair_eq`.
  The Python boundaries `11/27` and `7/27` appear as `k = 22` and
  `k = 14` on the `k/54` grid.

Headlines:

* `choice_*` — the six registered concerns select four distinct
  screens; the mirrored pair selects the `q_stab0`/`q_stab_last`
  duals (reversal naturality at the choice layer).
* `unweighted_strictly_beaten` — the concern-free Paper F choice
  `q_perm` loses to `q_stab0` by sum-gap 21 under `bag + first_bit`.
* `boundary_base` — the dial crosses `q_perm → q_id` at exactly
  `k = 22` (ε = 11/27); the tie keeps `q_perm` by fewest fibres.
* `boundary_ext`, `boundary_menu_relative` — under the extended menu
  the dial crosses `q_perm → q_pair01` at exactly `k = 14`
  (ε = 7/27): the concern boundary is menu-relative.
-/

namespace StructuralIntelligence
namespace ConcernChoice

open KappaScreen (World W allWorlds ScreenId TaskId Action TaskValue
  evalScreen evalTask uniqueCount popcount represents fiberCount menu
  screenLt)

set_option maxRecDepth 4000000
set_option maxHeartbeats 16000000

/-! ## Base-menu concern choice -/

/-- Registered serving cost: fibre count when the screen represents
    the task, `2 · n_worlds = 32` when it does not. -/
def cost (t : TaskId) (s : ScreenId) : Nat :=
  if represents t s then fiberCount s else 32

/-- `bag`'s representing screens in the base menu (all five). -/
def candidates : List ScreenId :=
  menu.filter (fun s => represents .bag s)

theorem bag_representing_all_five : candidates.length = 5 := by decide

/-- Min-cost pick with Paper F's tie-break: strictly cheaper wins;
    on a cost tie, fewer fibres then lexicographic name wins. -/
def pick (c : ScreenId → Nat) : List ScreenId → Option ScreenId
  | [] => none
  | s :: ss =>
    some (ss.foldl
      (fun a b =>
        if c b < c a || (c b == c a && screenLt b a) then b else a) s)

def sumCost (ts : List TaskId) (s : ScreenId) : Nat :=
  ts.foldl (fun acc t => acc + cost t s) 0

def choosePair (t1 t2 : TaskId) : Option ScreenId :=
  pick (fun s => cost t1 s + cost t2 s) candidates

/-! ## The six registered concerns -/

theorem choice_delta_bag :
    pick (fun s => cost .bag s) candidates = some .q_perm := by decide

theorem choice_bag_first :
    choosePair .bag .first_bit = some .q_stab0 := by decide

theorem choice_bag_last :
    choosePair .bag .last_bit = some .q_stab_last := by decide

theorem choice_bag_pair_eq :
    choosePair .bag .pair_eq = some .q_id := by decide

theorem choice_bag_parity :
    choosePair .bag .parity = some .q_perm := by decide

def allSix : List TaskId :=
  [.bag, .first_bit, .last_bit, .parity, .pair_eq, .identity]

theorem choice_all_six :
    pick (sumCost allSix) candidates = some .q_id := by decide

/-- The concern-free Paper F choice `q_perm` is strictly beaten under
    `bag + first_bit`: sum costs 16 vs 37, gap 21 (expected-cost gap
    21/2). -/
theorem unweighted_strictly_beaten :
    cost .bag .q_stab0 + cost .first_bit .q_stab0 + 21 =
      cost .bag .q_perm + cost .first_bit .q_perm := by decide

/-! ## The base-menu dial: boundary at k = 22 (ε = 11/27) -/

/-- Expected cost of `w_ε` at `ε = k/54`, scaled by 54. -/
def costEps (k : Nat) (s : ScreenId) : Nat :=
  (54 - k) * cost .bag s + k * cost .pair_eq s

def chooseEps (k : Nat) : Option ScreenId := pick (costEps k) candidates

/-- **Door 3 boundary, base menu.**  On the full `k/54` grid the dial
    picks `q_perm` up to and including the exact tie at `k = 22`
    (ε = 11/27, kept by fewest fibres) and `q_id` above it. -/
theorem boundary_base :
    ∀ k ∈ List.range 55,
      chooseEps k =
        some (if k ≤ 22 then ScreenId.q_perm else ScreenId.q_id) := by
  decide

/-! ## Extended menu: the boundary is menu-relative -/

/-- Seven-screen alphabet for the extended menu. -/
inductive SX where
  | id
  | rot
  | perm
  | stab0
  | stabLast
  | pair01
  | pair23
deriving DecidableEq, Repr

def evalSX : SX → World → World
  | .id, w => w
  | .rot, w => evalScreen .q_rot w
  | .perm, w => evalScreen .q_perm w
  | .stab0, w => evalScreen .q_stab0 w
  | .stabLast, w => evalScreen .q_stab_last w
  | .pair01, w => W (w.b0 && w.b1) (w.b0 || w.b1) w.b2 w.b3
  | .pair23, w => W w.b0 w.b1 (w.b2 && w.b3) (w.b2 || w.b3)

/-- Python name order:
    `q_id < q_pair01 < q_pair23 < q_perm < q_rot < q_stab0 < q_stab_last`. -/
def nameRankSX : SX → Nat
  | .id => 0
  | .pair01 => 1
  | .pair23 => 2
  | .perm => 3
  | .rot => 4
  | .stab0 => 5
  | .stabLast => 6

def repSX (t : TaskId) (s : SX) : Bool :=
  allWorlds.all fun x =>
    allWorlds.all fun x' =>
      !(decide (evalSX s x = evalSX s x')) ||
        decide (evalTask t x = evalTask t x')

def fibSX (s : SX) : Nat := uniqueCount (allWorlds.map (evalSX s))

def costSX (t : TaskId) (s : SX) : Nat :=
  if repSX t s then fibSX s else 32

def screenLtSX (a b : SX) : Bool :=
  fibSX a < fibSX b || (fibSX a == fibSX b && nameRankSX a < nameRankSX b)

def menuExt : List SX :=
  [.id, .rot, .perm, .stab0, .stabLast, .pair01, .pair23]

def candidatesExt : List SX := menuExt.filter (fun s => repSX .bag s)

theorem bag_ext_representing_seven : candidatesExt.length = 7 := by decide

def pickSX (c : SX → Nat) : List SX → Option SX
  | [] => none
  | s :: ss =>
    some (ss.foldl
      (fun a b =>
        if c b < c a || (c b == c a && screenLtSX b a) then b else a) s)

def costEpsExt (k : Nat) (s : SX) : Nat :=
  (54 - k) * costSX .bag s + k * costSX .pair_eq s

def chooseEpsExt (k : Nat) : Option SX := pickSX (costEpsExt k) candidatesExt

/-- **Door 3b boundary, extended menu.**  The dial crosses
    `q_perm → q_pair01` at exactly `k = 14` (ε = 7/27); the tie keeps
    `q_perm` by fewest fibres, and above it `q_pair01` beats both
    `q_pair23` (name) and `q_id` (12 < 16 fibres). -/
theorem boundary_ext :
    ∀ k ∈ List.range 55,
      chooseEpsExt k =
        some (if k ≤ 14 then SX.perm else SX.pair01) := by
  decide

/-- The mirrored concern pair chooses the reversal duals under the
    extended menu as well. -/
theorem mirrored_dual_ext :
    pickSX (fun s => costSX .bag s + costSX .first_bit s)
        candidatesExt = some .stab0 ∧
    pickSX (fun s => costSX .bag s + costSX .last_bit s)
        candidatesExt = some .stabLast := by
  decide

/-- **The concern boundary is menu-relative**: `k = 22` (ε = 11/27) on
    the base menu against `k = 14` (ε = 7/27) on the extended menu. -/
theorem boundary_menu_relative : (22 : Nat) ≠ 14 := by decide

#print axioms choice_bag_first
#print axioms boundary_base
#print axioms boundary_ext
#print axioms mirrored_dual_ext

end ConcernChoice
end StructuralIntelligence
