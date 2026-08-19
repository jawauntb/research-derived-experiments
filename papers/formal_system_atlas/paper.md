# Formal Atlas of the Research Derived Experiments System

## Proofs, dynamics, empirical findings, failures, and open conjectures

Jawaun Brown, human author and research director

Audit and manuscript production by OpenAI Codex under direction and review

Audit date: 2026-08-19

Repository state: commit `3a86730`

> This is an audit, not a declaration that the program's grand synthesis has
> been proved. The strongest defensible result is a layered system: a sizable
> finite formal core, many bounded exact and empirical instruments, an explicit
> failure ledger, and a broader conjectural research program.

## Executive verdict

The repository contains a real formal and empirical research system, but not
one proved theorem saying that geometry explains intelligence. Its most mature
mathematical center is task-relative representation: a task family induces a
quotient of concrete realizations; the quotient's fibers record distinctions
treated as irrelevant; a compiler chooses or generates realizations inside a
fiber; and interventions, concern, viability, and access determine which
realizations are reachable and useful.

Four conclusions survive the repository-wide audit.

- The finite quotient-fiber-compiler core is substantive. Lean source contains
  hundreds of theorem, lemma, and proposition declarations with no actual
  `sorry`, `admit`, project-local `axiom`, or `native_decide`. The formal scope
  is often finite, discrete, algebraic, or a registered witness. It must not be
  silently transported to measure-theoretic, stochastic, neural, or natural
  domains.
- The empirical program is strongest where it performs exact finite
  enumeration, declares noncompensatory gates, and preserves counterexamples.
  Obstruction-aware admission, relative identifiability fixtures, the SIC
  finite instruments, delete-repair cells, and the EML access split are the
  clearest examples.
- The program has advanced through failed equivalences as often as through
  positive findings. Behavior is not representation; uncertainty is not
  current error; current error is not value of information; completeness is
  not access; shortest description is not always access; fiber mass is not a
  process-independent search law; and a catalog of repairs is not a universal
  calculus.
- The grand claims remain conjectural. General SIC, natural-world common
  sufficient screens, universal weakness-to-OOD transport, active attractor
  geometry, concern as valence, real-agent selfhood or intention, open-world
  discovery, and general neural EML access are not established.

The audit also found status drift. The current repository policy defines
verified as SafeVerify replay with headline axioms contained in `{propext}`.
The latest receipt accepts `Quot.sound` for several passed headlines. Those
headlines are SafeVerify-passed but do not satisfy the current literal policy.
Mathlib results are Lean-proved but not SafeVerify-verified. Several older
papers use verified more broadly. This atlas uses the stricter current policy
and records the inconsistency rather than resolving it by fiat.

## 1. Epistemic types and audit method

Every claim in this atlas belongs to one of five types.

- Definition: fixes an object, map, state, score, or relation. A definition has
  no truth status beyond being well-formed.
- Verified theorem: a named Lean headline with an applicable SafeVerify
  receipt and an axiom footprint satisfying the repository's current literal
  whitelist.
- Proved, not verified: Lean elaborates with no placeholders, but the statement
  lacks an accepted SafeVerify receipt, uses the mathlib lane, or has a receipt
  whose axiom policy conflicts with the current rule.
- Empirically supported: an exact enumeration, deterministic computation, or
  preregistered stochastic result that passed its relevant gates. The claim is
  bounded to the registered representation, data clock, process, and controls.
- Conjecture or interpretation: an unproved generalization, philosophical
  reading, causal transport claim, or proposed architectural law.

The audit treats the repository as a typed discovery graph. Artifact types are
Lean declarations, papers, preregistrations, experiment manifests, committed
result summaries, evidence and claim registries, SafeVerify receipts, tests,
and rejected or withheld artifacts. Operations include proof elaboration,
kernel replay, exact enumeration, seeded simulation, model training,
intervention, adjudication, and synthesis. Gates include theorem assumptions,
SafeVerify policy, preregistered fatal gates, negative controls, integrity
checks, uncertainty requirements, and provenance links.

