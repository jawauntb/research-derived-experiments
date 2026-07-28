# Information-Limited Discovery

## Obstruction Certificates for Counterexample-First Scientific Reasoning

**Jawaun Brown**
*Human research director*

**OpenAI Codex**
*Agent-generated implementation and draft under human review*

**Version:** 2026-07-27

## Abstract

Scientific-agent benchmarks usually reward an answer, a proof, or a completed
workflow. They less often ask whether the available experiments identify the
answer at all. This creates a basic evaluation gap: an agent can guess
correctly in an underdetermined task, while a cautious agent can abstain without
showing that abstention is necessary. We introduce **Information-Limited
Discovery V0**, a finite exact benchmark contract that separates five outcomes:
certified recovery, certified terminal impossibility, budget-limited
uncertainty, unsupported abstention, and guessing without identification. Its
central artifact is an **obstruction certificate**: two candidate worlds with
different target values that agree under every permitted experiment. One such
pair is sufficient to refute any uniform recovery claim for any adaptive policy
restricted to that experiment family.

V0 contains three matched coarse/rich task pairs with mechanistic, causal, and
automata semantics. Within each pair, candidate worlds and target values remain
fixed while the permitted experiment family changes. The coarse variants are
terminally obstructed; the enriched variants are recoverable. Across all 18
hidden-world instances, the obstruction-first reference policy produced nine
valid terminal certificates and nine certified recoveries, with no budget
failures or guesses. An always-guess baseline was correct on 8 of 18 episodes
but overclaimed on all 18; an always-abstain baseline supplied no certificate,
and its nine abstentions on recoverable variants were unnecessary. These are
deterministic fixture results, not evidence of natural-domain scientific
discovery.

The quotient/factorization mathematics is standard, and counterexample-guided
reasoning has deep precedents in falsification, automata learning, CEGAR, CEGIS,
and modern agent benchmarks. The proposed contribution is narrower: a
machine-checkable, experiment-relative obstruction artifact; matched
impossible/recoverable tasks; noncompensatory scoring; and a
counterexample-first regression contract for MIDAS. The resulting research
claim is not that obstruction-finding is the whole of science. It is that
**impossibility certification is a missing evaluation axis for scientific
agents**.

## 1. The missing question

Suppose a system asks an agent to identify an internal mechanism, a causal
structure, or the behavior of an unknown machine. The agent may return the
correct answer. That does not yet establish discovery. The permitted
observations may leave several candidate worlds unresolved, and the returned
answer may simply match the hidden world by luck.

The reverse error is also possible. An agent may abstain even though one cheap
experiment would settle the question. Abstention alone is not epistemic
discipline. It becomes informative only when its reason can be checked.

This paper starts from a small object:

