# Structural Intelligence Lean 4 Proofs

Machine-checked artifact for the algebraic cores of Theorems 4
(Cross-task stability, conditional), 5 (discrete learnability) and
6 (ε-covering reduction) of the *Structural Intelligence* paper
(`papers/structural_intelligence/paper.md`), the identifiability
core of Theorem CT-1 (MDL identification) of the *Compiler
Tomography* companion paper (`papers/compiler_tomography/paper.md`),
and the algebraic cores of nine further theorems (CS-1, CS-2, SA-1,
AF-1, AF-2, AG-2, TA-1 (two halves), RR-2, AA-2) spanning the
remaining Structural-Intelligence companion papers.

## What is formalized

### Theorem 4 (algebraic core) — `StructuralIntelligence/CommonSuffScreen.lean`

- `StructuralIntelligence.commonSuffScreen_refines` — the **Functional
  Common-Sufficient Screen** theorem.  Given a candidate quotient
  `q : X → Z` such that every task in a family
  `Y : ∀ α : A, X → Yfam α` factors through `q` (there is
  `h_α : Z → Yfam α` with `Y α = h_α ∘ q`), any two inputs
  `x, x'` with `q x = q x'` satisfy `Y α x = Y α x'` for every
  task index `α`.  Equivalently, `~_q` refines `~_Y`.
  This is Theorem 4's mechanism-of-action in its purely functional
  form; the probability-space conclusion
  `Y_α ⟂ Y_β | q(X)` reduces to it via the standard fact that
  `σ(q)`-measurable functions are exactly the `q`-fibre-constant
  functions.  Proof strategy: unfold the factorisation on each side of
  `hq : q x = q x'` and `rw`.  Depends on **no axioms**.
- `StructuralIntelligence.jointTaskQuotient` — the canonical common
  sufficient screen `q_Y : X → (∀ α, Yfam α)` sending `x` to
  `(α ↦ Y α x)`.  Every task factors through `q_Y` via the α-th
  projection.
- `StructuralIntelligence.commonSuffScreen_coarsest` — **coarsest
  common-sufficient-statistic corollary.**  If `q` satisfies both the
  factoring hypothesis and the converse
  `(∀ α, Y α x = Y α x') → q x = q x'`, then for any other common
  sufficient screen `q'`, agreement under `q'` implies agreement under
  `q`.  Depends on **no axioms**.
- `StructuralIntelligence.commonSuffScreen_eq_jointTaskQuotient_iff` —
  two-form of the corollary: `q`'s equivalence relation is exactly the
  joint-task equivalence relation.

### Theorem 5 — union bound + pigeonhole

- `StructuralIntelligence.theorem5_union_bound` — the counting form of
  the union bound.  For any list `L : List α` and predicate family
  `P : Fin M → α → Bool`,
  `L.countP (∃ i, P i x)  ≤  Σ_{i : Fin M} L.countP (P i)`.
  This is the Theorem 5 step
  `Pr[some fibre missed] ≤ Σᵢ Pr[fibre i missed]` in counting form
  (division by `|L|` to move to probabilities is a triviality).
- `StructuralIntelligence.theorem5_deterministic_lower_bound` — the
  coupon-collector pigeonhole.  For `N < M`, every sample sequence
  `f : Fin N → Fin M` misses at least one class:
  `∃ i, ∀ j, f j ≠ i`.  This is the deterministic zero-probability
  regime of the coupon-collector bound (no algorithm can recover an
  `M`-element partition from fewer than `M` observations).
- `StructuralIntelligence.coupon_collector_pigeonhole` — the
  contrapositive: if `f : Fin N → Fin M` covers `Fin M`, then `M ≤ N`.
- Supporting lemmas: `sumFin`/`anyFin` over `Fin M`, the pointwise
  indicator union bound, the counting identity
  `Σ_{i : Fin M} count i L = L.length`, and the "sum-of-indicators
  equals one" lemma.

### Theorem 6 (algebraic core) — `StructuralIntelligence/Refinement.lean`

- `StructuralIntelligence.Refines` — refinement of binary relations,
  `Refines P₁ P₂ := ∀ a b, P₂ a b → P₁ a b`.  In partition terms,
  `P₂` (the second argument) is at-least-as-fine as `P₁`.
- `StructuralIntelligence.refinement_transitive` — refinement is
  transitive.  Depends on **no axioms**.
