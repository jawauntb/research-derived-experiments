# Phase 5 Preregistration: Semantic Retrieval Transfer for SCG

**Date:** 2026-07-06

## Question

Can learned structure-compatibility predict OOD retrieval behavior when the
candidate transformation family is inferred from frozen text-encoder semantic
neighborhoods rather than supplied as an explicit template substitution?

## Current Regime

- Phase 1 used oracle transformations.
- Phase 2 inferred finite modular shifts.
- Phase 3 learned finite generators and transferred to vision rotations.
- Phase 4 rendered a finite task as language templates with explicit
  number-word substitutions.

## New Operation

Phase 5 builds a finite semantic retrieval corpus with paraphrase/entity orbits.
Actual frozen sentence encoders embed the texts. Nearest-neighbor structure
infers candidate same-orbit transformations; wrong cross-label neighbors are
held as controls. Retrieval selectors are trained only on train variants and
evaluated on held-out semantic variants.

## Positive Targets

- `compatibility_discovered` should positively predict OOD retrieval accuracy.
- Discovered compatibility should beat wrong cross-label compatibility.
- The semantic-rule exact row should dominate a lexical shortcut in true and
  discovered compatibility.

## Negative Controls

- Lexical selectors that can fit local surface forms.
- Random projections that can lose semantic orbit structure.
- Wrong cross-label nearest neighbors.
- Standard selectors: train and ID accuracy.

## Acceptance Rules

The result may claim semantic retrieval transfer only if:

1. The Modal run uses actual frozen text encoders.
2. Learned compatibility is a positive OOD predictor in the non-exact domain.
3. Wrong compatibility does not dominate learned compatibility.

## Withheld Claims

- Do not claim arbitrary natural-language paraphrase certification.
- Do not claim production model robustness.
- Do not use OOD labels for retrieval selector fitting or generator inference.

## Store

- JSON payload:
  `artifacts/structure_compatible_generalization/semantic_retrieval_transfer.json`
- Report:
  `experiments/structure_compatible_generalization/results/semantic_retrieval_transfer_2026_07_06.md`
- Paper:
  `papers/structure_compatible_generalization/semantic_retrieval_transfer.md`
- PDF:
  `papers/structure_compatible_generalization/semantic_retrieval_transfer.pdf`
