"""Exact numerical witness of SIC-A derived in the finite discrete positive-support case.

Companion instrument to `papers/structural_intelligence_foundations/paper.md` and
Lean formalisation
`formal/structural-intelligence-mathlib/StructuralIntelligenceMathlib/SICA_FiniteExistence.lean`.

Setup (4-bit Boolean world of Instrument 4, aligned to the parent paper's
joint-parity latent):

- ``X = {0, 1}^4``, |X| = 16.
- ``Theta = {t_00, t_01, t_10, t_11}`` -- four parameters, one per joint
  parity pair in ``Z/2 x Z/2``.  Each ``t_ij`` describes a task-natural
  pmf that concentrates on the 4-world fibre with joint parity
  ``(parity{0,1}, parity{2,3}) = (i, j)``:

      P_hat(t_ij, x) = 1/4  if (parity{0,1}(x), parity{2,3}(x)) = (i, j),
                     = 0    otherwise.

- Laplace smoothing (``+1/16`` -- the task-spec value): the pre-smoothed
  ``P_hat`` has zero-mass entries, which violate T1's ``0 < P theta x``
  hypothesis.  We add ``+1/16`` uniformly on every world and renormalise:

      P(t_ij, x) = (P_hat(t_ij, x) + 1/16) / 2
                 = 5/32   on the 4 worlds with joint parity (i, j),
                 = 1/32   on the 12 worlds without.

  Every entry is strictly positive (matches T1's `0 < P theta x`
  hypothesis).  Sum per theta: 4 * 5/32 + 12 * 1/32 = 32/32 = 1.

- ``theta_0 := t_00`` (canonical pivot).
- ``q(x)`` = the LR-vector against theta_0
  (``theta |-> P(theta, x) / P(theta_0, x))``, evaluated at all four thetas).
- ``K(z, x)`` = the uniform-on-fibre kernel:
      ``1 / |q^{-1}(z)|`` if ``q(x) = z``, else ``0``.

Under this setup the LR-vector partition equals the **known joint-parity
minimal sufficient statistic** ``(parity{0,1}, parity{2,3})`` bit-exact.
This is the reference MSS used in the parent paper's Instrument 4 and in
`experiments/cross_task_sufficiency/`.

Four pre-registered gates verify the SIC-A construction:

1. **T1 characterisation.**  Two ``x, x'`` satisfy ``q(x) = q(x')`` iff
   for every ``theta, theta'``:
       ``P(theta, x) * P(theta', x') = P(theta, x') * P(theta', x)``.
2. **Fibration structure.**  ``K(z, x) > 0`` iff ``q(x) = z``.
3. **Fibre normalisation.**  ``sum_x K(z, x) = 1`` for every ``z`` in image(q)
   (bit-exact under rational arithmetic).
4. **Agreement with the known minimal sufficient statistic.**  The
   LR-vector-induced partition of X equals the joint-parity partition
   ``x |-> (parity{0,1}(x), parity{2,3}(x))``, bit-exact -- so the
   number of fibres, their sizes, and their elements all match.

Everything is exact.  No sampling, no seeds, no Monte Carlo.  All values
are computed in Python's ``fractions.Fraction`` for bit-exact rational
arithmetic.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from fractions import Fraction
from itertools import product

Bit = int
World = tuple[Bit, Bit, Bit, Bit]
Theta = tuple[int, int]  # (i, j) in Z/2 x Z/2


# ---------------------------------------------------------------------------
# World enumeration and parameter set
# ---------------------------------------------------------------------------


def all_worlds() -> list[World]:
    """The 16-element sample space X = {0, 1}^4."""

    return [(b0, b1, b2, b3) for b0, b1, b2, b3 in product((0, 1), repeat=4)]


def all_thetas() -> list[Theta]:
    """The 4-element parameter set Theta = {(0,0), (0,1), (1,0), (1,1)}."""

    return [(i, j) for i in (0, 1) for j in (0, 1)]


THETA_0: Theta = (0, 0)


# ---------------------------------------------------------------------------
# Joint-parity latent (the known minimal sufficient statistic reference)
# ---------------------------------------------------------------------------


def joint_parity(x: World) -> tuple[int, int]:
    """The joint-parity statistic: ``(parity{0,1}(x), parity{2,3}(x))``.

    For the joint-parity-concentrated task family with pivot ``t_00``,
    this is the known minimal sufficient statistic on ``X`` -- it
    partitions the 16-world cube into 4 fibres of 4 worlds each.
    """

    return (x[0] ^ x[1], x[2] ^ x[3])


# ---------------------------------------------------------------------------
# Task-natural pmf family + Laplace smoothing to positivity
# ---------------------------------------------------------------------------


def _p_hat(theta: Theta, x: World) -> Fraction:
    """Concentrated pmf: mass 1/4 on the 4 worlds sharing theta's joint parity,
    zero elsewhere.  Zero-mass entries violate T1's positivity hypothesis,
    so we Laplace-smooth below."""

    if joint_parity(x) == theta:
        return Fraction(1, 4)
    return Fraction(0)


def p_smoothed(theta: Theta, x: World) -> Fraction:
    """Laplace-smoothed pmf: ``(P_hat + 1/16) / 2`` (task-spec `+1/16` value).

    Per-entry values:
      P(theta, x) = 5/32 if joint_parity(x) = theta,
                    1/32 otherwise.
    Sum: 4 * 5/32 + 12 * 1/32 = 20/32 + 12/32 = 1.  Every entry > 0
    (matches T1's ``0 < P theta x`` hypothesis).
    """

    raw = _p_hat(theta, x) + Fraction(1, 16)
    return raw / Fraction(2)


def p_all(worlds: Sequence[World], thetas: Sequence[Theta]) -> dict[tuple[Theta, World], Fraction]:
    """Precomputed table ``(theta, x) -> P(theta, x)``."""

    return {(theta, x): p_smoothed(theta, x) for theta in thetas for x in worlds}


# ---------------------------------------------------------------------------
# LR-vector statistic (Theorem 1)
# ---------------------------------------------------------------------------


def lr_vector(
    p_table: dict[tuple[Theta, World], Fraction], x: World, thetas: Sequence[Theta]
) -> tuple[Fraction, ...]:
    """LR-vector against theta_0: (P(theta, x) / P(theta_0, x))_theta."""

    denom = p_table[(THETA_0, x)]
    return tuple(p_table[(theta, x)] / denom for theta in thetas)


def build_q(
    worlds: Sequence[World],
    thetas: Sequence[Theta],
    p_table: dict[tuple[Theta, World], Fraction],
) -> dict[World, tuple[Fraction, ...]]:
    """The corestriction of the LR-vector; ``q(x)`` is the LR-vector at x."""

    return {x: lr_vector(p_table, x, thetas) for x in worlds}


def image_of_q(q: dict[World, tuple[Fraction, ...]]) -> list[tuple[Fraction, ...]]:
    """The finite set Z = image(q), ordered by first-appearance for determinism."""

    seen: dict[tuple[Fraction, ...], None] = {}
    for x in q:
        v = q[x]
        if v not in seen:
            seen[v] = None
    return list(seen.keys())


def fibre_of(
    q: dict[World, tuple[Fraction, ...]], z: tuple[Fraction, ...]
) -> list[World]:
    return [x for x, v in q.items() if v == z]


# ---------------------------------------------------------------------------
# Uniform-on-fibre kernel K (Proposition 3 side conditions concrete)
# ---------------------------------------------------------------------------


def uniform_fibre_kernel(
    q: dict[World, tuple[Fraction, ...]], z: tuple[Fraction, ...], x: World
) -> Fraction:
    """K(z, x) = 1/|q^{-1}(z)| if q(x) = z else 0."""

    if q[x] != z:
        return Fraction(0)
    size = len(fibre_of(q, z))
    return Fraction(1, size)


# ---------------------------------------------------------------------------
# Gate 1: T1 characterisation biconditional
# ---------------------------------------------------------------------------


def _cross_multiplication_holds(
    p_table: dict[tuple[Theta, World], Fraction],
    thetas: Sequence[Theta],
    x: World,
    x_prime: World,
) -> bool:
    """Check ``P(theta, x) * P(theta', x') = P(theta, x') * P(theta', x)`` for all pairs."""

    for theta in thetas:
        for theta_prime in thetas:
            lhs = p_table[(theta, x)] * p_table[(theta_prime, x_prime)]
            rhs = p_table[(theta, x_prime)] * p_table[(theta_prime, x)]
            if lhs != rhs:
                return False
    return True


def check_t1_characterisation(
    worlds: Sequence[World],
    thetas: Sequence[Theta],
    q: dict[World, tuple[Fraction, ...]],
    p_table: dict[tuple[Theta, World], Fraction],
) -> dict:
    """Verify: q(x) = q(x') <=> cross-multiplication identity for all theta pairs."""

    disagreements = []
    total_pairs = 0
    matched_pairs = 0
    for x in worlds:
        for x_prime in worlds:
            total_pairs += 1
            q_equal = q[x] == q[x_prime]
            xmult = _cross_multiplication_holds(p_table, thetas, x, x_prime)
            if q_equal != xmult:
                disagreements.append(
                    {"x": list(x), "x_prime": list(x_prime), "q_equal": q_equal, "cross_mult": xmult}
                )
            else:
                matched_pairs += 1
    return {
        "total_pairs": total_pairs,
        "matched_pairs": matched_pairs,
        "disagreements": disagreements,
        "biconditional_holds": len(disagreements) == 0,
    }


# ---------------------------------------------------------------------------
# Gate 2: Fibration structure
# ---------------------------------------------------------------------------


def check_fibration_structure(
    worlds: Sequence[World],
    q: dict[World, tuple[Fraction, ...]],
    Z: Sequence[tuple[Fraction, ...]],
) -> dict:
    """Verify: K(z, x) > 0  iff  q(x) = z, for every (z, x)."""

    disagreements = []
    for z_idx, z in enumerate(Z):
        for x in worlds:
            k_val = uniform_fibre_kernel(q, z, x)
            k_positive = k_val > 0
            q_equal = q[x] == z
            if k_positive != q_equal:
                disagreements.append(
                    {"z_index": z_idx, "x": list(x), "k_positive": k_positive, "q_equal": q_equal}
                )
    return {
        "n_pairs_checked": len(worlds) * len(Z),
        "disagreements": disagreements,
        "biconditional_holds": len(disagreements) == 0,
    }


# ---------------------------------------------------------------------------
# Gate 3: Fibre normalisation
# ---------------------------------------------------------------------------


def check_fibre_normalisation(
    worlds: Sequence[World],
    q: dict[World, tuple[Fraction, ...]],
    Z: Sequence[tuple[Fraction, ...]],
) -> dict:
    """Verify: sum_x K(z, x) = 1 for every z in Z."""

    per_z = []
    all_pass = True
    for z_idx, z in enumerate(Z):
        total = sum((uniform_fibre_kernel(q, z, x) for x in worlds), Fraction(0))
        matches_one = total == Fraction(1)
        if not matches_one:
            all_pass = False
        per_z.append(
            {
                "z_index": z_idx,
                "fibre_size": len(fibre_of(q, z)),
                "sum_K": float(total),
                "sum_K_equals_one": matches_one,
            }
        )
    return {
        "n_z_checked": len(Z),
        "per_z": per_z,
        "all_z_sum_to_one": all_pass,
    }


# ---------------------------------------------------------------------------
# Gate 4: Agreement with the known joint-parity minimal sufficient statistic
# ---------------------------------------------------------------------------


def _partition_of(
    worlds: Sequence[World], stat: Mapping[World, object]
) -> list[frozenset[World]]:
    """Return the fibre partition of a statistic (as a sorted list of frozensets)."""

    cells: dict[object, list[World]] = {}
    for x in worlds:
        cells.setdefault(stat[x], []).append(x)
    return sorted(
        (frozenset(cell) for cell in cells.values()),
        key=lambda s: tuple(sorted(s)),
    )


def known_joint_parity_partition(worlds: Sequence[World]) -> list[frozenset[World]]:
    """Reference MSS partition: joint(parity{0,1}, parity{2,3}) fibres.

    For the joint-parity-concentrated task family with pivot ``t_00``,
    this is the known minimal sufficient statistic on X.  It partitions
    the 16-world cube into 4 fibres of 4 worlds each.
    """

    stat: dict[World, object] = {x: joint_parity(x) for x in worlds}
    return _partition_of(worlds, stat)


def check_partition_agreement(
    worlds: Sequence[World], q: dict[World, tuple[Fraction, ...]]
) -> dict:
    """Compare the LR-vector partition to the reference joint-parity partition, bit-exact."""

    part_q = _partition_of(worlds, q)
    part_ref = known_joint_parity_partition(worlds)
    return {
        "n_cells_q": len(part_q),
        "n_cells_reference": len(part_ref),
        "cell_sizes_q": sorted(len(cell) for cell in part_q),
        "cell_sizes_reference": sorted(len(cell) for cell in part_ref),
        "partitions_equal": part_q == part_ref,
    }


# ---------------------------------------------------------------------------
# Top-level benchmark
# ---------------------------------------------------------------------------


def evaluate_benchmark() -> dict:
    worlds = all_worlds()
    thetas = all_thetas()
    p_table = p_all(worlds, thetas)
    q = build_q(worlds, thetas, p_table)
    Z = image_of_q(q)

    t1 = check_t1_characterisation(worlds, thetas, q, p_table)
    fibration = check_fibration_structure(worlds, q, Z)
    normalisation = check_fibre_normalisation(worlds, q, Z)
    agreement = check_partition_agreement(worlds, q)

    gates = {
        "t1_characterisation_biconditional": t1["biconditional_holds"],
        "fibration_structure_biconditional": fibration["biconditional_holds"],
        "fibre_normalisation_sums_to_one": normalisation["all_z_sum_to_one"],
        "lr_partition_equals_joint_parity_mss": agreement["partitions_equal"],
    }
    status = "pass" if all(gates.values()) else "fail"
    return {
        "status": status,
        "gates": gates,
        "world_size": len(worlds),
        "n_theta": len(thetas),
        "n_fibres": len(Z),
        "fibre_sizes": sorted(len(fibre_of(q, z)) for z in Z),
        "t1_characterisation": {
            "total_pairs": t1["total_pairs"],
            "matched_pairs": t1["matched_pairs"],
            "n_disagreements": len(t1["disagreements"]),
        },
        "fibration_structure": {
            "n_pairs_checked": fibration["n_pairs_checked"],
            "n_disagreements": len(fibration["disagreements"]),
        },
        "fibre_normalisation": {
            "n_z_checked": normalisation["n_z_checked"],
            "per_z": normalisation["per_z"],
        },
        "partition_agreement": agreement,
    }
