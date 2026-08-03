# Causal Semantics

## Meaning as naturally equivalent update operators across independent contexts, on the stochastic-fibration compiler

**Jawaun Brown**
Human author and research director

**Claude Code (agent)**
Experiment code, analysis, and manuscript production under direction and review

**Date:** August 3, 2026
**Status:** two theorems + one corollary + one exact worked example (six messages, four contexts). Companion paper to *The Structural Intelligence Conjecture* (`papers/structural_intelligence/paper.md`); depends on Theorem 4 of that paper (common sufficient statistic under a shared Markov screen) and instantiates the extended-program clause §5.7 as a theorem.

---

## Abstract

Extended-program clause §5.7 of *The Structural Intelligence Conjecture*
conjectures that "two symbols are equivalent when they induce naturally
equivalent update operators `Ψ_{m, c}` across independent contexts — a
meaning layer that ordinary co-occurrence embeddings omit". This paper
turns that clause into a theorem in the discrete-message case, and
gives its natural companion instrument.

- **Theorem CS-1 (Ψ-equivalence is a congruence).** *For a message
  space `𝓜`, a context space `𝓒`, and an update operator
  `Ψ : 𝓜 × 𝓒 → 𝒫(𝒳)` sending each `(m, c)` to a distribution over
  future states, the relation*
  ```
  m_1 ~_Ψ m_2   :⇔   ∀ c ∈ 𝓒 :  Ψ(m_1, c) = Ψ(m_2, c)
  ```
  *is a proper equivalence relation on `𝓜` (reflexive, symmetric,
  transitive), and it is preserved under context substitution: if
  `m_1 ~_Ψ m_2` then for every finite context sequence
  `c_1, …, c_n ∈ 𝓒`, `Ψ(m_1, c_i) = Ψ(m_2, c_i)` for every `i`.*
- **Theorem CS-2 (Meaning quotient is the coarsest sufficient
  statistic on messages).** *The quotient `𝓜 / ~_Ψ` is the coarsest
  partition of `𝓜` that preserves every downstream distribution
  `Ψ(·, c)`. Formally, `𝓜 / ~_Ψ` is a **common sufficient statistic**
  for the family `{Ψ(·, c) : c ∈ 𝓒}` on `𝓜` in the sense of Theorem 4
  of the parent paper, and no strictly coarser partition of `𝓜` has
  the same property.*
- **Corollary (Causal semantics ⊥ ambient co-occurrence).** *Naïve
  co-occurrence embeddings group messages by the ambient
  distribution of the messages themselves (which tokens appear next
  to which), not by their downstream causal effect. Ψ-equivalence
  and co-occurrence-equivalence are, in general, incomparable
  partitions of `𝓜`. Concretely, the worked example of §4 exhibits
  six messages with a four-class Ψ-quotient `{{m_0, m_1}, {m_2, m_3},
  {m_4}, {m_5}}` and a two-class co-occurrence partition
  `{{m_0, m_2, m_4}, {m_1, m_3, m_5}}`: neither refines the other,
  and no single-cluster overlap coincides.*

We close with an exact worked example (`experiments/causal_semantics_pair`)
of six messages and four contexts on a four-state future space
`𝒳 = {x_0, x_1, x_2, x_3}`. Ψ is hand-built so that `m_0 ~_Ψ m_1`
(identical downstream distributions on every context), `m_2 ~_Ψ m_3`
(identical downstream, different from the `m_0` class), and `m_4`,
`m_5` each stand alone. The distractor co-occurrence matrix is
designed so that a naïve co-occurrence clustering pools messages by
their ambient token signature — grouping the even-indexed messages
against the odd-indexed messages — an orthogonal structure to
`~_Ψ`. Every gate of the pre-registered set passes exactly.

The paper is a *reduction*, not a new representation-learning
recipe. Its content is *organising*: it lets the vague §5.7 clause be
read as a concrete equivalence-relation theorem, and it identifies
exactly which axis of a candidate embedding is doing the load-bearing
work of *meaning* (constancy of `Ψ(·, c)`) versus *co-occurrence*
(constancy of ambient marginals).

---

## 1. Setup

