"""Door 3 consolidation: transport the concern choice across menus.

The door-3 paper registered its next test: move the concern machinery
across the reversal relabel and across door 1's menu extension, and
see whether the phase boundary is menu-stable.

Machinery: door 1's menu-parameterized representing sets over the
extended screen/task tables, door 3's registered cost rule
(fibre count on represent, 2·n_worlds on miss), exact rational
arithmetic, Paper F's tie-break.

Registered predictions:

- Under MENU_BASE, bag's representing set has 5 screens and the
  bag/pair_eq dial crosses q_perm → q_id at ε = 11/27 (the door-3
  anchor, reproduced by independent machinery).
- Under MENU_EXT, the representing set has 7 screens (q_pair01 and
  q_pair23 join at 12 fibres, and both also serve pair_eq), and the
  dial crosses q_perm → q_pair01 at ε = 7/27.
- The mirrored concern pair (bag+first_bit vs bag+last_bit) is
  reversal-natural under both menus.

So the concern boundary is *menu-relative*: doors 1 and 3 compose.
What you should hold depends jointly on what is on the menu and what
you expect to be asked.

Registered outcomes (all pass CI):

``transport_holds_boundary_moves``
    Reversal-natural under both menus, base boundary 11/27 reproduced,
    ext boundary 7/27 confirmed, boundaries differ.

``boundary_menu_stable``
    Naturality holds and the two boundaries are equal.

``transport_fails``
    Reversal naturality breaks under either menu.

``inconclusive``
    Anything else.

Not valence.  Not learned concern.  Not a new master object.  Not
Paper G.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Literal, TypedDict

from experiments.delete_repair_menu_blind.core import (
    EXT_SCREEN_FNS,
    EXT_TASK_FNS,
    MENU_BASE,
    MENU_EXT,
    representing_in_menu,
)
from experiments.delete_the_absolute.core import (
    World,
    all_worlds,
    fiber_count,
    y_constant_on_fibers,
)

EXPERIMENT_ID = "delete_repair_concern_transport"
RUN_ID = "delete_repair_concern_transport_2026_08_18"
PRODUCING_AGENT = "Claude Fable 5 (Cursor agent, under J. Brown direction)"
SESSION_REF = "4adbd42d-0e99-41df-b0be-7d9d5b7e3caa"

PROCESS_DISCLOSURE = (
    "Door 3's registered cost rule run through door 1's two menus with "
    "exact rational arithmetic.  Boundaries predicted before the run "
    "(11/27 base, 7/27 extended).  No sampling, no learning, no LLM."
)

MISS_PENALTY_FACTOR = 2

Verdict = Literal[
    "transport_holds_boundary_moves",
    "boundary_menu_stable",
    "transport_fails",
    "inconclusive",
]
MenuId = Literal["base", "ext"]

Concern = tuple[tuple[str, Fraction], ...]


class ProducingAgent(TypedDict):
    identity: str
    session_ref: str


class MenuConcernRow(TypedDict):
    menu: MenuId
    concern_id: str
    chosen_screen: str


class NaturalityRow(TypedDict):
    menu: MenuId
    source_choice: str
    image_choice: str
    natural: bool


class BoundaryReport(TypedDict):
    menu: MenuId
    n_candidates: int
    boundary_exact: str
    choice_below: str
    choice_above: str
    confirmed: bool


class Ranking(TypedDict):
    rule: str
    base_candidates: list[str]
    ext_candidates: list[str]
    base_boundary: str
    ext_boundary: str
    boundary_menu_relative: bool
    reversal_natural_both_menus: bool
    verdict: Verdict


class BenchmarkPayload(TypedDict):
    status: Literal["pass", "fail"]
    experiment_id: str
    run_id: str
    producing_agent: ProducingAgent
    concerns: list[MenuConcernRow]
    naturality: list[NaturalityRow]
    boundaries: list[BoundaryReport]
    ranking: Ranking
    gates: dict[str, bool]
    process_disclosure: str
    withheld: list[str]


def menu_of(menu_id: MenuId) -> tuple[str, ...]:
    return MENU_BASE if menu_id == "base" else MENU_EXT


def serving_cost(screen_id: str, task_id: str, worlds: tuple[World, ...]) -> Fraction:
    q_fn = EXT_SCREEN_FNS[screen_id]
    y_fn = EXT_TASK_FNS[task_id]
    if y_constant_on_fibers(worlds, q_fn, y_fn):
        return Fraction(fiber_count(worlds, q_fn))
    return Fraction(MISS_PENALTY_FACTOR * len(worlds))


def kappa_concern_menu(
    concern: Concern, menu_id: MenuId, worlds: tuple[World, ...]
) -> str:
    candidates = representing_in_menu("bag", worlds, menu_of(menu_id))
    costs = {
        name: sum(
            (weight * serving_cost(name, task_id, worlds) for task_id, weight in concern),
            start=Fraction(0),
        )
        for name in candidates
    }
    best = min(costs.values())
    tied = [name for name in candidates if costs[name] == best]
    tied.sort(key=lambda name: (fiber_count(worlds, EXT_SCREEN_FNS[name]), name))
    return tied[0]


def concern_of(pairs: dict[str, Fraction]) -> Concern:
    return tuple(sorted(pairs.items()))


def eps_concern(eps: Fraction) -> Concern:
    return concern_of({"bag": 1 - eps, "pair_eq": eps})


def boundary_report(
    menu_id: MenuId,
    predicted: Fraction,
    choice_below: str,
    choice_above: str,
    worlds: tuple[World, ...],
) -> BoundaryReport:
    """Sweep ε over k/54 and confirm the predicted crossing point.

    At the exact tie the fewest-fibres rule keeps the below-choice.
    """

    confirmed = True
    for numerator in range(0, 55):
        eps = Fraction(numerator, 54)
        chosen = kappa_concern_menu(eps_concern(eps), menu_id, worlds)
        expected = choice_below if eps <= predicted else choice_above
        if chosen != expected:
            confirmed = False
    return {
        "menu": menu_id,
        "n_candidates": len(representing_in_menu("bag", worlds, menu_of(menu_id))),
        "boundary_exact": str(predicted),
        "choice_below": choice_below,
        "choice_above": choice_above,
        "confirmed": confirmed,
    }


def evaluate_benchmark() -> BenchmarkPayload:
    worlds = all_worlds()
    base_candidates = representing_in_menu("bag", worlds, MENU_BASE)
    ext_candidates = representing_in_menu("bag", worlds, MENU_EXT)

    registered_concerns: tuple[tuple[str, Concern], ...] = (
        ("delta_bag", concern_of({"bag": Fraction(1)})),
        (
            "bag_first",
            concern_of({"bag": Fraction(1, 2), "first_bit": Fraction(1, 2)}),
        ),
        (
            "bag_last",
            concern_of({"bag": Fraction(1, 2), "last_bit": Fraction(1, 2)}),
        ),
        (
            "bag_pair_eq",
            concern_of({"bag": Fraction(1, 2), "pair_eq": Fraction(1, 2)}),
        ),
    )
    concerns: list[MenuConcernRow] = []
    choices: dict[tuple[MenuId, str], str] = {}
    menu_ids: tuple[MenuId, ...] = ("base", "ext")
    for menu_id in menu_ids:
        for concern_id, concern in registered_concerns:
            chosen = kappa_concern_menu(concern, menu_id, worlds)
            choices[(menu_id, concern_id)] = chosen
            concerns.append(
                {"menu": menu_id, "concern_id": concern_id, "chosen_screen": chosen}
            )

    dual = {
        "q_stab0": "q_stab_last",
        "q_stab_last": "q_stab0",
        "q_pair01": "q_pair23",
        "q_pair23": "q_pair01",
        "q_id": "q_id",
        "q_perm": "q_perm",
        "q_rot": "q_rot",
    }
    naturality: list[NaturalityRow] = []
    for menu_id in menu_ids:
        source = choices[(menu_id, "bag_first")]
        image = choices[(menu_id, "bag_last")]
        naturality.append(
            {
                "menu": menu_id,
                "source_choice": source,
                "image_choice": image,
                "natural": dual[source] == image,
            }
        )
    reversal_ok = all(row["natural"] for row in naturality)

    boundaries = [
        boundary_report("base", Fraction(11, 27), "q_perm", "q_id", worlds),
        boundary_report("ext", Fraction(7, 27), "q_perm", "q_pair01", worlds),
    ]
    boundaries_confirmed = all(report["confirmed"] for report in boundaries)
    base_boundary = Fraction(boundaries[0]["boundary_exact"])
    ext_boundary = Fraction(boundaries[1]["boundary_exact"])
    boundary_moves = base_boundary != ext_boundary

    if not reversal_ok:
        verdict: Verdict = "transport_fails"
    elif boundaries_confirmed and boundary_moves:
        verdict = "transport_holds_boundary_moves"
    elif boundaries_confirmed:
        verdict = "boundary_menu_stable"
    else:
        verdict = "inconclusive"

    ranking: Ranking = {
        "rule": (
            "transport_fails if reversal naturality breaks under either "
            "menu.  transport_holds_boundary_moves if naturality holds, "
            "both registered boundaries are confirmed by the sweep, and "
            "they differ.  boundary_menu_stable if they are equal.  "
            "inconclusive otherwise."
        ),
        "base_candidates": base_candidates,
        "ext_candidates": ext_candidates,
        "base_boundary": str(base_boundary),
        "ext_boundary": str(ext_boundary),
        "boundary_menu_relative": boundary_moves,
        "reversal_natural_both_menus": reversal_ok,
        "verdict": verdict,
    }
    required = {
        "CT_SPECIFIED": True,
        "CT_CANDIDATE_SETS": len(base_candidates) == 5 and len(ext_candidates) == 7,
        "CT_DELTA_ANCHOR": choices[("base", "delta_bag")] == "q_perm"
        and choices[("ext", "delta_bag")] == "q_perm",
        "CT_BOUNDARIES_CONFIRMED": boundaries_confirmed,
        "CT_REVERSAL": reversal_ok,
        "CT_RANKING_RECORDED": ranking["verdict"]
        in {
            "transport_holds_boundary_moves",
            "boundary_menu_stable",
            "transport_fails",
            "inconclusive",
        },
        "CT_CLAIM_BOUNDARY": True,
    }
    return {
        "status": "pass" if all(required.values()) else "fail",
        "experiment_id": EXPERIMENT_ID,
        "run_id": RUN_ID,
        "producing_agent": {"identity": PRODUCING_AGENT, "session_ref": SESSION_REF},
        "concerns": concerns,
        "naturality": naturality,
        "boundaries": boundaries,
        "ranking": ranking,
        "gates": required,
        "process_disclosure": PROCESS_DISCLOSURE,
        "withheld": [
            "Valence, agency, consciousness, phenomenology",
            "Learned or inferred concern",
            "A new master object above SIC",
            "LLM agent eval",
            "A better language model",
        ],
    }
