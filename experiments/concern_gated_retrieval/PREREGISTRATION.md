# Concern-Gated Off-Context Retrieval - Preregistration

**Frozen design date:** 2026-07-23
**Package:** `experiments/concern_gated_retrieval/`
**Human director:** Jawaun Brown
**Evidence class:** deterministic synthetic diagnostic
**External method source:** Zhang and Levin (2026), *Intelligence from
Learnable Novelty*, arXiv:2607.18433v1, equations (7)-(9).

## Abstract

A bounded observer cannot load everything it knows into its active
representation and must instead nominate a small set of off-context facts that
could improve its trajectory without destabilizing it. We test a
concern-gated retrieval rule on typed synthetic memory graphs containing one
load-bearing node, one-sided context and care distractors, a high-salience
alarm, a dual-activated coincidence trap, and neutral nodes. The proposed
method computes personalized PageRank from active context and persistent care,
ranks candidates by their rarity-corrected Hadamard product, and applies a
goal-conditioned bounded-observer verifier based on Zhang and Levin's
closed-form reservoir/ridge epiplexity estimator. Registered controls are
context-only PageRank, care-only PageRank, additive PageRank, unverified
coincidence ranking, constant futures, and shuffled-noise futures. A separate
exploratory condition updates care-anchor weights only from the observed
utility of the nominated probe. The experiment supports only a synthetic
algorithmic claim: joint diffusion and bounded-observer verification can be
tested for discriminating registered graph roles. It does not test human
memory, semantic meaning, selfhood, or general intelligence.

## Target object and decision

- **Target object:** a candidate-selection rule for a finite typed memory graph
  at one retrieval event.
- **Decision:** promote the composition as a synthetic diagnostic only if all
  fatal gates pass; otherwise retain it as a scaffold or bounded null.
- **Observational unit:** one seeded graph episode with one active-context
  restart set, three care anchors, six off-context candidates, and one
  registered load-bearing candidate.
- **Budget:** nominate at most three of six off-context candidates.
- **Horizon:** one retrieval event plus a 128-step synthetic reachable-future
  trace for each nominated candidate.
- **Units:** graph weights, restart mass, care weights, and PageRank
  probabilities are dimensionless; epiplexity is measured in bits; utility is
  a dimensionless simulator reward in `[-1, 1]`.

## Representation and data clock

The scientific object is candidate selection under bounded context. Its
surrogate is an undirected weighted graph:

\[
G_t=(V_t,E_t,W_t),\quad R_t\subset V_t,\quad C=\{c_1,c_2,c_3\}.
\]

Each episode is generated before policy evaluation from a frozen seed. Node
roles are hidden from the ranking functions but retained by the evaluator.
The graph clock is one episode; the reachable-future clock is a fixed
128-sample phase grid. These are design surrogates, not a claim that natural
memory is undirected, stationary, or graph-complete.

## Mathematical objects and assumptions

Concern warps the base edge weights without changing support:

\[
W^c_{ij}=W_{ij}\left(1+\gamma(c_i+c_j)/2\right),\quad
\gamma=0.45,\quad c_i\geq0.
\]

For restart distribution \(\pi\) and restart probability \(\alpha=0.2\),
personalized PageRank is the unique probability vector

\[
r=\alpha\pi+(1-\alpha)P^\top r.
\]

Dangling mass, if present, returns through \(\pi\). Context and care produce
\(r_{\mathrm{ctx}}\) and \(r_{\mathrm{care}}\). Candidate nomination uses

\[
q(v)=\frac{
  r_{\mathrm{ctx}}(v)r_{\mathrm{care}}(v)
}{
  \max(r_{\mathrm{freq}}(v),10^{-15})^{0.25}
},
\]

where \(r_{\mathrm{freq}}\) is PageRank under a uniform restart. The product is
a soft intersection; it is not claimed to be the unique or optimal
intersection operator.

For each nominated candidate, a frozen random reservoir produces standardized
features \(\widetilde H\), the goal-conditioned future target is centered and
scaled by a fixed unit \(u_Y=1\), and the ridge readout is computed by stable
least squares:

\[
W_\lambda=\arg\min_W\|\widetilde Y-\widetilde HW\|_F^2+
\lambda\|W\|_F^2,\qquad \lambda=2.
\]

The utilization score is the Zhang-Levin estimator

\[
S^\phi(Y\mid X)=\tfrac12\log_2\det(I+\eta W_\lambda W_\lambda^\top),
\qquad\eta=1.
\]

A candidate is retained when \(S^\phi>0.75\) bits. Because the zero baseline
future has zero score after centering, this is also the registered
\(\Delta S^\phi\) threshold in this benchmark.

Material assumptions:

1. Positive edge weights and positive restart mass make the PPR problem
   well-posed.
2. The synthetic load-bearing role is encoded by joint graph proximity and a
   learnable goal-conditioned future. Passing therefore validates the
   implementation and decomposition, not the semantics that created those
   labels.
3. The reservoir, target scale, ridge, graph templates, thresholds, and seeds
   are frozen before the pilot receipt is generated.
4. Online care updates receive only the realized utility of the actually
   selected candidate. The simulator still defines that utility; this does
   not remove the experimenter or establish selfhood.

## Conditions and decisive controls

Every episode contains:

- **load-bearing:** moderately connected to active context and the relevant
  care anchor; future target is structured and goal-conditioned.
- **context-only:** strongly context-connected but care-distant; constant
  future.
- **care-only:** strongly care-connected but context-distant; constant future.
- **alarm:** very strongly attached to a standing alarm concern but weakly
  context-connected; noise future and negative utility.
- **coincidence trap:** moderately attached to both context and alarm concern;
  noise future and negative utility.
- **neutral:** weak diffuse connectivity; constant future.

Registered ranking policies:

1. context-only PPR;
2. care-only PPR;
3. additive \(r_{\mathrm{ctx}}+r_{\mathrm{care}}\);
4. rarity-corrected coincidence product;
5. coincidence top-3 followed by the epiplexity utilization filter.

The pilot uses seeds `64..127` in base, sparse, and noisy graph regimes after
care learning on base-regime seeds `0..63`. No result-dependent threshold
changes are permitted.

## Fatal gates

Fatal gates are noncompensatory.

1. **NUMERICAL_VALIDITY.** Maximum PPR fixed-point L1 residual is at most
   `1e-10`, and structured reachable futures exceed every constant/noise
   control by at least `0.75` epiplexity bits.
2. **DUAL_ACTIVATION_SELECTIVITY.** Coincidence hit@1 is at least `0.85`,
   exceeds the better one-sided policy by at least `0.20` in aggregate, and
   exceeds it by at least `0.10` in every registered graph regime.
3. **UTILIZATION_FILTER.** Within the coincidence top-3 nominations, the
   epiplexity filter has precision at least `0.90` and recall at least `0.90`
   for load-bearing nodes.

The additive baseline is reported as a decisive alternative but is not part of
the dual-vs-single fatal contrast. If additive matches or beats the product,
the claimed need for multiplicative coincidence is withheld even if the three
implementation gates pass.

## Exploratory gate

**ONLINE_CARE_RECOVERY.** Learned-care coincidence hit@1 must not regress from
uniform initialization and must fall within `0.05` of oracle-care hit@1. This
is exploratory and cannot rescue or invalidate the fatal-gate claim. It
supports only "utility feedback can update this synthetic restart prior," not
"selfhood emerges."

## Executable mathematical checks

- PPR vectors sum to one and satisfy their fixed-point equation.
- Concern warping preserves edge support and symmetry.
- Constant targets have zero epiplexity after centering.
- Structured targets beat shuffled-noise targets by the registered margin.
- The spectral price is invariant to orthogonal rotations of the output
  coordinates.
- Results are byte-stable under repeated runs.

## Discovery-regime audit

- **Old regime:** nearest-neighbor or single-restart retrieval scored by
  topical proximity; no separate concern restart or utilization verifier.
- **Transition:** a typed dual-restart graph artifact, Hadamard coincidence
  operator, and goal-conditioned bounded-observer gate.
- **Transported evidence:** standard PPR fixed-point checks, deterministic seed
  receipts, explicit baselines, and Zhang-Levin equations (7)-(9).
- **Rejected alternatives preserved:** context-only, care-only, additive,
  unverified product, constant future, and noise future.
- **Residual finding sought:** whether the product supplies selectivity beyond
  each one-sided walk and whether epiplexity rejects dual-activated traps.
- **Readiness before execution:** mathematical and numerical gates are
  specified; empirical, human, neural, interpretive, and operational validity
  are untested.
- **Allowed claim:** at most `synthetic diagnostic`.
- **Next operation if passed:** replace role-authored graph structure with
  learned memory edges and sealed task utility; do not jump to human or
  selfhood claims.

## Evidence and provenance

- Code: `experiments/concern_gated_retrieval/`
- Tests: `tests/test_concern_gated_retrieval.py`
- Public receipt: `experiments/concern_gated_retrieval/results/summary.json`
- Package provenance: `experiments/concern_gated_retrieval/PROVENANCE.md`
- Source PDF supplied by the human director:
  `/Users/jawaun/Downloads/2607.18433v1.pdf` (external, not committed)

Raw exploratory outputs, if any, remain under gitignored `artifacts/`.
