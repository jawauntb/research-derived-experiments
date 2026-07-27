# Future-Commitment Quotient

This package runs the preregistered finite-agent double dissociation in
[`PREREGISTRATION.md`](PREREGISTRATION.md).

The experiment crosses coordinate preservation/destruction with preservation
or alteration of one delayed transition constraint. Exact Moore-machine
partition refinement and product-state witness search determine whether future
commitments are equivalent. Coordinate geometry, current outputs, and
depth-one outputs are registered baselines.

Run the confirmatory suite:

```bash
uv run --no-sync python -m experiments.future_commitment_quotient.run_experiment
```

Run focused verification:

```bash
uv run --no-sync python -m pytest -q tests/test_future_commitment_quotient.py
```

Public rows and summaries are written to `results/`. The complete run is
written to the gitignored `artifacts/future_commitment_quotient/` directory.
The G5 claim boundary is recorded in `claim_calibration.json` and verified
against the exact paper digest, five preregistered content obligations, and an
independent agent adjudication during every run; human review remains recorded
separately as pending.
The theorem is a deterministic finite-agent specialization of classical
automata minimization and bisimulation, not a novel quotient theorem.
