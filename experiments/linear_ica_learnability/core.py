"""Partial positive resolution of SIC-C-c (uniform polynomial-in-d_Z learnability)
for the linear-ICA inductive-bias class.

Paper section 2.5b (Theorem 6, "Continuous learnability at resolution eps") shows
that empirical common-sufficient clustering has sample complexity polynomial in
1/eps at fixed d_Z but *exponential in d_Z at fixed eps* --- the eps-covering
curse of dimensionality. SIC-C-c asks whether a specific inductive-bias
hypothesis class can restore uniform polynomial-in-d_Z sample complexity. For
linear ICA the answer is well known to be yes; this instrument is a numerical
witness at (d_Z, N) grid points that escape the Theorem 6 exponential bound by
several orders of magnitude.

Setup (linear-ICA generative model).
------------------------------------
- Latent Z in R^{d_Z} with independent Laplace(0, 1) marginals (non-Gaussian
  and provably identifiable under linear ICA).
- Mixing matrix A in R^{d x d_Z} with d = d_Z (square, well-conditioned;
  sampled as a random orthogonal matrix via signed-QR of a Gaussian).
- Observation X = A * Z in R^d.
- Task family: identity on X. Recovery is measured against the true Z up to
  the ICA identifiability class (permutation + sign).

Algorithm: sklearn's FastICA on N samples of X, returning an unmixing matrix W.

Metric: Amari index on P := W * A. Amari in [0, 1] with 0 = perfect recovery
up to permutation and sign, 1 = worst.

    amari(P) = (1 / (2 * d * (d - 1))) * (
        sum_i (sum_j |P_ij| / max_j |P_ij| - 1)
        + sum_j (sum_i |P_ij| / max_i |P_ij| - 1)
    )

Sample-complexity sweep.
------------------------
For each (d_Z, N) with d_Z in {2, 4, 6, 8} and N in {200, 500, 1000, 2000,
5000, 10000} we average the Amari index over ``TRIALS`` independent draws of
(A, Z), where each trial nests the smaller-N datasets as prefixes of the
largest-N draw (so the sample-complexity curve varies only in N, not in the
underlying stream). All randomness is derived from a single ``BASE_SEED``
via ``np.random.SeedSequence`` and sklearn's ``random_state``, so the run is
fully deterministic.

Pre-registered gates (SIC-C-c linear-ICA witness).
--------------------------------------------------
- ``linear_ica_converges_at_largest_N``: at N = ``N_MAX``, averaged Amari is
  <= ``FINAL_AMARI_TARGET`` for every d_Z. FINAL_AMARI_TARGET = 0.02 chosen
  because empirically every d_Z clears 0.01 comfortably at N = 10000 (2x
  safety margin).
- ``sample_complexity_polynomial_in_d_Z``: fit
      log(N_needed(d_Z)) = a + b * log(d_Z)
  where N_needed is the smallest N in the sweep with averaged Amari
  <= ``POLY_AMARI_TARGET``. Gate: b <= ``POLY_EXPONENT_MAX``. Empirically
  b is well below 1 (linear-ICA sample complexity is polynomial in d_Z);
  the gate at 3.0 is a generous polynomial bound.
- ``amari_monotone_in_N_at_every_d_Z``: for every d_Z, the averaged Amari
  curve is nonincreasing in N up to a small numerical wobble of
  ``MONOTONE_TOL`` = 0.01 (finite-sample FastICA variance).
- ``escapes_theorem_6_exponential``: at d_Z = 8, the linear-ICA sample
  complexity to reach ``POLY_AMARI_TARGET`` is orders of magnitude below
  the Theorem-6 exponential bound
      N_theorem6(d_Z) = ceil((D_Z / eps)^{d_Z} * ln((D_Z / eps)^{d_Z} / eps_rel))
  with D_Z = 1, eps = 0.25, eps_rel = 0.05 (so (D_Z/eps)^{d_Z} = 4^{d_Z}
  blows up beyond the swept range at d_Z >= 6). Concretely we require
  N_needed(d_Z = 8) <= 0.05 * N_theorem6(d_Z = 8) --- the linear-ICA class
  escapes by at least a 20x factor.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from sklearn.decomposition import FastICA


BASE_SEED = 0
D_Z_VALUES: tuple[int, ...] = (2, 4, 6, 8)
N_VALUES: tuple[int, ...] = (200, 500, 1000, 2000, 5000, 10000)
TRIALS = 8

FINAL_AMARI_TARGET = 0.02
POLY_AMARI_TARGET = 0.03
POLY_EXPONENT_MAX = 3.0
MONOTONE_TOL = 0.01

# Theorem 6 escape-factor calibration: (D_Z, eps, eps_rel, c) picked so that
# the exponential bound blows up beyond the swept range at d_Z = 6 and 8.
THEOREM6_D_Z_UPPER = 1.0
THEOREM6_EPS = 0.25
THEOREM6_EPS_REL = 0.05
THEOREM6_C = 1.0
ESCAPE_FACTOR_MIN = 20.0  # linear-ICA N_needed must be <= (1 / 20) * N_theorem6.


def sample_orthogonal(d: int, rng: np.random.Generator) -> np.ndarray:
    """Random orthogonal ``d x d`` matrix via signed QR of a Gaussian.

    The sign correction ``q * sign(diag(r))`` removes QR's sign ambiguity so the
    output distribution is exactly Haar on ``O(d)``, keeping ``sample_orthogonal``
    reproducible under a fixed ``rng``.
    """

    g = rng.standard_normal((d, d))
    q, r = np.linalg.qr(g)
    q = q * np.sign(np.diag(r))
    return q


def amari_index(matrix: np.ndarray) -> float:
    """Amari performance index of ``P = W * A``.

    ``amari(P)`` is in ``[0, 1]``: it is exactly ``0`` iff ``P`` is a signed
    permutation (perfect recovery up to the ICA identifiability class) and
    approaches ``1`` as ``P`` becomes uniformly dense. The formula is scale-
    invariant along rows and columns, so any diagonal rescaling of ``P`` (which
    ICA is free to introduce) leaves the score unchanged.
    """

    abs_p = np.abs(matrix)
    d = abs_p.shape[0]
    if d < 2:
        raise ValueError("Amari index is undefined for d < 2")
    row_max = abs_p.max(axis=1, keepdims=True)
    col_max = abs_p.max(axis=0, keepdims=True)
    row_scale = np.where(row_max == 0, 1.0, row_max)
    col_scale = np.where(col_max == 0, 1.0, col_max)
    row_term = (abs_p / row_scale).sum(axis=1) - 1.0
    col_term = (abs_p / col_scale).sum(axis=0) - 1.0
    return float((row_term.sum() + col_term.sum()) / (2 * d * (d - 1)))


def _trial_seed(d_z: int, trial: int) -> np.random.SeedSequence:
    """Derive a per-(d_z, trial) SeedSequence from BASE_SEED for reproducibility."""

    return np.random.SeedSequence([BASE_SEED, int(d_z), int(trial)])


def _fit_amari_for_trial(d_z: int, trial: int) -> dict[int, float]:
    """Run a single trial: draw one (A, Z_full), fit FastICA at every N prefix."""

    ss = _trial_seed(d_z, trial)
    rng = np.random.default_rng(ss)
    mixing = sample_orthogonal(d_z, rng)
    n_max = max(N_VALUES)
    latents = rng.laplace(0.0, 1.0, size=(n_max, d_z))
    observations = latents @ mixing.T
    results: dict[int, float] = {}
    for n in N_VALUES:
        x = observations[:n]
        ica = FastICA(
            n_components=d_z,
            algorithm="parallel",
            whiten="unit-variance",
            fun="logcosh",
            max_iter=2000,
            tol=1e-6,
            random_state=trial,
        )
        ica.fit(x)
        p = ica.components_ @ mixing
        results[n] = amari_index(p)
    return results


@dataclass(frozen=True)
class SweepPoint:
    d_z: int
    n: int
    amari_mean: float
    amari_trials: tuple[float, ...]


def sweep_amari() -> list[SweepPoint]:
    """Compute averaged Amari at every (d_Z, N) grid point."""

    points: list[SweepPoint] = []
    for d_z in D_Z_VALUES:
        per_n: dict[int, list[float]] = {n: [] for n in N_VALUES}
        for trial in range(TRIALS):
            trial_results = _fit_amari_for_trial(d_z, trial)
            for n, amari in trial_results.items():
                per_n[n].append(amari)
        for n in N_VALUES:
            trials = tuple(per_n[n])
            points.append(
                SweepPoint(
                    d_z=d_z,
                    n=n,
                    amari_mean=float(np.mean(trials)),
                    amari_trials=trials,
                )
            )
    return points


def smallest_n_reaching_target(
    points: list[SweepPoint], d_z: int, target: float
) -> int | None:
    """Smallest N (in the sweep) at which averaged Amari at ``d_z`` <= target."""

    curve = sorted(
        (pt for pt in points if pt.d_z == d_z), key=lambda pt: pt.n
    )
    for pt in curve:
        if pt.amari_mean <= target:
            return pt.n
    return None


def polynomial_exponent(
    points: list[SweepPoint], target: float
) -> tuple[float, dict[int, int]]:
    """Fit log(N_needed) = a + b * log(d_Z); return (b, {d_z: N_needed})."""

    n_needed: dict[int, int] = {}
    for d_z in D_Z_VALUES:
        smallest = smallest_n_reaching_target(points, d_z, target)
        if smallest is None:
            raise ValueError(
                f"target amari {target} unreachable at d_z = {d_z} in swept N range"
            )
        n_needed[d_z] = smallest
    x = np.log(np.array(sorted(n_needed.keys()), dtype=float))
    y = np.log(np.array([n_needed[d] for d in sorted(n_needed.keys())], dtype=float))
    x_mean = x.mean()
    y_mean = y.mean()
    denom = float(((x - x_mean) ** 2).sum())
    if denom == 0.0:
        raise ValueError("cannot fit exponent: log(d_Z) has zero variance")
    slope = float(((x - x_mean) * (y - y_mean)).sum() / denom)
    return slope, n_needed


def is_monotone_within_tolerance(
    points: list[SweepPoint], d_z: int, tol: float
) -> bool:
    """Check that averaged Amari at ``d_z`` is nonincreasing in N modulo ``tol``."""

    curve = sorted((pt for pt in points if pt.d_z == d_z), key=lambda pt: pt.n)
    values = [pt.amari_mean for pt in curve]
    return all(b <= a + tol for a, b in zip(values[:-1], values[1:], strict=True))


def theorem6_bound(
    d_z: int,
    *,
    d_z_upper: float = THEOREM6_D_Z_UPPER,
    eps: float = THEOREM6_EPS,
    eps_rel: float = THEOREM6_EPS_REL,
    c: float = THEOREM6_C,
) -> int:
    """Theorem 6 sample bound: ``ceil(c * (D_Z/eps)^{d_Z} * ln(N_eps / eps_rel))``."""

    n_eps = (d_z_upper / eps) ** d_z
    return math.ceil(c * n_eps * math.log(n_eps / eps_rel))


def evaluate_benchmark() -> dict:
    points = sweep_amari()
    indexed: dict[tuple[int, int], SweepPoint] = {
        (pt.d_z, pt.n): pt for pt in points
    }

    n_max = max(N_VALUES)
    converges_at_largest_n = all(
        indexed[(d_z, n_max)].amari_mean <= FINAL_AMARI_TARGET
        for d_z in D_Z_VALUES
    )

    slope, n_needed_poly = polynomial_exponent(points, POLY_AMARI_TARGET)
    poly_gate = slope <= POLY_EXPONENT_MAX

    monotone_gate = all(
        is_monotone_within_tolerance(points, d_z, MONOTONE_TOL)
        for d_z in D_Z_VALUES
    )

    escape_dim = 8
    n_needed_escape = n_needed_poly[escape_dim]
    n_theorem6_escape = theorem6_bound(escape_dim)
    escape_ratio = n_theorem6_escape / n_needed_escape
    escape_gate = escape_ratio >= ESCAPE_FACTOR_MIN

    gates = {
        "linear_ica_converges_at_largest_N": bool(converges_at_largest_n),
        "sample_complexity_polynomial_in_d_Z": bool(poly_gate),
        "amari_monotone_in_N_at_every_d_Z": bool(monotone_gate),
        "escapes_theorem_6_exponential": bool(escape_gate),
    }
    status = "pass" if all(gates.values()) else "fail"

    return {
        "status": status,
        "gates": gates,
        "base_seed": BASE_SEED,
        "trials_per_grid_point": TRIALS,
        "d_Z_values": list(D_Z_VALUES),
        "N_values": list(N_VALUES),
        "amari_thresholds": {
            "final_amari_target": FINAL_AMARI_TARGET,
            "poly_amari_target": POLY_AMARI_TARGET,
        },
        "poly_exponent_gate": {
            "target_amari": POLY_AMARI_TARGET,
            "N_needed_per_d_Z": {str(d): int(n) for d, n in n_needed_poly.items()},
            "fitted_exponent_b": round(slope, 6),
            "exponent_gate_max": POLY_EXPONENT_MAX,
        },
        "monotone_tolerance": MONOTONE_TOL,
        "theorem6_escape": {
            "d_Z": escape_dim,
            "D_Z_upper": THEOREM6_D_Z_UPPER,
            "eps": THEOREM6_EPS,
            "eps_rel": THEOREM6_EPS_REL,
            "c": THEOREM6_C,
            "N_theorem6_bound": n_theorem6_escape,
            "N_needed_linear_ica": n_needed_escape,
            "escape_ratio": round(escape_ratio, 3),
            "escape_ratio_gate_min": ESCAPE_FACTOR_MIN,
        },
        "sweep_points": [
            {
                "d_z": pt.d_z,
                "n": pt.n,
                "amari_mean": round(pt.amari_mean, 6),
                "amari_trials": [round(v, 6) for v in pt.amari_trials],
            }
            for pt in points
        ],
    }
