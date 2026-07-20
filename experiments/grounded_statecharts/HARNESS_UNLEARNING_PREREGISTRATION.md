# Deterministic Functional Harness Unlearning Fixture

Frozen design date: 2026-07-20

## Question

After proving that a stale memory causally changes commitment, can a scoped
memory lifecycle stop that influence under a world shift and restore the useful
memory when the prior regime recurs?

## Fixed episode

A tool-pattern memory and its derived summary correctly select `legacy_name`
under tool regime `v2`. Regime `v3` changes the required field to
`current_name`, making both records stale. Later, `v2` recurs. An unrelated
active memory is the matched suppression placebo.

## Required causal-use prerequisite

From the same shifted checkpoint, compare:

1. active target memory and descendant;
2. target family suppressed from commitment context; and
3. matched placebo memory suppressed.

The prerequisite passes only if target-family suppression changes the committed
action from failure to success while placebo suppression leaves it unchanged.
Lifecycle results are not generated if this gate fails.

## Lifecycle and controls

- `active -> quarantined` after paired suppression clears the influence gate;
- `quarantined -> revalidating -> retired` after a bounded `v3` probe fails;
- retired memory remains auditable and ineligible for ordinary commitment;
- `retired -> revalidating -> active` after a bounded recurrence probe passes;
- append-only fails after shift, while full reset fails on recurrence;
- a matched non-shift does not trigger quarantine.

## Exit gates

- commitment-level causal use passes before lifecycle execution;
- target and descendant stop influencing ordinary `v3` commitment;
- all active, quarantined, retired, and revalidating states are observed;
- shift recovery and recurrence recovery both succeed;
- the matched non-shift has zero false forgetting;
- every status change has an immutable evidence receipt;
- public artifacts regenerate byte-for-byte.

## Claim boundary

Passing establishes functional memory control on one deterministic tool-regime
shift/recurrence fixture. It is not neural unlearning, legal erasure, a
population estimate, or evidence for HU1–HU7, stochastic, OOD, or sealed-shift
claims.

