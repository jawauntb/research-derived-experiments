import StructuralIntelligence.KappaScreen

/-!
# Structural Intelligence — Door 1: gold is menu-relative (Wave 5)

Honesty.  This file banks the door-1 headline of
`experiments/delete_repair_menu_blind/`: empirical repair gold, exactly
Paper E's rule with the menu as an explicit argument, **flips** on a
fixed case when the menu is extended.  Therefore no menu-blind κ — no
function of (task, screen, edges) alone, of any width — can match gold
under both menus.  The impossibility step is a two-point separation:
one input, two required outputs.

Everything is built on the Wave 2 vocabulary in
`StructuralIntelligence.KappaScreen` (worlds, screens, tasks,
`represents`, `fiberCount`, Paper E `gold`).  We do not re-prove
Theorem 4, Path A/B, or the Wave 2 headlines.  No Mathlib.  No
`native_decide`.  Kernel `decide` only.

New objects, registered in the Python instrument first:

* `qPair01` — sort the first two bits; 12 fibres.
* `qPair23` — sort the last two bits; 12 fibres.
* `menuBase` — the Paper E five-screen menu.
* `menuExt`  — `menuBase` plus the two pair screens.
* `goldMenu` — Paper E `gold` with the menu as an argument.

Headlines:

* `gold_flip_pair_eq`, `gold_flip_pair23` — the registered flips
  (`noop` under `menuBase`, `quotient` under `menuExt`).
* `menu_blind_kappa_impossible` — ∀ f : task → screen → edges → action,
  f cannot agree with gold under both menus.
* `base_gold_consistent` — on the six Paper E tasks and five base
  screens, `goldMenu · menuBase` equals Wave 2's `gold` exactly.
-/

namespace StructuralIntelligence
namespace MenuBlind

open KappaScreen (World W allWorlds ScreenId TaskId Action TaskValue
  evalScreen evalTask uniqueCount popcount Aff aff kirchhoffFlat
  kirchhoffMismatch gold)

/-- Sort the first two bits: `(b0, b1) ↦ (b0 && b1, b0 || b1)`. -/
def qPair01 (w : World) : World :=
  W (w.b0 && w.b1) (w.b0 || w.b1) w.b2 w.b3

/-- Sort the last two bits: `(b2, b3) ↦ (b2 && b3, b2 || b3)`. -/
def qPair23 (w : World) : World :=
  W w.b0 w.b1 (w.b2 && w.b3) (w.b2 || w.b3)

/-- Extended screen alphabet: the five Paper E screens plus the two
    pair screens. -/
inductive ScreenX where
  | base (s : ScreenId)
  | pair01
  | pair23
deriving DecidableEq, Repr

/-- Extended task alphabet: the six Paper E tasks plus the three new
    held-out tasks of the door-1 instrument. -/
inductive TaskX where
  | base (t : TaskId)
  | pair23
  | orT
  | countGe2
deriving DecidableEq, Repr

def evalScreenX : ScreenX → World → World
  | .base s, w => evalScreen s w
  | .pair01, w => qPair01 w
  | .pair23, w => qPair23 w

def evalTaskX : TaskX → World → TaskValue
  | .base t, w => evalTask t w
  | .pair23, w => .bit (decide (w.b2 = w.b3))
  | .orT, w => .bit (w.b0 || w.b1 || w.b2 || w.b3)
  | .countGe2, w => .bit (decide (2 ≤ popcount w))

