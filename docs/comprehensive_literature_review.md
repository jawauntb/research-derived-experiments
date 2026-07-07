# Comprehensive Literature Review of the Research-Derived Experiments Program

Date: 2026-07-07

## Reader map

This review synthesizes the papers, notes, preregistrations, paper reviews, source manifest, and ICML package references in this repository. It is written for a reader who does not yet know machine learning, philosophy of mind, neuroscience, or dynamical systems. The shortest version is this:

1. A finite agent cannot represent everything about the world. It must keep the distinctions that matter for staying viable and acting well.
2. The distinctions that matter become geometry: distances, directions, boundaries, basins, clusters, manifolds, symmetry groups, and control surfaces.
3. Passive geometry is not enough. The project repeatedly asks whether a representation changes behavior under intervention, survives distribution shift, reopens inquiry after surprise, and carries early information to later action.
4. Across the papers, the same invariant keeps reappearing: intelligence-like behavior depends on turning global constraints into local action signals without letting proxy shortcuts pass the test.

The program is best understood as a sequence of increasingly hard anti-proxy tests. Each paper asks whether a system has the right internal structure or only a behaviorally convenient imitation. The strongest contribution is not one model; it is a method: define the proxy that would fake the capability, then add a minimal architectural or experimental pressure that makes the intended structure load-bearing.

## Part 1: First principles

### Systems, state, and viability

A system is something whose condition can change over time. Its state is the information needed to describe where it is now, at the level we care about. A thermostat's state might be room temperature and target temperature. A cell's state might include metabolites, membrane potentials, and gene-expression levels. A neural-network agent's state might include observations, hidden activations, memory, and learned weights.

Viability means the system remains within conditions where it can keep functioning. For a biological organism, viability includes things like energy, temperature, hydration, tissue integrity, and social or ecological affordances. In this repository's minimal agents, viability is simplified into variables such as energy, food, medicine, shock, internal weights, or target values. That simplification is deliberate: the goal is not to simulate life in full, but to isolate the logic of concern, attribution, and action.

Concern is the project name for viability-relevant difference. A world event matters to an agent when it changes the agent's expected ability to remain viable or achieve its current commitments. In the code and papers, this often appears as Delta E, Delta V, reward deformation, stress, or a "concern" feature. In plain English: concern is "what this event means for keeping the system going."

### Representation and compression

No finite system can store the world exactly. It must compress. Compression is not just making things smaller; it is deciding which differences to preserve and which to ignore. A map of a subway system preserves station connectivity but ignores building height. A navigation grid preserves reachable paths but ignores the smell of each street. A learned embedding preserves some relations among observations but collapses others.

This is why geometry appears everywhere. Geometry is the language of preserved relations:

- near versus far,
- same versus different,
- reachable versus unreachable,
- stable versus unstable,
- inside versus outside a boundary,
- movement along one direction versus another,
- transformations that preserve structure.

When a model learns a representation, it is implicitly choosing a geometry. The central question is whether that geometry preserves the distinctions that matter for action under the conditions the agent will face.

### Feedback, action, and control

A passive predictor observes the world and predicts what comes next. A controller acts, observes the result, and changes future behavior. Feedback is the loop that connects action to consequence. Feedback is why agency is harder than prediction: the agent's own behavior changes the data it will later see.

Many failures in this corpus come from confusing passive prediction with controlled agency. A representation can look clean in a static embedding, but fail when the agent's policy changes the state distribution. A probe can predict one useful variable while being irrelevant to the choice that matters. A memory can exist in hidden state but fail to reach the final dispatch surface where an action is selected. These are not small implementation details; they are the substance of the research program.

### Self/world attribution

Self/world attribution asks whether a system can distinguish changes caused by its own action from changes caused by external forces. In neuroscience this is related to reafference, efference copy, comparator models, and sense of agency. In causal machine learning it relates to intervention, identifiability, and separating latent causes. In philosophy it touches the boundary between agent and environment.

The project repeatedly finds that passive factorization is underdetermined. If two internal heads can trade credit without changing observable behavior, then the model has a gauge symmetry: multiple internal explanations fit the same data. Active identifying interventions, such as null actions or probes, can break that symmetry by producing evidence that would differ depending on the true source of change.

### Relevance and meaning

