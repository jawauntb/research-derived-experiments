# From Prediction to Concern: A Comprehensive Literature Review and Research Synthesis for the Research-Derived Experiments Corpus

## Abstract

This review synthesizes the research-derived experiments corpus as a single interdisciplinary program about minimal agency, representation, uncertainty, and meaning. It integrates the local corpus audit, the stored-paper PDF review, and the external citation enrichment pass over the papers' cited literature. The evidential base is deliberately tiered: 60 locally stored PDFs were text-extracted across all pages; 164 atomized outside citation candidates were extracted from our authored papers; 67 of those external candidates were resolved with abstract-level evidence; 3 were resolved with metadata only; 42 were preserved as manual foundational topic seeds; and 52 remain unresolved or malformed bibliography fragments. The review therefore advances a strong but bounded thesis: across machine learning, neuroscience, philosophy of biology, dynamical systems, and geometry, the recurring object is not intelligence as raw predictive success but intelligence as controlled sensitivity to what matters. The program's central invariants are viability, intervention, calibrated uncertainty, boundary maintenance, and transformation-stable representation. The paper builds the argument from first principles, explains the relevant mathematics and theorem families, locates our papers in the surrounding literature, and ends with a research agenda and an explicit unread-source register.

## Status of Evidence

This is the canonical synthesis rewrite, not another audit report. The audits are used as provenance. The exhaustive local audit established what our repository contains: 110 tracked paper source files, 177 extracted citation/reference rows, and 60 tracked PDFs whose pages were all text-extracted. The external enrichment pass then atomized bundled citation rows into 164 external/reference candidates and resolved 67 with abstracts.

The paper uses three evidence labels:

- Full local corpus support: claims grounded in our authored papers or PDFs stored in the repository.
- Abstract-level external support: claims grounded in resolved outside sources whose abstracts or scholarly metadata were read.
- Bibliography-repair support: claims supported only as topic seeds because the exact source was unresolved, malformed, or not yet full-read.

The last category is intentionally visible. A literature review that hides unread sources becomes rhetorically smooth and scientifically weak. A stronger review states what has been read, what has been inferred, and what must be repaired before publication.

## First Principles: The Minimum Vocabulary

The whole program can be built from six elementary ideas.

First, a system has state. State is the collection of variables needed to describe what the system can do next. A thermostat, a cell, a neural network, a language-model agent, and a person differ enormously, but each can be described as a state-changing process coupled to an environment.

Second, an environment is not just an input stream. It is the set of external conditions that constrain the system's future states. Once a system can act, the environment is no longer merely observed. It is partly sampled, changed, avoided, simplified, or exploited.

Third, prediction is not the same as agency. Prediction asks what will happen. Agency asks which futures remain possible, which variables are preserved, which interventions are chosen, and which errors cause repair. A passive predictor can be accurate without caring which world obtains. An agent, even a minimal one, is organized around consequences.

Fourth, information has value only relative to use. A signal is useful if it changes the action, representation, boundary, or future experiment in a way that matters. This is why uncertainty appears throughout the corpus: uncertainty is not merely a defect in knowledge but a control variable that decides whether to probe, update, defer, or disengage.

Fifth, representation is compression with consequence. A representation is not better because it contains more bits. It is better when it preserves distinctions that matter for intervention, prediction, viability, explanation, or transfer. Causal representation learning, geometric deep learning, active inference, and ecological perception all converge on this point from different directions.

Sixth, meaning is not raw symbol manipulation. In the tradition running through Ashby, Gibson, Uexkull, Maturana and Varela, Di Paolo, Thompson, Levin, Bennett, and Vervaeke, meaning arises when differences in the world are organized relative to a situated system's possible action, viability, relevance, and repair. This does not license sloppy claims about machine consciousness. It licenses operational questions: what does the system maintain, what can disturb it, what does it notice, and what does it do when its world model fails?

## The Central Thesis

The corpus is best understood as a research program on concern-like structure in minimal agents. "Concern" here should not be read as a private feeling or anthropomorphic projection. It names a functional pattern: a system has concern-like organization when some variables are treated as viability-relevant, when perturbations to those variables alter action or inquiry, when representations preserve self/world or object/action distinctions needed for control, and when the system reengages after world change rather than merely optimizing a static reward proxy.

This thesis is deliberately weaker than "machines understand" and stronger than "models predict tokens." It says that between raw prediction and human understanding there is a large, scientifically tractable middle territory: systems that maintain boundaries, allocate attention, value information, form intervention-sensitive representations, and generalize by preserving invariants.

