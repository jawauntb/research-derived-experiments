"""Exact witness of Theorems AG-1 (Viability under a bounded transition
kernel) and AG-2 (Viability preserved under coarser V) from the companion
paper *Alignment as Ensemble Governance*
(``papers/alignment_as_ensemble_governance/paper.md``).

Setup (matches paper section 5, 4-state Markov chain):

- ``Z`` = {0, 1, 2, 3}; ``V`` = {0, 1, 2}; unviable = {3}.
- ``A`` = {"stay", "move"}.
- From ``z in V``:
    * ``stay``: ``T(z | z, stay) = 1 - beta``, ``T(3 | z, stay) = beta``.
    * ``move``: cycles among V (0 -> 1 -> 2 -> 0) with probability
      ``1 - beta``, leaks to ``3`` with probability ``beta``.
- From ``z = 3``: absorbing (``T(3 | 3, a) = 1``).
- Policy pi: uniform random over ``A`` at every ``z in V``.
- Leakage rate ``beta = 0.05``.

Induced coarse Markov kernel on Z under pi:

    ---     ->  0       1       2       3
    from 0  [ 0.475,  0.475,  0.000,  0.050 ]
    from 1  [ 0.000,  0.475,  0.475,  0.050 ]
    from 2  [ 0.475,  0.000,  0.475,  0.050 ]
    from 3  [ 0.000,  0.000,  0.000,  1.000 ]

Because "3" is absorbing, the survival probability
``Pr[q(X_t) in V for all t <= T]`` is exactly the row-sum of the T-th
power of the sub-matrix P_V restricted to V. By construction, every row
of P_V sums to ``1 - beta = 0.95``, and every row of ``P_V^T`` sums to
``(1 - beta)^T``. Theorem AG-1's lower bound is therefore tight for this
world at every T.

AG-2 is verified by extending V to V' = Z (everything viable): survival
is trivially 1.0 at every T.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import cast

# ---------- Fixed world parameters (matches paper section 5) ----------

Z_STATES: tuple[int, ...] = (0, 1, 2, 3)
V_STATES: tuple[int, ...] = (0, 1, 2)
UNVIABLE_STATES: tuple[int, ...] = (3,)
ACTIONS: tuple[str, ...] = ("stay", "move")
BETA: float = 0.05
T_HORIZONS: tuple[int, ...] = (1, 3, 5, 10, 20)
NUMERIC_TOLERANCE: float = 1e-12


# ---------- Kernel construction ----------


def _stay_row(z: int, beta: float) -> dict[int, float]:
    """T(. | z, stay): stay at z w.p. 1-beta, leak to 3 w.p. beta."""

    if z == 3:
        return {3: 1.0}
    return {z: 1.0 - beta, 3: beta}


def _move_row(z: int, beta: float) -> dict[int, float]:
    """T(. | z, move): cycle among V w.p. 1-beta, leak to 3 w.p. beta."""

    if z == 3:
        return {3: 1.0}
    next_z = (z + 1) % 3  # cycle 0 -> 1 -> 2 -> 0 within V
    return {next_z: 1.0 - beta, 3: beta}


def action_kernel(z: int, action: str, beta: float = BETA) -> dict[int, float]:
    """T(. | z, a) as a mapping z' -> probability. Zero-entries omitted."""

    if action == "stay":
        return _stay_row(z, beta)
    if action == "move":
        return _move_row(z, beta)
    raise ValueError(f"unknown action: {action}")


def uniform_policy_kernel(beta: float = BETA) -> list[list[float]]:
    """Return the 4x4 transition matrix ``P[i][j] = T_pi(j | i)`` under
    the uniform-random policy on Z_STATES. Row/column order = Z_STATES."""

    n = len(Z_STATES)
    matrix = [[0.0] * n for _ in range(n)]
    for i, z in enumerate(Z_STATES):
        for action in ACTIONS:
            row = action_kernel(z, action, beta=beta)
            weight = 1.0 / len(ACTIONS)
            for z_next, p in row.items():
                j = Z_STATES.index(z_next)
                matrix[i][j] += weight * p
    return matrix


# ---------- Matrix arithmetic (pure Python, tiny sizes) ----------


def _matmul(
    a: Sequence[Sequence[float]], b: Sequence[Sequence[float]]
) -> list[list[float]]:
    n = len(a)
    m = len(b[0])
    k = len(b)
    return [
        [sum(a[i][t] * b[t][j] for t in range(k)) for j in range(m)] for i in range(n)
    ]