Meaning in this program is not defined as a word's dictionary entry. It is a relation between a system's constraints and its possible actions. A feature is meaningful to an agent when it helps select, preserve, or revise viable action. This is why the external citations include pragmatism, ecological psychology, enactivism, active inference, cybernetics, and TAME. These traditions disagree in many ways, but they share one pressure: cognition is not detached description; it is organized coping, inquiry, and control.

## Part 2: External literatures that anchor the program

### Representation learning and probes

Representation learning studies how models transform raw inputs into useful internal variables. The project draws on work about disentanglement, probing, concept vectors, persona vectors, and activation editing. The key caution from Locatello et al. is that unsupervised disentanglement is not identifiable without assumptions or inductive bias. Hewitt and Liang's probe-control warning also matters: a probe can extract information from a representation without proving that the model uses that information.

The repository's answer is intervention. Do not only ask whether a direction or probe exists. Ask whether changing it changes behavior in the predicted way, whether controls fail, and whether it still works under held-out shifts.

### Causal representation learning

Causal representation learning asks how latent variables can be recovered when observations are generated by underlying causes. Pearl-style causal inference formalizes interventions; Schölkopf et al. argue that causal structure is central to robust representation; Brehmer et al. show that weak intervention labels can make otherwise ambiguous latent structure identifiable. The project imports this logic but applies it to small agent loops: null actions, probe actions, mediated effects, world shocks, and action-correlated perturbations.

The core lesson is that causality is not a decoration on top of embeddings. If the agent must act under shift, the learned variables need to line up with intervention-relevant causes.

### Active learning, uncertainty, and inquiry

Active learning asks when a system should query more information. Bayesian active learning, BALD, deep ensembles, dropout uncertainty, epistemic neural networks, novelty bonuses, and random network distillation all offer ways to value information. The repository's results are unusually skeptical and useful here. Ensemble variance often fails to signal the dangerous boundary. Current residuals can be anti-calibrated unless recomputed against the present model. Probe value can be real while still producing anxiety or over-probing.

The project therefore moves from "uncertainty as a number" to "inquiry as a controlled action with cost, refractory dynamics, re-engagement, and calibration."

### Reinforcement learning, world models, and agent benchmarks

RL provides the setting: an agent observes, acts, receives reward, and learns a policy. World models and model-based planning let an agent predict the consequences of candidate actions. Agent benchmarks such as ReAct, Reflexion, Voyager, Toolformer, AgentBench, WebArena, OSWorld, GAIA, SWE-bench, BIG-bench, and HELM show how language-model agents can plan, use tools, and be evaluated.

The repository's benchmark contribution is proxy resistance. A benchmark is weak if a model can pass through superficial behavior. A stronger benchmark requires the relevant causal structure to be present at the action surface. The "causally grounded finite agents" line turns this into four empirical laws: predictive policy closure, reafferent identifiability, re-engagement floor, and commitment-surface memory.

### Domain generalization, invariance, and symmetry

Underspecification means many models can fit the training data while failing differently under deployment shift. Invariant risk minimization, DomainBed, GroupDRO, WILDS, shortcut learning, and group-equivariant networks all address this in different ways. The structure-compatible generalization papers ask a precise question: when in-distribution evidence is ambiguous, can we select or train for functions that preserve the transformations expected to generate the deployment cases?

The learned-symmetry work connects to group theory and representation theory. A model that respects a rotation, reflection, or other transformation has fewer arbitrary degrees of freedom. Weakness here means a smaller compatible hypothesis volume, not necessarily a simpler-looking rule.

### Neuroscience and cognitive science

Several neuroscience ideas recur:

- Reafference and comparator models: distinguish self-caused sensory change from external change.
- Predictive processing and active inference: perception and action are organized around reducing uncertainty or expected free energy under prior preferences.
- Allostasis and homeostasis: organisms regulate internal variables by anticipating and correcting future deviations, not merely reacting to current error.
- Habituation and refractory periods: repeated signals should not always trigger the same costly response, but the system must still reopen when the world changes.
- Geometry of cognition: spatial navigation, head direction, conceptual spaces, and neural manifolds often reveal rings, tori, attractor basins, and low-dimensional structure.

The repository does not claim to solve consciousness. It operationalizes narrower components: viability variables, self/world attribution, inquiry, re-engagement, and memory at action.

### Philosophy of mind, biology, and meaning

