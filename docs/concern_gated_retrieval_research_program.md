# Concern-Gated Retrieval: Theory, Evidence, and Research Program

**Status:** canonical theory and advancement roadmap
**Date:** 2026-07-23
**Human director:** Jawaun Brown
**Current evidence:** deterministic synthetic diagnostic only
**Authoritative implementation:** `experiments/concern_gated_retrieval/`

## Executive thesis

A bounded agent knows more than it can hold in active representation. Its
problem is therefore not only how to store knowledge, but how to decide which
currently absent fact deserves scarce attention now.

Concern-gated retrieval proposes a two-stage answer:

1. nominate facts that are simultaneously connected to the current context
   and to persistent, historically grounded concern; and
2. retain only candidates whose inclusion improves a separately evaluated
   reachable future.

The motivating claim is broader than "better semantic search." For a finite
agent, part of practical meaning may live in the learned geometry that
determines which differences become worth noticing. That claim is a research
direction, not a result of the current pilot.

The merged pilot establishes only that the proposed decomposition can be made
precise and can discriminate authored synthetic roles. Advancing the theory
requires learned representations, adversarially misspecified concern, sealed
utility, non-ceiling comparisons, cross-domain transfer, and eventually
external agent evidence.

## What advances next

The shortest credible path is:

1. **Validate the premise and calibrate variance.** On licensed public or
   consented, governed long-horizon traces, estimate how often agents fail
   because a consequential off-context constraint was omitted and whether a
   history-derived concern signal explains failures beyond context and semantic
   retrieval. Keep these rows out of confirmatory evaluation. Synthetic work
   may continue while this practical-value gate is unresolved, but broad
   usefulness claims may not.
2. **Run COGR-E2a, a cheap concern-recovery screen.** Hold geometry fixed and
   withheld, start concern wrong, force exploratory probes, and test whether
   outcome feedback can recover useful priorities without circular observation.
3. **Run COGR-E2b, the learned-geometry confirmation.** Cross learned,
   frequency-matched, and oracle geometry with frozen-wrong, learned, and oracle
   concern. Use sealed outcomes and matched-budget alternatives.
4. **Run one narrow live-agent beachhead.** Demonstrate constraint preservation
   or task success at matched cost before investing in broad substrate transfer.
5. **Transfer only what survives.** Freeze the smallest winning mechanism and
   test it across memory substrates, task families, and independent
   implementations.

This order makes each failure informative. Concern recovery cannot block a
valid L1 retrieval result, and a useful dual-source retriever cannot be
relabelled as evidence for history-derived concern.

## The intuition: two flashlights over memory

Imagine memory as a large network. One flashlight starts from what is active
now. A second starts from what has historically mattered to the agent. A fact
becomes a retrieval candidate where the two beams overlap.

The canonical example is a date-sensitive commitment:

- **Current context:** March 7, Tuesday, work, errands.
- **Persistent concern:** relationships and commitments.
- **Off-context load-bearing fact:** a partner's birthday is March 7.
- **Context-only distractor:** March has 31 days.
- **Care-only distractor:** a globally important but presently irrelevant
  crisis.

Context-only retrieval finds related trivia. Care-only retrieval repeatedly
raises important but untimely concerns. The desired fact is both relevant now
and important to this agent.

This is an **AND**, not an **OR**:

> retrieve what is relevant now **and** important to the agent, then test
> whether attending to it actually helps.

Concern is not identical to salience, urgency, reward, novelty, or semantic
similarity. A signal can be loud, surprising, globally important, or highly
rewarded while still being the wrong use of the current attention budget.
In the implementation-era notes, **care** is an alias for persistent concern;
the research program uses **concern** except when naming an existing variable
or result.

## The bounded-agent problem

The target problem has five parts:

1. **Capacity:** only a small subset of stored knowledge can be active.
2. **Off-context need:** useful facts may not be locally obvious from the
   present representation.
3. **Personal consequence:** the same fact can matter differently to different
   agents because their histories and commitments differ.
4. **Attention risk:** retrieving a salient but useless fact can consume
   budget, distort planning, or destabilize action.
