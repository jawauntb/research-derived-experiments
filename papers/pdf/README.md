# Compiled Paper PDFs

Committed, shareable renders of the project's papers (the rest of `artifacts/` is
gitignored). Regenerate with the committed builders:

- `weakness_predicts_ood.pdf` — flagship "Weakness, Not Compression: Symmetry-Compatible
  Hypothesis Volume Predicts Out-of-Distribution Generalization."
  Rebuild: `python scripts/build_weakness_pdf.py`
- `weakness_predicts_topology.pdf` — Paper A "Weakness Predicts the Toroidal Topology and
  Generalization of Population Codes" (preliminary CPU results).
  Rebuild: `python scripts/build_gridcell_pdf.py`

- `concern_deforms_metric.pdf` — Paper B "Value-Weighted Training Deforms Learned
  Metrics" (controlled 64-seed moved-location test across RNN, Transformer, and
  JEPA-style spatial models; the 2% report threshold is met with the stricter frozen 1%
  audit retained as a non-passing precision check).
  Rebuild: `python scripts/build_paperB_pdf.py`

- `reward_deformation_effective_dimension_law.pdf` — standalone Newton-gate paper: the
  2-D exponent is falsified and the measured law has effective dimension near 1.
  Rebuild: `python scripts/build_effective_dimension_pdf.py`

Toolkit: `scripts/paperkit.py` (LaTeX-free; reportlab + matplotlib).
