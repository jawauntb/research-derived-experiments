# Formal System Atlas

This package is the repository-wide audit of the Research Derived Experiments
program as of commit `3a86730` on 2026-08-19.

- Source monograph: `paper.md`
- Builder: `scripts/build_formal_system_atlas_pdf.py`
- Final PDF: `output/pdf/research_derived_experiments_formal_system_atlas_2026-08-19.pdf`

Rebuild from the repository root:

```bash
python3 scripts/build_formal_system_atlas_pdf.py
```

The builder derives the exhaustive experiment, preregistration, claim,
evidence, and Lean declaration appendices from the checked-in registries and
source tree. The prose distinguishes definitions, SafeVerify-verified
headlines, Lean-proved statements without an accepted receipt, bounded
empirical findings, and conjectures.