- `StructuralIntelligence.refinement_preserves_screen` — the
  **Refinement-reduction** theorem, algebraic content of Theorem 6
  (§2.5b of the paper).  If `q₁ : X → Z₁` is a common sufficient
  screen for a task family and `q₂ : X → Z₂` refines `q₁` in the
  functional sense that `q₁ = r ∘ q₂` for some `r : Z₂ → Z₁`, then
  `q₂` is also a common sufficient screen.  Proof: composition
  (`Y α = h ∘ q₁ = h ∘ r ∘ q₂`).  Depends on **no axioms**.
- `StructuralIntelligence.refinement_preserves_screen_qRel` —
  companion at the relational level: under the same factorisation
  hypothesis, the fibre equivalence of `q₂` refines that of `q₁`.

  This is the direction of composition; the quantitative ε-covering
  rate `N ≥ c · N_ε · ln(N_ε / ε_rel)` needs real logs and is out
  of scope (see *What is not formalized*).

### Squaring separation (US-2 / US-3 core) — `StructuralIntelligence/Compiler/SquaringSeparation.lean`

- `MulTree` / `SqTree` — full binary multiplication trees, and the
  same language with a definable unary `sq`.
- `MulTree.size_succ_eq_two_mul_degree` — `size + 1 = 2 * degree`.
- `SqTree.sqTower_size` / `sqTower_degree` — `sq^n(x)` has size
  `n+1` and degree `2^n`.
- `SqTree.expand_degree` — expanding `sq(t) = t × t` preserves
  degree (conservative extension of denotations).
- `circuitMaxDegree_le_pow2` — a sharing circuit of `k` steps has
  max degree `≤ 2^k`.
- `StructuralIntelligence.Compiler.SquaringSeparation.squaring_separation`
  — combined headline: same degree `2^n`, Mul size `2^{n+1}-1`,
  Sq size `n+1`, circuit size `n`.  Uses `propext, Quot.sound`
  (via `omega` / list lemmas).  The necessity half
  `circuit_pow2_needs_n_steps` additionally uses `Classical.choice`.
  Kernel-checked on Lean 4.31; zero `sorry`.

  Catalan counts and Gibbs fiber masses are the Python instrument
  `experiments/squaring_separation`, not this file.

### EML zero identity — `StructuralIntelligence/EmlZeroIdentity.lean`

- `StructuralIntelligence.EmlZeroIdentity.ExpLn` — Mathlib-free
  exp/ln/subtraction fragment.  Class fields are the explicit
  hypotheses `ln(exp x)=x`, `Pos x → exp(ln x)=x`, `exp 0 = 1`,
  `Pos(exp x)`, `x-0=x`, and `x-x=0`.  Not environment `axiom`s.
- `eml a b := exp a - ln b` — Odrzywołek's operator as a definition.
- `ln_one` / `eml_right_one` / `eml_eml_right_one` — the rewrite
  `ln 1 = 0`, `eml(a,1)=exp(a)`, `eml(eml(a,1),1)=exp(exp(a))`.
- `middle_pos` / `exp_ln_middle` — the middle argument is in the
  image of `exp`, so `ln 0` is off the path (Paper 0 is not used).
- `StructuralIntelligence.EmlZeroIdentity.ExpLn.eml_zero_identity`
  — **headline.**  `eml(a, eml(eml(a,1),1)) = 0` for any carrier
  element `a`.  Depends on **no axioms**.
- `eml_zero_identity_one` / `eml_zero_identity_x` — the two
  registered leaves `a = 1` and `a = x`.  Also axiom-free.

  Not claimed: a construction of `ℝ`, a proof that the usual real
  `exp`/`ln` inhabit `ExpLn`, or identity of functions from a
  numerical grid.

### Compiler-Tomography CT-1 core — `StructuralIntelligence/CompilerTomography.lean`

- `StructuralIntelligence.IsIdentifiable` — a deterministic-support
  compiler family `K : Θ → S → X → Bool` is identifiable if every
  pair `θ ≠ θ'` disagrees on some `(s, x)`.
- `StructuralIntelligence.ConsistentWith`,
  `StructuralIntelligence.RefutedBy` — a parameter is consistent
  with the data when it agrees with the truth on every observed
  pair; refuted when some observed pair witnesses a disagreement.