The project draws from Dewey's inquiry, Gibson's affordances, Uexkull's Umwelt, Heidegger's readiness-to-hand, Canguilhem's normativity of life, Jonas's organismic meaning, Maturana and Varela's autopoiesis, Di Paolo's adaptivity, Thompson's enactive cognition, Levin's TAME, Vervaeke's relevance realization, and Bennett's critique of meaning in language models. The shared idea is that meaning is not just representation; it is relevance for situated action.

The research program translates that philosophical claim into finite tests. Does the model's internal signal preserve viability-relevant differences? Does it control action? Does it reopen inquiry under surprise? Does it remain honest when shortcut proxies are available?

## Part 3: Internal research arcs

### Arc A: Concern, valence, and metric deformation

The earliest concern and valence papers ask whether a viability-relevant objective reshapes representation. Valence object formation shows encoders clustering objects by causal role rather than sensory similarity. Homeostatic objects and passive-to-active geometry then ask whether that structure transfers to control. Concern bootstrap and two-bottlenecks reveal an important split: Delta E auxiliary losses can build useful valence geometry, but sparse-reward policies may fail to exploit it.

The latent finding is that representation and competence are separable. A model can have the right-looking geometry without the control pathway needed to use it. This becomes one of the program's recurring invariants: geometry must be made load-bearing.

### Arc B: State-dependent concern and boundary failure

State-dependent concern, off-policy state coverage, regime-sensitive Delta E, allostatic control, and ensemble uncertainty focus on a diagnostic boundary: the same object or action can be good or bad depending on internal state. The sharp failure occurs near a boundary, often E = 0.5 in the simplified tasks. Learned models can smooth through a discontinuity, ensembles can be overconfident, and trajectory concentration can hide the rare state where the rule changes.

The lesson is not merely "add more data." The right feature, boundary representation, or state-sensitive architecture matters. The project also learns a caution: uncertainty estimates that look principled can be flat exactly where the agent most needs them.

### Arc C: First-order self and identifying interventions

First-order self shows that architectural factorization alone does not recover self/world attribution. Null intervention then demonstrates that active anchoring can reduce false credit by creating evidence that distinguishes self-caused from world-caused change. Costly null probes, online identifying interventions, current-error calibration, vector first-order self, and scale-normalized V-probe extend the result under cost, online data regimes, vector-valued viability, calibration, and dimensional scaling.

The central invariant is the reafferent gauge-breaking principle: when multiple internal explanations are observationally equivalent, the agent needs an intervention that changes one explanation differently from the other. In ordinary language: if looking cannot tell whether "I did it" or "the world did it," the agent must do something diagnostic.

### Arc D: Responsive worlds and re-engagement

World Responds makes the environment action-correlated: shocks or changes can be linked to the agent's behavior. Probe-value re-engagement then asks when an agent should ask again. Habituated re-engagement and Suite C introduce bounded burst-and-refractory dynamics: probe when surprise warrants it, cool down after probing, and preserve the ability to reopen inquiry after a second shift.

This arc turns active learning into a control problem. A good inquiry policy is not maximal curiosity. It is calibrated, costly, stateful, and re-openable.

### Arc E: Planning from concern

Planning from concern and planning hardening show that Delta E style models can support action selection when coupled to model-based planning. The important distinction is between a reward label and a predictive model that can be queried for candidate actions. Planning from concern makes viability prediction part of the policy loop; planning hardening tests whether success depends on one fragile axis or distributed concern geometry.

The program-level finding is predictive policy closure: a concern model matters when the policy actually closes the loop through it.

### Arc F: Commitment-surface memory and long horizons

The long-horizon bottleneck papers ask whether information from early in an episode reaches the later action that requires it. The project tests prompt JSON surfaces, generated JSON surfaces, hidden localization, causal patching, transfer, API black-box behavior, and dispatch-surface robustness. The repeated lesson is that memory is not proved by recoverability somewhere in the trace. It must influence the final choice under the right aliases, parser formats, repairs, and action constraints.

This is one of the most general results in the repository. It applies to small agents, LLM tool agents, and human organizations: a commitment is real only if it reaches the surface where behavior is selected.

### Arc G: Structure-compatible generalization and learned symmetry

Weakness invariance, learned symmetry discovery, neural group generator, and the structure-compatible generalization suite ask how to choose models that will generalize out of distribution. The key move is to evaluate compatibility with transformations, not just in-distribution error. Later phases weaken the oracle by inferring transformations, using language template substitution, learned generators, semantic retrieval, and semantic selection controls.

