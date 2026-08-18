"""Frozen domains, groups, truths, and OOD splits.

Nothing here is sampled at analysis time. Random groups were drawn once
with ``random.Random`` at the registered seeds and then written down as
literals.
"""

from __future__ import annotations

from fractions import Fraction
from typing import TypedDict


class FamilySpec(TypedDict):
    family_id: str
    n: int
    truth: tuple[int, ...]
    groups: dict[str, tuple[tuple[int, ...], ...]]
    aligned_is_full_symmetric: bool
    ood_train: tuple[int, ...]
    ood_test: tuple[int, ...]
    orbits: int


def _rots(n: int) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple((x + k) % n for x in range(n)) for k in range(n))


def _refs(n: int) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple((k - x) % n for x in range(n)) for k in range(n))


def _dihedral(n: int) -> tuple[tuple[int, ...], ...]:
    seen: set[tuple[int, ...]] = set()
    out: list[tuple[int, ...]] = []
    for perm in (*_rots(n), *_refs(n)):
        if perm not in seen:
            seen.add(perm)
            out.append(perm)
    return tuple(out)


C7 = _rots(7)
D7 = _dihedral(7)
C6 = _rots(6)
ID6 = tuple(range(6))
ID7 = tuple(range(7))
PARTNER6 = tuple(x ^ 1 for x in range(6))

CYCLIC_WRONG = (
    ID7,
    (2, 0, 4, 3, 5, 6, 1),
    (5, 4, 3, 2, 6, 0, 1),
    (1, 4, 0, 5, 2, 6, 3),
    (0, 5, 6, 1, 3, 4, 2),
    (5, 1, 4, 3, 6, 0, 2),
    (5, 1, 0, 6, 4, 3, 2),
)
CYCLIC_RANDOM = (
    ID7,
    (3, 6, 4, 1, 5, 2, 0),
    (3, 0, 5, 4, 2, 6, 1),
    (2, 0, 5, 1, 6, 3, 4),
    (3, 4, 1, 2, 0, 6, 5),
    (2, 4, 5, 6, 1, 3, 0),
    (2, 3, 4, 0, 1, 5, 6),
)
DIHEDRAL_WRONG = (
    ID7,
    (3, 4, 1, 6, 2, 5, 0),
    (5, 3, 4, 0, 1, 6, 2),
    (4, 2, 3, 6, 5, 0, 1),
    (6, 4, 5, 3, 2, 1, 0),
    (0, 4, 2, 3, 1, 5, 6),
    (0, 2, 4, 6, 1, 5, 3),
    (1, 6, 5, 2, 0, 3, 4),
    (6, 2, 4, 1, 3, 0, 5),
    (2, 0, 5, 4, 1, 3, 6),
    (5, 0, 4, 6, 1, 2, 3),
    (4, 6, 0, 3, 5, 1, 2),
    (6, 5, 4, 3, 1, 2, 0),
    (4, 6, 5, 3, 0, 2, 1),
)
DIHEDRAL_RANDOM = (
    ID7,
    (0, 3, 2, 5, 4, 1, 6),
    (5, 1, 2, 3, 4, 6, 0),
    (0, 3, 2, 5, 6, 1, 4),
    (4, 1, 3, 5, 6, 0, 2),
    (5, 0, 2, 6, 1, 3, 4),
    (1, 6, 2, 0, 3, 4, 5),
    (4, 5, 0, 3, 2, 1, 6),
    (2, 0, 5, 6, 3, 4, 1),
    (2, 0, 3, 4, 6, 1, 5),
    (1, 5, 4, 6, 3, 2, 0),
    (1, 6, 2, 3, 0, 4, 5),
    (6, 2, 4, 5, 0, 1, 3),
    (2, 0, 5, 4, 1, 6, 3),
)
COLOR_RANDOM = (
    ID6,
    (5, 3, 1, 4, 0, 2),
    (4, 5, 2, 1, 0, 3),
    (5, 0, 3, 2, 1, 4),
    (4, 1, 3, 5, 0, 2),
    (4, 1, 3, 5, 2, 0),
    (0, 4, 1, 2, 5, 3),
    (0, 1, 2, 5, 3, 4),
    (2, 1, 5, 0, 4, 3),
    (4, 3, 5, 2, 0, 1),
    (3, 5, 4, 0, 1, 2),
    (1, 5, 0, 3, 4, 2),
)

FAMILIES: tuple[FamilySpec, ...] = (
    {
        "family_id": "cyclic",
        "n": 7,
        "truth": (3, 4, 5, 6, 0, 1, 2),
        "groups": {
            "aligned": C7,
            "incomplete": C7[:3],
            "wrong": CYCLIC_WRONG,
            "random": CYCLIC_RANDOM,
        },
        "aligned_is_full_symmetric": False,
        "ood_train": (0, 1, 2),
        "ood_test": (3, 4, 5, 6),
        "orbits": 1,
    },
    {
        "family_id": "dihedral",
        "n": 7,
        "truth": (1, 0, 6, 5, 4, 3, 2),
        "groups": {
            "aligned": D7,
            "incomplete": C7,
            "wrong": DIHEDRAL_WRONG,
            "random": DIHEDRAL_RANDOM,
        },
        "aligned_is_full_symmetric": False,
        "ood_train": (0, 1, 2),
        "ood_test": (3, 4, 5, 6),
        "orbits": 1,
    },
    {
        "family_id": "parity",
        "n": 6,
        "truth": PARTNER6,
        "groups": {
            "aligned": (ID6, PARTNER6),
            "incomplete": (ID6,),
            "wrong": C6,
            "random": (ID6, (4, 0, 1, 2, 5, 3)),
        },
        "aligned_is_full_symmetric": False,
        "ood_train": (0, 2, 4),
        "ood_test": (1, 3, 5),
        "orbits": 3,
    },
    {
        "family_id": "color",
        "n": 6,
        "truth": (1, 2, 3, 4, 5, 0),
        "groups": {
            "aligned": (),
            "incomplete": C6,
            "wrong": C6,
            "random": COLOR_RANDOM,
        },
        "aligned_is_full_symmetric": True,
        "ood_train": (0, 1, 2),
        "ood_test": (3, 4, 5),
        "orbits": 1,
    },
)

GROUP_NAMES: tuple[str, ...] = ("aligned", "incomplete", "wrong", "random")
PI_SCHEDULES: tuple[str, ...] = ("uniform", "high", "low")
IID_SEEDS: tuple[int, ...] = (7, 11, 13, 17, 19)
IID_MS: tuple[int, ...] = (8, 32)
DELTA = 0.05
VACUOUS_BOUND = 0.99
HYPERPRIOR_WEIGHT = Fraction(1, 4)
