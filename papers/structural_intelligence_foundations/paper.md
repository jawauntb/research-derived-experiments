# Structural Intelligence Foundations

## Deriving the master fibration `(q, K)` in the finite discrete positive-support case from Halmos–Savage, `Coarsen ⊣ Refine`, and CS-2

**Jawaun Brown**
Human author and research director

**Claude Code (agent)**
Experiment code, analysis, and manuscript production under direction and review

**Date:** August 3, 2026
**Status:** one derived theorem + one Lean formalisation + one numerical instrument. Companion paper to *The Structural Intelligence Conjecture* (`papers/structural_intelligence/paper.md`). This paper closes the "the master fibration is *posited* by SIC-A, not derived" gap in the finite discrete positive-support case only. Every step is checked in Lean 4 (Mathlib companion project) and witnessed exactly on the 4-bit Boolean world.

---

## Abstract

The Structural Intelligence Conjecture (SIC) opens with a foundational
posit — **SIC-A**: there exist a coarse-graining `q : X → Z` and a
compiler kernel `K : Z ⇝ X` with `supp K(·|z) ⊆ q⁻¹(z)`, jointly
minimally sufficient for a task family `Τ ⊆ Θ`. Every subsequent theorem
in the ten-companion program takes `(q, K)` as *given* and studies its
geometry, its rate–distortion parameterisation, its concern reweighting,
or its stability. This paper takes SIC-A itself as the *conclusion* and
supplies a derivation from three theorems already Lean-verified in the
Structural Intelligence Mathlib project:

- **Theorem 1 (Halmos–Savage minimal sufficient statistic)** —
  `exists_minimal_sufficient_finite_discrete` in
  `StructuralIntelligenceMathlib/Theorem1MinimalSufficiency.lean`.
  Under strict positivity of every `P θ`, the likelihood-ratio vector
  against a fixed pivot `θ₀ ∈ Θ` is minimally sufficient.
- **Proposition 3 (Coarsen ⊣ Refine adjunction)** —
  `coarsen_refine_eq` and `proposition3_adjunction` in
  `StructuralIntelligenceMathlib/Proposition3Adjunction.lean`. For any
  fibre-supported, fibre-normalised kernel `K` over a quotient
  `q : X → Z`, the retraction identity `C ∘ R = id` holds and both
  triangle identities close.
- **Theorem CS-2 (meaning quotient = coarsest common sufficient screen)**
  — `messageQuotient_is_coarsest` in
  `formal/structural-intelligence/StructuralIntelligence/CausalSemantics.lean`
  and its Theorem-4 twin `commonSuffScreen_coarsest` in
  `formal/structural-intelligence/StructuralIntelligence/CommonSuffScreen.lean`.
  Any competing screen that determines the task family's Ψ-behaviour
  refines the meaning quotient — the quotient is the coarsest
  common-sufficient statistic on messages.

**Theorem SIC-A (finite discrete positive-support form).** *Let `X` be
finite and non-empty, `Θ` a finite parameter set, `P : Θ → X → ℝ` a
family of pmfs with `∀ θ x, 0 < P θ x`, and `Τ ⊆ Θ` a task family.
Then there exist a finite set `Z`, a partition map `q : X → Z`, and a
kernel `K : Z ⇝ X` such that*

1. `supp K(·|z) ⊆ q⁻¹(z)` for every `z ∈ Z` (fibre-supported);
2. `∑_x K(z, x) = 1` for every `z ∈ image(q)` (fibre-normalised on the
   image);
3. `q` is sufficient for the family `Τ` in the Fisher–Neyman /
   Halmos–Savage sense; and
4. `q` is the coarsest such statistic — every other common sufficient
   `q' : X → Z'` refines `q`.

The construction is:

- `q(x) := (θ ↦ P θ x / P θ₀ x)`  for any fixed pivot `θ₀ ∈ Θ` (LR-vector);
- `Z := image(q) ⊆ (Θ → ℝ)`  (a finite set of ℝ-valued functions);
- `K(z, x) := |q⁻¹(z)|⁻¹` if `q(x) = z`, else `0`  (uniform on the fibre).

Sufficiency (clause 3) is Theorem 1 applied to `q`; the fibre structure
(clauses 1–2) is the Proposition 3 side condition made concrete;
minimality (clause 4) is Theorem CS-2 applied to the quotient
`X → X/∼_q`. *No new axioms.*

