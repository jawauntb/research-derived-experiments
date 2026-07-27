# Preregistration: Constraint-Swap Causal Geometry

**Frozen:** 2026-07-27 03:41:10 EDT, before implementation or result inspection.

## Design amendment 1 - 2026-07-27 03:48 EDT, before any model training

The proof-first F0 unit test rejected the initial vertical-fiber versus
horizontal-fiber design. Its reachable-future RDMs were identical under an
action-axis relabeling, and its marginal behavior-action counts differed
maximally (vertical moves versus horizontal moves). That design therefore could
not distinguish a metric deformation from a coordinate rename or action
frequency.

Before any model was trained, the active design was replaced with two balanced
future-admissibility constraints on an even grid:

- \(C_A\): current and goal have the same checkerboard parity;
- \(C_B\): current and goal have the same horizontal-stripe parity.

The behavior is the binary decision `accept`/`reject`; physical action suffixes
remain \(N,S,E,W,\mathrm{stay}\) in the independently enumerated future
language. Both constraints have exactly 50% accept/reject labels, while their
future-language RDMs are non-collinear on the frozen probe set. A third
deterministic rule \(C_D\), equality of vertical-stripe parity, is the
equally-balanced learnable control. The active grids are a \(6\times6\) torus
and untouched \(7\times7\) horizontal cylinder. The rejected fiber design and
its failing test evidence remain in Git history and this amendment.

## Analysis amendment 2 - 2026-07-27 04:10 EDT, before confirmatory seeds

The metric implementation made two preregistered controls explicit:
`history_identity` and `probe_frequency` are exactly constant because matched
histories are averaged before the unit RDM and every unit has eight probes.
Including zero columns would make the nuisance design rank-deficient by
construction. They are therefore tested and reported as zero-variance integrity
controls, not entered as regression columns. All other registered nuisances
must enter the design unless a deterministic pre-outcome rank check identifies
exact collinearity; any such exclusion is reported. No threshold or endpoint
changed.

## Decision and claim boundary

The registered question is:

> In a finite, exactly enumerable goal-navigation world, does changing only the
> conditional rule that determines successful futures change a frozen
> meta-recurrent agent's reachability-aligned hidden geometry, and do
> state-independent low-rank transports of that geometry selectively reverse
> and accelerate the corresponding behavior?

The strongest possible positive conclusion is an existence result for the
registered model, tasks, intervention class, seeds, and topologies:

> A constraint-conditioned, reachability-aligned hidden subspace is causally
> relevant to behavior in this controlled regime.

This experiment cannot prove that every goal, meaning, or intelligent behavior
is a constraint-induced deformation. A valid negative can reject the complete
registered causal chain in this regime only after competence, measurement
sensitivity, and intervention-validity gates pass. Otherwise the result is
withheld rather than treated as evidence that no relevant representation
exists.

The experiment does **not** claim "the same information." Different constraints
necessarily convey different conditional information. It matches the
observation alphabet, transition kernel, example schedule, feedback channel,
feedback timing, scalar feedback magnitude, action budget, marginal task
entropy, model initialization, architecture, and optimizer budget.

## Formal objects

### Environment and constraints

For topology \(g\), the finite world is

\[
\mathcal X_g = \mathbb Z_{n_x}\times\mathbb Z_{n_y},\qquad
\mathcal A_0 = \{N,S,E,W,\mathrm{stay}\},\qquad
\mathcal Y=\{\mathrm{reject},\mathrm{accept}\}.
\]

A decision unit is \(u=(x,g^\star)\in\mathcal U_g=\mathcal X_g^2\), where
\(x\) is the current cell and \(g^\star\) is the goal. The physical transition
map \(f_g(x,a)\) is fixed within a topology. The active constraint is hidden
from the model:

- The original vertical-fiber \(C_A\) was rejected in Design amendment 1. The
  active \(C_A\) accepts iff
  \((x_1+x_2)\bmod2=(g^\star_1+g^\star_2)\bmod2\).
- The rejected horizontal-fiber \(C_B\) was replaced by the active rule that
  accepts iff \(x_1\bmod2=g^\star_1\bmod2\).
