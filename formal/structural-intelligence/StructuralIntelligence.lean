import StructuralIntelligence.Basic
import StructuralIntelligence.UnionBound
import StructuralIntelligence.Pigeonhole
import StructuralIntelligence.CouponCollector
import StructuralIntelligence.CommonSuffScreen
import StructuralIntelligence.Refinement
import StructuralIntelligence.CompilerTomography
import StructuralIntelligence.Compiler.SquaringSeparation
import StructuralIntelligence.CausalSemantics
import StructuralIntelligence.Antecedents
import StructuralIntelligence.AbstractionFrontier
import StructuralIntelligence.AlignmentGovernance
import StructuralIntelligence.TheoryAtlas
import StructuralIntelligence.RepresentationRepair
import StructuralIntelligence.AutocatalyticArtwork
import StructuralIntelligence.DeleteRepair
import StructuralIntelligence.EmlZeroIdentity
import StructuralIntelligence.KappaCheap
import StructuralIntelligence.KappaScreen
import StructuralIntelligence.KappaUnique
import StructuralIntelligence.KappaRelabel
import StructuralIntelligence.Aff13
import StructuralIntelligence.DiamondInterval
import StructuralIntelligence.SurgeryMiss
import StructuralIntelligence.DtaN4
import StructuralIntelligence.SwapTyped
import StructuralIntelligence.MenuBlind
import StructuralIntelligence.GeneratorBorder
import StructuralIntelligence.ConcernChoice
import StructuralIntelligence.CrossingUnique
import StructuralIntelligence.SilentSubstitution
import StructuralIntelligence.MeaningVsCompany
import StructuralIntelligence.WeakestAdequate
import StructuralIntelligence.KleisliSection
import StructuralIntelligence.DialZero
import StructuralIntelligence.EmlCatalan
import StructuralIntelligence.RepairTable
import StructuralIntelligence.ObstructionTaxonomy

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
*   `StructuralIntelligence.Compiler.SquaringSeparation.squaring_separation`
    — US-2/US-3 kernel: `x^(2^n)` has Mul-tree size `2^{n+1}-1`,
    Sq-tower size `n+1`, and sharing-circuit size `n`.
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
*   `StructuralIntelligence.DeleteRepair.symmetry_mismatch_nogo` —
    delete–repair core: an invariant screen cannot factor a
    non-invariant target (over-invariance no-go).
*   `StructuralIntelligence.DeleteRepair.cycle_integrates_iff_sum_zero`
    — a closed walk of relative steps exists iff the steps sum to 0.
*   `StructuralIntelligence.DeleteRepair.potentials_unique_up_to_translation`
    — two discrete integrals of the same step field differ by a constant.
*   `StructuralIntelligence.DeleteRepair.repair_splits_disagreement`
    — exact repair must split leftover fibre disagreement.
*   `StructuralIntelligence.DeleteRepair.repair_paths_disagree`
    — delete-then-default and relative-then-drop disagree on a finite witness.
*   `StructuralIntelligence.EmlZeroIdentity.ExpLn.eml_zero_identity`
    — EML zero witness: `eml(a, eml(eml(a,1),1)) = 0` from
    `eml(a,b) := exp(a)-ln(b)` plus `ln∘exp` / `exp∘ln` cancellation.
    No `Real`, no `Float`, no `Complex.log`.
*   `StructuralIntelligence.KappaCheap.kappa_cheap_not_function`
    — Paper F: the cheap 5-field signature is not a function to gold.
*   `StructuralIntelligence.KappaScreen.kappa_screen_hits_suite`
    — Paper F: κ_screen equals gold on the registered 11-row suite.
    Cites CommonSuffScreen; adds only a named total order.
*   `StructuralIntelligence.KappaUnique.bag_not_unique`
    — Paper F: `bag` has five representing menu screens.
*   `StructuralIntelligence.KappaRelabel.kappa_relabel_natural`
    — Paper F: bit swap `0↔3` sends first_bit/q_stab0 to last_bit/q_stab_last.
*   `StructuralIntelligence.Aff13.affine_escapes_kirchhoff`
    — Paper C: Aff(1, Z/3) holonomy is not integer Kirchhoff.
*   `StructuralIntelligence.DiamondInterval.poset_not_determine_interval`
    — Paper D: two diamond embeddings, same poset, different `s²`.
*   `StructuralIntelligence.SurgeryMiss.surgery_miss_pair_eq`
    — Paper E: cheap `decide` says quotient on `pair_eq`/`q_id`; gold is noop.
