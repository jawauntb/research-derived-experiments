# Prior-art and novelty map

This ledger was drafted before implementation. It narrows the claim rather than
supporting a priority claim.

| Lineage | Existing object or result | Consequence for this project |
|---|---|---|
| Popperian falsification and Lakatosian research programmes | Counterinstances can reject universal claims; scientific programmes also develop constructively | Do not claim that obstruction-first reasoning defines all science |
| Blackwell comparison of experiments | Informativeness is relative to an experiment and decision problem | Do not claim that “available information determines recoverable conclusions” is new |
| Myhill--Nerode and Angluin \(L^\*\) | Indistinguishability classes and counterexamples drive automata minimization and learning | Quotients and counterexample-guided refinement are prior art |
| CEGAR and CEGIS | Verification failures generate counterexamples that refine abstractions or candidate programs | “Counterexample before proof” is an established computational pattern |
| Testing equivalence, bisimulation, and contextual equivalence | Allowed observations determine behavioral equivalence | Observer-relative equivalence is not a new foundation |
| REFUTE | LLMs are benchmarked on constructing counterexamples for subtly incorrect programs | Counterexample-generation benchmarks already exist |
| Failing to Falsify | Interactive hidden-rule tasks measure confirmation bias and benefit from counterexample prompting | Interactive falsification benchmarks already exist |
| DiscoveryWorld, ScienceAgentBench, and SDABench | End-to-end or component-level scientific-discovery agents are already benchmarked | Do not claim the first scientific-discovery benchmark |
| AgentAbstain | Paired impossible/possible agent tasks evaluate abstention and task solving | Impossibility awareness and paired abstention evaluation are already benchmarked |
| FirstResearch | Research-question certificates include assumptions, falsifiers, and minimal decisive tests | Structured falsifier/minimal-test artifacts are already proposed |
| Relative Identifiability package in this repository | Exact finite target factorization, obstruction, refinement, and minimum-family search | Treat the mathematics as the benchmark kernel, not the headline novelty |

## Defensible V0 contribution

The narrow contribution under test is a single executable contract combining:

1. a target-relative terminal obstruction pair checked against a declared
   experiment family;
2. a local-versus-terminal obstruction distinction;
3. matched family enrichments that flip the correct response from certified
   impossibility to recovery;
4. separate accounting for certified recovery, certified impossibility,
   budget exhaustion, lucky overclaiming, and unsupported or unnecessary
   abstention; and
5. a theorem-to-regression format intended for MIDAS.

Any closer precedent narrows this boundary further.

## Primary sources

- D. Blackwell, “Comparison of Experiments,” 1951.
  <https://doi.org/10.1525/9780520411586-009>
- D. Angluin, “Learning Regular Sets from Queries and Counterexamples,”
  *Information and Computation* 75(2), 1987.
  <https://doi.org/10.1016/0890-5401(87)90052-6>
- E. M. Clarke, O. Grumberg, S. Jha, Y. Lu, and H. Veith,
  “Counterexample-Guided Abstraction Refinement,” CAV 2000.
  <https://doi.org/10.1007/10722167_15>
- A. Solar-Lezama, C. G. Jones, and R. Bodík,
  “Sketching Concurrent Data Structures,” PLDI 2008.
  <https://people.csail.mit.edu/asolar/papers/Solar-LezamaJB08.pdf>
- K. Sinha et al., “Can Language Models Falsify? Evaluating Algorithmic
  Reasoning with Counterexample Creation,” 2025.
  <https://arxiv.org/abs/2502.19414>
- S. Jhaveri et al., “Failing to Falsify: Confirmation Bias in LLM-Based
  Scientific Reasoning,” 2026.
  <https://arxiv.org/abs/2604.02485>
- P. Jansen et al., “DiscoveryWorld: A Virtual Environment for Developing and
  Evaluating Automated Scientific Discovery Agents,” NeurIPS 2024.
  <https://proceedings.neurips.cc/paper_files/paper/2024/file/13836f251823945316ae067350a5c366-Paper-Datasets_and_Benchmarks_Track.pdf>
- Y. Chen et al., “ScienceAgentBench: Toward Rigorous Assessment of
  Language Agents for Data-Driven Scientific Discovery,” ICLR 2025.
  <https://proceedings.iclr.cc/paper_files/paper/2025/hash/f12b4df26344f3be803c06b555252efe-Abstract-Conference.html>
- “SDABench: Benchmarking AI Agents for Scientific Data Analysis,” 2026.
  <https://arxiv.org/abs/2607.11079>
- “AgentAbstain: A Benchmark for Abstention in Autonomous Agents,” 2026.
  <https://arxiv.org/abs/2607.10059>
- “FirstResearch: A Benchmark and Training Framework for Evaluating Research
  Question Generation,” 2026.
  <https://arxiv.org/abs/2607.05682>

## Claim-safe thesis

> Counterexample-first reasoning is not the whole of science. It is a missing
> evaluation axis: can an agent recognize and certify when permitted
> experiments do not identify its claim?