- `StructuralIntelligence.not_consistent_iff_refuted` — the two
  notions are logical negations.
- `StructuralIntelligence.identifiability_implies_unique_by_witness`
  — **CT-1 core**: if every wrong `θ ≠ θ*` is refuted by the data
  set `D`, then `θ*` is the unique parameter consistent with `D`,
  i.e., `ConsistentWith K θ* D θ ↔ θ = θ*`.  This is what makes the
  MDL argmin (over zero-training-error hypotheses) identify `θ*`
  uniquely.  Uses `propext, Classical.choice, Quot.sound`.
- `StructuralIntelligence.identifiability_yields_refuting_data` —
  constructive companion: for any listing of candidate parameters,
  identifiability lets us build a data set that refutes every
  wrong `θ` in the list.
- `StructuralIntelligence.identifiability_isolates_theta_star` —
  full form: for any finite list of candidates, identifiability
  yields a data set on which the consistent parameters are exactly
  `{θ*}` — the algebraic content of CT-1 identification.

  The passage from "eventually every wrong `θ` is refuted" to the
  probabilistic MDL rate `O(√(log N / N))` needs concentration +
  KL positivity + real logs and is left to `Mathlib` (see *What is
  not formalized*).

### Causal Semantics CS-1 core — `StructuralIntelligence/CausalSemantics.lean`

- `StructuralIntelligence.PsiEquiv` — Ψ-equivalence:
  `PsiEquiv psi m₁ m₂ ↔ ∀ c, psi m₁ c = psi m₂ c`.
- `psiEquiv_refl`, `psiEquiv_symm`, `psiEquiv_trans` — Ψ-equivalence is
  an equivalence relation (three one-line lemmas).  Depend on
  **no axioms**.
- `StructuralIntelligence.psi_equiv_preserves_under_context` — **CS-1
  core**: Ψ-equivalent messages yield the same list of context-slot
  values under any list of contexts,
  `cs.map (psi m₁) = cs.map (psi m₂)`.  Proof: list induction on
  `cs`.  Depends on **no axioms**.

### Causal Semantics CS-2 core — same file

- `StructuralIntelligence.MessageQuotient`,
  `StructuralIntelligence.messageQuotientMap` — the message
  quotient, definitionally `PsiEquiv`, together with its canonical
  map `M → (C → D)`.
- `StructuralIntelligence.messageQuotient_is_common_sufficient` —
  every context slot of `psi` factors through
  `messageQuotientMap psi` (definitional).  No axioms.
- `StructuralIntelligence.messageQuotientMap_eq_iff` — the
  induced equivalence relation of `messageQuotientMap psi` is
  exactly `PsiEquiv psi`.
- `StructuralIntelligence.messageQuotient_is_coarsest` — **CS-2
  core**: any other message screen `q : M → Q` in the "sufficient
  direction" (`q m₁ = q m₂ → PsiEquiv m₁ m₂`) refines the Ψ-equivalence
  relation, i.e., `Refines (PsiEquiv psi) (qRel q)`.  Depends on
  **no axioms**.

### Antecedent Taxonomy SA-1 core — `StructuralIntelligence/Antecedents.lean`

- `StructuralIntelligence.IntersectionScreen` — the intersection
  screen of a family `q : ∀ u : U, X → Z u`:
  `IntersectionScreen q x₁ x₂ ↔ ∀ u, q u x₁ = q u x₂`.
- `intersection_refines_each` — the intersection screen refines
  every family member.  Definitional.
- `StructuralIntelligence.LocallySufficient` — a task family is
  locally sufficient for `{q u}` if every task is determined by
  *some* family member.
- `StructuralIntelligence.intersection_is_common_sufficient` —
  **SA-1 core**: local sufficiency + intersection agreement implies
  every task agrees.  Depends on **no axioms**.
- `StructuralIntelligence.intersection_is_coarsest_over_family` —
  **SA-1 coarsest corollary**: any competing screen `q'` that
  captures every `q u` refines the intersection screen.  Depends on
  **no axioms**.

### Abstraction Frontier AF-1 and AF-2 core — `StructuralIntelligence/AbstractionFrontier.lean`

- `StructuralIntelligence.Dominates` — componentwise `≤` on every
  axis + strict `<` on some axis; axes modelled as `Fin n → Nat`
  (integer proxies for real axes; lower is better).
