# The Structural Intelligence Conjecture

## Representation as a Stochastic Fibration, with Four Exact Instruments

**Jawaun Brown**
Human author and research director

**Claude Code (agent)**
Experiment code, analysis, and manuscript production under direction and review

**Date:** August 3, 2026
**Status:** two theorems + one conditional theorem + one conjecture + four exact executable instruments (dissociations on solvable cases; the residual learnability claim remains open)

---

## Abstract

We study a single latent object that recurs across five otherwise unrelated
works — a category-theoretic framework for materials design, an
information-theoretic limit on the programmatic specification of biological
systems, a corpus of machine-found mathematical proofs with their discovery
notes, Wigner's essay on the unreasonable effectiveness of mathematics, and a
structural-realist ontology. The common object is a **stochastic fibration with
a compiler**: a coarse-graining `q : X → Z` together with a kernel `K : Z ⇝ X`
whose support lies in the fiber `q⁻¹(z)`. We derive the object — it is not
posited: for any statistical task on a standard Borel space, the minimal
sufficient σ-algebra of Halmos and Savage yields `(q, K)` as its quotient and
regular-conditional pair (Theorem 1); Shannon's rate–distortion pair
parameterises the same object at a distortion budget (Theorem 2); the
construction is the unit/counit of an adjunction (Proposition 3). Cross-task
stability — a single quotient that is sufficient for a whole task family —
holds *if and only if* the family admits a shared Markov screen, i.e. a common
latent generator (Theorem 4, a conditional theorem). What then remains a
conjecture is only *learnability* — that a finite adaptive system in fact
discovers such a quotient from data (Conjecture C1). We build four exact,
deterministic, unit-tested instruments: (1) a *Fiber Finder* showing that
sufficiency-then-compression recovers a ground-truth invariant where
description-length minimization and accuracy maximization fail (witness of
Theorem 1); (2) a *structure compiler* exhibiting one dynamical structure
realized across four substrates with verified structural identity; (3) an
*agency benchmark* showing that signal, control, knowledge, and agency
dissociate; and (4) a *cross-task sufficiency* instrument showing that the
coarsest common sufficient statistic of a family sharing a latent Z is Z
itself, while a family that reveals X beyond Z has only the identity as CSS
(witness of Theorem 4). We develop ten further constructs and close with an
honest construction target for conscious and reliable agents.

---

## 1. The master object

Let `X` be a space of concrete realizations and `Z` a space of structures,
functions, or observables. Two maps carry the construction:

- a coarse-graining `q : X → Z` saying which concrete differences do not matter,
  with **fiber** `q⁻¹(z)` the set of embodiments of structure `z`;
- a **compiler** `K : Z ⇝ X`, a Markov kernel with `supp K(· | z) ⊆ q⁻¹(z)`,
  producing a *distribution* of realizations rather than a single one.

This sharpens the adjunction `R ⊣ C` of the companion synthesis
(`notes/latent_structures_meta_framework.md`): `q = C` (coarse-grain) and `K` is
a stochastic section of `R` (realize). The biology paper of
Kiiskinen–Kivinen–Rivas is exactly this construction — the genome names `z`, the
physics substrate is the compiler `K` that "computes the samples," and selection
acts on the ensemble statistics — and its coarse-graining threshold `C*` proves
that below a critical resolution the fiber is too large to address with the
specification budget. The stochastic-fibration formulation is the director's
synthesis; no single source states it in this form.

**A note on rigor.** Cross-domain resemblance is not isomorphism. The honest
hierarchy of sameness runs isomorphism ⊃ bisimulation ⊃ functor ⊃ natural
transformation ⊃ adjunction/Galois connection ⊃ Morita-like equivalence ⊃
simulation-at-a-resolution. Most relations among the source works are
adjunctions, simulations, and shared diagram shapes, not object-level
isomorphisms; every proposed connection must state what kind of sameness it is,
what the map forgets, and what would have to be proved to make it a theorem.

---

## 2. Derivations

The three theorems and one conditional theorem below promote the master
fibration from an organizing analogy to a mathematical object with a specific
derivation, and split the fifth clause of the Structural Intelligence Conjecture
into a conditional theorem about the world's task ensemble and a residual
learnability conjecture about finite adaptive systems.

### 2.1 Existence via minimal sufficiency (Theorem 1)

