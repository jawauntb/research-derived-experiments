"""DR1 — the execution-free nominators.

A nominator scores a candidate deletion **without** running the parent task.
That is the whole point: nomination must be cheap so the expensive verifier
runs only on survivors. Each nominator sees the toy's propositions and
hypothesis space; none may call ``fits_omega``.

* ``weakness``  -- growth of the extension when ``D`` is removed. Fires when the
  over-specification blocks *coverage*.
* ``cost``      -- improvement in the best achievable resource cost. Fires when
  the over-specification blocks *reachability*.
* ``disjunctive`` -- ``max`` of the two after per-toy max-normalisation, so the
  two scales are comparable within a toy.
* ``random``    -- seeded control.
* ``size_only`` -- prefers larger deletions; a degenerate control that should
  lose whenever ranking is doing real work.

The structural hypothesis DR1 tests is that no *single* nominator ranks the
load-bearing deletion highly on both toys.
"""

from __future__ import annotations

import random
from typing import Callable, Final, Mapping, Sequence

from experiments.deletion_repair.toys import ToySystem


__all__ = ["NOMINATORS", "score_all", "rank", "tie_fraction"]

RANDOM_SEED: Final[int] = 20_260_724


def _extension_size(toy: ToySystem, deletion: Sequence[str]) -> int:
    return len(toy.extension(frozenset(deletion)))


def _best_cost(toy: ToySystem, deletion: Sequence[str]) -> float:
    members = toy.extension(frozenset(deletion))
    if not members:
        return float("inf")
    return min(float(toy.cost(h)) for h in members)


def weakness_gain(toy: ToySystem, deletion: Sequence[str]) -> float:
    """How much larger the extension gets when ``D`` is dropped."""
    return float(_extension_size(toy, deletion) - _extension_size(toy, ()))


def cost_attribution(toy: ToySystem, deletion: Sequence[str]) -> float:
    """How much the best achievable cost improves when ``D`` is dropped."""
    base = _best_cost(toy, ())
    after = _best_cost(toy, deletion)
    if base == float("inf") or after == float("inf"):
        return 0.0
    return float(base - after)


def _normalise(values: Mapping[tuple[str, ...], float]) -> dict[tuple[str, ...], float]:
    peak = max((abs(v) for v in values.values()), default=0.0)
    if peak <= 0.0:
        return {k: 0.0 for k in values}
    return {k: v / peak for k, v in values.items()}


def disjunctive(
    toy: ToySystem, deletions: Sequence[Sequence[str]]
) -> dict[tuple[str, ...], float]:
    """``max`` of the two nominators after per-toy max-normalisation."""
    w = _normalise({tuple(d): weakness_gain(toy, d) for d in deletions})
    c = _normalise({tuple(d): cost_attribution(toy, d) for d in deletions})
    return {k: max(w[k], c[k]) for k in w}


def _random_scores(deletions: Sequence[Sequence[str]]) -> dict[tuple[str, ...], float]:
    rng = random.Random(RANDOM_SEED)
    return {tuple(d): rng.random() for d in deletions}


def _size_only(deletions: Sequence[Sequence[str]]) -> dict[tuple[str, ...], float]:
    return {tuple(d): float(len(d)) for d in deletions}


#: Every nominator maps ``(toy, deletions) -> {deletion: score}``. Higher is
#: better; ties are broken deterministically by deletion name in :func:`rank`.
NOMINATORS: Final[dict[str, Callable[..., dict[tuple[str, ...], float]]]] = {
    "weakness": lambda toy, ds: {tuple(d): weakness_gain(toy, d) for d in ds},
    "cost": lambda toy, ds: {tuple(d): cost_attribution(toy, d) for d in ds},
    "disjunctive": disjunctive,
    "random": lambda toy, ds: _random_scores(ds),
    "size_only": lambda toy, ds: _size_only(ds),
}


def score_all(
    toy: ToySystem, deletions: Sequence[Sequence[str]]
) -> dict[str, dict[tuple[str, ...], float]]:
    return {name: fn(toy, deletions) for name, fn in NOMINATORS.items()}


def rank(
    scores: Mapping[tuple[str, ...], float], *, seed: int = RANDOM_SEED
) -> list[tuple[str, ...]]:
    """Deletions best-first, with ties broken by a SEEDED SHUFFLE.

    Tie-breaking by name would hand a completely flat nominator real credit
    whenever the load-bearing deletion happens to sort early -- a permitted
    field (the alphabet) carrying information it has not earned. That is the
    erratum-E1 failure mode, and it fired during DR1's construction: ``cost``
    is constant on the kinematics toy, so *every* score ties at zero, and
    alphabetical ordering alone put a load-bearing pair in its top 3.

    Shuffling within each tie group makes a silent nominator score at chance,
    which is the truthful representation of "this signal says nothing here".
    Reproducible given ``seed``.
    """
    rng = random.Random(seed)
    groups: dict[float, list[tuple[str, ...]]] = {}
    for deletion, value in scores.items():
        groups.setdefault(float(value), []).append(deletion)
    ordered: list[tuple[str, ...]] = []
    for value in sorted(groups, reverse=True):
        bucket = sorted(groups[value])
        rng.shuffle(bucket)
        ordered.extend(bucket)
    return ordered


def tie_fraction(scores: Mapping[tuple[str, ...], float]) -> float:
    """Share of candidates sitting in the single largest tie group.

    A nominator with ``tie_fraction == 1.0`` is silent on this toy: it has no
    opinion at all, and any apparent ranking is an artefact of tie-breaking.
    """
    if not scores:
        return 1.0
    counts: dict[float, int] = {}
    for value in scores.values():
        counts[float(value)] = counts.get(float(value), 0) + 1
    return max(counts.values()) / len(scores)
