/-!
# Structural Intelligence — κ_cheap is not a function

Paper F's cheap map is Paper E `decide` on the five-field signature
`(mixes, nFibres, nWorlds, yHasNontrivialSymmetry, connectionMismatch)`.
On the registered Paper F suite that signature collides: the same
cheap 5-tuple is shared by rows whose empirical golds differ
(`quotient` vs `noop`).  Therefore κ_cheap is not a function from
cheap signatures to golds.

Honesty.  This is not a new master object.  Possibility 1 as a
*new cheap function* is dead on this finite harness.  Gold is
menu-relative representability (Paper E `gold_of`), not `decide`.
The signature is not refit: the collision is the theorem.  Path A/B
and `CommonSuffScreen` are not re-proved here.  No `Mathlib`, no
`Complex.log`, no analysis.

### Mathematical claim card

* Objects.  `World` is `{0,1}^4` (`|X| = 16`).  Screens are the
  disclosed menu `{q_id, q_rot, q_perm, q_stab0, q_stab_last}`.
  Tasks are `yBag`, `yLastBit`, `yParity`, `yPairEq`.  `Signature`
  is Paper E's five-field cheap diagnostic.  `Gold` is
  `{restore, quotient, transport, noop, broken}`.
* Claim.  `∃ s : Signature, ∃ g1 g2 : Gold, g1 ≠ g2` and two
  registered KIRCHHOFF_FLAT rows (the Paper F collision bucket)
  realise `(s, g1)` and `(s, g2)`.
* Quantifiers.  Finite: four named rows, all on `q_id`, all with
  `connectionMismatch = false`.
* Assumptions.  Gold looks at the disclosed menu.  Nontrivial
  symmetry is existence of a non-identity `S_4` permutation
  preserving `Y`.  Action: `(g · x)_i = x[perm i]`.
* Identification.  `kappaCheap` is Paper E `decide`, not a new rule.
* Edge / null.  Kill this file if the signature is enlarged or
  otherwise "fixed" so the collision disappears.
* Executable check.  `lake lean StructuralIntelligence/KappaCheap.lean`;
  `#print axioms kappa_cheap_not_function` empty or standard.
-/

namespace StructuralIntelligence
namespace KappaCheap

/-! ## 1. Worlds `{0,1}^4` -/

/-- A 4-bit world.  `X = {0,1}^4`, `|X| = 16`. -/
structure World where
  b0 : Bool
  b1 : Bool
  b2 : Bool
  b3 : Bool
deriving BEq, DecidableEq

/-- Kernel-computable list-bind.  Prelude `List.flatMap` / `.bind` is
    `noncomputable` on Lean 4.31, so it does not reduce under `decide`. -/
def listBind {α β} (as : List α) (f : α → List β) : List β :=
  as.foldl (fun acc a => acc ++ f a) []

/-- Enumerate `X` by binding `[false, true]` on each bit. -/
def allWorlds : List World :=
  listBind [false, true] fun b0 =>
  listBind [false, true] fun b1 =>
  listBind [false, true] fun b2 =>
  [false, true].map fun b3 =>
    ⟨b0, b1, b2, b3⟩

def World.bit (x : World) (i : Fin 4) : Bool :=
  match i.val with
  | 0 => x.b0
  | 1 => x.b1
  | 2 => x.b2
  | _ => x.b3

def World.toNat (x : World) : Nat :=
  (if x.b0 then 8 else 0) + (if x.b1 then 4 else 0) +
  (if x.b2 then 2 else 0) + (if x.b3 then 1 else 0)

def World.le (x y : World) : Bool := decide (x.toNat ≤ y.toNat)

def World.min (x y : World) : World := if x.le y then x else y

def World.rotate (x : World) : World := ⟨x.b1, x.b2, x.b3, x.b0⟩

def boolToNat (b : Bool) : Nat := if b then 1 else 0

/-- First-occurrence nub.  Kernel-reduces; used for fibre counting. -/
def nub {α} [BEq α] (xs : List α) : List α :=
  xs.foldl (fun acc x => if acc.any (fun y => y == x) then acc else acc ++ [x]) []

/-! ## 2. `S_4` action `(g · x)_i = x[perm i]` -/

/-- A 4-tuple of indices in `Fin 4`.  The registered list `allPerms`
    is exactly `S_4` (the 24 bijections). -/
structure Perm where
  p0 : Fin 4
  p1 : Fin 4
  p2 : Fin 4
  p3 : Fin 4
deriving BEq, DecidableEq

/-- `(g · x)_i = x[perm i]`. -/
def applyPerm (p : Perm) (x : World) : World where
  b0 := x.bit p.p0
  b1 := x.bit p.p1
  b2 := x.bit p.p2
  b3 := x.bit p.p3

