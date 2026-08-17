/-!
# Structural Intelligence — Paper E surgery miss (`pair_eq` / `q_id`)

Paper E asked whether the three-cell taxonomy is a *one-shot name-blind
agent rule*: a cheap 5-field signature that picks a repair without
trying the disclosed menu.  It is not.  Verdict `surgery_killed`.

This file kernel-checks the held-out grain miss.  On `(pair_eq, q_id,
KIRCHHOFF_FLAT)` the cheap rule returns `quotient` and empirical gold
is `noop`.  Unused symmetry is not leftover privilege: `pair_eq` has a
non-identity symmetry and the identity screen still represents it, so
the miss is not "the identity left a privileged coordinate that a
coarser menu screen already names."

Honesty.

* Objects are the registered Paper E harness: `X = {0,1}^4`, menu
  `{q_id, q_rot, q_perm, q_stab0, q_stab_last}`, task `pair_eq`.
* The cheap signature stays five fields.  No sixth field is added to
  erase the miss.  The rule is not refit.
* Gold is menu-relative representability (and Kirchhoff mismatch), not
  a cell name.
* `kirchhoffFlat` is the registered mismatch flag `false` for
  `KIRCHHOFF_FLAT`.  This file does not re-prove Aff(1, Z/3) or Path A/B.
* No `Mathlib`.  No `Complex.log`.  No new scientific letter.

### Mathematical claim card

* Objects.  `World` = 4 `Bool`s; `allWorlds` has 16 elements;
  screens `q_id, q_rot, q_perm, q_stab0, q_stab_last`; task `pair_eq`;
  `Signature` with fields
  `(mixes, nFibres, nWorlds, yHasNontrivialSymmetry, connectionMismatch)`;
  actions `{restore, quotient, transport, noop, broken}`.
* Claim.  `decide (signature pair_eq q_id kirchhoffFlat) = quotient`
  and `goldOf pair_eq q_id kirchhoffFlat = noop`.
* Assumptions.  Gold searches the disclosed five-screen menu.  Symmetry
  is `S_4` acting by permuting bit positions.  `kirchhoffFlat` has no
  connection mismatch.
* Kill.  The formalization dies if the cheap rule is changed so the
  miss disappears, or if a sixth signature field is invented.
-/

namespace StructuralIntelligence
namespace SurgeryMiss

/-! ## 1. Worlds `{0,1}^4` -/

/-- A world is four bits.  `false` is `0`, `true` is `1`. -/
structure World where
  b0 : Bool
  b1 : Bool
  b2 : Bool
  b3 : Bool
deriving DecidableEq, Repr, Inhabited

instance : BEq World where
  beq a b := decide (a = b)

/-- Lexicographic `{0,1}^4`, matching Python `itertools.product((0,1), repeat=4)`. -/
def allWorlds : List World :=
  [ ⟨false, false, false, false⟩
  , ⟨false, false, false, true⟩
  , ⟨false, false, true,  false⟩
  , ⟨false, false, true,  true⟩
  , ⟨false, true,  false, false⟩
  , ⟨false, true,  false, true⟩
  , ⟨false, true,  true,  false⟩
  , ⟨false, true,  true,  true⟩
  , ⟨true,  false, false, false⟩
  , ⟨true,  false, false, true⟩
  , ⟨true,  false, true,  false⟩
  , ⟨true,  false, true,  true⟩
  , ⟨true,  true,  false, false⟩
  , ⟨true,  true,  false, true⟩
  , ⟨true,  true,  true,  false⟩
  , ⟨true,  true,  true,  true⟩
  ]

theorem allWorlds_length : allWorlds.length = 16 := rfl

theorem mem_allWorlds (x : World) : x ∈ allWorlds := by
  cases x with
  | mk a b c d =>
    cases a <;> cases b <;> cases c <;> cases d <;> decide

/-! ## 2. Bit permutations (`S_4` on positions) -/

/-- Source-index 4-tuple.  `(g·x)_i = x[perm[i]]`, as in Paper A/E Python. -/
structure Perm where
  p0 : Nat
  p1 : Nat
  p2 : Nat
  p3 : Nat
deriving DecidableEq, Repr

def Perm.identity : Perm := ⟨0, 1, 2, 3⟩

/-- Read bit `i` of a world.  Indices other than `0,1,2` return bit 3. -/
def World.bit (x : World) : Nat → Bool
  | 0 => x.b0
  | 1 => x.b1
  | 2 => x.b2
  | _ => x.b3

