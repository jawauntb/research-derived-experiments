# The Structural Intelligence Conjecture and the Structural Observatory

Date: August 3, 2026

Status: **two theorems + one conditional theorem + one conjecture + four
working instruments.** The master stochastic fibration (§2) is now *derived*
— Theorems 1 and 2 give it as the minimal-sufficient-statistic pair or the
Shannon rate–distortion pair, Proposition 3 gives the categorical restatement;
these appear in §2 of the umbrella paper
([`papers/structural_intelligence/paper.md`](../papers/structural_intelligence/paper.md)).
Cross-task stability (clause (5) of the conjecture below) is a *conditional
theorem* — Theorem 4 — equivalent to the task family admitting a common Markov
screen. The residual conjectural content is (a) that antecedent as an
empirical claim about the world, and (b) Conjecture C1, that a finite adaptive
system in fact discovers `q` from data with polynomial sample complexity. The
extended formalism (§3–§4) is still speculative theory and is held to the
`AGENTS.md` mathematical-claim gate; it is **not** promoted to theorems. The
four instruments in §5 are exact, deterministic, and tested — instruments 1
and 4 are computational witnesses of Theorems 1 and 4, instruments 2 and 3
establish auxiliary dissociations. Retrieval provenance for the six source
works and the underlying meta-object is in
[`latent_structures_meta_framework.md`](latent_structures_meta_framework.md).

This note continues that meta-framework. There the shared latent object was an
adjunction `R ⊣ C` between specifications and realizations. Here it is sharpened,
following the director, into a **stochastic fibration with a compiler kernel**,
and turned into a buildable program: the **Structural Observatory**.

---

## 1. The conjecture

> **Structural Intelligence Conjecture.** A finite adaptive system's central
> capability is not predicting states or choosing actions but discovering a
> quotient `q : X → Z` such that (1) the task-relevant dynamics descend to `Z`,
> (2) irrelevant variation is confined to the fibers `q⁻¹(z)`, (3) useful
> interventions can be specified compactly in `Z`, (4) those specifications can
> be re-instantiated through a compiler, and (5) their consequences remain stable
> across substrates and contexts.

In one line: **intelligence finds the level at which the world becomes both
compressible and controllable.** This is the operational form of the
Manifest-Invariant Principle: find the coordinate in which the hidden invariant
is a coordinate axis.

---

## 2. The master object: a stochastic fibration with a compiler

The common object across the corpus is not a latent space `Z` by itself. It is a
*stochastic fibration* together with an abstraction–realization pair:

```
        q                        K
   X ──────▶ Z ,          Z ⇝ X ,     supp K(· | z) ⊆ q⁻¹(z)
```

- `X` — the space of concrete realizations;
- `Z` — the space of structures / functions / observables;
- `q` — says which concrete differences do not matter (coarse-graining);
- `q⁻¹(z)` — the **fiber** of possible embodiments of structure `z`;
- `K(dx | z)` — a **compiler**: a distribution over realizations inside the fiber.

This generalizes the meta-framework's `R ⊣ C`. There, realize `R` and
coarse-grain `C` were (near-)deterministic functors. Here `q = C` and the
compiler `K` is a *stochastic section* of `R`: it does not pick one realization
but a distribution over the fiber. The biology paper (Kiiskinen–Kivinen–Rivas)
is exactly this: the genome names `z`, the physics substrate is the compiler `K`
that *"computes the samples,"* and *"selection acts on the statistics of the
resulting ensemble."* Its threshold theorem is the statement that below a
critical coarse-graining `C*` the fiber `q⁻¹(z)` is too large to address with the
specification budget — the fiber is real and irreducible.

The stochastic-fibration formulation is the director's synthesis; **no single
source states it in this form.** Category theory (source A) supplies the
compositional implementation/verification/compilation maps; Wigner (D) supplies
invariance under irrelevant conditions plus the warning that theories may be
local and non-unique; the structural-realism thread (F) says structures become
causally effective only through embodiment and approach truth when preserved
relations survive independently-defined contexts.