The current regime is broad but uneven. There are 115 provenance-bearing
top-level experiment packages plus the shared `common` support package, 128
paper sources, 60 Lean files, 190 Python test modules, 67 structured experiment
contracts, and 48 legacy exceptions. A package appearing in the verification
index establishes traceability, not scientific truth. A result file with
`status: pass` establishes that its local runner completed its recorded gates;
it does not override a false scientific gate or a stricter claim registry.

## 2. The master formal object

### Definition 2.1 - Realization system

A realization system is a tuple

```text
S = (X, Theta, T, Z, q, K, C, A, G, V, E)
```

where `X` is a concrete realization or world space; `Theta` is a parameter or
hypothesis family; `T` is a family of tasks or observables; `Z` is a structural
state space; `q : X -> Z` is a coarse-graining; `K : Z ~> X` is a compiler or
Markov kernel; `C` is a concern state; `A` is an action set; `G` is a symmetry
or transformation family; `V` is a viability region; and `E` is an allowed
experiment family.

This tuple unifies the main programs without claiming they share one physical
mechanism. Different papers instantiate only subsets of it.

### Definition 2.2 - Fiber and compiler

For `z in Z`, the fiber is `F_z = {x in X : q(x) = z}`. A valid compiler is
fiber-supported:

```text
K(F_z | z) = 1.
```

The quotient says which differences are ignored at the structural level. The
compiler says how a structural state is realized. Those are distinct: the same
quotient can support many compiler dynamics, priors, or search procedures.

### Definition 2.3 - Common sufficient screen

A quotient `q` is sufficient for task `Y` when `Y` factors through `q`. It is a
common sufficient screen for task family `T` when every member factors through
it. A coarsest common sufficient screen preserves all registered task behavior
while discarding the most concrete variation.

### Proposition 2.4 - Finite SIC-A construction

In the finite nonempty positive-support setting, the repository proves a
construction of the master fibration. A likelihood-ratio vector against a pivot
defines `q`; `Z` is its image; a uniform-on-fiber kernel defines `K`; and finite
Halmos-Savage minimal sufficiency, the coarsen-refine retraction, and CS-2 give
the relevant sufficiency and minimality statements. This is Lean-proved in the
mathlib companion and witnessed exactly on the 4-bit Boolean world.

The result is not the general SIC-A claimed by the program's broadest prose.
Standard-Borel, topological, measure-theoretic, open-support, and learned-task
versions remain open.

### Proposition 2.5 - Rate-distortion deformation

For registered finite sources, a distortion budget deforms the fibration from
fine task-preserving structure toward a constant encoder. The uniform Hamming
closed form, achievability, and converse are Lean-proved in the mathlib lane.
The experimental rate-distortion pair passes its exact finite gates. This
supports the finite parameterization, not a universal claim about learned
neural representation paths.

### Proposition 2.6 - Learnability under covering assumptions

Finite common-sufficient recovery obeys coupon-collector-style bounds under
separation and fiber-balance assumptions. At resolution `epsilon`, an
`epsilon`-cover reduces the continuous problem to a finite one, producing an
exponential dependence on intrinsic dimension absent stronger bias. The
repository's exact instruments support the bound on registered grids.

Uniform polynomial learnability in intrinsic dimension is false without
additional structure. Linear ICA, sparse ICA, auxiliary-variable, and
interventional settings are conditional antecedents, not a general escape.

## 3. Representation dynamics

### Definition 3.1 - Abstraction frontier

A representation is scored by task insufficiency, dynamical non-closure,
coding cost, and control regret. The non-dominated set is a Pareto antichain.
This replaces the idea of a single universal ladder from concrete to abstract.

AF-1's antichain property is a direct order-theoretic fact. The registered
static instrument finds a two-point frontier and confirms that identity can be
dominated by a coarser sufficient quotient. The interpretation is important:
more detail is not automatically a better representation.

### Definition 3.2 - Obstruction

Given a candidate screen `q_D` and target `Y`, an obstruction is a pair
`x, x'` such that `q_D(x) = q_D(x')` but `Y(x) != Y(x')`. One such pair proves
that `Y` cannot factor through `q_D`.

### Definition 3.3 - Repair

A repair adds a coordinate, changes a quotient, or supplies transport so that
the target becomes representable. The delete-repair program distinguishes:

- over-invariance: restore a distinction that was wrongly collapsed;
- under-invariance: quotient or covariantize a leftover privilege;
- covariant compensation: retain multiple charts and add transport.

### Lemma 3.4 - Independent repair composition

The formal RR-2 core requires more than the informal phrase "each lift repairs
its invariant." A lift must preserve an invariant once captured, and the lifts
must commute. Under those assumptions, their composition ensures both
invariants. Without preservation, one lift can destroy what the other fixed.

### Finding 3.5 - The universal repair calculus failed

The eight-row repair table is useful but is not a universal function from a
cheap failure signature to a unique minimal lift. Finite menu-blind and relabel
tests kill that stronger claim. The successful `kappa_screen` uses the same
common-sufficient screen as SIC plus a disclosed total order. Multiple adequate
repairs can be incomparable, no largest adequate repair need exist, and greedy
repair can depend on order.

The resulting house conclusion is conservative and stronger: delete-repair is
motion on SIC's task-relative frontier, not a second master object.

## 4. Local theories, causal meaning, and gluing

### Definition 4.1 - Causal meaning quotient

For a message `m`, context `c`, and downstream update `Psi(m,c)`, define

```text
m1 ~_Psi m2 iff for every c, Psi(m1,c) = Psi(m2,c).
```

The quotient by this equivalence is the coarsest downstream-preserving meaning
screen. A co-occurrence partition can be incomparable with it. The finite
theorem is formal; the broader claim that human linguistic meaning is exactly
this quotient is an interpretation.

### Definition 4.2 - Theory atlas

Local contexts carry charts `M_i` with transition maps `T_ij`. A cocycle
discrepancy compares direct and composed transitions on triple overlaps. In
the registered finite classifier, discrepancy support separates three cases:
glue, a localized boundary, and a distributed missing-latent signature.

### Formal boundary 4.3

The SafeVerify-verified object is the finite TA-2 classifier and registered
witnesses. The naked paper-level TA-1 "cocycle iff gluing" needs injectivity or
an equivalent condition; a constant family is a counterexample to the
unqualified version. The smallest alphabet enlargement that repairs an
arbitrary failed cocycle is unproved.

## 5. Concern, compiler ecology, and viability

### Definition 5.1 - Concern reweighting

Given utility or concern statistic `U_c`, concern changes a compiler inside an
existing fiber:

```text
K_c(x | z) proportional to exp(beta * U_c(x,z)) K(x | z).
```

The support remains inside the fiber. Concern therefore selects among
realizations without by itself changing what the quotient represents.

### Proposition 5.2 - Finite concern geometry

For the registered finite exponential-family model, the Fisher information is
the covariance of the sufficient statistic, scaled by `beta^2`. The repository
also proves a finite rectangular holonomy/area identity. These are mathlib
proved-not-verified results. Their interpretation as contextual meaning,
valence, or lived concern is not proved.

### Definition 5.3 - Compiler ecology

A compiler population can evolve by a Boltzmann update:

```text
K_(t+1)(x | z) proportional to K_t(x | z) exp(beta * r_t(x,z)).
```

The finite Chebyshev/Boltzmann core proves that nonnegative reward tilt does not
decrease expected reward under the stated assumptions. A Bayesian compiler
update coincides with this form when reward is log likelihood. Full stochastic
MDL consistency and broad evolutionary interpretations remain open.

### Definition 5.4 - Viability dynamics

Let `V subset Z` be viable. A bounded agent attempts to keep `q(X_t)` in `V`
while learning which effects are self-caused, world-caused, or jointly caused.
The most defensible maintained-concern loop is

```text
disturbance -> detect -> allocate intervention -> update attribution
            -> regulate -> cool or satiate -> quiesce -> re-engage
```

This is a state machine assembled from synthetic experiments. It is not a
theorem of consciousness, general agency, or selfhood.

## 6. Weakness, symmetry, and OOD generalization

### Definition 6.1 - Symmetry-compatible weakness

`W_G(f)` counts or weights transformations in `G` for which a hypothesis
transports consistently with an allowed output action. Large compatible volume
is "weak" because the hypothesis commits to fewer arbitrary distinctions while
remaining valid.