We inherit the master object of *The Structural Intelligence
Conjecture* §1: a stochastic fibration `(q : X → Z, K : Z ⇝ X)` on a
standard Borel `X`. Fix

- a **message space** `𝓜` (a countable or standard-Borel set of
  discrete messages an agent may emit or receive),
- a **context space** `𝓒` (the same, but for the ambient state in
  which a message is encountered), and
- a **future-state space** `𝒳` on which a probability measure lives,
  together with an **update operator**
  ```
  Ψ : 𝓜 × 𝓒 → 𝒫(𝒳),   Ψ(m, c) ∈ 𝒫(𝒳),
  ```
  sending each `(message, context)` pair to a distribution over future
  states. Operationally `Ψ(m, c)` is the law of the next fine state
  when the agent is in context `c` and receives message `m` — the
  literal *update* the message induces on the agent's fine-state
  distribution.

**Ψ-equivalence of messages.** Two messages `m_1, m_2 ∈ 𝓜` are
**Ψ-equivalent** iff
```
∀ c ∈ 𝓒 :  Ψ(m_1, c) = Ψ(m_2, c),
```
written `m_1 ~_Ψ m_2`. Two Ψ-equivalent messages induce the same
downstream distribution in every possible context, and are therefore
downstream-indistinguishable.

**Meaning quotient.** The set of equivalence classes
`𝓜 / ~_Ψ` is called the **meaning quotient** of `𝓜` with respect to
`Ψ`. Its cells are the coarsest downstream-preserving grouping of
messages: two messages are pooled iff no context can tell them apart
by the future they induce.

**Distractor: naïve co-occurrence.** For contrast, fix a **co-occurrence
signature map** `κ : 𝓜 → ℝ^d_κ` (e.g. a row of an ambient
message-by-token count matrix, normalised to a probability vector,
or a Word2Vec-style embedding). Define
```
m_1 ~_κ m_2   :⇔   κ(m_1) = κ(m_2)
```
as **co-occurrence-equivalence** of messages. The corresponding
partition `𝓜 / ~_κ` is what a naïve embedding recovers when
messages have no downstream distribution to be measured against —
it groups by *which other tokens the message appears near*, not by
*what the message causes*. Concrete embeddings (Word2Vec, GloVe,
BERT masked-token, etc.) typically produce a continuous version
whose partition is a nearest-neighbour clustering of `κ`; here we
take the exact discrete case where the signature `κ(m)` is a
finite-dimensional vector and messages with identical vectors form
a co-occurrence class.

`~_Ψ` and `~_κ` are, in general, distinct equivalence relations on
`𝓜`. §3 proves this in the sharp form: neither refines the other,
and neither is implied by the other — the two axes of representation
are formally orthogonal.

---

## 2. Theorem CS-1: Ψ-equivalence is a congruence

**Setup (CS-1).** Fix `Ψ : 𝓜 × 𝓒 → 𝒫(𝒳)`. Define `~_Ψ` as in §1.

**Theorem CS-1 (Ψ-equivalence is a congruence).** *`~_Ψ` is a
proper equivalence relation on `𝓜`: reflexive, symmetric, and
transitive. Furthermore, `~_Ψ` is preserved under context substitution:
if `m_1 ~_Ψ m_2` then for every finite sequence of contexts
`c_1, …, c_n ∈ 𝓒`, `Ψ(m_1, c_i) = Ψ(m_2, c_i)` for every `i ∈ {1, …, n}`.*

**Proof.**

*(Reflexivity.)* For every `m ∈ 𝓜` and every `c ∈ 𝓒`, `Ψ(m, c) = Ψ(m, c)`
by definition of a function. Hence `m ~_Ψ m` for every `m`.

*(Symmetry.)* Suppose `m_1 ~_Ψ m_2`. Then for every `c ∈ 𝓒`,
`Ψ(m_1, c) = Ψ(m_2, c)`, so `Ψ(m_2, c) = Ψ(m_1, c)` by symmetry of
equality. Hence `m_2 ~_Ψ m_1`.

*(Transitivity.)* Suppose `m_1 ~_Ψ m_2` and `m_2 ~_Ψ m_3`. Then for
every `c ∈ 𝓒`, `Ψ(m_1, c) = Ψ(m_2, c) = Ψ(m_3, c)` by transitivity
of equality applied pointwise. Hence `m_1 ~_Ψ m_3`.

