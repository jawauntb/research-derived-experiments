# Concern as Fiber Geometry

## A Fisher-metric derivation of concern, transport, and holonomy on the stochastic-fibration compiler

**Jawaun Brown**
Human author and research director

**Claude Code (agent)**
Experiment code, analysis, and manuscript production under direction and review

**Date:** August 3, 2026
**Status:** two theorems + one worked example (finite Boolean world). Companion paper to *The Structural Intelligence Conjecture* (`papers/structural_intelligence/paper.md`); depends on Theorem 1 of that paper (existence of the master fibration).

---

## Abstract

The Structural Intelligence Conjecture (SIC) posits a master stochastic
fibration `(q, K)`: a coarse-graining `q : X → Z` and a compiler kernel
`K : Z ⇝ X` with `supp K(·|z) ⊆ q⁻¹(z)`. The companion paper derives
`(q, K)` from Halmos–Savage minimal sufficiency (Theorem 1) and gives its
rate–distortion parameterisation (Theorem 2). This paper adds **concern
geometry** to that object: a concern state `c` is a reweighting of the
compiler on the fiber, `K_c(dx|z) ∝ e^{β U_c(x,z)} K(dx|z)`, and the
family `{K_c}` is a **statistical manifold** with a canonical
Fisher–Rao metric `g_c`. We prove two clean theorems from this setup:

- **Theorem CG-1 (Fisher metric on the fiber).** For a smooth exponential-
  family concern parameterisation, the Fisher information matrix of `K_c`
  on the fiber `q⁻¹(z)` is the covariance of the sufficient statistic of
  the concern parameters under `K_c(·|z)`. This makes concern distinctness
  measurable in bits and gives concern transport its own Riemannian
  geometry, entirely inside the SIC framework.
- **Theorem CG-2 (Concern holonomy = failure of exactness).** Concern
  transport around a closed loop of fibers has zero holonomy if and only
  if the concern-parameterised kernel comes from a *global* potential
  function on `X × Z` (i.e. the concern-1-form is exact). This gives an
  operational test — the holonomy integral — for whether concern is
  path-independent (a "flat" concern field) or path-dependent (a
  non-integrable concern field). Path-dependence is the SIC formalisation
  of the "meaning shifts under context" intuition.

We close with an exact worked example on the 4-bit Boolean world of
Instrument 4: two concern parameterisations of the compiler on the four
fibers, an explicit `2 × 2` Fisher matrix at every parameter value, and a
numerical demonstration that a specific non-exact concern field has
non-zero holonomy around the natural fiber-loop, while its exact
counterpart has zero holonomy.

---

## 1. Setup

We take the SIC master object as given: a stochastic fibration `(q, K)`
with `X` a standard Borel space, `Z` a countable coarse space,
`q : X → Z` measurable, `K(·|z)` a probability measure on `q⁻¹(z) ⊆ X`
for each `z ∈ Z` (see *The Structural Intelligence Conjecture* §1–§2 for
provenance and Theorem 1 for existence).

**Concern reweighting.** A *concern state* is a parameter `c ∈ C ⊆ ℝ^k`
together with a *concern potential* `U_c : X × Z → ℝ` that is jointly
measurable and finitely integrable against `K(·|z)`. Concern reweights
the compiler:

```
K_c(dx | z)  :=  exp(β U_c(x, z)) · K(dx | z)  /  Ξ_c(z),
                                                (β > 0 is a fixed inverse-scale)
Ξ_c(z)       :=  ∫_{q⁻¹(z)} exp(β U_c(x, z)) K(dx | z).
```

The support condition `supp K_c(·|z) ⊆ q⁻¹(z)` is preserved: reweighting
never crosses fibers. `Ξ_c(z)` is a *fiber partition function*; requiring
`Ξ_c(z) < ∞` for all `z` restricts admissible concerns.

**Concern manifold.** For each `z`, the map `c ↦ K_c(·|z)` gives a
parametric family of probability measures on `q⁻¹(z)` indexed by `c`.
When `c ↦ U_c(x, z)` is smooth, this family is a smooth statistical
manifold in the sense of Amari–Nagaoka.

