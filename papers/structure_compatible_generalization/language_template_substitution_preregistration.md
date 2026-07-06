# Phase 4 Preregistration: Language-Template Substitution for SCG

**Date:** 2026-07-06

## Question

Can learned substitution compatibility predict and improve OOD behavior in a
controlled language-like template domain, without using OOD labels?

## Current Regime

- Phase 1: oracle deployment transformations predicted OOD across symbolic,
  vision, and modular domains.
- Phase 2: supported modular shifts were inferred from observed train-label
  overlaps and used for regularization.
- Phase 3: finite affine transports and vision rotations were learned or
  inferred from data.

## New Operation

Phase 4 renders a finite modular task as short text-like templates:

```text
compute three plus five
evaluate three with offset five
return sum of three and five
map three through shift five
```

The label remains `a + b mod n`. Training observes a local prefix of the first
number-word slot. Deployment holds out number-word substitutions. Candidate
substitutions are inferred from observed input/label-overlap evidence:

- first-number substitutions: `(a,b,t,y)->(a+k,b,t,y+k)`;
- offset-word substitutions: `(a,b,t,y)->(a,b+k,t,y+k)`;
- template substitutions: `(a,b,template_i,y)->(a,b,template_j,y)`.

## Positive Targets

- `compatibility_discovered` should positively predict OOD accuracy among
  trained text-template classifiers.
- Compatibility regularization under the inferred substitution generator should
  improve high-ID OOD relative to zero regularization.
- The exact true rule should score higher than a train-perfect local template
  shortcut under the learned generator.

## Negative Controls

- Wrong substitution transports with mismatched label shifts.
- Standard selectors: train accuracy, ID accuracy, train loss, parameter norm,
  and sharpness proxy.
- A wrong-substitution augmentation arm that adds shortcut-labeled held-out
  examples.

## Acceptance Rules

The result may claim a controlled language/template transfer only if:

1. Learned substitution compatibility is a positive OOD predictor in the neural
   language-template domain.
2. At least one nonzero compatibility-regularization arm improves high-ID OOD
   over zero regularization.
3. Wrong controls do not dominate the learned generator in the main
   compatibility comparison.

## Withheld Or Bounded Claims

- Do not claim arbitrary natural-language paraphrase discovery.
- Do not claim LLM-scale semantic generalization.
- Do not use OOD labels for training, selection, or generator inference.
- Preserve negative outcomes if random or wrong substitutions match the learned
  generator.

## Store

- JSON payload:
  `artifacts/structure_compatible_generalization/language_template_substitution.json`
- Report:
  `experiments/structure_compatible_generalization/results/language_template_substitution_2026_07_06.md`
- Paper:
  `papers/structure_compatible_generalization/language_template_substitution.md`
- PDF:
  `papers/structure_compatible_generalization/language_template_substitution.pdf`
