import StructuralIntelligence.CommonSuffScreen

/-!
# Structural Intelligence — κ_screen (Paper F, registered suite)

Honesty.  `κ_screen` is **not** a new master object.  It is Theorem 4
(`IsCommonSuffScreen` / `commonSuffScreen_refines` in
`StructuralIntelligence.CommonSuffScreen`) evaluated on the disclosed
five-screen menu, plus one named total order: fewest fibres, then
lexicographic screen id.  That order is the *only* extra datum beyond
Theorem 4.  We cite `IsCommonSuffScreen` as the meaning of
“`Y` is constant on `q`-fibres”.  We do **not** re-prove
`commonSuffScreen_refines` or `commonSuffScreen_coarsest`.  We do not
re-prove Path A/B.  We do not touch `Complex.log`.  No Mathlib.

Paper F rule, in this order:

1. Path-ordered `Aff(1, ℤ/3)` holonomy ≠ Kirchhoff `(1, ∑ b)` (mod 3)
   → action `transport`, no screen.
2. Else `r*` = unique coarsest representing menu screen
   (fewest fibres, then `min` on the string id).
   If none → `broken` (must not happen on the suite).
3. If current `q` does not represent `Y` → `restore`.
4. Else if `fiberCount r* < fiberCount q` → `quotient`.
5. Else → `noop`.

Lexicographic ids (Python `min(tied)` on names):
`q_id < q_perm < q_rot < q_stab0 < q_stab_last`.

Status: **verified** after replacing `native_decide` with kernel `decide`
(high `maxRecDepth`).  No `sorry`.  No Mathlib.
-/

namespace StructuralIntelligence
namespace KappaScreen

/-! ## Worlds `{0,1}⁴` -/

/-- A 4-bit world.  `false` is bit `0`, `true` is bit `1`. -/
structure World where
  b0 : Bool
  b1 : Bool
  b2 : Bool
  b3 : Bool
deriving DecidableEq, Repr

def W (b0 b1 b2 b3 : Bool) : World := { b0, b1, b2, b3 }

/-- Lexicographic enumeration matching Python `product((0,1), repeat=4)`. -/
def allWorlds : List World :=
  [ W false false false false, W false false false true
  , W false false true  false, W false false true  true
  , W false true  false false, W false true  false true
  , W false true  true  false, W false true  true  true
  , W true  false false false, W true  false false true
  , W true  false true  false, W true  false true  true
  , W true  true  false false, W true  true  false true
  , W true  true  true  false, W true  true  true  true ]

theorem allWorlds_length : allWorlds.length = 16 := rfl

/-! ## Menu screens and tasks -/

/-- Disclosed menu.  Constructor order is *not* the name order. -/
inductive ScreenId where
  | q_id
  | q_perm
  | q_rot
  | q_stab0
  | q_stab_last
deriving DecidableEq, Repr

/-- Python `min` on the string ids `q_id`, `q_perm`, `q_rot`, `q_stab0`, `q_stab_last`. -/
def ScreenId.nameRank : ScreenId → Nat
  | .q_id => 0
  | .q_perm => 1
  | .q_rot => 2
  | .q_stab0 => 3
  | .q_stab_last => 4

theorem nameRank_is_lex_id :
    ScreenId.q_id.nameRank < ScreenId.q_perm.nameRank ∧
    ScreenId.q_perm.nameRank < ScreenId.q_rot.nameRank ∧
    ScreenId.q_rot.nameRank < ScreenId.q_stab0.nameRank ∧
    ScreenId.q_stab0.nameRank < ScreenId.q_stab_last.nameRank := by
  decide

inductive TaskId where
  | bag
  | first_bit
  | last_bit
  | identity
  | parity
  | pair_eq
deriving DecidableEq, Repr

inductive Action where
  | restore
  | quotient
  | transport
  | noop
  | broken
deriving DecidableEq, Repr

inductive TaskValue where
  | bit : Bool → TaskValue
  | count : Nat → TaskValue
  | world : World → TaskValue
