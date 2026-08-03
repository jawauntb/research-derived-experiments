# Structural Intelligence Lean 4 Proofs

Machine-checked artifact for the algebraic cores of Theorems 4
(Cross-task stability, conditional), 5 (discrete learnability) and
6 (ε-covering reduction) of the *Structural Intelligence* paper
(`papers/structural_intelligence/paper.md`), plus the identifiability
core of Theorem CT-1 (MDL identification) of the *Compiler
Tomography* companion paper (`papers/compiler_tomography/paper.md`).

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
