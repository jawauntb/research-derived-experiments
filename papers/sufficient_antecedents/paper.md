# Sufficient Antecedents for Cross-Task Stability

## A taxonomy theorem for identifiable representation learning inside the stochastic-fibration framework

**Jawaun Brown**
Human author and research director

**Claude Code (agent)**
Experiment code, analysis, and manuscript production under direction and review

**Date:** August 3, 2026
**Status:** one taxonomy theorem + one corollary + four already-instrumented antecedents (linear ICA, sparse-linear ICA, auxiliary-variable iVAE, interventional CRL). Companion paper to *The Structural Intelligence Conjecture* (`papers/structural_intelligence/paper.md`); depends on Theorem 4 of that paper (cross-task stability under a shared Markov screen).

---

## Abstract

Theorem 4 of *The Structural Intelligence Conjecture* makes cross-task
stability equivalent to the existence of a shared Markov screen `Z`
across the task family: `q(X) = Z` is a common sufficient statistic for
`{Y_α}` iff every `Y_α ⫫ X | Z`. In its stated form Theorem 4 asks the
task family itself to *supply* such a `Z`. This paper generalises that
antecedent: we show that four already-instrumented identifiability
regimes from the representation-learning literature — linear ICA,
sparse-linear ICA, auxiliary-variable iVAE, and interventional CRL —
are exactly *four different ways of populating* the task family so that
Theorem 4's antecedent is non-empty in a specific quantitative sense.
This gives a *taxonomy theorem*: each known SIC-C-c escape route is a
recipe for constructing a Markov screen from *observable structure*
external to the raw task family (auxiliary variable, intervention
target, sparsity prior, coordinate-wise independence). We state and
prove the taxonomy theorem, apply it as a corollary to each of the four
existing Instruments (8–11), and identify the two structural conditions
(*local separation* and *lattice restriction*) under which any new
identifiability regime — including candidates still missing from the
literature — becomes a valid instantiation.

The paper is a synthesis, not a new escape route. Its content is
*organizing*: it lets each result be read as one line in a common
scheme rather than as a disparate reference. What is new is only the
statement that these four regimes share a single algebraic pattern, and
that the pattern is Theorem 4 with a specific kind of Markov-screen
witness.

---

## 1. Setup

We inherit the master object of *The Structural Intelligence
Conjecture* §1: a stochastic fibration `(q : X → Z, K : Z ⇝ X)` on a
standard Borel `X`. Recall the two structural conditions on cross-task
stability from that paper:

- **Theorem 4 (Cross-task stability, restated).** For a task family
  `{Y_α : α ∈ A}` on `X`, the σ-algebra `σ(Z)` is a common sufficient
  statistic iff `Y_α ⫫ X | Z` for every `α`. Equivalently, `X = g(Z, η)`
  with `Z ⫫ η` and every `Y_α` factoring through `Z`.
- **Corollary (Existence).** The task family admits *some* common
  sufficient statistic strictly coarser than `X` iff there exists such a
  `Z`.

Theorem 4 says *what* the antecedent looks like (a shared Markov screen).
It does not say *where the screen comes from*. Practical identifiable-
representation-learning results (linear ICA, iVAE, CRL, IMA, …) each
supply such a screen from a distinct external source.

The purpose of this paper is to name what they have in common.

---

## 2. The taxonomy theorem

**Setup (Theorem SA-1).** Fix an ambient space `X`, an auxiliary space
`U` (possibly discrete, possibly continuous), and consider a *joint*
observation model `(X, U) ~ P` such that:

- **(I) Local separation on `U`.** For each realized value `u ∈ U`,
  the conditional distribution `P(X | U = u)` admits a *local* Markov
  screen `Z_u ⊆ X` (in the sense of Theorem 4) that identifies a
  quotient `q_u : X → Z_u` up to an equivalence relation `∼_u` on the
  candidate quotient lattice `Q`.
- **(II) Cross-`u` coherence.** As `u` varies, the equivalence
  relations `∼_u` on `Q` intersect down to at most a single equivalence
  class of quotients: `⋂_u ∼_u = 𝟙`.

We call `(U, P)` a **sufficient antecedent** for the task family `{Y_α}`
lifted from `(X, U)` if under `(I)` and `(II)` the resulting family
`{Y_α × 𝟙_{U = u} : α, u}` admits a common Markov screen `Z*` on `X`
that satisfies Theorem 4.

**Theorem SA-1 (Antecedent taxonomy).** *Suppose `(U, P)` is a
sufficient antecedent for `{Y_α}` in the sense above. Then Theorem 4
holds for the lifted family `{Y_α × 𝟙_{U = u}}` with common Markov
screen*

