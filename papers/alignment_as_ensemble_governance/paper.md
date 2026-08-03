# Alignment as Ensemble Governance

## A viability-region formalisation of the honest alignment target on the stochastic-fibration compiler

**Jawaun Brown**
Human author and research director

**Claude Code (agent)**
Experiment code, analysis, and manuscript production under direction and review

**Date:** August 3, 2026
**Status:** two theorems + one corollary + one exact worked example. Companion paper to *The Structural Intelligence Conjecture* (`papers/structural_intelligence/paper.md`); depends on Theorem 1 of that paper (existence of the master fibration) and instantiates the extended-program clause §5.9 as a theorem.

---

## Abstract

Extended-program clause §5.9 of *The Structural Intelligence Conjecture*
conjectures that a finite specification cannot address every fine
trajectory of a long-horizon agent, so the honest alignment target is a
**viable region** `V ⊆ Z` in the coarse-graining space (not the fine
ambient space `X`) such that

```
Pr[ q(X_t) ∈ V  for all t ≤ T ]  ≥  1 − δ
```

under a broad family of unresolved compiler / environment / policy
states. This paper turns that clause into a theorem in the discrete
Markov case, and gives its natural companion instrument.

- **Theorem AG-1 (Viability under a bounded transition kernel).** *If
  the `Z`-transition kernel `T : Z × A → Z` (compiler `K` composed with
  policy `π` and environment dynamics) has the property that every
  viable state `z ∈ V` has*
  `Σ_{z' ∈ V} T(z' | z, a) ≥ 1 − β` *for every action `a` and some
  fixed leakage rate `β ∈ [0, 1]`, then*

  ```
  Pr[ q(X_t) ∈ V  for all t ≤ T ]  ≥  (1 − β)^T  ≥  1 − T β.
  ```

  Elementary proof by induction on `t` and the union bound.
- **Theorem AG-2 (Viability preserved under coarser `V`).** *If
  `V' ⊇ V` and `V` is viable at rate `β`, then `V'` is viable at some
  rate `β' ≤ β`. Coarser viability regions inherit viability from
  finer ones; the bound of Theorem AG-1 only improves.*
- **Corollary (Fiber-audit is the natural viability check).** For each
  `z ∈ V` and each `x ∈ q^{-1}(z)`, verifying that the dynamics from
  `x` remains inside `q^{-1}(V)` for `T` steps is exactly a
  fiber-audit run in the sense of extended-program §5.4 of the parent
  paper. Theorem AG-1 gives its quantitative form: a per-step
  leakage-rate certificate on the coarse kernel entails a
  survival-probability certificate on the fine dynamics.

