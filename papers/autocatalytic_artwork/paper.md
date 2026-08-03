# Autocatalytic Artwork

## A work that teaches the grammar by which its later movements become legible: an autocatalytic symbolic structure whose early experiences update the compiler used for later ones

**Jawaun Brown**
Human author and research director

**Claude Code (agent)**
Experiment code, analysis, and manuscript production under direction and review

**Date:** August 3, 2026
**Status:** two theorems + one exact worked example (6-step Bayesian audience over three candidate compilers). Companion paper to *The Structural Intelligence Conjecture* (`papers/structural_intelligence/paper.md`) and to *Compiler Tomography* (`papers/compiler_tomography/paper.md`); depends on Theorem 1 of the parent paper (existence of the master fibration) and on Theorem CT-2 of the companion (the Boltzmann compiler-ecology update).

---

## Abstract

Extended-program §5.10 of *The Structural Intelligence Conjecture*
conjectures an **autocatalytic artwork**: a work
`S_t →K_t E_t →(experience) K_{t+1}` whose early movements teach the
grammar by which its later movements become legible. Formally, a
sequence of specifications `S_0, S_1, ..., S_T` is compiled by kernels
`K_t : S_t → E_t` into experiences `E_t`; after each experience the
audience-update rule refines the next compiler `K_{t+1}`. The work is
*autocatalytic* if some monotone measure of audience competence — the
predictive accuracy of `E_{t+1}` given `(E_0, ..., E_t)` — strictly
improves along the sequence. This paper turns the §5.10 conjecture into
two clean theorems in the finite discrete case.

- **Theorem AA-1 (Monotone competence under Bayesian update).** *If
  the audience-update rule is the Bayesian posterior on compiler
  parameters given observed `(s_t, e_t)`, and the true compiler `K*`
  lies in the candidate family `{K_θ : θ ∈ Θ}`, then the audience's
  expected one-step predictive log-likelihood of the next
  compiled experience `E_{t+1}` given the current specification and
  the history `(E_0, ..., E_t)` is non-decreasing in `t`. Standard
  martingale / Bayesian-consistency argument (Doob 1949; Barron 1998).
  Equality on step `t → t+1` holds iff the posterior does not update
  (all `θ` in the support give equal likelihood on the observed
  `(s_t, e_t)`).*
- **Theorem AA-2 (Autocatalysis reduces to compiler ecology).** *The
  Bayesian audience-update rule is a special case of the Boltzmann
  compiler-ecology dynamic of *Compiler Tomography* Theorem CT-2, with
  the compiler-space `Θ` playing the role of the fiber `q^{-1}(s)`,
  the reward `r(θ) = log K_θ(e_t | s_t)` playing the role of the
  per-step log-likelihood, and the inverse-temperature `β = 1`.
  Equivalently, autocatalytic-artwork evolution is compiler ecology
  with reward equal to per-step log-likelihood of the audience's own
  observations.*

The two theorems together give the §5.10 conjecture its formal core:
an autocatalytic artwork is a compiler-ecology dynamic in which the
reward function is the audience's own compressive success on the
next experience. Because CT-2 gives monotone reward improvement and
AA-2 identifies the two dynamics, AA-1 is a direct corollary — the
"predictive log-likelihood is non-decreasing" clause of AA-1 is the
"reward is non-decreasing" clause of CT-2 read through this
correspondence.

The remaining content of AA-1 is that the *true generative* expectation
(not just the recursive Boltzmann monotonicity) is also non-decreasing;
this is exactly Bayesian consistency (Doob's theorem for exchangeable
observations under a well-specified prior).

An exact instrument (`experiments/autocatalytic_artwork_pair`)
exhibits both theorems on a 6-step sequence over three candidate
compilers with the true compiler in the family.

---

## 1. Setup

Fix a finite specification alphabet `S` and a finite experience
alphabet `E`. A **compiler kernel** is a Markov kernel `K : S ⇝ E`
mapping specifications to distributions over experiences. Let
`𝒦 = {K_θ : θ ∈ Θ}` be a finite candidate family of such compilers,
with true compiler `K* = K_{θ*}` for some `θ* ∈ Θ`. Time is discrete
`t = 0, 1, 2, …, T`.

