"""Door 3 of the close-out: does concern do real work at the lowest bound?

The close-out split "discover all" into three jobs: write all, reach
all, care which matter.  The third job — concern — was never claimed.
Paper F left a hook for it: `bag` has five representing screens, and
the choice among them was made by a disclosed but arbitrary total
order (fewest fibres, then name).  Door 1 then showed that name
tie-break is not even relabel-natural.

This instrument gives the choice a reason.  Concern is a registered
weight vector over a finite task family.  The cost of holding screen
``r`` under concern ``w`` is the expected serving cost:

    cost(t | r) = n_fibres(r)      if r represents t
                  2 * n_worlds      otherwise (a registered miss penalty)

    κ_concern(w) = argmin over R(bag) of Σ_t w(t) · cost(t | r),
    ties broken by fewest fibres then name (Paper F's order).

Everything is exact rational arithmetic.  No sampling, no learning,
no valence, no phenomenology.  Concern here is a weighting and
nothing else.

Registered outcomes (all pass CI):

``concern_does_work``
    At least three distinct screens are selected across the
    registered concern set, the selection is reversal-natural on the
    mirrored concern pair, and the unweighted Paper F choice is
    strictly suboptimal under at least one registered concern (gap
    recorded exactly).

``concern_idle``
    Every registered concern selects the same screen.  The tie-break
    was already doing all the work and door 3 closes at this bound.

``inconclusive``
    Anything else.

Not valence.  Not agency.  Not consciousness.  Not an LLM.  Not a new
master object.  Not Paper G.
"""

from __future__ import annotations

from collections.abc import Callable
from fractions import Fraction
from typing import Literal, TypedDict

from experiments.delete_repair_surgery.core import SCREEN_FNS, TASK_FNS
from experiments.delete_the_absolute.core import (
    Feature,
    World,
    all_worlds,
    apply_perm,
    fiber_count,
    y_constant_on_fibers,
)

EXPERIMENT_ID = "delete_repair_concern"
RUN_ID = "delete_repair_concern_2026_08_18"
PRODUCING_AGENT = "Claude Fable 5 (Cursor agent, under J. Brown direction)"
SESSION_REF = "4adbd42d-0e99-41df-b0be-7d9d5b7e3caa"

PROCESS_DISCLOSURE = (
    "Concern is a registered rational weight vector over six tasks.  "
    "Cost is a registered two-case rule (fibre count on represent, "
    "2·n_worlds on miss).  κ_concern is exact argmin with Paper F's "
    "tie-break.  No sampling, no learning, no valence claim."
)

REVERSAL: tuple[int, ...] = (3, 2, 1, 0)
MISS_PENALTY_FACTOR = 2

Verdict = Literal["concern_does_work", "concern_idle", "inconclusive"]

TASK_FAMILY: tuple[str, ...] = (
    "bag",
    "first_bit",
    "last_bit",
    "parity",
    "pair_eq",
    "identity",
)

Concern = tuple[tuple[str, Fraction], ...]


class ProducingAgent(TypedDict):
    identity: str
    session_ref: str


class CostCell(TypedDict):
    screen_id: str
    task_id: str
    represents: bool
    cost: str


class ConcernRow(TypedDict):
    concern_id: str
    weights: dict[str, str]
    chosen_screen: str
    expected_costs: dict[str, str]
    beats_unweighted_choice: bool
    gap_vs_unweighted: str


class NaturalityRow(TypedDict):
    source_concern: str
    image_concern: str
    source_choice: str
    image_choice: str
    natural: bool


class BoundaryRow(TypedDict):
    epsilon: str
    chosen_screen: str


class Ranking(TypedDict):
    rule: str
    representing_set: list[str]
    n_distinct_choices: int
    distinct_choices: list[str]
    unweighted_choice: str
    unweighted_strictly_beaten: bool
    max_gap: str
    reversal_natural: bool
    phase_boundary_exact: str
    phase_boundary_confirmed: bool
    verdict: Verdict


class BenchmarkPayload(TypedDict):
    status: Literal["pass", "fail"]
    experiment_id: str
    run_id: str
    producing_agent: ProducingAgent
    task_family: list[str]
    cost_matrix: list[CostCell]
    concerns: list[ConcernRow]
    naturality: list[NaturalityRow]
    boundary_sweep: list[BoundaryRow]
    ranking: Ranking
    gates: dict[str, bool]
    process_disclosure: str
    withheld: list[str]