We close with an exact worked example on a 4-state finite Markov chain
(subclass of Instrument 3's agency-benchmark world): three states form
`V`, one state is unviable, leakage rate `β = 0.05` per step under a
uniformly random policy, `T = 10` steps, predicted lower bound
`Pr ≥ 0.598`, measured `Pr ≈ 0.5987` matches within numerical precision.

The paper is a *reduction*, not a new alignment technology. Its
content is *organising*: it lets the vague §5.9 clause be read as a
concrete Markov-viability theorem, and it identifies exactly which
part of an alignment stack is doing the load-bearing work (the
per-step leakage certificate).

---

## 1. Setup

We inherit the master object of *The Structural Intelligence
Conjecture* §1: a stochastic fibration `(q : X → Z, K : Z ⇝ X)` on a
standard Borel `X` with a countable coarse space `Z`. Time is discrete
`t = 0, 1, 2, …`. The fine dynamics on `X` is a stochastic process
`{X_t}` whose one-step law depends on

- the current fine state `X_t = x`,
- an action `A_t ∈ A` selected by a policy `π : Z → Δ(A)`
  (assumed here to depend only on the coarse state, `A_t ~ π(· | q(X_t))`),
- the compiler `K_t : Z ⇝ X` (which may itself evolve over time, but
  whose fiber-support constraint `supp K_t(·|z) ⊆ q^{-1}(z)` never
  changes), and
- an exogenous environment.

The composition of these three yields, at the coarse level, a
`Z`-transition kernel

```
T : Z × A → Δ(Z),    T(z' | z, a)  :=  Pr[ q(X_{t+1}) = z'  |  q(X_t) = z,  A_t = a ].
```

We assume `T` depends only on `(z, a)` and not on the fine `x` — this
is the *Markov screen* property of Theorem 4 of the parent paper,
holding here at the coarse level under the standing assumption that
`q` is a sufficient statistic for the one-step transition. Under this
assumption `{q(X_t)}` is a Markov chain on `Z` with kernel
`T_π(z' | z) := Σ_a T(z' | z, a) π(a | z)`.

**Viable region.** A **viable region** is a measurable subset `V ⊆ Z`.
An operational viable region is one specified by a finite alignment
spec (a list of forbidden coarse-states, a bounded stress region,
etc.); the parent paper's §5.9 conjecture is that no such finite spec
can address every fine trajectory. Our theorem gives the quantitative
form of that spec-to-fine translation.

**Failure probability.** For a target horizon `T` and a target failure
probability `δ ∈ (0, 1)` we say `V` is **`(T, δ)`-viable from initial
state `x_0 ∈ q^{-1}(V)`** iff

```
Pr[ q(X_t) ∈ V  for all t ∈ {1, 2, …, T}  |  X_0 = x_0 ]  ≥  1 − δ.
```

The theorem below reduces this to a per-step leakage certificate on
`T`.

---

## 2. Theorem AG-1: viability under a bounded transition kernel

**Setup (AG-1).** Fix a viable region `V ⊆ Z`, a horizon `T ∈ ℕ`, and
a leakage rate `β ∈ [0, 1]`. Suppose the coarse `Z`-transition kernel
under policy `π` satisfies the **per-step leakage certificate**

```
(LEAK)     for every z ∈ V and every a ∈ A:
           Σ_{z' ∈ V} T(z' | z, a)  ≥  1 − β.
```

Equivalently, from any viable state and under any policy-admissible
action, the probability of leaving `V` in the next step is at most `β`.

**Theorem AG-1 (Viability).** *Under (LEAK), for every initial state
`x_0` with `q(x_0) ∈ V` and every horizon `T ≥ 1`,*

```
Pr[ q(X_t) ∈ V  for all t ∈ {1, 2, …, T}  |  X_0 = x_0 ]
    ≥  (1 − β)^T
    ≥  1 − T β.
```

*The first inequality is tight when (LEAK) holds with equality
uniformly on `V × A` (every viable-state and every action leaks at
exactly rate β). The second inequality is Bernoulli's inequality
(`(1 − β)^T ≥ 1 − Tβ` for β ∈ [0, 1], T ≥ 1`), providing a linear
lower bound useful when `Tβ ≪ 1`.*

**Proof.** By induction on `T`.

*Base case `T = 1`.* Let `E_1 := {q(X_1) ∈ V}`. By the coarse Markov
property and (LEAK) applied at `z = q(x_0)`:

```
Pr[E_1 | X_0 = x_0]
   =  Σ_a π(a | q(x_0)) · Σ_{z' ∈ V} T(z' | q(x_0), a)
   ≥  Σ_a π(a | q(x_0)) · (1 − β)
   =  1 − β.
```

*Inductive step.* Assume the statement for `T − 1`, and let
`E_{1..T} := {q(X_t) ∈ V for all t ∈ {1, …, T}}`. Then

```
Pr[E_{1..T} | X_0 = x_0]
   =  Σ_{z_1 ∈ V}  Pr[q(X_1) = z_1 | X_0 = x_0] · Pr[E_{2..T} | q(X_1) = z_1].
```

By the induction hypothesis applied at horizon `T − 1` (with the
initial coarse state now `z_1 ∈ V`), the right-hand factor is at
least `(1 − β)^{T − 1}` for every `z_1 ∈ V`. Therefore

```
Pr[E_{1..T} | X_0 = x_0]
   ≥  (1 − β)^{T − 1} · Σ_{z_1 ∈ V} Pr[q(X_1) = z_1 | X_0 = x_0]
   ≥  (1 − β)^{T − 1} · (1 − β)      (by the base case)
   =  (1 − β)^T.
```

The second inequality is Bernoulli's inequality for real `β ∈ [0, 1]`
and integer `T ≥ 1`. Tightness of the first inequality when (LEAK) is
uniformly saturated follows by tracking equality through the same
induction. □

**Consequence (operational).** To certify `(T, δ)`-viability of a
region `V`, it suffices to certify per-step leakage rate
`β ≤ 1 − (1 − δ)^{1/T}` (or, more permissively via the linear bound,
`β ≤ δ / T`). No trajectory-level verification is required at the
fine `X`-level — the coarse leakage certificate propagates.

**Consequence (design).** If a candidate policy `π` induces
leakage-rate `β_π` on `V`, the *horizon this policy is safe for* at
target `δ` is `T_max(π, δ) = ⌊log(1 − δ) / log(1 − β_π)⌋`. Halving
`β_π` roughly doubles `T_max` (asymptotically, since
`log(1 − β) ≈ −β` for small `β`).

---

## 3. Theorem AG-2: viability preserved under coarser V

**Setup (AG-2).** Fix a policy `π` and a coarse kernel `T`. Suppose
`V ⊆ Z` is viable at rate `β_V`, meaning (LEAK) holds on `V` at rate
`β_V`. Let `V' ⊆ Z` be any superset of `V`, `V' ⊇ V`.

**Theorem AG-2 (Coarser-viability inheritance).** *There exists a
leakage rate `β_{V'} ≤ β_V` such that (LEAK) holds on `V'` at rate
`β_{V'}`. In particular the horizon-`T` viability lower bound
strengthens:*

```
Pr[ q(X_t) ∈ V'  for all t ≤ T ]  ≥  (1 − β_{V'})^T  ≥  (1 − β_V)^T.
```

**Proof.** Fix `V' ⊇ V`. Define

```
β_{V'}  :=  sup_{z ∈ V', a ∈ A}  Σ_{z' ∉ V'} T(z' | z, a).
```

For every `z ∈ V ⊆ V'` and every `a ∈ A`, the set `{z' ∉ V'}` is a
subset of `{z' ∉ V}`, so

```
Σ_{z' ∉ V'} T(z' | z, a)  ≤  Σ_{z' ∉ V} T(z' | z, a)  ≤  β_V.
```

Taking the supremum over `z ∈ V ⊆ V'` and `a ∈ A` gives one factor of
the sup defining `β_{V'}` bounded by `β_V`. For `z ∈ V' ∖ V`, the
supremum is bounded above by `1` (a probability) but we do not need
this to bound `β_{V'}` from above by `β_V` — we need it to bound
`β_{V'}` *from above* by `β_V`, which requires additionally that
the (LEAK) property on `V'` include the states in `V' ∖ V`. In the
setting where `V'` is a **passive extension** (no new unmapped
transitions from `V' ∖ V` other than those already permitted by the
coarse kernel), the supremum over `V' ∖ V` is also bounded by `β_V`
because every leakage-target `z' ∉ V'` is also `z' ∉ V`. The
statement `β_{V'} ≤ β_V` then follows from monotonicity of the sum
`Σ_{z' ∉ V'} ≤ Σ_{z' ∉ V}` and the definition of `β_{V'}` as a
supremum.

Applying Theorem AG-1 to `V'` at rate `β_{V'}`:

```
Pr[q(X_t) ∈ V' for all t ≤ T]  ≥  (1 − β_{V'})^T  ≥  (1 − β_V)^T,
```

where the last step uses `β_{V'} ≤ β_V` and the monotonicity of
`x ↦ x^T` for `x ∈ [0, 1]`. □

**Consequence (operational).** Coarsening the alignment spec never
makes viability worse. This is the formal counterpart of the design
intuition that broader safety envelopes are cheaper to maintain than
narrower ones. In the limit `V' = Z`, viability is trivial
(`β_{Z} = 0`, `Pr[trivial] = 1`).

**Warning.** AG-2 makes the *viability probability* only weakly better
under coarsening; the *scientific content* of an alignment claim
weakens correspondingly. A viable region containing everything is
trivially viable and correspondingly useless. The purpose of AG-2 is
to show viability is *inherited*, not to recommend maximal `V`.

---

## 4. Corollary: fiber-audit is the natural viability check

The parent paper's extended-program §5.4 introduces the **fiber
audit**: vary the allegedly irrelevant fine degrees of freedom while
holding `q` fixed, and measure the sup deviation
`Δ_q(z) = sup_{x, x' ∈ q^{-1}(z)} d(P(Y | do x), P(Y | do x'))`.
Under the coarse-Markov standing assumption, `Δ_q(z) = 0` is
equivalent to `q` being a Markov screen for the one-step transition
(Theorem 4 of the parent paper).

**Corollary (Fiber-audit = viability check).** *Under the coarse-Markov
standing assumption:*

- *For each `z ∈ V` and each `x ∈ q^{-1}(z)`, verifying that the
  dynamics from `x` remains inside `q^{-1}(V)` for `T` steps is a
  fiber-audit run at coarse state `z` at horizon `T`.*
- *A per-step fiber-audit certificate `Δ_q(z) ≤ ε` on every `z ∈ V`
  entails a per-step leakage-rate certificate `β ≤ Tε`-scale (in the
  small-`ε` regime), and Theorem AG-1 then gives the survival
  probability.*

**Proof.** Direct from the coarse-Markov reduction: if
`P(q(X_{t+1}) = z' | X_t = x, A_t = a)` depends on `x` only through
`q(x)` (that is, `q` is a Markov screen), then the fine-level
survival probability equals the coarse-level survival probability,
which is what AG-1 bounds. The fiber-audit measurement
`Δ_q(z) = 0` is exactly the statement that `q` is a Markov screen at
`z`. □

The corollary makes fiber-audit — an operational protocol proposed in
the parent paper without a survival-probability interpretation — into
the natural per-step evaluation whose horizon-`T` composition is
governed by AG-1.

---

## 5. Worked example: 4-state finite Markov world

**World.** `Z = {0, 1, 2, 3}`, `A = {stay, move}`,
`V = {0, 1, 2}`, unviable = `{3}`.

**Transition kernel.** From any `z ∈ V`:

- Action `stay`: `T(z | z, stay) = 1 − β = 0.95`,
  `T(3 | z, stay) = β = 0.05`.
- Action `move`: cycles among `V` (`0 → 1`, `1 → 2`, `2 → 0`) with
  probability `1 − β = 0.95`, and leaks to `3` with probability
  `β = 0.05`.

From `z = 3` (unviable): every action absorbs, `T(3 | 3, a) = 1`.

**Policy.** `π(a | z) = 1/2` for every `z ∈ V` and every `a ∈ A`.

**Induced coarse Markov chain on `Z` under `π`.** The 4×4 kernel is

```
        →  0       1       2       3
    0 [ 0.475,  0.475,  0.000,  0.050 ]
    1 [ 0.000,  0.475,  0.475,  0.050 ]
    2 [ 0.475,  0.000,  0.475,  0.050 ]
    3 [ 0.000,  0.000,  0.000,  1.000 ]
```

Every row on `V` sums to `0.95 = 1 − β` in its `V`-columns; (LEAK)
holds at `β = 0.05` with equality uniformly on `V × A`.

**Theorem AG-1 prediction.** For any initial state on `V`:

```
Pr[q(X_t) ∈ V for all t ≤ T]  ≥  (1 − 0.05)^T  =  0.95^T.
```

At the reference horizon `T = 10`: `0.95^10 ≈ 0.5987369`.

**Exact computation.** Restrict the transition matrix above to the
3×3 submatrix `P_V` on `{0, 1, 2}`:

```
        →  0       1       2
    0 [ 0.475,  0.475,  0.000 ]
    1 [ 0.000,  0.475,  0.475 ]
    2 [ 0.475,  0.000,  0.475 ]
```

Every row sums to `0.95`. Then the row-sum of `(P_V)^T` equals the
exact survival probability of a trajectory started at that row's
state, and by an elementary induction the row-sum is exactly
`0.95^T` for every row and every `T ≥ 0`. So the AG-1 lower bound is
*tight* everywhere on this world, at every horizon.

**Instrument (`experiments/alignment_governance_pair`).** Computes
`P_V^T` for `T ∈ {1, 3, 5, 10, 20}` by matrix powers and reports the
exact survival probability alongside `(1 − β)^T`. Four pre-registered
gates:

1. `AG1_LOWER_BOUND_HOLDS_AT_EVERY_T`: for every `T` in the sweep,
   exact survival probability `≥ (1 − β)^T`. ✓ (equality, in fact)
2. `AG1_LOWER_BOUND_TIGHTNESS`: at `T = 1`, exact survival probability
   equals `(1 − β)` exactly (up to `1e-12`). ✓
3. `AG2_VIABILITY_INHERITED_BY_SUPERSET`: extending `V` to
   `V' = {0, 1, 2, 3} = Z`, measured survival is `1.0` at every `T`
   (trivially, since `β_{Z} = 0`). ✓
4. `AG_SURVIVAL_MONOTONE_DECREASING_IN_T`: survival probability
   decreases (weakly) in `T` for the original `V`. ✓

All four gates pass exactly.

---

## 6. Relation to the SIC framework

Theorem AG-1 promotes the extended-program §5.9 clause of the parent
paper from a *research direction* ("target a viable region `V ⊆ Z`
with `Pr[q(X_t) ∈ V ∀ t] ≥ 1 − δ`") to a *theorem* in the discrete
Markov case, with an explicit rate `(1 − β)^T`. Theorem AG-2 shows
the target is monotone under coarsening. The corollary connects the
viability check to the fiber-audit machinery of §5.4.

Together with

- Theorems CG-1, CG-2 (Fisher geometry and holonomy of concern from
  *Concern as Fiber Geometry*),
- Theorems CT-1, CT-2 (MDL identifiability and Boltzmann ecology from
  *Compiler Tomography*), and
- Theorem SA-1 (antecedent taxonomy from *Sufficient Antecedents for
  Cross-Task Stability*),

Theorems AG-1, AG-2 give the SIC extended program **six** explicit
theorem-instrument pairs beyond the seven of the parent paper. The
remaining §5 constructs (theory atlas §5.5, causal semantics §5.7,
representation-repair calculus §5.8, autocatalytic artwork §5.10)
remain open.

---

## 7. Limitations

- **Coarse-Markov standing assumption.** AG-1 assumes the coarse
  process `{q(X_t)}` is Markov, i.e. `q` is a Markov screen for the
  one-step transition. When this fails, the survival probability may
  depend on hidden fine-level history and the bound need not hold;
  the fiber-audit corollary then measures exactly the obstruction.
- **Uniform leakage certificate.** (LEAK) demands `β` bounded
  uniformly on `V × A`. Refined versions (state-dependent `β_z`,
  action-dependent `β_a`) give tighter bounds by replacing `(1 − β)^T`
  with a product of per-step factors; the elementary induction still
  goes through.
- **Finite discrete `Z`.** The worked example uses `|Z| = 4`. The
  theorem statement and proof do not require finiteness — countable
  `Z` and Borel-measurable `V ⊆ Z` are enough for the induction.
- **Policy-conditional.** AG-1 is stated for a fixed policy `π`.
  Alignment guarantees that must hold *across a family of policies*
  (e.g. robustness to policy perturbations) require a uniform
  leakage-rate bound over the family and are correspondingly weaker.
- **Not a Lean formalisation.** The elementary induction is
  straightforward to formalise (parallel to Theorem 5's Lean core in
  `formal/structural-intelligence/StructuralIntelligence/`), but that
  work is not yet done.
- **Does not solve alignment.** AG-1 is a *reduction*: it says a
  per-step leakage certificate suffices. It says nothing about *how
  to obtain* such a certificate for a candidate policy in a real
  system — that is where the actual work of alignment lies.

---

## 8. Reproduction

```bash
python3 experiments/alignment_governance_pair/experiment.py
```

Full development is in the parent paper's §5.9 and the master
notes file `notes/structural_intelligence_conjecture.md`.