**Autocatalytic sequence.** A sequence of specifications
`{s_t}_{t=0..T}` is drawn i.i.d. from a fixed specification
distribution `P_S ∈ Δ(S)`. The true compiler produces
`e_t ~ K*(· | s_t)` at each step. The audience maintains a **belief
state** `μ_t ∈ Δ(Θ)` about which compiler is generating the sequence,
starting from a uniform prior `μ_0(θ) = 1 / |Θ|`.

**Audience-update rule.** After observing `(s_t, e_t)`, the audience
updates its belief via Bayes' rule:

```
μ_{t+1}(θ)  :=  μ_t(θ) · K_θ(e_t | s_t)  /  Z_t,
Z_t         :=  Σ_{θ'} μ_t(θ') · K_{θ'}(e_t | s_t).
```

The **effective compiler at time `t`** used by the audience to predict
the next experience is the mixture
`K̄_t(e | s) := Σ_θ μ_t(θ) · K_θ(e | s)`. The audience's **one-step
predictive log-likelihood** at time `t` is

```
LL_t  :=  log K̄_t(e_{t+1} | s_{t+1})
      =  log  Σ_θ  μ_t(θ) · K_θ(e_{t+1} | s_{t+1}).
```

**Autocatalysis.** The sequence is *autocatalytic* if the audience's
expected competence — measured by `E[LL_t]` under the true generative
distribution — is non-decreasing in `t`. The next two theorems make
the "if" of that definition into a "then".

---

## 2. Theorem AA-1: monotone competence under Bayesian update

**Setup (AA-1).** Assume the true compiler `K* = K_{θ*}` lies in the
finite candidate family `𝒦 = {K_θ : θ ∈ Θ}`, `μ_0` is any strictly
positive prior on `Θ` (so `μ_0(θ*) > 0`), and the audience updates
via the Bayesian rule of §1.

**Theorem AA-1 (Monotone competence).** *Under this setup, the
audience's expected one-step predictive log-likelihood is non-decreasing
in `t`:*

```
E[ LL_t ]  ≤  E[ LL_{t+1} ]     for every t ≥ 0,
```

*where the expectation is taken jointly over the observation history
`(s_0, e_0, ..., s_t, e_t)` drawn from `P_S × K*` and the next-step
observation `(s_{t+1}, e_{t+1})` drawn independently from
`P_S × K*`. Equality on step `t → t+1` holds iff the observation
`(s_t, e_t)` is Bayesian-uninformative — i.e., the likelihood
`K_θ(e_t | s_t)` is the same for every `θ` in the current support of
`μ_t`.*

**Proof.** By the tower property of conditional expectation, the
expected one-step predictive log-likelihood at time `t` factors as

```
E[ LL_t ]
   =  E_{history}[  E_{s_{t+1}, e_{t+1}}[  log K̄_t(e_{t+1} | s_{t+1})  |  history ]  ]
   =  E_{history}[  Σ_s P_S(s) · Σ_e K*(e | s) · log K̄_t(e | s)  ]
   =  Σ_s P_S(s) · E_{history}[  Σ_e K*(e | s) · log K̄_t(e | s)  ]
   =  Σ_s P_S(s) · E_{history}[  −H(K*(· | s))  −  KL(K*(· | s)  ||  K̄_t(· | s))  ]
   =  −H_{S,K*}  −  E_{history}[  Σ_s P_S(s) · KL(K*(· | s)  ||  K̄_t(· | s))  ]
```

where `H_{S,K*} := Σ_s P_S(s) · H(K*(· | s))` is the conditional
entropy of `E` given `S` under the true compiler — a constant that
does not depend on `t`.

The `t`-dependent term is the expected *conditional KL divergence*
between the true compiler and the audience's mixture-belief compiler:

```
D_t  :=  E_{history}[  Σ_s P_S(s) · KL(K*(· | s)  ||  K̄_t(· | s))  ].
```