## Literature Foundations by Field

### Machine Learning: Identifiability, Generalization, and Agent Evaluation

The ML literature supplies both the constructive methods and the warning labels. Locatello et al.'s disentanglement result blocks a naive fantasy: unsupervised learning does not automatically recover human-interpretable factors. Without inductive bias, supervision, interaction, or structural assumptions, many latent coordinate systems explain the same observations. This matters for our corpus because many of our papers ask whether an internal variable is "really" agency-relevant. The literature says that observational fit is insufficient.

Causal representation learning supplies the constructive alternative. Scholkpf et al. frame the intersection of causality and representation learning as a path toward variables that support transfer, intervention, and explanation. Brehmer et al. show that weakly supervised interventional pairs can help identify causal variables and structure. ACE, CausaLab, object-centric causal world models, and causal-JEPA-style work extend the same intuition: agents must learn not only what co-occurs but what changes when something is done.

OOD generalization and shortcut-learning work add the negative discipline. Invariant Risk Minimization, domain-generalization surveys, WILDS-style benchmark thinking, underspecification, shortcut learning, goal misgeneralization, and group DRO all show that success on a training distribution can be misleading. A model may learn a shortcut that works locally and fails under the shift that reveals the intended structure. Our corpus should therefore measure transfer across interventions and environmental changes, not merely in-distribution reward or prediction.

The modern agent-evaluation literature contributes a second warning. ReAct, Toolformer, Reflexion, Voyager, WebArena, OSWorld, SWE-bench, AgentBench, HELM, and related benchmarks show that tool use and language reasoning are not enough by themselves. Realistic agency requires state tracking, feedback use, repair after error, environment coupling, and long-horizon action. These benchmarks motivate our insistence on interventions, reengagement, and proxy resistance.

### Uncertainty and Inquiry: When Information Is Worth Action

The corpus repeatedly returns to the same practical question: when should a system ask, probe, sample, or intervene? Active learning, BALD, Bayesian active learning for classification and preference learning, dropout as Bayesian approximation, deep ensembles, Kendall and Gal's uncertainty taxonomy, epistemic neural networks, and calibrated uncertainty all treat uncertainty as actionable. The key distinction is epistemic versus aleatoric uncertainty. Epistemic uncertainty can in principle be reduced by information; aleatoric uncertainty reflects irreducible noise.

Probe-value papers in the corpus use this distinction to reinterpret attention. Attention is not just focusing on salient input. It is allocating costly measurement toward variables whose resolution would change action or model structure. Habituated reengagement extends the idea: a system may rationally stop responding to a repeated signal while preserving the capacity to detect when the signal becomes newly informative.

### Neuroscience and Active Inference: Detection Is Not Response

The neuroscience-adjacent literature is important because it prevents an overly simplistic ML picture. Biological systems often decouple detection from action. Habituation, refractory periods, sensory adaptation, precision weighting, and active inference all distinguish the availability of a signal from the choice to act on it.

Active inference and the free-energy principle supply a formal vocabulary for this coupling. They frame perception and action as attempts to minimize expected free energy through prediction, precision allocation, and policy selection. In the corpus, this is not used as an all-purpose explanation. It is used more narrowly: as a way to understand when an agent should attend, when information has expected value, and when reengagement is warranted after a change in the world.

### Philosophy and Biology: Meaning, Normativity, and the Organism-Relative World

The philosophical and biological citations provide conceptual discipline. Ashby's cybernetics, Canguilhem's normativity, Gibson's affordances, Uexkull's Umwelt, Jonas's organismic value, Maturana and Varela's autopoiesis, Di Paolo's adaptivity, Thompson's mind-in-life tradition, Levin's TAME framework, Bennett's work on meaning, and Vervaeke's relevance realization all converge on a central point: meaning is not merely an external semantic label. It is a relation between a system, its possible actions, and the differences that matter for its continued organization.

This is the deepest reason "concern" is a useful term if handled carefully. Concern is not assumed to be conscious feeling. It is the low-level organization by which a system treats some state differences as worth regulating, preserving, explaining, or investigating. The philosophical literature tells us to avoid reducing this to reward alone; the ML literature tells us to make it measurable anyway.

### Geometry, Symmetry, and Compression

