import StructuralIntelligence.DeleteRepair

/-!
# Structural Intelligence — uniqueness of a representing screen fails

Paper F's `κ_unique` claim: without a tie-break, the set of representing
menu screens is a singleton whenever a repair exists.  On the registered
`{0,1}^4` menu the `bag` / popcount task kills that claim: **five**
named screens represent `yBag`.

Honesty.  Uniqueness is dead.  `κ_screen` is still a function only
because of the *disclosed* total order (fewest fibres, then
lexicographic name).  That order is **not** used here, and must not be
smuggled in as a hidden unique representative.  The representing set
is not a singleton; a named total order merely picks one element of a
five-element set.

Path A / Path B (`DeleteRepair.repair_paths_disagree`) is the schedule
form of the same uniqueness failure.  It is cited, not re-proved.
CommonSuffScreen / Theorem 4 is not re-proved: representability here
is fibre-constancy of `yBag` on a named screen.

No `Mathlib`.  No `sorry`.  No `Complex.log`.  Not a new letter.

### Mathematical claim card

* Objects.  World `W = Bool⁴` (registered `{0,1}^4`).  Menu names
  `{q_id, q_rot, q_perm, q_stab0, q_stab_last}` with the orbit-canonical
  maps of `delete_the_absolute` / surgery cores.  Task `yBag` = popcount.
* Claim.  The list of representing menu screens for `yBag` has length 5,
  hence `¬ ∃! r, Represents (screenFn r) yBag` on the menu.
* Assumptions.  Finite discrete world; representability = fibre-constancy
  (`q x = q x' → yBag x = yBag x'`).  Menu is exactly those five names.
* Identification.  Screens are the Python maps, not a new primitive.
* Kill.  The claim dies if some menu screen fails fibre-constancy, or if
  the representing list is a singleton, or if uniqueness is restored by
  a hidden tie-break.
* Edge / null.  This is not uniqueness of `κ_screen` as a function
  (that uses the disclosed order).  It is not Path A/B (already Lean).
-/

namespace StructuralIntelligence
namespace KappaUnique

/-! ## Worlds, popcount, menu screens -/

/-- Registered world: four bits.  Same carrier as `{0,1}^4`. -/
structure World where
  b0 : Bool
  b1 : Bool
  b2 : Bool
  b3 : Bool
deriving DecidableEq, Repr

/-- `yBag` = popcount. -/
def yBag (x : World) : Nat :=
  (if x.b0 then 1 else 0) + (if x.b1 then 1 else 0) +
  (if x.b2 then 1 else 0) + (if x.b3 then 1 else 0)

/-- Named screens on the disclosed Paper E/F menu. -/
inductive ScreenName where
  | q_id
  | q_rot
  | q_perm
  | q_stab0
  | q_stab_last
deriving DecidableEq, Repr

/-- Identity screen. -/
def qId (x : World) : World := x

/-- One-step rotate-left: `(b0,b1,b2,b3) ↦ (b1,b2,b3,b0)`. -/
def rotLeft (x : World) : World :=
  ⟨x.b1, x.b2, x.b3, x.b0⟩

/-- Lex code: `b0` is the high bit (`false = 0 < true = 1`). -/
def worldCode (x : World) : Nat :=
  (if x.b0 then 8 else 0) + (if x.b1 then 4 else 0) +
  (if x.b2 then 2 else 0) + (if x.b3 then 1 else 0)

/-- Lex-least of two worlds. -/
def minWorld (x y : World) : World :=
  if worldCode x ≤ worldCode y then x else y

/-- `q_rot`: lexicographically least rotation. -/
def qRot (x : World) : World :=
  let x1 := rotLeft x
  let x2 := rotLeft x1
  let x3 := rotLeft x2
  minWorld (minWorld x x1) (minWorld x2 x3)

/-- `q_perm`: sorted tuple (`false` before `true`).  Same fibres as the
    bit histogram / popcount. -/
def qPerm (x : World) : World :=
  match yBag x with
  | 0 => ⟨false, false, false, false⟩
  | 1 => ⟨false, false, false, true⟩
  | 2 => ⟨false, false, true, true⟩
  | 3 => ⟨false, true, true, true⟩
  | _ => ⟨true, true, true, true⟩

/-- Sort three bits, `false` first. -/
def sort3 (a b c : Bool) : Bool × Bool × Bool :=
  let n := (if a then 1 else 0) + (if b then 1 else 0) + (if c then 1 else 0)
  match n with
  | 0 => (false, false, false)
  | 1 => (false, false, true)
  | 2 => (false, true, true)
  | _ => (true, true, true)

/-- `q_stab0`: keep bit 0, sort the rest.  Orbit-canonical for `Stab(0)`. -/
def qStab0 (x : World) : World :=
  let s := sort3 x.b1 x.b2 x.b3
  ⟨x.b0, s.1, s.2.1, s.2.2⟩

/-- `q_stab_last`: keep the last bit, sort the prefix.  Dual of `q_stab0`. -/
def qStabLast (x : World) : World :=
  let s := sort3 x.b0 x.b1 x.b2
  ⟨s.1, s.2.1, s.2.2, x.b3⟩

/-- Evaluate a named menu screen. -/
def screenFn : ScreenName → World → World
  | .q_id => qId
  | .q_rot => qRot
  | .q_perm => qPerm
  | .q_stab0 => qStab0
  | .q_stab_last => qStabLast

/-- Disclosed menu.  Order is the Python `MENU` tuple; it is **not** a
    uniqueness proof.  Fewest-fibres-then-lex is a later total order
    used by `κ_screen`, not by `representingScreens`. -/