- `StructuralIntelligence.IsPareto` — no quotient dominates.
- `StructuralIntelligence.pareto_set_is_antichain` — **AF-1 core**:
  two Pareto-optimal quotients cannot dominate each other; direct
  from the definition of `IsPareto`.  Depends on **no axioms**.
- `StructuralIntelligence.pareto_contains_css_when_zero_sufficiency`
  — **AF-2 core** (two-axis static case): any `q*` with zero task-
  insufficiency (axis `0`) that minimises coding cost (axis `1`)
  among common sufficient screens is Pareto.  Uses `[propext,
  Quot.sound]` (via `omega` closing the impossible index case for
  `Fin 2`).

### Alignment Governance AG-2 core — `StructuralIntelligence/AlignmentGovernance.lean`

- `StructuralIntelligence.ValidTrajectory` — a length-`T` path
  `Fin (T+1) → Z` is `viable`-valid iff every visited state is
  viable.
- `StructuralIntelligence.viability_inherited_by_superset` — **AG-2
  core**: enlarging the viability set (`V ⊆ V'`) preserves
  trajectory validity.  One-line proof, no axioms.
- `StructuralIntelligence.viability_valid_ext` — pointwise equality
  of viability predicates yields identical valid-trajectory sets.

  The **quantitative** AG-2 (probability of survival under a
  probabilistic transition kernel) requires real-valued measures and
  is out of scope for the Lean-core artifact.

### Theory Atlas TA-1 core — `StructuralIntelligence/TheoryAtlas.lean`

- `StructuralIntelligence.CocycleHolds` — the chart-transition
  cocycle: `T j k (T i j q) = T i k q`.
- `StructuralIntelligence.GluesTransitions` — a family `M` glues
  transitions if `M j (T i j q) = M i q`.
- `StructuralIntelligence.Injective` — local injectivity predicate
  (avoids importing Mathlib).
- `StructuralIntelligence.cocycle_implies_gluing` — **TA-1 forward
  direction**: from cocycle + inhabited chart index, the family
  `M i q := T i default q` glues the transitions and satisfies the
  canonical-chart idempotency `M default (M i q) = M i q`.  No
  axioms.
- `StructuralIntelligence.injective_gluing_implies_cocycle` — **TA-1
  reverse direction (under injectivity)**: any gluing family with
  injective components forces the cocycle to hold.  Proof: apply
  injectivity to `M k (T j k (T i j q)) = M k (T i k q)`.  No
  axioms.

  **Weakening from the paper's TA-1 ↔.**  The naked biconditional
  as stated in the paper is not provable in pure core: the trivial
  constant family `M := fun _ _ => q₀` satisfies the gluing equation
  and idempotency for any `q₀ : Q`, without forcing the cocycle.
  The honest content of TA-1 is the two-halves formulation above
  (forward direction always; reverse direction under injective
  components on the gluing family).  Recovering the full ↔ requires
  either bijective chart transitions or an auxiliary quotient
  construction, both beyond the pure-Lean-core scope.

### Representation Repair RR-2 core — `StructuralIntelligence/RepresentationRepair.lean`

- `StructuralIntelligence.LiftRepairs` — a lift repairs invariant
  `I` if it makes previously-broken representations capture `I`.
- `StructuralIntelligence.Preserves` — a lift preserves `I` if it
  never breaks existing captures.
- `StructuralIntelligence.LiftEnsures` — a lift ensures `I` if it
  always produces something capturing `I`.
- `StructuralIntelligence.Independent` — two lifts commute.
- `StructuralIntelligence.liftEnsures_of_repairs_preserves` —
  repair + preservation = ensures.  Uses `[propext, Classical.choice,
  Quot.sound]` (via `by_cases` on `captures r I`).
- `StructuralIntelligence.independent_lifts_compose_ensures` —
  **RR-2 core (strong form)**: two commuting lifts that each ensure
  their invariant compose to a lift that ensures both invariants.
  Depends on **no axioms**.
- `StructuralIntelligence.independent_lifts_compose` — **RR-2 core
  (RR form)**: two independent lifts, each repairing and preserving
  its invariant, compose to a lift repairing both.  Uses
  `[propext, Classical.choice, Quot.sound]` (via the strong form
  and case-split on captures).

  The pure `LiftRepairs`-only hypothesis is not enough: if `lift₂`
  breaks `I₁` on an input that captures it, no amount of
  independence with `lift₁` will save it (because `lift₁` only
  repairs *broken* `I₁`).  The paper implicitly assumes
  preservation, as is standard in belief-revision literature; the
  formalisation makes that hypothesis explicit.