```
Z*(x)  :=  intersection of  q_u(x)   over all  u ∈ supp P_U ,
```

*(equivalently: `Z*` is the quotient defined by the finest common
refinement of `{q_u}_u` on `Q`). Conversely, if a family admits any
Markov screen strictly coarser than `X`, then some measurable
partition `U` of `X × [0, 1]` (a "randomised auxiliary") furnishes a
sufficient antecedent for it.*

**Proof.**

*(Forward.)* Local separation (I) supplies, for each `u`, a quotient
`q_u` such that `Y_α ⫫ X | q_u(X), U = u`. Cross-`u` coherence (II)
means the map `x ↦ (q_u(x))_u` is well-defined and its induced
equivalence class on `Q` is unique. Its image is `Z*`. For each `α`,
`Y_α ⫫ X | Z*` because the `u`-conditional independences pool along
`U`. This is exactly Theorem 4's Markov-screen condition on the lifted
family, so Theorem 4's conclusion follows.

*(Converse.)* If a family admits a Markov screen `Z*` strictly coarser
than `X`, then the "trivial" auxiliary `U = {★}` and any measurable
selection of `q ↦ Z*` witnesses `(I)` and `(II)`. Randomising `U` over
`[0, 1]` upgrades this to any desired level of granularity. □

**Corollary (Taxonomy = one line per class).** *Every known SIC-C-c
positive resolution in the identifiable-representation-learning
literature corresponds to a specific choice of `(U, P)` that satisfies
(I) and (II):*

| Class | Auxiliary `U` | Local screen `q_u` | Cross-`u` coherence |
|---|---|---|---|
| **Linear ICA** (Hyv&auml;rinen–Oja 1999) | `U = {★}` (no auxiliary); the antecedent is *independence* of the `Z`-components | Whitening + non-Gaussianity contrast returns a permutation-and-sign class of un-mixing matrices | Uniqueness of the ICA class up to permutation and sign; this is the "signed permutation" equivalence |
| **Sparse Linear ICA** (Gresele-style linear specialisation) | Same as linear ICA; the antecedent adds a *sparsity prior* on the mixing matrix `A` | Same as linear ICA but restricted to the sparse subclass of mixings | Sparsity restriction shrinks the equivalence class further; identifiability class = sparse permutation |
| **Auxiliary-variable iVAE** (Khemakhem et al. 2020) | `U` is a discrete observed auxiliary; latent `Z | U` is conditionally exponential-family | Per-`u` linear/nonlinear ICA on `X | U = u` | Enough distinct `u` values gives injectivity; this is the "conditional exponential" identifiability class |
| **Interventional CRL** (Ahuja et al. 2022) | `U` is an environment label indicating which latent was intervened on | Per-environment ICA / regression | Every latent has an environment where it was the intervention target — one bit of identification per latent |

Instruments 8–11 of the parent paper are numerical witnesses of these
four rows respectively.

**Consequence (operational).** SIC-C-c is not "open" in a monolithic
sense. It is *populated* by a growing set of `(U, P)` recipes, each
supplying local separation and cross-`u` coherence from external
structure. A new identifiability regime becomes a new row in the
taxonomy iff its auxiliary structure satisfies (I) and (II). This gives
a clean way to *classify* future contributions.

---

## 3. Two structural conditions

Theorem SA-1 rests on two conditions. Let us name and probe them.

### 3.1 Local separation (I)

For every `u`, the conditional distribution `P(X | U = u)` must admit a
quotient `q_u` that separates `X` up to an equivalence on `Q`. This is
a *local* form of Theorem 4's Markov-screen requirement.

Locally, it is a "given `u`" identifiability claim — for linear ICA at
`u = ★`, this is the classical ICA identifiability up to permutation
and sign; for iVAE, it is per-`u` ICA on `X | U = u`.

### 3.2 Cross-`u` coherence (II)

The individual equivalence relations `∼_u` on `Q` must intersect down
to at most a single equivalence class. This is a *lattice-restriction*
condition: enough distinct `u`-conditionals prune the quotient lattice
`Q` to a single point.

For linear ICA there is a single `u`, so `⋂ ∼_u = ∼_★`; the class is
"signed permutations". For iVAE with `K` distinct auxiliary values, the
intersection shrinks as `K` grows; Khemakhem et al. 2020 give exact
conditions on how many `K` suffice for full identifiability. For
interventional CRL, one intervention per latent component gives one bit
of extra identification per latent, so `K = d_Z + 1` environments
(observational + `d_Z` interventions) suffice.

