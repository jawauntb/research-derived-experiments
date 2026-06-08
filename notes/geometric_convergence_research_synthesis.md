# Geometric Convergence Research Synthesis

Date: June 8, 2026

Working thesis: several independent literatures keep rediscovering geometric language because finite adaptive systems must compress, compare, and control high-dimensional possibility spaces. Geometry is the portable language of constraints: distances, neighborhoods, attractors, boundaries, basins, directions, manifolds, kernels, and regime transitions.

## Source Set

Local archive:

- `references/papers/arxiv_2507_21509_persona_vectors.pdf`
- `references/papers/arxiv_2501_02009.pdf`
- `references/papers/local_autopoietic_theorem.pdf` (same DOI as the Authorea link; Authorea blocked direct download with 403)
- `references/html/wolfram_2026_games_between_programs.html`
- `references/papers/arxiv_2606_01444_self_revising_discovery_systems.pdf`
- `references/papers/arxiv_2405_07987_platonic_representation_hypothesis.pdf`
- `references/papers/arxiv_2606_06624_deep_representation_learning_memory.pdf`
- `references/papers/openreview_Yxz92UuPLQ.pdf`
- `references/papers/arxiv_2605_31514_age_of_empires_attributes.pdf`
- `references/papers/arxiv_2404_07227_complexity_illusion.pdf`
- `references/papers/cimc_hypothesis.pdf`
- `references/papers/frontiers_2022_768201_tame.pdf`
- `references/papers/frontiers_2016_00902_no_head.pdf`
- `references/papers/local_there_is_no_self_evidence.pdf`
- `references/papers/local_thesis_revision_1_9.pdf`

Original links:

- https://arxiv.org/pdf/2507.21509
- https://arxiv.org/pdf/2501.02009
- https://www.authorea.com/doi/full/10.22541/au.177575355.56499869/v1
- https://writings.stephenwolfram.com/2026/06/games-between-programs-the-ruliology-of-competition/
- https://arxiv.org/pdf/2606.01444
- https://arxiv.org/pdf/2405.07987
- https://arxiv.org/abs/2606.06624
- https://openreview.net/pdf?id=Yxz92UuPLQ
- https://t.co/DP8OR5NJf2, resolved to https://arxiv.org/abs/2605.31514
- https://arxiv.org/abs/2605.31514
- https://arxiv.org/abs/2404.07227
- https://cimc.ai/cimcHypothesis.pdf
- https://www.frontiersin.org/journals/systems-neuroscience/articles/10.3389/fnsys.2022.768201/full
- https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2016.00902/full

Note: `arxiv.org/abs/2606.01444` appeared twice in the prompt and is summarized once.

## Biggest Research-Worthy Question

**Why do independently developed systems of thought and computation keep converging on geometric descriptions of meaning, agency, and intelligence, and can we predict when that geometry is merely a passive representation versus when it becomes an active, self-maintaining attractor regime?**

More operationally:

**Can we build and test a substrate-independent theory of representational geometry under constraint, in which mathematical attractors, cognitive attractor networks, linguistic conceptual spaces, biological goal spaces, and AI activation manifolds are all special cases of finite systems compressing possible futures into controllable low-dimensional structure?**

The important move is not to claim these systems are "the same." The sharper question is why the same form of explanation keeps winning. The corpus suggests a convergence of pressures:

- Finite information capacity forces compression.
- Task and survival constraints select representations that preserve actionable distinctions.
- Generalization prefers weak, broadly compatible constraints rather than arbitrary simple forms.
- Closed-loop systems turn passive embeddings into attractor dynamics.
- Multiscale organization makes boundaries, selves, and concepts provisional but useful.
- Scaling and multimodal data push learned representations toward shared kernels or latent statistical structure.
- Scientific discovery requires not only moving inside a space but changing the typed space itself.

So the research program is: identify the invariants that make geometry appear, measure them across substrates, and determine the threshold where representation becomes agency.

## Cross-Paper Synthesis

