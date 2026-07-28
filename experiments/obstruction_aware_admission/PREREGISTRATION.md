# Preregistration: Obstruction-Aware Admission V0

**Human director:** Jawaun Brown  
**Producing agent:** OpenAI Codex (GPT-5), directed  
**Date frozen:** 2026-07-27  
**Status:** frozen before implementation and benchmark execution

## 1. Question and decision

Can a bounded agent choose the next permitted experiment by the exact remaining
cost of target identification, while returning a machine-checkable obstruction
when the target cannot be recovered?

The intended decision is narrow: whether to promote an exact finite
**obstruction-aware admission contract** as a verified control and benchmark
kernel. This study cannot establish a universal theory of agency, a natural
scientific-discovery method, or a deployment-ready coding-agent controller.

## 2. Current discovery regime

- **Artifact types:** finite worlds, deterministic experiment tables, target
  maps, positive integer costs, version spaces, adaptive policies, recovery
  receipts, and scoped obstruction certificates.
- **Operations:** exact version-space filtering, target-constancy checks,
  terminal-pair search, dynamic programming over finite states, exhaustive
  enumeration, and deterministic replay.
- **Gates:** mathematical recurrence checks, sound recovery, fail-closed
  certificates, exact-oracle dominance, label invariance, and provenance
  replay.
- **Known limitations:** closed candidate set, exact deterministic outcomes,
  small finite instances, no model-call policy, and no natural task.

This is a **search and verifier addition** within the Information-Limited
Discovery regime. The new accepted artifact class, if the gates pass, is a
cost-to-identification witness that distinguishes structural impossibility from
resource insufficiency.

## 3. Mathematical objects

Let:

- \(R\) be a finite nonempty set of candidate worlds;
- \(E\) be a finite set of experiments;
- \(\operatorname{obs}_e:R\to O_e\) give deterministic outcomes;
- \(\tau:R\to T\) be the declared target;
- \(c:E\to\mathbb{N}_{>0}\) give experiment costs;
- \(V\subseteq R\) be the current nonempty version space; and
- \(A\subseteq E\) be the remaining permitted experiments.

The target-disagreement set is

\[
D_\tau(V)=\{\{r,r'\}\subseteq V:\tau(r)\ne\tau(r')\}.
\]

For an experiment \(e\), observing outcome \(o\) leaves

\[
V_{e,o}=\{r\in V:\operatorname{obs}_e(r)=o\}.
\]

The exact worst-case remaining identification cost is preregistered as

\[
C^\star(V,A)=
\begin{cases}
0,&D_\tau(V)=\varnothing,\\
\infty,&D_\tau(V)\ne\varnothing\text{ and no }e\in A
  \text{ separates a target-distinct pair},\\
\min_{e\in A}\left[
c(e)+\max_{o:V_{e,o}\ne\varnothing}
C^\star(V_{e,o},A\setminus\{e\})
\right],&\text{otherwise.}
\end{cases}
\]

Experiments that do not change the version space are inadmissible in the
minimum. Stable declared order breaks exact ties.

## 4. Registered claims

### C1 - Exact finite control

For every registered finite task, the dynamic program returns the minimum
worst-case experiment cost among adaptive policies restricted to the declared
family.

### C2 - Safe termination

The controller returns exactly one of:

1. `recovered`, only when \(\tau\) is constant on the current version space;
2. `terminal_obstruction`, only with a valid target-distinct pair agreeing
   under every remaining permitted experiment;
3. `budget_infeasible`, only when \(C^\star\) is finite but exceeds the
   remaining budget; or
4. `admit`, naming an experiment on an optimal branch.

Budget infeasibility is not an impossibility theorem.

### C3 - Greedy limitation

The target-pair-per-cost rule used by Information-Limited Discovery V0 is a
heuristic, not an optimality theorem. The benchmark will search the registered
finite domain for its smallest strict counterexample. If none is found, the
result will be reported only as a bounded null; universal optimality will
remain withheld.

### C4 - Integration boundary

The verified control depends on target-relative experiment outcomes, not on
learned concern geometry, PageRank, epiplexity, or a generic salience score.
Prior Concern-Gated Retrieval nulls remain in force.

## 5. Policies and comparators

