/-!
# Structural Intelligence — Aff(1, Z/3) escapes integer Kirchhoff

Paper C (`experiments/delete_repair_connection/core.py`): cell 3 is not
idle Kirchhoff packaging.  Path-ordered holonomy in the affine group
`Aff(1, Z/3)` is not, in general, the integer Kirchhoff prediction
`sum b` that Paper A banked on `List Int`.

Honesty.  This is **not** a Lorentz theorem, **not** CG-2, **not**
continuum physics, **not** Paper 0 / `Complex.log`.  Cell 3 is real as
the discrete comparison Aff(1, Z/3) vs `List Int` Kirchhoff.  Additive
(`a = 1`) cycles remain the control: on those, holonomy equals
`(1, sum b)`.  Status: **proved-not-verified** (kernel elaboration;
SafeVerify not run).

### Mathematical claim card

* Objects.  `Edge` is a pair `(a, b)` of `Nat`, intended `a ∈ {1,2}`
  (units mod 3) and `b ∈ {0,1,2}`.  Composition is
  `(a,b) ∘ (c,d) = ((a*c) % 3, (a*d + b) % 3)`, matching Python
  `compose(after, before)`.  `pathMap` is left-fold of `compose`
  from `IDENTITY = (1,0)` (apply before, then after).
  `kirchhoffPrediction` is `(1, (sum of shifts) % 3)`.
* Claim.  `∃ edges, pathMap edges ≠ kirchhoffPrediction edges`.
* Control.  Registered additive cycles `KIRCHHOFF_FLAT` and
  `KIRCHHOFF_CURVED` match Kirchhoff.
* Discriminators.  `AFFINE_A`: `sum b ≡ 0` but holonomy `(2,0) ≠ (1,0)`.
  `AFFINE_B`: `sum b ≡ 2` but holonomy `(1,0) ≠ (1,2)`.
  `AFFINE_C` (Paper E held-out): holonomy `(1,1)`, Kirchhoff `(1,0)`.
* Assumptions.  Arithmetic is `Nat` modulo 3, not a packaged `ZMod`.
  No `Mathlib`.  No analysis.
* Kill.  The claim dies if every registered affine cycle collapses to
  Kirchhoff, or if this file is read as a relativity theorem.
* Identification.  Same objects as Paper C `core.py`; Lean does not
  import the Python.
-/

namespace StructuralIntelligence
namespace Aff13

/-- An affine edge `x ↦ a x + b` with intended `a ∈ {1,2}` and
    `b ∈ {0,1,2}`.  Representatives are reduced by `% 3` in
    `compose`. -/
structure Edge where
  a : Nat
  b : Nat
  deriving DecidableEq, Repr

/-- Modulus of the affine line, matching Python `MOD = 3`. -/
def MOD : Nat := 3

/-- Identity `x ↦ x`. -/
def IDENTITY : Edge := ⟨1, 0⟩

/-- `after ∘ before`: apply `before`, then `after`.
    Matches `compose(after, before)` in Paper C. -/
def compose (after before : Edge) : Edge :=
  ⟨(after.a * before.a) % MOD, (after.a * before.b + after.b) % MOD⟩

/-- Path-ordered holonomy: fold `compose(edge, acc)` from `IDENTITY`.
    Matches Python `path_map`. -/
def pathMap (edges : List Edge) : Edge :=
  edges.foldl (fun acc e => compose e acc) IDENTITY

/-- Integer Kirchhoff prediction: pretend the walk is additive and
    return `(1, sum b)`.  Matches Python `kirchhoff_prediction`. -/
def kirchhoffPrediction (edges : List Edge) : Edge :=
  ⟨1, edges.foldl (fun s e => (s + e.b) % MOD) 0⟩

/-- Sum of shifts modulo 3. -/
def sum_b (edges : List Edge) : Nat :=
  edges.foldl (fun s e => (s + e.b) % MOD) 0

/-- Additive inverse in `Z/3` on `Nat` representatives. -/
def negMod (n : Nat) : Nat :=
  (MOD - n % MOD) % MOD

/-- Group inverse: units in `Z/3` square to 1, so the scale inverse
    is the scale.  Matches Python `inverse`. -/
def inverse (e : Edge) : Edge :=
  ⟨e.a % MOD, (e.a * negMod e.b) % MOD⟩

/-- Kirchhoff is exactly `(1, sum_b)`. -/
theorem kirchhoffPrediction_eq_sum_b (edges : List Edge) :
    kirchhoffPrediction edges = ⟨1, sum_b edges⟩ :=
  rfl

/-! ## Registered cycles (Paper C / Paper E) -/

/-- Additive control: holonomy `(1,0)` equals Kirchhoff. -/
def KIRCHHOFF_FLAT : List Edge :=
  [⟨1, 1⟩, ⟨1, 1⟩, ⟨1, 1⟩, ⟨1, 0⟩]

