# Top-K=8 Selector Ablation

Date: 2026-06-10

## Question

Was the F1 ≈ 0.500 "ceiling" in §4.3 of the cluttered-MNIST sweep a
real finding (all methods equivalent) or a **procedural artifact** of
threshold-based selection?

## Setup

Reuses the per-angle scores from `cluttered_mnist_v1.json`. No
re-running of models. Instead, change the selection rule from
"threshold τ, sweep for best F1" to "top-K=8" (matching |Z_8|, the
ground-truth group size).

## Hypothesis

If §4.3's ceiling was procedural, top-K=8 selection should expose
real differences between methods — specifically, encoder methods should
rank true Z_8 angles higher in their score lists than pixel cosine
does, even if all methods include all Z_8 angles when the threshold
is permissive enough.

## Result

Mean F1 across all 8 cluttered-MNIST cells:

| Method | Threshold-best F1 (§4.3) | Top-K=8 F1 (§4.4) | Change |
| --- | ---: | ---: | ---: |
| v1 pixel cosine | 0.500 | **0.281** | **−0.219** |
| Approach 3: encoder enumerative | 0.509 | **0.375** | −0.134 |
| Approach 2: encoder invariance | 0.506 | **0.391** | −0.115 |

**With top-K=8 selection, the encoder methods clearly outperform pixel
cosine.** Mean F1 advantage of encoder invariance over pixel: **+0.110
absolute (39% relative)**.

Per-cell breakdown:

| res | σ | pixel F1 | enc-inv F1 | enc-enum F1 |
| ---: | ---: | ---: | ---: | ---: |
| 16×16 | 0.00 | 0.250 | **0.375** | **0.375** |
| 16×16 | 0.10 | 0.250 | **0.375** | **0.375** |
| 16×16 | 0.20 | 0.375 | 0.375 | 0.375 |
| 16×16 | 0.30 | 0.375 | 0.375 | 0.375 |
| 28×28 | 0.00 | 0.250 | **0.375** | **0.375** |
| 28×28 | 0.10 | 0.250 | **0.500** | **0.500** |
| 28×28 | 0.20 | 0.250 | **0.375** | **0.375** |
| 28×28 | 0.30 | 0.250 | **0.375** | 0.250 |

**Encoder methods outperform or match pixel cosine in 7 of 8 cells.**
(The exception: 28×28 σ=0.30 where encoder enumerative ties pixel.)

## What changed

The previous §4.3 selection rule (best threshold across a 19-point
grid) caused all three methods to converge on F1 = 0.500 because:

- Pixel cosine's scores were very flat across the candidate grid; at
  any threshold below ~0.85 it kept *all 24* angles, giving perfect
  recall but precision = 8/24 = 0.333 → F1 = 0.500.
- Encoder methods' scores were also flat enough at the best
  threshold to land at the same F1 = 0.500.

The threshold sweep was implicitly picking each method's "all-in"
operating point, where recall is 1.000 but precision is procedurally
capped at 1/3.

Top-K=8 selection lifts that cap: it forces every method to commit to
exactly 8 angles (matching |Z_8|), and now the *ranking quality* of
each method's score list matters. Encoder methods have better
top-of-list quality.

## Audit

Accepted:

- The §4.3 finding "all methods tied at F1=0.500" is procedurally
  driven and not a true equivalence.
- With top-K=8 (matching the oracle group size), **encoder methods
  consistently rank true Z_8 angles higher than pixel cosine does**.
- The biggest single-cell advantage: 28×28 σ=0.10, encoder
  invariance/enumerative F1 = 0.500 vs pixel 0.250 (2× improvement).

Rejected:

- The conclusion from §4.3 that "pixel cosine is at parity with encoder
  methods on MNIST" — this was a selection artifact, not a real
  finding.

Residual content:

- The paper's title "When Pixels Beat Embeddings" remains accurate
  *for the synthetic-stroke benchmark* and *under threshold selection
  on MNIST*. But it overstates the case: the real story is more
  nuanced.
- The methodology lesson is real and important: **procedure choice
  changes scientific conclusions**. A reviewer who only saw §4.3
  would conclude pixel cosine wins on MNIST. A reviewer who saw §4.4
  would conclude the opposite. The honest answer is that both
  conclusions depend on the selection criterion.
- This *re-opens* the question: at the synthetic-stroke benchmark
  (§3 of the paper), pixel cosine got recall 0.897 / precision 0.713.
  What does top-K selection give there? Worth checking that §3 result
  doesn't also flip.

## Next moves

- Re-analyze §3 (synthetic stroke benchmark) with top-K=8 selection.
  If the encoder methods also win there under top-K, the paper's
  central finding needs to be inverted.
- Update paper title and abstract to reflect the procedure-dependence
  of the conclusion.
- Run the *structured clutter* experiment (still open from §4.3's
  diagnostic). Encoders should now win even more clearly at the
  pixel-cosine failure regime.