def idPerm : Perm := ⟨0, 1, 2, 3⟩

/-- All 24 permutations of `{0,1,2,3}`. -/
def allPerms : List Perm :=
  [ ⟨0, 1, 2, 3⟩, ⟨0, 1, 3, 2⟩, ⟨0, 2, 1, 3⟩, ⟨0, 2, 3, 1⟩, ⟨0, 3, 1, 2⟩, ⟨0, 3, 2, 1⟩
  , ⟨1, 0, 2, 3⟩, ⟨1, 0, 3, 2⟩, ⟨1, 2, 0, 3⟩, ⟨1, 2, 3, 0⟩, ⟨1, 3, 0, 2⟩, ⟨1, 3, 2, 0⟩
  , ⟨2, 0, 1, 3⟩, ⟨2, 0, 3, 1⟩, ⟨2, 1, 0, 3⟩, ⟨2, 1, 3, 0⟩, ⟨2, 3, 0, 1⟩, ⟨2, 3, 1, 0⟩
  , ⟨3, 0, 1, 2⟩, ⟨3, 0, 2, 1⟩, ⟨3, 1, 0, 2⟩, ⟨3, 1, 2, 0⟩, ⟨3, 2, 0, 1⟩, ⟨3, 2, 1, 0⟩ ]

/-! ## 3. Screens (Paper A / E menu) -/

/-- Identity screen. -/
def qId (x : World) : World := x

/-- Lex-least rotation of `(b0,b1,b2,b3)`. -/
def qRot (x : World) : World :=
  x.min (x.rotate.min (x.rotate.rotate.min x.rotate.rotate.rotate))

/-- Bits sorted, `false` before `true` (same fibres as popcount). -/
def qPerm (x : World) : World :=
  match boolToNat x.b0 + boolToNat x.b1 + boolToNat x.b2 + boolToNat x.b3 with
  | 0 => ⟨false, false, false, false⟩
  | 1 => ⟨false, false, false, true⟩
  | 2 => ⟨false, false, true, true⟩
  | 3 => ⟨false, true, true, true⟩
  | _ => ⟨true, true, true, true⟩

/-- Keep `b0`; sort `(b1,b2,b3)`. -/
def qStab0 (x : World) : World :=
  match boolToNat x.b1 + boolToNat x.b2 + boolToNat x.b3 with
  | 0 => ⟨x.b0, false, false, false⟩
  | 1 => ⟨x.b0, false, false, true⟩
  | 2 => ⟨x.b0, false, true, true⟩
  | _ => ⟨x.b0, true, true, true⟩

/-- Sort `(b0,b1,b2)`; keep `b3`. -/
def qStabLast (x : World) : World :=
  match boolToNat x.b0 + boolToNat x.b1 + boolToNat x.b2 with
  | 0 => ⟨false, false, false, x.b3⟩
  | 1 => ⟨false, false, true, x.b3⟩
  | 2 => ⟨false, true, true, x.b3⟩
  | _ => ⟨true, true, true, x.b3⟩

/-- Disclosed Paper E/F menu. -/
def menu : List (World → World) := [qId, qRot, qPerm, qStab0, qStabLast]

/-! ## 4. Tasks -/

/-- Popcount. -/
def yBag (x : World) : Nat :=
  boolToNat x.b0 + boolToNat x.b1 + boolToNat x.b2 + boolToNat x.b3

/-- Last bit. -/
def yLastBit (x : World) : Nat := boolToNat x.b3

/-- Parity (xor of all four bits / popcount mod 2). -/
def yParity (x : World) : Nat := yBag x % 2

/-- Pair equality `b0 == b1`. -/
def yPairEq (x : World) : Nat := boolToNat (x.b0 == x.b1)

/-! ## 5. Representability, fibres, symmetry -/

/-- `Y` factors through `q` (constant on `q`-fibres). -/
def Represents (q : World → World) (y : World → Nat) : Prop :=
  ∀ x x' : World, q x = q x' → y x = y x'

/-- Computational form of `Represents`, quantified over `allWorlds`. -/
def represents (q : World → World) (y : World → Nat) : Bool :=
  allWorlds.all fun x =>
    allWorlds.all fun x' =>
      !(q x == q x') || (y x == y x')

/-- Number of distinct `q`-images on `allWorlds`. -/
def fiberCount (q : World → World) : Nat :=
  (nub (allWorlds.map q)).length

/-- `Y` is invariant under a non-identity permutation of positions.
    `allPerms.contains p` is the kernel-decidable form of `p ∈ S_4`. -/
def HasNontrivialSymmetry (y : World → Nat) : Prop :=
  ∃ p : Perm, allPerms.contains p = true ∧ p ≠ idPerm ∧ ∀ x : World, y (applyPerm p x) = y x