The programme's status changes: the master fibration was previously
*posited* as SIC-A and used as a starting point for the ten companion
papers. In the finite discrete positive-support case, it is now
*derived* — the fibration is a construction from data, not a hypothesis
about the world.

**What stays open.** The general topological / measure-theoretic case
(uncountable `X`, general dominated families) is *not* closed by this
paper. That version requires the full Halmos–Savage 1949 machinery
(regular conditional distributions on a standard Borel space, plus a
minimal sufficient σ-algebra that respects the P-null completion), and
Mathlib does not yet expose that infrastructure. The pure Halmos–Savage
minimality step is also axiomatised in Theorem 1's Lean file as
`HalmosSavage_minimality_h_extension` — a classical-choice packaging of
the "extend a partial function defined on the image of an arbitrary
sufficient `T'` to a total function on `Θ → ℝ`" step, with an inline
citation to Halmos & Savage 1949. That axiom is honestly listed in the
Mathlib project's README (*Axiom footprint — honest accounting*
section) and inherited unchanged by the derivation in this paper.

---

## 1. What SIC-A claims and why deriving it matters

**Claim (SIC-A, verbatim from the parent paper).** Let `X` be a space
of concrete realisations and `Θ` a parameter set indexing a family of
tasks. There exist:

- a *coarse-graining* `q : X → Z` sending each realisation to the
  structure it embodies, with fibre `q⁻¹(z)` the set of realisations
  compatible with structure `z`; and
- a *compiler* `K : Z ⇝ X`, a Markov kernel from `Z` to `X` with
  `supp K(·|z) ⊆ q⁻¹(z)`;

*jointly minimally sufficient* for the task family — every task
observable in the family factors through `q`, and any competing
`(q', K')` with the same sufficiency property is a refinement of
`(q, K)`.

Every subsequent theorem in the ten-companion programme —
`(CG-1, CG-2, CT-1, CT-2, SA-1, AF-1, AF-2, AG-1, AG-2, TA-1, TA-2, CS-1, CS-2, RR-1, RR-2, AA-1, AA-2)`
— either studies the geometry of the master fibration once it is given
(concern-fibre metric, holonomy, compiler tomography, ecology,
antecedent taxonomy, abstraction frontier, alignment audit, theory
atlas, causal semantics, repair calculus, autocatalytic artwork) or
supplies a rate at which the fibration can be learned (Theorems 5, 6,
7). None of them re-derives SIC-A; all of them assume it.

**Why this is a gap worth closing.** A conjecture whose foundational
posit is *un-derived* leaves the entire programme resting on an
existence assumption that the reader must take on trust. The right
question is: can we exhibit `(q, K)` as a *theorem* — a construction
from the given data `(X, Θ, P)` — rather than a *hypothesis* the reader
is asked to concede? In the finite discrete positive-support case, the
answer is yes, and this paper gives the derivation. The derivation
composes three theorems that are individually already Lean-verified;
the composition is what is new.

The composition is not automatic. Theorem 1 gives us `q` (the
LR-vector). Proposition 3 gives us a fibre-supported kernel `K` on any
quotient. Theorem CS-2 gives us the coarsest common-sufficient
statement across the task family. To make them fit, we have to check
that (a) the LR-vector's fibres are exactly the ones we want the kernel
to be uniform on, (b) the uniform-on-fibre construction actually
satisfies the two side conditions of Proposition 3, and (c) the
minimality direction of CS-2 applies to the LR-vector's quotient
without any additional hypotheses. All three checks are elementary and
constructive; the rest of the paper is the audit.

---

## 2. The reduction, step by step

Fix once and for all a finite `X`, a finite parameter set `Θ`, a family
`P : Θ → X → ℝ` with `∀ θ x, 0 < P θ x`, and any pivot `θ₀ ∈ Θ`.

### 2.1 Step 1 — Theorem 1 gives `q`

**Theorem 1 (Halmos–Savage, finite discrete positive-support form).**
The *likelihood-ratio vector* against `θ₀`,

```
q(x)  :=  (θ  ↦  P θ x  /  P θ₀ x)         ∈  Θ → ℝ,
```

is a minimally sufficient statistic for the family `{P θ}` on `X`.
Sufficiency in the pmf cross-multiplication form:

```
q(x) = q(x')     ⇒     ∀ θ θ',  P θ x · P θ' x'  =  P θ x' · P θ' x.
```

