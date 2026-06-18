# Michael Levin — Three Most Recent Papers (brief for Track 3)

Compiled 2026-06-18 for the "minimal computational precursors of concern-like agency" lab.
Track 3 = a minimal embodied agent with a *plastic self/environment boundary prior*.

## Provenance & confidence note

- WebFetch was HTTP-403 blocked for arXiv, bioRxiv, Royal Society, OSF, drmichaellevin.org,
  and the Levin-lab blog throughout this session. **All details below come from WebSearch result
  summaries plus the official preprint/publication index, not from reading the full PDFs.**
  Treat abstracts/claims as *confirmed-from-metadata*; treat my Track-3 inferences as clearly
  labeled inference.
- "Recent + genuinely Michael Levin (Tufts / Allen Discovery Center / Wyss)" was verified for all
  three. Candidates I *rejected* for being older or peripheral: "Open Questions about Time and
  Self-reference in Living Systems" (arXiv 2508.11423, Aug 2025; Levin is 1 of 8 authors);
  "Topological constraints on self-organisation" (arXiv 2501.13188, Jan 2025); "Diffusion Models
  are Evolutionary Algorithms" (arXiv 2410.02543, an Oct-2024 paper with a 2026 re-post date).
- One caveat on **Paper 1 (Cognitive Glues)**: the *journal* version is May 2026, but the
  underlying preprint dates to Nov 2024 (Levin's own announcement tweet). So its *content* is
  ~18 months old even though the citable publication date is recent. Papers 2 and 3 are genuinely
  new 2026 work.

---

## Paper 1 — Cognitive glues are shared models of relative scarcities: the economics of collective intelligence

**Citation.** Levin, M. & Lyons, B. (2026). *Cognitive glues are shared models of relative
scarcities: the economics of collective intelligence.* Philosophical Transactions of the Royal
Society A, 384(2320), 20240528. Published 2026-05-14. DOI: 10.1098/rsta.2024.0528. (Preprint:
OSF 3fdya, Nov 2024.)

**Core claim.** Collective intelligence has problem-solving capacities distinct from those of its
subunits; the open question is what *interaction policy* lets a collective cohere. The paper argues
the price system is the economy's "cognitive glue": a *shared model of relative scarcities* that
acts as a coordinating affordance, letting autonomous multi-scale agents form mutually compatible
plans without any agent seeing the whole.

**Relevance to Track 3.**
- (a) *Boundary as plastic/prior:* The "glue" is what binds subunits into a larger problem-solver —
  i.e., where the larger self's boundary gets drawn is set by which agents share the scarcity signal.
  Inference: the self/world boundary is co-extensive with the reach of the shared coordinating
  signal, not a fixed anatomical fact.
- (b) *Multiscale / collective intelligence:* Direct. Economy framed as an explicit example of a
  scale-free collective intelligence with emergent goals.
- (c) *Operationalization:* A scalar "relative scarcity / price" broadcast to a set of cells is a
  concrete, cheap mechanism for boundary reassignment in a gridworld — agents reading the same
  price signal behave as one larger self; agents on a different signal split off.
- (d) *Falsifiable prediction (inferred):* Sub-agents sharing a common scarcity/price signal will
  show collective problem-solving (reach goals no individual reaches) that *disappears* when the
  shared signal is severed or made agent-local.

**Track-3 experiment suggestion.** Build a bandit/gridworld with N cell-agents each homeostatically
defending a resource budget. Add a single shared "price" channel = a function of aggregate scarcity.
Measure whether the collective solves a delayed/distributed-reward task only when the channel is
shared; ablate or fragment the channel to watch the larger "self" dissolve into smaller selves.

---

## Paper 2 — Homeostatic feedback model of energy metabolism with adaptive enzyme levels exhibits problem-solving behavior

**Citation.** de Baat, A. & Levin, M. (2026). *Homeostatic feedback model of energy metabolism with
adaptive enzyme levels exhibits problem-solving behavior.* bioRxiv, posted 2026-05-07 (indexed
~05-11). DOI: 10.64898/2026.05.07.721661. Levin affiliation: Dept. of Biology, Tufts University.

**Core claim.** A coarse-grained ODE model of mammalian energy metabolism (glucose, glutamine,
fatty-acid, OxPhos pathways; Michaelis–Menten fluxes, product-inhibition feedback, adaptive
enzyme-capacity regulation, explicit ATP cost for enzyme adjustment) is shown to display
learning-like, experience-dependent adaptation. The same homeostatic feedback architecture that
maintains robustness *also* yields "problem-solving": prior perturbation improves future response.

**Relevance to Track 3.**
- (a) *Boundary as plastic/prior:* Less direct, but the model is a clean instance of "homeostasis ->
  cognition" with no neurons — the substrate for a minimal homeostatic agent whose "self" is just
  the set of variables it defends.
- (b) *Multiscale:* Fits Levin's "stress-reduction -> information-seeking -> memory/prediction"
  ladder; this paper is the bottom rung made mechanistic.
- (c) *Operationalization:* This IS a tiny toy agent. Adaptive enzyme capacity with an explicit
  adjustment cost = a measurable plasticity/cost trade-off you can port to a gridworld energy budget.
- (d) *Falsifiable prediction (confirmed framing):* A purely homeostatic feedback system with
  *adaptive set-points* will exhibit memory/anticipation (better second-exposure response, i.e.
  hysteresis/priming) — testable directly in a minimal model and absent in a fixed-set-point control.

**Track-3 experiment suggestion.** Use this as Track 3's *agent core*: a homeostatic agent defending
internal variables with an adjustment cost. Then make the *boundary* itself one of the adjustable
variables — let the agent reassign which environmental variables count as "internal." Test whether
the same adaptive-set-point machinery that produces metabolic memory can also "learn" a self/world
boundary, and whether the priming/hysteresis signature transfers to boundary reassignment.

---

## Paper 3 — Remapping and navigation of an embedding space via error minimization: a fundamental organizational principle of cognition in natural and artificial systems

**Citation.** Hartl, B., Pio-Lopez, L., Fields, C. & Levin, M. (2026). *Remapping and navigation of
an embedding space via error minimization: a fundamental organizational principle of cognition in
natural and artificial systems.* arXiv:2601.14096. Submitted 2026-01-20; v2 2026-02-03. Allen
Discovery Center, Tufts (Levin also Wyss Institute, Harvard). Levin = corresponding author.

**Core claim.** Cognition in natural and artificial systems reduces to two substrate-independent
invariants: (i) *remapping* sensory/state information into an embedding ("problem/latent") space,
and (ii) *navigation* within that space toward goals via iterative error minimization. The same dual
principle spans single cells regenerating tissue, morphogenesis, transformers, diffusion models, and
neural cellular automata (NCA).

**Relevance to Track 3.** (Most directly useful of the three.)
- (a) *Boundary as plastic/prior:* The *remapping* step IS where the agent decides what its problem
  space — and implicitly its self — is. A plastic self/world boundary becomes a *re-parameterization
  of the embedding*, making boundary attribution a manipulable design variable, exactly the
  "boundary is a prior, not a fact" thesis.
- (b) *Multiscale / cognitive light cone:* Framed as substrate-independent across scales; competency
  = size/reach of the region of problem-space a system can navigate (operational cognitive light cone).
- (c) *Operationalization (confirmed wording):* "A goal is a target position in a problem space, and
  a system's competency is its ability to navigate that space toward the goal by actively minimizing
  deviation." This is a ready-made, measurable definition for a bandit/gridworld: define a metric
  embedding, place a goal, measure error-minimizing trajectory length / success as competency.
- (d) *Falsifiable prediction (confirmed framing):* Remapping + error-minimizing navigation is a
  *universal invariant* — any genuinely cognitive system (incl. a toy one) must exhibit both; a
  system that minimizes error without remapping (or vice versa) should fail at out-of-distribution
  goals. Testable: ablate the remapping capacity in a toy agent and predict loss of generalization.

**Track-3 experiment suggestion.** Make the self/world boundary an explicit coordinate in the agent's
embedding. The agent navigates a goal-space by error minimization (this paper's mechanism), but one
navigable axis is "how much of the environment is reassigned as self." Measure whether agents that
can *re-map their boundary* solve constraint-geometry tasks (e.g., reaching goals only achievable by
temporarily enlarging the self to include a tool/region) that fixed-boundary agents cannot — directly
testing the "boundary is removable/visible" thesis and the weakness-vs-simplicity generalization axis.

---

## Cross-cutting takeaways for Track 3

1. **Agent core (Paper 2) + navigation mechanism (Paper 3) + binding signal (Paper 1)** compose into
   one design: a homeostatic agent whose embedding includes a *boundary coordinate*, coordinated to
   peers by a shared scarcity signal.
2. The cleanest *measurable* boundary-as-prior operationalization comes from Paper 3: treat the
   self/world boundary as a navigable embedding axis, not a fixed label.
3. The cleanest *falsifiable* homeostasis->cognition signature (memory/priming from adaptive
   set-points) comes from Paper 2 and is the easiest to reproduce in a minimal model first.

## Source links
- Cognitive glues: https://doi.org/10.1098/rsta.2024.0528 ; preprint https://osf.io/preprints/osf/3fdya
- Homeostatic metabolism: https://www.biorxiv.org/content/10.64898/2026.05.07.721661v1
- Remapping/navigation: https://arxiv.org/abs/2601.14096
- Levin preprint index: https://drmichaellevin.org/publications/preprints.html (403 on fetch; via search)