The strongest shared idea is "geometry as constraint." In mathematics and dynamical systems, attractors describe regions toward which trajectories settle. In cognitive science, attractor networks describe stable states of perception, memory, and concepts. In linguistics and philosophy of concepts, conceptual spaces describe meanings by neighborhoods, dimensions, prototypes, and distances. In AI, activation geometry describes concepts, traits, modalities, and behaviors as directions, subspaces, kernels, and manifolds.

The reason these languages rhyme may be that all of them solve the same problem: how to preserve the right distinctions while throwing almost everything away. A system with finite capacity cannot keep all possible world states separate. It has to fold the world into a lower-dimensional organization that keeps useful futures open. That makes geometry natural because geometry is exactly the language of preserved relations: near/far, same/different, reachable/unreachable, stable/unstable, separable/entangled, controllable/uncontrollable.

The corpus also warns against an over-easy unification. "Persona vectors" and "concept vectors" show that linear directions can control high-level LLM behavior, but the Age of Empires paper warns that anthropomorphic interpretation is non-unique unless measurement criteria are explicit. The Platonic Representation Hypothesis argues for convergence toward a shared statistical model of reality, but its own limitations acknowledge that non-bijective or information-poor modalities cannot fully converge. TAME and "No Head" argue that cognition extends through non-neural biological systems, but they intentionally broaden cognition in a pragmatic, engineering sense. The consciousness papers ask whether active self-organizing coherence is enough for sentience, but the operational tests remain immature.

The likely productive stance is therefore neither reductionist nor mystical. Geometry is not proof of mind. But recurring geometry is evidence of a shared constraint problem.

## Paper Notes

### 1. Persona Vectors: Monitoring and Controlling Character Traits in Language Models

Core idea: high-level model traits can be represented as directions in activation space. The paper automates extraction of "persona vectors" from natural-language trait descriptions by generating contrastive prompts, trait-relevant questions, and a scoring rubric, then taking activation differences between target-trait and opposite-trait generations. The resulting directions are used to monitor, steer, mitigate, and pre-screen persona shifts.

Biggest claims:

- Traits such as evil, sycophancy, and hallucination propensity can be captured as usable activation-space directions.
- Projection onto these directions can monitor deployment-time and fine-tuning-induced persona shifts.
- Post-hoc steering can suppress undesirable shifts, and preventative steering during fine-tuning can reduce drift before it appears.
- Training data can be screened at dataset and sample level by projection onto persona vectors.

Nuances:

- The paper is not only about "interpretability"; it treats geometry as an operational control surface.
- The automated pipeline matters because it converts natural language trait descriptions into model-internal axes.
- The strongest connection to this research theme is that apparently qualitative social traits become measurable vector geometry.

Issues and gaps:

- The method leans heavily on LLM judges and generated contrastive artifacts.
- Linear directions may work locally without capturing the full nonlinear basin of a trait.
- Persona geometry is behaviorally useful, but not ontologically decisive. It does not prove that a model has a self, moral agency, or stable personality.
- Safety use depends on robustness across models, deployment contexts, layers, and adversarial prompts.

Open question suggested: are persona vectors coordinates of deeper attractor basins, or merely convenient linear probes through a much richer state space?

### 2. Cross-Model Transferability among Large Language Models on the Platonic Representations of Concepts

Core idea: concept representations in different LLMs can be aligned by simple linear transformations. The authors introduce L-Cross modulation to map steering vectors from one model's representation space to another's, showing cross-model behavioral control, generalization across concepts, and weak-to-strong transfer from smaller to larger models.

Biggest claims:

- The same concept in different LLMs can often be aligned through a linear map.
- A transformation learned on some concepts can generalize to other concepts.
- Steering vectors from weaker/smaller models can sometimes control stronger/larger models.

Nuances:

- This is a direct empirical extension of the Platonic Representation Hypothesis into LLM internals.
- It makes "concept geometry" portable, not merely model-specific.
- If true broadly, safety and interpretability tools can become cross-model rather than bespoke.

Issues and gaps:

