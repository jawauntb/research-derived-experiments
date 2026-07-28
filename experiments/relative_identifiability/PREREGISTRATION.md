# Preregistration: Experiment-Relative Identifiability

**Frozen:** 2026-07-27 18:14 EDT, before implementation, executable
counterexample search, or Lean proof authoring.

## Decision and claim boundary

The registered question is:

> Given a typed family of experiments and a target property of internal
> realizations, what is the weakest exact obstruction to recovering that target,
> and how must the identifiable quotient change when the experiment family is
> enriched?

The strongest allowed mathematical conclusion is deliberately elementary:

> A target is exactly identifiable from an experiment family if and only if it
> is constant on every fiber of the family's joint observation map; equivalently,
> it factors through the induced observational quotient. A single pair with the
> same complete experiment transcript but different target values is a complete
> obstruction certificate. Adding experiments can only refine the quotient.

This package may establish that the criterion is correctly formalized, executable,
and useful as a MIDAS regression contract. It may **not** claim that:

- the quotient/factorization criterion is a new theorem;
- experiment-relative equivalence is a new mathematical object;
- the richer-family refinement theorem is new;
- the theorem identifies which experiments should be run in a natural system;
- a finite exact table result transfers unchanged to stochastic, continuous,
  adaptive, noisy, or partially observed systems;
- DCR, Constraint Swap, activation geometry, causal representation, or
  mechanistic interpretability are solved by instantiating the schema;
- behavioral indistinguishability implies mechanistic identity or unreality.

The theorem is a standard kernel/quotient factorization fact. Automata
minimization, observational and testing equivalence, comparison of statistical
experiments, causal interventional equivalence, and contextual equivalence are
direct prior-art families. Most decisively for the proposed framing, Nixon
(2026), Proposition 4.11, already states that smaller probe classes induce
coarser quotients. The contribution under test is therefore an executable,
counterexample-first theorem-development benchmark with calibrated cross-domain
instantiations, not a new foundation of identifiability.

## Target object and decision

- **Target object:** a typed finite experiment system
  \(\mathcal E=(R,E,(O_e)_{e\in E},\operatorname{obs})\), a selected
  experiment family \(\Gamma\subseteq E\), and a target
  \(\tau:R\to T\).
- **Decision:** accept, reject, or withhold the claim that the implementation,
  proof, and regression fixtures realize the exact factorization/obstruction
  criterion and refinement law under their stated assumptions.
- **Observational unit:** one ordered realization pair under one complete
  selected-family transcript. Exhaustive finite-table checks aggregate exact
  logical cases; they are not treated as independent statistical samples.
- **Data clock:** none. Experiments are indexed typed observation functions.
  Sequential intervention words may be encoded as experiment names, but the
  core theorem does not assume a temporal model.
- **Evidence paths:** implementation and fixtures live under
  `experiments/relative_identifiability/`; machine-checked proofs live under
  `formal/relative-identifiability/`; executable checks live in
  `tests/test_relative_identifiability.py`; the calibrated theorem note lives
  under `papers/relative_identifiability/`.

## Formal objects, types, domains, and units

Let:

- \(R\) be a type of candidate internal realizations;
- \(E\) be a type of admissible experiments;
- \(O_e\) be the outcome type for experiment \(e\);
- \(\operatorname{obs}_e:R\to O_e\) be the deterministic exact observation map;
- \(\Gamma:E\to\mathrm{Prop}\) select the allowed experiment family;
- \(T\) be a target type;
- \(\tau:R\to T\) be the target to recover.

All objects are unitless unless an instantiated outcome type supplies units.
Equality is typed within each \(O_e\); outcomes from different experiments are
never compared directly.

Define experiment-relative indistinguishability by