*   `StructuralIntelligence.MenuBlind.menu_blind_kappa_impossible`
    — Door 1: gold flips between the base and extended menus on
    `pair_eq`/`q_id`, so no function of (task, screen, edges) matches
    gold under both.  With `gold_flip_pair_eq`, `gold_flip_pair23`,
    `base_gold_consistent`, `screen_exact_on_flip_rows`.
*   `StructuralIntelligence.GeneratorBorder.generator_border_sq`,
    `StructuralIntelligence.GeneratorBorder.generator_border_cube`
    — Door 2: exhaustive kernel enumerations of both generator
    episodes (9 vs 89 trees at bound 7, 4 vs 17 at bound 5); min
    formula size moves (7 vs 3, 5 vs 2) while denotation/size/depth
    are grammar-free; `min_size_not_shared_function` is the two-point
    separation.
*   `StructuralIntelligence.ConcernChoice.boundary_base`,
    `StructuralIntelligence.ConcernChoice.boundary_ext`
    — Door 3: the six registered concern choices (four distinct
    screens, mirrored duals), the strict sum-gap 21 over the
    concern-free choice, and both dials exact on the k/54 grid:
    base crosses at k = 22 (ε = 11/27), extended at k = 14
    (ε = 7/27) — the concern boundary is menu-relative.
*   `StructuralIntelligence.CrossingUnique.crossing_unique`
    — the door-3 dial has exactly one tie point on the registered
    grid (k = 22).  Proved by an autonomous Lea run and ported
    verbatim; verified twice (Lea `/verify` and the 4.29 replay).
*   `StructuralIntelligence.MeaningVsCompany.*` — the §7 sting of
    the intention essay on the registered six-message world: the
    meaning quotient (Ψ-classes, instantiating `CausalSemantics`)
    and the co-occurrence quotient are incomparable partitions —
    `neither_partition_refines_the_other`, with the transported
    forms `company_does_not_refine_meaning` and
    `meaning_does_not_refine_company`.
*   `StructuralIntelligence.WeakestAdequate.*` — review item 1 on
    the intention essay's D13: `no_largest_adequate` (no adequate
    region contains all adequate regions; general, not enumeration),
    `maximal_not_unique`, and the constructive repair
    `greedy_repair_works` / `greedy_depends_on_order` — selection
    needs a disclosed order, the κ_screen lesson transported.
*   `StructuralIntelligence.KleisliSection.*` — the categorical
    reading at its earned grade: sections of a quotient are
    specification-level indistinguishable
    (`sections_spec_indistinguishable`), the section space is closed
    under fiberwise replacement (`section_swap`), and the registered
    2×2 witness carries exactly four sections with one shadow.
*   `StructuralIntelligence.SilentSubstitution.*` — the intention
    essay's central kernel (P10): `tilt_monotone` (Theorem D's finite
    Chebyshev core — one ecology step weakly raises expected reward
    over any finite region, any monotone tilt; the two algebraic
    lemmas beneath it were proved by an autonomous Lea run),
    `monitor_constant` (Lemma L1, axiom-free: spec-level monitors are
    constant on a compliance class), and the registered opposed-reward
    witness where expected reward strictly rises while principal value
    strictly falls (axiom-free).
*   `StructuralIntelligence.DialZero.*` — Theorem B's D = 0 clause:
    the level-set partition of the task law has zero task-distortion
    (`levelCells_zero_distortion`), every zero-distortion encoder
    refines it (`zero_distortion_cell_in_level`), and on the
    registered witness no two-cell partition qualifies
    (`no_coarser_on_witness`).
*   `StructuralIntelligence.EmlCatalan.*` — Wave-7 EML censuses:
    the constant grammar's shells carry Catalan counts `C_0..C_6`
    (`emlFib_counts`, 197 trees), the variable grammar's carry
    `2^(k+1)·C_k` for `k = 0..5` (`emlVar_counts`, 3238 trees,
    single-pass bucket fold), and the size-2 pair is same-size,
    distinct, and separated by the registered `Nat` model of the
    `ExpLn` fragment (`eml_pair_diff`, with the carrier-general
    derivations `left_denotes` / `right_denotes`).
*   `StructuralIntelligence.RepairTable.*` — Theorem RR-1 on the
    eight registered witness worlds (`rr1_table_well_defined`):
    each canonical row's broken rep misses its invariant, the lift
    captures it (functional factorisation), and the lift is minimal
    over every nonempty drop-set of added components — all kernel
    `decide` at registered sizes (6–16 states, no reductions).
