# Structural Intelligence Lean 4 Proofs

Machine-checked artifact for Theorem 5 (discrete learnability) of the
*Structural Intelligence* paper
(`papers/structural_intelligence/paper.md`).

## What is formalized

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

## What is *not* formalized

- The analytic amplification of Theorem 5:
  - `(1 - 1/(cM))^N ≤ exp(-N/(cM))` for real `c, M`;
  - `M · exp(-N/(cM)) ≤ ε` whenever `N ≥ cM · ln(M/ε)`.
  Both statements need real numbers, `exp`, and `log`, none of which
  live in the Lean 4 core library.  A `Mathlib`-based amplification is
  a natural follow-up and would live in a separate sub-package so as
  not to blow the 15-minute CI budget with a fresh `Mathlib` build.
- Theorems 1, 2, 4, 6 and the continuous-case Corollary — these need
  measure theory (Theorem 4's minimality-of-quotient argument), ε-net
  arguments (Theorem 6), or additional real analysis, all beyond the
  Lean 4 core.

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
headline theorem.  All four sit on standard axioms (`propext`,
`Quot.sound`, and — for the deterministic lower bound — `Classical.choice`).

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

## Provenance

The pigeonhole and union-bound facts are elementary combinatorics; the
formalisation is a regression artifact against the informal proof in
§ 2.5 of the paper, not a novelty claim.