/-- Fibre-constancy over the 16 worlds, as in Wave 2. -/
def representsX (t : TaskX) (s : ScreenX) : Bool :=
  allWorlds.all fun x =>
    allWorlds.all fun x' =>
      !(decide (evalScreenX s x = evalScreenX s x')) ||
        decide (evalTaskX t x = evalTaskX t x')

def fiberCountX (s : ScreenX) : Nat :=
  uniqueCount (allWorlds.map (evalScreenX s))

/-- The Paper E menu, embedded. -/
def menuBase : List ScreenX :=
  [.base .q_id, .base .q_rot, .base .q_perm, .base .q_stab0,
   .base .q_stab_last]

/-- The extended menu of the door-1 instrument. -/
def menuExt : List ScreenX := menuBase ++ [.pair01, .pair23]

/-- Paper E `gold_of` with the menu as an explicit argument. -/
def goldMenu (t : TaskX) (q : ScreenX) (edges : List Aff)
    (m : List ScreenX) : Action :=
  if kirchhoffMismatch edges then .transport
  else if !representsX t q then
    if m.any (fun r => representsX t r && fiberCountX q < fiberCountX r)
    then .restore else .broken
  else if m.any (fun r => representsX t r && fiberCountX r < fiberCountX q)
  then .quotient else .noop

/-- Python lexicographic name order over the seven ids:
    `q_id < q_pair01 < q_pair23 < q_perm < q_rot < q_stab0 < q_stab_last`. -/
def nameRankX : ScreenX → Nat
  | .base .q_id => 0
  | .pair01 => 1
  | .pair23 => 2
  | .base .q_perm => 3
  | .base .q_rot => 4
  | .base .q_stab0 => 5
  | .base .q_stab_last => 6

def screenLtX (a b : ScreenX) : Bool :=
  fiberCountX a < fiberCountX b ||
    (fiberCountX a == fiberCountX b && nameRankX a < nameRankX b)

def minScreenX (a b : ScreenX) : ScreenX :=
  if screenLtX b a then b else a

/-- Coarsest representing screen in the given menu (Paper F order). -/
def coarsestX (t : TaskX) (m : List ScreenX) : Option ScreenX :=
  match m.filter (fun s => representsX t s) with
  | [] => none
  | s :: ss => some (ss.foldl minScreenX s)

/-- κ_screen with the menu as an argument (action only). -/
def kappaScreenMenu (t : TaskX) (q : ScreenX) (edges : List Aff)
    (m : List ScreenX) : Action :=
  if kirchhoffMismatch edges then .transport
  else
    match coarsestX t m with
    | none => .broken
    | some rStar =>
      if !representsX t q then .restore
      else if fiberCountX rStar < fiberCountX q then .quotient
      else .noop

def allTasksBase : List TaskId :=
  [.bag, .first_bit, .last_bit, .identity, .parity, .pair_eq]

def allScreensBase : List ScreenId :=
  [.q_id, .q_rot, .q_perm, .q_stab0, .q_stab_last]

set_option maxRecDepth 100000
set_option maxHeartbeats 4000000

/-! ## Fibre counts of the new screens -/

theorem fiberCount_pair01 : fiberCountX .pair01 = 12 := by decide

theorem fiberCount_pair23 : fiberCountX .pair23 = 12 := by decide

/-! ## The registered flips -/

/-- `pair_eq` on `q_id`: `noop` under the base menu, `quotient` once
    `q_pair01` joins. -/
theorem gold_flip_pair_eq :
    goldMenu (.base .pair_eq) (.base .q_id) kirchhoffFlat menuBase =
      .noop ∧
    goldMenu (.base .pair_eq) (.base .q_id) kirchhoffFlat menuExt =
      .quotient := by
  decide

/-- `pair23` on `q_id`: the second registered flip. -/
theorem gold_flip_pair23 :
    goldMenu .pair23 (.base .q_id) kirchhoffFlat menuBase = .noop ∧
    goldMenu .pair23 (.base .q_id) kirchhoffFlat menuExt = .quotient := by
  decide

/-! ## Headline: no menu-blind κ -/

/-- **Door 1, closed categorically.**  Any function of
    (task, screen, edges) alone — any menu-blind κ, of any signature
    width — is constant across menus, so it cannot match gold under
    both `menuBase` and `menuExt` on the flip case. -/
theorem menu_blind_kappa_impossible :
    ∀ f : TaskX → ScreenX → List Aff → Action,
      ¬ (f (.base .pair_eq) (.base .q_id) kirchhoffFlat =
           goldMenu (.base .pair_eq) (.base .q_id) kirchhoffFlat
             menuBase ∧
         f (.base .pair_eq) (.base .q_id) kirchhoffFlat =
           goldMenu (.base .pair_eq) (.base .q_id) kirchhoffFlat
             menuExt) := by
  intro f h
  have h1 := h.1
  have h2 := h.2
  rw [gold_flip_pair_eq.1] at h1
  rw [gold_flip_pair_eq.2] at h2
  exact Action.noConfusion (h1.symm.trans h2)

/-! ## Consistency with Wave 2 and per-menu exactness -/

/-- Under the base menu, `goldMenu` on embedded tasks and screens is
    exactly Wave 2's `gold`.  The instrument extends Paper E; it does
    not reinterpret it. -/
theorem base_gold_consistent :
    ∀ t ∈ allTasksBase, ∀ q ∈ allScreensBase,
      goldMenu (.base t) (.base q) kirchhoffFlat menuBase =
        gold t q kirchhoffFlat := by
  decide

/-- κ_screen, recomputed per menu, is exact on both flip rows under
    both menus. -/
theorem screen_exact_on_flip_rows :
    ∀ m ∈ [menuBase, menuExt],
      kappaScreenMenu (.base .pair_eq) (.base .q_id) kirchhoffFlat m =
        goldMenu (.base .pair_eq) (.base .q_id) kirchhoffFlat m ∧
      kappaScreenMenu .pair23 (.base .q_id) kirchhoffFlat m =
        goldMenu .pair23 (.base .q_id) kirchhoffFlat m := by
  decide

#print axioms gold_flip_pair_eq
#print axioms menu_blind_kappa_impossible
#print axioms base_gold_consistent
#print axioms screen_exact_on_flip_rows

end MenuBlind
end StructuralIntelligence