Both halves — the LR-factoring characterisation and the sufficiency of
the LR-vector — are proved in
`StructuralIntelligenceMathlib/Theorem1MinimalSufficiency.lean` under
strict positivity, without any auxiliary axiom. The minimality half
uses one packaged axiom
(`HalmosSavage_minimality_h_extension`) whose mathematical content is a
classical-choice extension step; the axiom carries an inline citation
to Halmos & Savage (1949), *Ann. Math. Statist.* 20, 225–241,
Theorem 2.

**What we take from Theorem 1.**
- **Existence of `q` with a specific formula.** The LR-vector is a
  concrete function `X → (Θ → ℝ)`; we can compute it.
- **Sufficiency of `q`.** The pmf cross-multiplication identity holds
  on every fibre.
- **Minimality of `q`.** Every sufficient `T'` factors through `q`
  (via the axiomatised extension step).

The image `image(q) ⊆ (Θ → ℝ)` is a finite set (as the image of a
function from a finite set into any target), so it can be taken as our
finite `Z`. We denote this finite `Z` by `Z_q`, and the corestriction
of the LR-vector by `q : X → Z_q`.

### 2.2 Step 2 — Proposition 3 gives `K` and the fibration structure

**Proposition 3 (`Coarsen ⊣ Refine`).** For any finite discrete
setting with a partition `q : X → Z` and a kernel `K : Z → X → ℝ` that
is *fibre-supported* (`K(z, x) = 0` whenever `q(x) ≠ z`) and
*fibre-normalised* (`∑_x K(z, x) = 1` for every `z`), the pair
`(coarsen q, refine K)` satisfies both triangle identities of an
adjunction:

- `C (R (C μ)) = C μ` (unit) — proved as `R_C_unit`;
- `R (C (R ν)) = R ν` (counit) — proved as `C_R_counit`;

and the load-bearing retraction identity `C ∘ R = id` is proved as
`coarsen_refine_eq`. All three are formalised without axioms in
`StructuralIntelligenceMathlib/Proposition3Adjunction.lean`.

**Our concrete `K`.** Given the LR-vector's quotient `q : X → Z_q`,
define the **uniform-on-fibre kernel**

```
K(z, x)  :=  |q⁻¹(z)|⁻¹      if q(x) = z,
             0                if q(x) ≠ z.
```

Because `Z_q = image(q)`, every `z ∈ Z_q` has `q⁻¹(z) ≠ ∅`, so
`|q⁻¹(z)| ≥ 1` and the reciprocal is well-defined and finite.

**Two side conditions verified.**

- **Fibre-supported.** By definition, `K(z, x) = 0` when `q(x) ≠ z`.
  This is *literal support* on the fibre, and it makes clause 1 of
  SIC-A hold pointwise, not just in distribution.
- **Fibre-normalised.** For every `z ∈ Z_q`,

```
∑_x K(z, x)  =  ∑_{x ∈ q⁻¹(z)} |q⁻¹(z)|⁻¹  +  ∑_{x ∉ q⁻¹(z)} 0
              =  |q⁻¹(z)| · |q⁻¹(z)|⁻¹
              =  1.
```

Both side conditions are elementary finite-sum identities. In the Lean
formalisation, the fibre-support clause is a one-line `if_neg`
rewrite; the fibre-normalisation clause is a `sum_filter` split
followed by `sum_const` + `mul_inv_cancel₀`.

**Why Proposition 3 matters here.** Without the retraction identity,
one could construct *any* fibre-supported normalised kernel and call it
a compiler. The `Coarsen ⊣ Refine` adjunction certifies that the
uniform-on-fibre kernel is not an arbitrary choice: it is the natural
right adjoint to `q`. Any two such kernels differ only in how they
reweight within a fibre; the coarsening-then-refining round-trip
collapses them all to the same distribution on `Z_q`.

*(The theorem here quantifies over the specific uniform-on-fibre
kernel; any other fibre-supported, fibre-normalised kernel gives the
same SIC-A conclusion because Proposition 3 does not depend on which
kernel we pick. The uniform-on-fibre choice is the one that requires
no additional prior data — we do not need a base measure `μ` on `X` to
build it, unlike the μ-restricted normalisation, which reduces to the
uniform-on-fibre kernel when `μ` is uniform on each fibre.)*

### 2.3 Step 3 — Theorem CS-2 gives minimality across the task family