def _matrix_power(a: Sequence[Sequence[float]], t: int) -> list[list[float]]:
    """Non-negative integer power of a square matrix a. Base case a^0 = I."""

    if t < 0:
        raise ValueError("matrix_power requires t >= 0")
    n = len(a)
    if t == 0:
        return [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    if t == 1:
        return [list(row) for row in a]
    half = _matrix_power(a, t // 2)
    squared = _matmul(half, half)
    if t % 2 == 0:
        return squared
    return _matmul(squared, a)


def submatrix_on(
    matrix: Sequence[Sequence[float]], keep_states: Sequence[int]
) -> list[list[float]]:
    """Return the submatrix of ``matrix`` indexed by the given Z-state values.

    Indexing follows Z_STATES; ``keep_states`` must be a subset of Z_STATES.
    """

    idxs = [Z_STATES.index(z) for z in keep_states]
    return [[matrix[i][j] for j in idxs] for i in idxs]


# ---------- Survival probability ----------


def survival_probability(
    matrix: Sequence[Sequence[float]],
    viable: Sequence[int],
    t: int,
    start_state: int | None = None,
) -> float:
    """Exact ``Pr[q(X_s) in viable for all s in {1..t}]`` under kernel matrix.

    Restricts to the sub-kernel on ``viable`` (unviable states are absorbing
    in the paper's construction, so trajectories staying in ``viable`` never
    visit unviable states). If ``start_state`` is None, average over a
    uniform initial distribution on ``viable``.
    """

    sub = submatrix_on(matrix, viable)
    powered = _matrix_power(sub, t)
    if start_state is None:
        n = len(viable)
        return sum(sum(row) for row in powered) / n
    if start_state not in viable:
        return 0.0
    i = list(viable).index(start_state)
    return sum(powered[i])


def theorem_lower_bound(t: int, beta: float = BETA) -> float:
    """Theorem AG-1's lower bound (1 - beta)^t."""

    return (1.0 - beta) ** t


def bernoulli_linear_bound(t: int, beta: float = BETA) -> float:
    """The second (looser) lower bound 1 - t*beta from AG-1's Bernoulli step."""

    return 1.0 - t * beta


# ---------- Gate helpers ----------


def survival_sweep(
    matrix: Sequence[Sequence[float]],
    viable: Sequence[int],
    horizons: Sequence[int] = T_HORIZONS,
    beta: float = BETA,
) -> list[dict[str, object]]:
    """Per-horizon survival records for gate evaluation."""

    records: list[dict[str, object]] = []
    for t in horizons:
        exact = survival_probability(matrix, viable, t)
        bound = theorem_lower_bound(t, beta=beta)
        linear = bernoulli_linear_bound(t, beta=beta)
        records.append(
            {
                "T": t,
                "exact_survival": exact,
                "ag1_lower_bound": bound,
                "bernoulli_linear_bound": linear,
                "bound_holds": exact + NUMERIC_TOLERANCE >= bound,
                "tightness_gap": exact - bound,
            }
        )
    return records


def _tight_at_t1(records: Sequence[dict[str, object]], beta: float = BETA) -> bool:
    for record in records:
        if record["T"] == 1:
            exact = float(cast(float, record["exact_survival"]))
            return abs(exact - (1.0 - beta)) <= NUMERIC_TOLERANCE
    return False


def _monotone_decreasing(records: Sequence[dict[str, object]]) -> bool:
    values = [float(cast(float, r["exact_survival"])) for r in records]
    return all(
        values[i] >= values[i + 1] - NUMERIC_TOLERANCE for i in range(len(values) - 1)
    )


def evaluate_benchmark() -> dict:
    matrix = uniform_policy_kernel(beta=BETA)

    v_records = survival_sweep(matrix, V_STATES, horizons=T_HORIZONS, beta=BETA)
    v_prime_records = survival_sweep(matrix, Z_STATES, horizons=T_HORIZONS, beta=BETA)

    ag1_bound_holds_at_every_T = all(bool(r["bound_holds"]) for r in v_records)
    ag1_tightness_at_t1 = _tight_at_t1(v_records, beta=BETA)
    ag2_viability_inherited = all(
        abs(float(cast(float, r["exact_survival"])) - 1.0) <= NUMERIC_TOLERANCE
        for r in v_prime_records
    )
    monotone_in_t = _monotone_decreasing(v_records)

    gates = {
        "ag1_lower_bound_holds_at_every_T": ag1_bound_holds_at_every_T,
        "ag1_lower_bound_tightness": ag1_tightness_at_t1,
        "ag2_viability_inherited_by_superset": ag2_viability_inherited,
        "ag_survival_monotone_decreasing_in_T": monotone_in_t,
    }
    status = "pass" if all(gates.values()) else "fail"
    return {
        "status": status,
        "gates": gates,
        "world": {
            "Z_states": list(Z_STATES),
            "V_states": list(V_STATES),
            "unviable_states": list(UNVIABLE_STATES),
            "actions": list(ACTIONS),
            "beta": BETA,
            "policy": "uniform random over actions on V",
            "horizons": list(T_HORIZONS),
        },
        "coarse_kernel_under_pi": matrix,
        "records_on_V": v_records,
        "records_on_V_prime_equals_Z": v_prime_records,
    }