def preserves (y : World → Nat) (p : Perm) : Bool :=
  allWorlds.all fun x => y (applyPerm p x) == y x

def hasNontrivialSymmetry (y : World → Nat) : Bool :=
  allPerms.any fun p => !(p == idPerm) && preserves y p

/-- The identity screen represents every task. -/
theorem represents_qId (y : World → Nat) : Represents qId y := by
  intro x x' h
  cases h
  rfl

/-! ## 6. Cheap signature and κ_cheap (Paper E `decide`; not refit) -/

/-- Paper E `Signature`.  Five fields, no names, no menu. -/
structure Signature where
  mixes : Bool
  nFibres : Nat
  nWorlds : Nat
  yHasNontrivialSymmetry : Bool
  connectionMismatch : Bool
deriving BEq, DecidableEq

/-- Empirical gold: which menu action repairs.  Not `decide`. -/
inductive Gold where
  | restore
  | quotient
  | transport
  | noop
  | broken
deriving BEq, DecidableEq

/-- Cheap diagnostic of `(q, Y, edges)`.  KIRCHHOFF_FLAT rows pass
    `connectionMismatch = false`. -/
def signatureOf (q : World → World) (y : World → Nat) (connectionMismatch : Bool) :
    Signature where
  mixes := !(represents q y)
  nFibres := fiberCount q
  nWorlds := allWorlds.length
  yHasNontrivialSymmetry := hasNontrivialSymmetry y
  connectionMismatch := connectionMismatch

/-- Paper E `decide` / κ_cheap.  Do not refit. -/
def kappaCheap (s : Signature) : Gold :=
  if s.connectionMismatch then .transport
  else if s.mixes then .restore
  else if s.yHasNontrivialSymmetry && decide (s.nFibres = s.nWorlds) then .quotient
  else .noop

/-- Paper E `gold_of`: Kirchhoff mismatch → transport; else restore if
    `q` mixes and a finer representing menu screen exists; else quotient
    if a coarser representing menu screen exists; else noop. -/
def goldOf (q : World → World) (y : World → Nat) (connectionMismatch : Bool) : Gold :=
  if connectionMismatch then
    .transport
  else if !(represents q y) then
    if menu.any fun r => decide (fiberCount q < fiberCount r) && represents r y then
      .restore
    else
      .broken
  else if menu.any fun r => decide (fiberCount r < fiberCount q) && represents r y then
    .quotient
  else
    .noop

/-! ## 7. Registered Paper F collision-bucket rows

All four are `q_id` on KIRCHHOFF_FLAT edges (`connectionMismatch = false`).
-/

inductive RegisteredCollision where
  | bag_q_id
  | last_bit_q_id
  | parity_q_id
  | pair_eq_q_id
deriving BEq, DecidableEq

def RegisteredCollision.q : RegisteredCollision → (World → World)
  | _ => qId

def RegisteredCollision.y : RegisteredCollision → (World → Nat)
  | .bag_q_id => yBag
  | .last_bit_q_id => yLastBit
  | .parity_q_id => yParity
  | .pair_eq_q_id => yPairEq

def RegisteredCollision.signature (r : RegisteredCollision) : Signature :=
  signatureOf r.q r.y false

def RegisteredCollision.gold (r : RegisteredCollision) : Gold :=
  goldOf r.q r.y false

/-- The cheap 5-tuple shared by the collision bucket. -/
def collisionSignature : Signature :=
  { mixes := false
    nFibres := 16
    nWorlds := 16
    yHasNontrivialSymmetry := true
    connectionMismatch := false }

/-! ## 8. Explicit nontrivial-symmetry witnesses -/

theorem bag_has_nontrivial_symmetry : HasNontrivialSymmetry yBag := by
  refine ⟨⟨1, 0, 2, 3⟩, by decide, by decide, ?_⟩
  intro x
  simp [yBag, applyPerm, World.bit, boolToNat]
  ac_rfl

theorem last_bit_has_nontrivial_symmetry : HasNontrivialSymmetry yLastBit := by
  refine ⟨⟨1, 0, 2, 3⟩, by decide, by decide, ?_⟩
  intro x
  rcases x with ⟨b0, b1, b2, b3⟩
  cases b0 <;> cases b1 <;> cases b2 <;> cases b3 <;> rfl

theorem parity_has_nontrivial_symmetry : HasNontrivialSymmetry yParity := by
  refine ⟨⟨1, 0, 2, 3⟩, by decide, by decide, ?_⟩
  intro x
  simp [yParity, yBag, applyPerm, World.bit, boolToNat]
  ac_rfl

