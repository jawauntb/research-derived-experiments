# From Concern to Action Surfaces

## A Critical Literature Review and Research Program for Causally Grounded Finite Agents

Date: 2026-07-07

## Abstract

This paper reviews the research-derived experiments corpus as a unified program about finite agents: systems that must compress a world, preserve viability-relevant distinctions, act under uncertainty, and remain honest under distribution shift. The review starts from first principles for readers without machine learning, neuroscience, or philosophy background, then links the repository's papers to external literatures in representation learning, causal inference, active learning, reinforcement learning, domain generalization, cybernetics, active inference, enactivism, and mathematical theories of symmetry and compression. The central synthesis is that the program is not a claim that current systems are conscious, nor a claim that behavior alone proves agency. It is a methodological claim: for every proposed agent capability, identify the proxy that could fake success, then add a test or architecture change that makes the intended causal structure load-bearing at the action surface. The paper critiques an earlier review draft, revisits the citation surface, separates established theorems from local empirical laws and formalizable conjectures, and proposes future work around reafferent gauge breaking, re-engagement floors, commitment-surface memory, structure-compatible generalization, and finite-capacity concern geometry.

## 1. Why the first review was not enough

The first comprehensive review was useful, but it was not good enough as a paper. It had four weaknesses.

1. It summarized the corpus more than it argued for a contribution.
2. It mixed established mathematical results, local empirical regularities, and speculative future theorems too easily.
3. Its reference appendix was too raw: extracted citation lines were noisy, line-wrapped, and mixed workflow links with academic references.
4. It did not place the paper-review caveats at the center. The corpus repeatedly warns against overclaiming: behavior is not representation, uncertainty is not error, a probe is not causal use, memory is not commitment, and finite control diagnostics are not consciousness proofs.

This revision therefore changes the genre. It is a critical literature review paper, not just a survey artifact. It treats the repository itself as a corpus, but it also asks what standards of evidence the corpus has learned.

## 2. First principles

### 2.1 Finite agents

A finite agent is a system with limited memory, limited sensing, limited action, and limited time. It can be a simple reinforcement-learning agent, a neural network in a controlled environment, a tool-using language model, a cell, an organism, or a human-built institution. The word "agent" should not be inflated: an agent is not automatically conscious, autonomous, or morally responsible. In this paper, "agent" means a system whose future state depends partly on its own actions.

The first problem for such a system is compression. The world has more detail than the system can store. The agent must decide which distinctions matter. A thermostat preserves temperature but ignores wallpaper. A navigation system preserves paths and obstacles but ignores most chemistry. A homeostatic agent preserves energy, shock, food, medicine, or target variables, because those variables affect future viability.

The second problem is control. A passive representation can describe; a controller must act. A learned internal direction, cluster, or feature is only agent-relevant if it reaches the surface where behavior is selected.

The third problem is identification. Many internal explanations can fit the same observations. The agent may confuse "I caused this" with "the world caused this," or a shortcut rule with a transportable rule. Observing more of the same data does not always solve this. Interventions, constraints, and anti-cheat controls are often required.

### 2.2 Concern

The repository uses "concern" for viability-relevant difference. A state, object, event, or prediction is concerning when it changes what the system should do to keep itself within acceptable bounds. In the papers this appears as Delta E, Delta V, reward deformation, stress, source attribution, probe value, commitment variables, or structure compatibility.

This use of concern is deliberately operational. It does not assume subjective feeling. It asks a smaller question: which variables become load-bearing for action because they affect the system's ability to maintain itself or complete its commitments?

### 2.3 Geometry

When a finite system compresses many possible situations into fewer internal states, it creates geometry. Geometry is the language of preserved relations: near and far, same and different, reachable and unreachable, stable and unstable, inside and outside a boundary, invariant and transformed. This is why the corpus keeps meeting manifolds, directions, clusters, basins, symmetry groups, kernels, spectra, and topology.

The key caution is that geometry can be passive. A model may contain a useful-looking direction while its policy ignores it. The repository's strongest work asks when geometry becomes active: when interventions along it change behavior, when planning closes through it, when it survives held-out transformations, and when it reaches future action surfaces.

### 2.4 Action surfaces

An action surface is the place in a system where a represented variable constrains behavior. It can be a policy head, a tool argument, a generated JSON field, a repair branch, a probe decision, a final-token distribution, a training selection rule, or a local stress feature. Much of the program can be compressed into one sentence:

