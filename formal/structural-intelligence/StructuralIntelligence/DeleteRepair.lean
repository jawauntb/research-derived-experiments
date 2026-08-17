/-!
# Structural Intelligence — Delete–obstruction–repair core

The algebraic core of the delete–obstruction–repair argument: over-invariance
is a no-go, positional steps integrate on a path and close on a cycle iff the
steps sum to zero, potentials are unique up to a global translation, exact
repair must split any leftover fibre disagreement, and the two repair
schedules (delete-then-default vs relative-then-drop) disagree on a finite
witness.

Honesty.  `symmetry_mismatch_nogo` is the group-action packaging of the
`CommonSuffScreen` contrapositive, not a new logical primitive.  The
counting form `|r`-values on a fibre` ≥ `|Y`-values on a fibre` is the
discrete `H(R | q_D) ≥ H(Y | q_D)`; we bank the split, not Shannon
entropy (no reals).  `repair_paths_disagree` is the finite
"position then pool ≠ pool then position" fact.  It is not a relativity
theorem.

Everything here is pure Lean 4 core (no `Mathlib`).
-/

namespace StructuralIntelligence
namespace DeleteRepair

universe u v w y r

/-! ## 1. Symmetry mismatch (over-invariance no-go) -/

/-- A (left) action of `G` on `X`.  No group laws are required: the
    no-go is about invariance under a family of maps, not about `G`
    being a group. -/
def Act (G X : Type _) := G → X → X

/-- `f` is invariant under `act` if acting first does not change `f`. -/
def IsInvariant {G X Y : Type _} (act : Act G X) (f : X → Y) : Prop :=
  ∀ g x, f (act g x) = f x

/-- `target` factors through `q` if `q`-agreement implies `target`-agreement.
    Equivalent to the existence of `h : Z → Y` with `target = h ∘ q` once
    one is willing to choose values on the image (we keep the relational
    form so the under-invariance fact needs no choice). -/
def FactorsThrough {X Z Y : Type _} (q : X → Z) (target : X → Y) : Prop :=
  ∀ x x', q x = q x' → target x = target x'

/-- **Over-invariance no-go (direct form).**  If the screen `q` is
    `act`-invariant and `target` factors through `q` as a postcomposition,
    then `target` is `act`-invariant.

    This is the group-action packaging of the `CommonSuffScreen`
    implication "factorisation ⇒ fibre-constancy", specialised to the
    orbit relation.  Not a new logical primitive. -/
theorem over_invariance_nogo
    {G X Z Y : Type _}
    (act : Act G X) (q : X → Z) (target : X → Y)
    (hq : IsInvariant act q)
    (hFactor : ∃ h : Z → Y, ∀ x, target x = h (q x)) :
    IsInvariant act target := by
  intro g x
  obtain ⟨h, hh⟩ := hFactor
  calc target (act g x)
      = h (q (act g x)) := hh (act g x)
    _ = h (q x)         := by rw [hq g x]
    _ = target x        := (hh x).symm

/-- **Symmetry-mismatch no-go.**  If `q` is `act`-invariant but `target`
    is not (witnessed at `(g, x)`), then `target` cannot factor through
    `q`.  Contrapositive of `over_invariance_nogo`. -/
