import StructuralIntelligence.Basic
import StructuralIntelligence.UnionBound
import StructuralIntelligence.Pigeonhole
import StructuralIntelligence.CouponCollector
import StructuralIntelligence.CommonSuffScreen
import StructuralIntelligence.Refinement
import StructuralIntelligence.CompilerTomography

/-!
# Structural Intelligence — Lean 4 formalisation

The Lean-checked ingredients of Theorems 4, 5 and 6-core of the
*Structural Intelligence* paper (`papers/structural_intelligence/paper.md`)
plus the CT-1 core of the *Compiler Tomography* companion paper
(`papers/compiler_tomography/paper.md`):

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

Everything is proven in pure Lean 4 core (no `Mathlib`).  The analytic
step `(1 - 1/(cM))^N ≤ exp(-N/(cM))` and the resulting
`M · exp(-N/(cM)) ≤ ε` bound, the measure-theoretic lift of
Theorem 4 to conditional independence, the quantitative ε-covering
rate `N ≥ c · N_ε · ln(N_ε / ε_rel)` of Theorem 6, and the
Wald/BIC probabilistic rate of CT-1, all require real analysis /
measure theory and are documented as future work in the package
`README.md`.
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