Let `X` be a standard Borel space, `{P_θ : θ ∈ Θ}` a dominated family of
probability measures on `X`, and `Y` a random variable whose distribution
depends on `θ` (equivalently: `θ` indexes the task). The Halmos–Savage
sufficiency theorem gives a *sufficient* σ-algebra `𝒮 ⊆ 𝔅(X)`; under mild
regularity (Bahadur 1954; Lehmann–Casella) there is a *minimal* sufficient
σ-algebra `T ⊆ 𝒮`, unique up to `P`-null completion.

Define:

- `Z := X/∼_T`, the quotient of `X` by `T`-equivalence (`x ∼ x'` iff `x` and
  `x'` agree on every event in `T`);
- `q : X → Z`, the canonical projection;
- `K(· | z) := P_θ(· | T)(x)` for any `x ∈ q⁻¹(z)` — the regular conditional
  distribution, which by sufficiency does *not* depend on `θ` (existence and
  uniqueness a.s. from standard-Borel structure).

**Theorem 1 (Existence of the master fibration).** *`(q, K)` is a stochastic
fibration with `supp K(·|z) ⊆ q⁻¹(z)`, and four of the five clauses of the
Structural Intelligence Conjecture hold as theorems:*

1. **Task-relevance descends.** `P_θ(Y ∈ B | X) = P_θ(Y ∈ B | q(X))` almost
   surely, by sufficiency of `T`.
2. **Irrelevant variation is confined to fibers.** For all `x, x' ∈ q⁻¹(z)`,
   `L(Y | X = x) = L(Y | X = x')`; within a fiber, variation in `X` is `Y`-null.
3. **Compact specification.** `|image(q)| = |atoms(T)| ≤ |X|`, with strict
   inequality iff `T` is nontrivial.
4. **Re-instantiation via `K`.** By construction, `K` is a Markov kernel
   `Z ⇝ X` with the correct support; sampling from `K(· | q(x))` produces a
   realization drawn from the fiber of `x`.

The Fiber Finder (Instrument 1, §4.1) is an exact computational witness of
Theorem 1: on `X = {0,1}ⁿ` with a known Boolean invariant, it exhibits the
minimal sufficient quotient by exhaustive enumeration and demonstrates the
dissociation of *sufficiency*, *description length*, and *accuracy* on which
Theorem 1's clauses (1)–(4) turn.

### 2.2 Rate–distortion parameterisation (Theorem 2)

Let `X ~ p_X` on `X` and `d : X × X̂ → ℝ_+` a distortion. Shannon's
rate–distortion function

```
R(D) = inf_{p(x̂|x) : E[d(X, X̂)] ≤ D} I(X; X̂)
```

is attained by an encoder `p*(x̂ | x)` and decoder marginal `p*(x̂)`.

**Theorem 2 (RD parameterisation of the master fibration).** *For every
distortion budget `D ≥ 0`, the RD-optimal pair defines a stochastic fibration
`(q_D, K_D)`:*

- `q_D : X ⇝ Z_D`, the RD-optimal encoder — *deterministic* when the RD-optimal
  partition of `X` is achievable, *stochastic* otherwise (a "soft" fibration);
- `K_D(· | z) := p(X | q_D(X) = z)`, the Bayes decoder.

*The family `{(q_D, K_D) : D ≥ 0}` is a one-parameter deformation of the
sufficiency fibration: at `D = 0` the encoder is minimal-sufficient; as `D`
grows the fibers grow and the specification shrinks along the RD curve.*

The biology paper of Kiiskinen–Kivinen–Rivas is exactly the special case: its
threshold `C*` is `R(D_bio)` for the domain's distortion measure, and its "no
fourth category" result is the assertion that no encoder below `C*` has bounded
distortion — the fiber is irreducibly large.

### 2.3 Categorical restatement (Proposition 3)

Let **Prob(X)** and **Prob(Z)** be the categories of probability measures on
`X` and `Z`. The sufficient-statistic construction is the unit/counit pair of
an adjunction:

- coarse-grain `C : Prob(X) → Prob(Z)`, `C(μ) = q_* μ`;
- realize `R : Prob(Z) → Prob(X)`, `R(ν) = ∫ K(· | z) ν(dz)`;
- `C ⊣ R`, with unit `x ↦ q(x)` and counit given by `K`.

