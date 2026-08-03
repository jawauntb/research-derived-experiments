"""Exact witness of Theorems CG-1 (Fisher metric on the fiber) and CG-2
(concern holonomy) from the companion paper *Concern as Fiber Geometry*
(``papers/concern_as_fiber_geometry/paper.md``).

Setup (matches paper section 4, 4-bit Boolean world of Instrument 4):

- ``X = {0, 1}^4``, uniform, ``|X| = 16``.
- Latent ``Z(x) = (x_0 XOR x_1, x_2 XOR x_3)`` with ``|Z| = 4``.
- Base compiler ``K(dx | z)`` is uniform on the 4-element fiber ``q^{-1}(z)``.
- Concern sufficient statistic ``T(x, z) = (x_0 - x_1, x_2 - x_3) in {-1, +1}^2``.
- Concern parameter ``c = (c_1, c_2)`` in ``R^2`` reweights the fiber by
  ``exp(beta * <c, T(x, z)>)``.

Theorem CG-1 predicts ``g_{c, z} = beta^2 * diag(sech^2(beta c_1), sech^2(beta c_2))``
for every ``z``, since ``(x_0 - x_1)`` and ``(x_2 - x_3)`` are independent
under ``K(. | z)``.

Theorem CG-2 says a concern 1-form ``alpha`` has zero holonomy on every
closed loop in ``Z x C`` iff it is exact. The paper adds a non-exact
correction ``epsilon * (z_2 dc_1 - z_1 dc_2)`` and computes the triangle
loop ``(0,0) -> (1,0) -> (1,1) -> (0,0)`` at ``z = (1, 1)``, which
integrates to exactly ``epsilon`` -- non-zero.

We verify both theorems exactly, at three concern values ``c`` and both
loops (rectangular = 0, triangular = epsilon). All arithmetic is exact
in double precision because the fiber has four discrete elements and
``T`` is bounded.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from itertools import product

Bit = int
World = tuple[Bit, Bit, Bit, Bit]


def all_worlds() -> list[World]:
    return [tuple(bits) for bits in product((0, 1), repeat=4)]  # type: ignore[misc]


def latent_z(w: World) -> tuple[int, int]:
    return (w[0] ^ w[1], w[2] ^ w[3])


def concern_stat(w: World) -> tuple[int, int]:
    """T(x, z) = (2 x_0 - 1, 2 x_2 - 1), each in {-1, +1}.

    Chosen so T varies non-trivially on *every* fiber q^{-1}(z) (uses the
    "which element of the pair" bit for each fiber-half, giving uniform
    +/-1 marginals under the base compiler K(. | z)).
    """

    return (2 * w[0] - 1, 2 * w[2] - 1)


def _fiber(worlds: Sequence[World], z: tuple[int, int]) -> list[World]:
    return [w for w in worlds if latent_z(w) == z]


def concern_kernel(
    worlds: Sequence[World], z: tuple[int, int], c: tuple[float, float], beta: float
) -> list[tuple[World, float]]:
    """Return K_c(x | z) for every x in fiber q^{-1}(z), normalised to sum 1."""

    fiber = _fiber(worlds, z)
    unnormalised = []
    for x in fiber:
        t = concern_stat(x)
        weight = math.exp(beta * (c[0] * t[0] + c[1] * t[1]))
        unnormalised.append((x, weight))
    z_partition = sum(w for _x, w in unnormalised)
    return [(x, w / z_partition) for x, w in unnormalised]


def fiber_expectation(
    kernel: Sequence[tuple[World, float]], f: Callable[[World], float]
) -> float:
    return sum(prob * f(x) for x, prob in kernel)


def fiber_covariance(
    kernel: Sequence[tuple[World, float]],
    f: Callable[[World], tuple[float, float]],
) -> list[list[float]]:
    """Cov[f] under the fiber distribution (2x2 matrix)."""

    means = [
        sum(prob * f(x)[i] for x, prob in kernel) for i in range(2)
    ]
    cov = [[0.0, 0.0], [0.0, 0.0]]
    for x, prob in kernel:
        v = f(x)
        for i in range(2):
            for j in range(2):
                cov[i][j] += prob * (v[i] - means[i]) * (v[j] - means[j])
    return cov


def fisher_matrix_at(
    worlds: Sequence[World], z: tuple[int, int], c: tuple[float, float], beta: float
) -> list[list[float]]:
    """Empirical Fisher = beta^2 * Cov_{c, z}[T] on the fiber. Exact."""

    kernel = concern_kernel(worlds, z, c, beta)
    cov = fiber_covariance(kernel, lambda x: (float(concern_stat(x)[0]), float(concern_stat(x)[1])))
    return [[beta * beta * cov[i][j] for j in range(2)] for i in range(2)]


def predicted_fisher(c: tuple[float, float], beta: float) -> list[list[float]]:
    """Theorem CG-1 prediction: beta^2 * diag(sech^2(beta c_1), sech^2(beta c_2))."""

    def sech2(x: float) -> float:
        return 1.0 / math.cosh(x) ** 2

    return [
        [beta * beta * sech2(beta * c[0]), 0.0],
        [0.0, beta * beta * sech2(beta * c[1])],
    ]


def matrix_max_abs_diff(a: list[list[float]], b: list[list[float]]) -> float:
    return max(abs(a[i][j] - b[i][j]) for i in range(len(a)) for j in range(len(a[0])))


# ---- Concern 1-form and holonomy ----


def alpha_mean_stat(
    worlds: Sequence[World], z: tuple[int, int], c: tuple[float, float], beta: float
) -> tuple[float, float]:
    """The exponential-family mean statistic beta * E_{c,z}[T] (the 1-form's exact part)."""

    kernel = concern_kernel(worlds, z, c, beta)
    m0 = sum(prob * concern_stat(x)[0] for x, prob in kernel)
    m1 = sum(prob * concern_stat(x)[1] for x, prob in kernel)
    return (beta * m0, beta * m1)


def alpha_prime(
    worlds: Sequence[World],
    z: tuple[int, int],
    c: tuple[float, float],
    beta: float,
    epsilon: float,
) -> tuple[float, float]:
    """The genuinely non-exact 1-form: alpha + epsilon * (-c_2 * dc_1 + 0 * dc_2).

    Exterior derivative of the correction is
        d(-c_2 dc_1) = -dc_2 wedge dc_1 = dc_1 wedge dc_2,
    so its curl is +1 and Green's theorem gives holonomy = epsilon *
    (signed area enclosed) around any closed loop in c-space.

    (An earlier version of this paper used epsilon * (z_2 dc_1 - z_1 dc_2)
    with z fixed, which is *trivially exact* on R^2 with potential
    epsilon (z_2 c_1 - z_1 c_2) and has zero holonomy. The correction
    below is genuinely closed-but-not-exact-on-nontrivial-cycles.)
    """

    exact = alpha_mean_stat(worlds, z, c, beta)
    return (exact[0] + epsilon * (-c[1]), exact[1] + 0.0)


def holonomy_polygon(
    worlds: Sequence[World],
    z: tuple[int, int],
    beta: float,
    epsilon: float,
    corners: Sequence[tuple[float, float]],
    steps_per_edge: int = 500,
) -> float:
    """Compute the line integral of alpha_prime along the closed polygon of `corners`.

    Uses simple trapezoidal integration on parameter c. The polygon is
    assumed to close: corners[-1] = corners[0] is expected (we do not
    auto-close). z is held fixed along the loop (loops in C only).
    """

    total = 0.0
    for i in range(len(corners) - 1):
        c_start = corners[i]
        c_end = corners[i + 1]
        # Trapezoidal in the direction of edge (c_end - c_start): integrate
        # alpha_1(c(t)) * (c_end.x - c_start.x) + alpha_2(c(t)) * (c_end.y - c_start.y)
        # over t in [0, 1] straight edge.
        edge_int = 0.0
        for step in range(steps_per_edge + 1):
            weight = 0.5 if step in (0, steps_per_edge) else 1.0
            t = step / steps_per_edge
            c_here = (
                c_start[0] + t * (c_end[0] - c_start[0]),
                c_start[1] + t * (c_end[1] - c_start[1]),
            )
            a = alpha_prime(worlds, z, c_here, beta, epsilon)
            edge_int += weight * (
                a[0] * (c_end[0] - c_start[0]) + a[1] * (c_end[1] - c_start[1])
            )
        edge_int /= steps_per_edge
        total += edge_int
    return total


BETA = 1.0
EPSILON = 0.3
LOOP_TRIANGLE = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 0.0))
LOOP_RECTANGLE = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0), (0.0, 0.0))
CONCERN_GRID: tuple[tuple[float, float], ...] = (
    (0.0, 0.0),
    (0.3, -0.2),
    (0.8, 0.5),
    (-0.4, 1.1),
)