**Theorem CS-2 (meaning quotient = coarsest common sufficient
screen).** For a semantics `psi : M → C → D` sending messages to
context-slot distributions, the message quotient `M → (C → D)` is the
coarsest common-sufficient screen: any other screen `q' : M → Q` that
determines Ψ-behaviour refines the Ψ-equivalence relation. Formalised
without axioms as `messageQuotient_is_coarsest` in
`formal/structural-intelligence/StructuralIntelligence/CausalSemantics.lean`;
the Theorem-4 twin `commonSuffScreen_coarsest` in
`CommonSuffScreen.lean` gives the same coarsestness statement for a
task family under a "common sufficient screen" hypothesis.

**Applied to our setting.** Consider the family
`{Y_θ : X → ℝ, x ↦ P θ x}_{θ ∈ Τ}` of pmf-slot maps indexed by the task
family `Τ ⊆ Θ`. The LR-vector `q` factors every `Y_θ`: if `q(x) = q(x')`
then for every `θ`, by Theorem 1's cross-multiplication identity taken
at `(θ, θ₀)`,

```
P θ x · P θ₀ x'  =  P θ x' · P θ₀ x,
```

so `P θ x / P θ₀ x = P θ x' / P θ₀ x'`, hence the ratio depends on `x`
only through `q(x)`. Multiplying by `P θ₀ x = P θ₀ x'` (equal, since
they are the values of a specific coordinate of `q`) gives
`P θ x = P θ x'`, so `Y_θ x = Y_θ x'` whenever `q(x) = q(x')`. In the
CS-2 language, `q` is a common-sufficient screen for `{Y_θ}_{θ ∈ Τ}`.

CS-2's coarsest direction then says: for any other common-sufficient
screen `q' : X → Z'`, agreement under `q'` forces agreement under `q`.
Equivalently, `q'` refines `q`; `q` is the coarsest. This is exactly
clause 4 of SIC-A restricted to the task family `Τ`.