*   `StructuralIntelligence.ObstructionTaxonomy.*` — Theorem TA-2's
    discrete taxonomy: the rank/support classifier is total,
    mutually exclusive, and exhaustive (`taxonomy_trichotomy`),
    tracks the paper's defining conditions on every finite chart
    world (`classify_conditions`), and assigns `glue` / `boundary` /
    `missingLatent` correctly to the three registered worlds
    (`ta2_taxonomy_classifies`).  Enlargement-existence (the
    universal-cover analogue) stays withheld, as in the paper.

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
#print axioms StructuralIntelligence.Compiler.SquaringSeparation.squaring_separation
#print axioms StructuralIntelligence.Compiler.SquaringSeparation.conservative_extension
#print axioms StructuralIntelligence.Compiler.SquaringSeparation.circuit_pow2_needs_n_steps
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
#print axioms StructuralIntelligence.DeleteRepair.symmetry_mismatch_nogo
#print axioms StructuralIntelligence.DeleteRepair.cycle_integrates_iff_sum_zero
#print axioms StructuralIntelligence.DeleteRepair.potentials_unique_up_to_translation
#print axioms StructuralIntelligence.DeleteRepair.repair_splits_disagreement
#print axioms StructuralIntelligence.DeleteRepair.repair_paths_disagree
#print axioms StructuralIntelligence.EmlZeroIdentity.ExpLn.eml_zero_identity
#print axioms StructuralIntelligence.EmlZeroIdentity.ExpLn.eml_zero_identity_one
#print axioms StructuralIntelligence.EmlZeroIdentity.ExpLn.eml_zero_identity_x
#print axioms StructuralIntelligence.KappaCheap.kappa_cheap_not_function
#print axioms StructuralIntelligence.KappaScreen.kappa_screen_hits_suite
#print axioms StructuralIntelligence.DtaN4.dta_n4_representable_iff
#print axioms StructuralIntelligence.SwapTyped.swap_typed_wins
#print axioms StructuralIntelligence.KappaUnique.bag_not_unique
#print axioms StructuralIntelligence.KappaRelabel.kappa_relabel_natural
#print axioms StructuralIntelligence.Aff13.affine_escapes_kirchhoff
#print axioms StructuralIntelligence.DiamondInterval.poset_not_determine_interval
#print axioms StructuralIntelligence.SurgeryMiss.surgery_miss_pair_eq
#print axioms StructuralIntelligence.MenuBlind.menu_blind_kappa_impossible
#print axioms StructuralIntelligence.MenuBlind.gold_flip_pair_eq
#print axioms StructuralIntelligence.GeneratorBorder.generator_border_sq
#print axioms StructuralIntelligence.GeneratorBorder.generator_border_cube
#print axioms StructuralIntelligence.GeneratorBorder.min_size_not_shared_function
#print axioms StructuralIntelligence.ConcernChoice.boundary_base
#print axioms StructuralIntelligence.ConcernChoice.boundary_ext
#print axioms StructuralIntelligence.ConcernChoice.mirrored_dual_ext
#print axioms StructuralIntelligence.CrossingUnique.crossing_unique
#print axioms StructuralIntelligence.SilentSubstitution.tilt_monotone
#print axioms StructuralIntelligence.SilentSubstitution.monitor_constant
#print axioms StructuralIntelligence.SilentSubstitution.silent_substitution_witness
#print axioms StructuralIntelligence.MeaningVsCompany.neither_partition_refines_the_other
#print axioms StructuralIntelligence.MeaningVsCompany.company_does_not_refine_meaning
#print axioms StructuralIntelligence.WeakestAdequate.no_largest_adequate
#print axioms StructuralIntelligence.WeakestAdequate.greedy_depends_on_order
#print axioms StructuralIntelligence.KleisliSection.sections_spec_indistinguishable
#print axioms StructuralIntelligence.KleisliSection.section_swap
#print axioms StructuralIntelligence.DialZero.zero_distortion_cell_in_level
#print axioms StructuralIntelligence.DialZero.no_coarser_on_witness
#print axioms StructuralIntelligence.EmlCatalan.emlFib_counts
#print axioms StructuralIntelligence.EmlCatalan.emlVar_counts
#print axioms StructuralIntelligence.EmlCatalan.eml_pair_diff
#print axioms StructuralIntelligence.RepairTable.rr1_table_well_defined
#print axioms StructuralIntelligence.ObstructionTaxonomy.taxonomy_trichotomy
#print axioms StructuralIntelligence.ObstructionTaxonomy.ta2_taxonomy_classifies
#print axioms StructuralIntelligence.ObstructionTaxonomy.classify_conditions