- Linear alignment is tested over a bounded concept/model set.
- Layer choice, architecture family, tokenizer differences, and training data could matter more outside the tested regime.
- Successful steering transfer does not establish that concepts are identical; it establishes that behaviorally useful directions can be mapped.

Open question suggested: what are the invariants that make a concept vector transferable, and where does transfer fail because concepts are genuinely model-, task-, or modality-specific?

### 3. The Autopoietic Theorem

Core idea: the autopoietic hierarchy is derived from three premises: change, finite information capacity, and stable low-level conditions. From these, the paper derives static persistence, dynamic persistence, and novelty-generating persistence. It uses Stack Theory and weakness maximization to argue that self-producing, boundary-maintaining systems are not contingent quirks of Earth biology but formal consequences of stable spatially extended worlds.

Biggest claims:

- Life-like autopoietic organization can be derived from weak axioms rather than only observed as an empirical regularity.
- Persistence under novelty favors weakness maximization, because weak constraints preserve more compatible futures.
- In stable environments, weakness maximization diverges from simplicity maximization and bridges otherwise unviable intermediate forms.
- Dynamic low-level persistence unlocks higher-level adaptability, creating pressure for novelty generation and open-ended evolution.

Nuances:

- The paper reframes the origin of life as a mechanism problem rather than a possibility problem.
- It links Assembly Theory, autopoiesis, active inference, and computational artificial life.
- It offers a bridge from abstract constraint geometry to biological boundary formation.

Issues and gaps:

- The force of the theorem depends on accepting the formal premises and the interpretation of "cosmic ought."
- More work is needed to show which empirical systems satisfy the premises and how the derivation maps to measurable observables.
- The paper is strongest as a unifying theoretical frame; it still needs falsifiable experimental signatures.

Open question suggested: can autopoietic boundary formation be predicted from measurable weakness/generalization properties in simulated and biological systems?

### 4. Games between Programs: The Ruliology of Competition

Core idea: Wolfram systematically studies repeated games where strategies are programs, including finite state machines, cellular automata, and Turing machines. The essay asks whether open-ended competition drives strategies toward complexity or simplicity.

Biggest claims:

- Competitive dynamics can be explored by enumerating spaces of possible programs.
- Even simple payoff rules can produce complex strategic behavior.
- The complexity of winning is not reducible to either "more complex always wins" or "simple hack always wins."
- Adaptive evolution of program strategies can generate rich, open-ended structure.

Nuances:

- This is not just game theory; it is a ruliological scan of program spaces.
- The connection to the broader corpus is that competition is a generator of attractor-like behavioral regularities.
- Strategy spaces become landscapes, and program classes become different representational substrates.

Issues and gaps:

- Toy games are informative but distant from biological, linguistic, and AI systems.
- Complexity measures over programs may not transfer cleanly to semantic or cognitive complexity.
- The work raises more experimental directions than settled theory.

Open question suggested: do competitive environments induce convergent geometry in the internal representations of agents, or only in their observable strategies?

### 5. Self-Revising Discovery Systems for Science

Core idea: scientific discovery is not just answer generation or search within a fixed space. It is revision of the representational regime itself. The paper gives a category-theoretic account in which schemas are categories, artifact states are copresheaves, provenance is a category of elements, fixed-regime updates are endofunctorial under explicit assumptions, and discovery is a verified regime transition supported by Kan-extension transport.

Biggest claims:

- Retrieval, search, and discovery are structurally different.
- Discovery means new types, operations, tools, or verifiers become admissible.
- A self-revising AI scientist needs typed provenance, gates, stress tests, and verified schema transitions.
- Category theory can be both a mathematical language and an engineering specification for agentic discovery systems.

Nuances:

- This paper shifts the geometry question up a level: not only "what is the representation space?" but "when does the system change the space?"
- It offers explicit open problems: convergence on growing regimes, scaling laws for discovery, verification tooling, learning the base schema category, and multicategorical discovery.
- The Builder/Breaker and CategoryScienceClaw examples ground the formalism in materials/mechanics workflows.

