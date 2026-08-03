/-!
# Structural Intelligence — Theory Atlas TA-1 (algebraic core)

The algebraic core of Theorem TA-1 (Cocycle condition ⟺ gluing) from
the *Theory Atlas* companion paper.

For a family of chart transitions `T : I → I → Q → Q` (where `T i j`
carries a state in chart `i` to its representation in chart `j`), the
**cocycle condition** says that composing transitions is consistent
with a single-step transition:

> `∀ i j k q, T j k (T i j q) = T i k q`.

Chart consistency ("gluing") is the existence of a family of maps
`M : I → Q → Q` such that `M j` normalises the transported state to
the same canonical form that `M i` produces on the original.

The paper's TA-1 is stated as an equivalence.  In pure Lean 4 core
we split it into two provable halves — the honest content of TA-1
without any auxiliary structure:

*   **Forward direction (proved here).**  From `CocycleHolds T` and
    an inhabited chart index, we construct an explicit gluing family
    `M i q := T i default q`.  This satisfies the gluing equation
    `M j (T i j q) = M i q` and a canonical-chart idempotency
    `M default (M i q) = M i q`.
*   **Reverse direction (proved here under injectivity).**  Any
    gluing family whose components `M i` are injective forces the
    cocycle to hold, because `M k (T j k (T i j q)) = M k (T i k q)`
    and injectivity cancels `M k`.

Together they give the "cocycle ⟺ gluing up to injective components"
content of TA-1.  The naked-`↔` statement of TA-1 (as printed in the
paper) is subtle: without injectivity, the trivial constant family
`M := fun _ _ => q₀` satisfies the gluing equation *and*
`M i (M i q) = M i q` for free, so the (⇐) direction is vacuous
without extra structure.  See the package `README.md` for the record.

Everything here is pure Lean 4 core (no `Mathlib`).
-/

namespace StructuralIntelligence

universe u v

section TheoryAtlas

variable {I : Type u} {Q : Type v}

/-- **Cocycle condition.**  Composing chart transitions from `i` to
    `j` and then `j` to `k` is the same as the direct transition from
    `i` to `k`. -/
def CocycleHolds (T : I → I → Q → Q) : Prop :=
  ∀ i j k : I, ∀ q : Q, T j k (T i j q) = T i k q

/-- **Gluing equation.**  A family `M : I → Q → Q` glues the
    transitions if `M j` on the transported representation equals
    `M i` on the original. -/
def GluesTransitions (T : I → I → Q → Q) (M : I → Q → Q) : Prop :=
  ∀ i j : I, ∀ q : Q, M j (T i j q) = M i q

/-- Injectivity of a function `f : α → β`, spelt out locally so we do
    not have to import Mathlib.  -/
def Injective {α : Sort u} {β : Sort v} (f : α → β) : Prop :=
  ∀ a₁ a₂ : α, f a₁ = f a₂ → a₁ = a₂

/-- **TA-1 forward direction.**  If the cocycle condition holds and
    the chart index `I` is inhabited, then the family
    `M i q := T i (default : I) q` glues the transitions and is
    canonical-chart idempotent: `M default (M i q) = M i q`.

    Interpretation: pick a distinguished chart `i₀ := default`; the
    "canonical representative" of `q` in the atlas is its transport
    to chart `i₀`.  The cocycle condition guarantees this
    representative is well-defined regardless of the source chart. -/
theorem cocycle_implies_gluing
    [Inhabited I] {T : I → I → Q → Q} (hCoc : CocycleHolds T) :
    ∃ M : I → Q → Q,
      GluesTransitions T M ∧
      (∀ i : I, ∀ q : Q, M (default : I) (M i q) = M i q) := by
  refine ⟨fun i => T i (default : I), ?_, ?_⟩
  · intro i j q
    show T j (default : I) (T i j q) = T i (default : I) q
    exact hCoc i j (default : I) q
  · intro i q
    show T (default : I) (default : I) (T i (default : I) q)
        = T i (default : I) q
    exact hCoc i (default : I) (default : I) q

/-- **TA-1 reverse direction (under injectivity).**  If a gluing
    family `M` has injective components (`∀ i, Injective (M i)`),
    then the cocycle condition holds.

    Proof: `M k (T j k (T i j q)) = M j (T i j q) = M i q` by the
    gluing equation applied twice, and `M k (T i k q) = M i q`
    similarly; injectivity of `M k` cancels the outer `M k`. -/
theorem injective_gluing_implies_cocycle
    {T : I → I → Q → Q} {M : I → Q → Q}
    (hInj : ∀ i : I, Injective (M i))
    (hGlue : GluesTransitions T M) :
    CocycleHolds T := by
  intro i j k q
  apply hInj k
  calc M k (T j k (T i j q))
      = M j (T i j q) := hGlue j k (T i j q)
    _ = M i q         := hGlue i j q
    _ = M k (T i k q) := (hGlue i k q).symm

end TheoryAtlas

end StructuralIntelligence