### Empirical finding 6.2

On registered shortcut-compatible symbolic and neural families, weakness is a
stronger predictor of OOD accuracy than the implemented loss, description
length, compression, sharpness, norm, and validation baselines. The largest
registered neural sweep contains 4,096 models; true-group weakness has Pearson
correlation about `+0.8085`, compared with `+0.2533` for parameter norm and
`+0.0924` for validation. Structure-compatible semantic selection reaches
about `0.978` OOD versus `0.919` for random or ID selection and `0.751` for a
wrong structure.

### Failure 6.3 - External portability

The external Pythia LoRA design hard-rejects portable weakness-to-generalization
causality in that setting: mean OOD is about `0.0285`, weakness correlation is
about `-0.0817`, and a classical comparator is stronger. The internal result
therefore remains real but domain-bounded.

### Formal boundary 6.4

A two-point finite coverage proposition and mixture-prior mass facts are
SafeVerify-replayed. The general group-completion statement, the
Langford-Seeger-Maurer PAC-Bayes inequality, neural parameter-space transport,
and OOD causality are not proved by those artifacts. The PAC-Bayes experiment's
top-level `pass` coexists with one false OOD wrong-group gate; its own claim
boundary withholds OOD transport. This atlas follows the gate, not the word
`pass`.

## 7. Access is process-relative

### Definition 7.1 - Expressivity and access

For a syntax language, `q` maps terms to denotations. A fiber contains all
terms with the same denotation. Expressivity asks whether the fiber is
inhabited. Access asks whether a specified process can reach a useful member.
Formula size, circuit size, prior mass, optimization basin, and rewrite basin
are different objects.

### Proposition 7.2 - Four-seam separation

The Mul/Sq monomial toy separates four seams exactly: both languages express
the target; tree size differs exponentially; shared circuit size does not;
and normalized Gibbs fiber mass differs sharply. At `n=4`, the registered
log2 mass ratio exceeds `28.28`. The Lean core proves the exact tree and circuit
facts; the finite instrument checks Catalan shell counts and normalization.

### Experiment sequence 7.3 - EML US-4 prime

- Truncated Gibbs mass distinguishes two same-minimum-size targets by
  `2.015625`, so shortest depth is insufficient.
- Matching-skeleton gradient descent succeeds `8/8` versus `6/8`, a bounded
  local result consistent with the mass ranking.
- Unknown-skeleton gradient descent ties `7` versus `7`; mass does not transfer
  to this freely retunable search process.
- Frozen-leaf greedy rewrite produces `43` versus `28` extra basins; the effect
  returns when the process preserves discrete structure.

The conclusion is not "fiber mass governs search." It is that access is a
property of a fiber plus a process. The neural bootstrap and any general law
mapping Gibbs mass to gradient recovery remain open.

## 8. Identification, discovery, and admission

### Definition 8.1 - Relative identifiability

Allowed experiments `E` induce observational equivalence on hidden worlds.
Target `tau` is identifiable exactly when it factors through the observational
quotient. A target-disagreeing indistinguishable pair is a complete obstruction
certificate. Adding experiments can only refine the quotient.

The Lean package proves the quotient/factorization kernel for arbitrary
dependent experiment systems. It does not prove statistical identifiability
under noise, misspecification, continuous spaces, or limited samples.

### Definition 8.2 - Typed scientific outcome

A bounded scientific controller should return one of four types:

- recovered target;
- terminal obstruction;
- recoverable but outside the current budget;
- a next experiment on an optimal worst-case branch.

This prevents a lucky guess, a resource failure, and a mathematical
impossibility from sharing one score.

### Empirical finding 8.3 - Exact obstruction-aware admission

The registered exhaustive screen evaluates 500,912 binary systems and
1,975,104 hidden-world episodes with zero mathematical, certificate, recovery,
or oracle-dominance failures. It preserves 26,304 strict counterexamples to
immediate target-pair greedy choice; the smallest registered case costs `3`
under greedy choice versus an optimal worst-case cost of `2`.

This is exact finite decision control. It is not new optimal-decision-tree
mathematics, a scalable open-world planner, natural scientific discovery, or
universal agency.

