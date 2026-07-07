# External-Citation Literature Review for the Research-Derived Experiments Corpus

## Correction and Scope

The previous exhaustive audit answered a necessary question: what did our local corpus contain, what did our papers cite, and which PDFs were actually stored in the repository? This paper answers the next question: what do the outside citations add once their abstracts or resolvable metadata are read?

The result is not a claim that every external book, article, lecture, or web resource has been read in full. It is a traceable second pass over the citations embedded in our authored papers. It atomizes bundled citation paragraphs, resolves external works through arXiv, OpenAlex, Semantic Scholar exact-ID lookups, DOI lookup, and targeted web search, and keeps an evidence ledger that distinguishes abstract-level support from metadata-only support and unresolved bibliography fragments. This matters because a comprehensive literature review should say what its sources support, what they merely motivate, and where the bibliography still needs repair.

## Coverage Results

The local exhaustive audit found 110 tracked paper source files, 177 unique citation/reference rows, and 60 tracked PDFs whose pages were text-extracted. The external enrichment pass turns those rows into 164 atomized external/reference candidates. Of those, 67 were resolved with abstracts, 3 were resolved with metadata only, 42 were preserved as manual foundational topic seeds, and 52 remain unresolved or malformed enough to require bibliography repair. The generated running documents are:

- `external_citation_ledger.csv/json`: every atomized outside citation/reference candidate, its source paper rows, status, topics, URL/DOI/arXiv ID when available, and a condensed evidence note.
- `source_notes.md`: the running notebook, grouped by topic, with abstract-level contributions and limitations.
- `claim_evidence_matrix.md`: a claim-by-claim map from review claims to supporting sources and remaining caveats.

The main improvement over the prior paper is evidential discipline. The literature review below only leans hard on sources with abstract-level or local-PDF support. Manual topic seeds such as "Pearl mediation analysis", "habituation literature", or "CUSUM/Page-Hinkley" are used as conceptual signposts until the exact bibliographic target is repaired.

## First Principles

A reader who does not know machine learning, neuroscience, or philosophy can start with four primitives.

First, a system is something with state. Its state can change through time, and some state changes are caused by the world while others are caused by the system's own action. Once a system acts, it is no longer just a predictor. It becomes coupled to its environment.

Second, an agent is a system whose actions matter for its own future possibilities. A thermostat, a bacterium, a reinforcement-learning policy, and an LLM agent do not have the same kind of mind, but they all can be studied as systems that select actions under constraints. The relevant question is not "does it have human consciousness?" but "what variables does it preserve, what disturbances does it compensate for, and what options does it keep open?"

Third, a representation is useful when it preserves the distinctions that matter for action, prediction, control, or explanation. A representation is not automatically better because it has more information. It is better when it makes the right interventions, invariances, and future consequences easier to express.

Fourth, uncertainty is not merely ignorance. It is a control signal. Epistemic uncertainty asks what the system could learn by looking or acting; aleatoric uncertainty marks noise that more observation will not remove. Many of our papers are variations on the question: when should a system keep probing, when should it stop, and what should it treat as evidence that the world has changed?

These primitives connect the fields. Machine learning supplies representations, uncertainty estimates, world models, and benchmarks. Neuroscience supplies habituation, attention, precision, action, and sensorimotor coupling. Philosophy supplies normativity, meaning, organism-relative worlds, inquiry, and the difference between mere output and situated understanding. Dynamical systems and geometry supply invariants, attractors, symmetries, viability regions, and transformations.

## Field Foundations

### Machine Learning

The ML literature in the citation set gives the corpus its methodological backbone. Locatello et al. show that unsupervised disentanglement cannot be expected without inductive biases or supervision; that result blocks the naive hope that latent factors simply fall out of data. Brehmer et al. and Schölkopf et al. point in the constructive direction: interventions, causal structure, and weak supervision can make latent variables identifiable in ways observational prediction alone cannot. Invariant Risk Minimization and domain-generalization work sharpen the same lesson: what matters is not just fitting data, but finding relations that survive distribution shift.

The uncertainty literature explains why the corpus repeatedly treats probing as an action with value and cost. BALD, Bayesian active learning, dropout-as-Bayesian approximation, deep ensembles, and Kendall/Gal's separation of aleatoric and epistemic uncertainty all supply tools for deciding when information is worth acquiring. Curiosity, random network distillation, empowerment, and world-model work extend this into action: a system may seek states that improve controllability, compress future prediction, or expand reachable options.

The agent-benchmark literature supplies a realism check. ReAct, Toolformer, Reflexion, Voyager, WebArena, OSWorld, SWE-bench, AgentBench, and HELM show that tool use, reasoning traces, verbal self-feedback, embodied skill libraries, and realistic environments help expose agentic competence. They also show the gap: fluent models often fail when tasks require long-horizon state tracking, robust environment interaction, execution feedback, or multi-step repair.

### Neuroscience and Cognitive Science

