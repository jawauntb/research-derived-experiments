/-!
# Structural Intelligence — the dial at zero (Wave 6)

Theorem B's D = 0 clause from "Intention Is All You Need" (§9), the
ledger row marked "Lean pending", now kernel-checked in the finite
discrete setting the essay actually uses.

Setting.  A finite world (a list of realizations) and a task law
`taskLaw : X → L` — the conditional task distribution each
realization induces, abstracted to any type with decidable equality
(the essay's `x ↦ P(Y|x)`).  An encoder is a family of cells.  Zero
task-distortion means every cell is law-constant: with the distortion
measured against the task, zero expected divergence forces every
realization in a cell to share one conditional task law.  That
identification of "zero distortion" with cell-constancy is the
essay's own two-line argument, taken as the definition here and
disclosed as such.

Results.

* `levelCells_zero_distortion` — the level-set partition of the task
  law has zero task-distortion.  (General.)
* `zero_distortion_cell_in_level` — any zero-distortion encoder's
  cell sits inside a single level set: the level-set partition is
  refined by every zero-distortion encoder.  (General.)
* `no_coarser_on_witness` — on the registered four-point, three-law
  world, every two-cell partition fails zero distortion, and the
  level partition has exactly three cells: no coarser encoder
  qualifies.  (Kernel enumeration of all seven two-cell splits.)

What is *not* claimed: anything about the rate–distortion curve away
from D = 0 (the "cells coarsen with the budget" reading is withdrawn
per review item 2 — the safe claim is that the optimal rate falls,
and the nestedness question is an instrument, not a theorem).  No
Mathlib.  No `native_decide`.
-/

namespace StructuralIntelligence
namespace DialZero

/-- A cell is law-constant when all its members share one task law. -/
def CellConstant (taskLaw : X → L) (cell : List X) : Prop :=
  ∀ x ∈ cell, ∀ y ∈ cell, taskLaw x = taskLaw y

/-- Zero task-distortion encoder: every cell is law-constant. -/
def ZeroDistortion (taskLaw : X → L) (cells : List (List X)) : Prop :=
  ∀ cell ∈ cells, CellConstant taskLaw cell

/-- The level set of a law value. -/
def levelCell [DecidableEq L] (taskLaw : X → L) (worlds : List X)
    (l : L) : List X :=
  worlds.filter fun x => decide (taskLaw x = l)

/-- **The level-set partition has zero task-distortion.**  (General:
    two members of a level cell share the law by construction.) -/
theorem levelCells_zero_distortion [DecidableEq L]
    (taskLaw : X → L) (worlds : List X) (l : L) :
    CellConstant taskLaw (levelCell taskLaw worlds l) := by
  intro x hx y hy
  have hx' := (List.mem_filter.mp hx).2
  have hy' := (List.mem_filter.mp hy).2
  have hxl : taskLaw x = l := of_decide_eq_true hx'
  have hyl : taskLaw y = l := of_decide_eq_true hy'
  rw [hxl, hyl]

/-- **Every zero-distortion cell sits inside one level set.**  Any
    encoder with zero task-distortion refines the level-set
    partition: for any member `x` of a cell, the whole cell lies in
    `x`'s level set.  (General.) -/
theorem zero_distortion_cell_in_level [DecidableEq L]
    (taskLaw : X → L) (worlds : List X) (cells : List (List X))
    (hzero : ZeroDistortion taskLaw cells)
    (hcover : ∀ cell ∈ cells, ∀ x ∈ cell, x ∈ worlds) :
    ∀ cell ∈ cells, ∀ x ∈ cell, ∀ y ∈ cell,
      y ∈ levelCell taskLaw worlds (taskLaw x) := by
  intro cell hcell x hx y hy
  apply List.mem_filter.mpr
  constructor
  · exact hcover cell hcell y hy
  · have := hzero cell hcell y hy x hx
    exact decide_eq_true this

/-! ## Registered witness: no coarser encoder qualifies -/

inductive W4 where
  | w0
  | w1
  | w2
  | w3
deriving DecidableEq, Repr

def worlds4 : List W4 := [.w0, .w1, .w2, .w3]

/-- Three law classes on four worlds: {w0, w1} share a law; w2 and w3
    each have their own. -/
def law4 : W4 → Nat
  | .w0 => 0
  | .w1 => 0
  | .w2 => 1
  | .w3 => 2

def cellConstantB (cell : List W4) : Bool :=
  cell.all fun x => cell.all fun y => decide (law4 x = law4 y)

def zeroDistortionB (cells : List (List W4)) : Bool :=
  cells.all cellConstantB

/-- All seven two-cell partitions of the four-point world. -/
def twoCellPartitions : List (List (List W4)) :=
  [ [[.w0], [.w1, .w2, .w3]]
  , [[.w1], [.w0, .w2, .w3]]
  , [[.w2], [.w0, .w1, .w3]]
  , [[.w3], [.w0, .w1, .w2]]
  , [[.w0, .w1], [.w2, .w3]]
  , [[.w0, .w2], [.w1, .w3]]
  , [[.w0, .w3], [.w1, .w2]] ]

/-- The three-cell level partition. -/
def levelPartition : List (List W4) :=
  [levelCell law4 worlds4 0, levelCell law4 worlds4 1,
    levelCell law4 worlds4 2]

/-- **D = 0 pins the level sets and nothing coarser.**  On the
    registered world: the level partition has zero distortion with
    exactly three cells, and every two-cell partition fails zero
    distortion. -/
theorem no_coarser_on_witness :
    (zeroDistortionB levelPartition = true) ∧
    (levelPartition.length = 3) ∧
    (twoCellPartitions.all
      (fun cells => !(zeroDistortionB cells)) = true) := by
  decide

#print axioms levelCells_zero_distortion
#print axioms zero_distortion_cell_in_level
#print axioms no_coarser_on_witness

end DialZero
end StructuralIntelligence