> A variable matters to agency when it is represented at the surface where future action is selected, and when proxy controls fail.

This sentence is not a theorem yet. It is a research program.

## 3. Review method and source corpus

The review covers Markdown, TeX, BibTeX, notes, critical reviews, preregistrations, source manifests, and benchmark documents in the repository. The audit pass found 165 text sources and 286 unique-ish raw reference lines after removing obvious duplicates and build artifacts. The primary paper coverage includes concern/valence geometry, state-dependent boundary failure, first-order self/world attribution, null interventions, probe value, re-engagement, planning from concern, long-horizon commitment surfaces, structure-compatible generalization, learned symmetry, concerned syntax, viable computational bodies, virtual-governor stress signals, coherence testbench documents, and ICML package drafts.

The review treats three evidence levels differently:

1. Established external theory, such as causal intervention, rate-distortion, group equivariance, invariant prediction, and the impossibility of unsupervised disentanglement without assumptions.
2. Repository empirical laws, such as predictive policy closure, reafferent identifiability, re-engagement floors, commitment-surface memory, and structure-compatible selection.
3. Formalizable conjectures, where the repository has enough structure to motivate theorem statements but not yet enough assumptions and proofs.

This split matters because a literature review that cannot separate theorem, experiment, and conjecture will mislead its reader.

## 4. External literatures

### 4.1 Representation learning and probes

Representation learning studies how systems turn observations into useful internal variables. Disentanglement work shows why this is hard: without assumptions, unsupervised factors are not identifiable. Probe literature adds a second warning: a linear readout can extract information from a representation without proving that the model uses that information. Activation-editing work, persona vectors, cross-model concept transfer, and factual editing show that internal geometry can sometimes be operationally useful, but the repository's stricter question is whether a feature is causal under intervention and controls.

The internal lesson is: do not stop at "the vector exists." Ask whether it changes behavior specifically, whether independent controls fail, and whether it remains meaningful after the surface changes.

### 4.2 Causal representation learning

Causal representation learning asks which latent variables correspond to intervention-relevant causes. Pearl-style interventions, invariant prediction, weakly supervised causal representation learning, and object-centric causal world models all matter here. The repository adapts this logic to minimal agents: null actions, probe actions, source labels, mediated effects, action-correlated shocks, and world changes are not incidental task details. They are the instruments that make attribution identifiable.

This is why the first-order self arc is important. A self head and a world head can look architecturally separated while still trading credit arbitrarily. Identification requires a signal that breaks the symmetry.

### 4.3 Active learning, uncertainty, and inquiry

Active learning asks when to gather information. Bayesian active learning, BALD, epistemic neural networks, deep ensembles, dropout uncertainty, curiosity, novelty, and random network distillation provide tools for valuing information. The repository's contribution is skeptical: uncertainty signals can be flat at the dangerous boundary, stale residuals can become anti-calibrated, and probe value can cause over-probing or anxiety.

The better abstraction is controlled inquiry. Inquiry has cost. It has refractory dynamics. It must re-engage after world change. It must preserve surprise while cooling action tendency. This reframes active learning as a closed-loop control problem rather than a scalar uncertainty ranking.

### 4.4 Reinforcement learning, world models, and agent benchmarks

Reinforcement learning supplies the action loop: observe, act, receive feedback, update. World models let agents evaluate candidate futures. Language-agent benchmarks show how modern systems plan, use tools, browse, repair, and solve tasks. But benchmark success is not enough. ReAct, Reflexion, Voyager, SayCan, Toolformer, AgentBench, WebArena, OSWorld, GAIA, SWE-bench, BIG-bench, and HELM all motivate the need for evaluation surfaces; the repository's distinctive move is proxy resistance.

The benchmark question becomes: did the agent succeed for the right causal reason? A final answer is necessary but not sufficient. The relevant variable must reach the behavior surface, and anti-cheat controls must fail.

### 4.5 Domain generalization, invariance, and symmetry

Underspecification is central: many models can fit the same training data while failing differently under shift. Invariant risk minimization, DomainBed, GroupDRO, WILDS, shortcut learning, causal representation learning, and group-equivariant networks all address this from different angles. The repository's structure-compatible line asks: when in-distribution data does not decide between shortcut and rule, can the expected deployment transformation decide?