## 9. The empirical correction chain

The long concern/agency arc is best understood as a sequence of corrected
identifications.

- Behavior is not representation. A controller can act correctly while the
  proposed hidden decomposition is wrong or unmeasured.
- Representation is not competence. Decodable geometry can exist without the
  intervention-sensitive mechanism needed by the task.
- Uncertainty is not error. Bootstrap ensembles can agree at a regime boundary
  where all members are confidently wrong.
- Residual magnitude is not systematic error. Irreducible Bernoulli noise can
  dominate a probe-value signal.
- A historical residual is not current error. Debiasing can remove noise yet
  preserve stale or unevenly sampled calibration.
- Current error is not value of information. Exact Bayesian enumeration gives
  counterexamples where the most informative misspecified probe has zero
  oracle EVSI and negative true regret reduction.
- Re-engagement is not stable re-engagement. A trigger can fire once yet fail
  latency, specificity, or repeated-disturbance gates.
- Total prediction is not component identifiability. Self/world heads can be
  gauge-symmetric while total outcome prediction stays accurate.

This correction chain is one of the repository's strongest findings. Each
failed equivalence narrows the object that a later experiment must identify.

## 10. Supported empirical findings by program

### 10.1 Finite formal instruments

The abstraction frontier, causal semantics, common sufficiency,
rate-distortion, finite SIC-A witness, representation repair, theory atlas,
compiler ecology, delete-repair suite, concern selection, silent substitution,
and related exact packages mostly pass their registered finite gates. Their
value is executable scope discipline: they demonstrate consistency and expose
missing assumptions. They are not independent evidence for natural-world SIC.

### 10.2 Concerned syntax and viable bodies

Concerned syntax passes its registered multi-seed symbolic/vector gate when
intervention use is gated by task concern. Viability-guided typed bodies pass
the joint formal, resource, action, and anti-cheat surface while shortcut
controls fail. These are bounded synthetic acceptance surfaces, not solved
natural perception, open semantics, or neural architecture search.

### 10.3 Causally grounded finite agents

World-responds Suite C passes its 64-seed bootstrap gate with recovery `1.0`
and a large selectivity lift. Long-horizon/tool experiments establish several
behavioral and memory surfaces, but also preserve provider-specific repair
failures and hidden-site negatives. The benchmark charter's strongest honest
claim is methodological: final-answer accuracy should be paired with at least
one structure-specific gate and anti-cheat control.

### 10.4 Hysteresis without bifurcation

The preregistered passive-active phase map rejects a reproducible discontinuous
bifurcation: critical-point stability and order-parameter co-location fail. A
separate matched-budget continuation result supports path dependence: loop area
is about `0.04471`, six contiguous couplings are significant, washout preserves
four, and reinitialization clears the effect. The correct statement is
synthetic hysteresis without established bifurcation or attractor basin.

### 10.5 Concern-gated retrieval

The E1 synthetic pilot passes 192 deterministic episodes: coincidence hit@1 is
`1.000` versus a best one-sided rate near `0.0052`, verifier precision and
recall are `1.000`, and the maximum PPR residual is tiny. Yet additive scoring
ties the product in two regimes and learned concern is already at ceiling.
Multiplicative necessity, learned care, selfhood, and live-agent transfer are
withheld. Later E2 waves expose ordering leakage, a killed wave, and only a
partial go decision.

## 11. Major failures, nulls, and invalid runs

### 11.1 Weakness external contact

The external Pythia LoRA transfer rejects the portability claim. Internal
symmetry-compatible success cannot be promoted to an external causal law.

### 11.2 Constraint-swap causal geometry

All five causal-geometry gates fail even though competence is `1.0`. Correct
answers do not imply that the proposed representation carries the causal
mechanism.

### 11.3 Commitment-surface generator generalization

E5 favors labeled coverage rather than generator structure: one coverage-local
OOD score is about `0.741` while the generator score is about `0.063`.
Generator, group-specificity, and transport gates fail. E6 is blocked at its
smoke gate. E7 has no scientific verdict because 6 of 32 matched groups violate
the frozen runtime budget.

### 11.4 Activation geometry