Geometric deep learning, group-equivariant networks, equivariance discovery, neural-kernel symmetry theory, representation learning for geometric trees, and related work show that generalization often depends on respecting structure. If a task is invariant under translation, rotation, permutation, object exchange, or role relabeling, a good representation should not relearn the task from scratch under each transformed copy.

This connects to the corpus's geometry papers and weakness/OOD papers. A representation that captures the right symmetry has fewer arbitrary degrees of freedom. It can compress without losing what matters. MDL, algorithmic probability, simplicity-bias work, grokking, flat-minima debates, and low-entropy Boolean-function bias give a second lens on the same theme: generalization is partly about which functions are easier, shorter, or more structurally natural for a learner to represent. But compression alone is not enough. The compression must preserve intervention-relevant variables.

## Cross-Field Invariants

### Invariant 1: Intervention Beats Observation

Across causal representation learning, mediation analysis, causal abstraction, active experimentation, model editing, and our intervention papers, the same rule recurs: passive observation underdetermines structure. Interventions reveal which variables actually do work. In the corpus, this becomes a methodological demand. If a latent is claimed to represent self, world, concern, agency, or causal structure, it should respond correctly when the relevant variable is perturbed.

### Invariant 2: Detection and Action Must Be Separable

Habituation, refractory periods, active learning, uncertainty calibration, and probe-value experiments all require this separation. A good system may detect a familiar signal and decline to act. It may also stop acting until a change makes the signal informative again. This invariant is central to the reengagement papers.

### Invariant 3: Viability Is a Constraint, Not Just a Reward

Viability theory, autopoiesis, TAME, active inference, empowerment, and homeostatic control all distinguish viability constraints from scalar rewards. A reward can point anywhere. A viability constraint says that some region of state-space must be preserved or recovered. This gives a more robust interpretation of concern-like behavior than reward maximization alone.

### Invariant 4: Boundary Maintenance Is Dynamic Coupling

The self/world boundary is neither a metaphysical wall nor a mere label. It is a regulated interface. Agents preserve a distinction between internal and external state while remaining coupled to the environment through sensors, actions, and latent models. The boundary can be tested by perturbing body variables, world variables, and action consequences separately.

### Invariant 5: Invariance and Equivariance Are the Geometry of Trust

OOD generalization asks what remains true under distribution shift. Geometry asks how representations should transform under symmetry. Philosophy and ecology ask which environmental differences are stable affordances. All are versions of the same problem: a system is trustworthy when the relevant structure survives the transformations it should survive and changes under the transformations it should not ignore.

### Invariant 6: Information Has Cost

Active learning, Bayesian experimental design, active inference, and our costly-null-probe papers share a simple intuition: information is not free. A rational system must decide whether the expected value of reducing uncertainty exceeds the cost of acquiring information. This turns attention into an economic and dynamical problem, not merely a salience filter.

### Invariant 7: Proxy Optimization Destroys Naive Metrics

Goodhart's law, underspecification, benchmark gaming, shortcut learning, and safety benchmark failures all warn that a proxy stops being faithful when optimized too directly. Any metric for concern, agency, meaning, or intelligence must therefore be accompanied by countermetrics, ablations, distribution shifts, and adversarial controls.

## Theorem and Proof Map

### No-Free-Lunch and Underspecification

Fields: statistical learning theory, decision theory, benchmark methodology.

Core idea: no finite dataset uniquely determines the correct rule for all future cases without assumptions. Many hypotheses fit the same observations. Underspecification is the modern ML version: many trained models can perform similarly on standard validation data while relying on different internal mechanisms.

Intuition: if two maps agree on the roads you have driven but differ elsewhere, your travel history alone cannot tell you which map is globally correct.

Relevance: our papers should never infer agency-relevant structure from performance alone. They need perturbation, transfer, and mechanistic tests.

### Disentanglement Impossibility

Fields: representation learning, latent-variable modeling, identifiability theory.

Core idea: without inductive biases or supervision, unsupervised learning cannot guarantee recovery of the intended independent factors. There are too many equivalent latent coordinate systems.

Intuition: rotating or warping a latent space may preserve the observations while destroying the human-interpretable axes.

Relevance: the corpus's latent probes need interventions, labels, environment changes, or architectural assumptions. Otherwise a "self" or "concern" coordinate may be a convenient fiction.

### Causal Representation Identifiability

Fields: causal inference, nonlinear ICA, representation learning, structural causal models.

Core idea: interventions or weakly supervised interventional pairs can reduce ambiguity about latent causal variables. The causal variables become more identifiable when the learner sees what changes under controlled disturbance.

