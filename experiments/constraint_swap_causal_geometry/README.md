# Constraint-Swap Causal Geometry

This package tests whether an exactly enumerable successful-future constraint
changes a frozen recurrent agent's hidden geometry and whether a targeted
low-rank hidden-state transport selectively changes behavior.

The preregistration is `PREREGISTRATION.md`; the portable package contract is
`experiment_manifest.json`, and the frozen full design is
`registered_design.json`. Fatal gates are noncompensatory. A geometry-only
result cannot establish the causal chain.

The 32-seed registered run rejected the scoped hypothesis. F0 integrity and F1
competence/sensitivity passed, while G1-G5 failed. Agents solved A, B, and the
learnable control D perfectly, the label sham stayed at chance, and an injected
geometry control was recovered; nevertheless, active reachability geometry,
constraint swaps, matched low-rank interventions, and topology transfer all
failed in the registered direction.

Run and rebuild:

```bash
uv run --no-sync python -m \
  experiments.constraint_swap_causal_geometry.run_experiment \
  --seeds 32 --workers 4
uv run --no-sync python scripts/make_constraint_swap_causal_geometry_figures.py
uv run --no-sync python scripts/build_constraint_swap_causal_geometry_pdf.py
```

Raw checkpoints and the complete run payload remain under gitignored
`artifacts/`. Public seed rows and gate summaries are under `results/`; the
paper is `papers/constraint_swap_causal_geometry/paper.pdf`.
