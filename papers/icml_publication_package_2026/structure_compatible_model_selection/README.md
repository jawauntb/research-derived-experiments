# ICML-Style Paper Package: Structure-Compatible Model Selection

This folder consolidates the sparse structure-compatible generalization papers
and the causally grounded finite-agent benchmark notes into one ICML-style paper
package.

## Primary Paper

**Working title:** Structure-Compatible Model Selection Under Underspecification

**Core claim:** when train and in-distribution validation cannot distinguish
shortcut and transportable solutions, compatibility with the transformations
expected at deployment can select better out-of-distribution models without OOD
labels.

The main paper is intentionally scoped around model selection and OOD
diagnostics. The causally grounded finite-agent material is included as a
companion appendix because it uses the same methodological rule:

> behavior alone is not a pass; a pass requires behavior plus a
> structure-specific gate and anti-cheat controls.

## Files

- `paper.tex`: ICML-style main paper source.
- `appendix.tex`: detailed results, benchmark companion, limitations, and
  reproducibility appendix.
- `references.bib`: BibTeX bibliography for the main paper and appendix.
- `result_tables.md`: source-backed result ledger copied into reviewer-facing
  tables.
- `figures_manifest.md`: figure inclusion plan with source paths and captions.
- `validation_checklist.md`: build, lint, type-check, and test status.

## Source Evidence

Primary structure-compatible result reports:

- `experiments/structure_compatible_generalization/results/structure_compatible_l4_2026_07_06.md`
- `experiments/structure_compatible_generalization/results/phase2_transformations_2026_07_06.md`
- `experiments/structure_compatible_generalization/results/phase3_learned_generators_2026_07_06.md`
- `experiments/structure_compatible_generalization/results/language_template_substitution_2026_07_06.md`
- `experiments/structure_compatible_generalization/results/semantic_retrieval_transfer_2026_07_06.md`
- `experiments/structure_compatible_generalization/results/semantic_selection_control_2026_07_06.md`

Companion finite-agent benchmark evidence:

- `docs/causally_grounded_agents_benchmark.md`
- `docs/causally_grounded_agents_release_schema.md`
- `experiments/world_responds/results/suite_c_reengagement_2026_07_06.md`
- `experiments/world_responds/results/suite_c_neural_transfer_2026_07_06.md`
- `experiments/long_horizon_bottleneck/BENCHMARK_CARD.md`

## Build

From this folder:

```bash
tectonic paper.tex
```

From the repository root:

```bash
tectonic papers/icml_publication_package_2026/structure_compatible_model_selection/paper.tex
```

The source uses standard LaTeX packages rather than a checked-in ICML style file
so the package can compile in this repository. For conference submission, move
the body into the current ICML template and keep the appendix and bibliography
in the same PDF.

## Claim Boundary

This package does not claim universal OOD certification, open-world paraphrase
understanding, general machine agency, consciousness, or production reliability.
It claims controlled finite evidence for a reusable model-selection and
benchmarking rule: evaluate whether success is supported by the structure that
deployment or future action will require.