Intuition: watching shadows is ambiguous; moving the lamp or object reveals the hidden structure.

Relevance: our intervention papers should be treated as attempts to make latent agency variables identifiable rather than merely correlated with reward.

### Invariant Risk Minimization

Fields: statistical learning, causal inference, OOD generalization.

Core idea: causal predictors tend to remain predictive across environments, while spurious correlates often vary. Learning invariants across environments can support out-of-distribution transfer.

Intuition: if a cue works only in one room, it is probably wallpaper; if it works across rooms, it may be structure.

Relevance: concern-like and agency-like variables should remain explanatory under controlled environment changes.

### Group Equivariance and Geometric Deep Learning

Fields: group theory, harmonic analysis, differential geometry, graph theory, deep learning.

Core idea: when data has symmetries, a model can be built so that transformations of the input produce predictable transformations of the representation or output.

Intuition: rotating an object should not force the model to rediscover objecthood from scratch.

Relevance: self/world boundaries, role-specific variables, and object-level causal states should transform predictably under the symmetries of the task.

### Viability Theory

Fields: dynamical systems, control theory, differential inclusions, mathematical biology.

Core idea: the viability kernel is the set of states from which a system can remain within acceptable constraints under available controls and disturbances.

Intuition: agency is not just moving toward reward; it is keeping enough future open to avoid falling outside the living or operating region.

Relevance: concern can be operationalized as preserving, returning to, or expanding a viability region.

### Variational Free Energy and Active Inference

Fields: variational inference, information theory, theoretical neuroscience, control.

Core idea: exact inference and control are hard; systems can optimize tractable bounds that couple prediction error, uncertainty, and policy selection.

Intuition: perception and action are two sides of reducing uncertainty about the causes of sensation and the consequences of action.

Relevance: probe value, attention, and reengagement can be modeled as expected information gain under cost.

### BALD and Bayesian Experimental Design

Fields: Bayesian statistics, active learning, information theory.

Core idea: a query is valuable when it is expected to reduce uncertainty about the model or hypothesis class, not merely when the current prediction is uncertain.

Intuition: the best question is the one whose answer would actually change your mind.

Relevance: costly probes should be triggered by expected epistemic value, not by novelty or error alone.

### Empowerment

Fields: information theory, reinforcement learning, control.

Core idea: empowerment measures how much an agent's actions can influence distinguishable future states.

Intuition: an agent is more empowered when its choices reliably open different futures.

Relevance: preserved option value is one measurable dimension of minimal agency.

### Minimum Description Length and Algorithmic Probability

Fields: information theory, algorithmic information theory, statistical model selection.

Core idea: among models that explain the data, shorter descriptions often capture reusable structure rather than noise.

Intuition: a compact rule that keeps working after perturbation is more plausible than a giant lookup table.

Relevance: simplicity helps explain generalization only when the compressed variables preserve causal and action-relevant distinctions.

### Goodhart's Law

Fields: economics, measurement theory, optimization, AI safety.

Core idea: when a measure becomes a target, it can cease to be a good measure.

Intuition: optimizing the scoreboard can decouple the score from the game.

Relevance: every metric in the corpus needs stress tests, countermetrics, and proxy-resistance checks.

## Synthesis of Our Papers

The early geometry and weakness papers ask when learned representations generalize beyond the training distribution. Their best interpretation after the citation review is not merely "flatness matters" or "simplicity matters." It is that the learner's parameter-function map, structural biases, symmetries, and environment changes jointly determine which functions are easy to learn and which transfer.

The concern and planning papers move from representation to action. They ask whether a system's behavior changes when viability-relevant variables are perturbed. The outside literature suggests that this should be framed through viability, empowerment, active inference, and causal intervention rather than reward alone.

The costly probes, current error calibration, and learning-to-ask papers form the uncertainty spine of the corpus. Their natural mathematical home is active learning and Bayesian experimental design. Their philosophical home is Deweyan inquiry: intelligence as situated correction under uncertainty.

The self/world and role-specific identifiability papers ask whether a system can separate its own action-relevant state from environmental structure. The literature says this requires interventions, not mere observation, and should be tested through body/world swaps, causal perturbations, and symmetry-respecting transformations.

The habituated reengagement papers are among the clearest bridges between neuroscience and ML. They operationalize the distinction between sensing and responding. The key claim is not that artificial agents literally habituate like organisms, but that a decision-layer cooling mechanism can preserve detection while reducing action, and that reengagement after world change is a measurable sign of adaptive inquiry.