1. `exact`: minimize \(C^\star\).
2. `greedy_target_pairs`: maximize immediately separated
   target-distinct pairs per unit cost.
3. `greedy_all_pairs`: maximize immediately separated candidate pairs per
   unit cost.
4. `fixed_order`: take the first informative permitted experiment.

No scalar reward combines soundness and cost. An incorrect recovery or invalid
certificate is fatal even if the policy is cheap.

## 6. Registered finite study

### 6.1 Exhaustive screen

Enumerate deterministic binary-outcome systems in increasing size, with:

- 2 through 4 worlds;
- 1 through 3 experiments;
- every nonconstant binary target map;
- positive integer costs from the registered set \(\{1,2\}\); and
- every world as the hidden actual world.

Degenerate duplicates remain present; they test redundancy and terminal
collisions. Enumeration order is worlds, experiments, outcome-table integer,
target integer, then cost vector. The first strict greedy counterexample in
this order is the registered minimal witness within the search boundary.

### 6.2 Hand-authored controls

- a target already determined at the root;
- a terminal target collision;
- a recoverable task whose minimum cost exceeds the budget;
- a task with a redundant experiment;
- a task with unequal experiment costs; and
- the minimal greedy counterexample found by the exhaustive screen, replayed
  as a frozen fixture if one exists.

### 6.3 Stress and invariance controls

- reverse world labels and target labels;
- reverse experiment labels while preserving declared-order semantics;
- add a redundant duplicate experiment;
- mutate each field of a valid terminal certificate; and
- compare the memoized recurrence with an independent non-memoized
  decision-tree enumeration on the registered small domain.

## 7. Noncompensatory gates

| Gate | Requirement | Failure consequence |
|---|---|---|
| G0 Object integrity | Every task has aligned finite objects, nonempty version spaces, and positive integer costs. | Reject run. |
| G1 Mathematical agreement | Memoized \(C^\star\) equals independent exhaustive decision-tree cost on every registered small case. | Block C1-C3. |
| G2 Recovery soundness | Every `recovered` result is target-constant and correct for every hidden world. | Block all claims. |
| G3 Certificate soundness | Every emitted obstruction validates; every registered mutation is rejected. | Block C2 and paper promotion. |
| G4 Oracle dominance | On every recoverable case, exact worst-case cost is no greater than each comparator's worst-case cost. | Block C1. |
| G5 Termination separation | Structural impossibility, finite over-budget recovery, and exact recovery receive distinct outcomes. | Block C2. |
| G6 Invariance | Relabeling preserves cost and outcome class; redundant experiments cannot improve the optimum. | Block C1. |
| G7 Greedy falsifier | A strict greedy counterexample is replayable, or the paper explicitly reports a bounded null and withholds universal claims. | Block only the counterexample claim if absent. |
| G8 Legacy-evidence integrity | The paper preserves the Concern-Gated Retrieval L1 KILL and does not use its failed geometry as positive evidence. | Block C4 and synthesis claim. |
| G9 Provenance | Manifest, source digest, results, tests, and paper numbers replay byte-for-byte. | Block release. |

## 8. Claim-strength ceiling

If G0-G9 pass, the strongest allowed conclusion is:

> Exact obstruction-aware admission is a verified finite control contract that
> returns a cost-optimal next experiment, a scoped terminal obstruction, or a
> distinct budget-infeasible verdict.

The study may also report the smallest registered counterexample to the greedy
target-pair heuristic if G7 finds one.

The following remain forbidden:

- “a new theorem of agency”;
- “a universally novel experiment-design algorithm”;
- “better scientific discovery in natural domains”;
- “concern-gated retrieval is validated”;
- “the controller is efficient for large state spaces”; and
- “structural impossibility follows from budget exhaustion.”

## 9. Evidence and output paths

- implementation: `experiments/obstruction_aware_admission/`
- frozen task manifest: `experiment_manifest.json`
- public receipt: `results/summary.json`
- human-readable result: `results/summary.md`
- paper: `papers/obstruction_aware_admission/paper.md`
- tests: `tests/test_obstruction_aware_admission.py`

Failed and dominated policies remain in the receipt. No failed alternative may
be deleted to simplify the narrative.
