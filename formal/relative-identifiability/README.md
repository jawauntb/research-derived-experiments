# Relative Identifiability Lean Proofs

This dependency-free Lean 4 package formalizes the exact theorem statements
registered in
`experiments/relative_identifiability/PREREGISTRATION.md`:

- observational indistinguishability is an equivalence relation;
- a target factors through the observational quotient iff it is constant on
  every observational fiber;
- a target-distinct collision is equivalent to failure of exact
  factorization;
- nested experiment families induce a canonical surjection from the richer
  quotient to the coarser quotient;
- the empty-family and constant-target edge cases.

Run the proof gate:

```bash
lake build
```

The file deliberately imports no `Mathlib` dependency. Classical reasoning is
used only for the negated-existential direction of the obstruction theorem.
The quotient/factorization mathematics is standard; this package is a
machine-checked MIDAS regression artifact, not a novelty claim.

Pull requests run this build in the repository's required quality workflow via
the official `leanprover/lean-action`; the local Python bridge is
`experiments.relative_identifiability.lean_gate`.
