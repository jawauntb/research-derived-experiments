"""Paper D: a transfer that should fail.

Possibility 6 says Lorentz geometry, Lamport happens-before, and
positional encodings are one object.  Paper A §4 predicted the
failures.  This package puts a finite transfer on the table.

Lorentz / Lamport toy: labeled events ``e0..e3`` placed on a
``{0,1,2,3}²`` integer Minkowski grid.  Causal order is
``Δt > 0`` and ``Δt² − Δx² ≥ 0``.  The diamond poset is
``e0`` precedes ``e1,e2,e3`` and ``e1,e2`` precede ``e3``,
with ``e1`` incomparable to ``e2``.

- Lamport task: concurrency of ``{e1,e2}``.  Constant on the
  diamond fibre.
- Lorentz task: interval ``s²(e1,e2)``.  Moves on that fibre.

PE toy: the Paper A/B ``first_bit`` / ``q_perm`` cell.  Disclosed
as already-enumerated.  The transfer "positions are leftover
privilege, quotient them" fails representability.

Kill Possibility 6 on this harness if ``s²(e1,e2)`` is unique on
the diamond fibre, or if ``q_perm`` represents ``first_bit``.
A reopen still passes CI.

Not a functor.  Not real Lorentz physics.  Not Paper E/F.
"""

from __future__ import annotations

from itertools import permutations
from typing import Literal, TypedDict

from experiments.delete_the_absolute.core import all_worlds, is_representable

EXPERIMENT_ID = "delete_repair_disanalogy"
RUN_ID = "delete_repair_disanalogy_2026_08_17"
PRODUCING_AGENT = "Cursor Grok 4.6 (cloud agent, under J. Brown direction)"
SESSION_REF = "bc-01a00d99-d2d8-7c5e-a8d0-d0090dfd7bdd"
GRID = 4
DIAMOND: frozenset[tuple[int, int]] = frozenset(
    {(0, 1), (0, 2), (0, 3), (1, 3), (2, 3)}
)

PROCESS_DISCLOSURE = (
    "Exact integer Minkowski diamond fibre plus the Paper A/B "
    "first_bit/q_perm cell.  Not a functor, not real Lorentz "
    "physics, not Paper E/F."
)


class ProducingAgent(TypedDict):
    identity: str
    session_ref: str


class Embedding(TypedDict):
    points: list[list[int]]
    s2_e1_e2: int


class LorentzLamport(TypedDict):
    n_grid_points: int
    n_injections: int
    n_diamond: int
    distinct_s2: list[int]
    n_distinct_s2: int
    n_by_s2: dict[str, int]
    concurrency_constant: bool
    witnesses: list[Embedding]


class PETransfer(TypedDict):
    source: str
    typed_representable: bool
    crossed_representable: bool
    crossed_screen: str


class Ranking(TypedDict):
    rule: str
    poset_does_not_fix_metric: bool
    poset_fixes_concurrency: bool
    pe_quotient_fails: bool
    pe_typed_works: bool
    verdict: Literal["disanalogy_holds", "identification_reopened"]


class BenchmarkPayload(TypedDict):
    status: Literal["pass", "fail"]
    experiment_id: str
    run_id: str
    producing_agent: ProducingAgent
    lorentz_lamport: LorentzLamport
    pe: PETransfer
    ranking: Ranking
    gates: dict[str, bool]
    process_disclosure: str
    withheld: list[str]


def interval(src: tuple[int, int], dst: tuple[int, int]) -> int:
    dt = dst[0] - src[0]
    dx = dst[1] - src[1]
    return dt * dt - dx * dx


def is_causal(src: tuple[int, int], dst: tuple[int, int]) -> bool:
    dt = dst[0] - src[0]
    return dt > 0 and interval(src, dst) >= 0


def poset_of(points: tuple[tuple[int, int], ...]) -> frozenset[tuple[int, int]]:
    related: set[tuple[int, int]] = set()
    for i, src in enumerate(points):
        for j, dst in enumerate(points):
            if i != j and is_causal(src, dst):
                related.add((i, j))
    return frozenset(related)


