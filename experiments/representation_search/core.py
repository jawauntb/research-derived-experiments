"""Exact Fiber Finder: search a lattice of quotient maps for the sufficient one.

The Structural Intelligence Conjecture (see
``notes/structural_intelligence_conjecture.md``) says an intelligent system's
central move is to discover a quotient ``q : X -> Z`` such that (1) the
task-relevant target descends to ``Z`` (nothing task-relevant is lost) and
(2) irrelevant variation is confined to the fibers ``q^{-1}(z)`` (maximal
compression). This module makes that move exact and falsifiable on a tiny
Boolean world where the ground-truth invariant is known.

For each task we enumerate the full population (all ``2**n`` worlds, uniform),
a library of candidate quotients, and three selectors:

* ``minimal_sufficient`` -- among quotients that lose no task information
  (``H(Y | q(X)) == 0``), pick the most compressed (min ``log2 |image|``).
  This is the counit-fidelity-then-compress rule of the meta-framework.
* ``mdl_only`` -- pick the most compressed quotient overall, ignoring the
  target. It collapses the obstruction.
* ``accuracy_only`` -- pick the highest-mutual-information quotient, tie-broken
  toward the finest. It never compresses.

The pre-registered claim: only ``minimal_sufficient`` recovers the ground-truth
invariant, exhibiting that sufficiency-then-compression dominates both pure
description-length minimization and pure accuracy maximization.
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
    """A candidate coarse-graining ``q : World -> Z`` with a readable name."""

    name: str
    coords: tuple[int, ...]  # coordinates the quotient reads (empty = constant)
    fn: Callable[[World], object] = field(compare=False)

    def image(self, worlds: Iterable[World]) -> set[object]:
        return {self.fn(w) for w in worlds}


@dataclass(frozen=True)
class Task:
    """A learning task: a target label defined by a ground-truth invariant."""

    name: str
    n_bits: int
    truth_coords: tuple[int, ...]  # the subset whose parity is the target
    description: str


def all_worlds(n_bits: int) -> list[World]:
    return [tuple(bits) for bits in product((0, 1), repeat=n_bits)]


def parity(coords: Sequence[int]) -> Callable[[World], object]:
    fixed = tuple(coords)

    def q(world: World) -> object:
        acc = 0
        for c in fixed:
            acc ^= world[c]
        return acc

    return q


def quotient_library(n_bits: int) -> list[Quotient]:
    """Constant, every-subset parity, and identity -- a lattice of coordinates."""
    library: list[Quotient] = [
        Quotient(name="constant", coords=(), fn=lambda _w: 0),
    ]
    for size in range(1, n_bits + 1):
        for subset in combinations(range(n_bits), size):
            label = "parity{" + ",".join(str(c) for c in subset) + "}"
            library.append(Quotient(name=label, coords=subset, fn=parity(subset)))
    library.append(
        Quotient(name="identity", coords=tuple(range(n_bits)), fn=lambda w: w)
    )
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
    """H(Y | q(X)) in bits under the uniform distribution over ``worlds``."""
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
    """I(q(X); Y) = H(Y) - H(Y | q(X)) in bits."""
    h_y = _entropy(Counter(target(w) for w in worlds).values())
    return h_y - conditional_entropy(worlds, target, q)


def description_length(worlds: Sequence[World], q: Quotient) -> float:
    """log2 of the size of the quotient's image (bits to name a coarse cell)."""
    size = len(q.image(worlds))
    return math.log2(size) if size > 0 else 0.0


@dataclass(frozen=True)
class QuotientScore:
    name: str
    coords: tuple[int, ...]
    mutual_information: float
    conditional_entropy: float
    description_length: float
    image_size: int
    sufficient: bool


def score_quotient(
    worlds: Sequence[World], target: Callable[[World], Label], q: Quotient
) -> QuotientScore:
    ce = conditional_entropy(worlds, target, q)
    mi = mutual_information(worlds, target, q)
    dl = description_length(worlds, q)
    return QuotientScore(
        name=q.name,
        coords=q.coords,
        mutual_information=round(mi, 12),
        conditional_entropy=round(ce, 12),
        description_length=round(dl, 12),
        image_size=len(q.image(worlds)),
        sufficient=ce <= 1e-12,
    )


