# Linear-ICA Learnability (SIC-C-c partial positive witness)

Instrument 8 of the Structural Observatory (see
[`notes/structural_intelligence_conjecture.md`](../../notes/structural_intelligence_conjecture.md)
and [`papers/structural_intelligence/paper.md`](../../papers/structural_intelligence/paper.md) §2.5b).

Hypothesis: Theorem 6 (Continuous-case learnability, at resolution ε) says
empirical common-sufficient clustering has sample complexity polynomial in
1/ε at fixed d_Z but *exponential in d_Z at fixed ε* — the ε-covering
curse of dimensionality. SIC-C-c asks: can we restore uniform polynomial-
in-d_Z sample complexity by restricting to a specific inductive-bias
hypothesis class? For **linear ICA** the answer is well known to be yes;
this instrument is a numerical witness on a (d_Z, N) sample-complexity
grid that escapes the Theorem 6 exponential bound by several orders of
magnitude.

Method: for each d_Z ∈ {2, 4, 6, 8} and N ∈ {200, 500, 1000, 2000, 5000,
10000}, we run `TRIALS = 8` independent draws of a linear-ICA problem.
Each trial samples

- a square orthogonal mixing matrix `A ∈ ℝ^{d_Z × d_Z}` via signed QR of
  a Gaussian (Haar on `O(d_Z)`);
- Laplace(0, 1) latents `Z ∈ ℝ^{max(N_VALUES) × d_Z}` (non-Gaussian, so
  linear ICA is provably identifiable), and forms `X = Z Aᵀ`;
- every smaller N in the sweep reuses the first `N` rows of the same
  draw as a prefix, so the sample-complexity curve varies only in N.

Each `(d_Z, N, trial)` fit is `sklearn.decomposition.FastICA(algorithm =
"parallel", fun = "logcosh", whiten = "unit-variance", max_iter = 2000,
tol = 1e-6, random_state = trial)`. Recovery is scored by the **Amari
performance index** on `P := W · A`:

    amari(P) = 1 / (2·d·(d - 1)) · [
        Σ_i (Σ_j |P_ij| / max_j |P_ij| - 1)
      + Σ_j (Σ_i |P_ij| / max_i |P_ij| - 1)
    ]

which is 0 for any signed permutation (perfect recovery up to the ICA
identifiability class) and 1 for a uniformly dense mixture. All
randomness is derived from a single `BASE_SEED = 0` via numpy
`SeedSequence([BASE_SEED, d_Z, trial])`, so the run is deterministic.

Pre-registered gates:

- `linear_ica_converges_at_largest_N`: at N = 10000, the averaged Amari
  index is ≤ 0.02 for every d_Z. Empirically clears at ≤ 0.009 across
  all d_Z (2x safety margin).
- `sample_complexity_polynomial_in_d_Z`: for target Amari τ = 0.03, the
  smallest N in the sweep reaching averaged Amari ≤ τ scales
  polynomially in d_Z; fit `log(N_needed) = a + b · log(d_Z)` yields
  slope `b ≤ 3.0`. Empirically `b ≈ 0.065` — well inside the bound.
- `amari_monotone_in_N_at_every_d_Z`: for every d_Z, the averaged Amari
  curve is nonincreasing in N modulo a 0.01 wobble tolerance
  (finite-sample FastICA variance).
- `escapes_theorem_6_exponential`: at d_Z = 8 the linear-ICA sample
  complexity to reach Amari ≤ 0.03 is at least 20x below the Theorem 6
  exponential bound `⌈(D_Z/ε)^{d_Z} · ln((D_Z/ε)^{d_Z}/ε_rel)⌉` with
  D_Z = 1, ε = 0.25, ε_rel = 0.05, c = 1. That bound at d_Z = 8 is
  923146 samples; the linear-ICA class needs N = 2000, an escape factor
  of ≈ 462x.

Result (`amari_mean` averaged over 8 trials):

| d_Z \ N | 200 | 500 | 1000 | 2000 | 5000 | 10000 |
|:-------:|:---:|:---:|:----:|:----:|:----:|:-----:|
| 2 | 0.0612 | 0.0333 | 0.0357 | 0.0247 | 0.0103 | 0.0070 |
| 4 | 0.0790 | 0.0387 | 0.0278 | 0.0188 | 0.0117 | 0.0080 |
| 6 | 0.0847 | 0.0414 | 0.0308 | 0.0213 | 0.0123 | 0.0083 |
| 8 | 0.0755 | 0.0457 | 0.0311 | 0.0209 | 0.0123 | 0.0089 |

Fitted polynomial exponent `b ≈ 0.065` at τ = 0.03. Theorem-6 escape
ratio at d_Z = 8 is ≈ 462x. All four pre-registered gates pass.

This is not a claim that all inductive-bias classes lift SIC-C-c's
polynomial-in-d_Z bar; the paper's discussion of Theorem 6 makes explicit
that ICA is one of a small family of classes (linear ICA, sparse coding,
exponential-family conditional latents, interventional data) for which
identifiability + uniform sample complexity is known. What this
instrument shows is that within the linear-ICA class, the transition
from "exponential in d_Z" (empirical common-sufficient clustering) to
"polynomial in d_Z" (linear ICA) is numerically visible at modest sample
sizes.

Run:

```bash
python3 experiments/linear_ica_learnability/experiment.py
```
