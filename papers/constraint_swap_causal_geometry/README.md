# Constraint Is Not Geometry

This bundle contains the citation-grounded manuscript source, four generated
figures, and the deterministic eight-page PDF for the registered
constraint-swap causal geometry experiment.

The paper reports a scoped counterexample: perfect constraint-dependent
behavior did not require the preregistered policy-free reachability geometry,
and matched low-rank transports did not establish that geometry as the causal
mediator of behavior.

Rebuild from committed public results:

```bash
uv run --no-sync python scripts/make_constraint_swap_causal_geometry_figures.py
uv run --no-sync python scripts/build_constraint_swap_causal_geometry_pdf.py
```

The builder writes `paper.pdf`, mirrors identical bytes to
`papers/pdf/constraint_swap_causal_geometry.pdf`, and copies the PDF to the
local Metaphysics of Intelligence archive when that directory exists.
