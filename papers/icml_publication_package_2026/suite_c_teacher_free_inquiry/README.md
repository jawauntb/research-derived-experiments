# Suite C Teacher-Free Inquiry Package

This package defines the next experiment needed to turn Suite C from a
teacher-trained learned probe result into a stronger ICML-style adaptive inquiry
paper.

## Motivation

Current Suite C evidence:

- hand-policy finite gate passes C1-C6;
- teacher-trained NumPy MLP probe head transfers C1-C6 on held-out seeds;
- stale-signal, wrong-signal, signal-suppression, and matched-random controls
  fail.

Open reviewer question:

> Did the policy learn adaptive inquiry, or did it imitate a hand-designed
> teacher?

## Required Next Result

Train the inquiry policy without teacher labels, using only downstream
recovery/cost/false-calm signals or self-supervised intervention feedback, then
require the same C1-C6 gates plus learned-signal controls.

## Files

- `preregistration.md`: acceptance gates and stop conditions.
- `experiment_design.md`: reward/self-supervised training design.
- `paper_outline.tex`: focused paper skeleton for the future result.
- `row_schema.json`: proposed JSONL row schema for public release.

## Claim Boundary

Until the teacher-free run exists, this package is a preregistered experiment
design, not a positive result.