### Autocatalytic Artwork AA-2 core — `StructuralIntelligence/AutocatalyticArtwork.lean`

- `StructuralIntelligence.bayesPosterior`,
  `StructuralIntelligence.boltzmannUpdate` — unnormalised Bayesian
  and Boltzmann update operators on `Nat`-valued weight functions
  `Θ → Nat` (using `Nat` in place of `ℝ` since proportionality is
  what matters; the extension to real-valued weights is orthogonal).
- `StructuralIntelligence.bayes_equals_boltzmann_with_reward_as_likelihood`
  — **AA-2 core**: the two update operators coincide pointwise once
  the reward plays the role of the likelihood.  By `rfl`.  No
  axioms.
- `StructuralIntelligence.bayesPosterior_eq_boltzmannUpdate` —
  function-level identity (not just pointwise).  Also by `rfl`.

### No `sorry`s

Every checked-in proof compiles fully; there are no `sorry`s anywhere
in the package.  `commonSuffScreen_refines`,
`commonSuffScreen_coarsest`, `refinement_transitive` and
`refinement_preserves_screen` depend on no axioms at all;
`commonSuffScreen_eq_jointTaskQuotient_iff` uses only `Quot.sound`
(via `funext` on the joint task quotient).  The
CT-1-core headlines depend on the standard `propext,
Classical.choice, Quot.sound` triple (used only for
`Classical.byContradiction` in the uniqueness step; no compiler-
family-specific axiom is added).

## What is *not* formalized

- The analytic amplification of Theorem 5:
  - `(1 - 1/(cM))^N ≤ exp(-N/(cM))` for real `c, M`;
  - `M · exp(-N/(cM)) ≤ ε` whenever `N ≥ cM · ln(M/ε)`.
  Both statements need real numbers, `exp`, and `log`, none of which
  live in the Lean 4 core library.  A `Mathlib`-based amplification is
  a natural follow-up and would live in a separate sub-package so as
  not to blow the 15-minute CI budget with a fresh `Mathlib` build.
- The **measure-theoretic lift of Theorem 4**.  What is formalised
  here is Theorem 4's algebraic core (`commonSuffScreen_refines`): if
  every task factors through `q`, then `q x = q x'` forces every task
  to agree at `x, x'`.  Promoting this to
  `Y_α ⟂ Y_β ∣ σ(q(X))` for measurable `q` requires
  σ-algebras, conditional probability, and independence of σ-algebras
  — all mathlib territory, out of scope for the Lean-core artifact.
  The passage is standard: σ(q)-measurable functions are exactly the
  q-fibre-constant functions, so once every task is q-fibre-constant
  (which is what `commonSuffScreen_refines` says at the pointwise
  level), the conditional distribution of each task given `σ(q)` is a
  point mass, hence independent of anything else.
- The **quantitative rate of Theorem 6**.  What is formalised is the
  refinement-reduction *mechanism*: a common sufficient screen is
  preserved under functional refinement.  The quantitative
  ε-covering rate `N_ε = O((D_Z/ε)^{d_Z})` and the resulting sample
  complexity `N ≥ c · N_ε · ln(N_ε / ε_rel)` need real-valued
  metrics, covering numbers and logs — all mathlib territory.
- The **probabilistic MDL rate of CT-1**.  What is formalised is the
  *identifiability-implies-uniqueness* core: given a data set that
  refutes every wrong parameter, MDL/argmin lands uniquely on
  `θ*`.  Promoting "every wrong `θ` is eventually refuted with
  probability 1" to the Wald/Rissanen `O(√(log N / N))` total-
  variation rate requires KL divergence, concentration inequalities,
  and BIC bounds — all mathlib territory.
- **CT-2 (compiler-improvement monotonicity)**.  The reward-driven
  update `K_{t+1}(· | s) ∝ K_t(· | s) · exp(β · r(s, x))` and its
  non-decreasing expected reward statement rest on a Cov ≥ 0
  inequality that needs real analysis; not attempted here.
- Theorems 1, 2 and the continuous-case Corollary — these need
  additional real analysis / measure theory, all beyond the Lean 4
  core.