The latent finding is that OOD generalization is often a model-selection problem before it is a training-loss problem. When data do not decide, the deployment transformation should decide.

### Arc H: Concerned syntax, viable computational bodies, and typed ontology gates

Concerned syntax and viable computational bodies ask whether structured, syntax-bearing computational bodies can be searched, gated, and validated. The Haskell ontology gate formalizes part of this with typed constraints. This arc connects neuro-symbolic reasoning, program synthesis, architecture search, and philosophy of ontology.

The important result is not that symbolic structure replaces neural learning. It is that type-like constraints can prevent nonsense combinations and make hidden commitments explicit. This is the same proxy-resistance logic at a higher abstraction level.

### Arc I: Virtual governors, autopoiesis, and external validity

Autopoietic control, virtual-governor stress signals, phase 4 metaphysics, phase 5 external validity, and phase 6 real-model validation try to export the earlier finite-agent logic to broader settings. The virtual-governor paper gives a useful vocabulary: a global constraint violation must become a local action signal. Autopoietic control adds the idea that a system must maintain the conditions of its own operation. The phase papers are honest about missing conditions and external-validity limits.

The important boundary is that these works motivate mechanistic hypotheses; they do not establish broad consciousness or alignment claims.

### Arc J: Coherence testbench and empirical humility

The coherence-testbench documents show a different but related research discipline. Phase 0 EEG validation hit a kill criterion; later eyetrack and quiz-score branches explored whether the signal exists in another modality. The post-mortem and next-steps documents are part of the literature because they model a scientific invariant: do not rescue a thesis by silently moving the goalpost. Record what failed, what it did not test, and which next branch would actually discriminate hypotheses.

## Part 4: Mathematical theorems, proof ideas, and relevant fields

This section separates established mathematical results from candidate program laws. The repository often uses "law" for empirical regularities. Those are not theorems unless assumptions and proof obligations are made explicit.

### No Free Lunch and underspecification

Field: learning theory, statistics, philosophy of induction.

Basic idea: without assumptions about the data-generating process, no learner is universally better than another. Modern underspecification says many models can fit the same training evidence while encoding different rules. Proof intuition: if every possible labeling or deployment world is allowed, success on one subset can be paired with failure on another. Generalization requires bias.

Program implication: the question is not whether to have inductive bias, but which bias preserves the deployment-relevant structure.

### Impossibility of unsupervised disentanglement

Field: representation learning, identifiability, causal inference.

Basic idea: Locatello et al. show that unsupervised disentanglement is not identifiable without assumptions. Proof intuition: a latent code can be transformed by an invertible map that preserves observations while changing the apparent factors. Observations alone cannot choose the "right" factors.

Program implication: self/world attribution and concern factors need interventions, architecture, supervision, or constraints.

### Causal intervention and do-calculus

Field: causal inference, graphical models.

Basic idea: interventions replace the normal mechanism for a variable, letting us ask what would happen if we set it directly. Pearl's do-calculus gives rules for when causal effects are identifiable from observed and interventional distributions. Proof intuition: graphical separation tells which paths remain open after intervention.

Program implication: null actions and probe actions are miniature interventions that make attribution testable.

### Invariant prediction and invariant risk minimization

Field: statistics, domain generalization, causal learning.

Basic idea: causal predictors tend to remain stable across environments, while shortcuts often change. Invariant prediction formalizes variable selection by requiring stable conditional relations. IRM tries to learn representations where the same classifier is optimal across environments. Proof intuition: true causes keep producing the target under changes that break noncausal correlations.

Program implication: structure-compatible model selection is an intervention- and transformation-aware version of this principle.

### Group equivariance and representation theory

Field: algebra, geometry, harmonic analysis, deep learning.

Basic idea: a function is equivariant when transforming the input transforms the output in a predictable matching way. Group-equivariant networks bake this constraint into architecture. Representation theory studies how abstract symmetries act as linear transformations. Proof intuition: if a network layer commutes with group actions, the whole composed network can preserve symmetry.

Program implication: learned weakness is not just simplicity; it is a smaller hypothesis space compatible with the transformation group.

### Spectral representations for group composition

Field: representation theory, Fourier analysis on groups, neural-network theory.