5. **Feedback:** the consequences of past retrievals can change what deserves
   priority later.

A complete mechanism must therefore distinguish:

- what is related to the current situation;
- what has persistent consequence for this agent;
- what is habitually active but not informative;
- what would improve action if loaded; and
- how concern changes when outcomes reveal that the prior was wrong.

## Mechanism decomposition

### 1. Memory substrate

The current implementation uses a finite weighted graph
\(G_t=(V_t,E_t,W_t)\). Nodes are candidate facts or concepts, edges encode
available relations, \(R_t\subset V_t\) is the active representation, and
\(k\ll |V_t|\) is the retrieval budget.

The graph is a surrogate. The theory does not require natural memory to be
undirected, stationary, explicit, or graph-complete. Future tests may use
learned directed graphs, latent transition models, vector stores with derived
neighborhoods, event logs, or hybrid symbolic-neural memory.

### 2. Concern geometry

Persistent concern supplies non-negative weights over anchors or regions of
memory. In the pilot, concern smoothly changes edge weights without changing
graph support. Intuitively, concern makes some paths easier to traverse.

Two agents can store the same propositions yet inhabit different effective
retrieval geometries because different histories made different distinctions
consequential.

This is the source of the phrase:

> concern deforms the metric.

It remains an operational metaphor until learned geometry and behavioral
consequences are identified independently.

### 3. Two-sided nomination

One personalized diffusion starts from the active context and another starts
from persistent concern:

\[
r_{\mathrm{ctx}},\qquad r_{\mathrm{care}}.
\]

The registered pilot nominates candidates using a rarity-corrected soft
intersection:

\[
q(v)=
\frac{r_{\mathrm{ctx}}(v)r_{\mathrm{care}}(v)}
{\max(r_{\mathrm{freq}}(v),\epsilon)^\beta}.
\]

The numerator implements the AND intuition. The denominator reduces monopoly
by facts that are chronically active everywhere. The Hadamard product is one
candidate intersection operator, not a theorem that multiplication is uniquely
correct.

### 4. Bounded-observer utilization filter

Nomination says "this might matter." It does not say "loading this will help."
The second stage asks whether a candidate-conditioned future contains useful,
learnable structure for a fixed bounded observer.

The pilot uses Zhang and Levin's frozen-reservoir, stable-ridge epiplexity
estimator as a reproducible utilization filter. This composes their estimator
with concern-gated retrieval; it does not imply that their work validates the
concern mechanism.

In later experiments, realized task outcome should become the primary external
criterion. Epiplexity can remain a preregistered mediator or secondary
diagnostic rather than defining usefulness by itself. Before it is promoted as
a mediator, independently reimplement or sensitivity-check the estimator.

### 5. Concern update

The ambitious loop is:

```text
care -> search -> retrieval -> action -> outcome -> care
```

If retrieving facts from a region repeatedly preserves or improves the agent's
trajectory, that region should become easier to reach. If a chronic alarm
repeatedly distracts or harms performance, its priority should fall.

A stable concern profile produced by this loop would be more interesting than
a hand-authored list, but stability alone is not selfhood. It may also be
habit, reward hacking, observer bias, or a self-sealing feedback loop. Those
alternatives require direct controls.

## What the current pilot established

The preregistered deterministic pilot evaluated 192 episodes across base,
sparse, and noisy graph regimes.

| Question | Result | Honest interpretation |
|---|---:|---|
| Does two-sided retrieval beat either one-sided walk? | Coincidence hit@1 `1.000`; best one-sided `0.0052` | Yes, on the authored graph family |
| Does the future filter separate registered controls? | Precision/recall `1.000/1.000`; worst margin `1.7210` bits | Yes, for authored structured versus constant/shuffled futures |
| Is the PageRank implementation numerically valid? | Maximum residual `7.83e-13` | Yes |
| Is multiplication necessary? | Additive hit@1 `0.9635`; tied in two regimes | Not established |
| Was concern learned from misspecification? | Initial/learned/oracle hit@1 all `1.000` | No discriminating evidence |
| Was meaning or selfhood demonstrated? | Not tested | No |