*(Context substitution.)* Suppose `m_1 ~_Ψ m_2` and let
`c_1, …, c_n ∈ 𝓒` be any finite context sequence. By definition of
`~_Ψ`, `Ψ(m_1, c) = Ψ(m_2, c)` for **every** `c ∈ 𝓒`; in particular
this holds at each `c_i`. □

**Remark (why *congruence*).** In the algebraic sense, a congruence on
a set with a family of unary operations `{f_c}_{c ∈ 𝓒}` is an
equivalence relation preserved by every `f_c`. Setting
`f_c(m) := Ψ(m, c) ∈ 𝒫(𝒳)`, the statement `m_1 ~_Ψ m_2 ⇒
f_c(m_1) = f_c(m_2) for every c` is *exactly* congruence with respect
to the family `{f_c}_{c ∈ 𝓒}`. So `~_Ψ` is the largest congruence
on `𝓜` compatible with the update-operator family. This is a
recasting of the well-known fact that the finest partition
respecting a family of maps is the intersection of the level-set
partitions of each map — but interpreted here as the *meaning* of a
symbol reduces to its downstream causal role under every context.

**Consequence.** Two Ψ-equivalent messages can be substituted for one
another in any context without altering the induced downstream
distribution. This is the operational meaning of "same meaning" in
this framework: substitutability preserves observable effect.

---

## 3. Theorem CS-2: Meaning quotient is the coarsest sufficient statistic on messages

**Setup (CS-2).** Fix `Ψ : 𝓜 × 𝓒 → 𝒫(𝒳)`. For each `c ∈ 𝓒`,
`Ψ(·, c) : 𝓜 → 𝒫(𝒳)` is a function on `𝓜`. Read this as a family
of `𝓜`-indexed distributions
```
{ Ψ(·, c) : c ∈ 𝓒 }
```
in the sense of Theorem 4 of the parent paper — a family of tasks
whose target is a distribution over `𝒳` and whose input is a
message `m ∈ 𝓜`.

**Theorem CS-2 (Meaning quotient is the coarsest sufficient statistic
on messages).** *The quotient `π_Ψ : 𝓜 → 𝓜 / ~_Ψ` is the coarsest
partition of `𝓜` that preserves every downstream distribution in the
family `{Ψ(·, c) : c ∈ 𝓒}`. Formally, `π_Ψ` is a common sufficient
statistic (in the Theorem-4 sense) for the family on `𝓜`, and no
strictly coarser partition of `𝓜` is common sufficient for the
family.*

**Proof.**

*(Sufficiency.)* Let `c ∈ 𝓒` and take two messages `m_1, m_2 ∈ 𝓜`
lying in the same Ψ-class, i.e. `π_Ψ(m_1) = π_Ψ(m_2)`. By definition
of `~_Ψ`, `Ψ(m_1, c) = Ψ(m_2, c)`. So the value of `Ψ(·, c)` is
constant on each Ψ-class — equivalently, `Ψ(·, c)` factors through
`π_Ψ`:
```
Ψ(m, c)  =  Ψ̂(π_Ψ(m), c)
```
for a well-defined `Ψ̂ : (𝓜 / ~_Ψ) × 𝓒 → 𝒫(𝒳)`. This is the
factorisation `Y_α ⫫ 𝓜 | π_Ψ(𝓜)` in the Theorem-4 template with
`Y_α := Ψ(·, c) ∈ 𝒫(𝒳)` and `X := 𝓜`. Hence `π_Ψ` is a common
sufficient statistic for the family.

*(Coarsest.)* Suppose `π' : 𝓜 → S'` is a strictly coarser partition
of `𝓜` than `π_Ψ` — i.e. `π'` identifies at least one pair of
messages that `π_Ψ` distinguishes. Take such a pair `m_1, m_2` with
`π'(m_1) = π'(m_2)` but `π_Ψ(m_1) ≠ π_Ψ(m_2)`. Then `m_1 ≁_Ψ m_2`, so
there exists a context `c* ∈ 𝓒` such that `Ψ(m_1, c*) ≠ Ψ(m_2, c*)`.
If `π'` were common sufficient for the family, then `Ψ(·, c*)` would
factor through `π'` and take the same value on `m_1` and `m_2`
(since `π'(m_1) = π'(m_2)`) — contradiction. So no strictly coarser
partition is common sufficient, and `π_Ψ` is the coarsest common
sufficient statistic on `𝓜`. □