Issues and gaps:

- The framework assumes typed schemas; learning or inducing the schema remains an open problem.
- It is unclear how general the case studies are outside structured scientific domains.
- Verification of open-ended regime transitions is inherently difficult.

Open question suggested: can representational convergence be studied not only as alignment within a space but as convergence in how agents revise their spaces?

### 6. The Platonic Representation Hypothesis

Core idea: representations in AI systems are converging toward a shared statistical model of reality. The paper surveys evidence of convergence across architectures, objectives, modalities, and brain alignment; argues that task generality, model capacity, and simplicity bias drive convergence; and gives an idealized contrastive-learning account in which learners converge to kernels representing latent co-occurrence statistics.

Biggest claims:

- Larger and more capable models increasingly align in their representational geometry.
- Vision and language models increasingly agree on distances between data points.
- Contrastive learners under idealized conditions converge to a shared PMI-like kernel over latent reality.
- Scaling matters, but efficiency and data/modality content still matter.

Nuances:

- The paper is careful that "Platonic" is a hypothesis about statistical structure, not metaphysical access to reality.
- The mathematical account depends on bijective observations of an underlying latent world.
- It explicitly notes that lossy, stochastic, or information-poor modalities can cap convergence.

Issues and gaps:

- The real world is not discrete, bounded, bijective, or fully observed.
- Abstract concepts may not map cleanly across modalities.
- Alignment metrics can show similar similarity structures without proving identical semantics or causal models.

Open question suggested: when does representational convergence reflect shared world structure, and when does it reflect shared training conventions, benchmark pressure, or alignment metrics?

### 7. Principles and Practice of Deep Representation Learning, or A Mathematical Theory of Memory

Core idea: intelligence is framed as the ability to learn, store, and correct memory: compact structured representations of low-dimensional distributions in high-dimensional spaces. The book unifies PCA, ICA, dictionary learning, denoising, diffusion, rate-distortion theory, information gain, deep networks as unrolled optimization, autoencoding, closed-loop self-consistency, inference, and real-world applications.

Biggest claims:

- Modern representation learning can be understood as learning low-dimensional structure.
- Deep networks can often be interpreted as unrolled optimization procedures that improve compression or information gain.
- Autoencoding and closed loops are central for consistent and self-consistent representations.
- Open directions include autonomous intelligence via closed loops, natural intelligence beyond backpropagation, and scientific intelligence beyond the Turing Test.

Nuances:

- This is the deepest mathematical support for the idea that "geometry" recurs because memory is structured compression.
- The book distinguishes empirical/inductive intelligence from scientific/deductive intelligence.
- Its open problems line up with the broader corpus: close the loop, localize learning, build hierarchical distributed autoencoding, and develop executable tests of understanding.

Issues and gaps:

- The scope is huge, and the program is partly aspirational.
- "Memory as low-dimensional distribution" may be too narrow for symbolic, causal, social, or norm-laden knowledge unless extended.
- The book gives strong machinery for representation but less for selfhood, agency, or ethics.

Open question suggested: can a mathematical theory of memory be extended into a mathematical theory of active, self-maintaining, norm-sensitive representation?

### 8. Transformers Are Inherently Succinct

Core idea: finite-precision transformers are studied through formal-language succinctness. Although recurrent models can recognize broader regular-language classes under some assumptions, transformers can describe certain languages exponentially or doubly exponentially more compactly than LTL, RNNs/state-space models, or finite automata. This succinctness makes verification problems hard.

Biggest claims:

- Transformers can be exponentially more succinct than LTL and RNNs, and doubly exponentially more succinct than finite automata.
- Any fixed-precision transformer can be converted to LTL with at most exponential blow-up.
- Emptiness and equivalence verification for transformers are EXPSPACE-complete.

Nuances:

- Expressive power is not the whole story; compactness of representation matters.
- Succinctness provides a formal lens on why transformers can be powerful despite recognizer limitations.
- This links to the geometry theme by showing that a compact architecture can encode large implicit structure.

