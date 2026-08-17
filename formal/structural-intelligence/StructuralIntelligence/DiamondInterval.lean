/-!
# Structural Intelligence — Paper D diamond interval (existential core)

Two explicit integer-grid embeddings of the same causal diamond poset with
different interval values `s²(e1, e2)`.  The poset does not determine the
interval.

Registered Paper D witnesses (results JSON; this file does **not** enumerate
the 196 diamond embeddings).  The Python census found four `s²` values
`{-1, -3, -4, -8}`; we use the two extremes as a discriminating pair.

* `wMinus1`: `e0=(0,0)`, `e1=(1,0)`, `e2=(1,1)`, `e3=(2,0)`, `s²(e1,e2)=-1`
* `wMinus8`: `e0=(0,1)`, `e1=(1,0)`, `e2=(2,3)`, `e3=(3,2)`, `s²(e1,e2)=-8`

Honesty.  This is a finite integer-grid fact.  It is **not** Lorentz physics,
**not** a functor unifying Lorentz / Lamport / positional encodings, and
**not** a Possibility 6 revival.  Possibility 6 stays dead: a shared cartoon
is not a shared theorem.

Everything here is pure Lean 4 core (no `Mathlib`).  No `sorry`.  No
`Complex.log`.  Path A/B and `CommonSuffScreen` are not re-proved.

### Mathematical claim card

* Objects.  `Point := { t, x : Int }`; `Embedding` a labeled 4-tuple
  `(e0,e1,e2,e3)`; `interval src dst := dt^2 - dx^2` with `dt = dst.t - src.t`,
  `dx = dst.x - src.x`; `IsCausal src dst := dt > 0 ∧ interval src dst ≥ 0`.
* Poset.  The set of index pairs `(i,j)` with `i ≠ j`, `i,j < 4`, and
  `IsCausal (event i) (event j)`.
* Diamond.  `{(0,1),(0,2),(0,3),(1,3),(2,3)}` — `e1` incomparable to `e2`.
* Claim.  `∃` two embeddings with the same poset (the diamond) and
  `interval e1 e2` different.
* Quantifiers.  Existential over two explicit witnesses; universal over
  index pairs `i, j : Nat` for poset equality.
* Assumptions.  Integer subtraction; the causal predicate above.  No
  continuum, no Lorentz group, no boosts.
* Kill.  If every diamond embedding had the same `s²(e1,e2)`, the poset
  would determine the interval on this harness.  The two witnesses kill that.
* Edge / null.  `e1, e2` are incomparable both ways on each witness
  (`dt = 0` on `wMinus1`; spacelike `s² = -8` on `wMinus8`).
-/

namespace StructuralIntelligence
namespace DiamondInterval

/-- Integer grid event `(t, x)`.  Differences are `Int` subtraction. -/
structure Point where
  t : Int
  x : Int
deriving DecidableEq

/-- Minkowski-style interval `s² = dt² - dx²` on the integer grid. -/
def interval (src dst : Point) : Int :=
  let dt := dst.t - src.t
  let dx := dst.x - src.x
  dt * dt - dx * dx

/-- Computational causal test: strictly later in `t`, and not spacelike. -/
def causalB (src dst : Point) : Bool :=
  decide (dst.t - src.t > (0 : Int)) && decide (interval src dst ≥ (0 : Int))

/-- Causal if the destination is strictly later in `t` and not spacelike. -/
def IsCausal (src dst : Point) : Prop :=
  causalB src dst = true

/-- Neither direction is causal. -/
def Incomparable (src dst : Point) : Prop :=
  causalB src dst = false ∧ causalB dst src = false

/-- Labeled 4-tuple `(e0, e1, e2, e3)` on the integer grid. -/
structure Embedding where
  e0 : Point
  e1 : Point
  e2 : Point
  e3 : Point

/-- Event lookup by index.  Dummy on `i ≥ 4` (poset membership requires `i < 4`). -/
def Embedding.event (w : Embedding) : Nat → Point
  | 0 => w.e0
  | 1 => w.e1
  | 2 => w.e2
  | 3 => w.e3
  | _ => w.e0

/-- Computational poset membership on labeled indices. -/
def inPosetB (w : Embedding) (i j : Nat) : Bool :=
  decide (i < 4) && decide (j < 4) && decide (i ≠ j) && causalB (w.event i) (w.event j)

/-- Causal pairs among the four labeled events. -/
def InPoset (w : Embedding) (i j : Nat) : Prop :=
  inPosetB w i j = true

