# Passive-to-Active Phase Map

A deterministic NumPy-only local-CPU diagnostic implementing a bounded first
tranche of systems-theory backlog items `T-SYS-011` and `T-SYS-012`.

The experiment sweeps action coupling across two architectures and five seeds,
compares discontinuous and smooth transition models on held-out seeds, and runs
matched-budget forward/reverse paths with reinitialization and washout controls.
Hysteresis intervals resample independent seed clusters while preserving both
architecture rows within each seed. A failed discontinuity gate is reported as
`bifurcation_not_supported`, not as positive evidence of a smooth crossover.
The strict gates and frozen configuration are in
[`preregistration.md`](preregistration.md).

Run the registered experiment from the repository root:

```bash
uvx --python 3.12 --with numpy python -m experiments.passive_active_phase_map.core --preset registered
```

Run the fast smoke configuration:

```bash
uvx --python 3.12 --with numpy python -m experiments.passive_active_phase_map.core --preset smoke \
  --raw-output artifacts/passive_active_phase_map/smoke_cells.json \
  --summary-output artifacts/passive_active_phase_map/smoke_summary.json \
  --report-output artifacts/passive_active_phase_map/smoke_summary.md
```

Raw per-seed cells stay under gitignored `artifacts/`. The committed-safe
aggregate outputs are `results/registered_summary.json` and
`results/registered_summary.md`.

This harness is evidence only about its controlled synthetic mechanism. It does
not support claims about dynamical attractors, biological criticality, or
foundation-model generality.