Basic idea: recent theory on group-composition learning shows neural networks can learn spectral or irreducible-representation structure when trained on group composition tables. Proof intuition: Fourier decomposition turns group convolution-like structure into blocks; gradient dynamics select low-rank aligned coefficients inside those blocks.

Program implication: the learned-symmetry papers have a theory-side anchor for why group pressure can produce discoverable internal geometry.

### Rate-distortion theory

Field: information theory, statistics, optimization.

Basic idea: rate-distortion asks how many bits are needed to represent a source while keeping expected distortion below a threshold. Proof intuition: an optimal encoder trades compression cost against distortion cost, yielding a variational solution that looks like a Gibbs distribution over code assignments.

Program implication: the reward-deformation notes propose a local rate-distortion law: when concern changes the distortion measure, it warps the learned metric and effective dimension.

### Ashby's law of requisite variety

Field: cybernetics, control theory.

Basic idea: a controller must have enough internal variety to counter the variety of disturbances it faces. Proof intuition: if disturbances produce more distinguishable harmful states than the controller can distinguish or act on, some states must receive the same response and at least one will fail.

Program implication: scalar valence is sometimes too little variety; vector concern, role-specific heads, or typed structure may be required.

### Free energy principle and active inference

Field: theoretical neuroscience, variational inference, control.

Basic idea: adaptive systems can be described as minimizing variational free energy or expected free energy, balancing prediction, preference, and epistemic value. Proof intuition: variational bounds turn intractable model evidence into an optimizable objective; action can be selected to make preferred and informative observations more likely.

Program implication: probe value, re-engagement, and concern-guided planning can be read as finite operational fragments of active inference, without inheriting its whole metaphysical apparatus.

### Empowerment

Field: information theory, reinforcement learning, embodied cognition.

Basic idea: empowerment measures how much influence an agent's actions can have on future states, often as channel capacity from actions to outcomes. Proof intuition: maximize mutual information between action choices and resulting states under the environment dynamics.

Program implication: viable agents need not only reward but controllability; however, control must be aligned to concern rather than raw option count.

### Goodhart's law

Field: economics, statistics, AI safety.

Basic idea: when a measure becomes a target, it can stop being a good measure. Proof intuition: optimizing a proxy selects cases where proxy and true target diverge.

Program implication: every benchmark in the repo asks what proxy could pass, then designs a gate to prevent that proxy from counting as success.

### Candidate program law: reafferent gauge-breaking

Field: causal inference, gauge symmetry analogy, agency.

Statement: if self-caused and world-caused explanations are observationally equivalent under passive data, an identifying intervention is required to break attribution symmetry.

Proof intuition: passive trajectories leave two parameterizations with the same likelihood. A null or probe action changes the expected observation under one parameterization but not the other, making the explanations distinguishable.

Status: empirically supported in the first-order self and null-intervention arc; formalizable as an identifiability lemma.

### Candidate program law: current replay calibration

Field: online learning, calibration, active learning.

Statement: an uncertainty or probe-value signal based on stale residuals can be anti-calibrated; recomputing residuals against the current model can restore positive calibration.

Proof intuition: when the model changes, old errors are not errors of the current hypothesis. A compact replay buffer updates the calibration target to match the current decision surface.

Status: empirical law in the current-error calibration line; needs formal assumptions for theorem status.

### Candidate program law: re-engagement floor

Field: control theory, change detection, active learning.

Statement: a converged agent in a responsive world needs a mechanism that can reopen inquiry after surprise, otherwise apparent calm can become self-confirming silence.

Proof intuition: if inquiry probability decays to zero and no surprise pathway raises it, post-shift evidence is never sampled; the agent cannot learn that the world changed.

Status: empirical law in World Responds and Suite C.

### Candidate program law: commitment-surface memory

Field: dynamical systems, program semantics, agent benchmarks.

Statement: memory counts for agency only when early information causally reaches the later surface where action is selected.

Proof intuition: hidden-state recoverability is insufficient. Patch, ablate, or counterfactually change the early information and measure whether the final dispatch changes under controls.

Status: empirical and methodological law in the long-horizon bottleneck work.

### Candidate program law: structure-compatible selection

Field: domain generalization, group theory, causal representation learning.

Statement: when in-distribution data underdetermines the rule, prefer models compatible with deployment-generating transformations.

