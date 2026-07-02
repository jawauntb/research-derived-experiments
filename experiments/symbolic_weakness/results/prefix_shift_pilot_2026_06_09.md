# Symbolic Weakness Prefix-Shift Pilot

Date: 2026-06-09

## Question

Can a weakness or invariance score identify the rule that generalizes OOD when training loss, simplicity, compression, and a flatness proxy are not enough?

## Setup

Task family: cyclic prefix shift.

Each trial samples a modulus from `{7, 11, 13}`, an offset from `1..modulus-1`, and exposes training examples only for the first three inputs. Several train-perfect candidates are then scored:

- `local_prefix_patch`: applies the observed shift on the training prefix and identity elsewhere.
- `memorize_train_examples`: memorizes observed examples and emits a default outside the prefix.
- `global_shift_offset`: applies the same modular shift everywhere.

Selectors:

- `train_loss`: perfect training accuracy, tied by simplicity.
- `simplicity`: shortest form.
- `compression`: shortest form plus training-error penalty.
- `flatness_proxy`: symbolic completion-volume/slack proxy, tied by
  simplicity; not Hessian or weight-space flatness.
- `weakness`: maximum translation-equivariance count.
- `random`: random train-consistent candidate.

Manifest:

- Command: `python3 experiments/symbolic_weakness/experiment.py --trials 300 --seed 11 --out artifacts/symbolic_weakness/prefix_shift_pilot.json`
- Trials: 300
- Seed: 11
- Raw artifact: `artifacts/symbolic_weakness/prefix_shift_pilot.json` (ignored)

## Gate

Acceptance rule:

- Every reported selector must be train-perfect on average.
- Weakness must select the invariant rule at least 95% of the time.
- Weakness must reach at least 95% mean OOD accuracy.
- Simplicity, compression, train loss, and flatness proxy should select the local patch at least 95% of the time and stay below 15% mean OOD accuracy.

Withheld rule:

- Do not claim neural or learned-rule evidence from this run.
- Do not claim that weakness beats all real flatness metrics yet. The pilot uses a deliberately weak symbolic flatness proxy to show the benchmark shape.

## Results

| Selector | Train acc | OOD acc | Full acc | Invariant rate | Local patch rate | Mean weakness | Mean form length |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| weakness | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 10.513 | 5.000 |
| train_loss | 1.000 | 0.000 | 0.304 | 0.000 | 1.000 | 1.000 | 3.000 |
| simplicity | 1.000 | 0.000 | 0.304 | 0.000 | 1.000 | 1.000 | 3.000 |
| compression | 1.000 | 0.000 | 0.304 | 0.000 | 1.000 | 1.000 | 3.000 |
| flatness_proxy | 1.000 | 0.000 | 0.304 | 0.000 | 1.000 | 1.000 | 3.000 |
| random | 1.000 | 0.380 | 0.570 | 0.343 | 0.347 | 4.347 | 4.307 |

## Audit

Accepted:

- The benchmark cleanly separates train-perfect local patching from train-perfect invariant generalization.
- In this symbolic regime, weakness as translation-equivariance count predicts OOD generalization better than training loss, description length, compression, random selection, and the current flatness proxy.

Rejected or withheld:

- This is not yet evidence that learned neural models discover the same invariant rule.
- This is not yet evidence that weakness beats strong sharpness or PAC-Bayes-style flatness measures.
- This run does not solve how to infer the admissible transformation group from data.

Residual content:

- The promising residual is not merely "geometry works." It is that the generalizing rule is the one compatible with more transformations while preserving the observed constraint.
- The core next question is whether compatible-transformation volume can be estimated from learned representations rather than supplied by a symbolic oracle.

Next move:

- Sweep symbolic regimes across seeds, moduli, train windows, and non-cyclic groups.
- Add wrong/noisy transformation-group controls.
- Train small neural models on the same tasks and test whether latent equivariance predicts OOD accuracy better than loss, compression, and sharpness.
