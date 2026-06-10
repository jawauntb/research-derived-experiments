# Cluttered MNIST sweep: resolution × Gaussian noise

Date: 2026-06-09

## Question

Where does pixel cosine finally fail? Sweep two dimensions of nuisance
variation expected to favour learned-feature methods:

- **resolution** ∈ {16×16 (downsampled), 28×28 (native)}
- **Gaussian background noise σ** ∈ {0.00, 0.10, 0.20, 0.30}

For each of 8 cells, score all 3 methods (v1 pixel cosine, encoder
invariance, encoder enumerative) on a partial-orbit Z_8 MNIST split with
24 candidate angles. Pick the threshold that maximizes F1 per cell.

## Hypothesis

As σ grows, pixel cosine's recall should drop sharply (rotated digits
mis-align relative to the noisy background, breaking exact pixel match),
while encoder methods — trained for class invariance — should be robust.

## Gate

Acceptance:

- At least one cell in which one encoder approach achieves a
  meaningfully higher F1 (≥ 0.1 absolute) than pixel cosine.

Withheld:

- No claim about non-Gaussian clutter (e.g., distractor patches,
  occlusion, structured noise).
- 24 samples per (class, rotation) cell is small; statistical noise
  in the metrics is real.

## Result

Best F1 per (method × cell):

| res | σ | pixel R / P / F1 | enc-inv R / P / F1 | enc-enum R / P / F1 |
| ---: | ---: | --- | --- | --- |
| 16×16 | 0.00 | 1.000 / 0.333 / **0.500** | 1.000 / 0.333 / 0.500 | 1.000 / 0.333 / 0.500 |
| 16×16 | 0.10 | 1.000 / 0.333 / **0.500** | 1.000 / 0.333 / 0.500 | 0.875 / 0.368 / 0.519 |
| 16×16 | 0.20 | 1.000 / 0.333 / **0.500** | 1.000 / 0.333 / 0.500 | 1.000 / 0.333 / 0.500 |
| 16×16 | 0.30 | 1.000 / 0.333 / **0.500** | 1.000 / 0.348 / 0.516 | 1.000 / 0.348 / 0.516 |
| 28×28 | 0.00 | 1.000 / 0.333 / **0.500** | 1.000 / 0.364 / 0.533 | 0.875 / 0.389 / 0.538 |
| 28×28 | 0.10 | 1.000 / 0.333 / **0.500** | 1.000 / 0.333 / 0.500 | 1.000 / 0.333 / 0.500 |
| 28×28 | 0.20 | 1.000 / 0.333 / **0.500** | 1.000 / 0.333 / 0.500 | 1.000 / 0.333 / 0.500 |
| 28×28 | 0.30 | 1.000 / 0.333 / **0.500** | 1.000 / 0.333 / 0.500 | 1.000 / 0.333 / 0.500 |

**Gate not met.** No cell shows a ≥ 0.1 F1 advantage for any encoder
method. The largest single-cell encoder gain is +0.038 F1 (28×28,
σ=0.00, encoder-enumerative).

## Audit

Accepted:

- Pixel cosine maintains **recall = 1.000 across all 8 cells**. Adding
  Gaussian noise up to σ = 0.30 does not break it.
- Encoder methods recover recall = 1.000 in most cells too, but with
  occasional drops (0.875) at specific noise levels.
- All three methods converge on F1 ≈ 0.500 because precision is
  procedure-limited (only 8 of 24 candidate angles are true Z_8, so
  precision ≤ 0.333 when recall is perfect).

Rejected:

- The hypothesis "neural methods finally win when Gaussian noise is
  added" is not supported by this sweep.

Residual content:

- Gaussian noise has zero mean; cosine similarity averages it out.
  MNIST digits are also sparse (most pixels are 0), so noise on the
  background doesn't disturb pixel patterns much.
- The procedure is recall-saturated. The next experiment should add
  **structured clutter** (small distractor patches, partial occlusion,
  digit fragments overlaid) — that's where pixel-cosine should fail.
- F1 is bounded above by 1/3 + ε in this regime because precision is
  capped by the candidate-to-true-angle ratio. A different selection
  criterion (e.g., top-k by score) might give a more informative
  precision number than threshold-based selection.

## Next moves

- Try **structured clutter**: paste random small digit fragments at
  random positions; pixel cosine should mis-match while encoders ignore
  the distractors.
- Try **higher noise** (σ ∈ {0.5, 0.7, 1.0}) — at some level the digit
  signal is destroyed and recall must drop.
- Replace threshold-based selection with top-K (K=8) and re-measure
  precision; the procedure-limit issue would dissolve.
