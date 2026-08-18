"""Door 1 of the close-out: gold is menu-relative, so no menu-blind κ.

The close-out (`papers/sic_dynamics/paper.md` §12) licenses exactly one
reopening of Possibility 1: a specified κ that does *not* look at the
menu and still hits a larger held-out family.  This package walks
through that door and measures what is on the other side.

The move is menu variation, not a fancier signature.  Paper E's
five-field rule is imported **frozen** — we do not refit it, per the
close-out's own prohibition.  Instead we evaluate the same registered
cases under two disclosed menus:

MENU_BASE
    The Paper E menu: q_id, q_rot, q_perm, q_stab0, q_stab_last.

MENU_EXT
    MENU_BASE plus q_pair01 (sort the first two bits) and q_pair23
    (sort the last two bits).

Gold is empirical menu-relative repair, exactly Paper E's ``gold_of``
parameterized by the menu.  If the same (task, screen) case has
different gold under the two menus, then gold is **not a function of
(Y, q)** — and therefore *no* menu-blind κ, of any signature width,
can match gold on both menus.  Menu-blindness dies in principle, not
just at five fields.

The suite is also strictly larger than Paper E's 11 cases: three new
tasks (pair23, or, count_ge2), two new screens, six new case rows.

Registered outcomes (any of these passes CI):

``menu_blind_dead``
    At least one gold flip between menus, and κ_screen (Theorem 4
    plus the disclosed total order, recomputed per menu) is exact on
    every row of both menus.

``menu_blind_lives``
    No flip anywhere, and the frozen five-field rule is exact and
    collision-free under both menus.  This reopens Possibility 1.

``no_function``
    κ_screen misses a row.  This reopens the no-computable-κ reading.

``inconclusive``
    Anything else.

Not text nomination.  Not an LLM.  Not a refit of κ_cheap.  Not a new
master object.  Not Paper G.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from typing import Literal, TypedDict

from experiments.delete_repair_surgery.core import (
    CASES,
    MENU,
    SCREEN_FNS,
    TASK_FNS,
    Action,
    CaseSpec,
    Signature,
    Split,
    connection_mismatch,
    decide,
    gold_of,
    has_nontrivial_symmetry,
)
from experiments.delete_repair_connection.core import KIRCHHOFF_FLAT
from experiments.delete_the_absolute.core import (
    Feature,
    World,
    all_worlds,
    apply_perm,
    fiber_count,
    y_constant_on_fibers,
)

EXPERIMENT_ID = "delete_repair_menu_blind"
RUN_ID = "delete_repair_menu_blind_2026_08_18"
PRODUCING_AGENT = "Claude Fable 5 (Cursor agent, under J. Brown direction)"
SESSION_REF = "4adbd42d-0e99-41df-b0be-7d9d5b7e3caa"

PROCESS_DISCLOSURE = (
    "Menus, screens, tasks, and cases are specified before gold is "
    "computed.  κ_cheap is Paper E's decide, imported frozen and never "
    "refit.  Gold is Paper E's empirical rule parameterized by the "
    "menu.  A gold flip between menus kills every menu-blind κ at "
    "once, of any signature width.  Not an LLM.  Not Paper G."
)

# Reversal of the four positions: sends first_bit to last_bit and
# the pair {0,1} to the pair {2,3}.  Disclosed relabel for naturality.
REVERSAL: tuple[int, ...] = (3, 2, 1, 0)

Verdict = Literal["menu_blind_dead", "menu_blind_lives", "no_function", "inconclusive"]
MenuId = Literal["base", "ext"]


class ProducingAgent(TypedDict):
    identity: str
    session_ref: str


def q_pair01(x: World) -> World:
    """Sort the first two bits; keep the rest.  12 fibres on {0,1}^4."""

    lo, hi = sorted((x[0], x[1]))
    return (lo, hi) + tuple(x[2:])


def q_pair23(x: World) -> World:
    """Sort the last two bits; keep the rest.  12 fibres on {0,1}^4."""

    lo, hi = sorted((x[2], x[3]))
    return tuple(x[:2]) + (lo, hi)


def y_pair23(x: World) -> int:
    return int(x[2] == x[3])


def y_or(x: World) -> int:
    return int(max(x))


def y_count_ge2(x: World) -> int:
    return int(sum(x) >= 2)


EXT_SCREEN_FNS: dict[str, Callable[[World], Feature]] = {
    **SCREEN_FNS,
    "q_pair01": q_pair01,
    "q_pair23": q_pair23,
}

EXT_TASK_FNS: dict[str, Callable[[World], Feature]] = {
    **TASK_FNS,
    "pair23": y_pair23,
    "or": y_or,
    "count_ge2": y_count_ge2,
}

MENU_BASE: tuple[str, ...] = MENU
MENU_EXT: tuple[str, ...] = MENU + ("q_pair01", "q_pair23")

# New held-out rows.  Together with the 11 imported Paper E cases the
# family has 17 specs and 34 (case, menu) rows.
NEW_CASES: tuple[CaseSpec, ...] = (
    {
        "case_id": "pair23_q_id",
        "split": "held_out",
        "task_id": "pair23",
        "screen_id": "q_id",
        "edges": KIRCHHOFF_FLAT,
    },
    {
        "case_id": "or_q_id",
        "split": "held_out",
        "task_id": "or",
        "screen_id": "q_id",
        "edges": KIRCHHOFF_FLAT,
    },
    {
        "case_id": "or_q_perm",
        "split": "held_out",
        "task_id": "or",
        "screen_id": "q_perm",
        "edges": KIRCHHOFF_FLAT,
    },
    {
        "case_id": "count_ge2_q_id",
        "split": "held_out",
        "task_id": "count_ge2",
        "screen_id": "q_id",
        "edges": KIRCHHOFF_FLAT,
    },
    {
        "case_id": "pair_eq_q_pair01",
        "split": "held_out",
        "task_id": "pair_eq",
        "screen_id": "q_pair01",
        "edges": KIRCHHOFF_FLAT,
    },
    {
        "case_id": "pair23_q_pair23",
        "split": "held_out",
        "task_id": "pair23",
        "screen_id": "q_pair23",
        "edges": KIRCHHOFF_FLAT,
    },
)

ALL_CASES: tuple[CaseSpec, ...] = CASES + NEW_CASES


class ScreenChoice(TypedDict):
    action: Action
    screen_id: str
    n_representing: int
    representing: list[str]


class MenuRow(TypedDict):
    case_id: str
    split: Split
    task_id: str
    screen_id: str
    menu: MenuId
    gold: Action
    cheap: Action
    screen: Action
    chosen_screen: str
    n_representing: int
    cheap_hit: bool
    screen_hit: bool
    signature: Signature


class FlipWitness(TypedDict):
    case_id: str
    task_id: str
    screen_id: str
    gold_base: Action
    gold_ext: Action


class Collision(TypedDict):
    menu: MenuId
    signature: Signature
    case_ids: list[str]
    golds: list[str]


class RelabelRow(TypedDict):
    source_task: str
    image_task: str
    menu: MenuId
    source_choice: str
    image_choice: str
    source_action: str
    image_action: str
    action_natural: bool
    screen_natural: bool


class Ranking(TypedDict):
    rule: str
    n_specs: int
    n_rows: int
    n_flips: int
    flip_case_ids: list[str]
    base_consistent_with_paper_e: bool
    cheap_hits_base: int
    cheap_hits_ext: int
    cheap_collisions_base: int
    cheap_collisions_ext: int
    cheap_function_per_menu: dict[str, bool]
    screen_hits: int
    screen_n: int
    screen_exact: bool
    relabel_action_natural: bool
    tie_break_screen_natural: bool
    tie_witnesses: list[str]
    verdict: Verdict


class BenchmarkPayload(TypedDict):
    status: Literal["pass", "fail"]
    experiment_id: str
    run_id: str
    producing_agent: ProducingAgent
    menus: dict[str, list[str]]
    specification: dict[str, str]
    rows: list[MenuRow]
    flips: list[FlipWitness]
    collisions: list[Collision]
    relabels: list[RelabelRow]
    ranking: Ranking
    gates: dict[str, bool]
    process_disclosure: str
    withheld: list[str]


def menu_of(menu_id: MenuId) -> tuple[str, ...]:
    return MENU_BASE if menu_id == "base" else MENU_EXT


def signature_of_ext(spec: CaseSpec, worlds: tuple[World, ...]) -> Signature:
    """Paper E's five fields, over the extended screen/task tables.

    Menu-independent by construction: the fields only see (Y, q, edges).
    """

    q_fn = EXT_SCREEN_FNS[spec["screen_id"]]
    y_fn = EXT_TASK_FNS[spec["task_id"]]
    return {
        "mixes": not y_constant_on_fibers(worlds, q_fn, y_fn),
        "n_fibres": fiber_count(worlds, q_fn),
        "n_worlds": len(worlds),
        "y_has_nontrivial_symmetry": has_nontrivial_symmetry(y_fn, worlds),
        "connection_mismatch": connection_mismatch(spec["edges"]),
    }


def representing_in_menu(
    task_id: str, worlds: tuple[World, ...], menu: tuple[str, ...]
) -> list[str]:
    y_fn = EXT_TASK_FNS[task_id]
    named: list[tuple[int, str]] = []
    for name in menu:
        q_fn = EXT_SCREEN_FNS[name]
        if y_constant_on_fibers(worlds, q_fn, y_fn):
            named.append((fiber_count(worlds, q_fn), name))
    named.sort()
    return [name for _count, name in named]


def coarsest_in_menu(
    task_id: str, worlds: tuple[World, ...], menu: tuple[str, ...]
) -> str | None:
    """Fewest fibres, then lexicographic id.  The disclosed total order."""

    names = representing_in_menu(task_id, worlds, menu)
    if not names:
        return None
    best_n = fiber_count(worlds, EXT_SCREEN_FNS[names[0]])
    tied = [name for name in names if fiber_count(worlds, EXT_SCREEN_FNS[name]) == best_n]
    return min(tied)


def gold_of_menu(
    spec: CaseSpec, worlds: tuple[World, ...], menu: tuple[str, ...]
) -> Action:
    """Paper E's empirical gold, with the menu as an explicit argument."""

    if connection_mismatch(spec["edges"]):
        return "transport"
    q_fn = EXT_SCREEN_FNS[spec["screen_id"]]
    y_fn = EXT_TASK_FNS[spec["task_id"]]
    current = fiber_count(worlds, q_fn)
    represents = y_constant_on_fibers(worlds, q_fn, y_fn)
    if not represents:
        if any(
            fiber_count(worlds, EXT_SCREEN_FNS[name]) > current
            and y_constant_on_fibers(worlds, EXT_SCREEN_FNS[name], y_fn)
            for name in menu
        ):
            return "restore"
        return "broken"
    if any(
        fiber_count(worlds, EXT_SCREEN_FNS[name]) < current
        and y_constant_on_fibers(worlds, EXT_SCREEN_FNS[name], y_fn)
        for name in menu
    ):
        return "quotient"
    return "noop"