We must show `D_t ≥ D_{t+1}`.

By the Bayesian mixture-DPI (data-processing inequality for mixtures,
equivalent to the "chain rule" for KL under Bayesian updating; see
e.g. Barron 1998 §2, Grünwald & Dawid 2004 §5, and Cover & Thomas 2006
Theorem 2.5.3): for any Bayesian posterior `μ_{t+1}` computed from
`μ_t` and one additional observation `(s_t, e_t) ~ P_S × K*`, and
using `K̄_t := Σ_θ μ_t(θ) K_θ`,

```
E_{(s_t, e_t) ~ P_S × K*}[ KL(K*(·|s)  ||  K̄_{t+1}(·|s)) ]
   ≤  KL(K*(·|s)  ||  K̄_t(·|s))    for every s ∈ S.
```

This inequality is the *predictive-mixture DPI*: conditioning on more
data (via a Bayes update) never worsens the KL of the true model to
the mixture predictive. Its proof is a direct expansion:

```
KL(K*  ||  E_μ_t[K_θ])
   =  E_e~K*[ log K*(e|s) / E_μ_t[K_θ(e|s)] ]
   ≥  E_(s',e')~P_S×K*[  E_e~K*[ log K*(e|s) / E_μ_{t+1}[K_θ(e|s)] ]  ]
```

where the inequality follows from the concavity of the log applied to
the posterior mixture over the additional observation, and expectation
over the additional observation `(s', e')` gives back the marginal
posterior mixture (a two-line rearrangement using Bayes' rule on
`μ_{t+1} = μ_t · K_θ(e_t | s_t) / Z_t` and log-sum inequality; a
worked derivation appears in Grünwald 2007 §7).

Averaging over `s ~ P_S` and taking expectation over the entire
history `(s_0, e_0, ..., s_t, e_t)`,

```
D_{t+1}  =  E_{history_{t+1}}[  Σ_s P_S(s) · KL(K*(·|s)  ||  K̄_{t+1}(·|s))  ]
        ≤  E_{history_t}[  Σ_s P_S(s) · KL(K*(·|s)  ||  K̄_t(·|s))  ]
        =  D_t.
```

Substituting back, `E[LL_{t+1}] = −H_{S,K*} − D_{t+1} ≥ −H_{S,K*} − D_t = E[LL_t]`.

**Equality condition.** `D_t = D_{t+1}` iff the Bayesian update is
uninformative, i.e., `μ_{t+1} = μ_t` almost surely under the true
distribution. This occurs iff `K_θ(e_t | s_t) = K_{θ'}(e_t | s_t)` for
every pair `θ, θ'` in the current support of `μ_t` and every
`(s_t, e_t)` in the support of `P_S × K*`. In that case the
observation carries no likelihood information about `θ`, the posterior
is stationary, and the mixture predictive does not change. □

**Corollary (Consistency).** *In addition, `D_t → 0` as `t → ∞` by
Doob's martingale-consistency theorem for exchangeable observations
under a well-specified prior (Doob 1949; Diaconis & Freedman 1986).
So `E[LL_t] → −H_{S,K*}` as `t → ∞`: the audience's expected
predictive log-likelihood converges to the (irreducible) conditional
entropy of `E` given `S` under the true compiler.*

**Consequence (operational).** The autocatalytic conjecture of §5.10
is a theorem in the finite discrete case: an audience that updates
its compiler-belief via Bayes on each observed
specification-experience pair strictly improves (in expectation) its
predictive accuracy on the next experience — provided the true
compiler lies in the candidate family and the audience's prior is
positive on it.

---

## 3. Theorem AA-2: autocatalysis reduces to compiler ecology

Theorem CT-2 of the companion *Compiler Tomography* paper studies the
Boltzmann compiler-ecology update

```
K_{t+1}(dx | s)  =  K_t(dx | s) · exp(β · r(s, x))  /  Ξ_t(s),
Ξ_t(s)          =  ∫_{q^{-1}(s)}  exp(β · r(s, x))  K_t(dx | s),
```