def Perm.apply (p : Perm) (x : World) : World :=
  ⟨x.bit p.p0, x.bit p.p1, x.bit p.p2, x.bit p.p3⟩

/-- `S_4` as `permutations(range(4))`, lexicographic. -/
def allPerms : List Perm :=
  [ ⟨0, 1, 2, 3⟩, ⟨0, 1, 3, 2⟩, ⟨0, 2, 1, 3⟩, ⟨0, 2, 3, 1⟩, ⟨0, 3, 1, 2⟩, ⟨0, 3, 2, 1⟩
  , ⟨1, 0, 2, 3⟩, ⟨1, 0, 3, 2⟩, ⟨1, 2, 0, 3⟩, ⟨1, 2, 3, 0⟩, ⟨1, 3, 0, 2⟩, ⟨1, 3, 2, 0⟩
  , ⟨2, 0, 1, 3⟩, ⟨2, 0, 3, 1⟩, ⟨2, 1, 0, 3⟩, ⟨2, 1, 3, 0⟩, ⟨2, 3, 0, 1⟩, ⟨2, 3, 1, 0⟩
  , ⟨3, 0, 1, 2⟩, ⟨3, 0, 2, 1⟩, ⟨3, 1, 0, 2⟩, ⟨3, 1, 2, 0⟩, ⟨3, 2, 0, 1⟩, ⟨3, 2, 1, 0⟩
  ]

/-- Swap bits 2↔3.  Preserves `pair_eq` (which only reads bits 0,1). -/
def swap23 : Perm := ⟨0, 1, 3, 2⟩

theorem swap23_mem : swap23 ∈ allPerms := by decide

theorem swap23_ne_identity : swap23 ≠ Perm.identity := by decide

/-! ## 3. Screens (disclosed menu) -/

/-- Identity screen.  16 singleton fibres. -/
def q_id (x : World) : World := x

/-- Lexicographic bit-order as a `Nat` (b0 most significant). -/
def World.toNat (x : World) : Nat :=
  (if x.b0 then 8 else 0) + (if x.b1 then 4 else 0) +
    (if x.b2 then 2 else 0) + (if x.b3 then 1 else 0)

def World.lexLt (x y : World) : Bool :=
  decide (x.toNat < y.toNat)

def World.rotateLeft (x : World) : World :=
  ⟨x.b1, x.b2, x.b3, x.b0⟩

def rotations (x : World) : List World :=
  let r1 := x.rotateLeft
  let r2 := r1.rotateLeft
  let r3 := r2.rotateLeft
  [x, r1, r2, r3]

def lexMin (xs : List World) (fallback : World) : World :=
  match xs with
  | [] => fallback
  | x :: rest => rest.foldl (fun a b => if b.lexLt a then b else a) x

/-- Lex-least rotation. -/
def q_rot (x : World) : World :=
  lexMin (rotations x) x

/-- Sorted tuple (bit histogram / popcount canonical). -/
def q_perm (x : World) : World :=
  let n :=
    (if x.b0 then 1 else 0) + (if x.b1 then 1 else 0) +
      (if x.b2 then 1 else 0) + (if x.b3 then 1 else 0)
  match n with
  | 0 => ⟨false, false, false, false⟩
  | 1 => ⟨false, false, false, true⟩
  | 2 => ⟨false, false, true,  true⟩
  | 3 => ⟨false, true,  true,  true⟩
  | _ => ⟨true,  true,  true,  true⟩

def sort3 (a b c : Bool) : Bool × Bool × Bool :=
  let n := (if a then 1 else 0) + (if b then 1 else 0) + (if c then 1 else 0)
  match n with
  | 0 => (false, false, false)
  | 1 => (false, false, true)
  | 2 => (false, true,  true)
  | _ => (true,  true,  true)

/-- Keep bit 0; sort the suffix. -/
def q_stab0 (x : World) : World :=
  let s := sort3 x.b1 x.b2 x.b3
  ⟨x.b0, s.1, s.2.1, s.2.2⟩

/-- Keep the last bit; sort the prefix. Dual of `q_stab0`. -/
def q_stab_last (x : World) : World :=
  let s := sort3 x.b0 x.b1 x.b2
  ⟨s.1, s.2.1, s.2.2, x.b3⟩

/-- Disclosed menu.  Gold is relative to this list, not to all maps `X → X`. -/
def menu : List (World → World) :=
  [q_id, q_rot, q_perm, q_stab0, q_stab_last]

/-! ## 4. Task `pair_eq` -/