- The **quantitative half of AG-2** (survival probability under a
  probabilistic transition kernel).  What is formalised is the
  qualitative superset-inheritance: enlarging the viability set
  cannot invalidate any trajectory.  The probability that a Markov
  trajectory stays inside `V` for `T` steps needs real-valued
  measures and lives in Mathlib territory.
- The **naked `↔` form of TA-1** (cocycle exactly iff gluing, with
  no injectivity hypothesis).  What is formalised are both halves
  separately: cocycle ⟹ gluing (via canonical-chart projection),
  and injective-gluing ⟹ cocycle.  The naked biconditional is not
  provable without extra structure: the trivial constant family
  `M := fun _ _ => q₀` glues any `T` and is idempotent for free.
  Recovering the full ↔ needs either bijective transitions or an
  auxiliary quotient construction.
- The **`LiftRepairs`-only form of RR-2**.  What is formalised is
  the "ensures" form (repair + preserve → ensures both invariants
  compose under independence).  A pure `LiftRepairs`-only version
  is false without a preservation hypothesis, because either lift
  could break the other invariant on an input where it was already
  present; the paper implicitly assumes preservation, and the
  formalisation makes that hypothesis explicit.
- The **normalisation constant of AA-2** (Bayes ↔ Boltzmann on the
  actual probability simplex).  What is formalised is the pointwise
  identity of the two update operators on unnormalised weights
  (`Nat`-valued for pure-core provability).  Dividing by
  `Σ_θ μ(θ) · lik(θ)` to obtain a probability distribution is
  routine once real division is available (Mathlib).

### Delete–repair core — `StructuralIntelligence/DeleteRepair.lean`

The algebraic core of the delete–obstruction–repair argument: an
invariant screen cannot reconstruct a non-invariant target; relative
steps integrate on a path and close on a cycle iff they sum to zero;
two discrete integrals of the same step field differ by a constant;
exact repair must split leftover fibre disagreement; and the two
repair schedules (delete-then-default vs relative-then-drop) disagree
on a finite witness.

- `StructuralIntelligence.DeleteRepair.over_invariance_nogo` — if
  `q` is `act`-invariant and `target` is a postcomposition of `q`,
  then `target` is `act`-invariant.
- `StructuralIntelligence.DeleteRepair.symmetry_mismatch_nogo` —
  **headline.**  Contrapositive: an invariant screen cannot factor a
  target that moves under the action.  This is the group-action
  packaging of the `CommonSuffScreen` contrapositive, not a new
  logical primitive.  Depends on **no axioms**.
- `StructuralIntelligence.DeleteRepair.invariant_orbits_factor` —
  if `target` is invariant and every `q`-fibre is an orbit, then
  `target` factors through `q`.
- `StructuralIntelligence.DeleteRepair.identity_always_factors` —
  the identity screen always factors; leftover privilege is not a
  no-go.
- `StructuralIntelligence.DeleteRepair.path_integrates` — prefix
  potential after `i+1` steps is the potential after `i` plus the
  `i`-th relative step.
- `StructuralIntelligence.DeleteRepair.cycle_integrates_iff_sum_zero`
  — **headline.**  `prefixSum rs rs.length = 0` iff `sumInt rs = 0`.
  Uses `[propext]` (via `rw` of the prefix-sum identity through
  `↔`).  No custom axioms.
- `StructuralIntelligence.DeleteRepair.potentials_unique_up_to_translation`
  — **headline.**  Two discrete integrals of the same step field on
  `{0,…,n}` differ by the constant `p 0 - q 0`.  Uses `[propext]`.
  No custom axioms.
- `StructuralIntelligence.DeleteRepair.repair_splits_disagreement`
  — **headline.**  Exact repair of `qD` by `r` forces any leftover
  `target`-disagreement on a `qD`-fibre to be an `r`-disagreement.
  The counting form `|r`-values on the fibre` ≥ `|Y`-values on the
  fibre` is the discrete `H(R | q_D) ≥ H(Y | q_D)`; we bank the
  split, not Shannon entropy (no reals).  Depends on **no axioms**.