---

## 2. Theorem CG-1: Fisher information on the fiber

**Setup (Theorem CG-1).** Fix `z ∈ Z`. Suppose `U_c(x, z) = ⟨c, T(x, z)⟩`
for some `k`-dimensional sufficient statistic `T(·, z) : q⁻¹(z) → ℝ^k`.
That is, `K_c(·|z)` is the exponential family with base `K(·|z)` and
sufficient statistic `T(·, z)`:

```
K_c(dx | z)  =  exp(β ⟨c, T(x, z)⟩ − log Ξ_c(z)) · K(dx | z).
```

Let `E_{c,z}` and `Cov_{c,z}` denote expectation and covariance under
`K_c(·|z)`.

**Theorem CG-1.** *Under the exponential-family setup, the Fisher
information matrix `g_{c,z}` on the fiber `q⁻¹(z)`, at parameter `c`, is*

```
g_{c,z}  =  β² · Cov_{c,z}[ T(·, z) ]     ∈  ℝ^{k × k}.
```

*Consequently the fiber-restricted Riemannian distance between two nearby
concerns `c, c + dc` is `(β/1) · √( dc^T · Cov_{c,z}[T] · dc )`, and this
distance equals (up to leading order) the square-root of twice the
Kullback–Leibler divergence*

```
KL( K_c(·|z)  ||  K_{c+dc}(·|z) )   =   ½ · dc^T · g_{c,z} · dc  +  o(||dc||²).
```

**Proof.** Direct computation. The log-likelihood ratio is

```
log K_c(dx|z) − log K_{c₀}(dx|z)
  =  β · ⟨c − c₀, T(x, z)⟩  −  log Ξ_c(z)  +  log Ξ_{c₀}(z).
```

The score at `c₀`, `∂_c log K_c(·|z)|_{c=c₀}`, is `β · (T(·, z) − E_{c₀,z}[T(·,z)])`
(differentiating `−log Ξ_c(z)` gives `−E_c[T]`, standard exponential-family
identity). The Fisher matrix is the outer-product expectation of the score:

```
g_{c₀,z}
  =  E_{c₀,z}[ (β(T − E_{c₀,z}[T])) · (β(T − E_{c₀,z}[T]))^T ]
  =  β² · Cov_{c₀,z}[T].
```

The KL–metric identity `KL(p || p + dp) = ½ dp^T g dp + o(||dp||²)` is the
standard second-order Taylor expansion of KL for smooth families
(Amari–Nagaoka, *Methods of Information Geometry*, 2000, Prop. 3.4). □

**Consequence (operational).** Two concerns are distinguishable in `n`
i.i.d. samples from the fiber iff their KL is at least `≈ 1/n`
(likelihood-ratio test asymptotics); equivalently, iff the geodesic
distance between them under `g_{c,z}` is at least `Θ(1/√n)`. Concern
geometry has a sample-complexity meaning, not just a metaphorical one.

---

## 3. Theorem CG-2: Concern holonomy

Cross-fiber concern transport takes the following shape. Fix a base
concern `c_0 ∈ C`. As `z` varies over `Z`, the fiber partition function
`Ξ_{c_0}(z)` varies, and the "canonical" concern-1-form on `Z × C` is

```
α(c, z)  :=  ∇_c log Ξ_c(z)  dc  =  β · E_{c,z}[ T(·, z) ]  dc.
```

This 1-form describes how the *mean concern statistic* along a fiber
changes as concern varies. Given a closed loop `γ : [0, 1] → Z × C` with
`γ(0) = γ(1)`, the **concern holonomy along `γ`** is

```
H(γ)  :=  ∮_γ α  =  ∮_γ β · E_{c,z}[T(·, z)]  dc.
```

**Theorem CG-2 (Concern holonomy vanishes iff concern is exact).** *`H(γ) = 0`
for every closed loop `γ` if and only if there exists a smooth function
`Φ : Z × C → ℝ` such that*

