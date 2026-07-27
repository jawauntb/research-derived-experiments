# Preregistration: Representation Swap, Future-Commitment Quotient

**Frozen:** 2026-07-27 15:14 EDT, before implementation or result inspection.

## Decision and claim boundary

The registered question is:

> For deterministic finite agents under a fixed, exhaustive intervention
> alphabet, do future-commitment equivalence classes remain invariant when
> internal coordinates are destroyed, and change when delayed transition
> constraints change while those coordinates and all depth-one commitment
> observations are preserved?

The strongest positive conclusion is deliberately narrow:

> In the registered finite Moore-machine families, the maximal
> commitment-bisimulation quotient is a coordinate-invariant, sufficient, and
> minimal state abstraction for all registered future interventions; raw
> coordinates and depth-one commitment observations are neither necessary nor
> sufficient for that scoped behavioral equivalence.

This is a constructive theorem-and-benchmark claim. It is **not** a claim that:

- all intelligence is constraint transport;
- representational objects are meaningless or nonexistent;
- the quotient recovers semantic, historical, or scientific constraints;
- a learned system can discover which constraint to relax;
- the quotient is a new mathematical object;
- the result overturns the rejected Constraint-Swap geometry experiment.

Classical automata minimization, state abstraction, and bisimulation are prior
art for the formal core. A recent bounded-interaction Myhill--Nerode theorem
also proves canonical minimal quotients for finite POMDP probe families. The
paper must describe the present theorem as a deterministic finite-agent
specialization and the experiment as an exact diagnostic double dissociation,
not as a new quotient theorem.

## Target object and decision

- **Target object:** a deterministic Moore agent
  \(A=(X,U,\delta,\pi,E)\), where \(X\) is a finite state set, \(U\) is a
  finite intervention alphabet, \(\delta:X\times U\to X\) is total,
  \(\pi:X\to Y\) is a deterministic commitment label, and
  \(E:X\to\mathbb R^d\) is an injective coordinate realization.
- **Decision:** accept, reject, or withhold the scoped statement that the
  commitment-bisimulation quotient, rather than \(E\), is the complete
  coordinate-invariant object for registered future commitments.
- **Observational unit:** one aligned state pair in one machine-family,
  condition, and fixed seed; agent-level gates aggregate exact state-pair
  checks without treating them as independent samples.
- **Data clock:** no wall-clock or training clock. The only clock is
  intervention-word length. Depth zero is the current commitment; depth one
  is the local baseline; the exact quotient ranges over all finite words via
  partition refinement.
- **Evidence paths:** public exact rows and summaries live under
  `experiments/future_commitment_quotient/results/`; implementation tests live
  in `tests/test_future_commitment_quotient.py`; the paper lives under
  `papers/future_commitment_quotient/`.

## Formal objects, domains, and units

Let \(U^\ast\) be the set of finite intervention words. Extend \(\delta\) by
\(\delta^\ast(x,\epsilon)=x\) and
\(\delta^\ast(x,wu)=\delta(\delta^\ast(x,w),u)\).

The future-commitment signature is

\[
\Sigma_A(x)=\left(\pi(\delta^\ast(x,w))\right)_{w\in U^\ast}.
\]

States from possibly different agents are future-commitment equivalent when

\[
x\equiv_\Sigma y
\quad\Longleftrightarrow\quad
\forall w\in U^\ast,\;
\pi_A(\delta_A^\ast(x,w))=\pi_B(\delta_B^\ast(y,w)).
\]

The maximal commitment-bisimulation relation \(R\) satisfies

\[
xRy \Longrightarrow
\pi_A(x)=\pi_B(y)
\;\land\;
\forall u\in U,\;\delta_A(x,u)R\delta_B(y,u).
\]

All quantities are dimensionless. Coordinate distances are Euclidean only
within one registered \(E\); they are baselines, not the target object.
Coordinate realizations have a common dimension within each factorial cell so
that equality and distance comparisons are typed. No cross-dimensional
padding is permitted.

## Theorem roadmap

### T1: Future-commitment completeness

For any two registered finite deterministic agents with the same \(U\) and
\(Y\), \(x\equiv_\Sigma y\) iff \(x\) and \(y\) are related by the greatest
commitment bisimulation on their disjoint union.

**Dependencies:** total deterministic transitions, common typed alphabets, and
exact commitment equality.

### T2: Gauge invariance under conjugacy