The accepted claim is:

> On this role-authored graph family, dual-source diffusion plus a
> bounded-observer utilization filter discriminates the registered synthetic
> roles under frozen seeds and regimes.

The pilot is a decomposition and implementation result. The graph topology,
node roles, future structure, and utility are authored. That design is useful
for checking the mechanism's plumbing but cannot establish that the mechanism
discovers relevance, concern, or meaning.

## Claim ladder and promotion semantics

Stronger claims must advance one rung at a time. Evidence cannot skip a rung.

| Level | Claim | Minimum new evidence |
|---|---|---|
| L0 — executable diagnostic | The composition can be implemented and checked | Current pilot; complete |
| L1 — learned-representation mechanism | Joint context/second-signal retrieval works when graph structure and roles are learned or withheld | Label-sealed learned edges, non-ceiling baselines, held-out graph families, best matched-budget baseline beaten |
| L2 — history-derived concern recovery | Outcome feedback recovers agent-specific concern from an adversarially wrong prior | Exploration coverage, logged propensities, negative updates, oracle distance falls, task benefit beyond reward/salience/task priority |
| L3 — transferable retrieval principle | The mechanism improves bounded retrieval across distinct task and memory substrates | Cross-family and cross-substrate generalization at matched budget |
| L4 — external agent validity | The mechanism improves real model or embodied-agent behavior without safety or cost regressions | Live agents, stochastic repeats, OOD tasks, matched compute, independent outcomes |
| L5 — cognitive or self-model interpretation | A persistent concern geometry is an identified part of agent-specific meaning or self-maintenance | Competing-mechanism controls, intervention on the learned geometry, longitudinal and independent replication |

"Groundbreaking" should mean surviving the transitions from L0 to at least L3
or L4, not attaching L5 language to an L0 result.

There are two related but distinct tracks:

- **Generic dual-source retrieval:** context plus any useful second signal.
  This earns L1 only by beating the best matched-budget alternative, including
  a learned one-stage ranker.
- **Agent-specific concern:** the second signal is derived from historical
  consequence and adds value beyond current goals, reward/value, salience,
  recency, and semantic relevance. Wrong-agent profiles must fail in the
  predicted direction. Only this track can advance to L2 and beyond.

Additive equivalence blocks a claim that multiplicative intersection is
necessary; it does not erase a joint-retrieval result that beats every
one-sided and learned matched-budget baseline. Conversely, tying a simpler
learned ranker may still yield an engineering result, but it blocks promotion
of the two-stage architecture as the necessary mechanism.

## Discovery-regime audit

### Current regime

- **Artifact types:** authored typed graphs, restart distributions, role labels,
  candidate-conditioned synthetic futures, deterministic policy receipts.
- **Operations:** concern warp, context/care diffusion, additive/product
  ranking, top-k nomination, epiplexity filtering, selected-probe updates.
- **Gates:** numerical fixed points, one-sided and additive baselines,
  constant/shuffled controls, three graph regimes, byte-stable provenance.
- **Known limitations:** authored geometry and utility, ceiling care condition,
  no learned memory, no external agent, no semantic identification.

### Next action class

The immediate next experiment is **discovery-enabling search**: it retains the
existing candidate-selection schema but replaces the artifacts that made the
pilot easy. A genuine regime transition occurs only if learned or withheld
representations plus sealed outcomes support a mechanism that the authored
fixture could not guarantee.

### Noncompensatory rule

Failure or uncertainty in leakage prevention, sealed utility, or the relevant
matched-budget comparison blocks the dependent claim regardless of downstream
accuracy. Gate families remain separate: concern-recovery failure blocks L2+
but cannot invalidate an independently supported L1 result. Held-out
link/neighborhood prediction is a representation diagnostic, not a fatal gate
by itself; causal contribution to sealed outcomes and leakage resistance are
the promotion requirements.

## Immediate experiment program: COGR-E2

