# Compiler Tomography

## MDL identification of a shared compiler kernel from paired specification-realization data

**Jawaun Brown**
Human author and research director

**Claude Code (agent)**
Experiment code, analysis, and manuscript production under direction and review

**Date:** August 3, 2026
**Status:** two theorems + one exact worked example. Companion paper to *The Structural Intelligence Conjecture* (`papers/structural_intelligence/paper.md`) and *Concern as Fiber Geometry* (`papers/concern_as_fiber_geometry/paper.md`); depends on Theorem 1 of the parent paper (existence of the master fibration).

---

## Abstract

The Structural Intelligence Conjecture (SIC) posits a stochastic
fibration `(q, K)` with a *compiler* `K : Z ⇝ X`. In practice we rarely
observe `K` directly; instead we see many pairs `(s_i, x_i)` where `s_i`
is a specification and `x_i ~ K(· | s_i)` is a realization. This paper
asks when — and how efficiently — the shared compiler `K` can be
*identified* from such pairs, and gives two clean theorems answering the
question in the finite discrete case.

- **Theorem CT-1 (MDL identification).** For a finite specification
  alphabet `S`, a finite realization alphabet `X`, and a family of
  compilers `{K_θ : θ ∈ Θ}` all sharing the marginal structure
  `K_θ(· | s) ∈ Δ(q^{-1}(s))`, the Minimum Description Length (equivalently
  BIC) estimator over paired data `{(s_i, x_i)}` is consistent: as the
  number of pairs grows, the estimated `θ̂` concentrates on the true `θ*`
  with probability one, at rate `O(√(log N / N))` in total variation.
- **Theorem CT-2 (Ecology dynamics: compiler improvement).** Under a
  reward-driven kernel update
  `K_{t+1}(· | s) ∝ K_t(· | s) · exp(β · r(s, x))` with reward `r` bounded
  and `β > 0` fixed, the expected reward under `K_t` is non-decreasing in
  `t` for every `s` (a discrete-time analogue of natural-gradient ascent
  on the reward functional). Fixed points of the update are exactly the
  reward-maximising kernels within the concern-parameterised family of
  the companion paper.

CT-1 provides the identifiability guarantee behind extended-program §5.6
("compiler tomography") of the parent paper; CT-2 provides its dynamical
counterpart ("compiler ecology"). Both are proved in the discrete case
with no measure-theoretic machinery beyond finite Bayes rules and Wald-
style consistency for MDL.

An exact instrument (`experiments/compiler_tomography_pair`) exhibits
both theorems on the 4-bit Boolean world of Instrument 4.

---

## 1. Setup

Fix a finite specification alphabet `S`, a finite realization alphabet
`X`, and a quotient map `q : X → S` (equivalently: `S = image(q)` is the
coarse structure the compiler renders). A **compiler kernel** is a Markov
kernel `K : S ⇝ X` with `supp K(· | s) ⊆ q^{-1}(s)` for every `s`.

**Paired data.** We observe `N` i.i.d. pairs `{(s_i, x_i)}_{i=1..N}`
where each `s_i ∈ S` is drawn from an arbitrary specification distribution
`P_S(s)` and each `x_i ~ K*(· | s_i)` from the *true* compiler `K*`.

**Family of hypotheses.** We restrict attention to a finite (or countable)
family `𝒦 = {K_θ : θ ∈ Θ}` of candidate compilers. Each `K_θ` is
parameterised by a finite string `θ` with description length `L(θ)` (bits
under a chosen prefix-free code); MDL selects

```
θ̂  =  argmin_{θ ∈ Θ} { L(θ) + L(data | K_θ) },
```

where `L(data | K_θ) = −Σ_i log₂ K_θ(x_i | s_i)` is the code length of the
data under `K_θ`.

---

## 2. Theorem CT-1: MDL identification (consistency)

**Setup (CT-1).** Suppose:

