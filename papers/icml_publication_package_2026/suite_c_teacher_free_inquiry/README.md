# Suite C Teacher-Free Inquiry Package

This package now records the teacher-free Suite C experiment needed to turn
Suite C from a teacher-trained learned probe result into a stronger ICML-style
adaptive inquiry paper.

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

## Completed Result

The first reward-trained version now exists in:

- `experiments/world_responds/suite_c_teacher_free.py`
- `experiments/world_responds/summarize_suite_c_teacher_free.py`
- `experiments/world_responds/results/suite_c_teacher_free_inquiry_rows_2026_07_06.jsonl`
- `experiments/world_responds/results/suite_c_teacher_free_inquiry_2026_07_06.json`
- `experiments/world_responds/results/suite_c_teacher_free_inquiry_2026_07_06.md`

Headline held-out result: `teacher_free_reward_policy` passes C1-C6 plus T1/N1
with final affected MAE 0.095, recovery rate 1.000, first-shift selectivity
12.500, second-shift reopenability 11.312, and 22.0 probes. The training loss
does not use teacher labels, teacher actions, or teacher probabilities.

## Files

- `preregistration.md`: acceptance gates and stop conditions.
- `experiment_design.md`: reward/self-supervised training design.
- `paper_outline.tex`: focused paper skeleton for the future result.
- `row_schema.json`: proposed JSONL row schema for public release.

## Claim Boundary

This is a positive finite diagnostic result, not an open-agent or production
reliability claim. The next paper-ready step is replication, confidence
intervals across wider seeds, and a less privileged source-estimate ablation.