/-- `yPairEq x = (b0 == b1)`. -/
def pair_eq (x : World) : Bool :=
  x.b0 == x.b1

theorem swap23_preserves_pair_eq (x : World) :
    pair_eq (swap23.apply x) = pair_eq x := rfl

/-! ## 5. Cheap 5-field signature (not refit) -/

inductive Action where
  | restore
  | quotient
  | transport
  | noop
  | broken
deriving DecidableEq, Repr

/-- Paper E `Signature`.  Five fields.  No sixth. -/
structure Signature where
  mixes : Bool
  nFibres : Nat
  nWorlds : Nat
  yHasNontrivialSymmetry : Bool
  connectionMismatch : Bool
deriving DecidableEq, Repr

/-- `Y` mixes on `q` iff some `q`-fibre is not `Y`-constant. -/
def mixes (y : World → Bool) (q : World → World) : Bool :=
  allWorlds.any fun x =>
    allWorlds.any fun x' => (q x == q x') && (y x != y x')

/-- Deduplicate, preserving first occurrence.  `foldl` avoids a
    `filter`-recursive termination argument. -/
def unique [DecidableEq α] (xs : List α) : List α :=
  xs.foldl (fun acc x => if x ∈ acc then acc else acc ++ [x]) []

def nFibres (q : World → World) : Nat :=
  (unique (allWorlds.map q)).length

/-- Nontrivial `S_4` symmetry of `Y`, matching Python `has_nontrivial_symmetry`. -/
def hasNontrivialSymmetry (y : World → Bool) : Bool :=
  allPerms.any fun p =>
    !decide (p = Perm.identity) &&
      allWorlds.all fun x => y (p.apply x) == y x

/-- Registered `KIRCHHOFF_FLAT` mismatch flag.  Path map equals the
    integer Kirchhoff prediction; this file does not re-open Paper C. -/
def kirchhoffFlat : Bool := false

def signature (y : World → Bool) (q : World → World) (mismatch : Bool) : Signature where
  mixes := mixes y q
  nFibres := nFibres q
  nWorlds := allWorlds.length
  yHasNontrivialSymmetry := hasNontrivialSymmetry y
  connectionMismatch := mismatch

/-- Empirical gold: which menu action repairs.
    `¬mixes` is checked first so a mixing screen does not force a
    fibre-count reduction; the predicate is Paper E `gold_of`. -/
def goldOf (y : World → Bool) (q : World → World) (mismatch : Bool) : Action :=
  if mismatch then
    .transport
  else if mixes y q then
    if menu.any fun q' => !(mixes y q') && Nat.blt (nFibres q) (nFibres q') then
      .restore
    else
      .broken
  else if menu.any fun q' => !(mixes y q') && Nat.blt (nFibres q') (nFibres q) then
    .quotient
  else
    .noop

/-- Pre-registered one-shot rule.  No names.  No menu search.
    Defined after `goldOf` so that file does not shadow prelude `decide`
    in the gold predicate. -/
def decide (s : Signature) : Action :=
  if s.connectionMismatch then
    .transport
  else if s.mixes then
    .restore
  else if s.yHasNontrivialSymmetry && (s.nFibres == s.nWorlds) then
    .quotient
  else
    .noop

/-! ## 6. Finite evaluations on the registered pair -/

/-- Mixing witnesses (same fibres, different `pair_eq`):
    `q_perm` / `q_stab0` / `q_stab_last` mix `(0,0,1,1)` with `(0,1,0,1)`;
    `q_rot` mixes `(0,0,1,1)` with `(1,0,0,1)`. -/
def w0011 : World := ⟨false, false, true, true⟩
def w0101 : World := ⟨false, true, false, true⟩
def w1001 : World := ⟨true, false, false, true⟩

theorem q_perm_mixes_pair : q_perm w0011 = q_perm w0101 ∧ pair_eq w0011 ≠ pair_eq w0101 := by
  decide

theorem q_stab0_mixes_pair : q_stab0 w0011 = q_stab0 w0101 ∧ pair_eq w0011 ≠ pair_eq w0101 := by
  decide

theorem q_stab_last_mixes_pair :
    q_stab_last w0011 = q_stab_last w0101 ∧ pair_eq w0011 ≠ pair_eq w0101 := by
  decide

theorem q_rot_mixes_pair : q_rot w0011 = q_rot w1001 ∧ pair_eq w0011 ≠ pair_eq w1001 := by
  decide

@[simp] theorem mixes_pair_eq_q_id : mixes pair_eq q_id = false := by decide
@[simp] theorem mixes_pair_eq_q_rot : mixes pair_eq q_rot = true := by decide
@[simp] theorem mixes_pair_eq_q_perm : mixes pair_eq q_perm = true := by decide
@[simp] theorem mixes_pair_eq_q_stab0 : mixes pair_eq q_stab0 = true := by decide
@[simp] theorem mixes_pair_eq_q_stab_last : mixes pair_eq q_stab_last = true := by decide

@[simp] theorem nFibres_q_id : nFibres q_id = 16 := by decide

@[simp] theorem hasNontrivialSymmetry_pair_eq :
    hasNontrivialSymmetry pair_eq = true := by decide

@[simp] theorem pair_eq_q_id_signature :
    signature pair_eq q_id kirchhoffFlat =
      { mixes := false
        nFibres := 16
        nWorlds := 16
        yHasNontrivialSymmetry := true
        connectionMismatch := false } := by
  simp [signature, kirchhoffFlat, allWorlds_length]

theorem nat_blt_16_16 : Nat.blt 16 16 = false := rfl

theorem menu_any_unfold
    (p : (World → World) → Bool) :
    menu.any p =
      (p q_id || (p q_rot || (p q_perm || (p q_stab0 || (p q_stab_last || false))))) := rfl

theorem menu_any_coarser_representing_pair_eq_q_id :
    (menu.any fun q' =>
        !(mixes pair_eq q') && Nat.blt (nFibres q') (nFibres q_id)) = false := by
  rw [menu_any_unfold]
  simp [nFibres_q_id, nat_blt_16_16]

/-! ## 7. Headlines -/

/-- `pair_eq` has unused symmetry, and `q_id` still represents it.
    Leftover privilege would be a coarser *representing* menu screen;
    that is gold `quotient`, which this pair is not.  The cheap rule
    nevertheless says `quotient` because it treats symmetry plus a
    singleton fibre count as a license to quotient. -/
theorem unused_symmetry_not_privilege :
    (∃ p : Perm, p ≠ Perm.identity ∧ ∀ x, pair_eq (p.apply x) = pair_eq x) ∧
    (∀ x x' : World, q_id x = q_id x' → pair_eq x = pair_eq x') := by
  constructor
  · refine ⟨swap23, swap23_ne_identity, ?_⟩
    intro x
    exact swap23_preserves_pair_eq x
  · intro x x' h
    simp [q_id] at h
    exact congrArg pair_eq h

/-- Held-out Paper E miss.  Cheap name-blind `decide` returns `quotient`;
    menu-relative gold is `noop`.  Taxonomy is not a one-shot agent rule. -/
theorem goldOf_pair_eq_q_id :
    goldOf pair_eq q_id kirchhoffFlat = .noop := by
  -- Do not `simp` `List.any`: that rewrites to `∀ q ∈ menu`, which
  -- quantifies over function equality.  Unfold `if false` by `rfl`.
  have hdef :
      goldOf pair_eq q_id kirchhoffFlat =
        (if kirchhoffFlat then Action.transport
         else if mixes pair_eq q_id then
           (if menu.any (fun q' =>
                 !(mixes pair_eq q') && Nat.blt (nFibres q_id) (nFibres q'))
            then Action.restore else Action.broken)
         else if menu.any (fun q' =>
               !(mixes pair_eq q') && Nat.blt (nFibres q') (nFibres q_id))
           then Action.quotient
           else Action.noop) := rfl
  rw [hdef, kirchhoffFlat, mixes_pair_eq_q_id]
  change
    (if menu.any (fun q' =>
          !(mixes pair_eq q') && Nat.blt (nFibres q') (nFibres q_id))
      then Action.quotient else Action.noop) = Action.noop
  rw [menu_any_coarser_representing_pair_eq_q_id]
  simp

theorem decide_pair_eq_q_id :
    decide (signature pair_eq q_id kirchhoffFlat) = .quotient := by
  rw [pair_eq_q_id_signature]
  unfold decide
  rfl

theorem surgery_miss_pair_eq :
    decide (signature pair_eq q_id kirchhoffFlat) = .quotient ∧
    goldOf pair_eq q_id kirchhoffFlat = .noop :=
  And.intro decide_pair_eq_q_id goldOf_pair_eq_q_id

end SurgeryMiss
end StructuralIntelligence

#print axioms StructuralIntelligence.SurgeryMiss.surgery_miss_pair_eq
#print axioms StructuralIntelligence.SurgeryMiss.unused_symmetry_not_privilege