/-- The diamond cartoon as a Boolean relation on indices. -/
def diamondB : Nat → Nat → Bool
  | 0, 1 | 0, 2 | 0, 3 | 1, 3 | 2, 3 => true
  | _, _ => false

/-- Prop wrapper: `(i,j)` is a diamond edge. -/
def Diamond (i j : Nat) : Prop :=
  diamondB i j = true

/-- Off-diagonal index pairs, row-major on `{0,1,2,3}`. -/
def offDiagPairs : List (Nat × Nat) :=
  [(0,1),(0,2),(0,3),(1,0),(1,2),(1,3),(2,0),(2,1),(2,3),(3,0),(3,1),(3,2)]

/-- Causal pairs of an embedding, as a list (Python `poset_of`). -/
def posetPairs (w : Embedding) : List (Nat × Nat) :=
  offDiagPairs.filter fun p => causalB (w.event p.1) (w.event p.2)

/-- `DIAMOND = {(0,1),(0,2),(0,3),(1,3),(2,3)}`. -/
def diamondPairs : List (Nat × Nat) :=
  [(0,1),(0,2),(0,3),(1,3),(2,3)]

/-! ## Registered witnesses -/

/-- Paper D witness with `s²(e1,e2) = -1`. -/
def wMinus1 : Embedding where
  e0 := ⟨0, 0⟩
  e1 := ⟨1, 0⟩
  e2 := ⟨1, 1⟩
  e3 := ⟨2, 0⟩

/-- Paper D witness with `s²(e1,e2) = -8`. -/
def wMinus8 : Embedding where
  e0 := ⟨0, 1⟩
  e1 := ⟨1, 0⟩
  e2 := ⟨2, 3⟩
  e3 := ⟨3, 2⟩

/-! ## Interval values -/

theorem interval_wMinus1 : interval wMinus1.e1 wMinus1.e2 = -1 := rfl
theorem interval_wMinus8 : interval wMinus8.e1 wMinus8.e2 = -8 := rfl

theorem interval_ne :
    interval wMinus1.e1 wMinus1.e2 ≠ interval wMinus8.e1 wMinus8.e2 := by
  decide

/-! ## Incomparability of `{e1, e2}` -/

theorem wMinus1_incomparable : Incomparable wMinus1.e1 wMinus1.e2 := ⟨rfl, rfl⟩
theorem wMinus8_incomparable : Incomparable wMinus8.e1 wMinus8.e2 := ⟨rfl, rfl⟩

/-! ## Poset of each witness is the diamond -/

/-- Split a `Nat → Nat → Bool` identity at 4.  Overflow identities are
    hypotheses so the helper itself never unfolds `f`/`g`. -/
private theorem eq_bool2_nat4 (f g : Nat → Nat → Bool)
    (h00 : f 0 0 = g 0 0) (h01 : f 0 1 = g 0 1) (h02 : f 0 2 = g 0 2) (h03 : f 0 3 = g 0 3)
    (h10 : f 1 0 = g 1 0) (h11 : f 1 1 = g 1 1) (h12 : f 1 2 = g 1 2) (h13 : f 1 3 = g 1 3)
    (h20 : f 2 0 = g 2 0) (h21 : f 2 1 = g 2 1) (h22 : f 2 2 = g 2 2) (h23 : f 2 3 = g 2 3)
    (h30 : f 3 0 = g 3 0) (h31 : f 3 1 = g 3 1) (h32 : f 3 2 = g 3 2) (h33 : f 3 3 = g 3 3)
    (hGeI : ∀ n m, f (n + 4) m = g (n + 4) m)
    (hGeJ0 : ∀ m, f 0 (m + 4) = g 0 (m + 4))
    (hGeJ1 : ∀ m, f 1 (m + 4) = g 1 (m + 4))
    (hGeJ2 : ∀ m, f 2 (m + 4) = g 2 (m + 4))
    (hGeJ3 : ∀ m, f 3 (m + 4) = g 3 (m + 4)) :
    ∀ i j, f i j = g i j := by
  intro i j
  cases i with
  | zero =>
    cases j with
    | zero => exact h00
    | succ j =>
      cases j with
      | zero => exact h01
      | succ j =>
        cases j with
        | zero => exact h02
        | succ j =>
          cases j with
          | zero => exact h03
          | succ m => exact hGeJ0 m
  | succ i =>
    cases i with
    | zero =>
      cases j with
      | zero => exact h10
      | succ j =>
        cases j with
        | zero => exact h11
        | succ j =>
          cases j with
          | zero => exact h12
          | succ j =>
            cases j with
            | zero => exact h13
            | succ m => exact hGeJ1 m
    | succ i =>
      cases i with
      | zero =>
        cases j with
        | zero => exact h20
        | succ j =>
          cases j with
          | zero => exact h21
          | succ j =>
            cases j with
            | zero => exact h22
            | succ j =>
              cases j with
              | zero => exact h23
              | succ m => exact hGeJ2 m
      | succ i =>
        cases i with
        | zero =>
          cases j with
          | zero => exact h30
          | succ j =>
            cases j with
            | zero => exact h31
            | succ j =>
              cases j with
              | zero => exact h32
              | succ j =>
                cases j with
                | zero => exact h33
                | succ m => exact hGeJ3 m
        | succ n =>
          exact hGeI n j