COGR-E2 breaks the two largest shortcuts in stages so a failure is
identifiable: the care prior already selects perfectly, and the role-authored
geometry already contains the answer. Calibration occurs first, uses
development-only templates, and freezes effect thresholds, sample sizes,
features, hyperparameters, and analysis code before any confirmatory row is
generated or inspected.

### Target object and decision

- **Target:** a bounded retrieval policy operating over a graph learned only
  from observable episode history.
- **L1 decision:** promote only if joint retrieval improves held-out action
  outcomes over the best matched-budget baseline with no role, target, or
  utility leakage.
- **L2 decision:** promote independently only if history-derived concern
  recovers from an adversarially misspecified prior, improves outcomes beyond
  generic second signals, and mediates the gain under adequate exploration.

### Staged identification

#### COGR-E2a — concern-recovery screen

Use fixed, withheld geometry whose construction is independent of the
downstream role labels. Compare frozen-wrong, online-learned, oracle, shuffled,
and wrong-agent concern. The policy must include randomized probe coverage,
log selection propensities, and preregister an off-policy or counterfactual
estimator so initially suppressed regions can generate evidence. E2a is a
screen for the update rule; it cannot establish learned geometry or L2 by
itself.

#### COGR-E2b — learned-geometry confirmation

Use a crossed design:

| Geometry | Concern state | Identified contrast |
|---|---|---|
| Frequency-matched random, learned, oracle | Frozen non-ceiling concern | Learned representation and L1 retrieval |
| Fixed/withheld, learned, oracle | Frozen-wrong, online-learned, oracle | Concern recovery and geometry/concern interaction |

Report claim-specific contrasts rather than one aggregate winner. The L1 gate
uses the frozen non-ceiling concern rows; the L2 gate uses the concern-update
rows and cannot block L1.

### Data-generating families

Use at least three procedurally distinct families with the same abstract need
but different surface structure:

1. **Delayed commitments:** dates, promises, dependencies, and interruptions.
2. **Maintenance and fault response:** old observations become relevant only
   when a later symptom appears.
3. **Resource-constrained planning:** a hidden prior obligation changes which
   otherwise valid action is best.

Generate episode histories before retrieval. Learn edges from permitted
co-occurrence, temporal, causal, or embedding features. Hold out whole
templates and paraphrase families, not only random rows.

### Decisive controls

- query or embedding similarity;
- context-only and care-only diffusion;
- additive and multiplicative two-sided operators;
- learned one-stage ranker at matched parameter and compute budget;
- learned one-stage ranker that may consume the same concern feature;
- information-matched generic value/advantage, task-priority, recency,
  eligibility, and learned-query second signals;
- larger active context, hierarchical summaries, and recurrent compression at
  matched cost;
- random and frequency-only retrieval;
- oracle graph and oracle care as diagnostic ceilings only;
- shuffled concern labels;
- wrong-agent concern profiles;
- frozen concern versus online concern update;
- verifier-free versus realized-outcome verification.

### Required anti-shortcut design

1. Retrieval code cannot read role labels, answer keys, future utilities, or
   evaluator-only fields.
2. The outcome scorer is sealed behind an environment interface and runs only
   after the retrieval/action decision.
3. Initial concern deliberately overweights a plausible alarm region and
   underweights at least one true commitment region.
4. The retrieval budget and distractor density prevent all reasonable
   two-sided methods from starting at ceiling.
5. Hyperparameters are calibrated on separate development templates, then
   frozen.
6. The held-out evaluation includes graph noise, paraphrase, reordered
   histories, unseen concern combinations, and larger memory sizes.
7. Permitted graph features receive a statistical leakage audit, including
   label permutations or randomized-generator controls, so answer information
   cannot be laundered through legitimate-looking co-occurrence features.
8. Trusted and untrusted history, tool-output, and feedback sources are typed;
   updates retain provenance, bound any single source's influence, and support
   detection and rollback of targeted concern poisoning.

### Reuse contract