Small Pythia-70M pockets leak target-family controls and fail replication at
Pythia-160M. A target direction can move intended relations while also moving
random relations. The evidence is model-specific and nonspecific, not a causal
activation-space geometry law.

### 11.5 Load-bearing prose

The load-bearing score is high, but the preregistered paraphrase invariance gate
is killed. The result is a bounded null: prose can contain commitment surfaces
on the tested substrate without surviving the registered paraphrase gauge.

### 11.6 Seed promotion

The deterministic calibration package rejects three-seed promotion. Three
seeds are insufficient in every registered regime; independent regimes require
about 16, hierarchical regimes about 64, and the weak high-noise regime remains
unpromotable. A local `pass` means the counterexample instrument worked, not
that three seeds are scientifically adequate.

### 11.7 Value-of-information surrogates

Current error, posterior variance, error-squared heuristics, and mutual
information do not universally rank probes by true expected regret reduction.
The exact enumeration passes because it preserves the counterexample. The
surrogate-generality claim is rejected.

### 11.8 Neural group discovery procedure sensitivity

Data-inferred group weakness retains much of the oracle signal in the
registered rotation setting, but the result depends on selection procedure.
Threshold selection can tie; top-k selection changes encoder-versus-pixel
rankings. A dense random-rotation control is not a strict null because it
inherits partial alignment by construction.

## 12. Formal theorem families and claim boundaries

The formal source is organized into three lanes.

### 12.1 Relative-identifiability lane

This lane proves equivalence-relation laws, factorization iff fiber constancy,
obstruction iff failure to factor, refinement under richer experiments, and
empty or constant edge cases. Its truth is quotient theory for deterministic
dependent experiment systems. Noise and statistical rates are outside scope.

### 12.2 Lean core lane

The core lane includes common sufficient screens, finite counting, refinement,
union-bound and pigeonhole facts, causal semantics, abstraction frontiers,
alignment arithmetic, theory-atlas classifiers, representation repair,
delete-repair witnesses, EML enumerations, concern choices, silent
substitution, and finite identifiability witnesses. Some headline subsets have
SafeVerify receipts; many supporting declarations only have a green Lean
build. File presence is not itself a receipt for every declaration.

### 12.3 Mathlib lane

The mathlib lane proves real exponential and logarithmic bounds, Chebyshev and
Boltzmann inequalities, finite positive-support Halmos-Savage, uniform-Hamming
rate-distortion including Fano/Jensen converse, coarsen-refine identities,
finite exponential-family Fisher identities, rectangular holonomy, Bayesian
mixture bounds, finite SIC-A, covering calculations, and a weakness KL
certificate. It uses standard axioms such as `Classical.choice` and is explicitly
proved-not-SafeVerify-verified.

The PAC-Bayes KL inequality is cited and accepted as a hypothesis in the plug-in
theorem; it is not proved locally. The general ICA theorem, probability-space
conditional independence, full CT-1 MDL rate, and several paper-level analytic
transports remain outside the current Lean statements.

## 13. System dynamics as a research process

The repository itself is an adaptive system. Let a research regime be

```text
R_t = (A_t, O_t, G_t, S_t)
```

where `A_t` is the set of representable artifact types, `O_t` the allowed
operations, `G_t` the gates and verifiers, and `S_t` the evidence store.

A run produces candidate artifacts and residuals:

```text
(accepted, rejected, residual) = Gate(R_t, Run(R_t, hypothesis)).
```

Retrieval adds an already representable artifact. Search explores within the
same schema. Discovery requires a stable change to an accepted artifact type,
operation, verifier, grammar, mechanism, or explanatory residual. A failed
candidate can therefore be productive: it changes the obstruction map even
when it does not expand the accepted theory.

The program's characteristic transition is:

```text
equivalence claim
  -> preregister a discriminator
  -> find a counterexample or boundary
  -> split the object into typed components
  -> build a narrower instrument
  -> preserve both the supported subclaim and the rejected transport
```

This pattern explains the progression from representation to competence,
uncertainty to error, error to value, completeness to access, and repair table
to task-relative frontier.

## 14. Hypotheses and what they have borne out

### H1 - Task-relevant structure is quotient-like