This connects to group theory. If a task has a symmetry, a compatible model should transform predictably when the input is transformed. Weakness, in this corpus, is not mere simplicity. It is a count or measure of compatible transformations: the learned function has fewer arbitrary ways to break the task's structure.

### 4.6 Neuroscience and cognitive science

Several neuroscience ideas recur:

- reafference and comparator models for self/world attribution;
- allostasis and homeostasis for state-dependent regulation;
- active inference and predictive processing for action-perception loops;
- habituation and refractory periods for bounded re-engagement;
- neural manifolds, rings, tori, and attractor basins for low-dimensional cognitive geometry;
- developmental plasticity, where activity can shape structure rather than merely ride on top of it.

The repository should not claim to prove consciousness. Its narrower contribution is to operationalize pieces of agency: viability sensitivity, attribution, inquiry, planning closure, memory at action, and structure-compatible generalization.

### 4.7 Philosophy, biology, and meaning

Dewey, Gibson, Uexkull, Heidegger, Canguilhem, Jonas, Maturana and Varela, Di Paolo, Thompson, Levin, Vervaeke, Bennett, and related enactive or cybernetic traditions are useful because they reject detached representation as the whole story. Meaning appears in relation to action, normativity, affordance, relevance, viability, and self-maintenance.

The repository translates that family of ideas into finite tests. It asks whether a signal is action-relevant, whether it maintains a boundary, whether it updates under surprise, and whether it resists proxy explanations.

## 5. Internal research arcs

### 5.1 Concern, valence, and metric deformation

The concern and valence papers ask whether viability-relevant objectives reshape representation. Valence object formation shows objects clustering by causal role rather than sensory similarity. Homeostatic objects and passive-to-active geometry test whether such representations transfer into control. Concern bootstrap and two-bottlenecks reveal that representation and competence can split: a Delta E auxiliary loss can create valence geometry while sparse-reward policy learning fails to exploit it.

The reward-deformation notes sharpen this into a mathematical program. A finite-capacity code under a value-weighted distortion objective should allocate more resolution where errors are costly. The clean two-dimensional exponent was not confirmed in the grid/RNN harness; instead the measured effective dimension was near one. That is not a failure of the program. It is a better result: the normative rate-distortion law exposed the architecture's actual allocation dimension.

### 5.2 State-dependent concern and boundary failure

State-dependent concern, off-policy coverage, regime-sensitive Delta E, allostatic control, and ensemble uncertainty all circle a boundary problem: the same thing can help or harm depending on internal state. Learned models often smooth across the exact state where the rule changes. Ensembles can be confident where they should be uncertain. More data is not always the answer; the system needs the right state variable and boundary representation.

The implication is that "uncertainty-aware" is not a magic phrase. An uncertainty signal is useful only when it is calibrated to the current decision surface and the failure mode it is supposed to detect.

### 5.3 First-order self and reafferent attribution

First-order self shows that architectural factorization alone does not identify self-caused and world-caused change. Null interventions reduce false credit by giving the agent an action whose expected consequences differ under the competing explanations. Costly null probes, online identifying interventions, current-error calibration, vector first-order self, and scale-normalized V-probe extend this through cost, online regimes, vector-valued viability, and calibration.

The program law is reafferent identifiability: passive input factorization is not source identification. Self/world attribution requires a gauge-breaking signal.

### 5.4 Inquiry, probe value, and re-engagement

World Responds makes the environment responsive to action. Probe-value re-engagement asks when to ask again. Habituated re-engagement and Suite C show that successful inquiry needs a burst-and-refractory structure: detect surprise, probe when valuable, cool down after probing, preserve the surprise signal, and reopen after a second shift.

The crucial negative is false calm. If probing goes to zero after convergence and no path reopens it, the agent can mistake silence for stability.

### 5.5 Planning from concern

Planning from concern shows that action-conditioned Delta E predictions can become a policy when the agent chooses actions by predicted viability change. Planning hardening shows that this is not just a single reward-axis trick. The architecture law is predictive policy closure: a concern model becomes agent-relevant when the policy actually closes through it.

### 5.6 Commitment-surface memory

The long-horizon bottleneck papers ask whether early information reaches the later surface where action is selected: final action, tool argument, repair branch, generated JSON value, hidden site, causal patch, or black-box dispatch. The strongest insight is negative as well as positive: memory somewhere in a hidden state is not enough. Memory is agent-relevant when it binds a future commitment surface.