```
α  =  dΦ,     equivalently     β · E_{c,z}[T(·, z)]  =  ∇_c Φ(z, c).
```

*Under smoothness of `α` (which follows from exponential-family regularity
in Theorem CG-1), this is equivalent to*

```
∂_{c_i}(β E_{c,z}[T_j])  =  ∂_{c_j}(β E_{c,z}[T_i])     for all  i, j, z.
```

**Proof.** Standard de Rham. `H(γ) = ∮_γ α = 0` for every closed loop `γ`
iff `α` is closed (`dα = 0`) on a simply-connected domain, iff `α` is
exact (`α = dΦ`) by the Poincaré lemma. Closedness in coordinates is the
symmetry-of-partial-derivatives condition above (Frobenius / Schwarz).
Exponential-family Fisher-metric arguments (Theorem CG-1) show `α` is
smooth in `c` under `Ξ_c < ∞`, so the coordinate condition is checkable
pointwise. □

**Consequence.** Non-vanishing holonomy is not an artefact of the
parameterisation: it is the *statement* that the concern field cannot be
recovered from a single potential `Φ` on `Z × C`. In SIC terms, the
system's concern is *irreducibly path-dependent* — it depends not on the
current `(z, c)` state alone but on how the state was reached. This
formalises the intuition (Geometry of Concern; Gauge-Fixed Transport of
Concern in the parent repo) that concern deforms under context in ways
a single scalar cannot capture.

---

## 4. Worked example: the 4-bit Boolean world of Instrument 4

We give a concrete finite calculation exhibiting both theorems.

**World.** `X = {0, 1}^4` uniform, `q(x) = (x_0 ⊕ x_1, x_2 ⊕ x_3) ∈ Z`,
`|Z| = 4`. Base compiler `K(·|z)` is uniform on the 4-element fiber
`q⁻¹(z)`.

**Concern parameterisation.** Take `k = 2` and

```
T(x, z)  =  (T_1(x, z), T_2(x, z))
         =  (2 x_0 − 1,  2 x_2 − 1)     ∈  {−1, +1}².
```

So concern parameter `c = (c_1, c_2) ∈ ℝ²` reweights the fiber by
`exp(β c_1 (2 x_0 − 1) + β c_2 (2 x_2 − 1))`. Because `q` fixes only the
*parities* of `(x_0, x_1)` and `(x_2, x_3)`, each of `x_0` and `x_2` still
ranges over `{0, 1}` on every fiber (the fiber has four elements: two
choices for `x_0` and, independently, two for `x_2`, with `x_1` and `x_3`
then determined by `z_1, z_2`). So `T_1, T_2 ∈ {−1, +1}` non-trivially on
*every* fiber, and under `K(· | z)` they are uniform ±1 and independent —
a product of two Rademacher marginals.

*(An earlier draft used `T = (x_0 − x_1, x_2 − x_3)`; that statistic is
identically `0` on the fibers where `x_0 = x_1` — half of them — so its
Fisher information degenerates there. The choice above is a correction to
match the "concern statistic varies on every fiber" requirement of the
worked-example setup.)*

**Fisher matrix (Theorem CG-1 applied).** Under `K_c(· | z)`, `T_1` and
`T_2` become independent Rademacher-tilted with means
`E_c[T_1] = tanh(β c_1)` and `E_c[T_2] = tanh(β c_2)`, so

```
g_{c,z}  =  β² · diag( 1 − tanh²(β c_1),  1 − tanh²(β c_2) )
         =  β² · diag( sech²(β c_1),  sech²(β c_2) )
```

for all `z ∈ Z` — the fiber index `z` really does drop out. Diagonal,
depends smoothly on `c`, with entries in `(0, β²]`. The instrument
verifies this exactly at every `(c, z)` in a pre-registered grid.

**A genuinely non-exact concern field.** Modify the concern-1-form to

```
α'  :=  α  +  ε · (− c_2 · dc_1  +  0 · dc_2).
```

