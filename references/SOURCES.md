# Source Manifest

The downloaded PDFs, HTML snapshots, and extracted full text are intentionally local-only and ignored by git. This manifest records the source list used for the first synthesis.

## Papers and Essays

- Persona Vectors: Monitoring and Controlling Character Traits in Language Models: https://arxiv.org/pdf/2507.21509
- Cross-model Transferability among Large Language Models on the Platonic Representations of Concepts: https://arxiv.org/pdf/2501.02009
- The Autopoietic Theorem: https://www.authorea.com/doi/full/10.22541/au.177575355.56499869/v1
- Games between Programs: The Ruliology of Competition: https://writings.stephenwolfram.com/2026/06/games-between-programs-the-ruliology-of-competition/
- Self-Revising Discovery Systems for Science: https://arxiv.org/pdf/2606.01444
- The Platonic Representation Hypothesis: https://arxiv.org/pdf/2405.07987
- Principles and Practice of Deep Representation Learning, or A Mathematical Theory of Memory: https://arxiv.org/abs/2606.06624
- Transformers Are Inherently Succinct: https://openreview.net/pdf?id=Yxz92UuPLQ
- If LLMs Have Human-Like Attributes, Then So Does Age of Empires II: https://arxiv.org/abs/2605.31514
- Is Complexity an Illusion?: https://arxiv.org/abs/2404.07227
- The Machine Consciousness Hypothesis: https://cimc.ai/cimcHypothesis.pdf
- Technological Approach to Mind Everywhere: https://www.frontiersin.org/journals/systems-neuroscience/articles/10.3389/fnsys.2022.768201/full
- On Having No Head: Cognition throughout Biological Systems: https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2016.00902/full
- Alignment Is to a Virtual Governor: A Theory of Coordination in Diverse Intelligence: https://doi.org/10.20944/preprints202607.0220.v1 - Preprints.org version posted 2026-07-03; not peer-reviewed. Useful as terminology and framing for decentralized alignment as a signal architecture that converts global constraint violations into local incentives. On-thesis for the allostatic/self-world/long-horizon lines, but cite only where the paper's "virtual governor" concept is actually used to motivate a mechanism, claim boundary, or limitation.
- Why Muon Outperforms Adam: A Curvature Perspective: https://arxiv.org/abs/2606.04662
- Neural Networks Provably Learn Spectral Representations for Group Composition: https://arxiv.org/abs/2606.02993
- Representations of Geometric Shapes Have Syntactic Structure: https://doi.org/10.1037/xge0001890
- Neural Language of Thought Models: https://arxiv.org/abs/2402.01203
- Active Causal Experimentalist (ACE): Learning Intervention Strategies via Direct Preference Optimization: https://arxiv.org/abs/2602.02451
- CausaLab: A Scalable Environment for Interactive Causal Discovery Toward AI Scientists: https://arxiv.org/abs/2605.26029
- Why LLMs Fail at Causal Discovery and How Interventional Agents Escape: https://arxiv.org/abs/2605.27567
- Latent State Design for World Models under Sufficiency Constraints: https://arxiv.org/abs/2605.01694
- Causal-JEPA: Learning World Models through Object-Level Latent Interventions: https://arxiv.org/abs/2602.11389
- HCLSM: Hierarchical Causal Latent State Machines for Object-Centric World Modeling: https://arxiv.org/abs/2603.29090
- Structuring Open-Ended NAS: Semi-Automated Design Knowledge Structuring with LLMs for Efficient Neural Architecture Search: https://arxiv.org/abs/2605.19247
- Representation Learning of Geometric Trees: https://arxiv.org/abs/2408.08799
- Compositional Neuro-Symbolic Reasoning: https://arxiv.org/abs/2604.02434
- Inducing Causal World Models in LLMs for Zero-Shot Physical Reasoning: https://arxiv.org/abs/2507.19855
- Object centric architectures enable efficient causal representation learning: https://openreview.net/forum?id=r9FsiXZxZt
- Object-Centric World Models for Causality-Aware Reinforcement Learning: https://arxiv.org/abs/2511.14262
- CausalARC: Abstract Reasoning with Causal World Models: https://arxiv.org/abs/2509.03636