This result is one of the easiest to export to modern tool agents. Did the variable that matters later actually constrain the tool call or emitted value?

### 5.7 Structure-compatible generalization

Weakness invariance, learned symmetry discovery, neural group generator, and the structure-compatible generalization suite ask how to select models when training evidence underdetermines the rule. The strongest bounded claim is: when a candidate deployment transformation family exists, compatibility with that family can beat loss, validation, norm, sharpness, and other proxies.

The paper reviews are right to insist on scope. This is not open-world OOD certification. It is finite-domain model selection and, in later phases, finite-domain transformation discovery and intervention.

### 5.8 Concerned syntax and viable computational bodies

Concerned syntax and viable computational bodies ask whether syntax-bearing architectures can be searched and gated. The Haskell typed ontology gate is useful because it moves some commitments out of ad hoc Python checks and into explicit admissibility constraints. The philosophical import is modest but real: ontology becomes executable when the system must say which combinations are well-typed before empirical scoring begins.

### 5.9 Virtual governors and stress transduction

The virtual-governor framing is useful but bounded. The Lyons, Pio-Lopez, and Levin preprint is not peer-reviewed and should not be imported as evidence. Its value is vocabulary: global constraint violations can be translated into local incentives. The repository makes this executable with stress-signal tests: live global stress should improve local recovery, while reward-only, local-only, stale, and wrong-signal controls should fail or degrade.

### 5.10 Coherence testbench and scientific discipline

The coherence-testbench documents matter because they record failure discipline. A Phase 0 EEG bet hit a kill criterion. Later eyetrack and quiz-score work explored alternatives, but the post-mortem did not silently rename failure as success. That is part of the program's method: publish the negative, state what it does and does not test, and make the next branch discriminative.

## 6. Cross-field invariants

The same invariants recur across ML, neuroscience, philosophy, and biology.

1. Finite capacity forces compression.
2. Compression creates geometry.
3. Geometry becomes meaningful when it preserves action-relevant distinctions.
4. Passive representation is weaker than closed-loop control.
5. Attribution needs intervention or constraint when passive data are underdetermined.
6. Inquiry must be calibrated, costly, stateful, and reopenable.
7. Memory matters at the commitment surface.
8. Generalization improves when the hypothesis space respects deployment-generating transformations.
9. Local action often needs a transduced global constraint signal.
10. Every benchmark needs anti-proxy controls.

These invariants are why the corpus naturally crosses fields. In ML they appear as probes, interventions, OOD shifts, and action heads. In neuroscience they appear as reafference, allostasis, habituation, and manifolds. In philosophy they appear as affordance, relevance, normativity, and situated coping. In biology they appear as autopoiesis, adaptivity, and function shaping structure.

## 7. Mathematical ledger: theorem, law, conjecture

### 7.1 Established theorem family: no free lunch and underspecification

Field: learning theory and statistics.

Idea: without assumptions, no learner is universally best. Modern underspecification says multiple models can fit the same data while encoding different deployment behavior. Proof intuition: for any learner that succeeds on one family of worlds, another allowed world can reverse the labels or deployment relation. Generalization needs bias.

Program implication: the problem is not whether to use inductive bias; it is whether the bias preserves the right causal or transformation structure.

### 7.2 Established theorem family: non-identifiability of unsupervised disentanglement

Field: representation learning and causal inference.

Idea: unsupervised latent factors are not identifiable without assumptions. An invertible transformation can preserve observations while changing the apparent factors. Program implication: concern, self/world, and role factors need intervention, supervision, architecture, or constraints.

### 7.3 Established theorem family: causal intervention and mediation

Field: causal inference.

Idea: interventions replace a variable's usual mechanism, allowing causal effects to be distinguished from correlations when graph and data assumptions permit. Program implication: null actions, probe actions, source labels, and interventional contrast are local causal instruments.

### 7.4 Established theorem family: invariant prediction and equivariance

Field: statistics, group theory, domain generalization.

Idea: causal mechanisms and symmetry-compatible functions remain stable across certain environment changes. Equivariant functions commute with group actions. Program implication: structure-compatible selection and weakness are ways of measuring whether a learned function respects the deployment transformation.

### 7.5 Established theorem family: rate-distortion and efficient coding

Field: information theory.

