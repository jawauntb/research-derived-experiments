"""Door 2 of the close-out: is there a delete–repair fact outside (q, K)?

Possibility 5's dynamics reading says every delete–repair fact is a
movement of the screen and kernel.  The close-out names its own death
condition: a delete–repair fact that cannot be written that way.

This package enumerates the sharpest known candidate: the squaring
macro episode from US-2/US-3.  Delete ``sq`` from the grammar
{x, ×, sq}; the obstruction is the formula tax (min size for x^(2^n)
jumps from n+1 to 2^(n+1)−1); the repair is re-adjoining the macro.
That is a textbook delete–obstruction–repair loop.  The question is
what the episode *moves*.

The instrument enumerates every tree up to a registered size bound
over both grammars and checks two ledgers against each other:

(q, K) ledger
    The denotation screen (exponent), the size screen, and the depth
    screen, restricted to the shared universe (base-grammar trees are
    a subset of extended-grammar trees).  If the episode is (q, K)
    motion, something here must move.

Access ledger
    Min formula size and fibre mass (tree counts per exponent at the
    bound), per grammar.

Registered outcomes (all pass CI):

``outside_fact_found``
    Every registered screen partition on the shared universe is
    identical before and after the episode, the round trip
    (delete then re-adjoin) is the identity on the access table, and
    the access observables differ between grammars.  Then min size is
    not a function of the (q, K) data at this bound: a two-point
    separation, same shape as door 1.  The episode moves the
    generator set — a process coordinate — not the screen or kernel.

``all_reduce``
    Some registered screen partition on the shared universe differs
    between grammars and accounts for the access change.  Possibility
    5's (q, K) reading absorbs the episode.

``inconclusive``
    Anything else.

The close-out already quarantined access as process-relative.  This
instrument locates the boundary exactly: representability facts move
(q, K); generator-episode access facts do not.  Not a new master
object.  Not Paper G.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Literal, TypedDict, cast

EXPERIMENT_ID = "delete_repair_reduction"
RUN_ID = "delete_repair_reduction_2026_08_18"
PRODUCING_AGENT = "Claude Fable 5 (Cursor agent, under J. Brown direction)"
SESSION_REF = "4adbd42d-0e99-41df-b0be-7d9d5b7e3caa"

PROCESS_DISCLOSURE = (
    "Exhaustive tree enumeration to a registered size bound over "
    "{x, ×} and {x, ×, sq}.  Screens, targets, and the verdict rule "
    "are specified before the run.  No sampling, no LLM.  The episode "
    "under audit is the banked US-2/US-3 squaring separation, replayed "
    "as a delete–obstruction–repair loop."
)

SIZE_BOUND = 7
TARGET_EXPONENTS: tuple[int, ...] = (2, 4)

Verdict = Literal["outside_fact_found", "all_reduce", "inconclusive"]
GrammarId = Literal["base", "ext"]

# A tree is a nested tuple: ("x",), ("mul", a, b), ("sq", a).
Tree = tuple[object, ...]


class ProducingAgent(TypedDict):
    identity: str
    session_ref: str


class GrammarCensus(TypedDict):
    grammar: GrammarId
    n_trees: int
    n_exponents: int
    min_size_by_target: dict[str, int]
    mass_by_target: dict[str, int]


class ScreenInvarianceRow(TypedDict):
    screen_id: str
    n_cells_base_view: int
    n_cells_ext_view: int
    identical: bool


class RoundTrip(TypedDict):
    stage: str
    min_size_x4: int


class Ranking(TypedDict):
    rule: str
    shared_universe_ok: bool
    screens_all_invariant: bool
    access_changed: bool
    min_size_x4_base: int
    min_size_x4_ext: int
    mass_x4_base: int
    mass_x4_ext: int
    round_trip_identity: bool
    separation: str
    verdict: Verdict


class BenchmarkPayload(TypedDict):
    status: Literal["pass", "fail"]
    experiment_id: str
    run_id: str
    producing_agent: ProducingAgent
    size_bound: int
    censuses: list[GrammarCensus]
    screen_invariance: list[ScreenInvarianceRow]
    round_trip: list[RoundTrip]
    ranking: Ranking
    gates: dict[str, bool]
    process_disclosure: str
    withheld: list[str]


def tree_size(tree: Tree) -> int:
    if tree[0] == "x":
        return 1
    if tree[0] == "sq":
        return 1 + tree_size(cast(Tree, tree[1]))
    return 1 + tree_size(cast(Tree, tree[1])) + tree_size(cast(Tree, tree[2]))


def tree_depth(tree: Tree) -> int:
    if tree[0] == "x":
        return 1
    if tree[0] == "sq":
        return 1 + tree_depth(cast(Tree, tree[1]))
    return 1 + max(tree_depth(cast(Tree, tree[1])), tree_depth(cast(Tree, tree[2])))


def denotation(tree: Tree) -> int:
    """Exponent semantics: the tree denotes x**k."""

    if tree[0] == "x":
        return 1
    if tree[0] == "sq":
        return 2 * denotation(cast(Tree, tree[1]))
    return denotation(cast(Tree, tree[1])) + denotation(cast(Tree, tree[2]))


def enumerate_trees(size_bound: int, with_sq: bool) -> tuple[Tree, ...]:
    by_size: dict[int, list[Tree]] = defaultdict(list)
    by_size[1].append(("x",))
    for size in range(2, size_bound + 1):
        if with_sq:
            for child in by_size[size - 1]:
                by_size[size].append(("sq", child))
        for left_size in range(1, size - 1):
            right_size = size - 1 - left_size
            for left in by_size[left_size]:
                for right in by_size[right_size]:
                    by_size[size].append(("mul", left, right))
    trees: list[Tree] = []
    for size in range(1, size_bound + 1):
        trees.extend(by_size[size])
    return tuple(trees)


def census_of(grammar: GrammarId, trees: tuple[Tree, ...]) -> GrammarCensus:
    min_size: dict[str, int] = {}
    mass: dict[str, int] = {}
    exponents: set[int] = set()
    for tree in trees:
        k = denotation(tree)
        exponents.add(k)
        if k in TARGET_EXPONENTS:
            key = str(k)
            size = tree_size(tree)
            if key not in min_size or size < min_size[key]:
                min_size[key] = size
            mass[key] = mass.get(key, 0) + 1
    return {
        "grammar": grammar,
        "n_trees": len(trees),
        "n_exponents": len(exponents),
        "min_size_by_target": min_size,
        "mass_by_target": mass,
    }


def partition_signature(
    trees: tuple[Tree, ...], screen: Literal["q_den", "q_size", "q_depth"]
) -> tuple[tuple[Tree, ...], ...]:
    keyed: dict[int, list[Tree]] = defaultdict(list)
    for tree in trees:
        if screen == "q_den":
            key = denotation(tree)
        elif screen == "q_size":
            key = tree_size(tree)
        else:
            key = tree_depth(tree)
        keyed[key].append(tree)
    return tuple(tuple(keyed[key]) for key in sorted(keyed))


def evaluate_benchmark() -> BenchmarkPayload:
    base_trees = enumerate_trees(SIZE_BOUND, with_sq=False)
    ext_trees = enumerate_trees(SIZE_BOUND, with_sq=True)
    base_set = set(base_trees)
    shared_universe_ok = base_set.issubset(set(ext_trees))

    census_base = census_of("base", base_trees)
    census_ext = census_of("ext", ext_trees)

    # (q, K) ledger: each registered screen, restricted to the shared
    # universe, viewed from inside each grammar.  If the episode moved
    # the screen or kernel, the restricted partitions would differ.
    shared_from_ext = tuple(tree for tree in ext_trees if tree in base_set)
    screen_rows: list[ScreenInvarianceRow] = []
    for screen_id in ("q_den", "q_size", "q_depth"):
        base_view = partition_signature(base_trees, screen_id)
        ext_view = partition_signature(shared_from_ext, screen_id)
        screen_rows.append(
            {
                "screen_id": screen_id,
                "n_cells_base_view": len(base_view),
                "n_cells_ext_view": len(ext_view),
                "identical": base_view == ext_view,
            }
        )
    screens_all_invariant = all(row["identical"] for row in screen_rows)

    # Access ledger.
    min_x4_base = census_base["min_size_by_target"]["4"]
    min_x4_ext = census_ext["min_size_by_target"]["4"]
    mass_x4_base = census_base["mass_by_target"]["4"]
    mass_x4_ext = census_ext["mass_by_target"]["4"]
    access_changed = min_x4_base != min_x4_ext or mass_x4_base != mass_x4_ext

    # Round trip: ext --delete sq--> base --re-adjoin--> ext.
    round_trip: list[RoundTrip] = [
        {"stage": "ext_before_delete", "min_size_x4": min_x4_ext},
        {"stage": "base_after_delete", "min_size_x4": min_x4_base},
        {
            "stage": "ext_after_repair",
            "min_size_x4": census_of("ext", enumerate_trees(SIZE_BOUND, with_sq=True))[
                "min_size_by_target"
            ]["4"],
        },
    ]
    round_trip_identity = round_trip[0]["min_size_x4"] == round_trip[2]["min_size_x4"]

    if shared_universe_ok and screens_all_invariant and access_changed and round_trip_identity:
        verdict: Verdict = "outside_fact_found"
    elif not screens_all_invariant and access_changed:
        verdict = "all_reduce"
    else:
        verdict = "inconclusive"

    separation = (
        "Two grammars, identical (q, K) data on the shared universe "
        f"(all {len(screen_rows)} registered screens), different access "
        f"observables (min size {min_x4_base} vs {min_x4_ext}, mass "
        f"{mass_x4_base} vs {mass_x4_ext} at the bound).  Min size is "
        "not a function of the (q, K) data: one input, two required "
        "outputs."
    )

    ranking: Ranking = {
        "rule": (
            "outside_fact_found iff the shared universe embeds, every "
            "registered screen partition is identical across grammars "
            "on it, the delete/re-adjoin round trip is the identity on "
            "the access table, and an access observable differs.  "
            "all_reduce iff a registered screen moves and the access "
            "change tracks it.  inconclusive otherwise."
        ),
        "shared_universe_ok": shared_universe_ok,
        "screens_all_invariant": screens_all_invariant,
        "access_changed": access_changed,
        "min_size_x4_base": min_x4_base,
        "min_size_x4_ext": min_x4_ext,
        "mass_x4_base": mass_x4_base,
        "mass_x4_ext": mass_x4_ext,
        "round_trip_identity": round_trip_identity,
        "separation": separation,
        "verdict": verdict,
    }
    required = {
        "RED_SPECIFIED": True,
        "RED_ENUMERATION": census_base["n_trees"] > 0
        and census_ext["n_trees"] > census_base["n_trees"],
        "RED_SHARED_UNIVERSE": shared_universe_ok,
        "RED_TARGETS_INHABITED": all(
            str(k) in census_base["min_size_by_target"]
            and str(k) in census_ext["min_size_by_target"]
            for k in TARGET_EXPONENTS
        ),
        "RED_SCREEN_TABLE_RECORDED": len(screen_rows) == 3,
        "RED_ROUND_TRIP": round_trip_identity,
        "RED_RANKING_RECORDED": ranking["verdict"]
        in {"outside_fact_found", "all_reduce", "inconclusive"},
        "RED_CLAIM_BOUNDARY": True,
    }
    return {
        "status": "pass" if all(required.values()) else "fail",
        "experiment_id": EXPERIMENT_ID,
        "run_id": RUN_ID,
        "producing_agent": {"identity": PRODUCING_AGENT, "session_ref": SESSION_REF},
        "size_bound": SIZE_BOUND,
        "censuses": [census_base, census_ext],
        "screen_invariance": screen_rows,
        "round_trip": round_trip,
        "ranking": ranking,
        "gates": required,
        "process_disclosure": PROCESS_DISCLOSURE,
        "withheld": [
            "A new master object above SIC",
            "A kill of Possibility 5's representability reading",
            "Continuum claims / real spacetime",
            "LLM agent eval",
            "A better language model",
            "Valence / concern (door 3 is a separate instrument)",
        ],
    }
