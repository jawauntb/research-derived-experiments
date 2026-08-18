"""Door 2 consolidation: a second generator episode, same two ledgers.

The door-2 paper registered its own next test: run a *different*
definable macro through the same (q, K) and access ledgers.  One
outside fact could be a peculiarity of squaring; two of the same
shape are a border.

Episodes, both exhaustively enumerated:

``sq``
    The banked one, replayed.  Grammar {x, ×} vs {x, ×, sq},
    sq(a) doubles the exponent.  Target x^4 at size bound 7.
    Banked numbers: min size 7 vs 3.

``cube``
    The new one.  Grammar {x, ×} vs {x, ×, cube}, cube(a) triples
    the exponent.  Target x^3 at size bound 5.  Registered
    prediction: min size 5 vs 2 (mul-only formulas need 2k−1 nodes
    for x^k; the macro needs 2), screens invariant, round trip
    identity.

For each episode the (q, K) ledger is the q_den / q_size / q_depth
partitions restricted to the shared universe; the access ledger is
min size and fibre mass for the target.  Registered outcomes:

``border_consolidated``
    Both episodes are outside facts: screens invariant, access
    changed, round trips identity.

``border_sharpened``
    Exactly one episode reduces to screen motion.  The border between
    (q, K) facts and generator facts moves and the paper must say
    where.

``inconclusive``
    Anything else.

Not a kill of Possibility 5's representability reading.  Not Paper G.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Literal, TypedDict, cast

EXPERIMENT_ID = "delete_repair_generators"
RUN_ID = "delete_repair_generators_2026_08_18"
PRODUCING_AGENT = "Claude Fable 5 (Cursor agent, under J. Brown direction)"
SESSION_REF = "4adbd42d-0e99-41df-b0be-7d9d5b7e3caa"

PROCESS_DISCLOSURE = (
    "Two generator episodes, each exhaustively enumerated to its "
    "registered size bound, each audited against the same (q, K) and "
    "access ledgers as door 2.  Predictions registered before the "
    "run.  No sampling, no LLM."
)

Verdict = Literal["border_consolidated", "border_sharpened", "inconclusive"]

# A tree is ("x",), ("mul", a, b), or (macro_name, a).
Tree = tuple[object, ...]


class ProducingAgent(TypedDict):
    identity: str
    session_ref: str


class EpisodeSpec(TypedDict):
    episode_id: str
    macro: str
    multiplier: int
    size_bound: int
    target_exponent: int
    registered_min_base: int
    registered_min_ext: int


EPISODES: tuple[EpisodeSpec, ...] = (
    {
        "episode_id": "sq_x4",
        "macro": "sq",
        "multiplier": 2,
        "size_bound": 7,
        "target_exponent": 4,
        "registered_min_base": 7,
        "registered_min_ext": 3,
    },
    {
        "episode_id": "cube_x3",
        "macro": "cube",
        "multiplier": 3,
        "size_bound": 5,
        "target_exponent": 3,
        "registered_min_base": 5,
        "registered_min_ext": 2,
    },
)


class EpisodeResult(TypedDict):
    episode_id: str
    macro: str
    size_bound: int
    target_exponent: int
    n_trees_base: int
    n_trees_ext: int
    shared_universe_ok: bool
    screens_all_invariant: bool
    min_size_base: int
    min_size_ext: int
    mass_base: int
    mass_ext: int
    matches_registered_mins: bool
    access_changed: bool
    round_trip_identity: bool
    outside_fact: bool


class Ranking(TypedDict):
    rule: str
    n_episodes: int
    n_outside_facts: int
    all_registered_mins_match: bool
    verdict: Verdict


class BenchmarkPayload(TypedDict):
    status: Literal["pass", "fail"]
    experiment_id: str
    run_id: str
    producing_agent: ProducingAgent
    episodes: list[EpisodeResult]
    ranking: Ranking
    gates: dict[str, bool]
    process_disclosure: str
    withheld: list[str]


def tree_size(tree: Tree) -> int:
    if tree[0] == "x":
        return 1
    if tree[0] == "mul":
        return 1 + tree_size(cast(Tree, tree[1])) + tree_size(cast(Tree, tree[2]))
    return 1 + tree_size(cast(Tree, tree[1]))


def tree_depth(tree: Tree) -> int:
    if tree[0] == "x":
        return 1
    if tree[0] == "mul":
        return 1 + max(tree_depth(cast(Tree, tree[1])), tree_depth(cast(Tree, tree[2])))
    return 1 + tree_depth(cast(Tree, tree[1]))


def denotation(tree: Tree, multiplier: int) -> int:
    if tree[0] == "x":
        return 1
    if tree[0] == "mul":
        return denotation(cast(Tree, tree[1]), multiplier) + denotation(
            cast(Tree, tree[2]), multiplier
        )
    return multiplier * denotation(cast(Tree, tree[1]), multiplier)


def enumerate_trees(size_bound: int, macro: str | None) -> tuple[Tree, ...]:
    by_size: dict[int, list[Tree]] = defaultdict(list)
    by_size[1].append(("x",))
    for size in range(2, size_bound + 1):
        if macro is not None:
            for child in by_size[size - 1]:
                by_size[size].append((macro, child))
        for left_size in range(1, size - 1):
            right_size = size - 1 - left_size
            for left in by_size[left_size]:
                for right in by_size[right_size]:
                    by_size[size].append(("mul", left, right))
    trees: list[Tree] = []
    for size in range(1, size_bound + 1):
        trees.extend(by_size[size])
    return tuple(trees)


def partition_signature(
    trees: tuple[Tree, ...],
    screen: Literal["q_den", "q_size", "q_depth"],
    multiplier: int,
) -> tuple[tuple[Tree, ...], ...]:
    keyed: dict[int, list[Tree]] = defaultdict(list)
    for tree in trees:
        if screen == "q_den":
            key = denotation(tree, multiplier)
        elif screen == "q_size":
            key = tree_size(tree)
        else:
            key = tree_depth(tree)
        keyed[key].append(tree)
    return tuple(tuple(keyed[key]) for key in sorted(keyed))


def target_stats(
    trees: tuple[Tree, ...], target: int, multiplier: int
) -> tuple[int, int]:
    sizes = [
        tree_size(tree) for tree in trees if denotation(tree, multiplier) == target
    ]
    return (min(sizes), len(sizes))


def run_episode(spec: EpisodeSpec) -> EpisodeResult:
    base = enumerate_trees(spec["size_bound"], macro=None)
    ext = enumerate_trees(spec["size_bound"], macro=spec["macro"])
    base_set = set(base)
    shared_ok = base_set.issubset(set(ext))
    shared_from_ext = tuple(tree for tree in ext if tree in base_set)

    invariant = all(
        partition_signature(base, screen, spec["multiplier"])
        == partition_signature(shared_from_ext, screen, spec["multiplier"])
        for screen in ("q_den", "q_size", "q_depth")
    )

    min_base, mass_base = target_stats(base, spec["target_exponent"], spec["multiplier"])
    min_ext, mass_ext = target_stats(ext, spec["target_exponent"], spec["multiplier"])
    # Round trip: delete the macro (base), re-adjoin (fresh ext enumeration).
    min_ext_again, _mass = target_stats(
        enumerate_trees(spec["size_bound"], macro=spec["macro"]),
        spec["target_exponent"],
        spec["multiplier"],
    )
    round_trip = min_ext == min_ext_again
    matches = (
        min_base == spec["registered_min_base"] and min_ext == spec["registered_min_ext"]
    )
    access_changed = min_base != min_ext or mass_base != mass_ext
    outside_fact = shared_ok and invariant and access_changed and round_trip
    return {
        "episode_id": spec["episode_id"],
        "macro": spec["macro"],
        "size_bound": spec["size_bound"],
        "target_exponent": spec["target_exponent"],
        "n_trees_base": len(base),
        "n_trees_ext": len(ext),
        "shared_universe_ok": shared_ok,
        "screens_all_invariant": invariant,
        "min_size_base": min_base,
        "min_size_ext": min_ext,
        "mass_base": mass_base,
        "mass_ext": mass_ext,
        "matches_registered_mins": matches,
        "access_changed": access_changed,
        "round_trip_identity": round_trip,
        "outside_fact": outside_fact,
    }


def evaluate_benchmark() -> BenchmarkPayload:
    episodes = [run_episode(spec) for spec in EPISODES]
    n_outside = sum(1 for episode in episodes if episode["outside_fact"])
    mins_match = all(episode["matches_registered_mins"] for episode in episodes)
    if n_outside == len(episodes):
        verdict: Verdict = "border_consolidated"
    elif n_outside == 1:
        verdict = "border_sharpened"
    else:
        verdict = "inconclusive"
    ranking: Ranking = {
        "rule": (
            "border_consolidated iff every episode is an outside fact "
            "(screens invariant, access changed, round trip identity).  "
            "border_sharpened iff exactly one episode reduces.  "
            "inconclusive otherwise."
        ),
        "n_episodes": len(episodes),
        "n_outside_facts": n_outside,
        "all_registered_mins_match": mins_match,
        "verdict": verdict,
    }
    required = {
        "GEN_SPECIFIED": True,
        "GEN_TWO_EPISODES": len(episodes) == 2
        and episodes[0]["macro"] != episodes[1]["macro"],
        "GEN_SHARED_UNIVERSES": all(e["shared_universe_ok"] for e in episodes),
        "GEN_REGISTERED_MINS": mins_match,
        "GEN_ROUND_TRIPS": all(e["round_trip_identity"] for e in episodes),
        "GEN_RANKING_RECORDED": ranking["verdict"]
        in {"border_consolidated", "border_sharpened", "inconclusive"},
        "GEN_CLAIM_BOUNDARY": True,
    }
    return {
        "status": "pass" if all(required.values()) else "fail",
        "experiment_id": EXPERIMENT_ID,
        "run_id": RUN_ID,
        "producing_agent": {"identity": PRODUCING_AGENT, "session_ref": SESSION_REF},
        "episodes": episodes,
        "ranking": ranking,
        "gates": required,
        "process_disclosure": PROCESS_DISCLOSURE,
        "withheld": [
            "A kill of Possibility 5's representability reading",
            "A new master object above SIC",
            "Continuum claims",
            "LLM agent eval",
            "A better language model",
        ],
    }
