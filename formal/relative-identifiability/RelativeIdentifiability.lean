/-!
# Experiment-Relative Identifiability

The target-independent experiment family induces an observational setoid.
A target is exactly identifiable precisely when it factors through that
quotient. A target-distinct observational collision is the complete
obstruction, and a richer experiment family induces a canonical surjection
from its finer quotient to the coarser quotient.

This is an elementary quotient/factorization result, formalized here as a
regression theorem rather than claimed as new mathematics.
-/

universe u v w z

namespace RelativeIdentifiability

/-- A typed family of total deterministic observation maps. -/
structure ExperimentSystem where
  Realization : Type u
  Experiment : Type v
  Outcome : Experiment → Type w
  observe : (experiment : Experiment) → Realization → Outcome experiment

namespace ExperimentSystem

variable (system : ExperimentSystem)

/-- A selected family of admissible experiments. -/
abbrev Family := system.Experiment → Prop

/-- Equality of every outcome exposed by the selected family. -/
def Indistinguishable
    (family : system.Family)
    (left right : system.Realization) : Prop :=
  ∀ experiment, family experiment →
    system.observe experiment left = system.observe experiment right

theorem indistinguishable_refl
    (family : system.Family)
    (realization : system.Realization) :
    system.Indistinguishable family realization realization := by
  intro experiment selected
  rfl

theorem indistinguishable_symm
    (family : system.Family)
    {left right : system.Realization}
    (equivalent : system.Indistinguishable family left right) :
    system.Indistinguishable family right left := by
  intro experiment selected
  exact (equivalent experiment selected).symm

theorem indistinguishable_trans
    (family : system.Family)
    {first second third : system.Realization}
    (firstSecond : system.Indistinguishable family first second)
    (secondThird : system.Indistinguishable family second third) :
    system.Indistinguishable family first third := by
  intro experiment selected
  exact (firstSecond experiment selected).trans
    (secondThird experiment selected)

/-- The observational equivalence relation induced by one family. -/
def observationalSetoid (family : system.Family) :
    Setoid system.Realization where
  r := system.Indistinguishable family
  iseqv := {
    refl := system.indistinguishable_refl family
    symm := system.indistinguishable_symm family
    trans := system.indistinguishable_trans family
  }

/-- The maximal object identifiable from the complete family transcript. -/
abbrev QuotientBy (family : system.Family) :=
  Quotient (system.observationalSetoid family)

/-- Map a realization to its observational equivalence class. -/
def quotientMap
    (family : system.Family)
    (realization : system.Realization) :
    system.QuotientBy family :=
  Quotient.mk (system.observationalSetoid family) realization

/-- A target is exactly identifiable when it has a decoder on the quotient. -/
def FactorsThrough
    {Target : Type z}
    (family : system.Family)
    (target : system.Realization → Target) : Prop :=
  ∃ decoder : system.QuotientBy family → Target,
    ∀ realization,
      decoder (system.quotientMap family realization) = target realization

/-- Equivalent realizations must have the same target value. -/
def FiberConstant
    {Target : Type z}
    (family : system.Family)
    (target : system.Realization → Target) : Prop :=
  ∀ left right,
    system.Indistinguishable family left right →
    target left = target right

/-- One target-distinct pair with the same transcript. -/
def HasObstruction
    {Target : Type z}
    (family : system.Family)
    (target : system.Realization → Target) : Prop :=
  ∃ left right,
    system.Indistinguishable family left right ∧
    target left ≠ target right

/--
The quotient factorization criterion: exact identifiability is equivalent to
constancy on every observational fiber.
-/
theorem factorsThrough_iff_fiberConstant
    {Target : Type z}
    (family : system.Family)
    (target : system.Realization → Target) :
    system.FactorsThrough family target ↔
      system.FiberConstant family target := by
  constructor
  · rintro ⟨decoder, decodes⟩ left right equivalent
    rw [← decodes left, ← decodes right]
    exact congrArg decoder (Quotient.sound equivalent)
  · intro constantOnFibers
    refine ⟨Quotient.lift target ?_, ?_⟩
    · intro left right equivalent
      exact constantOnFibers left right equivalent
    · intro realization
      rfl

/--
Universal obstruction theorem: a target-distinct observational collision exists
if and only if exact quotient factorization is impossible.
-/
theorem obstruction_iff_not_factors
    {Target : Type z}
    (family : system.Family)
    (target : system.Realization → Target) :
    system.HasObstruction family target ↔
      ¬ system.FactorsThrough family target := by
  classical
  constructor
  · rintro ⟨left, right, equivalent, targetDifferent⟩ factors
    have constantOnFibers :=
      (system.factorsThrough_iff_fiberConstant family target).mp factors
    exact targetDifferent (constantOnFibers left right equivalent)
  · intro doesNotFactor
    apply Classical.byContradiction
    intro noObstruction
    apply doesNotFactor
    apply (system.factorsThrough_iff_fiberConstant family target).mpr
    intro left right equivalent
    apply Classical.byContradiction
    intro targetDifferent
    exact noObstruction ⟨left, right, equivalent, targetDifferent⟩

/-- Inclusion of experiment families. -/
def FamilyIncluded
    (coarse rich : system.Family) : Prop :=
  ∀ experiment, coarse experiment → rich experiment

/--
Adding experiments can only remove equivalences, never introduce a new one.
-/
theorem indistinguishable_of_richer
    {coarse rich : system.Family}
    (included : system.FamilyIncluded coarse rich)
    {left right : system.Realization}
    (richEquivalent : system.Indistinguishable rich left right) :
    system.Indistinguishable coarse left right := by
  intro experiment coarseSelected
  exact richEquivalent experiment (included experiment coarseSelected)

/--
The canonical map that forgets the extra experiments in a richer quotient.
-/
def forgetExperiments
    {coarse rich : system.Family}
    (included : system.FamilyIncluded coarse rich) :
    system.QuotientBy rich → system.QuotientBy coarse :=
  Quotient.lift (system.quotientMap coarse) (by
    intro left right richEquivalent
    exact Quotient.sound
      (system.indistinguishable_of_richer included richEquivalent))

/-- The richer-to-coarser quotient map is surjective. -/
theorem forgetExperiments_surjective
    {coarse rich : system.Family}
    (included : system.FamilyIncluded coarse rich) :
    Function.Surjective (system.forgetExperiments included) := by
  intro coarseClass
  refine Quotient.inductionOn coarseClass ?_
  intro realization
  exact ⟨system.quotientMap rich realization, rfl⟩

/-- The empty experiment family collapses every realization into one fiber. -/
theorem indistinguishable_empty
    (left right : system.Realization) :
    system.Indistinguishable (fun _ => False) left right := by
  intro experiment selected
  exact False.elim selected

/-- A constant target is identifiable even from the empty family. -/
theorem constant_target_factors
    {Target : Type z}
    (family : system.Family)
    (value : Target) :
    system.FactorsThrough family (fun _ => value) := by
  apply (system.factorsThrough_iff_fiberConstant family (fun _ => value)).mpr
  intro left right equivalent
  rfl

end ExperimentSystem

end RelativeIdentifiability

#print axioms RelativeIdentifiability.ExperimentSystem.factorsThrough_iff_fiberConstant
#print axioms RelativeIdentifiability.ExperimentSystem.obstruction_iff_not_factors
#print axioms RelativeIdentifiability.ExperimentSystem.forgetExperiments_surjective
