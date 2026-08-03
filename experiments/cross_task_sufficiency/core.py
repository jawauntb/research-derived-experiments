"""Cross-task sufficiency: exact witness of Theorem 4.

Theorem 4 (Cross-task stability). If X = g(Z, eta) with Z independent of eta and
every task Y_alpha factors through Z, then Z is a sufficient statistic for the
family {Y_alpha} simultaneously; equivalently, the coarsest common sufficient
statistic (CSS) of the task family equals Z (up to sufficiency-preserving
refinement).

This module operationalises the theorem on a 4-bit Boolean world, exactly.

Setup.
------
- ``X = {0, 1}^4`` (16 worlds, uniform).
- Latent ``Z(x) = (parity{0,1}(x), parity{2,3}(x))`` (a 4-valued generator).
- ``shared`` task family: every task factors through Z.
- ``not_shared`` task family: at least one task depends on X beyond Z.

Enumeration.
------------
A lattice of quotients that includes single-bit reads, all subset parities,
joint quotients of disjoint parities, joint bit reads, and the identity.
The lattice explicitly contains ``joint(parity{0,1}, parity{2,3})`` -- which
is Z itself -- and the identity, so both the shared CSS and the not-shared CSS
are representable.

For each task family, every quotient is checked for sufficiency (``H(Y|q) = 0``
for every task in the family; equivalently, the quotient's partition refines
the task-induced partition). The coarsest common-sufficient quotient wins
(minimal description length; tie broken by name).

Predictions (pre-registered).
-----------------------------
- ``shared_css_equals_latent_Z``: for the shared family, the coarsest CSS is
  exactly the joint ``(parity{0,1}, parity{2,3})`` quotient.
- ``shared_css_strictly_coarser_than_identity``: its image is smaller than
  ``|X|``.
- ``not_shared_css_equals_identity``: for the not-shared family (tasks
  covering all four bits individually), the coarsest CSS is the identity.
- ``family_css_strictly_finer_than_some_single_task_mss``: for the shared
  family, at least one single task's minimal sufficient statistic is strictly
  coarser than the family CSS -- combining tasks tightens the required
  partition.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from itertools import combinations, product

World = tuple[int, ...]
Label = int


@dataclass(frozen=True)
class Quotient:
    """A candidate coarse-graining ``q : World -> hashable-cell``."""

    name: str
    fn: Callable[[World], object] = field(compare=False)

    def image(self, worlds: Iterable[World]) -> set[object]:
        return {self.fn(w) for w in worlds}

    def partition(self, worlds: Sequence[World]) -> list[frozenset[World]]:
        cells: dict[object, list[World]] = {}
        for w in worlds:
            cells.setdefault(self.fn(w), []).append(w)
        return [frozenset(members) for members in cells.values()]


@dataclass(frozen=True)
class Task:
    """A deterministic Boolean task on ``World``."""

    name: str
    n_bits: int
    fn: Callable[[World], Label] = field(compare=False)
    description: str = ""


def all_worlds(n_bits: int) -> list[World]:
    return [tuple(bits) for bits in product((0, 1), repeat=n_bits)]


def _parity(coords: Sequence[int]) -> Callable[[World], int]:
    fixed = tuple(coords)

    def q(world: World) -> int:
        acc = 0
        for c in fixed:
            acc ^= world[c]
        return acc

    return q


def quotient_library(n_bits: int) -> list[Quotient]:
    """A rich lattice: constant, subset parities, joint pair-parity, joint bits, identity."""

    library: list[Quotient] = [Quotient(name="constant", fn=lambda _w: 0)]
    for size in range(1, n_bits + 1):
        for subset in combinations(range(n_bits), size):
            label = "parity{" + ",".join(str(c) for c in subset) + "}"
            library.append(Quotient(name=label, fn=_parity(subset)))
    # Joint quotients built as tuples of coarser reads.
    # For n=4: the two disjoint pair parities (parity{0,1}, parity{2,3}) is Z.
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


def mutual_information(
    worlds: Sequence[World], target: Callable[[World], Label], q: Quotient
) -> float:
    h_y = _entropy(Counter(target(w) for w in worlds).values())
    return h_y - conditional_entropy(worlds, target, q)


def description_length(worlds: Sequence[World], q: Quotient) -> float:
    size = len(q.image(worlds))
    return math.log2(size) if size > 0 else 0.0


@dataclass(frozen=True)
class QuotientTaskScore:
    quotient: str
    task: str
    conditional_entropy: float
    mutual_information: float
    sufficient: bool


@dataclass(frozen=True)
class QuotientFamilyScore:
    quotient: str
    image_size: int
    description_length: float
    common_sufficient: bool


def score_task_pair(
    worlds: Sequence[World], task: Task, q: Quotient
) -> QuotientTaskScore:
    ce = conditional_entropy(worlds, task.fn, q)
    mi = mutual_information(worlds, task.fn, q)
    return QuotientTaskScore(
        quotient=q.name,
        task=task.name,
        conditional_entropy=round(ce, 12),
        mutual_information=round(mi, 12),
        sufficient=ce <= 1e-12,
    )


def score_family(
    worlds: Sequence[World], tasks: Sequence[Task], q: Quotient
) -> tuple[QuotientFamilyScore, list[QuotientTaskScore]]:
    task_scores = [score_task_pair(worlds, task, q) for task in tasks]
    common = all(s.sufficient for s in task_scores)
    return (
        QuotientFamilyScore(
            quotient=q.name,
            image_size=len(q.image(worlds)),
            description_length=round(description_length(worlds, q), 12),
            common_sufficient=common,
        ),
        task_scores,
    )


def coarsest_common_sufficient_statistic(
    worlds: Sequence[World],
    tasks: Sequence[Task],
    library: Sequence[Quotient],
) -> QuotientFamilyScore:
    """Coarsest quotient that is sufficient for every task; tie-broken by name."""

    scores = [score_family(worlds, tasks, q)[0] for q in library]
    common = [s for s in scores if s.common_sufficient]
    if not common:
        raise ValueError(
            "no common-sufficient statistic in the library (identity should always qualify)"
        )
    return min(common, key=lambda s: (s.description_length, s.quotient))


def minimal_sufficient_for_task(
    worlds: Sequence[World], task: Task, library: Sequence[Quotient]
) -> QuotientFamilyScore:
    scores = [score_family(worlds, [task], q)[0] for q in library]
    sufficient = [s for s in scores if s.common_sufficient]
    if not sufficient:
        raise ValueError(f"no sufficient statistic in the library for task {task.name}")
    return min(sufficient, key=lambda s: (s.description_length, s.quotient))


N_BITS = 4


def latent_z(world: World) -> tuple[int, int]:
    """The generative latent Z(x) = (parity{0,1}, parity{2,3}) used in Theorem 4 witness."""
    return (world[0] ^ world[1], world[2] ^ world[3])


SHARED_FAMILY: tuple[Task, ...] = (
    Task(
        name="shared_p01",
        n_bits=N_BITS,
        fn=lambda w: w[0] ^ w[1],
        description="parity{0,1} = first coordinate of Z.",
    ),
    Task(
        name="shared_p23",
        n_bits=N_BITS,
        fn=lambda w: w[2] ^ w[3],
        description="parity{2,3} = second coordinate of Z.",
    ),
    Task(
        name="shared_global_parity",
        n_bits=N_BITS,
        fn=lambda w: w[0] ^ w[1] ^ w[2] ^ w[3],
        description="parity{0,1,2,3} = XOR of the two coordinates of Z.",
    ),
)

NOT_SHARED_FAMILY: tuple[Task, ...] = (
    Task(
        name="notshared_bit_0",
        n_bits=N_BITS,
        fn=lambda w: w[0],
        description="Reveals bit 0 individually (not a function of Z).",
    ),
    Task(
        name="notshared_bit_1",
        n_bits=N_BITS,
        fn=lambda w: w[1],
        description="Reveals bit 1 individually.",
    ),
    Task(
        name="notshared_bit_2",
        n_bits=N_BITS,
        fn=lambda w: w[2],
        description="Reveals bit 2 individually.",
    ),
    Task(
        name="notshared_bit_3",
        n_bits=N_BITS,
        fn=lambda w: w[3],
        description="Reveals bit 3 individually.",
    ),
)


def evaluate_family(
    tasks: Sequence[Task],
    library: Sequence[Quotient],
    worlds: Sequence[World],
    label: str,
) -> dict:
    quotient_reports = []
    for q in library:
        family_score, task_scores = score_family(worlds, tasks, q)
        quotient_reports.append(
            {
                "quotient": family_score.quotient,
                "image_size": family_score.image_size,
                "description_length": family_score.description_length,
                "common_sufficient": family_score.common_sufficient,
                "per_task": [
                    {
                        "task": s.task,
                        "conditional_entropy": s.conditional_entropy,
                        "mutual_information": s.mutual_information,
                        "sufficient": s.sufficient,
                    }
                    for s in task_scores
                ],
            }
        )

    css = coarsest_common_sufficient_statistic(worlds, tasks, library)
    per_task_mss = [
        {
            "task": task.name,
            "minimal_sufficient": minimal_sufficient_for_task(
                worlds, task, library
            ).quotient,
            "minimal_sufficient_image_size": minimal_sufficient_for_task(
                worlds, task, library
            ).image_size,
        }
        for task in tasks
    ]

    return {
        "family": label,
        "n_tasks": len(tasks),
        "n_candidates": len(library),
        "coarsest_common_sufficient": {
            "quotient": css.quotient,
            "image_size": css.image_size,
            "description_length": css.description_length,
        },
        "per_task_minimal_sufficient": per_task_mss,
        "quotients": quotient_reports,
        "tasks": [{"name": t.name, "description": t.description} for t in tasks],
    }


def evaluate_benchmark() -> dict:
    worlds = all_worlds(N_BITS)
    library = quotient_library(N_BITS)

    shared = evaluate_family(SHARED_FAMILY, library, worlds, "shared_through_Z")
    not_shared = evaluate_family(
        NOT_SHARED_FAMILY, library, worlds, "not_shared_beyond_Z"
    )

    # Sanity-check the latent Z is in the library.
    z_name = "joint(parity{0,1},parity{2,3})"
    assert any(q.name == z_name for q in library), "latent Z must be in the library"

    shared_css = shared["coarsest_common_sufficient"]
    not_shared_css = not_shared["coarsest_common_sufficient"]

    # Family CSS strictly finer than SOME single-task MSS in the shared family:
    shared_single_max = max(
        item["minimal_sufficient_image_size"]
        for item in shared["per_task_minimal_sufficient"]
    )
    shared_family_image = shared_css["image_size"]

    gates = {
        "shared_css_equals_latent_Z": shared_css["quotient"] == z_name
        and shared_css["image_size"] == 4,
        "shared_css_strictly_coarser_than_identity": shared_css["image_size"]
        < 2**N_BITS,
        "not_shared_css_equals_identity": not_shared_css["quotient"] == "identity"
        and not_shared_css["image_size"] == 2**N_BITS,
        "family_css_strictly_finer_than_some_single_task_mss": shared_family_image
        > shared_single_max,
    }
    status = "pass" if all(gates.values()) else "fail"
    return {
        "status": status,
        "gates": gates,
        "latent_Z_definition": "joint(parity{0,1}, parity{2,3}) on a 4-bit Boolean world",
        "families": [shared, not_shared],
    }