- The learnable deterministic control \(C_D\) accepts iff
  \(x_2\bmod2=g^\star_2\bmod2\).

These exact orthogonal conservation laws replace the proposal's informal
"parity" and "orientation" labels. The replacement is deliberate: a decisive
experiment requires fully typed dynamics and success languages.

The primary topology is a \(6\times6\) torus. The untouched transfer topology
is a \(7\times7\) cylinder: the horizontal axis wraps and the vertical axis
reflects. The observation gives normalized current/goal coordinates, signed
shortest displacements, coordinate-equality bits, parity-relation bits, and
boundary bits; it never gives the active constraint.

### Policy-free reachable-future language

Let \(\mathcal A_0=\{N,S,E,W,\mathrm{stay}\}\), horizon \(H=4\), and
\(\alpha\in\mathcal A_0^H\) be an open-loop action suffix. For deterministic
topology \(g\),

\[
\phi_{C,g}(u)_\alpha =
|\mathcal A_0|^{-H/2}
\mathbf 1\!\left[
  u\text{ is }C\text{-admissible and }
  f_g^{(\alpha)}(x)=g^\star
\right].
\]

The registered constraint-conditioned reachability distance is

\[
d^2_{\mathrm{reach},C,g}(u,v)
=
\|\phi_{C,g}(u)-\phi_{C,g}(v)\|_2^2.
\]

The reachability volume

\[
V_{C,g}(u)=\sum_\alpha \phi_{C,g}(u)_\alpha^2
\]

is reported and residualized separately so the primary alignment is not merely
similar success-count proximity. This is a feasibility object, not a
policy-conditioned successor representation.

### Recurrent information state

The model never has a representation \(h(x)\) independent of history. Its
information state is

\[
\eta_t=(o_{0:t},a^\star_{0:t-1},r_{0:t-1}),\qquad
h_\theta(u,\eta_t)=\mathrm{GRU}_\theta(\eta_t,o(u)).
\]

Each demonstration supplies the oracle action \(a^\star\) and a constant
feedback token \(r=1\). This teacher-forced design exactly matches feedback
frequency and magnitude while varying only the conditional
unit-to-success/action mapping. Query behavior is measured after a fixed
number of demonstrations without giving a symbolic task label.

The architecture, insertion point, and probe clock are fixed:

- one-layer GRU;
- 48 hidden units;
- hidden output after the query observation and before the linear action head;
- 12 demonstrations for mature contexts;
- one new-task demonstration for the early-swap context;
- eight balanced probe histories per decision unit and context.

## Representation metric and alignment estimand

Probe histories are divided into two fixed halves. Let
\(\mu_u^{(1)},\mu_u^{(2)}\) be split-half hidden means. A shrinkage residual
covariance \(\widehat\Sigma\) is estimated from calibration probes only. The
registered hidden dissimilarity is the symmetrized split crossnobis distance

\[
d^H(u,v)=
(\mu_u^{(1)}-\mu_v^{(1)})^\top
\widehat\Sigma^{-1}
(\mu_u^{(2)}-\mu_v^{(2)}).
\]

Let \(y=\operatorname{vec}_\triangle(D_H)\),
\(x_C=\operatorname{vec}_\triangle(D_{\mathrm{reach},C})\), and let \(Z\)
contain an intercept plus preregistered nuisance dissimilarities:

1. sensory observation distance;
2. unconstrained physical shortest-path distance for current and goal cells;
3. time/history identity;
4. reachability-volume difference;
5. oracle-action equality;
6. exogenous probe frequency.

With \(M_Z=I-ZZ^+\), the primary partial alignment is

\[
A_C=\operatorname{cor}(M_Zy,M_Zx_C).
\]

The active-constraint geometry contrast is

\[
g=A_B-A_A.
\]

For an \(A\to B\) swap, the counterfactual no-swap-adjusted estimand is

\[
\tau_G =
\{g_{\mathrm{post}}-g_{\mathrm{pre}}\}_{A\to B}
-
\{g_{\mathrm{post}}-g_{\mathrm{pre}}\}_{A\to A}.
\]

The reciprocal \(B\to A\) contrast is registered and must pass separately.
The independently trained seed pair, not a state pair or trajectory, is the
inferential unit.

