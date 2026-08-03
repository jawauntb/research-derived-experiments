# Structural Intelligence Lean 4 Proofs

Machine-checked artifact for the algebraic core of Theorem 4
(Cross-task stability, conditional) and Theorem 5 (discrete
learnability) of the *Structural Intelligence* paper
(`papers/structural_intelligence/paper.md`).

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

### No `sorry`s

Every checked-in proof compiles fully; there are no `sorry`s anywhere
in the package.  `commonSuffScreen_refines` and
`commonSuffScreen_coarsest` depend on no axioms at all;
`commonSuffScreen_eq_jointTaskQuotient_iff` uses only `Quot.sound`
(via `funext` on the joint task quotient).

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
- Theorems 1, 2, 6 and the continuous-case Corollary — these need
  ε-net arguments (Theorem 6) or additional real analysis / measure
  theory, all beyond the Lean 4 core.

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
`Classical.choice`).  The Theorem-4-core headline
`commonSuffScreen_refines` and its coarsest-quotient corollary
`commonSuffScreen_coarsest` depend on **no axioms**;
`commonSuffScreen_eq_jointTaskQuotient_iff` uses only `Quot.sound`
(via a single `funext`).

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

## Provenance

The pigeonhole and union-bound facts are elementary combinatorics and
the common-sufficient-screen refinement is elementary functional
algebra; the formalisation is a regression artifact against the
informal proofs in §§ 2.4 and 2.5 of the paper, not a novelty claim.
The point is that the mechanism of each theorem survives translation
to a machine-checked setting with no probability or measure theory
required — the probabilistic overlays are entirely orthogonal.
