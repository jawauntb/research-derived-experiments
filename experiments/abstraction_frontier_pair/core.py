"""Exact witness of Theorems AF-1 and AF-2 (Abstraction frontier) from
*The Abstraction Frontier* (``papers/abstraction_frontier/paper.md``).

Setup
-----

The 4-bit Boolean world of Instrument 4:

- ``X = {0, 1}^4`` (16 worlds, uniform base distribution).
- Latent ``Z(x) = (parity{0,1}(x), parity{2,3}(x))`` with ``|image(Z)| = 4``.
- Shared-through-``Z`` task family from Instrument 4:

  * ``Y_1 = parity{0,1}``
  * ``Y_2 = parity{2,3}``
  * ``Y_3 = parity{0,1,2,3} = Y_1 XOR Y_2``

Each ``Y_alpha`` factors through ``Z``, so ``Z`` is a common sufficient
statistic (CSS) for the family and ``max_alpha H(Y_alpha | Z(X)) = 0``.

Quotient lattice
----------------

The same lattice as ``experiments/cross_task_sufficiency``:

- ``constant`` (image size 1, coding cost 0 bits).
- All 15 subset parities ``parity{S}`` for ``S`` in the non-empty
  subsets of ``{0, 1, 2, 3}`` (image size 2, coding cost 1 bit).
- Three joint pair-parities (image size 4, coding cost 2 bits) --
  ``joint(parity{0,1}, parity{2,3})`` is the true ``Z``; the two others
  are non-``Z`` pair-parity partitions.
- Two joint bit-reads at image size 4 (coding cost 2 bits) --
  ``joint(bit_0, bit_1)``, ``joint(bit_2, bit_3)``.
- One joint of three bits ``joint(bit_0, bit_1, bit_2)`` at image size 8
  (coding cost 3 bits).
- ``identity`` (image size 16, coding cost 4 bits).

That is 23 candidate quotients in total.

Four Pareto axes (lower = better on all)
----------------------------------------

- **task_sufficiency** := ``max_alpha H(Y_alpha | q(X))`` in bits under
  the uniform distribution. For deterministic ``Y_alpha = f_alpha(X)``,
  ``I(Y_alpha; X | q(X)) = H(Y_alpha | q(X))``, so this axis is the
  extended-program's ``I(Y; X | q(X))``.
- **coding_cost** := ``log2(|image(q)|)`` in bits.
- **dynamical_closure** := 0 by convention -- this static example has
  no dynamics ``(Z_{t+1}, A_t)`` to marginalise, so
  ``I(Z_{t+1}; X_t | Z_t, A_t)`` is not defined; we set it to 0
  uniformly across quotients so it contributes no dominance information.
  This is documented in the README.
- **control_regret** := 0 by convention -- no controller is being
  simulated; identical remark applies. See README.

The two zero axes collapse the effective Pareto analysis to
``(task_sufficiency, coding_cost)``. The Pareto frontier is
computed on all four axes for future compatibility, but the
static example only ever separates quotients on the first two.

Pareto notion
-------------

Standard Pareto: ``q'`` weakly dominates ``q`` iff ``q'`` is weakly
better on every axis and strictly better on at least one. The frontier
is the set of quotients that no other quotient in the lattice dominates.

Predictions (pre-registered)
----------------------------

- ``af1_frontier_is_antichain``: no two Pareto members dominate each
  other (holds by construction).
- ``af1_frontier_contains_true_Z``: the true ``Z``-partition is on the
  Pareto frontier.
- ``af1_frontier_contains_constant``: the constant map is on the Pareto
  frontier as the min-``coding_cost`` endpoint.
- ``af1_identity_is_dominated_in_static_case``: in this static setup
  the identity is strictly dominated by ``Z`` (same task-sufficiency,
  strictly higher coding cost) -- the direct observation Theorem AF-2's
  "static-case collapse" corollary predicts.
- ``af2_sufficient_frontier_is_true_Z_alone``: among Pareto members the
  only one with ``task_sufficiency = 0`` is the CSS ``Z``.
- ``af2_no_pareto_strictly_finer_than_true_Z``: every Pareto member is
  either equal to ``Z`` or strictly coarser than ``Z`` on the lattice
  (the "at least as fine as ``q*``" side of AF-2 collapses to
  ``= q*`` in the static case).
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from itertools import combinations, product

World = tuple[int, ...]
Label = int

N_BITS = 4


# ---------- Worlds, quotients, tasks ----------


def all_worlds(n_bits: int = N_BITS) -> list[World]:
    return [tuple(bits) for bits in product((0, 1), repeat=n_bits)]


@dataclass(frozen=True)
class Quotient:
    """A candidate coarse-graining ``q : World -> hashable-cell``."""

    name: str
    fn: Callable[[World], object] = field(compare=False)

    def image(self, worlds: Iterable[World]) -> set[object]:
        return {self.fn(w) for w in worlds}

    def partition(self, worlds: Sequence[World]) -> tuple[frozenset[World], ...]:
        cells: dict[object, list[World]] = {}
        for w in worlds:
            cells.setdefault(self.fn(w), []).append(w)
        return tuple(frozenset(members) for members in cells.values())


@dataclass(frozen=True)
class Task:
    """A deterministic Boolean task on ``World``."""

    name: str
    fn: Callable[[World], Label] = field(compare=False)


def _parity(coords: Sequence[int]) -> Callable[[World], int]:
    fixed = tuple(coords)

    def q(world: World) -> int:
        acc = 0
        for c in fixed:
            acc ^= world[c]
        return acc

    return q


def quotient_library(n_bits: int = N_BITS) -> list[Quotient]:
    """The concern-parameter lattice from Instrument 4:

    constant + all 15 subset-parities + joint pair-parities + joint bit-reads
    + one triple bit-read + identity.
    """

    library: list[Quotient] = [Quotient(name="constant", fn=lambda _w: 0)]
    for size in range(1, n_bits + 1):
        for subset in combinations(range(n_bits), size):
            label = "parity{" + ",".join(str(c) for c in subset) + "}"
            library.append(Quotient(name=label, fn=_parity(subset)))
    if n_bits == 4:
        def joint_p01_p23(world: World) -> tuple[int, int]:
            return (world[0] ^ world[1], world[2] ^ world[3])

        def joint_p02_p13(world: World) -> tuple[int, int]:
            return (world[0] ^ world[2], world[1] ^ world[3])

        def joint_p03_p12(world: World) -> tuple[int, int]:
            return (world[0] ^ world[3], world[1] ^ world[2])

        def joint_bit_0_1(world: World) -> tuple[int, int]:
            return (world[0], world[1])

        def joint_bit_2_3(world: World) -> tuple[int, int]:
            return (world[2], world[3])

        def joint_bit_0_1_2(world: World) -> tuple[int, int, int]:
            return (world[0], world[1], world[2])

        library.extend(
            [
                Quotient(name="joint(parity{0,1},parity{2,3})", fn=joint_p01_p23),
                Quotient(name="joint(parity{0,2},parity{1,3})", fn=joint_p02_p13),
                Quotient(name="joint(parity{0,3},parity{1,2})", fn=joint_p03_p12),
                Quotient(name="joint(bit_0,bit_1)", fn=joint_bit_0_1),
                Quotient(name="joint(bit_2,bit_3)", fn=joint_bit_2_3),
                Quotient(name="joint(bit_0,bit_1,bit_2)", fn=joint_bit_0_1_2),
            ]
        )
    library.append(Quotient(name="identity", fn=lambda w: w))
    return library


TRUE_Z_NAME = "joint(parity{0,1},parity{2,3})"


def latent_z(world: World) -> tuple[int, int]:
    return (world[0] ^ world[1], world[2] ^ world[3])


SHARED_FAMILY: tuple[Task, ...] = (
    Task(name="shared_p01", fn=lambda w: w[0] ^ w[1]),
    Task(name="shared_p23", fn=lambda w: w[2] ^ w[3]),
    Task(name="shared_global_parity", fn=lambda w: w[0] ^ w[1] ^ w[2] ^ w[3]),
)


# ---------- Axes ----------


def _entropy(counts: Iterable[int]) -> float:
    counts = [c for c in counts if c > 0]
    total = sum(counts)
    if total == 0:
        return 0.0
    return -sum((c / total) * math.log2(c / total) for c in counts)


def conditional_entropy(
    worlds: Sequence[World], target: Callable[[World], Label], q: Quotient
) -> float:
    """H(Y | q(X)) in bits under the uniform distribution."""

    cells: dict[object, Counter[Label]] = {}
    for w in worlds:
        cells.setdefault(q.fn(w), Counter())[target(w)] += 1
    total = len(worlds)
    residual = 0.0
    for counter in cells.values():
        cell_total = sum(counter.values())
        residual += (cell_total / total) * _entropy(counter.values())
    return residual


def task_sufficiency(
    worlds: Sequence[World], tasks: Sequence[Task], q: Quotient
) -> float:
    """max_alpha H(Y_alpha | q(X)) -- the extended-program's I(Y; X | q(X)) axis."""

    return max(conditional_entropy(worlds, t.fn, q) for t in tasks)