def menu : List ScreenName :=
  [.q_id, .q_rot, .q_perm, .q_stab0, .q_stab_last]

/-! ## Representability = fibre-constancy -/

/-- `y` factors through `q`: constant on every `q`-fibre. -/
def Represents {α β : Type} (q : World → α) (y : World → β) : Prop :=
  ∀ x x' : World, q x = q x' → y x = y x'

/-- If `q` merely rearranges bits (preserves popcount), it represents `yBag`. -/
theorem preserves_yBag_represents
    (q : World → World) (hq : ∀ x, yBag (q x) = yBag x) :
    Represents q yBag := by
  intro x x' h
  calc yBag x
      = yBag (q x)  := (hq x).symm
    _ = yBag (q x') := congrArg yBag h
    _ = yBag x'     := hq x'

/-- Popcount is definitionally preserved by `qId`. -/
theorem yBag_qId (x : World) : yBag (qId x) = yBag x := rfl

/-- Each of the 16 worlds: `qRot` is a rotation, so popcount is unchanged. -/
theorem yBag_qRot (x : World) : yBag (qRot x) = yBag x := by
  rcases x with ⟨a, b, c, d⟩
  cases a <;> cases b <;> cases c <;> cases d <;> rfl

/-- `qPerm` is the sorted tuple with the same number of `true` bits. -/
theorem yBag_qPerm (x : World) : yBag (qPerm x) = yBag x := by
  rcases x with ⟨a, b, c, d⟩
  cases a <;> cases b <;> cases c <;> cases d <;> rfl

/-- `qStab0` permutes the last three bits. -/
theorem yBag_qStab0 (x : World) : yBag (qStab0 x) = yBag x := by
  rcases x with ⟨a, b, c, d⟩
  cases a <;> cases b <;> cases c <;> cases d <;> rfl

/-- `qStabLast` permutes the first three bits. -/
theorem yBag_qStabLast (x : World) : yBag (qStabLast x) = yBag x := by
  rcases x with ⟨a, b, c, d⟩
  cases a <;> cases b <;> cases c <;> cases d <;> rfl

theorem qId_represents : Represents qId yBag :=
  preserves_yBag_represents qId yBag_qId

theorem qRot_represents : Represents qRot yBag :=
  preserves_yBag_represents qRot yBag_qRot

theorem qPerm_represents : Represents qPerm yBag :=
  preserves_yBag_represents qPerm yBag_qPerm

theorem qStab0_represents : Represents qStab0 yBag :=
  preserves_yBag_represents qStab0 yBag_qStab0

theorem qStabLast_represents : Represents qStabLast yBag :=
  preserves_yBag_represents qStabLast yBag_qStabLast

/-- Every named menu screen represents `yBag`. -/
theorem each_menu_represents (r : ScreenName) :
    Represents (screenFn r) yBag := by
  cases r with
  | q_id => exact qId_represents
  | q_rot => exact qRot_represents
  | q_perm => exact qPerm_represents
  | q_stab0 => exact qStab0_represents
  | q_stab_last => exact qStabLast_represents

/-- Decidable fibre-constancy on this finite menu: every name represents,
    so the instance is `isTrue` from `each_menu_represents`.  This is
    **not** a tie-break and does not pick a unique screen. -/
instance represents_yBag_decidable (r : ScreenName) :
    Decidable (Represents (screenFn r) yBag) :=
  isTrue (each_menu_represents r)

/-- Representing menu screens for `yBag`.  Filter of the disclosed menu
    by fibre-constancy.  No fewest-fibre / lex selection. -/
def representingScreens : List ScreenName :=
  menu.filter fun r => decide (Represents (screenFn r) yBag)

/-- Filter keeps every name: `decide` reduces by the `isTrue` instance. -/
theorem representingScreens_eq_menu : representingScreens = menu :=
  rfl

/-- **Headline.**  The `bag` task has five representing menu screens. -/
theorem bag_not_unique : representingScreens.length = 5 :=
  rfl

/-- Unique-existential (`∃!`) on the menu, written without Mathlib
    `ExistsUnique` notation. -/
def UniqueExistential {α : Sort _} (p : α → Prop) : Prop :=
  ∃ x, p x ∧ ∀ y, p y → y = x

/-- Unique-existential form: there is not a unique representing name
    on the menu.  Five distinct constructors all represent. -/
theorem uniqueExistential_fails :
    ¬ UniqueExistential fun r : ScreenName => Represents (screenFn r) yBag := by
  intro h
  rcases h with ⟨r, _hr, huniq⟩
  have hid := huniq .q_id (each_menu_represents .q_id)
  have hperm := huniq .q_perm (each_menu_represents .q_perm)
  have : ScreenName.q_id = ScreenName.q_perm := hid.trans hperm.symm
  cases this

/-- Schedule form of the same uniqueness failure: Path A / Path B.
    Cited from `DeleteRepair`; not re-proved. -/
theorem uniqueness_also_fails_as_schedules :
    ∃ p q : Nat × Nat,
      DeleteRepair.pathA p = DeleteRepair.pathA q ∧
      DeleteRepair.pathB p ≠ DeleteRepair.pathB q :=
  DeleteRepair.repair_paths_disagree

end KappaUnique
end StructuralIntelligence

#print axioms StructuralIntelligence.KappaUnique.bag_not_unique
#print axioms StructuralIntelligence.KappaUnique.uniqueExistential_fails
#print axioms StructuralIntelligence.KappaUnique.uniqueness_also_fails_as_schedules