Status: strongly supported in finite formal and synthetic settings. The
coarsest common sufficient screen, causal meaning quotient, relative
identifiability quotient, and finite SIC-A all instantiate the pattern. Natural
task ensembles and learned open-world screens remain unproved.

### H2 - Geometry is the portable language of constraints

Status: useful organizing conjecture, partially supported by synthetic metric,
fiber, chart, and intervention constructions. It is not a theorem and has
failed to transfer cleanly in activation-space and external-model settings.

### H3 - Weakness predicts transport better than generic simplicity

Status: strongly supported inside registered symmetry-compatible shortcut
families; rejected as a current external portability law. The formal coverage
kernel is much narrower than the empirical hypothesis.

### H4 - Passive geometry becomes an active attractor under coupling

Status: not established. Passive and intervention-sensitive geometry exist in
bounded settings; the discontinuous bifurcation claim fails. Synthetic
hysteresis survives, but basin and return dynamics remain open.

### H5 - Concern allocates representational or compiler capacity

Status: exact finite reweighting, Fisher, boundary, and selection effects are
supported. The bridge to learned real-world care, valence, or phenomenology is
conjectural.

### H6 - Two-sided context and care are multiplicatively necessary for recall

Status: the coincidence mechanism beats one-sided policies in the E1 synthetic
world, but additive scoring ties it in two regimes. Multiplicative necessity
and learned care are withheld; later leakage failures require a more sealed
design.

### H7 - A universal repair calculus maps failures to minimal lifts

Status: rejected in the strong form. The finite repair table works on its rows,
but menu blindness, relabeling, nonuniqueness, and order dependence kill a
cheap universal function. The surviving theory is task-relative frontier
movement.

### H8 - Description complexity controls access

Status: rejected as a general statement. Tree size, circuit size, Gibbs mass,
and process-specific basin geometry separate. Access is process-relative.

### H9 - Bounded agents should detect mathematical obstruction before acting

Status: exactly supported in finite deterministic worlds. Recovery,
obstruction, budget infeasibility, and optimal next action can be separated.
Open, stochastic, misspecified, and large natural systems remain future work.

### H10 - Maintained concern requires self/world attribution and selective
intervention

Status: a bounded synthetic mechanism exists, but architecture and calibration
failures remain. The program supports computational precursors, not a claim of
selfhood or consciousness.

### H11 - Specifications can stay green while objectives silently drift

Status: proved for the registered zero-leakage finite kernel. Real
specifications' leakage and real delegate behavior remain open empirical
halves.

### H12 - Discovery is a regime transition rather than high-scoring search

Status: a methodological rule supported by the repository's own correction
history. It is not yet an externally validated detector of scientific
discovery.

## 15. Documentation and status contradictions

The audit preserves the following contradictions as findings.

- Current policy says SafeVerify plus axioms contained in `{propext}` is needed
  for "verified." The Wave 5-12 receipt accepts `Quot.sound` and labels several
  such headlines passed. Those rows require policy clarification.
- Several papers say all named theorems are machine-checked or Lean-verified,
  while the current theorem backlog still marks general SIC-A, probability-space
  T4, classical T7, CT-1 MDL, naked TA-1, and other claims prose-only.
- The structural-intelligence-foundations paper calls mathlib predecessors
  verified; the latest receipts classify the mathlib lane as proved-not-verified.
- The Theory Atlas paper's unqualified gluing iff is superseded by an honesty
  ledger requiring injectivity or an equivalent guard.
- The top-level TODO contains stale tasks to install Lea and run initial proof
  waves even though later receipts record a local environment and many replayed
  waves.
- Early EML prose says US-4 prime is untested; later experiments establish a
  process split. Only the intended neural bootstrap and general law remain open.
- PAC-Bayes and some counterexample instruments use `status: pass` while the
  promoted scientific claim is false or withheld. Runner success and scientific
  adjudication must remain separate fields.
- Legacy paper-only packages are indexed for provenance but often lack a
  structured manifest, exact result summary, or independent adjudication. They
  should not be counted as equal-strength evidence.

## 16. Open conjectures and decisive next tests

### Formal residuals