The metric-stack and benchmark papers are the methodological culmination. They argue that no single score captures agency. A defensible benchmark must include viability preservation, intervention transfer, uncertainty calibration, boundary stability, OOD robustness, shortcut susceptibility, and proxy resistance.

## What the Literature Changes About the Program

The literature review strengthens the program by narrowing it. The strongest supported claim is not "we discovered machine concern." The stronger, more defensible claim is that concern-like structure can be operationalized as a conjunction of measurable invariants: viability-sensitive control, intervention-sensitive representation, calibrated information seeking, reengagement under world change, and robustness to proxy optimization.

The review also makes the unresolved work sharper. Several foundational areas are currently under-bibliographed in the local papers: exact habituation neuroscience, refractory-period literature, Pearl-style mediation, causal abstraction identifiability, comparator models of sense of agency, formal viability theory, and MDL/Solomonoff foundations. They are not irrelevant; they are precisely the areas where the next full-text pass should be concentrated.

Finally, the review shows that the program's most original contribution is not a single theorem. It is a synthesis constraint: if a system is claimed to have minimal agency, its representation, uncertainty, action, and boundary behavior must cohere under intervention.

## Research Agenda

### Experiment 1: Viability-Kernel Bandits

Construct minimal bandit or gridworld agents where reward conflicts with hidden viability constraints. Test whether learned policies preserve, recover, or sacrifice viability variables under distribution shift. The key ablation removes the viability variable or makes it spuriously correlated with reward.

### Experiment 2: Causal Reengagement After Habituation

Train agents with repeated irrelevant probes, then introduce world changes that make the same probe informative. A good system should reduce action during repetition without losing detection, then reengage when expected information gain rises.

### Experiment 3: Intervention-Identifiability Suite

Use paired interventional samples to test whether latent variables become more causally aligned than observational baselines. Compare passive prediction, contrastive learning, weak supervision, and active intervention policies.

### Experiment 4: Self/World Boundary Swaps

Create environments where body variables, world variables, and action consequences can be independently swapped. Test whether learned boundary representations transform correctly under each manipulation.

### Experiment 5: Proxy-Resistant Agent Benchmarks

Build benchmark tasks where visible reward, hidden viability, and shortcut features can be decoupled. Report not one score but a metric stack: reward, viability, uncertainty calibration, intervention transfer, reengagement latency, and shortcut dependence.

### Experiment 6: Geometry of Concern

Measure whether concern-relevant variables occupy lower-dimensional, symmetry-stable, or more intervention-sensitive subspaces than nuisance variables. Connect this to equivariance, representation rank, and causal abstraction.

## Claim Boundaries

The corpus can claim that minimal agency can be studied through viability, intervention, uncertainty, and invariant representation. It can claim that our experiments instantiate early versions of those tests. It can claim that the outside literature supports this operational framing.

The corpus should not yet claim that these systems have human-like consciousness, intrinsic meaning, or full biological concern. It should not overstate abstract-level citation support as full-text mastery. It should not treat unresolved bibliography fragments as evidence. It should not confuse benchmark performance with mechanism.

## Unread and Unresolved Sources

The unread-source register is a feature, not a defect. It identifies the work still required for publication-grade scholarship. The current register includes three kinds of rows:

- Unresolved external references: citation fragments that the automated pass could not reliably resolve.
- Manual foundational topic seeds: broad references such as habituation, Pearl mediation, CUSUM/Page-Hinkley, active inference, comparator models, or viability theory that need exact bibliographic targets.
- Metadata-only resolved sources: sources with usable bibliographic metadata but without abstract/full-text support in the pass.

These rows are listed in the generated `unread_sources.csv`, `unread_sources.md`, and the PDF appendix.

## Conclusion

The research-derived experiments corpus points toward a mature interdisciplinary thesis: intelligence becomes agency when prediction is organized around viable action, calibrated inquiry, intervention-sensitive representation, and stable boundaries under transformation. ML supplies the tests and failure modes. Neuroscience supplies the action/attention distinction. Philosophy and biology supply the organism-relative account of meaning and normativity. Geometry and dynamical systems supply the invariants.

The next step is not to make the language grander. It is to make the experiments stricter. A PhD-worthy version of this program should turn each philosophical term into a perturbation test, each metric into a proxy-resistance check, and each synthesis claim into a falsifiable benchmark.