/-- Additive control: holonomy `(1,1)` equals Kirchhoff. -/
def KIRCHHOFF_CURVED : List Edge :=
  [⟨1, 1⟩, ⟨1, 1⟩, ⟨1, 1⟩, ⟨1, 1⟩]

/-- `sum b ≡ 0`, holonomy `(2,0) ≠ (1,0)`.  Kirchhoff predicts flat. -/
def AFFINE_A : List Edge :=
  [⟨2, 1⟩, ⟨1, 2⟩, ⟨1, 0⟩, ⟨1, 0⟩]

/-- `sum b ≡ 2`, holonomy `(1,0) ≠ (1,2)`.  Kirchhoff predicts curved. -/
def AFFINE_B : List Edge :=
  [⟨2, 1⟩, ⟨2, 1⟩, ⟨1, 0⟩, ⟨1, 0⟩]

/-- Paper E held-out cycle: holonomy `(1,1)`, Kirchhoff `(1,0)`. -/
def AFFINE_C : List Edge :=
  [⟨1, 0⟩, ⟨1, 0⟩, ⟨2, 1⟩, ⟨2, 2⟩]

/-! ## Tiny group fragment

Concrete on the six-element group, so the kernel reduces without
`propext` from `List.Mem` unfolding. -/

theorem compose_id_left :
    compose IDENTITY ⟨1, 0⟩ = ⟨1, 0⟩ ∧
    compose IDENTITY ⟨1, 1⟩ = ⟨1, 1⟩ ∧
    compose IDENTITY ⟨1, 2⟩ = ⟨1, 2⟩ ∧
    compose IDENTITY ⟨2, 0⟩ = ⟨2, 0⟩ ∧
    compose IDENTITY ⟨2, 1⟩ = ⟨2, 1⟩ ∧
    compose IDENTITY ⟨2, 2⟩ = ⟨2, 2⟩ :=
  ⟨rfl, rfl, rfl, rfl, rfl, rfl⟩

theorem compose_id_right :
    compose ⟨1, 0⟩ IDENTITY = ⟨1, 0⟩ ∧
    compose ⟨1, 1⟩ IDENTITY = ⟨1, 1⟩ ∧
    compose ⟨1, 2⟩ IDENTITY = ⟨1, 2⟩ ∧
    compose ⟨2, 0⟩ IDENTITY = ⟨2, 0⟩ ∧
    compose ⟨2, 1⟩ IDENTITY = ⟨2, 1⟩ ∧
    compose ⟨2, 2⟩ IDENTITY = ⟨2, 2⟩ :=
  ⟨rfl, rfl, rfl, rfl, rfl, rfl⟩

theorem inverse_left :
    compose (inverse ⟨1, 0⟩) ⟨1, 0⟩ = IDENTITY ∧
    compose (inverse ⟨1, 1⟩) ⟨1, 1⟩ = IDENTITY ∧
    compose (inverse ⟨1, 2⟩) ⟨1, 2⟩ = IDENTITY ∧
    compose (inverse ⟨2, 0⟩) ⟨2, 0⟩ = IDENTITY ∧
    compose (inverse ⟨2, 1⟩) ⟨2, 1⟩ = IDENTITY ∧
    compose (inverse ⟨2, 2⟩) ⟨2, 2⟩ = IDENTITY :=
  ⟨rfl, rfl, rfl, rfl, rfl, rfl⟩

/-- Noncommutativity witness from Paper C `order_matters`. -/
theorem compose_noncomm :
    compose ⟨2, 0⟩ ⟨1, 1⟩ ≠ compose ⟨1, 1⟩ ⟨2, 0⟩ := by
  decide

/-! ## Additive control vs affine escape -/

theorem kirchhoff_flat_matches :
    pathMap KIRCHHOFF_FLAT = kirchhoffPrediction KIRCHHOFF_FLAT :=
  rfl

theorem kirchhoff_curved_matches :
    pathMap KIRCHHOFF_CURVED = kirchhoffPrediction KIRCHHOFF_CURVED :=
  rfl

theorem affine_A_escapes :
    pathMap AFFINE_A ≠ kirchhoffPrediction AFFINE_A := by
  decide

theorem affine_B_escapes :
    pathMap AFFINE_B ≠ kirchhoffPrediction AFFINE_B := by
  decide

theorem affine_C_escapes :
    pathMap AFFINE_C ≠ kirchhoffPrediction AFFINE_C := by
  decide

/-- Paper C headline: path-ordered Aff(1, Z/3) holonomy is not integer
    Kirchhoff `sum b` in general.  Witness: `AFFINE_A`. -/
theorem affine_escapes_kirchhoff :
    ∃ edges : List Edge, pathMap edges ≠ kirchhoffPrediction edges :=
  ⟨AFFINE_A, affine_A_escapes⟩

#print axioms affine_escapes_kirchhoff
#print axioms affine_A_escapes
#print axioms kirchhoff_flat_matches
#print axioms compose_noncomm
#print axioms inverse_left

end Aff13
end StructuralIntelligence