## Conditions and controls

The confirmatory evaluation contains:

1. mature \(A\) context;
2. mature \(B\) context;
3. randomized-label sham with the exact active-task action histogram;
4. a deterministic learnable non-reachability rule matched for label entropy;
5. \(A\to A\) and \(B\to B\) no-swap controls;
6. \(A\to B\) and \(B\to A\) counterbalanced swaps;
7. identity, opposite-direction, anchor-pair-permuted, and
   rank/norm/covariance-matched random latent transports;
8. dose \(0,0.5,1.0,1.5\) for targeted and random transports;
9. an injected known-geometry positive control for measurement sensitivity.

All schedules are generated before model evaluation. Confirmatory training
seeds are integers 0 through 31. Seeds 1000 through 1003 are implementation
smoke seeds and can never enter a confirmatory interval. No confirmatory
hyperparameter, layer, checkpoint, metric, rank, or threshold may be selected
from seeds 0 through 31.

## State-independent latent transports

Decision units are split by a stable hash into 60% transport-calibration
anchors and 40% untouched tests. No test unit or transfer-topology unit enters
transport fitting.

For paired hidden matrices \(H_S,H_T\), ridge regression estimates an affine
delta map, and a fixed rank-\(r=4\) SVD truncation produces

\[
T_{S\to T}(h)=h+b+hUV^\top,\qquad \operatorname{rank}(UV^\top)\le4.
\]

The map is state-independent and is applied once at the registered query
hidden output immediately before the unchanged action head. Primary causal
estimands are:

\[
N_B =
\mathbb E[\mathrm{Acc}_B(I)]
-
\mathbb E[\mathrm{Acc}_B(T_{B\to A})],
\]

\[
S_B =
\mathbb E[\mathrm{Acc}_B(T_{\mathrm{early}\to B})]
-
\mathbb E[\mathrm{Acc}_B(T_{\mathrm{matched\ random}})].
\]

The \(A\) direction is symmetric and must pass independently. These are
"selective impairment" and "selective rescue" tests. The terms necessity and
sufficiency apply only relative to the registered subspace, query-surface
intervention, and frozen background network; the experiment does not identify
a natural indirect effect or complete mediation.

## Statistical plan

- Report every seed as one paired row.
- Use a deterministic 10,000-resample paired seed bootstrap.
- Primary intervals are one-sided 95% lower confidence bounds for positive
  effects and two-sided 90% equivalence intervals for preservation outcomes.
- The overall positive result is an intersection-union claim: every fatal gate
  below must pass. Strong downstream effects cannot compensate for an upstream
  failure.
- Directions and topologies are not pooled to rescue a failure.
- Confirmatory endpoints are fixed below; exploratory metrics are labeled and
  cannot replace them.

## Noncompensatory gates

### F0 - Integrity and identifiability

Pass only if:

- every transition, success suffix, observation, target, split, and schedule is
  exactly reproducible from the manifest and seed;
- \(D_A\) and \(D_B\) are non-collinear after nuisance residualization;
- every nuisance design is full rank with maximum variance-inflation factor
  below 10;
- A/B exposure counts, feedback timing/magnitude, and marginal oracle-action
  counts match exactly;
- no confirmatory unit leaks into transport fitting.

Failure or unknown status blocks every geometry and causal claim.

### F1 - Competence and measurement sensitivity

Pass separately on the primary and transfer topology only if:

- mean mature query accuracy for both A and B is at least 0.85;
- at least 28 of 32 seeds exceed 0.80 on both tasks;
- randomized-sham accuracy is at most 0.10 above two-action chance;
- deterministic-control accuracy is at least 0.75;
- the known-geometry positive control has a lower confidence bound above 0.20.

A failure makes a null geometry/intervention result uninterpretable.

### G1 - Constraint-specific geometry

For both A and B, the paired bootstrap lower bound for
\(A_{\mathrm{active}}-A_{\mathrm{inactive}}\) must exceed 0.05, and the active
alignment must exceed sensory, physical, action, and randomized-sham alignment.
The same direction must hold on at least 28 of 32 seeds. A descriptive geometry
claim fails if this gate fails.