def grid_points() -> tuple[tuple[int, int], ...]:
    return tuple((t, x) for t in range(GRID) for x in range(GRID))


def diamond_embeddings() -> list[tuple[tuple[int, int], ...]]:
    found: list[tuple[tuple[int, int], ...]] = []
    for points in permutations(grid_points(), 4):
        if poset_of(points) == DIAMOND:
            found.append(points)
    return found


def _lorentz_lamport() -> LorentzLamport:
    points = grid_points()
    n_injections = 1
    for offset in range(4):
        n_injections *= len(points) - offset
    diamonds = diamond_embeddings()
    s2_list = [interval(item[1], item[2]) for item in diamonds]
    s2_values = sorted(set(s2_list))
    n_by_s2 = {str(value): s2_list.count(value) for value in s2_values}
    concurrent = [
        (not is_causal(item[1], item[2])) and (not is_causal(item[2], item[1]))
        for item in diamonds
    ]
    witnesses: list[Embedding] = []
    seen: set[int] = set()
    for item in diamonds:
        s2 = interval(item[1], item[2])
        if s2 in seen:
            continue
        seen.add(s2)
        witnesses.append({"points": [list(event) for event in item], "s2_e1_e2": s2})
        if len(witnesses) == 4:
            break
    return {
        "n_grid_points": len(points),
        "n_injections": n_injections,
        "n_diamond": len(diamonds),
        "distinct_s2": s2_values,
        "n_distinct_s2": len(s2_values),
        "n_by_s2": n_by_s2,
        "concurrency_constant": bool(concurrent) and all(concurrent),
        "witnesses": witnesses,
    }


def evaluate_benchmark() -> BenchmarkPayload:
    lorentz = _lorentz_lamport()
    worlds = all_worlds()
    pe_typed = is_representable(worlds, "q_stab0", "first_bit")
    pe_crossed = is_representable(worlds, "q_perm", "first_bit")
    pe: PETransfer = {
        "source": "delete_the_absolute first_bit/q_perm cell",
        "typed_representable": pe_typed,
        "crossed_representable": pe_crossed,
        "crossed_screen": "q_perm",
    }
    poset_moves_metric = lorentz["n_distinct_s2"] >= 2
    pe_fail = (not pe_crossed) and pe_typed
    disanalogy = poset_moves_metric and lorentz["concurrency_constant"] and pe_fail
    ranking: Ranking = {
        "rule": (
            "Disanalogy holds iff the diamond poset fibre has at least "
            "two s²(e1,e2) values, concurrency of {e1,e2} stays true, "
            "and the PE privilege-quotient fails. Unique s², or q_perm "
            "representing first_bit, reopens identification."
        ),
        "poset_does_not_fix_metric": poset_moves_metric,
        "poset_fixes_concurrency": lorentz["concurrency_constant"],
        "pe_quotient_fails": not pe_crossed,
        "pe_typed_works": pe_typed,
        "verdict": "disanalogy_holds" if disanalogy else "identification_reopened",
    }
    required = {
        "DIS_ENUMERATION": lorentz["n_diamond"] >= 2,
        "DIS_GRID": lorentz["n_grid_points"] == GRID * GRID,
        "DIS_PE_TYPED": pe_typed,
        "DIS_RANKING_RECORDED": ranking["verdict"]
        in {"disanalogy_holds", "identification_reopened"},
        "DIS_CLAIM_BOUNDARY": True,
    }
    return {
        "status": "pass" if all(required.values()) else "fail",
        "experiment_id": EXPERIMENT_ID,
        "run_id": RUN_ID,
        "producing_agent": {"identity": PRODUCING_AGENT, "session_ref": SESSION_REF},
        "lorentz_lamport": lorentz,
        "pe": pe,
        "ranking": ranking,
        "gates": required,
        "process_disclosure": PROCESS_DISCLOSURE,
        "withheld": [
            "A functor unifying Lorentz, Lamport, and positional encodings",
            "Real Lorentz physics / continuum boosts",
            "Paper E agent benchmark",
            "Universal calculus (Paper F)",
        ],
    }
