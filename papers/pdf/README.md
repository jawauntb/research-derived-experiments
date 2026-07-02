# Compiled Paper PDFs

Committed, shareable renders of the project's papers (the rest of `artifacts/` is
gitignored). Regenerate with the committed builders:

- `weakness_predicts_ood.pdf` — flagship "Weakness, Not Compression: Symmetry-Compatible
  Hypothesis Volume Predicts Out-of-Distribution Generalization."
  Rebuild: `python scripts/build_weakness_pdf.py`
- `weakness_predicts_topology.pdf` — Paper A "Weakness Predicts the Toroidal Topology and
  Generalization of Population Codes" (preliminary CPU results).
  Rebuild: `python scripts/build_gridcell_pdf.py`

- `concern_deforms_metric.pdf` — Paper B "Concern Deforms a Learned Metric" (64-seed
  moved-location replication across RNN, Transformer, and JEPA-style spatial models; 2%
  precision gate passes with the stricter 1% audit retained as a non-passing check).
  Rebuild: `python scripts/build_paperB_pdf.py`

- `reward_deformation_effective_dimension_law.pdf` — standalone Newton-gate paper: the
  2-D exponent is falsified and the measured law has effective dimension near 1.
  Rebuild: `python scripts/build_effective_dimension_pdf.py`

- `semantic_concern_geometry_boundary.pdf` — Paper B externality follow-up: a 256-seed
  real-text transformer/JEPA-like sweep that fails the preregistered semantic-margin
  transport gate while revealing positive companion geometry.
  Rebuild: `python scripts/build_semantic_concern_pdf.py`

Toolkit: `scripts/paperkit.py` (LaTeX-free; reportlab + matplotlib).