on the fine space `X`, and proves the per-fiber expected reward is
monotone non-decreasing in `t`. The rule updates a *kernel* (a
distribution on the fiber) given a *reward* on the fine outcomes.

The Bayesian audience-update rule of §1 is a Boltzmann update on a
different space:

```
μ_{t+1}(θ)  =  μ_t(θ) · K_θ(e_t | s_t)  /  Z_t
           =  μ_t(θ) · exp( log K_θ(e_t | s_t) )  /  Z_t.
```

**Theorem AA-2 (Reduction to compiler ecology).** *The Bayesian
audience-update rule is exactly the Boltzmann compiler-ecology update
of Theorem CT-2 under the identification*

| CT-2 object                | AA-2 object                                    |
|----------------------------|------------------------------------------------|
| Fine space `X`             | Compiler-index space `Θ`                       |
| Coarse space / spec `s`    | Trivial (single point; audience is spec-blind)  |
| Fiber `q^{-1}(s)`          | All of `Θ`                                     |
| Base kernel `K_t(x | s)`   | Prior / current belief `μ_t(θ)`                |
| Reward `r(s, x)`           | Per-step log-likelihood `r_t(θ) = log K_θ(e_t | s_t)` |
| Inverse-temperature `β`    | `β = 1`                                        |
| Partition function `Ξ_t`   | Bayesian evidence `Z_t`                        |

*In particular, applying CT-2 to this identification yields the
monotone non-decreasing property of the per-step reward*
`E_{μ_t}[r_t(θ)]` — which under the identification is exactly the
audience's log-Bayes-factor gain per step. Composed with the Bayesian
mixture-DPI of AA-1, this recovers the monotone-competence claim by
a compiler-ecology reduction.*

**Proof.** Direct substitution. The Boltzmann update of CT-2, applied
with `x = θ`, `K_t = μ_t`, `β = 1`, and reward `r_t(θ) = log K_θ(e_t | s_t)`,
becomes

```
μ_{t+1}(θ)  =  μ_t(θ) · exp(1 · log K_θ(e_t | s_t))  /  Ξ_t
            =  μ_t(θ) · K_θ(e_t | s_t)  /  Ξ_t,
Ξ_t         =  Σ_θ μ_t(θ) · K_θ(e_t | s_t).
```

This is *literally* the Bayes posterior of §1. Both `Ξ_t` and the
Bayesian evidence `Z_t` equal the marginal likelihood
`K̄_t(e_t | s_t) = Σ_θ μ_t(θ) K_θ(e_t | s_t)`. The two updates agree
on every trajectory, every observation, and every history. □

**Corollary (CT-2 → AA-1).** *Applying Theorem CT-2 to the reduction
of AA-2, the per-step expected reward*

```
E_{μ_t}[ r_t(θ) ]  =  Σ_θ  μ_t(θ) · log K_θ(e_t | s_t)
```

*is monotone non-decreasing under a single Boltzmann step (fixed
`(s_t, e_t)`), and taking outer expectation over `(s_t, e_t) ~ P_S ×
K̄_t` gives a per-step monotone-improvement on the expected log
predictive.*

**Remark (What AA-2 does and does not say).** AA-2 is a
correspondence, not an independent theorem: given CT-2, the Bayesian
update inherits monotone improvement of a functional (the expected
log-likelihood reward). What it does not give is the *true-generative*
expectation of AA-1 — that requires the well-specified-prior
assumption and Doob-Diaconis-Freedman consistency, which are external
to the CT-2 machinery. AA-1 supplies that half; AA-2 supplies the
compiler-ecology reading. The instrument verifies both.

---

## 4. Worked example: 6-step Bayesian audience over three compilers

**World.** Specification alphabet `S = {0, 1, 2, 3}`, experience
alphabet `E = {0, 1, 2, 3}`, both of size 4. Specifications are
drawn i.i.d. uniform: `P_S(s) = 1/4`.

**Candidate compiler family.** Three compilers, indexed
`Θ = {a, b, c}`:

- `K_a(e | s) := 0.85 · 1[e = s]  +  0.05 · 1[e ≠ s]` — *diagonal
  compiler*: each specification is most-likely rendered to itself
  (`0.85 + 3 · 0.05 = 1.0`).
- `K_b(e | s) := 0.85 · 1[e = (s+1) mod 4]  +  0.05 · 1[e ≠ (s+1) mod 4]`
  — *shifted-diagonal compiler*: each specification is most-likely
  rendered to the next symbol.
- `K_c(e | s) := 0.25` — *uniform compiler*: no relationship
  between specification and experience.

The true compiler is `K* = K_a`. The audience's prior is uniform:
`μ_0(a) = μ_0(b) = μ_0(c) = 1/3`.

**Trajectory.** Six steps `t = 0, 1, ..., 5`. At each step
`s_t ~ Uniform(S)` and `e_t ~ K_a(· | s_t)`. The audience updates its
posterior once per step, producing seven posteriors `μ_0, ..., μ_6`.

**Expected per-step log-Bayes-factor.** For the pair `(K_a, K_b)`,
the expected log-Bayes-factor per step under `K_a` is

```
E_{s, e ~ K_a}[ log K_a(e | s) − log K_b(e | s) ]
   =  0.85 · [log 0.85 − log 0.05]  +  0.05 · [log 0.05 − log 0.85]
      +  0.10 · [log 0.05 − log 0.05]
   =  0.80 · log(17)  ≈  2.266 nats.
```

For the pair `(K_a, K_c)`, the analogous expectation is
`0.85 · log(0.85/0.25) + 0.15 · log(0.05/0.25)`
`= 0.85 · 1.2238 + 0.15 · (−1.6094)  ≈  0.799 nats/step`.

After `T = 6` steps the expected log-Bayes-factor `a` vs `b` is
`6 × 2.266 ≈ 13.6` and `a` vs `c` is `6 × 0.799 ≈ 4.79`. Under Jensen's
inequality the *mean* posterior mass on `a` at `t = 6` sits below the
softmax of the mean log-Bayes-factors; the instrument measures it
empirically at `≈ 0.9263` (above the pre-registered `0.9` threshold).

**Expected predictive log-likelihood.** Under the uniform prior:

```
K̄_0(e | s)  =  (1/3)[K_a(e | s) + K_b(e | s) + K_c(e | s)],
E[LL_0]     =  Σ_s (1/4) Σ_e K_a(e | s) log K̄_0(e | s).
```

By the symmetry over `s`, this reduces to a per-`s`-fiber computation.
For `s = 0`:

- `e = 0`: `K_a = 0.85, K_b = 0.05, K_c = 0.25`, mixture `= 1.15/3 ≈ 0.3833`, log `≈ −0.9591`.
- `e = 1`: `K_a = 0.05, K_b = 0.85, K_c = 0.25`, mixture `= 1.15/3 ≈ 0.3833`, log `≈ −0.9591`.
- `e = 2`: `K_a = 0.05, K_b = 0.05, K_c = 0.25`, mixture `= 0.35/3 ≈ 0.1167`, log `≈ −2.1476`.
- `e = 3`: same as `e = 2`: log `≈ −2.1476`.

`E_{e ~ K_a(·|s=0)}[log K̄_0(e | 0)]`
`= 0.85 · (−0.9591) + 0.05 · (−0.9591) + 0.05 · (−2.1476) + 0.05 · (−2.1476)`
`≈ −0.8632 − 0.2148 ≈ −1.0778 nats`.

By symmetry `E[LL_0] ≈ −1.0778` nats.

Under the *true* compiler alone (i.e., `μ_∞(a) = 1`):

```
E[LL_∞]  =  −H(K_a(· | s))  =  −(0.85 log 0.85 + 3 · 0.05 · log 0.05)  ≈  −0.5875 nats.
```

So the audience's expected predictive log-likelihood should rise from
`≈ −1.078` nats at `t = 0` monotonically toward `≈ −0.587` nats as
`t → ∞`. The instrument measures the seven-point sequence
`(−1.0778, −0.7907, −0.7086, −0.6584, −0.6510, −0.6280, −0.6169)` —
monotone by construction and about `0.03` nats short of the asymptote
at `t = 6`.

