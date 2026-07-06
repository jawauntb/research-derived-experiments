# Phase 3 Preregistration: Learned Generators for Structure-Compatible Generalization

**Date:** 2026-07-06

## Question

Can a learned finite transformation generator, inferred from training evidence
rather than supplied as an oracle group, predict and improve OOD behavior under
underspecification?

## Current Regime

- Phase 1: compatibility with oracle deployment transformations predicted OOD
  across symbolic, vision, and modular domains.
- Phase 2: supported modular shifts were inferred from observed train-label
  overlaps, then used for compatibility regularization.

## New Operation

Phase 3 adds a learned-generator transfer protocol:

1. **Modular affine transports.** Infer finite offsets
   `(a,b,y)->(a+da,b+db,y+dy)` from observed input/label overlap evidence.
   This does not assume that only the first input coordinate moves or that the
   label shift must match that coordinate.
2. **Vision rotation transfer.** Infer rotations from training-image
   self-consistency, then train matched models under no augmentation, oracle
   augmentation, learned augmentation, and random augmentation.

## Positive Targets

- Learned-generator compatibility should correlate positively with OOD among
  trained models.
- In the modular arm, compatibility regularization under the learned generator
  should improve high-ID OOD over zero regularization without OOD labels.
- In the vision arm, learned augmentation should improve paired OOD over no
  augmentation and should be competitive with oracle augmentation.

## Negative Controls

- Wrong affine offsets where `dy != da+db mod n`.
- Random rotation groups of matched size in the vision arm.
- Standard selectors: train accuracy, ID accuracy, negative train loss,
  parameter norm, and sharpness proxy where available.

## Acceptance Rules

The result may claim a positive Phase 3 transfer only if:

1. `compatibility_discovered` is a positive OOD predictor in at least one
   non-exact domain.
2. At least one learned-generator intervention improves OOD over its matched
   no-generator baseline.
3. Wrong/random controls do not dominate the learned generator in the main
   intervention comparison.

## Withheld Or Bounded Claims

- Do not claim open-ended transformation discovery. The generator families are
  still experimenter-chosen.
- Do not claim language or LLM transfer unless a separate template/paraphrase
  run is added.
- Do not use OOD labels for model selection or training.
- Preserve negative outcomes, especially if random controls match or beat the
  learned generator.

## Store

- JSON payload:
  `artifacts/structure_compatible_generalization/phase3_learned_generators.json`
- Report:
  `experiments/structure_compatible_generalization/results/phase3_learned_generators_2026_07_06.md`
- Paper:
  `papers/structure_compatible_generalization/learned_generators_transfer.md`
- PDF:
  `papers/structure_compatible_generalization/learned_generators_transfer.pdf`