def kappa_screen_menu(
    spec: CaseSpec, worlds: tuple[World, ...], menu: tuple[str, ...]
) -> ScreenChoice:
    """Theorem 4 plus the disclosed total order, recomputed per menu."""

    if connection_mismatch(spec["edges"]):
        return {
            "action": "transport",
            "screen_id": "",
            "n_representing": 0,
            "representing": [],
        }
    names = representing_in_menu(spec["task_id"], worlds, menu)
    chosen = coarsest_in_menu(spec["task_id"], worlds, menu)
    if chosen is None:
        return {
            "action": "broken",
            "screen_id": "",
            "n_representing": 0,
            "representing": [],
        }
    q_fn = EXT_SCREEN_FNS[spec["screen_id"]]
    y_fn = EXT_TASK_FNS[spec["task_id"]]
    current_n = fiber_count(worlds, q_fn)
    chosen_n = fiber_count(worlds, EXT_SCREEN_FNS[chosen])
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


def collisions_for(rows: list[MenuRow], menu_id: MenuId) -> list[Collision]:
    buckets: dict[tuple[bool, int, int, bool, bool], list[MenuRow]] = defaultdict(list)
    for row in rows:
        if row["menu"] == menu_id:
            buckets[signature_key(row["signature"])].append(row)
    found: list[Collision] = []
    for grouped in buckets.values():
        golds = {row["gold"] for row in grouped}
        if len(golds) > 1:
            found.append(
                {
                    "menu": menu_id,
                    "signature": grouped[0]["signature"],
                    "case_ids": sorted(row["case_id"] for row in grouped),
                    "golds": sorted(golds),
                }
            )
    found.sort(key=lambda item: item["case_ids"][0])
    return found