Keep the existing graph/PPR numerical primitives, policy receipt shape,
ranking metrics, manifest/provenance machinery, and epiplexity implementation
for sensitivity comparisons. Replace the authored generator, graph
construction, concern update, and synthetic future as needed. Add only
interfaces with a current E2 consumer: learned-graph input, sealed environment
outcome, logged probe propensity, and concern-update receipt. Preserve
comparable pilot fields wherever their meaning remains unchanged; do not build
a parallel benchmark stack.

### Fatal gates by claim

- **Integrity:** no evaluator-only field is reachable from graph learning,
  ranking, concern update, or verification, including through statistically
  leaky permitted features.
- **L1 behavior:** at matched retrieval and compute budgets, the candidate
  improves sealed task outcome over the best one-sided, semantic, additive,
  resource-allocation, and learned one-stage baseline.
- **L1 representation contribution:** intervening on learned edges changes the
  registered downstream outcome in the predicted direction; held-out
  link/neighborhood quality is reported as a diagnostic.
- **L2 recovery:** the wrong prior moves toward useful concern because
  randomized and policy-selected outcomes provide informative positive and
  negative updates, with adequate coverage and valid propensity accounting.
- **L2 specificity:** history-derived concern adds outcome value beyond matched
  reward/value, task-priority, salience, recency, semantic, and wrong-agent
  profiles.
- **Non-ceiling:** each claim-specific contrast retains enough headroom to
  adjudicate its registered question.
- **Adversarial input:** targeted history or feedback poisoning cannot produce
  an undetected, irreversible attention-hijacking state above the preregistered
  tolerance.
- **Robustness:** the primary effect survives every preregistered task family
  and the most important OOD perturbations; aggregate success cannot hide a
  family-level reversal.

Calibration artifacts must include variance estimates, frozen effect
thresholds, sample sizes, features, hyperparameters, and a signed
preregistration. No calibration episode may enter confirmatory evaluation, and
confirmatory templates remain inaccessible during calibration.

### Safety and data-governance entry gates

COGR-E2 evaluation remains synthetic. The separate premise audit may inspect
licensed public or consented traces only after its governance controls pass.
Before any non-synthetic history, external memory, or public row-level release
is used, approve:

1. a data-flow and trust-boundary inventory for memory, model, embedding,
   telemetry, evaluator, and public sinks;
2. collection minimization, sensitivity classes, permitted purposes,
   retention, export, correction, and deletion propagation through raw
   histories, graphs, concern profiles, checkpoints, caches, logs, and
   receipts;
3. protection requirements for data at rest and in transit;
4. an actor-resource-operation matrix for reading, updating, exporting,
   transferring, and deleting concern profiles;
5. identity-bound isolation by default, with authorized, audited, revocable
   cross-agent transfer; and
6. disclosure, licensing, membership-inference, and attribute-inference review
   before any public rows or aggregates.

Profiles and derived geometry are sensitive even when the original history has
been removed. External processors receive only necessary fields and must have
explicit logging, training-use, retention, deletion, compromise, and incident
response terms.

## Advancement program

### Wave 0 — premise, safety, and calibration

Estimate the prevalence and cost of missed off-context constraints on a
governed trace sample, finalize the synthetic E2 generator, run calibration
only, and sign the preregistration. A null premise audit does not forbid the
synthetic mechanism study, but it blocks claims of an important real-agent
bottleneck. The required output is an internal premise receipt, calibration
receipt, and frozen promotion contract.

### Wave 1 — staged mechanism identification

Run E2a, then E2b. The required output is a reproducible internal benchmark
artifact, leakage audit, claim-specific gate receipt, and all registered
baselines. Release a public benchmark only after an L1 gate passes, the schema
is stable, and disclosure review is complete.

Stop or narrow the claim if the best learned one-stage or resource-allocation
baseline ties the candidate, gains vanish outside one family, or concern is
reproduced by a generic value/priority signal. Additive equivalence withholds
only multiplicative necessity. Failed E2a concern recovery withholds L2 but
does not block E2b's L1 rows.

### Wave 2 — narrow live-agent beachhead

After L1 and the data-governance entry gates pass, integrate the best frozen
policy into one real agent with external memory. Use tasks whose success
requires retrieving an old constraint or commitment after many irrelevant
events. Compare at matched context, token, tool, latency, and retrieval budgets.