- General measure-theoretic SIC-A and probability-space T4.
- A fully scoped classical ICA theorem rather than a finite signed-permutation
  class witness.
- CT-1 probabilistic MDL consistency and its quantitative rate.
- TA-1 with exact necessary assumptions and a minimal cocycle-closing
  enlargement theorem.
- Continuous or unique repair calculus statements with interacting-lift
  pushouts.
- A locally proved PAC-Bayes KL theorem or an explicit imported theorem object.
- A process-indexed access theorem that states when fiber statistics transport
  to a sampler, optimizer, or rewrite system.

### Empirical residuals

- A sealed learned-geometry concern-gated retrieval experiment without role or
  order leakage, followed by natural transfer only if the synthetic gates pass.
- Causal activation-space interventions that beat random-relation and
  wrong-subspace controls across model scales.
- A direct attractor test measuring basin volume, return dynamics, and
  perturbation recovery rather than proxy discontinuities.
- Open, stochastic, misspecified adapters for relative identifiability and
  obstruction-aware admission.
- Natural images and open semantics for concerned syntax, plus genuinely neural
  typed-body search.
- Disjoint or constrained self/world heads and counterfactual interventions
  that break the current attribution gauge.
- Odrzywolek-style neural bootstrap tests that distinguish formula search,
  known-structure optimization, and sampling.
- External weakness studies whose group, task, and intervention define a real
  causal transport test rather than a correlational proxy.

## 17. Final synthesis

The complete system can be stated compactly.

1. Tasks induce equivalence relations on realizations.
2. Quotients retain task-relevant structure; fibers retain ignored variation.
3. Compilers and search processes determine which fiber members are accessible.
4. Concern reweights realization and action without automatically changing the
   quotient.
5. Viability and intervention close the loop from representation to control.
6. Representations form a task-relative Pareto antichain, not one hierarchy.
7. Obstruction pairs and cocycle discrepancies diagnose why a claim cannot
   descend or glue.
8. Repair restores a coordinate, changes a quotient, or adds transport, but no
   cheap universal repair selector survives.
9. Identification and admission should distinguish recovery, impossibility,
   budget limits, and next action.
10. Scientific discovery is credible only when residual content survives
    controls and changes an accepted type, operation, mechanism, or verifier.

The system's durable center is therefore not the slogan that geometry explains
intelligence. It is a disciplined calculus of what a task treats as the same,
what a process can realize, what an intervention can distinguish, what a system
must preserve, and which claims survive their gates.

The grand synthesis remains a conjecture. The finite formal core is real. The
empirical boundaries are unusually informative. The failures are not debris;
they are the map of where the current regime stops.

## Source map for the narrative

Primary synthesis sources include `README.md`, `TODO.md`,
`docs/system_design.md`, `docs/discovery_regime_audit.md`,
`docs/verification.md`, `docs/verification.json`,
`docs/claim_registry.json`, `docs/program_evidence_registry.json`,
`docs/experiment_contract_registry.json`, `docs/lea/theorem_backlog.md`,
`docs/lea/VERIFY_RECEIPT_2026-08-17.md`, and
`docs/lea/VERIFY_RECEIPT_2026-08-18.md`.

Core theory sources include `papers/structural_intelligence/paper.md`,
`papers/structural_intelligence_foundations/paper.md`,
`papers/theory_atlas/paper.md`, `papers/causal_semantics/paper.md`,
`papers/representation_repair_calculus/paper.md`,
`papers/delete_the_absolute/paper.md`, `papers/sic_dynamics/paper.md`,
`papers/eml_universal_substrate/paper.md`,
`papers/eml_access_geometry/paper.md`,
`papers/concern_as_fiber_geometry/paper.md`,
`papers/weakness_invariance_neurips/paper.md`,
`papers/information_limited_discovery/paper.md`,
`papers/relative_identifiability/paper.md`, and
`papers/obstruction_aware_admission/paper.md`.

The generated appendices that follow in the PDF are authoritative indexes of
the checked-in claim registry, evidence registry, experiment packages,
preregistered hypotheses, result-status signals, and Lean declarations at the
audited commit. They are generated from repository sources at build time so the
atlas can be reproduced and drift can be detected.
