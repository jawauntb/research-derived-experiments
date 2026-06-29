# Compiled Paper PDFs

Committed, shareable renders of the project's papers (the rest of `artifacts/` is
gitignored). Regenerate with the committed builders:

- `weakness_predicts_ood.pdf` — flagship "Weakness, Not Compression: Symmetry-Compatible
  Hypothesis Volume Predicts Out-of-Distribution Generalization."
  Rebuild: `python scripts/build_weakness_pdf.py`
- `weakness_predicts_topology.pdf` — Paper A "Weakness Predicts the Toroidal Topology and
  Generalization of Population Codes" (preliminary CPU results).
  Rebuild: `python scripts/build_gridcell_pdf.py`

Toolkit: `scripts/paperkit.py` (LaTeX-free; reportlab + matplotlib).
