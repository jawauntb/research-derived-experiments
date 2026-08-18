import StructuralIntelligence.TheoryAtlas

/-!
# Structural Intelligence — Theory Atlas TA-2 (obstruction taxonomy)

Honesty.  This file banks the discrete taxonomy half of Theorem TA-2
from `papers/theory_atlas/paper.md` §3 on the registered three-chart
worlds of `experiments/theory_atlas_pair/core.py`.  We encode only the
**rank** and **support** classifiers on finite target alphabets; the
operational "missing latent" repair story (existence of a smallest
enlarged alphabet `𝒯' ⊇ 𝒯` in which transitions lift to close the
cocycle — a discrete universal-cover analogue) is **withheld** here,
as in the paper.

We reuse the TA-1 vocabulary (`CocycleHolds`, transition composition)
from `StructuralIntelligence.TheoryAtlas`, instantiated on the
registered `Fin 4` label alphabet and three pairwise edges.  No Mathlib.
No `native_decide`.  Kernel `decide` only.

**Mathematical claim card (TA-2, discrete core).**

* **Objects.**  Three chart indices `{1,2,3}`, target alphabet `𝒯 = Fin 4`,
  three registered pairwise transitions `T₁₂, T₂₃, T₁₃` as permutations
  on `𝒯`, triple-loop discrepancy
  `D := T₁₃⁻¹ ∘ T₂₃ ∘ T₁₂`, rank = moved-label count, support =
  non-identity edges.
* **Claim.**  The rank/support trichotomy (`glue` / `boundary` /
  `missingLatent`) is mutually exclusive, exhaustive, and assigns the
  correct taxon to each of the three registered witness families
  (`good`, `phase_boundary`, `bad`).
* **Withheld.**  Enlargement-existence (universal cover); rank-saturation
  on `|𝒯| = 2` (missing-latent vs category-error coincidence).
* **Check.**  General Boolean trichotomy lemmas plus kernel `decide` on
  the three named worlds.
-/

namespace StructuralIntelligence
namespace ObstructionTaxonomy

set_option maxRecDepth 4000000
set_option maxHeartbeats 16000000

/-! ## Registered chart indices and label alphabet -/

/-- The three context indices of the Theory Atlas instrument. -/
inductive Chart where
  | c1
  | c2
  | c3
deriving DecidableEq, Repr

def allCharts : List Chart := [.c1, .c2, .c3]

theorem allCharts_complete : ∀ c : Chart, c ∈ allCharts := by
  intro c; cases c <;> simp [allCharts]

abbrev Label := Fin 4

def allLabels : List Label := [0, 1, 2, 3]

theorem allLabels_complete : ∀ a : Label, a ∈ allLabels := by
  intro a
  match a with
  | 0 => simp [allLabels]
  | 1 => simp [allLabels]
  | 2 => simp [allLabels]
  | 3 => simp [allLabels]

/-! ## Permutations on `Fin 4` (registered cyclic shifts) -/

def shift1 (a : Label) : Label :=
  match a with
  | 0 => 1
  | 1 => 2
  | 2 => 3
  | 3 => 0

def shift2 (a : Label) : Label := shift1 (shift1 a)

def shift3 (a : Label) : Label := shift1 (shift1 (shift1 a))

def idLabel (a : Label) : Label := a

def compose (f g : Label → Label) (a : Label) : Label := f (g a)

/-- Pointwise inverse of a registered permutation table. -/
def inversePerm (f : Label → Label) (a : Label) : Label :=
  if f 0 == a then 0
  else if f 1 == a then 1
  else if f 2 == a then 2
  else 3

def isIdentity (f : Label → Label) : Bool :=
  (allLabels.filter (fun a => f a != a)).isEmpty

def permRank (f : Label → Label) : Nat :=
  (allLabels.filter (fun a => f a != a)).length

/-! ## Pairwise edges and transition tables -/

inductive Edge where
  | e12
  | e23
  | e13
deriving DecidableEq, Repr

def allEdges : List Edge := [.e12, .e23, .e13]

theorem allEdges_complete : ∀ e : Edge, e ∈ allEdges := by
  intro e; cases e <;> simp [allEdges]

/-- A registered three-edge chart world: three permutations on `Fin 4`. -/
structure ChartWorld where
  T12 : Label → Label
  T23 : Label → Label
  T13 : Label → Label

def transition (w : ChartWorld) : Edge → Label → Label
  | .e12 => w.T12
  | .e23 => w.T23
  | .e13 => w.T13

def edgeTransition (w : ChartWorld) (i j : Chart) (q : Label) : Label :=
  match i, j with
  | .c1, .c2 => w.T12 q
  | .c2, .c3 => w.T23 q
  | .c1, .c3 => w.T13 q
  | .c2, .c1 => inversePerm w.T12 q
  | .c3, .c2 => inversePerm w.T23 q
  | .c3, .c1 => inversePerm w.T13 q
  | _, _ => idLabel q

/-- Bridge to TA-1's `CocycleHolds` on the registered chart index type. -/
def cocycleHolds (w : ChartWorld) : Prop :=
  CocycleHolds (edgeTransition w)

/-- Triple-loop discrepancy `D = T₁₃⁻¹ ∘ T₂₃ ∘ T₁₂` on the sole
    registered triple `(c1,c2,c3)`. -/
def discrepancy (w : ChartWorld) (a : Label) : Label :=
  inversePerm w.T13 (w.T23 (w.T12 a))

def discrepancyF (w : ChartWorld) : Label → Label := discrepancy w

def discrepancyRank (w : ChartWorld) : Nat :=
  permRank (discrepancyF w)

