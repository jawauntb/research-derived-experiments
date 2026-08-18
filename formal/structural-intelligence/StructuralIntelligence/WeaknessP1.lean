/-!
# Structural Intelligence — WI Proposition 1, registered toy (Wave 9)

Honesty.  Banks the finite reading of Proposition 1 (group-completed
coverage) from `papers/weakness_invariance_neurips/paper.md`:

> Among train-consistent candidates, a candidate compatible with
> more group elements covers more of the group-completed deployment
> set.

The paper's general `G` is not constructed here.  This file uses
the two-element group `{id, flip}` on `{p0, p1}` with training
restricted to `p0`.  A candidate *transports* `g` when it sends
the trained point to the true label of `g · p0`.  The shortcut
transports only `id` and covers `{p0}`.  The invariant transports
both actions and covers `{p0, p1}`.  Misaligned / too-small /
too-large `G` stays out.  The overlapping-mixture prior mass
is `WeaknessMixture.lean` (Wave 11).  PAC-Bayes-kl stays out.

No Mathlib.  No `native_decide`.  Kernel `decide` only.

### Mathematical claim card

* Objects.  Points `{p0, p1}`, actions `{id, flip}`, two registered
  candidates, transport count, covered-set size.
* Claim.  The candidate that transports more group elements covers
  strictly more deployment points.
* Withheld.  PAC-Bayes bridge (WI-PB), misaligned `G`, neural tables.
-/

namespace StructuralIntelligence
namespace WeaknessP1

set_option maxRecDepth 400000
set_option maxHeartbeats 2000000

inductive Pt where
  | p0
  | p1
deriving DecidableEq, Repr

inductive Act where
  | id
  | flip
deriving DecidableEq, Repr

def apply : Act → Pt → Pt
  | .id, p => p
  | .flip, .p0 => .p1
  | .flip, .p1 => .p0

def label : Pt → Bool
  | .p0 => false
  | .p1 => true

/-- Shortcut: correct on the trained point, constant off-orbit. -/
def shortcut : Pt → Bool
  | .p0 => false
  | .p1 => false

/-- Invariant: matches `label` everywhere. -/
def invariant : Pt → Bool
  | .p0 => false
  | .p1 => true

/-- Train-consistency on the single observed point `p0`. -/
def trainConsistent (f : Pt → Bool) : Bool :=
  decide (f .p0 = label .p0)

/-- Transport of the observed label along `g`. -/
def transports (f : Pt → Bool) (g : Act) : Bool :=
  decide (f (apply g .p0) = label (apply g .p0))

def weakness (f : Pt → Bool) : Nat :=
  (if transports f .id then 1 else 0) +
  (if transports f .flip then 1 else 0)

/-- Covered deployment points: images of the training point under
    actions the candidate transports. -/
def covers (f : Pt → Bool) (p : Pt) : Bool :=
  (transports f .id && decide (apply .id .p0 = p)) ||
  (transports f .flip && decide (apply .flip .p0 = p))

def coverSize (f : Pt → Bool) : Nat :=
  (if covers f .p0 then 1 else 0) +
  (if covers f .p1 then 1 else 0)

theorem shortcut_train_ok : trainConsistent shortcut = true := by decide
theorem invariant_train_ok : trainConsistent invariant = true := by decide

theorem shortcut_weakness_one : weakness shortcut = 1 := by decide
theorem invariant_weakness_two : weakness invariant = 2 := by decide

theorem shortcut_covers_one : coverSize shortcut = 1 := by decide
theorem invariant_covers_two : coverSize invariant = 2 := by decide

/-- **WI-P1 on the registered toy.**  The candidate that transports
    more group elements covers strictly more of the group-completed
    deployment set. -/
theorem coverage_increases :
    trainConsistent shortcut = true ∧
    trainConsistent invariant = true ∧
    weakness shortcut < weakness invariant ∧
    coverSize shortcut < coverSize invariant := by
  decide

#print axioms coverage_increases
#print axioms shortcut_weakness_one
#print axioms invariant_weakness_two

end WeaknessP1
end StructuralIntelligence
