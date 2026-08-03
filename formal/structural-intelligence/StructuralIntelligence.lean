import StructuralIntelligence.Basic
import StructuralIntelligence.UnionBound
import StructuralIntelligence.Pigeonhole
import StructuralIntelligence.CouponCollector
import StructuralIntelligence.CommonSuffScreen
import StructuralIntelligence.Refinement
import StructuralIntelligence.CompilerTomography
import StructuralIntelligence.CausalSemantics
import StructuralIntelligence.Antecedents
import StructuralIntelligence.AbstractionFrontier
import StructuralIntelligence.AlignmentGovernance
import StructuralIntelligence.TheoryAtlas
import StructuralIntelligence.RepresentationRepair
import StructuralIntelligence.AutocatalyticArtwork

/-!
# Structural Intelligence — Lean 4 formalisation

The Lean-checked ingredients of Theorems 4, 5 and 6-core of the
*Structural Intelligence* paper (`papers/structural_intelligence/paper.md`)
plus the CT-1 core of the *Compiler Tomography* companion paper
(`papers/compiler_tomography/paper.md`) and the algebraic cores of
CS-1, CS-2, SA-1, AF-1, AF-2, AG-2, TA-1, RR-2 and AA-2 across the
remaining Structural-Intelligence companion papers:

*   `StructuralIntelligence.theorem5_union_bound` — the counting form
    of the union bound `Pr[⋃ᵢ Aᵢ] ≤ Σᵢ Pr[Aᵢ]`, formulated over lists
    and `Fin M`.
*   `StructuralIntelligence.theorem5_deterministic_lower_bound` — the
    coupon-collector pigeonhole: any sample sequence of length `N < M`
    from an `M`-element universe misses at least one element.
*   `StructuralIntelligence.commonSuffScreen_refines` — the algebraic
    core of Theorem 4 (Cross-task stability, conditional): if every
    task `Y α : X → Yfam α` factors through a common map `q : X → Z`,
    then `q x = q x'` implies `Y α x = Y α x'` for every task index
    `α`.  Equivalently, the equivalence relation induced on `X` by `q`
    refines the joint task equivalence relation.
*   `StructuralIntelligence.commonSuffScreen_coarsest` — the coarsest
    common-sufficient-statistic corollary: adding the converse
    implication makes `q` maximally coarse among common-sufficient
    screens.
*   `StructuralIntelligence.refinement_transitive` — refinement of
    binary relations is transitive.
*   `StructuralIntelligence.refinement_preserves_screen` — the
    algebraic core of Theorem 6 (§2.5b, ε-covering reduction): if
    `q₁ : X → Z₁` is a common sufficient screen for a task family
    and `q₂ : X → Z₂` refines `q₁` (functionally, via
    `q₁ = r ∘ q₂`), then `q₂` is also a common sufficient screen —
    the ε-cover inherits the factorisation by composition.
*   `StructuralIntelligence.identifiability_implies_unique_by_witness`
    — CT-1 core: if every wrong parameter `θ ≠ θ*` is refuted by
    the data set `D`, then `θ*` is the unique parameter consistent
    with `D`.
*   `StructuralIntelligence.identifiability_isolates_theta_star` —
    CT-1 core in constructive form: for any finite list of
    candidates, identifiability lets us build a `D` that isolates
    `θ*` uniquely.
*   `StructuralIntelligence.psi_equiv_preserves_under_context` —
    CS-1 core: Ψ-equivalent messages agree in every context list.
*   `StructuralIntelligence.messageQuotient_is_common_sufficient`,
    `StructuralIntelligence.messageQuotient_is_coarsest` — CS-2 core:
    the message quotient is a common sufficient screen and is the
    coarsest such screen on messages.
*   `StructuralIntelligence.intersection_is_common_sufficient`,
    `StructuralIntelligence.intersection_is_coarsest_over_family` —
    SA-1 core: the intersection of a family of antecedent quotients
    is a common sufficient screen for any locally-sufficient task
    family, and it is the coarsest quotient with that property.
*   `StructuralIntelligence.pareto_set_is_antichain` — AF-1 core:
    two Pareto-optimal quotients cannot dominate each other.
*   `StructuralIntelligence.pareto_contains_css_when_zero_sufficiency`
    — AF-2 core: in the two-axis static case, any cost-minimal
    common sufficient screen is Pareto.
*   `StructuralIntelligence.viability_inherited_by_superset` — AG-2
    core: enlarging the viability set preserves trajectory validity.
*   `StructuralIntelligence.cocycle_implies_gluing`,
    `StructuralIntelligence.injective_gluing_implies_cocycle` — TA-1
    core in both directions (up to injective components on the
    gluing family).
*   `StructuralIntelligence.independent_lifts_compose_ensures`,
    `StructuralIntelligence.independent_lifts_compose` — RR-2 core:
    two commuting lifts that each ensure their invariant compose to
    a lift that ensures both invariants.
*   `StructuralIntelligence.bayes_equals_boltzmann_with_reward_as_likelihood`
    — AA-2 core: the Bayesian posterior and Boltzmann update coincide
    pointwise once the reward plays the role of the likelihood.

Everything is proven in pure Lean 4 core (no `Mathlib`).  The analytic
step `(1 - 1/(cM))^N ≤ exp(-N/(cM))` and the resulting
`M · exp(-N/(cM)) ≤ ε` bound, the measure-theoretic lift of
Theorem 4 to conditional independence, the quantitative ε-covering
rate `N ≥ c · N_ε · ln(N_ε / ε_rel)` of Theorem 6, the Wald/BIC
probabilistic rate of CT-1, the AG-1 survival-probability bound, and
the naked `↔` form of TA-1 (which requires bijective chart transitions
or an auxiliary quotient) all require real analysis / measure theory
and are documented as future work in the package `README.md`.
-/

#print axioms StructuralIntelligence.theorem5_union_bound
#print axioms StructuralIntelligence.theorem5_deterministic_lower_bound
#print axioms StructuralIntelligence.coupon_collector_pigeonhole
#print axioms StructuralIntelligence.countP_anyFin_le_sumFin_countP
#print axioms StructuralIntelligence.commonSuffScreen_refines
#print axioms StructuralIntelligence.commonSuffScreen_coarsest
#print axioms StructuralIntelligence.commonSuffScreen_eq_jointTaskQuotient_iff
#print axioms StructuralIntelligence.refinement_transitive
#print axioms StructuralIntelligence.refinement_preserves_screen
#print axioms StructuralIntelligence.identifiability_implies_unique_by_witness
#print axioms StructuralIntelligence.identifiability_isolates_theta_star
#print axioms StructuralIntelligence.psi_equiv_preserves_under_context
#print axioms StructuralIntelligence.messageQuotient_is_common_sufficient
#print axioms StructuralIntelligence.messageQuotient_is_coarsest
#print axioms StructuralIntelligence.intersection_is_common_sufficient
#print axioms StructuralIntelligence.intersection_is_coarsest_over_family
#print axioms StructuralIntelligence.pareto_set_is_antichain
#print axioms StructuralIntelligence.pareto_contains_css_when_zero_sufficiency
#print axioms StructuralIntelligence.viability_inherited_by_superset
#print axioms StructuralIntelligence.cocycle_implies_gluing
#print axioms StructuralIntelligence.injective_gluing_implies_cocycle
#print axioms StructuralIntelligence.independent_lifts_compose_ensures
#print axioms StructuralIntelligence.independent_lifts_compose
#print axioms StructuralIntelligence.bayes_equals_boltzmann_with_reward_as_likelihood
