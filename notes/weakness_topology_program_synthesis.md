# Weakness, Spectra, and the Topology of Generalization — Program Synthesis

Date: 2026-06-28

A publication-strategy synthesis pulling the program together after the Webb–Miolane
("Geometry of Consciousness") talk. Grounded in the actual numbers across four clusters:
the weakness flagship, the metric-stack-of-concern / passive→active cluster, Phase 2A/2B,
and the strategy/handoff docs. Companion to [geometric_convergence_research_synthesis.md](geometric_convergence_research_synthesis.md)
and [webb_miolane_fit.md](webb_miolane_fit.md).

## 1. Where the program shines (ranked, honest)

1. **Weakness predicts OOD — the crown jewel.** `W_G(f) = |{g∈G : ∃h∈G, ∀x, f(g·x)=h·f(x)}|`
   selects the invariant rule in **100% of cyclic/dihedral trials vs 0% for every classical
   baseline** (train loss, val, MDL, compression, flatness); correlates with neural OOD at
   **r≈+0.81 replicated at 256 and 1024 models**; holds in vision (r=+0.67); and is **causal** —
   training with the *data-inferred* group as augmentation lifts OOD **+51.5pp, 90.7% of the
   oracle's effect**. Disciplined negatives (parity Z₂ too small; S_n wrong-involution)
   delineate the operating regime. Clean + causal + honest boundary.
2. **Passive→active geometry.** On real LLMs (Pythia-70M, GPT-2): action-coupling makes a
   paraphrase axis causally load-bearing (specific effect **+0.069→+0.486, 7×**), turns it
   into a **self-defending attractor** (wrong-direction fooling **85%→0%**), and it
   **autopoietically repairs** (0.45→0.965 in K=10 updates). Replicated 6/6 cells.
3. **The "X is not Y" anti-cheat methodology.** The Correction Chain (behavior≠representation,
   uncertainty≠error, current-error≠value-of-probing, total≠identifiable) and the Phase-2 gate
   framework (concern-gating is the *only* selector passing at 1.000/5 seeds; `uncertainty_only`
   fails purely by over-probing low-concern ambiguity 1.000 vs the 0.25 cap). A transferable way
   to do interventional representation science that refuses to fool itself.

**Honest valley.** The activation-geometry binary-relation steering saga is a **clean negative** —
apparent steering is Yes-bias/answer-polarity leakage (target gradients sit at cosine 0.962 to the
first control PC; Pythia-160M replication came back 0/2). The *strict verifier* that exposed the
leakage is the only salvageable contribution there. Do not dress it up.

The program shines at the **intersection of generalization + geometry + intervention on small,
clean systems, with discipline**; it is weakest reaching for behavioral steering at LM scale.

## 2. Most publication-worthy contribution already in hand

**Weakness as a reparameterization-invariant, data-inferable, *causal* predictor of OOD
generalization.** Nothing else is simultaneously this clean, novel, and defensible. Passive→active
is a strong #2. Phase-2 concern work is excellent *methodology* but its claims are bounded to a
synthetic world (framework paper, not a law paper).

## 3. The math intersection — the Fourier ↔ weakness ↔ torus triangle

**(a) Equivariance = Fourier-diagonal (cyclic case).** For G = Zₙ acting by translation, a map is
G-equivariant iff it is a circular convolution iff it is **diagonal in the DFT basis**
{χ_k(x)=e^{2πikx/n}}. Those characters are the **irreducible representations** of Zₙ — and they are
literally Miolane's "periodic basis vectors":

> grid cell of spatial period n/k ≡ Fourier mode χ_k ≡ irrep k of Zₙ.

**(b) Weakness = spectral concentration on the group's irreps.** A high-weakness function commutes
with the whole group, so in the Fourier basis its cross-layer coefficients become **rank-one and
phase-aligned in the group's rotational order** — exactly the theorem in the existing source
*Neural Networks Provably Learn Spectral Representations for Group Composition*. Miolane's optimality
argument ("truncate after the first two frequencies, still a good signal") **is**
weakness-under-a-fidelity-constraint. The "weak, broadly-compatible constraint that takes a simple
periodic form" from *Is Complexity an Illusion?* = a band-limited code.

**(c) The orbit of the representation is a torus.** Encode 2-D position with two cyclic factors
(Zₙ×Zₘ). The population vector r(x) = (cos θ₁, sin θ₁, cos θ₂, sin θ₂, …), θᵢ ∝ kᵢ·x, traces the
**orbit of the group representation = product of two circles = T²**. This answers Miolane's own
puzzle ("why a torus, not a plane?"): a periodic code is built from group characters, so it lives on
the **maximal torus of the representation**. Gardner et al. (Nature 2022) measured exactly this —
Betti numbers (b₀,b₁,b₂)=(1,2,1) — in mouse entorhinal cortex.

**Unification (one object, three names):**

