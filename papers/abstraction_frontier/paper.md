# The Abstraction Frontier

## A Pareto antichain of quotients trading task-sufficiency, dynamical closure, coding cost, and control regret

**Jawaun Brown**
Human author and research director

**Claude Code (agent)**
Experiment code, analysis, and manuscript production under direction and review

**Date:** August 3, 2026
**Status:** two elementary theorems + one worked example (4-bit Boolean world). Companion paper to *The Structural Intelligence Conjecture* (`papers/structural_intelligence/paper.md`) and to *Sufficient Antecedents for Cross-Task Stability* (`papers/sufficient_antecedents/paper.md`); depends on Theorem 4 of the parent paper (cross-task stability via a shared Markov screen).

---

## Abstract

Extended-program §5.3 of *The Structural Intelligence Conjecture*
conjectures that the set of "reasonable" quotients `q : X → Z` for a
task family `{Y_α}` is not a total order but a *Pareto frontier*
trading four axes: task-sufficiency `I(Y_α; X | q(X))`, dynamical
closure `I(Z_{t+1}; X_t | Z_t, A_t)`, coding cost `H_0(Z) = log|image(q)|`,
and control regret. This paper turns that conjecture into two clean
theorems:

- **Theorem AF-1 (Frontier is an antichain).** *The Pareto set of a
  candidate quotient lattice `Q` — quotients `q ∈ Q` such that no
  other `q' ∈ Q` weakly dominates `q` on all four axes and strictly on
  at least one — is an antichain in the product order. The Pareto set
  is monotone non-decreasing under lattice refinement: adding
  candidates to `Q` can only add (never remove) members from the
  frontier.*
- **Theorem AF-2 (Frontier reduces to CSS when tasks are decisive).**
  *If a common sufficient statistic `q*` exists for `{Y_α}` in the
  sense of Theorem 4 of the parent paper, then the Pareto frontier
  contains `q*`, and every Pareto member with zero task-sufficiency is
  at least as fine as `q*` on the lattice. If `q*` is unique and the
  dynamical-closure axis varies non-trivially with granularity, the
  zero-task-sufficiency portion of the frontier is a lattice segment
  rising from `q*` to the identity, ordered by coding cost. In the
  static case (dynamical closure and control regret constant across
  quotients), the zero-task-sufficiency portion collapses to `{q*}`
  alone: the identity is strictly dominated by `q*` on coding cost.*

The theorems are elementary: AF-1 is a definitional consequence of
Pareto optimality on a product order; AF-2 is Theorem 4 restated on the
Pareto-frontier side. Together they give a formal antidote to
"the best quotient" thinking: two representations can be equally
sufficient and equally cheap on some axes yet remain incomparable on
the others, so neither dominates the other, and both are honestly on
the frontier.

An exact instrument (`experiments/abstraction_frontier_pair`) exhibits
the antichain on the 4-bit Boolean world of Instrument 4. The library
of 23 quotients (concern-parameter lattice from that instrument) yields
a **two-element frontier `{constant, joint(parity{0,1}, parity{2,3})}`**:
the constant map (min-cost, worst-sufficiency endpoint) and the true
`Z` (best-sufficiency, next-to-min-cost). The identity is strictly
dominated by `Z`, and every single-bit or single-parity quotient is
strictly dominated by the constant. This is the *static-case collapse*
of AF-2, exhibited exactly and pre-registered as a gate.

---

## 1. Setup

We inherit the master object of *The Structural Intelligence
Conjecture* §1: a stochastic fibration `(q : X → Z, K : Z ⇝ X)` on a
standard Borel `X`, together with a *task family* `{Y_α : α ∈ A}` on
`X` and a *candidate quotient lattice* `Q` — a set of measurable maps
`q : X → Z_q` (each with its own coarse space `Z_q`) that we consider
as possible coarse-grainings.

For each `q ∈ Q` we define four scalar axes (all *lower = better*):

- **Task-sufficiency.**
  `TS(q) := sup_α I(Y_α ; X | q(X))`, with the supremum taken over the
  task family. For deterministic `Y_α = f_α(X)`, sufficiency reduces to
  `sup_α H(Y_α | q(X))` under a fixed base distribution `P` on `X`.
  Zero iff `q` is a *common sufficient statistic* (CSS) for `{Y_α}`.
