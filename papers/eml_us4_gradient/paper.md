# US-4′ gradient half at the lowest bound

**Jawaun Brown** (human director) and **Cursor Grok 4.6** (agent, under review)
**Date:** August 17, 2026
**Status:** Local matching-skeleton GD ranking banked. Neural bootstrap
withheld. Claim supported at this bound; margin is two seeds.

## Current frame

The Gibbs half of US-4′ showed that truncated fiber mass is not a
function of shortest depth. The identically-zero function has two
size-3 formulas; a typical size-3 constant has one; `Φ` differs by
about 2. That fact is about a *sampler of the same trees*. If access
is fiber mass, a different search process has to feel the same split.
Otherwise we only learned that Gibbs mass is Gibbs mass.

The protected assumption is that master-formula recovery is just
another name for the Gibbs ranking, or that min-size is still the
governor once the sampler is taken away.

## Assumption ledger

| Assumption | Type | Load-bearing? | Break test |
|---|---|---:|---|
| GD recovery tracks `Φ`, not min-size | Mechanism | high | Same min-size, different blind counts |
| The optimizer can recover a nearby correct weight | Measurement | high | Perturbed-correct on the zero skeleton |
| Matching-skeleton GD is the neural bootstrap | Ontology | high | Disclose; do not claim it |
| A Gibbs draw would be a fair test | Ontology | high | Forbid it; tautological |
| Grid tuples are identities | Measurement | high | Bank only the exact zero identity |

## Anomaly map

Both headline targets have `min_internal = 3` and four learnable
`1`-leaves. Min-size cannot rank them. The Gibbs masses differ because
of min-shell multiplicity. If GD is reading `Φ`, the fat zero target
should recover more often. If GD is reading min-size or a generic
basin, the counts should tie. A singleton win kills the `Φ` story.

## Candidate reframe

Access is not process-specific at this lowest bound: the same pair
that splits Gibbs mass also splits matching-skeleton GD, even though
the process never sees the census. The mechanism on the GD side is
not extra discrete trees. It is the larger, safer basin of the zero
identity `eml(a, eml(eml(a,1),1)) = 0`.

## Discriminating predictions

| Predictor | Blind ranking | Perturbed-correct fails |
|---|---|---|
| Min-size governs | equal counts | withhold, not reject |
| `Φ` predicts GD | zero `>` singleton by ≥1 of 8 | withhold |
| `Φ` is the wrong key | singleton `>` zero | withhold |

These rules were written in
`experiments/eml_us4_gradient/preregistration.json` before any blind
success count was computed.

## Severe experiment

Package: `experiments/eml_us4_gradient/`.
Process: hand-derived reverse-mode GD on the known size-3 skeleton;
`1`-leaves learnable and positive; `x` frozen. Loss is MSE on
`TEST_GRID` from `experiments.eml_variable_spectrum.core`. Blind inits
are log-uniform in `(0.1, 3.0)`. Success is MSE `< 1e-6`. Seeds
`0..7`. This is not a Gibbs tree sampler.

Fatal gates (all passed):

| Gate | Fact |
|---|---|
| `US4G_TARGETS_REGISTERED` | both `k=3`; zero is 0; singleton is `e-ln(e-1)` |
| `US4G_PROCESS_IS_NOT_GIBBS_SAMPLER` | GD-on-master-formula disclosure |
| `US4G_DETERMINISTIC` | replay matches |
| `US4G_PERTURBED_CORRECT` | 8/8 on the zero skeleton |
| `US4G_RANKING` | preregistered rule applied |
| `US4G_CLAIM_BOUNDARY` | neural bootstrap not claimed |

Observed ranking: zero blind **8/8**, singleton blind **6/8**,
perturbed-correct **8/8**. Verdict `phi_holds`. Claim **supported**.

The two singleton misses (seeds 4 and 7) finished at the undefined
sentinel `MSE = 1e6`, not just above `1e-6`. The same two starts
recovered the zero target. That is a domain/basin difference, not a
photo-finish.

Kill: singleton `>` zero. Equal counts reject `Φ`-predicts-GD at this
bound. Perturbed-correct 0/8 withholds.

## Claim boundary

**Supported.** On this registered local analogue, the optimizer works
and the preregistered ranking is `phi_holds` (8/8 vs 6/8).

**Weak / local.** The margin is two seeds on an eight-init budget.
Several successful losses sit just under `1e-6`. The master is the
known matching skeleton, not a formula search. This is not
Odrzywołek's neural bootstrap.

**Withheld.** Odrzywołek's neural master-formula bootstrap. Any claim
that GD *in general* tracks `Φ`. Function identity from the grid
except the exact zero target. Gibbs-sampler tautologies. Any claim
that the two singleton failures are extra discrete formulas rather
than an undefined right-spine.

**What would change the conclusion.** Equal counts on a pre-registered
larger seed list; singleton `>` zero; perturbed-correct failure; a
shared master that does not know the matching skeleton and ranks the
targets the other way or as a tie.

## Next best test

A process that does *not* know the matching skeleton: recover the
formula, not just the weights, from one shared master. If that
ranking still follows `Φ`, the access claim graduates. If it
collapses to a tie, this paper is an optimizer-on-a-known-identity
fact and nothing more.