For a bijection \(g:X\to X'\) with
\(g(\delta(x,u))=\delta'(g(x),u)\) and
\(\pi(x)=\pi'(g(x))\), every state and its image have identical
future-commitment signatures. The quotient is isomorphic even if coordinate
identity and geometry change.

**Dependencies:** bijectivity and exact transition/commitment preservation.

### T3: Minimal sufficient quotient

If \(r:X\to Z\) is any deterministic state abstraction with a well-defined
output map and total abstract transition maps satisfying
\(r(\delta(x,u))=\bar\delta(r(x),u)\), then
\(r(x)=r(y)\Rightarrow x\equiv_\Sigma y\). Therefore \(r\) refines the
commitment-bisimulation quotient, and the quotient is the coarsest exact
abstraction for all registered commitments.

**Dependencies:** the abstraction is Markov and exact. A non-Markov summary or
approximate predictor is outside the theorem.

### T4: Finite distinguishing bound

If states in agents with \(n_A\) and \(n_B\) states are not equivalent, breadth
first search on the product machine returns a distinguishing word of length
strictly less than \(n_A n_B\).

**Dependencies:** finite state sets and total deterministic transitions.

These statements are expected consequences of Moore-machine minimization and
bisimulation. The run verifies the implementation against them; simulation is
not presented as their proof.

## Competing hypotheses

### H0: Coordinate/local-representation primacy

Preserving the registered internal coordinates and depth-one commitment
responses is sufficient for future behavioral equivalence; destroying those
coordinates predicts behavioral change.

### H1: Future-commitment quotient primacy

Coordinate identity can be destroyed without behavioral change when the
transition/commitment structure is conjugate, while delayed behavior can
change despite identical coordinates and depth-one responses when a
load-bearing transition changes.

### H2: Registered-family insufficiency

The factorial construction or intervention alphabet fails to distinguish the
hypotheses. Any unknown theorem precondition, missing condition cell, failed
scramble integrity check, or absent delayed witness withholds the central
claim.

## Registered machine families

The confirmatory suite contains three independently specified delayed-rule
families:

1. **Parity memory:** a two-valued memory updated by binary interventions.
2. **Modulo-three memory:** a three-valued accumulator with two nonidentical
   updates.
3. **Order memory:** a three-valued finite memory distinguishing whether zero
   or one was most recently registered.

Each family crosses memory with a three-step commitment clock. Commitments are
`defer` before the terminal phase and family-specific `accept`/`reject` at the
terminal phase. The alphabet is exactly
`zero`, `one`, `advance`, and `reset`.

The delayed mutant changes exactly one registered memory transition at phase
zero. It must preserve:

- the state set;
- the coordinate matrix;
- every current commitment;
- every depth-one commitment response;
- the alphabet and clock transitions.

It must change at least one later commitment, witnessed at depth between two
and \(n_A n_B-1\).

## Four factorial conditions

| Condition | Coordinates | Transition constraint | Registered prediction |
|---|---|---|---|
| RP-CP | preserved | preserved | behavior preserved |
| RD-CP | destroyed | preserved by conjugacy | behavior preserved |
| RP-CA | preserved exactly | delayed edge altered | behavior changes |
| RD-CA | destroyed | delayed edge altered | behavior changes |

`RP`/`RD` mean representation preserved/destroyed. `CP`/`CA` mean future
constraint preserved/altered.

For each seed, `RD-CP` and `RD-CA` use the same state permutation and the same
injective hash-derived coordinate matrix. This pairing forces coordinate
statistics to be independent of the constraint label rather than relying on
an average over favorable random draws.

## Coordinate-destruction integrity

The preserved realization is a typed structural coordinate map containing
normalized clock, normalized memory, their interaction, and fixed nonlinear
features. The destroyed realization assigns fixed-seed continuous coordinates
to permuted states without using transitions or commitments.

An RD cell is valid only if:

1. the coordinate map is injective;
2. no coordinate row is preserved under the registered state alignment;
3. its off-diagonal Euclidean distance matrix is not identical to the RP
   distance matrix;
4. the state permutation is non-identity;
5. the transition and output conjugacy equations pass exactly for CP.

Scramble generation may reject a seed only for these pre-outcome integrity
conditions. It may not inspect a gate metric or distinguishing witness.

## Baselines and primary estimands

For each aligned agent pair:

- **coordinate equality:** fraction of aligned coordinate rows exactly equal;
- **coordinate geometry:** Pearson correlation between off-diagonal Euclidean
  distance matrices;
- **current-output agreement:** fraction of aligned states with equal
  depth-zero commitment;
- **depth-one agreement:** fraction of state/intervention pairs with equal
  successor commitment;
- **quotient agreement:** fraction of aligned states related by the greatest
  cross-agent commitment bisimulation;
- **behavioral disagreement:** fraction of aligned states separated by the
  finite distinguishing basis;
- **shortest witness:** minimum distinguishing-word length, or `null` when
  equivalent.

The primary predictor comparison uses leave-one-family-out thresholding.
Coordinate geometry, current-output agreement, depth-one agreement, and
quotient agreement each predict whether the full future constraint is
preserved. Balanced accuracy is used because constant baselines make AUROC
undefined.

## Exact run

- Confirmatory seeds: integers 0 through 63.
- Smoke seeds: integers 1000 through 1003; never enter confirmatory results.
- No learned hyperparameters and no stochastic training.
- All transitions, quotient blocks, product searches, and metrics are computed
  exactly except floating-point coordinate distances.
- The public row set contains all 3 families × 64 seeds × 4 conditions = 768
  rows.

## Noncompensatory gates

### F0: Construction and provenance

Pass only if the manifest, design, preregistration digest, family definitions,
seed sets, row count, and four factorial cells are exact; smoke and
confirmatory seeds are disjoint; every RD integrity check passes; and no result
file predates the frozen preregistration commit.

### F1: Formal implementation checks

Pass only if T1--T4 are matched by exhaustive executable checks on every
registered agent pair, quotient refinement reaches a fixed point, every
reported equivalent pair has no product-search witness, and every reported
inequivalent pair has a valid witness shorter than \(n_A n_B\).

### G1: Representation non-necessity

Pass only if every RD-CP row has zero behavioral disagreement, quotient
agreement exactly one, a quotient isomorphism, and destroyed-coordinate
integrity; no family or seed may fail.

### G2: Representation/local non-sufficiency

Pass only if every RP-CA row has coordinate equality, current-output
agreement, and depth-one agreement exactly one, while quotient agreement is
strictly below one and a valid delayed witness of length at least two exists;
no family or seed may fail.

### G3: Factorial predictor separation

Pass only if quotient agreement attains leave-one-family-out balanced accuracy
1.0 and each coordinate/current/depth-one baseline is at most 0.5. This is an
exact diagnostic separation within the constructed factorial, not an estimate
of natural-data performance.

### G4: Family transfer

Pass only if G1--G3 hold separately for parity, modulo-three, and order memory.
Pooling cannot rescue a failed family.

### G5: Claim calibration

Pass only if the paper:

- cites automata minimization, MDP state abstraction/bisimulation,
  representation non-identifiability, and causal abstraction;
- identifies the 2026 bounded-interaction Myhill--Nerode result as overlapping
  prior art;
- labels T1--T4 as proved specializations/corollaries rather than novel
  theorems;
- preserves the earlier Constraint-Swap null;
- withholds claims about learned constraint discovery, stochastic agents,
  real networks, natural tasks, and general intelligence.

The positive decision is `ACCEPT_SCOPED_FINITE_QUOTIENT_CLAIM` only if F0, F1,
and G1--G5 all pass. Otherwise the decision is
`WITHHOLD_SCOPED_FINITE_QUOTIENT_CLAIM`. No aggregate score can compensate for
a failed gate.

## Edge, limiting, and null cases

Executable checks must include:

- empty intervention word;
- one-state constant-output machine;
- all states output-identical but future-distinguishable;
- already minimal and fully collapsed quotients;
- identity and non-identity permutations;
- invalid noninjective coordinates;
- invalid transition tables and alphabet mismatch;
- equivalent states with redundant raw coordinates;
- altered edge with no reachable commitment effect, which must be rejected as
  a non-load-bearing mutant;
- shortest witness at depth two and a no-witness equivalent pair.

## Failure and stopping rules

- If F0 or F1 fails or is unknown, stop and withhold every theorem-facing
  empirical claim.
- If any one of G1--G4 fails, reject the double dissociation. Do not tune the
  mutant, scramble, family, seed, or threshold on confirmatory rows.
- If G5 fails, the mathematical checks may remain valid, but the paper cannot
  present them as a novel or major-ML result.
- If the quotient wins only because the target label is definitionally copied
  into a feature, report the construction as a tautological validator and
  withhold predictive-superiority language.
- A failure may motivate a separately preregistered successor. This run is not
  repaired after result inspection.

## Discovery-Regime Audit

**Question:** Does the proposed “constraint preserved to commitment” object
reduce, in the decisive finite case, to an exact coordinate-free quotient that
supports the claimed double dissociation?

**Current regime:**

- Artifact types: finite agents, coordinate realizations, transition tables,
  quotient partitions, witnesses, gate verdicts, and papers.
- Operations: conjugacy, delayed-edge mutation, partition refinement, product
  search, exact factorial comparison, and document review.
- Gates/verifiers: F0--G5 plus unit, lint, type, registry, provenance, and PDF
  checks.
- Known limitations: deterministic finite agents; white-box exhaustive access;
  fixed intervention alphabet; constructed factorial; no learning.

**Action class:** formal reduction and decisive verification inside an existing
automata/bisimulation schema. The benchmark packaging may be new to this
program, but the quotient itself is not registered as a discovery.

**Positive targets:** exact conjugacy invariance, exact delayed-transition
separation, quotient sufficiency/minimality, and family-level replication.

**Negative controls:** coordinate-preserved mutant, coordinate-destroyed
conjugate, identity clone, scrambled mutant, constant-output edge cases, and
the failed Constraint-Swap geometry result.

**Acceptance rule:** all noncompensatory gates pass at their stated scope.

**Withheld rule:** failed/unknown gates, novelty overstatement, or extension
beyond the registered finite white-box regime.

**Residual content if accepted:** learning the quotient from partial traces,
choosing an intervention family, discovering load-bearing constraints, and
performing minimal repair remain open.