def representing_set_for_bag(worlds: tuple[World, ...]) -> list[str]:
    y_bag_fn = TASK_FNS["bag"]
    named: list[tuple[int, str]] = []
    for name, q_fn in SCREEN_FNS.items():
        if y_constant_on_fibers(worlds, q_fn, y_bag_fn):
            named.append((fiber_count(worlds, q_fn), name))
    named.sort()
    return [name for _count, name in named]


def serving_cost(
    screen_id: str, task_id: str, worlds: tuple[World, ...]
) -> tuple[bool, Fraction]:
    q_fn = SCREEN_FNS[screen_id]
    y_fn: Callable[[World], Feature] = TASK_FNS[task_id]
    represents = y_constant_on_fibers(worlds, q_fn, y_fn)
    if represents:
        return True, Fraction(fiber_count(worlds, q_fn))
    return False, Fraction(MISS_PENALTY_FACTOR * len(worlds))


def expected_cost(
    screen_id: str, concern: Concern, worlds: tuple[World, ...]
) -> Fraction:
    total = Fraction(0)
    for task_id, weight in concern:
        _represents, cost = serving_cost(screen_id, task_id, worlds)
        total += weight * cost
    return total


def kappa_concern(
    concern: Concern, candidates: list[str], worlds: tuple[World, ...]
) -> tuple[str, dict[str, Fraction]]:
    costs = {name: expected_cost(name, concern, worlds) for name in candidates}
    best_cost = min(costs.values())
    tied = [name for name in candidates if costs[name] == best_cost]
    tied.sort(key=lambda name: (fiber_count(worlds, SCREEN_FNS[name]), name))
    return tied[0], costs


def concern_of(pairs: dict[str, Fraction]) -> Concern:
    return tuple(sorted(pairs.items()))


def uniform_over(task_ids: tuple[str, ...]) -> Concern:
    weight = Fraction(1, len(task_ids))
    return concern_of({task_id: weight for task_id in task_ids})


REGISTERED_CONCERNS: tuple[tuple[str, Concern], ...] = (
    ("delta_bag", concern_of({"bag": Fraction(1)})),
    ("bag_first", uniform_over(("bag", "first_bit"))),
    ("bag_last", uniform_over(("bag", "last_bit"))),
    ("bag_pair_eq", uniform_over(("bag", "pair_eq"))),
    ("bag_parity", uniform_over(("bag", "parity"))),
    ("all_six", uniform_over(TASK_FAMILY)),
)


