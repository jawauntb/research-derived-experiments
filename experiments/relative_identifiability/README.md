# Experiment-Relative Identifiability

This package turns one question into an executable theorem-development loop:

> Which target distinctions are recoverable from this exact experiment family?

For a finite table of candidate realizations and experiment outcomes, the engine
either:

1. returns a `FactorizationCertificate`, showing that the target is constant on
   every observational quotient block; or
2. returns an `ObstructionCertificate`, containing two target-distinct
   realizations with the same complete selected-family transcript.

It can also compare nested experiment families and exhaustively find every
minimum-cardinality family that identifies a target.

## Run

Run the MIDAS regression corpus:

```bash
uv run --no-sync python -m \
  experiments.relative_identifiability.run_regressions
```

Run the focused Python checks:

```bash
uv run --no-sync python -m pytest -q \
  tests/test_relative_identifiability.py
```

Run the machine-checked theorem gate:

```bash
uv run --no-sync python -m experiments.relative_identifiability.lean_gate
cd formal/relative-identifiability
lake build
```

The pull-request quality workflow also builds this pinned Lean package in its
own required job. The Python source checks are convenience guards, not a
substitute for typechecking.

The exact claim boundary and fatal gates are frozen in
[`PREREGISTRATION.md`](PREREGISTRATION.md). The Lean proof is in
`formal/relative-identifiability/RelativeIdentifiability.lean`, and the
MIDAS-facing theorem-to-test mapping is in `midas_contract.json`.

## Scope

The quotient/factorization and refinement results are standard mathematics.
This package does not claim a new identifiability theorem. Its contribution is
a typed obstruction certificate, minimum-family search, a mechanistic
internal-intervention fixture, and a proof-backed regression contract that can
be reused by MIDAS.
