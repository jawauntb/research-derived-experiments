/-!
# Structural Intelligence — the silent-substitution kernel (Wave 6)

Item 1 of the "Intention Is All You Need" work list (§24): the
essay's central negative result, P10, as a short composition of a
monotonicity theorem and an invisibility lemma, both finite and
discrete, no measure theory.

Provenance.  The two algebraic lemmas `rearrange` and
`tilt_pointwise` were proved by an **autonomous Lea run** (project
`sic-dynamics`, session `8b9108d5-45b5-4729-8cfd-c4b402528938`) and
are ported verbatim (namespace aside).  The list-level Chebyshev
induction `tilt_monotone`, the invisibility lemma, and the registered
witness were assembled by the orchestrating agent on top of them.

Objects.  A compliant region is a finite list of realizations (a
constraint set — nothing here assumes a single fiber).  A base
compiler is an unnormalized weight `k : α → Nat`.  A reward is
`r : α → Nat`.  One ecology step tilts the compiler by a monotone
function of the reward: `k' x = w (r x) * k x` — the finite stand-in
for `e^{β·r}` (β absorbed into `w`).

Results.

* `tilt_monotone` — **Theorem D, finite kernel**: one ecology step
  weakly raises expected reward, stated cross-multiplied so no
  division is needed.
* `monitor_constant` — **Lemma L1**: any monitor that factors
  through the specification level is constant across the compliant
  region.  A constant record carries no information.
* `witness_*` / `silent_substitution_witness` — **P10's sting** on a
  registered four-point region with principal value opposed to
  delegate reward: one step strictly raises expected reward,
  strictly lowers expected principal value, and the spec-level
  record cannot move.  Kernel `decide` on exact integers.

