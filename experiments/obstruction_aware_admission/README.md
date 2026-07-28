# Obstruction-Aware Admission V0

This package asks one finite control question:

> Which permitted experiment minimizes the worst-case remaining cost of
> identifying a declared target, and when should the controller stop instead?

The exact controller returns one of four statuses:

- `recovered`: the target is constant over the current version space;
- `terminal_obstruction`: a validated target-distinct pair agrees under every
  remaining permitted experiment;
- `budget_infeasible`: recovery is possible, but its exact minimum worst-case
  cost exceeds the remaining budget; or
- `admit`: the next experiment lies on a minimum-cost adaptive branch.

## Run

```bash
uv run --no-sync python -m \
  experiments.obstruction_aware_admission.run_benchmark
```

Focused tests:

```bash
uv run --no-sync python -m pytest -q \
  tests/test_obstruction_aware_admission.py
```

## Registered boundary

The benchmark exhausts all 500,912 deterministic binary systems containing:

- 2-4 worlds;
- 1-3 experiments;
- every nonconstant binary target;
- every binary outcome table; and
- costs in `{1, 2}`.

The public receipt is in `results/summary.json`. The first strict
counterexample to immediate target-pair gain is frozen in
`fixtures/minimal_greedy_counterexample.json`.

## Scope

The accepted result is an exact finite control contract. The optimal
decision-tree recurrence is established mathematics; the contribution is its
integration with target-relative obstruction certificates, typed budget
failure, exhaustive counterexample search, and a MIDAS regression contract.

The result does not validate a universal theory of agency, a natural-domain
scientific-discovery method, large-state efficiency, or Concern-Gated
Retrieval.
