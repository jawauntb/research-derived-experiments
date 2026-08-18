/-!
# Structural Intelligence — Door 2: the generator border (Wave 5)

Honesty.  This file banks the door-2 headlines of
`experiments/delete_repair_reduction/` and
`experiments/delete_repair_generators/`: two generator episodes
(the banked `sq` squaring macro and the new `cube` macro), each an
exhaustive enumeration, each showing the same shape — the *access*
observables (min formula size, fibre mass at the bound) change with
the generator set while the (q, K)-side observables are grammar-free.

In this formalization the grammar-independence of the (q, K) data is
**definitional**: there is one tree type and one denotation/size/depth
function; only the enumerated universe depends on the `withMac` flag.
The banked content is therefore (a) the base universe embeds in the
extended one, (b) the registered min sizes and masses land exactly
(matching US-2/US-3: formula `2^(n+1)−1` vs tower `n+1` at `n = 2`,
and `2k−1` vs `2` for the cube episode), and (c) the access
observables differ between the two universes — the two-point
separation that makes min size not a function of the shared data.

No imports.  No Mathlib.  No `native_decide`.  Kernel `decide` only.
-/

namespace StructuralIntelligence
namespace GeneratorBorder

/-- Expression trees over `{x, ×}` plus one unary macro symbol. -/
inductive GTree where
  | x
  | mul (a b : GTree)
  | mac (a : GTree)
deriving DecidableEq, Repr

/-- Node count. -/
def size : GTree → Nat
  | .x => 1
  | .mul a b => 1 + size a + size b
  | .mac a => 1 + size a

/-- Exponent semantics: `x ↦ 1`, `mul ↦ +`, `mac ↦ (· * m)` where `m`
    is the macro's registered multiplier (2 for `sq`, 3 for `cube`). -/
def den (m : Nat) : GTree → Nat
  | .x => 1
  | .mul a b => den m a + den m b
  | .mac a => m * den m a

/-- All trees of size ≤ `n`; `withMac` toggles the macro generator.
    Sizes are built in order, so `gen withMac n` extends
    `gen withMac (n−1)`. -/
def gen (withMac : Bool) : Nat → List GTree
  | 0 => []
  | n + 1 =>
    let smaller := gen withMac n
    let leaf := if n + 1 = 1 then [GTree.x] else []
    let macs :=
      if withMac then
        (smaller.filter (fun t => size t = n)).map GTree.mac
      else []
    let muls :=
      smaller.flatMap fun a =>
        (smaller.filter (fun b => size a + size b = n)).map
          (GTree.mul a)
    smaller ++ leaf ++ macs ++ muls

def baseTrees (n : Nat) : List GTree := gen false n

def extTrees (n : Nat) : List GTree := gen true n

/-- Min size of a tree denoting the target, `999` if none (targets are
    inhabited by the census theorems below). -/
def minSizeFor (l : List GTree) (m target : Nat) : Nat :=
  ((l.filter (fun t => den m t = target)).map size).foldl Nat.min 999

/-- Fibre mass at the bound: how many enumerated trees denote the
    target. -/
def massFor (l : List GTree) (m target : Nat) : Nat :=
  (l.filter (fun t => den m t = target)).length

set_option maxRecDepth 100000
set_option maxHeartbeats 4000000

/-! ## Universes -/

theorem base7_count : (baseTrees 7).length = 9 := by decide

theorem ext7_count : (extTrees 7).length = 89 := by decide

theorem base5_count : (baseTrees 5).length = 4 := by decide

theorem ext5_count : (extTrees 5).length = 17 := by decide

/-- The shared universe embeds: every base tree is an extended tree. -/
theorem base_subset_ext7 : ∀ t ∈ baseTrees 7, t ∈ extTrees 7 := by
  decide

theorem base_subset_ext5 : ∀ t ∈ baseTrees 5, t ∈ extTrees 5 := by
  decide

/-! ## Episode `sq` (multiplier 2, target x⁴, bound 7) — the banked
    US-2/US-3 numbers -/

theorem sq_min_base : minSizeFor (baseTrees 7) 2 4 = 7 := by decide

theorem sq_min_ext : minSizeFor (extTrees 7) 2 4 = 3 := by decide

theorem sq_mass_base : massFor (baseTrees 7) 2 4 = 5 := by decide

theorem sq_mass_ext : massFor (extTrees 7) 2 4 = 14 := by decide

/-! ## Episode `cube` (multiplier 3, target x³, bound 5) — the door-2b
    consolidation numbers -/

theorem cube_min_base : minSizeFor (baseTrees 5) 3 3 = 5 := by decide

theorem cube_min_ext : minSizeFor (extTrees 5) 3 3 = 2 := by decide

theorem cube_mass_base : massFor (baseTrees 5) 3 3 = 2 := by decide

theorem cube_mass_ext : massFor (extTrees 5) 3 3 = 3 := by decide

/-! ## Headlines: the access separation -/

/-- **Door 2.**  Min formula size for x⁴ differs between the two
    universes although denotation, size, and depth are one and the
    same functions of the tree.  The episode moves the generator set,
    not (q, K). -/
theorem generator_border_sq :
    minSizeFor (baseTrees 7) 2 4 ≠ minSizeFor (extTrees 7) 2 4 := by
  decide

/-- **Door 2b.**  The border replicates on the cube macro. -/
theorem generator_border_cube :
    minSizeFor (baseTrees 5) 3 3 ≠ minSizeFor (extTrees 5) 3 3 := by
  decide

/-- Two-point form: no function of the shared universe alone can
    return the min size of both universes on the sq episode. -/
theorem min_size_not_shared_function :
    ∀ f : List GTree → Nat,
      ¬ (f (baseTrees 7) = minSizeFor (baseTrees 7) 2 4 ∧
         f (baseTrees 7) = minSizeFor (extTrees 7) 2 4) := by
  intro f h
  have h1 := h.1
  have h2 := h.2
  rw [sq_min_base] at h1
  rw [sq_min_ext] at h2
  exact absurd (h1.symm.trans h2) (by decide)

#print axioms base_subset_ext7
#print axioms sq_min_base
#print axioms generator_border_sq
#print axioms min_size_not_shared_function

end GeneratorBorder
end StructuralIntelligence