## Talks and Transcripts

- The Geometry of Consciousness — Claire Webb & Nina Miolane (Long Now Talk): https://longnow.org/talks/02026-webb-miolane/ — full transcript archived at [webb-miolane-geometry-of-consciousness-transcript.md](webb-miolane-geometry-of-consciousness-transcript.md) (committed; user-provided paste). On-thesis: biological brains and trained artificial networks independently converge on the same geometric structures (torus of spatial navigation, ring of head direction); the Geometric Intelligence Lab program aims at a "mathematical theory of intelligence" (Kepler-observes / Newton-explains) via Fourier decomposition of space, with reward-driven metric deformation and sleep-state geometry as consciousness correlates.

## Neuroscience & External Sources

- **Function Shapes Structure — Lichtman lab, *Nature Neuroscience* (2026)** (Harvard MCB news writeup): https://www.mcb.harvard.edu/department/news/two-decades-study-reveals-how-brain-function-shapes-its-own-structure/ — PDF local-only at `references/papers/lichtman_function_shapes_structure_2026.pdf` (user-provided; text at `references/text/`). ~20-year developmental-connectomics study of the neuromuscular junction (Brainbow + EM). Core finding: **neural function generates structure** — activity from planned movements is present *before* the target circuitry forms and shapes how it wires, reversing the usual "structure explains function" framing. Gives a concrete biological mechanism for "neurons that fire together wire together": synchronous firing preserves connections, mistimed activity is pruned, at single-synapse and circuit levels; includes long-distance (up to 1 mm) NMJ competition via propagating action potentials whose collision/timing decides survival, and developmental efficiency via removal of redundant connections. **On-thesis (active geometry / Paper B):** the biological, causal counterpart of "concern/function deforms representational structure" — where Paper B shows a value signal warps a learned code's induced metric, this shows activity literally sculpts the wiring; the timing-based pruning-for-efficiency is a weakness/compression-style dynamic and an autopoietic self-shaping process.

## AI Science & Methodology

- **Position: The Age of AI Agents Demands a New Scientific Paradigm to Sustain Trustworthy Science** — Belinda Mo, ICML 2026 (Long Horizon Research). PDF local-only at `references/papers/mo_ai_agents_trustworthy_science_2026.pdf` (text at `references/text/`). Argues that autonomous research agents widen the *verification gap* (output vs. our ability to check it) by magnitudes, breaking science's social backstops. Proposes verification infrastructure built on three pillars: **observable-by-default workflows, scalable verification, and clear attribution**, against three failure modes — observability (can we see what happened?), attribution (who is responsible?), reproducibility (can we verify?). **Directly relevant to this repo:** its experiments are agent-generated, so the repo should be observable-by-default (pre-registration, committed result reports, gitignored raw + committed summaries, unit tests pinning results, honest negatives — mostly already in place) with explicit provenance/attribution per experiment. Motivates a lightweight per-experiment verification/provenance card (generator + model, exact command/seed/config, gates verified, raw-vs-summary, limitations).
- **Execution-grounded evaluation** — Bai et al., “The Story is Not the Science” (ICML 2026 AI4Science workshop): https://openreview.net/forum?id=cmXVfGR44k — supports checking code, data, and experimental process rather than narrative alone; treated as a bounded workshop result, not proof that automated review is sufficient.
- **Preregistration** — Nosek et al., “The Preregistration Revolution,” PNAS 2018: https://doi.org/10.1073/pnas.1708274114 — used to preserve the prediction/postdiction distinction and immutable original gates.
- **Bootstrap** — Efron, “Bootstrap Methods: Another Look at the Jackknife,” Annals of Statistics 1979: https://doi.org/10.1214/aos/1176344552 — source for resampling under an explicit sampling model; does not justify treating resamples as new independent runs.
- **Small-sample design** — Gelman & Carlin, “Beyond Power Calculations,” 2014: https://doi.org/10.1177/1745691614551642 — motivates Type-S/Type-M and precision simulation rather than a universal seed floor.
- **Analytic robustness** — Silberzahn et al., “Many Analysts, One Data Set,” 2018: https://doi.org/10.1177/2515245917747646 — motivates blinded independent analysis paths for theory-changing results.
- **PAC-Bayes-kl bound** — Langford & Seeger, “Bounds for Averaging
  Classifiers” (2001): http://reports-archive.adm.cs.cmu.edu/anon/2001/CMU-CS-01-102.pdf;
  Seeger, “PAC-Bayesian Generalisation Error Bounds for Gaussian Process
  Classification” (2002): https://www.jmlr.org/papers/v3/seeger02a.html; and
  Maurer, “A Note on the PAC Bayesian Theorem” (2004):
  https://arxiv.org/abs/cs/0411099 — sources for the bounded-loss
  PAC-Bayes-kl inequality used in the weakness complexity sketch.
