# The Structural Intelligence Conjecture

## Representation as a Stochastic Fibration, with Three Exact Instruments

**Jawaun Brown**
Human author and research director

**Claude Code (agent)**
Experiment code, analysis, and manuscript production under direction and review

**Date:** August 3, 2026
**Status:** conjecture + three exact executable instruments (dissociations on solvable cases; the general claims remain open)

---

## Abstract

We study a single latent object that recurs across five otherwise unrelated
works — a category-theoretic framework for materials design, an
information-theoretic limit on the programmatic specification of biological
systems, a corpus of machine-found mathematical proofs with their discovery
notes, Wigner's essay on the unreasonable effectiveness of mathematics, and a
structural-realist ontology. We argue the common object is not a latent space
but a **stochastic fibration with a compiler**: a coarse-graining `q : X → Z`
together with a kernel `K : Z ⇝ X` whose support lies in the fiber `q⁻¹(z)`.
From this object we state the **Structural Intelligence Conjecture** — that a
finite adaptive system's central capability is to discover the quotient in which
task-relevant dynamics descend while irrelevant variation is confined to fibers,
i.e. the representation in which a hidden invariant becomes a coordinate axis.
We build three exact, deterministic, unit-tested instruments that establish the
dissociations the conjecture depends on: (1) a *Fiber Finder* showing that
sufficiency-then-compression recovers a ground-truth invariant where
description-length minimization and accuracy maximization fail; (2) a
*structure compiler* exhibiting one dynamical structure realized across four
substrates with verified structural identity; and (3) an *agency benchmark*
showing that signal, control, knowledge, and agency dissociate, so no single
scalar of behavioural influence identifies agency. We develop ten further
constructs (a conditional rate–distortion control limit, concern-as-fiber
geometry, abstraction frontiers, adversarial fiber audits, a theory atlas,
compiler tomography, causal semantics, a representation-repair calculus,
ensemble-governance alignment, and autocatalytic art) and close with an honest
construction target for conscious and reliable agents. The instruments are toys
by design; the master fibration is posited, not derived.

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

## 2. The conjecture

> **Structural Intelligence Conjecture.** A finite adaptive system's central
> capability is to discover a quotient `q : X → Z` such that (1) the
> task-relevant dynamics descend to `Z`, (2) irrelevant variation is confined to
> the fibers `q⁻¹(z)`, (3) useful interventions are compactly specifiable in `Z`,
> (4) those specifications re-instantiate through a compiler, and (5) their
> consequences remain stable across substrates and contexts.

In one line: intelligence finds the level at which the world becomes both
compressible and controllable.

---

## 3. Three exact instruments

Each instrument is exact (no sampling), deterministic, and covered by a unittest
suite; each is registered with a preregistration and structured provenance in the
host repository. They establish *dissociations on solvable cases*, not the general
conjecture.

### 3.1 Fiber Finder (`experiments/representation_search`)

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
sufficiency-then-compress rule finds the invariant. This is the discrete,
non-interventional core of the fiber audit (§4.4) and connects to the host
repository's finding that *weakness* (a fiber quantity) predicts generalization
where MDL (a specification-length quantity) does not.

### 3.2 Structure compiler (`experiments/structure_compiler`)

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
faithful functors, and is the base case for the autocatalytic work of §4.10.

### 3.3 Agency benchmark (`experiments/symbolic_causation`)

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
(§4.1), causal semantics (§4.7), and ensemble-governance alignment (§4.9).

---

## 4. The extended program

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
   "right" yet incomparable. Seeded by §3.1.
4. **Fiber audit.** Vary the allegedly irrelevant degrees of freedom while
   holding `q` fixed and measure `Δ_q(z) = sup_{x,x'∈q⁻¹(z)} d(P(Y|do x), P(Y|do
   x'))`. The operational form of Wigner's relevant/irrelevant split and the
   ontology's truth-as-invariance criterion; seeded (non-interventional core) by
   §3.1.
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
   layer that ordinary co-occurrence embeddings omit. Extends §3.3.
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
    §3.2.

---

## 5. Capstone: conscious and reliable agents, honestly

The program bears on two natural questions — can agents be made conscious, and
can they be made never wrong — and the disciplined answer to both is *not in the
literal sense*. The strongest defensible construction factors as two nested
systems.

**Concerned Self-Modeling Core** — an active, self-maintaining fixed point of the
coarse-graining loop: a persistent agent that maintains world- and self-models,
represents concern-weighted futures (§4.1), broadcasts selected information,
remembers commitments, predicts its own action consequences, performs
false-credit tests on its own causal claims (exactly §3.3's calibration metric),
and reports uncertainty. It operationalizes proposed consciousness *indicators*
— and that is the ceiling of the claim: **functional selfhood ⇏ subjective
consciousness.**

**Proof-Carrying Reliability Shell** — the fibration with a verifier on the
counit: convert goals to contracts, separate observation from inference, attach
provenance to every claim, and commit an action only under machine-checkable
evidence, `execute(a) ⇔ V(s,a,φ) = PASS`, else abstain/ask/simulate/escalate. Its
correctness envelope is a fiber audit (§4.4): vary everything the spec calls
irrelevant and check the property survives. **Verified-in-a-bounded-domain ⇏
universal infallibility:** verification certifies the formal statement, not that
it captures intent, and reliability also depends on model, harness, tools,
environment, and budget.

The honest breakthrough available now is therefore not conscious, perfect agents,
but agents with **experimentally measurable selfhood and formally bounded error**
— two separate, non-inflated claims.

---

## 6. Limitations

The three instruments are toys by design: they establish dissociations on
exactly-solvable cases (finite Boolean worlds, tiny Markov systems, lossless
encoders) and do not establish the general conjecture, the conditional
rate–distortion limit, or the alignment claim, all of which remain conjectural.
Instrument 2's fidelity is unity by construction. The master fibration `(q, K)`
is a controlling structure, not a derived theorem; only the biology paper proves
a specialized version. Nothing here licenses a claim of machine phenomenology.

---

## 7. Reproduction

```bash
python3 experiments/representation_search/experiment.py
python3 experiments/structure_compiler/experiment.py   # add --wav to render audio
python3 experiments/symbolic_causation/experiment.py
python3 -m unittest tests.test_representation_search tests.test_structure_compiler tests.test_symbolic_causation
```

Full development, the stochastic-fibration formalism, and the ten constructs are
in `notes/structural_intelligence_conjecture.md`; the underlying six-work
synthesis is in `notes/latent_structures_meta_framework.md`. An interactive demo
of the three instruments is served from `sites/structural_observatory`.
