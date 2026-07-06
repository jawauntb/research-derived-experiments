# ICML Publication Package 2026

This umbrella folder contains the publication work needed to turn the July 2026
research arc from sparse memos into reviewer-facing paper packages.

## Package Tracks

1. `structure_compatible_model_selection/`
   - Primary ICML-style target.
   - Consolidates structure-compatible generalization, inferred
     transformations, learned generators, language templates, semantic
     retrieval, and semantic selection.
   - Headline: compatibility with deployment-relevant transformations can
     select better OOD models among high train/ID candidates without OOD labels.

2. `proxy_resistant_agent_benchmarks/`
   - Benchmark/workshop/dataset-style target.
   - Centers Suite C and Suite D/E.
   - Headline: no suite passes on behavior alone; a pass requires behavior plus
     a structure-specific gate plus anti-cheat controls.

3. `suite_c_teacher_free_inquiry/`
   - Focused adaptive-inquiry experiment package.
   - The reward/CEM Suite C run now moves beyond the current teacher-trained
     probe head in the finite NumPy harness.
   - Status: positive finite diagnostic result with public rows, summary JSON,
     and report under `experiments/world_responds/results/`.

4. `metric_stack_position_package/`
   - Broad synthesis/position track.
   - Should follow the narrower empirical papers.
   - Headline: concern-mediated agents improve when viability/error signals are
     vectorized, calibrated, coupled to intervention and commitment surfaces,
     and gated against proxy success.

## Completion State

This folder is a paper-engineering package, not a claim that every submission is
already venue-ready. It contains the comprehensive drafts, literature maps,
methods, figure plans, appendices, validation notes, and next-experiment
preregistration needed to move from sparse memos to venue-facing submissions.
The main structure-compatible statistical gap is now narrower: Phase 6 has
zoo-level bootstrap intervals, while phases 1-5 still need restored or
regenerated row-level artifacts for full uncertainty treatment. For Suite C,
the finite teacher-free result now has a 64-seed bootstrap; the next empirical
gap is less privileged source-estimation plus open-agent transfer.

## Validation Run

Completed on 2026-07-06 from the fresh branch
`codex/icml-paper-package-20260706`.

- `tectonic paper.tex` passed for
  `structure_compatible_model_selection/paper.tex`.
- `tectonic paper.tex` passed for
  `proxy_resistant_agent_benchmarks/paper.tex`.
- `tectonic paper_outline.tex` passed for
  `suite_c_teacher_free_inquiry/paper_outline.tex`.
- `uvx ruff check .` passed.
- `uvx --python 3.12 --with numpy --with torch --with scikit-learn --with scipy --with matplotlib --with pytest ty check scripts experiments tests`
  passed.
- `uvx --python 3.12 --with torch --with numpy --with scikit-learn --with scipy --with matplotlib --with pytest python -m pytest tests/test_structure_compatible_generalization.py tests/test_world_responds_suite_c.py tests/test_world_responds_suite_c_neural_transfer.py tests/test_long_horizon_bottleneck.py`
  passed: 104 passed, 3 skipped.

Updated on 2026-07-06 from
`codex/suite-c-stats-polish-20260706`.

- Phase 6 semantic selection regenerated and bootstrapped over 120 selection
  zoos with 1,000 reps.
- Suite C teacher-free wide stats regenerated over 64 held-out eval seeds with
  1,000 bootstrap reps.
- `tectonic paper.tex` passed for
  `structure_compatible_model_selection/paper.tex`.
- `tectonic paper_outline.tex` passed for
  `suite_c_teacher_free_inquiry/paper_outline.tex`.
- `uvx ruff check .` passed.
- `uvx --python 3.12 --with numpy --with torch --with scikit-learn --with scipy --with matplotlib --with pytest ty check scripts experiments tests`
  passed.
- Targeted pytest passed: 115 passed, 3 skipped.

## Safe Claim Boundary

Do not claim:

- universal OOD certification;
- open-world semantic robustness;
- production agent reliability;
- consciousness, human behavior, or biological validation;
- general autonomy.

Do claim, when backed by the cited source artifacts:

- finite structured OOD model-selection evidence;
- proxy-resistant finite-agent benchmark methodology;
- Suite C controlled re-engagement evidence;
- Suite C teacher-free finite reward-search evidence;
- Suite D/E commitment-surface evidence;
- a clear next step for replication and open-agent inquiry transfer.