This correction has non-zero curl:

```
∂_{c_2}(α'_1) − ∂_{c_1}(α'_2)  =  ∂_{c_2}(− ε c_2) − 0  =  − ε   ≠  0.
```

By Theorem CG-2, `α'` is not exact, and its holonomy around any closed
loop in `c`-space equals `ε · (signed area enclosed)` (Green's theorem;
the exact part `α` integrates to zero by exactness).

*(An earlier draft added `ε · (z_2 dc_1 − z_1 dc_2)` at fixed `z`; that
1-form is trivially exact on `ℝ²` — its potential is
`Φ(c) = ε z_2 c_1 − ε z_1 c_2` — and has zero holonomy on every loop.
Detected by the instrument on first run; corrected here to the genuine
non-exact form above.)*

**Numerical holonomy (both loops at fixed `z = (1, 1)`, `ε = 0.3`).**

- Rectangular loop `[0, 1] × [0, 1]` — enclosed area `1`, so
  `H(γ) = ε · 1 = 0.3` (predicted). Instrument computes `0.300000` by
  trapezoidal quadrature on 500 steps per edge.
- Triangular loop `(0,0) → (1,0) → (1,1) → (0,0)` — enclosed area `1/2`,
  so `H(γ) = ε / 2 = 0.15` (predicted). Instrument computes `0.150000`.

Both holonomies non-zero, of *different* magnitudes proportional to the
enclosed area — the concrete signature of a path-dependent concern field
in the SIC framework, on an exactly solvable finite case.

---

## 5. Relation to the SIC framework

Theorem CG-1 is a *direct consequence* of the SIC master object plus
exponential-family concern: no new mathematical apparatus beyond
Halmos–Savage sufficiency (SIC Theorem 1) and Amari's Fisher-metric
identity. It refines the extended-program construct §5.1 of the parent
paper ("Concern as fiber geometry") from a *target* to a *theorem*.

Theorem CG-2 is a purely geometric statement about 1-forms on `Z × C`; it
does not require probability beyond the smoothness that Theorem CG-1
supplies. Its content is entirely qualitative: it identifies when concern
transport is or is not path-dependent, and gives a coordinate condition
(symmetry of partial derivatives of `E_c[T]`) that is testable on any
concrete concern parameterisation. This refines the extended-program
target — the "holonomy measures path-dependence" claim — into an if-and-
only-if with a computable check.

Both theorems close targets in the parent paper's §5 extended program:
§5.1 "concern as fiber geometry" is now Theorem CG-1 + Theorem CG-2 for
the exponential-family + smooth 1-form case. The §5.6 compiler-tomography
construct, §5.9 alignment-as-ensemble-governance, and the remaining
targets are still open.

---

## 6. Limitations

- The exponential-family assumption of Theorem CG-1 is standard but not
  free: concerns that don't factor as `⟨c, T⟩` need a more general
  score-function argument, still yielding a Fisher matrix but no longer
  in closed form.
- Theorem CG-2's Poincaré lemma requires simply-connected `Z × C`. For
  multiply-connected topologies (finite `Z` with a chosen loop structure),
  the equivalence weakens to "exact ⇒ zero holonomy" and holonomy can
  detect topological non-triviality of `Z`.
- Nothing here upgrades SIC's *cross-task learnability* (SIC-C-b, SIC-C-c
  in the parent paper) or the *alignment claim* (extended program §5.9).
  Both remain untouched.
- No machine-checked Lean proof of Theorems CG-1 or CG-2 yet;
  Amari–Nagaoka's Fisher-metric identity would need mathlib's information
  geometry (which is minimal). Follow-up.

---

## 7. Reproduction

The worked example in §4 is finite and executable. See
`experiments/concern_fisher_pair` for an exact enumeration:

```bash
python3 experiments/concern_fisher_pair/experiment.py
```

Full development is in the parent paper's §5.1 and the notes file
`notes/structural_intelligence_conjecture.md`.
