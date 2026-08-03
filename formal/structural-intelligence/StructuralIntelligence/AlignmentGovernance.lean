/-!
# Structural Intelligence — Alignment Governance AG-2 (algebraic core)

The algebraic core of Theorem AG-2 (viability preserved under superset)
from the *Alignment Governance* companion paper.

For a viability check `viable : Z → Prop`, a length-`T` trajectory
`path : Fin (T+1) → Z` is **valid** if `viable (path t)` holds at every
step.  AG-2 says: if the viability set is enlarged (`V ⊆ V'`), then a
`V`-valid trajectory is automatically `V'`-valid — enlarging the
"acceptable" set of states can only add valid trajectories, never remove
them.

This is the qualitative half of AG-2.  The quantitative bound
(probability of trajectory survival under a Markov kernel) requires
real-valued measures and lives in Mathlib territory (see the package
`README.md`).

Everything here is pure Lean 4 core (no `Mathlib`).
-/

namespace StructuralIntelligence

universe u

section AlignmentGovernance

variable {Z : Type u}

/-- A length-`T` trajectory `path : Fin (T+1) → Z` is **valid** under
    a viability predicate `viable` if every visited state is viable. -/
def ValidTrajectory (T : Nat) (viable : Z → Prop)
    (path : Fin (T + 1) → Z) : Prop :=
  ∀ t : Fin (T + 1), viable (path t)

/-- **AG-2 (Viability inherited by superset, algebraic core).**

    If the viability predicate is enlarged (`∀ z, viable z → viable' z`,
    i.e., `V ⊆ V'`), then any `V`-valid trajectory is automatically
    `V'`-valid.  Proof: pointwise apply the containment.

    Interpretation: relaxing the safety criterion never removes valid
    trajectories; the set of `V`-valid trajectories is monotone in
    `V`.  This is what allows AG-2 to reduce "trajectory validity under
    a strict specification" to "trajectory validity under any
    superset specification" — the quantitative bound on survival
    probability then plugs into the superset directly. -/
theorem viability_inherited_by_superset
    (T : Nat) {viable viable' : Z → Prop}
    (hSuper : ∀ z : Z, viable z → viable' z)
    {path : Fin (T + 1) → Z}
    (hValid : ValidTrajectory T viable path) :
    ValidTrajectory T viable' path :=
  fun t => hSuper (path t) (hValid t)

/-- Corollary: if two viability predicates are equivalent
    (`V = V'` pointwise), then their valid-trajectory predicates
    coincide. -/
theorem viability_valid_ext
    (T : Nat) {viable viable' : Z → Prop}
    (hExt : ∀ z : Z, viable z ↔ viable' z)
    (path : Fin (T + 1) → Z) :
    ValidTrajectory T viable path ↔ ValidTrajectory T viable' path := by
  constructor
  · exact viability_inherited_by_superset T (fun z => (hExt z).mp)
  · exact viability_inherited_by_superset T (fun z => (hExt z).mpr)

end AlignmentGovernance

end StructuralIntelligence
