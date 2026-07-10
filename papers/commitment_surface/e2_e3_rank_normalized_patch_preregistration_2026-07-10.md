# E2/E3 Rank-Normalized Patch Follow-up — Frozen Addendum

Frozen before the follow-up sweep: 2026-07-10.

## Question

Does the small absolute E2/E3 fixed-top-k patch effect reflect a distributed
compatibility mechanism whose causal effect survives width after the
intervention is normalized by removed subspace mass, or was the original
B-minus-A patch gate driven by Arm A's negative patch artifact?

## Intervention

Fit a compatibility-aligned subspace from last-hidden-layer activation means
grouped by `(a + b) mod n`. Select the minimum SVD rank explaining at least 50%
of between-orbit spectral mass, project that subspace out on OOD examples, and
report:

- raw subspace patch-CE;
- patch-CE divided by the realized removed spectral-mass fraction;
- selected rank and realized mass;
- an `a`-only grouping as a matched wrong-subspace control;
- the legacy fixed-top-k metrics unchanged.

The subspace is identified on the full finite input grid without labels beyond
the known group index; evaluation remains on the frozen OOD split.

## Grid

- moduli: `{17, 19, 23}`;
- train fraction: `0.5`;
- widths: `{96, 128}`;
- depth: 2;
- four fixed seeds per arm;
- arms: A/B/C/D;
- 1,000 epochs;
- subspace target mass: 0.50.

## Gates

The distributed-mechanism claim passes only if all hold:

1. Arm B mean normalized compatibility-subspace patch-CE is positive at both
   widths.
2. Arm B exceeds Arm C by at least `+0.02` at both widths.
3. Arm B compatibility-subspace effect exceeds its wrong-subspace control at
   both widths.
4. The width-128 Arm B effect retains at least 50% of the width-96 effect.

Any failed condition is reported as a strict failure. No threshold may be
retuned from observed cells. A failure leaves the OOD augmentation result
intact but rejects or weakens the claim that this patch identifies a stable
distributed causal mechanism.

## Claim boundary

This follow-up can validate a width-comparable intervention inside the small
MLP modular-addition regime. It cannot establish localization in Pythia,
language, or non-group shifts.