_EPS = 1e-9


def select_minimal_sufficient(scores: Sequence[QuotientScore]) -> QuotientScore:
    """Counit-fidelity first (H(Y|q)=0), then maximal compression (min DL)."""
    sufficient = [s for s in scores if s.sufficient]
    pool = sufficient if sufficient else list(scores)
    return min(pool, key=lambda s: (s.description_length, len(s.coords), s.name))


def select_mdl_only(scores: Sequence[QuotientScore]) -> QuotientScore:
    """Pure description-length minimization; ignores the target."""
    return min(scores, key=lambda s: (s.description_length, len(s.coords), s.name))


def select_accuracy_only(scores: Sequence[QuotientScore]) -> QuotientScore:
    """Pure mutual-information maximization, tie-broken toward the finest map."""
    return max(
        scores,
        key=lambda s: (round(s.mutual_information, 9), s.description_length),
    )


SELECTORS: dict[str, Callable[[Sequence[QuotientScore]], QuotientScore]] = {
    "minimal_sufficient": select_minimal_sufficient,
    "mdl_only": select_mdl_only,
    "accuracy_only": select_accuracy_only,
}


def _truth_name(task: Task) -> str:
    return "parity{" + ",".join(str(c) for c in task.truth_coords) + "}"


def evaluate_task(task: Task) -> dict:
    worlds = all_worlds(task.n_bits)
    target = parity(task.truth_coords)

    def target_label(world: World) -> Label:
        value = target(world)
        assert isinstance(value, int)
        return value

    library = quotient_library(task.n_bits)
    scores = [score_quotient(worlds, target_label, q) for q in library]
    truth_name = _truth_name(task)

    selections: dict[str, dict] = {}
    for selector_name, selector in SELECTORS.items():
        chosen = selector(scores)
        selections[selector_name] = {
            "chosen": chosen.name,
            "recovered_ground_truth": chosen.name == truth_name,
            "sufficient": chosen.sufficient,
            "description_length": chosen.description_length,
            "image_size": chosen.image_size,
            "mutual_information": chosen.mutual_information,
        }

    return {
        "task": task.name,
        "n_bits": task.n_bits,
        "ground_truth_quotient": truth_name,
        "description": task.description,
        "n_candidates": len(library),
        "selections": selections,
    }


DEFAULT_TASKS: tuple[Task, ...] = (
    Task(
        name="three_bit_invariant",
        n_bits=6,
        truth_coords=(0, 1, 2),
        description="Target is the parity of three of six bits; the other three are pure noise.",
    ),
    Task(
        name="single_coordinate",
        n_bits=6,
        truth_coords=(5,),
        description="Target is one coordinate; the minimal sufficient quotient reads one bit.",
    ),
    Task(
        name="global_parity",
        n_bits=6,
        truth_coords=(0, 1, 2, 3, 4, 5),
        description="Target is global parity; sufficient quotient is one bit but needs every coordinate.",
    ),
)


def evaluate_benchmark(tasks: Sequence[Task] = DEFAULT_TASKS) -> dict:
    task_reports = [evaluate_task(task) for task in tasks]

    minimal_recovers_all = all(
        report["selections"]["minimal_sufficient"]["recovered_ground_truth"]
        for report in task_reports
    )
    mdl_never_sufficient = all(
        not report["selections"]["mdl_only"]["sufficient"] for report in task_reports
    )
    accuracy_never_compresses = all(
        report["selections"]["accuracy_only"]["chosen"] == "identity"
        for report in task_reports
    )
    minimal_strictly_compresses = all(
        report["selections"]["minimal_sufficient"]["description_length"]
        < report["selections"]["accuracy_only"]["description_length"]
        for report in task_reports
    )

    gates = {
        "minimal_sufficient_recovers_ground_truth": minimal_recovers_all,
        "mdl_only_collapses_obstruction": mdl_never_sufficient,
        "accuracy_only_never_compresses": accuracy_never_compresses,
        "sufficiency_beats_accuracy_on_compression": minimal_strictly_compresses,
    }
    status = "pass" if all(gates.values()) else "fail"
    return {"status": status, "gates": gates, "tasks": task_reports}