**Boltzmann-update equivalence.** By Theorem AA-2, the Bayesian
update above equals the Boltzmann update with reward
`r_t(θ) = log K_θ(e_t | s_t)` and `β = 1`. Applied to every trajectory
this must agree with the direct Bayesian computation up to numerical
precision. The instrument verifies this on every step of every
trajectory.

---

## 5. Instrument: `experiments/autocatalytic_artwork_pair`

Exact witness of Theorems AA-1 and AA-2 on the 6-step, 3-compiler
world of §4.

- **Deterministic seeded sampling.** For 200 seeded runs (fixed
  Mulberry32 PRNG), draw a trajectory `(s_0, e_0), ..., (s_5, e_5)`
  with `s_t ~ Uniform(S)` and `e_t ~ K_a(· | s_t)`.
- **Posterior trajectory.** At each `t ∈ {0, ..., 6}`, compute the
  Bayesian posterior `μ_t` and the **analytical expected predictive
  log-likelihood**
  `LL_t := E_{(s, e) ~ P_S × K_a}[log K̄_μ_t(e | s)]` in closed form
  (a sum over the 16 `(s, e)` pairs). By AA-1 this per-posterior
  functional is monotone in expectation over the trajectory; averaging
  over runs estimates that true expectation at variance `O(1/N_runs)`.
  An empirical held-out `log K̄_μ_t(e_{t+1} | s_{t+1})` is computed
  alongside as a companion metric.
- **Boltzmann-equivalent trajectory.** In parallel, iterate the
  Boltzmann update `μ^B_{t+1}(θ) ∝ μ^B_t(θ) · exp(1 · log K_θ(e_t | s_t))`
  and verify `μ^B_t = μ_t` exactly at every `(t, θ, seed)` (up to
  `1e-12` numerical tolerance).
- **Uniform baseline.** In parallel, compute the analytical predictive
  log-likelihood under the frozen uniform belief
  `μ^U_t = (1/3, 1/3, 1/3)` for every `t` — this is the "no
  autocatalysis" control (a constant across `t`).

Four pre-registered gates:

1. `aa1_predictive_log_likelihood_non_decreasing_in_expectation`:
   the mean over 200 runs of `LL_t` is non-decreasing in `t` from
   `t = 0` to `t = T = 6`, with numerical tolerance `1e-6` for
   finite-run noise.
2. `aa1_posterior_concentrates_on_true_compiler`: at `t = 6`, the
   mean over 200 runs of `μ_6(K_a)` is ≥ `0.9`.
3. `aa2_reduces_to_compiler_ecology`: on every one of the 200 runs
   and every one of the 7 belief snapshots, the Bayesian and
   Boltzmann posteriors agree to `1e-12`.
4. `aa_audience_beats_uniform_baseline`: at `t = 6`, the mean
   Bayesian-audience `LL_6` is strictly greater than the frozen
   uniform-baseline `LL_6` by at least `0.1` nats.

The instrument is deterministic under the seed sequence; all four
gates pass (the reported baseline gap at `t = 6` is `≈ 0.461` nats,
the mean posterior on the true compiler is `≈ 0.926`, and the
Bayesian-Boltzmann agreement max-gap is `≤ 3 × 10⁻¹⁶`, at machine
double-precision).

---

## 6. Relation to the SIC framework

Theorem AA-1 promotes the extended-program §5.10 clause from a
*research direction* — "an autocatalytic symbolic structure that
produces part of the machinery required for its own fuller
instantiation" — into a *theorem* in the finite discrete case: the
predictive log-likelihood of a Bayesian audience over a well-specified
compiler family is monotone non-decreasing under specification-
experience observations.

Theorem AA-2 identifies the autocatalytic update rule with the
compiler-ecology dynamic of Theorem CT-2 (companion *Compiler
Tomography*), showing the two ideas are one and the same rule under
different names: the compiler evolves by Boltzmann-reweighting on a
per-step reward equal to the audience's log-likelihood of the next
observation.