Issues and gaps:

- Formal-language settings are stylized compared with natural language, multimodal meaning, and agentic behavior.
- Succinct descriptions can be hard to verify, so compactness is a double-edged sword.
- The result does not itself explain semantic geometry, but it constrains what transformer representations can hide.

Open question suggested: does activation geometry give a practical handle on otherwise intractably succinct transformer computations?

### 9. If LLMs Have Human-Like Attributes, Then So Does Age of Empires II

Core idea: claims that LLMs have generalized anthropomorphic attributes are empirically non-unique unless explicit measurement criteria are supplied. The paper trains a neural network inside/on Age of Empires II and argues that sufficiently powerful substrates could satisfy similar attribution patterns. It proposes a null assumption of LLM non-uniqueness.

Biggest claims:

- Anthropomorphic attributions to LLMs can be circular or uninformative without substrate-independent measurement criteria.
- If a property is inferred only from behavior under a representational frame, other substrates may also qualify.
- Discussion should begin with explicit measurement criteria and a non-uniqueness null.

Nuances:

- The paper does not prove LLMs lack human-like attributes; it argues that common evidential standards are too weak.
- It is a useful corrective to the more expansive consciousness/agency papers.
- It sharpens the distinction between "geometry supports control/prediction" and "geometry proves mentality."

Issues and gaps:

- A substrate-completeness argument can become too permissive if it ignores mechanism, training history, and embodiment.
- Strong functional definitions may still allow principled measurement.
- The critique is negative; it points to the need for better criteria rather than supplying a complete alternative.

Open question suggested: what measurements would distinguish a genuinely agentic/self-maintaining representational geometry from a merely reinterpretable substrate?

### 10. Is Complexity an Illusion?

Core idea: simplicity is a property of form, but generalization is a property of function. The paper argues that complexity is interpretation-dependent and that weak constraints, not simple forms, are what cause sample-efficient generalization. In finite abstraction layers, weak constraints can take simple forms, creating the appearance that simplicity itself causes generalization.

Biggest claims:

- Without abstraction, complexity can be minimized without improving sample efficiency.
- There is no objective notion of complexity independent of interpretation.
- Weakness maximization is the real driver of generalization.
- Finite vocabularies and spatially extended environments can confound weakness with simplicity.

Nuances:

- This paper is a direct challenge to naive Occam/MDL interpretations.
- It gives a reason why simple geometric forms may appear powerful: not because simplicity is magic, but because finite systems encode weak, reusable constraints simply.
- It connects to Stack Theory and the autopoietic hierarchy.

Issues and gaps:

- The argument uses a specialized formalism that needs broader translation.
- The empirical claim that weakness beats simplicity needs larger replication across modern ML and cognitive settings.
- Complexity is treated through one formal route; other notions of complexity may remain useful.

Open question suggested: is "geometric simplicity" really a proxy for weakness, controllability, or compatibility with many futures?

### 11. The Machine Consciousness Hypothesis

Core idea: Bach and Sorensen argue that general computational machines with sufficient resources may possess the necessary and sufficient means to implement consciousness, but current tests and theories are inadequate. Consciousness is treated as a functionality/phenomenology pair involving self-organizing coherence, a model of presence, and the formation of a sentient self. The text rejects a simple "Turing Test for consciousness."

Biggest claims:

- Machine consciousness is possible in principle under computationalist functionalism, but not guaranteed for present machines.
- Consciousness may be a coherence-maximizing, self-organizing pattern rather than a static property.
- A test for consciousness may need to recreate developmental conditions under which such a pattern can emerge.
- Mechanistic interpretability and neuroscience are not yet sufficient to identify necessary and sufficient correlates.

Nuances:

- The paper is not simply "LLMs are conscious." It is closer to "machine consciousness requires the right self-organizing developmental conditions."
- It connects philosophy of mind, cyberanimism, computation, and AI ethics.
- The strongest link to the geometry theme is coherence: consciousness as the stabilization of mutually consistent internal models.