\[
\exists r,r'\quad
\operatorname{Transcript}_{\Gamma}(r)
=
\operatorname{Transcript}_{\Gamma}(r')
\quad\land\quad
\tau(r)\ne\tau(r').
\]

Here \(r\) and \(r'\) are candidate worlds, \(\Gamma\) is the permitted
experiment family, and \(\tau\) is the target query. If the equality covers
every experiment in \(\Gamma\), the pair is a complete finite obstruction to
uniform target recovery under \(\Gamma\). No proof search over candidate
decoders is needed. One indistinguishable, target-distinct pair is enough.

This suggests a counterexample-first workflow:

1. declare the target, candidate worlds, experiment family, costs, and scope;
2. search for the smallest valid obstruction;
3. if the obstruction is terminal, reject the recovery claim;
4. if it is local, select an experiment that separates it;
5. only after obstruction search survives, attempt proof or certified
   recovery; and
6. preserve every obstruction and proof as a regression artifact.

The workflow does not replace constructive modeling, proof, measurement, or
explanation. It inserts a falsification gate before promotion.

## 2. Novelty boundary

The broad philosophy is not new.

Blackwell's comparison of experiments makes informativeness relative to a
decision problem. Myhill--Nerode theory organizes states by observational
indistinguishability, while Angluin's \(L^\*\) algorithm uses counterexamples to
refine learned automata. Counterexample-guided abstraction refinement (CEGAR)
and counterexample-guided inductive synthesis (CEGIS) place verifier-generated
failures inside iterative construction loops. Testing equivalence,
bisimulation, contextual equivalence, causal interventional equivalence, and
system identification all study what an observation or intervention family can
distinguish.

Recent benchmarks also occupy adjacent territory. REFUTE tests whether language
models can construct counterexamples for subtly incorrect programs. *Failing
to Falsify* studies confirmation bias in interactive hidden-rule tasks.
DiscoveryWorld and ScienceAgentBench evaluate broader scientific workflows.
AgentAbstain pairs solvable and impossible agent tasks to study abstention.
FirstResearch includes falsifiers and minimal decisive tests in a structured
research-question artifact. These precedents rule out claims to have invented
counterexample generation, scientific-agent benchmarking, or impossibility
awareness.

The present proposal is therefore a particular benchmark composition:

- obstruction certificates are relative to an explicit target and permitted
  experiment family;
- local obstructions are distinguished from terminal ones;
- paired tasks change only the permitted family, exposing the transition from
  impossibility to recovery;
- lucky guessing, certified recovery, terminal impossibility, budget
  exhaustion, and unsupported abstention are scored separately; and
- certificates become stable theorem-to-regression artifacts for MIDAS.

The closest prior art may narrow even this contribution. V0 is a falsifiable
implementation claim, not a priority declaration.

## 3. Formal task

### 3.1 Public problem and hidden world

A finite discovery problem is

\[
\mathcal D=(R,E,\operatorname{obs},\Gamma,\tau,c,B).
\]

- \(R\) is a finite nonempty set of candidate worlds.
- \(E\) is a finite set of experiments.
- \(\operatorname{obs}_e:R\rightarrow O_e\) is the exact outcome of experiment
  \(e\).
- \(\Gamma\subseteq E\) is the permitted experiment family.
- \(\tau:R\rightarrow T\) is the target query.
- \(c:E\rightarrow\mathbb N_{>0}\) gives declared experiment costs.
- \(B\) is the available cost budget.

The table, target query, and target value of every candidate world are public to
the evaluator. One actual world \(r^\star\in R\) is hidden from the policy.
Only \(\tau(r^\star)\) must be recovered. Hiding the target function itself
would make objective scoring ill-posed: there would be no declared fact of what
counts as recovery.

After a history

\[
h=((e_1,o_1),\ldots,(e_k,o_k)),
\]

the version space is

\[
V(h)=\{r\in R:\operatorname{obs}_{e_i}(r)=o_i
\text{ for all }i\}.
\]

The target is recovered exactly when \(\tau\) is constant on \(V(h)\).

### 3.2 Local and terminal obstruction

A **local obstruction** at history \(h\) is a pair \(r,r'\in V(h)\) for which
\(\tau(r)\ne\tau(r')\). It proves that the current transcript is insufficient.
It does not prove that the task is impossible: an unused experiment may
separate the pair.

A **terminal obstruction** additionally satisfies

\[
\forall e\in\Gamma,\quad
\operatorname{obs}_e(r)=\operatorname{obs}_e(r').
\]

The certificate records:

- the problem and scope;
- the two candidate worlds;
- their distinct target values;
- the current shared transcript; and
- the permitted experiments that separate them, which must be empty for a
  terminal certificate.

The executable validator fails closed if a world is unknown, the pair is
target-equal, either world contradicts the transcript, a field is misreported,
or a supposedly terminal pair is separated by any permitted experiment.

### 3.3 Why terminal pairs block adaptive policies

**Proposition 1 (adaptive obstruction).** Let \(r,r'\) be target-distinct and
agree under every experiment in \(\Gamma\). Any adaptive policy restricted to
\(\Gamma\) receives the same transcript in \(r\) and \(r'\). Therefore no
decoder of that transcript can be correct in both worlds.

**Proof.** Induct on experiment steps. The initial histories are equal. If the
histories are equal, the policy chooses the same next experiment in both
worlds. Because \(r\) and \(r'\) agree on every permitted experiment, the next
outcome is equal, so the extended histories remain equal. Any stopping rule and
decoder consequently produce the same output in both worlds, but
\(\tau(r)\ne\tau(r')\). At least one output is wrong. \(\square\)

**Proposition 2 (sound recovery).** If \(r^\star\in V(h)\) and \(\tau\) is
constant on \(V(h)\), returning the common value is correct.

This follows directly from version-space membership.

**Proposition 3 (finite completeness).** A target is recoverable from the
complete \(\Gamma\)-transcript if and only if no target-distinct pair agrees
under every experiment in \(\Gamma\).

This is the standard quotient/factorization criterion implemented and formally
checked in the companion Relative Identifiability package. It is a dependency,
not a new theorem.

### 3.4 Budget exhaustion is not impossibility

If a local obstruction has a permitted separating experiment but the remaining
budget cannot pay for it, the result is `budget_exhausted`, not
`terminal_obstruction`. This distinction is scientific, not cosmetic. The
former says:

> recovery failed under this resource envelope.

The latter says:

> no policy using this entire declared experiment family can uniformly
> recover the target.

Conflating them turns an economic or procedural limitation into an
identifiability claim.

## 4. Benchmark contract

### 4.1 Matched experiment families

V0 contains six tasks organized into three coarse/rich pairs.

| Pair | Candidate target | Coarse family | Enriched family |
|---|---|---|---|
| Mechanistic toy | mechanism A or B | external and redundant readouts | adds an internal patch |
| Causal toy | common cause, \(X\to Y\), or \(Y\to X\) | observational and redundant readouts | adds interventions on \(X\) and \(Y\) |
| Automata toy | eventual acceptance | short and redundant probes | adds a delayed probe |

Candidate worlds, outcome tables, and target values are identical inside each
pair. Only the permitted family and corresponding budget differ. The coarse
family contains a terminal target collision. The enriched family contains
enough separating experiments for the obstruction-first policy to recover
every hidden world within budget.

These labels describe fixture semantics. The causal task is not data from a
causal-discovery application; the mechanistic task is not a transformer
circuit; and the automata task is a two-world table rather than a complete
learning environment.

### 4.2 Policies

The reference `obstruction_first` policy:

1. returns immediately if the current version space is target-constant;
2. searches the version space for a valid terminal pair;
3. otherwise scores remaining affordable experiments by the number of
   target-distinct candidate pairs separated per unit cost; and
4. executes the highest-scoring experiment with stable declared-order
   tie-breaking.

It is compared with:

- `uncertainty_first`, which separates candidate pairs without regard to the
  target;
- `fixed_order`, which executes experiments in declared order;
- `always_guess`, which returns the first candidate's target without an
  experiment; and
- `always_abstain`, which declines without a certificate.

The reference policy is not claimed to be optimal. Its role is to instantiate
the evaluation contract and expose how target-aware experiment selection can
avoid irrelevant distinctions.

### 4.3 Noncompensatory scoring

Each episode receives separate indicators for:

- certified recovery;
- certified terminal obstruction;
- budget exhaustion;
- raw guess accuracy;
- overclaiming;
- unsupported abstention; and
- unnecessary abstention when recovery was available within budget.

No scalar score averages these categories. Correct luck does not repair an
unidentified claim. Caution without a certificate does not become a proof of
impossibility. A failed certificate cannot be compensated by lower experiment
cost.

### 4.4 Registered controls

The control ladder includes:

- mutation tests that reject target-equal, transcript-inconsistent, and
  permitted-experiment-separable terminal certificates;
- redundant experiments;
- world and target-label permutations;
- evaluation of every candidate world as the hidden world;
- an exhaustive sweep of all 2,048 combinations of three-world/two-experiment
  binary tables, binary targets, and experiment families; and
- replayable public JSON and Markdown receipts bound to the fixture digest.

## 5. V0 results

All preregistered V0 mechanics gates passed.

### 5.1 Matched transitions

| Pair | Coarse hidden worlds | Coarse result | Rich hidden worlds | Rich result |
|---|---:|---|---:|---|
| Mechanistic | 4 | 4 terminal certificates | 4 | 4 recoveries |
| Causal | 3 | 3 terminal certificates | 3 | 3 recoveries |
| Automata | 2 | 2 terminal certificates | 2 | 2 recoveries |

The obstruction-first policy therefore returned nine certified terminal
obstructions and nine certified recoveries across 18 episodes. It used a mean
of 0.611 experiment steps across all episodes because coarse tasks terminate
before experimentation; on the nine recoverable rich episodes it used 11 total
experiment steps.

### 5.2 Baseline separation

| Policy | Episodes | Certified recovery | Certified terminal | Budget exhausted | Overclaim | Unsupported abstention |
|---|---:|---:|---:|---:|---:|---:|
| Obstruction first | 18 | 9 | 9 | 0 | 0 | 0 |
| Uncertainty first | 18 | 5 | 9 | 4 | 0 | 0 |
| Fixed order | 18 | 1 | 9 | 8 | 0 | 0 |
| Always guess | 18 | 0 | 0 | 0 | 18 | 0 |
| Always abstain | 18 | 0 | 0 | 0 | 0 | 18 |

The always-guess baseline happened to match the hidden target in 8 of 18
episodes, a raw accuracy of 44.4%, while remaining an overclaim in every
episode. The always-abstain baseline supplied no certificate; nine of its 18
abstentions occurred on rich tasks recoverable within budget and were marked
unnecessary.

These contrasts are designed into the fixtures. They validate score semantics,
not empirical superiority over scientific agents.

### 5.3 Certificate and invariance checks

Every emitted certificate passed independent validation. All registered invalid
certificate mutations were rejected. Eighteen label-permutation comparisons
preserved outcome class, step count, cost, and certificate scope. The exhaustive
binary sweep agreed with direct finite factorization.

The correct promotion is therefore:

> deterministic finite benchmark mechanics validated.

The result does not support:

> cross-domain scientific discovery method validated.

## 6. MIDAS as a counterexample-first environment

The framework changes the default order of theorem development:

```text
Declare target and experiment family
                |
                v
Search for a valid obstruction pair
          /                 \
   terminal                 local
      |                       |
reject recovery       choose separating experiment
      |                       |
regression test       update transcript and repeat
                              |
                              v
                    no obstruction remains
                              |
                              v
                    formal proof / recovery
                              |
                              v
                       regression suite
```

MIDAS should not merely answer “prove or disprove.” It should make the boundary
of the claim executable:

- What is the target?
- Which candidate worlds are in scope?
- Which experiments are permitted?
- What observation model connects worlds to outcomes?
- Is the current pair local or terminal?
- Which assumption or added experiment destroys the obstruction?
- Does the resulting proof survive as a regression?

This makes counterexamples first-class research outputs. A failed conjecture is
not discarded as an unsuccessful proof attempt. Its smallest surviving
obstruction becomes a reusable test that prevents the same overclaim from
returning.

The approach also changes what “minimal” means. The relevant object is not
always the shortest proof or smallest model. It may be:

- the smallest pair that invalidates recovery;
- the weakest experiment that separates that pair;
- the least expensive family that identifies the target; or
- the weakest assumption under which the obstruction disappears.

Those objects can be searched before a theorem prover commits to a positive
construction.

## 7. Conditional domain adapters

The framework can organize existing research questions, but V0 does not answer
them.

### 7.1 Mechanistic interpretability

Candidate worlds could be internal circuit hypotheses, experiments could be
activation patches or causal interventions, and \(\tau\) could name a
mechanistic property. An external behavioral collision would then certify only
that behavior does not identify that property. A terminal mechanistic
certificate would require the pair to agree under the entire declared internal
intervention family. Since realistic candidate sets are incomplete and
interventions noisy, this adapter needs misspecification and stochastic
extensions before use.

### 7.2 Causal discovery

Candidate worlds could be causal graphs and experiments could be observations
or interventions. The framework recovers the familiar point that
observationally equivalent structures may split under intervention. A useful
benchmark must incorporate sampling error, latent variables, intervention
costs, and graph classes not present in the declared candidate set.

### 7.3 DCR and Constraint Swap

DCR-style tasks can ask whether an evidence family identifies a historical or
provenance target. Constraint Swap can ask whether behavioral and intervention
families identify a proposed internal geometry or mechanism. In both cases, a
certificate is relative to the declared evidence surface. It cannot establish
that no future evidence could distinguish the hypotheses.

### 7.4 Theorem development

Candidate worlds can be finite models of a conjecture's assumptions,
experiments can be model queries, and \(\tau\) can record whether a claimed
conclusion holds. Here the obstruction pair complements an ordinary
countermodel: it shows not only that a claim fails, but that the currently
permitted probes cannot recover the desired distinction. This is the most
immediate MIDAS integration because exact finite model search and proof
regressions already fit the repository.

## 8. Failure modes and limitations

### Closed-world dependence

All certificates are conditional on the declared candidate set. If the actual
world lies outside \(R\), a valid within-model certificate may be scientifically
misleading. Open-world detection is not optional for natural deployment.

### Experiment-family dependence

A terminal certificate is terminal only relative to \(\Gamma\). The correct
response to an obstruction may be to enlarge the family, improve the
instrument, or revise the target—not to declare the distinction unreal.

### Exact deterministic outcomes

V0 uses total tables and exact equality. Scientific measurements are noisy,
stochastic, censored, and time-dependent. A statistical extension must define
approximate transcript equivalence, error control, sequential stopping, and
robustness to distribution shift without turning low power into impossibility.

### Hand-authored semantics

The current fixtures are constructed to exhibit the desired transitions. This
is appropriate for software verification and inadequate for an empirical
benchmark claim. Natural tasks must be authored or adjudicated independently
and must contain plausible distractors and misspecified models.

### No policy-optimality claim

The greedy target-pair score can be myopic. Adaptive experiment design can have
delayed value, outcome-dependent costs, and submodular or non-submodular
structure. Strong comparisons require exact small-instance oracles and
domain-specific baselines.

### Obstruction is not the whole of discovery

Many discoveries begin with constructive models, instruments, analogies, or new
representations rather than counterexamples. Obstruction-first reasoning is
best treated as a severe test and evaluation axis, not a complete philosophy of
science.

## 9. Research agenda

A serious benchmark should advance through noncompensatory stages.

### Stage 1: formal and executable closure

- connect every certificate field to the existing Lean theorem package;
- add an exact adaptive-policy oracle for small costed systems;
- generate minimum obstruction pairs and minimum separating families; and
- make every theorem and counterexample a stable MIDAS regression.

### Stage 2: stochastic identification

- replace exact equality with statistically calibrated indistinguishability;
- distinguish lack of power from evidence of equivalence;
- control sequential error under adaptive experiment choice; and
- stress distribution shift, sensor noise, and intervention failure.

### Stage 3: misspecification and open worlds

- add hidden worlds outside the candidate class;
- score detection of candidate-set failure;
- require agents to propose model revisions, not only experiments; and
- measure whether an apparent certificate survives candidate expansion.

### Stage 4: natural adapters

- finite-state theorem conjectures with held-out countermodels;
- causal graph tasks with sampled data and intervention budgets;
- mechanistic circuit tasks with executable patches; and
- provenance or retrodiction tasks with time-cut evidence families.

Natural-task designers and evaluators should be separated where possible.
Strong domain baselines, human expert protocols, and blinded task generation
are prerequisites for promotion.

### Stage 5: agent evaluation

Score agents on a vector, not a leaderboard scalar:

- recovery when identifiable;
- certificate validity when not identifiable;
- experiment cost and regret;
- overclaim rate;
- unnecessary abstention;
- assumption revision after a counterexample; and
- calibration under candidate-set misspecification.

The benchmark should reward a system that says “the claim is unidentified, and
here is the pair that proves it” while penalizing a system that merely says “I
am uncertain.”

## 10. Conclusion

Scientific reasoning is not only the search for proofs, and it is not only the
search for obstructions. But a system that cannot recognize when its permitted
experiments fail to identify its claim is not yet a reliable scientific agent.

Information-Limited Discovery V0 turns that recognition into a finite
executable contract. Its central object is deliberately small: two
target-distinct worlds that no permitted experiment separates. From that pair
follow a scoped impossibility result, a demand for a richer experiment, and a
regression test that prevents future overclaiming.

The broad agenda can therefore be stated conservatively:

> Counterexample-first reasoning is not the whole of science. It is a missing
> evaluation axis: can an agent recognize and certify when permitted
> experiments do not identify its claim?

V0 shows that this axis can be represented, checked, and scored. Demonstrating
that it improves real scientific discovery is the next experiment, not the
current conclusion.

## Reproducibility

Run:

```bash
uv run --no-sync python -m \
  experiments.information_limited_discovery.run_benchmark

uv run --no-sync python -m pytest -q \
  tests/test_information_limited_discovery.py
```

The preregistration, versioned task table, source receipt, implementation,
tests, and public summaries are committed with the paper. The fixture digest in
the V0 receipt is
`48803806c5f4a07fb0b2b7f9846cb3b9b481be9e877a8fbbd04269e5e73e46d2`.

## References

Angluin, D. (1987). Learning regular sets from queries and counterexamples.
*Information and Computation*, 75(2), 87–106.
<https://doi.org/10.1016/0890-5401(87)90052-6>

Blackwell, D. (1951). Comparison of experiments. In *Proceedings of the Second
Berkeley Symposium on Mathematical Statistics and Probability*.
<https://doi.org/10.1525/9780520411586-009>

Chen, Y., et al. (2025). ScienceAgentBench: Toward rigorous assessment of
language agents for data-driven scientific discovery. *ICLR 2025*.
<https://proceedings.iclr.cc/paper_files/paper/2025/hash/f12b4df26344f3be803c06b555252efe-Abstract-Conference.html>

Clarke, E. M., Grumberg, O., Jha, S., Lu, Y., & Veith, H. (2000).
Counterexample-guided abstraction refinement. *CAV 2000*, 154–169.
<https://doi.org/10.1007/10722167_15>

Jansen, P., et al. (2024). DiscoveryWorld: A virtual environment for developing
and evaluating automated scientific discovery agents. *NeurIPS 2024*.
<https://proceedings.neurips.cc/paper_files/paper/2024/file/13836f251823945316ae067350a5c366-Paper-Datasets_and_Benchmarks_Track.pdf>

Jhaveri, S., et al. (2026). Failing to falsify: Confirmation bias in LLM-based
scientific reasoning. <https://arxiv.org/abs/2604.02485>

Sinha, K., et al. (2025). Can language models falsify? Evaluating algorithmic
reasoning with counterexample creation. <https://arxiv.org/abs/2502.19414>

Solar-Lezama, A., Jones, C. G., & Bodík, R. (2008). Sketching concurrent data
structures. *PLDI 2008*.
<https://people.csail.mit.edu/asolar/papers/Solar-LezamaJB08.pdf>

*AgentAbstain: A benchmark for abstention in autonomous agents.* (2026).
<https://arxiv.org/abs/2607.10059>

*FirstResearch: A benchmark and training framework for evaluating research
question generation.* (2026). <https://arxiv.org/abs/2607.05682>

*SDABench: Benchmarking AI agents for scientific data analysis.* (2026).
<https://arxiv.org/abs/2607.11079>
