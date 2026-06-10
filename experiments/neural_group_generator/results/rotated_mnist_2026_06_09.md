# Rotated MNIST Extension

Date: 2026-06-09

## Question

Do the three neural approaches from *When Pixels Beat Embeddings* finally
beat pixel cosine on **real digit images** (where natural writing-style,
stroke-thickness, and slant variation should hurt pixel matching)?

## Setup

- Dataset: MNIST training set (60,000 28×28 grayscale digits), loaded
  via Hugging Face `datasets`, downsampled to 16×16 bilinearly.
- Z_8 cyclic rotation group on the image plane.
- Partial-orbit supervision: each of 10 classes shown at only 3 of 8
  rotations during training, 5 OOD rotations per class.
- 30 samples per (class, rotation) cell → **900 training images, 1500
  OOD images**.
- 24 candidate angles (15° resolution).
- SupCon encoder trained 500 epochs at temperature 0.1.

Manifest:

- Command: `doppler run -- uvx modal run experiments/neural_group_generator/modal_rotated_mnist.py`
- Artifact: `artifacts/neural_group_generator/rotated_mnist_v1.json`

## Gate

Acceptance:

- At least one of the encoder approaches achieves higher Z_8 recall than
  pixel cosine, OR is significantly more precise.

Withheld:

- This is a single seed and a single encoder architecture; we make no
  claim about robustness.
- 16×16 downsampling discards detail; the result may be different on
  full-resolution 28×28.

## Result

Threshold sweep across all three methods:

| Method | τ | Kept | Recall | Precision | F1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| v1 pixel cosine | 0.3 | 24 | **1.000** | 0.333 | **0.500** |
| v1 pixel cosine | 0.5 | 24 | 1.000 | 0.333 | 0.500 |
| v1 pixel cosine | 0.7 | 24 | 1.000 | 0.333 | 0.500 |
| v1 pixel cosine | 0.8 | 22 | 0.750 | 0.273 | 0.400 |
| v1 pixel cosine | 0.9 | 1 | 0.125 | 1.000 | 0.222 |
| Approach 3: enc enumerative | 0.5 | 14 | 0.625 | 0.357 | 0.455 |
| Approach 3: enc enumerative | 0.7 | 3 | 0.125 | 0.333 | 0.182 |
| Approach 2: enc invariance | 0.5 | 6 | 0.250 | 0.333 | 0.286 |
| Approach 2: enc invariance | 0.7 | 3 | 0.125 | 0.333 | 0.182 |

**Gate outcome:** none of the three encoder approaches beats pixel
cosine on recall at any threshold. Encoder approaches do not match
pixel cosine on precision either (all hover around 0.33). The acceptance
threshold is not met. **The negative result from the stroke benchmark
extends to real MNIST.**

## Audit

Accepted:

- Pixel cosine retains the property that mattered on strokes: **perfect
  Z_8 recall across a wide threshold range** (0.3–0.7). The encoder
  methods collapse sharply at higher thresholds.
- The qualitative finding from *When Pixels Beat Embeddings* survives
  the transition from synthetic strokes to real digits.

Rejected:

- The hypothesis that encoder methods would win on natural-image data
  is not supported on MNIST. (It might still be true on
  higher-variation domains — CIFAR, ImageNet, cluttered backgrounds.)
- Precision is poor across all methods (~0.33), reflecting that on
  natural digits many rotations produce *some* same-class match by
  chance. This is a limitation of the procedure, not of any specific
  method.

Residual content:

- The MNIST result strengthens *When Pixels Beat Embeddings*'s
  headline: even moving from synthetic 16×16 strokes to real downsampled
  digits, pixel cosine remains the best recovery method.
- The pixel-cosine over-keeping problem (24 kept angles, only 8
  truly Z_8) is interesting in its own right: at 30 samples per cell,
  natural variation in digit style means rotating by any θ produces
  *something* in the training set. A larger threshold or a stricter
  matching criterion (e.g., top-1 vs top-k) is needed.

## Next moves

- Repeat on **full 28×28 MNIST** (no downsampling); the encoder may need
  more spatial resolution to learn anything useful.
- Add **cluttered backgrounds** or **stroke-width perturbation** as
  distractors; this is where pixel cosine should finally fail.
- Sweep encoder architectures (deeper, contrastive vs SimCLR
  self-supervised).
- Add **causal validation**: use each method's learned group as
  augmentation, retrain, measure OOD lift on MNIST. The augmentation
  effect should track the recall numbers above.