**Proposition 3 (Adjunction).** *`(q, K)` is the unit/counit pair of `C ⊣ R`.*
Clauses (1)–(4) of the SIC are the adjunction's triangle identities specialised
to the sufficiency reduction; the categorical framing adds compact language, not
new content.

### 2.4 Cross-task stability (Theorem 4, conditional)

Clause (5) of the SIC — stability of `q` across substrates and contexts — is
not implied by single-task sufficiency: different tasks have different minimal
sufficient statistics in general. The following upgrade shows clause (5) is
*equivalent to* the existence of a shared latent generator.

**Theorem 4 (Cross-task stability under latent generation).** *Suppose there
exists a random variable `Z` and, for every task in a family `{Y_α : α ∈ A}`,
a conditional independence*

```
Y_α  ⫫  X  |  Z.
```

*Then `Z` is a sufficient statistic for every `Y_α` simultaneously; equivalently,
the σ-algebra `σ(Z)` is a common sufficient σ-algebra for `{Y_α}` on `X`.*

*Proof.* For each `α`, sufficiency of `Z` for `Y_α` from `X` is exactly the
Markov property `Y_α ⫫ X | Z`; the family case is the pointwise conjunction.
□

**Corollary (Equivalence).** *A task family `{Y_α}` admits a common sufficient
statistic strictly coarser than `X` if and only if there is a decomposition
`X = g(Z, η)` with `Z ⫫ η` and every `Y_α` factoring through `Z`.*

Theorem 4 turns clause (5) into a claim about the *world* — the joint law of
`X` and the task family — rather than about *intelligence*. Its antecedent is
the manifold / disentanglement hypothesis of representation learning; where
that antecedent holds, cross-task stability is a theorem, not a conjecture.

The Cross-Task Sufficiency instrument (Instrument 4, §4.4) is an exact
computational witness of Theorem 4 on a 4-bit Boolean world with latent
`Z = (parity{0,1}, parity{2,3})`. For a task family whose members all factor
through `Z`, the coarsest common sufficient statistic is exactly `Z` (image
size 4, `< |X| = 16`); for a family that reveals individual coordinates
instead, the coarsest common sufficient statistic collapses to the identity.
Combining tasks strictly tightens the required partition: the family CSS is
finer than any single task's minimal sufficient statistic.

### 2.5 Learnability (Conjecture C1)

What Theorems 1–4 do **not** derive is that a finite adaptive system in fact
*discovers* `q` from data. That is an algorithmic/architectural claim about
learnability, not a mathematical one about existence.

**Conjecture C1 (Learnability).** *For any decomposition `X = g(Z, η)` with `Z`
low-dimensional (`dim Z ≪ dim X`), task family `{Y_α}` factoring through `Z`,
and identifiability gap `δ > 0`, there exists a finite adaptive architecture —
a hypothesis class, an optimizer, and a sample budget `N` — whose learned
quotient `q̂` satisfies*

```
I(Z; q̂(X))  /  I(Z; X)  →  1     as   N → ∞,
```

*at sample-complexity rate polynomial in `dim(Z)` and `1/δ`, uniformly over
the compiler `K`.*

Conjecture C1 is the honest residual: it says the sufficient-statistic quotient
(an object whose existence is guaranteed by Theorem 1) is *efficiently
recoverable* under the low-dimensional-`Z` antecedent of Theorem 4. This is
neither trivial (best-known bounds for disentanglement and information
bottleneck have exponential worst-case dependence on hypothesis-class
complexity) nor obvious. It is where the Structural Observatory becomes a
research programme rather than a theorem-book exercise.

### 2.6 SIC in the honest split

The theorems above split the Structural Intelligence Conjecture into three
strata, of increasing empirical exposure:

- **SIC-A — Existence.** Theorem 1 + Proposition 3. The master fibration
  exists as a mathematical object for any well-posed task. *Not conjectural.*
- **SIC-B — Cross-task stability.** Theorem 4 (conditional). Stability of a
  single `q` across a task family is equivalent to the family admitting a
  shared latent generator. *Theorem given the antecedent; the antecedent is
  empirical about the world / task ensemble.*
- **SIC-C — Learnability.** Conjecture C1. Whether a finite adaptive system
  in fact recovers such a `q` efficiently. *Genuinely open.*

The remainder of the paper states the SIC in its full-strength form (§3),
exhibits its four exact instruments (§4), sketches ten further constructs
generated by the master object (§5), and closes with an honest construction
target for conscious and reliable agents (§6).

