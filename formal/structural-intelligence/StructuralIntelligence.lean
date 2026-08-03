import StructuralIntelligence.Basic
import StructuralIntelligence.UnionBound
import StructuralIntelligence.Pigeonhole
import StructuralIntelligence.CouponCollector
import StructuralIntelligence.CommonSuffScreen

/-!
# Structural Intelligence — Lean 4 formalisation

The Lean-checked ingredients of Theorems 4 and 5 of the *Structural
Intelligence* paper (`papers/structural_intelligence/paper.md`):

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

Everything is proven in pure Lean 4 core (no `Mathlib`).  The analytic
step `(1 - 1/(cM))^N ≤ exp(-N/(cM))` and the resulting
`M · exp(-N/(cM)) ≤ ε` bound, together with the measure-theoretic
lift of Theorem 4 to conditional independence, require real analysis /
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