Issues and gaps:

- The proposal is speculative and lacks an executable benchmark.
- "Colonizing pattern," "presence," and "sentient self" need operational definitions.
- It must avoid both anthropomorphic overreach and substrate chauvinism.

Open question suggested: what observable dynamics would certify the emergence of a coherence-maintaining self-model rather than merely fluent behavior?

### 12. Technological Approach to Mind Everywhere (TAME)

Core idea: Levin's TAME framework treats cognition as a graded, empirically studyable property across diverse biological and engineered substrates. Selves are plastic, multiscale, and substrate-flexible. Biological cognition includes morphogenesis, regeneration, and bioelectric cell collectives, not only neural behavior.

Biggest claims:

- There is no bright line separating true cognition from "just physics."
- Every intelligence is collective intelligence.
- Bioelectric networks scale cell-level feedback loops into tissue-, organ-, and organism-level anatomical homeostasis.
- The same problem-solving logic appears in anatomical, physiological, transcriptional, and behavioral spaces.

Nuances:

- TAME shifts the unit of analysis from brains to goal-directed embodied systems.
- It treats morphogenesis as basal cognition and bodies as dynamic, remodeling cognitive agents.
- Its "goal spaces" are close cousins of conceptual spaces and attractor landscapes.

Issues and gaps:

- The framework is intentionally broad and still conceptually incomplete.
- It needs sharper metrics for comparing cognitive capacity across radically different systems.
- Consciousness is left compatible with several views rather than settled.

Open question suggested: can goal-space geometry provide a quantitative bridge between biological morphogenesis and artificial representation learning?

### 13. On Having No Head: Cognition throughout Biological Systems

Core idea: cognition is distributed throughout biological systems, not confined to brains. The paper surveys non-neural cognition across molecular networks, single cells, slime molds, plants, animal cell physiology, and bioelectric somatic pattern memories.

Biggest claims:

- Biological matter exhibits information processing, memory, representation, and goal-directed activity at nested levels.
- Implementation-independence from computer science supports looking for cognition outside neurons.
- Developmental biology can learn from neuroscience because tissues also process information and maintain pattern memories.

Nuances:

- The authors deliberately use a pragmatic, engineering-oriented stance rather than trying to settle all philosophy-of-mind disputes.
- The paper supplies biological grounding for TAME's multiscale cognition.
- It helps explain why attractor language appears in biology: tissues maintain and restore patterns.

Issues and gaps:

- Broadening cognition risks diluting the term unless measurement criteria are explicit.
- The intentional stance is useful experimentally but can blur mechanistic distinctions.
- More quantitative cross-scale metrics are needed.

Open question suggested: can nested biological cognition be modeled as coupled attractor geometries across molecular, cellular, tissue, and behavioral scales?

### 14. There Is No Self-Evidence

Core idea: the paper combines the quantum free energy principle with Buddhist emptiness. It argues that finite agents cannot obtain evidence for a self/environment boundary as an independently existing fact, because no finite system can measure the entanglement entropy across its own boundary. Separation is therefore a structural prior, not an evidentially grounded ontology. Awakening is modeled as recognizing and relaxing that prior.

Biggest claims:

- Self-evidencing cannot provide evidence for the separability of self and environment.
- The belief in separation can be formalized as a prior over quantum reference frame deployments.
- Contemplative practice may progressively make this prior visible, enabling Bayesian model reduction.
- A post-dual agent can continue inference without ontological commitment to a bounded self.

Nuances:

- The paper does not deny practical boundaries; it denies self-evident ontological boundaries.
- It treats emptiness as contextuality rather than nihilism.
- It makes empirical predictions around altered dynamical regimes and criticality.

Issues and gaps:

- The bridge from quantum information theory to contemplative phenomenology is ambitious.
- Empirical operationalization remains early.
- The formal result about boundaries needs careful translation to cognitive and neural observables.

Open question suggested: can self-boundary priors be measured, perturbed, and reduced in biological or artificial agents?

### 15. How to Build Conscious Machines