- **Dynamical closure.**
  `DC(q) := I(Z_{t+1} ; X_t | Z_t, A_t)`, the residual information
  the coarse next-state `Z_{t+1} := q(X_{t+1})` still carries about
  the current *fine* state `X_t` given the current coarse state
  `Z_t := q(X_t)` and action `A_t`. Zero iff `q` is *self-contained*
  as a dynamical system (the coarse process is Markov on its own).
- **Coding cost.**
  `H_0(q) := log_2 |image(q)|`, the description length of a single
  code from `image(q)` in a uniform prefix-free code. This is the
  simplest granularity axis and lower-bounds any lossless code.
- **Control regret.**
  `CR(q) := V*(X) - V*(q(X))`, the loss in optimal value when a
  controller must condition its action only on `q(X)` rather than on
  `X`. Zero iff a controller optimal on `X` factors through `q`.

Write `axes(q) := (TS(q), DC(q), H_0(q), CR(q)) ∈ ℝ_{≥ 0}^4`.

**Standard Pareto.** For `q, q' ∈ Q`, we say `q'` **weakly dominates**
`q` iff `axes(q')_i ≤ axes(q)_i` for every axis `i` and
`axes(q')_i < axes(q)_i` for at least one axis. The **Pareto frontier**
`F(Q)` is the subset of `Q` that no other member of `Q` weakly
dominates.

---

## 2. Theorem AF-1: the frontier is an antichain

**Theorem AF-1 (Frontier is an antichain).** *`F(Q)` is an antichain
in the product order on `ℝ_{≥ 0}^4`: no two members of `F(Q)` weakly
dominate each other. Moreover, `F(Q)` is monotone non-decreasing under
lattice refinement: for `Q ⊆ Q'`, every member of `F(Q)` that is not
weakly dominated by some new candidate in `Q' ∖ Q` remains in `F(Q')`,
and `F(Q')` may contain additional members from `Q' ∖ Q`.*

**Proof.**

*(Antichain.)* Suppose `q, q' ∈ F(Q)` and `q'` weakly dominates `q`.
Then by definition of the Pareto frontier, `q ∉ F(Q)`, contradicting
`q ∈ F(Q)`. So no two Pareto members weakly dominate each other,
i.e. `F(Q)` is an antichain.

*(Monotonicity.)* Let `Q ⊆ Q'`. Take `q ∈ F(Q)`. If no member of
`Q' ∖ Q` weakly dominates `q`, then no member of `Q' ⊇ Q` does either
(since `q` was Pareto in `Q`), so `q ∈ F(Q')`. Conversely, a member
`q'' ∈ Q' ∖ Q` is in `F(Q')` iff no member of `Q'` weakly dominates
it; there is no a-priori reason for this to fail, so `Q' ∖ Q` can
contribute additional Pareto members. Hence `F(Q')` contains every
`q ∈ F(Q)` not dominated by a new candidate, plus possibly new
members. □

**Corollary (No total order).** *For `|F(Q)| ≥ 2` there is no total
order on `F(Q)` induced by the product order on `ℝ_{≥ 0}^4`. Different
frontier members correspond to genuinely different trade-offs and are
incomparable.*

**Remark (Trivial closure and identity endpoints).** The constant map
`q_⊥` (image size 1) always has `H_0(q_⊥) = 0`; no other quotient can
match it on coding cost, so `q_⊥` is on the frontier whenever `TS`,
`DC`, and `CR` at the constant are finite (which they always are for a
bounded task family and finite `V*`). The identity `q_⊤` (image `X`)
always has `TS(q_⊤) = 0` on the deterministic-task case but has the
maximum coding cost `H_0(q_⊤) = log_2 |X|`. Whether `q_⊤` is on the
frontier depends on whether any other quotient matches `TS(q_⊤) = 0`
at strictly smaller `H_0` — precisely the content of Theorem AF-2.

---

## 3. Theorem AF-2: the frontier and the CSS

**Setup (Theorem AF-2).** Assume the task family `{Y_α}` admits a
common sufficient statistic `q* : X → Z*` in the sense of Theorem 4 of
the parent paper: `Y_α ⫫ X | q*(X)` for every `α`, equivalently
`TS(q*) = 0`.

