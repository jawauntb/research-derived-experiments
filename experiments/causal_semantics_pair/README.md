# Causal-Semantics Pair (Theorems CS-1, CS-2 witness)

Companion instrument for
[`papers/causal_semantics/paper.md`](../../papers/causal_semantics/paper.md).

Hypothesis: for a message space `M`, a context space `C`, and an
update operator `Ψ : M × C → 𝒫(𝒳)` sending each `(m, c)` to a
distribution over future states, Theorem CS-1 says
`m_1 ~_Ψ m_2 :⇔ ∀ c ∈ C : Ψ(m_1, c) = Ψ(m_2, c)` is a proper
equivalence relation on `M` and is preserved under context
substitution. Theorem CS-2 says the meaning quotient `M / ~_Ψ` is
the coarsest partition of `M` that preserves every downstream
distribution `Ψ(·, c)` — the common sufficient statistic for the
family `{Ψ(·, c) : c ∈ C}` on `M`, in the sense of Theorem 4 of the
parent paper. The corollary says causal semantics and ambient
co-occurrence are, in general, orthogonal axes of representation.

Method: six discrete messages `M = {m_0, …, m_5}`, four discrete
contexts `C = {c_0, …, c_3}`, four discrete future states
`𝒳 = {x_0, …, x_3}`. `Ψ` is hand-built so `m_0 ~_Ψ m_1` (class A),
`m_2 ~_Ψ m_3` (class B), `m_4` alone (class C), `m_5` alone (class
D); the four class-conditional context maps `D_A, D_B, D_C, D_D`
are distinct at `c_0`. Distractor co-occurrence signature
`κ : M → ℤ^4_{≥ 0}` groups the even-indexed messages
`{m_0, m_2, m_4}` (signature `(4, 4, 1, 1)`) against the odd-indexed
messages `{m_1, m_3, m_5}` (signature `(1, 1, 4, 4)`) — an
orthogonal partition to the Ψ-quotient.

Pre-registered gates (all four pass exactly):

- `cs1_psi_equivalence_is_reflexive_symmetric_transitive`: the
  binary relation `~_Ψ` on `M × M` is verified reflexive,
  symmetric, and transitive by exhaustive enumeration.
- `cs2_psi_quotient_has_four_classes`: the equivalence classes of
  `~_Ψ` on `M` are exactly
  `{{m_0, m_1}, {m_2, m_3}, {m_4}, {m_5}}`.
- `cs2_psi_quotient_is_common_sufficient`: for every context
  `c ∈ C`, the downstream distribution `Ψ(·, c)` is constant within
  each Ψ-class (`π_Ψ` is a common sufficient statistic in the
  Theorem-4 sense for `{Ψ(·, c) : c ∈ C}` on `M`).
- `cs_cooccurrence_partition_differs_from_psi_quotient`: the
  co-occurrence partition `M / ~_κ` and the Ψ-quotient
  `M / ~_Ψ` are distinct partitions of `M`.

Result: all four gates pass exactly. The Ψ-quotient has four
classes; the co-occurrence quotient has two classes; neither
partition refines the other, and they share no cell — instantiating
the orthogonality corollary of §3 in the paper.

Run:

```bash
python3 experiments/causal_semantics_pair/experiment.py
```