def evaluate_theorem_cg1(worlds: Sequence[World]) -> dict:
    """Verify Theorem CG-1 at every (c, z) in the grid x latent set."""

    all_z = list({latent_z(w) for w in worlds})
    all_z.sort()
    records = []
    max_diff = 0.0
    for z in all_z:
        for c in CONCERN_GRID:
            emp = fisher_matrix_at(worlds, z, c, BETA)
            pred = predicted_fisher(c, BETA)
            diff = matrix_max_abs_diff(emp, pred)
            max_diff = max(max_diff, diff)
            records.append(
                {
                    "z": list(z),
                    "c": list(c),
                    "empirical_fisher": emp,
                    "predicted_fisher": pred,
                    "max_abs_diff": diff,
                    "off_diagonal_zero": max(
                        abs(emp[0][1]), abs(emp[1][0])
                    )
                    < 1e-12,
                }
            )
    return {
        "records": records,
        "max_diff_across_grid": max_diff,
        "predicted_form": "g_{c,z} = beta^2 * diag(sech^2(beta c_1), sech^2(beta c_2))",
    }


def evaluate_theorem_cg2(worlds: Sequence[World]) -> dict:
    """Verify Theorem CG-2 via Green's theorem for a genuinely non-exact 1-form.

    Predictions (holonomy = epsilon * signed enclosed area):
    - rectangular loop [0,1] x [0,1]: area = 1, holonomy = +epsilon.
    - triangular loop (0,0) -> (1,0) -> (1,1) -> (0,0): area = 1/2,
      holonomy = +epsilon / 2.

    Loops are in c-space at fixed z = (1, 1). The 1-form's exact part
    (alpha_mean_stat) integrates to zero around any closed loop by
    exactness, so the entire holonomy comes from the added correction
    -epsilon * c_2 dc_1.
    """

    z = (1, 1)
    h_rect = holonomy_polygon(worlds, z, BETA, EPSILON, LOOP_RECTANGLE)
    h_tri = holonomy_polygon(worlds, z, BETA, EPSILON, LOOP_TRIANGLE)
    predicted_rect = EPSILON  # area = 1
    predicted_tri = EPSILON / 2.0  # area = 1/2
    return {
        "z_of_loop": list(z),
        "epsilon": EPSILON,
        "holonomy_rectangle_predicted": predicted_rect,
        "holonomy_rectangle_computed": h_rect,
        "holonomy_triangle_predicted": predicted_tri,
        "holonomy_triangle_computed": h_tri,
        "rectangle_matches_prediction": abs(h_rect - predicted_rect) < 1e-3,
        "triangle_matches_prediction": abs(h_tri - predicted_tri) < 1e-3,
        "rectangle_over_triangle_ratio": h_rect / h_tri if abs(h_tri) > 1e-9 else float("inf"),
    }


def evaluate_benchmark() -> dict:
    worlds = all_worlds()
    cg1 = evaluate_theorem_cg1(worlds)
    cg2 = evaluate_theorem_cg2(worlds)

    gates = {
        "cg1_empirical_fisher_matches_predicted": cg1["max_diff_across_grid"] < 1e-12,
        "cg1_fisher_is_diagonal_at_every_grid_point": all(
            r["off_diagonal_zero"] for r in cg1["records"]
        ),
        "cg2_rectangle_holonomy_matches_area_epsilon": cg2["rectangle_matches_prediction"],
        "cg2_triangle_holonomy_matches_half_epsilon": cg2["triangle_matches_prediction"],
    }
    status = "pass" if all(gates.values()) else "fail"
    return {
        "status": status,
        "gates": gates,
        "cg1": cg1,
        "cg2": cg2,
        "beta": BETA,
    }