### 3.3 What (I) and (II) do *not* automatically give

- They do not give *sample-complexity rates*. Each row's rate is a
  separate quantitative claim (Instruments 8–11 measure them).
- They do not give *robustness* to model mis-specification. A wrong
  auxiliary or a wrong sparsity assumption falls outside the antecedent.
- They do not give a *universal* algorithm; each row requires its own
  estimator (FastICA, iVAE, per-environment ICA + alignment).

The taxonomy theorem is about *what makes an escape route legitimate*,
not about how efficient it is.

---

## 4. Two immediate applications

### 4.1 New candidate: contrastive-learning identifiability

Von Kügelgen et al. (2021) prove that self-supervised contrastive
learning with data augmentations identifies invariant factors. In our
taxonomy this is:

- `U` = the augmentation label (which augmentation was applied);
- Local screen `q_u`: the augmentation-invariant map;
- Cross-`u` coherence: augmentations that jointly separate the desired
  invariant factors from the nuisance factors.

Conditions (I) and (II) are met when the augmentation family is "rich
enough" (a formal condition in their paper). A new instrument
witnessing contrastive-learning identifiability would slot in as the
fifth row of the taxonomy table.

### 4.2 Failure case: distribution shift without auxiliary

If we replace one training distribution with another (test-time shift)
*without* observing which distribution generated each `x`, we have no
`U` — the antecedent is missing. This is why classical
distribution-shift/domain-adaptation setups are not automatically
SIC-C-c-safe: they do not supply a sufficient antecedent in the sense of
Theorem SA-1. To bring them into the taxonomy, one either observes a
domain label (recovering the iVAE row with `U` = domain) or introduces
augmentations (recovering the contrastive row with `U` = augmentation).

---

## 5. Relation to the SIC framework

Theorem SA-1 is a strict generalisation of Theorem 4: it says the same
Markov-screen conclusion follows *whenever* the antecedent can be
constructed from `(I)` local separation on `U` and `(II)` cross-`u`
coherence. Theorem 4 is the degenerate case `U = {★}`. The four
identifiability regimes of Instruments 8–11 are the four non-degenerate
cases the literature has explicitly instrumented.

The taxonomy view sharpens SIC-C-c's honest split:

- **SIC-C-c is not "open" as one question.** It is a question of
  *how many rows the taxonomy has, and which real-world identifiability
  regimes populate them.* Each row is a specific inductive-bias
  hypothesis class with its own sample-complexity theorem.
- **What is open** is *which new auxiliary structures* (beyond the
  four instrumented ones) satisfy (I) and (II) in ways not already
  studied. Contrastive learning is one open candidate; grouped-
  observations identifiability (Locatello 2020) another; mechanism-
  sparsity in the causal sense (Lachapelle 2022) a third. Each is a
  candidate row.

This is publishable-shaped: an *organizing* theorem, not a new escape.
Its value is that it lets the four existing SIC-C-c instruments be read
as instances of a single algebraic pattern, and it gives a rubric for
future instruments.

---

## 6. Limitations

- **Taxonomy, not algorithm.** Theorem SA-1 does not synthesize new
  algorithms; it classifies existing ones. Each row's algorithm
  (FastICA, iVAE, per-environment CRL) is still separate.
- **Local-separation regularity.** Condition (I) requires each
  `P(X | U = u)` to admit a local Markov screen. For pathological
  conditionals (e.g. non-standard-Borel `X | U = u`) this may fail even
  though the joint model is well-defined.
- **Cross-`u` coherence is quantitative in practice.** For finite `U`,
  Condition (II) may fail to shrink `∼_u` fully; a "partial" antecedent
  still gives partial identifiability. The taxonomy theorem in this
  paper handles only the full-coherence case; the partial case is a
  natural refinement.
- **No Lean formalisation.** Theorem SA-1's proof is a functional-
  intersection argument on equivalence relations; it is straightforward
  to formalise in the same style as `CommonSuffScreen.lean`'s
  Theorem-4-core, but that is future work.

---

## 7. Reproduction

There is no dedicated instrument for this paper — it is an *organizing*
theorem over Instruments 8, 9, 10, 11. Re-running each of those
instruments in turn (see paper §8 of *The Structural Intelligence
Conjecture*) verifies the individual rows of the taxonomy table.

An `experiments/antecedent_taxonomy_pair` would be an exact re-check
that each of the four rows' `q_u` families does satisfy (I) and (II) on
the specific setups Instruments 8–11 use. That is a natural follow-up.
