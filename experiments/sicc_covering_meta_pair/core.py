"""Numerical witness of the SIC-C-c covering meta-theorem
(``papers/structural_intelligence_covering_learnability/paper.md``).

The meta-theorem says: for any inductive-bias hypothesis class ``H`` with
epsilon-covering number ``N(eps, H) <= K``, the sample complexity to
recover the minimally sufficient fibration ``q`` on the finite eps-cover
at confidence ``1 - delta`` is bounded by

    n  >=  c * K * log(K / delta),

for some constant ``c >= 1`` (Lean-verified as
``StructuralIntelligenceMathlib.sicc_covering_meta`` and
``sicc_covering_poly``).

**What the instrument tests.**  We instantiate the meta-theorem on a
*controlled continuous space*: a 2-D Gaussian world with a rotational
latent angle ``theta in [0, 2*pi)``, quantised at resolution
``2*pi / K``.  The eps-cover of the latent angle is exactly ``K`` bins,
and "recovery on the eps-cover" is the classical coupon-collector event
"every one of the ``K`` cells has been observed at least once" -- which
is exactly the mechanism the Theorem-5 union-bound step turns into the
``N >= c * M * log(M/eps)`` rate.

For each ``K`` in the sweep we compute:

- ``n_emp(K, delta)`` = smallest ``N`` such that the exact recovery
  probability (inclusion-exclusion coupon-collector) is at least
  ``1 - delta``.
- ``c_fitted(K) = n_emp(K, delta) / (K * log(K / delta))``.

**Gate (the sharp meta-theorem test).**  The fitted constant
``c_fitted(K)`` should be *stable* across ``K``: the meta-theorem
predicts ``n = c * K * log(K/delta)`` with a *single* class-independent
``c`` for the entire scaling family, so if ``c_fitted(K)`` drifts by
more than ``STABILITY_TOL_PCT = 20%`` between the smallest and largest
``K``, the meta-theorem's constant is not merely loose -- it has the
wrong ``K``-dependence, and the composition (Theorem 6 * Theorem 5-rate)
would be *empirically* wrong for this controlled instance.

Both the empirical curve and the meta-theorem's fitted constant are
exact in double precision (inclusion-exclusion is a finite sum), so no
Monte Carlo noise: the gate either holds or fails exactly.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass


BASE_SEED = 0
K_VALUES: tuple[int, ...] = (8, 16, 32, 64, 128, 256)
DELTA = 0.05
STABILITY_TOL_PCT = 0.20


def exact_recovery_probability(K: int, N: int) -> float:
    """Exact ``P(all K eps-cover cells hit at least once in N uniform iid samples)``.

    Standard inclusion-exclusion on the coupon-collector event:

        P(all hit)  =  sum_{s = 0}^{K}  (-1)^s * C(K, s) * ((K - s) / K)^N.

    This is the "each cell of the eps-cover is empirically instantiated at
    least once" event -- exactly the mechanism behind the Theorem-5 union
    bound that the meta-theorem invokes on the finite K-sized cover.
    Below the pigeonhole floor ``N < K`` the probability is trivially
    zero.
    """

    if N < K:
        return 0.0
    total = 0.0
    for s in range(K + 1):
        remaining = (K - s) / K
        # C(K, s) can be huge, but the alternating (1 - s/K)^N terms cancel
        # to a value in [0, 1]; math.comb + float arithmetic is stable at
        # our sweep range (K <= 256).
        term = math.comb(K, s) * (remaining**N)
        if s % 2 == 0:
            total += term
        else:
            total -= term
    return max(0.0, min(1.0, total))


def smallest_N_for_recovery(K: int, delta: float) -> int:
    """Smallest ``N`` with ``P(recovery on the K-cover) >= 1 - delta``.

    Uses expanding-window followed by binary search.  ``P(recovery)`` is
    nondecreasing in ``N`` (coupling: extra samples never uncollect a
    cell), so binary search is well-defined.
    """

    target = 1.0 - delta
    # Expected coupon-collector wait is ``K * H_K``; the concentration
    # bound gives roughly ``K * log(K/delta)``.  Start the upper bracket
    # at 4x this and double until we clear the target.
    hi = max(K, 4 * int(math.ceil(K * math.log(K / delta))))
    while exact_recovery_probability(K, hi) < target:
        hi *= 2
    lo = K
    while lo < hi:
        mid = (lo + hi) // 2
        if exact_recovery_probability(K, mid) >= target:
            hi = mid
        else:
            lo = mid + 1
    return lo


def meta_theorem_bound_at_c(K: int, delta: float, c: float) -> float:
    """The meta-theorem's ``c * K * log(K / delta)`` bound."""

    return c * K * math.log(K / delta)


@dataclass(frozen=True)
class KRow:
    K: int
    n_emp: int
    meta_bound_at_c1: float
    c_fitted: float
    p_recover_at_n_emp: float
    p_recover_at_n_emp_minus_one: float


def sweep_row(K: int, delta: float = DELTA) -> KRow:
    n_emp = smallest_N_for_recovery(K, delta)
    bound_c1 = meta_theorem_bound_at_c(K, delta, c=1.0)
    c_fitted = n_emp / bound_c1
    return KRow(
        K=K,
        n_emp=n_emp,
        meta_bound_at_c1=bound_c1,
        c_fitted=c_fitted,
        p_recover_at_n_emp=exact_recovery_probability(K, n_emp),
        p_recover_at_n_emp_minus_one=(
            exact_recovery_probability(K, n_emp - 1) if n_emp > 0 else 0.0
        ),
    )


def evaluate_benchmark() -> dict:
    rows: list[KRow] = [sweep_row(K, DELTA) for K in K_VALUES]

    c_values = [row.c_fitted for row in rows]
    c_min = min(c_values)
    c_max = max(c_values)
    c_mean = sum(c_values) / len(c_values)
    stability_span = (c_max - c_min) / c_mean

    # Sanity checks on the exact recovery curve.
    all_meet_target = all(row.p_recover_at_n_emp >= 1.0 - DELTA - 1e-12 for row in rows)
    all_tight = all(
        row.p_recover_at_n_emp_minus_one < 1.0 - DELTA for row in rows
    )
    # n_emp must be at least K (pigeonhole).
    all_above_pigeonhole = all(row.n_emp >= row.K for row in rows)

    gates = {
        "sicc_meta_fitted_c_stable_across_K": stability_span <= STABILITY_TOL_PCT,
        "sicc_meta_empirical_meets_target": all_meet_target,
        "sicc_meta_empirical_is_tight_by_one_sample": all_tight,
        "sicc_meta_above_pigeonhole_floor": all_above_pigeonhole,
    }
    status = "pass" if all(gates.values()) else "fail"

    return {
        "status": status,
        "gates": gates,
        "delta": DELTA,
        "stability_tol_pct": STABILITY_TOL_PCT,
        "K_values": list(K_VALUES),
        "c_fitted": {
            "min": c_min,
            "max": c_max,
            "mean": c_mean,
            "span_over_mean": stability_span,
        },
        "meta_theorem_form": "n >= c * K * log(K / delta)",
        "rows": [
            {
                "K": row.K,
                "n_emp": row.n_emp,
                "meta_bound_at_c1": row.meta_bound_at_c1,
                "c_fitted": row.c_fitted,
                "p_recover_at_n_emp": row.p_recover_at_n_emp,
                "p_recover_at_n_emp_minus_one": row.p_recover_at_n_emp_minus_one,
            }
            for row in rows
        ],
    }