**Corollary (Causal semantics ⊥ ambient co-occurrence).** *The
meaning quotient `𝓜 / ~_Ψ` and the co-occurrence quotient
`𝓜 / ~_κ` are, in general, distinct partitions of `𝓜`. In
particular, `~_Ψ` need not refine `~_κ`, and `~_κ` need not refine
`~_Ψ` — the two axes are incomparable. This is because `~_Ψ` is
determined by the map `m ↦ Ψ(m, ·) ∈ 𝒫(𝒳)^𝓒`, while `~_κ` is
determined by the map `m ↦ κ(m) ∈ ℝ^{d_κ}`; there is no formal
constraint relating these two maps, and the worked example of §4
exhibits a case where the partitions are strictly incomparable.*

**Proof.** Take the six-message, four-context worked example of §4.
The Ψ-quotient there is
```
𝓜 / ~_Ψ  =  { {m_0, m_1}, {m_2, m_3}, {m_4}, {m_5} }    (4 classes)
```
and the co-occurrence quotient is
```
𝓜 / ~_κ  =  { {m_0, m_2, m_4}, {m_1, m_3, m_5} }         (2 classes).
```
No cell of one partition is a union of cells of the other: `{m_0, m_1}`
is neither a subset nor a superset of `{m_0, m_2, m_4}` (they share
only `m_0` but each contains a message the other does not). So
neither partition refines the other. □

**Consequence (operational).** A representation that groups messages
by ambient co-occurrence (Word2Vec, GloVe, contextualised token
embeddings without downstream-consequence signal, etc.) will in
general *fail* to recover the meaning quotient of §1. What it
recovers is a different partition — the one adapted to which
tokens co-occur with which, not to which futures each token causes.
The two axes may agree in some corpora (where downstream causal role
correlates with ambient co-occurrence, e.g. in synonym pairs that
also co-occur with the same words), but they are formally
independent. Where they diverge, a naïve embedding grouped by
`~_κ` is not learning meaning in the sense of §1.

---

## 4. Worked example: six messages, four contexts

**Message space.** `𝓜 = {m_0, m_1, m_2, m_3, m_4, m_5}` (six
discrete symbols, no additional structure).

**Context space.** `𝓒 = {c_0, c_1, c_2, c_3}` (four discrete
contexts).

**Future-state space.** `𝒳 = {x_0, x_1, x_2, x_3}` (four discrete
future states).

**Update operator `Ψ`.** Hand-built so that four distinct
downstream-distribution *classes* arise:
```
Ψ(m_0, ·) = Ψ(m_1, ·) = D_A(·)     [class A]
Ψ(m_2, ·) = Ψ(m_3, ·) = D_B(·)     [class B]
Ψ(m_4, ·) = D_C(·)                  [class C]
Ψ(m_5, ·) = D_D(·)                  [class D]
```
where the four class-conditional context maps are (rows = contexts,
columns = future states `x_0, x_1, x_2, x_3`):

| context | `D_A(c)`             | `D_B(c)`             | `D_C(c)`             | `D_D(c)`             |
|---:|---|---|---|---|
| `c_0` | (0.50, 0.50, 0.00, 0.00) | (0.00, 0.00, 0.50, 0.50) | (1.00, 0.00, 0.00, 0.00) | (0.00, 0.00, 0.00, 1.00) |
| `c_1` | (0.25, 0.25, 0.25, 0.25) | (0.70, 0.10, 0.10, 0.10) | (0.10, 0.70, 0.10, 0.10) | (0.10, 0.10, 0.70, 0.10) |
| `c_2` | (0.30, 0.30, 0.20, 0.20) | (0.20, 0.20, 0.30, 0.30) | (0.50, 0.50, 0.00, 0.00) | (0.00, 0.00, 0.50, 0.50) |
| `c_3` | (0.40, 0.10, 0.40, 0.10) | (0.10, 0.40, 0.10, 0.40) | (0.25, 0.25, 0.25, 0.25) | (0.10, 0.40, 0.40, 0.10) |