def allRanksZero (w : ChartWorld) : Bool :=
  discrepancyRank w == 0

def someRankPos (w : ChartWorld) : Bool :=
  !allRanksZero w

def edgeNonIdentity (w : ChartWorld) (e : Edge) : Bool :=
  !isIdentity (transition w e)

def numNonIdentityEdges (w : ChartWorld) : Nat :=
  (allEdges.filter (edgeNonIdentity w ·)).length

def hasIdentityEdge (w : ChartWorld) : Bool :=
  numNonIdentityEdges w < allEdges.length

def allEdgesNonIdentity (w : ChartWorld) : Bool :=
  numNonIdentityEdges w == allEdges.length

/-! ## Taxonomy classifier -/

inductive Taxon where
  | glue
  | boundary
  | missingLatent
deriving DecidableEq, Repr

/-- Total classifier matching `experiments/theory_atlas_pair/core.py`
    `taxonomy_verdict`. -/
def classify (w : ChartWorld) : Taxon :=
  if allRanksZero w then
    .glue
  else if hasIdentityEdge w then
    .boundary
  else
    .missingLatent

/-! ## General trichotomy (decidable case analysis) -/

/-! ## General trichotomy -/

/-- The classifier output is always one of the three taxa. -/
theorem taxon_exhaustive (w : ChartWorld) :
    classify w = .glue ∨ classify w = .boundary ∨ classify w = .missingLatent := by
  rcases classify w with _ | _ | _ <;> simp

/-- The three taxa are pairwise distinct outputs of `classify`. -/
theorem taxon_mutually_exclusive (w : ChartWorld) :
    (classify w = .glue → classify w ≠ .boundary) ∧
    (classify w = .glue → classify w ≠ .missingLatent) ∧
    (classify w = .boundary → classify w ≠ .missingLatent) := by
  rcases classify w with _ | _ | _ <;> simp

/-- **TA-2 trichotomy (general).**  Exhaustiveness and mutual exclusivity
    of the three taxa; the defining rank/support conditions match
    `classify` by construction (see `classify` above).  The iff
    refinements against `allRanksZero`, `hasIdentityEdge`, and
    `allEdgesNonIdentity` are kernel-checked on each registered world
    below rather than abstractly, because `ChartWorld` carries
    arbitrary function tables. -/
theorem taxonomy_trichotomy (w : ChartWorld) :
    (classify w = .glue ∨ classify w = .boundary ∨ classify w = .missingLatent) ∧
    (classify w = .glue → classify w ≠ .boundary) ∧
    (classify w = .glue → classify w ≠ .missingLatent) ∧
    (classify w = .boundary → classify w ≠ .missingLatent) := by
  exact ⟨taxon_exhaustive w, (taxon_mutually_exclusive w).1,
    (taxon_mutually_exclusive w).2.1, (taxon_mutually_exclusive w).2.2⟩

/-! ## Registered witness worlds (names match `core.py`) -/

/-- Good charts: cocycle holds (`good_family`). -/
def goodWorld : ChartWorld where
  T12 := shift1
  T23 := shift1
  T13 := shift2

/-- Phase/boundary reference: only `T₁₂` non-identity (`phase_boundary_family`). -/
def phaseBoundaryWorld : ChartWorld where
  T12 := shift1
  T23 := idLabel
  T13 := idLabel

/-- Bad charts: cocycle fails, all edges non-identity (`bad_family`). -/
def badWorld : ChartWorld where
  T12 := shift1
  T23 := shift1
  T13 := shift3

inductive RegisteredWorld where
  | good
  | phaseBoundary
  | bad
deriving DecidableEq, Repr

def registeredWorlds : List RegisteredWorld :=
  [.good, .phaseBoundary, .bad]

def toChartWorld : RegisteredWorld → ChartWorld
  | .good => goodWorld
  | .phaseBoundary => phaseBoundaryWorld
  | .bad => badWorld

/-! ## Kernel-checked witnesses -/

theorem good_classified_glue :
    classify goodWorld = .glue := by decide

theorem phase_boundary_classified_boundary :
    classify phaseBoundaryWorld = .boundary := by decide

theorem bad_classified_missing_latent :
    classify badWorld = .missingLatent := by decide

theorem good_discrepancy_rank_zero :
    discrepancyRank goodWorld = 0 := by decide

theorem bad_discrepancy_rank_four :
    discrepancyRank badWorld = 4 := by decide

theorem phase_boundary_discrepancy_rank_four :
    discrepancyRank phaseBoundaryWorld = 4 := by decide

theorem bad_all_edges_non_identity :
    allEdgesNonIdentity badWorld := by decide

theorem phase_boundary_has_identity_edge :
    hasIdentityEdge phaseBoundaryWorld := by decide

/-! ## Headline wrapper -/

theorem ta2_taxonomy_classifies :
    (∀ rw ∈ registeredWorlds, classify (toChartWorld rw) = .glue → rw = .good) ∧
    (∀ rw ∈ registeredWorlds, classify (toChartWorld rw) = .boundary →
      rw = .phaseBoundary) ∧
    (∀ rw ∈ registeredWorlds, classify (toChartWorld rw) = .missingLatent →
      rw = .bad) ∧
    classify goodWorld = .glue ∧
    classify phaseBoundaryWorld = .boundary ∧
    classify badWorld = .missingLatent := by
  decide

#print axioms ta2_taxonomy_classifies
#print axioms taxonomy_trichotomy
#print axioms good_classified_glue
#print axioms phase_boundary_classified_boundary
#print axioms bad_classified_missing_latent

end ObstructionTaxonomy
end StructuralIntelligence
