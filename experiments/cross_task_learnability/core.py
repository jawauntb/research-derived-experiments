"""Exact witness of Theorem 5 (discrete learnability of the master fibration).

Theorem 5 (paper.md §2.5) says: given a task family that separates the true
partition ``q : X -> Z`` (|Z| = M), a distribution on X with min-fibre mass
``p_min >= 1/(cM)``, and empirical common-sufficient clustering, the recovered
``q_hat`` equals ``q`` with probability at least ``1 - eps`` from
``N >= c * M * ln(M / eps)`` i.i.d. samples of X.

This module computes the *exact* recovery probability
``P(all M fibres hit at least once in N i.i.d. samples)`` via inclusion-
exclusion, and pre-registers four gates that verify Theorem 5's discrete
prediction on the shared-through-Z task family of Instrument 4:

Setup.
------
- ``X = {0, 1}^4`` (16 worlds).
- Latent ``Z(x) = (parity{0,1}(x), parity{2,3}(x))``, so ``|Z| = M = 4``.
- Task family from Instrument 4 (shared through Z) separates Z (verified).
- Two distributions:
  - ``uniform``: ``p_min = 1/M = 0.25`` (balanced, ``c = 1``).
  - ``skewed``: mass distribution ``(0.625, 0.125, 0.125, 0.125)`` on fibres,
    ``p_min = 0.125 = 1/(2M)`` (``c = 2``).

Because tasks are deterministic and separating, the *only* random event
mediating recovery is whether every fibre of ``q`` gets at least one sample:
this is a coupon-collector question on the fibre partition, and its
distribution is a pure combinatorial fact of the fibre masses -- computable
exactly.

Gates.
------
- ``exact_recovery_at_theorem_bound_shared_uniform``: at ``N`` equal to the
  smallest integer ``>= c * M * ln(M / eps)`` with ``c = 1``, ``M = 4``,
  ``eps = 0.05``, the exact recovery probability is at least ``1 - eps``.
- ``exact_recovery_at_theorem_bound_shared_skewed``: same for the skewed
  distribution with ``c = 2``.
- ``recovery_zero_below_M``: ``P(recover) = 0`` for every ``N < M``
  (pigeonhole).
- ``recovery_monotone_in_N``: the exact recovery curve is nondecreasing in
  ``N`` up to the theorem bound.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from itertools import combinations, product

World = tuple[int, ...]


def all_worlds(n_bits: int) -> list[World]:
    return [tuple(bits) for bits in product((0, 1), repeat=n_bits)]


def latent_z(world: World) -> tuple[int, int]:
    """Instrument-4 latent: Z(x) = (parity{0,1}, parity{2,3})."""
    return (world[0] ^ world[1], world[2] ^ world[3])


def fibre_masses(
    worlds: Sequence[World], distribution: str
) -> tuple[tuple[tuple[int, int], float], ...]:
    """Return an ordered ``(z, P_X(fibre_z))`` for each latent class ``z``.

    ``uniform`` puts equal mass on each world; ``skewed`` puts extra mass on
    the ``z = (0, 0)`` fibre so that ``p_min = 1/8`` (i.e. ``c = 2``).
    """

    classes: dict[tuple[int, int], list[World]] = {}
    for w in worlds:
        classes.setdefault(latent_z(w), []).append(w)

    if distribution == "uniform":
        weights = {z: 1.0 / len(worlds) for z in worlds}
    elif distribution == "skewed":
        # Total mass on the (0,0) fibre = 0.625; others each 0.125.
        target = {(0, 0): 0.625, (0, 1): 0.125, (1, 0): 0.125, (1, 1): 0.125}
        weights = {}
        for z, members in classes.items():
            per_world = target[z] / len(members)
            for w in members:
                weights[w] = per_world
    else:
        raise ValueError(f"unknown distribution: {distribution!r}")

    fibre_probability: dict[tuple[int, int], float] = {}
    for z, members in classes.items():
        fibre_probability[z] = sum(weights[w] for w in members)

    return tuple(sorted(fibre_probability.items()))


def exact_recovery_probability(masses: Sequence[float], n_samples: int) -> float:
    """Exact ``P(all fibres hit at least once in n_samples)`` by inclusion-exclusion.

    For masses ``p_1, ..., p_M`` summing to 1,

        P(all hit) = sum over subsets S of [M] of (-1)^|S| * (1 - sum_{i in S} p_i)^N,

    which is exact and evaluates in ``O(2^M * M)`` time (M is small).
    """

    m = len(masses)
    if n_samples < m:
        # Pigeonhole: cannot hit M fibres with fewer than M samples.
        return 0.0
    total = 0.0
    for size in range(m + 1):
        for subset in combinations(range(m), size):
            excluded_mass = sum(masses[i] for i in subset)
            remaining = 1.0 - excluded_mass
            if remaining <= 0.0:
                term = 0.0 if n_samples > 0 else 1.0
            else:
                term = remaining**n_samples
            sign = 1 if size % 2 == 0 else -1
            total += sign * term
    return max(0.0, min(1.0, total))


def theorem_bound(m: int, c: float, eps: float) -> int:
    """Theorem 5's sufficient sample count: smallest integer >= c * M * ln(M / eps)."""

    return math.ceil(c * m * math.log(m / eps))


