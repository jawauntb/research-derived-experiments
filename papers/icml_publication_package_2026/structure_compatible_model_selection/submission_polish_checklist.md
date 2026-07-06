# Submission Polish Checklist

This is the final venue-template pass for the structure-compatible ICML-style
track. It separates what is now done from what remains before a real submission.

## Done In This Package

- Main paper is scoped around structure-compatible model selection under
  underspecification.
- Phase 6 is the headline result rather than a broad survey claim.
- Zoo-level bootstrap CIs are tracked for Phase 6 semantic selection:
  `experiments/structure_compatible_generalization/results/semantic_selection_bootstrap_2026_07_06.md`.
- The new uncertainty figure is generated at
  `papers/structure_compatible_generalization/figures/fig13_semantic_selection_bootstrap_ci.png`.
- Wrong-compatibility controls remain visible in the main result.
- Suite C teacher-free is framed as a positive finite companion result, not as
  a foundation-model agency claim.

## Remaining Before Venue Submission

- Move `paper.tex`, `appendix.tex`, and `references.bib` into the current venue
  LaTeX template and keep the main body within the page limit.
- Publish or archive a curated Phase 6 row-level payload corresponding to the
  regenerated local artifact under `artifacts/`.
- Add deterministic tie-break stress tests for the Phase 6 selector:
  mean-of-ties, worst-tied-candidate, and random-tie bootstrap.
- Restore or regenerate row-level artifacts for phases 1-5 if those phases keep
  quantitative table space in the main paper.
- Decide whether the agent-benchmark appendix should stay as a short appendix
  or move entirely to the separate benchmark paper.
- Rebuild PDFs after template conversion and rerun lint, type checks, and
  targeted tests on the submission branch.

## Safe Main Claim

When train and in-distribution validation cannot distinguish shortcut and
transportable candidates in finite model zoos, discovered compatibility with
deployment-relevant transformations can select better OOD models without OOD
labels, and wrong-transformation controls expose proxy success.
