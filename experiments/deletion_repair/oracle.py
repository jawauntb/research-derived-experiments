"""DR1 — exhaustive oracle over candidate deletions.

Enumerates every ``D`` subset of the deletable propositions with ``|D| <= 2``
and labels it:

* **valid on alpha** -- the surviving extension still contains a member that
  solves the child task. A deletion that destroys the child task is invalid no
  matter what it unlocks.
* **covers omega** -- the surviving extension contains a member that solves the
  parent task *and* meets the parent cost budget.

``D`` is **load-bearing** iff both hold. Because propositions can be entangled
facets of one commitment, the load-bearing set may contain pairs whose
individual members are worthless on their own -- which is exactly the case
DR1's kinematics toy is built to exhibit.

Nothing here is a nominator. This is ground truth, computed by execution, and
it is what the execution-free nominators are scored against.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Sequence

from experiments.deletion_repair.toys import ToySystem


__all__ = ["DeletionRow", "OracleResult", "enumerate_deletions", "build_oracle"]

MAX_DELETION_SIZE = 2


@dataclass(frozen=True)
class DeletionRow:
    """One candidate deletion and its ground-truth labels."""

    deletion: tuple[str, ...]
    extension_size: int
    valid_on_alpha: bool
    covers_omega: bool
    min_cost: float

    @property
    def load_bearing(self) -> bool:
        return self.valid_on_alpha and self.covers_omega


@dataclass(frozen=True)
class OracleResult:
    toy: str
    baseline_extension: int
    rows: tuple[DeletionRow, ...]

    @property
    def load_bearing(self) -> tuple[tuple[str, ...], ...]:
        return tuple(r.deletion for r in self.rows if r.load_bearing)


def enumerate_deletions(
    toy: ToySystem, max_size: int = MAX_DELETION_SIZE
) -> tuple[tuple[str, ...], ...]:
    """Every ``D`` with ``1 <= |D| <= max_size``, in a stable order."""
    names = [p.name for p in toy.deletable]
    out: list[tuple[str, ...]] = []
    for size in range(1, max_size + 1):
        out.extend(tuple(sorted(combo)) for combo in itertools.combinations(names, size))
    return tuple(out)


def _min_cost(toy: ToySystem, members: Sequence) -> float:
    if not members:
        return float("inf")
    return min(float(toy.cost(h)) for h in members)


def build_oracle(toy: ToySystem, max_size: int = MAX_DELETION_SIZE) -> OracleResult:
    """Label every candidate deletion by execution."""
    rows: list[DeletionRow] = []
    for deletion in enumerate_deletions(toy, max_size):
        ext = toy.extension(frozenset(deletion))
        valid = any(toy.fits_alpha(h) for h in ext)
        covers = any(
            toy.fits_omega(h) and float(toy.cost(h)) <= toy.omega_cost_budget
            for h in ext
        )
        rows.append(
            DeletionRow(
                deletion=deletion,
                extension_size=len(ext),
                valid_on_alpha=valid,
                covers_omega=covers,
                min_cost=_min_cost(toy, ext),
            )
        )
    return OracleResult(
        toy=toy.name,
        baseline_extension=len(toy.extension()),
        rows=tuple(rows),
    )