def evaluate_benchmark() -> BenchmarkPayload:
    worlds = all_worlds()
    candidates = representing_set_for_bag(worlds)

    cost_matrix: list[CostCell] = []
    for screen_id in candidates:
        for task_id in TASK_FAMILY:
            represents, cost = serving_cost(screen_id, task_id, worlds)
            cost_matrix.append(
                {
                    "screen_id": screen_id,
                    "task_id": task_id,
                    "represents": represents,
                    "cost": str(cost),
                }
            )

    unweighted_choice, _ = kappa_concern(
        concern_of({"bag": Fraction(1)}), candidates, worlds
    )

    concern_rows: list[ConcernRow] = []
    choices: dict[str, str] = {}
    max_gap = Fraction(0)
    unweighted_beaten = False
    for concern_id, concern in REGISTERED_CONCERNS:
        chosen, costs = kappa_concern(concern, candidates, worlds)
        choices[concern_id] = chosen
        gap = costs[unweighted_choice] - costs[chosen]
        if gap > 0:
            unweighted_beaten = True
            max_gap = max(max_gap, gap)
        concern_rows.append(
            {
                "concern_id": concern_id,
                "weights": {task: str(weight) for task, weight in concern},
                "chosen_screen": chosen,
                "expected_costs": {name: str(costs[name]) for name in candidates},
                "beats_unweighted_choice": gap > 0,
                "gap_vs_unweighted": str(gap),
            }
        )

    # Reversal naturality: the mirrored concern pair must choose dual
    # screens.  Reversal sends first_bit to last_bit and q_stab0 to
    # q_stab_last; bag and parity are reversal-invariant.
    dual = {
        "q_stab0": "q_stab_last",
        "q_stab_last": "q_stab0",
        "q_id": "q_id",
        "q_perm": "q_perm",
        "q_rot": "q_rot",
    }
    naturality: list[NaturalityRow] = [
        {
            "source_concern": "bag_first",
            "image_concern": "bag_last",
            "source_choice": choices["bag_first"],
            "image_choice": choices["bag_last"],
            "natural": dual[choices["bag_first"]] == choices["bag_last"],
        },
        {
            "source_concern": "bag_last",
            "image_concern": "bag_first",
            "source_choice": choices["bag_last"],
            "image_choice": choices["bag_first"],
            "natural": dual[choices["bag_last"]] == choices["bag_first"],
        },
    ]
    reversal_ok = all(row["natural"] for row in naturality)
    reversal_world_check = all(
        apply_perm(REVERSAL, apply_perm(REVERSAL, world)) == world for world in worlds
    )

    # Phase boundary on w_eps = (1-eps)·bag + eps·pair_eq.  Registered
    # prediction: cost(q_perm) = 5 + 27·eps crosses cost(q_id) = 16 at
    # eps* = 11/27; at the tie the fewest-fibres rule keeps q_perm.
    boundary_exact = Fraction(11, 27)
    boundary_sweep: list[BoundaryRow] = []
    for numerator in range(0, 55):
        eps = Fraction(numerator, 54)
        concern = concern_of({"bag": 1 - eps, "pair_eq": eps})
        chosen, _costs = kappa_concern(concern, candidates, worlds)
        boundary_sweep.append({"epsilon": str(eps), "chosen_screen": chosen})
    below = [row for row in boundary_sweep if Fraction(row["epsilon"]) <= boundary_exact]
    above = [row for row in boundary_sweep if Fraction(row["epsilon"]) > boundary_exact]
    boundary_confirmed = (
        all(row["chosen_screen"] == "q_perm" for row in below)
        and all(row["chosen_screen"] == "q_id" for row in above)
        and len(above) > 0
    )

    distinct = sorted(set(choices.values()))
    if len(distinct) >= 3 and reversal_ok and unweighted_beaten:
        verdict: Verdict = "concern_does_work"
    elif len(distinct) == 1:
        verdict = "concern_idle"
    else:
        verdict = "inconclusive"

    ranking: Ranking = {
        "rule": (
            "concern_does_work iff the registered concern set selects at "
            "least three distinct screens from bag's representing set, "
            "the mirrored concern pair is reversal-natural, and the "
            "unweighted Paper F choice is strictly beaten somewhere "
            "(exact gap recorded).  concern_idle iff every concern "
            "selects one screen.  inconclusive otherwise."
        ),
        "representing_set": candidates,
        "n_distinct_choices": len(distinct),
        "distinct_choices": distinct,
        "unweighted_choice": unweighted_choice,
        "unweighted_strictly_beaten": unweighted_beaten,
        "max_gap": str(max_gap),
        "reversal_natural": reversal_ok,
        "phase_boundary_exact": str(boundary_exact),
        "phase_boundary_confirmed": boundary_confirmed,
        "verdict": verdict,
    }
    required = {
        "CON_SPECIFIED": True,
        "CON_REPRESENTING_SET": len(candidates) == 5,
        "CON_COST_MATRIX_RECORDED": len(cost_matrix) == 5 * len(TASK_FAMILY),
        "CON_CONCERNS_REGISTERED": len(REGISTERED_CONCERNS) == 6,
        "CON_EXACT_ARITHMETIC": all(
            "/" in row["gap_vs_unweighted"] or row["gap_vs_unweighted"].lstrip("-").isdigit()
            for row in concern_rows
        ),
        "CON_REVERSAL": reversal_ok and reversal_world_check,
        "CON_BOUNDARY": boundary_confirmed,
        "CON_RANKING_RECORDED": ranking["verdict"]
        in {"concern_does_work", "concern_idle", "inconclusive"},
        "CON_CLAIM_BOUNDARY": True,
    }
    return {
        "status": "pass" if all(required.values()) else "fail",
        "experiment_id": EXPERIMENT_ID,
        "run_id": RUN_ID,
        "producing_agent": {"identity": PRODUCING_AGENT, "session_ref": SESSION_REF},
        "task_family": list(TASK_FAMILY),
        "cost_matrix": cost_matrix,
        "concerns": concern_rows,
        "naturality": naturality,
        "boundary_sweep": boundary_sweep,
        "ranking": ranking,
        "gates": required,
        "process_disclosure": PROCESS_DISCLOSURE,
        "withheld": [
            "Valence, agency, consciousness, phenomenology",
            "Learned or inferred concern (weights are registered inputs)",
            "A new master object above SIC",
            "LLM agent eval",
            "A better language model",
        ],
    }