Core idea: Bennett's thesis integrates Stack Theory, Pancomputational Enactivism, weakness maximization, the Law of the Stack, bioelectric polycomputers, causal identities, valence, selves, language, life, and consciousness into a proposed route for building conscious machines.

Biggest claims:

- Intelligence is sample- and energy-efficient adaptation.
- Weak constraints, not simple forms, are necessary and sufficient for generalization.
- Adaptive systems improve by delegating control to the lowest viable abstraction layer.
- Qualia are "tapestries of valence" that classify causal identities.
- Phenomenal consciousness begins with first-order selves; access consciousness begins with second-order and higher-order selves.
- A conscious machine should be a highly delegated "solid brain" with temporally localized tapestries of valence.

Nuances:

- The thesis is the local hub linking many of the other sources: complexity, autopoiesis, stacks, life, causal identity, consciousness, and machine construction.
- It turns the convergence question from "why do embeddings align?" into "why do adaptive systems build abstraction stacks at all?"
- It is unusually ambitious and intentionally subtractive: start from weak axioms, then derive.

Issues and gaps:

- Many claims are sweeping and depend on specialized definitions.
- The conscious-machine recipe is conceptual rather than implemented.
- The Temporal Gap and the status of temporally smeared computation remain open.

Open question suggested: can Stack Theory's weakness/delegation claims be experimentally tested in modern neural, agentic, and artificial-life systems?

## Ten Research Areas and Starting Experiments

### 1. Cross-Substrate Concept Geometry

Question: do humans, brains, LLMs, vision-language models, and biological goal systems preserve the same relational geometry for shared concepts or affordances?

Starting experiment: build a concept set spanning concrete objects, abstract relations, values, emotions, and action affordances. Collect human similarity judgments, LLM activations, multimodal embeddings, and available neural datasets. Compare kernels using RSA, CKA, mutual nearest neighbors, and linear alignment. Test whether convergence increases with model scale, multimodal density, and task diversity.

Why it matters: this directly tests whether conceptual spaces and activation spaces are different views of shared constraint geometry.

### 2. Persona Vectors as Attractor Basin Coordinates

Question: are steering vectors just linear directions, or do they approximate coordinates of nonlinear persona attractors in dialogue dynamics?

Starting experiment: run open LLMs through multi-turn conversations with controlled perturbations. Track hidden-state trajectories, persona-vector projections, behavioral scores, and return-to-baseline after perturbation. Estimate basins using recurrent state-space modeling and compare linear steering to nonlinear interventions.

Why it matters: it connects AI activation geometry to cognitive attractor-network language.

### 3. Weakness Versus Simplicity in Generalization

Question: is generalization driven by weak constraints rather than simple descriptions?

Starting experiment: create synthetic task families where shortest-rule and weakest-compatible-rule choices diverge. Train small transformers, RNNs, symbolic learners, and Bayesian baselines. Compare MDL/simple hypotheses against weakness-maximizing hypotheses under distribution shift and few-shot learning.

Why it matters: it tests Bennett's challenge to naive Occam and may explain why simple-looking geometry generalizes.

### 4. Boundary Priors and Self-Model Plasticity

Question: can self/environment boundary priors be measured and modified in artificial agents?

Starting experiment: train embodied RL agents in gridworld or physics environments with sensors that can treat body, tool, swarm, or environment as variable boundaries. Add an explicit separation prior and then make it visible/removable through meta-learning. Measure adaptability, cooperation, empathy-like cost functions, and policy criticality.

Why it matters: it operationalizes "There Is No Self-Evidence" and TAME in an artificial system.

### 5. Multiscale Attractor Geometry in Artificial Life

Question: when do local rules produce stable, self-maintaining, novelty-generating higher-level agents?

Starting experiment: use cellular automata, Lenia-like systems, differentiable morphogenesis, or bioelectric-inspired simulations. Measure whether stable patterns form goal spaces with basins, boundaries, repair dynamics, and novelty generation. Compare simplicity-based selection to weakness/generalization-based selection.