def coding_cost(worlds: Sequence[World], q: Quotient) -> float:
    """log2(|image(q)|)."""

    size = len(q.image(worlds))
    return math.log2(size) if size > 0 else 0.0


def dynamical_closure(_worlds: Sequence[World], _q: Quotient) -> float:
    """Static world: no dynamics -> closure fixed to 0 (see README)."""

    return 0.0


def control_regret(_worlds: Sequence[World], _q: Quotient) -> float:
    """Static world: no controller -> regret fixed to 0 (see README)."""

    return 0.0


# ---------- Pareto machinery ----------


@dataclass(frozen=True)
class QuotientAxes:
    quotient: str
    image_size: int
    task_sufficiency: float
    coding_cost: float
    dynamical_closure: float
    control_regret: float

    def as_axis_tuple(self) -> tuple[float, float, float, float]:
        return (
            self.task_sufficiency,
            self.coding_cost,
            self.dynamical_closure,
            self.control_regret,
        )


def score_quotient(
    worlds: Sequence[World], tasks: Sequence[Task], q: Quotient
) -> QuotientAxes:
    return QuotientAxes(
        quotient=q.name,
        image_size=len(q.image(worlds)),
        task_sufficiency=round(task_sufficiency(worlds, tasks, q), 12),
        coding_cost=round(coding_cost(worlds, q), 12),
        dynamical_closure=dynamical_closure(worlds, q),
        control_regret=control_regret(worlds, q),
    )