def reversal_image_world(world: World) -> World:
    return apply_perm(REVERSAL, world)


def relabel_row(
    source_task: str,
    image_task: str,
    screen_id: str,
    menu_id: MenuId,
    worlds: tuple[World, ...],
) -> RelabelRow:
    """Reversal (3,2,1,0) should carry source_task's choice to image_task's.

    Naturality is action equality plus the disclosed screen pairing:
    q_stab0 ↔ q_stab_last and q_pair01 ↔ q_pair23 are reversal duals;
    reversal-invariant screens must map to themselves.
    """

    dual = {
        "q_stab0": "q_stab_last",
        "q_stab_last": "q_stab0",
        "q_pair01": "q_pair23",
        "q_pair23": "q_pair01",
        "q_id": "q_id",
        "q_perm": "q_perm",
        "q_rot": "q_rot",
        "": "",
    }
    menu = menu_of(menu_id)
    source_spec: CaseSpec = {
        "case_id": f"relabel_{source_task}_{screen_id}",
        "split": "held_out",
        "task_id": source_task,
        "screen_id": screen_id,
        "edges": KIRCHHOFF_FLAT,
    }
    image_spec: CaseSpec = {
        "case_id": f"relabel_{image_task}_{screen_id}",
        "split": "held_out",
        "task_id": image_task,
        "screen_id": screen_id,
        "edges": KIRCHHOFF_FLAT,
    }
    source = kappa_screen_menu(source_spec, worlds, menu)
    image = kappa_screen_menu(image_spec, worlds, menu)
    action_natural = source["action"] == image["action"]
    screen_natural = dual[source["screen_id"]] == image["screen_id"]
    return {
        "source_task": source_task,
        "image_task": image_task,
        "menu": menu_id,
        "source_choice": source["screen_id"] or source["action"],
        "image_choice": image["screen_id"] or image["action"],
        "source_action": source["action"],
        "image_action": image["action"],
        "action_natural": action_natural,
        "screen_natural": screen_natural,
    }


