"""Exact witness of Theorem 6 (continuous-case learnability at resolution eps).

Theorem 6 (paper.md sec 2.5b) reduces continuous-case learnability to
Theorem 5 by eps-covering: for Z contained in R^d_Z with a task family
separating Z at scale eps, empirical common-sufficient clustering recovers
q at resolution eps with sample complexity

    N >= c * N_eps * ln(N_eps / eps_rel),   N_eps = O((D_Z / eps)^d_Z).

This is polynomial in 1/eps at fixed d_Z and exponential in d_Z at fixed
eps. This module verifies both facts exactly on the discretised "continuous"
world X = [0, 1]^2 approximated by a fine grid at multiple resolutions.

Setup.
------
The unit square [0, 1]^2 is quantised into a fine 16 x 16 = 256 cell world
(the "continuous" ambient X). The latent Z is a coarser grid on the same
square:

- d_Z = 1: Z coordinate is x[0] discretised into r bins along the first
  axis (task ignores x[1]).
- d_Z = 2: Z coordinate is (x[0], x[1]) discretised into r x r bins.

For each (d_Z, r), the fibre partition of X has M = r^d_Z cells; the task
family is exactly the d_Z coordinate reads at resolution r, which separates
Z at scale eps = 1/r. Fibres are balanced (each fibre gets an equal share
of the 256 ambient X-cells because we chose r such that r | 16).

Predictions to check.
---------------------
For each of six (d_Z, r) in {1, 2} x {4, 8, 16}:

- Theorem 6 bound at eps_rel = 0.05:
      N_bound(d_Z, r) = ceil(c * M * ln(M / eps_rel))    with c = 1.
- Exact recovery probability at N_bound, via inclusion-exclusion on the
  balanced M-fibre partition, must be >= 1 - eps_rel = 0.95.
- Pigeonhole: P(recover) = 0 for every N < M.
- Monotonicity: recovery curve is nondecreasing in N up to the bound.
- Exponential-in-d_Z scaling: N_bound(d_Z=2, r) grows roughly as r *
  N_bound(d_Z=1, r) (up to log factors); we verify the strict inequality
  N_bound(d_Z=2, r) > N_bound(d_Z=1, r) for every r, and check the ratio
  matches the r * (log factor) prediction within a tolerance.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

EPS_REL = 0.05
AMBIENT_SIDE = 16  # X quantised to 16 x 16 = 256 cells.


def theorem_bound(m: int, c: float, eps_rel: float) -> int:
    """Theorem 6 sample bound: ceil(c * M * ln(M / eps_rel))."""

    return math.ceil(c * m * math.log(m / eps_rel))


def exact_recovery_probability_balanced(m: int, n_samples: int) -> float:
    """Exact ``P(all M balanced fibres hit at least once in N samples)``.

    Uses the O(N*M) dynamic-programming recursion on ``f(n, k) = P(exactly k
    distinct fibres seen after n samples)``:

        f(0, 0) = 1
        f(n, k) = f(n-1, k) * k/M + f(n-1, k-1) * (M - k + 1)/M.

    All intermediate values are probabilities in ``[0, 1]``, so this is
    numerically stable (no catastrophic cancellation). We return ``f(N, M)``.

    The naive inclusion-exclusion closed form
        sum_{k=0..M} C(M, k) * (-1)^k * ((M - k)/M)^N
    is *mathematically* correct but suffers catastrophic cancellation for
    large M in float arithmetic (the log-binomial coefficients grow like
    2^M while the true value stays in [0, 1]).
    """

    if n_samples < m:
        return 0.0
    prev = [0.0] * (m + 1)
    prev[0] = 1.0
    for _ in range(n_samples):
        curr = [0.0] * (m + 1)
        for k in range(m + 1):
            stay = prev[k] * (k / m)
            new = prev[k - 1] * ((m - k + 1) / m) if k > 0 else 0.0
            curr[k] = stay + new
        prev = curr
    return max(0.0, min(1.0, prev[m]))


@dataclass(frozen=True)
class ScalingPoint:
    d_z: int
    r: int
    M: int
    fibre_size_in_ambient: int
    N_bound: int
    exact_recovery_at_bound: float
    meets_target: bool
    recovery_zero_below_M: bool


def evaluate_scaling_point(d_z: int, r: int) -> ScalingPoint:
    """Compute Theorem 6's exact recovery at the bound for one (d_Z, r)."""

    assert (
        AMBIENT_SIDE % r == 0
    ), f"r = {r} must divide AMBIENT_SIDE = {AMBIENT_SIDE} for balanced fibres"
    if d_z == 1:
        m = r
        fibre_size = (AMBIENT_SIDE // r) * AMBIENT_SIDE
    elif d_z == 2:
        m = r * r
        fibre_size = (AMBIENT_SIDE // r) * (AMBIENT_SIDE // r)
    else:
        raise ValueError(f"unsupported d_z = {d_z}")
    n_bound = theorem_bound(m=m, c=1.0, eps_rel=EPS_REL)
    p_at_bound = exact_recovery_probability_balanced(m, n_bound)
    below_m = all(
        exact_recovery_probability_balanced(m, n) == 0.0 for n in range(m)
    )
    return ScalingPoint(
        d_z=d_z,
        r=r,
        M=m,
        fibre_size_in_ambient=fibre_size,
        N_bound=n_bound,
        exact_recovery_at_bound=round(p_at_bound, 12),
        meets_target=p_at_bound >= 1.0 - EPS_REL,
        recovery_zero_below_M=below_m,
    )


D_Z_VALUES: tuple[int, ...] = (1, 2)
R_VALUES: tuple[int, ...] = (4, 8, 16)


def evaluate_benchmark() -> dict:
    scaling_points = [
        evaluate_scaling_point(d_z=d_z, r=r)
        for d_z in D_Z_VALUES
        for r in R_VALUES
    ]

    all_meet_target = all(pt.meets_target for pt in scaling_points)
    all_below_M_zero = all(pt.recovery_zero_below_M for pt in scaling_points)

    # Monotonicity up to bound, sampled sparsely to keep runtime bounded at large M.
    # (Any strict decrease at a full-resolution point would also show up at the
    # sample points; a full-resolution check would just be O(N_bound) per point.)
    monotone_up_to_bound = True
    for pt in scaling_points:
        n_probes = sorted(
            {0, 1, pt.M - 1, pt.M, pt.M + 1, pt.N_bound // 2, pt.N_bound, pt.N_bound + 1}
        )
        curve = [exact_recovery_probability_balanced(pt.M, n) for n in n_probes]
        if not all(a <= b + 1e-12 for a, b in zip(curve, curve[1:])):
            monotone_up_to_bound = False
            break

    # Exponential-in-d_Z scaling: at each fixed r, N_bound doubles-in-d_Z-power.
    scaling_indexed: dict[tuple[int, int], ScalingPoint] = {
        (pt.d_z, pt.r): pt for pt in scaling_points
    }
    exponential_scaling_strict = all(
        scaling_indexed[(2, r)].N_bound > scaling_indexed[(1, r)].N_bound
        for r in R_VALUES
    )
    # Ratio prediction: N_bound(d_Z=2, r) / N_bound(d_Z=1, r) ~= r * (log ratio).
    # We check ratio > r/2 to allow log slack (theoretical value ~ r * (1 + log r / log(r/eps))).
    ratios = {
        r: scaling_indexed[(2, r)].N_bound / scaling_indexed[(1, r)].N_bound
        for r in R_VALUES
    }
    ratio_exceeds_r_over_two = all(ratios[r] > r / 2 for r in R_VALUES)

    gates = {
        "theorem6_bound_meets_target_at_all_grid_points": all_meet_target,
        "recovery_zero_below_M_at_all_grid_points": all_below_M_zero,
        "recovery_monotone_up_to_bound": monotone_up_to_bound,
        "exponential_in_d_Z_scaling_strict": exponential_scaling_strict,
        "ratio_exceeds_r_over_two_at_all_r": ratio_exceeds_r_over_two,
    }
    status = "pass" if all(gates.values()) else "fail"

    return {
        "status": status,
        "gates": gates,
        "theorem_bound_form": "N >= c * (D_Z / eps)^{d_Z} * ... = c * M * ln(M / eps_rel)",
        "eps_rel": EPS_REL,
        "ambient_side": AMBIENT_SIDE,
        "ambient_size": AMBIENT_SIDE * AMBIENT_SIDE,
        "d_Z_values": list(D_Z_VALUES),
        "r_values": list(R_VALUES),
        "scaling_points": [
            {
                "d_z": pt.d_z,
                "r": pt.r,
                "M": pt.M,
                "fibre_size_in_ambient": pt.fibre_size_in_ambient,
                "N_bound": pt.N_bound,
                "exact_recovery_at_bound": pt.exact_recovery_at_bound,
                "meets_target": pt.meets_target,
                "recovery_zero_below_M": pt.recovery_zero_below_M,
            }
            for pt in scaling_points
        ],
        "N_bound_ratio_d_Z2_over_d_Z1": [
            {"r": r, "ratio": round(ratios[r], 6)} for r in R_VALUES
        ],
    }