| Phase 1 (this program) | Spectral source | Miolane / Gardner |
|---|---|---|
| **weakness** W_G (scalar) | **irrep selection** (mechanism) | **toroidal topology** (observable) |

> **Claim:** weakness is the scalar that controls whether a learned population code carries the
> correct *topological structure* of the task's symmetry group — and that topology is what makes it
> generalize. Generalization, spectral structure, and manifold topology are three measurements of
> one event: *the code discovered the group.*

**Two intersections that fall out for free:**
- **Platonic Representation Hypothesis** → weakness explains *when* convergence must happen: a task
  with a symmetry drives every capable learner to the high-weakness irrep code → same kernel → same
  topology. Weakness is a *mechanism* for the Platonic hypothesis in the symmetric-task regime.
- **Autopoietic theorem / weakness-maximization (Bennett)** → the passive→active self-defending
  attractor *is* boundary-maintenance; `autopoietic_control` already shows Ashby ultrastability.

## 4. The gap the talk exposes (the good kind)

`valence_tapestry` **tried** to show "reward role reshapes encoder geometry" and the RSA gate
**failed (0.31 vs 0.5)**. The program has "goal-coupling tightens/defends an axis"
(passive→active) and "viability self-organizes a reward axis" (concern_bootstrap, rg +1.00 with no
reward labels) — but **no clean "reward continuously deforms a metric/manifold" result.** The bandit
has no metric manifold to deform; the navigation torus does. Mechanism, in-house language:

> A globally translation-invariant (high-weakness) code *cannot* have extra resolution at one
> location — invariance forbids privileging a point. To buy local resolution you must **break the
> symmetry locally → spend weakness locally**. **Concern deforms representational geometry by
> locally spending symmetry (weakness) to buy resolution where viability matters.**

This unifies all three phases: Phase 1 (global weakness sets topology + generalization) → Phase 2
(concern locally deforms the metric) → with Miolane's torus as the substrate where both are
measurable, in brains and nets.

## 5. Best next experiment + the notoriety version

**Experiment — "Weakness predicts the topology of population codes."** Reimplement the public
grid-cell-from-RNN path-integration task (self-contained; no external repo needed — see prereg).
Across many initializations measure per network: (i) **weakness** W_G under the translation group,
(ii) **persistent homology / Betti numbers** of the population manifold, (iii) **OOD generalization**
(held-out arena geometry / path integration). Predicted law:
**high weakness ⟺ clean toroidal topology (b₁=2) ⟺ high OOD.** Check the spectral leg: high
weakness ⟺ low-rank, phase-aligned Fourier support.

**Notoriety version — add the brain and the reward.**
- *Brain replication* on the public Gardner et al. grid-cell data: if weakness tracks toroidal
  integrity in biological recordings, the program supplies Miolane's "why the torus" its **Newton**
  (the Kepler/Newton framing) — a cross-substrate law. (Data not reachable from this environment;
  framed as a prediction / deferred to a data-access environment.)
- *Reward deformation*: reproduce Miolane's torus deformation and show it equals **a local drop in
  weakness traded for local resolution** — closing the `valence_tapestry` gap on the substrate where
  it is measurable.

Risk allocation: **the network leg is robust and sufficient for a strong standalone paper.** The
brain-data replication is the high-variance, high-payoff bet.

**Theory hardener (parallel):** derive the analytic weakness↔PAC-Bayes link the flagship lists as
future work — an invariant (high-weakness) code has a smaller effective hypothesis volume → reduced
KL/complexity term in a PAC-Bayes bound. Turns "better empirical predictor" into "predictor with a
generalization-theoretic reason to work."

## 6. The aligned program

**Arc: "Weakness, Spectra, and the Topology of Generalization."**
- **Paper A** (~1 scale-up from submittable): *Weakness predicts OOD* — the flagship (data-inferred +
  causal) hardened with (i) the PAC-Bayes/Fourier formalization and (ii) the grid-cell-RNN result
  (weakness↔Betti↔OOD). Miolane/Gardner is the abstract's hook. Preregistration:
  [../papers/grid_cell_weakness/preregistration.md](../papers/grid_cell_weakness/preregistration.md).
- **Paper B**: *Active geometry: concern locally spends symmetry for resolution* — passive→active
  (have it) + reward-deforms-the-torus (new; fills the `valence_tapestry` gap).

Phase 2A/2B and the Correction Chain become the **methods backbone**, not the headline.

## 7. Guardrails

- Activation-steering stays a clean negative + verifier contribution; do not resurrect as positive.
- No "consciousness" claims (the papers already discipline this — keep it).
- Everything is single-author toy-scale; the **scale-up onto the navigation torus + the external
  Gardner anchor** is the specific thing that converts a tidy program into a noticed one.
- Carry the weakness caveat: pure weakness is unsafe without a validity gate (broad-excluder
  failure) — weakness is a selection pressure *after* verifiers.