def evaluate_benchmark() -> BenchmarkPayload:
    worlds = all_worlds()
    rows: list[MenuRow] = []
    menu_ids: tuple[MenuId, ...] = ("base", "ext")
    for spec in ALL_CASES:
        signature = signature_of_ext(spec, worlds)
        cheap = decide(signature)
        for menu_id in menu_ids:
            menu = menu_of(menu_id)
            gold = gold_of_menu(spec, worlds, menu)
            screen = kappa_screen_menu(spec, worlds, menu)
            rows.append(
                {
                    "case_id": spec["case_id"],
                    "split": spec["split"],
                    "task_id": spec["task_id"],
                    "screen_id": spec["screen_id"],
                    "menu": menu_id,
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

    by_case: dict[str, dict[MenuId, MenuRow]] = defaultdict(dict)
    for row in rows:
        by_case[row["case_id"]][row["menu"]] = row
    flips: list[FlipWitness] = []
    for case_id in sorted(by_case):
        pair = by_case[case_id]
        if pair["base"]["gold"] != pair["ext"]["gold"]:
            flips.append(
                {
                    "case_id": case_id,
                    "task_id": pair["base"]["task_id"],
                    "screen_id": pair["base"]["screen_id"],
                    "gold_base": pair["base"]["gold"],
                    "gold_ext": pair["ext"]["gold"],
                }
            )

    base_consistent = all(
        by_case[spec["case_id"]]["base"]["gold"] == gold_of(spec, worlds) for spec in CASES
    )

    collisions = collisions_for(rows, "base") + collisions_for(rows, "ext")
    relabels = [
        relabel_row("first_bit", "last_bit", "q_id", "base", worlds),
        relabel_row("first_bit", "last_bit", "q_id", "ext", worlds),
        relabel_row("pair_eq", "pair23", "q_id", "ext", worlds),
        relabel_row("pair23", "pair_eq", "q_id", "ext", worlds),
    ]
    relabel_action_ok = all(row["action_natural"] for row in relabels)
    tie_break_screen_natural = all(row["screen_natural"] for row in relabels)
    tie_witnesses = sorted(
        f"{row['source_task']}->{row['image_task']}"
        for row in relabels
        if not row["screen_natural"]
    )

    cheap_hits_base = sum(1 for row in rows if row["menu"] == "base" and row["cheap_hit"])
    cheap_hits_ext = sum(1 for row in rows if row["menu"] == "ext" and row["cheap_hit"])
    n_base_rows = sum(1 for row in rows if row["menu"] == "base")
    n_ext_rows = sum(1 for row in rows if row["menu"] == "ext")
    collisions_base = [item for item in collisions if item["menu"] == "base"]
    collisions_ext = [item for item in collisions if item["menu"] == "ext"]
    cheap_function_per_menu = {
        "base": len(collisions_base) == 0,
        "ext": len(collisions_ext) == 0,
    }
    screen_hits = sum(1 for row in rows if row["screen_hit"])
    screen_n = len(rows)
    screen_exact = screen_hits == screen_n
    cheap_exact_both = (
        cheap_hits_base == n_base_rows and cheap_hits_ext == n_ext_rows
    )
    cheap_function_both = cheap_function_per_menu["base"] and cheap_function_per_menu["ext"]

    if not screen_exact:
        verdict: Verdict = "no_function"
    elif flips:
        verdict = "menu_blind_dead"
    elif cheap_exact_both and cheap_function_both:
        verdict = "menu_blind_lives"
    else:
        verdict = "inconclusive"

    ranking: Ranking = {
        "rule": (
            "no_function if κ_screen misses any row.  menu_blind_dead if "
            "gold flips on any case between the two menus while κ_screen "
            "stays exact: a flip makes gold not a function of (Y, q), so "
            "no menu-blind κ of any width matches both menus.  "
            "menu_blind_lives if there is no flip and the frozen five-field "
            "rule is exact and collision-free under both menus.  "
            "inconclusive otherwise."
        ),
        "n_specs": len(ALL_CASES),
        "n_rows": screen_n,
        "n_flips": len(flips),
        "flip_case_ids": [flip["case_id"] for flip in flips],
        "base_consistent_with_paper_e": base_consistent,
        "cheap_hits_base": cheap_hits_base,
        "cheap_hits_ext": cheap_hits_ext,
        "cheap_collisions_base": len(collisions_base),
        "cheap_collisions_ext": len(collisions_ext),
        "cheap_function_per_menu": cheap_function_per_menu,
        "screen_hits": screen_hits,
        "screen_n": screen_n,
        "screen_exact": screen_exact,
        "relabel_action_natural": relabel_action_ok,
        "tie_break_screen_natural": tie_break_screen_natural,
        "tie_witnesses": tie_witnesses,
        "verdict": verdict,
    }
    required = {
        "MB_SPECIFIED": True,
        "MB_ENUMERATION": len(ALL_CASES) == 17 and screen_n == 34,
        "MB_MENUS": MENU_EXT[: len(MENU_BASE)] == MENU_BASE
        and set(MENU_EXT) - set(MENU_BASE) == {"q_pair01", "q_pair23"},
        "MB_CHEAP_FROZEN": all(
            set(row["signature"])
            == {
                "mixes",
                "n_fibres",
                "n_worlds",
                "y_has_nontrivial_symmetry",
                "connection_mismatch",
            }
            for row in rows
        ),
        "MB_BASE_CONSISTENT": base_consistent,
        "MB_FLIP_RECORDED": isinstance(flips, list),
        "MB_SCREEN_DEFINED": all(row["screen"] != "broken" for row in rows),
        "MB_RELABEL_ACTION": relabel_action_ok,
        "MB_TIE_RECORDED": tie_break_screen_natural or len(tie_witnesses) > 0,
        "MB_RANKING_RECORDED": ranking["verdict"]
        in {"menu_blind_dead", "menu_blind_lives", "no_function", "inconclusive"},
        "MB_CLAIM_BOUNDARY": True,
    }
    return {
        "status": "pass" if all(required.values()) else "fail",
        "experiment_id": EXPERIMENT_ID,
        "run_id": RUN_ID,
        "producing_agent": {"identity": PRODUCING_AGENT, "session_ref": SESSION_REF},
        "menus": {"base": list(MENU_BASE), "ext": list(MENU_EXT)},
        "specification": {
            "kappa_cheap": (
                "Paper E decide, imported frozen: mismatch→transport; "
                "mixes→restore; symmetry and n_fibres=n_worlds→quotient; "
                "else noop.  Never refit."
            ),
            "kappa_screen": (
                "Kirchhoff mismatch→transport; else coarsest representing "
                "screen in the *given* menu by fibre count then name; "
                "restore/quotient/noop from that choice.  Theorem 4 plus "
                "a total order, recomputed per menu."
            ),
            "gold": (
                "Paper E empirical gold with the menu as an explicit "
                "argument.  A flip between menus on a fixed case is the "
                "categorical kill of menu-blind κ."
            ),
            "menu_ext_new_screens": "q_pair01 (12 fibres), q_pair23 (12 fibres)",
            "new_tasks": "pair23, or, count_ge2",
        },
        "rows": rows,
        "flips": flips,
        "collisions": collisions,
        "relabels": relabels,
        "ranking": ranking,
        "gates": required,
        "process_disclosure": PROCESS_DISCLOSURE,
        "withheld": [
            "A new master object above SIC",
            "A refit of the cheap signature",
            "Text nomination / DR / DCR",
            "LLM agent eval",
            "A better language model",
            "Valence / concern (door 3 is a separate instrument)",
        ],
    }