Primary outcomes should be task success, constraint preservation, false
retrieval cost, recovery after a wrong prior, and useful-autonomy rate.
Epiplexity remains secondary unless it predicts these external outcomes on
held-out tasks.

Broad transfer is blocked unless the beachhead improves a preregistered task
success or constraint-preservation outcome at acceptable cost. This beachhead
is a continuation decision, not L4 promotion; the transferable L3 claim still
requires Wave 3.

### Wave 3 — substrate transfer

Repeat the frozen mechanism across symbolic event graphs, embedding-derived
text memory, directed temporal or causal graphs, and a hybrid store where only
some relations are explicit. If every substrate needs new labels, thresholds,
or hand-authored anchors, the result is task-specific engineering rather than
a general principle.

### Wave 4 — safety, scaling, and independent replication

Stress:

- attention hijacking and adversarial concern injection;
- chronic-alarm monopoly and rarity correction;
- self-confirming care loops;
- catastrophic forgetting of low-frequency commitments;
- privacy leakage from personalized concern;
- compute scaling with memory size and candidate budget;
- stochastic and OOD live-agent replication after the L3 transfer gate;
- transfer between agents with different histories; and
- replication by an implementation that does not reuse the original graph
  generator or scoring code.

Only after these waves should the program promote broad claims about
agent-specific meaning, persistent concern, or a fixed-point account of
selfhood.

## Applicability contract

The mechanism is potentially useful wherever a system has:

1. more stored state than active capacity;
2. a current context;
3. a persistent, agent- or task-specific consequence signal;
4. a bounded candidate budget; and
5. an outcome or counterfactual verifier independent of nomination.

Candidate domains include long-horizon assistants, coding agents, maintenance
systems, scientific agents, robots, and alert-management systems. Clinical,
legal, financial, or other high-stakes deployment requires domain-specific
validation and human governance; success on agent benchmarks would not license
those uses.

Generality is not the number of examples listed. It is the ability to reuse the
same typed interface and frozen mechanism across substrates while preserving
independently measured benefit.

## Failure modes and alternative explanations

| Failure mode | Why it matters | Required control |
|---|---|---|
| Additive equivalence | The AND story may not need multiplication | Strong additive and learned fusion baselines |
| Authored geometry | The graph may encode the answer | Learned/withheld edges and leakage audit |
| Utility leakage | The verifier may receive the label indirectly | Sealed environment outcomes |
| Ceiling initialization | Online learning cannot be identified | Adversarially wrong care prior |
| Chronic concern monopoly | A standing alarm can consume attention | Rarity, cooldown, and budget ablations |
| Self-sealing care | Retrieval determines evidence that reinforces retrieval | Randomized probes and counterfactual updates |
| Verifier gaming | The agent may optimize the proxy rather than outcomes | External task outcomes and proxy-disagreement tests |
| Semantic baseline weakness | Graph gains may reflect a weak comparator | Modern embedding and learned-ranker baselines |
| Generic second-signal equivalence | "Concern" may be ordinary value or task priority | Information-matched value, priority, recency, salience, and wrong-agent controls |
| Task-family leakage | Templates may repeat the same latent rule | Family and generator holdouts |
| Cost displacement | Better retrieval may use more compute | Matched budgets and cost-effect curves |
| Personalization leakage | Concern profiles can expose sensitive history | Minimal retention, access controls, privacy evaluation |
| Poisoned concern | Untrusted history or feedback can redirect attention | Source provenance, bounded influence, detection, and rollback |
| Candidate-selection circularity | The current care model chooses what gets tested, so unnominated memories generate no corrective evidence. The loop learns "among what I looked at, these helped" — not "these were the most useful available." | Split the k retrieval slots as `k_care + k_uncertain + k_audit`; guaranteed ε>0 exploration on every step; propensity logging for IPS/DR debiasing; on synthetic families, oracle top-k with `Recall@k` and simple `regret = max_u Δ(u) − Δ(selected)` as first-class metrics |
| Verifier utilization vs nomination-completeness | Verifier can measure whether the selected memory helped, but not whether an unnominated memory would have helped more. Usefulness and optimality are distinct claims. | Separate metrics: `Δ(v) > 0` (utilization) vs `Δ(v) ≥ Δ(v*) − ε` (completeness). Report the second only when the candidate set is exhaustively evaluable. |
| Verifier-circularity | If the evaluator's definition of "improvement" is shaped by the same care model, care decides both what to inspect and whether the result was good. | Name a care-independent task-success criterion at design time (e.g. "did the agent honor the specific date-bound commitment," not "did the user report satisfaction"). External-outcome scoring only, and disagreement audits between proxy and outcome. |
| Recency ≈ oracle family-design confound | Wave 1a KILL: on procedurally-generated families where the load-bearing memory happens to be the most recent placement, `info_matched_recency` reproduces the oracle ceiling byte-for-byte. Any specificity contrast against recency then collapses. | Family generators must ensure the load-bearing memory is _not_ systematically the most recent. Cross-tabulate recency, salience, semantic similarity, and load-bearing role so no single generic signal aces the family. |
| Marginal-only verification | Testing one candidate at a time cannot find useful bundles or dangerous combinations (e.g. "chocolate is fine" + "cake contains hazelnuts" + "allergic to nuts"). | Add a bundle-KILL cell in Wave 4 where the load-bearing content is a set of ≥ 2 memories with super-additive utility; report set-selection regret. |

