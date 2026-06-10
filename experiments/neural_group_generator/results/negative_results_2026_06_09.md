# Neural Group Discovery: Two Negative Results

Date: 2026-06-09

## Question

Can a neural module replace the enumerative `infer_rotation_group_from_training`
procedure from the Learning the Group paper for non-enumerable symmetries?

## Setup

Same rotated-stroke partial-orbit benchmark (8 classes × 3-of-8 training
rotations × 16×16 grayscale). Reference: v1 enumerative procedure with
pixel-cosine self-consistency achieves **89.7% recall, 71.3% precision**
vs the oracle Z_8 group at threshold τ = 0.5.

## Approach 1: Direct rotation-angle generator

A small CNN-encoder + MLP that takes anchor image x and latent z ∈ R^4
and predicts a rotation angle θ ∈ R. Training loss:

- intra-class: rotate(x_i, θ) should be close to nearest same-class x_j
- diversity: K = 8 simultaneous z draws should produce angles spread
  on the circle (low pairwise 1 + cos Δθ)

After training, sample many z's per anchor and find peaks in the angle
distribution.

### Result

**Mode collapses to θ ≈ 0.** Across all z draws, the predicted angles
cluster within ±10° of identity. Top peak after NMS: 2.5°. Recall vs
Z_8 = 12.5% (only the identity is recovered).

Diagnostic: the intra-class loss is already low at θ = 0 because the
nearest same-class example (out of 24 per class) has some baseline
similarity to the anchor without any rotation. The diversity term
cannot overcome this local minimum without much stronger regularization
that itself distorts the learned distribution.

## Approach 2: Contrastive encoder + invariance scoring

A small CNN encoder e_φ trained via supervised contrastive (SupCon) loss
to pull same-class examples together. The encoder's *implicit invariance
group* is the set of input-space rotations under which e_φ(rotate(x, θ))
≈ e_φ(x). We score each candidate angle θ by mean cosine similarity.

### Result

The encoder shows highest invariance for **small rotations near 0°**
(perceptual smoothness), not for the true Z_8 angles. Top 12 angles by
invariance score:

| Angle | Encoder cosine | In Z_8? |
| ---: | ---: | --- |
| 0° | 1.000 | ✓ |
| 5° | 0.918 | ✗ |
| 355° | 0.897 | ✗ |
| 10° | 0.806 | ✗ |
| 350° | 0.784 | ✗ |
| 15° | 0.748 | ✗ |
| 20° | 0.706 | ✗ |
| 345° | 0.703 | ✗ |
| ... | ... | ... |

The encoder learns to cluster same-class examples into a single point
regardless of rotation; small rotations preserve this point (because
they don't change perception much), and large rotations move away
(because the perceptual content changes). **Encoder invariance reflects
perceptual smoothness, not data symmetry.**

## Approach 3: Enumerative procedure with encoder features

Replace pixel cosine in the v1 procedure with learned-encoder cosine.
Use the trained SupCon encoder as a feature extractor; otherwise
identical to v1.

### Result

| Threshold τ | Kept angles | Recall vs Z_8 | Precision vs Z_8 |
| ---: | ---: | ---: | ---: |
| 0.5 | 8 | **0.375** | **0.375** |
| 0.6 | 5 | 0.250 | 0.400 |
| 0.7 | 3 | 0.125 | 0.333 |
| 0.8 | 1 | 0.125 | 1.000 |

For reference, v1 with **pixel** cosine: recall 0.897, precision 0.713.

**Learned features hurt group discovery on this task.** The encoder
over-generalizes, treating non-Z_8 rotations (15°, 30°, 330°, 345°) as
similar to identity. Pixel cosine, paradoxically, is sharper because it
is literal: rotating by 45° produces a pixel pattern that matches
another training example only when 45° is in the true symmetry orbit.

## Combined headline

Across two natural neural approaches and one hybrid, **none beats the
pixel-cosine enumerative baseline** on this task:

| Method | Recall vs Z_8 | Precision vs Z_8 |
| --- | ---: | ---: |
| v1 enumerative with pixel cosine (Learning the Group baseline) | **0.897** | **0.713** |
| Encoder-based enumerative (this paper, Approach 3) | 0.375 | 0.375 |
| Direct rotation generator (this paper, Approach 1) | 0.125 | 1.000 |
| Encoder invariance scoring (this paper, Approach 2) | 0.250 | 0.250 |

## What this means

The enumerative pixel-cosine procedure works precisely because:

1. It tests *specific candidate rotations* against the training data.
2. The criterion is *exact intra-class match*: rotate(x_i, θ) must
   land near a *literal* training image x_j of the same class.
3. The procedure is selective: rotations that don't preserve literal
   pixel content rarely match anything.

Neural alternatives fail in distinctive ways:

- **Generators** must produce a *parameter*, and the loss landscape
  rewards safe (identity-like) outputs.
- **Encoders** abstract too aggressively, washing out the geometric
  precision the enumerative procedure exploits.

This is not a claim that neural approaches *cannot* work for group
discovery — only that two natural approaches do not work on
controlled-rotation data where pixel cosine is essentially optimal.
The natural follow-on is to test these methods on *natural* images
where pixel cosine should fail (cluttered backgrounds, texture
variation, partial occlusion). In that regime, an encoder's ability to
ignore irrelevant variation may matter more than its tendency to
over-generalize.

## Audit

Accepted:

- Three distinct neural approaches were tested and reported with
  ground-truth recall/precision vs oracle Z_8.
- All three underperform the v1 pixel-cosine baseline on this benchmark.
- Diagnostic explanations are given for each failure mode (mode
  collapse for generators; perceptual smoothness for encoder invariance;
  over-generalization for encoder-based enumeration).

Rejected/withheld:

- We do not claim neural approaches cannot work for symmetry discovery
  in general.
- We do not claim pixel cosine is universally better; it likely fails
  on natural images, which we have not tested.
- We do not propose a *new* neural method that works — only document
  what does not.

## Next moves

- Test all three approaches on rotated MNIST or rotated CIFAR-10, where
  pixel cosine is known to fail.
- Try a CONDITIONAL FLOW or learned-equivariant architecture (e.g.,
  van der Ouderaa 2024) as Approach 4.
- Combine: use encoder features for a coarse pass, then refine with
  pixel cosine.