Every row is a valid probability vector (sums to 1). By direct
inspection at `c_0`, `D_A`, `D_B`, `D_C`, `D_D` are four distinct
distributions on `𝒳`, so the Ψ-classes are pairwise distinct. By
construction, within each class the downstream distribution is
identical in every context, so the Ψ-quotient is exactly
```
𝓜 / ~_Ψ  =  { {m_0, m_1}, {m_2, m_3}, {m_4}, {m_5} }.
```

**Distractor: co-occurrence signature.** Hand-built ambient
co-occurrence matrix `κ : 𝓜 → ℤ^4_{≥ 0}` (rows = messages, columns
= ambient tokens `t_0, t_1, t_2, t_3`):

| message | `κ(m)` |
|---:|---|
| `m_0` | (4, 4, 1, 1) |
| `m_1` | (1, 1, 4, 4) |
| `m_2` | (4, 4, 1, 1) |
| `m_3` | (1, 1, 4, 4) |
| `m_4` | (4, 4, 1, 1) |
| `m_5` | (1, 1, 4, 4) |

Even-indexed messages `{m_0, m_2, m_4}` share the signature
`(4, 4, 1, 1)`; odd-indexed messages `{m_1, m_3, m_5}` share the
signature `(1, 1, 4, 4)`. Under `~_κ` the co-occurrence quotient is
therefore
```
𝓜 / ~_κ  =  { {m_0, m_2, m_4}, {m_1, m_3, m_5} }.
```

This is *orthogonal* to the Ψ-quotient: `m_0` and `m_1` are `~_Ψ`
but not `~_κ`; `m_0` and `m_2` are `~_κ` but not `~_Ψ`. Neither
partition refines the other, and the Corollary of §3 is instantiated
exactly.

**Instrument gates.** The witness (`experiments/causal_semantics_pair`)
computes both partitions exactly (no random seeds, no Monte Carlo)
and verifies:

1. `cs1_psi_equivalence_is_reflexive_symmetric_transitive`: the
   binary relation `~_Ψ` on `𝓜 × 𝓜` is verified reflexive,
   symmetric, and transitive by exhaustive enumeration of all
   `36 = 6 × 6` ordered pairs and, for transitivity, all
   `216 = 6³` ordered triples.
2. `cs2_psi_quotient_has_four_classes`: the equivalence classes of
   `~_Ψ` on `𝓜` are exactly `{{m_0, m_1}, {m_2, m_3}, {m_4}, {m_5}}`.
3. `cs2_psi_quotient_is_common_sufficient`: for every context
   `c ∈ 𝓒`, the downstream distribution `Ψ(·, c)` is constant within
   each Ψ-class (i.e., `π_Ψ` is a common sufficient statistic for
   the family `{Ψ(·, c) : c ∈ 𝓒}` on `𝓜`).
4. `cs_cooccurrence_partition_differs_from_psi_quotient`: the
   co-occurrence partition `𝓜 / ~_κ` and the Ψ-quotient
   `𝓜 / ~_Ψ` are distinct partitions of `𝓜` (as sets of cells).
   Neither refines the other, and no cell of either partition
   coincides with a cell of the other.

All four gates pass exactly.

---

## 5. Relation to the SIC framework

