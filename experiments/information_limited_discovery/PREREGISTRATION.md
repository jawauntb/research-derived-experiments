# Preregistration: Information-Limited Discovery V0

**Frozen:** 2026-07-27 19:11 EDT, after prior-art mapping and before
implementation, fixture execution, or result generation.

## Decision and novelty boundary

The registered question is:

> Can a finite discovery benchmark distinguish justified recovery, certified
> impossibility, budget-limited uncertainty, unsupported abstention, and lucky
> guessing when every agent is restricted to a declared experiment family?

The strongest allowed conclusion is:

> In exact finite candidate-world tasks, a target-distinct pair that agrees on
> every permitted experiment is a machine-checkable certificate that no
> permitted adaptive policy can recover the target uniformly. Paired task
> variants can test whether adding a separating experiment changes the correct
> outcome from certified impossibility to recovery.

This V0 may establish a benchmark contract and deterministic reference
implementation. It may **not** claim that:

- counterexample-first reasoning, falsification, quotienting, or
  counterexample-guided search is new;
- obstruction-finding is the nature of all scientific reasoning;
- an obstruction under one declared family proves that the target is unreal,
  meaningless, or unknowable under richer experiments;
- success on encoded finite tables demonstrates autonomous scientific
  discovery in natural domains;
- the target function itself can be hidden while recovery remains objectively
  scoreable;
- a greedy experiment policy is optimal;
- exact deterministic certificates transfer unchanged to noisy, stochastic,
  continuous, misspecified, or open-world settings.

The quotient and factorization mathematics remains in
`experiments/relative_identifiability/` as the standard technical base. The
contribution under test here is the composition of:

1. experiment-family-relative, machine-checkable obstruction certificates;
2. matched impossible/recoverable tasks that differ by permitted experiments;
3. separate scoring for recovery, certified impossibility, overclaiming,
   budget exhaustion, and unsupported or unnecessary abstention; and
4. an obstruction-first theorem-to-regression workflow for MIDAS.

## Discovery regime

- **Regime class:** proposed regime change, not yet validated discovery.
- **Target object:** a finite public candidate-world table, a public target
  query \(\tau\), a declared permitted experiment family \(\Gamma\), an
  experiment budget, and one hidden actual world \(r^\star\).
- **Decision:** accept, reject, or withhold the claim that V0 correctly
  separates the five outcome classes above and emits valid obstruction
  certificates.
- **Observational unit:** one complete episode for one hidden world. Every
  candidate world is evaluated once per public task and policy; these are exact
  enumerations, not independent statistical samples.
- **Data clock:** discrete experiment steps. Outcomes are exact and
  deterministic; the benchmark does not model acquisition delay or drift.
- **Representation:** a declared table of candidate-world outcomes. Domain
  labels such as “causal” and “mechanistic” are semantic fixtures, not natural
  data.
- **Evidence paths:** implementation and receipts live under
  `experiments/information_limited_discovery/`; tests live in
  `tests/test_information_limited_discovery.py`; the calibrated paper lives in
  `papers/information_limited_discovery/`.

## Formal objects, types, domains, and units

Let:

- \(R\) be a finite nonempty set of candidate worlds;
- \(E\) be a finite set of named experiments;
- \(O_e\) be the outcome type of experiment \(e\);
- \(\operatorname{obs}_e:R\to O_e\) be its exact deterministic outcome map;
- \(\Gamma\subseteq E\) be the permitted experiment family;
- \(T\) be a target-value type;
- \(\tau:R\to T\) be the public target query;
- \(r^\star\in R\) be the hidden actual world;
- \(B\in\mathbb N\) be the total experiment-cost budget.

The target **query** and candidate-world target values are declared; only
\(r^\star\), and therefore \(\tau(r^\star)\), is hidden. If \(\tau\) itself
were unspecified, the benchmark would have no determinate recovery criterion.

After observing a partial transcript \(h\), define the version space

\[
V(h)=\{r\in R:\operatorname{obs}_e(r)=o
\text{ for every }(e,o)\in h\}.
\]