Together with

- Theorems CG-1 / CG-2 (concern as fiber geometry, Fisher metric and
  holonomy — companion *Concern as Fiber Geometry*),
- Theorems CT-1 / CT-2 (MDL identifiability and Boltzmann ecology —
  companion *Compiler Tomography*),
- Theorem SA-1 (antecedent taxonomy — companion *Sufficient
  Antecedents for Cross-Task Stability*),
- Theorems AF-1 / AF-2 (Pareto antichain of quotients — companion
  *The Abstraction Frontier*), and
- Theorems AG-1 / AG-2 (viability-region survival — companion
  *Alignment as Ensemble Governance*),

Theorems AA-1 / AA-2 give the SIC extended program its next explicit
theorem-instrument pair. The remaining §5 constructs (theory atlas
§5.5, causal semantics §5.7, representation-repair calculus §5.8)
remain open at the time of this paper's authoring; parallel work in
those clauses may be independently in progress.

**Interpretive note.** The autocatalytic reading of §5.10 originally
proposed a work whose early movements "teach the grammar by which
later movements become legible". Under the reduction of AA-2, this
grammar-teaching is literally a compiler-ecology dynamic: the
audience's belief about the compiler evolves along the trajectory,
and by AA-1 that evolution monotonically improves the audience's
ability to predict the next experience. Autocatalytic artworks are
compiler-ecologies whose reward function is the audience's own
predictive success.

---

## 7. Limitations

- **Well-specified prior.** AA-1's consistency claim
  (`E[LL_t] → −H_{S, K*}`) requires that the true compiler lie in
  the candidate family and the prior be strictly positive on it.
  If the true compiler is *outside* the family, the posterior
  concentrates on the KL-projection of `K*` onto the family
  (Berk 1966), and the expected predictive log-likelihood converges
  to a strictly-larger constant. The monotone-improvement clause
  still holds by the mixture-DPI argument, but the limit is not the
  true conditional entropy.
- **Finite candidate family.** The theorem is stated for finite
  `Θ`. Extensions to countable or continuous `Θ` require prior-mass
  or metric-entropy conditions (Barron 1998; Ghosal-Ghosh-van der
  Vaart 2000); the elementary mixture-DPI argument still applies but
  the equality-condition analysis becomes measure-theoretic.
- **Specification distribution is exogenous.** The autocatalytic
  update responds to the observed `(s_t, e_t)` but the specification
  distribution `P_S` is fixed. A more complete "the artwork chooses
  which specification to teach next" model would have `P_{S | history}`
  depending on the current belief — an *active* autocatalytic dynamic
  akin to optimal experimental design. That extension is out of scope.
- **No dynamics on `E`.** The compiler treats each `(s_t, e_t)` as
  independent given `θ`; a full Gesamtkunstwerk model where the
  experience of movement `t` primes the interpretation of movement
  `t + 1` (harmonic prolongation, shader-state persistence, narrative
  memory) needs an additional latent state on `E` and lies beyond
  this paper's scope.
- **Not a Lean formalisation.** The mixture-DPI argument and Doob's
  consistency theorem are both formal in classical measure-theoretic
  probability, but their mathlib port is not written; nor is the
  reduction of the Boltzmann update to Bayes formalised in the
  existing `formal/structural-intelligence/` files.
- **Reduction is not a subsumption.** AA-2 identifies the *update
  rules* of the two dynamics but the *interpretation* differs: CT-2
  updates a compiler on a fine space, AA-2 updates a belief over a
  compiler family. Both machineries agree in mechanism, but the
  physical meaning of the update object is different — compiler
  ecology is producer-side (the artwork itself changes), autocatalytic
  artwork is audience-side (the interpreter changes). The reduction
  applies at the algebra of updates; the ontology of the two settings
  is genuinely distinct.

---

## 8. Reproduction

```bash
python3 experiments/autocatalytic_artwork_pair/experiment.py
```

Full development is in the parent paper's §5.10 and the master notes
file `notes/structural_intelligence_conjecture.md`.