theorem symmetry_mismatch_nogo
    {G X Z Y : Type _}
    (act : Act G X) (q : X → Z) (target : X → Y)
    (hq : IsInvariant act q)
    {g : G} {x : X} (hY : target (act g x) ≠ target x) :
    ¬ ∃ h : Z → Y, ∀ x', target x' = h (q x') := by
  intro hFactor
  exact hY (over_invariance_nogo act q target hq hFactor g x)

/-- If `target` is `act`-invariant and every `q`-fibre is an `act`-orbit
    (more precisely: `q x = q x'` implies some `g` carries `x` to `x'`),
    then `target` factors through `q`. -/
theorem invariant_orbits_factor
    {G X Z Y : Type _}
    (act : Act G X) (q : X → Z) (target : X → Y)
    (hY : IsInvariant act target)
    (hFiber : ∀ x x', q x = q x' → ∃ g, act g x = x') :
    FactorsThrough q target := by
  intro x x' hq
  obtain ⟨g, hg⟩ := hFiber x x' hq
  calc target x
      = target (act g x) := (hY g x).symm
    _ = target x'        := congrArg target hg

/-- **Under-invariance is not a no-go.**  The identity screen always
    factors every target: leftover privilege (a finer screen) does not
    by itself obstruct reconstruction. -/
theorem identity_always_factors {X Y : Type _} (target : X → Y) :
    FactorsThrough (fun x : X => x) target := by
  intro x x' hx
  exact congrArg target hx

/-! ## 2. Positional integration (the connection core)

    Relative steps are a `List Int`.  `prefixSum rs i` is the potential
    after `i` steps, starting at `0`.  `sumInt` is the ordinary list
    sum (written locally so we do not depend on prelude `List.sum`
    unfolding). -/

/-- Prefix potential of a relative-step list.  `prefixSum rs 0 = 0`
    and each successor adds `rs.getD n 0` (out-of-range steps are `0`). -/
def prefixSum (rs : List Int) : Nat → Int
  | 0 => 0
  | n + 1 => prefixSum rs n + rs.getD n 0

/-- On a path, the potential after `i+1` steps is the potential after
    `i` steps plus the `i`-th relative step.  Definitional in `i`; the
    length hypothesis records that we are still on the path. -/
theorem path_integrates (rs : List Int) :
    ∀ i, i < rs.length → prefixSum rs (i + 1) = prefixSum rs i + rs.getD i 0 := by
  intro i _
  rfl

/-- Local `Int` list sum.  Avoids leaning on prelude `List.sum`. -/
def sumInt : List Int → Int
  | [] => 0
  | x :: xs => x + sumInt xs

/-- Stepping past the head of a cons-list adds that head and then
    integrates the tail. -/
theorem prefixSum_cons (x : Int) (xs : List Int) :
    ∀ n, prefixSum (x :: xs) (n + 1) = x + prefixSum xs n := by
  intro n
  induction n with
  | zero =>
    -- `prefixSum (x :: xs) 1 = 0 + x` and `x + prefixSum xs 0 = x + 0`.
    change (0 : Int) + (x :: xs).getD 0 0 = x + prefixSum xs 0
    change (0 : Int) + x = x + (0 : Int)
    exact Int.add_comm 0 x
  | succ n ih =>
    calc prefixSum (x :: xs) (n + 1 + 1)
        = prefixSum (x :: xs) (n + 1) + (x :: xs).getD (n + 1) 0 := rfl
      _ = (x + prefixSum xs n) + (x :: xs).getD (n + 1) 0 := by rw [ih]
      _ = (x + prefixSum xs n) + xs.getD n 0 := rfl
      _ = x + (prefixSum xs n + xs.getD n 0) := Int.add_assoc x (prefixSum xs n) (xs.getD n 0)
      _ = x + prefixSum xs (n + 1) := rfl

/-- The potential after reading the whole list equals the list sum. -/
theorem prefixSum_length_eq_sumInt : ∀ rs : List Int,
    prefixSum rs rs.length = sumInt rs
  | [] => rfl
  | x :: xs => by
    change prefixSum (x :: xs) (xs.length + 1) = x + sumInt xs
    rw [prefixSum_cons, prefixSum_length_eq_sumInt xs]

/-- **Cycle integration.**  A closed walk (prefix potential returns to
    `0` after `rs.length` steps) exists iff the relative steps sum to
    zero. -/
theorem cycle_integrates_iff_sum_zero (rs : List Int) :
    (prefixSum rs rs.length = 0) ↔ (sumInt rs = 0) := by
  rw [prefixSum_length_eq_sumInt]

/-- **Potentials are unique up to a global translation.**  Two discrete
    integrals of the same step field `r` on `{0,…,n}` differ by the
    constant `p 0 - q 0`. -/
theorem potentials_unique_up_to_translation
    (n : Nat) (r : Nat → Int) (p q : Nat → Int)
    (hp : ∀ i, i < n → p (i + 1) = p i + r i)
    (hq : ∀ i, i < n → q (i + 1) = q i + r i) :
    ∀ i, i ≤ n → p i = q i + (p 0 - q 0) := by
  intro i hi
  induction i with
  | zero =>
    calc p 0
        = (p 0 - q 0) + q 0 := (Int.sub_add_cancel (p 0) (q 0)).symm
      _ = q 0 + (p 0 - q 0) := Int.add_comm (p 0 - q 0) (q 0)
  | succ i ih =>
    have hi' : i < n := Nat.lt_of_succ_le hi
    have hi'' : i ≤ n := Nat.le_of_lt hi'
    calc p (i + 1)
        = p i + r i := hp i hi'
      _ = (q i + (p 0 - q 0)) + r i := by rw [ih hi'']
      _ = q i + ((p 0 - q 0) + r i) := Int.add_assoc (q i) (p 0 - q 0) (r i)
      _ = q i + (r i + (p 0 - q 0)) := by rw [Int.add_comm (p 0 - q 0) (r i)]
      _ = (q i + r i) + (p 0 - q 0) := (Int.add_assoc (q i) (r i) (p 0 - q 0)).symm
      _ = q (i + 1) + (p 0 - q 0) := by rw [hq i hi']

/-! ## 3. Deterministic repair debt -/

/-- `r` is an **exact repair** of the deleted screen `qD` for `target`
    when any two inputs that agree on both `qD` and `r` agree on
    `target`.  Equivalently, `target` factors through `(qD, r)`. -/
def ExactRepair {X Z R Y : Type _} (qD : X → Z) (r : X → R) (target : X → Y) : Prop :=
  ∀ x x', qD x = qD x' → r x = r x' → target x = target x'

/-- **Repair splits disagreement.**  If `r` exactly repairs `qD` for
    `target`, then any leftover `target`-disagreement on a `qD`-fibre
    is already a disagreement of `r`.

    The counting form `|r`-values on the fibre` ≥ `|Y`-values on the
    fibre` is the discrete `H(R | q_D) ≥ H(Y | q_D)`.  We bank the
    split, not Shannon entropy (no reals). -/
theorem repair_splits_disagreement
    {X Z R Y : Type _}
    {qD : X → Z} {r : X → R} {target : X → Y}
    (hR : ExactRepair qD r target)
    {x x' : X} (hq : qD x = qD x') (hY : target x ≠ target x') :
    r x ≠ r x' :=
  fun hr => hY (hR x x' hq hr)

/-! ## 4. Repair noncommutativity witness

    Concrete world `Nat × Nat`.  Path A deletes the absolute first
    coordinate and writes the default origin `x = 0`.  Path B forms
    the relative `y - x` and then drops the absolute.  The two
    schedules disagree on `(0,1)` vs `(1,1)`: same leftover `y`,
    different `y - x`.

    This is the finite "position then pool ≠ pool then position" fact.
    It is not a relativity theorem. -/

def dropX (p : Nat × Nat) : Nat := p.2

def defaultOrigin (y : Nat) : Nat × Nat := (0, y)

def relThenDrop (p : Nat × Nat) : Int := (Int.ofNat p.2) - (Int.ofNat p.1)

/-- Path A: delete absolute `x`, then "repair" by writing `x = 0`. -/
def pathA (p : Nat × Nat) : Nat × Nat := defaultOrigin (dropX p)

/-- Path B: form the relative, then drop the absolute. -/
def pathB (p : Nat × Nat) : Int := relThenDrop p

/-- The two repair schedules disagree: `(0,1)` and `(1,1)` share a
    Path-A image but not a Path-B image. -/
theorem repair_paths_disagree :
    ∃ p q : Nat × Nat,
      pathA p = pathA q ∧ pathB p ≠ pathB q := by
  refine ⟨(0, 1), (1, 1), rfl, ?_⟩
  -- `pathB (0,1) = 1 - 0 = 1` and `pathB (1,1) = 1 - 1 = 0`.
  decide

end DeleteRepair
end StructuralIntelligence