---

## 3. The conjecture

> **Structural Intelligence Conjecture.** A finite adaptive system's central
> capability is to discover a quotient `q : X → Z` such that (1) the
> task-relevant dynamics descend to `Z`, (2) irrelevant variation is confined to
> the fibers `q⁻¹(z)`, (3) useful interventions are compactly specifiable in `Z`,
> (4) those specifications re-instantiate through a compiler, and (5) their
> consequences remain stable across substrates and contexts.

In one line: intelligence finds the level at which the world becomes both
compressible and controllable.

---

## 4. Four exact instruments

Each instrument is exact (no sampling), deterministic, and covered by a unittest
suite; each is registered with a preregistration and structured provenance in the
host repository. Instruments 1 and 4 are computational witnesses of Theorems 1
and 4 respectively; instruments 2 and 3 establish auxiliary dissociations on
solvable cases.

### 4.1 Fiber Finder (`experiments/representation_search`)

Over all `2ⁿ` worlds of an `n`-bit Boolean space with a known ground-truth
invariant, we enumerate a lattice of candidate quotients (constant, every-subset
parity, identity) and three selectors. Writing `H(Y | q(X))` for the residual
task entropy and `log₂|image(q)|` for the description length:

- `minimal_sufficient` — among quotients with `H(Y | q(X)) = 0`, minimize
  description length;
- `mdl_only` — minimize description length;
- `accuracy_only` — maximize mutual information, tie-broken toward the finest map.

**Result (exact).** In every task, `minimal_sufficient` recovers the exact
ground-truth invariant; `mdl_only` selects the constant map (insufficient —
`H(Y | q(X)) > 0`, the obstruction collapses); `accuracy_only` selects the
identity (sufficient but uncompressed, `log₂|image| = n`). Sufficiency,
description length, and accuracy are three different quantities, and only the
sufficiency-then-compress rule finds the invariant. This is the computational
witness of Theorem 1: it exhibits the minimal sufficient quotient by
exhaustive enumeration and shows the failure modes of the two natural
alternatives. It is also the discrete, non-interventional core of the fiber
audit (§5.4) and connects to the host repository's finding that *weakness* (a
fiber quantity) predicts generalization where MDL (a specification-length
quantity) does not.

### 4.2 Structure compiler (`experiments/structure_compiler`)

An abstract automaton exhibits accumulation (a level integrates an input), a
phase transition (a regime flips at an up-threshold), and hysteresis (the
down-threshold is lower, so the regime remembers). From a fixed input schedule it
produces a deterministic trajectory of `(level, regime)` pairs. Four compilers
`Fᵢ` map the trajectory into music (pitch/octave), a visual field (height/hue),
text (regime-keyed lexicon, line length ∝ level), and spatial navigation (a
corridor with regime-gated edges); each has a readback `qᵢ`.

**Result (exact).** For every medium `qᵢ ∘ Fᵢ = id` on the trajectory
(fidelity 1.0), and all media read back to the *same* abstract trajectory: the
four embodiments are verifiably one work, not four mood-matched artefacts. The
structure genuinely contains the motifs (a mid-level appears in both regimes).
Fidelity is 1.0 *by construction* — the instrument tests that the compilers are
faithful functors, and is the base case for the autocatalytic work of §5.10.

### 4.3 Agency benchmark (`experiments/symbolic_causation`)

An exact finite-state world with target and failure regions; futures are
enumerated to the horizon. A symbolic model `m` is an operation on the trajectory
distribution `P(γ | s)`. We measure **signal** `Δ_KL = KL(P(γ|m) ‖ P(γ|baseline))`,
**control** `goal_gain`, **knowledge** `predictive_accuracy`, and **agency**
(control + small `calibration_error` between claimed and true do-effect +
positive `transfer` under a perturbation the intervention did not choose).

**Result (exact).** Seven hand-built conditions realize distinct metric
signatures recovered by a fixed classifier: a `noise_signal` condition moves the
distribution with zero control; a `knowledge_only` condition predicts with zero
signal; a **false_credit** condition improves the observed outcome while its true
do-effect is zero and its self-attribution is miscalibrated; and a brittle
controller controls but does not transfer. No single scalar of behavioural
influence identifies agency. This is the measurement core for concern geometry
(§5.1), causal semantics (§5.7), and ensemble-governance alignment (§5.9).