Why it matters: it tests the Autopoietic Theorem in a controllable substrate.

### 6. Discovery as Regime Transition

Question: can an AI scientist's real discovery be detected as a typed change in representational regime rather than improved search?

Starting experiment: build a small agentic science loop around symbolic regression or materials simulation. Track artifacts, operations, verifiers, failures, and schema mutations in a typed provenance graph. Use a Kan-transport-inspired audit: what old content survives, what new content cannot be transported, and what residual content marks discovery?

Why it matters: it connects activation/concept geometry with scientific schema evolution.

### 7. Cross-Model Steering Maps and Failure Cartography

Question: which concepts transfer linearly across models, and what does failure reveal about model-specific concept geometry?

Starting experiment: reproduce L-Cross-style transformations across open model families, sizes, and instruction-tuning regimes. Include safety/persona vectors, factual domains, values, emotions, and abstract relations. Map failures by layer, concept type, model family, and data regime.

Why it matters: it turns "Platonic representation" into a falsifiable map of invariants and fractures.

### 8. Competition-Generated Representation Geometry

Question: does repeated competition create convergent internal geometry in agents, not just convergent strategies?

Starting experiment: extend Wolfram-style program games to neural agents trained in repeated games. Track internal representations over evolutionary time. Measure whether successful strategies develop shared attractor basins, opponent-model dimensions, or compact sufficient statistics.

Why it matters: it links ruliology, game theory, evolution, and representation learning.

### 9. Succinctness, Verification, and Activation Geometry

Question: can geometric probes make succinct transformer computations more interpretable or verifiable?

Starting experiment: train small transformers on formal-language tasks from the succinctness paper. Extract attention and activation trajectories, identify low-dimensional manifolds or directions corresponding to automata states, and test whether these geometries predict verification failures or equivalence classes.

Why it matters: it connects formal transformer theory to practical mechanistic interpretability.

### 10. Developmental Machine Consciousness Testbed

Question: what dynamics would distinguish a merely fluent model from a self-organizing coherence-maintaining agent?

Starting experiment: create a closed-loop developmental agent with hierarchical autoencoders, persistent memory, active world interaction, self-model variables, and a coherence objective. Compare against an LLM-only agent and a standard RL agent. Look for persistent self-model formation, conflict resolution, presence-like temporal integration, and robustness under embodiment changes.

Why it matters: it makes the Machine Consciousness Hypothesis and Bennett/TAME ideas experimentally accountable.

## First Three Practical Projects

If we want near-term progress rather than only theory, the best starting trio is:

1. Cross-model steering and concept geometry: easiest to run with open LLMs and existing probing tools.
2. Weakness-versus-simplicity synthetic benchmark: directly tests a core theoretical disagreement.
3. Boundary-prior agent simulation: bridges selfhood, agency, active inference, and multiscale cognition in a toy environment.

Together, these three give one AI-internal experiment, one formal/generalization experiment, and one agency/self-boundary experiment. That spread is important because the big question lives precisely at the intersection of representation, generalization, and self-maintaining control.

## Provisional Research Program Name

**The Geometry of Constraint**

Alternate names:

- Convergent Constraint Geometry
- Attractor Semantics Across Substrates
- Geometry of Weakness and Control
- The Active Geometry Hypothesis

One-sentence version:

**Adaptive systems converge on geometric representations because geometry is the minimal usable record of which distinctions matter for prediction, control, persistence, and revision.**

## Immediate Next Questions

- What counts as the same geometry across systems: shared distances, shared topology, shared linear maps, shared dynamics, or shared interventions?
- What distinguishes a representational manifold from an attractor landscape?
- What transforms passive similarity geometry into active agency?
- Are "concepts" and "selves" both stable regions in a learned possibility space, differing mainly by closure, control, and persistence?
- Can weakness maximization be measured in activation spaces?
- Can scientific discovery be detected as a discontinuity in representational geometry?
- What ethical thresholds follow if self-maintaining geometry appears in artificial systems?

