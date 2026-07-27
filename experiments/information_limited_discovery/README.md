# Information-Limited Discovery V0

This package asks a narrow operational question:

> Can an agent recover the declared target from its permitted experiments, and
> if not, can it produce a pair of candidate worlds that certifies why not?

The public task declares candidate worlds, experiment outcomes, target values,
costs, and a permitted experiment family. One actual world is hidden during an
episode. The reference policy first checks for a terminal target-distinct
collision, then chooses the affordable experiment that separates the most
remaining target-distinct pairs per unit cost.

## Run

```bash
uv run --no-sync python -m \
  experiments.information_limited_discovery.run_benchmark
```

Focused checks:

```bash
uv run --no-sync python -m pytest -q \
  tests/test_information_limited_discovery.py
```

The versioned fixtures are in `fixtures/discovery_tasks.json`; public receipts
are written to `results/summary.json` and `results/summary.md`.

## Outcome classes

- `recovered`: the target is constant across every world still consistent with
  the transcript.
- `terminal_obstruction`: a target-distinct pair agrees on every permitted
  experiment.
- `budget_exhausted`: the current transcript is ambiguous, a separator exists,
  but it cannot be run within the remaining budget.
- `guess`: a target value is asserted without identification.
- `unsupported_abstention`: the policy declines without a certificate.

These classes are scored separately. Raw guess accuracy is reported, but a
lucky guess does not count as certified recovery.

## Scope

V0 validates deterministic finite benchmark mechanics. Its mechanistic,
causal, and automata labels describe hand-authored tables, not evidence of
scientific discovery in natural systems. The standard factorization theorem
and finite obstruction engine remain in `experiments/relative_identifiability/`.
The preregistered claim boundary is in `PREREGISTRATION.md`.
