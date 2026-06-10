# Learned-Symmetry Discovery Modal Sweep

Date: 2026-06-09

## Question

Does a *data-inferred* transformation group — recovered from training data
with no oracle access — give a weakness selector that predicts OOD
generalization as well as the oracle group?

## Setup

256-model sweep on Modal (8 shards × 32 models). Same rotated-stroke task
as the prior rotation_weakness paper (Z_8 cyclic group, 16×16 grayscale
strokes, 3-of-8 train rotations per class, OOD = remaining 5).

Manifest:

- Command: `doppler --scope /Users/jawaun/superoptimizers run -- uvx --python 3.12 --from modal modal run experiments/learned_symmetry/modal_sweep.py --n-shards 8 --models-per-shard 32 --epochs 250 --candidates 24 --threshold 0.5 --base-seed 20260609 --out artifacts/learned_symmetry/modal_sweep_v1.json`
- Total models: 256
- Mean OOD accuracy: 0.507
- Fraction with perfect OOD: 10.5%

## Group recovery

| Statistic | Value |
| --- | ---: |
| Mean learned-group size | 10.21 |
| Mean recall vs oracle Z_8 | **0.897** |
| Mean precision vs oracle Z_8 | **0.713** |

We recover ~90% of the true Z_8 rotation angles from training data alone,
with 71% precision (the false positives are near-identity angles like 15°
and 345° that score high on pixel similarity). No oracle access.

## OOD generalization correlations

| Predictor | Pearson r | Spearman ρ |
| --- | ---: | ---: |
| **`weakness_oracle`** (with oracle access) | **+0.736** | **+0.677** |
| **`weakness_learned`** (no oracle) | **+0.662** | **+0.604** |
| `weakness_random` (control, dense candidate set) | +0.551 | +0.553 |
| `parameter_l2` | +0.429 | +0.407 |
| `train_accuracy` | +0.420 | +0.281 |
| `final_train_loss` | −0.395 | −0.291 |
| `sharpness_proxy` (Hutchinson) | +0.220 | +0.283 |

## Per-augmentation breakdown

| Augmentation | n | Mean OOD | Mean `w_learned` | Mean `w_oracle` |
| --- | ---: | ---: | ---: | ---: |
| `full_rotation` | 56 | 0.834 | 0.846 | 0.903 |
| `partial_rotation` | 65 | 0.705 | 0.742 | 0.758 |
| `wrong_permute` | 68 | 0.281 | 0.478 | 0.438 |
| `none` | 67 | 0.270 | 0.484 | 0.403 |

## Headline finding

**Data-inferred group weakness retains 90% of the oracle's predictive
signal.** Learned r = +0.662 vs oracle r = +0.736; both dominate every
classical predictor (parameter L_2, training accuracy, training loss,
Hutchinson sharpness). On a partial-orbit cyclic-symmetry task — precisely
the regime that defeats conventional supervised networks per Perin &
Deny 2024 — the symmetry group is recoverable from training data alone
with high enough fidelity to drive the weakness selector.

## Honest limitation: the random-rotation control is only a partial null

`weakness_random` (10 random rotations from a 24-candidate set, identity
included) has Pearson +0.551 — high. This is not the clean null we wanted
to see. Reason: with 24 evenly-spaced candidate angles, a random subset
of size 10 covers 41% of the candidate space; under our 7.5° matching
tolerance, ~33% of random angles fall within tolerance of a true Z_8 angle
by chance. So the "random-rotation" control inherits some of Z_8's
structure passively.

The cleaner null was already in our prior rotation_weakness paper:
`weakness_wrong_group_norm` under random *pixel permutations* (not random
rotations) had Pearson −0.341, correctly anti-correlated with OOD. The
takeaway is that rotation-from-dense-grid is a soft control; pixel-shuffle
is a hard control. Both confirm that the *cyclic-rotation structure* is
what's load-bearing — but only the second one is a strict null.

## What this advances

- The prior weakness paper proved weakness predicts OOD given oracle group.
  Reviewers correctly objected: "what if you don't have the oracle?"
- This sweep shows that for finite groups recoverable by training-set
  self-consistency, the answer is **the data is enough**: 89.7% recall and
  71.3% precision recovery from training data, and the resulting selector
  retains 90% of the oracle's Pearson correlation with OOD.
- This addresses Perin & Deny 2024's open problem ("networks lack a
  mechanism to learn symmetries not explicitly embedded in architecture
  or sufficiently represented in data") for the enumerable-candidate case.

## What this does not advance

- Continuous groups (SO(3), Lie groups generally).
- Non-enumerable symmetries (paraphrase substitution on a large vocabulary,
  arbitrary algebraic invariants). A neural generator like van der Ouderaa
  2024 is needed.
- Pixel-space similarity is the bottleneck on natural images. A learned
  feature space (e.g., self-supervised encoder) is likely needed at MNIST
  / CIFAR / ImageNet scale.
- Causal validation: we have not retrained models *with* the learned-group
  data augmentation and verified OOD improves correspondingly.