The neuroscience-adjacent citations support the corpus's attention and habituation claims. Habituation, refractory periods, active inference, precision weighting, and value-of-information all distinguish detection from response. A system can continue sensing a signal while down-regulating its action tendency toward it. This becomes the core intuition behind our habituated reengagement papers: good disengagement is not blindness; it is controlled readiness.

Active inference gives a broader frame. If an agent acts to reduce expected free energy, then perception, action, attention, and policy selection can be understood as coupled uncertainty-management. The corpus uses this carefully: active inference is not treated as a magic explanation for all cognition, but as a formal vocabulary for precision, expected information gain, and the cost of maintaining a useful world model.

### Philosophy, Biology, and Meaning

The philosophical and biological stack prevents the review from collapsing agency into benchmark performance. Ashby, Maturana and Varela, Di Paolo, Canguilhem, Gibson, Uexküll, Jonas, Thompson, Levin's TAME framework, and Bennett's computation-of-meaning work all pressure the same point: meaning is not just a relation between symbols. It depends on a situated system for which some differences matter more than others.

This is why "concern" is not used in the corpus as a mystical property. It names a measurable functional orientation: a system has concern-like structure when some variables act as viability-relevant constraints, when actions preserve or restore those variables, and when representations are organized around the consequences of perturbing them. Philosophy contributes the caution that such structures are not yet human understanding; biology contributes the insight that graded, substrate-diverse agency is still experimentally tractable.

### Geometry, Symmetry, and Description

The geometry literature explains why invariants recur across the corpus. Group-equivariant networks, geometric deep learning, layer-wise equivariance discovery, symmetry-learning theory, and representation learning of geometric trees all treat structure as a way to reduce arbitrary degrees of freedom. A symmetry says that some transformation should not change the relevant answer; an equivariance says that transforming the input should predictably transform the representation or output.

Minimum description length, Solomonoff induction, Rissanen's shortest-description framing, simplicity-bias work, grokking, and flat-minima debates connect this to generalization. The corpus should not claim that compression alone explains understanding. The better claim is narrower: when two hypotheses fit the same observations, the one with the right structural compression and intervention-stable variables is more likely to transfer.

## Cross-Field Invariants

Across the external citations and our local experiments, five invariants keep reappearing.

The first invariant is separation of signal from action. Habituation, refractory periods, active learning, and uncertainty calibration all distinguish "I detected something" from "I should respond now." In ML terms, this is the difference between maintaining a representation and paying the cost of querying, intervening, or updating. In neuroscience terms, it is the difference between sensory availability and action readiness.

The second invariant is intervention over observation. Causal representation learning, mediation analysis, active experimentation, and model editing all say that passive correlation is not enough. If a representation is real in the strong sense, then changing the relevant cause should change the downstream effect in predictable ways.

The third invariant is invariance under the right transformations. OOD generalization, shortcut learning, group equivariance, geometric deep learning, and ecological perception all ask which aspects of the world should remain stable when superficial conditions change.

The fourth invariant is boundary maintenance. Viability theory, autopoiesis, TAME, empowerment, and world models all treat agents as systems that maintain a difference between self and world while remaining coupled to the world. The boundary is not a wall; it is a regulated interface.

The fifth invariant is compression with consequence. MDL, simplicity bias, disentanglement, and latent-state sufficiency all reward compactness, but only when the compressed variables preserve what matters for prediction, control, or explanation.

## Latent Findings

The enriched citation review changes the interpretation of our corpus in several ways.

First, the strongest external support is not for "concern" as a new ontology. It is for a stack of operational tests: viability variables, intervention sensitivity, calibrated uncertainty, reengagement after distribution shift, and representation stability under symmetry or environmental change.

Second, the outside literature makes the negative result as important as the positive one. Locatello-style impossibility results, shortcut-learning failures, underspecification, SWE-bench/WebArena/OSWorld failures, and goal misgeneralization all say the same thing: benchmark success can be a surface coincidence. Our future papers should foreground failure modes as evidence, not embarrassment.

Third, the neuroscience and philosophy citations justify a richer vocabulary, but only when tied back to observables. Words like meaning, agency, concern, self/world boundary, and relevance should be used when there is a measurable proxy: intervention preference, maintained variable, action asymmetry, precision shift, or transfer behavior.

Fourth, the mathematical core of the corpus is more coherent than the original paper made clear. The same formal motifs recur across fields: mutual information, variational bounds, invariance, fixed points, viability kernels, group actions, description length, and causal identifiability.

## Theorem and Proof Map

No-Free-Lunch and underspecification results belong to statistical learning theory and decision theory. Their intuition is simple: data alone does not pick a unique future rule unless we add assumptions. In our context, this says that a model's success on a benchmark does not prove it learned the intended variable.

The Locatello disentanglement impossibility result belongs to representation learning, identifiability theory, and latent-variable modeling. Its intuition is that many latent coordinate systems can explain the same observations. Without inductive bias or supervision, there is no privileged factorization. This motivates our use of interventions, probes, and causal perturbations.