A **local obstruction** is a pair \(r,r'\in V(h)\) with
\(\tau(r)\ne\tau(r')\). It shows that the current transcript does not identify
the target, but a remaining permitted experiment may still separate the pair.

A **terminal obstruction** is a local obstruction that also satisfies

\[
\forall e\in\Gamma,\quad
\operatorname{obs}_e(r)=\operatorname{obs}_e(r').
\]

This is the finite exact obstruction certificate. It blocks uniform recovery
under every adaptive policy restricted to \(\Gamma\), because both worlds
produce the same outcome after every possible permitted choice.

Costs are positive integer units supplied by the fixture. No physical units or
cross-task cost comparability are claimed.

## Registered claims

### C1: Sound recovery

If \(\tau\) is constant on \(V(h)\), returning that common value is correct for
the hidden world, provided the declared model is realizable and
\(r^\star\in V(h)\).

### C2: Current-transcript obstruction

If \(V(h)\) contains a target-distinct pair, no decoder of the current
transcript alone can be uniformly correct on \(V(h)\).

### C3: Adaptive terminal obstruction

If a target-distinct pair in \(V(h)\) agrees on every experiment in
\(\Gamma\), no finite adaptive policy restricted to \(\Gamma\) can distinguish
that pair or uniformly recover \(\tau\).

### C4: Finite completeness

For a finite exact system, absence of a full-family target-distinct collision is
equivalent to target identifiability under the complete \(\Gamma\) transcript.
This is transported directly from the standard criterion implemented in
`relative_identifiability`; it is not a new theorem.

### C5: Matched-family transition

For each registered paired fixture, the coarse family must yield a terminal
obstruction and the enriched family must recover the target for every hidden
world within its registered budget.

## Assumption and identification ledger

| Assumption | Role | Needed by | Failure consequence |
|---|---|---|---|
| Hidden world belongs to declared \(R\) | identification | C1-C5 | recovery and certificate calibration are withheld |
| Total deterministic outcome table | theorem/implementation | C1-C5 | exact transcript matching is invalid |
| Public target query and candidate target values | scoring | all benchmark scores | “recovery” is ill-posed |
| Exact typed equality within each experiment | representation | C1-C5 | version-space membership is undefined |
| Declared permitted family is complete for the scope claim | interpretation | C3 | certificate is only local to an underspecified family |
| Positive integer experiment costs | computational | budget results | cost and budget comparisons are invalid |
| Finite \(R,E\) | computational | exhaustive V0 | enumeration may not terminate |
| Correct candidate-world model | external validity | natural-domain transfer | table results do not license natural-domain claims |
| Greedy policy optimality | **not assumed** | none | policy is a reference baseline only |
| Independent episodes | **not assumed** | none | no inferential statistics are reported |

## Registered fixtures and controls

Each pair shares the same candidate worlds and target. Only the permitted
experiment family changes.

1. **Mechanistic pair:** external behavior leaves mechanisms colliding; an
   internal patch experiment separates the mechanism target.
2. **Causal pair:** observation alone leaves three causal structures colliding;
   two interventions jointly identify the causal target.
3. **Automata pair:** short probes leave delayed behavior colliding; a longer
   probe identifies the target.

Controls:

- **Lucky-guess control:** an always-guess baseline may achieve nonzero target
  accuracy but must be scored as overclaiming whenever its transcript leaves
  target-distinct worlds.
- **Unsupported-abstention control:** an always-abstain baseline supplies no
  certificate and must not receive certified-impossibility credit.
- **Unnecessary-abstention control:** abstention is marked unnecessary when the
  permitted family identifies the target within budget.
- **Invalid-certificate control:** wrong pairs, target-equal pairs, or pairs
  separable by a permitted experiment must fail terminal-certificate
  validation.
- **Redundant-experiment control:** adding a duplicate experiment may increase
  cost options without changing identifiability.
- **Label-permutation control:** renaming worlds and target labels must not
  change outcome classes.
- **Exhaustive finite control:** all small binary systems in the registered
  test range must agree with direct enumeration.

## Metrics

Metrics are counts and rates over the exact episode set:

- certified recovery rate;
- certified terminal-obstruction rate;
- budget-exhaustion rate;
- raw guess accuracy and overclaim rate;
- unsupported-abstention rate;
- unnecessary-abstention rate;
- invalid-certificate count;
- mean experiment count and mean declared cost for acting policies.

No aggregate “discovery score” will combine these categories. A lucky correct
guess cannot compensate for overclaiming, and an unsupported abstention cannot
compensate for a missed recoverable target.

## Fatal gates

| Gate | Acceptance rule | Fatal failure / unknown rule |
|---|---|---|
| G0 preregistration integrity | this file predates implementation and result artifacts | withhold confirmatory language |
| G1 certificate validity | every emitted terminal pair is transcript-consistent, target-distinct, and equal under all permitted experiments | reject obstruction-certificate claim |
| G2 outcome separation | recovery, terminal obstruction, budget exhaustion, guess, and unsupported abstention are distinct result classes | reject benchmark-contract claim |
| G3 matched-family transition | all three coarse/rich pairs reproduce the registered impossible-to-recoverable transition | reject paired-benchmark claim |
| G4 negative controls | lucky guesses remain overclaims; unsupported and unnecessary abstentions are not rewarded | reject scoring claim |
| G5 exhaustive finite agreement | executable classifications agree with direct enumeration on the registered small-system sweep | reject reference implementation |
| G6 prior-art calibration | paper treats falsification, CEGAR/CEGIS, active learning, and quotient mathematics as prior art | reject novelty framing |
| G7 scope calibration | synthetic tables are not described as evidence of natural scientific discovery | reject cross-domain claim |
| G8 reproducibility | public fixture, command, receipt, and tests reproduce without secrets or network access | withhold MIDAS regression claim |

Fatal gates are noncompensatory.

## Promotion ladder

V0 can be promoted only to:

> deterministic finite benchmark mechanics validated.

It cannot be promoted to:

> cross-domain discovery method validated.

That stronger claim requires a later preregistration with natural task
adapters, hidden or misspecified candidate sets, stochastic observations,
model-agent runs, human or oracle adjudication independent of the developer,
and comparison against strong domain-specific experiment-design baselines.

## Smallest break and consolidation experiments

- **Break:** find one emitted terminal certificate whose pair differs on a
  permitted experiment, or one “recovered” episode whose version space contains
  two target values.
- **Consolidate V0 mechanics:** reproduce all three matched transitions, all
  negative controls, and exhaustive finite agreement.

The break experiment has priority. Failure artifacts remain public and block
dependent claims.