\[
r\sim_\Gamma r'
\quad\Longleftrightarrow\quad
\forall e\in\Gamma,\;
\operatorname{obs}_e(r)=\operatorname{obs}_e(r').
\]

Let \(q_\Gamma:R\to Q_\Gamma=R/{\sim_\Gamma}\) be the quotient map. Exact
identifiability of \(\tau\) means that there is a decoder
\(\bar\tau:Q_\Gamma\to T\) satisfying
\(\tau=\bar\tau\circ q_\Gamma\).

For the executable finite specialization, \(R\), \(E\), and every recorded
outcome set are finite; realization names and experiment names are unique; the
outcome table is total; target values and outcomes are hashable; and experiment
families contain only declared experiments.

## Registered theorem package

### T1: Observational equivalence and quotient existence

For every typed system and family \(\Gamma\), \(\sim_\Gamma\) is an equivalence
relation, so \(Q_\Gamma\) exists.

**Dependencies:** exact equality in each outcome type and total observation maps.
Finiteness and decidable equality are not required for the abstract theorem.

### T2: Universal obstruction / factorization criterion

For every target \(\tau:R\to T\), the following are equivalent:

1. \(\tau\) factors through \(q_\Gamma\);
2. \(\tau\) is constant on every \(\sim_\Gamma\) class;
3. there is no pair \(r,r'\) with \(r\sim_\Gamma r'\) and
   \(\tau(r)\ne\tau(r')\).

The pair in item 3 is the registered `ObstructionCertificate`.

**Dependencies:** items 1 and 2 are constructive. The stated equivalence with
the negated existential uses classical reasoning in the Lean development.

### T3: Experiment-family refinement

For \(\Gamma_1\subseteq\Gamma_2\),

\[
r\sim_{\Gamma_2}r' \Longrightarrow r\sim_{\Gamma_1}r'.
\]

Therefore \(Q_{\Gamma_2}\) refines \(Q_{\Gamma_1}\), with a canonical
surjection \(Q_{\Gamma_2}\to Q_{\Gamma_1}\).

**Dependencies:** both families index observation maps on the same realization
type. No strict refinement is promised; a new experiment may be redundant.

### T4: Finite minimal separating-family search

For a finite declared experiment set, exhaustive subset search returns every
minimum-cardinality family that identifies \(\tau\), or returns the full-family
obstruction when no separating family exists.

**Dependencies:** finite total tables, deterministic equality, and exhaustive
enumeration. This is a correctness claim, not a polynomial-time claim.

## Assumption minimization ledger

| Assumption | Role | Needed by | Failure consequence |
|---|---|---|---|
| Total observation map for every selected experiment | theorem condition | T1-T3 | transcript equality is undefined |
| Typed equality within each outcome type | theorem condition | T1-T3 | indistinguishability is undefined |
| Same realization domain for nested families | theorem condition | T3 | quotient refinement is ill-typed |
| Deterministic exact outcomes | finite implementation condition | executable T2-T4 | stochastic/noisy claims are withheld |
| Finite declared \(R,E\) | computational condition | T4 | exhaustive search may not terminate |
| Hashable finite outcomes/targets | implementation convenience | Python engine | abstract mathematics remains valid |
| Nonempty family | **not assumed** | all | the empty family induces the universal relation |
| Injective observations | **not assumed** | all | collisions are the object being diagnosed |
| Markov dynamics or intervention closure | **not assumed** | all | sequential structure belongs to an instantiation |
| Coordinate system or metric | **not assumed** | all | geometry has no privileged role in the theorem |

## Edge, limiting, and null cases

The registered executable checks include:

- one realization;
- an empty experiment family;
- a constant target;
- a full-family target collision;
- a redundant added experiment that does not strictly refine the quotient;
- a strict internal-intervention refinement;
- multiple distinct minimum identifying families;
- malformed partial tables, duplicate names, and unknown family members.

## Executable counterexample and control ladder

### Positive target

An external readout identifies a behavioral target in the mechanistic fixture.

### Negative control

The same external family does not identify the mechanism label: two
realizations have identical external transcripts and different mechanisms.
The engine must return the registered pair as an obstruction certificate.

### Mechanistic refinement

Adding an internal patch experiment must split each behaviorally identical
mechanism pair and make the mechanism target identifiable. This demonstrates
only observer-relative refinement, not that the internal experiment family is
complete.

### Redundancy control

Adding an experiment whose outcome is a deterministic duplicate of an existing
readout must leave the quotient unchanged.

### Geometry/gauge control

Two coordinate realizations with the same external transcript but different
coordinate labels must obstruct recovery of that coordinate target. This
establishes non-identifiability under the selected family, not nonexistence or
scientific irrelevance of the coordinates.

## Exhaustive finite stress check

The test suite will enumerate every binary observation table with:

- three realizations;
- three experiments;
- binary outcomes;
- every binary target;
- every experiment family.

It will verify T1-T3 and compare T4's returned minimum families against direct
enumeration. This is an executable finite sanity check, not a proof substitute.

## Fatal gates

| Gate | Acceptance rule | Fatal failure / unknown rule |
|---|---|---|
| G0 preregistration integrity | this file predates implementation and result artifacts | withhold all confirmatory language |
| G1 Lean proof | pinned Lean build passes with no `sorry`, `admit`, or unsound axiom introduced by this package | withhold mathematical promotion |
| G2 Python/Lean statement alignment | names, quantifiers, family inclusion direction, and factorization target agree | withhold implementation claim |
| G3 exhaustive finite cross-check | every registered binary-table case passes | reject executable theorem engine |
| G4 control ladder | positive, obstruction, strict refinement, redundancy, and gauge controls all pass | reject MIDAS fixture claim |
| G5 prior-art calibration | paper names the kernel/quotient result as standard and cites the direct refinement precedent | reject novelty or foundational framing |
| G6 assumption/edge audit | all registered invalid and null cases are exercised | withhold weakest-assumption claim |
| G7 MIDAS regression contract | machine-readable fixtures reproduce stable expected verdicts and certificates | withhold MIDAS-facing usefulness claim |
| G8 cross-domain calibration | DCR/Constraint Swap/mechanistic examples are labeled instantiations or analogies, not proofs of those empirical programs | reject cross-domain corollary language |

Fatal gates are noncompensatory. A passing executable sweep cannot repair a
failed proof, and a passing proof cannot repair a false novelty claim.

## Prior-art comparison targets

The theorem note must compare its exact object and scope with:

1. Blackwell's comparison of statistical experiments;
2. Myhill--Nerode minimization and Angluin's counterexample-driven automata
   learning;
3. testing equivalence and probabilistic bisimulation;
4. contextual equivalence and full abstraction;
5. interventional Markov equivalence and active causal experiment design;
6. Nixon's probe-family-relative quotient and refinement proposition;
7. activation patching as an internal-intervention family.

If a closer source is found, both the current and closer claims remain in the
ledger; the apparent novelty is narrowed rather than the precedent being
discarded.

## Discovery-regime audit

### Question

Can the existing finite future-commitment quotient regime represent and verify
target-relative impossibility across arbitrary experiment families?

### Current regime

- **Artifact types:** finite Moore agents, exact future-word witnesses,
  commitment-bisimulation quotients, factorial result rows.
- **Operations:** partition refinement, product-state witness search,
  conjugacy checks, pytest verification.
- **Gates/verifiers:** formal fixed-point checks, preregistered factorial gates,
  claim-calibration digest, repository quality checks.
- **Known limitations:** the intervention alphabet and target were supplied;
  the engine does not emit a target-relative obstruction certificate or search
  for the weakest separating experiment subfamily.

### Action class

- **Retrieval/search:** the mathematical quotient and refinement results are
  transported prior art.
- **Potential discovery:** a new accepted repository artifact type,
  `ObstructionCertificate`, plus a MIDAS regression schema that makes failed
  identifiability claims first-class and machine-checkable.

### Gate

Accept the regime transition only if G1-G8 pass. Otherwise retain the prior
finite-quotient regime and preserve the rejected theorem-package artifacts.

### Residual content

Even on success, the project will not choose natural interventions, handle
noise, prove approximate lower bounds, learn experiment families, or establish
mechanistic completeness. Those remain explicit residuals rather than being
absorbed into the exact finite result.

