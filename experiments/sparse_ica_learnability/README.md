# Sparse-ICA Learnability (SIC-C-c second positive witness)

Instrument 9 of the Structural Observatory (see
[`notes/structural_intelligence_conjecture.md`](../../notes/structural_intelligence_conjecture.md)
and [`papers/structural_intelligence/paper.md`](../../papers/structural_intelligence/paper.md) §2.5c).

Hypothesis: paper §2.5c notes that after linear ICA (instrument 8)
"other inductive-bias classes (sparse ICA, iVAE, interventional CRL)
have their own analogues, each with its own sample-complexity theorem.
A full SIC-C-c programme would add one more instrument per class."
This is the sparse-mixing / **independent-mechanism analysis (IMA)**
sibling (Gresele et al. 2021, *Independent Mechanism Analysis, a New
Concept?*): a numerical witness that the IMA-style inductive bias also
lifts Theorem 6's exponential-in-d_Z bound to uniform polynomial
sample complexity.

Method: for each `d_Z ∈ {2, 4, 6, 8}`, `N ∈ {200, 500, 1000, 2000,
5000, 10000}`, and sparsity `s ∈ {0.5, 0.25}` we run `TRIALS = 8`
independent draws of a sparse-linear-ICA problem. Each trial:

- draws a Haar-orthogonal `Q ∈ ℝ^{d_Z × d_Z}` via signed QR of a
  Gaussian;
- draws a Bernoulli(`s`) mask `M ∈ {0, 1}^{d_Z × d_Z}` and applies it
  entry-wise to `Q`, retrying up to `MASK_RETRIES = 32` fresh masks
  if the masked matrix would be rank-deficient (empty row or column,
  or numerical rank < d_Z); on persistent failure falls back to a
  milder `keep_diag` scheme that forces the on-diagonal mask to 1
  before re-QR (auditable via the `scheme_counts` field of the
  summary --- in this run every grid point used the primary
  `full_mask` scheme);
- re-orthonormalises the masked matrix via a second signed QR to
  produce the mixing `A ∈ ℝ^{d_Z × d_Z}`;
- draws Laplace(0, 1) latents `Z ∈ ℝ^{max(N_VALUES) × d_Z}` and forms
  `X = Z Aᵀ`; every smaller `N` reuses the first `N` rows as a
  prefix, so the sample-complexity curve varies only in `N`.

Each `(d_Z, N, s, trial)` fit is `sklearn.decomposition.FastICA(
algorithm = "parallel", fun = "logcosh", whiten = "unit-variance",
max_iter = 2000, tol = 1e-6, random_state = trial)`. Recovery is
scored by the **Amari performance index** on `P := W · A` (0 for a
signed permutation, 1 for a uniformly dense mixture; identical to
instrument 8). All randomness is derived from `BASE_SEED = 0` via
numpy `SeedSequence([BASE_SEED, d_Z, trial, int(round(s * 1000))])`,
so the run is fully deterministic.

Pre-registered gates:

- `SICA_FASTICA_CONVERGES_AT_LARGEST_N_BOTH_SPARSITIES`: at N = 10000
  the averaged Amari index is ≤ 0.02 for every d_Z and every
  sparsity. Empirically every cell clears at ≤ 0.0099 (~2x safety
  margin).
- `SICA_SPARSER_MIXING_IMPROVES_OR_MATCHES_RECOVERY`: at N = 10000
  `amari(s=0.25) − amari(s=0.5) ≤ 0.01` for every d_Z. Empirically
  the largest gap is 0.0012 (d_Z=2), well inside tolerance; d_Z=4
  and d_Z=8 actually see sparser mixing recover *better* than
  denser.
- `SICA_SAMPLE_COMPLEXITY_POLYNOMIAL_IN_D_Z`: for target Amari τ =
  0.03, the smallest N reaching averaged Amari ≤ τ scales
  polynomially in d_Z at every sparsity; fitted slope `b ≤ 3.0`.
  Empirically `b = 0.000` (s=0.5) and `b ≈ 0.508` (s=0.25).
- `SICA_AMARI_MONOTONE_IN_N_AT_EVERY_D_Z_AND_S`: for every (d_Z, s),
  the averaged Amari curve is nonincreasing in N modulo the 0.01
  wobble tolerance.

Result (`amari_mean` averaged over 8 trials):

`s = 0.5` (denser mixing):

| d_Z \ N | 200 | 500 | 1000 | 2000 | 5000 | 10000 |
|:-------:|:---:|:---:|:----:|:----:|:----:|:-----:|
| 2 | 0.0617 | 0.0393 | 0.0239 | 0.0250 | 0.0137 | 0.0078 |
| 4 | 0.0902 | 0.0375 | 0.0296 | 0.0229 | 0.0143 | 0.0090 |
| 6 | 0.1075 | 0.0402 | 0.0277 | 0.0206 | 0.0122 | 0.0091 |
| 8 | 0.0820 | 0.0403 | 0.0282 | 0.0185 | 0.0118 | 0.0092 |

`s = 0.25` (sparser mixing):

| d_Z \ N | 200 | 500 | 1000 | 2000 | 5000 | 10000 |
|:-------:|:---:|:---:|:----:|:----:|:----:|:-----:|
| 2 | 0.0923 | 0.0251 | 0.0225 | 0.0145 | 0.0110 | 0.0089 |
| 4 | 0.0626 | 0.0405 | 0.0283 | 0.0183 | 0.0110 | 0.0084 |
| 6 | 0.0682 | 0.0415 | 0.0296 | 0.0204 | 0.0143 | 0.0099 |
| 8 | 0.0739 | 0.0416 | 0.0285 | 0.0191 | 0.0129 | 0.0089 |

Fitted polynomial exponent `b = 0` (s=0.5) and `b ≈ 0.51` (s=0.25)
at τ = 0.03. Sparser-vs-denser deltas at N=10000 are all within
[-0.001, +0.001], well inside the 0.01 tolerance. All four
pre-registered gates pass.

Together with instrument 8, this shows that the SIC-C-c transition
from "exponential in d_Z" (empirical common-sufficient clustering)
to "polynomial in d_Z" (identifiable-latent inductive-bias classes)
is numerically visible for at least two distinct inductive biases
--- dense linear ICA (instrument 8) and sparse mixing / IMA
(instrument 9) --- at modest sample sizes. The paper's discussion of
Theorem 6 is explicit that this list is not exhaustive; the two
instruments here are two points on the promised
"one-instrument-per-class" spectrum, not a claim that every
inductive-bias class lifts the exponential barrier.

Run:

```bash
python3 experiments/sparse_ica_learnability/experiment.py
```
