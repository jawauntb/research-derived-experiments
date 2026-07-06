# Validation Checklist

This file records the validation expected for the ICML-style paper package.

## Package Requirements

- [x] New subfolder exists:
  `papers/icml_publication_package_2026/structure_compatible_model_selection/`
- [x] Main paper source exists: `paper.tex`
- [x] Appendix exists: `appendix.tex`
- [x] Bibliography exists: `references.bib`
- [x] Source-backed result ledger exists: `result_tables.md`
- [x] Figure plan exists: `figures_manifest.md`
- [x] README with claim boundary and build command exists.

## Build Validation

Passed on 2026-07-06:

```bash
cd papers/icml_publication_package_2026/structure_compatible_model_selection
tectonic paper.tex
```

Result: `paper.pdf` generated. Remaining TeX messages are underfull-line
warnings from dense text/bibliography breaks.

Updated build on 2026-07-06 from
`codex/suite-c-stats-polish-20260706`:

- `tectonic paper.tex`: passed and regenerated `paper.pdf` with the Phase 6
  bootstrap CI figure.
- `tectonic ../suite_c_teacher_free_inquiry/paper_outline.tex`: passed and
  regenerated the teacher-free Suite C outline PDF.

## Repository Validation

Per repository instructions, run lint, type checks, and targeted tests before
commit.

Expected commands from the root README:

```bash
uvx ruff check .
uvx --python 3.12 --with numpy --with torch --with scikit-learn --with scipy --with matplotlib --with pytest ty check scripts experiments tests
uvx --python 3.12 --with torch --with numpy --with scikit-learn --with pytest python -m unittest discover -s tests
```

For this paper-only package, targeted tests should include the result families
used in the paper:

```bash
uvx --python 3.12 --with torch --with numpy --with scikit-learn --with scipy --with matplotlib --with pytest python -m pytest \
  tests/test_structure_compatible_generalization.py \
  tests/test_world_responds_suite_c.py \
  tests/test_world_responds_suite_c_neural_transfer.py \
  tests/test_long_horizon_bottleneck.py
```

Actual run on 2026-07-06:

- `uvx ruff check .`: passed.
- `uvx --python 3.12 --with numpy --with torch --with scikit-learn --with scipy --with matplotlib --with pytest ty check scripts experiments tests`:
  passed.
- Targeted pytest command above: passed, 104 passed and 3 skipped.

Updated run on `codex/suite-c-stats-polish-20260706`:

- `uvx ruff check .`: passed.
- `uvx --python 3.12 --with numpy --with torch --with scikit-learn --with scipy --with matplotlib --with pytest ty check scripts experiments tests`:
  passed.
- `uvx --python 3.12 --with numpy --with torch --with scikit-learn --with scipy --with matplotlib --with pytest python -m pytest tests/test_structure_compatible_generalization.py tests/test_structure_compatible_semantic_selection_bootstrap.py tests/test_world_responds_suite_c.py tests/test_world_responds_suite_c_neural_transfer.py tests/test_world_responds_suite_c_teacher_free.py tests/test_world_responds_suite_c_teacher_free_wide_stats.py tests/test_long_horizon_bottleneck.py`:
  passed, 115 passed and 3 skipped.

## Manual Paper Audit

- [x] Main claim is bounded to finite structured shifts.
- [x] Phase 6 semantic selection is the headline result.
- [x] Phase 6 semantic selection now includes zoo-bootstrap CIs.
- [x] Vision and random-augmentation caveats are explicit.
- [x] Causally grounded agents material is framed as companion appendix, not as
  the primary ICML claim.
- [x] No consciousness, general-agency, production-reliability, or universal OOD
  claims are made.