Idea: finite representational capacity creates an optimization problem: allocate code precision where distortion is costly. The high-resolution solution predicts power-law relationships between value density and code density. Program implication: concern should deform metric geometry when capacity is binding. The repository's measured effective-dimension result turns this into an empirical architecture diagnostic.

### 7.6 Established theorem family: Ashby's law of requisite variety

Field: cybernetics and control.

Idea: a controller needs enough response variety to match relevant disturbance variety. Program implication: scalar drive models can fail where vector concern, role-specific heads, or typed structures are required.

### 7.7 Local empirical law: reafferent gauge breaking

Claim: when self-caused and world-caused explanations are observationally equivalent, an identifying intervention is required to break attribution symmetry.

Proof roadmap: formalize two latent source models with equal passive likelihood; define an action whose expected observation differs by source; show that source posterior cannot concentrate without the intervention but can under the intervention.

### 7.8 Local empirical law: current replay calibration

Claim: stale residuals can be anti-calibrated for the current model; recomputing residuals against the present model can restore probe-value calibration.

Proof roadmap: model online learning as changing hypothesis h_t; old residuals estimate error of h_old, not h_t; replay recomputes residuals under h_t and aligns calibration with the present decision surface.

### 7.9 Local empirical law: re-engagement floor

Claim: in responsive worlds, a converged inquiry policy needs a path back into probing after surprise.

Proof roadmap: if probe probability decays to zero and no surprise-gated term can raise it, post-shift evidence is not sampled; the agent cannot identify the shift.

### 7.10 Local empirical law: commitment-surface memory

Claim: memory is agent-relevant when early information causally reaches the later surface where action is selected.

Proof roadmap: define a future-critical variable z and a final action surface a; use patching or counterfactual replacement of z while controlling distractors; memory counts when a changes specifically with z.

### 7.11 Local empirical law: structure-compatible selection

Claim: when in-distribution evidence underdetermines shortcut and rule, select models compatible with deployment-generating transformations.

Proof roadmap: define a transformation family T and a compatibility score; show that equal-ID models differ in T-compatibility; under deployment generated by T, incompatible shortcuts have higher expected OOD error.

### 7.12 Conjecture: action-surface sufficiency

Conjecture: for finite-agent benchmarks, a capability claim is evidentially strong only when behavior, representation, intervention specificity, and action-surface coupling are all present under anti-proxy controls.

This is less a theorem than a benchmark-design standard. Its value is practical: it tells us what to test before using words like grounded, agentic, or concern-mediated.

## 8. Implications

### 8.1 For AI evaluation

Benchmarks should report vectors, not only scalar scores: behavior, causal representation, attribution, inquiry, commitment, and generalization. Passing behavior without the relevant structure should be treated as a partial pass or a fail, depending on the claim.

### 8.2 For interpretability

Interpretability should move from feature discovery to feature use. A direction, probe, or circuit matters when interventions on it produce specific behavioral effects and controls fail.

### 8.3 For agent design

The architecture pattern is recurring:

- vectorize viability signals when scalar reward is insufficient;
- calibrate against current evidence, not stale residuals;
- add safe identifying interventions when attribution is ambiguous;
- preserve re-engagement after surprise;
- bind memory to future commitments;
- expose deployment transformations as selection or training surfaces;
- transduce global stress into local action pressure.

### 8.4 For philosophy and neuroscience

The work gives operational handles for old words: concern, self, relevance, meaning, inquiry, and boundary. It does not solve their metaphysics. It shows how to ask narrower mechanistic questions without pretending those questions exhaust the phenomena.

## 9. Future directions

1. Formalize the local laws as lemmas with explicit assumptions and counterexamples.
2. Replace hand-coded interventions with learned intervention discovery.
3. Test action-surface laws in tool-using LLM agents and robotics.
4. Measure geometry beyond linear probes: curvature, effective dimension, topology, spectral concentration, and basin structure.
5. Build per-experiment provenance cards for agent-generated science.
6. Separate agency diagnostics from consciousness claims in every paper.
7. Turn structure-compatible selection into a public benchmark suite with wrong-transformation controls.
8. Connect virtual-governor stress transduction to multi-agent and decentralized coordination tests.

## 10. Conclusion

The research-derived experiments program is strongest when it is hardest on itself. Its durable contribution is not that one toy world proves agency, nor that one vector proves meaning. Its contribution is a disciplined pattern:

