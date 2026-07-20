# Deterministic Replay and Minimal Grounded Statechart Fixture

Frozen design date: 2026-07-20

## Question

Can the shared harness substrate restore a pre-commit checkpoint exactly, then
change only the verification guard and produce the expected causal path change
on a deterministic false-success fixture?

## Fixed fixture

The executor reports success without writing the required artifact. The chart
is limited to `Observe -> Act -> Verify -> Commit/Repair`, with
`Repair -> Act` as the only retry edge. The repair action writes the exact
artifact declared by the task fixture.

## Conditions

1. G0 self-report guard: accepts the executor's success report.
2. No-op replay: restores the same pre-verification checkpoint and reuses the
   G0 manifest unchanged.
3. G3 artifact guard: restores the same checkpoint and replaces only the guard
   component with a deterministic expected-digest check.

The chart, fixture, repair action, event schema, logical clock, and checkpoint
remain fixed across conditions.

## Exit gates

- Every public event has exactly the required typed event fields.
- The two harness manifests differ only in `guard`.
- The no-op replay event stream and outcome exactly equal the original.
- The G0 condition reaches `commit` while the artifact is missing.
- The G3 condition rejects the first commit, enters `repair`, then reaches
  `commit` with the expected artifact present.

Any failed gate prevents publication of the generated replay bundle.

## Claim boundary

Passing this fixture establishes only the D1 deterministic replay identity and
the minimal Stage 2 mechanism demonstration. It does not estimate a population
effect, evaluate a live model, or support Constraint Transport,
Counterfactual Harness Search, or Harness Unlearning claims.