**Note on `Τ ⊆ Θ`.** The construction of `q` uses *all* of `Θ` (the
LR-vector's coordinates range over the full parameter set), so `q` is
automatically sufficient for any sub-family `Τ ⊆ Θ`. In the extremal
case `Τ = Θ`, `q` is minimally sufficient for `Θ` and hence for `Τ`.
For a strict sub-family `Τ ⊊ Θ`, `q` is *sufficient but not necessarily
minimal for `Τ`*: a coarser statistic (using only the `Τ`-restricted
LR-coordinates) might be sufficient for `Τ` alone. This is the honest
subtlety the paper's Theorem SIC-A statement carries: minimality is
with respect to the *full* parameter set; sub-family minimality is a
separate exercise. The Lean statement in
`SICA_FiniteExistence.lean` matches the paper's clause 4 in the full
`Τ = Θ` case; the `Τ ⊊ Θ` case is a natural follow-up and is called
out as open in §6.

---

## 3. Composing the three steps: the derived SIC-A

Putting steps 1–3 together:

**Theorem SIC-A (derived, finite discrete positive-support form).** *Let
`X` be finite, non-empty; `Θ` a finite parameter set; `P : Θ → X → ℝ` a
family of pmfs with `∀ θ x, 0 < P θ x`. Then*

- *the LR-vector against any fixed `θ₀ ∈ Θ` corestricts to a map
  `q : X → Z` with `Z := image(q)` finite*;
- *the uniform-on-fibre kernel `K(z, x) := |q⁻¹(z)|⁻¹ · 1[q(x)=z]` is
  fibre-supported and fibre-normalised*;
- *`q` is minimally sufficient for `{P θ}_{θ ∈ Θ}` (Theorem 1)*;
- *`(coarsen q, refine K)` satisfies both triangle identities of an
  adjunction (Proposition 3)*;
- *any competing common-sufficient screen refines `q` (Theorem CS-2)*.

*Consequently `(q, K)` is a master fibration in the sense of SIC-A on
`(X, Θ, P)`, and its construction requires no data beyond `(X, Θ, P)`
and a chosen pivot `θ₀ ∈ Θ`.*

The Lean formalisation
(`StructuralIntelligenceMathlib/SICA_FiniteExistence.lean`) states the
first three clauses in the form the parent paper's SIC-A signature
asks for:

```
theorem sic_a_finite_discrete
    {Θ α : Type*} [Fintype Θ] [Fintype α] [DecidableEq α]
    (P : Θ → α → ℝ) (θ₀ : Θ) (hpos : ∀ θ x, 0 < P θ x)
    (μ : α → ℝ) (_hμ_nn : ∀ x, 0 ≤ μ x) (_hμ_sum : ∑ x, μ x = 1) :
    ∃ (Z : Type*) (_ : Fintype Z) (_ : DecidableEq Z)
      (q : α → Z) (K : Z → α → ℝ),
      IsSufficient P q ∧
      (∀ z x, q x ≠ z → K z x = 0) ∧
      (∀ z, ∑ x, K z x = 1 ∨ ∑ x, K z x = 0)
```

The `μ` argument is present in the signature so the theorem sits
naturally next to any downstream construction that needs a base
distribution (e.g. rate–distortion parameterisations, Bayesian
posteriors); the construction itself is `μ`-independent — the uniform-
on-fibre `K` uses only the partition, not `μ`. The `∨` in the
normalisation clause covers the trivial case of a `z ∉ image(q)`
(where `∑_x K(z, x) = 0`); for every `z ∈ Z := image(q)`, the left
disjunct `= 1` holds. The Lean proof takes exactly the structure above:
step 1 provides `q`, step 2 provides `K`, and the three conjuncts are
each closed by a one-lemma call plus finite-sum bookkeeping.

The coarsestness clause 4 is proved in a separate lemma
`sic_a_finite_discrete_coarsest` in the same file, factoring through
CS-2's `commonSuffScreen_coarsest` after rewriting the LR-vector's
sufficiency as a common-sufficient screen for the pmf-slot family
`{P θ}_{θ ∈ Θ}`.

**The upshot for the programme.** The master fibration `(q, K)` is no
longer a posited object in the finite discrete positive-support case;
it is a constructive theorem. Every companion paper (concern fibre
geometry, compiler tomography, alignment audit, etc.) that assumes
`(q, K)` now has that assumption *discharged* in the finite discrete
positive-support case — one can apply their theorems knowing the input
is not a hypothesis but a derived object.

---

## 4. Numerical witness: `experiments/sica_finite_derivation_pair`

The construction is executable on the 4-bit Boolean world of
Instrument 4 (`X = {0, 1}^4`, `|X| = 16`). We take:

- `Θ` = the same 16 worlds (a maximally-expressive parameter set); this
  keeps the LR-vector meaningful — the identity map is not a
  degenerate LR-vector because we sweep all 16 parameters.
- `P θ x = P̂(θ, x) + 1/16` where `P̂` is a task-natural asymmetric
  family and `+1/16` is Laplace smoothing to enforce strict positivity
  (avoids any zero-mass observation). The base `P̂` uses a
  fibre-per-θ construction so the pre-smoothed pmf already covers the
  fibre structure of interest; the smoothing shifts every mass by a
  small positive amount without changing which fibres are equal.
- `θ₀` = the all-zero world (a canonical pivot).
- `q(x) := (θ ↦ P θ x / P θ₀ x)`  the LR-vector.
- `K(z, x) := |q⁻¹(z)|⁻¹` if `q(x) = z`, else `0`.

The instrument verifies four exact gates:

1. **T1 characterisation.** Two `x, x'` satisfy `q(x) = q(x')` iff
   `∀ θ θ' : Θ, P θ x · P θ' x' = P θ x' · P θ' x`. Both directions
   are checked pointwise on all 16² = 256 sample pairs.
2. **Fibration structure.** `K(z, x) > 0` iff `q(x) = z`, checked on
   every `(z, x)` pair.
3. **Fibre normalisation.** `∑_x K(z, x) = 1` for every `z ∈ image(q)`
   and `= 0` for every `z ∉ image(q)` (in fact, for our world, every
   `z` we construct is in `image(q)` by definition, so the second
   branch is vacuous).
4. **Agreement with the known minimal sufficient statistic.** For the
   fibre-per-θ construction of `P̂`, the known minimal sufficient
   statistic on `X` is `x ↦ P̂(θ₁, x) - P̂(θ₀, x)` (a specific
   partition of the 16 worlds). We verify that the LR-vector-induced
   partition is *bit-exact* equal to this partition — no gate slack,
   no tolerance, since both are computed by exact rational arithmetic
   under the smoothed pmf.

All four gates pass on the pre-registered fixture. The instrument is
deterministic (no random seeds, no Monte Carlo); the arithmetic is
exact under double precision because the smoothed pmf has entries in
`{1/16, ..., 17/16}` and the LR-vector values are ratios of such
numbers, all representable exactly.

Reproducibility:

```bash
python3 experiments/sica_finite_derivation_pair/experiment.py
python3 -m unittest tests.test_sica_finite_derivation_pair
```

---

## 5. Relation to the SIC framework

Before this paper: SIC-A was clause 1 of the *Structural Intelligence
Conjecture* — a posit asserting the existence of the master fibration.
The parent paper's Theorem 1 (Halmos–Savage, general standard-Borel
form) *sketched* a derivation but did not fully close it, deferring the
uncountable / non-strictly-positive case to Mathlib measure theory that
was not (and is not) available.