/-- `pair_eq` is invariant under swapping positions 2↔3.  That unused
    `S_4`-symmetry is not leftover privilege: gold on `q_id` is `noop`. -/
theorem pair_eq_has_nontrivial_symmetry : HasNontrivialSymmetry yPairEq := by
  refine ⟨⟨0, 1, 3, 2⟩, by decide, by decide, ?_⟩
  intro x
  rcases x with ⟨b0, b1, b2, b3⟩
  cases b0 <;> cases b1 <;> cases b2 <;> cases b3 <;> rfl

/-! ## 9. Finite facts (kernel `decide`; no `native_decide`) -/

set_option maxHeartbeats 2000000

theorem allWorlds_length : allWorlds.length = 16 := rfl

theorem bag_q_id_signature :
    signatureOf qId yBag false = collisionSignature := by
  decide

theorem last_bit_q_id_signature :
    signatureOf qId yLastBit false = collisionSignature := by
  decide

theorem parity_q_id_signature :
    signatureOf qId yParity false = collisionSignature := by
  decide

theorem pair_eq_q_id_signature :
    signatureOf qId yPairEq false = collisionSignature := by
  decide

theorem bag_q_id_row_signature :
    RegisteredCollision.bag_q_id.signature = collisionSignature :=
  bag_q_id_signature

theorem last_bit_q_id_row_signature :
    RegisteredCollision.last_bit_q_id.signature = collisionSignature :=
  last_bit_q_id_signature

theorem parity_q_id_row_signature :
    RegisteredCollision.parity_q_id.signature = collisionSignature :=
  parity_q_id_signature

theorem pair_eq_q_id_row_signature :
    RegisteredCollision.pair_eq_q_id.signature = collisionSignature :=
  pair_eq_q_id_signature

/-- The four named rows share the registered collision signature. -/
theorem collision_rows_share_signature :
    RegisteredCollision.bag_q_id.signature = collisionSignature ∧
    RegisteredCollision.last_bit_q_id.signature = collisionSignature ∧
    RegisteredCollision.parity_q_id.signature = collisionSignature ∧
    RegisteredCollision.pair_eq_q_id.signature = collisionSignature :=
  ⟨bag_q_id_row_signature, last_bit_q_id_row_signature,
    parity_q_id_row_signature, pair_eq_q_id_row_signature⟩

theorem bag_q_id_gold : goldOf qId yBag false = .quotient := by
  decide

theorem last_bit_q_id_gold : goldOf qId yLastBit false = .quotient := by
  decide

theorem parity_q_id_gold : goldOf qId yParity false = .quotient := by
  decide

theorem pair_eq_q_id_gold : goldOf qId yPairEq false = .noop := by
  decide

theorem bag_q_id_row_gold : RegisteredCollision.bag_q_id.gold = .quotient :=
  bag_q_id_gold

theorem last_bit_q_id_row_gold : RegisteredCollision.last_bit_q_id.gold = .quotient :=
  last_bit_q_id_gold

theorem parity_q_id_row_gold : RegisteredCollision.parity_q_id.gold = .quotient :=
  parity_q_id_gold

theorem pair_eq_q_id_row_gold : RegisteredCollision.pair_eq_q_id.gold = .noop :=
  pair_eq_q_id_gold

theorem gold_quotient_ne_noop : Gold.quotient ≠ Gold.noop := fun h => nomatch h

/-- Paper E `decide` sends the collision signature to `quotient`.
    That matches bag / last_bit / parity golds and misses `pair_eq`. -/
theorem kappaCheap_collisionSignature :
    kappaCheap collisionSignature = Gold.quotient := rfl

/-! ## 10. Headline: κ_cheap is not a function on the registered suite -/

/-- On the registered Paper F suite, κ_cheap is not a function from
    cheap 5-field signatures to golds: the same signature is realised
    by two golds (`quotient` on `bag_q_id`, `noop` on `pair_eq_q_id`). -/
theorem kappa_cheap_not_function :
    ∃ s : Signature, ∃ g1 g2 : Gold,
      g1 ≠ g2 ∧
      (∃ r : RegisteredCollision, r.signature = s ∧ r.gold = g1) ∧
      (∃ r : RegisteredCollision, r.signature = s ∧ r.gold = g2) := by
  refine ⟨collisionSignature, Gold.quotient, Gold.noop, gold_quotient_ne_noop, ?_, ?_⟩
  · exact ⟨.bag_q_id, bag_q_id_row_signature, bag_q_id_row_gold⟩
  · exact ⟨.pair_eq_q_id, pair_eq_q_id_row_signature, pair_eq_q_id_row_gold⟩

#print axioms kappa_cheap_not_function

end KappaCheap
end StructuralIntelligence