deriving DecidableEq, Repr

/-! ## Screen functions (Paper A / E Python) -/

def ble (x y : Bool) : Bool := !x || y

def insertSorted (x : Bool) : List Bool → List Bool
  | [] => [x]
  | y :: ys => if ble x y then x :: y :: ys else y :: insertSorted x ys

def sortBools : List Bool → List Bool
  | [] => []
  | x :: xs => insertSorted x (sortBools xs)

def pack4 : List Bool → World
  | [a, b, c, d] => W a b c d
  | _ => W false false false false

def rotateLeft (w : World) : World :=
  W w.b1 w.b2 w.b3 w.b0

/-- Lex order on worlds: `false < true`, then `b0`, `b1`, `b2`, `b3`. -/
def lexLt (x y : World) : Bool :=
  if x.b0 != y.b0 then !x.b0 && y.b0
  else if x.b1 != y.b1 then !x.b1 && y.b1
  else if x.b2 != y.b2 then !x.b2 && y.b2
  else !x.b3 && y.b3

def minWorld (x y : World) : World :=
  if lexLt y x then y else x

/-- `q_rot` = lex-least rotation (Python `orbit_canonical` for `ℤ/4`). -/
def qRot (w : World) : World :=
  let r0 := w
  let r1 := rotateLeft r0
  let r2 := rotateLeft r1
  let r3 := rotateLeft r2
  minWorld (minWorld r0 r1) (minWorld r2 r3)

def qPerm (w : World) : World :=
  pack4 (sortBools [w.b0, w.b1, w.b2, w.b3])

def qStab0 (w : World) : World :=
  match sortBools [w.b1, w.b2, w.b3] with
  | [a, b, c] => W w.b0 a b c
  | _ => w

def qStabLast (w : World) : World :=
  match sortBools [w.b0, w.b1, w.b2] with
  | [a, b, c] => W a b c w.b3
  | _ => w

def evalScreen : ScreenId → World → World
  | .q_id, w => w
  | .q_perm, w => qPerm w
  | .q_rot, w => qRot w
  | .q_stab0, w => qStab0 w
  | .q_stab_last, w => qStabLast w

def popcount (w : World) : Nat :=
  (if w.b0 then 1 else 0) +
  (if w.b1 then 1 else 0) +
  (if w.b2 then 1 else 0) +
  (if w.b3 then 1 else 0)

def evalTask : TaskId → World → TaskValue
  | .bag, w => .count (popcount w)
  | .first_bit, w => .bit w.b0
  | .last_bit, w => .bit w.b3
  | .identity, w => .world w
  | .parity, w => .bit (decide (popcount w % 2 = 1))
  | .pair_eq, w => .bit (decide (w.b0 = w.b1))

/-! ## Representability = CSS fibre-constancy (cited, not re-proved) -/

/-- Computational form: `Y` is constant on `q`-fibres.  This is the
    singleton-family reading of `IsCommonSuffScreen`. -/
