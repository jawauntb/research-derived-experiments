# Experiments

Experiments should include:

- a small manifest or README describing the hypothesis;
- deterministic seeds where possible;
- explicit positive targets, negative controls, and stress tests;
- accepted and rejected artifacts;
- a short discovery-regime audit after each meaningful run.

Raw outputs should stay under `artifacts/` until summarized and intentionally committed.

## Active Tracks

- `weakness_vs_simplicity`: Boolean hypothesis-selection worlds.
- `symbolic_weakness`: symbolic symmetry worlds where local patches and invariant rules tie on training data but separate OOD.
- `concept_geometry`: embedding-space concept geometry probes.
- `activation_geometry`: hidden-state and intervention probes.
- `concerned_syntax`: Arc 2A causal-constituency and concern-gated intervention benchmark.
- `viable_computational_bodies`: Arc 2B typed architecture-body evolution under viability and formal gates.
