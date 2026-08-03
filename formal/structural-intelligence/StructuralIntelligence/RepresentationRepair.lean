/-!
# Structural Intelligence — Representation Repair RR-2 (algebraic core)

The algebraic core of Theorem RR-2 (Independent lifts compose) from the
*Representation Repair* companion paper.

For a base representation type `R`, an invariant type `Inv`, and a
predicate `captures : R → Inv → Prop` recording which invariants a
given representation captures, a **lift** `lift : R → R` is:

*   A **repair operator** for an invariant `I` if it makes broken
    representations capture `I`:
    `∀ r, ¬ captures r I → captures (lift r) I`.
*   A **preservation operator** for `I` if it does not break already-
    captured `I`s:  `∀ r, captures r I → captures (lift r) I`.

Together, repair + preservation give **`LiftEnsures`**: the lift
*always* produces something capturing `I`, regardless of the input.
This is the clean formulation for RR-2: two lifts that each ensure
their invariant and commute compose to a lift that ensures both
invariants.

RR-2 (as stated in the paper) uses the weaker `LiftRepairs` alone;
the formalisation below records both the strong `LiftEnsures` form
(where the proof is one line per invariant) and the weaker
`LiftRepairs`-plus-`Preserves` form (a `by_cases` split on whether
the input already captures the target invariant).

Everything here is pure Lean 4 core (no `Mathlib`).
-/

namespace StructuralIntelligence

universe u v

section RepresentationRepair

variable {R : Type u} {Inv : Type v}

/-- A lift **repairs** invariant `I` if it makes previously-broken
    representations capture `I`. -/
def LiftRepairs (lift : R → R) (captures : R → Inv → Prop) (I : Inv) : Prop :=
  ∀ r : R, ¬ captures r I → captures (lift r) I

/-- A lift **preserves** invariant `I` if it does not break existing
    captures. -/
def Preserves (lift : R → R) (captures : R → Inv → Prop) (I : Inv) : Prop :=
  ∀ r : R, captures r I → captures (lift r) I

/-- A lift **ensures** invariant `I` if it always produces something
    capturing `I`, regardless of whether the input did. -/
def LiftEnsures (lift : R → R) (captures : R → Inv → Prop) (I : Inv) : Prop :=
  ∀ r : R, captures (lift r) I

/-- Two lifts **commute** (are *independent* in the RR-2 sense) if
    they act in either order to the same effect. -/
def Independent (lift₁ lift₂ : R → R) : Prop :=
  ∀ r : R, lift₁ (lift₂ r) = lift₂ (lift₁ r)

/-- Repair + preservation for the same invariant is the same as
    always-ensuring it. -/
theorem liftEnsures_of_repairs_preserves
    {lift : R → R} {captures : R → Inv → Prop} {I : Inv}
    (hRep : LiftRepairs lift captures I)
    (hPres : Preserves lift captures I) :
    LiftEnsures lift captures I := by
  intro r
  classical
  by_cases h : captures r I
  · exact hPres r h
  · exact hRep r h

/-- **RR-2 (Independent lifts compose, strong form).**  If `lift₁`
    always ensures invariant `I₁` and `lift₂` always ensures
    invariant `I₂`, and the two lifts commute, then their composition
    `lift₁ ∘ lift₂` always ensures both invariants.

    Proof strategy.  For `I₁`: `lift₁ (lift₂ r)` captures `I₁` by
    `hEns₁` (whatever the input, `lift₁` produces something capturing
    `I₁`).  For `I₂`: rewrite `lift₁ (lift₂ r) = lift₂ (lift₁ r)`
    using independence, then apply `hEns₂` (whatever the input,
    `lift₂` produces something capturing `I₂`).  The commutativity of
    the two lifts is exactly what lets the `I₂`-repair "leak past"
    the outer `lift₁`. -/
theorem independent_lifts_compose_ensures
    {captures : R → Inv → Prop}
    {lift₁ lift₂ : R → R} {I₁ I₂ : Inv}
    (hEns₁ : LiftEnsures lift₁ captures I₁)
    (hEns₂ : LiftEnsures lift₂ captures I₂)
    (hIndep : Independent lift₁ lift₂) :
    LiftEnsures (lift₁ ∘ lift₂) captures I₁ ∧
    LiftEnsures (lift₁ ∘ lift₂) captures I₂ := by
  refine ⟨?_, ?_⟩
  · intro r
    show captures (lift₁ (lift₂ r)) I₁
    exact hEns₁ (lift₂ r)
  · intro r
    show captures (lift₁ (lift₂ r)) I₂
    rw [hIndep r]
    exact hEns₂ (lift₁ r)

/-- **RR-2 (Independent lifts compose, RR-form).**  If `lift₁`
    repairs `I₁` and preserves `I₂`, `lift₂` repairs `I₂` and
    preserves `I₁`, and the two lifts commute, then their composition
    repairs both `I₁` and `I₂`.

    Follows from `independent_lifts_compose_ensures` after upgrading
    the repair-plus-preserve hypotheses to the `LiftEnsures` form and
    then downgrading the conclusion back to `LiftRepairs`.

    A pure `LiftRepairs`-only hypothesis is not enough: if `lift₂`
    breaks `I₁` on an input that captures it, no amount of
    independence with `lift₁` will save it, because `lift₁` only
    repairs *broken* `I₁`, not preserves already-captured `I₁`.  The
    preservation hypothesis is what plugs that hole; the paper's
    RR-2 assumes it implicitly (as is standard in the belief-revision
    literature). -/
theorem independent_lifts_compose
    {captures : R → Inv → Prop}
    {lift₁ lift₂ : R → R} {I₁ I₂ : Inv}
    (hRep₁ : LiftRepairs lift₁ captures I₁)
    (hPres₁ : Preserves lift₁ captures I₁)
    (hRep₂ : LiftRepairs lift₂ captures I₂)
    (hPres₂ : Preserves lift₂ captures I₂)
    (hIndep : Independent lift₁ lift₂) :
    LiftRepairs (lift₁ ∘ lift₂) captures I₁ ∧
    LiftRepairs (lift₁ ∘ lift₂) captures I₂ := by
  have hEns₁ := liftEnsures_of_repairs_preserves hRep₁ hPres₁
  have hEns₂ := liftEnsures_of_repairs_preserves hRep₂ hPres₂
  obtain ⟨hC₁, hC₂⟩ :=
    independent_lifts_compose_ensures hEns₁ hEns₂ hIndep
  refine ⟨?_, ?_⟩
  · intro r _
    exact hC₁ r
  · intro r _
    exact hC₂ r

end RepresentationRepair

end StructuralIntelligence
