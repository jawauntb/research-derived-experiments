import StructuralIntelligence.UnionBound
import StructuralIntelligence.Pigeonhole

/-!
# Structural Intelligence — coupon-collector union bound (combined)

The two Lean-checked ingredients that Theorem 5 assembles into
`Pr[some fibre missed] ≤ M · exp(-N/(cM)) ≤ ε`:

*   `countP_anyFin_le_sumFin_countP` — the finite union bound.
*   `coupon_collector_pigeonhole` — the deterministic pigeonhole:
    a sequence of `N < M` draws from an `M`-element universe cannot
    cover the universe.

Combined here into two headline theorems named after the paper.
The remaining step, `(1 - 1/(cM))^N ≤ exp(-N/(cM))` and
`M · exp(-N/(cM)) ≤ ε` for `N ≥ cM ln(M/ε)`, needs `Real`, `exp`, `log`
and is therefore out of scope for this pure-Lean-core artifact.  See the
package `README.md`.
-/

namespace StructuralIntelligence

/-- **Theorem 5 (combinatorial content).**

    The number of `x ∈ L` for which *some* fibre indicator `P i x`
    fires is at most the sum, over fibres `i : Fin M`, of the number
    of `x ∈ L` for which `P i x` fires.

    Interpretation.  Take `L` to be an enumeration of realizations of a
    sample of size `|L|`, and let `P i x` be the indicator "sample `x`
    misses fibre `i`."  Then the theorem is exactly

    `Pr[some fibre missed]  ≤  Σᵢ Pr[fibre i missed]`,

    the union bound used in Theorem 5.  Division by `|L|` to convert
    counts to probabilities is a triviality that does not require
    additional formalisation. -/
theorem theorem5_union_bound {α : Type u}
    (M : Nat) (P : Fin M → α → Bool) (L : List α) :
    L.countP (fun x => anyFin M (fun i => P i x)) ≤
      sumFin M (fun i => L.countP (P i)) :=
  countP_anyFin_le_sumFin_countP M P L

/-- **Theorem 5 (deterministic base case).**

    For `N < M`, every sample sequence `f : Fin N → Fin M` from an
    `M`-element universe misses at least one fibre.  This is the
    zero-probability regime of the coupon-collector bound: no
    algorithm can recover an `M`-element partition from fewer than
    `M` observations. -/
theorem theorem5_deterministic_lower_bound
    {N M : Nat} (h : N < M) (f : Fin N → Fin M) :
    ∃ i : Fin M, ∀ j : Fin N, f j ≠ i := by
  classical
  -- Assume the negation; then `f` covers `Fin M`, contradicting `N < M`.
  apply Classical.byContradiction
  intro hnot
  -- From `¬ ∃ i, ∀ j, f j ≠ i` we extract, for each `i`, a `j` with `f j = i`.
  have hcover : ∀ i : Fin M, ∃ j : Fin N, f j = i := by
    intro i
    apply Classical.byContradiction
    intro hi
    apply hnot
    refine ⟨i, ?_⟩
    intro j hj
    exact hi ⟨j, hj⟩
  have hM : M ≤ N := coupon_collector_pigeonhole f hcover
  exact Nat.not_lt.mpr hM h

end StructuralIntelligence