### 4.4 Cross-task sufficiency (`experiments/cross_task_sufficiency`)

On the 4-bit Boolean world `X = {0,1}⁴` with latent
`Z(x) = (parity{0,1}(x), parity{2,3}(x))`, we enumerate a lattice of quotients
that includes single-bit reads, all subset parities, joint pair-parities
(including `Z` itself), joint bit reads, and the identity. Two task families:

- *Shared through* `Z`: `parity{0,1}`, `parity{2,3}`, `parity{0,1,2,3}` —
  every task factors through `Z`.
- *Not shared beyond* `Z`: `bit_0`, `bit_1`, `bit_2`, `bit_3` — each task
  reveals a single coordinate.

For each family and each quotient we compute exact per-task conditional
entropies and common-sufficiency status; the coarsest common sufficient
statistic (CSS) is the smallest-image quotient that is sufficient for every
task in the family.

**Result (exact).** For the shared family, the coarsest CSS is exactly
`joint(parity{0,1}, parity{2,3}) = Z` (image size 4, description length 2 bits,
strictly less than `log₂|X| = 4` bits). For the not-shared family, the coarsest
CSS is the identity map (image size 16, no compression). For the shared family,
each single task's minimal sufficient statistic is a 1-bit parity (image size
2), strictly coarser than the family CSS's 4-class partition: combining tasks
tightens the required partition by a factor of two.

This is the computational witness of Theorem 4. Cross-task stability — the
world's tasks admitting a single shared quotient — is *not* a property the
system posits; it is a property of the task family. When the family admits a
common Markov screen, the CSS collapses to the screen. When it does not, the
CSS is the identity. The dissociation is exact.

---

## 5. The extended program

Each construct is a target generated by the master object; those marked
*conjectural* are not proved here.

1. **Concern as fiber geometry.** A concern state reweights the compiler,
   `K_c(dx|z) ∝ e^{β U_c(x,z)} K(dx|z)`, inducing an information geometry (Fisher
   metric) on concern states; concern transport between contexts is transport
   between kernels, and its holonomy measures path-dependence. Extends the host
   repository's *Geometry of Concern* and *Gauge-Fixed Transport of Concern*.
2. **Conditional rate–distortion control limit** (*conjectural*). Robust control
   of `Y = f(X)` from a coarse spec `Z = q(X)` requires `H(Y|Z) ≈ 0`, or under
   tolerated distortion `D`, extra addressed bits `B_extra ≥ R_{Y|Z}(D)` — a
   generalization of the biology theorem explaining why exact micromanagement
   fails.
3. **Abstraction frontier.** The Pareto set trading task-sufficiency
   `I(Y;X|q(X))`, dynamical closure `I(Z_{t+1};X_t|Z_t,A_t)`, cost `H₀(Z)`, and
   control regret — an antichain, explaining why two representations can both be
   "right" yet incomparable. Seeded by §4.1.
4. **Fiber audit.** Vary the allegedly irrelevant degrees of freedom while
   holding `q` fixed and measure `Δ_q(z) = sup_{x,x'∈q⁻¹(z)} d(P(Y|do x), P(Y|do
   x'))`. The operational form of Wigner's relevant/irrelevant split and the
   ontology's truth-as-invariance criterion; seeded (non-interventional core) by
   §4.1. *Cross-task version:* Instrument 4 (§4.4) — the coarsest common
   sufficient statistic is the operational fiber audit at the family level.
5. **Theory atlas.** Treat theories as charts `M_i` on contexts `U_i` with
   translations `T_ij`; test the cocycle `T_jk ∘ T_ij = T_ik`. Where it fails, the
   obstruction is informative — a sheaf/stack view of theory integration for
   Wigner's non-unification worry.
6. **Compiler tomography.** Infer the shared compiler and compact specs from many
   `(s_i, x_i)` by MDL; then compiler ecology `K_{t+1} = U(K_t, outcomes)` — build
   a compiler under which good outcomes are cheap, the formal language for
   education, institutions, and long-horizon training.
7. **Causal semantics.** Two symbols are equivalent when they induce naturally
   equivalent update operators `Ψ_{m,c}` across independent contexts — a meaning
   layer that ordinary co-occurrence embeddings omit. Extends §4.3.
8. **Representation-repair calculus.** A library mapping failure signatures to
   minimal structural lifts (scalar→operator, global norm→localized measure,
   quotient→restored fiber, static→path space, affine→projective, point→ensemble,
   non-composing→interface, symmetry→gauge-fix). Reads the machine discovery notes
   directly.