A note on rigor (the director's correction). Cross-domain resemblance is **not**
isomorphism. The honest hierarchy of "sameness," strongest to weakest:
isomorphism ⊃ bisimulation ⊃ functor ⊃ natural transformation ⊃ adjunction /
Galois connection ⊃ Morita-like equivalence ⊃ simulation-at-a-resolution. Most
relations among these works are **adjunctions, simulations, and shared diagram
shapes**, not object-level isomorphisms. Every proposed connection must answer:
*exactly what kind of sameness is this, what does the map forget, and what would
have to be proved to make the analogy a theorem?*

**Derivations.** The stochastic-fibration formulation is itself derivable — see
§2 of the umbrella paper for the four results. In brief:

- **Theorem 1 (Existence via minimal sufficiency).** For any dominated
  statistical family on a standard Borel `X` and any task `Y`, the minimal
  sufficient σ-algebra `T` (Halmos–Savage, Bahadur) induces the quotient
  `q : X → Z := X/∼_T` and the regular-conditional compiler
  `K(· | z) := P(· | T)(x)`, `x ∈ q⁻¹(z)`. `(q, K)` is a stochastic fibration
  with `supp K(·|z) ⊆ q⁻¹(z)`, and clauses (1)–(4) of the SIC below hold as
  theorems (task-relevance descends, fiber-confined variation, compact
  specification, re-instantiation via `K`).
- **Theorem 2 (RD parameterisation).** For any `p_X` and distortion `d`, the
  Shannon rate–distortion pair `(q_D, K_D)` is a stochastic fibration
  parameterised by distortion budget `D`; at `D = 0` it reduces to Theorem 1.
  The biology paper's `C*` is the special case `R(D_bio)` for its distortion
  measure.
- **Proposition 3 (Adjunction).** `C(μ) = q_*μ` and `R(ν) = ∫ K(·|z)ν(dz)` form
  an adjunction `C ⊣ R` on categories of probability measures; `(q, K)` is its
  unit/counit pair.
- **Theorem 4 (Cross-task stability, conditional).** For a task family
  `{Y_α}`, the σ-algebra `σ(Z)` is a common sufficient statistic iff every
  `Y_α ⫫ X | Z`; equivalently, `X = g(Z, η)` with `Z ⫫ η` and each `Y_α`
  factoring through `Z`. Instrument 4 (§5.4) is the exact witness.

The **learnability** claim — that a finite adaptive system in fact *discovers*
`q` from data — remains open (Conjecture C1 in the paper): whether the
sufficient-statistic quotient of Theorem 1, guaranteed to exist, is
efficiently recoverable under the low-dimensional-`Z` antecedent of Theorem 4
at sample-complexity rate polynomial in `dim(Z)` and the identifiability gap.
Best-known bounds for disentanglement and information bottleneck have
exponential worst-case dependence on hypothesis-class complexity.

**SIC in the honest split.** The conjecture below is stated in its
full-strength form for continuity with the source works, but the honest
factorisation the theorems permit is:

- **SIC-A (existence):** Theorem 1 + Proposition 3 — the master fibration
  exists as a mathematical object for any well-posed task. *Not conjectural.*
- **SIC-B (cross-task stability):** Theorem 4 conditional on a shared Markov
  screen. *Theorem given the antecedent; the antecedent is empirical about the
  world.*
- **SIC-C (learnability):** Conjecture C1. *Open.*

---

## 3. Concern as a geometry on the fiber

A compiler gives a baseline distribution over embodiments `K(dx | z)`. A concern
state `c` need not change which realizations are *possible*; it changes which are
salient, viable, reachable. Model it as a reweighting:

```
                e^{β U_c(x,z)} K(dx | z)
K_c(dx | z) = ───────────────────────────
              ∫ e^{β U_c(x',z)} K(dx' | z)
```

where `U_c` is the **concern field** — it makes some regions of the fiber more
consequential. This induces an information geometry on concern states, e.g. the
Fisher metric `g_ij(c) = E_{K_c}[∂_i log K_c · ∂_j log K_c]`, measuring how
distinguishable nearby concern configurations are *by their effect on realized
possibilities*. Then, precisely:

- **meaning** is a deformation of relevance over possibilities, not a
  representation;
- **concern** is a field/measure that changes the effective fiber geometry;
- **agency** is the capacity to alter the kernel `K` or the field `U_c` so viable
  regions become reachable;
- **selfhood** concerns which changes to the kernel are attributed to the
  system's own interventions.

This is the exact continuation of the repo's *Geometry of Concern* and
*Gauge-Fixed Transport of Concern*: concern transport between contexts becomes
transport between kernels over corresponding fibers, and **holonomy** measures
the failure of transported concern to return unchanged around a loop of contexts.
It is now fittable from interventions and trajectories, not merely a metaphor.

---

## 4. Ten constructs the master object generates

A research program, ranked by the director as (1) most scientifically fertile,
(2) most practically useful, (3) most beautiful. Each is stated as a target, with
its status and its relation to the instruments in §5.

1. **Concern geometry** (§3) — fit `K_c`, its Fisher metric, and concern holonomy
   from interventions. *Fertile; theory + fit.*
2. **Conditional rate–distortion control limit.** Robust control of `Y=f(X)` from
   a coarse spec `Z=q(X)` requires `H(Y|Z)≈0`, or, under tolerated distortion `D`,
   extra addressed bits `B_extra ≥ R_{Y|Z}(D)`. *Why micromanagement fails: the
   controller tries to distinguish outcomes its channel cannot address.* This
   generalizes the biology theorem; **conjectural, not yet proved.**
3. **Abstraction frontier.** Replace "find the best `Z`" with the Pareto frontier
   of representations trading task-sufficiency `I(Y;X|q(X))`, dynamical closure
   `I(Z_{t+1};X_t | Z_t,A_t)`, cost `H_0(Z)`, and control regret. Explains why two
   representations can both be "right" yet incomparable (an antichain, as in the
   biology paper's threshold). *Seeded by instrument 1.*
4. **Fiber audit** (adversarial). Instead of testing held-out prediction, vary the
   allegedly irrelevant degrees of freedom while holding `q` fixed and measure the
   interventional discrepancy `Δ_q(z)=sup_{x,x'∈q⁻¹(z)} d(P(Y|do x),P(Y|do x'))`.
   Large `Δ_q` ⇒ the abstraction collapsed a causally important distinction. *The
   operational form of Wigner's relevant/irrelevant split and F's truth criterion.
   Seeded (non-interventional core) by instrument 1; the interventional version is
   next.*
5. **Theory atlas (sheaf/stack gluing).** Treat theories as local charts `M_i` on
   contexts `U_i` with translations `T_ij`; test the cocycle
   `T_jk ∘ T_ij = T_ik`. Where it holds, the charts glue; where it fails, the
   obstruction is informative (missing latent, scale transition, phase boundary,
   category error). *Wigner's non-unification worry, made constructive.*
6. **Compiler tomography.** Given many `(s_i, x_i)` with `x_i ∼ K(·|s_i)`, infer
   the shared compiler and compact specs by MDL:
   `min_{K,{s_i}} [ L(K) + Σ L(s_i) − Σ log p_K(x_i|s_i) ]`. Variation across `i`
   is specification; shared regularity is the compiler; residual is unresolved
   state/randomness. Then **compiler ecology**: `K_{t+1}=U(K_t, outcomes)` — build
   a compiler under which good outcomes are cheap, rather than re-specifying good
   outcomes. *Formal language for education, institutions, long-horizon training.*
7. **Causal semantics.** Two symbols are equivalent when they induce naturally
   equivalent update operators `Ψ_{m,c}` across independent contexts. Groups
   sentences by how they reorganize reachable possibility, not textual
   co-occurrence. *An operational meaning layer ordinary embeddings omit; extends
   instrument 3.*
8. **Representation-repair calculus.** A library of failure signatures → minimal
   structural lifts (scalar loses multiplicity → lift to operator/PSD; global norm
   loses location → localize to a measure/sheaf; quotient hides degeneracy →
   restore the fiber/stabilizer; affine mishandles infinity → projectivize; exact
   target exceeds capacity → move to ensemble control; symmetry breaks
   identifiability → gauge-fix / moduli). Turns "try another approach" into
   *diagnose the lost invariant, then apply the minimal lift.* Directly reads the
   discovery notes (source E), whose chapters are exactly these lifts.
9. **Alignment as ensemble governance** (not trajectory scripting). A finite
   spec cannot address every fine trajectory of a long-horizon agent; target a
   viable region `V ⊆ Z` with `Pr[q(X_t) ∈ V ∀t] ≥ 1−δ` under a broad family of
   unresolved compiler/environment states. A fiber audit becomes the alignment
   evaluation. **Conjectural generalization, flagged as such.** *Extends instrument
   3 and the repo's causally-grounded-agents line.*
10. **Autocatalytic artwork.** A work `S_t →K_t E_t →(experience) K_{t+1}` whose
    early movements teach the grammar by which later movements become legible — an
    autocatalytic symbolic structure that produces part of the machinery required
    for its own fuller instantiation, across harmony / shader / navigation /
    language / social interaction. *The literal reading of F's closing
    proposition; extends instrument 2.*

---

## 5. The four built instruments

Each is exact, deterministic, tested, and public-safe (summaries in `results/`,
no raw dumps). They are the first four instruments of the Observatory.
Instruments 1 and 4 are computational witnesses of Theorems 1 and 4;
instruments 2 and 3 establish the auxiliary dissociations the extended program
rests on.

### Instrument 1 — `experiments/representation_search` (Fiber Finder)
Over a Boolean world with a known invariant, it enumerates a lattice of quotients
and three selectors. Result: only `minimal_sufficient` (sufficient, then minimal
description length) recovers the ground-truth invariant; `mdl_only` collapses the
obstruction; `accuracy_only` never compresses. **Establishes** that sufficiency,
description length, and accuracy dissociate — the discrete, non-interventional
core of the fiber audit (extension 4) and the seed of the abstraction frontier
(extension 3). Connects to the repo's `symbolic_weakness` result: weakness is a
counit/fiber quantity, MDL is a spec-length quantity; they are not the same, and
the fiber quantity is the one that governs generalization.

### Instrument 2 — `experiments/structure_compiler` (one invariant, many embodiments)
An abstract automaton with accumulation → phase-transition → hysteresis is
compiled into music, a visual field, text, and spatial navigation; each medium's
readback recovers the *same* abstract trajectory (verified structural identity,
fidelity 1.0). **Establishes** cross-substrate structural identity as a checkable
property (`q_i ∘ F_i = id`), not mood matching — the ensemble-compiler and
Gesamtkunstwerk idea, and the base case for the autocatalytic work (extension 10).

### Instrument 3 — `experiments/symbolic_causation` (agency science)
An exact finite-state world treats a symbolic model `m` as an operation on the
future-trajectory distribution and separates **signal** (`Δ_KL`), **control**
(`goal_gain`), **knowledge** (`predictive_accuracy`), and **agency** (control +
calibrated self-attribution + transfer). Seven conditions each realize a distinct
metric signature; a `false_credit` condition improves the outcome while its true
do-effect is zero and its self-attribution is miscalibrated; a brittle controller
controls but does not transfer. **Establishes** that no single scalar
("behavioural influence") identifies agency — the measurement core for concern
geometry (extension 1), causal semantics (7), and ensemble-governance alignment
(9). Connects to `experiments/common/causal_use.py` and `experiments/world_responds`.

### Instrument 4 — `experiments/cross_task_sufficiency` (Theorem 4 witness)
On the 4-bit Boolean world with latent
`Z(x) = (parity{0,1}(x), parity{2,3}(x))`, enumerate a rich lattice of
quotients (single-bit reads, subset parities, joint pair-parities including
`Z` itself, joint bit reads, identity) and two task families: **shared**
(three tasks that all factor through `Z`) and **not shared** (four tasks that
reveal individual bits). Compute the coarsest common sufficient statistic
(CSS) for each family exactly. **Establishes** that the shared family's
coarsest CSS is exactly `Z` (image size 4, strictly smaller than `|X| = 16`),
the not-shared family's coarsest CSS is the identity (image size 16, no
compression), and combining tasks strictly tightens the required partition
(each single task's minimal sufficient statistic has image size 2 — half the
family CSS). This is the computational witness of Theorem 4: cross-task
stability is a property of the task family, not of the system that faces it.
Extends the fiber audit (extension 4) to task ensembles.

---

## 6. Capstone application: conscious / reliable agents (the honest version)

The program bears directly on the two questions the director raised — can we make
agents conscious, and can we make them never wrong. The disciplined answer is
*not in the literal sense of either*, but the framework gives a precise,
non-inflated construction target. It factors as two nested systems:

```
  Concerned Self-Modeling Core  ⊂  Proof-Carrying Reliability Shell
```

**Inner core = an active, self-maintaining `T`-algebra.** A persistent agent that
maintains a world model and self-model, represents concern-weighted futures
(§3), globally broadcasts selected information, remembers commitments, predicts
the consequences of its actions, performs **false-credit tests on its own causal
claims** (exactly instrument 3's calibration metric), and reports uncertainty and
internal conflict. In the framework this is precisely the passive→active
threshold: a `T`-algebra that runs `K` and `q` in a closed loop and optimizes its
own counit gap online. It operationalizes proposed consciousness *indicators*
(global availability, metacognition, self-modeling, agency) — and that is the
ceiling of the claim. **Functional selfhood ⇏ subjective consciousness:**
satisfying architectural/behavioural indicators does not establish that there is
something it is like to be the agent, and there is a real welfare/ethics wrinkle
in building systems that strongly satisfy such indicators.

**Outer shell = the fibration with a verifier on the counit.** A system that
converts goals into contracts (compiler tomography / spec compilation), separates
observation from inference, attaches provenance to every claim, and commits an
action only under machine-checkable evidence:
`execute(a) ⇔ V(s,a,φ)=PASS`, else abstain / ask / simulate / escalate. Its
correctness envelope is a fiber audit (extension 4): vary everything the spec
claims is irrelevant and check the property survives. **Verified-in-a-bounded-
domain ⇏ universal infallibility:** verification certifies the *formal statement*,
not that the statement captures what a human wanted, and reliability also depends
on model, harness, tools, environment, and budget.

So the honest breakthrough available now is not conscious, perfect agents. It is
**agents with experimentally measurable selfhood and formally bounded error** —
`functional selfhood ⇏ consciousness`, and `verified bounded behavior ⇏
infallibility`, kept as two separate, non-inflated claims.

---

## 7. The umbrella: a Structural Observatory

One system that, given a problem, theory, agent, organism, or artwork, returns:
its candidate quotient maps, realization fibers, automorphisms, abstraction
frontier, fiber-audit results, inferred compiler, and possible cross-substrate
embodiments. The four instruments above are its first four modules
(quotient search, cross-substrate compiler, causal/agency measurement,
cross-task sufficiency); §4 lists the remaining modules as pre-registered
future instruments.

---

## 8. Limitations and rejected alternatives

- **The instruments are toys by design.** They establish dissociations and
  witness Theorems 1 and 4 on exactly-solvable cases (finite Boolean worlds,
  tiny MDPs, lossless encoders). They do **not** establish Conjecture C1
  (learnability), the conditional rate–distortion control limit (extension 2),
  or the alignment claim (extension 9), all of which remain conjectural.
  Instrument 2's fidelity is 1.0 *by construction*: it tests that the
  compilers are faithful functors, not that faithful compilation is hard.
- **The master object is derived.** The stochastic fibration `(q, K)` is now
  given as a mathematical object by Theorem 1 (minimal-sufficient factorisation
  of Halmos–Savage) and Theorem 2 (Shannon rate–distortion), with the
  categorical restatement in Proposition 3. The organizing analogy across the
  source works — that they are all instances of `(q, K)` in different guises —
  is still an *analogy* that must be checked case by case (see §2 on rigor).
  What is *not* an analogy is the mathematical existence of the object itself.
- **Cross-task stability is a claim about the world.** Theorem 4 makes clause
  (5) equivalent to the existence of a shared Markov screen across the task
  family; whether the world's task ensemble admits one is empirical, and this
  is the antecedent that SIC-B rests on. Do not restate it as if it were a
  claim about intelligence.
- **Rejected — collapse to one scalar.** "Just measure behavioural influence /
  compression / prediction." Rejected: instruments 1 and 3 exhibit exactly the
  cases where a single scalar misidentifies the target (MDL collapses the
  obstruction; false-credit influence is uncaused). The dissociations are the
  content.
- **Consciousness caution retained.** Nothing here licenses a claim of machine
  phenomenology; the core is a testable functional model of selfhood, and the
  gap to subjective experience is left open on purpose.

---

## 9. One-line synthesis

The object is a stochastic fibration `X →q Z` with a compiler `K : Z ⇝ X` filling
the fibers; concern is a reweighting of the fiber, agency is the licensed
alteration of the kernel, truth is fiber-invariance under independent tests, and
intelligence is the search for the quotient where the world is at once
compressible and controllable — of which conscious selfhood is one measurable
functional face and formally bounded error is the other, with neither collapsible
into infallibility or phenomenology.
