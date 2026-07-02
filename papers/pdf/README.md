# Compiled Paper PDFs

Committed, shareable renders of the project's papers (the rest of `artifacts/` is
gitignored). Regenerate with the committed builders:

- `weakness_predicts_ood.pdf` — flagship "Symmetry-Compatible Hypothesis Volume
  Predicts Out-of-Distribution Generalization."
  Rebuild: `python scripts/build_weakness_pdf.py`
- `weakness_predicts_topology.pdf` — empirical note "Translation Augmentation Produces
  Toroidal Codes and Larger-Arena Generalization in Path-Integration RNNs" (320-network
  Modal sweep; negative mediation result for weakness as the governing scalar).
  Rebuild: `python scripts/build_gridcell_pdf.py`

- `concern_deforms_metric.pdf` — Paper B "Value-Weighted Training Deforms Learned
  Metrics" (controlled 64-seed moved-location test across RNN, Transformer, and
  JEPA-style spatial models; the 2% report threshold is met with the stricter frozen 1%
  audit retained as a non-passing precision check). Appendix A adds the semantic
  transformer boundary check, where naive text-encoder transfer does not meet the
  registered local semantic-margin gate.
  Rebuild: `python scripts/build_paperB_pdf.py`

- `reward_deformation_effective_dimension_law.pdf` — standalone effective-dimension note:
  the d=2 exponent is rejected in this harness and the measured law has effective dimension near 1.
  Rebuild: `python scripts/build_effective_dimension_pdf.py`

- `unified_metric_weakness_portfolio/finite_representations_portfolio_with_bookmarks.pdf` —
  portfolio packet combining the four July 2026 arXiv-ready papers with front matter,
  reading guide, divider pages, and bookmarks.
  Rebuild: `python scripts/build_unified_portfolio_pdf.py`

Toolkit: `scripts/paperkit.py` (LaTeX-free; reportlab + matplotlib).
