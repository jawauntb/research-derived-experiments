# Semantic Selection Control Preregistration

Date: 2026-07-06

## Question

Can learned structure compatibility select the OOD-robust semantic retrieval model
among train/ID-equivalent candidates without using OOD labels?

## Current Regime

- Artifact types: semantic retrieval diagnostic rows from public frozen sentence
  encoders, learned candidate transformation pairs, selection records.
- Operations: generate encoder-threshold model zoos, filter candidates by high
  train and ID validation performance, select by OOD-free predictors.
- Gates: learned compatibility must beat train/ID selectors and random
  selection; wrong compatibility must fail as a negative control.
- Store: JSON payload, markdown report, figures, and descriptive paper PDF under
  `papers/structure_compatible_generalization/`.

## Positive Target

`compatibility_discovered` should choose candidates with higher mean held-out OOD
accuracy than `id_validation_accuracy`, `train_accuracy`, and random candidate
selection across at least 20 eligible zoos.

## Negative Control

`compatibility_wrong` should not outperform random candidate selection by more
than 0.02 mean selected OOD.

## Acceptance Rule

The phase is accepted only if all pre-registered gates pass:

1. At least 20 eligible ID-equivalent zoos.
2. Learned compatibility beats ID validation by more than 0.05 selected OOD.
3. Learned compatibility beats train accuracy by more than 0.05 selected OOD.
4. Learned compatibility beats random candidate selection by more than 0.05
   selected OOD.
5. Wrong compatibility fails the negative-control gate.

## Scope

This is an OOD-certifiability-lite result for finite semantic retrieval
candidates generated with public frozen encoders. It is not a guarantee for
open-ended language generation or arbitrary paraphrase invariance.