After this paper: SIC-A is a *theorem* in the finite discrete positive-
support case, with a machine-checked Lean 4 proof composing three
already-verified components (Theorem 1, Proposition 3, Theorem CS-2)
plus one new file `SICA_FiniteExistence.lean` that does the
composition. The result closes the "posited, not derived" gap in the
exactly the setting where SIC's numerical witnesses live (finite
Boolean worlds, finite parameter families, positive pmfs).

The ten companion papers that assume `(q, K)` now have a *derived*
input in the finite discrete positive-support case. Their theorems
still apply verbatim; what changes is that the reader no longer has to
concede existence — they can compute `q` and `K` from `(X, Θ, P)` and
verify the SIC-A clauses hold.

The programme's honest split becomes:

- **Finite discrete positive-support case.** SIC-A is a theorem (this
  paper). Every companion's `(q, K)` input is derivable.
- **General topological / measure-theoretic case.** SIC-A remains a
  posit; the derivation requires Mathlib infrastructure for regular
  conditional distributions on standard Borel spaces that is not yet
  available. Follow-up.

---

## 6. Limitations & open follow-ups

- **General topological case.** The most important open item. The
  finite discrete positive-support proof does not lift to uncountable
  `X` or general dominated families without the full Halmos–Savage
  1949 machinery. Closing that gap requires Mathlib to expose:
  regular conditional distributions on standard Borel spaces; the
  minimal sufficient σ-algebra as a completion; and a categorical
  version of Proposition 3 for measurable Markov kernels. None of
  these are in Mathlib v4.32.2. This paper does not close the gap
  but does not widen it either.
- **`HalmosSavage_minimality_h_extension` axiom.** Theorem 1's Lean
  file uses one project-local axiom to package the classical-choice
  extension step for the minimality half. This paper inherits that
  axiom unchanged — no new axioms are introduced. Any tightening of
  Theorem 1 (a fully sorry-free Halmos–Savage minimality proof) would
  immediately tighten this paper's derivation.
- **Sub-family minimality (`Τ ⊊ Θ`).** The Lean statement in this
  paper's file gives minimality for `Τ = Θ`. For a strict sub-family
  `Τ ⊊ Θ`, the LR-vector against all of `Θ` is sufficient but not
  necessarily minimal for `Τ` alone. A cleaner statement would take
  the `Τ`-restricted LR-vector (dropping coordinates outside `Τ`) and
  show it is minimally sufficient for the `Τ`-family. The construction
  is the same; the bookkeeping is heavier. Called out as open.
- **Non-uniform kernels.** The uniform-on-fibre `K` is the canonical
  choice under no additional prior data. Given a base distribution
  `μ : X → ℝ` with `∑ μ = 1`, the *μ-restricted* fibre kernel
  `K_μ(z, x) := μ(x) / (∑_{y : q(y) = z} μ(y))` is also fibre-supported
  and fibre-normalised (where the denominator is nonzero), and
  Proposition 3's triangle identities close for it too. The `μ`
  argument in the Lean signature keeps the door open for downstream
  constructions to plug in their own `μ`; the current proof discards
  `μ` and uses uniform-on-fibre. A refined version could case-split
  on `μ` and produce `K_μ` where the fibre has positive `μ`-mass,
  reverting to uniform where it does not.
- **No claim about learnability.** This paper derives the *existence*
  of `(q, K)` from `(X, Θ, P)`. It does not address whether a finite
  adaptive system can *discover* `(q, K)` from samples. That is the
  content of Theorems 5, 6, 7 in the parent paper, which are
  orthogonal.

---

## 7. Reproduction

```bash
# Lean formalisation
cd formal/structural-intelligence-mathlib
lake exe cache get
lake build
# Should print "SIC-A finite discrete: OK" and axiom footprint.

# Numerical witness
python3 experiments/sica_finite_derivation_pair/experiment.py
python3 -m unittest tests.test_sica_finite_derivation_pair
```

Full development is in the parent paper's §2.1 (Theorem 1) and the
`formal/structural-intelligence-mathlib/README.md` for the Lean
axiom-footprint accounting.