9. **Alignment as ensemble governance** (*conjectural*). Target a viable region
   `V ⊆ Z` with `Pr[q(X_t) ∈ V ∀t] ≥ 1−δ` under a broad family of unresolved
   compiler/environment states; a fiber audit is the alignment evaluation.
10. **Autocatalytic artwork.** `S_t →K_t E_t →(experience) K_{t+1}`: early
    movements teach the grammar by which later movements become legible. Extends
    §4.2.

---

## 6. Capstone: conscious and reliable agents, honestly

The program bears on two natural questions — can agents be made conscious, and
can they be made never wrong — and the disciplined answer to both is *not in the
literal sense*. The strongest defensible construction factors as two nested
systems.

**Concerned Self-Modeling Core** — an active, self-maintaining fixed point of the
coarse-graining loop: a persistent agent that maintains world- and self-models,
represents concern-weighted futures (§5.1), broadcasts selected information,
remembers commitments, predicts its own action consequences, performs
false-credit tests on its own causal claims (exactly §4.3's calibration metric),
and reports uncertainty. It operationalizes proposed consciousness *indicators*
— and that is the ceiling of the claim: **functional selfhood ⇏ subjective
consciousness.**

**Proof-Carrying Reliability Shell** — the fibration with a verifier on the
counit: convert goals to contracts, separate observation from inference, attach
provenance to every claim, and commit an action only under machine-checkable
evidence, `execute(a) ⇔ V(s,a,φ) = PASS`, else abstain/ask/simulate/escalate. Its
correctness envelope is a fiber audit (§5.4): vary everything the spec calls
irrelevant and check the property survives. **Verified-in-a-bounded-domain ⇏
universal infallibility:** verification certifies the formal statement, not that
it captures intent, and reliability also depends on model, harness, tools,
environment, and budget.

The honest breakthrough available now is therefore not conscious, perfect agents,
but agents with **experimentally measurable selfhood and formally bounded error**
— two separate, non-inflated claims.

---

## 7. Limitations

The four instruments are toys by design: they establish dissociations and
witness the two existence theorems on exactly-solvable cases (finite Boolean
worlds, tiny Markov systems, lossless encoders). The master fibration `(q, K)`
*is* derived — Theorem 1 (minimal sufficiency) and Theorem 2 (rate–distortion)
give it as a mathematical object for any well-posed task on a standard Borel
space, and Proposition 3 gives the categorical restatement. The residual
conjectural content is:

- **SIC-B antecedent (empirical).** Theorem 4 gives cross-task stability
  conditional on the task family admitting a common Markov screen. Whether the
  actual world's task ensemble admits one is an empirical question about
  physics, biology, cognition, and culture — not a theorem this paper proves.
  The manifold / disentanglement hypothesis in representation learning is one
  operational form of the antecedent.
- **SIC-C (Conjecture C1, algorithmic).** Whether a finite adaptive system in
  fact *discovers* `q` from data with polynomial sample complexity remains
  open; best-known bounds for disentanglement and information bottleneck have
  exponential worst-case dependence on hypothesis-class complexity.
- **Extended-program conditionals.** The conditional rate–distortion control
  limit (§5.2) and the alignment claim (§5.9) remain flagged as conjectural in
  §5. Instrument 2's fidelity is unity *by construction* — it tests that the
  compilers are faithful functors, not that faithful compilation is hard.
- **No machine phenomenology.** Nothing in Theorems 1–4 or Conjecture C1
  licenses a claim of subjective experience; §6 draws that line explicitly.

---

## 8. Reproduction

```bash
python3 experiments/representation_search/experiment.py
python3 experiments/structure_compiler/experiment.py   # add --wav to render audio
python3 experiments/symbolic_causation/experiment.py
python3 experiments/cross_task_sufficiency/experiment.py
python3 -m unittest tests.test_representation_search \
                    tests.test_structure_compiler \
                    tests.test_symbolic_causation \
                    tests.test_cross_task_sufficiency
```

Full development, the stochastic-fibration formalism, and the ten constructs are
in `notes/structural_intelligence_conjecture.md`; the underlying six-work
synthesis is in `notes/latent_structures_meta_framework.md`. An interactive demo
of the four instruments is served from `sites/structural_observatory`.