private theorem inPosetB_eq_diamondB_wMinus1 :
    ∀ i j, inPosetB wMinus1 i j = diamondB i j :=
  eq_bool2_nat4 (inPosetB wMinus1) diamondB
    rfl rfl rfl rfl
    rfl rfl rfl rfl
    rfl rfl rfl rfl
    rfl rfl rfl rfl
    (fun _ _ => rfl)
    (fun _ => rfl) (fun _ => rfl) (fun _ => rfl) (fun _ => rfl)

private theorem inPosetB_eq_diamondB_wMinus8 :
    ∀ i j, inPosetB wMinus8 i j = diamondB i j :=
  eq_bool2_nat4 (inPosetB wMinus8) diamondB
    rfl rfl rfl rfl
    rfl rfl rfl rfl
    rfl rfl rfl rfl
    rfl rfl rfl rfl
    (fun _ _ => rfl)
    (fun _ => rfl) (fun _ => rfl) (fun _ => rfl) (fun _ => rfl)

/-- `poset(wMinus1) = DIAMOND` as a relation on indices. -/
theorem poset_wMinus1 (i j : Nat) : InPoset wMinus1 i j ↔ Diamond i j := by
  unfold InPoset Diamond
  rw [inPosetB_eq_diamondB_wMinus1]

/-- `poset(wMinus8) = DIAMOND` as a relation on indices. -/
theorem poset_wMinus8 (i j : Nat) : InPoset wMinus8 i j ↔ Diamond i j := by
  unfold InPoset Diamond
  rw [inPosetB_eq_diamondB_wMinus8]

/-- Computational certificate: the filtered pair-list is exactly `DIAMOND`. -/
theorem posetPairs_wMinus1 : posetPairs wMinus1 = diamondPairs := rfl

/-- Computational certificate: the filtered pair-list is exactly `DIAMOND`. -/
theorem posetPairs_wMinus8 : posetPairs wMinus8 = diamondPairs := rfl

theorem poset_eq (i j : Nat) : InPoset wMinus1 i j ↔ InPoset wMinus8 i j :=
  Iff.trans (poset_wMinus1 i j) (poset_wMinus8 i j).symm

/-! ## Headline -/

/-- **The poset does not determine the interval.**  There exist two
    integer-grid embeddings of the same causal diamond with different
    `s²(e1,e2)`.  Not continuum physics.  Not a functor. -/
theorem poset_not_determine_interval :
    ∃ w₁ w₂ : Embedding,
      (∀ i j, InPoset w₁ i j ↔ InPoset w₂ i j) ∧
      (∀ i j, InPoset w₁ i j ↔ Diamond i j) ∧
      posetPairs w₁ = diamondPairs ∧
      posetPairs w₂ = diamondPairs ∧
      interval w₁.e1 w₁.e2 ≠ interval w₂.e1 w₂.e2 ∧
      Incomparable w₁.e1 w₁.e2 ∧
      Incomparable w₂.e1 w₂.e2 :=
  ⟨wMinus1, wMinus8,
    poset_eq, poset_wMinus1,
    posetPairs_wMinus1, posetPairs_wMinus8,
    interval_ne, wMinus1_incomparable, wMinus8_incomparable⟩

#print axioms poset_not_determine_interval
#print axioms poset_wMinus1
#print axioms poset_wMinus8
#print axioms posetPairs_wMinus1
#print axioms posetPairs_wMinus8
#print axioms interval_ne

end DiamondInterval
end StructuralIntelligence