- **Invariance and PAC-Bayes** — Lyle et al., “On the Benefits of Invariance in
  Neural Networks” (2020): https://arxiv.org/abs/2005.00178; Beck & Ochs,
  “Symmetries in PAC-Bayesian Learning” (2025):
  https://arxiv.org/abs/2510.17303 — prior work showing that symmetry-aware
  restriction or symmetrization can reduce PAC-Bayes complexity; cited as
  related theory, not evidence that this repo's weakness metric already yields a
  nonvacuous neural bound.
- **Nonvacuous neural PAC-Bayes** — Dziugaite & Roy, “Computing Nonvacuous
  Generalization Bounds for Deep (Stochastic) Neural Networks with Many More
  Parameters than Training Data” (UAI 2017):
  https://arxiv.org/abs/1703.11008 — motivates the withheld neural perturbation
  test and the requirement to report numerical nonvacuity rather than analogy.

## Philosophy of Mind, Content, and Kinds

- **Structuring versus triggering causes** — Fred Dretske, *Explaining Behavior* (1988): https://mitpress.mit.edu/9780262540612/explaining-behavior/ — sharpens availability versus causal use; it does not make arbitrary activation patches valid structuring-cause tests.
- **Biosemantics and proper function** — Ruth Garrett Millikan, “Biosemantics” (1989): https://doi.org/10.2307/2027123 and “In Defense of Proper Functions” (1989): https://doi.org/10.1086/289488 — motivates producer/consumer, normal-use, malfunction, and misrepresentation controls for “objects from concern.”
- **Homeostatic property-cluster kinds** — Richard Boyd, “Homeostasis, Species, and Higher Taxa” (1999 draft): https://www.joelvelasco.net/teaching/systematics/boyd%2099%20-%20Homeostasis%20Species%20and%20Higher%20Taxa%20%28draft%29.pdf — distinguishes projectible, mechanism-maintained clusters from useful experimenter labels.
- **Real patterns** — Daniel Dennett, “Real Patterns” (1991): https://doi.org/10.2307/2027085 — motivates rival-pattern, compression, and held-out prediction tests for model-relative realism.
- **Self-model theory** — Thomas Metzinger, *Being No One* (2003): https://mitpress.mit.edu/9780262633086/being-no-one/ — informs computational self-model comparisons while reinforcing the firewall against phenomenal-self claims.

## Local User-Provided Files

These remain local-only:

- `/Users/jawaun/Downloads/Thesis_Revision_1-9 (1).pdf`
- `/Users/jawaun/Downloads/autopoietic_theorem.pdf`
- `/Users/jawaun/Downloads/There_is_no_self_evidence.pdf`
- `/Users/jawaun/Downloads/2027-43747-005.pdf`
- `/Users/jawaun/Metaphysics of Intelligence/dynamical_ontologies_blueprint.pdf`
- `/Users/jawaun/Metaphysics of Intelligence/Maintained_Concern_Axioms_for_Meaning_Self_and_Epistemic_Action_fixed.pdf`
- `/Users/jawaun/Downloads/preprints202607.0220.v1.pdf`