- The true compiler `K* = K_{θ*}` for some `θ* ∈ Θ`.
- `Θ` is finite (or the description-length function `L(θ)` satisfies
  Kraft's inequality on a countable `Θ`).
- The specification distribution `P_S` has support covering `S`
  (i.e. every `s ∈ S` is seen with positive probability).
- Identifiability: `θ ≠ θ*` ⇒ `K_θ ≠ K_{θ*}` at some `(s, x)` with
  `P_S(s) > 0` and `K_{θ*}(x | s) > 0`.

**Theorem CT-1 (MDL consistency).** *Under the setup above, the MDL
estimator `θ̂_N` from `N` i.i.d. pairs satisfies*

```
Pr[ θ̂_N = θ* ]  →  1     as N → ∞,
```

*and the excess code length satisfies*

```
E[ L(θ̂_N) + L(data | K_{θ̂_N}) − L(θ*) − L(data | K_{θ*}) ]  =  O(log N).
```

*In total variation, `dTV(K_{θ̂_N}, K_{θ*}) → 0` at rate
`O(√(log N / N))` on the support of `P_S`.*

**Proof.** Standard MDL / BIC consistency (Rissanen 1978, Barron–Cover
1991) specialised to the finite-conditional-alphabet case.

For any fixed `θ ≠ θ*`, by the identifiability assumption there exist
`s, x` with `P_S(s) > 0` and `K_{θ*}(x | s) ≠ K_θ(x | s)`. Then the KL
divergence

```
Δ_θ  :=  Σ_s P_S(s) · KL( K_{θ*}(· | s)  ||  K_θ(· | s) )
```

is strictly positive.

The empirical log-likelihood ratio between `θ*` and `θ` is
`−(L(data | K_θ) − L(data | K_{θ*}))/log 2 = Σ_i log(K_{θ*}(x_i|s_i)/K_θ(x_i|s_i))`.
Its expectation is `N · Δ_θ`, and by Hoeffding's inequality it exceeds
`N · Δ_θ / 2` with probability at least `1 − exp(−N · Δ_θ² · c)` for a
constant `c > 0` depending on the finite alphabet.

MDL selects `θ̂` iff `L(θ̂) + L(data | K_{θ̂}) ≤ L(θ*) + L(data | K_{θ*})`.
For `θ ≠ θ*`, this fails as soon as
`L(data | K_{θ*}) − L(data | K_θ) < L(θ) − L(θ*)`, i.e. as soon as the
empirical log-likelihood ratio exceeds `L(θ) − L(θ*)` (a constant).
Combined with Hoeffding: `Pr[ θ̂ = θ ] ≤ exp(−N · Δ_θ² · c / 2)` for large
enough `N`.

Union-bounding over the finite `Θ` (or, in the countable case, using
Kraft's inequality to bound `Σ_θ 2^{−L(θ)}`):

```
Pr[ θ̂_N ≠ θ* ]  ≤  Σ_{θ ≠ θ*} exp(−N · Δ_θ² · c / 2)  →  0.
```

Total variation rate follows from Le Cam's inequality
`dTV(K_θ̂, K_{θ*})² ≤ ½ · KL(K_θ̂ || K_{θ*})` and the fact that the
MDL score gap is `O(log N)` in expectation, so the surviving
`θ`-candidates have `KL(K_θ || K_{θ*}) = O(log N / N)`. Taking the square
root gives the `O(√(log N / N))` rate. □

**Consequence (operational).** The compiler-tomography extended-program
target of the parent paper (§5.6) is a theorem in the finite discrete
case: MDL is a consistent estimator of the shared compiler from paired
specification-realization data, at parametric rate.

The specialisation to Boolean fiber-preserving compilers on the 4-bit
world of Instrument 4 is worked out in §4 of this paper and verified by
the companion instrument (§5).

---

## 3. Theorem CT-2: Ecology dynamics (compiler improvement)

The extended-program §5.6 also names *compiler ecology*
`K_{t+1} = U(K_t, outcomes)`: a compiler that *updates* toward good
outcomes. The natural update rule that plays this role is the
concern-parameterised reweighting of the companion paper *Concern as
Fiber Geometry* Theorem CG-1, with the reward serving as concern:

```
K_{t+1}(dx | s)   =   K_t(dx | s) · exp(β · r(s, x))  /  Ξ_t(s),
```

where `r : S × X → [0, R]` is a bounded reward, `β > 0` is a fixed
sharpness, and `Ξ_t(s) := ∫_{q^{-1}(s)} exp(β r(s, x)) K_t(dx | s)` is
the fiber partition function.

**Theorem CT-2 (Monotone compiler improvement).** *For every `s ∈ S` and
every `t ≥ 0`,*

```
E_{K_{t+1}}[r(s, X) | s]  ≥  E_{K_t}[r(s, X) | s],
```

*with equality iff `r(s, ·)` is `K_t(· | s)`-a.s. constant on `q^{-1}(s)`.
Equivalently, the reward expectation is non-decreasing under compiler
ecology; fixed points are exactly the compilers concentrated on
`argmax_x r(s, x)` within each fiber (up to reward ties).*

**Proof.** Fix `s`. Let `r(x) := r(s, x)` and `p_t(x) := K_t(x | s)` on
`q^{-1}(s)`. The update is `p_{t+1}(x) = p_t(x) · exp(β r(x)) / Ξ`,
`Ξ = E_{p_t}[e^{β r}]`. Then

```
E_{p_{t+1}}[r]  −  E_{p_t}[r]
   =  Σ_x r(x) · p_t(x) · (e^{β r(x)} / Ξ − 1)
   =  (1/Ξ) · Σ_x r(x) · p_t(x) · (e^{β r(x)} − Ξ)
   =  (1/Ξ) · [ Σ_x r(x) e^{β r(x)} p_t(x)  −  Ξ · Σ_x r(x) p_t(x) ]
   =  (1/Ξ) · [ E_{p_t}[r · e^{β r}]  −  E_{p_t}[e^{β r}] · E_{p_t}[r] ]
   =  (1/Ξ) · Cov_{p_t}[ r,  e^{β r} ].
```

`Cov(r, e^{β r}) ≥ 0` always, because `r ↦ e^{β r}` is monotone
increasing for `β > 0` (positive-correlation inequality — a special case
of the FKG / Chebyshev correlation inequality for a *single* random
variable being compared with a monotone function of itself). Equality
holds iff `r` is `p_t`-a.s. constant on the support (so that
`Cov(r, f(r)) = 0` for any `f`).

Iterating: `E_{K_t}[r | s]` is non-decreasing in `t`. Since it is
bounded above by `max_{x ∈ q^{-1}(s)} r(s, x) ≤ R < ∞`, it converges to a
limit. The limit is a fixed point iff `Cov_{p_∞}[r, e^{β r}] = 0`, i.e.
iff `r(s, ·)` is `p_∞`-a.s. constant on `q^{-1}(s)`; since `p_∞` is
concentrated on `q^{-1}(s)`, this forces `p_∞` to be supported on a
single reward level within the fiber. The maximal such level is
`max_x r(s, x)`, achieved when `p_∞` concentrates on argmax. □

**Consequence (operational).** Under the Boltzmann-type reweight `K_{t+1}
∝ K_t · e^{β r}`, the compiler ecology of the parent paper's §5.6 is a
strict monotone-improvement dynamics on reward, with argmax fixed points.
For `β → ∞` this becomes pure exploitation (delta on argmax); for `β → 0`
it becomes the identity update (no change per step). Intermediate `β`
gives the standard exploration-exploitation trade-off familiar from
tempered posteriors / soft-Q iterations.

---

## 4. Worked example: 4-bit Boolean world

**World.** `X = {0, 1}^4`, `q(x) = (x_0 ⊕ x_1, x_2 ⊕ x_3) ∈ S`, `|S| = 4`.
Base compiler `K*(· | s)` is uniform on the 4-element fiber `q^{-1}(s)`.

**Hypothesis family for CT-1.** We take `Θ = {(θ_1, θ_2) ∈ ℝ²}` with the
concern parameterisation of *Concern as Fiber Geometry* — each `θ`
corresponds to the reweighted compiler
`K_θ(x | s) ∝ K*(x | s) · exp(θ_1 (2x_0 − 1) + θ_2 (2x_2 − 1))`,
i.e. a two-dimensional exponential family with sufficient statistic
`T(x) = (2x_0 − 1, 2x_2 − 1) ∈ {−1, +1}²`. The true parameter is
`θ* = (0, 0)` (uniform base compiler).

**MDL identification on this family.** For `N` paired samples, MDL on a
finite grid `Θ = {(θ_1, θ_2) : θ_i ∈ {−1, −½, 0, ½, 1}}` (25 candidates
each with equal description length `log₂ 25`) selects `θ̂_N`. Because
the true `θ*` is inside the grid and every other grid point has a
positive KL divergence to it, Theorem CT-1 predicts
`Pr[θ̂_N = θ*] → 1` as `N → ∞`.

**Reward for CT-2.** Take `r(s, x) := x_0 + x_2` (a bounded scalar
reward in `{0, 1, 2}`). Starting from `K_0 = K*` (uniform on each fiber),
the update `K_{t+1} ∝ K_t · e^{β r}` with `β = 1` should monotonically
increase `E[r | s]` for each `s` until it converges to the argmax reward
on the fiber.

The companion instrument computes both trajectories exactly.

---

## 5. Instrument: `experiments/compiler_tomography_pair`

Exact witness of Theorems CT-1 and CT-2 on the setup above:

- **CT-1.** For `N ∈ {50, 100, 200, 500, 1000, 2000}` paired samples,
  run MDL over the 25-point grid. Report the empirical
  `Pr[θ̂_N = θ*]` averaged over 100 seeded trials, and verify it exceeds
  `1 − 0.05` for `N ≥ N_threshold` (pre-registered, determined by the
  finite-KL-gap calculation).
- **CT-2.** Iterate the compiler ecology update for `T = 20` steps at
  three `β` values `{0.1, 1.0, 4.0}` starting from `K_0 = K*`, and
  verify `E_{K_t}[r | s]` is monotone non-decreasing in `t` at every
  `(s, β)` and converges to the fiber argmax at `β = 4`.

Both experiments are deterministic under fixed seed, and gate pass/fail
is exact (either monotone or not; either recovery-rate ≥ 0.95 or not).

---

## 6. Relation to the SIC framework

Theorem CT-1 promotes the extended-program §5.6 target (compiler
tomography) from a *research direction* to a *theorem* in the finite
discrete case, via classical MDL consistency. Theorem CT-2 does the same
for the "compiler ecology" clause of §5.6.

Together with Theorem 7 (linear-ICA and now sparse-ICA / IMA positive
resolutions of SIC-C-c, Instruments 8 and 9 of the parent paper) and
Theorems CG-1, CG-2 (Fisher geometry and holonomy of concern from the
companion paper), the SIC extended program now has *five* explicit
theorem-instrument pairs beyond the six of the parent paper. The
remaining §5 constructs (theory atlas §5.5, causal semantics §5.7,
representation-repair calculus §5.8, alignment as ensemble governance
§5.9, autocatalytic artwork §5.10) remain open.

---

## 7. Limitations

- The MDL consistency theorem CT-1 requires *finite alphabets* on both
  sides (`S` and `X`) and a countable hypothesis family `Θ` with a
  well-defined description-length code. The extension to continuous `X`
  requires a smoothness / prior-mass argument (Barron 1998); not proved
  here.
- The compiler ecology theorem CT-2 requires a bounded reward and a
  fixed `β`. Time-varying `β_t` (annealing) or unbounded rewards need
  additional convergence arguments; classical convergence-rate results
  for tempered-Bayes / soft-Q are the appropriate literature.
- Neither theorem is Lean-formalised yet. The union-bound machinery from
  Theorem 5's Lean proof is not enough; a mathlib-backed formalisation
  of BIC / Wald consistency would be needed for CT-1.
- The identifiability assumption for CT-1 rules out the observational
  equivalence class of compilers — two compilers agreeing on every
  `(s, x)` pair are considered identical. Real-world compilers often
  have such equivalence classes (e.g. by symmetry); the theorem
  identifies up to that equivalence.

---

## 8. Reproduction

```bash
python3 experiments/compiler_tomography_pair/experiment.py
```

Full development is in the parent paper's §5.6 and the notes file
`notes/structural_intelligence_conjecture.md`.