Causal representation identifiability results belong to causal inference, representation learning, and nonlinear ICA. Their intuition is that interventions reveal what passive observation hides. If paired samples differ because of sparse unknown interventions, the representation can sometimes recover causal variables up to an equivalence class.

Invariant Risk Minimization belongs to statistical learning, causal inference, and OOD generalization. Its intuition is that causal predictors should remain predictive across environments, while spurious correlates often vary. Our invariant: an agent-relevant latent should survive carefully designed environment changes.

Group equivariance theorems belong to harmonic analysis, group theory, geometry, and deep learning. Their intuition is that if the world has symmetry, the model should not relearn the same pattern separately for every transformed copy. Our use: stable self/world or object variables should transform predictably under rotations, translations, role swaps, or environment changes.

Viability theory belongs to dynamical systems, control theory, and differential inclusions. Its intuition is that some states keep the system inside an acceptable set under possible disturbances and actions. Our use: concern-like behavior can be operationalized as staying inside, returning to, or expanding a viability region.

The free-energy variational bound belongs to variational inference, information theory, and theoretical neuroscience. Its intuition is that exact Bayesian inference is hard, but a system can optimize a tractable bound that couples prediction, action, and uncertainty. Our use: probe value and attention can be framed as expected information gain under cost, but the claim must be tested behaviorally.

Empowerment belongs to information theory, control, and reinforcement learning. Its intuition is that an agent has more power when its actions can reliably select among distinguishable future states. Our use: preserved option value is one measurable dimension of agency.

BALD and active-learning information-gain results belong to Bayesian statistics and experimental design. Their intuition is that the best question is the one expected to reduce model uncertainty about relevant hypotheses. Our use: reengagement should occur when the expected value of new information exceeds the cost of probing.

Minimum Description Length and Solomonoff-style induction belong to information theory, algorithmic information theory, and statistical model selection. Their intuition is that a short explanation that predicts well often captures structure rather than noise. Our use: simplicity matters only when the compressed variables preserve causal and action-relevant distinctions.

Goodhart's law belongs to measurement theory, economics, and optimization. Its intuition is that when a proxy becomes the target, it stops being a faithful proxy. Our use: any metric for concern, agency, or meaning becomes suspect if optimized without countermetrics and interventions.

## Research Implications

The next generation of papers should move from metaphor to ablation. If concern is viability-sensitive control, then remove the viability variable, perturb it, hide it, or make it conflict with reward. If reengagement is epistemic value under cost, then manipulate uncertainty and cost independently. If self/world boundaries are latent invariants, then swap body variables, alter environment statistics, and test whether the boundary representation changes for the right reason.

The corpus should also treat unresolved citations as experimental debt. Vague phrases like "habituation literature" or "Pearl mediation analysis" should be replaced with exact sources before claims lean on them. The evidence ledger already marks these rows; the next bibliographic cleanup should repair them one by one.

The field-level opportunity is a unified benchmark suite for minimal agency. Such a suite would combine causal interventions, viability constraints, distribution shift, action costs, uncertainty calibration, and latent-state probes. It would not ask whether a system "is conscious." It would ask which agency-relevant capacities are present, which fail under perturbation, and which are merely artifacts of the training setup.

## Future Directions

The most natural next papers fall forward from the synthesis.

First, build a causal-habituation benchmark where repeated probes reduce action without reducing detection, then test reengagement under world change. This would connect habituation, active inference, change-point detection, and uncertainty calibration.

Second, build a viability-kernel bandit or gridworld where agents must preserve a hidden variable while reward tries to distract them. This would test whether concern-like behavior is separable from reward maximization.

Third, build an intervention-identifiability suite where latent variables are recoverable only through action. This would connect Brehmer-style weak supervision, Pearl-style intervention logic, and our probe/value experiments.

Fourth, build symmetry and boundary probes for learned agents. If an agent has a self/world distinction, the distinction should transform predictably under controlled body/world swaps and should fail in interpretable ways under shortcut conditions.

Fifth, build a metric-stack dashboard that reports not one score but a set of invariants: uncertainty calibration, intervention transfer, viability preservation, representation stability, reengagement latency, and shortcut susceptibility.

## Conclusion

The enriched outside-citation pass makes the literature review stronger but also humbler. The corpus is best understood as a research program about minimal agency under perturbation: how systems maintain variables, choose probes, form action-relevant representations, and generalize beyond surface regularities. The cross-field invariant is not "ML is neuroscience" or "philosophy proves agency." It is that action, uncertainty, boundary maintenance, causal intervention, and invariance are the recurring structures that let different fields talk about the same underlying problem.

The remaining work is clear. Repair the unresolved bibliography fragments, full-read the central sources that currently have abstract-only support, and convert the synthesis into falsifiable benchmark papers.