def represents (t : TaskId) (s : ScreenId) : Bool :=
  allWorlds.all fun x =>
    allWorlds.all fun x' =>
      !(decide (evalScreen s x = evalScreen s x')) ||
        decide (evalTask t x = evalTask t x')

/-- **Citation, not a new proof of Theorem 4.**  A common-sufficient
    screen is fibre-constant.  This is exactly
    `commonSuffScreen_refines` on a singleton task family. -/
theorem represents_of_isCommonSuffScreen
    (t : TaskId) (s : ScreenId)
    (h : IsCommonSuffScreen (fun _ : Unit => evalTask t) (evalScreen s))
    {x x' : World} (hq : evalScreen s x = evalScreen s x') :
    evalTask t x = evalTask t x' :=
  commonSuffScreen_refines h hq ()

def uniqueCount {α : Type} [DecidableEq α] : List α → Nat
  | [] => 0
  | x :: xs => uniqueCount xs + if decide (x ∈ xs) then 0 else 1

def fiberCount (s : ScreenId) : Nat :=
  uniqueCount (allWorlds.map (evalScreen s))

def menu : List ScreenId :=
  [.q_id, .q_rot, .q_perm, .q_stab0, .q_stab_last]

/-- Named total order: fewer fibres, then lexicographic id. -/
def screenLt (s1 s2 : ScreenId) : Bool :=
  let n1 := fiberCount s1
  let n2 := fiberCount s2
  (n1 < n2) || (n1 == n2 && s1.nameRank < s2.nameRank)

def minScreen (s1 s2 : ScreenId) : ScreenId :=
  if screenLt s1 s2 then s1 else s2

/-- Coarsest representing menu screen.  Specified before the run. -/
def coarsestRepresenting (t : TaskId) : Option ScreenId :=
  match menu.filter (fun s => represents t s) with
  | [] => none
  | s :: ss => some (ss.foldl minScreen s)

/-! ## Aff(1, ℤ/3) holonomy vs Kirchhoff -/

structure Aff where
  scale : Nat
  shift : Nat
deriving DecidableEq, Repr

def aff (scale shift : Nat) : Aff := { scale, shift }

def affId : Aff := aff 1 0

/-- `(a,b) ∘ (c,d) = (a c, a d + b)` (mod 3). -/
def affCompose (after before : Aff) : Aff where
  scale := (after.scale * before.scale) % 3
  shift := (after.scale * before.shift + after.shift) % 3

/-- Left-fold compose, starting at `(1,0)`.  Apply edges in list order. -/
def pathMap (edges : List Aff) : Aff :=
  edges.foldl (fun acc e => affCompose e acc) affId

def kirchhoffPrediction (edges : List Aff) : Aff :=
  aff 1 ((edges.foldl (fun s e => s + e.shift) 0) % 3)

def kirchhoffMismatch (edges : List Aff) : Bool :=
  decide (pathMap edges ≠ kirchhoffPrediction edges)

def kirchhoffFlat : List Aff := [aff 1 1, aff 1 1, aff 1 1, aff 1 0]
def affineA : List Aff := [aff 2 1, aff 1 2, aff 1 0, aff 1 0]
def affineC : List Aff := [aff 1 0, aff 1 0, aff 2 1, aff 2 2]

theorem kirchhoffFlat_matches :
    kirchhoffMismatch kirchhoffFlat = false := rfl

theorem affineA_mismatch :
    kirchhoffMismatch affineA = true := rfl

theorem affineC_holonomy :
    pathMap affineC = aff 1 1 := rfl

theorem affineC_kirchhoff :
    kirchhoffPrediction affineC = aff 1 0 := rfl

theorem affineC_mismatch :
    kirchhoffMismatch affineC = true := rfl

/-! ## κ_screen and empirical gold -/

structure Choice where
  action : Action
  chosen : Option ScreenId
deriving DecidableEq, Repr

/-- Written function.  Menu-relative.  Theorem 4 plus a total order. -/
def kappaScreen (t : TaskId) (q : ScreenId) (edges : List Aff) : Choice :=
  if kirchhoffMismatch edges then
    { action := .transport, chosen := none }
  else
    match coarsestRepresenting t with
    | none => { action := .broken, chosen := none }
    | some rStar =>
      if !represents t q then
        { action := .restore, chosen := some rStar }
      else if fiberCount rStar < fiberCount q then
        { action := .quotient, chosen := some rStar }
      else
        { action := .noop, chosen := some rStar }

/-- Paper E `gold_of`: mismatch → transport; else restore if `q` mixes
    and some finer representing menu screen exists; quotient if `q`
    represents and some coarser representing exists; else noop. -/
def gold (t : TaskId) (q : ScreenId) (edges : List Aff) : Action :=
  if kirchhoffMismatch edges then
    .transport
  else if !represents t q then
    if menu.any (fun r => represents t r && fiberCount q < fiberCount r) then
      .restore
    else
      .broken
  else if menu.any (fun r => represents t r && fiberCount r < fiberCount q) then
    .quotient
  else
    .noop

/-! ## Registered 11-row suite -/

structure RegisteredRow where
  caseId : String
  task : TaskId
  screen : ScreenId
  edges : List Aff
  expectedAction : Action
  expectedChosen : Option ScreenId
deriving DecidableEq, Repr

def suite : List RegisteredRow :=
  [ { caseId := "first_bit_q_perm", task := .first_bit, screen := .q_perm,
      edges := kirchhoffFlat, expectedAction := .restore,
      expectedChosen := some .q_stab0 }
  , { caseId := "bag_q_id", task := .bag, screen := .q_id,
      edges := kirchhoffFlat, expectedAction := .quotient,
      expectedChosen := some .q_perm }
  , { caseId := "bag_q_perm", task := .bag, screen := .q_perm,
      edges := kirchhoffFlat, expectedAction := .noop,
      expectedChosen := some .q_perm }
  , { caseId := "bag_q_perm_affine_a", task := .bag, screen := .q_perm,
      edges := affineA, expectedAction := .transport,
      expectedChosen := none }
  , { caseId := "last_bit_q_perm", task := .last_bit, screen := .q_perm,
      edges := kirchhoffFlat, expectedAction := .restore,
      expectedChosen := some .q_stab_last }
  , { caseId := "last_bit_q_id", task := .last_bit, screen := .q_id,
      edges := kirchhoffFlat, expectedAction := .quotient,
      expectedChosen := some .q_stab_last }
  , { caseId := "parity_q_id", task := .parity, screen := .q_id,
      edges := kirchhoffFlat, expectedAction := .quotient,
      expectedChosen := some .q_perm }
  , { caseId := "identity_q_id", task := .identity, screen := .q_id,
      edges := kirchhoffFlat, expectedAction := .noop,
      expectedChosen := some .q_id }
  , { caseId := "pair_eq_q_perm", task := .pair_eq, screen := .q_perm,
      edges := kirchhoffFlat, expectedAction := .restore,
      expectedChosen := some .q_id }
  , { caseId := "pair_eq_q_id", task := .pair_eq, screen := .q_id,
      edges := kirchhoffFlat, expectedAction := .noop,
      expectedChosen := some .q_id }
  , { caseId := "bag_q_perm_affine_c", task := .bag, screen := .q_perm,
      edges := affineC, expectedAction := .transport,
      expectedChosen := none } ]

theorem suite_length : suite.length = 11 := rfl

set_option maxRecDepth 100000
set_option maxHeartbeats 400000

/-! ## Fibre-count lemmas (kernel-friendly stepping stones) -/

theorem fiberCount_q_id : fiberCount .q_id = 16 := by decide
theorem fiberCount_q_perm : fiberCount .q_perm = 5 := by decide
theorem fiberCount_q_rot : fiberCount .q_rot = 6 := by decide
theorem fiberCount_q_stab0 : fiberCount .q_stab0 = 8 := by decide
theorem fiberCount_q_stab_last : fiberCount .q_stab_last = 8 := by decide

/-! ## Headline: κ_screen hits the suite -/

/-- On the registered 11-row Paper F suite, `κ_screen` action equals
    gold, and the chosen coarsest representing screen matches
    (transport rows have no screen). -/
theorem kappa_screen_hits_suite :
    ∀ row ∈ suite,
      (kappaScreen row.task row.screen row.edges).action = row.expectedAction ∧
      (kappaScreen row.task row.screen row.edges).action =
        gold row.task row.screen row.edges ∧
      (kappaScreen row.task row.screen row.edges).chosen = row.expectedChosen := by
  decide

#print axioms kappa_screen_hits_suite
#print axioms represents_of_isCommonSuffScreen
#print axioms fiberCount_q_perm

end KappaScreen
end StructuralIntelligence