### G2 - Swap tracking

The paired lower bound for \(\tau_G\) must exceed 0.05 for both \(A\to B\) and
\(B\to A\), with no-swap absolute drift below 0.05. The gate must pass
separately on the untouched cylinder topology.

### G3 - Selective impairment

For each direction:

- the targeted undo must reduce active-task accuracy by at least 0.10 more than
  the strongest matched random/permuted control;
- the lower bound on active-to-opposite compatible error shift must exceed
  0.05;
- the transport must move the registered geometry contrast in the intended
  direction;
- state/goal decoding loss must lie within a 0.03 equivalence margin;
- activation norm and covariance drift must remain within 10% of the mature
  context reference;
- the dose response must be monotone from 0 through 1.0.

### G4 - Selective rescue

For each direction:

- the early targeted transport must improve active-task accuracy by at least
  0.10 more than the strongest matched random/permuted control;
- the lower bound on the compatible-choice shift must exceed 0.05;
- geometry movement and nuisance-preservation criteria from G3 must pass;
- the dose response must be monotone from 0 through 1.0.

### G5 - Topology transport

F0 through G4 must all pass without refitting the GRU, action head, metric,
transport rank, or thresholds on the \(7\times7\) cylinder. The affine transport
may be fit only on primary-topology anchors. This supports one fixed-topology
transfer, not generalization to a population of topologies.

## Decision table

- **All F0-F1 and G1-G5 pass:** accept the scoped existence claim.
- **F0 or F1 fails:** WITHHELD; the test cannot adjudicate the causal principle.
- **F0-F1 pass, G1 fails:** reject constraint-specific deformation in this
  regime.
- **F0-F1 and G1-G2 pass, G3 or G4 fails:** retain descriptive/swap-tracking
  geometry but reject the registered geometry-to-behavior causal chain.
- **Primary passes but G5 fails:** retain the primary-topology claim and reject
  topology transport.
- Random, sham, no-swap, or deterministic non-reachability controls matching a
  primary effect reject the corresponding specificity claim.

Failed and superseded artifacts remain in the evidence ledger.

## Discovery-Regime Audit

**Question:** Does a constraint change behavior through a
reachability-aligned hidden subspace?

**Current regime**

- Artifact types: finite MDP/topology, future-language RDM, recurrent hidden
  RDM, seed row, transport, gate verdict, paper, PDF.
- Operations: exact suffix enumeration, paired meta-GRU training,
  split-crossnobis RSA, nuisance residualization, low-rank affine transport,
  seed bootstrap, topology transfer.
- Gates/verifiers: F0-F1 and G1-G5, unit tests, numerical identities, lint/type
  checks, PDF render inspection.
- Store: raw seed rows under gitignored `artifacts/`; compact results under
  `experiments/constraint_swap_causal_geometry/results/`; paper under
  `papers/constraint_swap_causal_geometry/`.

**Action class:** Search inside the existing learned-systems/causal-intervention
schema. A positive result is not called a new discovery regime unless the
future-language verifier and intervention survive all controls.

**Positive targets:** active reachability alignment, counterbalanced swap
tracking, selective impairment, selective rescue, topology transport.

**Negative controls:** random-label sham, deterministic non-reachability task,
no-swap drift, wrong-direction transport, permuted anchors, matched random
low-rank transports.

**Withheld/rejected rule:** any unknown or failed fatal prerequisite blocks the
dependent claim; rejected alternatives and raw rows are preserved.

## Mathematical audit

- Objects are finite sets and real-valued matrices; distances are dimensionless.
- The constraint language and horizon are explicit.
- The future-language metric is a Euclidean pseudometric; distinct decision
  units may have distance zero when their success languages coincide.
- Crossnobis values may be negative in finite samples; no nonnegativity claim is
  made for that estimator.
- Affine transports are not coordinate-invariant causal objects. Their claim is
  restricted to the frozen hidden basis and fixed action head.
- Null and edge cases tested executably include identical units, empty
  reachable languages, unreachable goals, already-satisfied goals, reflected
  boundaries, rank-deficient nuisance matrices, zero-dose identity, and
  rank-zero transports.