Not claimed: that any real delegation satisfies the premises (the
essay's bridge, priced as a bet), annealed tilts, drifting rewards,
or anything about experience.  No Mathlib.  No `native_decide`.
-/

namespace StructuralIntelligence
namespace SilentSubstitution

/-- Sum of `f` over a list. -/
def sumBy (f : α → Nat) : List α → Nat
  | [] => 0
  | x :: xs => f x + sumBy f xs

/-- Four-variable rearrangement (Lea-proved): if `a ≤ b` and `c ≤ d`
    then `a·d + b·c ≤ a·c + b·d`. -/
theorem rearrange {a b c d : Nat} (hab : a ≤ b) (hcd : c ≤ d) :
    a * d + b * c ≤ a * c + b * d := by
  have ⟨e, he⟩ := Nat.exists_eq_add_of_le hab
  have ⟨f, hf⟩ := Nat.exists_eq_add_of_le hcd
  subst he
  subst hf
  have h1 : a * (c + f) = a * c + a * f := Nat.mul_add a c f
  have h2 : (a + e) * c = a * c + e * c := Nat.add_mul a e c
  have h3 : (a + e) * (c + f) = a * (c + f) + e * (c + f) :=
    Nat.add_mul a e (c + f)
  have h4 : e * (c + f) = e * c + e * f := Nat.mul_add e c f
  rw [h1, h2, h3, h1, h4]
  generalize a * c = x
  generalize a * f = y
  generalize e * c = z
  generalize e * f = w
  omega

/-- Pointwise Chebyshev step (Lea-proved): for a monotone tilt `w`,
    aligned products dominate crossed products, uniformly in `m`. -/
theorem tilt_pointwise (w : Nat → Nat)
    (hw : ∀ {a b : Nat}, a ≤ b → w a ≤ w b) (ra ry m : Nat) :
    w ra * m * ry + w ry * m * ra ≤ w ra * m * ra + w ry * m * ry := by
  have hbase : w ra * ry + w ry * ra ≤ w ra * ra + w ry * ry := by
    cases Nat.le_total ra ry with
    | inl h =>
      exact rearrange (hw h) h
    | inr h =>
      have h1 := rearrange (hw h) h
      rw [Nat.add_comm (w ry * ra)] at h1
      rw [Nat.add_comm (w ry * ry)] at h1
      exact h1
  have hmul := Nat.mul_le_mul_right m hbase
  have eq1 : w ra * m * ry = w ra * ry * m := by
    rw [Nat.mul_assoc, Nat.mul_comm m ry, ← Nat.mul_assoc]
  have eq2 : w ry * m * ra = w ry * ra * m := by
    rw [Nat.mul_assoc, Nat.mul_comm m ra, ← Nat.mul_assoc]
  have eq3 : w ra * m * ra = w ra * ra * m := by
    rw [Nat.mul_assoc, Nat.mul_comm m ra, ← Nat.mul_assoc]
  have eq4 : w ry * m * ry = w ry * ry * m := by
    rw [Nat.mul_assoc, Nat.mul_comm m ry, ← Nat.mul_assoc]
  rw [eq1, eq2, eq3, eq4]
  have h_add_mul1 : w ra * ry * m + w ry * ra * m
      = (w ra * ry + w ry * ra) * m := by
    rw [Nat.add_mul]
  have h_add_mul2 : w ra * ra * m + w ry * ry * m
      = (w ra * ra + w ry * ry) * m := by
    rw [Nat.add_mul]
  rw [h_add_mul1, h_add_mul2]
  exact hmul

/-! ## Sum algebra helpers -/

theorem sumBy_le_sumBy (f g : α → Nat) (l : List α)
    (h : ∀ x ∈ l, f x ≤ g x) : sumBy f l ≤ sumBy g l := by
  induction l with
  | nil => exact Nat.le_refl 0
  | cons a tl ih =>
    have ha := h a (by simp)
    have htl := ih (fun x hx => h x (by simp [hx]))
    exact Nat.add_le_add ha htl

theorem sumBy_mul_left (c : Nat) (f : α → Nat) (l : List α) :
    c * sumBy f l = sumBy (fun y => c * f y) l := by
  induction l with
  | nil => simp [sumBy]
  | cons a tl ih =>
    simp only [sumBy]
    rw [Nat.mul_add, ih]

theorem sumBy_mul_right (c : Nat) (f : α → Nat) (l : List α) :
    sumBy f l * c = sumBy (fun y => f y * c) l := by
  induction l with
  | nil => simp [sumBy]
  | cons a tl ih =>
    simp only [sumBy]
    rw [Nat.add_mul, ih]

theorem sumBy_add (f g : α → Nat) (l : List α) :
    sumBy f l + sumBy g l = sumBy (fun y => f y + g y) l := by
  induction l with
  | nil => simp [sumBy]
  | cons a tl ih =>
    simp only [sumBy]
    omega

/-- Pointwise cross inequality, rescaled by both weights. -/
theorem cross_point (w : Nat → Nat)
    (hw : ∀ {a b : Nat}, a ≤ b → w a ≤ w b)
    (ra ka ry ky : Nat) :
    ka * ra * (w ry * ky) + ky * ry * (w ra * ka) ≤
      w ra * ka * ra * ky + w ry * ky * ry * ka := by
  have hbase := tilt_pointwise w hw ra ry 1
  have hb : w ra * ry + w ry * ra ≤ w ra * ra + w ry * ry := by
    have e1 : w ra * 1 * ry = w ra * ry := by
      rw [Nat.mul_one]
    have e2 : w ry * 1 * ra = w ry * ra := by
      rw [Nat.mul_one]
    have e3 : w ra * 1 * ra = w ra * ra := by
      rw [Nat.mul_one]
    have e4 : w ry * 1 * ry = w ry * ry := by
      rw [Nat.mul_one]
    rw [e1, e2, e3, e4] at hbase
    exact hbase
  have hmul := Nat.mul_le_mul_right (ka * ky) hb
  have lhs_eq : ka * ra * (w ry * ky) + ky * ry * (w ra * ka)
      = (w ra * ry + w ry * ra) * (ka * ky) := by
    simp [Nat.mul_add, Nat.mul_comm, Nat.mul_left_comm, Nat.add_comm]
  have rhs_eq : w ra * ka * ra * ky + w ry * ky * ry * ka
      = (w ra * ra + w ry * ry) * (ka * ky) := by
    simp [Nat.mul_add, Nat.mul_comm, Nat.mul_left_comm]
  rw [lhs_eq, rhs_eq]
  exact hmul

/-- **Theorem D, finite kernel (one ecology step, cross-multiplied).**
    Over any finite compliant region, tilting a base compiler by a
    monotone function of the reward weakly raises expected reward. -/
theorem tilt_monotone (support : List α) (k r : α → Nat)
    (w : Nat → Nat) (hw : ∀ {a b : Nat}, a ≤ b → w a ≤ w b) :
    sumBy (fun x => k x * r x) support *
        sumBy (fun x => w (r x) * k x) support ≤
      sumBy (fun x => w (r x) * k x * r x) support *
        sumBy k support := by
  induction support with
  | nil => exact Nat.le_refl 0
  | cons a tl ih =>
    simp only [sumBy]
    -- Cross terms, summed from the pointwise inequality.
    have crossL_eq :
        k a * r a * sumBy (fun x => w (r x) * k x) tl +
          sumBy (fun x => k x * r x) tl * (w (r a) * k a)
        = sumBy (fun y => k a * r a * (w (r y) * k y) +
            k y * r y * (w (r a) * k a)) tl := by
      rw [sumBy_mul_left (k a * r a) (fun x => w (r x) * k x) tl,
        sumBy_mul_right (w (r a) * k a) (fun x => k x * r x) tl,
        sumBy_add]
    have crossR_eq :
        w (r a) * k a * r a * sumBy k tl +
          sumBy (fun x => w (r x) * k x * r x) tl * k a
        = sumBy (fun y => w (r a) * k a * r a * k y +
            w (r y) * k y * r y * k a) tl := by
      rw [sumBy_mul_left (w (r a) * k a * r a) k tl,
        sumBy_mul_right (k a) (fun x => w (r x) * k x * r x) tl,
        sumBy_add]
    have cross_le :
        k a * r a * sumBy (fun x => w (r x) * k x) tl +
          sumBy (fun x => k x * r x) tl * (w (r a) * k a) ≤
        w (r a) * k a * r a * sumBy k tl +
          sumBy (fun x => w (r x) * k x * r x) tl * k a := by
      rw [crossL_eq, crossR_eq]
      apply sumBy_le_sumBy
      intro y _
      exact cross_point w hw (r a) (k a) (r y) (k y)
    -- Head terms are equal after commuting.
    have head_eq : k a * r a * (w (r a) * k a)
        = w (r a) * k a * r a * k a := by
      simp [Nat.mul_comm, Nat.mul_left_comm]
    -- Expand both products of sums and assemble.
    have expandL :
        (k a * r a + sumBy (fun x => k x * r x) tl) *
          (w (r a) * k a + sumBy (fun x => w (r x) * k x) tl)
        = k a * r a * (w (r a) * k a) +
            (k a * r a * sumBy (fun x => w (r x) * k x) tl +
              sumBy (fun x => k x * r x) tl * (w (r a) * k a)) +
            sumBy (fun x => k x * r x) tl *
              sumBy (fun x => w (r x) * k x) tl := by
      rw [Nat.add_mul, Nat.mul_add, Nat.mul_add]
      omega
    have expandR :
        (w (r a) * k a * r a + sumBy (fun x => w (r x) * k x * r x) tl) *
          (k a + sumBy k tl)
        = w (r a) * k a * r a * k a +
            (w (r a) * k a * r a * sumBy k tl +
              sumBy (fun x => w (r x) * k x * r x) tl * k a) +
            sumBy (fun x => w (r x) * k x * r x) tl * sumBy k tl := by
      rw [Nat.add_mul, Nat.mul_add, Nat.mul_add]
      omega
    rw [expandL, expandR]
    exact Nat.add_le_add
      (Nat.add_le_add (Nat.le_of_eq head_eq) cross_le) ih

/-- **Lemma L1 (invisibility).**  A monitor that factors through the
    specification level is constant across the compliant region.  A
    constant record carries no information about how far the ecology
    has run. -/
theorem monitor_constant {Spec Obs : Type} (q : α → Spec)
    (M : Spec → Obs) (s0 : Spec) (region : List α)
    (compliant : ∀ x ∈ region, q x = s0) :
    ∀ x ∈ region, ∀ y ∈ region, M (q x) = M (q y) := by
  intro x hx y hy
  rw [compliant x hx, compliant y hy]

/-! ## The registered witness (P10's sting)

Four compliant realizations, base compiler uniform, delegate reward
`0,1,2,3`, principal value `3,2,1,0` (opposed), tilt `w n = n + 1`.
One ecology step: expected reward strictly rises (cross-multiplied
`20·4 > 6·10`), expected principal value strictly falls
(`10·4 < 6·10`), and the spec-level record is constant. -/

inductive R4 where
  | x0
  | x1
  | x2
  | x3
deriving DecidableEq, Repr

def region4 : List R4 := [.x0, .x1, .x2, .x3]

def kBase : R4 → Nat := fun _ => 1

def reward : R4 → Nat
  | .x0 => 0
  | .x1 => 1
  | .x2 => 2
  | .x3 => 3

def value : R4 → Nat
  | .x0 => 3
  | .x1 => 2
  | .x2 => 1
  | .x3 => 0

def tiltW (n : Nat) : Nat := n + 1

theorem witness_reward_strictly_rises :
    sumBy (fun x => kBase x * reward x) region4 *
        sumBy (fun x => tiltW (reward x) * kBase x) region4 <
      sumBy (fun x => tiltW (reward x) * kBase x * reward x) region4 *
        sumBy kBase region4 := by
  decide

theorem witness_value_strictly_falls :
    sumBy (fun x => tiltW (reward x) * kBase x * value x) region4 *
        sumBy kBase region4 <
      sumBy (fun x => kBase x * value x) region4 *
        sumBy (fun x => tiltW (reward x) * kBase x) region4 := by
  decide

/-- **P10, finite kernel, assembled**: on the registered region one
    ecology step strictly raises expected delegate reward and
    strictly lowers expected principal value, while `tilt_monotone`
    covers the general weak direction and `monitor_constant` covers
    the invisibility clause. -/
theorem silent_substitution_witness :
    (sumBy (fun x => kBase x * reward x) region4 *
        sumBy (fun x => tiltW (reward x) * kBase x) region4 <
      sumBy (fun x => tiltW (reward x) * kBase x * reward x) region4 *
        sumBy kBase region4) ∧
    (sumBy (fun x => tiltW (reward x) * kBase x * value x) region4 *
        sumBy kBase region4 <
      sumBy (fun x => kBase x * value x) region4 *
        sumBy (fun x => tiltW (reward x) * kBase x) region4) :=
  ⟨witness_reward_strictly_rises, witness_value_strictly_falls⟩

#print axioms rearrange
#print axioms tilt_pointwise
#print axioms tilt_monotone
#print axioms monitor_constant
#print axioms silent_substitution_witness

end SilentSubstitution
end StructuralIntelligence