> Name the capability, name the proxy that could fake it, design the intervention or architecture surface that would make the intended structure load-bearing, and publish the boundary when it fails.

That pattern is the bridge between the repository's papers and the external literatures. It turns broad philosophical intuitions about meaning, self, and concern into finite empirical questions. It turns ML worries about underspecification, shortcuts, and probes into action-surface tests. And it points toward a research program where grounded agents are evaluated not by success alone, but by whether the right variables become causal where future action is chosen.

## Curated references

### Foundations, biology, and philosophy

- Ashby, W. R. (1952). Design for a Brain. Chapman & Hall.
- Bennett, M. T. (2023). On the computation of meaning, language models, and incomprehensible horrors. Synthese, 201(75).
- Canguilhem, G. (1966). Le Normal et le pathologique. Presses Universitaires de France.
- Dewey, J. (1938). Logic: The Theory of Inquiry. Henry Holt.
- Di Paolo, E. (2005). Autopoiesis, adaptivity, teleology, agency. Phenomenology and the Cognitive Sciences, 4(4), 429-452.
- Friston, K. (2010). The free-energy principle: a unified brain theory? Nature Reviews Neuroscience, 11(2), 127-138.
- Gibson, J. J. (1979). The Ecological Approach to Visual Perception. Houghton Mifflin.
- Goodhart, C. (1975). Problems of monetary management: the U.K. experience. Papers in Monetary Economics.
- Heidegger, M. (1927). Being and Time. Niemeyer.
- Jonas, H. (1966). The Phenomenon of Life. Harper & Row.
- Klyubin, A. S., Polani, D., and Nehaniv, C. L. (2005). Empowerment: a universal agent-centric measure of control. IEEE Congress on Evolutionary Computation.
- Levin, M. (2022). Technological Approach to Mind Everywhere. Frontiers in Systems Neuroscience.
- Lyons, B., Pio-Lopez, L., and Levin, M. (2026). Alignment is to a virtual governor: A theory of coordination in diverse intelligence. Preprints.org. Not peer reviewed.
- Maturana, H. R., and Varela, F. J. (1980). Autopoiesis and Cognition. D. Reidel.
- Parr, T., Pezzulo, G., and Friston, K. (2022). Active Inference. MIT Press.
- Simondon, G. (1958). L'individu et sa genese physico-biologique. Presses Universitaires de France.
- Thompson, E. (2007). Mind in Life. Harvard University Press.
- Uexkull, J. von (1934/2010). A Foray into the Worlds of Animals and Humans. University of Minnesota Press.
- Vervaeke, J. (2019). Awakening from the Meaning Crisis. Lecture series.

### Representation, causality, and probes

- Brehmer, J., De Haan, P., Lippe, P., and Cohen, T. (2022). Weakly supervised causal representation learning. NeurIPS.
- Hewitt, J., and Liang, P. (2019). Designing and interpreting probes with control tasks. EMNLP-IJCNLP.
- Locatello, F., Bauer, S., Lucic, M., Raetsch, G., Gelly, S., Schoelkopf, B., and Bachem, O. (2019). Challenging common assumptions in the unsupervised learning of disentangled representations. ICML.
- Meng, K., Bau, D., Andonian, A., and Belinkov, Y. (2022). Locating and editing factual associations in GPT. NeurIPS.
- Pearl, J. (2009). Causality. Cambridge University Press.
- Schoelkopf, B., Locatello, F., Bauer, S., Ke, N. R., Kalchbrenner, N., Goyal, A., and Bengio, Y. (2021). Toward causal representation learning. Proceedings of the IEEE, 109(5), 612-634.

### Active learning, uncertainty, and exploration

- Burda, Y., Edwards, H., Storkey, A., and Klimov, O. (2019). Exploration by random network distillation. ICLR.
- Gal, Y., and Ghahramani, Z. (2016). Dropout as a Bayesian approximation. ICML.
- Gal, Y., Islam, R., and Ghahramani, Z. (2017). Deep Bayesian active learning with image data. ICML.
- Houlsby, N., Huszar, F., Ghahramani, Z., and Lengyel, M. (2011). Bayesian active learning for classification and preference learning. arXiv:1112.5745.
- Kendall, A., and Gal, Y. (2017). What uncertainties do we need in Bayesian deep learning for computer vision? NeurIPS.
- Lakshminarayanan, B., Pritzel, A., and Blundell, C. (2017). Simple and scalable predictive uncertainty estimation using deep ensembles. NeurIPS.
- Osband, I. et al. (2023). Epistemic neural networks. NeurIPS.
- Pathak, D., Agrawal, P., Efros, A. A., and Darrell, T. (2017). Curiosity-driven exploration by self-supervised prediction. ICML.
- Settles, B. (2009). Active learning literature survey. University of Wisconsin-Madison.