- `StructuralIntelligence.DeleteRepair.repair_paths_disagree` —
  **headline.**  Finite witness that delete-then-default (`pathA`)
  and relative-then-drop (`pathB`) disagree: `(0,1)` and `(1,1)`
  share a Path-A image but not a Path-B image.  This is
  "position then pool ≠ pool then position", not a relativity
  theorem.  Depends on **no axioms**.

  Not claimed: Shannon entropy inequalities, a measure-theoretic
  connection form, or any identification of the finite witness with
  special relativity.  The optional
  `integrates_implies_closed_walk_zero` lemma was skipped; the
  cycle-sum characterisation already records closed-walk vanishing.

## Design constraints

The `formal/relative-identifiability/` sister project runs on the
GitHub Actions `lean` job in ~90 seconds because it imports no
`Mathlib`.  We mirror that constraint here:

- `lean-toolchain` is pinned to `leanprover/lean4:v4.31.0` (identical
  to `formal/relative-identifiability/lean-toolchain`).
- `lakefile.toml` declares a single `lean_lib` and no external
  dependencies.
- The CI `lean` job is extended to build this package with the same
  15-minute timeout (see `.github/workflows/quality.yml`).

## Running the proofs

```bash
cd formal/structural-intelligence
lake build
```

`lake build` prints, via `#print axioms`, the axiom footprint of each
headline theorem.  The Theorem-5 headlines sit on standard axioms
(`propext`, `Quot.sound`, and — for the deterministic lower bound —
`Classical.choice`).  The Theorem-4-core headlines
`commonSuffScreen_refines` and `commonSuffScreen_coarsest`, together
with the Theorem-6-core headlines `refinement_transitive` and
`refinement_preserves_screen`, depend on **no axioms**;
`commonSuffScreen_eq_jointTaskQuotient_iff` uses only `Quot.sound`
(via a single `funext`).  The CT-1-core headlines
`identifiability_implies_unique_by_witness` and
`identifiability_isolates_theta_star` use the standard
`propext, Classical.choice, Quot.sound` triple (for the classical
"either `θ = θ*` or the data refutes `θ`" case split).

The CS-1/CS-2, SA-1, AF-1, AG-2, TA-1, RR-2-ensures, and AA-2 core
headlines depend on **no axioms**.  `pareto_contains_css_when_zero_sufficiency`
uses `[propext, Quot.sound]` (via `omega` closing the impossible
`Fin 2` index case).  `independent_lifts_compose` (RR-2 form) uses
`[propext, Classical.choice, Quot.sound]` (via `by_cases` on
`captures r I`).  The squaring-separation headline
`squaring_separation` uses `[propext, Quot.sound]`;
`circuit_pow2_needs_n_steps` uses the standard
`propext, Classical.choice, Quot.sound` triple.  A full clean build
(post-toolchain-download) takes ~3 seconds.

## Files

- `StructuralIntelligence.lean` — top-level module, re-exports and
  `#print axioms` checks.
- `StructuralIntelligence/Basic.lean` — `sumFin` / `anyFin` utilities.
- `StructuralIntelligence/UnionBound.lean` — pointwise and counting
  union bound (`theorem5_union_bound`).
- `StructuralIntelligence/Pigeonhole.lean` — the counting pigeonhole
  and `coupon_collector_pigeonhole`.
- `StructuralIntelligence/CouponCollector.lean` — the two headline
  Theorem-5-named exports.
- `StructuralIntelligence/CommonSuffScreen.lean` —
  `IsCommonSuffScreen`, `jointTaskQuotient`, and the Theorem-4-core
  headlines `commonSuffScreen_refines`,
  `commonSuffScreen_coarsest`,
  `commonSuffScreen_eq_jointTaskQuotient_iff`.
- `StructuralIntelligence/Refinement.lean` — `Refines`, `qRel`, and
  the Theorem-6-core headlines `refinement_transitive`,
  `refinement_preserves_screen`,
  `refinement_preserves_screen_qRel`.
- `StructuralIntelligence/CompilerTomography.lean` —
  `IsIdentifiable`, `ConsistentWith`, `RefutedBy`, and the
  CT-1-core headlines `identifiability_implies_unique_by_witness`,
  `identifiability_yields_refuting_data`,
  `identifiability_isolates_theta_star`.
- `StructuralIntelligence/CausalSemantics.lean` — `PsiEquiv`,
  `MessageQuotient`, `messageQuotientMap`, and the CS-1/CS-2 core
  headlines `psi_equiv_preserves_under_context`,
  `messageQuotient_is_common_sufficient`,
  `messageQuotient_is_coarsest`.