Rejected alternatives and negative results remain part of the evidence ledger.
They should not be removed when the narrative changes.

## Publication and benchmark path

A credible public contribution should choose its primary identity at each
stage: first a bounded-retrieval mechanism, and only later—if L2-L5 controls
survive—a philosophical theory of agent-specific meaning. It should contain:

1. a theory paper that clearly separates the bounded-agent problem, mechanism,
   and philosophical interpretation;
2. a benchmark with row-level data, generator holdouts, sealed outcomes, and
   strong semantic and learned-ranking baselines;
3. a mechanism paper or section identifying when dual-source retrieval helps
   beyond additive fusion;
4. a live-agent study with matched budgets and task-clustered uncertainty;
5. negative and null results, including regimes where concern hurts; and
6. an independent replication or alternate implementation.

The memorable framing is the two-flashlight intuition. The scientific center
is the claim ladder and the set of controls that can falsify each rung.

## Terminology

- **Active context:** the small representation currently available to action.
- **Persistent concern:** a slowly changing priority structure grounded in
  historical consequence, not merely current salience.
- **Care:** implementation-era alias for persistent concern.
- **Off-context fact:** stored information absent from the active
  representation.
- **Load-bearing fact:** a fact whose retrieval changes an independently scored
  action or outcome.
- **Two-sided retrieval:** nomination using both active context and persistent
  concern.
- **Rarity correction:** a penalty for chronically or globally active nodes.
- **Utilization filter:** a bounded test of whether loading a candidate helps.
- **Epiplexity:** learnable novelty for a bounded observer; used here as a
  secondary utilization diagnostic, not as task utility itself.
- **Care manifold:** shorthand for persistent concern geometry; not evidence of
  selfhood by itself.
- **Concern recovery:** learning useful priorities from outcomes after the
  initial prior is wrong.

## Authoritative references

- Frozen design:
  `experiments/concern_gated_retrieval/PREREGISTRATION.md`
- Pilot report:
  `experiments/concern_gated_retrieval/results/pilot_2026_07_23.md`
- Machine receipt:
  `experiments/concern_gated_retrieval/results/summary.json`
- Implementation:
  `experiments/concern_gated_retrieval/`
- Verification:
  `tests/test_concern_gated_retrieval.py`
- Discovery ledger:
  `docs/discovery_regime_audit.md`
- Continuation handoff:
  `docs/next_agent_concern_gated_retrieval_handoff_2026-07-23.md`
- External estimator source: Zhang and Levin (2026), *Intelligence from
  Learnable Novelty*, arXiv:2607.18433v1.