Theorem CS-1 promotes the extended-program §5.7 clause of the parent
paper from a *research direction* ("two symbols are equivalent when
they induce naturally equivalent update operators `Ψ_{m, c}` across
independent contexts — a meaning layer that ordinary co-occurrence
embeddings omit") to a *theorem* in the discrete-message case:
`~_Ψ` is a proper equivalence relation, closed under context
substitution. Theorem CS-2 identifies the meaning quotient
`𝓜 / ~_Ψ` as the exact object promised by §5.7 — the coarsest
common sufficient statistic on messages for the context-conditional
downstream family — thereby applying Theorem 4 of the parent paper
one level up, at the message layer rather than the world-state
layer.

The corollary makes the orthogonality claim precise: co-occurrence
embeddings and causal-semantic embeddings are, in general,
independent partitions of `𝓜`, and the worked example exhibits a
concrete case where they are strictly incomparable. This is the
*meaning layer that ordinary co-occurrence embeddings omit* of
§5.7, made into a theorem and a numerical witness.

Together with

- Theorems CG-1, CG-2 (Fisher geometry and holonomy of concern from
  *Concern as Fiber Geometry*),
- Theorems CT-1, CT-2 (MDL identifiability and Boltzmann ecology from
  *Compiler Tomography*),
- Theorem SA-1 (antecedent taxonomy from *Sufficient Antecedents for
  Cross-Task Stability*),
- Theorems AF-1, AF-2 (abstraction frontier as a Pareto antichain
  from *The Abstraction Frontier*), and
- Theorems AG-1, AG-2 (viability under bounded leakage from
  *Alignment as Ensemble Governance*),

Theorems CS-1, CS-2 give the SIC extended program another explicit
theorem-instrument pair. The remaining §5 constructs (theory atlas
§5.5, representation-repair calculus §5.8, autocatalytic artwork
§5.10) remain open — each is a direction rather than a theorem.

The CS framing sharpens the SIC honesty condition on
representation choice: an embedding that reports "these two symbols
mean the same thing" must be checkable against the meaning quotient
`𝓜 / ~_Ψ`, not merely against a co-occurrence quotient
`𝓜 / ~_κ`. Where the two agree, no distinction is drawn; where
they disagree, the embedding is naming co-occurrence and calling it
meaning.

---

## 6. Limitations

- **Discrete messages, discrete contexts.** CS-1 and CS-2 are stated
  and proved in the countable-message, countable-context case. The
  statements extend directly to standard-Borel `𝓜` and `𝓒` under
  the usual measure-theoretic definitions of equivalence (a.s.
  equality of the two update laws for every context), but the
  worked-example instrument uses the discrete case for exact
  witness.
- **Exact operator equality.** `~_Ψ` requires exact equality of the
  downstream distributions across every context. In practice, one
  measures a metric on `𝒫(𝒳)` (total variation, KL, Wasserstein) and
  works with an ε-relaxation `~_Ψ^ε`. The proofs of CS-1 and CS-2
  go through for the ε-relaxation with the obvious modifications
  (reflexivity holds for `ε ≥ 0`, transitivity holds up to `2ε` in
  the triangle-inequality sense for any metric, sufficiency holds
  up to `ε`), at the cost of a quantitative rather than exact
  statement.
- **No estimator.** This paper does not construct an estimator of
  `~_Ψ` from data; it exhibits the object as an equivalence relation
  and a coarsest sufficient statistic. A follow-up instrument would
  study sample-efficient recovery of `~_Ψ` from finite context /
  outcome samples — the natural bridge to the SIC-C-c
  learnability question of the parent paper §2.5.
- **Co-occurrence as a straw-man.** The distractor here is
  intentionally the *simplest* co-occurrence signature (exact row
  equality of an ambient-token count matrix). Modern embeddings
  (contextualised transformers, joint text-and-behaviour models)
  will already partially recover downstream-effect structure to the
  extent their training loss couples message identity to a
  behaviourally-relevant signal. The orthogonality claim of §3 is
  formally correct at the level of *what the embedding is a
  function of*, but the practical distance between `~_Ψ` and `~_κ`
  for a specific embedding is an empirical question.
- **Not a Lean formalisation.** The proofs of CS-1 and CS-2 are
  elementary set-theoretic arguments (proper equivalence relation,
  finest partition respecting a family of maps). Formalising them
  in Lean 4 alongside Theorem 4's core in
  `formal/structural-intelligence/StructuralIntelligence/` would
  give the meaning quotient a machine-checked object; that work is
  not yet done.
- **Does not solve meaning.** CS-1 is a *reduction*: it says the
  right object of *meaning* under this framework is the Ψ-quotient,
  and the right check against a candidate embedding is the
  coarsest-common-sufficient-statistic property. It says nothing
  about *how to construct* an embedding whose partition equals
  `~_Ψ` — that is where the actual work of semantic representation
  learning lies.

---

## 7. Reproduction

```bash
python3 experiments/causal_semantics_pair/experiment.py
```

Full development is in the parent paper's §5.7 and the master
notes file `notes/structural_intelligence_conjecture.md`.