def weakly_dominates(a: QuotientAxes, b: QuotientAxes) -> bool:
    """Standard Pareto: a weakly dominates b iff a <= b on every axis
    and a < b on at least one."""

    ta = a.as_axis_tuple()
    tb = b.as_axis_tuple()
    weakly_better_everywhere = all(x <= y for x, y in zip(ta, tb, strict=True))
    strictly_better_somewhere = any(x < y for x, y in zip(ta, tb, strict=True))
    return weakly_better_everywhere and strictly_better_somewhere


def pareto_frontier(records: Sequence[QuotientAxes]) -> list[QuotientAxes]:
    """The subset of records that no other record dominates."""

    result: list[QuotientAxes] = []
    for r in records:
        dominated = any(
            weakly_dominates(other, r) for other in records if other.quotient != r.quotient
        )
        if not dominated:
            result.append(r)
    return result


def is_antichain(records: Sequence[QuotientAxes]) -> bool:
    """No pair of records dominates each other (Pareto antichain)."""

    for a in records:
        for b in records:
            if a.quotient == b.quotient:
                continue
            if weakly_dominates(a, b):
                return False
    return True


# ---------- Partition refinement (for the AF-2 fine-vs-coarse test) ----------


def _to_partition(
    q: Quotient, worlds: Sequence[World]
) -> frozenset[frozenset[World]]:
    return frozenset(q.partition(worlds))


