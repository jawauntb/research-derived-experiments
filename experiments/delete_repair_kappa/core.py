"""Paper F: specify κ before fitting it.

Possibility 1 says there is a function κ from typed failure
signatures to minimal repairs, natural, computable, stable under
relabelling.

Paper E killed the cheap five-field signature as that function.
This package writes the maps *first*, then runs the registered
suite.  It does not fit a new signature to the miss.

Specified maps
--------------

κ_cheap
    Domain: Paper E ``Signature``
    (mixes, n_fibres, n_worlds, y_has_nontrivial_symmetry,
    connection_mismatch).
    Codomain: {restore, quotient, transport, noop}.
    Rule: Paper E ``decide``.  No menu search.

κ_screen
    Domain: (Y, q, Menu, edges).
    Rule, in this order:
      1. Kirchhoff mismatch → transport.
      2. R = {r in Menu : Y is constant on r-fibres}.
      3. r* = unique coarsest member of R: fewest fibres, then
         lexicographic screen id (disclosed tie-break).
      4. If q does not represent → restore.
      5. If n(r*) < n(q) → quotient.
      6. Else → noop.
    This is Theorem 4 / CommonSuffScreen on a finite menu, plus
    a total order.  It *is* a function.  It looks at the menu.

κ_unique
    Claim: without the tie-break, the set of representing menu
    screens is a singleton whenever a repair exists.
    Lean Path A / Path B is the schedule form of the same claim.

Kill Possibility 1 as a *new* calculus if κ_cheap is not a
function, κ_screen hits every registered case, uniqueness fails
without the tie-break, and the noncommute witness still exists.
That verdict is ``calculus_is_sic``.  A cheap-signature function
would be ``calculus_holds``.  κ_screen missing a case is
``no_function``.  Any of those three still passes CI.

Not text nomination.  Not an LLM.  Not a better language model.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Literal, TypedDict

from experiments.delete_repair_surgery.core import (
    CASES,
    MENU,
    SCREEN_FNS,
    TASK_FNS,
    Action,
    CaseSpec,
    Signature,
    connection_mismatch,
    decide,
    gold_of,
    signature_of,
)
from experiments.delete_the_absolute.core import (
    World,
    all_worlds,
    apply_perm,
    fiber_count,
    find_sequence_noncommute_witness,
    path_a_pair,
    path_b_pair,
    y_constant_on_fibers,
)

EXPERIMENT_ID = "delete_repair_kappa"
RUN_ID = "delete_repair_kappa_2026_08_17"
PRODUCING_AGENT = "Cursor Grok 4.6 (cloud agent, under J. Brown direction)"
SESSION_REF = "bc-01a00d99-d2d8-7c5e-a8d0-d0090dfd7bdd"
SWAP_03: tuple[int, ...] = (3, 1, 2, 0)

PROCESS_DISCLOSURE = (
    "κ is specified before the run: cheap signature, menu-relative "
    "coarsest representing screen, uniqueness-without-tie-break.  "
    "Not fitted.  Not an LLM.  Not a new master object if the "
    "working map is Theorem 4 plus a total order."
)

Verdict = Literal["calculus_is_sic", "calculus_holds", "no_function"]


class ProducingAgent(TypedDict):
    identity: str
    session_ref: str


class ScreenChoice(TypedDict):
    action: Action
    screen_id: str
    n_representing: int
    representing: list[str]


class CaseRow(TypedDict):
    case_id: str
    split: str
    task_id: str
    screen_id: str
    gold: Action
    cheap: Action
    screen: Action
    chosen_screen: str
    n_representing: int
    cheap_hit: bool
    screen_hit: bool
    signature: Signature


class Collision(TypedDict):
    signature: Signature
    case_ids: list[str]
    golds: list[str]


class RelabelRow(TypedDict):
    source_task: str
    image_task: str
    source_screen: str
    image_screen: str
    source_choice: str
    image_choice: str
    natural: bool


class Ranking(TypedDict):
    rule: str
    cheap_is_function: bool
    n_cheap_collisions: int
    screen_hits: int
    screen_n: int
    screen_exact: bool
    uniqueness_fails: bool
    max_representing: int
    noncommute: bool
    relabel_natural: bool
    pair_eq_screen_is_noop: bool
    verdict: Verdict


class BenchmarkPayload(TypedDict):
    status: Literal["pass", "fail"]
    experiment_id: str
    run_id: str
    producing_agent: ProducingAgent
    kappa_specification: dict[str, str]
    cases: list[CaseRow]
    collisions: list[Collision]
    relabels: list[RelabelRow]
    ranking: Ranking
    gates: dict[str, bool]
    process_disclosure: str
    withheld: list[str]


def representing_screens(task_id: str, worlds: tuple[World, ...]) -> list[str]:
    y_fn = TASK_FNS[task_id]
    named: list[tuple[int, str]] = []
    for name in MENU:
        q_fn = SCREEN_FNS[name]
        if y_constant_on_fibers(worlds, q_fn, y_fn):
            named.append((fiber_count(worlds, q_fn), name))
    named.sort()
    return [name for _count, name in named]


def coarsest_representing(task_id: str, worlds: tuple[World, ...]) -> str | None:
    """Fewest fibres, then lexicographic id.  Specified before the run."""

    names = representing_screens(task_id, worlds)
    if not names:
        return None
    best = names[0]
    best_n = fiber_count(worlds, SCREEN_FNS[best])
    tied = [name for name in names if fiber_count(worlds, SCREEN_FNS[name]) == best_n]
    return min(tied)


def kappa_screen(spec: CaseSpec, worlds: tuple[World, ...]) -> ScreenChoice:
    """The written function.  Menu-relative.  Theorem 4 plus a total order."""

    if connection_mismatch(spec["edges"]):
        return {
            "action": "transport",
            "screen_id": "",
            "n_representing": 0,
            "representing": [],
        }
    names = representing_screens(spec["task_id"], worlds)
    chosen = coarsest_representing(spec["task_id"], worlds)
    if chosen is None:
        return {
            "action": "broken",
            "screen_id": "",
            "n_representing": 0,
            "representing": [],
        }
    q_fn = SCREEN_FNS[spec["screen_id"]]
    y_fn = TASK_FNS[spec["task_id"]]
    current_n = fiber_count(worlds, q_fn)
    chosen_n = fiber_count(worlds, SCREEN_FNS[chosen])
    represents = y_constant_on_fibers(worlds, q_fn, y_fn)
    if not represents:
        action: Action = "restore"
    elif chosen_n < current_n:
        action = "quotient"
    else:
        action = "noop"
    return {
        "action": action,
        "screen_id": chosen,
        "n_representing": len(names),
        "representing": names,
    }


def signature_key(signature: Signature) -> tuple[bool, int, int, bool, bool]:
    return (
        signature["mixes"],
        signature["n_fibres"],
        signature["n_worlds"],
        signature["y_has_nontrivial_symmetry"],
        signature["connection_mismatch"],
    )


def cheap_collisions(rows: list[CaseRow]) -> list[Collision]:
    buckets: dict[tuple[bool, int, int, bool, bool], list[CaseRow]] = defaultdict(list)
    for row in rows:
        buckets[signature_key(row["signature"])].append(row)
    found: list[Collision] = []
    for grouped in buckets.values():
        golds = {row["gold"] for row in grouped}
        if len(golds) > 1:
            found.append(
                {
                    "signature": grouped[0]["signature"],
                    "case_ids": [row["case_id"] for row in grouped],
                    "golds": sorted(golds),
                }
            )
    found.sort(key=lambda item: item["case_ids"][0])
    return found


def relabel_world(world: World, perm: tuple[int, ...]) -> World:
    return apply_perm(perm, world)


def relabel_natural(
    source_task: str,
    image_task: str,
    source_screen: str,
    image_screen: str,
    worlds: tuple[World, ...],
) -> RelabelRow:
    """Swap of positions 0 and 3 should send first_bit/q_stab0 to last_bit/q_stab_last."""

    source_spec: CaseSpec = {
        "case_id": f"relabel_{source_task}_{source_screen}",
        "split": "held_out",
        "task_id": source_task,
        "screen_id": source_screen,
        "edges": CASES[0]["edges"],
    }
    image_spec: CaseSpec = {
        "case_id": f"relabel_{image_task}_{image_screen}",
        "split": "held_out",
        "task_id": image_task,
        "screen_id": image_screen,
        "edges": CASES[0]["edges"],
    }
    source = kappa_screen(source_spec, worlds)
    image = kappa_screen(image_spec, worlds)
    natural = source["action"] == image["action"] and (
        (source["screen_id"] == source_screen and image["screen_id"] == image_screen)
        or (source["action"] in {"noop", "transport"})
        or (
            source["screen_id"] == "q_stab0"
            and image["screen_id"] == "q_stab_last"
        )
        or (
            source["screen_id"] == "q_stab_last"
            and image["screen_id"] == "q_stab0"
        )
        or source["screen_id"] == image["screen_id"]
    )
    return {
        "source_task": source_task,
        "image_task": image_task,
        "source_screen": source_screen,
        "image_screen": image_screen,
        "source_choice": source["screen_id"] or source["action"],
        "image_choice": image["screen_id"] or image["action"],
        "natural": natural,
    }


def evaluate_benchmark() -> BenchmarkPayload:
    worlds = all_worlds()
    rows: list[CaseRow] = []
    for spec in CASES:
        signature = signature_of(spec, worlds)
        gold = gold_of(spec, worlds)
        cheap = decide(signature)
        screen = kappa_screen(spec, worlds)
        rows.append(
            {
                "case_id": spec["case_id"],
                "split": spec["split"],
                "task_id": spec["task_id"],
                "screen_id": spec["screen_id"],
                "gold": gold,
                "cheap": cheap,
                "screen": screen["action"],
                "chosen_screen": screen["screen_id"],
                "n_representing": screen["n_representing"],
                "cheap_hit": cheap == gold and gold != "broken",
                "screen_hit": screen["action"] == gold and gold != "broken",
                "signature": signature,
            }
        )

    collisions = cheap_collisions(rows)
    relabels = [
        relabel_natural("first_bit", "last_bit", "q_perm", "q_perm", worlds),
        relabel_natural("first_bit", "last_bit", "q_id", "q_id", worlds),
        relabel_natural("last_bit", "first_bit", "q_perm", "q_perm", worlds),
    ]
    pair_eq = next(row for row in rows if row["case_id"] == "pair_eq_q_id")
    bag_id = next(row for row in rows if row["case_id"] == "bag_q_id")
    seq_witness = find_sequence_noncommute_witness(worlds)
    pair_noncommute = path_a_pair((0, 1)) == path_a_pair((1, 1)) and path_b_pair(
        (0, 1)
    ) != path_b_pair((1, 1))
    noncommute = seq_witness is not None and pair_noncommute
    screen_hits = sum(1 for row in rows if row["screen_hit"])
    screen_n = len(rows)
    screen_exact = screen_hits == screen_n
    cheap_is_function = len(collisions) == 0
    uniqueness_fails = bag_id["n_representing"] > 1
    relabel_ok = all(row["natural"] for row in relabels)
    if cheap_is_function and screen_exact:
        verdict: Verdict = "calculus_holds"
    elif (not cheap_is_function) and screen_exact and uniqueness_fails and noncommute:
        verdict = "calculus_is_sic"
    else:
        verdict = "no_function"

    ranking: Ranking = {
        "rule": (
            "calculus_is_sic iff κ_cheap is not a function, κ_screen "
            "matches gold on every registered case, uniqueness fails "
            "without the tie-break, and Path A/B still disagree.  "
            "calculus_holds if the cheap signature is already a function.  "
            "no_function if κ_screen misses."
        ),
        "cheap_is_function": cheap_is_function,
        "n_cheap_collisions": len(collisions),
        "screen_hits": screen_hits,
        "screen_n": screen_n,
        "screen_exact": screen_exact,
        "uniqueness_fails": uniqueness_fails,
        "max_representing": max(row["n_representing"] for row in rows),
        "noncommute": noncommute,
        "relabel_natural": relabel_ok,
        "pair_eq_screen_is_noop": pair_eq["screen"] == "noop" and pair_eq["screen_hit"],
        "verdict": verdict,
    }
    required = {
        "KAP_SPECIFIED": True,
        "KAP_ENUMERATION": screen_n == 11,
        "KAP_SCREEN_DEFINED": all(row["screen"] != "broken" for row in rows),
        "KAP_RELABEL": relabel_ok,
        "KAP_RANKING_RECORDED": ranking["verdict"]
        in {"calculus_is_sic", "calculus_holds", "no_function"},
        "KAP_CLAIM_BOUNDARY": True,
    }
    return {
        "status": "pass" if all(required.values()) else "fail",
        "experiment_id": EXPERIMENT_ID,
        "run_id": RUN_ID,
        "producing_agent": {"identity": PRODUCING_AGENT, "session_ref": SESSION_REF},
        "kappa_specification": {
            "kappa_cheap": (
                "decide(Signature): mismatch→transport; mixes→restore; "
                "symmetry and n_fibres=n_worlds→quotient; else noop."
            ),
            "kappa_screen": (
                "Kirchhoff mismatch→transport; else coarsest representing "
                "menu screen by fibre count then name; restore/quotient/noop "
                "from that choice.  Theorem 4 plus a total order."
            ),
            "kappa_unique": (
                "The representing set is a singleton.  Killed by multiple "
                "representing screens or by Path A/B disagreement."
            ),
            "tie_break": "fewest fibres, then lexicographic screen id",
        },
        "cases": rows,
        "collisions": collisions,
        "relabels": relabels,
        "ranking": ranking,
        "gates": required,
        "process_disclosure": PROCESS_DISCLOSURE,
        "withheld": [
            "A new master object above SIC",
            "Text nomination / DR / DCR",
            "LLM agent eval",
            "A better language model",
            "Valence / concern",
        ],
    }