**Theorem AF-2 (Frontier reduces to CSS when tasks are decisive).**
*Under this assumption:*

1. *`q* ∈ F(Q)`.*
2. *Every `q ∈ F(Q)` with `TS(q) = 0` is at least as fine as `q*` on
   the lattice of quotients of `X` (equivalently, `q` refines `q*`).*
3. *If `q*` is unique among CSS candidates in `Q` and if the
   dynamical-closure axis `DC` varies non-trivially with granularity
   (finer quotients strictly reduce `DC`), then the zero-task-
   sufficiency portion of `F(Q)` is a lattice segment rising from
   `q*` to the identity `q_⊤`, ordered by `H_0(q)`.*
4. *In the **static case** — `DC` and `CR` constant across all
   `q ∈ Q` — the zero-task-sufficiency portion of `F(Q)` collapses to
   `{q*}` alone: any strictly finer sufficient quotient is dominated by
   `q*` on coding cost.*

**Proof.**

*(1) `q* ∈ F(Q)`.* Suppose some `q' ∈ Q` weakly dominates `q*`. Then
`TS(q') ≤ TS(q*) = 0`, so `TS(q') = 0`; the domination is not on the
`TS` axis. Since `q*` has `H_0(q*) = log_2 |image(q*)|` and `q'` weakly
dominates `q*` on `H_0`, we have `|image(q')| ≤ |image(q*)|`, so `q'`
is at least as coarse as `q*`. But `TS(q') = 0` means `q'` is also
sufficient. A sufficient quotient no coarser than `q*` (the coarsest
CSS by Theorem 4's corollary) must equal `q*` up to
sufficiency-preserving refinement. Then `q'` is not *strictly* better
than `q*` on any axis, contradicting weak domination. So `q* ∈ F(Q)`.

*(2) Sufficient Pareto members refine `q*`.* Take `q ∈ F(Q)` with
`TS(q) = 0`. By Theorem 4's corollary applied to `Y_α ⫫ X | q(X)`,
`σ(q)` is a sufficient sub-σ-algebra of `σ(X)` containing `σ(Y_α)`
after the sufficiency reduction; combined with `σ(q*)` being the
coarsest such, `σ(q*) ⊆ σ(q)`, i.e. `q` refines `q*`. So every
sufficient Pareto member is at least as fine as `q*`.

*(3) The zero-`TS` segment.* Under the two assumptions, the
zero-`TS` portion consists of quotients refining `q*`. Along that
refinement chain `q* → q_1 → q_2 → ... → q_⊤`, `H_0` strictly
increases (by definition of refinement adding new lattice cells) while
`TS` stays zero. If `DC` strictly decreases along refinement, then no
two elements of the chain dominate each other: coarser members have
lower `H_0` but higher `DC`, finer members lower `DC` but higher
`H_0`. So every element of the chain is on the frontier, and the
frontier's zero-`TS` portion is the chain itself.

*(4) Static-case collapse.* If `DC` and `CR` are constant across `Q`,
then those two axes never separate quotients, and the effective Pareto
reduces to `(TS, H_0)`. Every strictly finer sufficient quotient
`q ≻ q*` has `TS = 0 = TS(q*)` and `H_0(q) > H_0(q*)`; `q*` weakly
dominates `q` (equal on `TS`, `DC`, `CR`; strictly better on `H_0`). So
`q ∉ F(Q)`, and the zero-`TS` portion of `F(Q)` collapses to
`{q*}`. □

**Corollary (Two representations can be equally right yet incomparable).**
*Suppose `q_1 ≠ q_2 ∈ F(Q)` and both have `TS(q_1) = TS(q_2) = 0`.
By AF-1, `q_1` and `q_2` do not weakly dominate each other, so they
differ on at least one of `DC`, `H_0`, `CR` in opposite directions —
`q_1` is better on one, `q_2` is better on another. Neither can be
called "the right" quotient without further weight on the axes; the
frontier itself encodes the honest trade-off.*

This is the formal antidote to *"the best quotient"* thinking. Two
disentangled representations that agree on cross-task sufficiency can
still legitimately disagree on how compact their code is or how
self-contained their dynamics are, and both remain on the Pareto
frontier as different balances of the same four axes.

---

## 4. Worked example: 4-bit Boolean world

**World.** `X = {0, 1}^4` (16 elements, uniform base distribution).
Latent `Z(x) := (x_0 ⊕ x_1, x_2 ⊕ x_3)`, image size 4.

**Task family** (shared-through-`Z` from Instrument 4):

- `Y_1 = parity{0, 1}`,
- `Y_2 = parity{2, 3}`,
- `Y_3 = parity{0, 1, 2, 3} = Y_1 ⊕ Y_2`.

Each `Y_α` factors through `Z`, so `Z` is a CSS and `TS(Z) = 0`.

**Quotient lattice.** The concern-parameter lattice from Instrument 4
(`experiments/cross_task_sufficiency`), 23 candidates:

- `constant` (image 1, `H_0 = 0`),
- 15 subset parities `parity{S}` for `S ⊆ {0, 1, 2, 3}, S ≠ ∅`
  (image 2, `H_0 = 1`),
- 3 joint pair-parities at image 4, `H_0 = 2`
  (`joint(parity{0,1}, parity{2,3}) = Z`,
  `joint(parity{0,2}, parity{1,3})`,
  `joint(parity{0,3}, parity{1,2})`),
- 2 joint bit-reads at image 4, `H_0 = 2`
  (`joint(bit_0, bit_1)`, `joint(bit_2, bit_3)`),
- 1 joint triple-bit-read `joint(bit_0, bit_1, bit_2)` at image 8,
  `H_0 = 3`,
- `identity` (image 16, `H_0 = 4`).

**Axes.** `DC = CR = 0` for every `q` — the world is static and there
is no controller, so these two axes are constants by convention. The
effective Pareto reduces to `(TS, H_0)`.

**Exact `TS`.** Each `Y_α` is a balanced Boolean, so `H(Y_α) = 1` bit.
Under the uniform base distribution:

- `TS(constant) = 1` (no information from `q`, every `Y_α`'s residual
  entropy is its own entropy 1).
- Any subset parity `parity{S}` reveals a single bit of information
  that is generically independent of the parity that defines `Y_α`;
  a direct computation gives `TS(parity{S}) = 1` for every `S` (one
  task is deterministic, the other two remain balanced).
- Only `Z` and any strictly-finer joint on `X` give `TS = 0`. Among
  the 23 candidates, exactly two do: `Z` itself (`H_0 = 2`) and the
  `identity` (`H_0 = 4`). Every other joint (non-`Z` pair-parity,
  joint bit-read, triple bit-read) has `TS = 1` (at least one `Y_α`
  is not determined by the joint).

**Pareto set.** With `DC = CR = 0`, standard Pareto on `(TS, H_0)`:

| Quotient | `H_0` | `TS` | Dominator |
|---|---:|---:|---|
| `constant` | 0 | 1 | — (frontier) |
| every subset parity | 1 | 1 | `constant` (better `H_0`, equal `TS`) |
| non-`Z` pair-parities and bit-joints | 2 | 1 | `constant` |
| `Z = joint(parity{0,1}, parity{2,3})` | 2 | 0 | — (frontier) |
| triple bit-read | 3 | 1 | `constant` |
| `identity` | 4 | 0 | `Z` (better `H_0`, equal `TS`) |

**Frontier = `{constant, Z}`.** A two-element antichain: the constant
is incomparable with `Z` (better `H_0`, worse `TS`), and `Z` is
incomparable with the constant (worse `H_0`, better `TS`).

This is the **static-case collapse** of Theorem AF-2 clause (4): even
though `identity ≻ Z` on the lattice with `TS(identity) = 0`, it is
dominated by `Z` on coding cost, so the zero-`TS` portion of the
frontier collapses to `{Z}`. In a dynamical setting where finer
quotients strictly reduce `DC`, the identity (or intermediate
refinements between `Z` and identity) would rejoin the frontier as
alternative trade-offs.

**Interpretation.** The `constant` sits on the frontier because it is
the cheapest representation to code (0 bits), but pays for that with
maximal task-residual entropy. `Z` sits on the frontier because it is
the *cheapest* sufficient representation (2 bits, strictly less than
the 4-bit identity), and no coarser sufficient representation exists.
Every other quotient in the 23-element lattice is honestly dominated —
by the constant on the `TS = 1` plateau, by `Z` on the `TS = 0`
plateau — and thus not on the frontier.

---

## 5. Instrument: `experiments/abstraction_frontier_pair`

Exact witness of Theorems AF-1 and AF-2 on the setup above.

- Enumerate the 23-quotient library.
- For each `q`, compute `TS`, `H_0`, `DC := 0`, `CR := 0` exactly.
- Compute the Pareto frontier under standard weak-domination.
- Pre-registered gates (all six pass exactly):
  - `af1_frontier_is_antichain`: no two Pareto members dominate.
  - `af1_frontier_contains_true_Z`: `Z` is on the frontier.
  - `af1_frontier_contains_constant`: the constant is on the frontier.
  - `af1_identity_is_dominated_in_static_case`: `Z` weakly dominates
    the identity (equal `TS`, strictly better `H_0`).
  - `af2_sufficient_frontier_is_true_Z_alone`: among Pareto members
    with `TS = 0`, the only one is `Z`.
  - `af2_no_pareto_strictly_finer_than_true_Z`: no frontier member
    is strictly finer than `Z` on the lattice.

The instrument is deterministic (no random seeds, no Monte Carlo) and
the frontier is `{constant, joint(parity{0,1}, parity{2,3})}` exactly.

---

## 6. Relation to the SIC framework

Theorem AF-1 turns extended-program §5.3 from a *research direction*
into a *theorem* about the shape of the reasonable-quotient set: an
antichain, not a total order, monotone under lattice refinement.
Theorem AF-2 links that shape back to Theorem 4 of the parent paper —
the CSS `q*` is on the frontier and every zero-task-sufficiency
frontier member refines it. Together with:

- Theorem CG-1 / CG-2 (concern as fiber geometry, Fisher metric and
  holonomy),
- Theorem CT-1 / CT-2 (compiler tomography, MDL identifiability and
  compiler ecology),
- Theorem SA-1 (antecedent taxonomy — four canonical `(U, P)` recipes
  populating Theorem 4),

the SIC extended program now has *six* explicit theorem-instrument
pairs beyond the six of the parent paper. The remaining §5 constructs
(theory atlas §5.5, causal semantics §5.7, representation-repair
calculus §5.8, alignment as ensemble governance §5.9, autocatalytic
artwork §5.10) remain open — each is a direction rather than a
theorem.

The frontier framing sharpens the SIC honesty condition: representation
choice is not a single quotient-level answer but an antichain of
distinct trade-offs. Two disentangled representations can both be
"right" and remain incomparable — the frontier itself is the ground
truth.

---

## 7. Limitations

- **Static-case collapse is generic.** On a truly static world, the
  zero-`TS` portion of the frontier reduces to `{q*}` alone; the
  "segment from `q*` to identity" statement of AF-2 clause (3)
  requires the dynamical-closure or control-regret axes to move
  non-trivially with granularity. In many applications those axes
  *do* move (state-abstraction MDPs are the canonical example), but
  the 4-bit example instrumented here does not exercise them. A
  Markov-decision-process instrument would exhibit clause (3)
  directly.
- **`DC` and `CR` are convention-set to 0.** In this instrument the
  two dynamical/controller axes are set to 0 for every quotient by
  convention; they carry no dominance information. A follow-up
  instrument on a Markov chain with induced coarse dynamics
  `(Z_t, A_t) → Z_{t+1}` would compute `DC` exactly and let those axes
  contribute to Pareto selection.
- **Task-sufficiency assumes finite tasks.** The definition
  `TS(q) := sup_α I(Y_α ; X | q(X))` is well-defined for a finite (or
  countable) task family; for a continuum family, the supremum may
  not be attained, and a metric on the task family is needed for a
  robust extension.
- **No Lean formalisation.** AF-1 is a definitional consequence of
  Pareto optimality on a product order, straightforward to formalise
  once product-order lemmas from mathlib are imported. AF-2 uses
  Theorem 4's Markov-screen argument (already formalised in
  `CommonSuffScreen.lean`); the reduction argument would slot on top.
  Both are future work.

---

## 8. Reproduction

```bash
python3 experiments/abstraction_frontier_pair/experiment.py
```

Full development is in the parent paper's §5.3 and the notes file
`notes/structural_intelligence_conjecture.md`.