def strictly_finer(
    finer: Quotient, coarser: Quotient, worlds: Sequence[World]
) -> bool:
    """finer < coarser on the lattice iff every finer-block is inside a
    coarser-block AND the partitions are not equal."""

    fine = _to_partition(finer, worlds)
    coarse = _to_partition(coarser, worlds)
    if fine == coarse:
        return False
    coarse_list = list(coarse)
    for block in fine:
        if not any(block.issubset(cb) for cb in coarse_list):
            return False
    return True


def strictly_coarser(
    coarser: Quotient, finer: Quotient, worlds: Sequence[World]
) -> bool:
    return strictly_finer(finer, coarser, worlds)


# ---------- Benchmark ----------


def evaluate_benchmark() -> dict:
    worlds = all_worlds(N_BITS)
    library = quotient_library(N_BITS)
    tasks = SHARED_FAMILY

    scored = [score_quotient(worlds, tasks, q) for q in library]
    by_name = {r.quotient: r for r in scored}
    q_by_name = {q.name: q for q in library}

    frontier = pareto_frontier(scored)
    frontier_names = {r.quotient for r in frontier}

    z_record = by_name[TRUE_Z_NAME]
    identity_record = by_name["identity"]
    constant_record = by_name["constant"]

    # AF1 gates
    af1_frontier_is_antichain = is_antichain(frontier)
    af1_frontier_contains_true_Z = TRUE_Z_NAME in frontier_names
    af1_frontier_contains_constant = "constant" in frontier_names

    # Static-case collapse: Z dominates identity.
    af1_identity_is_dominated_in_static_case = weakly_dominates(
        z_record, identity_record
    )

    # AF2 gates
    af2_sufficient_frontier_is_true_Z_alone = frontier_names.intersection(
        {r.quotient for r in scored if r.task_sufficiency == 0.0}
    ) == {TRUE_Z_NAME}

    # Every Pareto member is either equal-to-Z or strictly coarser than Z on
    # the lattice. (Equivalently: no Pareto member is strictly finer than Z.)
    z_quotient = q_by_name[TRUE_Z_NAME]
    af2_no_pareto_strictly_finer_than_true_Z = not any(
        strictly_finer(q_by_name[r.quotient], z_quotient, worlds)
        for r in frontier
    )

    gates = {
        "af1_frontier_is_antichain": af1_frontier_is_antichain,
        "af1_frontier_contains_true_Z": af1_frontier_contains_true_Z,
        "af1_frontier_contains_constant": af1_frontier_contains_constant,
        "af1_identity_is_dominated_in_static_case": (
            af1_identity_is_dominated_in_static_case
        ),
        "af2_sufficient_frontier_is_true_Z_alone": (
            af2_sufficient_frontier_is_true_Z_alone
        ),
        "af2_no_pareto_strictly_finer_than_true_Z": (
            af2_no_pareto_strictly_finer_than_true_Z
        ),
    }
    status = "pass" if all(gates.values()) else "fail"

    return {
        "status": status,
        "gates": gates,
        "latent_Z_definition": (
            "joint(parity{0,1}, parity{2,3}) on a 4-bit Boolean world"
        ),
        "num_quotients": len(scored),
        "quotients": [
            {
                "quotient": r.quotient,
                "image_size": r.image_size,
                "task_sufficiency": r.task_sufficiency,
                "coding_cost": r.coding_cost,
                "dynamical_closure": r.dynamical_closure,
                "control_regret": r.control_regret,
                "pareto": r.quotient in frontier_names,
            }
            for r in scored
        ],
        "pareto_frontier": sorted(frontier_names),
        "constant_record": {
            "quotient": constant_record.quotient,
            "task_sufficiency": constant_record.task_sufficiency,
            "coding_cost": constant_record.coding_cost,
        },
        "true_Z_record": {
            "quotient": z_record.quotient,
            "task_sufficiency": z_record.task_sufficiency,
            "coding_cost": z_record.coding_cost,
        },
        "identity_record": {
            "quotient": identity_record.quotient,
            "task_sufficiency": identity_record.task_sufficiency,
            "coding_cost": identity_record.coding_cost,
        },
    }