### Generalization, symmetry, and agents

- Ahn, M. et al. (2023). Do As I Can, Not As I Say: Grounding language in robotic affordances. CoRL.
- Amodei, D. et al. (2016). Concrete problems in AI safety. arXiv:1606.06565.
- Arjovsky, M., Bottou, L., Gulrajani, I., and Lopez-Paz, D. (2019). Invariant Risk Minimization. arXiv:1907.02893.
- Cohen, T., and Welling, M. (2016). Group equivariant convolutional networks. ICML.
- D'Amour, A. et al. (2022). Underspecification presents challenges for credibility in modern machine learning. JMLR.
- Geirhos, R. et al. (2020). Shortcut learning in deep neural networks. Nature Machine Intelligence.
- Gulrajani, I., and Lopez-Paz, D. (2021). In search of lost domain generalization. ICLR.
- Ha, D., and Schmidhuber, J. (2018). World models. NeurIPS.
- Jimenez, C. E. et al. (2024). SWE-bench: Can language models resolve real-world GitHub issues? ICLR.
- Koh, P. W. et al. (2021). WILDS: A benchmark of in-the-wild distribution shifts. ICML.
- Langosco, L. et al. (2022). Goal misgeneralization in deep reinforcement learning. ICML.
- Liang, P. et al. (2022). Holistic Evaluation of Language Models. arXiv:2211.09110.
- Liu, X. et al. (2023). AgentBench: Evaluating LLMs as agents. arXiv:2308.03688.
- Mialon, G. et al. (2024). GAIA: A benchmark for general AI assistants. ICLR.
- Peters, J., Buehlmann, P., and Meinshausen, N. (2016). Causal inference by using invariant prediction. JRSS-B.
- Sagawa, S., Koh, P. W., Hashimoto, T. B., and Liang, P. (2020). Distributionally robust neural networks for group shifts. ICLR.
- Schick, T. et al. (2023). Toolformer: Language models can teach themselves to use tools. NeurIPS.
- Shinn, N. et al. (2023). Reflexion: Language agents with verbal reinforcement learning. NeurIPS.
- Srivastava, A. et al. (2022). BIG-bench. TMLR.
- Wang, G. et al. (2023). Voyager: An open-ended embodied agent with large language models. TMLR.
- Xie, T. et al. (2024). OSWorld: Benchmarking multimodal agents for open-ended tasks. arXiv:2404.07972.
- Yao, S. et al. (2023). ReAct: Synergizing reasoning and acting in language models. ICLR.
- Yao, S. et al. (2023). Tree of Thoughts: Deliberate problem solving with large language models. NeurIPS.
- Zhou, S. et al. (2024). WebArena: A realistic web environment for building autonomous agents. ICLR.

### Source-manifest additions used as current context

- Active Causal Experimentalist (ACE): Learning intervention strategies via direct preference optimization. arXiv:2602.02451.
- CausaLab: A scalable environment for interactive causal discovery toward AI scientists. arXiv:2605.26029.
- Causal-JEPA: Learning world models through object-level latent interventions. arXiv:2602.11389.
- Cross-model transferability among LLMs on platonic representations of concepts. arXiv:2501.02009.
- Geometric Deep Learning: Grids, Groups, Graphs, Geodesics, and Gauges. arXiv:2104.13478.
- The Geometry of Consciousness, Webb and Miolane Long Now transcript, archived in references.
- Neural networks provably learn spectral representations for group composition. arXiv:2606.02993.
- Persona Vectors: Monitoring and controlling character traits in language models. arXiv:2507.21509.
- The Platonic Representation Hypothesis. arXiv:2405.07987.
- Representations of geometric shapes have syntactic structure. Journal of Experimental Psychology: General, 2026.
- Why LLMs fail at causal discovery and how interventional agents escape. arXiv:2605.27567.