- `StructuralIntelligence/Antecedents.lean` — `IntersectionScreen`,
  `LocallySufficient`, and the SA-1 core headlines
  `intersection_is_common_sufficient`,
  `intersection_is_coarsest_over_family`.
- `StructuralIntelligence/AbstractionFrontier.lean` — `Dominates`,
  `IsPareto`, and the AF-1/AF-2 core headlines
  `pareto_set_is_antichain`,
  `pareto_contains_css_when_zero_sufficiency`.
- `StructuralIntelligence/AlignmentGovernance.lean` —
  `ValidTrajectory` and the AG-2 core headline
  `viability_inherited_by_superset` (plus `viability_valid_ext`).
- `StructuralIntelligence/TheoryAtlas.lean` — `CocycleHolds`,
  `GluesTransitions`, `Injective`, and the TA-1 core headlines
  `cocycle_implies_gluing`, `injective_gluing_implies_cocycle`
  (both halves; the naked ↔ is weakened — see *What is not
  formalized*).
- `StructuralIntelligence/RepresentationRepair.lean` — `LiftRepairs`,
  `Preserves`, `LiftEnsures`, `Independent`, and the RR-2 core
  headlines `independent_lifts_compose_ensures`,
  `independent_lifts_compose`.
- `StructuralIntelligence/AutocatalyticArtwork.lean` —
  `bayesPosterior`, `boltzmannUpdate`, and the AA-2 core headline
  `bayes_equals_boltzmann_with_reward_as_likelihood` (plus the
  function-level `bayesPosterior_eq_boltzmannUpdate`).
- `StructuralIntelligence/DeleteRepair.lean` — delete–obstruction–
  repair core: `Act` / `IsInvariant` / `FactorsThrough`,
  `prefixSum` / `sumInt`, `ExactRepair`, `pathA` / `pathB`, and the
  headlines `symmetry_mismatch_nogo`,
  `cycle_integrates_iff_sum_zero`,
  `potentials_unique_up_to_translation`,
  `repair_splits_disagreement`, `repair_paths_disagree`.
- `StructuralIntelligence/Compiler/SquaringSeparation.lean` —
  Mul/Sq trees, expand-preserves-degree, and the US-2/US-3 headlines
  `tree_size_separation`, `circuit_size_of_pow2`,
  `conservative_extension`, `squaring_separation`.
- `StructuralIntelligence/EmlZeroIdentity.lean` — EML zero witness
  `eml(a, eml(eml(a,1),1)) = 0` from `eml(a,b):=exp(a)-ln(b)` and
  exp/ln cancellation.  Headlines `eml_zero_identity`,
  `eml_zero_identity_one`, `eml_zero_identity_x`.
- `StructuralIntelligence/KappaCheap.lean` — Paper F
  `kappa_cheap_not_function`.  **Proved, not verified.**
- `StructuralIntelligence/KappaScreen.lean` — Paper F
  `kappa_screen_hits_suite`.  Cites CommonSuffScreen.  **Proved, not verified.**
- `StructuralIntelligence/KappaUnique.lean` — Paper F
  `bag_not_unique`.  **Proved, not verified.**
- `StructuralIntelligence/KappaRelabel.lean` — Paper F
  `kappa_relabel_natural`.  **Proved, not verified.**
- `StructuralIntelligence/Aff13.lean` — Paper C
  `affine_escapes_kirchhoff`.  **Proved, not verified.**
- `StructuralIntelligence/DiamondInterval.lean` — Paper D
  `poset_not_determine_interval`.  **Proved, not verified.**
- `StructuralIntelligence/SurgeryMiss.lean` — Paper E
  `surgery_miss_pair_eq`.  **Proved, not verified.**

## Provenance

The pigeonhole and union-bound facts are elementary combinatorics,
the common-sufficient-screen refinement and the ε-covering
refinement-reduction are elementary functional algebra, and the
CT-1 identifiability-uniqueness step is elementary logic; the
formalisation is a regression artifact against the informal proofs
in §§ 2.4, 2.5, 2.5b of the *Structural Intelligence* paper and § 2
of the *Compiler Tomography* companion paper, not a novelty claim.
The point is that the mechanism of each theorem survives translation
to a machine-checked setting with no probability, measure theory, or
real analysis required — the probabilistic and analytic overlays are
entirely orthogonal.