Proof intuition: compatibility reduces the viable hypothesis volume to functions that commute with or preserve the expected shift structure, excluding shortcuts with equal ID score.

Status: empirical law in the weakness and structure-compatible generalization work; formally related to invariance and equivariance.

## Part 5: Cross-field invariants

Across ML, neuroscience, philosophy, and biology, the same patterns recur:

1. Finite capacity forces compression.
2. Compression produces geometry.
3. Geometry becomes meaningful when it preserves action-relevant distinctions.
4. Passive representation is weaker than closed-loop control.
5. Identifiability usually requires intervention or constraint.
6. Uncertainty is useful only if calibrated to the current decision surface.
7. Relevance is state-dependent.
8. Memory matters at the action surface, not merely in storage.
9. Generalization improves when the hypothesis space respects real transformations.
10. Good benchmarks are anti-proxy instruments.

These invariants are the bridge between fields. In neuroscience, they appear as reafference, attractor basins, habituation, and allostatic regulation. In philosophy, they appear as affordances, relevance, normativity, and situated coping. In ML, they appear as representations, interventions, calibration, invariance, and OOD generalization. In biology, they appear as autopoiesis, adaptivity, and function shaping structure.

## Part 6: Latent findings and research implications

The latent finding is that "agency" decomposes into several load-bearing surfaces:

- a viability or concern surface that defines what matters,
- a representation surface that preserves useful distinctions,
- an attribution surface that separates self, world, and mediated effects,
- an inquiry surface that decides when to gather information,
- a planning surface that closes prediction into action,
- a memory surface that carries commitments forward,
- a compatibility surface that excludes shortcut hypotheses,
- a governance surface that converts global constraint violation into local action pressure.

Each surface can fail independently. That is why one impressive metric rarely proves the whole capability. A system can represent concern but not use it; probe accurately but not act better; remember but not dispatch; generalize ID but fail OOD; signal stress but use a stale proxy.

The implication for AI evaluation is direct: benchmark suites should be organized around causal surfaces, not only task scores. The implication for interpretability is also direct: a discovered vector or feature is not enough until it is tied to interventions and behavior. The implication for philosophy is more cautious but interesting: many traditional concepts of meaning, self, inquiry, and agency can be made experimentally tractable by asking which finite surfaces carry which constraints.

## Part 7: Future directions

The next natural work falls into several branches:

1. Formalize the candidate laws. Turn reafferent gauge-breaking, re-engagement floors, commitment-surface memory, and structure-compatible selection into theorem statements with assumptions, proof sketches, and counterexamples.
2. Scale from finite grids to richer agents. Apply the same anti-proxy gates to tool-using LLM agents, robotics, browser agents, and multi-agent systems.
3. Replace hand-coded interventions with learned intervention discovery. Let agents discover which actions best identify self/world structure or deployment transformations.
4. Deepen the geometry. Measure curvature, effective dimension, spectral structure, basins, and topology, not only linear probes.
5. Build causal provenance for agent-generated science. Every experiment should include source, command, seed, gates, raw/summary split, and failure conditions.
6. Test cross-substrate transfer. Compare finite agents, neural nets, LLM activations, biological data, and human cognitive tasks under the same geometric and intervention metrics.
7. Separate consciousness claims from agency claims. The current evidence supports mechanistic claims about control, attribution, inquiry, and generalization. Subjective experience remains outside the demonstrated scope.

## Part 8: What the whole program points toward

The repository points toward a substrate-independent science of maintained concern: how finite systems compress the world, preserve viability-relevant distinctions, act to test their own uncertainty, and keep commitments alive across time and shift.

The strongest form of the thesis is not "geometry proves mind" or "LLMs are agents." The stronger, safer, and more useful thesis is:

> Across substrates, finite adaptive systems become intelligible when we identify the constraints they must maintain, the geometry by which they compress possible worlds, and the interventions that make those representations matter for action.

That thesis is broad enough to connect ML, neuroscience, philosophy, and biology, but narrow enough to test. The work already shows a disciplined pattern: make a claim, name the proxy, preregister gates, accept negative results, and move the structure closer to the action surface. That is the durable research implication.

## Appendix: source coverage and references

The generated PDF includes dynamic appendices listing the repository papers and extracted raw reference lines used for this review. The extraction sources are `papers/`, `docs/`, `notes/`, and `references/`, with BibTeX entries from the ICML packages included.