@dataclass(frozen=True)
class RecoveryPoint:
    n_samples: int
    p_recover: float


def recovery_curve(
    masses: Sequence[float], n_max: int
) -> tuple[RecoveryPoint, ...]:
    """Exact recovery curve for ``n = 0 .. n_max`` on this fibre partition."""

    return tuple(
        RecoveryPoint(n_samples=n, p_recover=exact_recovery_probability(masses, n))
        for n in range(n_max + 1)
    )


EPS = 0.05
N_BITS = 4
M = 4


def evaluate_distribution(
    distribution: str, c: float
) -> dict:
    worlds = all_worlds(N_BITS)
    entries = fibre_masses(worlds, distribution)
    masses = tuple(mass for _z, mass in entries)
    assert abs(sum(masses) - 1.0) < 1e-12
    p_min = min(masses)
    inferred_c = 1.0 / (M * p_min)
    assert (
        abs(inferred_c - c) < 1e-9
    ), f"c mismatch for {distribution}: expected {c}, got {inferred_c}"

    n_bound = theorem_bound(m=M, c=c, eps=EPS)
    p_at_bound = exact_recovery_probability(masses, n_bound)
    curve = recovery_curve(masses, n_max=n_bound + 5)

    # Monotonicity check up to the theorem bound.
    curve_probs = [pt.p_recover for pt in curve if pt.n_samples <= n_bound]
    monotone = all(a <= b + 1e-12 for a, b in zip(curve_probs, curve_probs[1:]))

    # Below-M pigeonhole.
    below_m_zero = all(
        pt.p_recover == 0.0 for pt in curve if pt.n_samples < M
    )

    return {
        "distribution": distribution,
        "fibre_mass_distribution": [
            {"z": list(z), "mass": mass} for z, mass in entries
        ],
        "p_min": p_min,
        "c_from_p_min": inferred_c,
        "M": M,
        "eps": EPS,
        "theorem_bound_N": n_bound,
        "exact_recovery_at_theorem_bound": p_at_bound,
        "exact_recovery_meets_target": p_at_bound >= 1.0 - EPS,
        "monotone_up_to_bound": monotone,
        "recovery_zero_below_M": below_m_zero,
        "curve": [
            {"n_samples": pt.n_samples, "p_recover": round(pt.p_recover, 12)}
            for pt in curve
        ],
    }


def evaluate_benchmark() -> dict:
    uniform = evaluate_distribution("uniform", c=1.0)
    skewed = evaluate_distribution("skewed", c=2.0)

    gates = {
        "exact_recovery_at_theorem_bound_shared_uniform": uniform[
            "exact_recovery_meets_target"
        ],
        "exact_recovery_at_theorem_bound_shared_skewed": skewed[
            "exact_recovery_meets_target"
        ],
        "recovery_zero_below_M": uniform["recovery_zero_below_M"]
        and skewed["recovery_zero_below_M"],
        "recovery_monotone_in_N": uniform["monotone_up_to_bound"]
        and skewed["monotone_up_to_bound"],
    }
    status = "pass" if all(gates.values()) else "fail"
    return {
        "status": status,
        "gates": gates,
        "theorem_bound_form": "N >= c * M * ln(M / eps)",
        "eps": EPS,
        "M": M,
        "distributions": [uniform, skewed],
    }
